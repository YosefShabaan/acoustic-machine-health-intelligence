"""Grounded technician output from context, explanation, and retrieval."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import json
import re
from typing import Any, Protocol

from context.schemas import TIMBRE_ATTRIBUTES, validate_structured_context
from rag import LocalRetriever, RetrievalResponse, RetrievalResult, validate_citations

from .diagnostic_agent import explain_context


class MaintenanceGroundingError(ValueError):
    """Raised when maintenance output violates grounding guardrails."""


class MaintenanceTextGenerator(Protocol):
    """Optional external generator interface for grounded maintenance actions."""

    def generate(self, prompt: str) -> Any:
        """Return generated structured maintenance output."""


MAINTENANCE_PROMPT_VERSION = "maintenance_actions_v2_gemini_json_2026-07-09"
REQUIRED_MAINTENANCE_KEYS = (
    "event_summary",
    "observed_evidence",
    "inspection_priority",
    "recommended_next_actions",
    "limitations",
)
ACTION_ORIENTATION_PATTERN = re.compile(
    r"\b(inspect|inspection|check|review|verify|compare|record|monitor|observe|examine|clean|lubricat|measure)\b",
    re.IGNORECASE,
)
FORBIDDEN_MAINTENANCE_PATTERNS = (
    re.compile(r"\bRUL\b", re.IGNORECASE),
    re.compile(r"remaining useful life", re.IGNORECASE),
    re.compile(r"time to failure", re.IGNORECASE),
    re.compile(r"\b\d+(?:\.\d+)?\s?%"),
    re.compile(r"\bconfidence\b", re.IGNORECASE),
    re.compile(r"\b(?:fault|failure|component)\s+probability\b", re.IGNORECASE),
    re.compile(r"\bprobability\s+(?:of|that|is|=)\b", re.IGNORECASE),
    re.compile(r"root cause", re.IGNORECASE),
    re.compile(r"\bdiagnos(?:e|is|tic)\b", re.IGNORECASE),
    re.compile(r"\bbearing(?:s)?\s+(?:is|are|has|have|failed|damaged)\b", re.IGNORECASE),
    re.compile(r"\bbearing(?:s)?\s+(?:fault|failure|damage)\b", re.IGNORECASE),
    re.compile(r"will fail", re.IGNORECASE),
    re.compile(r"motor (?:has )?failed", re.IGNORECASE),
    re.compile(r"confirmed (?:fault|failure|component)", re.IGNORECASE),
)


@dataclass
class GroundedMaintenanceAgent:
    """Create source-grounded maintenance communication."""

    retriever: Any | None = None
    generator: MaintenanceTextGenerator | None = None
    retriever_type: str | None = None
    corpus_version: str | None = None

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
        retrieved_guidance = [result.to_dict() for result in retrieval.results]
        retriever_type = self._retriever_type()
        corpus_version = self._corpus_version(retrieval)

        if not retrieval.available:
            output = self._safe_unavailable_output(
                context,
                explanation,
                retrieved_guidance,
                retriever_type=retriever_type,
                corpus_version=corpus_version,
            )
            validate_maintenance_output(output)
            return output

        prompt = build_maintenance_prompt(context, explanation, retrieval)
        metadata_base = {
            "retriever_type": retriever_type,
            "corpus_version": corpus_version,
            "prompt_version": MAINTENANCE_PROMPT_VERSION,
        }
        if self.generator is not None:
            generator_metadata = _generator_metadata(self.generator)
            try:
                generated = self.generator.generate(prompt)
                payload = coerce_maintenance_payload(generated)
                recommendation = _recommendation_from_payload(payload, retrieval)
                metadata = {
                    **metadata_base,
                    "provider": generator_metadata.get("provider", "external_generator"),
                    "model": generator_metadata.get("model"),
                    "generation_mode": generator_metadata.get(
                        "generation_mode",
                        "external_generator",
                    ),
                    "fallback_used": False,
                    "fallback_reason": None,
                }
            except Exception as exc:
                recommendation = _build_fallback_recommendation(retrieval)
                metadata = {
                    **metadata_base,
                    "provider": generator_metadata.get("provider", "external_generator"),
                    "model": generator_metadata.get("model"),
                    "generation_mode": "deterministic_fallback",
                    "fallback_used": True,
                    "fallback_reason": exc.__class__.__name__,
                }
        else:
            recommendation = _build_fallback_recommendation(retrieval)
            metadata = {
                **metadata_base,
                "provider": "deterministic",
                "model": None,
                "generation_mode": "deterministic_fallback",
                "fallback_used": True,
                "fallback_reason": "generator_not_configured",
            }

        output = {
            "agent": "GroundedMaintenanceAgent",
            "mode": "source_grounded",
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
            "limitations": _maintenance_limitations(),
            "metadata": metadata,
            "prompt": prompt,
        }
        validate_maintenance_output(output)
        return output

    def _retrieve_for_context(self, context: dict[str, Any]) -> RetrievalResponse:
        retriever = self.retriever or LocalRetriever()
        return retriever.retrieve(build_retrieval_query(context))

    def _retriever_type(self) -> str:
        if self.retriever_type:
            return self.retriever_type
        if self.retriever is None:
            return "lexical"
        return self.retriever.__class__.__name__

    def _corpus_version(self, retrieval: RetrievalResponse) -> str:
        if self.corpus_version:
            return self.corpus_version
        versions = [result.corpus_version for result in retrieval.results if result.corpus_version]
        return versions[0] if versions else "unversioned"

    def _safe_unavailable_output(
        self,
        context: dict[str, Any],
        explanation: dict[str, Any],
        retrieved_guidance: list[dict[str, Any]],
        *,
        retriever_type: str,
        corpus_version: str,
    ) -> dict[str, Any]:
        event = context["event"]
        return {
            "agent": "GroundedMaintenanceAgent",
            "mode": "safe_unavailable",
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
            "recommendation": {
                "available": False,
                "event_summary": "No source-grounded maintenance action is available.",
                "inspection_priority": "unavailable",
                "recommended_next_actions": [],
                "text": (
                    "No source-grounded maintenance recommendation is available because "
                    "no approved maintenance source was retrieved."
                ),
                "citations": [],
                "chunk_citations": [],
                "limitations": _maintenance_limitations(),
            },
            "limitations": _maintenance_limitations(),
            "metadata": {
                "provider": None,
                "model": None,
                "generation_mode": "safe_unavailable",
                "fallback_used": False,
                "fallback_reason": None,
                "prompt_version": MAINTENANCE_PROMPT_VERSION,
                "retriever_type": retriever_type,
                "corpus_version": corpus_version,
            },
            "prompt": None,
        }


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


def build_maintenance_prompt(
    context: dict[str, Any],
    explanation: dict[str, Any],
    retrieval: RetrievalResponse,
    *,
    max_chunks: int = 5,
) -> str:
    """Build a source-grounded prompt without raw audio."""
    validate_structured_context(context)
    event = context["event"]
    expert_a = context["expert_a"]
    ranks = context["expert_b"]["timbre_rank_scores"]
    rank_lines = "\n".join(
        f"- {attribute}: rank_score={float(ranks[attribute]['rank_score']):.3f}, direction=null"
        for attribute in TIMBRE_ATTRIBUTES
    )
    explanation_payload = explanation.get("explanation", {})
    explanation_lines = "\n".join(
        f"- {item}"
        for item in _flatten_text(
            {
                "summary": explanation_payload.get("summary", ""),
                "observations": explanation_payload.get("observations", []),
                "hypotheses": explanation_payload.get("hypotheses", []),
                "limitations": explanation_payload.get("limitations", []),
            }
        )
        if item
    )
    chunk_lines = "\n\n".join(
        [
            "\n".join(
                [
                    f"source_id: {result.source_id}",
                    f"chunk_id: {result.chunk_id}",
                    f"title: {result.title}",
                    f"section: {result.section_heading}",
                    f"text: {result.snippet}",
                ]
            )
            for result in retrieval.results[:max_chunks]
        ]
    )
    return "\n".join(
        [
            "You are producing cautious maintenance communication for a technician.",
            "Use ONLY the supplied structured ML evidence and retrieved approved maintenance text.",
            "Do not diagnose a failed component. Do not state a physical cause.",
            "Do not state probabilities, percentages, confidence, or remaining-life estimates.",
            "Avoid the words probability, confidence, root cause, diagnosis, failure, failed, RUL, and percent in the output.",
            "Every recommended action must be inspection-oriented and must cite one retrieved source_id and chunk_id.",
            f"Event ID: {event['event_id']}",
            f"Machine: {event['machine_type']} {event['machine_id']} ({event['snr_tag']})",
            (
                "Expert A evidence: "
                f"score={float(expert_a['anomaly_score']):.6f}, "
                f"threshold={float(expert_a['threshold']):.6f}, "
                f"anomaly={expert_a['is_anomaly']}"
            ),
            "Expert B qualitative timbre ranks:",
            rank_lines,
            "Guarded explanation evidence:",
            explanation_lines,
            "Retrieved approved maintenance chunks:",
            chunk_lines,
            "Return only JSON with keys: event_summary, observed_evidence, "
            "inspection_priority, recommended_next_actions, limitations.",
            "Each recommended_next_actions item must have: action, reason, source_id, chunk_id.",
        ]
    )


def coerce_maintenance_payload(generated: Any) -> dict[str, Any]:
    """Coerce a generator response into the target maintenance schema."""
    if isinstance(generated, Mapping):
        payload = dict(generated)
    elif isinstance(generated, str):
        stripped = _strip_json_fence(generated)
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise MaintenanceGroundingError("Maintenance generator did not return JSON") from exc
        if not isinstance(payload, dict):
            raise MaintenanceGroundingError("Maintenance JSON must be an object")
    else:
        raise MaintenanceGroundingError("Maintenance generator returned unsupported type")
    validate_maintenance_payload_shape(payload)
    return payload


def validate_maintenance_payload_shape(payload: Mapping[str, Any]) -> None:
    """Validate generated maintenance action payload shape."""
    for key in REQUIRED_MAINTENANCE_KEYS:
        if key not in payload:
            raise MaintenanceGroundingError(f"Maintenance payload missing required key: {key}")
    if not isinstance(payload["event_summary"], str) or not payload["event_summary"].strip():
        raise MaintenanceGroundingError("event_summary must be a nonempty string")
    if not isinstance(payload["inspection_priority"], str) or not payload["inspection_priority"].strip():
        raise MaintenanceGroundingError("inspection_priority must be a nonempty string")
    for key in ("observed_evidence", "limitations"):
        value = payload[key]
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            raise MaintenanceGroundingError(f"{key} must be a list of strings")
    actions = payload["recommended_next_actions"]
    if not isinstance(actions, list) or not actions:
        raise MaintenanceGroundingError("recommended_next_actions must be a nonempty list")
    for index, action in enumerate(actions):
        if not isinstance(action, Mapping):
            raise MaintenanceGroundingError(f"action {index} must be an object")
        for key in ("action", "reason", "source_id", "chunk_id"):
            if not isinstance(action.get(key), str) or not str(action[key]).strip():
                raise MaintenanceGroundingError(f"action {index} missing nonempty {key}")


def validate_maintenance_output(output: dict[str, Any]) -> None:
    """Validate generated maintenance output and citation grounding."""
    recommendation = output.get("recommendation", {})
    retrieved = output.get("retrieved_maintenance_guidance", [])
    retrieved_ids = {row.get("source_id") for row in retrieved if isinstance(row, dict)}
    retrieved_pairs = {
        (row.get("source_id"), row.get("chunk_id"))
        for row in retrieved
        if isinstance(row, dict)
    }
    cited_ids = recommendation.get("citations", [])
    missing = sorted(set(cited_ids) - retrieved_ids)
    if missing:
        raise MaintenanceGroundingError(
            "Recommendation cites non-retrieved source IDs: " + ", ".join(missing)
        )
    actions = recommendation.get("recommended_next_actions", [])
    if recommendation.get("available"):
        if not actions:
            raise MaintenanceGroundingError("Available recommendation must include actions")
        for action in actions:
            if not isinstance(action, Mapping):
                raise MaintenanceGroundingError("Recommendation action must be an object")
            source_id = action.get("source_id")
            chunk_id = action.get("chunk_id")
            if source_id not in retrieved_ids:
                raise MaintenanceGroundingError(
                    f"Recommendation action cites non-retrieved source_id: {source_id}"
                )
            if (source_id, chunk_id) not in retrieved_pairs:
                raise MaintenanceGroundingError(
                    f"Recommendation action cites non-retrieved chunk_id: {chunk_id}"
                )
            action_text = f"{action.get('action', '')} {action.get('reason', '')}"
            if not ACTION_ORIENTATION_PATTERN.search(action_text):
                raise MaintenanceGroundingError("Recommendation action is not inspection-oriented")
        validate_citations(_retrieval_from_guidance(output), cited_ids)
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


def _recommendation_from_payload(
    payload: Mapping[str, Any],
    retrieval: RetrievalResponse,
) -> dict[str, Any]:
    recommendation = {
        "available": True,
        "event_summary": str(payload["event_summary"]),
        "observed_evidence": list(payload["observed_evidence"]),
        "inspection_priority": str(payload["inspection_priority"]),
        "recommended_next_actions": [
            {
                "action": str(action["action"]),
                "reason": str(action["reason"]),
                "source_id": str(action["source_id"]),
                "chunk_id": str(action["chunk_id"]),
            }
            for action in payload["recommended_next_actions"]
        ],
        "limitations": list(payload["limitations"]),
    }
    _add_citation_summaries(recommendation)
    recommendation["text"] = _recommendation_text(recommendation)
    output = {
        "recommendation": recommendation,
        "retrieved_maintenance_guidance": [result.to_dict() for result in retrieval.results],
        "limitations": _maintenance_limitations(),
        "observed_ml_evidence": {},
    }
    validate_maintenance_output(output)
    return recommendation


def _build_fallback_recommendation(retrieval: RetrievalResponse) -> dict[str, Any]:
    if not retrieval.available:
        return {
            "available": False,
            "event_summary": "No source-grounded maintenance action is available.",
            "inspection_priority": "unavailable",
            "recommended_next_actions": [],
            "text": (
                "No source-grounded maintenance recommendation is available because "
                "no approved maintenance source was retrieved."
            ),
            "citations": [],
            "chunk_citations": [],
            "limitations": _maintenance_limitations(),
        }
    result = retrieval.results[0]
    recommendation = {
        "available": True,
        "event_summary": "The acoustic event should be treated as inspection context only.",
        "observed_evidence": [
            "Expert A/B evidence indicates a changed acoustic pattern, not a component finding.",
        ],
        "inspection_priority": "review retrieved fan maintenance guidance before any follow-up action",
        "recommended_next_actions": [
            {
                "action": "Inspect the fan system using the retrieved approved guidance.",
                "reason": (
                    "The retrieved maintenance chunk provides inspection context for abnormal "
                    "fan acoustic or operating evidence."
                ),
                "source_id": result.source_id,
                "chunk_id": result.chunk_id,
            }
        ],
        "limitations": _maintenance_limitations(),
    }
    _add_citation_summaries(recommendation)
    recommendation["text"] = _recommendation_text(recommendation)
    return recommendation


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


def _generator_metadata(generator: MaintenanceTextGenerator) -> dict[str, Any]:
    metadata_fn = getattr(generator, "metadata", None)
    if callable(metadata_fn):
        metadata = metadata_fn()
        if isinstance(metadata, dict):
            return dict(metadata)
    return {}


def _add_citation_summaries(recommendation: dict[str, Any]) -> None:
    recommendation["citations"] = list(
        dict.fromkeys(action["source_id"] for action in recommendation["recommended_next_actions"])
    )
    recommendation["chunk_citations"] = list(
        dict.fromkeys(action["chunk_id"] for action in recommendation["recommended_next_actions"])
    )


def _recommendation_text(recommendation: Mapping[str, Any]) -> str:
    actions = recommendation.get("recommended_next_actions", [])
    if not actions:
        return str(recommendation.get("event_summary") or "")
    action_text = "; ".join(str(action["action"]) for action in actions)
    return f"{recommendation['event_summary']} Next actions: {action_text}."


def _maintenance_limitations() -> list[str]:
    return [
        "Maintenance output requires retrieved approved-source evidence.",
        "Acoustic evidence is not a component-level finding.",
        "No lifetime estimate is available in the active architecture.",
        "Use retrieved guidance as inspection context only.",
    ]


def _retrieval_from_guidance(output: Mapping[str, Any]) -> RetrievalResponse:
    results = []
    for row in output.get("retrieved_maintenance_guidance", []):
        if not isinstance(row, Mapping):
            continue
        results.append(
            RetrievalResult(
                source_id=str(row.get("source_id", "")),
                title=str(row.get("title", "")),
                version=str(row.get("version", "")),
                chunk_id=str(row.get("chunk_id", "")),
                snippet=str(row.get("snippet", "")),
                score=float(row.get("score", 0.0)),
                path=row.get("path", ""),
                publisher=str(row.get("publisher", "")),
                corpus_version=str(row.get("corpus_version", "")),
                section_id=str(row.get("section_id", "")),
                section_heading=str(row.get("section_heading", "")),
                source_url=str(row["source_url"]) if row.get("source_url") else None,
            )
        )
    return RetrievalResponse(
        query="validated output guidance",
        available=bool(results),
        results=tuple(results),
        message="Reconstructed retrieved guidance for validation.",
    )


def _strip_json_fence(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`").strip()
        if stripped.lower().startswith("json"):
            stripped = stripped[4:].strip()
    return stripped


def _flatten_text(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, Mapping):
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
    retriever: Any | None = None,
    generator: MaintenanceTextGenerator | None = None,
    retriever_type: str | None = None,
    corpus_version: str | None = None,
) -> dict[str, Any]:
    """Convenience wrapper for grounded maintenance output generation."""
    return GroundedMaintenanceAgent(
        retriever=retriever,
        generator=generator,
        retriever_type=retriever_type,
        corpus_version=corpus_version,
    ).generate(
        context,
        explanation=explanation,
        retrieval=retrieval,
    )
