# Production Security Review

## Authentication
- **Session-based authentication** implemented using Signed Cookies (`itsdangerous` via Starlette `SessionMiddleware`).
- **Single-tenant technician model** bootstrapped via `AMHI_ADMIN_USERNAME` and `AMHI_ADMIN_PASSWORD_HASH`.
- Passwords hashed using `bcrypt` (default 12 rounds).
- **CSRF protection** enforced for state-changing operations via `X-CSRF-Token` headers.
- **Fail closed in production**: API refuses to start if `AMHI_ADMIN_PASSWORD_HASH` or `AMHI_SESSION_SECRET` are missing and `DEBUG_MODE=false`.

## Rate Limiting & DoS Protection
- `slowapi` bounds login attempts (10/min) and event creation (5/min).
- Global payload size limit enforced via application layer check (`DEFAULT_MAX_UPLOAD_BYTES = 25MB`).

## Hardening
- **Debug Mode Disabled**: By default `DEBUG_MODE=false`. This hides traceback details, Swagger `/docs`, `/redoc`, and `/openapi.json`.
- **CORS Restricted**: Allowed origins constrained via `ALLOWED_ORIGINS` environment variable.
- **Trusted Host**: Allowed hosts constrained via `ALLOWED_HOSTS` environment variable.
- **Secure Headers Middleware**: Applies `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Strict-Transport-Security: max-age=31536000; includeSubDomains`.
- **HttpOnly, Secure, SameSite=Lax** session cookies (Secure is tied to `DEBUG_MODE=false`).

## Logging & Secrets
- `AMHI_ADMIN_PASSWORD_HASH` and `AMHI_SESSION_SECRET` managed exclusively via environment variables.
- Structured Logger implemented, no DB credentials or Gemini API keys are logged.

## Container Hardening
- Base image is `python:3.11-slim` with explicitly defined unprivileged users.
- No embedded secrets.

## Final Review
Repository secret scan performed. No raw passwords, API tokens, or keys identified in committed files.
