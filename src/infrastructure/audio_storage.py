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
