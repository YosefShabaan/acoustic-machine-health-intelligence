"""SQLite-backed local persistence for Fan Production MVP tests and dev."""

from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
import sqlite3
from typing import Any
from uuid import uuid4

from application.repositories import (
    ANALYSIS_STATUS_COMPLETED,
    ANALYSIS_STATUS_FAILED,
    ANALYSIS_STATUS_PROCESSING,
    EVENT_STATUS_QUEUED,
    AnalysisResultRecord,
    AnalysisRunRecord,
    EventRecord,
    validate_analysis_status,
    validate_event_status,
)


SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
  event_id TEXT PRIMARY KEY,
  machine_type TEXT NOT NULL,
  machine_id TEXT NOT NULL,
  snr_tag TEXT NOT NULL,
  audio_reference TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('queued', 'processing', 'completed', 'failed')),
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  error_code TEXT,
  error_summary TEXT
);

CREATE INDEX IF NOT EXISTS idx_events_status_created
  ON events(status, created_at);

CREATE INDEX IF NOT EXISTS idx_events_machine_created
  ON events(machine_type, machine_id, created_at);

CREATE TABLE IF NOT EXISTS analysis_runs (
  analysis_run_id TEXT PRIMARY KEY,
  event_id TEXT NOT NULL REFERENCES events(event_id) ON DELETE CASCADE,
  pipeline_version TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('processing', 'completed', 'failed')),
  started_at TEXT NOT NULL,
  completed_at TEXT,
  total_duration REAL,
  artifact_metadata_json TEXT NOT NULL,
  error_code TEXT,
  error_summary TEXT
);

CREATE INDEX IF NOT EXISTS idx_analysis_runs_event
  ON analysis_runs(event_id, started_at);

CREATE TABLE IF NOT EXISTS analysis_results (
  analysis_run_id TEXT PRIMARY KEY REFERENCES analysis_runs(analysis_run_id) ON DELETE CASCADE,
  expert_a_result_json TEXT NOT NULL,
  expert_b_evidence_json TEXT,
  structured_context_json TEXT,
  retrieval_metadata_json TEXT,
  explanation_output_json TEXT,
  maintenance_output_json TEXT,
  timing_metadata_json TEXT NOT NULL
);
"""


def connect_sqlite(path: str | Path = ":memory:") -> sqlite3.Connection:
    """Connect to SQLite and initialize the local persistence schema."""
    connection = sqlite3.connect(str(path))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    initialize_sqlite_schema(connection)
    return connection


def initialize_sqlite_schema(connection: sqlite3.Connection) -> None:
    """Initialize SQLite tables for local/test persistence."""
    connection.executescript(SQLITE_SCHEMA)
    connection.commit()


class SQLiteEventRepository:
    """SQLite implementation of EventRepository."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def create_event(
        self,
        *,
        machine_type: str,
        machine_id: str,
        snr_tag: str,
        audio_reference: str,
        event_id: str | None = None,
    ) -> EventRecord:
        now = _now()
        resolved_event_id = event_id or f"event_{uuid4().hex}"
        self.connection.execute(
            """
            INSERT INTO events (
              event_id, machine_type, machine_id, snr_tag, audio_reference,
              status, created_at, updated_at, error_code, error_summary
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL)
            """,
            (
                resolved_event_id,
                machine_type,
                machine_id,
                snr_tag,
                audio_reference,
                EVENT_STATUS_QUEUED,
                now,
                now,
            ),
        )
        self.connection.commit()
        record = self.get_event(resolved_event_id)
        if record is None:
            raise RuntimeError("created event could not be read back")
        return record

    def get_event(self, event_id: str) -> EventRecord | None:
        row = self.connection.execute(
            "SELECT * FROM events WHERE event_id = ?",
            (event_id,),
        ).fetchone()
        return _event_from_row(row) if row else None

    def list_events(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
        status: str | None = None,
    ) -> list[EventRecord]:
        if status is not None:
            validate_event_status(status)
            rows = self.connection.execute(
                """
                SELECT * FROM events
                WHERE status = ?
                ORDER BY created_at ASC, event_id ASC
                LIMIT ? OFFSET ?
                """,
                (status, limit, offset),
            ).fetchall()
        else:
            rows = self.connection.execute(
                """
                SELECT * FROM events
                ORDER BY created_at ASC, event_id ASC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            ).fetchall()
        return [_event_from_row(row) for row in rows]

    def list_machine_events(
        self,
        *,
        machine_type: str,
        machine_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[EventRecord]:
        rows = self.connection.execute(
            """
            SELECT * FROM events
            WHERE machine_type = ? AND machine_id = ?
            ORDER BY created_at ASC, event_id ASC
            LIMIT ? OFFSET ?
            """,
            (machine_type, machine_id, limit, offset),
        ).fetchall()
        return [_event_from_row(row) for row in rows]

    def update_status(
        self,
        event_id: str,
        status: str,
        *,
        error_code: str | None = None,
        error_summary: str | None = None,
    ) -> EventRecord:
        validate_event_status(status)
        self.connection.execute(
            """
            UPDATE events
            SET status = ?, updated_at = ?, error_code = ?, error_summary = ?
            WHERE event_id = ?
            """,
            (status, _now(), error_code, error_summary, event_id),
        )
        self.connection.commit()
        record = self.get_event(event_id)
        if record is None:
            raise KeyError(f"event not found: {event_id}")
        return record


class SQLiteAnalysisRepository:
    """SQLite implementation of AnalysisRepository."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def create_run(
        self,
        *,
        event_id: str,
        pipeline_version: str,
        analysis_run_id: str | None = None,
        artifact_metadata: dict[str, Any] | None = None,
    ) -> AnalysisRunRecord:
        resolved_run_id = analysis_run_id or f"analysis_{uuid4().hex}"
        self.connection.execute(
            """
            INSERT INTO analysis_runs (
              analysis_run_id, event_id, pipeline_version, status, started_at,
              completed_at, total_duration, artifact_metadata_json,
              error_code, error_summary
            )
            VALUES (?, ?, ?, ?, ?, NULL, NULL, ?, NULL, NULL)
            """,
            (
                resolved_run_id,
                event_id,
                pipeline_version,
                ANALYSIS_STATUS_PROCESSING,
                _now(),
                _json_dumps(artifact_metadata or {}),
            ),
        )
        self.connection.commit()
        record = self.get_run(resolved_run_id)
        if record is None:
            raise RuntimeError("created analysis run could not be read back")
        return record

    def get_run(self, analysis_run_id: str) -> AnalysisRunRecord | None:
        row = self.connection.execute(
            "SELECT * FROM analysis_runs WHERE analysis_run_id = ?",
            (analysis_run_id,),
        ).fetchone()
        return _analysis_run_from_row(row) if row else None

    def complete_run(
        self,
        analysis_run_id: str,
        *,
        total_duration: float,
    ) -> AnalysisRunRecord:
        return self._update_run_status(
            analysis_run_id,
            ANALYSIS_STATUS_COMPLETED,
            total_duration=total_duration,
        )

    def fail_run(
        self,
        analysis_run_id: str,
        *,
        error_code: str,
        error_summary: str,
    ) -> AnalysisRunRecord:
        return self._update_run_status(
            analysis_run_id,
            ANALYSIS_STATUS_FAILED,
            error_code=error_code,
            error_summary=error_summary,
        )

    def save_result(
        self,
        *,
        analysis_run_id: str,
        expert_a_result: dict[str, Any],
        expert_b_evidence: dict[str, Any] | None,
        structured_context: dict[str, Any] | None,
        retrieval_metadata: dict[str, Any] | None,
        explanation_output: dict[str, Any] | None,
        maintenance_output: dict[str, Any] | None,
        timing_metadata: dict[str, Any],
    ) -> AnalysisResultRecord:
        self.connection.execute(
            """
            INSERT OR REPLACE INTO analysis_results (
              analysis_run_id, expert_a_result_json, expert_b_evidence_json,
              structured_context_json, retrieval_metadata_json,
              explanation_output_json, maintenance_output_json, timing_metadata_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                analysis_run_id,
                _json_dumps(expert_a_result),
                _json_dumps_or_none(expert_b_evidence),
                _json_dumps_or_none(structured_context),
                _json_dumps_or_none(retrieval_metadata),
                _json_dumps_or_none(explanation_output),
                _json_dumps_or_none(maintenance_output),
                _json_dumps(timing_metadata),
            ),
        )
        self.connection.commit()
        record = self.get_result(analysis_run_id)
        if record is None:
            raise RuntimeError("saved analysis result could not be read back")
        return record

    def get_result(self, analysis_run_id: str) -> AnalysisResultRecord | None:
        row = self.connection.execute(
            "SELECT * FROM analysis_results WHERE analysis_run_id = ?",
            (analysis_run_id,),
        ).fetchone()
        return _analysis_result_from_row(row) if row else None

    def _update_run_status(
        self,
        analysis_run_id: str,
        status: str,
        *,
        total_duration: float | None = None,
        error_code: str | None = None,
        error_summary: str | None = None,
    ) -> AnalysisRunRecord:
        validate_analysis_status(status)
        self.connection.execute(
            """
            UPDATE analysis_runs
            SET status = ?, completed_at = ?, total_duration = ?,
                error_code = ?, error_summary = ?
            WHERE analysis_run_id = ?
            """,
            (status, _now(), total_duration, error_code, error_summary, analysis_run_id),
        )
        self.connection.commit()
        record = self.get_run(analysis_run_id)
        if record is None:
            raise KeyError(f"analysis run not found: {analysis_run_id}")
        return record


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _json_dumps(value: dict[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _json_dumps_or_none(value: dict[str, Any] | None) -> str | None:
    return None if value is None else _json_dumps(value)


def _json_loads(value: str) -> dict[str, Any]:
    loaded = json.loads(value)
    if not isinstance(loaded, dict):
        raise ValueError("stored JSON payload must be an object")
    return loaded


def _json_loads_or_none(value: str | None) -> dict[str, Any] | None:
    return None if value is None else _json_loads(value)


def _event_from_row(row: sqlite3.Row) -> EventRecord:
    return EventRecord(
        event_id=str(row["event_id"]),
        machine_type=str(row["machine_type"]),
        machine_id=str(row["machine_id"]),
        snr_tag=str(row["snr_tag"]),
        audio_reference=str(row["audio_reference"]),
        status=str(row["status"]),
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
        error_code=row["error_code"],
        error_summary=row["error_summary"],
    )


def _analysis_run_from_row(row: sqlite3.Row) -> AnalysisRunRecord:
    return AnalysisRunRecord(
        analysis_run_id=str(row["analysis_run_id"]),
        event_id=str(row["event_id"]),
        pipeline_version=str(row["pipeline_version"]),
        status=str(row["status"]),
        started_at=str(row["started_at"]),
        completed_at=row["completed_at"],
        total_duration=row["total_duration"],
        artifact_metadata=_json_loads(str(row["artifact_metadata_json"])),
        error_code=row["error_code"],
        error_summary=row["error_summary"],
    )


def _analysis_result_from_row(row: sqlite3.Row) -> AnalysisResultRecord:
    return AnalysisResultRecord(
        analysis_run_id=str(row["analysis_run_id"]),
        expert_a_result=_json_loads(str(row["expert_a_result_json"])),
        expert_b_evidence=_json_loads_or_none(row["expert_b_evidence_json"]),
        structured_context=_json_loads_or_none(row["structured_context_json"]),
        retrieval_metadata=_json_loads_or_none(row["retrieval_metadata_json"]),
        explanation_output=_json_loads_or_none(row["explanation_output_json"]),
        maintenance_output=_json_loads_or_none(row["maintenance_output_json"]),
        timing_metadata=_json_loads(str(row["timing_metadata_json"])),
    )
