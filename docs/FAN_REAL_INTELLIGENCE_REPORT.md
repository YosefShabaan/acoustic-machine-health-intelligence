# Fan Real Intelligence Report

Date: 2026-07-09

Scope: Real Intelligence Completion phase for the bounded MIMII Fan `id_00`
`minus6dB` MVP.

## What Was Implemented

The Fan MVP was upgraded from offline/fixture-era components to a real
Gemini-backed, approved-source, bounded-evaluated Fan intelligence pipeline:

```text
Fan audio event
-> Expert A anomaly detection
-> Expert B same-audio timbre characterization
-> Structured Health Context v0.2
-> selected semantic Fan maintenance RAG
-> live Gemini explanation
-> live Gemini grounded maintenance output
-> strict validation
-> bounded Fan system evaluation
-> static evidence dashboard
```

This remains a research MVP, not a production system.

## Gemini Provider And Model

- Provider: `gemini`.
- Text model: `gemini-2.5-flash`.
- Embedding model: `gemini-embedding-2`.
- Secret handling: `GEMINI_API_KEY` is read from the process environment and is
  never stored in repository configuration.
- Live explanation verified: yes.
- Live maintenance generation verified: yes.
- Raw WAV audio is not sent to Gemini; prompts use Structured Health Context and
  retrieved maintenance evidence.

## RAG Corpus

- Corpus version: `AMHI-FAN-MAINT-KB-v1`.
- Approved sources:
  - DOE Fan Sourcebook, 2003.
  - DOE/FEMP O&M Best Practices Release 3.0 fan maintenance material.
- Source provenance is tracked in `data/manuals/approved_sources.json` and
  `docs/RAG_SOURCE_REGISTER.md`.
- Section-aware chunks preserve source ID, title, publisher, version, corpus
  version, section ID, section heading, chunk ID, path, and source URL.

## Retriever Evaluation

Evaluation set:

- `AMHI-FAN-MAINT-RETRIEVAL-EVAL-v1`.
- 24 project-annotated Fan maintenance retrieval queries.

Results:

| Retriever | Hit@1 | Hit@3 | MRR | Failures |
|---|---:|---:|---:|---:|
| Lexical | 0.875000 | 0.958333 | 0.918056 | 1 |
| Semantic | 0.958333 | 1.000000 | 0.979167 | 0 |
| Hybrid | 0.916667 | 1.000000 | 0.958333 | 0 |

Selected retriever:

```text
semantic
```

The selection is bounded to the current Fan corpus and 24-query project
evaluation set. It is not a general production-superiority claim.

## Maintenance Agent V2

Maintenance Agent V2:

- Uses source-grounded retrieved chunks.
- Produces inspection-oriented maintenance actions.
- Requires each action to cite a retrieved `source_id` and `chunk_id`.
- Validates citation pairs.
- Rejects unsupported RUL, time-to-failure, confidence, probability, root-cause,
  diagnosis, and confirmed component-failure wording.
- Falls back deterministically if live Gemini output is malformed, unsafe, or
  uncited.

Live V2 smoke:

- Artifact: `D:\PDM_Data\MIMII\processed\grounded_maintenance_output_fan_id_00_minus6dB_task_maint_01.json`.
- Generation mode: `live_gemini`.
- Fallback used: `false`.
- Citation-valid inspection actions: 3.

## Structured Context Version

Structured Health Context:

- Current schema: `0.2.0`.
- Legacy schema `0.1.0` remains supported.
- v0.2 records:
  - `analysis_run_id`
  - `created_at`
  - `pipeline_version`
  - Expert A model and normalization artifact IDs
  - Expert B reference index ID, embedding model, `k`, and distance
  - LLM provider/model/prompt/generation metadata
  - RAG retriever/corpus/query metadata
  - Maintenance provider/model/prompt/generation metadata

## One-Event Real Smoke

Artifact:

```text
D:\PDM_Data\MIMII\processed\real_intelligence_end_to_end_fan_id_00_minus6dB_task_fan_13.json
```

Event:

```text
fan_id_00_minus6dB_00000002
```

Expert A:

- Score: `0.622095`.
- Threshold: `0.593284`.
- Is anomaly: `true`.

Expert B:

- `k=30`.
- Distance: `euclidean`.
- `rank_threshold=null`.
- Direction fields: null by design.
- Rank scores:
  - sharpness: `0.933333`
  - roughness: `0.933333`
  - boominess: `0.000000`
  - brightness: `0.933333`
  - depth: `0.666667`

Retrieved sources:

- `doe_fan_sourcebook_2003#DOE-FAN-2003-COMMON-FAN-PROBLEMS`
- `doe_fan_sourcebook_2003#DOE-FAN-2003-BASIC-MAINTENANCE`
- `doe_om_best_practices_release_3_fans#DOE-OM-R3-MAINTENANCE-PROGRAMS`

Generation:

- Gemini explanation: `live_gemini`, fallback `false`.
- Gemini maintenance: `live_gemini`, fallback `false`.
- Maintenance action count: 3.
- Citation failures: 0.
- Forbidden generated-claim hits: 0.
- Total runtime: `25.781358s`.

## Bounded Fan System Evaluation

Artifact:

```text
D:\PDM_Data\MIMII\processed\fan_system_evaluation_fan_id_00_minus6dB_task_fan_14.json
```

Selection:

- 10 normal events: first 10 lexicographic normal WAV files.
- 10 abnormal events: first 10 Expert A-flagged abnormal WAV files from
  lexicographic scan, excluding the `TASK-FAN-13` reference event.
- Abnormal candidates scanned: 59.

This is an integration stress set, not an Expert A recall estimate.

Results:

| Metric | Value |
|---|---:|
| Total events | 20 |
| Expert A flagged count | 10 |
| Expert B run count | 10 |
| Same-audio identity successes | 10 |
| Context validation successes | 10 |
| Retrieval available | 10 |
| Gemini explanation fallbacks | 0 |
| Maintenance fallbacks | 0 |
| Citation validation failures | 0 |
| Pipeline failures | 0 |
| Forbidden generated-claim failures | 0 |

Latency:

- Completed pipeline total mean: `23.444230s`.
- Completed pipeline total min: `18.117228s`.
- Completed pipeline total max: `31.403587s`.
- Total evaluation wall time: `242.509219s`.

## Dashboard

Artifact:

```text
D:\PDM_Data\MIMII\processed\dashboard_real_intelligence_fan_id_00_minus6dB_task_dash_02.html
```

Inspection result:

- HTML size: `14580` bytes.
- Required sections present.
- Displays event identity, Expert A/B evidence, context v0.2 traceability,
  Gemini provider/model/prompt metadata, semantic RAG corpus/query/source/chunk
  snippets, maintenance actions with citations, timing metadata, bounded
  evaluation summary, fallback fields, scientific limits, and limitations.
- Generated explanation/recommendation/limitations forbidden hits: 0.
- Retrieved source excerpts may contain component terms from approved source
  text; those are displayed as source evidence, not as generated diagnosis.

## Fallback Behavior

Observed live runs:

- TASK-MAINT-01 maintenance smoke fallback: `false`.
- TASK-FAN-13 explanation fallback: `false`.
- TASK-FAN-13 maintenance fallback: `false`.
- TASK-FAN-14 explanation fallback count: `0`.
- TASK-FAN-14 maintenance fallback count: `0`.

Fallback logic and dashboard visibility are covered by unit tests.

## Limitations

The current system still does not support:

- production readiness,
- production maintenance validation,
- confirmed physical root-cause diagnosis,
- fault probability,
- confidence percentage,
- severity percentage,
- RUL,
- exact time-to-failure,
- Expert B quantitative direction accuracy,
- Pump, Valve, Slide Rail, cross-machine, or MIMII DG generalization,
- exact reproduction of Nishida et al.

## Supported Claims

Supported:

- The bounded Fan `id_00` pipeline can run real Gemini explanation and
  source-grounded Gemini maintenance output over approved public Fan maintenance
  chunks.
- The selected semantic retriever is evidence-based for the current Fan corpus
  and project retrieval evaluation set.
- Structured Health Context v0.2 records provenance for the bounded pipeline.
- One same-audio Fan event completed the real Gemini + semantic RAG path with
  validated citation-grounded maintenance output.
- A bounded 20-event Fan integration stress set completed with 10 downstream
  continuations and zero observed fallback, citation, or pipeline failures.
- The static dashboard renders real Gemini/RAG provenance, bounded evaluation
  summary, timings, citations, and limitations.

## Unsupported Claims

Still not enabled:

- root-cause diagnosis,
- production maintenance recommendations,
- remaining useful life,
- fault probability or confidence,
- Expert B direction accuracy,
- multi-machine generalization,
- domain robustness,
- production deployment readiness.

## Commit Range

Real Intelligence Completion commits:

```text
171006d feat: add gemini provider preflight
2e638a9 feat: add live gemini explanation generator
bdface9 feat: add approved fan maintenance corpus
9eed9c6 feat: add section-aware rag chunking
d30e0ca feat: add gemini semantic rag retriever
fbf5545 feat: add fan rag retrieval evaluation set
92880cc feat: evaluate fan rag retrievers
3889d90 feat: add gemini grounded maintenance v2
861611d feat: add structured context v0.2 provenance
ac26395 feat: add real intelligence fan smoke
92c38f7 feat: evaluate bounded fan intelligence system
0918940 feat: update fan intelligence dashboard
```
