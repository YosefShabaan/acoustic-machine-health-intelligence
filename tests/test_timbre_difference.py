"""Tests for the bounded Expert B timbre difference implementation."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from models.timbre_difference import (  # noqa: E402
    AcousticTimbreDifferenceExpert,
    TimbreValues,
    _ensure_timbral_models_compatibility,
    direction_from_rank,
    rank_score,
)
from utils.audio_reference_index import (  # noqa: E402
    ReferenceIndex,
    ReferenceItem,
    filter_references,
)


class FakeEmbedder:
    """Small deterministic embedder for tests."""

    metadata = {
        "embedding_model": "expert_a_bottleneck_adaptation",
        "embedding_status": "project_mvp_adaptation_not_paper_encoder",
    }

    def embed_audio(self, audio_path: str | Path) -> np.ndarray:
        """Return a fixed query embedding."""
        return np.asarray([0.0, 0.0], dtype=np.float32)


def _item(
    path: str,
    machine_type: str = "fan",
    machine_id: str = "id_00",
    snr_tag: str = "minus6dB",
    embedding: tuple[float, float] = (1.0, 0.0),
    base: float = 1.0,
) -> ReferenceItem:
    """Build one fake normal reference."""
    return ReferenceItem(
        path=path,
        machine_type=machine_type,
        machine_id=machine_id,
        snr_tag=snr_tag,
        embedding=list(embedding),
        timbre_values={
            "sharpness": base,
            "roughness": base + 1.0,
            "boominess": base + 2.0,
            "brightness": base + 3.0,
            "depth": base + 4.0,
        },
    )


def _contains_key(value: object, forbidden: set[str]) -> bool:
    """Return whether any forbidden key appears recursively."""
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in forbidden or _contains_key(nested, forbidden):
                return True
    elif isinstance(value, list):
        return any(_contains_key(item, forbidden) for item in value)
    return False


class TimbreDifferenceTests(unittest.TestCase):
    """Unit tests for Expert B guardrails."""

    def test_rank_score_bounds_and_monotonic_cases(self) -> None:
        """Rank scores follow the Nishida normalized rank rule."""
        refs = [1.0, 2.0, 3.0]
        self.assertEqual(rank_score(0.5, refs), 0.0)
        self.assertAlmostEqual(rank_score(2.5, refs), 2.0 / 3.0)
        self.assertEqual(rank_score(4.0, refs), 1.0)

    def test_direction_from_rank_threshold_none(self) -> None:
        """MVP does not infer direction without explicit threshold."""
        self.assertEqual(direction_from_rank(0.0, None), (None, None))
        self.assertEqual(direction_from_rank(0.5, None), (None, None))
        self.assertEqual(direction_from_rank(1.0, None), (None, None))

    def test_direction_from_rank_configured_threshold(self) -> None:
        """Threshold conversion works when explicitly configured."""
        self.assertEqual(direction_from_rank(0.05, 0.1), ("decreased", -1))
        self.assertEqual(direction_from_rank(0.5, 0.1), ("unchanged", 0))
        self.assertEqual(direction_from_rank(0.95, 0.1), ("increased", 1))

    def test_timbral_models_legacy_resample_call_is_supported(self) -> None:
        """AudioCommons dependency works with newer librosa keyword-only API."""
        _ensure_timbral_models_compatibility()
        from timbral_models import timbral_util

        padded = np.lib.pad(np.zeros(2, dtype=np.float32), (1, 1), "constant")
        self.assertEqual(padded.shape, (4,))

        resampled = timbral_util.librosa.core.resample(
            np.zeros(16, dtype=np.float32),
            16000,
            44100,
        )
        self.assertEqual(resampled.ndim, 1)
        self.assertGreater(len(resampled), 16)
        onsets = timbral_util.librosa.onset.onset_detect(
            np.zeros(4410, dtype=np.float32),
            44100,
            backtrack=True,
            units="samples",
        )
        self.assertEqual(onsets.ndim, 1)
        strength = timbral_util.librosa.onset.onset_strength(
            np.zeros(4410, dtype=np.float32),
            44100,
        )
        self.assertEqual(strength.ndim, 1)

    def test_reference_filtering_rejects_cross_machine_and_snr(self) -> None:
        """Only same machine and SNR references pass the MVP filter."""
        index = ReferenceIndex(
            metadata={},
            items=[
                _item("same.wav"),
                _item("wrong_machine.wav", machine_type="pump"),
                _item("wrong_id.wav", machine_id="id_02"),
                _item("wrong_snr.wav", snr_tag="0dB"),
            ],
        )
        filtered = filter_references(
            index,
            machine_type="fan",
            machine_id="id_00",
            snr_tag="minus6dB",
        )
        self.assertEqual([item.path for item in filtered], ["same.wav"])

    def test_json_guardrails_with_no_rank_threshold(self) -> None:
        """Expert B JSON has scores only, null directions, and no diagnosis fields."""
        references = [
            _item(f"ref_{idx}.wav", embedding=(float(idx + 1), 0.0), base=float(idx))
            for idx in range(3)
        ]
        index = ReferenceIndex(metadata={}, items=references)
        expert = AcousticTimbreDifferenceExpert(
            reference_index=index,
            embedder=FakeEmbedder(),
            k=3,
            distance="euclidean",
            rank_threshold=None,
        )
        output = expert.characterize(
            audio_path="abnormal.wav",
            machine_type="fan",
            machine_id="id_00",
            snr_tag="minus6dB",
            expert_a={
                "anomaly_score": 1.0,
                "threshold": 0.5,
                "is_anomaly": True,
            },
            test_timbre_values=TimbreValues(
                sharpness=10.0,
                roughness=10.0,
                boominess=10.0,
                brightness=10.0,
                depth=10.0,
            ),
        )
        self.assertEqual(output["method"]["k"], 3)
        self.assertEqual(output["method"]["distance"], "euclidean")
        self.assertIsNone(output["method"]["rank_threshold"])
        self.assertEqual(set(output["timbre_differences"]), {
            "sharpness",
            "roughness",
            "boominess",
            "brightness",
            "depth",
        })
        for values in output["timbre_differences"].values():
            self.assertGreaterEqual(values["rank_score"], 0.0)
            self.assertLessEqual(values["rank_score"], 1.0)
            self.assertIsNone(values["direction"])
            self.assertIsNone(values["direction_code"])
        self.assertFalse(_contains_key(output, {"confidence_pct", "root_cause", "diagnosis"}))

    def test_same_audio_identity_is_preserved_in_output(self) -> None:
        """Expert B output records the exact audio path it characterized."""
        references = [
            _item(f"ref_{idx}.wav", embedding=(float(idx + 1), 0.0), base=float(idx))
            for idx in range(3)
        ]
        index = ReferenceIndex(metadata={}, items=references)
        expert = AcousticTimbreDifferenceExpert(
            reference_index=index,
            embedder=FakeEmbedder(),
            k=3,
            distance="euclidean",
            rank_threshold=None,
        )
        output = expert.characterize(
            audio_path=Path("same_event_abnormal.wav"),
            machine_type="fan",
            machine_id="id_00",
            snr_tag="minus6dB",
            expert_a={
                "anomaly_score": 1.0,
                "threshold": 0.5,
                "is_anomaly": True,
            },
            test_timbre_values=TimbreValues(
                sharpness=10.0,
                roughness=10.0,
                boominess=10.0,
                brightness=10.0,
                depth=10.0,
            ),
        )
        self.assertEqual(output["input_audio"]["path"], str(Path("same_event_abnormal.wav")))
        self.assertEqual(output["input_audio"]["machine_type"], "fan")
        self.assertEqual(output["input_audio"]["machine_id"], "id_00")
        self.assertEqual(output["input_audio"]["snr_tag"], "minus6dB")


if __name__ == "__main__":
    unittest.main()
