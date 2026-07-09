"""Tests for machine-aware artifact registry resolution."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from infrastructure import ArtifactNotRegisteredError, ArtifactRegistry  # noqa: E402


class ArtifactRegistryTests(unittest.TestCase):
    """ArtifactRegistry must not silently fall back to Fan artifacts."""

    def test_fan_minus6db_resolves_full_real_intelligence_artifacts(self) -> None:
        config = ArtifactRegistry().resolve(
            machine_type="fan",
            machine_id="id_00",
            snr_tag="minus6dB",
        )

        self.assertEqual(config.machine_type, "fan")
        self.assertEqual(config.machine_id, "id_00")
        self.assertEqual(config.snr_tag, "minus6dB")
        self.assertEqual(config.expert_a_model_path.name, "anomaly_detector_minus6dB.pt")
        self.assertEqual(config.expert_a_norm_stats_path.name, "ad_norm_stats_minus6dB.npz")
        self.assertEqual(
            config.expert_b_reference_index_path.name,
            "timbre_reference_index_fan_id_00_minus6dB.json",
        )
        self.assertEqual(config.embedding_model, "expert_a_bottleneck_adaptation")
        self.assertEqual(config.k, 30)
        self.assertEqual(config.distance, "euclidean")
        self.assertIsNone(config.rank_threshold)
        self.assertEqual(config.rag_corpus_version, "AMHI-FAN-MAINT-KB-v1")
        self.assertEqual(config.rag_retriever_type, "semantic")
        self.assertIsNotNone(config.semantic_index_path)
        self.assertTrue(config.real_intelligence_available)
        self.assertIs(config.require_real_intelligence(), config)

    def test_fan_zero_and_plus_snr_resolve_expert_a_only(self) -> None:
        registry = ArtifactRegistry()
        for snr_tag in ("0dB", "plus6dB"):
            config = registry.resolve(
                machine_type="fan",
                machine_id="id_00",
                snr_tag=snr_tag,
            )
            self.assertEqual(config.expert_a_model_path.name, f"anomaly_detector_{snr_tag}.pt")
            self.assertEqual(config.expert_a_norm_stats_path.name, f"ad_norm_stats_{snr_tag}.npz")
            self.assertTrue(config.expert_a_available)
            self.assertFalse(config.expert_b_available)
            self.assertIsNone(config.expert_b_reference_index_path)
            self.assertIsNone(config.semantic_index_path)
            self.assertFalse(config.real_intelligence_available)
            with self.assertRaises(ArtifactNotRegisteredError):
                config.require_real_intelligence()

    def test_unsupported_machine_rejected(self) -> None:
        with self.assertRaises(ArtifactNotRegisteredError):
            ArtifactRegistry().resolve(
                machine_type="pump",
                machine_id="id_00",
                snr_tag="minus6dB",
            )

    def test_unknown_machine_id_rejected(self) -> None:
        with self.assertRaises(ArtifactNotRegisteredError):
            ArtifactRegistry().resolve(
                machine_type="fan",
                machine_id="id_01",
                snr_tag="minus6dB",
            )

    def test_unregistered_snr_rejected(self) -> None:
        with self.assertRaises(ArtifactNotRegisteredError):
            ArtifactRegistry().resolve(
                machine_type="fan",
                machine_id="id_00",
                snr_tag="unknownSNR",
            )

    def test_no_silent_fan_fallback_for_other_machines(self) -> None:
        registry = ArtifactRegistry()
        for machine_type in ("pump", "valve", "slide rail"):
            with self.assertRaises(ArtifactNotRegisteredError) as context:
                registry.resolve(
                    machine_type=machine_type,
                    machine_id="id_00",
                    snr_tag="minus6dB",
                )
            self.assertIn(machine_type, str(context.exception))


if __name__ == "__main__":
    unittest.main()
