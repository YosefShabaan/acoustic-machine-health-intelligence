"""OpenAPI-visible schemas for the AMHI API v1 contract."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


API_VERSION = "v1"


class ErrorBody(BaseModel):
    """Safe API error payload."""

    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    request_id: str | None = None


class ErrorResponse(BaseModel):
    """Standard non-2xx response body."""

    api_version: Literal["v1"] = API_VERSION
    error: ErrorBody


class EventError(BaseModel):
    """Safe persisted event error."""

    code: str
    summary: str


class AudioSummary(BaseModel):
    """Sanitized audio metadata exposed by the API."""

    file_name: str | None = None
    suffix: str | None = None
    size_bytes: int | None = None
    storage_backend: str | None = None
    reference_exposed: bool = False


class EventSummary(BaseModel):
    """Public event state."""

    event_id: str
    machine_type: str
    machine_id: str
    snr_tag: str
    status: str
    created_at: str
    updated_at: str
    error: EventError | None = None
    audio: AudioSummary | None = None


class AnalysisRunSummary(BaseModel):
    """Public analysis run state."""

    analysis_run_id: str
    pipeline_version: str
    status: str
    started_at: str
    completed_at: str | None = None
    total_duration: float | None = None
    artifact_metadata: dict[str, Any] = Field(default_factory=dict)
    error: EventError | None = None


class EventCreateResponse(BaseModel):
    """Response for accepted event creation."""

    api_version: Literal["v1"] = API_VERSION
    event: EventSummary
    links: dict[str, str] = Field(default_factory=dict)


class EventDetailResponse(BaseModel):
    """Response for event lookup."""

    api_version: Literal["v1"] = API_VERSION
    event: EventSummary
    analysis_run: AnalysisRunSummary | None = None
    result: dict[str, Any] | None = None


class Pagination(BaseModel):
    """Offset pagination metadata."""

    limit: int
    offset: int
    count: int
    next_offset: int | None = None


class EventListResponse(BaseModel):
    """Event list response."""

    api_version: Literal["v1"] = API_VERSION
    items: list[EventSummary] = Field(default_factory=list)
    pagination: Pagination


class HealthResponse(BaseModel):
    """Process health response."""

    api_version: Literal["v1"] = API_VERSION
    status: str
    service: str


class DependencyStatus(BaseModel):
    """Readiness dependency status."""

    status: str
    detail: str | None = None


class ReadyResponse(BaseModel):
    """Readiness response."""

    api_version: Literal["v1"] = API_VERSION
    ready: bool
    status: str
    dependencies: dict[str, DependencyStatus] = Field(default_factory=dict)
