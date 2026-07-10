"""Tests for event-correlated structured logging."""

from __future__ import annotations

import json
import logging
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from api import ApiDependencies, create_app  # noqa: E402
from application import EventProcessingService  # noqa: E402
from infrastructure import (  # noqa: E402
    ArtifactRegistry,
    LocalDurableAudioStorage,
    SQLiteAnalysisRepository,
    SQLiteEventRepository,
    connect_sqlite,
)
from observability import StructuredLogger  # noqa: E402


class StructuredLoggingTests(unittest.TestCase):
    """Structured log format and lifecycle instrumentation tests."""

    def test_secret_fields_are_redacted(self) -> None:
        records, logger = _memory_logger("test.secret")
        structured = StructuredLogger(logger)

        event = structured.emit(
            "event_created",
            event_id="event-secret",
            machine_type="fan",
            machine_id="id_00",
            gemini_api_key="redaction-sentinel-value",
            nested={"token": "nested-redaction-sentinel", "safe": "visible"},
        )

        self.assertEqual(event["gemini_api_key"], "[REDACTED]")
        self.assertEqual(event["nested"]["token"], "[REDACTED]")
        self.assertEqual(event["nested"]["safe"], "visible")
        self.assertNotIn("redaction-sentinel-value", records[0].getMessage())
        self.assertNotIn("nested-redaction-sentinel", records[0].getMessage())
        parsed = json.loads(records[0].getMessage())
        self.assertEqual(parsed["event_id"], "event-secret")

    def test_api_event_creation_logs_correlation(self) -> None:
        records, logger = _memory_logger("test.api")
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            connection = connect_sqlite(":memory:", check_same_thread=False)
            try:
                app = create_app(
                    ApiDependencies(
                        event_repository=SQLiteEventRepository(connection),
                        analysis_repository=SQLiteAnalysisRepository(connection),
                        artifact_registry=ArtifactRegistry(),
                        audio_storage=LocalDurableAudioStorage(upload_dir=tmp_path / "uploads"),
                        structured_logger=StructuredLogger(logger),
                        upload_dir=tmp_path / "uploads",
                    ),
                )
                from api.auth import verify_dashboard_session, verify_api_session, verify_csrf_token
                app.dependency_overrides[verify_dashboard_session] = lambda: None
                app.dependency_overrides[verify_api_session] = lambda: None
                app.dependency_overrides[verify_csrf_token] = lambda: None
                app.state.limiter.enabled = False
                response = TestClient(app).post(
                    "/api/v1/events",
                    data={"machine_type": "fan", "machine_id": "id_00", "snr_tag": "minus6dB"},
                    files={"audio_file": ("logged.wav", b"logged", "audio/wav")},
                )
            finally:
                connection.close()

        self.assertEqual(response.status_code, 202)
        parsed = [json.loads(record.getMessage()) for record in records]
        names = [row["event_name"] for row in parsed]
        self.assertIn("event_created", names)
        self.assertIn("event_queued", names)
        self.assertTrue(all(row["event_id"] == response.json()["event"]["event_id"] for row in parsed))
        self.assertTrue(all(row["machine_type"] == "fan" for row in parsed))
        self.assertNotIn(str(tmp_path), "\n".join(record.getMessage() for record in records))

    def test_worker_success_logs_stage_events_and_durations(self) -> None:
        records, logger = _memory_logger("test.worker.success")
        connection = connect_sqlite(":memory:")
        try:
            events = SQLiteEventRepository(connection)
            analyses = SQLiteAnalysisRepository(connection)
            events.create_event(
                event_id="event-logged",
                machine_type="fan",
                machine_id="id_00",
                snr_tag="minus6dB",
                audio_reference="registered://event-logged.wav",
            )
            service = EventProcessingService(
                events,
                analyses,
                LoggedPipeline(),
                structured_logger=StructuredLogger(logger),
            )

            result = service.process_next_event()
        finally:
            connection.close()

        self.assertEqual(result.final_status, "completed")
        parsed = [json.loads(record.getMessage()) for record in records]
        names = {row["event_name"] for row in parsed}
        self.assertIn("event_processing_started", names)
        self.assertIn("expert_a_completed", names)
        self.assertIn("expert_b_completed", names)
        self.assertIn("retrieval_completed", names)
        self.assertIn("pipeline_completed", names)
        self.assertTrue(all(row["event_id"] == "event-logged" for row in parsed))
        self.assertTrue(all(row["analysis_run_id"] for row in parsed))
        pipeline_log = next(row for row in parsed if row["event_name"] == "pipeline_completed")
        self.assertIsInstance(pipeline_log["duration_ms"], float)

    def test_worker_failure_logs_safe_failure(self) -> None:
        records, logger = _memory_logger("test.worker.failure")
        connection = connect_sqlite(":memory:")
        try:
            events = SQLiteEventRepository(connection)
            analyses = SQLiteAnalysisRepository(connection)
            events.create_event(
                event_id="event-fail-log",
                machine_type="fan",
                machine_id="id_00",
                snr_tag="minus6dB",
                audio_reference="registered://event-fail-log.wav",
            )
            service = EventProcessingService(
                events,
                analyses,
                LoggedPipeline(fail=True),
                structured_logger=StructuredLogger(logger),
            )

            result = service.process_next_event()
        finally:
            connection.close()

        self.assertEqual(result.final_status, "failed")
        parsed = [json.loads(record.getMessage()) for record in records]
        failure = next(row for row in parsed if row["event_name"] == "pipeline_failed")
        self.assertEqual(failure["event_id"], "event-fail-log")
        self.assertEqual(failure["error_code"], "pipeline_runtimeerror")
        self.assertIn("safe failure", failure["error_summary"])


class LoggedPipeline:
    """Small deterministic pipeline used for logging tests."""

    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail

    def process_event(
        self,
        audio_reference: str,
        machine_type: str,
        machine_id: str,
        snr_tag: str,
        *,
        task_id: str,
    ) -> dict[str, object]:
        if self.fail:
            raise RuntimeError("safe failure without secret values")
        return {
            "expert_a": {"is_anomaly": True},
            "expert_b_output": {"k": 30, "distance": "euclidean", "rank_threshold": None},
            "structured_context": {"schema_version": "0.2.0"},
            "retrieval": {"retriever_type": "semantic"},
            "guarded_explanation": {"metadata": {"fallback_used": False}},
            "technician_output": {"metadata": {"fallback_used": True}},
            "timings": {
                "artifact_resolution_seconds": 0.001,
                "expert_a_seconds": 0.002,
                "expert_b_seconds": 0.003,
                "context_seconds": 0.004,
                "retrieval_seconds": 0.005,
                "explanation_seconds": 0.006,
                "maintenance_seconds": 0.007,
                "total_seconds": 0.028,
            },
        }


class ListHandler(logging.Handler):
    """Collect log records in memory."""

    def __init__(self) -> None:
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


def _memory_logger(name: str) -> tuple[list[logging.LogRecord], logging.Logger]:
    logger = logging.getLogger(name)
    logger.handlers.clear()
    logger.propagate = False
    logger.setLevel(logging.INFO)
    handler = ListHandler()
    logger.addHandler(handler)
    return handler.records, logger


if __name__ == "__main__":
    unittest.main()
