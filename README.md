# Acoustic Machine Health Intelligence

[![CI](https://github.com/YosefShabaan/acoustic-machine-health-intelligence/actions/workflows/ci.yml/badge.svg)](https://github.com/YosefShabaan/acoustic-machine-health-intelligence/actions/workflows/ci.yml)

Explainable acoustic condition monitoring for industrial machine audio.

The current bounded MVP uses MIMII Fan `id_00`. Expert A detects anomalous machine
audio with a normal-only reconstruction-error model. Expert B characterizes how
the same Expert A-flagged audio differs from same-machine normal references using
five timbre rank scores. The evidence is translated into a structured context,
explained cautiously, combined with source-preserving retrieval, and rendered in
a dashboard.

## Architecture

```text
machine audio event
-> Expert A anomaly detection
-> Expert B same-audio timbre characterization
-> Structured Health Context
-> guarded explanation
-> maintenance RAG
-> grounded technician output
-> dashboard
```

The core invariant is same machine, same audio event. Expert B characterizes the
audio event that Expert A evaluated; it is not an independent diagnosis system.

## Fan MVP Status

The Fan MVP is complete through `TASK-LAUNCH-06` for one bounded same-audio Fan
`id_00` path and is now a **deployed browser-based product MVP**.

Done:

- Expert A preprocessing, training, scoring, thresholding, and controlled SNR evaluation.
- Expert B bounded reference indexing, same-audio smoke, and qualitative evidence protocol.
- Structured Health Context schema and translator.
- Guardrailed explanation agent.
- Manifest-gated local maintenance retriever.
- Gemini-backed grounded maintenance agent with chunk-level citation guardrails and deterministic fallback.
- End-to-end Fan MVP orchestrator.
- Static dashboard MVP.
- Final Fan MVP evidence report and academic claims register.
- Real Gemini + selected semantic RAG end-to-end Fan smoke using Structured Health Context v0.2.
- Bounded 20-event Fan system integration evaluation.
- Updated static Fan intelligence evidence dashboard.
- Production API service with unified persistence (SQLite/Postgres).
- Modular background event processing worker.
- Click-only end-user dashboard with real-time UI refresh.
- Authenticated browser session management and security hardening.
- Containerized deployment architecture (Docker Compose, GCE ready).

Current remaining work:

- Multi-machine Pump generalization remains blocked because
  `D:\PDM_Data\MIMII\pump\id_00` is not staged.

## Verified Results

Expert A controlled SNR evaluation for Fan `id_00`:

| SNR | AUC | Threshold | Recall | FPR | Specificity |
|---|---:|---:|---:|---:|---:|
| `minus6dB` | 0.6142 | 0.593284 | 0.14 | 0.135 | 0.865 |
| `0dB` | 0.8306 | 0.680019 | 0.52 | 0.130 | 0.870 |
| `plus6dB` | 0.9980 | 1.133451 | 1.00 | 0.050 | 0.950 |

The controlled result strongly indicates low SNR as the primary limitation of
the weak `minus6dB` separation. It does not prove the model is perfect, and it
does not prove the same performance for other machines.

Bounded Fan MVP evidence:

- Expert B reference index: 40 normal references, default `k=30`.
- Same abnormal event: `fan_id_00_minus6dB_00000002`.
- Expert A event score: `0.622095`; threshold: `0.593284`; anomalous: `true`.
- Expert B rank scores: boominess `0.000000`, brightness `0.933333`, depth `0.666667`, roughness `0.933333`, sharpness `0.933333`.
- End-to-end smoke runtime: `15.792862s`.
- Dashboard artifact size: `7561` bytes.

Real intelligence Fan smoke (`TASK-FAN-13`):

- Same abnormal event: `fan_id_00_minus6dB_00000002`.
- Structured Health Context schema: `0.2.0`.
- Selected retriever: semantic over `AMHI-FAN-MAINT-KB-v1`.
- Retrieved chunks: DOE Fan Sourcebook common fan problems, DOE Fan Sourcebook basic maintenance, and DOE O&M Best Practices maintenance programs.
- Gemini explanation: `live_gemini`, fallback `false`.
- Gemini grounded maintenance: `live_gemini`, fallback `false`, 3 citation-valid inspection actions.
- Total runtime: `25.781358s`.
- Forbidden claim hits: `[]`.
- TASK-10 comparison is historical only; changed free text is not scientific improvement evidence.

Bounded Fan system evaluation (`TASK-FAN-14`):

- Event set: 10 normal Fan events + 10 Expert A-flagged abnormal Fan events.
- Expert B executions: 10.
- Same-audio identity successes: 10.
- Context validation successes: 10.
- Retrieval available: 10.
- Gemini explanation fallbacks: 0.
- Maintenance fallbacks: 0.
- Citation validation failures: 0.
- Pipeline failures: 0.
- Total wall time: `242.509219s`.

Updated dashboard (`TASK-DASH-02`):

- Artifact: `D:\PDM_Data\MIMII\processed\dashboard_real_intelligence_fan_id_00_minus6dB_task_dash_02.html`.
- HTML size: `14580` bytes.
- Displays event identity, Expert A/B evidence, Structured Health Context v0.2 provenance, Gemini provider/model/prompt metadata, semantic RAG corpus/query/source/chunk snippets, maintenance actions with citations, timing, bounded evaluation summary, and limitations.

## Workflow

Use the task plan and project state as the execution source of truth:

- `docs/MASTER_EXECUTION_PLAN.md`
- `docs/TASK_EXECUTION_LOG.md`
- `project_state.json`
- `docs/fan_mvp_final_report.md`
- `docs/FAN_REAL_INTELLIGENCE_REPORT.md`
- `docs/academic_claims.md`

Large scientific data and generated model artifacts live outside Git under:

```text
D:\PDM_Data\MIMII
```

Do not commit WAV files, generated `.npy/.npz` arrays, model weights, reference
indexes, smoke outputs, benchmark outputs, or other generated scientific artifacts.

## Quick Start

These commands are safe for repository validation. They do not train models,
build reference indexes, or process the full dataset.

```powershell
python -m pip install -r requirements.txt
python -m unittest discover -s tests -p "test_*.py"
python -m compileall -q src scripts tests app
```

Do not run training, SNR experiments, Expert B indexing, or end-to-end data
scripts as quick-start commands. Those workflows require external artifacts and
the bounded runtime ladder documented in the execution plan.

## Tests

The local unit suite currently covers:

- Expert B rank, filtering, null-direction, and JSON guardrails.
- Structured Health Context v0.2 schema validation and legacy migration.
- Guardrailed explanation output.
- RAG source preservation and citation validation.
- RAG retrieval evaluation metrics and hybrid fusion behavior.
- Gemini-backed grounded maintenance output.
- End-to-end Fan MVP orchestration behavior.
- Static dashboard rendering.

Current local evidence:

```text
python -m unittest discover -s tests -p "test_*.py"
Ran 76 tests
OK
```

GitHub Actions `CI` runs:

- `compile`
- `unit tests`
- `large-artifact guard`

## Scientific Limits

Supported:

- Expert A detects anomalous Fan `id_00` sounds under the evaluated split.
- Expert A performance is SNR-sensitive in the controlled Fan experiment.
- A bounded Expert B Fan reference index exists.
- Expert B can qualitatively characterize one Expert A-flagged Fan event using same-machine normal references.
- Structured context, guarded explanation, retrieval, maintenance output, end-to-end orchestration, and dashboard artifacts exist for the bounded Fan MVP.
- A bounded Fan maintenance retrieval evaluation selected semantic retrieval for the next Fan MVP maintenance-grounding task.
- A bounded live Gemini maintenance-agent smoke produced citation-valid inspection actions over approved Fan maintenance chunks.
- Structured Health Context v0.2 records provenance for Expert A, Expert B, LLM, RAG, and Maintenance Agent outputs.
- One bounded real Gemini + semantic RAG Fan smoke completed with live Gemini explanation and live Gemini grounded maintenance output.
- One bounded 20-event Fan system integration evaluation completed with 10 downstream continuations and no observed fallback, citation, or pipeline failures.
- The static dashboard now renders real Gemini/RAG provenance, bounded evaluation summary, timings, and limitations.
- AMHI provides a deployed browser-based Fan MVP that executes the verified multi-expert acoustic intelligence workflow and presents grounded AI-assisted maintenance evidence to an authenticated end user.

Not supported:

- Expert B timbre-direction accuracy.
- Physical root-cause diagnosis.
- Rank score as confidence, probability, or severity percentage.
- Remaining Useful Life or exact time-to-failure prediction.
- Evaluated production maintenance recommendations.
- Pump, Valve, Slide Rail, or MIMII DG generalization.
- Exact reproduction of Nishida et al.

## Roadmap

Backlog and blocked work:

- Pump data staging.
- Pump Expert A evaluation.
- Pump Expert B reference indexing and smoke.
- Valve generalization.
- Slide Rail generalization.
- Cross-machine comparison.
- MIMII DG robustness.
- Expert B label or threshold protocol for stronger timbre-direction claims.
