# Academic Claims Register

Date: 2026-07-08

Scope: claims supported by the current repository after `TASK-12`.

## Claim Classification Rules

- `PAPER FACT`: stated by a cited paper or official method source.
- `VERIFIED REPOSITORY FACT`: verified from repository code, tests, docs, or produced artifacts.
- `PROJECT DECISION`: an explicit design choice made by this project.
- `INFERENCE`: a cautious interpretation from verified results.
- `UNKNOWN`: not established by current data or artifacts.

## Paper Facts

| Statement | Classification | Source |
|---|---|---|
| MIMII provides industrial machine audio for normal and anomalous conditions. | PAPER FACT | Purohit et al., MIMII, 2019 |
| MIMII includes machine categories including fan, pump, valve, and slide rail. | PAPER FACT | Purohit et al., MIMII, 2019 |
| Nishida et al. frame timbre-difference characterization around sharpness, roughness, boominess, brightness, and depth. | PAPER FACT | Nishida et al., 2024 |
| Nishida et al. use local normal-reference comparison and `k=30` in experiments. | PAPER FACT | Nishida et al., 2024 |
| Direction labels require a threshold policy. | PAPER FACT | Nishida et al., 2024 method framing |

## Repository Facts

| Statement | Classification | Evidence |
|---|---|---|
| Fan `id_00` data are staged for `minus6dB`, `0dB`, and `plus6dB`. | VERIFIED REPOSITORY FACT | `project_state.json`, `D:\PDM_Data\MIMII` artifact inspection |
| Each staged Fan SNR variant has 1011 normal and 407 abnormal WAV files. | VERIFIED REPOSITORY FACT | `project_state.json`, `REPORT.md` |
| Expert A SNR AUC values are 0.6142, 0.8306, and 0.9980 for `minus6dB`, `0dB`, and `plus6dB`. | VERIFIED REPOSITORY FACT | `D:\PDM_Data\MIMII\processed\snr_ad_summary.json` |
| The Expert B bounded Fan reference index contains 40 normal references and supports `k=30`. | VERIFIED REPOSITORY FACT | `docs/TASK_03_REFERENCE_INDEX_VALIDATION.md` |
| TASK-04 characterized abnormal file `00000002.wav` after Expert A flagged it. | VERIFIED REPOSITORY FACT | `docs/TASK_04_SAME_AUDIO_SMOKE.md`, TASK-04 JSON |
| TASK-04 Expert B rank scores are boominess 0.000000, brightness 0.933333, depth 0.666667, roughness 0.933333, and sharpness 0.933333. | VERIFIED REPOSITORY FACT | TASK-04 JSON |
| Structured Health Context schema version `0.1.0` exists and was instantiated for the Fan event. | VERIFIED REPOSITORY FACT | TASK-06 JSON, `src/context` tests |
| Guardrailed explanation output exists for the Fan event. | VERIFIED REPOSITORY FACT | TASK-07 JSON, `tests/test_llm_guardrails.py` |
| Production maintenance retrieval is unavailable because no approved production source manifest exists. | VERIFIED REPOSITORY FACT | TASK-08 JSON |
| Grounded maintenance output exists using an approved fixture source. | VERIFIED REPOSITORY FACT | TASK-09 JSON |
| One end-to-end Fan MVP JSON exists. | VERIFIED REPOSITORY FACT | TASK-10 JSON |
| One static dashboard HTML artifact exists. | VERIFIED REPOSITORY FACT | TASK-11 HTML |

## Project Decisions

| Statement | Classification | Rationale |
|---|---|---|
| The active architecture is sequential: Expert A detects, Expert B characterizes, context/LLM/RAG/dashboard communicate evidence. | PROJECT DECISION | `CLAUDE.md`, `docs/MASTER_EXECUTION_PLAN.md` |
| Fan `id_00` is the reference MVP. | PROJECT DECISION | `CLAUDE.md`, `project_state.json` |
| RUL and PRONOSTIA are outside active runtime scope. | PROJECT DECISION | `CLAUDE.md`, `REPORT.md` |
| Expert B uses Expert A bottleneck embeddings as the current MVP adapter. | PROJECT DECISION | TASK-04 JSON |
| Expert B uses Euclidean distance as the current MVP distance metric. | PROJECT DECISION | TASK-04 JSON |
| `rank_threshold=None` is used until a threshold policy is approved. | PROJECT DECISION | TASK-04 JSON, qualitative protocol |
| Production maintenance recommendations require approved retrieved source evidence. | PROJECT DECISION | RAG and maintenance-agent guardrail tests |

## Cautious Inferences

| Statement | Classification | Evidence | Required wording |
|---|---|---|---|
| Low SNR is the primary observed limitation of weak `minus6dB` Expert A separation. | INFERENCE | Controlled SNR-only comparison, AUC improves 0.6142 -> 0.8306 -> 0.9980 | "strongly indicated as the primary limitation" |
| The bounded Fan MVP integration works for one same-audio abnormal event. | INFERENCE | TASK-10 JSON and TASK-11 dashboard artifact | "one bounded Fan MVP path" |
| Expert B rank scores can guide qualitative listening/inspection focus. | INFERENCE | TASK-04 rank scores and qualitative protocol | "relative rank among selected normal references" |

## Unsupported Or Forbidden Claims

| Claim | Status | Why not supported |
|---|---|---|
| Expert B accurately predicts timbre direction. | UNSUPPORTED | no five-attribute timbre-difference labels for current Fan data |
| Expert B diagnoses the physical root cause. | FORBIDDEN | no diagnosis labels/model; architecture only characterizes acoustic difference |
| Expert B rank score is confidence or failure probability. | FORBIDDEN | rank score is a local relative rank, not calibrated probability |
| The system predicts remaining useful life. | OUT OF SCOPE | RUL/PRONOSTIA removed from active architecture |
| The system predicts exact time to failure. | OUT OF SCOPE | no run-to-failure target in active MIMII runtime |
| Maintenance recommendations are production-grounded. | UNSUPPORTED | production approved-source manifest is absent |
| The architecture generalizes to Pump, Valve, or Slide Rail. | UNSUPPORTED | those machine datasets are not staged/evaluated |
| The system is robust to domain shift. | UNSUPPORTED | MIMII DG phase not executed |
| The current Expert B exactly reproduces Nishida et al. | UNSUPPORTED | MVP uses Expert A bottleneck adapter and lacks paper-equivalent labels/assets |

## Presentation-Ready Claim Set

Allowed:

```text
We implement a sequential acoustic health-monitoring MVP on MIMII Fan id_00.
Expert A detects anomalous sound using a normal-only reconstruction-error model.
In a controlled SNR experiment, Expert A AUC improved from 0.6142 at -6 dB to
0.8306 at 0 dB and 0.9980 at +6 dB, strongly indicating low SNR as the primary
limitation of the weak -6 dB result.
For one Expert A-flagged Fan event, Expert B compares the same audio with
same-machine normal references and reports five qualitative timbre rank scores.
Those outputs are translated into structured evidence, explained cautiously,
combined with source-preserving retrieval, and rendered in a static dashboard.
```

Must include limitation:

```text
The current Fan MVP does not validate Expert B timbre-direction accuracy, does
not diagnose physical root cause, does not predict remaining useful life, and
does not yet provide production-manual-grounded maintenance recommendations.
```

## Next Required Evidence Before Stronger Claims

| Stronger future claim | Required evidence |
|---|---|
| Expert B direction accuracy | five-attribute timbre labels or approved equivalent protocol |
| Production-grounded maintenance recommendations | approved production source manifest and documents |
| Pump/Valve/Slide Rail generalization | staged data, machine-specific artifacts, bounded per-machine evaluation |
| Domain robustness | MIMII DG data/assets and approved protocol |
| Production readiness | broader validation, operations requirements, monitoring, and reviewed maintenance content |
