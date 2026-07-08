"""Grounded technician output from context, explanation, and retrieval."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

from context.schemas import TIMBRE_ATTRIBUTES, validate_structured_context
from rag import LocalRetriever, RetrievalResponse, validate_citations

from .diagnostic_agent import explain_context


class MaintenanceGroundingError(ValueError):
    """Raised when maintenance output violates grounding guardrails."""


FORBIDDEN_MAINTENANCE_PATTERNS = (
    re.compile(r"\bRUL\b", re.IGNORECASE),
    re.compile(r"remaining useful life", re.IGNORECASE),
    re.compile(r"time to failure", re.IGNORECASE),
    re.compile(r"\b\d+(?:\.\d+)?\s?%"),
    re.compile(r"\bconfidence\b", re.IGNORECASE),
    re.compile(r"root cause", re.IGNORECASE),
    re.compile(r"\bbearing\b", re.IGNORECASE),
    re.compile(r"will fail", re.IGNORECASE),
    re.compile(r"confirmed (?:fault|failure|component)", re.IGNORECASE),
)


@dataclass
class GroundedMaintenanceAgent:
    """Create source-grounded maintenance communication."""

    retriever: LocalRetriever | None = None

    def generate(
        self,
        context: dict[str, Any],
        *,
        explanation: dict[str, Any] | None = None,
        retrieval: RetrievalResponse | None = None,
    ) -> dict[str, Any]:
        """Build a guarded technician output."""
        validate_structured_context(context)
        explanation = explanation or explain_context(context)
        retrieval = retrieval or self._retrieve_for_context(context)

        event = context["event"]
        recommendation = _build_recommendation(retrieval)
        retrieved_guidance = [result.to_dict() for result in retrieval.results]
        output = {
            "agent": "GroundedMaintenanceAgent",
            "mode": "source_grounded" if recommendation["available"] else "safe_unavailable",
            "event": {
                "event_id": event["event_id"],
                "asset_id": event["asset_id"],
                "machine_type": event["machine_type"],
                "machine_id": event["machine_id"],
                "snr_tag": event["snr_tag"],
            },
            "observed_ml_evidence": _observed_evidence(context),
            "technician_explanation": explanation["explanation"],
            "retrieved_maintenance_guidance": retrieved_guidance,
            "recommendation": recommendation,
            "limitations": [
                "Maintenance recommendation requires retrieved approved-source evidence.",
                "Acoustic evidence is not a component-level finding.",
                "No lifetime estimate is available in the active architecture.",
                "Use retrieved guidance as inspection context only.",
            ],
        }
        validate_maintenance_output(output)
        return output

    def _retrieve_for_context(self, context: dict[str, Any]) -> RetrievalResponse:
        retriever = self.retriever or LocalRetriever()
        return retriever.retrieve(build_retrieval_query(context))


def build_retrieval_query(context: dict[str, Any]) -> str:
    """Build a deterministic maintenance retrieval query from structured context."""
    validate_structured_context(context)
    event = context["event"]
    ranks = context["expert_b"]["timbre_rank_scores"]
    notable_attributes = [
        attribute
        for attribute in TIMBRE_ATTRIBUTES
        if abs(float(ranks[attribute]["rank_score"]) - 0.5) >= 0.3
    ]
    pieces = [
        str(event["machine_type"]),
        "abnormal acoustic noise inspection",
        "mechanical inspection",
    ]
    pieces.extend(notable_attributes)
    return " ".join(pieces)


def validate_maintenance_output(output: dict[str, Any]) -> None:
    """Validate generated maintenance output and citation grounding."""
    recommendation = output.get("recommendation", {})
    retrieved = output.get("retrieved_maintenance_guidance", [])
    retrieved_ids = {row.get("source_id") for row in retrieved if isinstance(row, dict)}
    cited_ids = recommendation.get("citations", [])
    missing = sorted(set(cited_ids) - retrieved_ids)
    if missing:
        raise MaintenanceGroundingError(
            "Recommendation cites non-retrieved source IDs: " + ", ".join(missing)
        )
    generated_text = " ".join(
        _flatten_text(
            {
                "recommendation": recommendation,
                "limitations": output.get("limitations", []),
                "observed_ml_evidence": output.get("observed_ml_evidence", {}),
            }
        )
    )
    for pattern in FORBIDDEN_MAINTENANCE_PATTERNS:
        if pattern.search(generated_text):
            raise MaintenanceGroundingError(
                f"Maintenance output contains forbidden wording: {pattern.pattern}"
            )


def _build_recommendation(retrieval: RetrievalResponse) -> dict[str, Any]:
    if not retrieval.available:
        return {
            "available": False,
            "text": (
                "No source-grounded maintenance recommendation is available because "
                "no approved maintenance source was retrieved."
            ),
            "citations": [],
        }
    citations = list(dict.fromkeys(retrieval.source_ids))
    validate_citations(retrieval, citations)
    return {
        "available": True,
        "text": (
            "Use the retrieved approved guidance as the inspection basis for this "
            "acoustic event, and keep the Expert A/B evidence separate from any "
            "component-level finding."
        ),
        "citations": citations,
    }


def _observed_evidence(context: dict[str, Any]) -> dict[str, Any]:
    expert_a = context["expert_a"]
    ranks = context["expert_b"]["timbre_rank_scores"]
    return {
        "expert_a": {
            "anomaly_score": expert_a["anomaly_score"],
            "threshold": expert_a["threshold"],
            "is_anomaly": expert_a["is_anomaly"],
        },
        "expert_b": {
            attribute: {
                "rank_score": ranks[attribute]["rank_score"],
                "direction": ranks[attribute]["direction"],
            }
            for attribute in TIMBRE_ATTRIBUTES
        },
    }


def _flatten_text(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        rows: list[str] = []
        for nested in value.values():
            rows.extend(_flatten_text(nested))
        return rows
    if isinstance(value, list):
        rows = []
        for nested in value:
            rows.extend(_flatten_text(nested))
        return rows
    return []


def generate_grounded_maintenance_output(
    context: dict[str, Any],
    *,
    explanation: dict[str, Any] | None = None,
    retrieval: RetrievalResponse | None = None,
    retriever: LocalRetriever | None = None,
) -> dict[str, Any]:
    """Convenience wrapper for grounded maintenance output generation."""
    return GroundedMaintenanceAgent(retriever=retriever).generate(
        context,
        explanation=explanation,
        retrieval=retrieval,
    )
