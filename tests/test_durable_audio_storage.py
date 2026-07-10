import sys
from pathlib import Path

# Add src to the Python path for testing
src_path = str(Path(__file__).resolve().parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

import pytest
from infrastructure.audio_storage import (
    LocalDurableAudioStorage,
    AudioStorageError,
    UnsupportedAudioTypeError,
    AudioNotFoundError,
)

def test_store_valid_audio(tmp_path: Path):
    storage = LocalDurableAudioStorage(upload_dir=tmp_path)
    content = b"fake audio content"
    event_id = "event_123"
    
    reference = storage.store(event_id, "test.wav", content)
    
    # Target path should contain event_id and safe file name test.wav
    expected_path = tmp_path / event_id / "test.wav"
    assert reference == str(expected_path)
    assert expected_path.exists()
    assert expected_path.read_bytes() == content

def test_store_empty_content(tmp_path: Path):
    storage = LocalDurableAudioStorage(upload_dir=tmp_path)
    with pytest.raises(AudioStorageError, match="empty"):
        storage.store("event_123", "test.wav", b"")

def test_store_exceeds_max_size(tmp_path: Path):
    storage = LocalDurableAudioStorage(upload_dir=tmp_path, max_size_bytes=10)
    with pytest.raises(AudioStorageError, match="maximum size"):
        storage.store("event_123", "test.wav", b"0123456789A")

def test_store_unsupported_type(tmp_path: Path):
    storage = LocalDurableAudioStorage(upload_dir=tmp_path)
    with pytest.raises(UnsupportedAudioTypeError, match="Unsupported audio file type"):
        storage.store("event_123", "test.mp3", b"content")

def test_store_path_traversal(tmp_path: Path):
    storage = LocalDurableAudioStorage(upload_dir=tmp_path)
    with pytest.raises(AudioStorageError, match="path traversal"):
        storage.store("../outside_event", "test.wav", b"content")

def test_resolve_valid_reference(tmp_path: Path):
    storage = LocalDurableAudioStorage(upload_dir=tmp_path)
    event_dir = tmp_path / "event_123"
    event_dir.mkdir()
    audio_path = event_dir / "test.wav"
    audio_path.write_bytes(b"content")
    
    metadata = storage.resolve(str(audio_path))
    assert metadata.storage_backend == "local_durable"
    assert metadata.exists is True
    assert metadata.size_bytes == 7

def test_resolve_not_found(tmp_path: Path):
    storage = LocalDurableAudioStorage(upload_dir=tmp_path)
    audio_path = tmp_path / "missing.wav"
    with pytest.raises(AudioNotFoundError):
        storage.resolve(str(audio_path))

def test_resolve_unsupported_type(tmp_path: Path):
    storage = LocalDurableAudioStorage(upload_dir=tmp_path)
    audio_path = tmp_path / "test.mp3"
    audio_path.write_bytes(b"content")
    with pytest.raises(UnsupportedAudioTypeError):
        storage.resolve(str(audio_path))
