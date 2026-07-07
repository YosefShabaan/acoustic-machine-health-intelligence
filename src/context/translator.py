"""Translate Expert A/B outputs into Structured Health Context."""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any

import config as cfg
from .schemas import CONTEXT_SCHEMA_VERSION, TIMBRE_ATTRIBUTES, validate_structured_context


def _event_id(machine_type: str, machine_id: str, snr_tag: str, audio_path: str) -> str:
    """Build a stable event identifier from machine scope and audio filename."""
    stem = Path(audio_path).stem
    raw = f"{machine_type}_{machine_id}_{snr_tag}_{stem}"
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", raw)


def _system_limits() -> dict[str, Any]:
    """Return mandatory scientific and product limits for downstream agents."""
    return {
        "evidence_only": True,
        "specific_fault_confirmed": False,
        "physical_cause_confirmed": False,
        "remaining_life_prediction_available": False,
        "paper_equivalent_timbre_accuracy_validated": False,
        "timbre_direction_accuracy_validated": False,
        "rank_score_is_confidence": False,
        "llm_or_rag_grounding_available": False,
        "limitations": [
            "Structured context preserves evidence; it is not a diagnosis.",
            "No five-attribute timbre-difference ground-truth labels are available for the current Fan data.",
            "Expert B rank scores are qualitative relative ranks, not probabilities or confidence.",
            "Expert A bottleneck embeddings are a project adaptation, not a Nishida paper encoder.",
            "No remaining-life prediction is available in the active architecture.",
            "LLM and RAG grounding are not implemented at this stage.",
        ],
    }


def _timbre_rank_scores(expert_b_output: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Copy the five Expert B timbre rows into the context schema."""
    source = expert_b_output["timbre_differences"]
    return {
        attribute: {
            "test_value": float(source[attribute]["test_value"]),
            "rank_score": float(source[attribute]["rank_score"]),
            "direction": source[attribute]["direction"],
            "direction_code": source[attribute]["direction_code"],
        }
        for attribute in TIMBRE_ATTRIBUTES
    }


def context_from_expert_b_output(
    expert_b_output: dict[str, Any],
    *,
    asset_id: str = cfg.ASSET_ID,
    event_id: str | None = None,
) -> dict[str, Any]:
    """Translate one Expert B JSON output into Structured Health Context."""
    input_audio = expert_b_output["input_audio"]
    expert_a = expert_b_output["expert_a"]
    method = expert_b_output["method"]
    references = expert_b_output["references"]
    resolved_event_id = event_id or _event_id(
        str(input_audio["machine_type"]),
        str(input_audio["machine_id"]),
        str(input_audio["snr_tag"]),
        str(input_audio["path"]),
    )

    context = {
        "schema_version": CONTEXT_SCHEMA_VERSION,
        "event": {
            "event_id": resolved_event_id,
            "asset_id": asset_id,
            "machine_type": str(input_audio["machine_type"]),
            "machine_id": str(input_audio["machine_id"]),
            "snr_tag": str(input_audio["snr_tag"]),
            "audio_path": str(input_audio["path"]),
        },
        "expert_a": {
            "expert": "ExpertAAnomalyDetector",
            "anomaly_score": float(expert_a["anomaly_score"]),
            "threshold": float(expert_a["threshold"]),
            "is_anomaly": bool(expert_a["is_anomaly"]),
        },
        "expert_b": {
            "expert": str(expert_b_output["expert"]),
            "method": {
                "paper": method.get("paper"),
                "status": str(method["status"]),
                "embedding_model": str(method["embedding_model"]),
                "embedding_status": method.get("embedding_status"),
                "embedding_metadata": dict(method.get("embedding_metadata", {})),
                "timbre_model": str(method["timbre_model"]),
                "k": int(method["k"]),
                "distance": str(method["distance"]),
                "rank_threshold": method.get("rank_threshold"),
            },
            "references": {
                "pool_size": int(references["pool_size"]),
                "selected_count": int(references["selected_count"]),
                "filter": dict(references["filter"]),
                "neighbors": [
                    {
                        "path": str(neighbor["path"]),
                        "distance": float(neighbor["distance"]),
                        "rank": int(neighbor["rank"]),
                    }
                    for neighbor in references["neighbors"]
                ],
            },
            "timbre_rank_scores": _timbre_rank_scores(expert_b_output),
            "warnings": list(expert_b_output.get("warnings", [])),
        },
        "system_limits": _system_limits(),
    }
    validate_structured_context(context)
    return context


def load_expert_b_output(path: str | Path) -> dict[str, Any]:
    """Load an Expert B JSON output file."""
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_context(context: dict[str, Any], path: str | Path) -> None:
    """Validate and save a Structured Health Context JSON file."""
    validate_structured_context(context)
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(context, handle, indent=2)
