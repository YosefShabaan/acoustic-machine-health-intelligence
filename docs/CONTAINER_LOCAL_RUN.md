# Fan Production MVP Local Containers

Task: `TASK-PROD-13`

This configuration starts a bounded local Fan Production MVP stack:

- `api`: FastAPI application on `/api/v1`
- `worker`: database-backed event worker
- `postgres`: PostgreSQL 16 persistent database

API and worker share the same PostgreSQL database via `DATABASE_URL`. When
`DATABASE_URL` is not set, both fall back to SQLite for local tests.

The Docker image installs the verified local CPU Torch line
`torch==2.11.0+cpu` before the general requirements file. This avoids pulling a
large CUDA runtime into the local CPU-only container image.

## Database

PostgreSQL 16 is the production database. The migration
`src/infrastructure/persistence/migrations/001_initial_postgres.sql` is applied
automatically at application startup by the `connect_postgres` function.

API and worker connect using the `DATABASE_URL` environment variable:

```text
postgresql://amhi:amhi_local_dev_password@postgres:5432/amhi
```

Data persists in the `postgres-data` Docker volume across restarts.

## Artifact Policy

The image must not contain:

- MIMII datasets
- WAV files
- NumPy arrays
- model weights
- semantic embedding artifacts
- Gemini API keys

External development artifacts are mounted into the containers:

```powershell
$env:AMHI_EXTERNAL_ARTIFACT_ROOT = "D:/PDM_Data/MIMII"
```

Inside the containers this is available as:

```text
/mnt/amhi-artifacts
```

`PDM_DATA_ROOT` points to that mounted path.

## Build

```powershell
docker compose build
```

## Start

```powershell
$env:GEMINI_API_KEY = "<configured outside Git>"
$env:AMHI_EXTERNAL_ARTIFACT_ROOT = "D:/PDM_Data/MIMII"
docker compose up -d postgres api worker
```

Health:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/health
```

Readiness:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/ready
```

## Smoke Test

The smoke script uses `AMHI_WORKER_PIPELINE_MODE=stub` so it can verify the
container lifecycle without scoring audio, running Expert B, retrieving RAG, or
calling Gemini.

```powershell
python scripts/container_smoke.py
```

The stub mode enables only this claim:

```text
API -> PostgreSQL persistence -> worker -> persisted result lifecycle works in containers.
```

It does not enable any scientific model, root-cause, maintenance grounding, RUL,
confidence, probability, production acceptance, or multi-machine claim.

For a real Fan pipeline run, keep the default worker mode:

```powershell
$env:AMHI_WORKER_PIPELINE_MODE = "real"
```

That path requires the external Fan artifacts, semantic RAG index, readable Fan
audio, and Gemini provider configuration to be available through mounted
configuration.

## Stop

```powershell
docker compose down
```

## Data Persistence

Event and analysis data persists in the `postgres-data` Docker volume.
To destroy all data:

```powershell
docker compose down -v
```
