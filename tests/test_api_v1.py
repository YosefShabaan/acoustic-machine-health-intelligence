"""Tests for the Fan Production MVP API v1 routes."""

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
from application import EVENT_STATUS_COMPLETED  # noqa: E402
from infrastructure import (  # noqa: E402
    ArtifactRegistry,
    LocalDurableAudioStorage,
    SQLiteAnalysisRepository,
    SQLiteEventRepository,
    connect_sqlite,
)


class ApiV1Tests(unittest.TestCase):
    """FastAPI route behavior with bounded local dependencies."""

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
                audio_storage=LocalDurableAudioStorage(upload_dir=self.tmp_path / "uploads"),
                upload_dir=self.tmp_path / "uploads",
                allow_registered_audio_reference=True,
                max_upload_bytes=1024 * 1024,
            ),
        )
        # Explicit test dependency overrides — no environment-variable bypasses.
        from api.auth import verify_dashboard_session, verify_api_session, verify_csrf_token
        self.app.dependency_overrides[verify_dashboard_session] = lambda: None
        self.app.dependency_overrides[verify_api_session] = lambda: None
        self.app.dependency_overrides[verify_csrf_token] = lambda: None
        # Disable rate limiter for test isolation.
        self.app.state.limiter.enabled = False
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.connection.close()
        self.tmp.cleanup()

    def test_event_submission_upload_returns_accepted_event(self) -> None:
        response = self._post_upload(filename="fan-event.wav")

        self.assertEqual(response.status_code, 202)
        body = response.json()
        event = body["event"]
        self.assertEqual(body["api_version"], "v1")
        self.assertEqual(event["machine_type"], "fan")
        self.assertEqual(event["machine_id"], "id_00")
        self.assertEqual(event["snr_tag"], "minus6dB")
        self.assertEqual(event["status"], "queued")
        self.assertEqual(event["audio"]["file_name"], "fan-event.wav")
        self.assertFalse(event["audio"]["reference_exposed"])
        self.assertIn("/api/v1/events/", body["links"]["self"])
        self.assertNotIn(str(self.tmp_path), response.text)
        self.assertIsNotNone(self.events.get_event(event["event_id"]))

    def test_invalid_machine_is_rejected_without_event_creation(self) -> None:
        response = self._post_upload(machine_type="pump")

        self.assertEqual(response.status_code, 422)
        body = response.json()
        self.assertEqual(body["error"]["code"], "unsupported_machine")
        self.assertEqual(self.events.list_events(), [])

    def test_invalid_audio_type_is_rejected(self) -> None:
        response = self._post_upload(filename="fan-event.txt")

        self.assertEqual(response.status_code, 415)
        self.assertEqual(response.json()["error"]["code"], "unsupported_audio_type")

    def test_event_lookup_list_and_machine_filter(self) -> None:
        created = self._post_upload(filename="first.wav").json()["event"]
        self._post_upload(filename="second.wav")

        lookup = self.client.get(f"/api/v1/events/{created['event_id']}")
        self.assertEqual(lookup.status_code, 200)
        self.assertEqual(lookup.json()["event"]["status"], "queued")
        self.assertIsNone(lookup.json()["analysis_run"])
        self.assertIsNone(lookup.json()["result"])

        event_list = self.client.get("/api/v1/events", params={"status": "queued"})
        self.assertEqual(event_list.status_code, 200)
        self.assertEqual(event_list.json()["pagination"]["count"], 2)

        machine_list = self.client.get("/api/v1/machines/fan/id_00/events")
        self.assertEqual(machine_list.status_code, 200)
        self.assertEqual(machine_list.json()["pagination"]["count"], 2)

    def test_missing_event_returns_safe_error(self) -> None:
        response = self.client.get("/api/v1/events/missing-event")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"]["code"], "event_not_found")

    def test_completed_event_detail_returns_persisted_result(self) -> None:
        audio_path = self.tmp_path / "completed.wav"
        audio_path.write_bytes(b"not-real-audio-but-valid-api-storage-test")
        event = self.events.create_event(
            event_id="event-completed",
            machine_type="fan",
            machine_id="id_00",
            snr_tag="minus6dB",
            audio_reference=str(audio_path),
        )
        self.events.update_status(event.event_id, EVENT_STATUS_COMPLETED)
        run = self.analyses.create_run(
            analysis_run_id="analysis-completed",
            event_id=event.event_id,
            pipeline_version="amhi-real-intelligence-v0.2",
            artifact_metadata={
                "k": 30,
                "distance": "euclidean",
                "rank_threshold": None,
                "rag_retriever_type": "semantic",
            },
        )
        self.analyses.save_result(
            analysis_run_id=run.analysis_run_id,
            expert_a_result={"anomaly_score": 0.622095, "threshold": 0.593284, "is_anomaly": True},
            expert_b_evidence={"k": 30, "distance": "euclidean", "rank_threshold": None},
            structured_context={"schema_version": "0.2.0"},
            retrieval_metadata={"retriever_type": "semantic"},
            explanation_output={"metadata": {"fallback_used": False}},
            maintenance_output={"metadata": {"fallback_used": False}},
            timing_metadata={"total_seconds": 20.0},
        )
        self.analyses.complete_run(run.analysis_run_id, total_duration=20.0)

        response = self.client.get("/api/v1/events/event-completed")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["event"]["status"], "completed")
        self.assertEqual(body["analysis_run"]["artifact_metadata"]["k"], 30)
        self.assertEqual(body["result"]["expert_b"]["distance"], "euclidean")
        self.assertEqual(body["result"]["structured_context"]["schema_version"], "0.2.0")
        self.assertFalse(body["result"]["limits"]["rank_scores_are_probabilities"])
        self.assertNotIn(str(self.tmp_path), response.text)

    def test_registered_reference_json_is_config_gated(self) -> None:
        audio_path = self.tmp_path / "registered.wav"
        audio_path.write_bytes(b"registered-reference")

        response = self.client.post(
            "/api/v1/events",
            json={
                "machine_type": "fan",
                "machine_id": "id_00",
                "snr_tag": "minus6dB",
                "registered_audio_reference": str(audio_path),
            },
        )

        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.json()["event"]["audio"]["file_name"], "registered.wav")
        self.assertNotIn(str(self.tmp_path), response.text)

    def test_health_readiness_and_openapi_are_available(self) -> None:
        health = self.client.get("/api/v1/health")
        ready = self.client.get("/api/v1/ready")
        openapi = self.client.get("/openapi.json")

        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json()["status"], "ok")
        self.assertEqual(ready.status_code, 200)
        self.assertIn("database", ready.json()["dependencies"])
        self.assertIn("worker", ready.json()["dependencies"])
        self.assertEqual(openapi.status_code, 200)
        paths = openapi.json()["paths"]
        self.assertIn("/api/v1/events", paths)
        self.assertIn("/api/v1/health", paths)

    def _post_upload(
        self,
        *,
        filename: str = "event.wav",
        machine_type: str = "fan",
        machine_id: str = "id_00",
        snr_tag: str = "minus6dB",
    ):
        return self.client.post(
            "/api/v1/events",
            data={
                "machine_type": machine_type,
                "machine_id": machine_id,
                "snr_tag": snr_tag,
            },
            files={"audio_file": (filename, b"minimal-wav-bytes", "audio/wav")},
        )


if __name__ == "__main__":
    unittest.main()
