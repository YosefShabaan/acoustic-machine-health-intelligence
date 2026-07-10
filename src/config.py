"""Central configuration for the active acoustic health-monitoring project.

This file contains active runtime and experiment constants only. The current
architecture is same-machine acoustic condition monitoring:

audio event -> Expert A anomaly detection -> Expert B timbre characterization
-> Structured Health Context -> LLM + RAG -> Dashboard.
"""

from pathlib import Path
import os

# ---------------------------------------------------------------------------
# PROJECT PATHS
# ---------------------------------------------------------------------------
# PROJECT_ROOT resolves to the repository root (this file lives in src/).
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Small, code-adjacent assets such as approved RAG manuals may stay in the repo.
DATA_DIR = PROJECT_ROOT / "data"

# ---------------------------------------------------------------------------
# EXTERNAL DATA ROOT
# ---------------------------------------------------------------------------
# All raw datasets and generated .npy/.npz/model artifacts live outside Git.
# In production containers, this defaults to /mnt/amhi-artifacts.
# On local Windows development, this defaults to D:\PDM_Data\MIMII.
_DEFAULT_ROOT = r"D:\PDM_Data\MIMII" if os.name == "nt" else "/mnt/amhi-artifacts"
PDM_DATA_ROOT = Path(os.environ.get("PDM_DATA_ROOT", _DEFAULT_ROOT))
PDM_ZIPS_DIR = PDM_DATA_ROOT.parent / "Zips"
PROCESSED_DIR = PDM_DATA_ROOT / "processed"
MODELS_DIR = PDM_DATA_ROOT / "models_store"

# ---------------------------------------------------------------------------
# MIMII RAW DATASET LOCATIONS
# ---------------------------------------------------------------------------
# SNR variants are extracted into distinct top-level folders to avoid collision.
MIMII_SNR_DIRS = {
    "minus6dB": PDM_DATA_ROOT / "fan_minus6dB" / "id_00",
    "0dB": PDM_DATA_ROOT / "fan_0dB" / "id_00",
    "plus6dB": PDM_DATA_ROOT / "fan_plus6dB" / "id_00",
}

MIMII_SNR_ZIPS = {
    "minus6dB": PDM_ZIPS_DIR / "-6_dB_fan.zip",
    "0dB": PDM_ZIPS_DIR / "0_dB_fan.zip",
    "plus6dB": PDM_ZIPS_DIR / "6_dB_fan.zip",
}

# Default single-SNR working set: noisy stress-test baseline.
MIMII_FAN_DIR = MIMII_SNR_DIRS["minus6dB"]
MIMII_NORMAL_DIR = MIMII_FAN_DIR / "normal"
MIMII_ABNORMAL_DIR = MIMII_FAN_DIR / "abnormal"
MIMII_ANOMALY_DIR = MIMII_ABNORMAL_DIR

MIMII_NORMAL_FOLDER = "normal"
MIMII_ABNORMAL_FOLDER = "abnormal"

# --- Processed artifact paths (legacy default = -6 dB baseline) ---
X_TRAIN_AD_PATH = PROCESSED_DIR / "X_train_ad.npy"
X_TEST_AD_PATH = PROCESSED_DIR / "X_test_ad.npy"
Y_TEST_AD_PATH = PROCESSED_DIR / "y_test_ad.npy"


def ad_paths_for(snr_tag: str) -> dict:
    """Return per-SNR processed-artifact paths so results never overwrite.

    Keys: x_train, x_test, y_test, norm_stats, model.
    Example tag values: "minus6dB", "0dB", "plus6dB", or "all".
    """
    return {
        "x_train": PROCESSED_DIR / f"X_train_ad_{snr_tag}.npy",
        "x_test": PROCESSED_DIR / f"X_test_ad_{snr_tag}.npy",
        "y_test": PROCESSED_DIR / f"y_test_ad_{snr_tag}.npy",
        "norm_stats": PROCESSED_DIR / f"ad_norm_stats_{snr_tag}.npz",
        "model": MODELS_DIR / f"anomaly_detector_{snr_tag}.pt",
    }


MIMII_COMBINED_TAG = "all"
ANOMALY_DETECTOR_PATH = MODELS_DIR / "anomaly_detector.pt"


def report_paths() -> str:
    """Build a human-readable report of every resolved active data path."""
    lines = [
        "=== PDM DATA PATHS (resolved) ===",
        f"PDM_DATA_ROOT (env or default): {PDM_DATA_ROOT}",
        f"  on D: drive?                : {str(PDM_DATA_ROOT).upper().startswith('D:')}",
        f"Zips dir                      : {PDM_ZIPS_DIR}",
        f"Processed (.npy/.npz) dir     : {PROCESSED_DIR}",
        f"Models dir                    : {MODELS_DIR}",
        "Raw SNR dirs:",
    ]
    for tag, directory in MIMII_SNR_DIRS.items():
        lines.append(f"  {tag:9s} -> {directory}")
        lines.append(f"            normal/   -> {directory / MIMII_NORMAL_FOLDER}")
        lines.append(f"            abnormal/ -> {directory / MIMII_ABNORMAL_FOLDER}")
    lines.append("Source zips:")
    for tag, zip_path in MIMII_SNR_ZIPS.items():
        lines.append(f"  {tag:9s} -> {zip_path}")
    lines.append(f"PROJECT_ROOT (code)          : {PROJECT_ROOT}")
    return "\n".join(lines)


# ===========================================================================
# MIMII ACOUSTIC PIPELINE (Expert A input)
# ===========================================================================
SR = 16000
N_FFT = 1024
HOP_LENGTH = 512
N_MELS = 64

MEL_TIME_FRAMES = 313
MEL_SHAPE = (MEL_TIME_FRAMES, N_MELS)

MAX_NORMAL = 200
MAX_ANOMALY = 50

LABEL_NORMAL = 0
LABEL_ANOMALY = 1


# ===========================================================================
# EXPERT A (CONVOLUTIONAL AUTOENCODER) TRAINING / THRESHOLD
# ===========================================================================
AD_INPUT_SHAPE = MEL_SHAPE
AD_LOSS = "mse"
AD_THRESHOLD_STD_MULT = 2.0

# AUC targets are calibrated to the current -6 dB fan id_00 baseline.
AD_BASELINE_AUC_MINUS6DB = 0.576
AD_TARGET_AUC = 0.60
AD_STRETCH_AUC = 0.85

AD_BATCH_SIZE = 32
AD_EPOCHS = 250
AD_LR = 0.001
AD_LATENT_DIM = 128


# ===========================================================================
# STRUCTURED HEALTH CONTEXT / AGENT CONFIG
# ===========================================================================
ASSET_ID = "FAN-ID00-001"

SEVERITY_LEVELS = ("LOW", "MEDIUM", "HIGH", "CRITICAL")
TREND_STATES = ("STABLE", "DEGRADING", "CRITICAL")
ANOMALY_STATES = ("NORMAL", "ANOMALY_DETECTED")

# Gemini API integration.
# The API key is never stored in configuration; providers read it from this
# environment variable at runtime.
GEMINI_API_KEY_ENV_VAR = "GEMINI_API_KEY"

# Default selected from Google AI Gemini documentation inspected on 2026-07-09:
# `gemini-2.5-flash` is listed as a stable Gemini text-output model with
# structured-output support. Override via GEMINI_MODEL when needed.
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_REQUEST_TIMEOUT_SECONDS = float(
    os.environ.get("GEMINI_REQUEST_TIMEOUT_SECONDS", "30")
)

# Default selected from Google AI Gemini embedding documentation inspected on
# 2026-07-09: `gemini-embedding-2` is the stable latest embedding model, and
# 768 dimensions are in the recommended range for retrieval-oriented use.
GEMINI_EMBEDDING_MODEL = os.environ.get(
    "GEMINI_EMBEDDING_MODEL",
    "gemini-embedding-2",
)
GEMINI_EMBEDDING_DIMENSION = int(os.environ.get("GEMINI_EMBEDDING_DIMENSION", "768"))

# Backward-compatible alias for legacy call sites that refer to a generic LLM.
LLM_MODEL = GEMINI_MODEL
CHROMA_DIR = PROJECT_ROOT / "chroma_store"
RAG_MANUALS_DIR = DATA_DIR / "manuals"

# PROJECT DECISION after TASK-RAG-05 on AMHI-FAN-MAINT-RETRIEVAL-EVAL-v1:
# semantic retrieval is selected for the bounded Fan MVP RAG path.
RAG_FAN_MVP_SELECTED_RETRIEVER = "semantic"


# ===========================================================================
# REPRODUCIBILITY
# ===========================================================================
RANDOM_SEED = 42


# ===========================================================================
# SECURITY & AUTHENTICATION
# ===========================================================================
AMHI_ADMIN_USERNAME = os.environ.get("AMHI_ADMIN_USERNAME")
AMHI_ADMIN_PASSWORD_HASH = os.environ.get("AMHI_ADMIN_PASSWORD_HASH")
AMHI_SESSION_SECRET = os.environ.get("AMHI_SESSION_SECRET")
# CSRF protection secret
AMHI_CSRF_SECRET = os.environ.get("AMHI_CSRF_SECRET", AMHI_SESSION_SECRET)
# Disable debug mode by default in production
DEBUG_MODE = os.environ.get("DEBUG_MODE", "false").lower() == "true"


if __name__ == "__main__":
    print(report_paths())
