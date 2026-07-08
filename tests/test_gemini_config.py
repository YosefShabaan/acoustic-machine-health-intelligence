"""Tests for secure Gemini provider configuration."""

from __future__ import annotations

from pathlib import Path
import os
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import config as cfg  # noqa: E402
from agents.gemini_provider import (  # noqa: E402
    GeminiConfigurationError,
    GeminiProviderConfig,
    gemini_preflight_metadata,
)


class GeminiConfigTests(unittest.TestCase):
    """Gemini secret and model configuration tests."""

    def test_default_model_is_stable_gemini_flash(self) -> None:
        """Model metadata uses the documented default unless the env overrides it."""
        self.assertEqual(cfg.GEMINI_MODEL, os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"))
        self.assertEqual(cfg.LLM_MODEL, cfg.GEMINI_MODEL)

    def test_preflight_reports_presence_without_secret_value(self) -> None:
        """Preflight metadata records presence but never includes the key value."""
        secret = "-".join(("redacted", "value", "never", "log"))
        metadata = gemini_preflight_metadata({"GEMINI_API_KEY": secret})
        text = repr(metadata)
        self.assertTrue(metadata["api_key_present"])
        self.assertIn("GEMINI_API_KEY", text)
        self.assertNotIn(secret, text)

    def test_missing_key_error_does_not_include_secret_value(self) -> None:
        """Missing-key errors name the env var but contain no secret material."""
        config = GeminiProviderConfig()
        with self.assertRaises(GeminiConfigurationError) as raised:
            config.load_api_key({})
        message = str(raised.exception)
        self.assertIn("GEMINI_API_KEY", message)
        self.assertNotIn("api_key=", message.lower())

    def test_load_api_key_reads_only_environment_mapping(self) -> None:
        """Provider config can load the key for a future client without storing it."""
        config = GeminiProviderConfig()
        self.assertEqual(config.load_api_key({"GEMINI_API_KEY": "value"}), "value")


if __name__ == "__main__":
    unittest.main()
