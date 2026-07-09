# Fan Event Processing Worker

Status: `TASK-PROD-08_IMPLEMENTED`

Scope: Fan `id_00` / `minus6dB` Fan Production MVP event lifecycle.

## Purpose

The API ingestion path returns `202 Accepted` after persisting a queued event.
The worker boundary processes queued events outside the HTTP request path:

```text
queued
-> processing
-> AMHIPipelineService
-> completed
```

or:

```text
queued
-> processing
-> failed
```

## Architecture

Implemented component:

- `src/application/event_processing.py`

Core class:

- `EventProcessingService`

Injected dependencies:

- `EventRepository`
- `AnalysisRepository`
- pipeline service implementing `process_event(...)`

The worker does not import FastAPI routes and the API routes do not implement
Expert A, Expert B, RAG, Gemini, or maintenance orchestration.

## Claim And Locking Behavior

The SQLite local/test adapter implements:

```text
claim_next_queued()
```

The claim operation uses `BEGIN IMMEDIATE`, selects the oldest queued event,
and updates it to `processing` before returning it to the worker. This is the
bounded local equivalent of a database-backed polling claim.

Future PostgreSQL implementation should use a row-locking claim such as
`FOR UPDATE SKIP LOCKED` or an equivalent transactional claim pattern.

## Duplicate Processing Protection

Only events with status `queued` can be claimed.

After an event is claimed, its status becomes `processing`, so a second worker
poll does not receive the same event.

This is bounded duplicate protection for the current local worker. It is not a
distributed worker fleet design.

## Retry Policy

Current retry policy:

- `max_retries = 0`
- no automatic retry loop

Failure is persisted as `failed` with a safe error code and summary. A future
retry phase can add attempt counters and explicit retry scheduling if evidence
shows it is needed.

## Provider Failure And Fallback Behavior

The worker treats the injected pipeline service as the authority for internal
Gemini/RAG fallback behavior.

If the pipeline returns a completed payload with fallback metadata, the worker
persists that payload as completed evidence.

If the pipeline raises an exception, the worker:

- marks the analysis run `failed`
- marks the event `failed`
- stores only a safe error code and bounded summary
- does not store tracebacks or secrets

## Shutdown Behavior

`process_next_event()` processes at most one event.

`process_available(max_events=N)` processes a bounded number of currently
queued events and then returns. There is no infinite loop in this task.

A later service runner can wrap this bounded worker in a polling loop with
signal-aware shutdown.

## Timing Metadata

The worker result records:

- queue delay seconds, when event timestamps are parseable
- processing duration seconds
- total event duration seconds, when event timestamps are parseable

This is application lifecycle timing, not scientific model performance.

## Scientific Guardrails

The worker does not change:

- Expert A architecture or metrics
- Expert B `k=30`
- Expert B `distance=euclidean`
- Expert B `rank_threshold=None`
- selected semantic Fan retriever
- Structured Health Context v0.2 semantics

The worker does not enable:

- remaining useful life
- time to failure
- confirmed physical root cause
- confidence or probability claims
- production maintenance validation
- multi-machine generalization
- domain robustness
