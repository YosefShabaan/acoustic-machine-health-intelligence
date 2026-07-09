"""Tests for Structured Health Context schema and translation."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from context import CONTEXT_SCHEMA_VERSION, context_from_expert_b_output  # noqa: E402
from context import LEGACY_CONTEXT_SCHEMA_VERSION, migrate_context_v01_to_v02  # noqa: E402
from context.schemas import ContextValidationError, validate_structured_context  # noqa: E402


def _expert_b_output() -> dict:
    """Return a minimal valid Expert B output fixture."""
    return {
        "expert": "AcousticTimbreDifferenceExpert",
        "method": {
            "paper": "Nishida et al. 2024, arXiv:2410.22033",
            "status": "adaptation_not_exact_reproduction",
            "embedding_model": "expert_a_bottleneck_adaptation",
            "embedding_status": "project_mvp_adaptation_not_paper_encoder",
            "embedding_metadata": {
                "embedding_model": "expert_a_bottleneck_adaptation",
                "embedding_dim": 128,
            },
            "timbre_model": "AudioCommons timbral_models",
            "k": 3,
            "distance": "euclidean",
            "rank_threshold": None,
        },
        "input_audio": {
            "path": r"D:\PDM_Data\MIMII\fan_minus6dB\id_00\abnormal\00000002.wav",
            "machine_type": "fan",
            "machine_id": "id_00",
            "snr_tag": "minus6dB",
        },
        "expert_a": {
            "anomaly_score": 0.6220951080322266,
            "threshold": 0.5932844281196594,
            "is_anomaly": True,
        },
        "references": {
            "pool_size": 3,
            "selected_count": 3,
            "filter": {
                "machine_type": "fan",
                "machine_id": "id_00",
                "snr_tag": "minus6dB",
            },
            "neighbors": [
                {
                    "path": rf"D:\PDM_Data\MIMII\fan_minus6dB\id_00\normal\0000000{idx}.wav",
                    "distance": float(idx + 1),
                    "rank": idx + 1,
                }
                for idx in range(3)
            ],
        },
        "timbre_differences": {
            "sharpness": {
                "test_value": 53.9,
                "rank_score": 0.9333333333333333,
                "direction": None,
                "direction_code": None,
            },
            "roughness": {
                "test_value": 67.8,
                "rank_score": 0.9333333333333333,
                "direction": None,
                "direction_code": None,
            },
            "boominess": {
                "test_value": 26.0,
                "rank_score": 0.0,
                "direction": None,
                "direction_code": None,
            },
            "brightness": {
                "test_value": 68.5,
                "rank_score": 0.9333333333333333,
                "direction": None,
                "direction_code": None,
            },
            "depth": {
                "test_value": 64.7,
                "rank_score": 0.6666666666666666,
                "direction": None,
                "direction_code": None,
            },
        },
        "warnings": [
            "No paper-specific timbre ground-truth labels available; output is qualitative characterization only.",
            "Expert A bottleneck embedding is a project MVP adaptation, not a Nishida paper encoder.",
        ],
    }


class ContextSchemaTests(unittest.TestCase):
    """Structured context guardrail tests."""

    def test_translator_builds_required_versioned_context(self) -> None:
        """Translator emits the required top-level schema fields."""
        context = context_from_expert_b_output(
            _expert_b_output(),
            created_at="2026-07-09T00:00:00+00:00",
        )
        self.assertEqual(context["schema_version"], CONTEXT_SCHEMA_VERSION)
        self.assertEqual(set(context), {
            "schema_version",
            "event",
            "expert_a",
            "expert_b",
            "system_limits",
            "analysis",
        })
        validate_structured_context(context)

    def test_same_event_identity_and_machine_metadata_are_preserved(self) -> None:
        """The context keeps the Expert B input audio and machine scope."""
        source = _expert_b_output()
        context = context_from_expert_b_output(
            source,
            asset_id="FAN-ID00-001",
            created_at="2026-07-09T00:00:00+00:00",
        )
        self.assertEqual(context["event"]["audio_path"], source["input_audio"]["path"])
        self.assertEqual(context["event"]["machine_type"], "fan")
        self.assertEqual(context["event"]["machine_id"], "id_00")
        self.assertEqual(context["event"]["snr_tag"], "minus6dB")
        self.assertEqual(context["event"]["asset_id"], "FAN-ID00-001")
        self.assertEqual(context["event"]["event_id"], "fan_id_00_minus6dB_00000002")

    def test_expert_outputs_and_limits_are_preserved(self) -> None:
        """Expert A/B evidence and mandatory limits are explicit."""
        context = context_from_expert_b_output(
            _expert_b_output(),
            created_at="2026-07-09T00:00:00+00:00",
        )
        self.assertTrue(context["expert_a"]["is_anomaly"])
        self.assertEqual(context["expert_b"]["method"]["rank_threshold"], None)
        self.assertEqual(context["expert_b"]["references"]["selected_count"], 3)
        self.assertEqual(context["expert_b"]["timbre_rank_scores"]["boominess"]["rank_score"], 0.0)
        limits = context["system_limits"]
        self.assertTrue(limits["evidence_only"])
        self.assertFalse(limits["specific_fault_confirmed"])
        self.assertFalse(limits["physical_cause_confirmed"])
        self.assertFalse(limits["remaining_life_prediction_available"])
        self.assertFalse(limits["paper_equivalent_timbre_accuracy_validated"])
        self.assertFalse(limits["timbre_direction_accuracy_validated"])
        self.assertFalse(limits["rank_score_is_confidence"])

    def test_traceability_metadata_uses_available_artifact_identifiers(self) -> None:
        """v0.2 records model, reference, retriever, LLM, and maintenance provenance."""
        context = context_from_expert_b_output(
            _expert_b_output(),
            created_at="2026-07-09T00:00:00+00:00",
            reference_index_path=r"D:\PDM_Data\MIMII\processed\timbre_reference_index_fan_id_00_minus6dB.json",
            llm_metadata={
                "provider": "gemini",
                "model": "gemini-test",
                "prompt_version": "diagnostic-test",
                "generation_mode": "live_gemini",
                "fallback_used": False,
            },
            rag_metadata={
                "retriever_type": "semantic",
                "corpus_version": "AMHI-FAN-MAINT-KB-v1",
                "retrieval_query": "fan abnormal acoustic noise",
            },
            maintenance_metadata={
                "provider": "gemini",
                "model": "gemini-test",
                "prompt_version": "maintenance-test",
                "generation_mode": "live_gemini",
                "fallback_used": False,
            },
        )

        analysis = context["analysis"]
        self.assertEqual(analysis["analysis_run_id"], "analysis_fan_id_00_minus6dB_00000002_0.2.0")
        self.assertEqual(analysis["pipeline_version"], "amhi-real-intelligence-v0.2")
        self.assertEqual(analysis["expert_a"]["model_id"], "anomaly_detector_minus6dB.pt")
        self.assertEqual(analysis["expert_a"]["model_version"], "unversioned")
        self.assertEqual(analysis["expert_a"]["normalization_artifact_id"], "ad_norm_stats_minus6dB.npz")
        self.assertEqual(
            analysis["expert_b"]["reference_index_id"],
            "timbre_reference_index_fan_id_00_minus6dB.json",
        )
        self.assertEqual(analysis["expert_b"]["embedding_model"], "expert_a_bottleneck_adaptation")
        self.assertEqual(analysis["expert_b"]["k"], 3)
        self.assertEqual(analysis["expert_b"]["distance"], "euclidean")
        self.assertEqual(analysis["llm"]["provider"], "gemini")
        self.assertEqual(analysis["rag"]["retriever_type"], "semantic")
        self.assertEqual(analysis["maintenance"]["prompt_version"], "maintenance-test")

    def test_forbidden_claim_keys_are_rejected(self) -> None:
        """Context validation rejects unsupported claim fields."""
        context = context_from_expert_b_output(
            _expert_b_output(),
            created_at="2026-07-09T00:00:00+00:00",
        )
        for forbidden_key in (
            "confidence_pct",
            "diagnosis",
            "root_cause",
            "rul_prediction",
            "pronostia",
        ):
            mutated = deepcopy(context)
            mutated["expert_b"][forbidden_key] = "unsupported"
            with self.assertRaises(ContextValidationError):
                validate_structured_context(mutated)

    def test_null_rank_threshold_requires_null_directions(self) -> None:
        """Direction fields stay null when no rank threshold is configured."""
        context = context_from_expert_b_output(
            _expert_b_output(),
            created_at="2026-07-09T00:00:00+00:00",
        )
        context["expert_b"]["timbre_rank_scores"]["sharpness"]["direction"] = "increased"
        with self.assertRaises(ContextValidationError):
            validate_structured_context(context)

    def test_legacy_v01_context_can_migrate_to_v02(self) -> None:
        """Migration preserves old scientific evidence while adding trace metadata."""
        v02 = context_from_expert_b_output(
            _expert_b_output(),
            created_at="2026-07-09T00:00:00+00:00",
        )
        legacy = deepcopy(v02)
        legacy["schema_version"] = LEGACY_CONTEXT_SCHEMA_VERSION
        legacy.pop("analysis")
        validate_structured_context(legacy)

        migrated = migrate_context_v01_to_v02(
            legacy,
            created_at="2026-07-09T00:00:00+00:00",
        )

        self.assertEqual(migrated["schema_version"], CONTEXT_SCHEMA_VERSION)
        self.assertEqual(migrated["event"], legacy["event"])
        self.assertEqual(migrated["expert_a"], legacy["expert_a"])
        self.assertEqual(migrated["expert_b"], legacy["expert_b"])
        self.assertIn("analysis", migrated)

    def test_v02_requires_analysis_metadata(self) -> None:
        """v0.2 contexts cannot omit traceability metadata."""
        context = context_from_expert_b_output(
            _expert_b_output(),
            created_at="2026-07-09T00:00:00+00:00",
        )
        context.pop("analysis")
        with self.assertRaises(ContextValidationError):
            validate_structured_context(context)


if __name__ == "__main__":
    unittest.main()
