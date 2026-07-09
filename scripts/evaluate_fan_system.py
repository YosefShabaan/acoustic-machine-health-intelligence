"""Run the bounded multi-event Fan system evaluation for TASK-FAN-14."""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
import json
from pathlib import Path
import statistics
import sys
from time import perf_counter
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import config as cfg  # noqa: E402
from models.timbre_difference import DEFAULT_DISTANCE, DEFAULT_K, ExpertABottleneckEmbedder  # noqa: E402
from rag import default_embedding_index_path  # noqa: E402

from run_expert_b_smoke import _default_index, score_expert_a  # noqa: E402
from run_real_intelligence_fan_smoke import (  # noqa: E402
    CORPUS_VERSION,
    default_task10_output_path,
    find_forbidden_claim_hits,
    run_real_intelligence_fan_smoke,
)


TASK_ID = "TASK-FAN-14"
REFERENCE_SMOKE_AUDIO_NAME = "00000002.wav"
GEMINI_CALLS_PER_CONTINUATION = 3


@dataclass(frozen=True)
class SelectedEvent:
    """One bounded evaluation event selected for TASK-FAN-14."""

    event_index: int
    label: str
    audio_path: Path
    expert_a: dict[str, Any]
    expert_a_seconds: float
    selection_note: str

    @property
    def event_id(self) -> str:
        """Return the stable project event ID for this Fan event."""
        return f"fan_id_00_minus6dB_{self.audio_path.stem}"

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-serializable selection metadata."""
        return {
            "event_index": self.event_index,
            "label": self.label,
            "event_id": self.event_id,
            "audio_path": str(self.audio_path),
            "audio_name": self.audio_path.name,
            "expert_a": self.expert_a,
            "expert_a_seconds": self.expert_a_seconds,
            "selection_note": self.selection_note,
        }


def default_output_path(machine_type: str, machine_id: str, snr_tag: str) -> Path:
    """Return the external TASK-FAN-14 evaluation artifact path."""
    return cfg.PROCESSED_DIR / (
        f"fan_system_evaluation_{machine_type}_{machine_id}_{snr_tag}_task_fan_14.json"
    )


def default_event_output_dir(machine_type: str, machine_id: str, snr_tag: str) -> Path:
    """Return external per-continuation event output directory."""
    return cfg.PROCESSED_DIR / (
        f"fan_system_evaluation_{machine_type}_{machine_id}_{snr_tag}_task_fan_14_events"
    )


def select_bounded_event_set(
    *,
    normal_dir: Path,
    abnormal_dir: Path,
    embedder: ExpertABottleneckEmbedder,
    count_per_class: int = 10,
    exclude_abnormal_names: tuple[str, ...] = (REFERENCE_SMOKE_AUDIO_NAME,),
) -> tuple[list[SelectedEvent], dict[str, Any]]:
    """Select 10 normal events plus 10 Expert A-flagged abnormal events.

    This is an integration stress set, not a detection-accuracy sample. The
    abnormal side intentionally selects events that continue past Expert A so
    the downstream intelligence path is exercised multiple times.
    """
    if count_per_class <= 0:
        raise ValueError("count_per_class must be positive")

    normal_paths = sorted(normal_dir.glob("*.wav"), key=lambda path: path.name)
    abnormal_paths = sorted(abnormal_dir.glob("*.wav"), key=lambda path: path.name)
    if len(normal_paths) < count_per_class:
        raise ValueError(f"Need at least {count_per_class} normal events")

    normal_rows: list[SelectedEvent] = []
    abnormal_rows: list[SelectedEvent] = []
    normal_score_seconds = 0.0
    abnormal_scan_seconds = 0.0
    abnormal_scanned = 0

    for path in normal_paths[:count_per_class]:
        start = perf_counter()
        expert_a = score_expert_a(path, embedder)
        elapsed = perf_counter() - start
        normal_score_seconds += elapsed
        normal_rows.append(
            SelectedEvent(
                event_index=-1,
                label="normal",
                audio_path=path,
                expert_a=expert_a,
                expert_a_seconds=elapsed,
                selection_note="first_10_normal_lexicographic",
            )
        )

    excluded = set(exclude_abnormal_names)
    for path in abnormal_paths:
        abnormal_scanned += 1
        start = perf_counter()
        expert_a = score_expert_a(path, embedder)
        elapsed = perf_counter() - start
        abnormal_scan_seconds += elapsed
        if path.name in excluded:
            continue
        if expert_a["is_anomaly"]:
            abnormal_rows.append(
                SelectedEvent(
                    event_index=-1,
                    label="abnormal",
                    audio_path=path,
                    expert_a=expert_a,
                    expert_a_seconds=elapsed,
                    selection_note=(
                        "first_10_expert_a_flagged_abnormal_lexicographic_"
                        "excluding_task_fan_13_reference"
                    ),
                )
            )
            if len(abnormal_rows) >= count_per_class:
                break
    if len(abnormal_rows) < count_per_class:
        raise ValueError(
            f"Only found {len(abnormal_rows)} Expert A-flagged abnormal events"
        )

    ordered = interleave_event_rows(normal_rows, abnormal_rows)
    indexed = [
        SelectedEvent(
            event_index=index,
            label=row.label,
            audio_path=row.audio_path,
            expert_a=row.expert_a,
            expert_a_seconds=row.expert_a_seconds,
            selection_note=row.selection_note,
        )
        for index, row in enumerate(ordered, start=1)
    ]
    metadata = {
        "policy": (
            "normal: first 10 lexicographic Fan id_00 minus6dB normal WAVs; "
            "abnormal: first 10 Expert A-flagged lexicographic Fan id_00 "
            "minus6dB abnormal WAVs, excluding the TASK-FAN-13 reference event "
            "to avoid duplicate Gemini calls"
        ),
        "purpose": (
            "bounded downstream integration stress set; not Expert A recall, "
            "fault diagnosis, or production-maintenance validation"
        ),
        "normal_candidates_used": count_per_class,
        "abnormal_candidates_scanned": abnormal_scanned,
        "excluded_abnormal_names": sorted(excluded),
        "normal_score_seconds": normal_score_seconds,
        "abnormal_scan_seconds": abnormal_scan_seconds,
    }
    return indexed, metadata


def interleave_event_rows(
    normal_rows: list[SelectedEvent],
    abnormal_rows: list[SelectedEvent],
) -> list[SelectedEvent]:
    """Interleave normal and abnormal rows for timing and reporting."""
    rows: list[SelectedEvent] = []
    for normal, abnormal in zip(normal_rows, abnormal_rows):
        rows.extend([normal, abnormal])
    rows.extend(normal_rows[len(abnormal_rows):])
    rows.extend(abnormal_rows[len(normal_rows):])
    return rows


def build_preflight(
    *,
    events: list[SelectedEvent],
    selection_metadata: dict[str, Any],
    reference_smoke_path: Path,
    max_live_continuations: int,
) -> dict[str, Any]:
    """Build the required timing/cost preflight before live continuations."""
    reference = load_reference_smoke_timing(reference_smoke_path)
    flagged_count = sum(1 for event in events if event.expert_a["is_anomaly"])
    first_three = events[:3]
    first_three_flagged = sum(1 for event in first_three if event.expert_a["is_anomaly"])
    expert_a_total = sum(float(event.expert_a_seconds) for event in events)
    continuation_seconds = reference.get("continuation_seconds_estimate")
    estimated_total_seconds = None
    if continuation_seconds is not None:
        estimated_total_seconds = expert_a_total + flagged_count * continuation_seconds
    estimated_gemini_calls = flagged_count * GEMINI_CALLS_PER_CONTINUATION
    return {
        "unit_tests_required_before_live_run": True,
        "one_event_timing_source": str(reference_smoke_path),
        "one_event_timing": reference,
        "three_event_timing_cost_estimate": {
            "event_ids": [event.event_id for event in first_three],
            "expert_a_seconds": sum(float(event.expert_a_seconds) for event in first_three),
            "flagged_count": first_three_flagged,
            "estimated_gemini_calls": first_three_flagged * GEMINI_CALLS_PER_CONTINUATION,
        },
        "full_live_estimate": {
            "event_count": len(events),
            "expert_a_flagged_count": flagged_count,
            "estimated_gemini_calls": estimated_gemini_calls,
            "estimated_total_seconds": estimated_total_seconds,
            "max_live_continuations": max_live_continuations,
            "reasonable_for_live_run": flagged_count <= max_live_continuations,
        },
        "api_quota_rate_handling_review": {
            "sequential_calls": True,
            "duplicate_task_fan_13_event_excluded": True,
            "gemini_calls_per_continuation": GEMINI_CALLS_PER_CONTINUATION,
            "no_parallel_gemini_burst": True,
            "fallbacks_counted_not_hidden": True,
            "downgrade_policy": (
                "If Expert A continuation count exceeds max_live_continuations, "
                "stop before live generation and require an explicit bounded subset."
            ),
        },
        "selection": selection_metadata,
    }


def load_reference_smoke_timing(path: Path) -> dict[str, Any]:
    """Load compact timing metadata from the TASK-FAN-13 smoke artifact."""
    if not path.is_file():
        return {
            "available": False,
            "continuation_seconds_estimate": None,
            "message": "TASK-FAN-13 timing artifact was not found.",
        }
    payload = json.loads(path.read_text(encoding="utf-8"))
    timings = payload.get("timings", {})
    total = timings.get("total_seconds")
    expert_a = timings.get("audio_expert_a_seconds", 0.0)
    continuation = None
    if total is not None:
        continuation = float(total) - float(expert_a or 0.0)
    return {
        "available": True,
        "event_id": payload.get("structured_context", {}).get("event", {}).get("event_id"),
        "total_seconds": total,
        "audio_expert_a_seconds": expert_a,
        "continuation_seconds_estimate": continuation,
        "gemini_explanation_seconds": timings.get("gemini_explanation_seconds"),
        "retrieval_seconds": timings.get("retrieval_seconds"),
        "gemini_maintenance_seconds": timings.get("gemini_maintenance_seconds"),
    }


def run_bounded_fan_system_evaluation(
    *,
    machine_type: str,
    machine_id: str,
    snr_tag: str,
    reference_index_path: Path,
    semantic_index_path: Path,
    output_path: Path,
    event_output_dir: Path,
    max_live_continuations: int = 10,
    count_per_class: int = 10,
) -> dict[str, Any]:
    """Run TASK-FAN-14 on the bounded 20-event Fan integration set."""
    total_start = perf_counter()
    embedder = ExpertABottleneckEmbedder(snr_tag=snr_tag)
    events, selection_metadata = select_bounded_event_set(
        normal_dir=cfg.MIMII_SNR_DIRS[snr_tag] / cfg.MIMII_NORMAL_FOLDER,
        abnormal_dir=cfg.MIMII_SNR_DIRS[snr_tag] / cfg.MIMII_ABNORMAL_FOLDER,
        embedder=embedder,
        count_per_class=count_per_class,
    )
    preflight = build_preflight(
        events=events,
        selection_metadata=selection_metadata,
        reference_smoke_path=cfg.PROCESSED_DIR
        / f"real_intelligence_end_to_end_{machine_type}_{machine_id}_{snr_tag}_task_fan_13.json",
        max_live_continuations=max_live_continuations,
    )
    if not preflight["full_live_estimate"]["reasonable_for_live_run"]:
        raise RuntimeError(
            "Estimated live continuation count exceeds max_live_continuations; "
            "explicit bounded subset approval is required."
        )

    event_output_dir.mkdir(parents=True, exist_ok=True)
    event_results: list[dict[str, Any]] = []
    live_continuations = 0
    for event in events:
        if not event.expert_a["is_anomaly"]:
            event_results.append(unflagged_event_result(event))
            continue
        live_continuations += 1
        event_output = event_output_dir / f"{event.event_id}_task_fan_14.json"
        event_start = perf_counter()
        try:
            output = run_real_intelligence_fan_smoke(
                machine_type=machine_type,
                machine_id=machine_id,
                snr_tag=snr_tag,
                reference_index_path=reference_index_path,
                semantic_index_path=semantic_index_path,
                audio_path=event.audio_path,
                output_path=event_output,
                old_task10_output_path=default_task10_output_path(
                    machine_type,
                    machine_id,
                    snr_tag,
                ),
                k=DEFAULT_K,
                distance=DEFAULT_DISTANCE,
                retrieval_top_k=3,
                require_live_gemini=False,
                task_id=TASK_ID,
            )
            event_results.append(continued_event_result(event, output, event_start))
        except Exception as exc:
            event_results.append(
                {
                    **event.to_dict(),
                    "status": "pipeline_failed",
                    "pipeline_failed": True,
                    "error_type": exc.__class__.__name__,
                    "error_message": str(exc),
                    "wall_seconds": perf_counter() - event_start,
                }
            )

    evaluation = {
        "task": TASK_ID,
        "machine_scope": {
            "machine_type": machine_type,
            "machine_id": machine_id,
            "snr_tag": snr_tag,
        },
        "selection_policy": selection_metadata,
        "preflight": preflight,
        "events": event_results,
        "summary": summarize_evaluation(event_results),
        "limits": {
            "not_expert_a_retraining": True,
            "not_expert_b_direction_accuracy": True,
            "not_fault_diagnosis_accuracy": True,
            "not_production_maintenance_validation": True,
            "not_multi_machine_generalization": True,
            "rank_scores_are_probabilities": False,
            "remaining_life_prediction_available": False,
        },
        "runtime": {
            "total_wall_seconds": perf_counter() - total_start,
            "live_continuations_requested": live_continuations,
        },
    }
    validate_fan_system_evaluation(evaluation)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(evaluation, indent=2), encoding="utf-8")
    return evaluation


def unflagged_event_result(event: SelectedEvent) -> dict[str, Any]:
    """Return result row for an event gated out by Expert A."""
    return {
        **event.to_dict(),
        "status": "expert_a_not_flagged",
        "expert_b_ran": False,
        "pipeline_completed": False,
        "pipeline_failed": False,
        "same_audio_identity_success": None,
        "context_validation_success": None,
        "retrieval_available": None,
        "gemini_explanation_success": None,
        "gemini_explanation_fallback_used": None,
        "maintenance_generation_success": None,
        "maintenance_fallback_used": None,
        "citation_validation_failed": False,
        "forbidden_claim_hits": [],
        "timings": {
            "expert_a_seconds": event.expert_a_seconds,
        },
    }


def continued_event_result(
    event: SelectedEvent,
    output: dict[str, Any],
    event_start: float,
) -> dict[str, Any]:
    """Return result row for an event that completed the intelligence path."""
    context = output["structured_context"]
    technician = output["technician_output"]
    explanation_metadata = output["guarded_explanation"]["metadata"]
    maintenance_metadata = technician["metadata"]
    first_result = output["retrieval"]["results"][0] if output["retrieval"]["results"] else {}
    return {
        **event.to_dict(),
        "status": "pipeline_completed",
        "expert_b_ran": True,
        "pipeline_completed": True,
        "pipeline_failed": False,
        "same_audio_identity_success": (
            context["event"]["audio_path"] == output["audio_path"]
            and output["expert_b_output"]["input_audio"]["path"] == output["audio_path"]
        ),
        "context_validation_success": context["schema_version"] == "0.2.0",
        "retrieval_available": bool(output["retrieval"]["available"]),
        "retrieval_top_source_id": first_result.get("source_id"),
        "retrieval_top_chunk_id": first_result.get("chunk_id"),
        "retrieved_source_chunk_pairs": [
            {
                "source_id": row["source_id"],
                "chunk_id": row["chunk_id"],
                "score": row["score"],
            }
            for row in output["retrieval"]["results"]
        ],
        "gemini_explanation_success": (
            explanation_metadata.get("generation_mode") == "live_gemini"
            and not explanation_metadata.get("fallback_used")
        ),
        "gemini_explanation_fallback_used": bool(explanation_metadata.get("fallback_used")),
        "maintenance_generation_success": (
            maintenance_metadata.get("generation_mode") == "live_gemini"
            and not maintenance_metadata.get("fallback_used")
        ),
        "maintenance_fallback_used": bool(maintenance_metadata.get("fallback_used")),
        "maintenance_action_count": len(
            technician["recommendation"].get("recommended_next_actions", [])
        ),
        "citation_validation_failed": False,
        "forbidden_claim_hits": find_forbidden_claim_hits(output),
        "analysis_run_id": context["analysis"]["analysis_run_id"],
        "event_output_path": str(output.get("output_path", "")),
        "timings": output["timings"],
        "wall_seconds": perf_counter() - event_start,
    }


def summarize_evaluation(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize bounded Fan system evaluation results."""
    flagged = [event for event in events if event["expert_a"]["is_anomaly"]]
    completed = [event for event in events if event.get("pipeline_completed")]
    failures = [event for event in events if event.get("pipeline_failed")]
    top_sources = Counter(
        event.get("retrieval_top_source_id")
        for event in completed
        if event.get("retrieval_top_source_id")
    )
    stage_latency = summarize_stage_latencies(events)
    return {
        "total_events": len(events),
        "normal_events": sum(1 for event in events if event["label"] == "normal"),
        "abnormal_events": sum(1 for event in events if event["label"] == "abnormal"),
        "expert_a_flagged_count": len(flagged),
        "expert_b_execution_count": sum(1 for event in events if event.get("expert_b_ran")),
        "same_audio_identity_success": sum(
            1 for event in completed if event.get("same_audio_identity_success")
        ),
        "context_validation_success": sum(
            1 for event in completed if event.get("context_validation_success")
        ),
        "retrieval_available": sum(1 for event in completed if event.get("retrieval_available")),
        "retrieval_top_source_distribution": dict(sorted(top_sources.items())),
        "gemini_explanation_success": sum(
            1 for event in completed if event.get("gemini_explanation_success")
        ),
        "gemini_explanation_fallback_count": sum(
            1 for event in completed if event.get("gemini_explanation_fallback_used")
        ),
        "maintenance_generation_success": sum(
            1 for event in completed if event.get("maintenance_generation_success")
        ),
        "maintenance_fallback_count": sum(
            1 for event in completed if event.get("maintenance_fallback_used")
        ),
        "citation_validation_failures": sum(
            1 for event in events if event.get("citation_validation_failed")
        ),
        "pipeline_failures": len(failures),
        "forbidden_claim_failure_count": sum(
            1 for event in events if event.get("forbidden_claim_hits")
        ),
        "per_stage_latency_seconds": stage_latency,
    }


def summarize_stage_latencies(events: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    """Return min/mean/max latency by stage across event rows."""
    values: dict[str, list[float]] = {}
    for event in events:
        timings = event.get("timings", {})
        for key, value in timings.items():
            if isinstance(value, (int, float)):
                values.setdefault(key, []).append(float(value))
    summary: dict[str, dict[str, float]] = {}
    for key, rows in values.items():
        summary[key] = {
            "count": len(rows),
            "min": min(rows),
            "mean": statistics.fmean(rows),
            "max": max(rows),
        }
    return summary


def validate_fan_system_evaluation(evaluation: dict[str, Any]) -> None:
    """Validate bounded evaluation shape and core scientific guardrails."""
    if evaluation.get("task") != TASK_ID:
        raise ValueError(f"evaluation task must be {TASK_ID}")
    summary = evaluation["summary"]
    if summary["total_events"] != 20:
        raise ValueError("TASK-FAN-14 evaluation must contain 20 events")
    if summary["normal_events"] != 10 or summary["abnormal_events"] != 10:
        raise ValueError("TASK-FAN-14 must contain 10 normal and 10 abnormal events")
    for event in evaluation["events"]:
        if event.get("expert_b_ran") and not event["expert_a"]["is_anomaly"]:
            raise ValueError("Expert B ran for an event not flagged by Expert A")
        if event.get("pipeline_completed"):
            if not event.get("same_audio_identity_success"):
                raise ValueError("same-audio identity failed for a completed event")
            if not event.get("context_validation_success"):
                raise ValueError("context validation failed for a completed event")
            if not event.get("retrieval_available"):
                raise ValueError("retrieval unavailable for a completed event")
            if event.get("citation_validation_failed"):
                raise ValueError("citation validation failed for a completed event")
            if event.get("forbidden_claim_hits"):
                raise ValueError("forbidden claim pattern found in completed event")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--machine-type", default="fan")
    parser.add_argument("--machine-id", default="id_00")
    parser.add_argument("--snr-tag", default="minus6dB", choices=sorted(cfg.MIMII_SNR_DIRS))
    parser.add_argument("--reference-index", type=Path)
    parser.add_argument("--semantic-index", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--event-output-dir", type=Path)
    parser.add_argument("--max-live-continuations", type=int, default=10)
    return parser.parse_args()


def main() -> None:
    """CLI entrypoint."""
    args = parse_args()
    reference_index_path = args.reference_index or _default_index(
        args.machine_type,
        args.machine_id,
        args.snr_tag,
    )
    semantic_index_path = args.semantic_index or default_embedding_index_path(CORPUS_VERSION)
    output_path = args.output or default_output_path(
        args.machine_type,
        args.machine_id,
        args.snr_tag,
    )
    event_output_dir = args.event_output_dir or default_event_output_dir(
        args.machine_type,
        args.machine_id,
        args.snr_tag,
    )
    evaluation = run_bounded_fan_system_evaluation(
        machine_type=args.machine_type,
        machine_id=args.machine_id,
        snr_tag=args.snr_tag,
        reference_index_path=reference_index_path,
        semantic_index_path=semantic_index_path,
        output_path=output_path,
        event_output_dir=event_output_dir,
        max_live_continuations=args.max_live_continuations,
    )
    summary = evaluation["summary"]
    print("FAN_SYSTEM_EVALUATION=OK")
    print(f"EVENTS={summary['total_events']}")
    print(f"NORMAL_EVENTS={summary['normal_events']}")
    print(f"ABNORMAL_EVENTS={summary['abnormal_events']}")
    print(f"EXPERT_A_FLAGGED={summary['expert_a_flagged_count']}")
    print(f"EXPERT_B_RUNS={summary['expert_b_execution_count']}")
    print(f"PIPELINE_FAILURES={summary['pipeline_failures']}")
    print(f"EXPLANATION_FALLBACKS={summary['gemini_explanation_fallback_count']}")
    print(f"MAINTENANCE_FALLBACKS={summary['maintenance_fallback_count']}")
    print(f"CITATION_FAILURES={summary['citation_validation_failures']}")
    print(f"TOP_SOURCES={summary['retrieval_top_source_distribution']}")
    print(f"TOTAL_SECONDS={evaluation['runtime']['total_wall_seconds']:.6f}")
    print(f"OUTPUT={output_path}")


if __name__ == "__main__":
    main()
