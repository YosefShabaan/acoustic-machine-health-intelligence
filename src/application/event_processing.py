"""Database-backed event processing service for the Fan Production MVP."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from time import perf_counter
from typing import Any, Protocol

from .repositories import (
    EVENT_STATUS_COMPLETED,
    EVENT_STATUS_FAILED,
    AnalysisRepository,
    EventRecord,
    EventRepository,
)


PIPELINE_VERSION = "amhi-real-intelligence-v0.2"
WORKER_KIND = "database_polling_worker_v1"


class PipelineService(Protocol):
    """Minimal pipeline interface used by the worker."""

    def process_event(
        self,
        audio_reference: str,
        machine_type: str,
        machine_id: str,
        snr_tag: str,
        *,
        task_id: str,
    ) -> dict[str, Any]:
        """Process one event and return the structured pipeline payload."""


@dataclass(frozen=True)
class EventProcessingConfig:
    """Bounded worker configuration."""

    pipeline_version: str = PIPELINE_VERSION
    worker_kind: str = WORKER_KIND
    task_id_prefix: str = "task_prod_08_worker"
    max_retries: int = 0


@dataclass(frozen=True)
class EventProcessingResult:
    """Outcome of one worker claim/process attempt."""

    processed: bool
    event_id: str | None
    analysis_run_id: str | None
    final_status: str
    queue_delay_seconds: float | None = None
    processing_duration_seconds: float | None = None
    total_event_duration_seconds: float | None = None
    error_code: str | None = None
    error_summary: str | None = None


@dataclass
class EventProcessingService:
    """Claim queued events and run the injected AMHI pipeline service."""

    event_repository: EventRepository
    analysis_repository: AnalysisRepository
    pipeline_service: PipelineService
    config: EventProcessingConfig = EventProcessingConfig()

    def process_next_event(self) -> EventProcessingResult:
        """Claim and process one queued event, if available."""
        claim_time = datetime.now(UTC)
        claimed = self.event_repository.claim_next_queued()
        if claimed is None:
            return EventProcessingResult(
                processed=False,
                event_id=None,
                analysis_run_id=None,
                final_status="idle",
            )

        run = self.analysis_repository.create_run(
            event_id=claimed.event_id,
            pipeline_version=self.config.pipeline_version,
            artifact_metadata={
                "worker_kind": self.config.worker_kind,
                "max_retries": self.config.max_retries,
            },
        )

        processing_start = perf_counter()
        try:
            payload = self.pipeline_service.process_event(
                audio_reference=claimed.audio_reference,
                machine_type=claimed.machine_type,
                machine_id=claimed.machine_id,
                snr_tag=claimed.snr_tag,
                task_id=f"{self.config.task_id_prefix}_{claimed.event_id}",
            )
            processing_duration = perf_counter() - processing_start
            self.analysis_repository.save_result(
                analysis_run_id=run.analysis_run_id,
                expert_a_result=dict(payload.get("expert_a") or {}),
                expert_b_evidence=_expert_b_payload(payload),
                structured_context=payload.get("structured_context"),
                retrieval_metadata=payload.get("retrieval"),
                explanation_output=payload.get("guarded_explanation"),
                maintenance_output=payload.get("technician_output"),
                timing_metadata=dict(payload.get("timings") or {}),
            )
            self.analysis_repository.complete_run(
                run.analysis_run_id,
                total_duration=processing_duration,
            )
            completed = self.event_repository.update_status(
                claimed.event_id,
                EVENT_STATUS_COMPLETED,
            )
            return EventProcessingResult(
                processed=True,
                event_id=claimed.event_id,
                analysis_run_id=run.analysis_run_id,
                final_status=EVENT_STATUS_COMPLETED,
                queue_delay_seconds=_elapsed_since(claimed.created_at, claim_time),
                processing_duration_seconds=processing_duration,
                total_event_duration_seconds=_elapsed_to_now(completed.created_at),
            )
        except Exception as exc:
            processing_duration = perf_counter() - processing_start
            error_code, error_summary = _safe_error(exc)
            self.analysis_repository.fail_run(
                run.analysis_run_id,
                error_code=error_code,
                error_summary=error_summary,
            )
            failed = self.event_repository.update_status(
                claimed.event_id,
                EVENT_STATUS_FAILED,
                error_code=error_code,
                error_summary=error_summary,
            )
            return EventProcessingResult(
                processed=True,
                event_id=claimed.event_id,
                analysis_run_id=run.analysis_run_id,
                final_status=EVENT_STATUS_FAILED,
                queue_delay_seconds=_elapsed_since(claimed.created_at, claim_time),
                processing_duration_seconds=processing_duration,
                total_event_duration_seconds=_elapsed_to_now(failed.created_at),
                error_code=error_code,
                error_summary=error_summary,
            )

    def process_available(self, *, max_events: int) -> list[EventProcessingResult]:
        """Process up to max_events currently queued events."""
        if max_events < 1:
            raise ValueError("max_events must be at least 1")
        results: list[EventProcessingResult] = []
        for _ in range(max_events):
            result = self.process_next_event()
            if not result.processed:
                break
            results.append(result)
        return results


def _expert_b_payload(payload: dict[str, Any]) -> dict[str, Any] | None:
    if payload.get("expert_b_output") is not None:
        return payload["expert_b_output"]
    if payload.get("expert_b_skipped") is not None:
        return payload["expert_b_skipped"]
    return None


def _safe_error(exc: Exception) -> tuple[str, str]:
    code = f"pipeline_{exc.__class__.__name__.lower()}"
    summary = str(exc).strip() or exc.__class__.__name__
    return code[:80], summary[:300]


def _elapsed_since(iso_timestamp: str, end_time: datetime) -> float | None:
    started = _parse_iso(iso_timestamp)
    if started is None:
        return None
    return max((end_time - started).total_seconds(), 0.0)


def _elapsed_to_now(iso_timestamp: str) -> float | None:
    return _elapsed_since(iso_timestamp, datetime.now(UTC))


def _parse_iso(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)
