"""Session-based authentication and CSRF protection for Fan Production MVP."""

import bcrypt
import secrets
from fastapi import Request, HTTPException, status
import os
from config import AMHI_ADMIN_USERNAME, AMHI_ADMIN_PASSWORD_HASH, AMHI_SESSION_SECRET, DEBUG_MODE

def verify_secrets_configured() -> None:
    """Fail closed in production if security secrets are missing."""
    if not DEBUG_MODE:
        if not AMHI_ADMIN_USERNAME or not AMHI_ADMIN_PASSWORD_HASH or not AMHI_SESSION_SECRET:
            raise RuntimeError("Missing required authentication/session secrets in production environment.")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify bcrypt password hash."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

def verify_dashboard_session(request: Request) -> None:
    """Verify that the user has a valid authenticated session for the dashboard.

    No implicit environment-variable bypass. Tests must use explicit
    FastAPI dependency overrides to replace this dependency.
    """
    if not request.session.get("authenticated"):
        raise HTTPException(
            status_code=status.HTTP_302_FOUND,
            headers={"Location": "/dashboard/login"}
        )

def verify_api_session(request: Request) -> None:
    """Verify that the user has a valid authenticated session for the API.

    No implicit environment-variable bypass. Tests must use explicit
    FastAPI dependency overrides to replace this dependency.
    """
    if not request.session.get("authenticated"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Valid session required"
        )

def verify_csrf_token(request: Request) -> None:
    """Verify that the state-changing request contains a valid CSRF token.

    No implicit environment-variable bypass. Tests must use explicit
    FastAPI dependency overrides to replace this dependency.
    """
    if request.method in ("POST", "PUT", "DELETE", "PATCH"):
        session_token = request.session.get("csrf_token")
        header_token = request.headers.get("X-CSRF-Token")

        if not session_token or not header_token or not secrets.compare_digest(session_token, header_token):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid or missing CSRF token"
            )

def generate_csrf_token() -> str:
    """Generate a random CSRF token."""
    return secrets.token_urlsafe(32)
