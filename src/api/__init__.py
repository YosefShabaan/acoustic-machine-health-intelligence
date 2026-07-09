"""FastAPI application boundary for the Fan Production MVP."""

from .app import ApiDependencies, create_app

__all__ = [
    "ApiDependencies",
    "create_app",
]
