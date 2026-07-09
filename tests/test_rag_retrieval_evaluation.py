"""Unit tests for bounded RAG retrieval evaluation helpers."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
SCRIPTS_DIR = REPO_ROOT / "scripts"
for path in (SRC_DIR, SCRIPTS_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from evaluate_rag_retrieval import (  # noqa: E402
    compute_query_metrics,
    reciprocal_rank_fusion,
    select_retriever,
)
from rag import RetrievalResult  # noqa: E402


def _result(chunk_id: str, *, source_id: str = "source", score: float = 1.0) -> RetrievalResult:
    return RetrievalResult(
        source_id=source_id,
        title="Title",
        version="v1",
        chunk_id=chunk_id,
        snippet="snippet",
        score=score,
        path=Path("manual.md"),
        publisher="Publisher",
        corpus_version="corpus-v1",
        section_id=chunk_id.rsplit("#", 1)[-1],
        section_heading=chunk_id,
        source_url="https://example.test/manual",
    )


class RAGRetrievalEvaluationTests(unittest.TestCase):
    """Evaluation math and fusion behavior."""

    def test_compute_query_metrics_records_rank_hits_and_mrr(self) -> None:
        """Expected chunk at rank two yields Hit@3 and MRR 0.5."""
        metrics = compute_query_metrics(
            [_result("source#wrong"), _result("source#expected")],
            ["source"],
            ["source#expected"],
        )

        self.assertFalse(metrics.hit_at_1)
        self.assertTrue(metrics.hit_at_3)
        self.assertEqual(metrics.first_expected_rank, 2)
        self.assertEqual(metrics.reciprocal_rank, 0.5)
        self.assertIsNone(metrics.failure_reason)

    def test_compute_query_metrics_classifies_wrong_top_source(self) -> None:
        """Missing expected source in top three is an explicit failure pattern."""
        metrics = compute_query_metrics(
            [
                _result("other#a", source_id="other"),
                _result("other#b", source_id="other"),
                _result("other#c", source_id="other"),
            ],
            ["source"],
            ["source#expected"],
        )

        self.assertFalse(metrics.hit_at_3)
        self.assertEqual(metrics.failure_reason, "expected_source_absent_top3")

    def test_reciprocal_rank_fusion_preserves_metadata_and_combines_ranks(self) -> None:
        """A result appearing in both lists should rise above single-list hits."""
        fused = reciprocal_rank_fusion(
            [_result("source#a"), _result("source#b")],
            [_result("source#b"), _result("source#c")],
            top_k=3,
        )

        self.assertEqual([item.chunk_id for item in fused], ["source#b", "source#a", "source#c"])
        self.assertEqual(fused[0].source_id, "source")
        self.assertEqual(fused[0].corpus_version, "corpus-v1")
        self.assertGreater(fused[0].score, fused[1].score)

    def test_select_retriever_uses_metrics_then_simplicity(self) -> None:
        """Metric ties select the lower-latency simpler retriever."""
        selected = select_retriever(
            {
                "lexical": {
                    "hit_at_3": 1.0,
                    "mrr": 0.8,
                    "hit_at_1": 0.7,
                    "mean_latency_seconds": 0.01,
                },
                "semantic": {
                    "hit_at_3": 1.0,
                    "mrr": 0.8,
                    "hit_at_1": 0.7,
                    "mean_latency_seconds": 0.2,
                },
                "hybrid": {
                    "hit_at_3": 1.0,
                    "mrr": 0.8,
                    "hit_at_1": 0.7,
                    "mean_latency_seconds": 0.2,
                },
            }
        )

        self.assertEqual(selected["selected_retriever"], "lexical")


if __name__ == "__main__":
    unittest.main()
