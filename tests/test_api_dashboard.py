"""Tests for the API-backed technician dashboard routes."""

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
from application import (  # noqa: E402
    EVENT_STATUS_COMPLETED,
    EVENT_STATUS_FAILED,
    EVENT_STATUS_PROCESSING,
)
from infrastructure import (  # noqa: E402
    ArtifactRegistry,
    LocalAudioStorage,
    SQLiteAnalysisRepository,
    SQLiteEventRepository,
    connect_sqlite,
)


class ApiDashboardTests(unittest.TestCase):
    """Dashboard routes render persisted event state without recomputation."""

    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        self.tmp_path = Path(self.tmp.name)
        self.connection = connect_sqlite(":memory:", check_same_thread=False)
        self.events = SQLiteEventRepository(self.connection)
        self.analyses = SQLiteAnalysisRepository(self.connection)
        self.app = create_app(
            ApiDependencies(
                event_repository=self.events,
                analysis_repository=self.analyses,
                artifact_registry=ArtifactRegistry(),
                audio_storage=LocalAudioStorage(),
                upload_dir=self.tmp_path / "uploads",
                allow_registered_audio_reference=True,
            ),
        )
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.connection.close()
        self.tmp.cleanup()

    def test_dashboard_event_list_shows_lifecycle_statuses(self) -> None:
        self._create_event("event-queued")
        self.events.update_status(
            self._create_event("event-processing").event_id,
            EVENT_STATUS_PROCESSING,
        )
        self.events.update_status(
            self._create_event("event-failed").event_id,
            EVENT_STATUS_FAILED,
            error_code="pipeline_runtimeerror",
            error_summary="Pipeline failed safely.",
        )

        response = self.client.get("/dashboard")

        self.assertEqual(response.status_code, 200)
        html = response.text
        self.assertIn("Event List", html)
        self.assertIn("event-queued", html)
        self.assertIn("queued", html)
        self.assertIn("processing", html)
        self.assertIn("failed", html)
        self.assertNotIn(str(self.tmp_path), html)

    def test_completed_event_detail_shows_evidence_fallbacks_and_citations(self) -> None:
        event = self._create_event("event-completed", audio_name="completed.wav")
        self.events.update_status(event.event_id, EVENT_STATUS_COMPLETED)
        run = self.analyses.create_run(
            analysis_run_id="analysis-dashboard",
            event_id=event.event_id,
            pipeline_version="amhi-real-intelligence-v0.2",
            artifact_metadata={
                "k": 30,
                "distance": "euclidean",
                "rank_threshold": None,
                "rag_retriever_type": "semantic",
                "rag_corpus_version": "AMHI-FAN-MAINT-KB-v1",
            },
        )
        self.analyses.save_result(
            analysis_run_id=run.analysis_run_id,
            expert_a_result={"anomaly_score": 0.622095, "threshold": 0.593284, "is_anomaly": True},
            expert_b_evidence={"k": 30, "distance": "euclidean", "rank_threshold": None},
            structured_context={"schema_version": "0.2.0"},
            retrieval_metadata={
                "retriever_type": "semantic",
                "corpus_version": "AMHI-FAN-MAINT-KB-v1",
                "query": "fan anomaly acoustic maintenance inspection",
                "sources": [
                    {"title": "Fan guide", "source_id": "source-1", "chunk_id": "chunk-1"},
                ],
            },
            explanation_output={
                "summary": "Bounded explanation",
                "metadata": {"fallback_used": True},
            },
            maintenance_output={
                "recommendation": {
                    "text": "Inspect fan assembly.",
                    "recommended_next_actions": [
                        {"action": "Inspect housing", "source_id": "source-1", "chunk_id": "chunk-1"},
                    ],
                },
                "metadata": {"fallback_used": True},
            },
            timing_metadata={"total_seconds": 20.0},
        )
        self.analyses.complete_run(run.analysis_run_id, total_duration=20.0)

        response = self.client.get("/dashboard/events/event-completed")

        self.assertEqual(response.status_code, 200)
        html = response.text
        self.assertIn("Expert A", html)
        self.assertIn("0.622095", html)
        self.assertIn("Expert B", html)
        self.assertIn("euclidean", html)
        self.assertIn("0.2.0", html)
        self.assertIn("semantic", html)
        self.assertIn("Fallback used", html)
        self.assertIn("source-1", html)
        self.assertIn("chunk-1", html)
        self.assertIn("No RUL", html)
        self.assertNotIn(str(self.tmp_path), html)

    def test_failed_event_detail_shows_safe_error(self) -> None:
        event = self._create_event("event-safe-failed")
        self.events.update_status(
            event.event_id,
            EVENT_STATUS_FAILED,
            error_code="pipeline_runtimeerror",
            error_summary="Pipeline failed safely.",
        )

        response = self.client.get("/dashboard/events/event-safe-failed")

        self.assertEqual(response.status_code, 200)
        self.assertIn("pipeline_runtimeerror", response.text)
        self.assertIn("Pipeline failed safely.", response.text)

    def test_queued_event_detail_does_not_require_result(self) -> None:
        self._create_event("event-queued-detail")

        response = self.client.get("/dashboard/events/event-queued-detail")

        self.assertEqual(response.status_code, 200)
        self.assertIn("No worker has claimed this event.", response.text)
        self.assertIn("No analysis result available yet.", response.text)

    def test_missing_event_returns_dashboard_404(self) -> None:
        response = self.client.get("/dashboard/events/missing")

        self.assertEqual(response.status_code, 404)
        self.assertIn("Event not found", response.text)

    def _create_event(self, event_id: str, *, audio_name: str | None = None):
        audio_path = self.tmp_path / (audio_name or f"{event_id}.wav")
        audio_path.write_bytes(b"dashboard-audio-reference")
        return self.events.create_event(
            event_id=event_id,
            machine_type="fan",
            machine_id="id_00",
            snr_tag="minus6dB",
            audio_reference=str(audio_path),
        )


if __name__ == "__main__":
    unittest.main()
