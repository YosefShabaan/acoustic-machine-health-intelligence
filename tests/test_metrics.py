"""Tests for bounded application and pipeline metrics."""

from __future__ import annotations

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
from observability import MetricsRegistry  # noqa: E402


class MetricsTests(unittest.TestCase):
    """Metrics registry and instrumentation tests."""

    def test_registry_renders_prometheus_text(self) -> None:
        registry = MetricsRegistry()
        registry.increment("amhi_events_created_total")
        registry.set_gauge("amhi_events_queued", 2)
        registry.observe_duration("amhi_pipeline_duration_seconds", 1.25)

        output = registry.render_prometheus()

        self.assertIn("# TYPE amhi_events_created_total counter", output)
        self.assertIn("amhi_events_created_total 1", output)
        self.assertIn("# TYPE amhi_events_queued gauge", output)
        self.assertIn("amhi_events_queued 2", output)
        self.assertIn("amhi_pipeline_duration_seconds_count 1", output)
        self.assertIn("amhi_pipeline_duration_seconds_sum 1.25", output)

    def test_api_event_creation_and_queue_depth_metrics(self) -> None:
        registry = MetricsRegistry()
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
                        metrics_registry=registry,
                        upload_dir=tmp_path / "uploads",
                    ),
                )
                client = TestClient(app)
                created = client.post(
                    "/api/v1/events",
                    data={"machine_type": "fan", "machine_id": "id_00", "snr_tag": "minus6dB"},
                    files={"audio_file": ("metric.wav", b"metric", "audio/wav")},
                )
                metrics = client.get("/api/v1/metrics")
            finally:
                connection.close()

        self.assertEqual(created.status_code, 202)
        self.assertEqual(metrics.status_code, 200)
        self.assertIn("amhi_events_created_total 1", metrics.text)
        self.assertIn("amhi_events_queued 1", metrics.text)

    def test_worker_success_metrics_include_durations_and_fallbacks(self) -> None:
        registry = MetricsRegistry()
        connection = connect_sqlite(":memory:")
        try:
            events = SQLiteEventRepository(connection)
            analyses = SQLiteAnalysisRepository(connection)
            events.create_event(
                event_id="event-metrics",
                machine_type="fan",
                machine_id="id_00",
                snr_tag="minus6dB",
                audio_reference="registered://event-metrics.wav",
            )
            service = EventProcessingService(
                events,
                analyses,
                MetricsPipeline(),
                metrics_registry=registry,
            )

            result = service.process_next_event()
        finally:
            connection.close()

        self.assertEqual(result.final_status, "completed")
        output = registry.render_prometheus()
        self.assertIn("amhi_events_completed_total 1", output)
        self.assertIn("amhi_anomalies_flagged_total 1", output)
        self.assertIn("gemini_fallback_total 1", output)
        self.assertIn("maintenance_fallback_total 1", output)
        self.assertIn("citation_validation_failure_total 1", output)
        self.assertIn("amhi_pipeline_duration_seconds_count 1", output)
        self.assertIn("amhi_expert_a_duration_seconds_sum 0.002", output)
        self.assertIn("amhi_expert_b_duration_seconds_sum 0.003", output)
        self.assertIn("amhi_retrieval_duration_seconds_sum 0.005", output)
        self.assertIn("amhi_explanation_duration_seconds_sum 0.006", output)
        self.assertIn("amhi_maintenance_duration_seconds_sum 0.007", output)

    def test_worker_failure_increments_failed_counter(self) -> None:
        registry = MetricsRegistry()
        connection = connect_sqlite(":memory:")
        try:
            events = SQLiteEventRepository(connection)
            analyses = SQLiteAnalysisRepository(connection)
            events.create_event(
                event_id="event-metrics-failed",
                machine_type="fan",
                machine_id="id_00",
                snr_tag="minus6dB",
                audio_reference="registered://event-metrics-failed.wav",
            )
            service = EventProcessingService(
                events,
                analyses,
                MetricsPipeline(fail=True),
                metrics_registry=registry,
            )

            result = service.process_next_event()
        finally:
            connection.close()

        self.assertEqual(result.final_status, "failed")
        self.assertIn("amhi_events_failed_total 1", registry.render_prometheus())


class MetricsPipeline:
    """Deterministic pipeline for metrics tests."""

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
            raise RuntimeError("metrics failure")
        return {
            "expert_a": {"is_anomaly": True},
            "expert_b_output": {"k": 30, "distance": "euclidean", "rank_threshold": None},
            "structured_context": {"schema_version": "0.2.0"},
            "retrieval": {"retriever_type": "semantic"},
            "guarded_explanation": {"metadata": {"fallback_used": True}},
            "technician_output": {
                "metadata": {
                    "fallback_used": True,
                    "citation_validation_failed": True,
                },
            },
            "timings": {
                "expert_a_seconds": 0.002,
                "expert_b_seconds": 0.003,
                "retrieval_seconds": 0.005,
                "explanation_seconds": 0.006,
                "maintenance_seconds": 0.007,
                "total_seconds": 0.023,
            },
        }


if __name__ == "__main__":
    unittest.main()
