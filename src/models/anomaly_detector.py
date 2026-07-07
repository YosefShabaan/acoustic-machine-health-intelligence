"""Convolutional autoencoder for MIMII acoustic anomaly detection."""

from pathlib import Path
import logging
import sys
from typing import Any

sys.path.append(str(Path(__file__).resolve().parent.parent))

from config import (
    AD_BATCH_SIZE,
    AD_EPOCHS,
    AD_LATENT_DIM,
    AD_LR,
    AD_TARGET_AUC,
    AD_THRESHOLD_STD_MULT,
    ANOMALY_DETECTOR_PATH,
    ad_paths_for,
    MEL_SHAPE,
    MEL_TIME_FRAMES,
    MODELS_DIR,
    N_MELS,
    PROCESSED_DIR,
    RANDOM_SEED,
    X_TEST_AD_PATH,
    X_TRAIN_AD_PATH,
    Y_TEST_AD_PATH,
)
import numpy as np
from sklearn.metrics import roc_auc_score
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset


NORM_STATS_PATH = PROCESSED_DIR / "ad_norm_stats.npz"


def _resolve_ad_paths(snr_tag: str | None) -> dict[str, Path]:
    """Return legacy or per-SNR anomaly-detector artifact paths."""
    if snr_tag is not None:
        return ad_paths_for(snr_tag)
    return {
        "x_train": X_TRAIN_AD_PATH,
        "x_test": X_TEST_AD_PATH,
        "y_test": Y_TEST_AD_PATH,
        "norm_stats": NORM_STATS_PATH,
        "model": ANOMALY_DETECTOR_PATH,
    }


class ConvAutoencoder(nn.Module):
    """Conv1d autoencoder that reconstructs log-mel spectrogram inputs."""

    def __init__(self) -> None:
        """Initialize encoder and decoder layers."""
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Conv1d(N_MELS, 128, kernel_size=3, padding=1, stride=2),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Conv1d(128, 256, kernel_size=3, padding=1, stride=2),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Conv1d(256, 256, kernel_size=3, padding=1, stride=2),
            nn.BatchNorm1d(256),
            nn.ReLU(),
        )
        encoder_training = self.encoder.training
        self.encoder.eval()
        with torch.no_grad():
            dummy_input = torch.zeros(1, N_MELS, MEL_TIME_FRAMES)
            encoded_shape = self.encoder(dummy_input).shape
        self.encoder.train(encoder_training)
        self.conv_channels = encoded_shape[1]
        self.conv_out_len = encoded_shape[-1]
        self.flat_dim = self.conv_channels * self.conv_out_len
        self.bottleneck = nn.Sequential(
            nn.Flatten(start_dim=1),
            nn.Linear(self.flat_dim, AD_LATENT_DIM),
            nn.ReLU(),
            nn.Linear(AD_LATENT_DIM, self.flat_dim),
            nn.ReLU(),
            nn.Unflatten(
                dim=1,
                unflattened_size=(self.conv_channels, self.conv_out_len),
            ),
        )
        self.decoder = nn.Sequential(
            nn.ConvTranspose1d(
                256,
                256,
                kernel_size=3,
                stride=2,
                padding=1,
                output_padding=0,
            ),
            nn.ReLU(),
            nn.ConvTranspose1d(
                256,
                128,
                kernel_size=3,
                stride=2,
                padding=1,
                output_padding=0,
            ),
            nn.ReLU(),
            nn.ConvTranspose1d(
                128,
                N_MELS,
                kernel_size=3,
                stride=2,
                padding=1,
                output_padding=0,
            ),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Return a reconstruction with the same shape as ``x``."""
        encoded_conv = self.encoder(x)
        z = self.bottleneck(encoded_conv)
        reconstructed = self.decoder(z)
        return reconstructed[:, :, :MEL_TIME_FRAMES]


def _get_device() -> torch.device:
    """Return the available PyTorch device."""
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def _seed_everything() -> None:
    """Seed NumPy and PyTorch for deterministic training setup."""
    np.random.seed(RANDOM_SEED)
    torch.manual_seed(RANDOM_SEED)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(RANDOM_SEED)


def _load_train_array(snr_tag: str | None = None) -> np.ndarray:
    """Load the anomaly-detector training array."""
    return np.load(_resolve_ad_paths(snr_tag)["x_train"]).astype(np.float32)


def _transpose_to_model_input(x: np.ndarray) -> np.ndarray:
    """Convert saved arrays from ``(B, time, mel)`` to ``(B, mel, time)``."""
    expected_saved_shape = (MEL_TIME_FRAMES, N_MELS)
    if tuple(x.shape[1:]) != expected_saved_shape:
        raise ValueError(
            f"Expected input arrays with per-sample shape {expected_saved_shape}, "
            f"got {tuple(x.shape[1:])}."
        )
    if MEL_SHAPE != expected_saved_shape:
        raise ValueError(
            f"MEL_SHAPE {MEL_SHAPE} does not match expected saved shape "
            f"{expected_saved_shape}."
        )
    # The loader saves arrays as (B, 313, 64); the model consumes (B, 64, 313).
    return np.transpose(x, (0, 2, 1)).astype(np.float32)


def _fit_normalization(
    train_x: np.ndarray,
    snr_tag: str | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Fit per-mel-band normalization statistics on the train split only."""
    mean = train_x.mean(axis=(0, 2)).astype(np.float32)
    std = (train_x.std(axis=(0, 2)) + 1e-8).astype(np.float32)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    np.savez(_resolve_ad_paths(snr_tag)["norm_stats"], mean=mean, std=std)
    return mean, std


def _load_normalization(snr_tag: str | None = None) -> tuple[np.ndarray, np.ndarray]:
    """Load saved per-mel-band normalization statistics."""
    stats = np.load(_resolve_ad_paths(snr_tag)["norm_stats"])
    return stats["mean"].astype(np.float32), stats["std"].astype(np.float32)


def _normalize(x: np.ndarray, mean: np.ndarray, std: np.ndarray) -> np.ndarray:
    """Apply per-mel-band normalization to model-shaped arrays."""
    return ((x - mean[None, :, None]) / std[None, :, None]).astype(np.float32)


def _to_tensor(x: np.ndarray, device: torch.device) -> torch.Tensor:
    """Convert a NumPy array to a float tensor on ``device``."""
    return torch.from_numpy(x).float().to(device)


def rebuild_validation_tensor(snr_tag: str | None = None) -> torch.Tensor:
    """Rebuild the validation tensor using saved train normalization stats."""
    device = _get_device()
    x_all = _transpose_to_model_input(_load_train_array(snr_tag))
    split_index = int(x_all.shape[0] * 0.9)
    val_x = x_all[split_index:]
    mean, std = _load_normalization(snr_tag)
    return _to_tensor(_normalize(val_x, mean, std), device)


def train_anomaly_detector(
    snr_tag: str | None = None,
    epochs: int | None = None,
) -> ConvAutoencoder:
    """Train the convolutional autoencoder and save its state dict."""
    _seed_everything()
    device = _get_device()
    artifact_paths = _resolve_ad_paths(snr_tag)
    effective_epochs = AD_EPOCHS if epochs is None else epochs

    x_all = _transpose_to_model_input(_load_train_array(snr_tag))
    split_index = int(x_all.shape[0] * 0.9)
    train_x = x_all[:split_index]
    val_x = x_all[split_index:]

    mean, std = _fit_normalization(train_x, snr_tag)
    train_x = _normalize(train_x, mean, std)
    val_x = _normalize(val_x, mean, std)

    train_tensor = _to_tensor(train_x, device)
    val_tensor = _to_tensor(val_x, device)
    train_loader = DataLoader(
        TensorDataset(train_tensor),
        batch_size=AD_BATCH_SIZE,
        shuffle=True,
    )

    model = ConvAutoencoder().to(device)
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=AD_LR)

    for epoch in range(effective_epochs):
        model.train()
        train_loss_total = 0.0
        sample_count = 0

        for (batch,) in train_loader:
            optimizer.zero_grad()
            reconstruction = model(batch)
            loss = criterion(reconstruction, batch)
            loss.backward()
            optimizer.step()

            batch_size = batch.size(0)
            train_loss_total += loss.item() * batch_size
            sample_count += batch_size

        train_loss = train_loss_total / sample_count

        model.eval()
        with torch.no_grad():
            val_reconstruction = model(val_tensor)
            val_loss = criterion(val_reconstruction, val_tensor).item()

        logging.info(
            "Epoch %d/%d - train_loss=%.6f val_loss=%.6f",
            epoch + 1,
            effective_epochs,
            train_loss,
            val_loss,
        )

    artifact_paths["model"].parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), artifact_paths["model"])
    return model


def compute_threshold(
    model: ConvAutoencoder,
    val_tensor: torch.Tensor,
) -> tuple[float, np.ndarray]:
    """Compute the anomaly threshold from validation reconstruction errors."""
    model.eval()
    with torch.no_grad():
        reconstruction = model(val_tensor)
        errors = torch.mean((reconstruction - val_tensor) ** 2, dim=(1, 2))

    val_errors = errors.detach().cpu().numpy()
    threshold = float(
        val_errors.mean() + AD_THRESHOLD_STD_MULT * val_errors.std()
    )
    return threshold, val_errors


def evaluate(
    model: ConvAutoencoder,
    threshold: float,
    snr_tag: str | None = None,
) -> dict[str, Any]:
    """Evaluate the model on the saved MIMII anomaly-detection test split."""
    device = next(model.parameters()).device
    artifact_paths = _resolve_ad_paths(snr_tag)
    mean, std = _load_normalization(snr_tag)

    x_test = _transpose_to_model_input(
        np.load(artifact_paths["x_test"]).astype(np.float32)
    )
    x_test = _normalize(x_test, mean, std)
    y_test = np.load(artifact_paths["y_test"])
    test_tensor = _to_tensor(x_test, device)

    model.eval()
    with torch.no_grad():
        reconstruction = model(test_tensor)
        errors = torch.mean((reconstruction - test_tensor) ** 2, dim=(1, 2))

    scores = errors.detach().cpu().numpy()
    preds = scores > threshold
    auc = float(roc_auc_score(y_test, scores))
    accuracy = float((preds == y_test.astype(bool)).mean())
    passed = auc >= AD_TARGET_AUC

    logging.info("Anomaly detector AUC: %.6f", auc)
    logging.info("Accuracy at threshold %.6f: %.6f", threshold, accuracy)
    logging.info(
        "AUC target %.6f: %s",
        AD_TARGET_AUC,
        "PASS" if passed else "FAIL",
    )

    return {
        "auc": auc,
        "threshold": threshold,
        "scores": scores,
        "preds": preds,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    trained_model = train_anomaly_detector()
    validation_tensor = rebuild_validation_tensor()
    anomaly_threshold, _ = compute_threshold(trained_model, validation_tensor)
    results = evaluate(trained_model, anomaly_threshold)
    final_status = "PASS" if results["auc"] >= AD_TARGET_AUC else "FAIL"
    print(f"AUC={results['auc']:.6f} {final_status} vs target {AD_TARGET_AUC:.6f}")
