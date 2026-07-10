"""Web Security Hardening for Fan Production MVP."""

from typing import Callable, Awaitable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from config import DEBUG_MODE

import os

limiter = Limiter(key_func=get_remote_address)
if os.environ.get("PYTEST_CURRENT_TEST") or os.environ.get("TESTING") == "true":
    limiter.enabled = False

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
