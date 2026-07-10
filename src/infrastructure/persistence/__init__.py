"""Persistence adapters for Fan Production MVP event state."""

from .sqlite_repository import (
    SQLiteAnalysisRepository,
    SQLiteEventRepository,
    connect_sqlite,
    initialize_sqlite_schema,
)

__all__ = [
    "SQLiteAnalysisRepository",
    "SQLiteEventRepository",
    "connect_sqlite",
    "initialize_sqlite_schema",
]

# PostgreSQL adapters are imported lazily to avoid requiring psycopg2
# in environments that only use SQLite (tests, local dev).
# Use: from infrastructure.persistence.postgres_repository import ...
# Or:  from infrastructure import PostgresEventRepository (when psycopg2 is available)


def __getattr__(name: str):
    """Lazy import for PostgreSQL adapters."""
    _pg_names = {
        "PostgresAnalysisRepository",
        "PostgresEventRepository",
        "connect_postgres",
    }
    if name in _pg_names:
        from .postgres_repository import (
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
