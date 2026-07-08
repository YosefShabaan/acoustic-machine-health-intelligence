"""Secure Gemini provider configuration helpers."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import os
from typing import Any

import config as cfg


class GeminiConfigurationError(RuntimeError):
    """Raised when Gemini provider configuration is incomplete or invalid."""


@dataclass(frozen=True)
class GeminiProviderConfig:
    """Environment-based Gemini configuration without storing secrets."""

    model: str = cfg.GEMINI_MODEL
    api_key_env_var: str = cfg.GEMINI_API_KEY_ENV_VAR
    request_timeout_seconds: float = cfg.GEMINI_REQUEST_TIMEOUT_SECONDS

    def api_key_present(self, environ: Mapping[str, str] | None = None) -> bool:
        """Return whether the configured API key environment variable is present."""
        env = os.environ if environ is None else environ
        return bool(str(env.get(self.api_key_env_var, "")).strip())

    def load_api_key(self, environ: Mapping[str, str] | None = None) -> str:
        """Load the Gemini API key from the environment without logging it."""
        env = os.environ if environ is None else environ
        value = str(env.get(self.api_key_env_var, "")).strip()
        if not value:
            raise GeminiConfigurationError(
                f"{self.api_key_env_var} is not configured in the process environment"
            )
        return value

    def public_metadata(self, environ: Mapping[str, str] | None = None) -> dict[str, Any]:
        """Return non-secret provider configuration metadata."""
        return {
            "provider": "gemini",
            "model": self.model,
            "api_key_env_var": self.api_key_env_var,
            "api_key_present": self.api_key_present(environ),
            "request_timeout_seconds": self.request_timeout_seconds,
        }


def gemini_preflight_metadata(
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Return non-secret Gemini preflight metadata for validation and tests."""
    return GeminiProviderConfig().public_metadata(environ)
