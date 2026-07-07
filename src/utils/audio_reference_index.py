"""Reference-index utilities for Expert B normal-audio comparisons."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np


@dataclass(frozen=True)
class ReferenceItem:
    """One normal reference clip with metadata, embedding, and timbre values."""

    path: str
    machine_type: str
    machine_id: str
    snr_tag: str
    embedding: list[float]
    timbre_values: dict[str, float]
    section: str | None = None
    domain: str | None = None

    def embedding_array(self) -> np.ndarray:
        """Return the embedding as a NumPy vector."""
        return np.asarray(self.embedding, dtype=np.float32)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable dictionary."""
        return {
            "path": self.path,
            "machine_type": self.machine_type,
            "machine_id": self.machine_id,
            "snr_tag": self.snr_tag,
            "section": self.section,
            "domain": self.domain,
            "embedding": [float(value) for value in self.embedding],
            "timbre_values": {
                key: float(value) for key, value in self.timbre_values.items()
            },
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReferenceItem":
        """Create a reference item from serialized data."""
        return cls(
            path=str(data["path"]),
            machine_type=str(data["machine_type"]),
            machine_id=str(data["machine_id"]),
            snr_tag=str(data["snr_tag"]),
            section=data.get("section"),
            domain=data.get("domain"),
            embedding=[float(value) for value in data["embedding"]],
            timbre_values={
                key: float(value) for key, value in data["timbre_values"].items()
            },
        )


@dataclass(frozen=True)
class ReferenceIndex:
    """A collection of normal reference clips."""

    items: list[ReferenceItem]
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable dictionary."""
        return {
            "metadata": self.metadata,
            "items": [item.to_dict() for item in self.items],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReferenceIndex":
        """Load an index from serialized data."""
        return cls(
            metadata=dict(data.get("metadata", {})),
            items=[ReferenceItem.from_dict(item) for item in data.get("items", [])],
        )


@dataclass(frozen=True)
class Neighbor:
    """A kNN result row."""

    item: ReferenceItem
    distance: float


def build_reference_index(
    normal_paths: Iterable[str | Path],
    *,
    machine_type: str,
    machine_id: str,
    snr_tag: str,
    embedder: Any,
    timbre_fn: Any,
    section: str | None = None,
    domain: str | None = None,
) -> ReferenceIndex:
    """Compute embeddings and timbre values for normal reference WAV files."""
    items: list[ReferenceItem] = []
    for audio_path in normal_paths:
        path = Path(audio_path)
        embedding = embedder.embed_audio(path)
        timbre_values = timbre_fn(path).to_dict()
        items.append(
            ReferenceItem(
                path=str(path),
                machine_type=machine_type,
                machine_id=machine_id,
                snr_tag=snr_tag,
                section=section,
                domain=domain,
                embedding=[float(value) for value in np.asarray(embedding).ravel()],
                timbre_values=timbre_values,
            )
        )
    return ReferenceIndex(
        items=items,
        metadata={
            "machine_type": machine_type,
            "machine_id": machine_id,
            "snr_tag": snr_tag,
            "section": section,
            "domain": domain,
            "embedding_model": "expert_a_bottleneck_adaptation",
            "normal_reference_only": True,
        },
    )


def filter_references(
    reference_index: ReferenceIndex,
    *,
    machine_type: str,
    machine_id: str | None = None,
    snr_tag: str | None = None,
    section: str | None = None,
    domain: str | None = None,
) -> list[ReferenceItem]:
    """Filter references by same-machine metadata."""
    filtered: list[ReferenceItem] = []
    for item in reference_index.items:
        if item.machine_type != machine_type:
            continue
        if machine_id is not None and item.machine_id != machine_id:
            continue
        if snr_tag is not None and item.snr_tag != snr_tag:
            continue
        if section is not None and item.section != section:
            continue
        if domain is not None and item.domain != domain:
            continue
        filtered.append(item)
    return filtered


def _distance(left: np.ndarray, right: np.ndarray, distance: str) -> float:
    """Compute a supported vector distance."""
    if distance == "euclidean":
        return float(np.linalg.norm(left - right))
    if distance == "cosine":
        denom = float(np.linalg.norm(left) * np.linalg.norm(right))
        if denom == 0.0:
            raise ValueError("cosine distance is undefined for zero vectors")
        return float(1.0 - (np.dot(left, right) / denom))
    raise ValueError(f"Unsupported distance: {distance}")


def knn(
    query_embedding: Sequence[float] | np.ndarray,
    references: Sequence[ReferenceItem],
    *,
    k: int,
    distance: str = "euclidean",
) -> list[Neighbor]:
    """Return deterministic nearest normal references."""
    if k <= 0:
        raise ValueError("k must be positive")
    if len(references) < k:
        raise ValueError(f"Need at least {k} references, got {len(references)}")
    query = np.asarray(query_embedding, dtype=np.float32).ravel()
    rows = [
        Neighbor(item=item, distance=_distance(query, item.embedding_array(), distance))
        for item in references
    ]
    return sorted(rows, key=lambda row: (row.distance, row.item.path))[:k]


def save_reference_index(reference_index: ReferenceIndex, path: str | Path) -> None:
    """Save a reference index as UTF-8 JSON."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(reference_index.to_dict(), handle, indent=2)


def load_reference_index(path: str | Path) -> ReferenceIndex:
    """Load a JSON reference index."""
    with Path(path).open("r", encoding="utf-8") as handle:
        return ReferenceIndex.from_dict(json.load(handle))
