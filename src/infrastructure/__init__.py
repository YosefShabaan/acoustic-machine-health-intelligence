"""Infrastructure adapters for the Fan Production MVP."""

from .artifact_registry import (
    ArtifactNotRegisteredError,
    ArtifactRegistry,
    ResolvedArtifactConfig,
)
from .audio_storage import (
    AudioNotFoundError,
    AudioStorage,
    AudioStorageError,
    AudioStorageMetadata,
    LocalAudioStorage,
    UnsupportedAudioTypeError,
)
from .persistence import (
    SQLiteAnalysisRepository,
    SQLiteEventRepository,
    connect_sqlite,
    initialize_sqlite_schema,
)

__all__ = [
    "AudioNotFoundError",
    "AudioStorage",
    "AudioStorageError",
    "AudioStorageMetadata",
    "ArtifactNotRegisteredError",
    "ArtifactRegistry",
    "LocalAudioStorage",
    "ResolvedArtifactConfig",
    "SQLiteAnalysisRepository",
    "SQLiteEventRepository",
    "UnsupportedAudioTypeError",
    "connect_sqlite",
    "initialize_sqlite_schema",
]
