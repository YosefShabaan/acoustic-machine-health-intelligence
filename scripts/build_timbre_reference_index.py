"""Build a same-machine normal reference index for Expert B."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import time

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import config as cfg  # noqa: E402
from models.timbre_difference import (  # noqa: E402
    DEFAULT_K,
    ExpertABottleneckEmbedder,
    compute_timbre_values_timed,
)
from utils.audio_reference_index import ReferenceIndex, ReferenceItem, save_reference_index  # noqa: E402


def _default_output(machine_type: str, machine_id: str, snr_tag: str) -> Path:
    """Return an external generated-artifact path."""
    return (
        cfg.PROCESSED_DIR
        / f"timbre_reference_index_{machine_type}_{machine_id}_{snr_tag}.json"
    )


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--machine-type", default="fan")
    parser.add_argument("--machine-id", default="id_00")
    parser.add_argument("--snr-tag", default="minus6dB", choices=sorted(cfg.MIMII_SNR_DIRS))
    parser.add_argument("--normal-dir", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--limit",
        type=int,
        default=40,
        help="Maximum normal references to index. Use 0 for all files.",
    )
    parser.add_argument(
        "--timbre-input",
        choices=("path", "array"),
        default="array",
        help=(
            "array loads the WAV once and uses the official AudioCommons array+fs "
            "API; path preserves the original behavior where every timbral metric "
            "receives a file path."
        ),
    )
    return parser.parse_args()


def main() -> None:
    """Build and save the reference index."""
    args = parse_args()
    normal_dir = args.normal_dir or (
        cfg.MIMII_SNR_DIRS[args.snr_tag] / cfg.MIMII_NORMAL_FOLDER
    )
    output_path = args.output or _default_output(
        args.machine_type,
        args.machine_id,
        args.snr_tag,
    )
    paths = sorted(normal_dir.glob("*.wav"), key=lambda path: path.name)
    if args.limit > 0:
        paths = paths[: args.limit]
    if len(paths) < DEFAULT_K:
        print(
            f"WARNING: building only {len(paths)} references, below k={DEFAULT_K}. "
            "This is valid for timing forensics but not sufficient for Expert B kNN.",
            flush=True,
        )

    embedder = ExpertABottleneckEmbedder(snr_tag=args.snr_tag)
    items: list[ReferenceItem] = []
    per_file_timings: list[dict[str, float]] = []
    total_start = time.perf_counter()
    total_count = len(paths)
    for index, path in enumerate(paths, start=1):
        file_start = time.perf_counter()
        embed_start = time.perf_counter()
        embedding = embedder.embed_audio(path)
        embedding_seconds = time.perf_counter() - embed_start

        timbre_values, timbre_timings = compute_timbre_values_timed(
            path,
            reuse_loaded_audio=args.timbre_input == "array",
        )
        file_seconds = time.perf_counter() - file_start
        timing_row = {
            "audio_load": timbre_timings["audio_load"],
            "embedding": embedding_seconds,
            "sharpness": timbre_timings["sharpness"],
            "roughness": timbre_timings["roughness"],
            "boominess": timbre_timings["boominess"],
            "brightness": timbre_timings["brightness"],
            "depth": timbre_timings["depth"],
            "timbre_total": timbre_timings["timbre_total"],
            "total": file_seconds,
        }
        per_file_timings.append(timing_row)
        items.append(
            ReferenceItem(
                path=str(path),
                machine_type=args.machine_type,
                machine_id=args.machine_id,
                snr_tag=args.snr_tag,
                embedding=[float(value) for value in embedding.ravel()],
                timbre_values=timbre_values.to_dict(),
            )
        )
        print(
            f"[{index}/{total_count}] {path.name} | "
            f"audio_load={timing_row['audio_load']:.2f}s | "
            f"embed={embedding_seconds:.2f}s | "
            f"timbre={timing_row['timbre_total']:.2f}s | "
            f"total={file_seconds:.2f}s",
            flush=True,
        )
        print(
            "  metrics | "
            f"sharpness={timing_row['sharpness']:.2f}s | "
            f"roughness={timing_row['roughness']:.2f}s | "
            f"boominess={timing_row['boominess']:.2f}s | "
            f"brightness={timing_row['brightness']:.2f}s | "
            f"depth={timing_row['depth']:.2f}s",
            flush=True,
        )
        if index >= 3 and index < total_count:
            elapsed = time.perf_counter() - total_start
            estimated_total = elapsed * total_count / index
            remaining = max(0.0, estimated_total - elapsed)
            print(f"  ETA remaining={remaining:.2f}s", flush=True)

    reference_index = ReferenceIndex(
        items=items,
        metadata={
            "machine_type": args.machine_type,
            "machine_id": args.machine_id,
            "snr_tag": args.snr_tag,
            "embedding_model": "expert_a_bottleneck_adaptation",
            "normal_reference_only": True,
            "timbre_input": args.timbre_input,
            "timings": per_file_timings,
        },
    )
    save_start = time.perf_counter()
    save_reference_index(reference_index, output_path)
    serialization_seconds = time.perf_counter() - save_start
    total_seconds = time.perf_counter() - total_start
    if per_file_timings:
        mean_embedding = sum(row["embedding"] for row in per_file_timings) / len(per_file_timings)
        mean_audio_load = sum(row["audio_load"] for row in per_file_timings) / len(per_file_timings)
        mean_timbre = sum(row["timbre_total"] for row in per_file_timings) / len(per_file_timings)
        mean_total = sum(row["total"] for row in per_file_timings) / len(per_file_timings)
        print("TIMING SUMMARY")
        print(f"AUDIO LOAD: mean={mean_audio_load:.6f}s")
        print("PREPROCESSING: included in AudioCommons metric/model stages")
        print(f"EMBEDDING: mean={mean_embedding:.6f}s")
        print(f"METRIC/MODEL STAGES: mean={mean_timbre:.6f}s")
        print(f"SERIALIZATION: {serialization_seconds:.6f}s")
        print(f"TOTAL PER FILE: mean={mean_total:.6f}s")
    print(f"REFERENCE_INDEX={output_path}")
    print(f"REFERENCES={len(reference_index.items)}")
    print("EMBEDDING_MODEL=expert_a_bottleneck_adaptation")
    print("NORMAL_REFERENCES_ONLY=True")
    print(f"TIMBRE_INPUT={args.timbre_input}")
    print(f"SERIALIZATION={serialization_seconds:.6f}s")
    print(f"TOTAL={total_seconds:.6f}s")


if __name__ == "__main__":
    main()
