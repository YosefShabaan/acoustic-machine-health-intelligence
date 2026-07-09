"""Evaluate Fan maintenance RAG retrievers on the bounded project eval set."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
from time import perf_counter
from typing import Any, Iterable
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import config as cfg  # noqa: E402
from rag import (  # noqa: E402
    GeminiEmbeddingProvider,
    LocalRetriever,
    RetrievalResult,
    SemanticRetriever,
    build_knowledge_base,
    default_embedding_index_path,
    load_embedding_index,
)


EVAL_SET_PATH = REPO_ROOT / "data" / "manuals" / "fan_maintenance_retrieval_eval_v1.json"
DEFAULT_TOP_K = 15
DEFAULT_OUTPUT_PATH = (
    cfg.PROCESSED_DIR / "rag_retrieval_evaluation_amhi_fan_maint_kb_v1_task_rag_05.json"
)
RETRIEVER_ORDER = ("lexical", "semantic", "hybrid")


@dataclass(frozen=True)
class EvaluationQuery:
    """One project-annotated retrieval evaluation query."""

    query_id: str
    query: str
    expected_source_ids: tuple[str, ...]
    expected_chunk_ids: tuple[str, ...]
    rationale: str


@dataclass(frozen=True)
class QueryMetrics:
    """Rank metrics for one query/retriever pair."""

    hit_at_1: bool
    hit_at_3: bool
    reciprocal_rank: float
    first_expected_rank: int | None
    top_result_expected_source_match: bool
    top_result_expected_chunk_match: bool
    failure_reason: str | None


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eval-set", type=Path, default=EVAL_SET_PATH)
    parser.add_argument("--manuals-dir", type=Path, default=cfg.RAG_MANUALS_DIR)
    parser.add_argument(
        "--semantic-index",
        type=Path,
        default=default_embedding_index_path("AMHI-FAN-MAINT-KB-v1"),
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)
    parser.add_argument("--limit", type=int)
    return parser.parse_args()


def load_evaluation_queries(path: Path, *, limit: int | None = None) -> tuple[dict[str, Any], list[EvaluationQuery]]:
    """Load the project-annotated retrieval evaluation set."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("queries") or []
    queries = [
        EvaluationQuery(
            query_id=str(row["query_id"]),
            query=str(row["query"]),
            expected_source_ids=tuple(str(item) for item in row["expected_source_ids"]),
            expected_chunk_ids=tuple(str(item) for item in row["expected_chunk_ids"]),
            rationale=str(row["rationale"]),
        )
        for row in rows
    ]
    if limit is not None:
        queries = queries[:limit]
    return payload, queries


def compute_query_metrics(
    results: Iterable[RetrievalResult],
    expected_source_ids: Iterable[str],
    expected_chunk_ids: Iterable[str],
) -> QueryMetrics:
    """Compute Hit@1, Hit@3, MRR, and failure classification."""
    ranked = tuple(results)
    expected_sources = set(expected_source_ids)
    expected_chunks = set(expected_chunk_ids)
    ranked_chunk_ids = [result.chunk_id for result in ranked]
    ranked_source_ids = [result.source_id for result in ranked]

    first_expected_rank: int | None = None
    for rank, chunk_id in enumerate(ranked_chunk_ids, start=1):
        if chunk_id in expected_chunks:
            first_expected_rank = rank
            break

    top_result = ranked[0] if ranked else None
    top_source_match = bool(top_result and top_result.source_id in expected_sources)
    top_chunk_match = bool(top_result and top_result.chunk_id in expected_chunks)
    hit_at_1 = first_expected_rank == 1
    hit_at_3 = first_expected_rank is not None and first_expected_rank <= 3
    reciprocal_rank = 0.0 if first_expected_rank is None else 1.0 / first_expected_rank

    failure_reason = None
    if not ranked:
        failure_reason = "no_results"
    elif not hit_at_3 and top_source_match:
        failure_reason = "expected_source_wrong_chunk_top3"
    elif not hit_at_3 and any(source_id in expected_sources for source_id in ranked_source_ids[:3]):
        failure_reason = "expected_source_present_wrong_chunk_top3"
    elif not hit_at_3:
        failure_reason = "expected_source_absent_top3"

    return QueryMetrics(
        hit_at_1=hit_at_1,
        hit_at_3=hit_at_3,
        reciprocal_rank=reciprocal_rank,
        first_expected_rank=first_expected_rank,
        top_result_expected_source_match=top_source_match,
        top_result_expected_chunk_match=top_chunk_match,
        failure_reason=failure_reason,
    )


def reciprocal_rank_fusion(
    lexical_results: Iterable[RetrievalResult],
    semantic_results: Iterable[RetrievalResult],
    *,
    rrf_k: int = 60,
    top_k: int = DEFAULT_TOP_K,
) -> tuple[RetrievalResult, ...]:
    """Fuse lexical and semantic ranked lists using reciprocal-rank fusion."""
    scores: dict[str, float] = {}
    metadata: dict[str, RetrievalResult] = {}
    for results in (tuple(lexical_results), tuple(semantic_results)):
        for rank, result in enumerate(results, start=1):
            scores[result.chunk_id] = scores.get(result.chunk_id, 0.0) + 1.0 / (rrf_k + rank)
            metadata.setdefault(result.chunk_id, result)

    ranked_chunk_ids = sorted(
        scores,
        key=lambda chunk_id: (-scores[chunk_id], metadata[chunk_id].source_id, chunk_id),
    )
    fused: list[RetrievalResult] = []
    for chunk_id in ranked_chunk_ids[:top_k]:
        base = metadata[chunk_id]
        fused.append(
            RetrievalResult(
                source_id=base.source_id,
                title=base.title,
                version=base.version,
                chunk_id=base.chunk_id,
                snippet=base.snippet,
                score=round(scores[chunk_id], 6),
                path=base.path,
                publisher=base.publisher,
                corpus_version=base.corpus_version,
                section_id=base.section_id,
                section_heading=base.section_heading,
                source_url=base.source_url,
            )
        )
    return tuple(fused)


def summarize_query_results(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate metric rows for one retriever."""
    items = list(rows)
    query_count = len(items)
    if query_count == 0:
        return {
            "query_count": 0,
            "hit_at_1": 0.0,
            "hit_at_3": 0.0,
            "mrr": 0.0,
            "mean_latency_seconds": 0.0,
            "max_latency_seconds": 0.0,
            "failure_count": 0,
            "failure_patterns": {},
        }

    failure_patterns: dict[str, int] = {}
    for item in items:
        reason = item["metrics"].get("failure_reason")
        if reason:
            failure_patterns[reason] = failure_patterns.get(reason, 0) + 1

    return {
        "query_count": query_count,
        "hit_at_1": round(_mean(1.0 if item["metrics"]["hit_at_1"] else 0.0 for item in items), 6),
        "hit_at_3": round(_mean(1.0 if item["metrics"]["hit_at_3"] else 0.0 for item in items), 6),
        "mrr": round(_mean(float(item["metrics"]["reciprocal_rank"]) for item in items), 6),
        "mean_latency_seconds": round(_mean(float(item["latency_seconds"]) for item in items), 6),
        "max_latency_seconds": round(max(float(item["latency_seconds"]) for item in items), 6),
        "failure_count": sum(1 for item in items if item["metrics"]["failure_reason"]),
        "failure_patterns": dict(sorted(failure_patterns.items())),
    }


def select_retriever(summary_by_retriever: dict[str, dict[str, Any]]) -> dict[str, str]:
    """Select the Fan MVP retriever by metrics, then latency, then simplicity."""
    simplicity_rank = {"lexical": 0, "hybrid": 1, "semantic": 2}
    selected = max(
        summary_by_retriever,
        key=lambda name: (
            float(summary_by_retriever[name]["hit_at_3"]),
            float(summary_by_retriever[name]["mrr"]),
            float(summary_by_retriever[name]["hit_at_1"]),
            -float(summary_by_retriever[name]["mean_latency_seconds"]),
            -simplicity_rank[name],
        ),
    )
    return {
        "selected_retriever": selected,
        "selection_policy": (
            "Choose highest Hit@3, then MRR, then Hit@1, then lower mean latency, "
            "then simpler runtime dependency."
        ),
    }


def evaluate_retrievers(
    queries: list[EvaluationQuery],
    *,
    manuals_dir: Path,
    semantic_index_path: Path,
    top_k: int,
) -> dict[str, list[dict[str, Any]]]:
    """Evaluate lexical, semantic, and hybrid retrievers over all queries."""
    if not semantic_index_path.exists():
        raise FileNotFoundError(f"semantic index not found: {semantic_index_path}")

    knowledge_base = build_knowledge_base(manuals_dir)
    lexical_retriever = LocalRetriever(knowledge_base)
    semantic_retriever = SemanticRetriever(
        load_embedding_index(semantic_index_path),
        GeminiEmbeddingProvider(),
    )

    rows_by_retriever: dict[str, list[dict[str, Any]]] = {name: [] for name in RETRIEVER_ORDER}
    for item in queries:
        lexical_start = perf_counter()
        lexical_response = lexical_retriever.retrieve(item.query, top_k=top_k)
        lexical_latency = perf_counter() - lexical_start

        semantic_start = perf_counter()
        semantic_response = semantic_retriever.retrieve(item.query, top_k=top_k)
        semantic_latency = perf_counter() - semantic_start

        hybrid_start = perf_counter()
        hybrid_results = reciprocal_rank_fusion(
            lexical_response.results,
            semantic_response.results,
            top_k=top_k,
        )
        hybrid_latency = perf_counter() - hybrid_start

        rows_by_retriever["lexical"].append(
            _query_row(item, lexical_response.results, lexical_latency)
        )
        rows_by_retriever["semantic"].append(
            _query_row(item, semantic_response.results, semantic_latency)
        )
        rows_by_retriever["hybrid"].append(
            _query_row(item, hybrid_results, lexical_latency + semantic_latency + hybrid_latency)
        )

    return rows_by_retriever


def build_evaluation_payload(
    *,
    eval_set_payload: dict[str, Any],
    queries: list[EvaluationQuery],
    rows_by_retriever: dict[str, list[dict[str, Any]]],
    semantic_index_path: Path,
    top_k: int,
) -> dict[str, Any]:
    """Build a JSON-serializable evaluation report."""
    summary = {
        retriever: summarize_query_results(rows)
        for retriever, rows in rows_by_retriever.items()
    }
    selection = select_retriever(summary)
    return {
        "schema_version": "1.0.0",
        "artifact_type": "rag_retrieval_evaluation",
        "created_at": datetime.now(UTC).isoformat(),
        "evaluation_set_id": eval_set_payload["evaluation_set_id"],
        "evaluation_set_status": eval_set_payload["status"],
        "corpus_version": eval_set_payload["corpus_version"],
        "query_count": len(queries),
        "top_k": top_k,
        "retrievers": list(RETRIEVER_ORDER),
        "semantic_index_path": str(semantic_index_path),
        "semantic_index_tracked_in_git": False,
        "metrics": {
            "primary": "Hit@3",
            "secondary": ["MRR", "Hit@1", "latency_seconds"],
        },
        "summary": summary,
        "selection": selection,
        "query_results": rows_by_retriever,
        "claim_limits": [
            "Project retrieval annotations are not paper ground truth.",
            "Retrieval performance does not validate maintenance correctness.",
            "No RUL, root-cause, probability, confidence, or multi-machine claim is enabled.",
        ],
    }


def write_payload(payload: dict[str, Any], output_path: Path) -> Path:
    """Write the generated evaluation payload outside Git by default."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return output_path


def main() -> None:
    """Run the bounded retrieval evaluation."""
    args = parse_args()
    eval_set_payload, queries = load_evaluation_queries(args.eval_set, limit=args.limit)
    rows_by_retriever = evaluate_retrievers(
        queries,
        manuals_dir=args.manuals_dir,
        semantic_index_path=args.semantic_index,
        top_k=args.top_k,
    )
    payload = build_evaluation_payload(
        eval_set_payload=eval_set_payload,
        queries=queries,
        rows_by_retriever=rows_by_retriever,
        semantic_index_path=args.semantic_index,
        top_k=args.top_k,
    )
    output_path = write_payload(payload, args.output)

    print("RAG_RETRIEVAL_EVALUATION=OK")
    print(f"EVAL_SET_ID={payload['evaluation_set_id']}")
    print(f"QUERY_COUNT={payload['query_count']}")
    print(f"TOP_K={payload['top_k']}")
    for retriever in RETRIEVER_ORDER:
        summary = payload["summary"][retriever]
        print(
            f"{retriever.upper()} "
            f"HIT_AT_1={summary['hit_at_1']} "
            f"HIT_AT_3={summary['hit_at_3']} "
            f"MRR={summary['mrr']} "
            f"MEAN_LATENCY_SECONDS={summary['mean_latency_seconds']} "
            f"FAILURES={summary['failure_count']}"
        )
    print(f"SELECTED_RETRIEVER={payload['selection']['selected_retriever']}")
    print(f"OUTPUT={output_path}")


def _query_row(
    item: EvaluationQuery,
    results: Iterable[RetrievalResult],
    latency_seconds: float,
) -> dict[str, Any]:
    ranked = tuple(results)
    metrics = compute_query_metrics(
        ranked,
        item.expected_source_ids,
        item.expected_chunk_ids,
    )
    return {
        "query_id": item.query_id,
        "query": item.query,
        "expected_source_ids": list(item.expected_source_ids),
        "expected_chunk_ids": list(item.expected_chunk_ids),
        "latency_seconds": round(latency_seconds, 6),
        "metrics": {
            "hit_at_1": metrics.hit_at_1,
            "hit_at_3": metrics.hit_at_3,
            "reciprocal_rank": round(metrics.reciprocal_rank, 6),
            "first_expected_rank": metrics.first_expected_rank,
            "top_result_expected_source_match": metrics.top_result_expected_source_match,
            "top_result_expected_chunk_match": metrics.top_result_expected_chunk_match,
            "failure_reason": metrics.failure_reason,
        },
        "top_results": [
            {
                "rank": rank,
                "source_id": result.source_id,
                "chunk_id": result.chunk_id,
                "section_heading": result.section_heading,
                "score": result.score,
                "expected_source_match": result.source_id in item.expected_source_ids,
                "expected_chunk_match": result.chunk_id in item.expected_chunk_ids,
            }
            for rank, result in enumerate(ranked, start=1)
        ],
    }


def _mean(values: Iterable[float]) -> float:
    items = list(values)
    return sum(items) / len(items) if items else 0.0


if __name__ == "__main__":
    main()
