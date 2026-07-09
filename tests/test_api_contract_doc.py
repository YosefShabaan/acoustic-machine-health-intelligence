"""Tests for the API v1 contract document."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = REPO_ROOT / "docs" / "API_CONTRACT_V1.md"
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from application import (  # noqa: E402
    EVENT_STATUS_COMPLETED,
    EVENT_STATUS_FAILED,
    EVENT_STATUS_PROCESSING,
    EVENT_STATUS_QUEUED,
)


class ApiContractDocTests(unittest.TestCase):
    """Contract checks before route implementation."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.text = DOC_PATH.read_text(encoding="utf-8")

    def test_required_endpoints_are_documented(self) -> None:
        for endpoint in (
            "POST /api/v1/events",
            "GET /api/v1/events/{event_id}",
            "GET /api/v1/events",
            "GET /api/v1/machines/{machine_type}/{machine_id}/events",
            "GET /api/v1/health",
            "GET /api/v1/ready",
        ):
            self.assertIn(endpoint, self.text)

    def test_event_statuses_match_repository_contract(self) -> None:
        for status in (
            EVENT_STATUS_QUEUED,
            EVENT_STATUS_PROCESSING,
            EVENT_STATUS_COMPLETED,
            EVENT_STATUS_FAILED,
        ):
            self.assertIn(f"`{status}`", self.text)

    def test_contract_captures_ingestion_and_async_behavior(self) -> None:
        self.assertIn("multipart/form-data", self.text)
        self.assertIn("202 Accepted", self.text)
        self.assertIn("registered-reference", self.text)
        self.assertIn("Background processing is defined in TASK-PROD-08", self.text)

    def test_contract_keeps_claim_and_path_guardrails_visible(self) -> None:
        forbidden_claims = (
            "remaining useful life",
            "confirmed physical root cause",
            "fault probability",
            "confidence percentage",
            "multi-machine generalization",
        )
        for phrase in forbidden_claims:
            self.assertIn(phrase, self.text)
        self.assertIn("must not expose", self.text)
        self.assertNotIn("D:\\PDM_Data", self.text)


if __name__ == "__main__":
    unittest.main()
