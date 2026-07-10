"""FastAPI routes for the Fan Production MVP event API."""

from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path
import tempfile
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, FastAPI, Query, Request, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, PlainTextResponse
from starlette.datastructures import UploadFile as StarletteUploadFile
from starlette.middleware.sessions import SessionMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException

from api.auth import verify_api_session, verify_csrf_token, verify_secrets_configured
from api.security import SecureHeadersMiddleware, limiter

from application import (
    EVENT_STATUS_COMPLETED,
    EVENT_STATUS_FAILED,
    EVENT_STATUS_PROCESSING,
    EVENT_STATUS_QUEUED,
    AnalysisRepository,
    AnalysisResultRecord,
    AnalysisRunRecord,
    EventRecord,
    EventRepository,
)
from infrastructure import (
    ArtifactNotRegisteredError,
    ArtifactRegistry,
    AudioNotFoundError,
    AudioStorage,
    AudioStorageError,
    AudioStorageMetadata,
    DurableAudioStorage,
    LocalDurableAudioStorage,
    LocalAudioStorage,
    SQLiteAnalysisRepository,
    SQLiteEventRepository,
    UnsupportedAudioTypeError,
    connect_sqlite,
)
from infrastructure.artifact_registry import (
    FAN_MACHINE_ID,
    FAN_MACHINE_TYPE,
    FAN_REAL_INTELLIGENCE_SNR,
)
from observability import MetricsRegistry, StructuredLogger, get_structured_logger

from .schemas import (
    API_VERSION,
    AnalysisRunSummary,
    AudioSummary,
    DependencyStatus,
    ErrorBody,
    ErrorResponse,
    EventCreateResponse,
    EventDetailResponse,
    EventError,
    EventListResponse,
    EventSummary,
    HealthResponse,
    Pagination,
    ReadyResponse,
)
from .dashboard import dashboard_router


SERVICE_NAME = "amhi-fan-production-mvp"
DEFAULT_MAX_UPLOAD_BYTES = 25 * 1024 * 1024


@dataclass
class ApiDependencies:
    """Runtime dependencies injected into API routes."""

    event_repository: EventRepository
    analysis_repository: AnalysisRepository
    artifact_registry: ArtifactRegistry = field(default_factory=ArtifactRegistry)
    audio_storage: DurableAudioStorage | None = None
    structured_logger: StructuredLogger = field(default_factory=get_structured_logger)
    metrics_registry: MetricsRegistry = field(default_factory=MetricsRegistry)
    upload_dir: Path = field(
        default_factory=lambda: Path(tempfile.gettempdir()) / "amhi_uploads",
    )
    allow_registered_audio_reference: bool = False
    max_upload_bytes: int = DEFAULT_MAX_UPLOAD_BYTES
    service_name: str = SERVICE_NAME
    worker_initialized: bool = True


@dataclass(frozen=True)
class EventSubmission:
    """Parsed event creation request."""

    event_id: str
    machine_type: str
    machine_id: str
    snr_tag: str
    uploaded_file: StarletteUploadFile | None = None
    registered_audio_reference: str | None = None


@dataclass(frozen=True)
class StoredAudio:
    """Internal audio reference plus public summary."""

    internal_reference: str
    summary: AudioSummary


class ApiException(Exception):
    """Exception converted into the standard API error schema."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or {}


def create_default_dependencies() -> ApiDependencies:
    """Create a local default dependency set for import-time app creation."""
    database_url = os.environ.get("DATABASE_URL", "")
    upload_dir = Path(
        os.environ.get(
            "AMHI_UPLOAD_DIR",
            str(Path(tempfile.gettempdir()) / "amhi_uploads"),
        ),
    )
    if database_url:
        from infrastructure import (
            PostgresEventRepository,
            PostgresAnalysisRepository,
            connect_postgres,
        )
        pg_connection = connect_postgres(database_url)
        event_repository = PostgresEventRepository(pg_connection)
        analysis_repository = PostgresAnalysisRepository(pg_connection)
    else:
        sqlite_path = os.environ.get("AMHI_SQLITE_PATH", ":memory:")
        connection = connect_sqlite(sqlite_path, check_same_thread=False)
        event_repository = SQLiteEventRepository(connection)
        analysis_repository = SQLiteAnalysisRepository(connection)
    return ApiDependencies(
        event_repository=event_repository,
        analysis_repository=analysis_repository,
        upload_dir=upload_dir,
        audio_storage=LocalDurableAudioStorage(upload_dir=upload_dir),
        allow_registered_audio_reference=(
            os.environ.get("AMHI_ALLOW_REGISTERED_AUDIO_REFERENCE", "0") == "1"
        ),
        worker_initialized=(os.environ.get("AMHI_WORKER_INITIALIZED", "1") == "1"),
    )


def create_app(dependencies: ApiDependencies | None = None) -> FastAPI:
    """Create the FastAPI app with injectable repositories and storage."""
    app = FastAPI(
        title="Acoustic Machine Health Intelligence API",
        version=API_VERSION,
        docs_url=None if not os.environ.get("DEBUG_MODE", "false").lower() == "true" else "/docs",
        redoc_url=None if not os.environ.get("DEBUG_MODE", "false").lower() == "true" else "/redoc",
        openapi_url=None if not os.environ.get("DEBUG_MODE", "false").lower() == "true" else "/openapi.json",
    )
    
    verify_secrets_configured()
    
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    # Session middleware requires a secret key
    from config import AMHI_SESSION_SECRET
    app.add_middleware(
        SessionMiddleware, 
        secret_key=AMHI_SESSION_SECRET, 
        session_cookie="amhi_session",
        max_age=3600, # 1 hour bounded session
        same_site="lax",
        https_only=not os.environ.get("DEBUG_MODE", "false").lower() == "true"
    )
    
    app.add_middleware(
        TrustedHostMiddleware, allowed_hosts=os.environ.get("ALLOWED_HOSTS", "*").split(",")
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=os.environ.get("ALLOWED_ORIGINS", "*").split(","),
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )
    app.add_middleware(SecureHeadersMiddleware)
    
    app.state.dependencies = dependencies or create_default_dependencies()
    router = APIRouter(prefix="/api/v1")

    @app.exception_handler(ApiException)
    async def api_exception_handler(_: Request, exc: ApiException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_model_to_dict(
                ErrorResponse(
                    error=ErrorBody(
                        code=exc.code,
                        message=exc.message,
                        details=exc.details,
                    ),
                ),
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        _: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=_model_to_dict(
                ErrorResponse(
                    error=ErrorBody(
                        code="invalid_request",
                        message="Request validation failed.",
                        details={"errors": _safe_validation_errors(exc)},
                    ),
                ),
            ),
        )

    @router.post(
        "/events",
        status_code=202,
        response_model=EventCreateResponse,
        responses={
            400: {"model": ErrorResponse},
            415: {"model": ErrorResponse},
            422: {"model": ErrorResponse},
        },
        openapi_extra={
            "requestBody": {
                "content": {
                    "multipart/form-data": {
                        "schema": {
                            "type": "object",
                            "required": [
                                "machine_type",
                                "machine_id",
                                "snr_tag",
                                "audio_file",
                            ],
                            "properties": {
                                "machine_type": {"type": "string", "enum": ["fan"]},
                                "machine_id": {"type": "string", "enum": ["id_00"]},
                                "snr_tag": {"type": "string", "enum": ["minus6dB"]},
                                "audio_file": {"type": "string", "format": "binary"},
                                "client_event_id": {"type": "string"},
                            },
                        },
                    },
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "required": [
                                "machine_type",
                                "machine_id",
                                "snr_tag",
                                "registered_audio_reference",
                            ],
                            "properties": {
                                "machine_type": {"type": "string", "enum": ["fan"]},
                                "machine_id": {"type": "string", "enum": ["id_00"]},
                                "snr_tag": {"type": "string", "enum": ["minus6dB"]},
                                "registered_audio_reference": {"type": "string"},
                            },
                        },
                    },
                },
            },
        },
        dependencies=[Depends(verify_api_session), Depends(verify_csrf_token)]
    )
    @limiter.limit("5/minute")
    async def create_event(request: Request) -> EventCreateResponse:
        deps = _dependencies(request)
        submission = await _parse_submission(request, deps)
        try:
            _validate_fan_scope(
                deps,
                submission.machine_type,
                submission.machine_id,
                submission.snr_tag,
            )
            stored_audio = await _store_audio_submission(submission, deps)
            event = deps.event_repository.create_event(
                event_id=submission.event_id,
                machine_type=submission.machine_type,
                machine_id=submission.machine_id,
                snr_tag=submission.snr_tag,
                audio_reference=stored_audio.internal_reference,
            )
            deps.structured_logger.emit(
                "event_created",
                event_id=event.event_id,
                machine_type=event.machine_type,
                machine_id=event.machine_id,
                stage="api",
                status=event.status,
                audio_file_name=stored_audio.summary.file_name,
                storage_backend=stored_audio.summary.storage_backend,
            )
            deps.metrics_registry.increment("amhi_events_created_total")
            deps.structured_logger.emit(
                "event_queued",
                event_id=event.event_id,
                machine_type=event.machine_type,
                machine_id=event.machine_id,
                stage="api",
                status=event.status,
            )
            return EventCreateResponse(
                event=_event_summary(event, stored_audio.summary),
                links={"self": f"/api/v1/events/{event.event_id}"},
            )
        finally:
            await _close_submission_upload(submission)

    @router.get(
        "/events/{event_id}",
        response_model=EventDetailResponse,
        responses={404: {"model": ErrorResponse}},
        dependencies=[Depends(verify_api_session)]
    )
    async def get_event(event_id: str, request: Request) -> EventDetailResponse:
        deps = _dependencies(request)
        event = _require_event(deps, event_id)
        run = deps.analysis_repository.get_latest_run_for_event(event_id)
        result = deps.analysis_repository.get_result(run.analysis_run_id) if run else None
        return EventDetailResponse(
            event=_event_summary(event, _audio_summary_for_event(event, deps)),
            analysis_run=_analysis_run_summary(run) if run else None,
            result=_analysis_result_payload(result) if result else None,
        )

    @router.get(
        "/events",
        response_model=EventListResponse,
        dependencies=[Depends(verify_api_session)]
    )
    async def list_events(
        request: Request,
        status: str | None = Query(default=None),
        limit: int = Query(default=50, ge=1, le=100),
        offset: int = Query(default=0, ge=0),
    ) -> EventListResponse:
        deps = _dependencies(request)
        if status is not None and status not in {
            EVENT_STATUS_QUEUED,
            EVENT_STATUS_PROCESSING,
            EVENT_STATUS_COMPLETED,
            EVENT_STATUS_FAILED,
        }:
            raise ApiException(422, "invalid_request", f"Unsupported event status: {status}")
        rows = deps.event_repository.list_events(limit=limit, offset=offset, status=status)
        return EventListResponse(
            items=[_event_summary(row, _audio_summary_for_event(row, deps)) for row in rows],
            pagination=Pagination(
                limit=limit,
                offset=offset,
                count=len(rows),
                next_offset=offset + len(rows) if len(rows) == limit else None,
            ),
        )

    @router.get(
        "/machines/{machine_type}/{machine_id}/events",
        response_model=EventListResponse,
        responses={
            422: {"model": ErrorResponse},
        },
        dependencies=[Depends(verify_api_session)]
    )
    async def list_machine_events(
        machine_type: str,
        machine_id: str,
        request: Request,
        limit: int = Query(default=50, ge=1, le=100),
        offset: int = Query(default=0, ge=0),
    ) -> EventListResponse:
        deps = _dependencies(request)
        if str(machine_type).strip().lower() != FAN_MACHINE_TYPE:
            raise ApiException(
                422,
                "unsupported_machine",
                "Only fan/id_00 is supported by this Fan Production MVP.",
            )
        if machine_id != FAN_MACHINE_ID:
            raise ApiException(
                422,
                "unsupported_machine_id",
                "Only fan/id_00 is supported by this Fan Production MVP.",
            )
        rows = deps.event_repository.list_machine_events(
            machine_type=FAN_MACHINE_TYPE,
            machine_id=FAN_MACHINE_ID,
            limit=limit,
            offset=offset,
        )
        return EventListResponse(
            items=[_event_summary(row, _audio_summary_for_event(row, deps)) for row in rows],
            pagination=Pagination(
                limit=limit,
                offset=offset,
                count=len(rows),
                next_offset=offset + len(rows) if len(rows) == limit else None,
            ),
        )

    @router.get("/health", response_model=HealthResponse)
    async def health(request: Request) -> HealthResponse:
        return HealthResponse(status="ok", service=_dependencies(request).service_name)

    @router.get("/ready", response_model=ReadyResponse)
    async def ready(request: Request) -> ReadyResponse:
        deps = _dependencies(request)
        dependency_status = _readiness(deps)
        is_ready = all(
            row.status in {"ok", "configured", "initialized"}
            for row in dependency_status.values()
        )
        return ReadyResponse(
            ready=is_ready,
            status="ready" if is_ready else "not_ready",
            dependencies=dependency_status,
        )

    @router.get("/metrics", response_class=PlainTextResponse, dependencies=[Depends(verify_api_session)])
    async def metrics(request: Request) -> PlainTextResponse:
        deps = _dependencies(request)
        deps.metrics_registry.set_gauge(
            "amhi_events_queued",
            deps.event_repository.count_events(status=EVENT_STATUS_QUEUED),
        )
        return PlainTextResponse(
            deps.metrics_registry.render_prometheus(),
            media_type="text/plain; version=0.0.4",
        )

    app.include_router(router)
    app.include_router(dashboard_router)
    return app

async def _parse_submission(request: Request, deps: ApiDependencies) -> EventSubmission:
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > deps.max_upload_bytes:
        raise ApiException(413, "payload_too_large", f"Request exceeds maximum size of {deps.max_upload_bytes} bytes.")
        
    content_type = request.headers.get("content-type", "")
    event_id = f"event_{uuid4().hex}"
    if "multipart/form-data" in content_type:
        form = await request.form()
        upload = form.get("audio_file")
        if not isinstance(upload, StarletteUploadFile):
            raise ApiException(400, "invalid_request", "audio_file is required.")
        try:
            return EventSubmission(
                event_id=event_id,
                machine_type=_required_form_text(form, "machine_type"),
                machine_id=_required_form_text(form, "machine_id"),
                snr_tag=_required_form_text(form, "snr_tag"),
                uploaded_file=upload,
            )
        except Exception:
            await upload.close()
            raise
    if "application/json" in content_type:
        if not deps.allow_registered_audio_reference:
            raise ApiException(
                400,
                "invalid_request",
                "Registered audio references are disabled for this API instance.",
            )
        try:
            payload = await request.json()
        except ValueError as exc:
            raise ApiException(400, "invalid_request", "Invalid JSON request body.") from exc
        return EventSubmission(
            event_id=event_id,
            machine_type=_required_json_text(payload, "machine_type"),
            machine_id=_required_json_text(payload, "machine_id"),
            snr_tag=_required_json_text(payload, "snr_tag"),
            registered_audio_reference=_required_json_text(
                payload,
                "registered_audio_reference",
            ),
        )
    raise ApiException(
        400,
        "invalid_request",
        "Use multipart/form-data upload or enabled application/json registered-reference mode.",
    )


def _required_form_text(form: Any, key: str) -> str:
    value = form.get(key)
    if (
        value is None
        or isinstance(value, StarletteUploadFile)
        or str(value).strip() == ""
    ):
        raise ApiException(400, "invalid_request", f"{key} is required.")
    return str(value).strip()


def _required_json_text(payload: Any, key: str) -> str:
    if not isinstance(payload, dict):
        raise ApiException(400, "invalid_request", "JSON request body must be an object.")
    value = payload.get(key)
    if value is None or str(value).strip() == "":
        raise ApiException(400, "invalid_request", f"{key} is required.")
    return str(value).strip()


def _validate_fan_scope(
    deps: ApiDependencies,
    machine_type: str,
    machine_id: str,
    snr_tag: str,
) -> None:
    normalized_machine_type = str(machine_type).strip().lower().replace(" ", "_")
    if normalized_machine_type != FAN_MACHINE_TYPE:
        raise ApiException(
            422,
            "unsupported_machine",
            "Only fan/id_00 is supported by this Fan Production MVP.",
        )
    if machine_id != FAN_MACHINE_ID:
        raise ApiException(
            422,
            "unsupported_machine_id",
            "Only fan/id_00 is supported by this Fan Production MVP.",
        )
    if snr_tag != FAN_REAL_INTELLIGENCE_SNR:
        raise ApiException(
            422,
            "unsupported_snr",
            "Only fan/id_00/minus6dB has full Real Intelligence artifacts.",
        )
    try:
        deps.artifact_registry.resolve(
            machine_type=machine_type,
            machine_id=machine_id,
            snr_tag=snr_tag,
        ).require_real_intelligence()
    except ArtifactNotRegisteredError as exc:
        raise ApiException(422, "unsupported_machine", str(exc)) from exc


async def _store_audio_submission(
    submission: EventSubmission,
    deps: ApiDependencies,
) -> StoredAudio:
    if submission.uploaded_file is not None:
        return await _store_uploaded_audio(submission, deps)
    if submission.registered_audio_reference is not None:
        return _resolve_registered_audio(submission.registered_audio_reference, deps)
    raise ApiException(400, "invalid_request", "No audio input was provided.")


async def _store_uploaded_audio(
    submission: EventSubmission,
    deps: ApiDependencies,
) -> StoredAudio:
    upload = submission.uploaded_file
    if upload is None:
        raise ApiException(400, "invalid_request", "audio_file is required.")
    
    if deps.audio_storage is None:
        raise ApiException(500, "server_error", "Audio storage is not configured.")
        
    source_name = Path(upload.filename or "audio.wav").name
    content = await upload.read(deps.max_upload_bytes + 1)
    
    try:
        reference = deps.audio_storage.store(submission.event_id, source_name, content)
    except UnsupportedAudioTypeError as exc:
        raise ApiException(415, "unsupported_audio_type", str(exc)) from exc
    except AudioStorageError as exc:
        if "size" in str(exc).lower():
            raise ApiException(413, "audio_too_large", str(exc), details={"max_upload_bytes": deps.max_upload_bytes}) from exc
        raise ApiException(400, "invalid_request", str(exc)) from exc

    return _resolve_stored_audio(reference, deps)


async def _close_submission_upload(submission: EventSubmission) -> None:
    if submission.uploaded_file is not None:
        await submission.uploaded_file.close()


def _resolve_registered_audio(reference: str, deps: ApiDependencies) -> StoredAudio:
    return _resolve_stored_audio(Path(reference), deps)


def _resolve_stored_audio(reference: str | Path, deps: ApiDependencies) -> StoredAudio:
    if deps.audio_storage is None:
        raise ApiException(500, "server_error", "Audio storage is not configured.")
    try:
        metadata = deps.audio_storage.resolve(reference)
    except UnsupportedAudioTypeError as exc:
        raise ApiException(415, "unsupported_audio_type", str(exc)) from exc
    except AudioNotFoundError as exc:
        raise ApiException(404, "audio_not_found", "Audio reference was not readable.") from exc
    except AudioStorageError as exc:
        raise ApiException(400, "invalid_request", str(exc)) from exc
    return StoredAudio(
        internal_reference=str(metadata.processing_path),
        summary=_audio_summary(metadata),
    )


def _require_event(deps: ApiDependencies, event_id: str) -> EventRecord:
    event = deps.event_repository.get_event(event_id)
    if event is None:
        raise ApiException(404, "event_not_found", f"Event not found: {event_id}")
    return event


def _event_summary(
    event: EventRecord,
    audio_summary: AudioSummary | None = None,
) -> EventSummary:
    return EventSummary(
        event_id=event.event_id,
        machine_type=event.machine_type,
        machine_id=event.machine_id,
        snr_tag=event.snr_tag,
        status=event.status,
        created_at=event.created_at,
        updated_at=event.updated_at,
        error=(
            EventError(code=event.error_code, summary=event.error_summary or "")
            if event.error_code
            else None
        ),
        audio=audio_summary,
    )


def _analysis_run_summary(run: AnalysisRunRecord) -> AnalysisRunSummary:
    return AnalysisRunSummary(
        analysis_run_id=run.analysis_run_id,
        pipeline_version=run.pipeline_version,
        status=run.status,
        started_at=run.started_at,
        completed_at=run.completed_at,
        total_duration=run.total_duration,
        artifact_metadata=_safe_artifact_metadata(run.artifact_metadata),
        error=(
            EventError(code=run.error_code, summary=run.error_summary or "")
            if run.error_code
            else None
        ),
    )


def _analysis_result_payload(result: AnalysisResultRecord) -> dict[str, Any]:
    return {
        "expert_a": result.expert_a_result,
        "expert_b": result.expert_b_evidence,
        "structured_context": result.structured_context,
        "retrieval": result.retrieval_metadata,
        "explanation": result.explanation_output,
        "maintenance": result.maintenance_output,
        "timings": result.timing_metadata,
        "limits": {
            "same_machine_same_audio": True,
            "rank_scores_are_probabilities": False,
            "physical_root_cause_confirmed": False,
            "remaining_life_prediction_available": False,
            "production_maintenance_validation_complete": False,
            "multi_machine_generalization_enabled": False,
        },
    }


def _audio_summary_for_event(event: EventRecord, deps: ApiDependencies) -> AudioSummary | None:
    if deps.audio_storage is None:
        return None
    try:
        return _audio_summary(deps.audio_storage.resolve(event.audio_reference))
    except AudioStorageError:
        return None


def _audio_summary(metadata: AudioStorageMetadata) -> AudioSummary:
    return AudioSummary(
        file_name=metadata.file_name,
        suffix=metadata.suffix,
        size_bytes=metadata.size_bytes,
        storage_backend=metadata.storage_backend,
        reference_exposed=False,
    )


def _safe_artifact_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    blocked_keys = {
        "expert_a_model_path",
        "expert_a_norm_stats_path",
        "semantic_index_path",
    }
    return {key: value for key, value in metadata.items() if key not in blocked_keys}


def _readiness(deps: ApiDependencies) -> dict[str, DependencyStatus]:
    rows: dict[str, DependencyStatus] = {}
    try:
        deps.event_repository.list_events(limit=1, offset=0)
        rows["database"] = DependencyStatus(
            status="ok",
            detail="event repository query succeeded",
        )
    except Exception as exc:  # pragma: no cover - defensive readiness boundary
        rows["database"] = DependencyStatus(status="failed", detail=exc.__class__.__name__)
    try:
        artifact = deps.artifact_registry.resolve(
            machine_type=FAN_MACHINE_TYPE,
            machine_id=FAN_MACHINE_ID,
            snr_tag=FAN_REAL_INTELLIGENCE_SNR,
        ).require_real_intelligence()
        deps.artifact_registry.verify_manifest(artifact, check_hashes=False)
        rows["artifact_registry"] = DependencyStatus(
            status="ok",
            detail="fan/id_00/minus6dB Real Intelligence artifacts are registered and verified",
        )
        rows["rag_index"] = DependencyStatus(
            status=(
                "ok"
                if artifact.semantic_index_path and artifact.semantic_index_path.exists()
                else "missing"
            ),
            detail=(
                "semantic RAG index is available"
                if artifact.semantic_index_path and artifact.semantic_index_path.exists()
                else "semantic RAG index is unavailable"
            ),
        )
    except Exception as exc:  # pragma: no cover - defensive readiness boundary
        rows["artifact_registry"] = DependencyStatus(status="failed", detail=exc.__class__.__name__)
        rows["rag_index"] = DependencyStatus(
            status="missing",
            detail="semantic RAG index cannot be checked without registered artifacts",
        )
    try:
        deps.upload_dir.mkdir(parents=True, exist_ok=True)
        probe_path = deps.upload_dir / ".amhi_write_probe"
        probe_path.write_text("ok", encoding="utf-8")
        probe_path.unlink(missing_ok=True)
        rows["audio_storage"] = DependencyStatus(
            status="ok",
            detail="upload storage is writable",
        )
    except Exception as exc:  # pragma: no cover - defensive readiness boundary
        rows["audio_storage"] = DependencyStatus(status="failed", detail=exc.__class__.__name__)
    rows["gemini_config"] = DependencyStatus(
        status="configured" if os.environ.get("GEMINI_API_KEY") else "missing",
        detail=(
            "Gemini provider configuration is present"
            if os.environ.get("GEMINI_API_KEY")
            else "Gemini provider configuration is missing"
        ),
    )
    rows["worker"] = DependencyStatus(
        status="initialized" if deps.worker_initialized else "not_initialized",
        detail=(
            "bounded event processing path is initialized"
            if deps.worker_initialized
            else "bounded event processing path is not initialized"
        ),
    )
    return rows


def _dependencies(request: Request) -> ApiDependencies:
    return request.app.state.dependencies


def _safe_validation_errors(exc: RequestValidationError) -> list[dict[str, Any]]:
    safe_errors = []
    for error in exc.errors():
        safe_errors.append(
            {
                "loc": [str(item) for item in error.get("loc", [])],
                "msg": str(error.get("msg", "validation error")),
                "type": str(error.get("type", "validation_error")),
            },
        )
    return safe_errors


def _model_to_dict(model: Any) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()
