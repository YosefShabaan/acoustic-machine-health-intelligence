"""Default ASGI entrypoint for the Fan Production MVP API."""

from .app import create_app


app = create_app()
