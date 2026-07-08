"""Tests for Gemini semantic retrieval plumbing with mocked embeddings."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from rag import (  # noqa: E402
    SemanticRetriever,
    build_knowledge_base,
    build_semantic_embedding_index,
    load_embedding_index,
    write_embedding_index,
)


class FakeEmbeddingProvider:
    """Deterministic fake embedding provider for retrieval tests."""

    def metadata(self) -> dict:
        """Return fake provider metadata."""
        return {
            "embedding_provider": "fake",
            "embedding_model": "fake-embedding-model",
            "embedding_dimension": 3,
        }

    def embed_text(self, text: str, *, purpose: str) -> list[float]:
        """Embed text into a tiny deterministic vector."""
        lowered = text.lower()
        return [
            1.0 if "belt" in lowered or "pulley" in lowered else 0.0,
            1.0 if "record" in lowered or "log" in lowered else 0.0,
            1.0 if "duct" in lowered or "wiring" in lowered else 0.0,
        ]


def _manuals_dir(root: Path) -> Path:
    (root / "manual.md").write_text(
        "# Fan Manual\n\n"
        "## FAN-BELT\n\n"
        "Inspect belt tension, belt alignment, and pulley condition.\n\n"
        "## FAN-RECORDS\n\n"
        "Record inspection observations in the maintenance log.\n\n"
        "## FAN-DUCT\n\n"
        "Inspect ductwork, wiring, and loose connections.",
        encoding="utf-8",
    )
    (root / "approved_sources.json").write_text(
        json.dumps(
            {
                "corpus_version": "semantic-test-v1",
                "sources": [
                    {
                        "source_id": "manual",
                        "title": "Manual",
                        "publisher": "Publisher",
                        "version": "v1",
                        "path": "manual.md",
                        "approved": True,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return root


class SemanticRetrieverTests(unittest.TestCase):
    """Semantic retriever behavior."""

    def test_embedding_index_round_trips_with_vectors_and_metadata(self) -> None:
        """Embedding cache preserves corpus, chunk, and vector metadata."""
        with tempfile.TemporaryDirectory() as tmp:
            root = _manuals_dir(Path(tmp))
            kb = build_knowledge_base(root)
            index = build_semantic_embedding_index(
                kb,
                FakeEmbeddingProvider(),
                created_at="2026-07-09T00:00:00+00:00",
            )
            output = Path(tmp) / "semantic_index.json"
            write_embedding_index(index, output)
            loaded = load_embedding_index(output)

        self.assertEqual(loaded.corpus_version, "semantic-test-v1")
        self.assertEqual(loaded.embedding_provider, "fake")
        self.assertEqual(loaded.embedding_model, "fake-embedding-model")
        self.assertEqual(loaded.embedding_dimension, 3)
        self.assertEqual(len(loaded.records), 3)
        self.assertEqual(loaded.records[0].section_id, "FAN-BELT")
        self.assertEqual(len(loaded.records[0].embedding), 3)

    def test_semantic_retriever_returns_source_preserving_result(self) -> None:
        """Semantic retrieval returns the same source-preserving contract."""
        with tempfile.TemporaryDirectory() as tmp:
            kb = build_knowledge_base(_manuals_dir(Path(tmp)))
            index = build_semantic_embedding_index(kb, FakeEmbeddingProvider())

        response = SemanticRetriever(index, FakeEmbeddingProvider()).retrieve(
            "belt pulley inspection",
            top_k=1,
        )

        self.assertTrue(response.available)
        self.assertEqual(len(response.results), 1)
        result = response.results[0]
        self.assertEqual(result.source_id, "manual")
        self.assertEqual(result.section_id, "FAN-BELT")
        self.assertEqual(result.corpus_version, "semantic-test-v1")
        self.assertGreater(result.score, 0.0)
        self.assertIn("belt", result.snippet.lower())


if __name__ == "__main__":
    unittest.main()
