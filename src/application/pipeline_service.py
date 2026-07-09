"""Reusable AMHI Fan pipeline application service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
import re
from pathlib import Path
from time import perf_counter
from typing import Any, Callable

import numpy as np
import torch

import config as cfg
from agents import (
    GeminiMaintenanceTextGenerator,
    GeminiTextGenerator,
    build_retrieval_query,
    explain_context,
    generate_grounded_maintenance_output,
)
from context.translator import context_from_expert_b_output
from data_loader import _extract_logmel
from infrastructure import (
    ArtifactNotRegisteredError,
    ArtifactRegistry,
    AudioStorage,
    LocalAudioStorage,
    ResolvedArtifactConfig,
)
from models.anomaly_detector import compute_threshold, rebuild_validation_tensor
from models.timbre_difference import (
    DEFAULT_DISTANCE,
    DEFAULT_K,
    AcousticTimbreDifferenceExpert,
    ExpertABottleneckEmbedder,
)
from rag import (
    GeminiEmbeddingProvider,
    RetrievalResponse,
    SemanticRetriever,
    load_embedding_index,
)
from utils.audio_reference_index import load_reference_index


CORPUS_VERSION = "AMHI-FAN-MAINT-KB-v1"
PIPELINE_ARCHITECTURE = (
    "audio -> Expert A -> Expert B -> Structured Health Context v0.2 -> "
    "semantic RAG -> Gemini guarded explanation -> Gemini grounded "
    "maintenance -> validation"
)


class UnsupportedMachineScopeError(ArtifactNotRegisteredError):
    """Raised when the Fan Production MVP service receives unsupported scope."""


@dataclass(frozen=True)
class FanPipelineArtifactConfig:
    """Resolved artifacts for the current Fan Production MVP path."""

    reference_index_path: Path
    semantic_index_path: Path


@dataclass
class AMHIPipelineDependencies:
    """Injectable dependencies for fast unit tests and future adapters."""

    reference_index_loader: Callable[[Path], Any] = load_reference_index
    embedder_factory: Callable[..., Any] = ExpertABottleneckEmbedder
    expert_a_scorer: Callable[[Path, Any], dict[str, Any]] = field(
        default_factory=lambda: score_expert_a_event,
    )
    expert_b_factory: Callable[..., Any] = AcousticTimbreDifferenceExpert
    context_builder: Callable[..., dict[str, Any]] = context_from_expert_b_output
    explanation_generator_factory: Callable[[], Any] = GeminiTextGenerator
    explain_fn: Callable[..., dict[str, Any]] = explain_context
    semantic_index_loader: Callable[[Path], Any] = load_embedding_index
    embedding_provider_factory: Callable[[], Any] = GeminiEmbeddingProvider
    semantic_retriever_factory: Callable[..., Any] = SemanticRetriever
    retrieval_fn: Callable[[dict[str, Any], str, int], RetrievalResponse] | None = None
    maintenance_generator_factory: Callable[[], Any] = GeminiMaintenanceTextGenerator
    maintenance_fn: Callable[..., dict[str, Any]] = generate_grounded_maintenance_output


@dataclass
class AMHIPipelineService:
    """Run one Fan event through the reusable AMHI application pipeline."""

    artifacts: FanPipelineArtifactConfig | None = None
    artifact_registry: ArtifactRegistry = field(default_factory=ArtifactRegistry)
    audio_storage: AudioStorage = field(default_factory=LocalAudioStorage)
    dependencies: AMHIPipelineDependencies = field(
        default_factory=AMHIPipelineDependencies,
    )
    k: int = DEFAULT_K
    distance: str = DEFAULT_DISTANCE
    retrieval_top_k: int = 3
    corpus_version: str = CORPUS_VERSION

    def process_event(
        self,
        audio_reference: str | Path,
        machine_type: str,
        machine_id: str,
        snr_tag: str,
        *,
        task_id: str,
    ) -> dict[str, Any]:
        """Process one audio event and return a structured pipeline result."""
        artifact_config = self._resolve_artifacts(machine_type, machine_id, snr_tag)
        if self.k != DEFAULT_K:
            raise ValueError(f"Fan Production MVP preserves Expert B k={DEFAULT_K}")
        if self.distance != DEFAULT_DISTANCE:
            raise ValueError(
                f"Fan Production MVP preserves Expert B distance={DEFAULT_DISTANCE}"
            )
        if artifact_config.k != self.k or artifact_config.distance != self.distance:
            raise ValueError("Resolved Expert B artifact metadata does not match service configuration")
        if artifact_config.rag_retriever_type != "semantic":
            raise ValueError("Fan Production MVP requires the selected semantic retriever")
        if artifact_config.rag_corpus_version != self.corpus_version:
            raise ValueError("Resolved RAG corpus version does not match service configuration")

        audio_metadata = self.audio_storage.resolve(audio_reference)
        audio_path = audio_metadata.processing_path
        timings: dict[str, float] = {}
        total_start = perf_counter()

        start = perf_counter()
        reference_index = self.dependencies.reference_index_loader(
            artifact_config.expert_b_reference_index_path,
        )
        embedder = self.dependencies.embedder_factory(snr_tag=snr_tag)
        timings["load_reference_index_and_embedder_seconds"] = perf_counter() - start

        start = perf_counter()
        expert_a = self.dependencies.expert_a_scorer(audio_path, embedder)
        timings["audio_expert_a_seconds"] = perf_counter() - start

        if not bool(expert_a.get("is_anomaly")):
            timings["total_seconds"] = perf_counter() - total_start
            return self._unflagged_result(
                task_id=task_id,
                machine_type=machine_type,
                machine_id=machine_id,
                snr_tag=snr_tag,
                audio_path=audio_path,
                expert_a=expert_a,
                timings=timings,
                artifacts=artifact_config,
                audio_storage_metadata=audio_metadata.to_dict(),
            )

        start = perf_counter()
        expert = self.dependencies.expert_b_factory(
            reference_index=reference_index,
            embedder=embedder,
            k=self.k,
            distance=self.distance,
            rank_threshold=None,
        )
        expert_b_output = expert.characterize(
            audio_path=audio_path,
            machine_type=machine_type,
            machine_id=machine_id,
            snr_tag=snr_tag,
            expert_a=expert_a,
        )
        timings["expert_b_seconds"] = perf_counter() - start

        created_at = datetime.now(UTC).isoformat()
        task_token = re.sub(r"[^a-z0-9]+", "_", task_id.lower()).strip("_")
        analysis_run_id = (
            f"analysis_{machine_type}_{machine_id}_{snr_tag}_{audio_path.stem}_{task_token}"
        )

        start = perf_counter()
        pre_context = self.dependencies.context_builder(
            expert_b_output,
            created_at=created_at,
            analysis_run_id=analysis_run_id,
            reference_index_path=artifact_config.expert_b_reference_index_path,
        )
        timings["context_translation_seconds"] = perf_counter() - start

        start = perf_counter()
        explanation = self.dependencies.explain_fn(
            pre_context,
            generator=self.dependencies.explanation_generator_factory(),
        )
        timings["gemini_explanation_seconds"] = perf_counter() - start

        start = perf_counter()
        retrieval_query = build_retrieval_query(pre_context)
        retrieval = self._retrieve(pre_context, retrieval_query, artifact_config)
        timings["retrieval_seconds"] = perf_counter() - start

        start = perf_counter()
        technician_output = self.dependencies.maintenance_fn(
            pre_context,
            explanation=explanation,
            retrieval=retrieval,
            generator=self.dependencies.maintenance_generator_factory(),
            retriever_type="semantic",
            corpus_version=self.corpus_version,
        )
        timings["gemini_maintenance_seconds"] = perf_counter() - start

        start = perf_counter()
        final_context = self.dependencies.context_builder(
            expert_b_output,
            created_at=created_at,
            analysis_run_id=analysis_run_id,
            reference_index_path=artifact_config.expert_b_reference_index_path,
            llm_metadata=explanation.get("metadata"),
            rag_metadata={
                "retriever_type": "semantic",
                "corpus_version": self.corpus_version,
                "retrieval_query": retrieval_query,
            },
            maintenance_metadata=technician_output.get("metadata"),
        )
        timings["context_provenance_update_seconds"] = perf_counter() - start
        timings["total_seconds"] = perf_counter() - total_start

        return {
            "task": task_id,
            "pipeline_status": "completed",
            "architecture": PIPELINE_ARCHITECTURE,
            "machine_scope": {
                "machine_type": machine_type,
                "machine_id": machine_id,
                "snr_tag": snr_tag,
            },
            "audio_path": str(audio_path),
            "audio_storage": audio_metadata.to_dict(),
            "reference_index_path": str(artifact_config.expert_b_reference_index_path),
            "semantic_index_path": str(artifact_config.semantic_index_path),
            "artifact_metadata": artifact_config.to_metadata(),
            "retrieval_top_k": self.retrieval_top_k,
            "retrieval_query": retrieval_query,
            "expert_a": expert_a,
            "expert_b_output": expert_b_output,
            "structured_context": final_context,
            "guarded_explanation": explanation,
            "retrieval": retrieval.to_dict(),
            "technician_output": technician_output,
            "limits": {
                "same_machine_same_audio": True,
                "rank_scores_are_probabilities": False,
                "physical_root_cause_confirmed": False,
                "remaining_life_prediction_available": False,
                "production_maintenance_validation_complete": False,
                "multi_machine_generalization_enabled": False,
                "free_text_change_is_scientific_improvement": False,
            },
            "timings": timings,
        }

    def _retrieve(
        self,
        context: dict[str, Any],
        retrieval_query: str,
        artifacts: ResolvedArtifactConfig,
    ) -> RetrievalResponse:
        if self.dependencies.retrieval_fn is not None:
            return self.dependencies.retrieval_fn(
                context,
                retrieval_query,
                self.retrieval_top_k,
            )
        semantic_index = self.dependencies.semantic_index_loader(
            artifacts.semantic_index_path,
        )
        retriever = self.dependencies.semantic_retriever_factory(
            semantic_index,
            self.dependencies.embedding_provider_factory(),
        )
        return retriever.retrieve(retrieval_query, top_k=self.retrieval_top_k)

    def _resolve_artifacts(
        self,
        machine_type: str,
        machine_id: str,
        snr_tag: str,
    ) -> ResolvedArtifactConfig:
        registered = self.artifact_registry.resolve(
            machine_type=machine_type,
            machine_id=machine_id,
            snr_tag=snr_tag,
        ).require_real_intelligence()
        if self.artifacts is not None:
            return ResolvedArtifactConfig(
                machine_type=registered.machine_type,
                machine_id=registered.machine_id,
                snr_tag=registered.snr_tag,
                expert_a_model_path=registered.expert_a_model_path,
                expert_a_norm_stats_path=registered.expert_a_norm_stats_path,
                expert_a_available=registered.expert_a_available,
                expert_b_reference_index_path=self.artifacts.reference_index_path,
                expert_b_available=True,
                embedding_model=registered.embedding_model,
                embedding_status=registered.embedding_status,
                timbre_model=registered.timbre_model,
                k=registered.k,
                distance=registered.distance,
                rank_threshold=registered.rank_threshold,
                rag_corpus_version=registered.rag_corpus_version,
                rag_retriever_type=registered.rag_retriever_type,
                semantic_index_path=self.artifacts.semantic_index_path,
                real_intelligence_available=True,
            )
        return registered

    def _unflagged_result(
        self,
        *,
        task_id: str,
        machine_type: str,
        machine_id: str,
        snr_tag: str,
        audio_path: Path,
        expert_a: dict[str, Any],
        timings: dict[str, float],
        artifacts: ResolvedArtifactConfig,
        audio_storage_metadata: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "task": task_id,
            "pipeline_status": "expert_a_not_flagged",
            "architecture": PIPELINE_ARCHITECTURE,
            "machine_scope": {
                "machine_type": machine_type,
                "machine_id": machine_id,
                "snr_tag": snr_tag,
            },
            "audio_path": str(audio_path),
            "audio_storage": audio_storage_metadata,
            "reference_index_path": str(artifacts.expert_b_reference_index_path),
            "semantic_index_path": str(artifacts.semantic_index_path),
            "artifact_metadata": artifacts.to_metadata(),
            "expert_a": expert_a,
            "expert_b_skipped": {
                "skipped": True,
                "reason": "expert_a_not_anomaly",
            },
            "expert_b_output": None,
            "structured_context": None,
            "guarded_explanation": None,
            "retrieval": None,
            "technician_output": None,
            "limits": {
                "same_machine_same_audio": True,
                "rank_scores_are_probabilities": False,
                "physical_root_cause_confirmed": False,
                "remaining_life_prediction_available": False,
                "production_maintenance_validation_complete": False,
                "multi_machine_generalization_enabled": False,
            },
            "timings": timings,
        }


def score_expert_a_event(
    audio_path: Path,
    embedder: ExpertABottleneckEmbedder,
) -> dict[str, Any]:
    """Score one audio file with the existing Expert A model."""
    val_tensor = rebuild_validation_tensor(snr_tag=embedder.snr_tag)
    threshold, _ = compute_threshold(embedder.model, val_tensor)
    tensor = _model_input_for_audio(audio_path, embedder.mean, embedder.std)
    with torch.no_grad():
        reconstruction = embedder.model(tensor)
        score = torch.mean((reconstruction - tensor) ** 2).item()
    return {
        "anomaly_score": float(score),
        "threshold": float(threshold),
        "is_anomaly": bool(score > threshold),
    }


def _model_input_for_audio(
    audio_path: Path,
    mean: np.ndarray,
    std: np.ndarray,
) -> torch.Tensor:
    """Build normalized Expert A tensor for one audio file."""
    spec = _extract_logmel(audio_path)[None, :, :]
    model_input = np.transpose(spec, (0, 2, 1)).astype(np.float32)
    model_input = ((model_input - mean[None, :, None]) / std[None, :, None]).astype(
        np.float32,
    )
    return torch.from_numpy(model_input).float()
