"""Web Security Hardening for Fan Production MVP."""

from typing import Callable, Awaitable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from config import DEBUG_MODE


# Rate limiter is always enabled. Tests that need to bypass rate limiting
# must use explicit app-level configuration (e.g. setting limiter.enabled
# in a test fixture), not implicit environment-variable bypasses.
limiter = Limiter(key_func=get_remote_address)


class SecureHeadersMiddleware(BaseHTTPMiddleware):
    """Adds security headers to all responses."""

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        response = await call_next(request)

        # Prevent MIME-sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent Clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Strict Transport Security (HSTS) only in HTTPS production contexts
        if not DEBUG_MODE and request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Content Security Policy
        # - default-src 'self'
        # - style-src 'self' 'unsafe-inline' (needed for inline styles in dashboard)
        # - script-src 'self' 'unsafe-inline' (needed for inline scripts in dashboard)
        response.headers["Content-Security-Policy"] = "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'"

        return response
