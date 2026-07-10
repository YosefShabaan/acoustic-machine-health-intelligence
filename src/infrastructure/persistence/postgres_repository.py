"""PostgreSQL-backed persistence for Fan Production MVP."""

from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

import psycopg2
import psycopg2.extras

from application.repositories import (
    ANALYSIS_STATUS_COMPLETED,
    ANALYSIS_STATUS_FAILED,
    ANALYSIS_STATUS_PROCESSING,
    EVENT_STATUS_QUEUED,
    EVENT_STATUS_PROCESSING,
    AnalysisResultRecord,
    AnalysisRunRecord,
    EventRecord,
    validate_analysis_status,
    validate_event_status,
)


MIGRATION_DIR = Path(__file__).parent / "migrations"


def connect_postgres(database_url: str) -> psycopg2.extensions.connection:
    """Connect to PostgreSQL and apply migrations."""
    connection = psycopg2.connect(database_url)
    connection.autocommit = False
    psycopg2.extras.register_default_jsonb(connection)
    _apply_migrations(connection)
    return connection


def _apply_migrations(connection: psycopg2.extensions.connection) -> None:
    """Apply SQL migration files in order."""
    migration_files = sorted(MIGRATION_DIR.glob("*.sql"))
    for migration_file in migration_files:
        sql = migration_file.read_text(encoding="utf-8")
        with connection.cursor() as cursor:
            cursor.execute(sql)
    connection.commit()


class PostgresEventRepository:
    """PostgreSQL implementation of EventRepository."""

    def __init__(self, connection: psycopg2.extensions.connection) -> None:
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
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO events (
                  event_id, machine_type, machine_id, snr_tag, audio_reference,
                  status, created_at, updated_at, error_code, error_summary
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NULL, NULL)
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
        with self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute("SELECT * FROM events WHERE event_id = %s", (event_id,))
            row = cursor.fetchone()
        return _event_from_row(row) if row else None

    def list_events(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
        status: str | None = None,
    ) -> list[EventRecord]:
        with self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            if status is not None:
                validate_event_status(status)
                cursor.execute(
                    """
                    SELECT * FROM events
                    WHERE status = %s
                    ORDER BY created_at ASC, event_id ASC
                    LIMIT %s OFFSET %s
                    """,
                    (status, limit, offset),
                )
            else:
                cursor.execute(
                    """
                    SELECT * FROM events
                    ORDER BY created_at ASC, event_id ASC
                    LIMIT %s OFFSET %s
                    """,
                    (limit, offset),
                )
            rows = cursor.fetchall()
        return [_event_from_row(row) for row in rows]

    def count_events(self, *, status: str | None = None) -> int:
        with self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            if status is not None:
                validate_event_status(status)
                cursor.execute(
                    "SELECT COUNT(*) AS count FROM events WHERE status = %s",
                    (status,),
                )
            else:
                cursor.execute("SELECT COUNT(*) AS count FROM events")
            row = cursor.fetchone()
        return int(row["count"]) if row else 0

    def list_machine_events(
        self,
        *,
        machine_type: str,
        machine_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[EventRecord]:
        with self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute(
                """
                SELECT * FROM events
                WHERE machine_type = %s AND machine_id = %s
                ORDER BY created_at ASC, event_id ASC
                LIMIT %s OFFSET %s
                """,
                (machine_type, machine_id, limit, offset),
            )
            rows = cursor.fetchall()
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
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE events
                SET status = %s, updated_at = %s, error_code = %s, error_summary = %s
                WHERE event_id = %s
                """,
                (status, _now(), error_code, error_summary, event_id),
            )
        self.connection.commit()
        record = self.get_event(event_id)
        if record is None:
            raise KeyError(f"event not found: {event_id}")
        return record

    def claim_next_queued(self) -> EventRecord | None:
        """Atomically claim the next queued event using SELECT ... FOR UPDATE."""
        with self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute(
                """
                UPDATE events
                SET status = %s, updated_at = %s, error_code = NULL, error_summary = NULL
                WHERE event_id = (
                    SELECT event_id FROM events
                    WHERE status = %s
                    ORDER BY created_at ASC, event_id ASC
                    LIMIT 1
                    FOR UPDATE SKIP LOCKED
                )
                RETURNING *
                """,
                (EVENT_STATUS_PROCESSING, _now(), EVENT_STATUS_QUEUED),
            )
            row = cursor.fetchone()
        self.connection.commit()
        return _event_from_row(row) if row else None


class PostgresAnalysisRepository:
    """PostgreSQL implementation of AnalysisRepository."""

    def __init__(self, connection: psycopg2.extensions.connection) -> None:
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
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO analysis_runs (
                  analysis_run_id, event_id, pipeline_version, status, started_at,
                  completed_at, total_duration, artifact_metadata,
                  error_code, error_summary
                )
                VALUES (%s, %s, %s, %s, %s, NULL, NULL, %s, NULL, NULL)
                """,
                (
                    resolved_run_id,
                    event_id,
                    pipeline_version,
                    ANALYSIS_STATUS_PROCESSING,
                    _now(),
                    json.dumps(artifact_metadata or {}, sort_keys=True),
                ),
            )
        self.connection.commit()
        record = self.get_run(resolved_run_id)
        if record is None:
            raise RuntimeError("created analysis run could not be read back")
        return record

    def get_run(self, analysis_run_id: str) -> AnalysisRunRecord | None:
        with self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute(
                "SELECT * FROM analysis_runs WHERE analysis_run_id = %s",
                (analysis_run_id,),
            )
            row = cursor.fetchone()
        return _analysis_run_from_row(row) if row else None

    def get_latest_run_for_event(self, event_id: str) -> AnalysisRunRecord | None:
        with self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute(
                """
                SELECT * FROM analysis_runs
                WHERE event_id = %s
                ORDER BY started_at DESC, analysis_run_id DESC
                LIMIT 1
                """,
                (event_id,),
            )
            row = cursor.fetchone()
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
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO analysis_results (
                  analysis_run_id, expert_a_result, expert_b_evidence,
                  structured_context, retrieval_metadata,
                  explanation_output, maintenance_output, timing_metadata
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (analysis_run_id) DO UPDATE SET
                  expert_a_result = EXCLUDED.expert_a_result,
                  expert_b_evidence = EXCLUDED.expert_b_evidence,
                  structured_context = EXCLUDED.structured_context,
                  retrieval_metadata = EXCLUDED.retrieval_metadata,
                  explanation_output = EXCLUDED.explanation_output,
                  maintenance_output = EXCLUDED.maintenance_output,
                  timing_metadata = EXCLUDED.timing_metadata
                """,
                (
                    analysis_run_id,
                    json.dumps(expert_a_result, sort_keys=True),
                    _json_dumps_or_none(expert_b_evidence),
                    _json_dumps_or_none(structured_context),
                    _json_dumps_or_none(retrieval_metadata),
                    _json_dumps_or_none(explanation_output),
                    _json_dumps_or_none(maintenance_output),
                    json.dumps(timing_metadata, sort_keys=True),
                ),
            )
        self.connection.commit()
        record = self.get_result(analysis_run_id)
        if record is None:
            raise RuntimeError("saved analysis result could not be read back")
        return record

    def get_result(self, analysis_run_id: str) -> AnalysisResultRecord | None:
        with self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
            cursor.execute(
                "SELECT * FROM analysis_results WHERE analysis_run_id = %s",
                (analysis_run_id,),
            )
            row = cursor.fetchone()
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
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE analysis_runs
                SET status = %s, completed_at = %s, total_duration = %s,
                    error_code = %s, error_summary = %s
                WHERE analysis_run_id = %s
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


def _json_dumps_or_none(value: dict[str, Any] | None) -> str | None:
    return None if value is None else json.dumps(value, sort_keys=True)


def _json_loads_safe(value: Any) -> dict[str, Any]:
    """Parse a JSON value that might already be a dict (from psycopg2 JSONB)."""
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        loaded = json.loads(value)
        if not isinstance(loaded, dict):
            raise ValueError("stored JSON payload must be an object")
        return loaded
    if value is None:
        return {}
    raise ValueError(f"unexpected JSON column type: {type(value)}")


def _json_loads_safe_or_none(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    return _json_loads_safe(value)


def _event_from_row(row: Any) -> EventRecord:
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


def _analysis_run_from_row(row: Any) -> AnalysisRunRecord:
    return AnalysisRunRecord(
        analysis_run_id=str(row["analysis_run_id"]),
        event_id=str(row["event_id"]),
        pipeline_version=str(row["pipeline_version"]),
        status=str(row["status"]),
        started_at=str(row["started_at"]),
        completed_at=str(row["completed_at"]) if row["completed_at"] else None,
        total_duration=float(row["total_duration"]) if row["total_duration"] is not None else None,
        artifact_metadata=_json_loads_safe(row["artifact_metadata"]),
        error_code=row["error_code"],
        error_summary=row["error_summary"],
    )


def _analysis_result_from_row(row: Any) -> AnalysisResultRecord:
    return AnalysisResultRecord(
        analysis_run_id=str(row["analysis_run_id"]),
        expert_a_result=_json_loads_safe(row["expert_a_result"]),
        expert_b_evidence=_json_loads_safe_or_none(row["expert_b_evidence"]),
        structured_context=_json_loads_safe_or_none(row["structured_context"]),
        retrieval_metadata=_json_loads_safe_or_none(row["retrieval_metadata"]),
        explanation_output=_json_loads_safe_or_none(row["explanation_output"]),
        maintenance_output=_json_loads_safe_or_none(row["maintenance_output"]),
        timing_metadata=_json_loads_safe(row["timing_metadata"]),
    )
