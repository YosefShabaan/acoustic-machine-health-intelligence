"""JSON structured logging for event-correlated AMHI lifecycle events."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import json
import logging
from typing import Any


SECRET_KEY_FRAGMENTS = (
    "api_key",
    "apikey",
    "secret",
    "token",
    "password",
    "credential",
)


def get_structured_logger(name: str = "amhi.structured") -> "StructuredLogger":
    """Return a structured logger wrapper."""
    return StructuredLogger(logging.getLogger(name))


@dataclass
class StructuredLogger:
    """Emit bounded JSON log events."""

    logger: logging.Logger

    def emit(
        self,
        event_name: str,
        *,
        event_id: str | None = None,
        analysis_run_id: str | None = None,
        machine_type: str | None = None,
        machine_id: str | None = None,
        stage: str | None = None,
        duration_ms: float | None = None,
        status: str | None = None,
        error_code: str | None = None,
        level: int = logging.INFO,
        **fields: Any,
    ) -> dict[str, Any]:
        """Emit one sanitized JSON log record and return the record."""
        record: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "event_name": event_name,
            "event_id": event_id,
            "analysis_run_id": analysis_run_id,
            "machine_type": machine_type,
            "machine_id": machine_id,
            "stage": stage,
            "duration_ms": duration_ms,
            "status": status,
            "error_code": error_code,
        }
        for key, value in fields.items():
            record[key] = _sanitize(key, value)
        payload = json.dumps(record, sort_keys=True, separators=(",", ":"))
        self.logger.log(level, payload, extra={"structured_event": record})
        return record


def _sanitize(key: str, value: Any) -> Any:
    lowered = key.lower()
    if any(fragment in lowered for fragment in SECRET_KEY_FRAGMENTS):
        return "[REDACTED]"
    if isinstance(value, dict):
        return {str(child_key): _sanitize(str(child_key), child_value) for child_key, child_value in value.items()}
    if isinstance(value, list):
        return [_sanitize(key, item) for item in value]
    if isinstance(value, tuple):
        return [_sanitize(key, item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)
