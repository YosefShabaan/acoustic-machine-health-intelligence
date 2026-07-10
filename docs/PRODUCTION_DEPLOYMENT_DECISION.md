# AMHI Fan MVP — Production Deployment Decision

## Date
2026-07-10

## Status
**DEPLOYMENT_APPROVAL_REQUIRED=true**

---

## Measured System Requirements

| Metric | Value |
|---|---|
| Docker image size | 2.14 GB |
| Runtime memory (API + Worker) | ~817 MiB |
| Event processing latency | ~23 seconds (includes Gemini API calls) |
| Worker type | Polling loop (SQLite/Postgres, no external queue) |
| ML artifacts | ~200 MB (model weights, norm stats, RAG embeddings, reference index) |
| Uploaded WAV per event | Up to 25 MB |
| Concurrency model | Single-worker sequential processing |

## Architecture Candidates Evaluated

### Option A: Google Compute Engine VM (Selected)

**Architecture**: Single e2-medium or e2-standard-2 VM running Docker Compose with:
- API container (uvicorn on port 8000)
- Worker container (Python polling loop)
- PostgreSQL container (or Cloud SQL Micro)
- Caddy reverse proxy for automatic HTTPS via Let's Encrypt
- Persistent disk for uploads and ML artifacts

**Advantages**:
- Simplest lift-and-shift from local Docker environment
- 2.14 GB image runs without modification
- 817 MiB memory fits comfortably in 4 GB RAM
- Persistent disk for PostgreSQL, uploads, and ML artifacts
- Caddy auto-HTTPS with zero certificate management
- Fixed monthly cost (~$25-35/month for e2-standard-2)
- No cold starts, no image size constraints
- Background worker runs continuously

**Disadvantages**:
- Manual OS updates (mitigated by Container-Optimized OS)
- Single VM availability (acceptable for MVP)

### Option B: Google Cloud Run (Not Selected)

**Architecture**: Two Cloud Run services (API + Worker) with Cloud SQL and GCS.

**Why not selected**:
- 2.14 GB image exceeds comfortable Cloud Run deploy/startup times
- Cold start with 817 MiB memory would be 30+ seconds
- Background worker requires "always-on" Cloud Run instance (cost overhead)
- Cloud SQL connection requires Auth Proxy or VPC connector (complexity)
- GCS integration for uploaded audio adds code changes
- Requires PostgreSQL migration from SQLite (already supported, but adds deploy steps)
- Higher operational complexity than a simple VM for this single-tenant MVP

### Option C: Railway/Render/Fly.io (Not Evaluated)

Third-party PaaS platforms were not evaluated because the user's existing GCP context and the measured resource requirements make GCE the natural fit.

---

## Selected Architecture

```
SELECTED_PROVIDER:            Google Cloud Platform — Compute Engine
WEB_API:                      Docker container (uvicorn, port 8000)
WORKER:                       Docker container (Python polling loop)
DATABASE:                     PostgreSQL in Docker (or Cloud SQL Micro)
AUDIO_STORAGE:                Persistent disk directory (/data/uploads)
ARTIFACT_STORAGE:             Persistent disk directory (/data/artifacts)
ESTIMATED_COST_CATEGORY:      ~$25-35/month (e2-standard-2 + 30 GB disk)
EXACT_USER_ACTION_REQUIRED:   User must create a GCP project (or confirm existing),
                              enable Compute Engine API, and provide a domain name
                              (or accept IP-based access with self-signed cert).
```

## Deployment Architecture Diagram

```
[End User Browser]
        |
        | HTTPS (port 443)
        v
  [Caddy Reverse Proxy]  -- auto Let's Encrypt SSL
        |
        | HTTP (port 8000)
        v
  [AMHI API Container]   -- FastAPI + uvicorn
        |
        | shared PostgreSQL
        v
  [PostgreSQL Container]  -- persistent volume
        ^
        |
  [AMHI Worker Container] -- polling loop, processes queued events
        |
        v
  [ML Artifacts Volume]   -- model weights, norm stats, RAG index
  [Upload Storage Volume]  -- persisted uploaded WAV files
```

## Required Secrets (Environment Variables)

| Variable | Description |
|---|---|
| `GEMINI_API_KEY` | Google AI Gemini API key |
| `AMHI_SESSION_SECRET` | Session cookie signing key |
| `AMHI_ADMIN_USERNAME` | Technician login username |
| `AMHI_ADMIN_PASSWORD_HASH` | bcrypt hash of technician password |
| `DATABASE_URL` | PostgreSQL connection string |

## User Action Required Before Deployment

1. Confirm or create a GCP project
2. Confirm or provide a domain name (or accept IP-only access)
3. Provide a Gemini API key
4. Choose technician username and password
5. Approve the estimated ~$25-35/month cost

## Scientific Scope

This deployment does not change the scientific scope of the AMHI Fan MVP:
- Same-machine same-audio bounded Fan id_00 minus6dB
- No RUL, no confirmed root cause, no fault probability
- No multi-machine generalization
- Expert B rank scores are qualitative local ranks
- Production maintenance validation is not complete
