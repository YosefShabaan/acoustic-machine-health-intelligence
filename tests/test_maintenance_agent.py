"""Tests for grounded maintenance output guardrails."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from agents import (  # noqa: E402
    GeminiMaintenanceTextGenerator,
    GeminiProviderConfig,
    MaintenanceGroundingError,
    build_maintenance_prompt,
    build_retrieval_query,
    generate_grounded_maintenance_output,
    validate_maintenance_output,
)
from rag import RetrievalResponse, RetrievalResult  # noqa: E402


def _context() -> dict:
    rank_rows = {
        "sharpness": 0.9333333333333333,
        "roughness": 0.9333333333333333,
        "boominess": 0.0,
        "brightness": 0.9333333333333333,
        "depth": 0.6666666666666666,
    }
    return {
        "schema_version": "0.1.0",
        "event": {
            "event_id": "fan_id_00_minus6dB_00000002",
            "asset_id": "FAN-ID00-001",
            "machine_type": "fan",
            "machine_id": "id_00",
            "snr_tag": "minus6dB",
            "audio_path": r"D:\PDM_Data\MIMII\fan_minus6dB\id_00\abnormal\00000002.wav",
        },
        "expert_a": {
            "expert": "ExpertAAnomalyDetector",
            "anomaly_score": 0.6220951080322266,
            "threshold": 0.5932844281196594,
            "is_anomaly": True,
        },
        "expert_b": {
            "expert": "AcousticTimbreDifferenceExpert",
            "method": {
                "status": "adaptation_not_exact_reproduction",
                "embedding_model": "expert_a_bottleneck_adaptation",
                "timbre_model": "AudioCommons timbral_models",
                "k": 2,
                "distance": "euclidean",
                "rank_threshold": None,
            },
            "references": {
                "pool_size": 2,
                "selected_count": 2,
                "filter": {
                    "machine_type": "fan",
                    "machine_id": "id_00",
                    "snr_tag": "minus6dB",
                },
                "neighbors": [
                    {"path": "normal_a.wav", "distance": 1.2, "rank": 1},
                    {"path": "normal_b.wav", "distance": 2.8, "rank": 2},
                ],
            },
            "timbre_rank_scores": {
                attribute: {
                    "test_value": 10.0,
                    "rank_score": score,
                    "direction": None,
                    "direction_code": None,
                }
                for attribute, score in rank_rows.items()
            },
            "warnings": [
                "No paper-specific timbre ground-truth labels available; output is qualitative characterization only.",
            ],
        },
        "system_limits": {
            "evidence_only": True,
            "specific_fault_confirmed": False,
            "physical_cause_confirmed": False,
            "remaining_life_prediction_available": False,
            "paper_equivalent_timbre_accuracy_validated": False,
            "timbre_direction_accuracy_validated": False,
            "rank_score_is_confidence": False,
            "llm_or_rag_grounding_available": False,
            "limitations": [
                "Structured context preserves evidence; it is not a diagnosis.",
                "Expert B rank scores are qualitative relative ranks, not probabilities.",
            ],
        },
    }


def _retrieval(available: bool = True) -> RetrievalResponse:
    if not available:
        return RetrievalResponse(
            query="fan abnormal noise",
            available=False,
            results=(),
            message="No approved maintenance source was retrieved.",
        )
    return RetrievalResponse(
        query="fan abnormal noise",
        available=True,
        results=(
            RetrievalResult(
                source_id="approved_proc",
                title="Approved Fan Procedure",
                version="2026-07",
                chunk_id="approved_proc#chunk-1",
                snippet="For abnormal fan noise, inspect mounting condition and rotating assembly condition.",
                score=0.8,
                path=Path("procedure.md"),
                publisher="Approved Publisher",
                corpus_version="corpus-v1",
                section_id="chunk-1",
                section_heading="Inspection",
            ),
        ),
        message="Retrieved 1 approved maintenance source chunk.",
    )


class GoodMaintenanceGenerator:
    """Mock valid grounded maintenance generator."""

    def metadata(self) -> dict:
        """Return mock provider metadata."""
        return {
            "provider": "gemini",
            "model": "gemini-test",
            "generation_mode": "live_gemini",
        }

    def generate(self, prompt: str) -> dict:
        """Return valid source-cited maintenance actions."""
        return {
            "event_summary": "The fan event should be treated as inspection context.",
            "observed_evidence": ["Expert A flagged the event and Expert B ranks changed."],
            "inspection_priority": "Inspect the fan using retrieved guidance.",
            "recommended_next_actions": [
                {
                    "action": "Inspect the mounting condition and rotating assembly condition.",
                    "reason": "The retrieved approved procedure describes inspection context for abnormal fan noise.",
                    "source_id": "approved_proc",
                    "chunk_id": "approved_proc#chunk-1",
                }
            ],
            "limitations": ["This is inspection guidance only."],
        }


class InventedSourceGenerator(GoodMaintenanceGenerator):
    """Generator that cites a source that was not retrieved."""

    def generate(self, prompt: str) -> dict:
        payload = super().generate(prompt)
        payload["recommended_next_actions"][0]["source_id"] = "invented_source"
        return payload


class InventedChunkGenerator(GoodMaintenanceGenerator):
    """Generator that cites a chunk that was not retrieved."""

    def generate(self, prompt: str) -> dict:
        payload = super().generate(prompt)
        payload["recommended_next_actions"][0]["chunk_id"] = "approved_proc#invented"
        return payload


class ForbiddenDiagnosisGenerator(GoodMaintenanceGenerator):
    """Generator that makes a forbidden component failure claim."""

    def generate(self, prompt: str) -> dict:
        payload = super().generate(prompt)
        payload["recommended_next_actions"][0]["reason"] = "The motor has failed as the root cause."
        return payload


class UnsupportedPercentageGenerator(GoodMaintenanceGenerator):
    """Generator that invents a percentage claim."""

    def generate(self, prompt: str) -> dict:
        payload = super().generate(prompt)
        payload["event_summary"] = "The fan has a 92% fault probability."
        return payload


class MalformedMaintenanceGenerator:
    """Generator that returns malformed payload."""

    def metadata(self) -> dict:
        """Return mock provider metadata."""
        return {"provider": "gemini", "model": "gemini-test"}

    def generate(self, prompt: str) -> dict:
        """Return missing keys."""
        return {"event_summary": "missing action fields"}


class ExceptionMaintenanceGenerator(MalformedMaintenanceGenerator):
    """Generator that simulates provider failure."""

    def generate(self, prompt: str) -> dict:
        """Raise a provider-like exception."""
        raise RuntimeError("provider unavailable")


class FakeGeminiMaintenanceResponse:
    """Fake Google GenAI maintenance response object."""

    parsed = GoodMaintenanceGenerator().generate("prompt")
    text = ""


class FakeGeminiModels:
    """Fake models namespace for the Google GenAI client."""

    def __init__(self) -> None:
        self.calls = []

    def generate_content(self, **kwargs):
        """Record the request and return a fake structured response."""
        self.calls.append(kwargs)
        return FakeGeminiMaintenanceResponse()


class FakeGeminiClient:
    """Fake Google GenAI client."""

    def __init__(self) -> None:
        self.models = FakeGeminiModels()


class MaintenanceAgentTests(unittest.TestCase):
    """Grounded maintenance agent behavior."""

    def test_recommendation_requires_source_evidence(self) -> None:
        output = generate_grounded_maintenance_output(
            _context(),
            retrieval=_retrieval(available=False),
        )
        self.assertEqual(output["mode"], "safe_unavailable")
        self.assertFalse(output["recommendation"]["available"])
        self.assertEqual(output["recommendation"]["citations"], [])
        self.assertEqual(output["metadata"]["generation_mode"], "safe_unavailable")
        self.assertEqual(output["retrieved_maintenance_guidance"], [])

    def test_grounded_output_includes_sources_and_citations(self) -> None:
        output = generate_grounded_maintenance_output(_context(), retrieval=_retrieval())
        self.assertEqual(output["mode"], "source_grounded")
        self.assertTrue(output["recommendation"]["available"])
        self.assertEqual(output["recommendation"]["citations"], ["approved_proc"])
        self.assertEqual(output["recommendation"]["chunk_citations"], ["approved_proc#chunk-1"])
        self.assertTrue(output["metadata"]["fallback_used"])
        self.assertEqual(
            output["retrieved_maintenance_guidance"][0]["source_id"],
            "approved_proc",
        )

    def test_valid_gemini_grounded_response_has_actions_and_metadata(self) -> None:
        output = generate_grounded_maintenance_output(
            _context(),
            retrieval=_retrieval(),
            generator=GoodMaintenanceGenerator(),
            retriever_type="semantic",
            corpus_version="corpus-v1",
        )

        self.assertEqual(output["mode"], "source_grounded")
        self.assertFalse(output["metadata"]["fallback_used"])
        self.assertEqual(output["metadata"]["provider"], "gemini")
        self.assertEqual(output["metadata"]["model"], "gemini-test")
        self.assertEqual(output["metadata"]["retriever_type"], "semantic")
        self.assertEqual(output["metadata"]["corpus_version"], "corpus-v1")
        action = output["recommendation"]["recommended_next_actions"][0]
        self.assertEqual(action["source_id"], "approved_proc")
        self.assertEqual(action["chunk_id"], "approved_proc#chunk-1")

    def test_invented_source_uses_safe_fallback(self) -> None:
        output = generate_grounded_maintenance_output(
            _context(),
            retrieval=_retrieval(),
            generator=InventedSourceGenerator(),
        )
        self.assertTrue(output["metadata"]["fallback_used"])
        self.assertEqual(output["metadata"]["fallback_reason"], "MaintenanceGroundingError")
        self.assertEqual(output["recommendation"]["citations"], ["approved_proc"])

    def test_invented_chunk_uses_safe_fallback(self) -> None:
        output = generate_grounded_maintenance_output(
            _context(),
            retrieval=_retrieval(),
            generator=InventedChunkGenerator(),
        )
        self.assertTrue(output["metadata"]["fallback_used"])
        self.assertEqual(output["recommendation"]["chunk_citations"], ["approved_proc#chunk-1"])

    def test_forbidden_diagnosis_uses_safe_fallback(self) -> None:
        output = generate_grounded_maintenance_output(
            _context(),
            retrieval=_retrieval(),
            generator=ForbiddenDiagnosisGenerator(),
        )
        self.assertTrue(output["metadata"]["fallback_used"])
        text = json.dumps(output["recommendation"]).lower()
        self.assertNotIn("root cause", text)
        self.assertNotIn("motor has failed", text)

    def test_unsupported_percentage_uses_safe_fallback(self) -> None:
        output = generate_grounded_maintenance_output(
            _context(),
            retrieval=_retrieval(),
            generator=UnsupportedPercentageGenerator(),
        )
        self.assertTrue(output["metadata"]["fallback_used"])
        self.assertNotIn("92%", json.dumps(output))

    def test_malformed_json_uses_safe_fallback(self) -> None:
        output = generate_grounded_maintenance_output(
            _context(),
            retrieval=_retrieval(),
            generator=MalformedMaintenanceGenerator(),
        )
        self.assertTrue(output["metadata"]["fallback_used"])
        self.assertEqual(output["metadata"]["fallback_reason"], "MaintenanceGroundingError")

    def test_api_failure_uses_safe_fallback_without_exception_text(self) -> None:
        output = generate_grounded_maintenance_output(
            _context(),
            retrieval=_retrieval(),
            generator=ExceptionMaintenanceGenerator(),
        )
        self.assertTrue(output["metadata"]["fallback_used"])
        self.assertEqual(output["metadata"]["fallback_reason"], "RuntimeError")
        self.assertNotIn("provider unavailable", json.dumps(output))

    def test_missing_citation_is_rejected(self) -> None:
        output = generate_grounded_maintenance_output(_context(), retrieval=_retrieval())
        output["recommendation"]["citations"] = ["missing_source"]
        with self.assertRaises(MaintenanceGroundingError):
            validate_maintenance_output(output)

    def test_missing_chunk_citation_is_rejected(self) -> None:
        output = generate_grounded_maintenance_output(_context(), retrieval=_retrieval())
        output["recommendation"]["recommended_next_actions"][0]["chunk_id"] = "approved_proc#missing"
        with self.assertRaises(MaintenanceGroundingError):
            validate_maintenance_output(output)

    def test_output_avoids_rul_root_cause_and_confidence_claims(self) -> None:
        output = generate_grounded_maintenance_output(_context(), retrieval=_retrieval())
        text = json.dumps(
            {
                "recommendation": output["recommendation"],
                "limitations": output["limitations"],
                "observed_ml_evidence": output["observed_ml_evidence"],
            }
        ).lower()
        self.assertNotIn("rul", text)
        self.assertNotIn("remaining useful life", text)
        self.assertNotIn("time to failure", text)
        self.assertNotIn("root cause", text)
        self.assertNotIn("confidence", text)
        self.assertNotIn("%", text)
        self.assertNotIn("bearing", text)

    def test_retrieval_query_uses_context_attributes(self) -> None:
        query = build_retrieval_query(_context())
        self.assertIn("fan", query)
        self.assertIn("sharpness", query)
        self.assertIn("roughness", query)

    def test_maintenance_prompt_excludes_raw_audio_path(self) -> None:
        prompt = build_maintenance_prompt(
            _context(),
            {"explanation": {"summary": "summary", "observations": [], "hypotheses": [], "limitations": []}},
            _retrieval(),
        )
        self.assertIn("approved_proc#chunk-1", prompt)
        self.assertNotIn(".wav", prompt)
        self.assertNotIn("audio_path", prompt)

    def test_gemini_maintenance_generator_uses_structured_request(self) -> None:
        fake_client = FakeGeminiClient()
        generator = GeminiMaintenanceTextGenerator(
            config=GeminiProviderConfig(model="gemini-test"),
            client=fake_client,
        )
        payload = generator.generate("Return maintenance JSON.")
        self.assertEqual(payload["recommended_next_actions"][0]["source_id"], "approved_proc")
        self.assertEqual(len(fake_client.models.calls), 1)
        call = fake_client.models.calls[0]
        self.assertEqual(call["model"], "gemini-test")
        self.assertEqual(call["contents"], "Return maintenance JSON.")


if __name__ == "__main__":
    unittest.main()
