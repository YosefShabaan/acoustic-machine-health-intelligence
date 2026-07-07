"""Guardrailed technician-facing explanation agent."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Protocol

from context.schemas import TIMBRE_ATTRIBUTES, validate_structured_context


class ExplanationGuardrailError(ValueError):
    """Raised when generated explanation text violates project guardrails."""


class TextGenerator(Protocol):
    """Optional external text generator interface."""

    def generate(self, prompt: str) -> str:
        """Return generated text for a guarded prompt."""


FORBIDDEN_TEXT_PATTERNS = (
    re.compile(r"\bRUL\b", re.IGNORECASE),
    re.compile(r"remaining useful life", re.IGNORECASE),
    re.compile(r"time to failure", re.IGNORECASE),
    re.compile(r"\b\d+(?:\.\d+)?\s?%"),
    re.compile(r"\bconfidence\b", re.IGNORECASE),
    re.compile(r"root cause", re.IGNORECASE),
    re.compile(r"\bdiagnosis\b", re.IGNORECASE),
    re.compile(r"\bbearing\b", re.IGNORECASE),
    re.compile(r"motor (?:has )?failed", re.IGNORECASE),
    re.compile(r"will fail", re.IGNORECASE),
)


def _rank_phrase(score: float) -> str:
    """Convert a rank score into qualitative relative-rank language."""
    if score <= 0.2:
        return "low relative rank"
    if score >= 0.8:
        return "high relative rank"
    if 0.4 <= score <= 0.6:
        return "near the local reference middle"
    if score < 0.4:
        return "below the local reference middle"
    return "above the local reference middle"


def _rank_observations(context: dict[str, Any]) -> list[str]:
    """Build deterministic Expert B rank observations."""
    ranks = context["expert_b"]["timbre_rank_scores"]
    rows = []
    for attribute in TIMBRE_ATTRIBUTES:
        score = float(ranks[attribute]["rank_score"])
        rows.append((attribute, abs(score - 0.5), score, _rank_phrase(score)))
    rows.sort(key=lambda row: row[1], reverse=True)
    return [
        f"{attribute}: rank_score={score:.3f}, {phrase} among selected normal references."
        for attribute, _, score, phrase in rows
    ]


def validate_explanation_text(text: str) -> None:
    """Reject explanation text that contains unsupported claims."""
    for pattern in FORBIDDEN_TEXT_PATTERNS:
        if pattern.search(text):
            raise ExplanationGuardrailError(
                f"Explanation contains forbidden wording: {pattern.pattern}"
            )


def build_guarded_prompt(context: dict[str, Any]) -> str:
    """Build a bounded prompt from Structured Health Context without raw audio."""
    validate_structured_context(context)
    event = context["event"]
    expert_a = context["expert_a"]
    expert_b = context["expert_b"]
    observations = "\n".join(f"- {item}" for item in _rank_observations(context))
    return "\n".join(
        [
            "You are explaining structured machine-health evidence to a technician.",
            "Use only the supplied structured evidence. Do not infer component failures.",
            "Do not use raw audio. Do not state probabilities, percentages, or remaining-life estimates.",
            f"Event ID: {event['event_id']}",
            f"Machine: {event['machine_type']} {event['machine_id']} ({event['snr_tag']})",
            (
                "Expert A: "
                f"score={expert_a['anomaly_score']:.6f}, "
                f"threshold={expert_a['threshold']:.6f}, "
                f"anomaly={expert_a['is_anomaly']}"
            ),
            (
                "Expert B: "
                f"{expert_b['method']['status']}, "
                f"{expert_b['references']['selected_count']} selected normal references, "
                f"rank_threshold={expert_b['method']['rank_threshold']}"
            ),
            "Timbre rank observations:",
            observations,
            "Required limits: qualitative ranks only; no component-level finding; no remaining-life estimate.",
        ]
    )


@dataclass
class DiagnosticExplanationAgent:
    """Generate cautious explanation text from Structured Health Context."""

    generator: TextGenerator | None = None

    def explain(self, context: dict[str, Any]) -> dict[str, Any]:
        """Return a JSON-serializable guarded explanation result."""
        prompt = build_guarded_prompt(context)
        if self.generator is not None:
            text = self.generator.generate(prompt)
            validate_explanation_text(text)
            return {
                "agent": "DiagnosticExplanationAgent",
                "mode": "external_generator",
                "prompt": prompt,
                "explanation": {
                    "summary": text,
                    "observations": [],
                    "limitations": [],
                    "hypotheses": [],
                    "inspection_notes": [],
                },
            }

        expert_a = context["expert_a"]
        expert_b = context["expert_b"]
        event = context["event"]
        observations = [
            (
                f"Expert A flagged event {event['event_id']} as anomalous: "
                f"score {expert_a['anomaly_score']:.6f} exceeded threshold "
                f"{expert_a['threshold']:.6f}."
            ),
            (
                "Expert B compared the same event with "
                f"{expert_b['references']['selected_count']} selected normal references "
                f"from the same machine and SNR scope."
            ),
            *_rank_observations(context),
        ]
        limitations = [
            "Expert B rank scores are qualitative local ranks, not probabilities.",
            "No five-attribute timbre labels are available for this Fan dataset.",
            "The embedding model is a project adaptation, not a paper encoder.",
            "No remaining-life estimate or physical cause confirmation is available.",
            "No retrieval-grounded maintenance source has been applied yet.",
        ]
        hypotheses = [
            (
                "The acoustic evidence may indicate a changed operating sound pattern "
                "relative to the selected normal references."
            ),
            (
                "The high relative ranks for sharpness, roughness, and brightness can guide "
                "what to listen for during inspection, but they do not identify a failed component."
            ),
        ]
        inspection_notes = [
            "Use the acoustic differences as inspection context, not as a component-level finding.",
            "Prioritize listening, mechanical inspection, and comparison with normal operating recordings.",
        ]
        summary = (
            "The fan audio event was flagged as acoustically anomalous. "
            "Relative to selected normal recordings from the same machine and SNR condition, "
            "Expert B found notable timbre-rank differences. These are acoustic evidence only."
        )
        result = {
            "agent": "DiagnosticExplanationAgent",
            "mode": "deterministic_offline",
            "prompt": prompt,
            "explanation": {
                "summary": summary,
                "observations": observations,
                "limitations": limitations,
                "hypotheses": hypotheses,
                "inspection_notes": inspection_notes,
            },
        }
        validate_explanation_text(" ".join(_flatten_text(result["explanation"])))
        return result


def _flatten_text(value: Any) -> list[str]:
    """Collect strings from a nested explanation payload."""
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


def explain_context(
    context: dict[str, Any],
    *,
    generator: TextGenerator | None = None,
) -> dict[str, Any]:
    """Convenience wrapper for deterministic or mockable explanation generation."""
    return DiagnosticExplanationAgent(generator=generator).explain(context)
