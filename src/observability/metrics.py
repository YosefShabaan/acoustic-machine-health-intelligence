"""Bounded in-process metrics for the Fan Production MVP."""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from typing import Any


@dataclass
class MetricsRegistry:
    """Small Prometheus-text-compatible metrics registry."""

    counters: dict[str, float] = field(default_factory=dict)
    gauges: dict[str, float] = field(default_factory=dict)
    durations: dict[str, list[float]] = field(default_factory=dict)
    _lock: Lock = field(default_factory=Lock, repr=False)

    def increment(self, name: str, amount: float = 1.0) -> None:
        """Increment a counter."""
        with self._lock:
            self.counters[name] = self.counters.get(name, 0.0) + amount

    def set_gauge(self, name: str, value: float) -> None:
        """Set a gauge value."""
        with self._lock:
            self.gauges[name] = float(value)

    def observe_duration(self, name: str, seconds: float | None) -> None:
        """Observe a duration in seconds."""
        if seconds is None:
            return
        with self._lock:
            self.durations.setdefault(name, []).append(float(seconds))

    def snapshot(self) -> dict[str, Any]:
        """Return a copy of current metric values."""
        with self._lock:
            return {
                "counters": dict(self.counters),
                "gauges": dict(self.gauges),
                "durations": {name: list(values) for name, values in self.durations.items()},
            }

    def render_prometheus(self) -> str:
        """Render metrics as Prometheus text exposition."""
        snapshot = self.snapshot()
        lines: list[str] = []
        for name in sorted(snapshot["counters"]):
            lines.append(f"# TYPE {name} counter")
            lines.append(f"{name} {_fmt(snapshot['counters'][name])}")
        for name in sorted(snapshot["gauges"]):
            lines.append(f"# TYPE {name} gauge")
            lines.append(f"{name} {_fmt(snapshot['gauges'][name])}")
        for name in sorted(snapshot["durations"]):
            values = snapshot["durations"][name]
            total = sum(values)
            lines.append(f"# TYPE {name} summary")
            lines.append(f"{name}_count {len(values)}")
            lines.append(f"{name}_sum {_fmt(total)}")
        return "\n".join(lines) + ("\n" if lines else "")


def _fmt(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.6f}".rstrip("0").rstrip(".")
