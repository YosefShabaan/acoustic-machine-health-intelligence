"""Tests for the static Fan MVP dashboard renderer."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = REPO_ROOT / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from dashboard import render_dashboard_html, write_dashboard  # noqa: E402


def _data() -> dict:
    return {
        "task": "TASK-FAN-13",
        "timings": {
            "total_seconds": 25.781358,
            "gemini_explanation_seconds": 9.707559,
            "retrieval_seconds": 1.639424,
            "gemini_maintenance_seconds": 8.912582,
        },
        "limits": {
            "same_machine_same_audio": True,
            "rank_scores_are_probabilities": False,
            "physical_root_cause_confirmed": False,
            "remaining_life_prediction_available": False,
            "production_maintenance_validation_complete": False,
            "multi_machine_generalization_enabled": False,
        },
        "structured_context": {
            "schema_version": "0.2.0",
            "event": {
                "event_id": "fan_id_00_minus6dB_00000002",
                "asset_id": "FAN-ID00-001",
                "machine_type": "fan",
                "machine_id": "id_00",
                "snr_tag": "minus6dB",
                "audio_path": r"D:\PDM_Data\MIMII\fan_minus6dB\id_00\abnormal\00000002.wav",
            },
            "expert_a": {
                "anomaly_score": 0.622095,
                "threshold": 0.593284,
                "is_anomaly": True,
            },
            "expert_b": {
                "references": {"selected_count": 30, "pool_size": 40},
                "timbre_rank_scores": {
                    "sharpness": {"rank_score": 0.933333},
                    "roughness": {"rank_score": 0.933333},
                    "boominess": {"rank_score": 0.0},
                    "brightness": {"rank_score": 0.933333},
                    "depth": {"rank_score": 0.666667},
                },
            },
            "analysis": {
                "analysis_run_id": "analysis_fan_id_00_minus6dB_00000002_task_fan_13",
                "pipeline_version": "amhi-real-intelligence-v0.2",
                "llm": {
                    "provider": "gemini",
                    "model": "gemini-2.5-flash",
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
                    "model": "gemini-2.5-flash",
                    "prompt_version": "maintenance_actions_v2_gemini_json_2026-07-09",
                    "generation_mode": "live_gemini",
                    "fallback_used": False,
                },
            },
        },
        "guarded_explanation": {
            "metadata": {
                "provider": "gemini",
                "model": "gemini-2.5-flash",
                "generation_mode": "live_gemini",
                "fallback_used": False,
            },
        },
        "technician_output": {
            "metadata": {
                "provider": "gemini",
                "model": "gemini-2.5-flash",
                "prompt_version": "maintenance_actions_v2_gemini_json_2026-07-09",
                "generation_mode": "live_gemini",
                "fallback_used": False,
            },
            "technician_explanation": {
                "summary": "The fan audio event was flagged as acoustically anomalous.",
                "observations": ["Expert A flagged the event.", "Expert B compared normal references."],
                "hypotheses": ["The acoustic evidence may indicate a changed operating sound pattern."],
            },
            "retrieved_maintenance_guidance": [
                {
                    "source_id": "doe_fan_sourcebook_2003",
                    "title": "Improving Fan System Performance",
                    "version": "2003",
                    "chunk_id": "doe_fan_sourcebook_2003#DOE-FAN-2003-BASIC-MAINTENANCE",
                    "snippet": "Inspect mounting condition and rotating assembly condition.",
                }
            ],
            "recommendation": {
                "available": True,
                "text": "Use the retrieved approved guidance as inspection context only.",
                "citations": ["doe_fan_sourcebook_2003"],
                "recommended_next_actions": [
                    {
                        "action": "Inspect mounting condition.",
                        "reason": "Retrieved approved guidance supports inspection context.",
                        "source_id": "doe_fan_sourcebook_2003",
                        "chunk_id": "doe_fan_sourcebook_2003#DOE-FAN-2003-BASIC-MAINTENANCE",
                    }
                ],
            },
            "limitations": [
                "Acoustic evidence is not a component-level finding.",
                "No lifetime estimate is available in the active architecture.",
            ],
        },
    }


def _evaluation() -> dict:
    return {
        "summary": {
            "total_events": 20,
            "expert_b_execution_count": 10,
            "pipeline_failures": 0,
            "gemini_explanation_fallback_count": 0,
            "maintenance_fallback_count": 0,
            "citation_validation_failures": 0,
            "per_stage_latency_seconds": {
                "total_seconds": {"mean": 23.444230},
            },
        }
    }


class DashboardTests(unittest.TestCase):
    """Static dashboard rendering tests."""

    def test_render_contains_required_sections(self) -> None:
        html = render_dashboard_html(_data(), evaluation=_evaluation())
        self.assertIn("Fan Intelligence Evidence Dashboard", html)
        self.assertIn("Expert A", html)
        self.assertIn("Expert B Timbre Ranks", html)
        self.assertIn("LLM", html)
        self.assertIn("RAG", html)
        self.assertIn("Maintenance Actions", html)
        self.assertIn("Pipeline Timings", html)
        self.assertIn("Bounded Fan Evaluation", html)
        self.assertIn("Limitations", html)
        self.assertIn("gemini-2.5-flash", html)
        self.assertIn("AMHI-FAN-MAINT-KB-v1", html)
        self.assertIn("doe_fan_sourcebook_2003", html)
        self.assertIn("TASK-FAN-13", html)
        self.assertIn("20", html)

    def test_render_keeps_limits_visible_without_forbidden_claims(self) -> None:
        html = render_dashboard_html(_data(), evaluation=_evaluation()).lower()
        self.assertIn("not a component-level finding", html)
        self.assertNotIn("rul", html)
        self.assertNotIn("remaining useful life", html)
        self.assertNotIn("time to failure", html)
        self.assertNotIn("root cause", html)
        self.assertNotIn("confidence", html)
        self.assertNotIn("%", html)
        self.assertNotIn("bearing", html)

    def test_write_dashboard_outputs_html_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = write_dashboard(
                _data(),
                Path(tmp) / "dashboard.html",
                evaluation=_evaluation(),
            )
            self.assertTrue(output.exists())
            self.assertGreater(output.stat().st_size, 1000)

    def test_live_fallback_is_visible_when_present(self) -> None:
        data = deepcopy(_data())
        data["structured_context"]["analysis"]["llm"]["fallback_used"] = True
        data["structured_context"]["analysis"]["maintenance"]["fallback_used"] = True
        html = render_dashboard_html(data, evaluation=_evaluation())
        self.assertGreaterEqual(html.count("Fallback used"), 2)


if __name__ == "__main__":
    unittest.main()
