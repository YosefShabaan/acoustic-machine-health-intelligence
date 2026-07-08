"""Tests for the static Fan MVP dashboard renderer."""

from __future__ import annotations

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
        "maintenance_source_mode": "approved_fixture_not_production_manual",
        "timings": {"total_seconds": 15.792862},
        "structured_context": {
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
        },
        "technician_output": {
            "technician_explanation": {
                "summary": "The fan audio event was flagged as acoustically anomalous.",
                "observations": ["Expert A flagged the event.", "Expert B compared normal references."],
                "hypotheses": ["The acoustic evidence may indicate a changed operating sound pattern."],
            },
            "retrieved_maintenance_guidance": [
                {
                    "source_id": "task10_fixture_fan_inspection",
                    "title": "TASK-10 Fixture Fan Inspection Procedure",
                    "version": "task10-smoke-v1",
                    "chunk_id": "task10_fixture_fan_inspection#chunk-1",
                    "snippet": "Inspect mounting condition and rotating assembly condition.",
                }
            ],
            "recommendation": {
                "available": True,
                "text": "Use the retrieved approved guidance as inspection context only.",
                "citations": ["task10_fixture_fan_inspection"],
            },
            "limitations": [
                "Acoustic evidence is not a component-level finding.",
                "No lifetime estimate is available in the active architecture.",
            ],
        },
    }


class DashboardTests(unittest.TestCase):
    """Static dashboard rendering tests."""

    def test_render_contains_required_sections(self) -> None:
        html = render_dashboard_html(_data())
        self.assertIn("Fan MVP Evidence Dashboard", html)
        self.assertIn("Expert A", html)
        self.assertIn("Expert B Timbre Ranks", html)
        self.assertIn("Retrieved Sources", html)
        self.assertIn("Recommendation", html)
        self.assertIn("Limitations", html)
        self.assertIn("task10_fixture_fan_inspection", html)

    def test_render_keeps_limits_visible_without_forbidden_claims(self) -> None:
        html = render_dashboard_html(_data()).lower()
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
            output = write_dashboard(_data(), Path(tmp) / "dashboard.html")
            self.assertTrue(output.exists())
            self.assertGreater(output.stat().st_size, 1000)


if __name__ == "__main__":
    unittest.main()
