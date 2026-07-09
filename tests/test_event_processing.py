"""Tests for bounded asynchronous event processing."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from application import (  # noqa: E402
    EVENT_STATUS_COMPLETED,
    EVENT_STATUS_FAILED,
    EVENT_STATUS_PROCESSING,
    EventProcessingService,
)
from infrastructure import (  # noqa: E402
    SQLiteAnalysisRepository,
    SQLiteEventRepository,
    connect_sqlite,
)


class EventProcessingTests(unittest.TestCase):
    """Database-backed worker lifecycle tests."""

    def setUp(self) -> None:
        self.connection = connect_sqlite(":memory:")
        self.events = SQLiteEventRepository(self.connection)
        self.analyses = SQLiteAnalysisRepository(self.connection)

    def tearDown(self) -> None:
        self.connection.close()

    def test_process_next_event_completes_and_persists_result(self) -> None:
        event = self._create_event("event-complete")
        pipeline = FakePipeline()
        service = EventProcessingService(self.events, self.analyses, pipeline)

        result = service.process_next_event()

        self.assertTrue(result.processed)
        self.assertEqual(result.event_id, event.event_id)
        self.assertEqual(result.final_status, EVENT_STATUS_COMPLETED)
        self.assertIsNotNone(result.processing_duration_seconds)
        self.assertEqual(self.events.get_event(event.event_id).status, EVENT_STATUS_COMPLETED)
        run = self.analyses.get_latest_run_for_event(event.event_id)
        self.assertIsNotNone(run)
        self.assertEqual(run.status, EVENT_STATUS_COMPLETED)
        saved = self.analyses.get_result(run.analysis_run_id)
        self.assertEqual(saved.expert_a_result["is_anomaly"], True)
        self.assertEqual(saved.expert_b_evidence["k"], 30)
        self.assertEqual(saved.structured_context["schema_version"], "0.2.0")
        self.assertEqual(pipeline.calls[0]["audio_reference"], "registered://event-complete.wav")

    def test_no_queued_event_returns_idle_without_pipeline_call(self) -> None:
        pipeline = FakePipeline()
        service = EventProcessingService(self.events, self.analyses, pipeline)

        result = service.process_next_event()

        self.assertFalse(result.processed)
        self.assertEqual(result.final_status, "idle")
        self.assertEqual(pipeline.calls, [])

    def test_pipeline_failure_persists_failed_event_and_run(self) -> None:
        event = self._create_event("event-failed")
        service = EventProcessingService(self.events, self.analyses, FakePipeline(fail=True))

        result = service.process_next_event()

        self.assertTrue(result.processed)
        self.assertEqual(result.final_status, EVENT_STATUS_FAILED)
        self.assertEqual(result.error_code, "pipeline_runtimeerror")
        failed_event = self.events.get_event(event.event_id)
        self.assertEqual(failed_event.status, EVENT_STATUS_FAILED)
        self.assertEqual(failed_event.error_code, "pipeline_runtimeerror")
        run = self.analyses.get_latest_run_for_event(event.event_id)
        self.assertEqual(run.status, EVENT_STATUS_FAILED)
        self.assertEqual(run.error_code, "pipeline_runtimeerror")
        self.assertIsNone(self.analyses.get_result(run.analysis_run_id))

    def test_claim_next_queued_prevents_duplicate_claim(self) -> None:
        event = self._create_event("event-claim")

        first_claim = self.events.claim_next_queued()
        second_claim = self.events.claim_next_queued()

        self.assertEqual(first_claim.event_id, event.event_id)
        self.assertEqual(first_claim.status, EVENT_STATUS_PROCESSING)
        self.assertIsNone(second_claim)

    def test_process_available_processes_three_events(self) -> None:
        for index in range(3):
            self._create_event(f"event-three-{index}")
        pipeline = FakePipeline()
        service = EventProcessingService(self.events, self.analyses, pipeline)

        results = service.process_available(max_events=3)

        self.assertEqual(len(results), 3)
        self.assertTrue(all(result.final_status == EVENT_STATUS_COMPLETED for result in results))
        self.assertEqual(len(pipeline.calls), 3)
        self.assertEqual(
            [event.status for event in self.events.list_events()],
            [EVENT_STATUS_COMPLETED, EVENT_STATUS_COMPLETED, EVENT_STATUS_COMPLETED],
        )

    def _create_event(self, event_id: str):
        return self.events.create_event(
            event_id=event_id,
            machine_type="fan",
            machine_id="id_00",
            snr_tag="minus6dB",
            audio_reference=f"registered://{event_id}.wav",
        )


class FakePipeline:
    """Small deterministic pipeline test double."""

    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.calls: list[dict[str, str]] = []

    def process_event(
        self,
        audio_reference: str,
        machine_type: str,
        machine_id: str,
        snr_tag: str,
        *,
        task_id: str,
    ) -> dict[str, object]:
        self.calls.append(
            {
                "audio_reference": audio_reference,
                "machine_type": machine_type,
                "machine_id": machine_id,
                "snr_tag": snr_tag,
                "task_id": task_id,
            },
        )
        if self.fail:
            raise RuntimeError("fake pipeline failed safely")
        return {
            "expert_a": {
                "anomaly_score": 0.622095,
                "threshold": 0.593284,
                "is_anomaly": True,
            },
            "expert_b_output": {
                "k": 30,
                "distance": "euclidean",
                "rank_threshold": None,
            },
            "structured_context": {"schema_version": "0.2.0"},
            "retrieval": {"retriever_type": "semantic"},
            "guarded_explanation": {"metadata": {"fallback_used": False}},
            "technician_output": {"metadata": {"fallback_used": False}},
            "timings": {"total_seconds": 0.01},
        }


if __name__ == "__main__":
    unittest.main()
