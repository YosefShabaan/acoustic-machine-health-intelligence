"""Container entrypoint for the bounded Fan event worker."""

from __future__ import annotations

import json
import os
from pathlib import Path
from time import sleep
from typing import Any

from infrastructure import (
    LocalAudioStorage,
    SQLiteAnalysisRepository,
    SQLiteEventRepository,
    connect_sqlite,
)

from .event_processing import EventProcessingConfig, EventProcessingService
from .pipeline_service import AMHIPipelineService


DEFAULT_SQLITE_PATH = "/app/runtime/amhi.sqlite"
DEFAULT_UPLOAD_DIR = "/app/runtime/uploads"


def main() -> int:
    """Run the database-backed worker loop."""
    database_url = os.environ.get("DATABASE_URL", "")
    upload_dir = Path(os.environ.get("AMHI_UPLOAD_DIR", DEFAULT_UPLOAD_DIR))
    upload_dir.mkdir(parents=True, exist_ok=True)

    if database_url:
        from infrastructure import (
            PostgresEventRepository,
            PostgresAnalysisRepository,
            connect_postgres,
        )
        connection = connect_postgres(database_url)
        event_repository = PostgresEventRepository(connection)
        analysis_repository = PostgresAnalysisRepository(connection)
        _close = connection.close
    else:
        sqlite_path = Path(os.environ.get("AMHI_SQLITE_PATH", DEFAULT_SQLITE_PATH))
        sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        connection = connect_sqlite(sqlite_path, check_same_thread=False)
        event_repository = SQLiteEventRepository(connection)
        analysis_repository = SQLiteAnalysisRepository(connection)
        _close = connection.close

    service = EventProcessingService(
        event_repository=event_repository,
        analysis_repository=analysis_repository,
        pipeline_service=_pipeline_service_from_env(),
        config=EventProcessingConfig(
            task_id_prefix=os.environ.get(
                "AMHI_WORKER_TASK_ID_PREFIX",
                "container_worker",
            ),
        ),
    )
    max_events = _positive_int("AMHI_WORKER_MAX_EVENTS_PER_TICK", 1)
    idle_sleep = _non_negative_float("AMHI_WORKER_IDLE_SLEEP_SECONDS", 2.0)
    run_once = os.environ.get("AMHI_WORKER_RUN_ONCE", "0") == "1"

    try:
        while True:
            results = service.process_available(max_events=max_events)
            for result in results:
                print(
                    json.dumps(
                        {
                            "worker_event": "processed",
                            "event_id": result.event_id,
                            "analysis_run_id": result.analysis_run_id,
                            "final_status": result.final_status,
                            "error_code": result.error_code,
                        },
                        sort_keys=True,
                    ),
                    flush=True,
                )
            if run_once:
                return 0
            if not results:
                sleep(idle_sleep)
    finally:
        _close()


def _pipeline_service_from_env():
    mode = os.environ.get("AMHI_WORKER_PIPELINE_MODE", "real").strip().lower()
    if mode == "real":
        return AMHIPipelineService(audio_storage=LocalAudioStorage())
    if mode == "stub":
        return ContainerSmokePipelineService()
    raise ValueError(f"Unsupported AMHI_WORKER_PIPELINE_MODE: {mode}")


class ContainerSmokePipelineService:
    """Lifecycle-only pipeline used by the container smoke test.

    This mode proves API -> persistence -> worker -> result lifecycle wiring.
    It intentionally does not score audio, characterize timbre, retrieve RAG,
    call Gemini, or enable any scientific claim.
    """

    def process_event(
        self,
        audio_reference: str,
        machine_type: str,
        machine_id: str,
        snr_tag: str,
        *,
        task_id: str,
    ) -> dict[str, Any]:
        return {
            "task": task_id,
            "pipeline_status": "container_smoke_stub_completed",
            "machine_scope": {
                "machine_type": machine_type,
                "machine_id": machine_id,
                "snr_tag": snr_tag,
            },
            "audio_storage": {
                "storage_backend": "container_smoke_stub",
                "reference_received": bool(audio_reference),
            },
            "expert_a": {
                "anomaly_score": 0.0,
                "threshold": 1.0,
                "is_anomaly": False,
                "mode": "container_smoke_stub",
            },
            "expert_b_skipped": {
                "skipped": True,
                "reason": "container_smoke_stub_no_scientific_processing",
            },
            "expert_b_output": None,
            "structured_context": None,
            "retrieval": {
                "retriever_type": "container_smoke_stub",
                "results": [],
            },
            "guarded_explanation": {
                "metadata": {
                    "mode": "container_smoke_stub",
                    "fallback_used": True,
                },
            },
            "technician_output": {
                "metadata": {
                    "mode": "container_smoke_stub",
                    "fallback_used": True,
                    "citation_validation_failed": False,
                },
                "actions": [],
            },
            "limits": {
                "same_machine_same_audio": True,
                "rank_scores_are_probabilities": False,
                "physical_root_cause_confirmed": False,
                "remaining_life_prediction_available": False,
                "production_maintenance_validation_complete": False,
                "multi_machine_generalization_enabled": False,
                "container_smoke_is_scientific_evaluation": False,
            },
            "timings": {
                "artifact_resolution_seconds": 0.0,
                "expert_a_seconds": 0.0,
                "expert_b_seconds": 0.0,
                "retrieval_seconds": 0.0,
                "explanation_seconds": 0.0,
                "maintenance_seconds": 0.0,
                "total_seconds": 0.0,
            },
        }


def _positive_int(name: str, default: int) -> int:
    value = int(os.environ.get(name, str(default)))
    if value < 1:
        raise ValueError(f"{name} must be at least 1")
    return value


def _non_negative_float(name: str, default: float) -> float:
    value = float(os.environ.get(name, str(default)))
    if value < 0:
        raise ValueError(f"{name} must be non-negative")
    return value


if __name__ == "__main__":
    raise SystemExit(main())
