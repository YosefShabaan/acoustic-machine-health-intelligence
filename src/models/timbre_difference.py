"""Expert B: same-audio acoustic timbre difference characterization.

This module implements a bounded Nishida et al. 2024 adaptation for this
repository. The paper's kNN/rank rule is used, but the embedding model is the
existing Expert A bottleneck, not one of the paper's experimental encoders.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Protocol, Sequence
import sys
import time

import numpy as np
import soundfile as sf
import torch
from torch.nn import functional as F

SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import config as cfg  # noqa: E402
from data_loader import _extract_logmel  # noqa: E402
from models.anomaly_detector import ConvAutoencoder  # noqa: E402
from utils.audio_reference_index import ReferenceIndex, filter_references, knn  # noqa: E402


TIMBRE_ATTRIBUTES = ("sharpness", "roughness", "boominess", "brightness", "depth")
DEFAULT_K = 30
DEFAULT_DISTANCE = "euclidean"
EMBEDDING_MODEL_NAME = "expert_a_bottleneck_adaptation"
METHOD_STATUS = "adaptation_not_exact_reproduction"


class AudioEmbedder(Protocol):
    """Protocol for audio embedding adapters used by Expert B."""

    def embed_audio(self, audio_path: str | Path) -> np.ndarray:
        """Return a one-dimensional embedding for an audio file."""


@dataclass(frozen=True)
class TimbreValues:
    """Five AudioCommons timbre metric values used by Nishida et al."""

    sharpness: float
    roughness: float
    boominess: float
    brightness: float
    depth: float

    def to_dict(self) -> dict[str, float]:
        """Return a JSON-serializable dictionary."""
        return asdict(self)


def _finite_float(value: Any, name: str) -> float:
    """Convert a timbre output to a finite Python float."""
    result = float(value)
    if not np.isfinite(result):
        raise ValueError(f"{name} produced a non-finite timbre value: {result}")
    return result


def compute_timbre_values(audio_path: str | Path) -> TimbreValues:
    """Compute the five paper attributes using AudioCommons timbral models."""
    values, _ = compute_timbre_values_timed(audio_path, reuse_loaded_audio=False)
    return values


def _timbral_functions() -> dict[str, Any]:
    """Load AudioCommons timbral metric functions."""
    try:
        import timbral_models
    except ImportError as exc:
        raise ImportError(
            "timbral_models is required for Expert B. Install the dependency "
            "from requirements.txt before running timbre characterization."
        ) from exc
    return {
        "sharpness": timbral_models.timbral_sharpness,
        "roughness": timbral_models.timbral_roughness,
        "boominess": timbral_models.timbral_booming,
        "brightness": timbral_models.timbral_brightness,
        "depth": timbral_models.timbral_depth,
    }


def _compute_timbre_values_from_source(
    source: str | np.ndarray,
    *,
    sample_rate: int | float = 0,
) -> tuple[TimbreValues, dict[str, float]]:
    """Compute timbre values from a file path or official array+fs API."""
    functions = _timbral_functions()
    timings: dict[str, float] = {}
    results: dict[str, float] = {}
    for attribute, function in functions.items():
        start = time.perf_counter()
        if sample_rate:
            value = function(source, fs=sample_rate)
        else:
            value = function(source)
        timings[attribute] = time.perf_counter() - start
        results[attribute] = _finite_float(value, attribute)
    return TimbreValues(
        sharpness=results["sharpness"],
        roughness=results["roughness"],
        boominess=results["boominess"],
        brightness=results["brightness"],
        depth=results["depth"],
    ), timings


def compute_timbre_values_from_audio(
    audio_samples: np.ndarray,
    sample_rate: int | float,
) -> TimbreValues:
    """Compute timbre values using the official array+sample-rate API."""
    values, _ = _compute_timbre_values_from_source(
        audio_samples,
        sample_rate=sample_rate,
    )
    return values


def compute_timbre_values_timed(
    audio_path: str | Path,
    *,
    reuse_loaded_audio: bool = False,
) -> tuple[TimbreValues, dict[str, float]]:
    """Compute timbre values and return per-stage timings.

    ``reuse_loaded_audio=False`` preserves the original path-based behavior:
    each AudioCommons metric receives the file path and performs its own
    internal file read/preprocessing.
    """
    total_start = time.perf_counter()
    path_text = str(Path(audio_path))
    timings: dict[str, float] = {"audio_load": 0.0}
    if reuse_loaded_audio:
        load_start = time.perf_counter()
        audio_samples, sample_rate = sf.read(path_text, always_2d=False)
        timings["audio_load"] = time.perf_counter() - load_start
        values, metric_timings = _compute_timbre_values_from_source(
            audio_samples,
            sample_rate=sample_rate,
        )
    else:
        values, metric_timings = _compute_timbre_values_from_source(path_text)
    timings.update(metric_timings)
    timings["timbre_total"] = sum(metric_timings.values()) + timings["audio_load"]
    timings["total"] = time.perf_counter() - total_start
    return values, timings


def rank_score(test_value: float, reference_values: Sequence[float]) -> float:
    """Return Nishida rank score ``(r - 1) / k`` for one timbre value.

    The paper does not define tie handling. This implementation uses a stable
    lower-rank insertion policy: references strictly below the test value count
    toward ``r - 1``; equal values do not.
    """
    if not reference_values:
        raise ValueError("reference_values must not be empty")
    test = _finite_float(test_value, "test_value")
    refs = np.asarray(reference_values, dtype=np.float64)
    if not np.all(np.isfinite(refs)):
        raise ValueError("reference_values must all be finite")
    below_count = int(np.sum(refs < test))
    return float(below_count / len(refs))


def direction_from_rank(
    score: float,
    threshold: float | None,
) -> tuple[str | None, int | None]:
    """Convert a rank score to a direction only when threshold is configured."""
    score_value = _finite_float(score, "score")
    if score_value < 0.0 or score_value > 1.0:
        raise ValueError(f"score must be in [0, 1], got {score_value}")
    if threshold is None:
        return None, None
    threshold_value = _finite_float(threshold, "threshold")
    if threshold_value < 0.0 or threshold_value > 0.5:
        raise ValueError("threshold must be in [0, 0.5]")
    if score_value <= threshold_value:
        return "decreased", -1
    if score_value >= 1.0 - threshold_value:
        return "increased", 1
    return "unchanged", 0


class ExpertABottleneckEmbedder:
    """Embedding adapter using the existing Expert A 128-d bottleneck."""

    def __init__(
        self,
        snr_tag: str = "minus6dB",
        model_path: str | Path | None = None,
        norm_stats_path: str | Path | None = None,
    ) -> None:
        """Load Expert A without changing its architecture or training logic."""
        self.snr_tag = snr_tag
        paths = cfg.ad_paths_for(snr_tag)
        self.model_path = Path(model_path) if model_path is not None else paths["model"]
        self.norm_stats_path = (
            Path(norm_stats_path) if norm_stats_path is not None else paths["norm_stats"]
        )
        if not self.model_path.is_file():
            raise FileNotFoundError(f"Expert A model not found: {self.model_path}")
        if not self.norm_stats_path.is_file():
            raise FileNotFoundError(
                f"Expert A normalization stats not found: {self.norm_stats_path}"
            )

        self.device = torch.device("cpu")
        self.model = ConvAutoencoder().to(self.device)
        state = torch.load(self.model_path, map_location=self.device)
        self.model.load_state_dict(state)
        self.model.eval()

        stats = np.load(self.norm_stats_path)
        self.mean = stats["mean"].astype(np.float32)
        self.std = stats["std"].astype(np.float32)

    @property
    def metadata(self) -> dict[str, Any]:
        """Return method metadata for outputs."""
        return {
            "embedding_model": EMBEDDING_MODEL_NAME,
            "embedding_dim": cfg.AD_LATENT_DIM,
            "embedding_status": "project_mvp_adaptation_not_paper_encoder",
            "model_path": str(self.model_path),
            "norm_stats_path": str(self.norm_stats_path),
            "snr_tag": self.snr_tag,
        }

    def embed_audio(self, audio_path: str | Path) -> np.ndarray:
        """Return the activated 128-dimensional Expert A bottleneck vector."""
        spec = _extract_logmel(Path(audio_path))[None, :, :]
        model_input = np.transpose(spec, (0, 2, 1)).astype(np.float32)
        model_input = ((model_input - self.mean[None, :, None]) / self.std[None, :, None]).astype(
            np.float32
        )
        tensor = torch.from_numpy(model_input).float().to(self.device)
        with torch.no_grad():
            encoded = self.model.encoder(tensor)
            flat = torch.flatten(encoded, start_dim=1)
            latent = self.model.bottleneck[1](flat)
            latent = F.relu(latent)
        embedding = latent.detach().cpu().numpy()[0].astype(np.float32)
        if embedding.shape != (cfg.AD_LATENT_DIM,):
            raise ValueError(
                f"Expected Expert A bottleneck shape {(cfg.AD_LATENT_DIM,)}, "
                f"got {embedding.shape}"
            )
        return embedding


class AcousticTimbreDifferenceExpert:
    """Characterize timbre differences against same-machine normal references."""

    def __init__(
        self,
        reference_index: ReferenceIndex,
        embedder: AudioEmbedder,
        k: int = DEFAULT_K,
        distance: str = DEFAULT_DISTANCE,
        rank_threshold: float | None = None,
    ) -> None:
        """Create the Expert B orchestrator."""
        if k <= 0:
            raise ValueError("k must be positive")
        self.reference_index = reference_index
        self.embedder = embedder
        self.k = k
        self.distance = distance
        self.rank_threshold = rank_threshold

    def characterize(
        self,
        audio_path: str | Path,
        machine_type: str,
        machine_id: str,
        snr_tag: str,
        expert_a: dict[str, Any],
        test_timbre_values: TimbreValues | None = None,
    ) -> dict[str, Any]:
        """Return JSON-serializable timbre difference characterization."""
        if not bool(expert_a.get("is_anomaly", False)):
            raise ValueError("Expert B requires Expert A to mark the same audio as anomalous")

        filtered = filter_references(
            self.reference_index,
            machine_type=machine_type,
            machine_id=machine_id,
            snr_tag=snr_tag,
        )
        if len(filtered) < self.k:
            raise ValueError(
                f"Need at least k={self.k} normal references after filtering; "
                f"found {len(filtered)}"
            )

        query_embedding = self.embedder.embed_audio(audio_path)
        neighbors = knn(query_embedding, filtered, k=self.k, distance=self.distance)
        selected_items = [neighbor.item for neighbor in neighbors]
        test_values = test_timbre_values or compute_timbre_values(audio_path)
        test_dict = test_values.to_dict()

        differences: dict[str, dict[str, Any]] = {}
        for attribute in TIMBRE_ATTRIBUTES:
            reference_values = [
                float(item.timbre_values[attribute])
                for item in selected_items
            ]
            score = rank_score(float(test_dict[attribute]), reference_values)
            direction, direction_code = direction_from_rank(score, self.rank_threshold)
            differences[attribute] = {
                "test_value": float(test_dict[attribute]),
                "reference_values": reference_values,
                "rank_score": score,
                "direction": direction,
                "direction_code": direction_code,
            }

        embedder_metadata = getattr(self.embedder, "metadata", {})
        return {
            "expert": "AcousticTimbreDifferenceExpert",
            "method": {
                "paper": "Nishida et al. 2024, arXiv:2410.22033",
                "status": METHOD_STATUS,
                "embedding_model": EMBEDDING_MODEL_NAME,
                "embedding_status": "project_mvp_adaptation_not_paper_encoder",
                "embedding_metadata": embedder_metadata,
                "timbre_model": "AudioCommons timbral_models",
                "k": self.k,
                "k_note": "Paper experimental setting k=30; paper reports similar results around k=10-40.",
                "distance": self.distance,
                "distance_note": (
                    "Euclidean distance is a project implementation choice supported "
                    "by the paper's generic distance formulation; Nishida et al. do "
                    "not mandate Euclidean distance."
                ),
                "rank_threshold": self.rank_threshold,
            },
            "input_audio": {
                "path": str(Path(audio_path)),
                "machine_type": machine_type,
                "machine_id": machine_id,
                "snr_tag": snr_tag,
            },
            "expert_a": {
                "anomaly_score": float(expert_a["anomaly_score"]),
                "threshold": float(expert_a["threshold"]),
                "is_anomaly": bool(expert_a["is_anomaly"]),
            },
            "references": {
                "pool_size": len(filtered),
                "selected_count": len(neighbors),
                "filter": {
                    "machine_type": machine_type,
                    "machine_id": machine_id,
                    "snr_tag": snr_tag,
                },
                "neighbors": [
                    {
                        "path": str(neighbor.item.path),
                        "distance": float(neighbor.distance),
                        "rank": index + 1,
                    }
                    for index, neighbor in enumerate(neighbors)
                ],
            },
            "timbre_differences": differences,
            "warnings": [
                "No paper-specific timbre ground-truth labels available; output is qualitative characterization only.",
                "Expert A bottleneck embedding is a project MVP adaptation, not a Nishida paper encoder.",
                "rank_threshold is not configured; direction and direction_code are null by design.",
            ],
        }
