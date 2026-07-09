# AMHI API Contract v1

Status: `CONTRACT_APPROVED_FOR_IMPLEMENTATION`

Scope: Fan Production MVP only.

Base path: `/api/v1`

This contract defines the REST boundary before route implementation. It does
not implement FastAPI routes, worker behavior, dashboard rendering, or pipeline
execution.

## Scope

Supported machine scope for v1:

- `machine_type`: `fan`
- `machine_id`: `id_00`
- `snr_tag`: `minus6dB`

Known unsupported scopes:

- Pump
- Valve
- Slide Rail
- Cross-machine requests
- MIMII DG/domain-shift requests

Unsupported machine scopes must return a bounded API error. They must not reuse
Fan artifacts silently.

## Ingestion Mode Decision

Canonical Fan Production MVP ingestion uses `multipart/form-data` upload on:

`POST /api/v1/events`

The request includes a WAV file and explicit machine metadata. The API stores
the uploaded file through the audio storage boundary and persists only an
internal audio reference plus safe metadata. Raw audio bytes are not stored in
relational database rows and are not committed to Git.

Development and unit tests may use a JSON registered-reference request only
when explicitly enabled by application configuration. That mode is not the
canonical staging ingestion path and must not expose local absolute processing
paths in API responses.
The reference string must be resolvable by the configured `AudioStorage`
adapter. The current `LocalAudioStorage` adapter resolves local paths; a
future registry URI adapter can support `registered://` references without
changing the public endpoint.

## Statuses

Event status values:

- `queued`
- `processing`
- `completed`
- `failed`

Analysis run status values:

- `processing`
- `completed`
- `failed`

## Endpoints

Required v1 endpoints:

- `POST /api/v1/events`
- `GET /api/v1/events/{event_id}`
- `GET /api/v1/events`
- `GET /api/v1/machines/{machine_type}/{machine_id}/events`
- `GET /api/v1/health`
- `GET /api/v1/ready`

## Timestamp Format

All timestamps are ISO 8601 UTC strings.

Example:

```json
"2026-07-09T14:30:00Z"
```

## Error Response

All non-2xx API errors return:

```json
{
  "api_version": "v1",
  "error": {
    "code": "unsupported_machine",
    "message": "Only fan/id_00 is supported by this Fan Production MVP.",
    "details": {},
    "request_id": "req_01HY..."
  }
}
```

Allowed error codes include:

- `invalid_request`
- `unsupported_machine`
- `unsupported_machine_id`
- `unsupported_snr`
- `unsupported_audio_type`
- `audio_not_found`
- `audio_too_large`
- `event_not_found`
- `dependency_not_ready`
- `internal_error`

Errors must not expose secrets, internal tracebacks, raw prompts, provider API
keys, local processing paths, or full private configuration.

## Event Summary Schema

Event summaries appear in create/list/detail responses:

```json
{
  "event_id": "event_01HY...",
  "machine_type": "fan",
  "machine_id": "id_00",
  "snr_tag": "minus6dB",
  "status": "queued",
  "created_at": "2026-07-09T14:30:00Z",
  "updated_at": "2026-07-09T14:30:00Z",
  "error": null,
  "audio": {
    "file_name": "00000002.wav",
    "suffix": ".wav",
    "size_bytes": 2560080,
    "storage_backend": "local",
    "reference_exposed": false
  }
}
```

The `audio` object may expose file name, suffix, size, and backend type. It must
not expose the local processing path by default.

## POST /api/v1/events

Create a persistent queued event and return immediately with `202 Accepted`.
The request must not hold the HTTP connection open for the full Gemini/pipeline
path.

### Multipart Request

Content type: `multipart/form-data`

Required fields:

- `machine_type`: `fan`
- `machine_id`: `id_00`
- `snr_tag`: `minus6dB`
- `audio_file`: WAV file

Optional fields:

- `client_event_id`: client-supplied idempotency/correlation token

Validation rules:

- `machine_type` must be `fan`.
- `machine_id` must be `id_00`.
- `snr_tag` must be `minus6dB` for the full Real Intelligence path.
- `audio_file` must have suffix `.wav`.
- The API validates file presence and supported type before creating work.

### Development JSON Request

This mode is allowed only when configured for local development or unit tests.

Content type: `application/json`

```json
{
  "machine_type": "fan",
  "machine_id": "id_00",
  "snr_tag": "minus6dB",
  "registered_audio_reference": "path-resolvable-by-configured-audio-storage.wav"
}
```

### Response: 202

```json
{
  "api_version": "v1",
  "event": {
    "event_id": "event_01HY...",
    "machine_type": "fan",
    "machine_id": "id_00",
    "snr_tag": "minus6dB",
    "status": "queued",
    "created_at": "2026-07-09T14:30:00Z",
    "updated_at": "2026-07-09T14:30:00Z",
    "error": null,
    "audio": {
      "file_name": "00000002.wav",
      "suffix": ".wav",
      "size_bytes": 2560080,
      "storage_backend": "local",
      "reference_exposed": false
    }
  },
  "links": {
    "self": "/api/v1/events/event_01HY..."
  }
}
```

Runtime gate: POST only creates and queues the event. Background processing
performs AMHIPipelineService execution in TASK-PROD-08.

## GET /api/v1/events/{event_id}

Return event state and, when available, analysis run/result data.
Queued events may return `analysis_run: null` and `result: null` until a
worker claims the event.

### Response: queued or processing

```json
{
  "api_version": "v1",
  "event": {
    "event_id": "event_01HY...",
    "machine_type": "fan",
    "machine_id": "id_00",
    "snr_tag": "minus6dB",
    "status": "processing",
    "created_at": "2026-07-09T14:30:00Z",
    "updated_at": "2026-07-09T14:30:05Z",
    "error": null,
    "audio": {
      "file_name": "00000002.wav",
      "suffix": ".wav",
      "size_bytes": 2560080,
      "storage_backend": "local",
      "reference_exposed": false
    }
  },
  "analysis_run": {
    "analysis_run_id": "analysis_01HY...",
    "pipeline_version": "amhi-real-intelligence-v0.2",
    "status": "processing",
    "started_at": "2026-07-09T14:30:05Z",
    "completed_at": null,
    "total_duration": null,
    "artifact_metadata": {
      "machine_type": "fan",
      "machine_id": "id_00",
      "snr_tag": "minus6dB",
      "expert_b_reference_index_id": "timbre_reference_index_fan_id_00_minus6dB.json",
      "k": 30,
      "distance": "euclidean",
      "rank_threshold": null,
      "rag_corpus_version": "AMHI-FAN-MAINT-KB-v1",
      "rag_retriever_type": "semantic"
    }
  },
  "result": null
}
```

### Response: completed

```json
{
  "api_version": "v1",
  "event": {
    "event_id": "event_01HY...",
    "machine_type": "fan",
    "machine_id": "id_00",
    "snr_tag": "minus6dB",
    "status": "completed",
    "created_at": "2026-07-09T14:30:00Z",
    "updated_at": "2026-07-09T14:30:25Z",
    "error": null,
    "audio": {
      "file_name": "00000002.wav",
      "suffix": ".wav",
      "size_bytes": 2560080,
      "storage_backend": "local",
      "reference_exposed": false
    }
  },
  "analysis_run": {
    "analysis_run_id": "analysis_01HY...",
    "pipeline_version": "amhi-real-intelligence-v0.2",
    "status": "completed",
    "started_at": "2026-07-09T14:30:05Z",
    "completed_at": "2026-07-09T14:30:25Z",
    "total_duration": 20.0,
    "artifact_metadata": {
      "k": 30,
      "distance": "euclidean",
      "rank_threshold": null,
      "rag_corpus_version": "AMHI-FAN-MAINT-KB-v1",
      "rag_retriever_type": "semantic"
    }
  },
  "result": {
    "expert_a": {
      "anomaly_score": 0.622095,
      "threshold": 0.593284,
      "is_anomaly": true
    },
    "expert_b": {
      "skipped": false,
      "k": 30,
      "distance": "euclidean",
      "rank_threshold": null,
      "timbre_rank_scores": {
        "hardness": {"rank_score": 0.7},
        "depth": {"rank_score": 0.4}
      },
      "directions": null
    },
    "structured_context": {
      "schema_version": "0.2.0"
    },
    "retrieval": {
      "retriever_type": "semantic",
      "corpus_version": "AMHI-FAN-MAINT-KB-v1",
      "query": "fan anomaly acoustic maintenance inspection",
      "sources": [
        {
          "source_id": "source-id",
          "chunk_id": "chunk-id",
          "title": "source title",
          "snippet": "short source-preserving excerpt"
        }
      ]
    },
    "explanation": {
      "summary": "Bounded technician-facing explanation.",
      "observations": [],
      "hypotheses": [],
      "metadata": {
        "provider": "gemini",
        "model": "configured-model",
        "generation_mode": "live_gemini",
        "fallback_used": false
      }
    },
    "maintenance": {
      "available": true,
      "text": "Source-grounded maintenance guidance.",
      "recommended_next_actions": [],
      "metadata": {
        "provider": "gemini",
        "generation_mode": "live_gemini",
        "fallback_used": false
      }
    },
    "timings": {
      "total_seconds": 20.0
    },
    "limits": {
      "same_machine_same_audio": true,
      "rank_scores_are_probabilities": false,
      "physical_root_cause_confirmed": false,
      "remaining_life_prediction_available": false,
      "production_maintenance_validation_complete": false,
      "multi_machine_generalization_enabled": false
    }
  }
}
```

### Response: failed

```json
{
  "api_version": "v1",
  "event": {
    "event_id": "event_01HY...",
    "status": "failed",
    "error": {
      "code": "audio_not_found",
      "summary": "Audio reference was not readable."
    }
  },
  "analysis_run": {
    "analysis_run_id": "analysis_01HY...",
    "status": "failed",
    "error": {
      "code": "audio_not_found",
      "summary": "Audio reference was not readable."
    }
  },
  "result": null
}
```

Failure payloads must include safe summaries only.

## GET /api/v1/events

List events with offset pagination.

Query parameters:

- `status`: optional one of `queued`, `processing`, `completed`, `failed`
- `limit`: optional integer, default `50`, maximum `100`
- `offset`: optional integer, default `0`

Response:

```json
{
  "api_version": "v1",
  "items": [],
  "pagination": {
    "limit": 50,
    "offset": 0,
    "count": 0,
    "next_offset": null
  }
}
```

## GET /api/v1/machines/{machine_type}/{machine_id}/events

List events for one machine.

Path parameters:

- `machine_type`: must be `fan`
- `machine_id`: must be `id_00`

Query parameters:

- `limit`: optional integer, default `50`, maximum `100`
- `offset`: optional integer, default `0`

Unsupported machines return `unsupported_machine` or
`unsupported_machine_id`.

## GET /api/v1/health

Health means the process can serve HTTP requests.

Response:

```json
{
  "api_version": "v1",
  "status": "ok",
  "service": "amhi-fan-production-mvp"
}
```

Health must not perform audio processing or live Gemini generation.

## GET /api/v1/ready

Readiness means the application dependencies are available enough to accept
Fan work.

Response:

```json
{
  "api_version": "v1",
  "ready": true,
  "status": "ready",
  "dependencies": {
    "database": {"status": "ok"},
    "artifact_registry": {"status": "ok"},
    "audio_storage": {"status": "ok"},
    "rag_index": {"status": "ok"},
    "gemini_config": {"status": "configured"},
    "worker": {"status": "initialized"}
  }
}
```

Readiness may check Gemini configuration presence, but must not make a live
Gemini generation call on every request. It must not process audio.

## API Versioning Policy

- v1 remains under `/api/v1`.
- Backward-incompatible response changes require a new base path.
- Additive optional fields are allowed in v1 when they do not weaken safety or
  claim guardrails.
- Deprecated fields must remain documented until the next major API path.

## Response Safety Rules

API responses must not expose:

- provider API keys or secrets
- internal tracebacks
- raw prompt internals by default
- local absolute processing paths by default
- raw audio bytes
- full maintenance manuals
- model weights, embeddings, NumPy arrays, or generated scientific artifacts

## Scientific Guardrails

API responses must not claim:

- remaining useful life
- time to failure
- confirmed physical root cause
- fault probability
- confidence percentage
- severity percentage
- Expert B quantitative timbre-direction accuracy
- production maintenance validation
- multi-machine generalization
- domain robustness

Expert A scores are anomaly scores and thresholds, not calibrated failure
probabilities. Expert B rank scores are qualitative local rank evidence, not
probabilities or confidence values.

## Implementation Notes For TASK-PROD-07

- Routes should call application services and repositories.
- Routes must not implement Expert A, Expert B, RAG, Gemini, or maintenance
  orchestration.
- `POST /api/v1/events` must create a queued persistent event and return
  `202 Accepted`.
- Background processing is defined in TASK-PROD-08.
- OpenAPI schemas should mirror this contract.
- CI unit tests must use mocked or bounded dependencies and must not make live
  Gemini calls.
