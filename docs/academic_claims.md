# Academic Claims Register

Date: 2026-07-09

Scope: claims supported by the current repository after `TASK-DASH-02`.

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
| Structured Health Context schema version `0.2.0` exists with traceability metadata and v0.1 migration support. | VERIFIED REPOSITORY FACT | external TASK-CTX-02 artifact, `tests/test_context_schema.py` |
| Guardrailed explanation output exists for the Fan event. | VERIFIED REPOSITORY FACT | TASK-07 JSON, `tests/test_llm_guardrails.py` |
| Approved public Fan maintenance corpus `AMHI-FAN-MAINT-KB-v1` exists with two DOE-source entries. | VERIFIED REPOSITORY FACT | `data/manuals/approved_sources.json`, `docs/RAG_SOURCE_REGISTER.md` |
| The current approved Fan corpus loads into the local RAG knowledge base and returns retrieved source chunks in a bounded smoke. | VERIFIED REPOSITORY FACT | `tests/test_rag_grounding.py`, TASK-RAG-01 smoke |
| A Gemini semantic retrieval baseline exists with an external 15-chunk embedding artifact. | VERIFIED REPOSITORY FACT | `docs/RAG_SEMANTIC_RETRIEVER_BASELINE.md`, external TASK-RAG-03 artifact |
| A 24-query Fan maintenance retrieval evaluation set exists as a project annotation artifact. | VERIFIED REPOSITORY FACT | `data/manuals/fan_maintenance_retrieval_eval_v1.json`, `docs/RAG_RETRIEVAL_EVALUATION_SET.md` |
| The bounded retrieval comparison produced lexical Hit@3 0.958333, semantic Hit@3 1.000000, and hybrid Hit@3 1.000000 on the 24-query project evaluation set. | VERIFIED REPOSITORY FACT | `docs/RAG_RETRIEVAL_EVALUATION.md`, external TASK-RAG-05 artifact |
| Grounded maintenance output exists using an approved fixture source. | VERIFIED REPOSITORY FACT | TASK-09 JSON |
| A live Gemini Maintenance Agent V2 smoke produced three citation-valid inspection actions over retrieved approved Fan corpus chunks with fallback_used=false. | VERIFIED REPOSITORY FACT | external TASK-MAINT-01 artifact, `tests/test_maintenance_agent.py` |
| One end-to-end Fan MVP JSON exists. | VERIFIED REPOSITORY FACT | TASK-10 JSON |
| TASK-FAN-13 ran one bounded Fan `id_00` same-audio event through Expert A, Expert B, Structured Health Context v0.2, selected semantic RAG, live Gemini explanation, and live Gemini grounded maintenance output. | VERIFIED REPOSITORY FACT | external TASK-FAN-13 artifact, `tests/test_real_intelligence_fan_smoke.py` |
| TASK-FAN-13 produced three citation-valid inspection actions over retrieved DOE Fan maintenance chunks with explanation fallback_used=false and maintenance fallback_used=false. | VERIFIED REPOSITORY FACT | external TASK-FAN-13 artifact |
| TASK-FAN-14 evaluated 20 bounded Fan events: 10 normal events and 10 Expert A-flagged abnormal events selected as an integration stress set. | VERIFIED REPOSITORY FACT | `docs/FAN_SYSTEM_EVALUATION.md`, external TASK-FAN-14 artifact |
| TASK-FAN-14 completed 10 downstream Expert B/context/RAG/Gemini/maintenance continuations with zero observed pipeline failures, zero Gemini explanation fallbacks, zero maintenance fallbacks, and zero citation validation failures. | VERIFIED REPOSITORY FACT | `docs/FAN_SYSTEM_EVALUATION.md`, external TASK-FAN-14 artifact |
| One historical static dashboard HTML artifact exists for the TASK-10 fixture-era MVP. | VERIFIED REPOSITORY FACT | TASK-11 HTML |
| TASK-DASH-02 rendered an updated static Fan intelligence dashboard over the real Gemini/RAG smoke and bounded Fan system evaluation artifacts. | VERIFIED REPOSITORY FACT | external TASK-DASH-02 HTML artifact, `tests/test_dashboard.py` |
| The Real Intelligence Completion report exists and summarizes provider, corpus, retrieval, maintenance, context, smoke, evaluation, dashboard, latency, and claim limits. | VERIFIED REPOSITORY FACT | `docs/FAN_REAL_INTELLIGENCE_REPORT.md` |

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
| Semantic retrieval is selected for the bounded Fan MVP RAG path. | PROJECT DECISION | TASK-RAG-05 selected semantic by Hit@3, MRR, and Hit@1 on `AMHI-FAN-MAINT-RETRIEVAL-EVAL-v1` |
| Maintenance Agent V2 outputs must remain inspection-oriented and cite retrieved source_id/chunk_id pairs. | PROJECT DECISION | TASK-MAINT-01 validation and tests |
| Structured Health Context v0.2 uses artifact identifiers rather than invented model versions when formal versions are unavailable. | PROJECT DECISION | TASK-CTX-02 translator and schema tests |

## Cautious Inferences

| Statement | Classification | Evidence | Required wording |
|---|---|---|---|
| Low SNR is the primary observed limitation of weak `minus6dB` Expert A separation. | INFERENCE | Controlled SNR-only comparison, AUC improves 0.6142 -> 0.8306 -> 0.9980 | "strongly indicated as the primary limitation" |
| The bounded Fan MVP integration works for the evaluated Fan stress set. | INFERENCE | TASK-FAN-14 20-event integration artifact | "bounded Fan integration evidence, not diagnostic accuracy" |
| The bounded Fan MVP integration works for one same-audio abnormal event. | INFERENCE | TASK-10 JSON, TASK-11 dashboard artifact, and TASK-FAN-13 real Gemini/RAG smoke | "one bounded Fan MVP path" |
| Expert B rank scores can guide qualitative listening/inspection focus. | INFERENCE | TASK-04 rank scores and qualitative protocol | "relative rank among selected normal references" |

## Unsupported Or Forbidden Claims

| Claim | Status | Why not supported |
|---|---|---|
| Expert B accurately predicts timbre direction. | UNSUPPORTED | no five-attribute timbre-difference labels for current Fan data |
| Expert B diagnoses the physical root cause. | FORBIDDEN | no diagnosis labels/model; architecture only characterizes acoustic difference |
| Expert B rank score is confidence or failure probability. | FORBIDDEN | rank score is a local relative rank, not calibrated probability |
| The system predicts remaining useful life. | OUT OF SCOPE | RUL/PRONOSTIA removed from active architecture |
| The system predicts exact time to failure. | OUT OF SCOPE | no run-to-failure target in active MIMII runtime |
| Maintenance recommendations are evaluated production guidance. | UNSUPPORTED | one bounded live smoke exists, but bounded multi-event evaluation and production validation are not complete |
| Semantic retrieval is production-superior or generally superior across corpora. | UNSUPPORTED | selection is bounded to the 24-query project evaluation set and current Fan corpus |
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
An approved public Fan maintenance corpus exists. On a bounded 24-query project
retrieval evaluation set, semantic retrieval achieved Hit@3 1.000000 and was
selected as the Fan MVP retriever. A live Gemini maintenance-agent smoke
produced three citation-valid inspection-oriented actions over retrieved
approved Fan corpus chunks. TASK-FAN-13 then ran one bounded same-audio Fan
event through the live Gemini explanation and live Gemini grounded maintenance
path with the selected semantic retriever and no fallback. Structured Health
Context v0.2 records the actual model, reference index, retriever, corpus, LLM,
and maintenance-agent metadata used for the bounded trace. TASK-FAN-14 adds a
bounded 20-event Fan integration evaluation with 10 downstream continuations,
zero observed Gemini fallbacks, zero maintenance fallbacks, zero citation
validation failures, and zero pipeline failures.
TASK-DASH-02 renders the real Gemini/RAG provenance, maintenance citations,
bounded evaluation summary, timing metadata, and limitations in a static evidence
dashboard.
AMHI provides a deployed browser-based Fan MVP that executes the verified
multi-expert acoustic intelligence workflow and presents grounded AI-assisted
maintenance evidence to an authenticated end user.
```

Must include limitation:

```text
The current Fan MVP does not validate Expert B timbre-direction accuracy, does
not diagnose physical root cause, does not predict remaining useful life, and
does not yet provide evaluated production maintenance recommendations.
```

## Next Required Evidence Before Stronger Claims

| Stronger future claim | Required evidence |
|---|---|
| Expert B direction accuracy | five-attribute timbre labels or approved equivalent protocol |
| Evaluated maintenance recommendations | bounded multi-event system evaluation plus production/maintenance review |
| Pump/Valve/Slide Rail generalization | staged data, machine-specific artifacts, bounded per-machine evaluation |
| Domain robustness | MIMII DG data/assets and approved protocol |
| Production readiness | broader validation, operations requirements, monitoring, and reviewed maintenance content |
