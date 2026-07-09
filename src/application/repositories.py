"""Repository contracts for Fan Production MVP event persistence."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


EVENT_STATUS_QUEUED = "queued"
EVENT_STATUS_PROCESSING = "processing"
EVENT_STATUS_COMPLETED = "completed"
EVENT_STATUS_FAILED = "failed"
EVENT_STATUSES = (
    EVENT_STATUS_QUEUED,
    EVENT_STATUS_PROCESSING,
    EVENT_STATUS_COMPLETED,
    EVENT_STATUS_FAILED,
)

ANALYSIS_STATUS_PROCESSING = "processing"
ANALYSIS_STATUS_COMPLETED = "completed"
ANALYSIS_STATUS_FAILED = "failed"
ANALYSIS_STATUSES = (
    ANALYSIS_STATUS_PROCESSING,
    ANALYSIS_STATUS_COMPLETED,
    ANALYSIS_STATUS_FAILED,
)


@dataclass(frozen=True)
class EventRecord:
    """Persistent event lifecycle record."""

    event_id: str
    machine_type: str
    machine_id: str
    snr_tag: str
    audio_reference: str
    status: str
    created_at: str
    updated_at: str
    error_code: str | None = None
    error_summary: str | None = None


@dataclass(frozen=True)
class AnalysisRunRecord:
    """Persistent analysis run metadata."""

    analysis_run_id: str
    event_id: str
    pipeline_version: str
    status: str
    started_at: str
    completed_at: str | None = None
    total_duration: float | None = None
    artifact_metadata: dict[str, Any] = field(default_factory=dict)
    error_code: str | None = None
    error_summary: str | None = None


@dataclass(frozen=True)
class AnalysisResultRecord:
    """Persistent structured analysis result payload."""

    analysis_run_id: str
    expert_a_result: dict[str, Any]
    expert_b_evidence: dict[str, Any] | None
    structured_context: dict[str, Any] | None
    retrieval_metadata: dict[str, Any] | None
    explanation_output: dict[str, Any] | None
    maintenance_output: dict[str, Any] | None
    timing_metadata: dict[str, Any]


class EventRepository(Protocol):
    """Boundary for event lifecycle persistence."""

    def create_event(
        self,
        *,
        machine_type: str,
        machine_id: str,
        snr_tag: str,
        audio_reference: str,
        event_id: str | None = None,
    ) -> EventRecord:
        """Create a queued event."""

    def get_event(self, event_id: str) -> EventRecord | None:
        """Return one event by id."""

    def list_events(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
        status: str | None = None,
    ) -> list[EventRecord]:
        """Return events with optional status filtering."""

    def list_machine_events(
        self,
        *,
        machine_type: str,
        machine_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[EventRecord]:
        """Return events for a specific machine."""

    def update_status(
        self,
        event_id: str,
        status: str,
        *,
        error_code: str | None = None,
        error_summary: str | None = None,
    ) -> EventRecord:
        """Update event lifecycle status."""


class AnalysisRepository(Protocol):
    """Boundary for analysis run and result persistence."""

    def create_run(
        self,
        *,
        event_id: str,
        pipeline_version: str,
        analysis_run_id: str | None = None,
        artifact_metadata: dict[str, Any] | None = None,
    ) -> AnalysisRunRecord:
        """Create a processing analysis run."""

    def get_run(self, analysis_run_id: str) -> AnalysisRunRecord | None:
        """Return one analysis run by id."""

    def complete_run(
        self,
        analysis_run_id: str,
        *,
        total_duration: float,
    ) -> AnalysisRunRecord:
        """Mark a run completed."""

    def fail_run(
        self,
        analysis_run_id: str,
        *,
        error_code: str,
        error_summary: str,
    ) -> AnalysisRunRecord:
        """Mark a run failed with a safe summary."""

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
        """Persist final structured analysis payloads."""

    def get_result(self, analysis_run_id: str) -> AnalysisResultRecord | None:
        """Return persisted analysis result payloads."""


def validate_event_status(status: str) -> None:
    """Validate event status value."""
    if status not in EVENT_STATUSES:
        raise ValueError(f"Unsupported event status: {status}")


def validate_analysis_status(status: str) -> None:
    """Validate analysis status value."""
    if status not in ANALYSIS_STATUSES:
        raise ValueError(f"Unsupported analysis status: {status}")
