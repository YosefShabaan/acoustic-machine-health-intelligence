"""Machine-aware artifact resolution for the Fan Production MVP."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import config as cfg
from models.timbre_difference import DEFAULT_DISTANCE, DEFAULT_K
from rag import default_embedding_index_path


FAN_MACHINE_TYPE = "fan"
FAN_MACHINE_ID = "id_00"
FAN_REAL_INTELLIGENCE_SNR = "minus6dB"
FAN_RAG_CORPUS_VERSION = "AMHI-FAN-MAINT-KB-v1"
FAN_SELECTED_RETRIEVER = "semantic"
EXPERT_A_SNRS = ("minus6dB", "0dB", "plus6dB")


class ArtifactNotRegisteredError(ValueError):
    """Raised when no explicit artifact mapping exists for a requested scope."""


@dataclass(frozen=True)
class ResolvedArtifactConfig:
    """Resolved machine/SNR artifact configuration."""

    machine_type: str
    machine_id: str
    snr_tag: str
    expert_a_model_path: Path
    expert_a_norm_stats_path: Path
    expert_a_available: bool
    expert_b_reference_index_path: Path | None
    expert_b_available: bool
    embedding_model: str
    embedding_status: str
    timbre_model: str
    k: int
    distance: str
    rank_threshold: float | None
    rag_corpus_version: str | None
    rag_retriever_type: str | None
    semantic_index_path: Path | None
    real_intelligence_available: bool

    def require_real_intelligence(self) -> "ResolvedArtifactConfig":
        """Return self or fail if the full Fan intelligence path is unavailable."""
        if not self.real_intelligence_available:
            raise ArtifactNotRegisteredError(
                "Full Real Intelligence artifacts are not registered for "
                f"{self.machine_type}/{self.machine_id}/{self.snr_tag}"
            )
        if self.expert_b_reference_index_path is None or self.semantic_index_path is None:
            raise ArtifactNotRegisteredError(
                "Expert B reference index and semantic RAG index are required for "
                f"{self.machine_type}/{self.machine_id}/{self.snr_tag}"
            )
        return self

    def to_metadata(self) -> dict[str, Any]:
        """Return JSON-safe non-secret artifact metadata."""
        return {
            "machine_type": self.machine_type,
            "machine_id": self.machine_id,
            "snr_tag": self.snr_tag,
            "expert_a_model_id": self.expert_a_model_path.name,
            "expert_a_norm_stats_id": self.expert_a_norm_stats_path.name,
            "expert_b_reference_index_id": (
                self.expert_b_reference_index_path.name
                if self.expert_b_reference_index_path
                else None
            ),
            "embedding_model": self.embedding_model,
            "embedding_status": self.embedding_status,
            "timbre_model": self.timbre_model,
            "k": self.k,
            "distance": self.distance,
            "rank_threshold": self.rank_threshold,
            "rag_corpus_version": self.rag_corpus_version,
            "rag_retriever_type": self.rag_retriever_type,
            "semantic_index_id": (
                self.semantic_index_path.name if self.semantic_index_path else None
            ),
            "real_intelligence_available": self.real_intelligence_available,
        }


class ArtifactRegistry:
    """Resolve verified machine-specific artifacts without silent fallback."""

    def resolve(
        self,
        *,
        machine_type: str,
        machine_id: str,
        snr_tag: str,
    ) -> ResolvedArtifactConfig:
        """Resolve a registered machine/SNR artifact configuration."""
        normalized_machine_type = _normalize_machine_type(machine_type)
        if normalized_machine_type != FAN_MACHINE_TYPE:
            raise ArtifactNotRegisteredError(
                f"No artifacts registered for machine_type={machine_type!r}"
            )
        if machine_id != FAN_MACHINE_ID:
            raise ArtifactNotRegisteredError(
                f"No Fan artifacts registered for machine_id={machine_id!r}"
            )
        if snr_tag not in EXPERT_A_SNRS:
            raise ArtifactNotRegisteredError(
                f"No Fan artifacts registered for snr_tag={snr_tag!r}"
            )

        paths = cfg.ad_paths_for(snr_tag)
        expert_b_reference_index_path: Path | None = None
        semantic_index_path: Path | None = None
        rag_corpus_version: str | None = None
        rag_retriever_type: str | None = None
        real_intelligence_available = False

        if snr_tag == FAN_REAL_INTELLIGENCE_SNR:
            expert_b_reference_index_path = (
                cfg.PROCESSED_DIR
                / f"timbre_reference_index_{FAN_MACHINE_TYPE}_{FAN_MACHINE_ID}_{snr_tag}.json"
            )
            rag_corpus_version = FAN_RAG_CORPUS_VERSION
            rag_retriever_type = FAN_SELECTED_RETRIEVER
            semantic_index_path = default_embedding_index_path(FAN_RAG_CORPUS_VERSION)
            real_intelligence_available = True

        return ResolvedArtifactConfig(
            machine_type=FAN_MACHINE_TYPE,
            machine_id=FAN_MACHINE_ID,
            snr_tag=snr_tag,
            expert_a_model_path=paths["model"],
            expert_a_norm_stats_path=paths["norm_stats"],
            expert_a_available=True,
            expert_b_reference_index_path=expert_b_reference_index_path,
            expert_b_available=expert_b_reference_index_path is not None,
            embedding_model="expert_a_bottleneck_adaptation",
            embedding_status="project_mvp_adaptation_not_paper_encoder",
            timbre_model="AudioCommons timbral_models",
            k=DEFAULT_K,
            distance=DEFAULT_DISTANCE,
            rank_threshold=None,
            rag_corpus_version=rag_corpus_version,
            rag_retriever_type=rag_retriever_type,
            semantic_index_path=semantic_index_path,
            real_intelligence_available=real_intelligence_available,
        )

    def verify_manifest(
        self,
        config: ResolvedArtifactConfig,
        check_hashes: bool = False,
    ) -> None:
        """Verify that required artifacts in the manifest are present and valid."""
        import json
        import hashlib
        
        manifest_path = (
            cfg.DATA_DIR 
            / "manifests" 
            / f"artifact_manifest_{config.machine_type}_{config.machine_id}_{config.snr_tag}.json"
        )
        if not manifest_path.exists():
            raise ArtifactNotRegisteredError(f"Missing artifact manifest: {manifest_path}")
            
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
            
        artifacts = manifest.get("artifacts", [])
        
        for item in artifacts:
            logical_ref = item["logical_reference"]
            expected_checksum = item["checksum"]
            
            # Resolve logical reference against PDM_DATA_ROOT
            artifact_path = cfg.PDM_DATA_ROOT / logical_ref
            
            if not artifact_path.exists():
                raise FileNotFoundError(
                    f"Required artifact missing: {logical_ref} "
                    f"(expected at {artifact_path})"
                )
                
            if check_hashes:
                hasher = hashlib.sha256()
                with open(artifact_path, "rb") as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        hasher.update(chunk)
                actual_checksum = hasher.hexdigest()
                if actual_checksum != expected_checksum:
                    raise ValueError(
                        f"Checksum mismatch for {logical_ref}. "
                        f"Expected: {expected_checksum}, Got: {actual_checksum}"
                    )


def _normalize_machine_type(machine_type: str) -> str:
    return str(machine_type).strip().lower().replace(" ", "_")
