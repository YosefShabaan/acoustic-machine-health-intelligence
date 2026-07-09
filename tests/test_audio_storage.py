"""Tests for local audio storage resolution."""

from __future__ import annotations

from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from infrastructure import (  # noqa: E402
    AudioNotFoundError,
    LocalAudioStorage,
    UnsupportedAudioTypeError,
)


class LocalAudioStorageTests(unittest.TestCase):
    """LocalAudioStorage validates references without copying datasets."""

    def test_valid_local_wav_reference_returns_metadata(self) -> None:
        with TemporaryDirectory() as tmp:
            wav_path = Path(tmp) / "event.wav"
            wav_path.write_bytes(b"RIFF-test")

            metadata = LocalAudioStorage().resolve(wav_path)

            self.assertEqual(metadata.processing_path, wav_path.resolve())
            self.assertEqual(metadata.original_reference, str(wav_path))
            self.assertEqual(metadata.storage_backend, "local")
            self.assertEqual(metadata.file_name, "event.wav")
            self.assertEqual(metadata.suffix, ".wav")
            self.assertTrue(metadata.exists)
            self.assertEqual(metadata.size_bytes, len(b"RIFF-test"))
            self.assertFalse(metadata.copied)

    def test_missing_wav_path_is_rejected(self) -> None:
        with TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing.wav"
            with self.assertRaises(AudioNotFoundError):
                LocalAudioStorage().resolve(missing)

    def test_unsupported_extension_is_rejected(self) -> None:
        with TemporaryDirectory() as tmp:
            txt_path = Path(tmp) / "event.txt"
            txt_path.write_text("not audio", encoding="utf-8")
            with self.assertRaises(UnsupportedAudioTypeError):
                LocalAudioStorage().resolve(txt_path)

    def test_no_copy_side_effect(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            wav_path = root / "event.wav"
            wav_path.write_bytes(b"RIFF-original")
            before = sorted(path.name for path in root.iterdir())

            metadata = LocalAudioStorage().resolve(wav_path)

            after = sorted(path.name for path in root.iterdir())
            self.assertEqual(before, after)
            self.assertEqual(wav_path.read_bytes(), b"RIFF-original")
            self.assertFalse(metadata.copied)


if __name__ == "__main__":
    unittest.main()
