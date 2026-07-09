"""Secure Gemini provider configuration helpers."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import json
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


EXPLANATION_RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "observations": {"type": "array", "items": {"type": "string"}},
        "hypotheses": {"type": "array", "items": {"type": "string"}},
        "limitations": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["summary", "observations", "hypotheses", "limitations"],
}

MAINTENANCE_RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "event_summary": {"type": "string"},
        "observed_evidence": {"type": "array", "items": {"type": "string"}},
        "inspection_priority": {"type": "string"},
        "recommended_next_actions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "action": {"type": "string"},
                    "reason": {"type": "string"},
                    "source_id": {"type": "string"},
                    "chunk_id": {"type": "string"},
                },
                "required": ["action", "reason", "source_id", "chunk_id"],
            },
        },
        "limitations": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "event_summary",
        "observed_evidence",
        "inspection_priority",
        "recommended_next_actions",
        "limitations",
    ],
}


class GeminiTextGenerator:
    """Gemini-backed text generator for guarded structured prompts."""

    def __init__(
        self,
        *,
        config: GeminiProviderConfig | None = None,
        client: Any | None = None,
    ) -> None:
        self.config = config or GeminiProviderConfig()
        self._client = client

    def metadata(self) -> dict[str, Any]:
        """Return non-secret provider/model metadata."""
        return {
            "provider": "gemini",
            "model": self.config.model,
            "generation_mode": "live_gemini",
        }

    def _build_client(self) -> Any:
        """Build the official Google GenAI SDK client using environment secrets."""
        from google import genai
        from google.genai import types

        return genai.Client(
            api_key=self.config.load_api_key(),
            http_options=types.HttpOptions(
                timeout=int(self.config.request_timeout_seconds * 1000)
            ),
        )

    @staticmethod
    def _response_to_payload(response: Any) -> dict[str, Any]:
        """Extract a JSON object payload from a Gemini SDK response."""
        parsed = getattr(response, "parsed", None)
        if parsed is not None:
            if isinstance(parsed, dict):
                return parsed
            if hasattr(parsed, "model_dump"):
                return parsed.model_dump()

        text = str(getattr(response, "text", "") or "").strip()
        if not text:
            raise GeminiConfigurationError("Gemini response did not contain text")
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].strip()
        payload = json.loads(text)
        if not isinstance(payload, dict):
            raise GeminiConfigurationError("Gemini response JSON was not an object")
        return payload

    def generate(self, prompt: str) -> dict[str, Any]:
        """Generate a structured explanation payload from a guarded prompt."""
        from google.genai import types

        client = self._client or self._build_client()
        response = client.models.generate_content(
            model=self.config.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                responseMimeType="application/json",
                responseSchema=EXPLANATION_RESPONSE_SCHEMA,
                temperature=0.2,
                httpOptions=types.HttpOptions(
                    timeout=int(self.config.request_timeout_seconds * 1000)
                ),
            ),
        )
        return self._response_to_payload(response)


class GeminiMaintenanceTextGenerator:
    """Gemini-backed generator for source-grounded maintenance actions."""

    def __init__(
        self,
        *,
        config: GeminiProviderConfig | None = None,
        client: Any | None = None,
    ) -> None:
        self.config = config or GeminiProviderConfig()
        self._client = client

    def metadata(self) -> dict[str, Any]:
        """Return non-secret provider/model metadata."""
        return {
            "provider": "gemini",
            "model": self.config.model,
            "generation_mode": "live_gemini",
        }

    def _build_client(self) -> Any:
        """Build the official Google GenAI SDK client using environment secrets."""
        from google import genai
        from google.genai import types

        return genai.Client(
            api_key=self.config.load_api_key(),
            http_options=types.HttpOptions(
                timeout=int(self.config.request_timeout_seconds * 1000)
            ),
        )

    def generate(self, prompt: str) -> dict[str, Any]:
        """Generate structured maintenance actions from a grounded prompt."""
        from google.genai import types

        client = self._client or self._build_client()
        response = client.models.generate_content(
            model=self.config.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                responseMimeType="application/json",
                responseSchema=MAINTENANCE_RESPONSE_SCHEMA,
                temperature=0.0,
                httpOptions=types.HttpOptions(
                    timeout=int(self.config.request_timeout_seconds * 1000)
                ),
            ),
        )
        return GeminiTextGenerator._response_to_payload(response)
