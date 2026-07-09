# Fan Production MVP Architecture

Task: `TASK-PROD-01`

Status: approved architecture baseline for the Fan Production MVP implementation.

This document defines the production-oriented Fan application architecture that
will wrap the already verified Fan Real Intelligence pipeline. It does not
change Expert A, Expert B, Structured Health Context, selected semantic RAG,
Gemini explanation, Maintenance Agent V2, or the bounded Fan evidence.

Active scope:

- `machine_type = fan`
- `machine_id = id_00`
- primary Fan production MVP condition: `snr_tag = minus6dB`

Allowed positioning:

- production-oriented Fan application architecture
- deployable Fan Production MVP
- bounded staging prototype
- Fan Production MVP integration evidence

Forbidden positioning:

- ready for production operation
- ready for enterprise operation
- production maintenance validated
- physical root-cause diagnosis
- fault probability, confidence percentage, severity percentage
- Remaining Useful Life or time to failure
- Expert B quantitative timbre-direction accuracy
- multi-machine generalization
- domain robustness

## CURRENT SCRIPT ARCHITECTURE

VERIFIED REPOSITORY FACT: the current real-intelligence Fan path is driven by
bounded scripts, not by a reusable application service or API.

`scripts/run_real_intelligence_fan_smoke.py` currently owns the complete live
Fan orchestration for one event:

- artifact resolution through `_default_index`, `default_embedding_index_path`,
  `default_audio_path`, and `src/config.py`
- audio path selection for the bounded Fan reference event
- Expert A scoring through `score_expert_a`
- Expert B construction and execution through
  `AcousticTimbreDifferenceExpert`
- Expert B anomaly gating by requiring Expert A to flag the event before the
  downstream path continues
- Structured Health Context v0.2 creation through
  `context_from_expert_b_output`
- semantic RAG query construction and retrieval through
  `build_retrieval_query`, `load_embedding_index`, `GeminiEmbeddingProvider`,
  and `SemanticRetriever`
- Gemini explanation through `GeminiTextGenerator` and `explain_context`
- Gemini grounded maintenance generation through
  `GeminiMaintenanceTextGenerator` and
  `generate_grounded_maintenance_output`
- validation through `validate_real_intelligence_output` and
  `validate_maintenance_output`
- timing collection
- JSON output serialization to the external processed-artifact directory

`scripts/run_end_to_end_demo.py` is an older bounded Fan MVP path. It preserves
the same Expert A -> Expert B -> context -> retrieval -> guarded output
sequence, but it can use a local fixture maintenance source and does not
represent the selected semantic RAG plus live Gemini Fan path.

`scripts/evaluate_fan_system.py` owns bounded multi-event evaluation behavior:

- deterministic 20-event Fan stress-set selection
- normal-event Expert A scoring
- downstream continuation only for Expert A-flagged events
- per-event output writing under the external processed-artifact directory
- summary metrics for integration behavior, fallbacks, citation failures, and
  pipeline failures

`app/dashboard.py` is a static HTML renderer. It reads existing JSON artifacts
and renders technician-facing evidence. It does not persist event state, call an
API, run Expert A or Expert B, perform retrieval, call Gemini, or manage event
processing.

PROJECT DECISION: the current scripts are valid bounded evidence tools. They
must remain useful, but productionized execution must move orchestration into a
reusable application service so CLI, API, worker, and future dashboard paths use
the same Fan pipeline semantics.

## TARGET FAN PRODUCTION MVP

PROJECT DECISION: use a modular monolith for the Fan Production MVP. Do not
split into microservices for appearance.

Target runtime:

```text
Fan audio source
-> Event Ingestion API
-> Audio Storage
-> Persistent Event Record
-> Background Processing
-> AMHI Pipeline Service
   -> Expert A anomaly detection
   -> Expert B only when Expert A flags anomaly
   -> Structured Health Context v0.2
   -> selected semantic Fan maintenance RAG
   -> guarded Gemini explanation
   -> Gemini Grounded Maintenance Agent V2
   -> validation
-> Persistent Analysis Result
-> Versioned REST API
-> API-backed Technician Dashboard
-> Structured Logging
-> Metrics
-> Health / Readiness
-> Containerized bounded deployment
```

Target conceptual package layout:

```text
src/application/
  pipeline_service.py
  processing_service.py
  repositories.py

src/infrastructure/
  artifact_registry.py
  audio_storage.py
  persistence/

src/api/
  app.py
  routes.py
  schemas.py

src/observability/
  logging.py
  metrics.py
  health.py

app/
  dashboard.py
```

The exact file names may evolve in later tasks, but dependency direction and
component responsibilities in this document are the approved boundaries.

## COMPONENT RESPONSIBILITIES

### AMHIPipelineService

Purpose: one reusable application service for the Fan intelligence pipeline.

Owns:

- artifact resolution request to `ArtifactRegistry`
- audio resolution request to `AudioStorage`
- Expert A execution
- Expert B anomaly gating
- Expert B same-audio characterization when gated in
- Structured Health Context v0.2 creation
- selected semantic RAG retrieval
- guarded Gemini explanation
- Gemini Maintenance Agent V2
- output validation
- stage timing
- final structured analysis result object

Does not own:

- HTTP request/response behavior
- database session management
- background worker claim/locking implementation
- dashboard rendering
- GitHub workflow or release logic
- training or indexing jobs

Scientific invariants:

- same machine
- same audio event
- Fan `id_00` only during this productionization goal
- Expert B runs only after Expert A flags the event
- Expert B keeps `k=30`, `distance=euclidean`, `rank_threshold=None`, and null
  direction fields
- selected Fan semantic retriever remains selected unless a future measured
  retrieval evaluation replaces it

### ArtifactRegistry

Purpose: explicit machine-aware artifact resolution.

For the active Fan scope, resolves:

- Expert A model path
- Expert A normalization artifact path
- Expert B reference index path
- embedding method metadata
- Expert B `k`, distance, and threshold policy
- Fan RAG corpus version
- selected retriever configuration
- semantic embedding index path

The registry must fail clearly for unsupported machines or unregistered
machine/SNR combinations. It must not silently reuse Fan artifacts for Pump,
Valve, Slide Rail, or MIMII DG.

### AudioStorage

Purpose: isolate the source of audio bytes from the scientific pipeline.

Initial implementation:

- `LocalAudioStorage`

Owns:

- accepting an audio reference from API/worker/CLI
- resolving it to a readable local processing path
- validating existence
- validating supported audio type
- returning storage metadata

Does not own:

- Expert A preprocessing
- copying the full MIMII dataset
- committing audio to Git
- cloud SDK behavior

Future adapter:

- `AzureBlobAudioStorage`, if staging later requires it

### EventRepository

Purpose: persist event lifecycle state.

Owns:

- event creation
- event lookup
- event list/filter queries
- status transition persistence
- safe error summary persistence

Minimum event states:

- `queued`
- `processing`
- `completed`
- `failed`

### AnalysisRepository

Purpose: persist analysis runs and final structured results.

Owns:

- creating an analysis run for a processing attempt
- storing pipeline version and artifact metadata
- storing Expert A result
- storing Expert B evidence when present
- storing Structured Health Context
- storing retrieval metadata
- storing explanation output
- storing maintenance output
- storing timing metadata
- retrieving final event result through the API/dashboard

Does not store:

- WAV bytes
- NumPy arrays
- model weights
- semantic embedding indexes
- full manuals or unbounded prompts

### EventProcessingService / Worker

Purpose: decouple ingestion from long-running Gemini and acoustic processing.

Owns:

- claiming queued events
- marking events processing
- invoking `AMHIPipelineService`
- storing analysis success or failure
- retry policy
- duplicate-processing protection
- graceful shutdown behavior

Does not own:

- scientific pipeline internals
- HTTP request processing
- dashboard rendering

### API layer

Purpose: versioned REST boundary for ingestion, state lookup, health, and
readiness.

Owns:

- `/api/v1` route definitions
- request validation
- response schemas
- mapping domain errors to bounded API errors
- returning `202 Accepted` for ingestion

Does not own:

- Expert A/B/RAG/Gemini orchestration
- direct artifact path selection
- database schema internals
- training or indexing

### Dashboard layer

Purpose: technician-facing display backed by API/application state.

Owns:

- event list view
- event detail view
- visible Fan-only scope
- visible fallback state
- visible failure state
- visible limitations and unsupported claims

Does not own:

- retraining
- rescoring
- Expert B recomputation
- Gemini calls during page rendering

### Observability layer

Purpose: correlated logs, metrics, health, and readiness.

Owns:

- structured event lifecycle logs
- `event_id` and `analysis_run_id` correlation
- application and pipeline metrics
- health endpoint implementation
- readiness dependency checks

Does not log:

- Gemini API keys
- raw secrets
- full raw audio
- entire maintenance manuals
- full private prompts by default
- unbounded result payloads

## DEPENDENCY DIRECTION

Approved dependency direction:

```text
src/api
  -> src/application
     -> src/models
     -> src/context
     -> src/rag
     -> src/agents
     -> src/infrastructure interfaces

src/infrastructure
  -> concrete storage, persistence, artifact path, logging, and metrics adapters

app/dashboard.py
  -> API or repository-backed read models
```

Rules:

- `src/models`, `src/context`, `src/rag`, and `src/agents` must not import
  FastAPI route modules.
- Scientific core modules must not own HTTP behavior.
- API routes must not duplicate Expert A/B/RAG/Gemini orchestration.
- Worker code must call `AMHIPipelineService`, not a script-specific copy of the
  Fan pipeline.
- CLI scripts may remain as thin wrappers over application services.
- Database code must sit behind repository interfaces.

## EVENT LIFECYCLE

Nominal lifecycle:

```text
POST /api/v1/events
-> validate Fan metadata and audio reference or upload
-> AudioStorage stores/resolves audio reference
-> EventRepository creates event(status=queued)
-> API returns 202 Accepted with event_id
-> worker claims queued event
-> EventRepository marks status=processing
-> AnalysisRepository creates analysis_run
-> AMHIPipelineService runs bounded Fan pipeline
-> AnalysisRepository stores result
-> EventRepository marks status=completed
-> API and dashboard can read event/result
```

Event identity requirements:

- `event_id` persists across API, worker, pipeline, context, result, logs, and
  dashboard
- `analysis_run_id` identifies a processing attempt
- audio identity is preserved from ingestion through Expert A and Expert B

## FAILURE LIFECYCLE

Failure lifecycle:

```text
queued
-> processing
-> failed
```

Failures must persist:

- safe error code
- safe error summary
- stage, where known
- retry count
- timestamp
- analysis run id, where applicable

Failure examples:

- unsupported machine type
- unknown machine id
- unregistered artifact scope
- missing audio file
- unsupported audio extension
- unreadable audio
- missing database dependency
- missing semantic RAG index
- Gemini configuration unavailable
- provider failure after bounded retry policy
- validation failure

Do not expose:

- internal traceback by default
- Gemini API key
- local absolute `D:\` path in public API responses
- raw prompt internals by default

## ARTIFACT RESOLUTION

Current script behavior uses path helpers and default functions:

- `cfg.MIMII_SNR_DIRS`
- `cfg.ad_paths_for`
- `_default_index`
- `default_embedding_index_path`
- `default_audio_path`

Target behavior:

- `ArtifactRegistry.resolve(machine_type, machine_id, snr_tag)` returns an
  explicit immutable artifact configuration
- Fan `id_00` `minus6dB` is the required registered real-intelligence path
- Fan `id_00` `0dB` and `plus6dB` may be represented only for verified Expert A
  artifacts; do not imply complete Real Intelligence indexes exist for them
- unsupported machines raise `ArtifactNotRegisteredError`
- unregistered SNRs raise `ArtifactNotRegisteredError`
- no secrets are stored in artifact configuration
- external development paths may point to `D:\PDM_Data\MIMII`
- future deployment must permit environment/config-based artifact locations

## STORAGE BOUNDARY

Current script behavior passes local paths directly into Expert A/B helpers.

Target behavior:

- API and worker handle user-facing audio references through `AudioStorage`
- `AMHIPipelineService` receives storage metadata and resolved processing path
- scientific code receives a readable local path only after storage validation
- raw datasets and generated scientific artifacts remain outside Git
- relational persistence stores audio references and metadata, not WAV bytes

Initial storage adapter:

- local filesystem references and bounded uploads mounted into a configured
  storage directory

Future storage adapter:

- Azure Blob or equivalent object storage, only when a staging target requires
  it

## PERSISTENCE BOUNDARY

Production-oriented persistence target:

- PostgreSQL

Local tests may use a lightweight test configuration where the repository
interface behavior remains equivalent.

Minimum persistent concepts:

- `events`
- `analysis_runs`
- `analysis_results`

`events` records:

- event id
- machine type
- machine id
- SNR tag
- audio reference
- status
- timestamps
- safe error code and summary

`analysis_runs` records:

- analysis run id
- event id
- pipeline version
- status
- started/completed timestamps
- total duration
- artifact metadata

`analysis_results` records:

- analysis run id
- Expert A result
- Expert B evidence
- Structured Health Context
- retrieval metadata
- explanation output
- maintenance output
- timing metadata

JSON/JSONB is acceptable for versioned scientific payloads where preserving the
contract matters more than relational column decomposition.

## ASYNC BOUNDARY

The API ingestion path must not wait for the full 20+ second intelligence path.

Approved baseline:

```text
POST /events
-> durable queued event
-> immediate 202
-> database-backed worker claims and processes
```

Do not add Kafka, Kubernetes, Event Hubs, Celery, or Redis merely for
appearance.

The first worker implementation should be the smallest reliable durable worker
that can be tested locally with the chosen persistence layer.

Worker design must define:

- claim/locking behavior
- duplicate processing protection
- retry policy and maximum retry count
- provider failure behavior
- deterministic fallback interaction
- safe failure persistence
- shutdown behavior

## API BOUNDARY

Base path:

```text
/api/v1
```

Required endpoints for the Fan Production MVP:

- `POST /api/v1/events`
- `GET /api/v1/events/{event_id}`
- `GET /api/v1/events`
- `GET /api/v1/machines/{machine_type}/{machine_id}/events`
- `GET /api/v1/health`
- `GET /api/v1/ready`

Ingestion mode decision for the first Fan Production MVP:

- prefer multipart upload plus explicit metadata if bounded implementation
  remains small
- allow registered/local audio reference only for development and tests

API responses must not expose:

- Gemini API key
- internal tracebacks
- raw prompt internals by default
- local `D:\` processing paths by default

Unsupported machines must return clear bounded API errors. Do not fake Pump,
Valve, Slide Rail, multi-machine, or MIMII DG support.

## DASHBOARD BOUNDARY

Current dashboard behavior:

- static renderer over external JSON artifacts

Target Fan Production MVP behavior:

- reads event list and event detail state through API/application data
- displays queued, processing, completed, and failed events
- shows Expert A evidence when available
- shows Expert B rank evidence when available
- shows Structured Health Context version
- shows Gemini provider/model/generation/fallback metadata
- shows RAG corpus, retriever, query, source ids, chunk ids, and snippets
- shows maintenance actions with citations
- shows limitations, timings, and failures

The dashboard must not:

- retrain
- re-score
- re-run Expert B
- call Gemini during page rendering
- hide safe-unavailable RAG or Gemini fallback modes

## OBSERVABILITY BOUNDARY

Structured logs must correlate:

- `event_id`
- `analysis_run_id`, where available

Required lifecycle events:

- `event_created`
- `event_queued`
- `event_processing_started`
- `artifact_resolution_completed`
- `expert_a_completed`
- `expert_b_skipped`
- `expert_b_completed`
- `context_completed`
- `retrieval_completed`
- `explanation_completed`
- `maintenance_completed`
- `pipeline_completed`
- `pipeline_failed`

Minimum metrics:

- `amhi_events_created_total`
- `amhi_events_completed_total`
- `amhi_events_failed_total`
- `amhi_anomalies_flagged_total`
- `amhi_pipeline_duration_seconds`
- `amhi_expert_a_duration_seconds`
- `amhi_expert_b_duration_seconds`
- `amhi_retrieval_duration_seconds`
- `amhi_explanation_duration_seconds`
- `amhi_maintenance_duration_seconds`
- `gemini_fallback_total`
- `maintenance_fallback_total`
- `citation_validation_failure_total`
- queue depth or queued event count when supported by the persistence layer

Health:

- process/application is alive

Readiness:

- database reachable
- Fan artifact registry can resolve the active reference configuration
- audio storage is initialized enough to accept work
- worker processing path is initialized
- Gemini configuration is present without live generation
- semantic RAG index/corpus are available

Readiness must not process audio or call live Gemini generation.

## OUT OF SCOPE

Out of scope for the Fan Production MVP productionization goal:

- Pump, Valve, Slide Rail, Cross-Machine comparison, and MIMII DG
- Expert B timbre-label research
- GitHub governance synchronization
- GitHub Project cleanup
- release-history cleanup
- retraining Expert A
- changing Expert A metrics
- changing Expert B semantics
- replacing selected semantic retrieval without a new measured retrieval
  evaluation
- Kubernetes, Kafka, Event Hubs, or cloud deployment by default
- ready-for-operation or enterprise-operation claims
- production maintenance validation
- physical root-cause diagnosis
- RUL or exact time-to-failure prediction

## FUTURE MULTI-MACHINE EXTENSION

PROJECT DECISION: the productionized architecture must stay machine-aware even
though this goal implements Fan only.

Future Pump, Valve, or Slide Rail work can register machine-specific artifacts
through `ArtifactRegistry` without rewriting the application architecture:

```text
ArtifactRegistry
  fan/id_00/minus6dB -> Fan Expert A, Fan Expert B index, Fan RAG config
  pump/id_00/...     -> future Pump Expert A, Pump Expert B index
  valve/id_00/...    -> future Valve Expert A, Valve Expert B index
  slide_rail/id_00/... -> future Slide Rail Expert A, Slide Rail Expert B index
```

This document does not approve implementing those future registrations now.

Future machine support requires:

- staged and verified machine data
- machine-specific Expert A baseline
- machine-specific Expert B reference index
- bounded same-machine same-audio smoke
- separate scientific review
- no universal-model or generalization claim until evaluated

## TASK-PROD-01 DEFINITION OF DONE

This task is complete when:

- the current script orchestration responsibilities are documented
- the target modular monolith architecture is documented
- required service boundaries are explicit
- dependency direction is explicit
- event, failure, artifact, storage, persistence, async, API, dashboard, and
  observability boundaries are explicit
- future multi-machine extension is described conceptually without implementing
  Pump, Valve, Slide Rail, Cross-Machine, or MIMII DG support
