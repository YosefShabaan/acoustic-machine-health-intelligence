"""Run one bounded Fan MVP flow from audio event to technician output."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from time import perf_counter
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import config as cfg  # noqa: E402
from agents import (  # noqa: E402
    explain_context,
    generate_grounded_maintenance_output,
    validate_maintenance_output,
)
from context.translator import context_from_expert_b_output  # noqa: E402
from models.timbre_difference import (  # noqa: E402
    DEFAULT_DISTANCE,
    DEFAULT_K,
    AcousticTimbreDifferenceExpert,
    ExpertABottleneckEmbedder,
)
from rag import LocalRetriever, build_knowledge_base  # noqa: E402
from utils.audio_reference_index import load_reference_index  # noqa: E402

from run_expert_b_smoke import (  # noqa: E402
    _default_index,
    _find_flagged_abnormal,
    score_expert_a,
)


FORBIDDEN_E2E_PATTERNS = (
    re.compile(r"\bRUL\b", re.IGNORECASE),
    re.compile(r"remaining useful life", re.IGNORECASE),
    re.compile(r"time to failure", re.IGNORECASE),
    re.compile(r"\b\d+(?:\.\d+)?\s?%"),
    re.compile(r"\bconfidence\b", re.IGNORECASE),
    re.compile(r"root cause", re.IGNORECASE),
    re.compile(r"\bbearing\b", re.IGNORECASE),
    re.compile(r"will fail", re.IGNORECASE),
)


def default_output_path(machine_type: str, machine_id: str, snr_tag: str) -> Path:
    """Return the machine/SNR-scoped default end-to-end output path."""
    return cfg.PROCESSED_DIR / (
        f"end_to_end_{machine_type}_{machine_id}_{snr_tag}_task10.json"
    )


def should_run_expert_b(expert_a_result: dict[str, Any]) -> bool:
    """Expert B runs only after Expert A flags the same event anomalous."""
    return bool(expert_a_result.get("is_anomaly"))


def validate_end_to_end_output(output: dict[str, Any]) -> None:
    """Validate high-level end-to-end identity and claim guardrails."""
    context = output["structured_context"]
    technician = output["technician_output"]
    event_id = context["event"]["event_id"]
    if technician["event"]["event_id"] != event_id:
        raise ValueError("technician output event_id does not match context event_id")
    if output["expert_b_output"]["input_audio"]["path"] != context["event"]["audio_path"]:
        raise ValueError("Expert B audio path does not match context audio_path")
    if not should_run_expert_b(context["expert_a"]):
        raise ValueError("End-to-end output contains Expert B despite Expert A not flagging anomaly")
    retrieved_ids = {
        row["source_id"]
        for row in technician.get("retrieved_maintenance_guidance", [])
    }
    cited_ids = set(technician.get("recommendation", {}).get("citations", []))
    if not cited_ids.issubset(retrieved_ids):
        missing = sorted(cited_ids - retrieved_ids)
        raise ValueError(f"technician output cites non-retrieved source IDs: {missing}")
    validate_maintenance_output(technician)
    generated_text = json.dumps(
        {
            "recommendation": technician.get("recommendation", {}),
            "limitations": technician.get("limitations", []),
            "observed_ml_evidence": technician.get("observed_ml_evidence", {}),
        }
    )
    for pattern in FORBIDDEN_E2E_PATTERNS:
        if pattern.search(generated_text):
            raise ValueError(f"end-to-end output contains forbidden wording: {pattern.pattern}")


def run_end_to_end(
    *,
    machine_type: str,
    machine_id: str,
    snr_tag: str,
    reference_index_path: Path,
    output_path: Path,
    audio_path: Path | None = None,
    abnormal_dir: Path | None = None,
    max_scan: int = 10,
    k: int = DEFAULT_K,
    distance: str = DEFAULT_DISTANCE,
    use_fixture_maintenance_source: bool = False,
) -> dict[str, Any]:
    """Run one bounded same-event Fan MVP flow."""
    timings: dict[str, float] = {}
    total_start = perf_counter()

    start = perf_counter()
    reference_index = load_reference_index(reference_index_path)
    embedder = ExpertABottleneckEmbedder(snr_tag=snr_tag)
    timings["load_reference_index_and_embedder_seconds"] = perf_counter() - start

    start = perf_counter()
    if audio_path is not None:
        selected_audio = audio_path
        expert_a = score_expert_a(selected_audio, embedder)
        if not should_run_expert_b(expert_a):
            raise ValueError(
                f"Expert A did not flag supplied audio: {selected_audio}; "
                f"score={expert_a['anomaly_score']:.6f}, threshold={expert_a['threshold']:.6f}"
            )
    else:
        selected_audio, expert_a = _find_flagged_abnormal(
            abnormal_dir or (cfg.MIMII_SNR_DIRS[snr_tag] / cfg.MIMII_ABNORMAL_FOLDER),
            embedder,
            max_scan,
        )
    timings["expert_a_select_and_score_seconds"] = perf_counter() - start

    start = perf_counter()
    expert = AcousticTimbreDifferenceExpert(
        reference_index=reference_index,
        embedder=embedder,
        k=k,
        distance=distance,
        rank_threshold=None,
    )
    expert_b_output = expert.characterize(
        audio_path=selected_audio,
        machine_type=machine_type,
        machine_id=machine_id,
        snr_tag=snr_tag,
        expert_a=expert_a,
    )
    timings["expert_b_characterization_seconds"] = perf_counter() - start

    start = perf_counter()
    context = context_from_expert_b_output(expert_b_output)
    timings["context_translation_seconds"] = perf_counter() - start

    start = perf_counter()
    explanation = explain_context(context)
    timings["guarded_explanation_seconds"] = perf_counter() - start

    start = perf_counter()
    retriever = _maintenance_retriever(output_path.parent, use_fixture_maintenance_source)
    retrieval_query = "fan abnormal acoustic noise inspection mounting rotating assembly"
    retrieval = retriever.retrieve(retrieval_query)
    timings["maintenance_retrieval_seconds"] = perf_counter() - start

    start = perf_counter()
    technician_output = generate_grounded_maintenance_output(
        context,
        explanation=explanation,
        retrieval=retrieval,
    )
    timings["maintenance_output_seconds"] = perf_counter() - start
    timings["total_seconds"] = perf_counter() - total_start

    output = {
        "task": "TASK-10",
        "architecture": "Expert A -> Expert B -> Structured Context -> RAG -> guarded technician output",
        "machine_scope": {
            "machine_type": machine_type,
            "machine_id": machine_id,
            "snr_tag": snr_tag,
        },
        "maintenance_source_mode": (
            "approved_fixture_not_production_manual"
            if use_fixture_maintenance_source
            else "production_manuals"
        ),
        "audio_path": str(selected_audio),
        "expert_b_output": expert_b_output,
        "structured_context": context,
        "guarded_explanation": explanation,
        "retrieval": retrieval.to_dict(),
        "technician_output": technician_output,
        "timings": timings,
        "limits": {
            "production_manuals_available": not use_fixture_maintenance_source
            and retrieval.available,
            "rank_scores_are_probabilities": False,
            "physical_cause_confirmed": False,
            "remaining_life_prediction_available": False,
        },
    }
    validate_end_to_end_output(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    return output


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--machine-type", default="fan")
    parser.add_argument("--machine-id", default="id_00")
    parser.add_argument("--snr-tag", default="minus6dB", choices=sorted(cfg.MIMII_SNR_DIRS))
    parser.add_argument("--reference-index", type=Path)
    parser.add_argument("--audio-path", type=Path)
    parser.add_argument("--abnormal-dir", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--k", type=int, default=DEFAULT_K)
    parser.add_argument("--distance", default=DEFAULT_DISTANCE, choices=("euclidean", "cosine"))
    parser.add_argument("--max-scan", type=int, default=10)
    parser.add_argument(
        "--use-fixture-maintenance-source",
        action="store_true",
        help="Use a generated approved local fixture source for a fully cited smoke.",
    )
    return parser.parse_args()


def main() -> None:
    """CLI entrypoint."""
    args = parse_args()
    reference_index_path = args.reference_index or _default_index(
        args.machine_type,
        args.machine_id,
        args.snr_tag,
    )
    output_path = args.output or default_output_path(
        args.machine_type,
        args.machine_id,
        args.snr_tag,
    )
    output = run_end_to_end(
        machine_type=args.machine_type,
        machine_id=args.machine_id,
        snr_tag=args.snr_tag,
        reference_index_path=reference_index_path,
        output_path=output_path,
        audio_path=args.audio_path,
        abnormal_dir=args.abnormal_dir,
        max_scan=args.max_scan,
        k=args.k,
        distance=args.distance,
        use_fixture_maintenance_source=args.use_fixture_maintenance_source,
    )
    technician = output["technician_output"]
    print("END_TO_END_MVP=OK")
    print(f"EVENT_ID={output['structured_context']['event']['event_id']}")
    print(f"AUDIO={output['audio_path']}")
    print(
        "EXPERT_A="
        f"score={output['structured_context']['expert_a']['anomaly_score']:.6f} "
        f"threshold={output['structured_context']['expert_a']['threshold']:.6f} "
        f"is_anomaly={output['structured_context']['expert_a']['is_anomaly']}"
    )
    print(f"EXPERT_B_REFERENCES={output['structured_context']['expert_b']['references']['selected_count']}")
    print(f"MAINTENANCE_MODE={technician['mode']}")
    print(f"RECOMMENDATION_AVAILABLE={technician['recommendation']['available']}")
    print(f"CITATIONS={technician['recommendation']['citations']}")
    print(f"TOTAL_SECONDS={output['timings']['total_seconds']:.6f}")
    print(f"OUTPUT={output_path}")


def _maintenance_retriever(
    output_dir: Path,
    use_fixture_maintenance_source: bool,
) -> LocalRetriever:
    if not use_fixture_maintenance_source:
        return LocalRetriever(build_knowledge_base(cfg.RAG_MANUALS_DIR))
    fixture_dir = output_dir / "task10_fixture_manuals"
    fixture_dir.mkdir(parents=True, exist_ok=True)
    (fixture_dir / "fan_inspection_procedure.md").write_text(
        "Approved TASK-10 fixture. For abnormal fan acoustic noise, inspect "
        "mounting condition, visible looseness, and rotating assembly condition. "
        "Compare findings with normal operating records. This fixture provides "
        "inspection guidance only and does not confirm a component-level finding.",
        encoding="utf-8",
    )
    (fixture_dir / "approved_sources.json").write_text(
        json.dumps(
            {
                "sources": [
                    {
                        "source_id": "task10_fixture_fan_inspection",
                        "title": "TASK-10 Fixture Fan Inspection Procedure",
                        "version": "task10-smoke-v1",
                        "path": "fan_inspection_procedure.md",
                        "approved": True,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    return LocalRetriever(build_knowledge_base(fixture_dir))


if __name__ == "__main__":
    main()
