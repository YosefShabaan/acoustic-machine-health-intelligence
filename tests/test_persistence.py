"""Tests for Fan Production MVP persistence repositories."""

from __future__ import annotations

from pathlib import Path
import sqlite3
import sys
from tempfile import TemporaryDirectory
import unittest

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from application import (  # noqa: E402
    ANALYSIS_STATUS_COMPLETED,
    ANALYSIS_STATUS_FAILED,
    EVENT_STATUS_COMPLETED,
    EVENT_STATUS_FAILED,
    EVENT_STATUS_PROCESSING,
    EVENT_STATUS_QUEUED,
)
from infrastructure import (  # noqa: E402
    SQLiteAnalysisRepository,
    SQLiteEventRepository,
    connect_sqlite,
)


class PersistenceTests(unittest.TestCase):
    """Repository behavior for local persistent event and result state."""

    def setUp(self) -> None:
        self.connection = connect_sqlite(":memory:")
        self.events = SQLiteEventRepository(self.connection)
        self.analyses = SQLiteAnalysisRepository(self.connection)

    def tearDown(self) -> None:
        self.connection.close()

    def test_event_create_read_list_and_machine_filter(self) -> None:
        first = self.events.create_event(
            event_id="event-1",
            machine_type="fan",
            machine_id="id_00",
            snr_tag="minus6dB",
            audio_reference=r"D:\PDM_Data\MIMII\fan_minus6dB\id_00\abnormal\00000002.wav",
        )
        self.events.create_event(
            event_id="event-2",
            machine_type="fan",
            machine_id="id_00",
            snr_tag="minus6dB",
            audio_reference="registered://fan/event-2.wav",
        )

        self.assertEqual(first.status, EVENT_STATUS_QUEUED)
        self.assertEqual(self.events.get_event("event-1"), first)
        self.assertEqual([event.event_id for event in self.events.list_events()], ["event-1", "event-2"])
        self.assertEqual(
            [event.event_id for event in self.events.list_machine_events(machine_type="fan", machine_id="id_00")],
            ["event-1", "event-2"],
        )

    def test_status_transitions_and_failed_event_persistence(self) -> None:
        self.events.create_event(
            event_id="event-status",
            machine_type="fan",
            machine_id="id_00",
            snr_tag="minus6dB",
            audio_reference="registered://fan/event-status.wav",
        )

        processing = self.events.update_status("event-status", EVENT_STATUS_PROCESSING)
        failed = self.events.update_status(
            "event-status",
            EVENT_STATUS_FAILED,
            error_code="audio_missing",
            error_summary="Audio reference was not readable.",
        )

        self.assertEqual(processing.status, EVENT_STATUS_PROCESSING)
        self.assertEqual(failed.status, EVENT_STATUS_FAILED)
        self.assertEqual(failed.error_code, "audio_missing")
        self.assertEqual(failed.error_summary, "Audio reference was not readable.")
        self.assertEqual(
            [event.event_id for event in self.events.list_events(status=EVENT_STATUS_FAILED)],
            ["event-status"],
        )

    def test_analysis_result_round_trip(self) -> None:
        self.events.create_event(
            event_id="event-analysis",
            machine_type="fan",
            machine_id="id_00",
            snr_tag="minus6dB",
            audio_reference="registered://fan/event-analysis.wav",
        )
        run = self.analyses.create_run(
            analysis_run_id="analysis-1",
            event_id="event-analysis",
            pipeline_version="amhi-real-intelligence-v0.2",
            artifact_metadata={"expert_a_model_id": "anomaly_detector_minus6dB.pt"},
        )
        result = self.analyses.save_result(
            analysis_run_id=run.analysis_run_id,
            expert_a_result={"anomaly_score": 0.622095, "threshold": 0.593284, "is_anomaly": True},
            expert_b_evidence={"k": 30, "distance": "euclidean", "rank_threshold": None},
            structured_context={
                "schema_version": "0.2.0",
                "event": {"event_id": "event-analysis"},
            },
            retrieval_metadata={
                "retriever_type": "semantic",
                "corpus_version": "AMHI-FAN-MAINT-KB-v1",
            },
            explanation_output={"metadata": {"fallback_used": False}},
            maintenance_output={"recommendation": {"available": True}},
            timing_metadata={"total_seconds": 17.0},
        )
        completed = self.analyses.complete_run(run.analysis_run_id, total_duration=17.0)

        self.assertEqual(completed.status, ANALYSIS_STATUS_COMPLETED)
        self.assertEqual(completed.total_duration, 17.0)
        self.assertEqual(result.expert_a_result["is_anomaly"], True)
        self.assertEqual(result.expert_b_evidence["k"], 30)
        self.assertEqual(result.structured_context["schema_version"], "0.2.0")
        self.assertEqual(result.retrieval_metadata["retriever_type"], "semantic")
        self.assertEqual(result.timing_metadata["total_seconds"], 17.0)
        self.assertEqual(self.analyses.get_result(run.analysis_run_id), result)

    def test_failed_analysis_run_persistence(self) -> None:
        self.events.create_event(
            event_id="event-failed-run",
            machine_type="fan",
            machine_id="id_00",
            snr_tag="minus6dB",
            audio_reference="registered://fan/event-failed-run.wav",
        )
        run = self.analyses.create_run(
            analysis_run_id="analysis-failed",
            event_id="event-failed-run",
            pipeline_version="amhi-real-intelligence-v0.2",
        )

        failed = self.analyses.fail_run(
            run.analysis_run_id,
            error_code="gemini_unavailable",
            error_summary="Provider call failed after bounded handling.",
        )

        self.assertEqual(failed.status, ANALYSIS_STATUS_FAILED)
        self.assertEqual(failed.error_code, "gemini_unavailable")
        self.assertEqual(failed.error_summary, "Provider call failed after bounded handling.")

    def test_state_survives_reconnect(self) -> None:
        with TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "amhi.sqlite"
            connection = connect_sqlite(db_path)
            SQLiteEventRepository(connection).create_event(
                event_id="event-persisted",
                machine_type="fan",
                machine_id="id_00",
                snr_tag="minus6dB",
                audio_reference="registered://fan/event-persisted.wav",
            )
            connection.close()

            reopened = connect_sqlite(db_path)
            try:
                record = SQLiteEventRepository(reopened).get_event("event-persisted")
                self.assertIsNotNone(record)
                self.assertEqual(record.status, EVENT_STATUS_QUEUED)
            finally:
                reopened.close()

    def test_schema_does_not_store_raw_audio_binary_columns(self) -> None:
        table_names = ("events", "analysis_runs", "analysis_results")
        for table_name in table_names:
            columns = self.connection.execute(f"PRAGMA table_info({table_name})").fetchall()
            column_types = [str(row["type"]).upper() for row in columns]
            self.assertFalse(any("BLOB" in column_type for column_type in column_types))
        event_columns = self.connection.execute("PRAGMA table_info(events)").fetchall()
        self.assertIn("audio_reference", [str(row["name"]) for row in event_columns])

        migration = (
            REPO_ROOT
            / "src"
            / "infrastructure"
            / "persistence"
            / "migrations"
            / "001_initial_postgres.sql"
        ).read_text(encoding="utf-8").upper()
        self.assertNotIn("BYTEA", migration)
        self.assertNotIn(" BLOB", migration)

    def test_invalid_status_is_rejected(self) -> None:
        self.events.create_event(
            event_id="event-invalid-status",
            machine_type="fan",
            machine_id="id_00",
            snr_tag="minus6dB",
            audio_reference="registered://fan/event-invalid-status.wav",
        )
        with self.assertRaises(ValueError):
            self.events.update_status("event-invalid-status", "done")


if __name__ == "__main__":
    unittest.main()
