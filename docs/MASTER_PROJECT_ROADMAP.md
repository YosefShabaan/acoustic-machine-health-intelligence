# Master Project Roadmap

Repository: `D:\IOT`

Created for the current active architecture in `CLAUDE.md`.

This roadmap is repository-ground-truth driven. It does not mark a component
complete because it is described in documentation. Completion requires code,
artifact, test, or measured run evidence.

## Authority Order

1. `CLAUDE.md`
2. `project_state.json`
3. `docs/MASTER_PROJECT_ROADMAP.md`
4. `docs/EXPERT_B_NISHIDA_METHOD_SPEC.md`
5. `REPORT_PHASE1_2.md`
6. `REPORT.md`
7. `CLAUDE_LEGACY_RUL.md`, if later restored, for legacy history only

RUL and PRONOSTIA are outside the active runtime architecture.

## Baseline Verdict

STATE:

- Active project: acoustic machine condition monitoring.
- Reference MVP: MIMII `fan / id_00`.
- Active runtime architecture: same machine, same audio event, Expert A detects, Expert B characterizes acoustic/timbre difference, structured context, RAG, LLM, dashboard.
- Verified Expert A/SNR work exists.
- Expert B implementation exists in code but is not verified end-to-end because the reference-index job became pathologically slow and was stopped.

FACTS:

- VERIFIED REPOSITORY FACT: `src/models/anomaly_detector.py` implements the Conv1D autoencoder Expert A.
- VERIFIED REPOSITORY FACT: `D:\PDM_Data\MIMII\processed\snr_ad_summary.json` contains AUC results: minus6dB `0.6142`, 0dB `0.8306`, plus6dB `0.9980`.
- VERIFIED REPOSITORY FACT: `src/models/timbre_difference.py`, `src/utils/audio_reference_index.py`, `scripts/build_timbre_reference_index.py`, `scripts/run_expert_b_smoke.py`, and `tests/test_timbre_difference.py` exist.
- VERIFIED REPOSITORY FACT: no `CLAUDE_LEGACY_RUL.md` exists in the repository.
- VERIFIED REPOSITORY FACT: `CLAUDE.md` begins with stale text from the prior skill-installation task before the real `# CLAUDE.md` content.
- VERIFIED REPOSITORY FACT: `DIOTCLAUDE.md` exists and appears to be an alternate active-context draft with an invalid-looking filename.
- VERIFIED REPOSITORY FACT: repo-local `data/raw` contains MIMII fan WAV files, while `src/config.py` now points active generated artifacts to `D:\PDM_Data\MIMII`.
- VERIFIED REPOSITORY FACT: all repository files are currently untracked from Git's point of view.

GAPS:

- UNKNOWN: the intended archival source for `CLAUDE_LEGACY_RUL.md` is missing.
- UNKNOWN: whether `DIOTCLAUDE.md` should be archived, deleted, or renamed; no deletion is done in this planning task.
- PROJECT DECISION: do not treat legacy RUL/PRONOSTIA config constants as active runtime architecture.
- PROJECT DECISION: do not resume Expert B smoke or the 40-file reference-index job until performance forensics is complete.

DECISION:

- Phase 0 records the source-of-truth baseline and maps cleanup needs. It does not perform source cleanup in this planning task.
- The next executable technical phase is Phase 1, routed to `$performance-forensics`, because the known blocker prevents trustworthy Expert B integration.

STOP CONDITION:

- This roadmap and `project_state.json` exist and validate.
- `AGENTS.md` tells future Codex runs how to continue one bounded phase.
- No project source code, model artifacts, SNR behavior, or dataset contents are modified.

## Repository Ground Truth

### Important Files And Modules

| PATH | STATUS | PURPOSE | KEEP / MODIFY / DEPRECATE | NOTES |
|---|---|---|---|---|
| `CLAUDE.md` | ACTIVE_BUT_UNVERIFIED | Active project source of truth | MODIFY | Content is authoritative, but first lines contain stale prior task text that should be cleaned in a documentation-only cleanup. |
| `AGENTS.md` | ACTIVE_BUT_UNVERIFIED | Codex routing and guardrails | MODIFY | Updated by this task for continuation policy. |
| `CLAUDE_LEGACY_RUL.md` | MISSING | Expected legacy archive | CREATE_OR_RESTORE_LATER | Mandatory by request, but not present. Do not invent content. |
| `DIOTCLAUDE.md` | OBSOLETE | Alternate context draft / malformed filename | DEPRECATE_LATER | Appears to duplicate active context ideas; do not use over `CLAUDE.md`. |
| `REPORT_PHASE1_2.md` | DOCUMENTATION_ONLY | Verified Expert A and SNR report | KEEP | Contains verified SNR AUC table and artifact descriptions. Some RUL wording is historical. |
| `REPORT.md` | DOCUMENTATION_ONLY | Historical phase report | KEEP | Contains obsolete PRONOSTIA/RUL plan; use only as history. |
| `docs/EXPERT_B_NISHIDA_METHOD_SPEC.md` | DOCUMENTATION_ONLY | Paper-forensics spec for Expert B | KEEP | Governs Expert B adaptation and scientific limits. |
| `requirements.txt` | ACTIVE_BUT_UNVERIFIED | Python dependencies | MODIFY_LATER | Contains `timbral_models`; comments still mention PRONOSTIA/RUL. |
| `src/config.py` | ACTIVE_BUT_UNVERIFIED | Global paths and constants | MODIFY_LATER | Active paths are SNR-aware. Also contains legacy PRONOSTIA/RUL constants that must not feed runtime architecture. |
| `src/data_loader.py` | ACTIVE_AND_VERIFIED | Log-Mel data loader for Expert A | KEEP | Matches reported shapes and SNR runner usage. |
| `src/models/anomaly_detector.py` | ACTIVE_AND_VERIFIED | Expert A ConvAutoencoder, training, threshold, evaluation | KEEP | Do not change architecture or training logic without explicit authorization. |
| `src/models/timbre_difference.py` | PARTIAL | Expert B adaptation | MODIFY_LATER | Implements timbre values, rank score, Expert A bottleneck embedder, and output JSON; performance blocked. |
| `src/utils/audio_reference_index.py` | PARTIAL | Expert B reference index utilities | MODIFY_LATER | JSON reference index, metadata filtering, deterministic kNN. Performance and artifact strategy need review. |
| `src/agents/__init__.py` | PLANNED | Future LLM/context agents package marker | KEEP | Placeholder only. |
| `src/utils/__init__.py` | PLANNED | Utilities package marker | KEEP | Placeholder only. |
| `scripts/snr_stage1.py` | ACTIVE_AND_VERIFIED | SNR zip staging and metadata verification | KEEP | Historical staging script. Do not rerun unless staging is intentionally repeated. |
| `scripts/run_snr_experiments.py` | ACTIVE_AND_VERIFIED | Controlled SNR Expert A experiment runner | KEEP | Behavior must remain unchanged. |
| `scripts/build_timbre_reference_index.py` | PARTIAL | Expert B normal-reference index builder | MODIFY_LATER | Known slow command originates here. Has timing/progress code but not reviewed by performance forensics. |
| `scripts/run_expert_b_smoke.py` | PARTIAL | Expert A -> Expert B smoke runner | MODIFY_LATER | Do not run until reference-index performance blocker is reviewed. |
| `tests/test_timbre_difference.py` | ACTIVE_BUT_UNVERIFIED | Expert B unit/guardrail tests | KEEP | Tests code-level guardrails; no Level 2 scientific validation. |
| `app/.gitkeep` | PLANNED | Dashboard placeholder | KEEP | No dashboard code yet. |
| `data/raw/mimii/fan/id_00` | GENERATED_ARTIFACT | Repo-local raw Fan WAV copy | DEPRECATE_LATER | Large data should live outside Git. Do not delete in planning task. |
| `data/processed/*.npy`, `data/processed/*.npz` | GENERATED_ARTIFACT | Legacy local Expert A arrays/stats | DEPRECATE_LATER | Active config writes to `D:\PDM_Data\MIMII\processed`. |
| `models_store/anomaly_detector.pt` | GENERATED_ARTIFACT | Legacy local Expert A model | DEPRECATE_LATER | Active config writes to `D:\PDM_Data\MIMII\models_store`. |
| `.codex/skills/project-architect` | ACTIVE_AND_VERIFIED | Legacy-discovered repo skill | KEEP | Runtime discovery sees `.codex` and `.agents`; `.agents` is official repo path. |
| `.codex/skills/paper-forensics` | ACTIVE_AND_VERIFIED | Legacy-discovered repo skill | KEEP | Duplicate of `.agents` skill. |
| `.codex/skills/scientific-implementer` | ACTIVE_AND_VERIFIED | Legacy-discovered repo skill | KEEP | Duplicate of `.agents` skill. |
| `.codex/skills/performance-forensics` | ACTIVE_AND_VERIFIED | Legacy-discovered repo skill | KEEP | Duplicate of `.agents` skill. |
| `.codex/skills/caveman` | LEGACY | Unrelated local communication skill | KEEP | Not part of project architecture. |
| `.agents/skills/*` | ACTIVE_AND_VERIFIED | Official repo skill path | KEEP | Runtime-discovered after migration. |
| `__pycache__` files | GENERATED_ARTIFACT | Python bytecode | DEPRECATE_LATER | Safe cleanup candidate, not source. |
| `_tmp_inspect_snr.py` | OBSOLETE | Temporary inspection script | DEPRECATE_LATER | Historical scratch file; do not run in normal workflow. |

### Documentation And Reality Disagreements

| DISAGREEMENT | REPOSITORY REALITY | IMPACT | ACTION |
|---|---|---|---|
| `CLAUDE_LEGACY_RUL.md` should exist | File is absent | Legacy archive requirement unmet | Restore/create only from actual historical source, not invention. |
| New `CLAUDE.md` should be clean active truth | File starts with stale skill-installation prompt text | Confusing top-of-file authority | Documentation cleanup needed. |
| Target structure in `CLAUDE.md` shows `.codex/skills` | Official repo skill path is `.agents/skills`; both are runtime-discovered | Potential confusion | AGENTS uses `.agents`; keep `.codex` as legacy duplicate. |
| Large datasets should stay outside repo | Repo contains raw MIMII WAVs and local processed artifacts | Git hygiene risk | Defer safe cleanup/move plan; do not delete now. |
| Active architecture has no RUL | `src/config.py`, `REPORT.md`, and `REPORT_PHASE1_2.md` still include RUL/PRONOSTIA constants/history | Risk of accidental reintroduction | Treat as legacy unless explicitly reactivated. |
| Expert B implementation exists | Runtime blocker prevents completion | Cannot claim Expert B works end-to-end | Phase 1 performance forensics first. |

## Current System State

| BLOCK | STATUS | WORKING | MISSING | SCIENTIFIC LIMIT | ENGINEERING LIMIT | NEXT ACTION |
|---|---|---|---|---|---|---|
| DATA | ACTIVE_AND_VERIFIED for Fan id_00 SNR variants | Three fan SNR directories have 1011 normal and 407 abnormal WAVs each under `D:\PDM_Data\MIMII` | Pump, valve, slide rail not staged; MIMII DG not staged | Current fan data cannot evaluate timbre-direction accuracy | Duplicate data also exists in repo | Do not block Fan MVP; record future staging phases. |
| PREPROCESSING | ACTIVE_AND_VERIFIED | Log-Mel loader and per-SNR artifact generation | No current context schema preprocessing | Log-Mel is Expert A input, not Expert B timbre substitute | Local vs external artifact roots differ | Preserve Expert A preprocessing. |
| EXPERT A | ACTIVE_AND_VERIFIED | ConvAutoencoder, threshold, SNR AUC results | No multi-machine models yet | Fan id_00 only | Do not alter architecture/training | Reuse as stable upstream detector. |
| SNR EXPERIMENT | ACTIVE_AND_VERIFIED | minus6dB/0dB/plus6dB AUCs verified in JSON | No MIMII DG robustness | SNR conclusions are Fan id_00 specific | Full retraining is expensive | Preserve artifacts; do not rerun casually. |
| EXPERT B | PARTIAL | Code exists for AudioCommons timbre metrics, rank score, JSON guardrails | Performance review; verified smoke output; Level 2 labels | Current output is qualitative only | 40-file reference job became multi-hour CPU-bound | Phase 1 performance forensics. |
| REFERENCE INDEX | PARTIAL | JSON index utilities and builder exist | Measured acceptable runtime; artifact policy decision | Normal references must remain same machine/SNR | Known slow loop | Profile 1 and 3 files before any 40-file run. |
| CONTEXT TRANSLATION | PLANNED | None beyond config constants | Schemas and translator | Must not include RUL or root cause | No code | Implement after Expert B MVP. |
| LLM | PLANNED | Config placeholder only | Prompt, guardrails, evaluation | LLM cannot diagnose from raw audio | No implementation | Build after structured context. |
| RAG | PLANNED | Config paths only | Knowledge base, retriever, approved docs | Maintenance recommendations ungrounded until retrieval exists | No implementation | Build after LLM/context or in parallel with guardrails. |
| END-TO-END ORCHESTRATION | PLANNED | None | One command/API preserving event identity | Cannot claim system-level behavior | No implementation | Build after Expert B, context, LLM, RAG. |
| DASHBOARD | PLANNED | `app/.gitkeep` only | UI/API/dashboard | No technician-facing evidence display | No app code | Build after end-to-end JSON exists. |
| TESTS | PARTIAL | Expert B unit guardrail tests exist | Expert A tests, context tests, RAG/LLM tests | Tests do not validate scientific timbre accuracy | No full CI state | Add per phase. |
| MULTI-MACHINE GENERALIZATION | PLANNED | Machine-aware fields in some Expert B code | Pump/valve/slide rail data and models | No generalization claim | Data not staged | Future Phase 9. |
| MIMII DG ROBUSTNESS | PLANNED | Paper analysis only | Dataset, labels/assets, protocol | Current data cannot support DG claim | No data/code | Future Phase 10. |
| MIMII-AGENT-INSPIRED EXTENSION | PLANNED | Concept in `CLAUDE.md` | Approved transformations and evaluation protocol | Optional only, no runtime diagnosis | No implementation | Future Phase 11. |
| LEGACY RUL CLEANUP | PARTIAL | Legacy references identified | Actual source cleanup | RUL unsupported/out of scope | Cleanup must preserve Expert A/SNR | Do before context/LLM prompts can accidentally ingest legacy constants. |

## Cheap Data Inventory

No WAV decoding was performed. Counts are directory/file metadata only.

| MACHINE_TYPE | MACHINE_ID | SNR_OR_DOMAIN | NORMAL_COUNT | ABNORMAL_COUNT | STATUS | NOTES |
|---|---|---:|---:|---:|---|---|
| fan | id_00 | minus6dB | 1011 | 407 | REFERENCE_MVP | `D:\PDM_Data\MIMII\fan_minus6dB\id_00`; current noisy MVP/stress condition. |
| fan | id_00 | 0dB | 1011 | 407 | READY_FOR_PIPELINE | Staged and used in SNR experiment. |
| fan | id_00 | plus6dB | 1011 | 407 | READY_FOR_PIPELINE | Staged and used in SNR experiment. |
| pump | id_00 | unknown | 0 | 0 | MISSING | Not staged under inspected `D:\PDM_Data\MIMII` layout. |
| valve | id_00 | unknown | 0 | 0 | MISSING | Not staged under inspected `D:\PDM_Data\MIMII` layout. |
| slide rail | id_00 | unknown | 0 | 0 | MISSING | Not staged under inspected `D:\PDM_Data\MIMII` layout. |
| MIMII DG | sections/domains | source/target | 0 | 0 | MISSING | Not staged. Required for domain-shift evaluation, not Fan MVP. |

External artifacts observed:

- Zips: `-6_dB_fan.zip`, `0_dB_fan.zip`, `6_dB_fan.zip`.
- Processed arrays/stats: per-SNR `X_train_ad_*`, `X_test_ad_*`, `y_test_ad_*`, `ad_norm_stats_*`.
- Models: per-SNR `anomaly_detector_minus6dB.pt`, `anomaly_detector_0dB.pt`, `anomaly_detector_plus6dB.pt`.
- Summary: `snr_ad_summary.json`, `snr_ad_summary.csv`.

## Final Active System Map

### Runtime Flow

```text
audio event
-> Expert A
-> conditional Expert B
-> Structured Health Context
-> RAG
-> LLM
-> technician output
-> dashboard
```

| COMPONENT | INPUT | OUTPUT | RESPONSIBILITY | NOT RESPONSIBLE FOR | DEPENDENCIES | CURRENT REPOSITORY STATUS |
|---|---|---|---|---|---|---|
| Audio event | WAV from a specific machine/event | Event identity and audio path | Carry machine metadata | Dataset-wide processing | MIMII staged paths | READY for Fan id_00. |
| Expert A | Log-Mel audio features | Anomaly score, threshold, boolean | Detect departure from learned normal audio | Explain timbre, diagnose root cause, RUL | `src/data_loader.py`, `src/models/anomaly_detector.py`, model/stats artifacts | ACTIVE_AND_VERIFIED. |
| Conditional Expert B | Same audio event plus Expert A anomaly result | Five timbre rank scores and references | Characterize acoustic/timbre difference vs same-domain normals | Diagnose physical root cause or confidence | AudioCommons, Expert A bottleneck, reference index | PARTIAL, performance blocked. |
| Structured Health Context | Expert A/B outputs, metadata, limits | Versioned JSON evidence | Preserve evidence and limitations | Invent labels or maintenance advice | Future `src/context` | PLANNED. |
| RAG | Health context query and approved docs | Retrieved maintenance evidence | Ground recommendation source material | Diagnose from raw audio | Future `src/rag`, approved docs | PLANNED. |
| LLM | Structured context plus retrieved evidence | Technician-facing explanation | Explain evidence cautiously | Direct raw-audio diagnosis, RUL, certainty invention | Future prompt/agent code | PLANNED. |
| Technician output | LLM/RAG result | Human-readable recommendation | Communicate evidence, limitations, inspection suggestions | Claim unsupported root cause | Orchestrator | PLANNED. |
| Dashboard | End-to-end JSON | UI | Display state/evidence/recommendation | Run training or data processing | Future app | PLANNED. |

### Offline Flow

```text
normal audio
-> Expert A training
-> per-machine/per-condition model artifacts

normal audio
-> Expert B reference indexing
-> embeddings + timbre values

evaluation datasets
-> Expert A / Expert B / robustness evaluation
```

| COMPONENT | INPUT | OUTPUT | RESPONSIBILITY | NOT RESPONSIBLE FOR | DEPENDENCIES | CURRENT REPOSITORY STATUS |
|---|---|---|---|---|---|---|
| Expert A training | Normal Log-Mel arrays | Model and norm stats | Train normal-only detector | Expert B timbre metrics | `scripts/run_snr_experiments.py` | COMPLETE for Fan id_00 SNRs. |
| Expert B reference indexing | Normal WAVs from same machine/SNR | Reference index with embeddings/timbre values | Cache expensive deterministic normal-reference features | Process abnormal samples as references | `scripts/build_timbre_reference_index.py` | PARTIAL, performance blocked. |
| Expert A evaluation | Normal/abnormal test arrays | AUC, threshold metrics | Quantify anomaly separation | Explain differences | SNR artifacts | COMPLETE for Fan id_00 SNRs. |
| Expert B evaluation | Labeled timbre-difference dataset | Per-attribute accuracy/MAE | Validate characterization accuracy | Use current fan data as label proxy | MIMII DG plus labels/annotations | PLANNED, data missing. |
| Robustness evaluation | MIMII DG / synthetic scenarios | Domain-shift report | Test transfer/robustness | Runtime diagnosis | Future data/protocol | PLANNED. |

## Execution Phases

Every phase has exactly one primary skill. A blocker may route to another skill
only when the blocker matches that skill.

### Phase 0 - Source-Of-Truth Baseline And Legacy Cleanup Map

PHASE: `phase_0_source_baseline`

STATUS: `COMPLETE_FOR_PLANNING_CURRENT_TASK`

GOAL:

- Establish active source of truth, map repository reality, record legacy/RUL risks, create this roadmap, create `project_state.json`, and update `AGENTS.md` continuation policy.

WHY NOW:

- The repository adopted a new active `CLAUDE.md` and must not continue from old RUL/PRONOSTIA assumptions.

PRIMARY SKILL: `$project-architect`

DEPENDENCIES:

- `CLAUDE.md`, reports, Expert B spec, repository inspection, cheap data metadata.

INPUTS:

- Required docs, source tree, `git status`, artifact metadata, `D:\PDM_Data` metadata.

FILES TO INSPECT:

- `CLAUDE.md`, `AGENTS.md`, `REPORT_PHASE1_2.md`, `REPORT.md`, `docs/EXPERT_B_NISHIDA_METHOD_SPEC.md`, `requirements.txt`, `src/`, `scripts/`, `tests/`, `app/`, `docs/`, `.codex/skills/`.

FILES TO CREATE:

- `docs/MASTER_PROJECT_ROADMAP.md`, `project_state.json`.

FILES TO MODIFY:

- `AGENTS.md` only for continuation policy.

ARTIFACTS:

- Roadmap and state file.

UNIT TESTS:

- JSON validation for `project_state.json`.

ONE-SAMPLE SMOKE:

- Not applicable; planning only.

THREE-SAMPLE TIMING:

- Not applicable; planning only.

SMALL BOUNDED RUN:

- Not applicable; planning only.

EXPENSIVE COMMANDS:

- Forbidden in this phase.

RUNTIME GATE:

- No dataset processing, no training, no Expert B job.

SCIENTIFIC CLAIM ENABLED:

- Current project state and phase order are evidence-based.

SCIENTIFIC CLAIM NOT ENABLED:

- No new model or Expert B scientific claim.

DEFINITION OF DONE:

- Roadmap created, state file validates, AGENTS continuation policy updated, source untouched.

STOP CONDITION:

- Stop after validation; do not start Phase 1.

NEXT PHASE DEPENDENCY:

- Phase 1 can start using `$performance-forensics`.

### Phase 1 - Expert B Performance Forensics

PHASE: `phase_1_expert_b_performance_forensics`

STATUS: `NEXT_EXECUTABLE`

GOAL:

- Find and fix scientifically equivalent redundant work behind the slow reference-index build.

WHY NOW:

- Expert B cannot be trusted operationally while a 40-file normal-reference job can run for hours.

PRIMARY SKILL: `$performance-forensics`

DEPENDENCIES:

- Existing Expert B code and current known slow command.

INPUTS:

- `scripts/build_timbre_reference_index.py`, `src/models/timbre_difference.py`, `src/utils/audio_reference_index.py`, one normal WAV metadata/path.

FILES TO INSPECT:

- `src/models/timbre_difference.py`, `src/utils/audio_reference_index.py`, `scripts/build_timbre_reference_index.py`, installed `timbral_models` source/API.

FILES TO CREATE:

- None unless a benchmark log file is explicitly needed.

FILES TO MODIFY:

- Only performance-equivalent redundant-work fixes in Expert B/index code, if measured.

ARTIFACTS:

- One-file and three-file benchmark outputs; optional 40-file result only if runtime is reasonable.

UNIT TESTS:

- `tests/test_timbre_difference.py`.

ONE-SAMPLE SMOKE:

- `build_timbre_reference_index.py --limit 1`, with stage timings.

THREE-SAMPLE TIMING:

- `build_timbre_reference_index.py --limit 3`, with scaling estimate.

SMALL BOUNDED RUN:

- `--limit 40` only after measured runtime is reasonable.

EXPENSIVE COMMANDS:

- Full reference indexing or abnormal Expert B smoke are forbidden until 1/3-file timings pass.

RUNTIME GATE:

- Visible progress, per-stage timing, ETA after 3 files, stop if estimate is unexpectedly large.

SCIENTIFIC CLAIM ENABLED:

- Expert B indexing runtime is understood and bounded.

SCIENTIFIC CLAIM NOT ENABLED:

- No Expert B accuracy or final system claim.

DEFINITION OF DONE:

- Root cause, before/after benchmarks, estimated 40-file runtime, and statement that output semantics changed: yes/no.

STOP CONDITION:

- Stop after benchmark; do not run abnormal Expert B smoke.

NEXT PHASE DEPENDENCY:

- Phase 2 requires reasonable reference-index runtime.

### Phase 2 - Expert B Integration MVP

PHASE: `phase_2_expert_b_integration_mvp`

STATUS: `BLOCKED_BY_PHASE_1`

GOAL:

- Run a bounded same-audio Expert A -> Expert B smoke test for Fan id_00.

WHY NOW:

- Needed before structured context can include timbre evidence.

PRIMARY SKILL: `$scientific-implementer`

DEPENDENCIES:

- Phase 1 complete; reference index build acceptable.

INPUTS:

- Same SNR abnormal audio event, Expert A result, same-machine normal reference index.

FILES TO INSPECT:

- `docs/EXPERT_B_NISHIDA_METHOD_SPEC.md`, Expert B code, smoke script, tests.

FILES TO CREATE:

- Smoke output JSON under a configured processed path.

FILES TO MODIFY:

- Expert B code only if smoke exposes bounded bugs.

ARTIFACTS:

- Reference index; abnormal smoke JSON.

UNIT TESTS:

- Expert B unit/guardrail tests.

ONE-SAMPLE SMOKE:

- One normal-reference index build and one abnormal same-audio characterization.

THREE-SAMPLE TIMING:

- Required if additional indexing or timbre loops run.

SMALL BOUNDED RUN:

- 30-reference minimum for kNN, only after timing gate.

EXPENSIVE COMMANDS:

- No full machine/dataset run.

RUNTIME GATE:

- Use execution ladder; stop if 30 references estimate is unreasonable.

SCIENTIFIC CLAIM ENABLED:

- Expert B technically emits qualitative timbre rank scores for one event.

SCIENTIFIC CLAIM NOT ENABLED:

- No timbre direction accuracy claim, no root cause, no confidence.

DEFINITION OF DONE:

- JSON has five rank scores, `direction=null`, same machine/id/SNR references, and no diagnosis/RUL fields.

STOP CONDITION:

- Stop after one abnormal smoke output.

NEXT PHASE DEPENDENCY:

- Phase 3 needs actual Expert B outputs to design qualitative review.

### Phase 3 - Expert B Qualitative Evidence Protocol

PHASE: `phase_3_expert_b_qualitative_protocol`

STATUS: `PLANNED`

GOAL:

- Define a repeatable qualitative review protocol for Expert B outputs without claiming accuracy.

WHY NOW:

- Current fan data lack five-attribute ground-truth labels.

PRIMARY SKILL: `$project-architect`

DEPENDENCIES:

- Phase 2 smoke JSON and reference neighbors.

INPUTS:

- Expert B output JSON, normal controls, abnormal examples.

FILES TO INSPECT:

- Expert B outputs, method spec, tests.

FILES TO CREATE:

- `docs/expert_b_qualitative_protocol.md` if needed.

FILES TO MODIFY:

- None by default.

ARTIFACTS:

- Protocol doc, optional plots/tables from small bounded samples.

UNIT TESTS:

- Not applicable unless helper code is added.

ONE-SAMPLE SMOKE:

- Inspect one abnormal and one normal control output.

THREE-SAMPLE TIMING:

- Required before any multi-sample qualitative batch.

SMALL BOUNDED RUN:

- Small fixed set only, with runtime estimate.

EXPENSIVE COMMANDS:

- Full abnormal dataset characterization forbidden.

RUNTIME GATE:

- Same ladder for any data loop.

SCIENTIFIC CLAIM ENABLED:

- Qualitative characterization procedure.

SCIENTIFIC CLAIM NOT ENABLED:

- Quantitative timbre direction accuracy.

DEFINITION OF DONE:

- Protocol clearly states evidence, review checks, limitations, and no accuracy claim.

STOP CONDITION:

- Stop at protocol document.

NEXT PHASE DEPENDENCY:

- Phase 4 can consume stable Expert A/B evidence fields.

### Phase 4 - Structured Health Context

PHASE: `phase_4_structured_health_context`

STATUS: `PLANNED`

GOAL:

- Implement a deterministic versioned JSON schema translating Expert A/B outputs into health context.

WHY NOW:

- LLM and RAG need structured evidence, not raw audio or free-form model output.

PRIMARY SKILL: `$scientific-implementer`

DEPENDENCIES:

- Phase 2 output schema and Phase 3 limitations.

INPUTS:

- Expert A result, Expert B result, machine metadata, system limits.

FILES TO INSPECT:

- `src/config.py`, Expert A/B outputs, `AGENTS.md`, `CLAUDE.md`.

FILES TO CREATE:

- `src/context/__init__.py`, `src/context/schemas.py`, `src/context/translator.py`, `tests/test_context_schema.py`.

FILES TO MODIFY:

- Minimal imports/config only if needed.

ARTIFACTS:

- Context JSON examples.

UNIT TESTS:

- Schema required fields, no RUL/root-cause fields, same event identity preserved.

ONE-SAMPLE SMOKE:

- Convert one Expert A/B output to context JSON.

THREE-SAMPLE TIMING:

- Required only if processing multiple examples.

SMALL BOUNDED RUN:

- Three fixed outputs at most.

EXPENSIVE COMMANDS:

- Full dataset context generation forbidden.

RUNTIME GATE:

- Cheap unit first; no full loops.

SCIENTIFIC CLAIM ENABLED:

- Evidence can be passed deterministically to LLM/RAG.

SCIENTIFIC CLAIM NOT ENABLED:

- Explanation quality or maintenance correctness.

DEFINITION OF DONE:

- Schema tests pass; context includes system limits and excludes RUL.

STOP CONDITION:

- Stop after schema tests and one sample context.

NEXT PHASE DEPENDENCY:

- Phase 5 LLM can consume context.

### Phase 5 - LLM Explanation Agent

PHASE: `phase_5_llm_explanation_agent`

STATUS: `PLANNED`

GOAL:

- Produce cautious explanation from structured health context.

WHY NOW:

- Technician-facing explanation requires guardrails before RAG recommendations.

PRIMARY SKILL: `$scientific-implementer`

DEPENDENCIES:

- Phase 4 context schema.

INPUTS:

- Structured health context JSON.

FILES TO INSPECT:

- `src/context`, `CLAUDE.md`, guardrails.

FILES TO CREATE:

- `src/agents/__init__.py`, `src/agents/diagnostic_agent.py`, `tests/test_llm_guardrails.py`.

FILES TO MODIFY:

- None outside agent package unless necessary.

ARTIFACTS:

- Example explanation JSON/text.

UNIT TESTS:

- No RUL, no root cause, no confidence invention, separates observation from hypothesis.

ONE-SAMPLE SMOKE:

- One static context input.

THREE-SAMPLE TIMING:

- Required before any multi-context batch.

SMALL BOUNDED RUN:

- Up to three static contexts.

EXPENSIVE COMMANDS:

- No model training; no full data processing.

RUNTIME GATE:

- If an external/local LLM is used, record latency and stop on unexpected runtime.

SCIENTIFIC CLAIM ENABLED:

- Guardrailed explanation prototype.

SCIENTIFIC CLAIM NOT ENABLED:

- Grounded maintenance recommendation.

DEFINITION OF DONE:

- Guardrail tests pass and one sample explanation is generated.

STOP CONDITION:

- Stop before RAG integration.

NEXT PHASE DEPENDENCY:

- Phase 6 adds retrieval grounding.

### Phase 6 - Maintenance RAG

PHASE: `phase_6_maintenance_rag`

STATUS: `PLANNED`

GOAL:

- Ground maintenance recommendations in approved documents.

WHY NOW:

- Recommendations must cite or trace source evidence.

PRIMARY SKILL: `$scientific-implementer`

DEPENDENCIES:

- Approved maintenance documents and Phase 4/5 interfaces.

INPUTS:

- Approved manuals/procedures, context query.

FILES TO INSPECT:

- `src/config.py`, future `data/manuals`, `src/agents`.

FILES TO CREATE:

- `src/rag/__init__.py`, `src/rag/knowledge_base.py`, `src/rag/retriever.py`, `tests/test_rag_grounding.py`.

FILES TO MODIFY:

- Agent integration only when bounded.

ARTIFACTS:

- Small indexed knowledge base, retrieval examples.

UNIT TESTS:

- Retrieval returns source text/IDs; recommendation cannot cite missing source.

ONE-SAMPLE SMOKE:

- One query against one small approved document.

THREE-SAMPLE TIMING:

- Three retrieval queries before larger indexing.

SMALL BOUNDED RUN:

- Small document set only.

EXPENSIVE COMMANDS:

- No large web crawl or unbounded ingestion.

RUNTIME GATE:

- Measure indexing/retrieval time and document count.

SCIENTIFIC CLAIM ENABLED:

- Maintenance recommendations can be source-grounded.

SCIENTIFIC CLAIM NOT ENABLED:

- Correct root-cause diagnosis.

DEFINITION OF DONE:

- Source-preserving retrieval and recommendation guardrail tests pass.

STOP CONDITION:

- Stop after small RAG smoke.

NEXT PHASE DEPENDENCY:

- Phase 7 orchestrates all components.

### Phase 7 - End-To-End Orchestration

PHASE: `phase_7_end_to_end_orchestration`

STATUS: `PLANNED`

GOAL:

- Provide one bounded command/API path from audio event to technician output.

WHY NOW:

- Components need event-identity preservation end to end.

PRIMARY SKILL: `$scientific-implementer`

DEPENDENCIES:

- Phases 2, 4, 5, 6.

INPUTS:

- One Fan id_00 audio event and required artifacts.

FILES TO INSPECT:

- Expert A/B code, context, agents, rag.

FILES TO CREATE:

- `scripts/run_end_to_end_demo.py`, tests for orchestration.

FILES TO MODIFY:

- Minimal integration imports only.

ARTIFACTS:

- End-to-end output JSON.

UNIT TESTS:

- Event identity, conditional Expert B, no RUL/root-cause leakage.

ONE-SAMPLE SMOKE:

- One abnormal audio event.

THREE-SAMPLE TIMING:

- Three events before any larger demo.

SMALL BOUNDED RUN:

- Three events only unless approved.

EXPENSIVE COMMANDS:

- Full dataset demo forbidden.

RUNTIME GATE:

- Timing per component and total runtime.

SCIENTIFIC CLAIM ENABLED:

- End-to-end technical integration works for Fan id_00 sample.

SCIENTIFIC CLAIM NOT ENABLED:

- Scientific accuracy beyond verified component claims.

DEFINITION OF DONE:

- One command produces full guarded JSON and tests pass.

STOP CONDITION:

- Stop after bounded demo output.

NEXT PHASE DEPENDENCY:

- Phase 8 dashboard can read output JSON.

### Phase 8 - Dashboard

PHASE: `phase_8_dashboard`

STATUS: `PLANNED`

GOAL:

- Visualize anomaly evidence, timbre differences, explanation, recommendations, and limitations.

WHY NOW:

- Presentation layer needs stable end-to-end output.

PRIMARY SKILL: `$scientific-implementer`

DEPENDENCIES:

- Phase 7 output JSON.

INPUTS:

- End-to-end JSON artifact.

FILES TO INSPECT:

- `app/`, orchestration output schema.

FILES TO CREATE:

- `app/dashboard.py` or a minimal agreed app file.

FILES TO MODIFY:

- None outside app unless needed.

ARTIFACTS:

- Local dashboard view.

UNIT TESTS:

- Basic import/schema rendering tests if feasible.

ONE-SAMPLE SMOKE:

- Load one output JSON.

THREE-SAMPLE TIMING:

- Not required unless rendering batches.

SMALL BOUNDED RUN:

- One local dashboard session.

EXPENSIVE COMMANDS:

- No training/data processing from UI.

RUNTIME GATE:

- App starts quickly and does not launch data loops.

SCIENTIFIC CLAIM ENABLED:

- Technician-facing visualization prototype.

SCIENTIFIC CLAIM NOT ENABLED:

- Field deployment readiness.

DEFINITION OF DONE:

- Dashboard displays evidence and limitations without unsupported claims.

STOP CONDITION:

- Stop after local dashboard smoke.

NEXT PHASE DEPENDENCY:

- Phase 9 can generalize once core Fan system works.

### Phase 9 - Pump / Valve / Slide Rail Generalization

PHASE: `phase_9_multi_machine_generalization`

STATUS: `PLANNED`

GOAL:

- Extend same architecture to pump, valve, and slide rail with machine-specific artifacts.

WHY NOW:

- Academic project should show generalization only after Fan MVP is stable.

PRIMARY SKILL: `$project-architect`

DEPENDENCIES:

- Completed Fan end-to-end system and staged additional machine data.

INPUTS:

- Additional MIMII machine datasets.

FILES TO INSPECT:

- Config, data loader assumptions, Expert A/B artifact naming, roadmap/state.

FILES TO CREATE:

- Machine-specific evaluation docs/artifact maps.

FILES TO MODIFY:

- Machine-aware configuration only after plan approval.

ARTIFACTS:

- Per-machine Expert A models/results and Expert B indexes.

UNIT TESTS:

- Machine-aware path and metadata tests.

ONE-SAMPLE SMOKE:

- One normal/abnormal per new machine after staging.

THREE-SAMPLE TIMING:

- Per machine before larger runs.

SMALL BOUNDED RUN:

- Small machine-specific run only.

EXPENSIVE COMMANDS:

- Full multi-machine training only after estimate and approval.

RUNTIME GATE:

- Ladder required for each machine.

SCIENTIFIC CLAIM ENABLED:

- Architecture transfer evidence, if evaluated.

SCIENTIFIC CLAIM NOT ENABLED:

- Universal model claim.

DEFINITION OF DONE:

- Per-machine results reported separately; no mixed universal baseline as first claim.

STOP CONDITION:

- Stop after bounded per-machine report.

NEXT PHASE DEPENDENCY:

- Phase 10 can test domain shift.

### Phase 10 - MIMII DG Robustness

PHASE: `phase_10_mimii_dg_robustness`

STATUS: `PLANNED`

GOAL:

- Evaluate source/target domain shift behavior.

WHY NOW:

- Robustness claims require MIMII DG-style domains.

PRIMARY SKILL: `$paper-forensics`

DEPENDENCIES:

- Core system stable; MIMII DG staged; exact protocol reviewed.

INPUTS:

- MIMII DG data and official/task documentation.

FILES TO INSPECT:

- MIMII DG docs/spec, current data pipeline, Expert A/B reference filters.

FILES TO CREATE:

- Robustness protocol and evaluation scripts only after plan.

FILES TO MODIFY:

- Dataset/config additions after approval.

ARTIFACTS:

- Domain robustness report.

UNIT TESTS:

- Domain metadata filtering tests.

ONE-SAMPLE SMOKE:

- One source-domain and one target-domain sample path check.

THREE-SAMPLE TIMING:

- Required before any domain batch.

SMALL BOUNDED RUN:

- One machine/section bounded run.

EXPENSIVE COMMANDS:

- Full MIMII DG benchmark only after timing estimate.

RUNTIME GATE:

- Ladder required.

SCIENTIFIC CLAIM ENABLED:

- Domain-shift robustness evidence if executed.

SCIENTIFIC CLAIM NOT ENABLED:

- Paper-equivalent timbre accuracy without labels.

DEFINITION OF DONE:

- Protocol and bounded results with limits.

STOP CONDITION:

- Stop before full benchmark unless approved.

NEXT PHASE DEPENDENCY:

- Phase 11 optional extension can use robustness protocol.

### Phase 11 - Optional MIMII-Agent-Inspired Evaluation

PHASE: `phase_11_optional_mimii_agent_inspired_evaluation`

STATUS: `OPTIONAL_PLANNED`

GOAL:

- Explore relative robustness using approved synthetic acoustic transformations.

WHY NOW:

- Optional academic extension after core and robustness phases.

PRIMARY SKILL: `$paper-forensics`

DEPENDENCIES:

- Core system, robustness protocol, paper inspection, approved transformations.

INPUTS:

- MIMII-Agent paper/assets, normal audio, approved transform list.

FILES TO INSPECT:

- MIMII-Agent primary paper/assets, current evaluation code.

FILES TO CREATE:

- Optional evaluation protocol and scripts.

FILES TO MODIFY:

- None until plan approved.

ARTIFACTS:

- Relative robustness report.

UNIT TESTS:

- Transform provenance and guardrail tests.

ONE-SAMPLE SMOKE:

- One transform on one normal sample after approval.

THREE-SAMPLE TIMING:

- Required before any synthetic batch.

SMALL BOUNDED RUN:

- Small fixed transform set only.

EXPENSIVE COMMANDS:

- No unbounded synthetic generation.

RUNTIME GATE:

- Ladder required.

SCIENTIFIC CLAIM ENABLED:

- Optional relative robustness evidence.

SCIENTIFIC CLAIM NOT ENABLED:

- Runtime root-cause diagnosis or automatic model improvement.

DEFINITION OF DONE:

- Report clearly states synthetic evaluation limits.

STOP CONDITION:

- Stop at optional report.

NEXT PHASE DEPENDENCY:

- None.

## Mandatory Execution Ladder

All data/model work must follow:

```text
UNIT TEST
-> ONE-SAMPLE SMOKE
-> THREE-SAMPLE TIMING
-> SMALL BOUNDED RUN
-> RUNTIME ESTIMATE
-> FULL RUN ONLY IF REASONABLE
```

Operational runtime gate:

- Loops must print visible progress.
- Long loops must emit measured per-stage timing.
- After at least three representative samples, estimate total runtime before a larger run.
- Unexpected multi-hour bounded jobs must stop.
- Any unexpectedly slow or CPU-bound data/model job routes to `$performance-forensics`.
- No future process may spend hours on 40 files without prior timing evidence.

## Scientific Claim Matrix

| CLAIM | SUPPORTED_NOW | EVIDENCE | BLOCKER | PHASE_ENABLING_CLAIM |
|---|---|---|---|---|
| Expert A detects anomalous Fan id_00 sounds. | YES | Expert A code, artifacts, SNR summary AUCs. | Fan id_00 scope only. | Already supported. |
| Expert A performance is sensitive to SNR. | YES | AUC 0.6142, 0.8306, 0.9980 across SNR. | Only fan id_00 evaluated. | Already supported. |
| Low SNR is strongly indicated as the primary limitation of weak -6 dB separation. | YES | Same pipeline/architecture improves monotonically with SNR. | Does not prove noise is only limitation. | Already supported. |
| Expert B technically characterizes acoustic/timbre differences. | NOT YET | Code exists, tests exist. | Performance blocker and no abnormal smoke output reviewed. | Phase 2. |
| Expert B accurately predicts timbre direction. | NO | No five-attribute ground-truth labels in current fan data. | Missing labels/threshold policy. | Phase 10 or separate labeled protocol. |
| Expert B diagnoses physical root cause. | NO | Active architecture forbids this. | No diagnosis labels/model. | Not in active scope. |
| LLM explanation is grounded. | NO | No LLM/context/RAG implementation. | Structured context and guardrails missing. | Phase 5 for explanation; Phase 6 for grounding. |
| Maintenance recommendations are grounded. | NO | No approved knowledge base/retriever. | RAG missing. | Phase 6. |
| Architecture generalizes to Pump. | NO | Pump data not staged. | Data/artifacts/evaluation missing. | Phase 9. |
| Architecture generalizes to Valve. | NO | Valve data not staged. | Data/artifacts/evaluation missing. | Phase 9. |
| Architecture generalizes to Slide Rail. | NO | Slide rail data not staged. | Data/artifacts/evaluation missing. | Phase 9. |
| System is robust to domain shift. | NO | MIMII DG not staged/evaluated. | DG data/protocol missing. | Phase 10. |
| System predicts RUL. | NO | RUL is outside active scope. | No run-to-failure labels; PRONOSTIA legacy only. | Not in active scope. |

## Target Repository Structure

Items are marked relative to the active target.

```text
IOT/ [EXISTING]
|-- AGENTS.md [MODIFY]
|-- CLAUDE.md [MODIFY]
|-- CLAUDE_LEGACY_RUL.md [CREATE if source is recovered]
|-- project_state.json [CREATE]
|-- requirements.txt [MODIFY]
|-- REPORT.md [LEGACY]
|-- REPORT_PHASE1_2.md [EXISTING]
|-- DIOTCLAUDE.md [DEPRECATE]
|-- _tmp_inspect_snr.py [DEPRECATE]
|-- .agents/skills/ [EXISTING]
|   |-- project-architect/ [EXISTING]
|   |-- paper-forensics/ [EXISTING]
|   |-- scientific-implementer/ [EXISTING]
|   |-- performance-forensics/ [EXISTING]
|-- .codex/skills/ [LEGACY]
|   |-- project-architect/ [EXISTING]
|   |-- paper-forensics/ [EXISTING]
|   |-- scientific-implementer/ [EXISTING]
|   |-- performance-forensics/ [EXISTING]
|   |-- caveman/ [LEGACY]
|-- src/ [EXISTING]
|   |-- __init__.py [EXISTING]
|   |-- config.py [MODIFY]
|   |-- data_loader.py [EXISTING]
|   |-- models/ [EXISTING]
|   |   |-- anomaly_detector.py [EXISTING]
|   |   |-- timbre_difference.py [MODIFY]
|   |-- utils/ [EXISTING]
|   |   |-- audio_reference_index.py [MODIFY]
|   |-- context/ [CREATE]
|   |   |-- __init__.py [CREATE]
|   |   |-- schemas.py [CREATE]
|   |   |-- translator.py [CREATE]
|   |-- agents/ [MODIFY]
|   |   |-- diagnostic_agent.py [CREATE]
|   |   |-- maintenance_agent.py [CREATE later if needed]
|   |-- rag/ [CREATE]
|       |-- __init__.py [CREATE]
|       |-- knowledge_base.py [CREATE]
|       |-- retriever.py [CREATE]
|-- scripts/ [EXISTING]
|   |-- snr_stage1.py [EXISTING]
|   |-- run_snr_experiments.py [EXISTING]
|   |-- build_timbre_reference_index.py [MODIFY]
|   |-- run_expert_b_smoke.py [MODIFY]
|   |-- run_end_to_end_demo.py [CREATE]
|-- app/ [EXISTING]
|   |-- dashboard.py [CREATE]
|-- docs/ [MODIFY]
|   |-- MASTER_PROJECT_ROADMAP.md [CREATE]
|   |-- EXPERT_B_NISHIDA_METHOD_SPEC.md [EXISTING]
|   |-- expert_b_qualitative_protocol.md [CREATE]
|   |-- evaluation_protocol.md [CREATE]
|   |-- academic_claims.md [CREATE]
|-- tests/ [MODIFY]
|   |-- test_timbre_difference.py [EXISTING]
|   |-- test_expert_a.py [CREATE]
|   |-- test_reference_index.py [CREATE or split from current test]
|   |-- test_context_schema.py [CREATE]
|   |-- test_llm_guardrails.py [CREATE]
|   |-- test_rag_grounding.py [CREATE]
|-- data/ [DEPRECATE for large generated data]
|-- models_store/ [DEPRECATE for generated model artifacts]
```

## First Executable Phase

`phase_1_expert_b_performance_forensics`

Do not start it automatically during this planning task.

## Next Command For Yosef

```text
continue project
```

Expected behavior: read `AGENTS.md`, read `CLAUDE.md`, read this roadmap, read
`project_state.json`, select Phase 1, invoke `$performance-forensics`, and stop
after the bounded benchmark.
