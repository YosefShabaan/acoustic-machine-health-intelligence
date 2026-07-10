"""Audio storage abstraction for Fan Production MVP processing."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol


class AudioStorageError(ValueError):
    """Raised when an audio reference cannot be resolved safely."""


class AudioNotFoundError(AudioStorageError):
    """Raised when an audio reference does not point to a file."""


class UnsupportedAudioTypeError(AudioStorageError):
    """Raised when an audio reference uses an unsupported file type."""


class AudioStorage(Protocol):
    """Resolve an audio reference into a local processing path."""

    def resolve(self, audio_reference: str | Path) -> "AudioStorageMetadata":
        """Resolve and validate an audio reference."""


@dataclass(frozen=True)
class AudioStorageMetadata:
    """Metadata returned by an AudioStorage implementation."""

    original_reference: str
    processing_path: Path
    storage_backend: str
    file_name: str
    suffix: str
    exists: bool
    size_bytes: int
    copied: bool = False
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-safe storage metadata."""
        return {
            "original_reference": self.original_reference,
            "processing_path": str(self.processing_path),
            "storage_backend": self.storage_backend,
            "file_name": self.file_name,
            "suffix": self.suffix,
            "exists": self.exists,
            "size_bytes": self.size_bytes,
            "copied": self.copied,
            "extra": dict(self.extra),
        }


@dataclass(frozen=True)
class LocalAudioStorage:
    """Resolve local WAV references without copying dataset files."""

    supported_suffixes: tuple[str, ...] = (".wav",)

    def resolve(self, audio_reference: str | Path) -> AudioStorageMetadata:
        """Validate a local audio reference and return metadata."""
        path = Path(audio_reference)
        suffix = path.suffix.lower()
        if suffix not in self.supported_suffixes:
            raise UnsupportedAudioTypeError(
                f"Unsupported audio file type {path.suffix!r}; supported: {self.supported_suffixes}"
            )
        if not path.exists() or not path.is_file():
            raise AudioNotFoundError(f"Audio reference does not exist as a file: {path}")
        resolved = path.resolve()
        return AudioStorageMetadata(
            original_reference=str(audio_reference),
            processing_path=resolved,
            storage_backend="local",
            file_name=resolved.name,
            suffix=suffix,
            exists=True,
            size_bytes=resolved.stat().st_size,
            copied=False,
            extra={
                "parent": str(resolved.parent),
            },
        )


class DurableAudioStorage(AudioStorage, Protocol):
    """
    Store and resolve audio references in a durable location.
    
    RETENTION POLICY:
    Uploaded audio is retained for 30 days. 
    - In local mode, the Docker volume `runtime-data` persists across restarts, 
      but a periodic cleanup script should prune older directories.
    - In production, object storage lifecycle rules (e.g. GCS Object Lifecycle)
      should be configured to automatically delete objects older than 30 days.
    """
    
    def store(self, event_id: str, file_name: str, content: bytes) -> str:
        """
        Store audio durably and return a logical reference.
        Validates the audio type, size, and filename.
        """


@dataclass(frozen=True)
class LocalDurableAudioStorage:
    """Implement DurableAudioStorage using a local mounted directory."""
    
    upload_dir: Path
    supported_suffixes: tuple[str, ...] = (".wav",)
    max_size_bytes: int = 10 * 1024 * 1024
    
    def store(self, event_id: str, file_name: str, content: bytes) -> str:
        """Store audio to the upload directory and return its path."""
        if not content:
            raise AudioStorageError("Audio content is empty.")
        if len(content) > self.max_size_bytes:
            raise AudioStorageError(f"Audio exceeds maximum size of {self.max_size_bytes} bytes.")
            
        path = Path(file_name)
        suffix = path.suffix.lower()
        if suffix not in self.supported_suffixes:
            raise UnsupportedAudioTypeError(
                f"Unsupported audio file type {suffix!r}; supported: {self.supported_suffixes}"
            )
            
        # Enforce safe filename, avoiding path traversal from the original name
        safe_file_name = "".join(c for c in path.name if c.isalnum() or c in "._-")
        if not safe_file_name or safe_file_name.startswith("."):
            safe_file_name = f"audio{suffix}"
        
        # Ensure event_id is safe (UUID hex)
        safe_event_dir = self.upload_dir / event_id
        resolved_dir = safe_event_dir.resolve()
        
        if not str(resolved_dir).startswith(str(self.upload_dir.resolve())):
            raise AudioStorageError("Invalid event_id path traversal detected.")
            
        resolved_dir.mkdir(parents=True, exist_ok=True)
        target_path = resolved_dir / safe_file_name
        
        with target_path.open("wb") as handle:
            handle.write(content)
            
        return str(target_path)

    def resolve(self, audio_reference: str | Path) -> AudioStorageMetadata:
        """Validate a local audio reference and return metadata."""
        path = Path(audio_reference)
        suffix = path.suffix.lower()
        if suffix not in self.supported_suffixes:
            raise UnsupportedAudioTypeError(
                f"Unsupported audio file type {path.suffix!r}; supported: {self.supported_suffixes}"
            )
        if not path.exists() or not path.is_file():
            raise AudioNotFoundError(f"Audio reference does not exist as a file: {path}")
        resolved = path.resolve()
        return AudioStorageMetadata(
            original_reference=str(audio_reference),
            processing_path=resolved,
            storage_backend="local_durable",
            file_name=resolved.name,
            suffix=suffix,
            exists=True,
            size_bytes=resolved.stat().st_size,
            copied=False,
            extra={
                "parent": str(resolved.parent),
            },
        )
