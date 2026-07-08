"""Tests for grounded maintenance output guardrails."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from agents import (  # noqa: E402
    MaintenanceGroundingError,
    build_retrieval_query,
    generate_grounded_maintenance_output,
    validate_maintenance_output,
)
from rag import RetrievalResponse, RetrievalResult  # noqa: E402


def _context() -> dict:
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
                    {"path": "normal_a.wav", "distance": 1.2, "rank": 1},
                    {"path": "normal_b.wav", "distance": 2.8, "rank": 2},
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


def _retrieval(available: bool = True) -> RetrievalResponse:
    if not available:
        return RetrievalResponse(
            query="fan abnormal noise",
            available=False,
            results=(),
            message="No approved maintenance source was retrieved.",
        )
    return RetrievalResponse(
        query="fan abnormal noise",
        available=True,
        results=(
            RetrievalResult(
                source_id="approved_proc",
                title="Approved Fan Procedure",
                version="2026-07",
                chunk_id="approved_proc#chunk-1",
                snippet="For abnormal fan noise, inspect mounting condition and rotating assembly condition.",
                score=0.8,
                path=Path("procedure.md"),
            ),
        ),
        message="Retrieved 1 approved maintenance source chunk.",
    )


class MaintenanceAgentTests(unittest.TestCase):
    """Grounded maintenance agent behavior."""

    def test_recommendation_requires_source_evidence(self) -> None:
        output = generate_grounded_maintenance_output(
            _context(),
            retrieval=_retrieval(available=False),
        )
        self.assertEqual(output["mode"], "safe_unavailable")
        self.assertFalse(output["recommendation"]["available"])
        self.assertEqual(output["recommendation"]["citations"], [])
        self.assertEqual(output["retrieved_maintenance_guidance"], [])

    def test_grounded_output_includes_sources_and_citations(self) -> None:
        output = generate_grounded_maintenance_output(_context(), retrieval=_retrieval())
        self.assertEqual(output["mode"], "source_grounded")
        self.assertTrue(output["recommendation"]["available"])
        self.assertEqual(output["recommendation"]["citations"], ["approved_proc"])
        self.assertEqual(
            output["retrieved_maintenance_guidance"][0]["source_id"],
            "approved_proc",
        )

    def test_missing_citation_is_rejected(self) -> None:
        output = generate_grounded_maintenance_output(_context(), retrieval=_retrieval())
        output["recommendation"]["citations"] = ["missing_source"]
        with self.assertRaises(MaintenanceGroundingError):
            validate_maintenance_output(output)

    def test_output_avoids_rul_root_cause_and_confidence_claims(self) -> None:
        output = generate_grounded_maintenance_output(_context(), retrieval=_retrieval())
        text = json.dumps(
            {
                "recommendation": output["recommendation"],
                "limitations": output["limitations"],
                "observed_ml_evidence": output["observed_ml_evidence"],
            }
        ).lower()
        self.assertNotIn("rul", text)
        self.assertNotIn("remaining useful life", text)
        self.assertNotIn("time to failure", text)
        self.assertNotIn("root cause", text)
        self.assertNotIn("confidence", text)
        self.assertNotIn("%", text)
        self.assertNotIn("bearing", text)

    def test_retrieval_query_uses_context_attributes(self) -> None:
        query = build_retrieval_query(_context())
        self.assertIn("fan", query)
        self.assertIn("sharpness", query)
        self.assertIn("roughness", query)


if __name__ == "__main__":
    unittest.main()
