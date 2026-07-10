"""Health and readiness behavior for the Fan Production MVP API."""

from __future__ import annotations

from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from api import ApiDependencies, create_app  # noqa: E402
from infrastructure import (  # noqa: E402
    LocalDurableAudioStorage,
    SQLiteAnalysisRepository,
    SQLiteEventRepository,
    connect_sqlite,
)
from infrastructure.artifact_registry import (  # noqa: E402
    ArtifactNotRegisteredError,
    FAN_MACHINE_ID,
    FAN_MACHINE_TYPE,
    FAN_RAG_CORPUS_VERSION,
    FAN_REAL_INTELLIGENCE_SNR,
    FAN_SELECTED_RETRIEVER,
    ResolvedArtifactConfig,
)


class HealthReadinessTests(unittest.TestCase):
    """Readiness dependency checks without live provider or audio processing."""

    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        self.tmp_path = Path(self.tmp.name)
        self.connection = connect_sqlite(":memory:", check_same_thread=False)
        self.events = SQLiteEventRepository(self.connection)
        self.analyses = SQLiteAnalysisRepository(self.connection)
        self.semantic_index_path = self.tmp_path / "semantic_index.json"
        self.semantic_index_path.write_text("{}", encoding="utf-8")

    def tearDown(self) -> None:
        self.connection.close()
        self.tmp.cleanup()

    def test_health_is_alive_without_dependency_checks(self) -> None:
        client = self._client(
            event_repository=_UnavailableEventRepository(),
            artifact_registry=_MissingArtifactRegistry(),
            worker_initialized=False,
        )

        response = client.get("/api/v1/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")
        self.assertEqual(response.json()["service"], "amhi-fan-production-mvp")

    def test_readiness_ready_when_required_dependencies_are_available(self) -> None:
        client = self._client()

        with patch.dict("os.environ", {"GEMINI_API_KEY": "configured-for-test"}):
            response = client.get("/api/v1/ready")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["ready"])
        self.assertEqual(body["status"], "ready")
        self.assertEqual(body["dependencies"]["database"]["status"], "ok")
        self.assertEqual(body["dependencies"]["artifact_registry"]["status"], "ok")
        self.assertEqual(body["dependencies"]["audio_storage"]["status"], "ok")
        self.assertEqual(body["dependencies"]["rag_index"]["status"], "ok")
        self.assertEqual(body["dependencies"]["gemini_config"]["status"], "configured")
        self.assertEqual(body["dependencies"]["worker"]["status"], "initialized")
        self.assertNotIn("configured-for-test", response.text)

    def test_readiness_reports_database_unavailable(self) -> None:
        client = self._client(event_repository=_UnavailableEventRepository())

        with patch.dict("os.environ", {"GEMINI_API_KEY": "configured-for-test"}):
            response = client.get("/api/v1/ready")

        body = response.json()
        self.assertFalse(body["ready"])
        self.assertEqual(body["status"], "not_ready")
        self.assertEqual(body["dependencies"]["database"]["status"], "failed")
        self.assertEqual(body["dependencies"]["database"]["detail"], "RuntimeError")

    def test_readiness_reports_artifact_missing(self) -> None:
        client = self._client(artifact_registry=_MissingArtifactRegistry())

        with patch.dict("os.environ", {"GEMINI_API_KEY": "configured-for-test"}):
            response = client.get("/api/v1/ready")

        body = response.json()
        self.assertFalse(body["ready"])
        self.assertEqual(body["dependencies"]["artifact_registry"]["status"], "failed")
        self.assertEqual(
            body["dependencies"]["artifact_registry"]["detail"],
            "ArtifactNotRegisteredError",
        )
        self.assertEqual(body["dependencies"]["rag_index"]["status"], "missing")

    def test_readiness_reports_missing_gemini_config_without_live_call(self) -> None:
        client = self._client()

        with patch.dict("os.environ", {}, clear=True):
            response = client.get("/api/v1/ready")

        body = response.json()
        self.assertFalse(body["ready"])
        self.assertEqual(body["dependencies"]["gemini_config"]["status"], "missing")
        self.assertNotIn("api_key", response.text.lower())

    def test_readiness_reports_rag_index_unavailable(self) -> None:
        missing_index_path = self.tmp_path / "missing_semantic_index.json"
        client = self._client(
            artifact_registry=_ReadyArtifactRegistry(missing_index_path),
        )

        with patch.dict("os.environ", {"GEMINI_API_KEY": "configured-for-test"}):
            response = client.get("/api/v1/ready")

        body = response.json()
        self.assertFalse(body["ready"])
        self.assertEqual(body["dependencies"]["artifact_registry"]["status"], "ok")
        self.assertEqual(body["dependencies"]["rag_index"]["status"], "missing")
        self.assertNotIn(str(missing_index_path), response.text)

    def test_readiness_reports_worker_not_initialized(self) -> None:
        client = self._client(worker_initialized=False)

        with patch.dict("os.environ", {"GEMINI_API_KEY": "configured-for-test"}):
            response = client.get("/api/v1/ready")

        body = response.json()
        self.assertFalse(body["ready"])
        self.assertEqual(body["dependencies"]["worker"]["status"], "not_initialized")

    def _client(
        self,
        *,
        event_repository=None,
        artifact_registry=None,
        worker_initialized: bool = True,
    ) -> TestClient:
        return TestClient(
            create_app(
                ApiDependencies(
                    event_repository=event_repository or self.events,
                    analysis_repository=self.analyses,
                    artifact_registry=artifact_registry
                    or _ReadyArtifactRegistry(self.semantic_index_path),
                    audio_storage=LocalDurableAudioStorage(upload_dir=self.tmp_path / "uploads"),
                    upload_dir=self.tmp_path / "uploads",
                    worker_initialized=worker_initialized,
                ),
            ),
        )


class _ReadyArtifactRegistry:
    def __init__(self, semantic_index_path: Path) -> None:
        self.semantic_index_path = semantic_index_path

    def resolve(
        self,
        *,
        machine_type: str,
        machine_id: str,
        snr_tag: str,
    ) -> ResolvedArtifactConfig:
        if (
            machine_type != FAN_MACHINE_TYPE
            or machine_id != FAN_MACHINE_ID
            or snr_tag != FAN_REAL_INTELLIGENCE_SNR
        ):
            raise ArtifactNotRegisteredError("Only fan/id_00/minus6dB is registered")
        return ResolvedArtifactConfig(
            machine_type=FAN_MACHINE_TYPE,
            machine_id=FAN_MACHINE_ID,
            snr_tag=FAN_REAL_INTELLIGENCE_SNR,
            expert_a_model_path=Path("anomaly_detector_fan_minus6dB.pt"),
            expert_a_norm_stats_path=Path("fan_minus6dB_norm_stats.npz"),
            expert_a_available=True,
            expert_b_reference_index_path=Path(
                "timbre_reference_index_fan_id_00_minus6dB.json",
            ),
            expert_b_available=True,
            embedding_model="expert_a_bottleneck_adaptation",
            embedding_status="project_mvp_adaptation_not_paper_encoder",
            timbre_model="AudioCommons timbral_models",
            k=30,
            distance="euclidean",
            rank_threshold=None,
            rag_corpus_version=FAN_RAG_CORPUS_VERSION,
            rag_retriever_type=FAN_SELECTED_RETRIEVER,
            semantic_index_path=self.semantic_index_path,
            real_intelligence_available=True,
        )

    def verify_manifest(self, config: ResolvedArtifactConfig, check_hashes: bool = False) -> None:
        pass


class _MissingArtifactRegistry:
    def resolve(self, *, machine_type: str, machine_id: str, snr_tag: str):
        raise ArtifactNotRegisteredError("missing test artifact")


class _UnavailableEventRepository:
    def list_events(self, *, limit: int = 100, offset: int = 0, status: str | None = None):
        raise RuntimeError("database unavailable")


if __name__ == "__main__":
    unittest.main()
