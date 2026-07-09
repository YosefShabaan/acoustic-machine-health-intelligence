"""Run the real Gemini + semantic RAG Fan smoke for TASK-FAN-13."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
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
    GeminiMaintenanceTextGenerator,
    GeminiTextGenerator,
    build_retrieval_query,
    explain_context,
    generate_grounded_maintenance_output,
    validate_maintenance_output,
)
from context.schemas import CONTEXT_SCHEMA_VERSION, TIMBRE_ATTRIBUTES, validate_structured_context  # noqa: E402
from context.translator import context_from_expert_b_output  # noqa: E402
from models.timbre_difference import (  # noqa: E402
    DEFAULT_DISTANCE,
    DEFAULT_K,
    AcousticTimbreDifferenceExpert,
    ExpertABottleneckEmbedder,
)
from rag import (  # noqa: E402
    GeminiEmbeddingProvider,
    SemanticRetriever,
    default_embedding_index_path,
    load_embedding_index,
)
from utils.audio_reference_index import load_reference_index  # noqa: E402

from run_expert_b_smoke import _default_index, score_expert_a  # noqa: E402


CORPUS_VERSION = "AMHI-FAN-MAINT-KB-v1"
TASK_ID = "TASK-FAN-13"

FORBIDDEN_REAL_INTELLIGENCE_PATTERNS = (
    re.compile(r"\bRUL\b", re.IGNORECASE),
    re.compile(r"remaining useful life", re.IGNORECASE),
    re.compile(r"time to failure", re.IGNORECASE),
    re.compile(r"\b\d+(?:\.\d+)?\s?%"),
    re.compile(r"\bconfidence\b", re.IGNORECASE),
    re.compile(r"\b(?:fault|failure|component)\s+probability\b", re.IGNORECASE),
    re.compile(r"\bprobability\s+(?:of|that|is|=)\b", re.IGNORECASE),
    re.compile(r"root[- ]cause", re.IGNORECASE),
    re.compile(r"\bdiagnos(?:e|is|tic)\b", re.IGNORECASE),
    re.compile(r"\bbearing(?:s)?\s+(?:is|are|has|have|failed|damaged)\b", re.IGNORECASE),
    re.compile(r"\bbearing(?:s)?\s+(?:fault|failure|damage)\b", re.IGNORECASE),
    re.compile(r"will fail", re.IGNORECASE),
    re.compile(r"motor (?:has )?failed", re.IGNORECASE),
    re.compile(r"confirmed (?:fault|failure|component)", re.IGNORECASE),
)


def default_audio_path(snr_tag: str) -> Path:
    """Return the bounded Fan reference abnormal event path."""
    return cfg.MIMII_SNR_DIRS[snr_tag] / cfg.MIMII_ABNORMAL_FOLDER / "00000002.wav"


def default_output_path(machine_type: str, machine_id: str, snr_tag: str) -> Path:
    """Return the external TASK-FAN-13 artifact path."""
    return cfg.PROCESSED_DIR / (
        f"real_intelligence_end_to_end_{machine_type}_{machine_id}_{snr_tag}_"
        "task_fan_13.json"
    )


def default_task10_output_path(machine_type: str, machine_id: str, snr_tag: str) -> Path:
    """Return the earlier TASK-10 artifact path used for bounded comparison."""
    return cfg.PROCESSED_DIR / f"end_to_end_{machine_type}_{machine_id}_{snr_tag}_task10.json"


def find_forbidden_claim_hits(output: dict[str, Any]) -> list[str]:
    """Return forbidden claim-pattern hits in generated user-facing payloads."""
    text = json.dumps(
        {
            "guarded_explanation": output.get("guarded_explanation", {}).get(
                "explanation",
                {},
            ),
            "technician_explanation": output.get("technician_output", {}).get(
                "technician_explanation",
                {},
            ),
            "maintenance_recommendation": output.get("technician_output", {}).get(
                "recommendation",
                {},
            ),
            "maintenance_limitations": output.get("technician_output", {}).get(
                "limitations",
                [],
            ),
            "observed_ml_evidence": output.get("technician_output", {}).get(
                "observed_ml_evidence",
                {},
            ),
        },
        sort_keys=True,
    )
    return [
        pattern.pattern
        for pattern in FORBIDDEN_REAL_INTELLIGENCE_PATTERNS
        if pattern.search(text)
    ]


def validate_real_intelligence_output(
    output: dict[str, Any],
    *,
    require_live_gemini: bool = True,
) -> None:
    """Validate TASK-FAN-13 identity, provenance, grounding, and claim bounds."""
    if output.get("task") != TASK_ID:
        raise ValueError(f"output task must be {TASK_ID}")

    context = output["structured_context"]
    validate_structured_context(context)
    if context["schema_version"] != CONTEXT_SCHEMA_VERSION:
        raise ValueError(f"context schema_version must be {CONTEXT_SCHEMA_VERSION}")

    event = context["event"]
    event_id = event["event_id"]
    audio_path = str(output["audio_path"])
    if event["audio_path"] != audio_path:
        raise ValueError("context audio_path does not match output audio_path")
    if output["expert_b_output"]["input_audio"]["path"] != audio_path:
        raise ValueError("Expert B input audio path does not match output audio_path")
    if output["technician_output"]["event"]["event_id"] != event_id:
        raise ValueError("technician output event_id does not match context event_id")

    expert_a = context["expert_a"]
    if not expert_a["is_anomaly"]:
        raise ValueError("Expert A must flag the reference event before Expert B runs")
    if not output["expert_b_output"]["expert_a"]["is_anomaly"]:
        raise ValueError("Expert B output must preserve Expert A anomaly flag")

    method = context["expert_b"]["method"]
    if int(method["k"]) != DEFAULT_K:
        raise ValueError(f"Expert B k must remain {DEFAULT_K}")
    if method["distance"] != DEFAULT_DISTANCE:
        raise ValueError(f"Expert B distance must remain {DEFAULT_DISTANCE}")
    if method["rank_threshold"] is not None:
        raise ValueError("Expert B rank_threshold must remain null")
    if int(context["expert_b"]["references"]["selected_count"]) != DEFAULT_K:
        raise ValueError("Expert B selected_count must match k=30")
    for attribute in TIMBRE_ATTRIBUTES:
        row = context["expert_b"]["timbre_rank_scores"][attribute]
        if row["direction"] is not None or row["direction_code"] is not None:
            raise ValueError(f"{attribute} direction fields must remain null")

    retrieval = output["retrieval"]
    if not retrieval.get("available"):
        raise ValueError("semantic retrieval must return approved guidance")
    retrieved_results = retrieval.get("results", [])
    if not retrieved_results:
        raise ValueError("semantic retrieval returned no results")

    technician = output["technician_output"]
    validate_maintenance_output(technician)
    recommendation = technician["recommendation"]
    if not recommendation.get("available"):
        raise ValueError("maintenance recommendation must be available")
    retrieved_pairs = {
        (row.get("source_id"), row.get("chunk_id"))
        for row in technician.get("retrieved_maintenance_guidance", [])
    }
    for action in recommendation.get("recommended_next_actions", []):
        pair = (action.get("source_id"), action.get("chunk_id"))
        if pair not in retrieved_pairs:
            raise ValueError(f"maintenance action cites non-retrieved pair: {pair}")

    explanation_metadata = output["guarded_explanation"].get("metadata", {})
    maintenance_metadata = technician.get("metadata", {})
    for name, metadata in (
        ("explanation", explanation_metadata),
        ("maintenance", maintenance_metadata),
    ):
        if metadata.get("provider") != "gemini":
            raise ValueError(f"{name} provider must be gemini")
        if require_live_gemini and metadata.get("fallback_used"):
            raise ValueError(f"{name} Gemini fallback was used")
        if require_live_gemini and metadata.get("generation_mode") != "live_gemini":
            raise ValueError(f"{name} generation_mode must be live_gemini")

    analysis = context["analysis"]
    if analysis["rag"]["retriever_type"] != "semantic":
        raise ValueError("context analysis must record semantic retriever")
    if analysis["rag"]["corpus_version"] != CORPUS_VERSION:
        raise ValueError(f"context analysis must record corpus {CORPUS_VERSION}")

    for prompt_name, prompt in (
        ("explanation", output["guarded_explanation"].get("prompt")),
        ("maintenance", technician.get("prompt")),
    ):
        if prompt and (".wav" in prompt.lower() or "audio_path" in prompt.lower()):
            raise ValueError(f"{prompt_name} prompt contains raw audio path material")

    forbidden_hits = find_forbidden_claim_hits(output)
    if forbidden_hits:
        raise ValueError(f"generated output contains forbidden claim patterns: {forbidden_hits}")


def run_real_intelligence_fan_smoke(
    *,
    machine_type: str,
    machine_id: str,
    snr_tag: str,
    reference_index_path: Path,
    semantic_index_path: Path,
    audio_path: Path,
    output_path: Path,
    old_task10_output_path: Path,
    k: int = DEFAULT_K,
    distance: str = DEFAULT_DISTANCE,
    retrieval_top_k: int = 3,
    require_live_gemini: bool = True,
) -> dict[str, Any]:
    """Run one bounded real Fan event through Expert A/B, RAG, and Gemini."""
    if cfg.RAG_FAN_MVP_SELECTED_RETRIEVER != "semantic":
        raise ValueError("TASK-FAN-13 requires the selected Fan MVP retriever to be semantic")
    if k != DEFAULT_K:
        raise ValueError(f"TASK-FAN-13 preserves Expert B k={DEFAULT_K}")
    if distance != DEFAULT_DISTANCE:
        raise ValueError(f"TASK-FAN-13 preserves Expert B distance={DEFAULT_DISTANCE}")

    timings: dict[str, float] = {}
    total_start = perf_counter()

    start = perf_counter()
    reference_index = load_reference_index(reference_index_path)
    embedder = ExpertABottleneckEmbedder(snr_tag=snr_tag)
    timings["load_reference_index_and_embedder_seconds"] = perf_counter() - start

    start = perf_counter()
    expert_a = score_expert_a(audio_path, embedder)
    if not expert_a["is_anomaly"]:
        raise ValueError(
            f"Expert A did not flag supplied audio: {audio_path}; "
            f"score={expert_a['anomaly_score']:.6f}, "
            f"threshold={expert_a['threshold']:.6f}"
        )
    timings["audio_expert_a_seconds"] = perf_counter() - start

    start = perf_counter()
    expert = AcousticTimbreDifferenceExpert(
        reference_index=reference_index,
        embedder=embedder,
        k=k,
        distance=distance,
        rank_threshold=None,
    )
    expert_b_output = expert.characterize(
        audio_path=audio_path,
        machine_type=machine_type,
        machine_id=machine_id,
        snr_tag=snr_tag,
        expert_a=expert_a,
    )
    timings["expert_b_seconds"] = perf_counter() - start

    created_at = datetime.now(UTC).isoformat()
    analysis_run_id = f"analysis_{machine_type}_{machine_id}_{snr_tag}_{audio_path.stem}_task_fan_13"

    start = perf_counter()
    pre_context = context_from_expert_b_output(
        expert_b_output,
        created_at=created_at,
        analysis_run_id=analysis_run_id,
        reference_index_path=reference_index_path,
    )
    timings["context_translation_seconds"] = perf_counter() - start

    start = perf_counter()
    explanation = explain_context(pre_context, generator=GeminiTextGenerator())
    timings["gemini_explanation_seconds"] = perf_counter() - start

    start = perf_counter()
    retrieval_query = build_retrieval_query(pre_context)
    semantic_index = load_embedding_index(semantic_index_path)
    retrieval = SemanticRetriever(
        semantic_index,
        GeminiEmbeddingProvider(),
    ).retrieve(retrieval_query, top_k=retrieval_top_k)
    timings["retrieval_seconds"] = perf_counter() - start

    start = perf_counter()
    technician_output = generate_grounded_maintenance_output(
        pre_context,
        explanation=explanation,
        retrieval=retrieval,
        generator=GeminiMaintenanceTextGenerator(),
        retriever_type="semantic",
        corpus_version=CORPUS_VERSION,
    )
    timings["gemini_maintenance_seconds"] = perf_counter() - start

    start = perf_counter()
    final_context = context_from_expert_b_output(
        expert_b_output,
        created_at=created_at,
        analysis_run_id=analysis_run_id,
        reference_index_path=reference_index_path,
        llm_metadata=explanation.get("metadata"),
        rag_metadata={
            "retriever_type": "semantic",
            "corpus_version": CORPUS_VERSION,
            "retrieval_query": retrieval_query,
        },
        maintenance_metadata=technician_output.get("metadata"),
    )
    timings["context_provenance_update_seconds"] = perf_counter() - start

    output = {
        "task": TASK_ID,
        "architecture": (
            "audio -> Expert A -> Expert B -> Structured Health Context v0.2 -> "
            "semantic RAG -> Gemini guarded explanation -> Gemini grounded "
            "maintenance -> validation"
        ),
        "machine_scope": {
            "machine_type": machine_type,
            "machine_id": machine_id,
            "snr_tag": snr_tag,
        },
        "audio_path": str(audio_path),
        "reference_index_path": str(reference_index_path),
        "semantic_index_path": str(semantic_index_path),
        "retrieval_top_k": retrieval_top_k,
        "retrieval_query": retrieval_query,
        "expert_b_output": expert_b_output,
        "structured_context": final_context,
        "guarded_explanation": explanation,
        "retrieval": retrieval.to_dict(),
        "technician_output": technician_output,
        "task10_comparison": load_task10_comparison(old_task10_output_path),
        "limits": {
            "same_machine_same_audio": True,
            "rank_scores_are_probabilities": False,
            "physical_root_cause_confirmed": False,
            "remaining_life_prediction_available": False,
            "production_maintenance_validation_complete": False,
            "multi_machine_generalization_enabled": False,
            "free_text_change_is_scientific_improvement": False,
        },
        "timings": timings,
    }

    start = perf_counter()
    validate_real_intelligence_output(output, require_live_gemini=require_live_gemini)
    timings["validation_seconds"] = perf_counter() - start
    timings["total_seconds"] = perf_counter() - total_start
    output["validation"] = {
        "validator": "validate_real_intelligence_output",
        "require_live_gemini": require_live_gemini,
        "citation_pairs_valid": True,
        "forbidden_claim_hits": find_forbidden_claim_hits(output),
    }
    validate_real_intelligence_output(output, require_live_gemini=require_live_gemini)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    return output


def load_task10_comparison(path: Path) -> dict[str, Any]:
    """Load compact, non-improvement comparison metadata for TASK-10."""
    comparison: dict[str, Any] = {
        "path": str(path),
        "exists": path.is_file(),
        "comparison_purpose": (
            "bounded historical comparison only; changed free text is not "
            "scientific improvement evidence"
        ),
    }
    if not path.is_file():
        return comparison
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        comparison["load_error"] = exc.__class__.__name__
        return comparison

    context = payload.get("structured_context", {})
    technician = payload.get("technician_output", {})
    comparison.update(
        {
            "task": payload.get("task"),
            "event_id": context.get("event", {}).get("event_id"),
            "context_schema_version": context.get("schema_version"),
            "maintenance_source_mode": payload.get("maintenance_source_mode"),
            "maintenance_mode": technician.get("mode"),
            "recommendation_available": technician.get("recommendation", {}).get(
                "available",
            ),
            "total_seconds": payload.get("timings", {}).get("total_seconds"),
        }
    )
    return comparison


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--machine-type", default="fan")
    parser.add_argument("--machine-id", default="id_00")
    parser.add_argument("--snr-tag", default="minus6dB", choices=sorted(cfg.MIMII_SNR_DIRS))
    parser.add_argument("--reference-index", type=Path)
    parser.add_argument("--semantic-index", type=Path)
    parser.add_argument("--audio-path", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--old-task10-output", type=Path)
    parser.add_argument("--k", type=int, default=DEFAULT_K)
    parser.add_argument("--distance", default=DEFAULT_DISTANCE, choices=("euclidean", "cosine"))
    parser.add_argument("--retrieval-top-k", type=int, default=3)
    parser.add_argument(
        "--allow-gemini-fallback",
        action="store_true",
        help="Allow deterministic fallback output while still recording provider metadata.",
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
    semantic_index_path = args.semantic_index or default_embedding_index_path(CORPUS_VERSION)
    audio_path = args.audio_path or default_audio_path(args.snr_tag)
    output_path = args.output or default_output_path(
        args.machine_type,
        args.machine_id,
        args.snr_tag,
    )
    old_task10_output_path = args.old_task10_output or default_task10_output_path(
        args.machine_type,
        args.machine_id,
        args.snr_tag,
    )
    output = run_real_intelligence_fan_smoke(
        machine_type=args.machine_type,
        machine_id=args.machine_id,
        snr_tag=args.snr_tag,
        reference_index_path=reference_index_path,
        semantic_index_path=semantic_index_path,
        audio_path=audio_path,
        output_path=output_path,
        old_task10_output_path=old_task10_output_path,
        k=args.k,
        distance=args.distance,
        retrieval_top_k=args.retrieval_top_k,
        require_live_gemini=not args.allow_gemini_fallback,
    )

    context = output["structured_context"]
    technician = output["technician_output"]
    ranks = context["expert_b"]["timbre_rank_scores"]
    rank_text = ", ".join(
        f"{attribute}={float(ranks[attribute]['rank_score']):.6f}"
        for attribute in TIMBRE_ATTRIBUTES
    )
    retrieved_chunks = ", ".join(
        f"{row['source_id']}#{row['chunk_id']}"
        for row in output["retrieval"]["results"]
    )
    print("REAL_INTELLIGENCE_FAN_SMOKE=OK")
    print(f"EVENT_ID={context['event']['event_id']}")
    print(f"AUDIO={output['audio_path']}")
    print(
        "EXPERT_A="
        f"score={context['expert_a']['anomaly_score']:.6f} "
        f"threshold={context['expert_a']['threshold']:.6f} "
        f"is_anomaly={context['expert_a']['is_anomaly']}"
    )
    print(f"EXPERT_B_RANKS={rank_text}")
    print(f"RETRIEVED_CHUNKS={retrieved_chunks}")
    print(
        "EXPLANATION="
        f"mode={output['guarded_explanation']['metadata']['generation_mode']} "
        f"fallback={output['guarded_explanation']['metadata']['fallback_used']}"
    )
    print(
        "MAINTENANCE="
        f"mode={technician['metadata']['generation_mode']} "
        f"fallback={technician['metadata']['fallback_used']} "
        f"actions={len(technician['recommendation']['recommended_next_actions'])}"
    )
    for index, action in enumerate(
        technician["recommendation"]["recommended_next_actions"],
        start=1,
    ):
        print(
            f"ACTION_{index}="
            f"{action['source_id']}#{action['chunk_id']} | {action['action']}"
        )
    print(f"FORBIDDEN_HITS={output['validation']['forbidden_claim_hits']}")
    print(f"TOTAL_SECONDS={output['timings']['total_seconds']:.6f}")
    print(f"OUTPUT={output_path}")


if __name__ == "__main__":
    main()
