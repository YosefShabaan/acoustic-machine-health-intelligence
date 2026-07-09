"""Tests for the reusable AMHI Fan pipeline service."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from application import (  # noqa: E402
    AMHIPipelineDependencies,
    AMHIPipelineService,
    FanPipelineArtifactConfig,
)
from infrastructure import ArtifactNotRegisteredError  # noqa: E402
from rag import RetrievalResponse, RetrievalResult  # noqa: E402


AUDIO_PATH = Path(r"D:\PDM_Data\MIMII\fan_minus6dB\id_00\abnormal\00000002.wav")


def _dependencies(
    *,
    flagged: bool = True,
    explanation_fallback: bool = False,
    maintenance_fallback: bool = False,
    calls: dict[str, int] | None = None,
) -> AMHIPipelineDependencies:
    counters = calls if calls is not None else {}

    def count(name: str) -> None:
        counters[name] = counters.get(name, 0) + 1

    def scorer(audio_path: Path, embedder: object) -> dict:
        count("expert_a")
        return {
            "anomaly_score": 0.622095 if flagged else 0.2,
            "threshold": 0.593284,
            "is_anomaly": flagged,
        }

    def expert_b_factory(**kwargs: object) -> object:
        count("expert_b")

        class FakeExpertB:
            def characterize(
                self,
                *,
                audio_path: Path,
                machine_type: str,
                machine_id: str,
                snr_tag: str,
                expert_a: dict,
            ) -> dict:
                return _expert_b_output(
                    audio_path=audio_path,
                    machine_type=machine_type,
                    machine_id=machine_id,
                    snr_tag=snr_tag,
                    expert_a=expert_a,
                )

        return FakeExpertB()

    def explain_fn(context: dict, *, generator: object | None = None) -> dict:
        count("explain")
        return {
            "agent": "DiagnosticExplanationAgent",
            "mode": "live_gemini",
            "prompt": "Event ID only.",
            "explanation": {
                "summary": "The fan event was flagged as acoustic evidence.",
                "observations": ["Expert A flagged the event."],
                "hypotheses": ["Use this as inspection context."],
                "limitations": ["No component finding is confirmed."],
            },
            "metadata": {
                "provider": "gemini",
                "model": "gemini-test",
                "prompt_version": "diagnostic-test",
                "generation_mode": (
                    "deterministic_fallback" if explanation_fallback else "live_gemini"
                ),
                "fallback_used": explanation_fallback,
            },
        }

    def retrieval_fn(context: dict, query: str, top_k: int) -> RetrievalResponse:
        count("retrieval")
        result = RetrievalResult(
            source_id="approved_proc",
            title="Approved Fan Procedure",
            version="2026-07",
            chunk_id="approved_proc#chunk-1",
            snippet="Inspect mounting condition for abnormal fan acoustic evidence.",
            score=0.8,
            path=Path("procedure.md"),
            publisher="Approved Publisher",
            corpus_version="AMHI-FAN-MAINT-KB-v1",
            section_id="chunk-1",
            section_heading="Inspection",
        )
        return RetrievalResponse(
            query=query,
            available=True,
            results=(result,),
            message="Retrieved 1 approved source chunk.",
        )

    def maintenance_fn(
        context: dict,
        *,
        explanation: dict,
        retrieval: RetrievalResponse,
        generator: object | None = None,
        retriever_type: str | None = None,
        corpus_version: str | None = None,
    ) -> dict:
        count("maintenance")
        return {
            "agent": "GroundedMaintenanceAgent",
            "mode": "source_grounded",
            "event": {
                "event_id": context["event"]["event_id"],
                "asset_id": context["event"]["asset_id"],
                "machine_type": context["event"]["machine_type"],
                "machine_id": context["event"]["machine_id"],
                "snr_tag": context["event"]["snr_tag"],
            },
            "observed_ml_evidence": {"expert_a": context["expert_a"]},
            "technician_explanation": explanation["explanation"],
            "retrieved_maintenance_guidance": [
                result.to_dict() for result in retrieval.results
            ],
            "recommendation": {
                "available": True,
                "event_summary": "Use the acoustic evidence as inspection context.",
                "observed_evidence": ["Expert A flagged the event."],
                "inspection_priority": "Inspect the fan using approved guidance.",
                "recommended_next_actions": [
                    {
                        "action": "Inspect mounting condition.",
                        "reason": "The retrieved guidance supports inspection context.",
                        "source_id": "approved_proc",
                        "chunk_id": "approved_proc#chunk-1",
                    }
                ],
                "citations": ["approved_proc"],
                "chunk_citations": ["approved_proc#chunk-1"],
                "text": "Use the acoustic evidence as inspection context. Next actions: Inspect mounting condition.",
                "limitations": ["Inspection context only."],
            },
            "limitations": ["No component finding is confirmed."],
            "metadata": {
                "provider": "gemini",
                "model": "gemini-test",
                "prompt_version": "maintenance-test",
                "generation_mode": (
                    "deterministic_fallback" if maintenance_fallback else "live_gemini"
                ),
                "fallback_used": maintenance_fallback,
                "retriever_type": retriever_type,
                "corpus_version": corpus_version,
            },
            "prompt": "Event ID only.",
        }

    return AMHIPipelineDependencies(
        reference_index_loader=lambda path: {"path": path},
        embedder_factory=lambda snr_tag: SimpleNamespace(snr_tag=snr_tag),
        expert_a_scorer=scorer,
        expert_b_factory=expert_b_factory,
        explanation_generator_factory=lambda: object(),
        explain_fn=explain_fn,
        retrieval_fn=retrieval_fn,
        maintenance_generator_factory=lambda: object(),
        maintenance_fn=maintenance_fn,
    )


def _service(
    dependencies: AMHIPipelineDependencies,
) -> AMHIPipelineService:
    return AMHIPipelineService(
        artifacts=FanPipelineArtifactConfig(
            reference_index_path=Path(
                r"D:\PDM_Data\MIMII\processed\timbre_reference_index_fan_id_00_minus6dB.json"
            ),
            semantic_index_path=Path(
                r"D:\PDM_Data\MIMII\processed\rag_semantic_index_AMHI-FAN-MAINT-KB-v1_gemini-embedding-2_768.json"
            ),
        ),
        dependencies=dependencies,
    )


def _expert_b_output(
    *,
    audio_path: Path,
    machine_type: str,
    machine_id: str,
    snr_tag: str,
    expert_a: dict,
) -> dict:
    rank_rows = {
        "sharpness": 0.9333333333333333,
        "roughness": 0.9333333333333333,
        "boominess": 0.0,
        "brightness": 0.9333333333333333,
        "depth": 0.6666666666666666,
    }
    return {
        "expert": "AcousticTimbreDifferenceExpert",
        "method": {
            "paper": "Nishida et al. 2024, arXiv:2410.22033",
            "status": "adaptation_not_exact_reproduction",
            "embedding_model": "expert_a_bottleneck_adaptation",
            "embedding_status": "project_mvp_adaptation_not_paper_encoder",
            "embedding_metadata": {},
            "timbre_model": "AudioCommons timbral_models",
            "k": 30,
            "distance": "euclidean",
            "rank_threshold": None,
        },
        "input_audio": {
            "path": str(audio_path),
            "machine_type": machine_type,
            "machine_id": machine_id,
            "snr_tag": snr_tag,
        },
        "expert_a": expert_a,
        "references": {
            "pool_size": 40,
            "selected_count": 30,
            "filter": {
                "machine_type": machine_type,
                "machine_id": machine_id,
                "snr_tag": snr_tag,
            },
            "neighbors": [
                {
                    "path": rf"D:\PDM_Data\MIMII\fan_minus6dB\id_00\normal\{idx:08d}.wav",
                    "distance": float(idx),
                    "rank": idx,
                }
                for idx in range(1, 31)
            ],
        },
        "timbre_differences": {
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
    }


class AMHIPipelineServiceTests(unittest.TestCase):
    """Pipeline service behavior without live artifacts or Gemini calls."""

    def test_unflagged_event_skips_expert_b_and_downstream(self) -> None:
        calls: dict[str, int] = {}
        service = _service(_dependencies(flagged=False, calls=calls))

        result = service.process_event(
            AUDIO_PATH,
            machine_type="fan",
            machine_id="id_00",
            snr_tag="minus6dB",
            task_id="TASK-PROD-02-TEST",
        )

        self.assertEqual(result["pipeline_status"], "expert_a_not_flagged")
        self.assertEqual(result["expert_b_skipped"]["reason"], "expert_a_not_anomaly")
        self.assertIsNone(result["expert_b_output"])
        self.assertIsNone(result["structured_context"])
        self.assertEqual(calls.get("expert_a"), 1)
        self.assertNotIn("expert_b", calls)
        self.assertNotIn("explain", calls)
        self.assertNotIn("retrieval", calls)
        self.assertNotIn("maintenance", calls)

    def test_flagged_event_runs_full_path_and_preserves_same_audio_identity(self) -> None:
        result = _service(_dependencies()).process_event(
            AUDIO_PATH,
            machine_type="fan",
            machine_id="id_00",
            snr_tag="minus6dB",
            task_id="TASK-PROD-02-TEST",
        )

        self.assertEqual(result["pipeline_status"], "completed")
        self.assertEqual(result["expert_b_output"]["input_audio"]["path"], str(AUDIO_PATH))
        self.assertEqual(result["structured_context"]["event"]["audio_path"], str(AUDIO_PATH))
        self.assertEqual(
            result["technician_output"]["event"]["event_id"],
            result["structured_context"]["event"]["event_id"],
        )
        self.assertEqual(
            result["structured_context"]["expert_b"]["method"]["rank_threshold"],
            None,
        )

    def test_retrieval_and_fallback_metadata_propagate_to_context(self) -> None:
        result = _service(
            _dependencies(explanation_fallback=True, maintenance_fallback=True),
        ).process_event(
            AUDIO_PATH,
            machine_type="fan",
            machine_id="id_00",
            snr_tag="minus6dB",
            task_id="TASK-PROD-02-TEST",
        )

        analysis = result["structured_context"]["analysis"]
        self.assertEqual(analysis["rag"]["retriever_type"], "semantic")
        self.assertEqual(analysis["rag"]["corpus_version"], "AMHI-FAN-MAINT-KB-v1")
        self.assertIn("fan abnormal acoustic noise inspection", analysis["rag"]["retrieval_query"])
        self.assertTrue(analysis["llm"]["fallback_used"])
        self.assertTrue(analysis["maintenance"]["fallback_used"])

    def test_stage_timings_are_present_for_full_path(self) -> None:
        result = _service(_dependencies()).process_event(
            AUDIO_PATH,
            machine_type="fan",
            machine_id="id_00",
            snr_tag="minus6dB",
            task_id="TASK-PROD-02-TEST",
        )

        for key in (
            "load_reference_index_and_embedder_seconds",
            "audio_expert_a_seconds",
            "expert_b_seconds",
            "context_translation_seconds",
            "gemini_explanation_seconds",
            "retrieval_seconds",
            "gemini_maintenance_seconds",
            "context_provenance_update_seconds",
            "total_seconds",
        ):
            self.assertIn(key, result["timings"])
            self.assertIsInstance(result["timings"][key], float)

    def test_unsupported_machine_scope_is_rejected(self) -> None:
        service = _service(_dependencies())
        with self.assertRaises(ArtifactNotRegisteredError):
            service.process_event(
                AUDIO_PATH,
                machine_type="pump",
                machine_id="id_00",
                snr_tag="minus6dB",
                task_id="TASK-PROD-02-TEST",
            )


if __name__ == "__main__":
    unittest.main()
