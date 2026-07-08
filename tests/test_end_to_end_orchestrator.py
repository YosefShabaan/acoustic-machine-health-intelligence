"""Tests for end-to-end Fan MVP orchestration guardrails."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
SCRIPTS_DIR = REPO_ROOT / "scripts"
for path in (SRC_DIR, SCRIPTS_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from run_end_to_end_demo import (  # noqa: E402
    should_run_expert_b,
    validate_end_to_end_output,
)


def _output() -> dict:
    event_id = "fan_id_00_minus6dB_00000002"
    audio_path = r"D:\PDM_Data\MIMII\fan_minus6dB\id_00\abnormal\00000002.wav"
    return {
        "expert_b_output": {
            "input_audio": {"path": audio_path},
        },
        "structured_context": {
            "event": {"event_id": event_id, "audio_path": audio_path},
            "expert_a": {"is_anomaly": True},
        },
        "technician_output": {
            "event": {"event_id": event_id},
            "observed_ml_evidence": {
                "expert_a": {
                    "anomaly_score": 0.62,
                    "threshold": 0.59,
                    "is_anomaly": True,
                }
            },
            "retrieved_maintenance_guidance": [
                {"source_id": "approved_proc", "snippet": "Inspect mounting condition."}
            ],
            "recommendation": {
                "available": True,
                "text": "Use retrieved approved guidance as inspection context only.",
                "citations": ["approved_proc"],
            },
            "limitations": [
                "Acoustic evidence is not a component-level finding.",
                "No lifetime estimate is available.",
            ],
        },
    }


class EndToEndOrchestratorTests(unittest.TestCase):
    """End-to-end output validation."""

    def test_event_identity_is_preserved(self) -> None:
        validate_end_to_end_output(_output())

    def test_expert_b_is_conditional_on_expert_a_anomaly(self) -> None:
        self.assertTrue(should_run_expert_b({"is_anomaly": True}))
        self.assertFalse(should_run_expert_b({"is_anomaly": False}))
        output = _output()
        output["structured_context"]["expert_a"]["is_anomaly"] = False
        with self.assertRaises(ValueError):
            validate_end_to_end_output(output)

    def test_missing_source_citation_is_rejected(self) -> None:
        output = _output()
        output["technician_output"]["recommendation"]["citations"] = ["missing_source"]
        with self.assertRaises(ValueError):
            validate_end_to_end_output(output)

    def test_forbidden_claims_are_rejected(self) -> None:
        output = _output()
        output["technician_output"]["recommendation"]["text"] = (
            "This has 93% confidence and will fail."
        )
        with self.assertRaises(ValueError):
            validate_end_to_end_output(output)


if __name__ == "__main__":
    unittest.main()
