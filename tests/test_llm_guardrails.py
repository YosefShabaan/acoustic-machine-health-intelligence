"""Tests for the guardrailed explanation agent."""

from __future__ import annotations

from pathlib import Path
import json
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from agents import (  # noqa: E402
    DiagnosticExplanationAgent,
    ExplanationGuardrailError,
    build_guarded_prompt,
    explain_context,
)


def _context() -> dict:
    """Return a minimal valid Structured Health Context fixture."""
    rank_rows = {
        "sharpness": 0.9333333333333333,
        "roughness": 0.9333333333333333,
        "boominess": 0.0,
        "brightness": 0.9333333333333333,
        "depth": 0.6666666666666666,
    }
    return {
        "schema_version": "0.1.0",
        "event": {
            "event_id": "fan_id_00_minus6dB_00000002",
            "asset_id": "FAN-ID00-001",
            "machine_type": "fan",
            "machine_id": "id_00",
            "snr_tag": "minus6dB",
            "audio_path": r"D:\PDM_Data\MIMII\fan_minus6dB\id_00\abnormal\00000002.wav",
        },
        "expert_a": {
            "expert": "ExpertAAnomalyDetector",
            "anomaly_score": 0.6220951080322266,
            "threshold": 0.5932844281196594,
            "is_anomaly": True,
        },
        "expert_b": {
            "expert": "AcousticTimbreDifferenceExpert",
            "method": {
                "status": "adaptation_not_exact_reproduction",
                "embedding_model": "expert_a_bottleneck_adaptation",
                "timbre_model": "AudioCommons timbral_models",
                "k": 2,
                "distance": "euclidean",
                "rank_threshold": None,
            },
            "references": {
                "pool_size": 2,
                "selected_count": 2,
                "filter": {
                    "machine_type": "fan",
                    "machine_id": "id_00",
                    "snr_tag": "minus6dB",
                },
                "neighbors": [
                    {
                        "path": r"D:\PDM_Data\MIMII\fan_minus6dB\id_00\normal\00000029.wav",
                        "distance": 1.2,
                        "rank": 1,
                    },
                    {
                        "path": r"D:\PDM_Data\MIMII\fan_minus6dB\id_00\normal\00000005.wav",
                        "distance": 2.8,
                        "rank": 2,
                    },
                ],
            },
            "timbre_rank_scores": {
                attribute: {
                    "test_value": 10.0,
                    "rank_score": score,
                    "direction": None,
                    "direction_code": None,
                }
                for attribute, score in rank_rows.items()
            },
            "warnings": [
                "No paper-specific timbre ground-truth labels available; output is qualitative characterization only.",
            ],
        },
        "system_limits": {
            "evidence_only": True,
            "specific_fault_confirmed": False,
            "physical_cause_confirmed": False,
            "remaining_life_prediction_available": False,
            "paper_equivalent_timbre_accuracy_validated": False,
            "timbre_direction_accuracy_validated": False,
            "rank_score_is_confidence": False,
            "llm_or_rag_grounding_available": False,
            "limitations": [
                "Structured context preserves evidence; it is not a diagnosis.",
                "Expert B rank scores are qualitative relative ranks, not probabilities.",
            ],
        },
    }


class BadGenerator:
    """Mock generator that violates guardrails."""

    def generate(self, prompt: str) -> str:
        """Return forbidden wording."""
        return "The bearing is 93% damaged and will fail soon."


class LLMGuardrailTests(unittest.TestCase):
    """Guardrailed explanation tests."""

    def test_prompt_uses_context_without_raw_audio_path(self) -> None:
        """Prompt construction excludes raw audio paths."""
        prompt = build_guarded_prompt(_context())
        self.assertIn("fan_id_00_minus6dB_00000002", prompt)
        self.assertIn("Expert A", prompt)
        self.assertIn("Expert B", prompt)
        self.assertNotIn(".wav", prompt)
        self.assertNotIn("audio_path", prompt)

    def test_deterministic_explanation_has_sections_and_limitations(self) -> None:
        """Offline mode separates evidence, hypotheses, limitations, and notes."""
        result = explain_context(_context())
        self.assertEqual(result["mode"], "deterministic_offline")
        explanation = result["explanation"]
        self.assertTrue(explanation["summary"])
        self.assertGreaterEqual(len(explanation["observations"]), 3)
        self.assertGreaterEqual(len(explanation["limitations"]), 3)
        self.assertGreaterEqual(len(explanation["hypotheses"]), 1)
        self.assertGreaterEqual(len(explanation["inspection_notes"]), 1)
        self.assertIn("qualitative", " ".join(explanation["limitations"]).lower())

    def test_explanation_avoids_rul_diagnosis_and_confidence_claims(self) -> None:
        """Generated output does not contain forbidden claims."""
        result = explain_context(_context())
        text = json.dumps(result["explanation"]).lower()
        self.assertNotIn("rul", text)
        self.assertNotIn("remaining useful life", text)
        self.assertNotIn("time to failure", text)
        self.assertNotIn("root cause", text)
        self.assertNotIn("diagnosis", text)
        self.assertNotIn("confidence", text)
        self.assertNotIn("%", text)
        self.assertNotIn("bearing", text)

    def test_external_generator_output_is_guarded(self) -> None:
        """Bad generator output is rejected before downstream use."""
        agent = DiagnosticExplanationAgent(generator=BadGenerator())
        with self.assertRaises(ExplanationGuardrailError):
            agent.explain(_context())


if __name__ == "__main__":
    unittest.main()
