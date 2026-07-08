"""Tests for approved-source maintenance retrieval guardrails."""

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
    LocalRetriever,
    RetrievalGroundingError,
    build_knowledge_base,
    validate_citations,
)


class RAGGroundingTests(unittest.TestCase):
    """Approved-source retrieval behavior."""

    def test_empty_knowledge_base_returns_safe_unavailable_result(self) -> None:
        """Missing approved source manifest does not produce invented guidance."""
        with tempfile.TemporaryDirectory() as tmp:
            kb = build_knowledge_base(Path(tmp))
            response = LocalRetriever(kb).retrieve("abnormal fan noise")
        self.assertFalse(response.available)
        self.assertEqual(response.results, ())
        self.assertIn("unavailable", response.message.lower())

    def test_files_without_approved_manifest_are_not_indexed(self) -> None:
        """Local files are ignored unless explicitly approved by manifest."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "fan_manual.md").write_text("Inspect mounting bolts.", encoding="utf-8")
            kb = build_knowledge_base(root)
        self.assertFalse(kb.is_available)
        self.assertEqual(kb.source_count, 0)

    def test_retrieval_returns_source_ids_and_snippets(self) -> None:
        """Approved documents produce source-preserving retrieval results."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "fan_manual.md").write_text(
                "When abnormal mechanical noise is reported, inspect fan mounting "
                "hardware and rotating assemblies according to the approved procedure.",
                encoding="utf-8",
            )
            (root / "approved_sources.json").write_text(
                json.dumps(
                    {
                        "sources": [
                            {
                                "source_id": "fan_manual_v1",
                                "title": "Fan Maintenance Manual",
                                "version": "v1",
                                "path": "fan_manual.md",
                                "approved": True,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            kb = build_knowledge_base(root)
            response = LocalRetriever(kb).retrieve("abnormal fan mechanical noise")

        self.assertTrue(response.available)
        self.assertEqual(response.results[0].source_id, "fan_manual_v1")
        self.assertEqual(response.results[0].version, "v1")
        self.assertIn("abnormal mechanical noise", response.results[0].snippet)
        self.assertGreater(response.results[0].score, 0.0)

    def test_section_aware_chunks_preserve_metadata(self) -> None:
        """Markdown sections keep source, corpus, and section identity."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "fan_manual.md").write_text(
                "# Fan Manual\n\n"
                "source metadata preface\n\n"
                "## FAN-SECTION-ONE\n\n"
                "Inspect belts and pulleys for fan acoustic noise.\n\n"
                "## FAN-SECTION-TWO\n\n"
                "Record vibration observations and inspection results.",
                encoding="utf-8",
            )
            (root / "approved_sources.json").write_text(
                json.dumps(
                    {
                        "corpus_version": "test-corpus-v1",
                        "sources": [
                            {
                                "source_id": "fan_manual_v1",
                                "title": "Fan Manual",
                                "publisher": "Approved Publisher",
                                "version": "v1",
                                "path": "fan_manual.md",
                                "approved": True,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            kb = build_knowledge_base(root)

        self.assertEqual(len(kb.chunks), 2)
        self.assertEqual(kb.chunks[0].chunk_id, "fan_manual_v1#FAN-SECTION-ONE")
        self.assertEqual(kb.chunks[0].section_id, "FAN-SECTION-ONE")
        self.assertEqual(kb.chunks[0].section_heading, "FAN-SECTION-ONE")
        self.assertEqual(kb.chunks[0].publisher, "Approved Publisher")
        self.assertEqual(kb.chunks[0].corpus_version, "test-corpus-v1")
        self.assertIn("FAN-SECTION-ONE", kb.chunks[0].text)

    def test_recommendation_cannot_cite_missing_source(self) -> None:
        """Downstream recommendations must cite only retrieved sources."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "procedure.md").write_text(
                "For abnormal fan noise, inspect mounting condition.",
                encoding="utf-8",
            )
            (root / "approved_sources.json").write_text(
                json.dumps(
                    {
                        "sources": [
                            {
                                "source_id": "approved_proc",
                                "title": "Approved Procedure",
                                "version": "2026-07",
                                "path": "procedure.md",
                                "approved": True,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            response = LocalRetriever(build_knowledge_base(root)).retrieve("fan noise")

        validate_citations(response, ["approved_proc"])
        with self.assertRaises(RetrievalGroundingError):
            validate_citations(response, ["missing_manual"])

    def test_repository_fan_corpus_manifest_loads_and_retrieves(self) -> None:
        """The approved Fan corpus manifest is loadable and retrievable."""
        root = REPO_ROOT / "data" / "manuals"
        kb = build_knowledge_base(root)
        self.assertTrue(kb.is_available)
        self.assertEqual(kb.source_count, 2)
        source_ids = {chunk.source_id for chunk in kb.chunks}
        self.assertIn("doe_fan_sourcebook_2003", source_ids)
        self.assertIn("doe_om_best_practices_release_3_fans", source_ids)

        response = LocalRetriever(kb).retrieve(
            "fan abnormal acoustic noise vibration belt inspection records"
        )

        self.assertTrue(response.available)
        self.assertGreaterEqual(len(response.results), 1)
        self.assertIn(response.results[0].source_id, source_ids)
        self.assertEqual(response.results[0].corpus_version, "AMHI-FAN-MAINT-KB-v1")
        self.assertTrue(response.results[0].section_id)
        self.assertTrue(response.results[0].section_heading)


if __name__ == "__main__":
    unittest.main()
