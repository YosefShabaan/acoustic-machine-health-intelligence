"""Tests for TASK-FAN-14 bounded Fan system evaluation helpers."""

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

from evaluate_fan_system import (  # noqa: E402
    SelectedEvent,
    interleave_event_rows,
    summarize_evaluation,
    validate_fan_system_evaluation,
)


def _event(label: str, index: int, flagged: bool) -> SelectedEvent:
    return SelectedEvent(
        event_index=index,
        label=label,
        audio_path=Path(f"{label}_{index:08d}.wav"),
        expert_a={
            "anomaly_score": 0.7 if flagged else 0.2,
            "threshold": 0.5,
            "is_anomaly": flagged,
        },
        expert_a_seconds=0.1,
        selection_note="test",
    )


def _result(label: str, index: int, flagged: bool, completed: bool = False) -> dict:
    event = _event(label, index, flagged).to_dict()
    event.update(
        {
            "status": "pipeline_completed" if completed else "expert_a_not_flagged",
            "expert_b_ran": completed,
            "pipeline_completed": completed,
            "pipeline_failed": False,
            "same_audio_identity_success": completed or None,
            "context_validation_success": completed or None,
            "retrieval_available": completed or None,
            "retrieval_top_source_id": "source_a" if completed else None,
            "gemini_explanation_success": completed,
            "gemini_explanation_fallback_used": False if completed else None,
            "maintenance_generation_success": completed,
            "maintenance_fallback_used": False if completed else None,
            "citation_validation_failed": False,
            "forbidden_claim_hits": [],
            "timings": {"expert_a_seconds": 0.1, "total_seconds": 2.0 if completed else 0.1},
        }
    )
    return event


class FanSystemEvaluationTests(unittest.TestCase):
    """Bounded evaluation helper tests."""

    def test_interleave_event_rows(self) -> None:
        rows = interleave_event_rows(
            [_event("normal", 1, False), _event("normal", 2, False)],
            [_event("abnormal", 1, True), _event("abnormal", 2, True)],
        )
        self.assertEqual(
            [(row.label, row.audio_path.name) for row in rows],
            [
                ("normal", "normal_00000001.wav"),
                ("abnormal", "abnormal_00000001.wav"),
                ("normal", "normal_00000002.wav"),
                ("abnormal", "abnormal_00000002.wav"),
            ],
        )

    def test_summary_counts_pipeline_results(self) -> None:
        events = [
            *[_result("normal", index, False) for index in range(10)],
            *[_result("abnormal", index, True, completed=True) for index in range(10)],
        ]
        summary = summarize_evaluation(events)
        self.assertEqual(summary["total_events"], 20)
        self.assertEqual(summary["normal_events"], 10)
        self.assertEqual(summary["abnormal_events"], 10)
        self.assertEqual(summary["expert_a_flagged_count"], 10)
        self.assertEqual(summary["expert_b_execution_count"], 10)
        self.assertEqual(summary["same_audio_identity_success"], 10)
        self.assertEqual(summary["retrieval_top_source_distribution"], {"source_a": 10})

    def test_validation_rejects_expert_b_without_expert_a_flag(self) -> None:
        events = [
            *[_result("normal", index, False) for index in range(10)],
            *[_result("abnormal", index, True, completed=True) for index in range(10)],
        ]
        events[0]["expert_b_ran"] = True
        evaluation = {
            "task": "TASK-FAN-14",
            "events": events,
            "summary": summarize_evaluation(events),
        }
        with self.assertRaises(ValueError):
            validate_fan_system_evaluation(evaluation)

    def test_validation_rejects_wrong_event_count(self) -> None:
        events = [_result("normal", 1, False)]
        evaluation = {
            "task": "TASK-FAN-14",
            "events": events,
            "summary": summarize_evaluation(events),
        }
        with self.assertRaises(ValueError):
            validate_fan_system_evaluation(evaluation)


if __name__ == "__main__":
    unittest.main()
