"""Validation tests for the Fan maintenance retrieval evaluation set."""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from rag import build_knowledge_base  # noqa: E402


EVAL_PATH = REPO_ROOT / "data" / "manuals" / "fan_maintenance_retrieval_eval_v1.json"
FORBIDDEN_QUERY_PATTERNS = (
    re.compile(r"\bRUL\b", re.IGNORECASE),
    re.compile(r"remaining useful life", re.IGNORECASE),
    re.compile(r"time to failure", re.IGNORECASE),
    re.compile(r"\b\d+(?:\.\d+)?\s?%"),
    re.compile(r"\bconfidence\b", re.IGNORECASE),
    re.compile(r"\bprobability\b", re.IGNORECASE),
    re.compile(r"\bwill fail\b", re.IGNORECASE),
)


class RAGEvaluationSetTests(unittest.TestCase):
    """Evaluation-set consistency checks."""

    @classmethod
    def setUpClass(cls) -> None:
        """Load corpus and evaluation set once for all tests."""
        cls.payload = json.loads(EVAL_PATH.read_text(encoding="utf-8"))
        cls.queries = cls.payload["queries"]
        cls.kb = build_knowledge_base(REPO_ROOT / "data" / "manuals")
        cls.source_ids = {chunk.source_id for chunk in cls.kb.chunks}
        cls.chunk_ids = {chunk.chunk_id for chunk in cls.kb.chunks}

    def test_evaluation_set_shape(self) -> None:
        """Evaluation set has the expected bounded size and metadata."""
        self.assertEqual(self.payload["schema_version"], "1.0.0")
        self.assertEqual(
            self.payload["evaluation_set_id"],
            "AMHI-FAN-MAINT-RETRIEVAL-EVAL-v1",
        )
        self.assertEqual(self.payload["corpus_version"], "AMHI-FAN-MAINT-KB-v1")
        self.assertEqual(self.payload["status"], "project_annotation_not_paper_ground_truth")
        self.assertGreaterEqual(len(self.queries), 20)
        self.assertLessEqual(len(self.queries), 30)

    def test_query_ids_are_unique(self) -> None:
        """Query identifiers are stable and unique."""
        query_ids = [row["query_id"] for row in self.queries]
        self.assertEqual(len(query_ids), len(set(query_ids)))

    def test_expected_sources_and_chunks_exist(self) -> None:
        """Expected IDs must point to approved corpus chunks."""
        for row in self.queries:
            self.assertTrue(row["query"].strip(), row["query_id"])
            self.assertTrue(row["rationale"].strip(), row["query_id"])
            self.assertTrue(row["expected_source_ids"], row["query_id"])
            self.assertTrue(row["expected_chunk_ids"], row["query_id"])
            self.assertTrue(set(row["expected_source_ids"]).issubset(self.source_ids))
            self.assertTrue(set(row["expected_chunk_ids"]).issubset(self.chunk_ids))

    def test_queries_do_not_encode_unsupported_claims(self) -> None:
        """Evaluation queries avoid unsupported production/failure claims."""
        for row in self.queries:
            text = f"{row['query']} {row['rationale']}"
            for pattern in FORBIDDEN_QUERY_PATTERNS:
                self.assertIsNone(
                    pattern.search(text),
                    f"{row['query_id']} contains forbidden wording: {pattern.pattern}",
                )


if __name__ == "__main__":
    unittest.main()
