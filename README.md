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

The Fan MVP is complete through `TASK-12` for one bounded same-audio Fan `id_00`
path.

Done:

- Expert A preprocessing, training, scoring, thresholding, and controlled SNR evaluation.
- Expert B bounded reference indexing, same-audio smoke, and qualitative evidence protocol.
- Structured Health Context schema and translator.
- Guardrailed explanation agent.
- Manifest-gated local maintenance retriever.
- Grounded maintenance agent with citation guardrails.
- End-to-end Fan MVP orchestrator.
- Static dashboard MVP.
- Final Fan MVP evidence report and academic claims register.

Current blocker:

- `TASK-13` Pump generalization is blocked because `D:\PDM_Data\MIMII\pump\id_00`
  is not staged.

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

## Workflow

Use the task plan and project state as the execution source of truth:

- `docs/MASTER_EXECUTION_PLAN.md`
- `docs/TASK_EXECUTION_LOG.md`
- `project_state.json`
- `docs/fan_mvp_final_report.md`
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
- Structured Health Context schema validation.
- Guardrailed explanation output.
- RAG source preservation and citation validation.
- Grounded maintenance output.
- End-to-end Fan MVP orchestration behavior.
- Static dashboard rendering.

Current local evidence:

```text
python -m unittest discover -s tests -p "test_*.py"
Ran 32 tests
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

Not supported:

- Expert B timbre-direction accuracy.
- Physical root-cause diagnosis.
- Rank score as confidence, probability, or severity percentage.
- Remaining Useful Life or exact time-to-failure prediction.
- Production-manual-grounded maintenance recommendations.
- Pump, Valve, Slide Rail, or MIMII DG generalization.
- Exact reproduction of Nishida et al.

## Roadmap

Backlog and blocked work:

- Production maintenance documents and `approved_sources.json`.
- Pump data staging.
- Pump Expert A evaluation.
- Pump Expert B reference indexing and smoke.
- Valve generalization.
- Slide Rail generalization.
- Cross-machine comparison.
- MIMII DG robustness.
- Expert B label or threshold protocol for stronger timbre-direction claims.
