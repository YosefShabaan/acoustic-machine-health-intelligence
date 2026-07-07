"""Data loading utilities for Pipeline A (MIMII Acoustic, Phase 1)."""

from pathlib import Path
import logging
import sys

sys.path.append(str(Path(__file__).resolve().parent))

import config as cfg
from config import (
    LABEL_ANOMALY,
    LABEL_NORMAL,
    MAX_ANOMALY,
    MAX_NORMAL,
    MEL_SHAPE,
    MEL_TIME_FRAMES,
    MIMII_ABNORMAL_FOLDER,
    MIMII_NORMAL_FOLDER,
    N_FFT,
    N_MELS,
    HOP_LENGTH,
    PROCESSED_DIR,
    SR,
    X_TEST_AD_PATH,
    X_TRAIN_AD_PATH,
    Y_TEST_AD_PATH,
)
import librosa
import numpy as np


def _extract_logmel(file_path: Path) -> np.ndarray:
    """Load one wav file and return a fixed-shape log-mel spectrogram."""
    y, _ = librosa.load(file_path, sr=SR, mono=True)
    mel = librosa.feature.melspectrogram(
        y=y,
        sr=SR,
        n_fft=N_FFT,
        hop_length=HOP_LENGTH,
        n_mels=N_MELS,
    )
    logmel = librosa.power_to_db(mel, ref=np.max).T

    frames = logmel.shape[0]
    if frames > MEL_TIME_FRAMES:
        logmel = logmel[:MEL_TIME_FRAMES, :]
    elif frames < MEL_TIME_FRAMES:
        pad_width = ((0, MEL_TIME_FRAMES - frames), (0, 0))
        logmel = np.pad(logmel, pad_width=pad_width, mode="constant")

    return logmel.astype(np.float32)


def _sorted_wav_files(folder: Path) -> list[Path]:
    """Return wav files sorted by filename ascending."""
    return sorted(folder.glob("*.wav"), key=lambda file_path: file_path.name)


def _load_specs(files: list[Path], cap: int, label: int) -> tuple[list[np.ndarray], list[int]]:
    """Load up to cap readable spectrograms from files, skipping bad inputs."""
    specs: list[np.ndarray] = []
    labels: list[int] = []

    for file_path in files:
        if len(specs) >= cap:
            break
        try:
            specs.append(_extract_logmel(file_path))
            labels.append(label)
        except Exception as exc:
            logging.warning("Skipping unreadable file %s: %s", file_path, exc)

    if len(specs) < cap:
        logging.warning(
            "Loaded %d readable files for label %d, fewer than requested cap %d.",
            len(specs),
            label,
            cap,
        )

    return specs, labels


def load_mimii_dataset(
    data_dir: str | Path,
    split: str,
    max_normal: int = MAX_NORMAL,
    max_anomaly: int = MAX_ANOMALY,
    snr_tag: str | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Load MIMII fan log-mel features for the anomaly-detection pipeline.

    Args:
        data_dir: Path to the MIMII fan id directory, such as
            ``.../mimii/fan/id_00/``.
        split: Dataset split to load. Must be ``"train"`` or ``"test"``.
        max_normal: Maximum number of normal files to use for the split.
        max_anomaly: Maximum number of abnormal files to use for the test split.
        snr_tag: Optional SNR tag used to save split artifacts to per-SNR paths.

    Returns:
        A tuple ``(X, y)`` where ``X`` contains fixed-shape log-mel arrays and
        ``y`` contains integer labels.

    Raises:
        ValueError: If ``split`` is not ``"train"`` or ``"test"``.
    """
    data_path = Path(data_dir)
    normal_dir = data_path / MIMII_NORMAL_FOLDER
    abnormal_dir = data_path / MIMII_ABNORMAL_FOLDER
    artifact_paths = cfg.ad_paths_for(snr_tag) if snr_tag is not None else None

    normal_files = _sorted_wav_files(normal_dir)
    abnormal_files = _sorted_wav_files(abnormal_dir)

    if split == "train":
        if len(normal_files) < max_normal:
            logging.warning(
                "Folder %s has %d wav files, fewer than requested cap %d.",
                normal_dir,
                len(normal_files),
                max_normal,
            )
        normal_specs, normal_labels = _load_specs(
            normal_files,
            max_normal,
            LABEL_NORMAL,
        )
        X = np.asarray(normal_specs, dtype=np.float32).reshape((-1, *MEL_SHAPE))
        y = np.asarray(normal_labels, dtype=np.int64)

        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        np.save(artifact_paths["x_train"] if artifact_paths else X_TRAIN_AD_PATH, X)
        return X, y

    if split == "test":
        test_normal_files = normal_files[max_normal:]
        if len(test_normal_files) < max_normal:
            logging.warning(
                "Folder %s has %d wav files after the train slice, fewer than requested cap %d.",
                normal_dir,
                len(test_normal_files),
                max_normal,
            )
        if len(abnormal_files) < max_anomaly:
            logging.warning(
                "Folder %s has %d wav files, fewer than requested cap %d.",
                abnormal_dir,
                len(abnormal_files),
                max_anomaly,
            )

        normal_specs, normal_labels = _load_specs(
            test_normal_files,
            max_normal,
            LABEL_NORMAL,
        )
        anomaly_specs, anomaly_labels = _load_specs(
            abnormal_files,
            max_anomaly,
            LABEL_ANOMALY,
        )
        specs = normal_specs + anomaly_specs
        labels = normal_labels + anomaly_labels
        X = np.asarray(specs, dtype=np.float32).reshape((-1, *MEL_SHAPE))
        y = np.asarray(labels, dtype=np.int64)

        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        np.save(artifact_paths["x_test"] if artifact_paths else X_TEST_AD_PATH, X)
        np.save(artifact_paths["y_test"] if artifact_paths else Y_TEST_AD_PATH, y)
        return X, y

    raise ValueError(f"Unknown split: {split}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    X_train, y_train = load_mimii_dataset(cfg.MIMII_FAN_DIR, "train")
    print("train", X_train.shape, X_train.dtype, y_train.shape, y_train.dtype)
    X_test, y_test = load_mimii_dataset(cfg.MIMII_FAN_DIR, "test")
    print("test", X_test.shape, X_test.dtype, y_test.shape, y_test.dtype)
