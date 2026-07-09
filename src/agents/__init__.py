"""Agent interfaces for the acoustic health monitoring project."""

from .diagnostic_agent import (
    DIAGNOSTIC_PROMPT_VERSION,
    DiagnosticExplanationAgent,
    ExplanationGuardrailError,
    build_guarded_prompt,
    coerce_explanation_payload,
    explain_context,
    validate_explanation_payload,
    validate_explanation_text,
)
from .gemini_provider import (
    GeminiConfigurationError,
    GeminiMaintenanceTextGenerator,
    GeminiProviderConfig,
    GeminiTextGenerator,
    gemini_preflight_metadata,
)
from .maintenance_agent import (
    GroundedMaintenanceAgent,
    MAINTENANCE_PROMPT_VERSION,
    MaintenanceGroundingError,
    build_retrieval_query,
    build_maintenance_prompt,
    coerce_maintenance_payload,
    generate_grounded_maintenance_output,
    validate_maintenance_output,
    validate_maintenance_payload_shape,
)

__all__ = [
    "DIAGNOSTIC_PROMPT_VERSION",
    "DiagnosticExplanationAgent",
    "ExplanationGuardrailError",
    "GeminiConfigurationError",
    "GeminiMaintenanceTextGenerator",
    "GeminiProviderConfig",
    "GeminiTextGenerator",
    "GroundedMaintenanceAgent",
    "MAINTENANCE_PROMPT_VERSION",
    "MaintenanceGroundingError",
    "build_guarded_prompt",
    "build_maintenance_prompt",
    "build_retrieval_query",
    "coerce_maintenance_payload",
    "coerce_explanation_payload",
    "explain_context",
    "gemini_preflight_metadata",
    "validate_explanation_payload",
    "generate_grounded_maintenance_output",
    "validate_explanation_text",
    "validate_maintenance_output",
    "validate_maintenance_payload_shape",
]
