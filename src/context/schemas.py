"""Versioned Structured Health Context schema and validation."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import math
from typing import Any


CONTEXT_SCHEMA_VERSION = "0.1.0"
TIMBRE_ATTRIBUTES = ("sharpness", "roughness", "boominess", "brightness", "depth")

FORBIDDEN_CLAIM_KEYS = {
    "confidence_pct",
    "diagnosis",
    "fault_confidence",
    "pronostia",
    "remaining_useful_life",
    "remaining_useful_life_prediction",
    "root_cause",
    "rul",
    "rul_prediction",
}

REQUIRED_SYSTEM_LIMIT_KEYS = {
    "evidence_only",
    "specific_fault_confirmed",
    "physical_cause_confirmed",
    "remaining_life_prediction_available",
    "paper_equivalent_timbre_accuracy_validated",
    "timbre_direction_accuracy_validated",
    "rank_score_is_confidence",
    "llm_or_rag_grounding_available",
    "limitations",
}


class ContextValidationError(ValueError):
    """Raised when a Structured Health Context payload is invalid."""


def _require_mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ContextValidationError(f"{name} must be an object")
    return value


def _require_keys(mapping: Mapping[str, Any], keys: set[str], name: str) -> None:
    missing = sorted(key for key in keys if key not in mapping)
    if missing:
        raise ContextValidationError(f"{name} missing required keys: {missing}")


def _finite_float(value: Any, name: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ContextValidationError(f"{name} must be finite")
    return result


def _assert_no_forbidden_claim_keys(value: Any, path: str = "$") -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            normalized = str(key).lower()
            if normalized in FORBIDDEN_CLAIM_KEYS:
                raise ContextValidationError(f"unsupported claim key at {path}.{key}")
            _assert_no_forbidden_claim_keys(nested, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _assert_no_forbidden_claim_keys(item, f"{path}[{index}]")


def validate_structured_context(context: Mapping[str, Any]) -> None:
    """Validate the Structured Health Context contract."""
    _assert_no_forbidden_claim_keys(context)
    _require_keys(
        context,
        {"schema_version", "event", "expert_a", "expert_b", "system_limits"},
        "context",
    )
    if context["schema_version"] != CONTEXT_SCHEMA_VERSION:
        raise ContextValidationError(
            f"schema_version must be {CONTEXT_SCHEMA_VERSION}, "
            f"got {context['schema_version']!r}"
        )

    event = _require_mapping(context["event"], "event")
    _require_keys(
        event,
        {"event_id", "asset_id", "machine_type", "machine_id", "snr_tag", "audio_path"},
        "event",
    )
    for key in ("event_id", "asset_id", "machine_type", "machine_id", "snr_tag", "audio_path"):
        if not str(event[key]):
            raise ContextValidationError(f"event.{key} must not be empty")

    expert_a = _require_mapping(context["expert_a"], "expert_a")
    _require_keys(
        expert_a,
        {"expert", "anomaly_score", "threshold", "is_anomaly"},
        "expert_a",
    )
    _finite_float(expert_a["anomaly_score"], "expert_a.anomaly_score")
    _finite_float(expert_a["threshold"], "expert_a.threshold")
    if not isinstance(expert_a["is_anomaly"], bool):
        raise ContextValidationError("expert_a.is_anomaly must be boolean")

    expert_b = _require_mapping(context["expert_b"], "expert_b")
    _require_keys(
        expert_b,
        {"expert", "method", "references", "timbre_rank_scores", "warnings"},
        "expert_b",
    )
    method = _require_mapping(expert_b["method"], "expert_b.method")
    _require_keys(
        method,
        {"status", "embedding_model", "timbre_model", "k", "distance", "rank_threshold"},
        "expert_b.method",
    )
    k = int(method["k"])
    if k <= 0:
        raise ContextValidationError("expert_b.method.k must be positive")

    references = _require_mapping(expert_b["references"], "expert_b.references")
    _require_keys(
        references,
        {"pool_size", "selected_count", "filter", "neighbors"},
        "expert_b.references",
    )
    if int(references["selected_count"]) > int(references["pool_size"]):
        raise ContextValidationError("selected_count cannot exceed pool_size")
    if int(references["selected_count"]) != k:
        raise ContextValidationError("selected_count must match method.k")

    ranks = _require_mapping(expert_b["timbre_rank_scores"], "expert_b.timbre_rank_scores")
    _require_keys(ranks, set(TIMBRE_ATTRIBUTES), "expert_b.timbre_rank_scores")
    for attribute in TIMBRE_ATTRIBUTES:
        row = _require_mapping(ranks[attribute], f"expert_b.timbre_rank_scores.{attribute}")
        _require_keys(
            row,
            {"test_value", "rank_score", "direction", "direction_code"},
            f"expert_b.timbre_rank_scores.{attribute}",
        )
        _finite_float(row["test_value"], f"{attribute}.test_value")
        score = _finite_float(row["rank_score"], f"{attribute}.rank_score")
        if score < 0.0 or score > 1.0:
            raise ContextValidationError(f"{attribute}.rank_score must be in [0, 1]")
        if method["rank_threshold"] is None:
            if row["direction"] is not None or row["direction_code"] is not None:
                raise ContextValidationError(
                    f"{attribute} direction fields must be null when rank_threshold is null"
                )

    warnings = expert_b["warnings"]
    if not isinstance(warnings, list) or not all(isinstance(item, str) for item in warnings):
        raise ContextValidationError("expert_b.warnings must be a list of strings")

    limits = _require_mapping(context["system_limits"], "system_limits")
    _require_keys(limits, REQUIRED_SYSTEM_LIMIT_KEYS, "system_limits")
    for key in REQUIRED_SYSTEM_LIMIT_KEYS - {"limitations"}:
        if not isinstance(limits[key], bool):
            raise ContextValidationError(f"system_limits.{key} must be boolean")
    limitations = limits["limitations"]
    if (
        not isinstance(limitations, Sequence)
        or isinstance(limitations, str)
        or not all(isinstance(item, str) and item for item in limitations)
    ):
        raise ContextValidationError("system_limits.limitations must be a nonempty string list")
