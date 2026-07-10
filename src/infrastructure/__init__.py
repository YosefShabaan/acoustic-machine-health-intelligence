"""Infrastructure adapters for the Fan Production MVP."""

from .artifact_registry import (
    ArtifactNotRegisteredError,
    ArtifactRegistry,
    ResolvedArtifactConfig,
)
from .audio_storage import (
    AudioNotFoundError,
    AudioStorage,
    DurableAudioStorage,
    AudioStorageError,
    AudioStorageMetadata,
    LocalAudioStorage,
    LocalDurableAudioStorage,
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
    "DurableAudioStorage",
    "AudioStorageError",
    "AudioStorageMetadata",
    "ArtifactNotRegisteredError",
    "ArtifactRegistry",
    "LocalAudioStorage",
    "LocalDurableAudioStorage",
    "PostgresAnalysisRepository",
    "PostgresEventRepository",
    "ResolvedArtifactConfig",
    "SQLiteAnalysisRepository",
    "SQLiteEventRepository",
    "UnsupportedAudioTypeError",
    "connect_postgres",
    "connect_sqlite",
    "initialize_sqlite_schema",
]


def __getattr__(name: str):
    """Lazy import for PostgreSQL adapters to avoid psycopg dependency at import time."""
    _pg_names = {
        "PostgresAnalysisRepository",
        "PostgresEventRepository",
        "connect_postgres",
    }
    if name in _pg_names:
        from .persistence.postgres_repository import (
            PostgresAnalysisRepository,
            PostgresEventRepository,
            connect_postgres,
        )
        _exports = {
            "PostgresAnalysisRepository": PostgresAnalysisRepository,
            "PostgresEventRepository": PostgresEventRepository,
            "connect_postgres": connect_postgres,
        }
        return _exports[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
