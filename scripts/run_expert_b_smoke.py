"""Run an Expert A -> Expert B same-audio smoke test."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

import numpy as np
import torch

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import config as cfg  # noqa: E402
from data_loader import _extract_logmel  # noqa: E402
from models.anomaly_detector import compute_threshold, rebuild_validation_tensor  # noqa: E402
from models.timbre_difference import (  # noqa: E402
    DEFAULT_DISTANCE,
    DEFAULT_K,
    AcousticTimbreDifferenceExpert,
    ExpertABottleneckEmbedder,
)
from utils.audio_reference_index import load_reference_index  # noqa: E402


def _default_index(machine_type: str, machine_id: str, snr_tag: str) -> Path:
    """Return the workspace-local default reference index path."""
    return (
        cfg.DATA_DIR
        / "processed"
        / f"timbre_reference_index_{machine_type}_{machine_id}_{snr_tag}.json"
    )


def _default_output(snr_tag: str) -> Path:
    """Return the workspace-local default smoke output path."""
    return cfg.DATA_DIR / "processed" / f"expert_b_smoke_{snr_tag}.json"


def _model_input_for_audio(
    audio_path: Path,
    mean: np.ndarray,
    std: np.ndarray,
) -> torch.Tensor:
    """Build normalized Expert A tensor for one audio file."""
    spec = _extract_logmel(audio_path)[None, :, :]
    model_input = np.transpose(spec, (0, 2, 1)).astype(np.float32)
    model_input = ((model_input - mean[None, :, None]) / std[None, :, None]).astype(
        np.float32
    )
    return torch.from_numpy(model_input).float()


def score_expert_a(
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


def _find_flagged_abnormal(
    abnormal_dir: Path,
    embedder: ExpertABottleneckEmbedder,
    max_scan: int,
) -> tuple[Path, dict[str, Any]]:
    """Find an abnormal clip that Expert A flags."""
    candidates = sorted(abnormal_dir.glob("*.wav"), key=lambda path: path.name)
    if max_scan > 0:
        candidates = candidates[:max_scan]
    if not candidates:
        raise ValueError(f"No abnormal wav files found in {abnormal_dir}")
    best_path = candidates[0]
    best_result = score_expert_a(best_path, embedder)
    for path in candidates:
        result = score_expert_a(path, embedder)
        if result["is_anomaly"]:
            return path, result
        if result["anomaly_score"] > best_result["anomaly_score"]:
            best_path = path
            best_result = result
    raise ValueError(
        "No abnormal clip was flagged by Expert A in the scan window. "
        f"Highest score was {best_result['anomaly_score']:.6f} for {best_path}, "
        f"threshold {best_result['threshold']:.6f}."
    )


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--machine-type", default="fan")
    parser.add_argument("--machine-id", default="id_00")
    parser.add_argument("--snr-tag", default="minus6dB", choices=sorted(cfg.MIMII_SNR_DIRS))
    parser.add_argument("--reference-index", type=Path)
    parser.add_argument("--audio-path", type=Path)
    parser.add_argument("--abnormal-dir", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--k", type=int, default=DEFAULT_K)
    parser.add_argument("--distance", default=DEFAULT_DISTANCE, choices=("euclidean", "cosine"))
    parser.add_argument(
        "--max-scan",
        type=int,
        default=50,
        help="Maximum abnormal clips to scan when --audio-path is omitted.",
    )
    return parser.parse_args()


def main() -> None:
    """Run Expert A and Expert B on one abnormal audio event."""
    args = parse_args()
    reference_index_path = args.reference_index or _default_index(
        args.machine_type,
        args.machine_id,
        args.snr_tag,
    )
    output_path = args.output or _default_output(args.snr_tag)
    reference_index = load_reference_index(reference_index_path)
    embedder = ExpertABottleneckEmbedder(snr_tag=args.snr_tag)

    if args.audio_path is not None:
        audio_path = args.audio_path
        expert_a = score_expert_a(audio_path, embedder)
        if not expert_a["is_anomaly"]:
            raise ValueError(
                f"Expert A did not flag supplied audio: {audio_path}. "
                f"score={expert_a['anomaly_score']:.6f}, "
                f"threshold={expert_a['threshold']:.6f}"
            )
    else:
        abnormal_dir = args.abnormal_dir or (
            cfg.MIMII_SNR_DIRS[args.snr_tag] / cfg.MIMII_ABNORMAL_FOLDER
        )
        audio_path, expert_a = _find_flagged_abnormal(
            abnormal_dir,
            embedder,
            args.max_scan,
        )

    expert = AcousticTimbreDifferenceExpert(
        reference_index=reference_index,
        embedder=embedder,
        k=args.k,
        distance=args.distance,
        rank_threshold=None,
    )
    result = expert.characterize(
        audio_path=audio_path,
        machine_type=args.machine_type,
        machine_id=args.machine_id,
        snr_tag=args.snr_tag,
        expert_a=expert_a,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)

    deviations = sorted(
        (
            (name, abs(values["rank_score"] - 0.5), values["rank_score"])
            for name, values in result["timbre_differences"].items()
        ),
        key=lambda row: row[1],
        reverse=True,
    )
    top_text = ", ".join(f"{name}={score:.3f}" for name, _, score in deviations)
    print("Expert B: AcousticTimbreDifferenceExpert")
    print(f"Status: {result['method']['status']}")
    print(f"Audio: {audio_path}")
    print(
        "Expert A: "
        f"score={expert_a['anomaly_score']:.6f} "
        f"threshold={expert_a['threshold']:.6f} "
        f"is_anomaly={expert_a['is_anomaly']}"
    )
    print(
        f"References: {result['references']['selected_count']}/"
        f"{result['references']['pool_size']}"
    )
    print(f"Top timbre rank deviations: {top_text}")
    print(f"Warnings: {len(result['warnings'])}")
    print(f"OUTPUT={output_path}")


if __name__ == "__main__":
    main()
