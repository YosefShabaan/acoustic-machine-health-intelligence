"""Tests for TASK-FAN-13 real intelligence smoke validation."""

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

from run_real_intelligence_fan_smoke import validate_real_intelligence_output  # noqa: E402


ATTRIBUTES = ("sharpness", "roughness", "boominess", "brightness", "depth")
AUDIO_PATH = r"D:\PDM_Data\MIMII\fan_minus6dB\id_00\abnormal\00000002.wav"
EVENT_ID = "fan_id_00_minus6dB_00000002"


def _context() -> dict:
    rank_rows = {
        "sharpness": 0.9333333333333333,
        "roughness": 0.9333333333333333,
        "boominess": 0.0,
        "brightness": 0.9333333333333333,
        "depth": 0.6666666666666666,
    }
    return {
        "schema_version": "0.2.0",
        "event": {
            "event_id": EVENT_ID,
            "asset_id": "FAN-ID00-001",
            "machine_type": "fan",
            "machine_id": "id_00",
            "snr_tag": "minus6dB",
            "audio_path": AUDIO_PATH,
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
                "paper": "Nishida et al. 2024, arXiv:2410.22033",
                "status": "adaptation_not_exact_reproduction",
                "embedding_model": "expert_a_bottleneck_adaptation",
                "embedding_status": "project_mvp_adaptation_not_paper_encoder",
                "embedding_metadata": {},
                "timbre_model": "AudioCommons timbral_models",
                "k": 30,
                "distance": "euclidean",
                "rank_threshold": None,
            },
            "references": {
                "pool_size": 40,
                "selected_count": 30,
                "filter": {
                    "machine_type": "fan",
                    "machine_id": "id_00",
                    "snr_tag": "minus6dB",
                },
                "neighbors": [
                    {"path": f"normal_{index:08d}.wav", "distance": float(index), "rank": index}
                    for index in range(1, 31)
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
        "analysis": {
            "analysis_run_id": "analysis_fan_id_00_minus6dB_00000002_task_fan_13",
            "created_at": "2026-07-09T00:00:00+00:00",
            "pipeline_version": "amhi-real-intelligence-v0.2",
            "expert_a": {
                "model_id": "anomaly_detector_minus6dB.pt",
                "model_version": "unversioned",
                "normalization_artifact_id": "ad_norm_stats_minus6dB.npz",
            },
            "expert_b": {
                "reference_index_id": "timbre_reference_index_fan_id_00_minus6dB.json",
                "embedding_model": "expert_a_bottleneck_adaptation",
                "k": 30,
                "distance": "euclidean",
            },
            "llm": {
                "provider": "gemini",
                "model": "gemini-test",
                "prompt_version": "diagnostic_explanation_v2_gemini_json_2026-07-09",
                "generation_mode": "live_gemini",
                "fallback_used": False,
            },
            "rag": {
                "retriever_type": "semantic",
                "corpus_version": "AMHI-FAN-MAINT-KB-v1",
                "retrieval_query": "fan abnormal acoustic noise inspection",
            },
            "maintenance": {
                "provider": "gemini",
                "model": "gemini-test",
                "prompt_version": "maintenance_actions_v2_gemini_json_2026-07-09",
                "generation_mode": "live_gemini",
                "fallback_used": False,
            },
        },
    }


def _output() -> dict:
    retrieved = {
        "source_id": "approved_proc",
        "title": "Approved Fan Procedure",
        "version": "2026-07",
        "publisher": "Approved Publisher",
        "corpus_version": "AMHI-FAN-MAINT-KB-v1",
        "chunk_id": "approved_proc#chunk-1",
        "section_id": "chunk-1",
        "section_heading": "Inspection",
        "snippet": "For abnormal fan noise, inspect mounting condition.",
        "score": 0.8,
        "path": "procedure.md",
        "source_url": None,
    }
    return {
        "task": "TASK-FAN-13",
        "audio_path": AUDIO_PATH,
        "expert_b_output": {
            "input_audio": {"path": AUDIO_PATH},
            "expert_a": {"is_anomaly": True},
        },
        "structured_context": _context(),
        "guarded_explanation": {
            "prompt": "Event ID only; no raw path.",
            "explanation": {
                "summary": "The fan event was flagged as acoustically anomalous.",
                "observations": ["Expert B reports qualitative local rank differences."],
                "hypotheses": ["The changed sound pattern can guide inspection context."],
                "limitations": ["This is acoustic evidence only."],
            },
            "metadata": {
                "provider": "gemini",
                "model": "gemini-test",
                "generation_mode": "live_gemini",
                "fallback_used": False,
            },
        },
        "retrieval": {
            "query": "fan abnormal acoustic noise inspection",
            "available": True,
            "message": "Retrieved 1 approved source chunk.",
            "warnings": [],
            "results": [retrieved],
        },
        "technician_output": {
            "event": {"event_id": EVENT_ID},
            "observed_ml_evidence": {
                "expert_a": {
                    "anomaly_score": 0.6220951080322266,
                    "threshold": 0.5932844281196594,
                    "is_anomaly": True,
                }
            },
            "technician_explanation": {
                "summary": "The fan event was flagged as acoustically anomalous.",
                "observations": ["Expert B reports qualitative local rank differences."],
                "hypotheses": ["The changed sound pattern can guide inspection context."],
                "limitations": ["This is acoustic evidence only."],
            },
            "retrieved_maintenance_guidance": [retrieved],
            "recommendation": {
                "available": True,
                "event_summary": "The fan event should be treated as inspection context.",
                "observed_evidence": ["Expert A flagged the event."],
                "inspection_priority": "Inspect the fan using retrieved guidance.",
                "recommended_next_actions": [
                    {
                        "action": "Inspect mounting condition.",
                        "reason": "The retrieved approved procedure supports inspection context.",
                        "source_id": "approved_proc",
                        "chunk_id": "approved_proc#chunk-1",
                    }
                ],
                "citations": ["approved_proc"],
                "chunk_citations": ["approved_proc#chunk-1"],
                "text": "The fan event should be treated as inspection context. Next actions: Inspect mounting condition.",
                "limitations": ["Use retrieved guidance as inspection context only."],
            },
            "limitations": [
                "Maintenance output requires retrieved approved-source evidence.",
                "Use retrieved guidance as inspection context only.",
            ],
            "metadata": {
                "provider": "gemini",
                "model": "gemini-test",
                "generation_mode": "live_gemini",
                "fallback_used": False,
                "prompt_version": "maintenance_actions_v2_gemini_json_2026-07-09",
                "retriever_type": "semantic",
                "corpus_version": "AMHI-FAN-MAINT-KB-v1",
            },
            "prompt": "Event ID only; no raw path.",
        },
    }


class RealIntelligenceFanSmokeTests(unittest.TestCase):
    """Validator tests for the real intelligence Fan smoke."""

    def test_valid_output_passes(self) -> None:
        validate_real_intelligence_output(_output())

    def test_missing_action_chunk_citation_is_rejected(self) -> None:
        output = _output()
        output["technician_output"]["recommendation"]["recommended_next_actions"][0][
            "chunk_id"
        ] = "approved_proc#missing"
        with self.assertRaises(ValueError):
            validate_real_intelligence_output(output)

    def test_raw_audio_prompt_is_rejected(self) -> None:
        output = _output()
        output["guarded_explanation"]["prompt"] = f"audio_path: {AUDIO_PATH}"
        with self.assertRaises(ValueError):
            validate_real_intelligence_output(output)

    def test_forbidden_claim_is_rejected(self) -> None:
        output = _output()
        output["guarded_explanation"]["explanation"]["summary"] = (
            "This has 91% confidence and will fail."
        )
        with self.assertRaises(ValueError):
            validate_real_intelligence_output(output)

    def test_gemini_fallback_rejected_by_default(self) -> None:
        output = _output()
        output["guarded_explanation"]["metadata"]["generation_mode"] = (
            "deterministic_fallback"
        )
        output["guarded_explanation"]["metadata"]["fallback_used"] = True
        with self.assertRaises(ValueError):
            validate_real_intelligence_output(output)
        validate_real_intelligence_output(output, require_live_gemini=False)


if __name__ == "__main__":
    unittest.main()
