"""Run controlled per-SNR anomaly-detection experiments for MIMII fan id_00."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys
from typing import Any

import numpy as np
from sklearn.metrics import roc_auc_score

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

import config as cfg  # noqa: E402
from data_loader import load_mimii_dataset  # noqa: E402
from models.anomaly_detector import (  # noqa: E402
    compute_threshold,
    evaluate,
    rebuild_validation_tensor,
    train_anomaly_detector,
)


DEFAULT_TAGS = ["minus6dB", "0dB", "plus6dB"]
EXPECTED_X_TRAIN = (200, 313, 64)
EXPECTED_X_TEST = (250, 313, 64)
EXPECTED_Y_TEST = (250,)


def _wav_count(folder: Path) -> int:
    """Return the number of wav files directly under ``folder``."""
    return len(list(folder.glob("*.wav")))


def _raw_ready(raw_dir: Path) -> bool:
    """Return whether both raw class folders exist and contain wav files."""
    normal_dir = raw_dir / cfg.MIMII_NORMAL_FOLDER
    abnormal_dir = raw_dir / cfg.MIMII_ABNORMAL_FOLDER
    return (
        normal_dir.is_dir()
        and abnormal_dir.is_dir()
        and _wav_count(normal_dir) > 0
        and _wav_count(abnormal_dir) > 0
    )


def _json_ready(value: Any) -> Any:
    """Convert NumPy scalars and arrays to JSON-serializable values."""
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    return value


def _paths_are_distinct(tag: str, tags: list[str]) -> bool:
    """Return whether a tag's AD artifact paths are unique and non-legacy."""
    legacy = {
        cfg.X_TRAIN_AD_PATH,
        cfg.X_TEST_AD_PATH,
        cfg.Y_TEST_AD_PATH,
        cfg.PROCESSED_DIR / "ad_norm_stats.npz",
        cfg.ANOMALY_DETECTOR_PATH,
    }
    all_paths: list[Path] = []
    for item in tags:
        paths = cfg.ad_paths_for(item)
        all_paths.extend(paths[key] for key in ("x_train", "x_test", "y_test", "norm_stats", "model"))
    tag_paths = list(cfg.ad_paths_for(tag).values())
    return len({str(path) for path in all_paths}) == len(all_paths) and all(
        path not in legacy for path in tag_paths
    )


def _shape_status(x_train: np.ndarray, x_test: np.ndarray, y_test: np.ndarray) -> tuple[bool, str]:
    """Validate expected per-SNR anomaly-detection split shapes and labels."""
    reasons: list[str] = []
    if x_train.shape != EXPECTED_X_TRAIN:
        reasons.append(f"X_train={x_train.shape}")
    if x_test.shape != EXPECTED_X_TEST:
        reasons.append(f"X_test={x_test.shape}")
    if y_test.shape != EXPECTED_Y_TEST:
        reasons.append(f"y_test={y_test.shape}")
    normal_count = int((y_test == cfg.LABEL_NORMAL).sum())
    abnormal_count = int((y_test == cfg.LABEL_ANOMALY).sum())
    if normal_count != 200:
        reasons.append(f"normal_labels={normal_count}")
    if abnormal_count != 50:
        reasons.append(f"abnormal_labels={abnormal_count}")
    return not reasons, "; ".join(reasons)


def _artifact_files_exist(tag: str) -> bool:
    """Return whether the per-SNR split artifacts exist on disk."""
    paths = cfg.ad_paths_for(tag)
    return all(paths[key].is_file() for key in ("x_train", "x_test", "y_test"))


def _preprocess_tag(tag: str, tags: list[str]) -> dict[str, Any]:
    """Preprocess one SNR tag and return a summary row."""
    raw_dir = cfg.MIMII_SNR_DIRS[tag]
    row: dict[str, Any] = {
        "snr": tag,
        "status": "ok",
        "raw_dir": raw_dir,
        "x_train_shape": None,
        "x_test_shape": None,
        "y_test_shape": None,
        "normal_labels": 0,
        "abnormal_labels": 0,
        "paths_distinct": _paths_are_distinct(tag, tags),
        "ready": False,
        "reason": "",
    }
    if not _raw_ready(raw_dir):
        row["status"] = "missing_raw"
        row["reason"] = "normal or abnormal folder missing/empty"
        return row

    try:
        x_train, _ = load_mimii_dataset(raw_dir, "train", snr_tag=tag)
        x_test, y_test = load_mimii_dataset(raw_dir, "test", snr_tag=tag)
        row["x_train_shape"] = tuple(x_train.shape)
        row["x_test_shape"] = tuple(x_test.shape)
        row["y_test_shape"] = tuple(y_test.shape)
        row["normal_labels"] = int((y_test == cfg.LABEL_NORMAL).sum())
        row["abnormal_labels"] = int((y_test == cfg.LABEL_ANOMALY).sum())
        shapes_ok, reason = _shape_status(x_train, x_test, y_test)
        files_ok = _artifact_files_exist(tag)
        row["ready"] = shapes_ok and files_ok and row["paths_distinct"]
        if not row["ready"]:
            row["status"] = "shape_error"
            missing = [] if files_ok else ["per-SNR files missing"]
            distinct = [] if row["paths_distinct"] else ["paths collide"]
            row["reason"] = "; ".join([item for item in [reason, *missing, *distinct] if item])
    except Exception as exc:
        row["status"] = "shape_error"
        row["reason"] = str(exc)
    return row


def _run_tag(tag: str, tags: list[str], epochs: int, preprocess_only: bool) -> dict[str, Any]:
    """Run preprocessing and optionally train/evaluate one SNR tag."""
    row = _preprocess_tag(tag, tags)
    if preprocess_only or row["status"] != "ok":
        return row

    model = train_anomaly_detector(snr_tag=tag, epochs=epochs)
    val_tensor = rebuild_validation_tensor(snr_tag=tag)
    threshold, _ = compute_threshold(model, val_tensor)
    result = evaluate(model, threshold, snr_tag=tag)

    y_test = np.load(cfg.ad_paths_for(tag)["y_test"])
    scores = result["scores"]
    preds = scores > threshold
    normal_mask = y_test == cfg.LABEL_NORMAL
    abnormal_mask = y_test == cfg.LABEL_ANOMALY
    tp = int((preds & abnormal_mask).sum())
    fp = int((preds & normal_mask).sum())

    row.update(
        {
            "auc": float(roc_auc_score(y_test, scores)),
            "threshold": float(threshold),
            "normal_mean": float(scores[normal_mask].mean()),
            "abnormal_mean": float(scores[abnormal_mask].mean()),
            "recall": tp / 50.0,
            "fpr": fp / 200.0,
            "specificity": 1.0 - (fp / 200.0),
        }
    )
    return row


def _write_summary(rows: list[dict[str, Any]]) -> None:
    """Write JSON and CSV SNR summaries to the processed directory."""
    cfg.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    json_path = cfg.PROCESSED_DIR / "snr_ad_summary.json"
    csv_path = cfg.PROCESSED_DIR / "snr_ad_summary.csv"
    with json_path.open("w", encoding="utf-8") as handle:
        json.dump(rows, handle, indent=2, default=_json_ready)

    columns = [
        "snr",
        "status",
        "ready",
        "x_train_shape",
        "x_test_shape",
        "y_test_shape",
        "normal_labels",
        "abnormal_labels",
        "auc",
        "threshold",
        "normal_mean",
        "abnormal_mean",
        "recall",
        "fpr",
        "specificity",
        "reason",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _metric_text(value: Any) -> str:
    """Format numeric metric cells for compact aligned output."""
    return "NA" if value is None else f"{float(value):.6f}"


def _print_metric_table(rows: list[dict[str, Any]]) -> None:
    """Print the requested compact metric table."""
    print("SNR       AUC       Threshold  NormalMean  AbnormalMean  Recall    FPR       Specificity")
    for row in rows:
        print(
            f"{row['snr']:<9} "
            f"{_metric_text(row.get('auc')):<9} "
            f"{_metric_text(row.get('threshold')):<10} "
            f"{_metric_text(row.get('normal_mean')):<11} "
            f"{_metric_text(row.get('abnormal_mean')):<13} "
            f"{_metric_text(row.get('recall')):<9} "
            f"{_metric_text(row.get('fpr')):<9} "
            f"{_metric_text(row.get('specificity')):<11}"
        )


def _print_preprocess_table(rows: list[dict[str, Any]]) -> None:
    """Print shape verification and readiness for preprocess-only runs."""
    print("SNR       Status       X_train        X_test         y_test   Labels       READY")
    for row in rows:
        labels = f"{row['normal_labels']}/{row['abnormal_labels']}"
        print(
            f"{row['snr']:<9} "
            f"{row['status']:<12} "
            f"{str(row['x_train_shape']):<14} "
            f"{str(row['x_test_shape']):<14} "
            f"{str(row['y_test_shape']):<8} "
            f"{labels:<12} "
            f"{'YES' if row['ready'] else 'NO'}"
        )
        if row["reason"]:
            print(f"  reason: {row['reason']}")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tags", nargs="+", default=DEFAULT_TAGS)
    parser.add_argument("--epochs", type=int, default=cfg.AD_EPOCHS)
    parser.add_argument("--preprocess-only", action="store_true")
    return parser.parse_args()


def main() -> None:
    """Run requested per-SNR preprocessing, training, and summary reporting."""
    args = parse_args()
    unknown = [tag for tag in args.tags if tag not in cfg.MIMII_SNR_DIRS]
    if unknown:
        raise ValueError(f"Unknown SNR tag(s): {unknown}")

    rows = [
        _run_tag(tag, args.tags, args.epochs, args.preprocess_only)
        for tag in args.tags
    ]
    try:
        _write_summary(rows)
    except OSError as exc:
        print(f"Summary write failed: {exc}")
    if args.preprocess_only:
        _print_preprocess_table(rows)
    else:
        _print_metric_table(rows)


if __name__ == "__main__":
    main()
