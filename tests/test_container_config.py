"""Static and bounded tests for the local container configuration."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from application.worker_runner import ContainerSmokePipelineService  # noqa: E402


class ContainerConfigTests(unittest.TestCase):
    """Container files should preserve artifact and claim boundaries."""

    def test_dockerfile_uses_bounded_copy_and_python_311(self) -> None:
        dockerfile = (REPO_ROOT / "Dockerfile").read_text(encoding="utf-8")

        self.assertIn("FROM python:3.11-slim", dockerfile)
        self.assertIn("COPY src /app/src", dockerfile)
        self.assertIn("COPY data/manuals /app/data/manuals", dockerfile)
        self.assertNotIn("COPY .", dockerfile)
        self.assertNotIn("GEMINI_API_KEY", dockerfile)
        self.assertNotIn("D:\\PDM_Data", dockerfile)

    def test_dockerignore_blocks_large_scientific_artifacts(self) -> None:
        dockerignore = (REPO_ROOT / ".dockerignore").read_text(encoding="utf-8")

        for pattern in ("*.wav", "*.npy", "*.npz", "*.pt", "*.pth", "*.zip"):
            self.assertIn(pattern, dockerignore)
        self.assertIn("**/__pycache__/", dockerignore)
        self.assertIn("**/*.pyc.*", dockerignore)
        self.assertIn("PDM_Data/**", dockerignore)
        self.assertIn("models_store/**", dockerignore)
        self.assertNotIn("data/manuals/**", dockerignore)

    def test_compose_defines_api_worker_and_postgres_without_baked_secrets(self) -> None:
        compose = (REPO_ROOT / "docker-compose.yml").read_text(encoding="utf-8")

        self.assertIn("postgres:", compose)
        self.assertIn("api:", compose)
        self.assertIn("worker:", compose)
        self.assertIn("postgres:16-alpine", compose)
        self.assertIn("DATABASE_URL:", compose)
        self.assertIn("PDM_DATA_ROOT: /mnt/amhi-artifacts", compose)
        self.assertIn("AMHI_EXTERNAL_ARTIFACT_ROOT", compose)
        self.assertIn("AMHI_WORKER_PIPELINE_MODE", compose)
        self.assertEqual(compose.count("build:"), 1)
        self.assertNotIn("D:\\PDM_Data", compose)
        self.assertNotIn("GEMINI_API_KEY: \"", compose)

    def test_container_smoke_pipeline_is_lifecycle_only(self) -> None:
        payload = ContainerSmokePipelineService().process_event(
            audio_reference="/app/runtime/uploads/container-smoke.wav",
            machine_type="fan",
            machine_id="id_00",
            snr_tag="minus6dB",
            task_id="container_smoke_test",
        )

        self.assertEqual(payload["pipeline_status"], "container_smoke_stub_completed")
        self.assertFalse(payload["expert_a"]["is_anomaly"])
        self.assertTrue(payload["expert_b_skipped"]["skipped"])
        self.assertFalse(payload["limits"]["container_smoke_is_scientific_evaluation"])
        forbidden = " ".join(str(value).lower() for value in payload.values())
        self.assertNotIn("root cause confirmed", forbidden)
        self.assertNotIn("rul", forbidden)
        self.assertNotIn("probability", forbidden)


if __name__ == "__main__":
    unittest.main()
