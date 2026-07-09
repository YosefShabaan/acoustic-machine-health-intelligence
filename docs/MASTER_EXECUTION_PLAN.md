# Master Execution Plan

Plan version: `master_execution_plan_v3_2026-07-07`

Repository: `D:\IOT`

Execution status: implementing approved plan.

Expected approval command:

```text
start implementation
```

This document is the executable task decomposition. It is different from
`docs/MASTER_PROJECT_ROADMAP.md`, which is a phase-level roadmap.

## Final Architecture

```text
SAME MACHINE
SAME AUDIO EVENT
-> Expert A detects anomaly
-> Expert B characterizes acoustic/timbre difference
-> Structured Health Context
-> LLM + RAG
-> Dashboard
```

Reference MVP: MIMII `fan / id_00`.

Later generalization targets: `pump`, `valve`, `slide rail`.

RUL and PRONOSTIA are outside active scope. `CLAUDE_LEGACY_RUL.md` was
intentionally deleted by Yosef and is not a blocker.

## Execution Policy

Stage 1 is architecture and complete task decomposition. It ends with this plan
and waits for approval.

Stage 2 starts only after `start implementation`. Codex implements tasks in
order, reviews every task, updates `project_state.json`, and continues to the
next approved task automatically.

Stop only when:

- a real scientific blocker requires Yosef's decision,
- required data or credentials are unavailable,
- the approved architecture must change,
- a task fails after a bounded diagnosis attempt,
- or the complete approved plan is finished.

## Global Runtime Gate

For all data/model work:

```text
UNIT TEST
-> ONE-SAMPLE SMOKE
-> THREE-SAMPLE TIMING
-> SMALL BOUNDED RUN
-> RUNTIME ESTIMATE
-> FULL RUN ONLY IF REASONABLE
```

Visible progress, per-stage timing, and estimated remaining time are required for
long loops. A 40-file job must not run for hours without prior 1-file and 3-file
timing evidence.

## Mandatory Review After Every Implemented Task

IMPLEMENTATION REVIEW:

- Does code match the task specification?
- Were unrelated files changed?
- Did tests actually run?
- Did smoke tests use actual data where required?
- Were actual outputs inspected?
- Are existing Expert A/SNR artifacts preserved?

SCIENTIFIC REVIEW:

- Is any paper claim overstated?
- Was a project choice presented as a paper fact?
- Were labels, thresholds, formulas, or metrics invented?
- Did output semantics change?
- Is the enabled scientific claim actually supported?

DIFF REVIEW:

- List changed files.
- Review actual git diff.
- Identify suspicious or unrelated changes.
- Confirm artifact paths cannot silently overwrite another machine/SNR.

FINAL TASK VERDICT:

- `DONE`
- `FAILED`
- `BLOCKED`

## Ordered Task List

### TASK 00

TASK ID: `TASK-00`

TITLE: Repository Normalization, Structure Cleanup, And Authoritative Technical Report

STATUS: `DONE`

GOAL:

- Normalize the repository structure and active documentation without changing Expert A scientific behavior or deleting verified model/data artifacts.

WHY:

- The repository mixed current acoustic Expert A/B scope with superseded PRONOSTIA/RUL documentation, duplicate local tool folders, Python caches, malformed context drafts, and unclassified local artifacts.

DEPENDENCIES:

- Explicit Yosef approval in the TASK-00 request.

PRIMARY SKILL: `$project-architect`

FILES INSPECTED:

- `AGENTS.md`
- `CLAUDE.md`
- `project_state.json`
- `docs/MASTER_PROJECT_ROADMAP.md`
- `docs/MASTER_EXECUTION_PLAN.md`
- `docs/EXPERT_B_NISHIDA_METHOD_SPEC.md`
- `REPORT.md`
- `REPORT_PHASE1_2.md`
- `requirements.txt`
- `.gitignore`
- `src/`
- `scripts/`
- `tests/`
- repository local artifact folders

FILES CREATED:

- `README.md`
- `docs/REPOSITORY_AUDIT.md`

FILES MODIFIED:

- `CLAUDE.md`
- `REPORT.md`
- `.gitignore`
- `requirements.txt`
- `src/config.py`
- `docs/MASTER_EXECUTION_PLAN.md`
- `docs/TASK_EXECUTION_LOG.md`
- `project_state.json`

IMPLEMENTATION:

- Removed stale active-context preface from `CLAUDE.md`.
- Removed active PRONOSTIA/RUL constants and comments from `src/config.py`.
- Rewrote `REPORT.md` as the authoritative current technical report.
- Added `README.md` with the current architecture, status, and operating notes.
- Created `docs/REPOSITORY_AUDIT.md` with structural findings and file classification.
- Removed duplicate local tool/skill folders while preserving `.agents/skills`.
- Removed Python caches, temporary inspection files, empty legacy placeholders, and the empty misleading repo-local `PDM_Data` directory.
- Archived the malformed duplicate context draft under `docs/archive/`.
- Updated `.gitignore` to keep local data/model artifacts and duplicate local tool folders out of Git.

UNIT TESTS:

- `python -m json.tool project_state.json`
- Import smoke for active modules.
- `python tests/test_timbre_difference.py`

SMOKE TEST:

- `python src/config.py`

RUNTIME GATE:

- No dataset processing, model training, 40-file Expert B index build, or abnormal Expert B smoke was run.

SCIENTIFIC GUARDRAILS:

- Expert A/SNR behavior, thresholds, hyperparameters, paths, and verified artifacts were preserved.
- RUL/PRONOSTIA remain historical/out of active runtime scope.
- Expert B remains partial and runtime-blocked pending performance-forensics.

REVIEW CHECKLIST:

- Active docs now describe same-machine, same-audio Expert A detects and Expert B characterizes.
- `REPORT.md` no longer presents RUL/PRONOSTIA as active architecture.
- `src/config.py` no longer exposes active RUL/PRONOSTIA settings.
- Local artifacts remain present and ignored rather than deleted.

DEFINITION OF DONE:

- Repository is normalized, authoritative reports exist, validation passes, and the plan/state point to the next real blocker task.

VERDICT:

- `DONE`

NEXT TASK:

- `TASK-00B`

### TASK 00B

TASK ID: `TASK-00B`

TITLE: Local Artifact Reconciliation And Git Review Baseline

STATUS: `DONE`

GOAL:

- Physically remove repo-local large/generated scientific artifacts after verifying external copies or preserving unique artifacts externally, then establish a real Git baseline for future diff review.

WHY:

- TASK-00 protected local artifacts with `.gitignore`, but `D:\IOT` still physically contained mirrored MIMII WAVs, generated `.npy/.npz` artifacts, and a trained `.pt` model. A clean repository baseline is required before TASK-02.

DEPENDENCIES:

- `TASK-00`.
- Explicit Yosef approval in the TASK-00B request.

PRIMARY SKILL: `$project-architect`

FILES INSPECTED:

- `.gitignore`
- `project_state.json`
- `docs/REPOSITORY_AUDIT.md`
- `D:\IOT\data`
- `D:\IOT\models_store`
- `D:\PDM_Data\MIMII\processed`
- `D:\PDM_Data\MIMII\models_store`
- `D:\PDM_Data\MIMII\fan_minus6dB\id_00`
- `D:\PDM_Data\MIMII\fan_0dB\id_00`
- `D:\PDM_Data\MIMII\fan_plus6dB\id_00`

FILES CREATED:

- `docs/LOCAL_ARTIFACT_RECONCILIATION.md`

FILES MODIFIED:

- `README.md`
- `REPORT.md`
- `docs/REPOSITORY_AUDIT.md`
- `docs/MASTER_EXECUTION_PLAN.md`
- `docs/TASK_EXECUTION_LOG.md`
- `project_state.json`

IMPLEMENTATION:

- Verified repo-local raw WAV mirror against external `fan_minus6dB` by count, size, relative paths, and representative hashes.
- Verified repo-local processed `.npy/.npz` artifacts against external `*_minus6dB` files by full SHA256.
- Moved the unique legacy repo-local model to `D:\PDM_Data\MIMII\models_store\anomaly_detector_legacy_repo_2026-06-29.pt` without overwrite.
- Removed repo-local `data/` and `models_store/`.
- Regenerated repository audit with 0 local large artifact files.
- Created a baseline Git commit containing source/docs/support files only.

UNIT TESTS:

- `python -m json.tool project_state.json`
- `python src/config.py`
- `python tests/test_timbre_difference.py`
- Active module import smoke.
- `python -m compileall -q src scripts tests`

SMOKE TEST:

- Active config path report only.

RUNTIME GATE:

- No dataset processing, model training, Expert B indexing, or abnormal Expert B smoke was run.

SCIENTIFIC GUARDRAILS:

- Expert A verified external SNR artifacts were preserved.
- No result values, labels, thresholds, equations, or model behavior were changed.
- No unknown artifact was deleted.

REVIEW CHECKLIST:

- Repo-local large artifact count is 0.
- No `.wav`, `.npy`, `.npz`, `.pt`, `.pth`, or reference index artifact is staged in Git.
- Future Git diffs can show task-specific edits.

DEFINITION OF DONE:

- Artifact reconciliation is complete, validation passes, baseline commit exists, and `TASK-02` remains next.

VERDICT:

- `DONE`

NEXT TASK:

- `TASK-02`

### TASK 01

TASK ID: `TASK-01`

TITLE: Repository Active-Scope Cleanup And Execution Wiring

STATUS: `SUPERSEDED_BY_TASK-00`

GOAL:

- Clean active project context and execution wiring so future implementation cannot accidentally use legacy RUL/PRONOSTIA scope.

WHY:

- Current repository still contains stale active-context text, legacy RUL constants/comments, duplicate malformed context file, and old one-phase continuation policy artifacts.

DEPENDENCIES:

- Superseded by `TASK-00`.

PRIMARY SKILL: `$scientific-implementer`

FILES TO INSPECT:

- `CLAUDE.md`
- `AGENTS.md`
- `project_state.json`
- `docs/MASTER_PROJECT_ROADMAP.md`
- `requirements.txt`
- `src/config.py`
- `DIOTCLAUDE.md`
- `.gitignore`

FILES TO CREATE:

- None by default.

FILES TO MODIFY:

- `CLAUDE.md` documentation cleanup only.
- `AGENTS.md` only if command policy needs small correction.
- `project_state.json`.
- `requirements.txt` comments only if needed.
- `src/config.py` only for legacy constant/comment cleanup that does not alter Expert A/SNR behavior.

IMPLEMENTATION:

- Remove stale preface text before the active `# CLAUDE.md` header.
- Record that `CLAUDE_LEGACY_RUL.md` was intentionally deleted and is not a blocker.
- Ensure active config/comments do not advertise RUL/PRONOSTIA as current Expert B.
- Preserve all Expert A paths, SNR path helpers, hyperparameters, and artifacts.
- Do not delete historical reports.
- Do not delete raw data or model artifacts.

UNIT TESTS:

- `python -m json.tool project_state.json`
- Import smoke for `src/config.py`.
- Existing Expert B unit tests by file path: `python tests/test_timbre_difference.py`.

SMOKE TEST:

- Print resolved active MIMII paths with `python src/config.py`; inspect output only.

RUNTIME GATE:

- No dataset processing.

SCIENTIFIC GUARDRAILS:

- RUL remains unsupported and outside active scope.
- PRONOSTIA remains legacy only.
- No Expert A architecture or training change.

REVIEW CHECKLIST:

- `CLAUDE.md` begins with active project context.
- `project_state.json` validates.
- No code path now suggests RUL as active runtime output.
- Expert A/SNR constants are unchanged.

DEFINITION OF DONE:

- Active-scope cleanup is complete and tests/import smoke pass.

BLOCKER CONDITIONS:

- Cleanup would require deleting historical reports or changing Expert A behavior.

### TASK 02

TASK ID: `TASK-02`

TITLE: Expert B Reference-Index Performance Root Cause And Optimization

STATUS: `DONE`

GOAL:

- Make Expert B normal-reference indexing operationally bounded without changing scientific output semantics.

WHY:

- Known evidence: the 40-file index run was CPU-bound for hours; a one-file path-based benchmark exceeded 23 minutes; `timbral_models` path calls repeat file read/downmix/loudness normalization/resampling per metric; 16 kHz inputs may be upsampled internally to 44.1 kHz.

DEPENDENCIES:

- `TASK-00B`.

PRIMARY SKILL: `$performance-forensics`

FILES TO INSPECT:

- `src/models/timbre_difference.py`
- `src/utils/audio_reference_index.py`
- `scripts/build_timbre_reference_index.py`
- Installed `timbral_models` source/API.
- `tests/test_timbre_difference.py`

FILES TO CREATE:

- Optional benchmark note under `docs/` only if useful.

FILES TO MODIFY:

- `src/models/timbre_difference.py`
- `src/utils/audio_reference_index.py`
- `scripts/build_timbre_reference_index.py`
- `tests/test_timbre_difference.py` if new guardrails are needed.
- `project_state.json`

IMPLEMENTATION:

- Use fast path first: identify measured slow stage, time exact stage, apply verified equivalent optimization, run one-sample verification, continue.
- Reuse one loaded waveform where official `timbral_models` array+`fs` API supports it.
- Avoid repeated deterministic embedding/timbre recomputation within a run.
- Add progress, ETA, and stage timings if incomplete.
- Escalate to deeper performance-forensics only if root cause remains unclear, semantics may change, or first bounded fix fails.

UNIT TESTS:

- Expert B unit tests.
- New tests for timing metadata/output options if code changes.

SMOKE TEST:

- One normal WAV reference-index build.
- Three normal WAV reference-index timing.
- Only if estimated reasonable: 40-file bounded benchmark.

RUNTIME GATE:

- Stop if one-file or three-file timing projects multi-hour runtime.
- Do not run abnormal Expert B smoke in this task.

SCIENTIFIC GUARDRAILS:

- Do not replace AudioCommons metrics with librosa approximations.
- Do not change Nishida rank-score semantics.
- Do not change `k=30` default.
- Do not change Expert A architecture/training.

REVIEW CHECKLIST:

- Root cause is measured, not guessed.
- Before/after timings are reported.
- Output schema/values remain semantically equivalent.
- 40-file run, if executed, has acceptable measured runtime.

DEFINITION OF DONE:

- Reference-index performance is bounded and reviewed, or the task is blocked with measured evidence.

BLOCKER CONDITIONS:

- `timbral_models` official API cannot be made operational without changing metric semantics.
- Runtime remains pathological after bounded equivalent optimization.

TASK-02 RESULT:

- Root cause was measured as dependency API drift between `timbral_models` and current NumPy/librosa.
- Added compatibility shims for legacy `librosa` positional calls and `np.lib.pad`.
- Switched the default Expert B timbre input path to the official AudioCommons array+`fs` API.
- Added timing summaries and external default output paths.
- One-sample, three-sample, and 40-file bounded runs completed.
- 40-file array-mode runtime: `172.222937s`.
- Scientific behavior did not change.

### TASK 03

TASK ID: `TASK-03`

TITLE: Expert B Reference Index Completion

STATUS: `DONE`

GOAL:

- Produce a usable same-machine, same-ID, same-SNR normal reference index for Fan id_00.

WHY:

- Expert B needs cached normal embeddings and timbre values before same-audio characterization can run reliably.

DEPENDENCIES:

- `TASK-02`.

PRIMARY SKILL: `$scientific-implementer`

FILES TO INSPECT:

- `scripts/build_timbre_reference_index.py`
- `src/models/timbre_difference.py`
- `src/utils/audio_reference_index.py`
- `src/config.py`

FILES TO CREATE:

- Bounded reference index artifact under an approved processed path.

FILES TO MODIFY:

- Reference-index code only if needed for artifact naming, metadata, or cache guardrails.
- `project_state.json`

IMPLEMENTATION:

- Build at least `k=30` normal references for `fan/id_00/minus6dB`.
- Use normal references only.
- Store metadata: machine type, machine ID, SNR tag, embedding model, timbre model, `k`, timing summary.
- Ensure artifact path cannot overwrite another machine/SNR.

UNIT TESTS:

- Reference filtering/kNN/unit JSON guardrails.

SMOKE TEST:

- One-sample build.
- Three-sample timing.
- Bounded `k=30` or `limit=40` run only after estimate.

RUNTIME GATE:

- Same global execution ladder.

SCIENTIFIC GUARDRAILS:

- No abnormal clips in the reference index.
- No cross-SNR or cross-machine references.
- Expert A bottleneck remains labeled as project adaptation.

REVIEW CHECKLIST:

- Reference count is sufficient for `k=30`.
- All references match `fan/id_00/minus6dB`.
- Timings and metadata are included.
- No SNR artifacts overwritten.

DEFINITION OF DONE:

- Reference index exists, validates, and is loadable by Expert B.

BLOCKER CONDITIONS:

- Acceptable runtime cannot be achieved.
- Required normal WAVs or Expert A artifacts are unavailable.

TASK-03 RESULT:

- Added output filename scope guardrails for machine type, machine ID, and SNR tag.
- Stored required reference-index metadata: machine type, machine ID, SNR tag, embedding model, timbre model, method status, `k`, distance, reference count, and timing summary.
- Built the bounded Fan `id_00` minus6dB normal reference index with 40 references.
- Artifact: `D:\PDM_Data\MIMII\processed\timbre_reference_index_fan_id_00_minus6dB.json`.
- Validation loaded the artifact, filtered 40 same-machine references, and selected 30 kNN references.
- 40-reference runtime: `162.762365s`, mean `4.067785s/file`.
- Evidence: `docs/TASK_03_REFERENCE_INDEX_VALIDATION.md`.

### TASK 04

TASK ID: `TASK-04`

TITLE: Expert A To Expert B Same-Audio Integration

STATUS: `DONE`

GOAL:

- Run one abnormal same-audio Fan id_00 event through Expert A and Expert B and save the actual Expert B JSON.

WHY:

- The active architecture depends on Expert B characterizing the same audio event that Expert A flags.

DEPENDENCIES:

- `TASK-03`.

PRIMARY SKILL: `$scientific-implementer`

FILES TO INSPECT:

- `scripts/run_expert_b_smoke.py`
- Expert B reference index.
- Expert A model/stats artifacts.
- `tests/test_timbre_difference.py`

FILES TO CREATE:

- One abnormal Expert B smoke JSON.

FILES TO MODIFY:

- Smoke script or Expert B code only if same-audio integration fails.
- `project_state.json`

IMPLEMENTATION:

- Score one abnormal Fan id_00 audio event with Expert A.
- Only run Expert B when Expert A marks that same event anomalous.
- Output five continuous rank scores.
- Keep `direction` and `direction_code` null because `rank_threshold=None`.

UNIT TESTS:

- Existing Expert B tests.
- Add same-audio identity test if missing.

SMOKE TEST:

- One abnormal same-audio event.

RUNTIME GATE:

- No full abnormal scan except bounded `max_scan` if needed to find an Expert A-flagged abnormal clip.

SCIENTIFIC GUARDRAILS:

- No confidence percentage.
- No root-cause diagnosis.
- No exact Nishida reproduction claim.

REVIEW CHECKLIST:

- Same audio path is preserved in Expert A and Expert B output.
- References are same machine/id/SNR.
- Five rank scores are finite and in `[0, 1]`.
- Output JSON inspected.

DEFINITION OF DONE:

- One reviewed Expert A -> Expert B JSON exists.

BLOCKER CONDITIONS:

- Expert A does not flag any bounded abnormal candidate.
- Expert B output contains unsupported directions or diagnosis.

TASK-04 RESULT:

- Ran a bounded `max_scan=10` abnormal same-audio smoke.
- Expert A flagged `D:\PDM_Data\MIMII\fan_minus6dB\id_00\abnormal\00000002.wav`.
- Expert A score: `0.622095`; threshold: `0.593284`; `is_anomaly=True`.
- Expert B characterized that same audio path using the Fan `id_00` minus6dB reference index.
- Output artifact: `D:\PDM_Data\MIMII\processed\expert_b_smoke_fan_id_00_minus6dB_task04.json`.
- Validation confirmed five finite rank scores in `[0, 1]`, selected `30/40` references, null directions with `rank_threshold=None`, and no diagnosis/confidence/root-cause fields.
- Evidence: `docs/TASK_04_SAME_AUDIO_SMOKE.md`.

### TASK 05

TASK ID: `TASK-05`

TITLE: Expert B Qualitative Evidence Protocol

STATUS: `DONE`

GOAL:

- Define and run a small qualitative evidence protocol for Expert B without claiming quantitative timbre accuracy.

WHY:

- Current Fan data lack five-attribute ground-truth timbre labels.

DEPENDENCIES:

- `TASK-04`.

PRIMARY SKILL: `$project-architect`

FILES TO INSPECT:

- Expert B smoke JSON.
- `docs/EXPERT_B_NISHIDA_METHOD_SPEC.md`
- `tests/test_timbre_difference.py`

FILES TO CREATE:

- `docs/expert_b_qualitative_protocol.md`
- Optional small qualitative output summary.

FILES TO MODIFY:

- `project_state.json`

IMPLEMENTATION:

- Define normal controls, abnormal examples, reference-neighbor checks, rank-score interpretation limits, and review criteria.
- Use only small bounded samples if any script is run.

UNIT TESTS:

- Not required unless helper code is added.

SMOKE TEST:

- Inspect one abnormal and one normal/control output if available.

RUNTIME GATE:

- Three-sample timing before any sample batch.

SCIENTIFIC GUARDRAILS:

- No direction-accuracy claim.
- No physical fault diagnosis.
- Rank score is not probability or confidence.

REVIEW CHECKLIST:

- Protocol distinguishes qualitative characterization from scientific validation.
- Missing labels are explicit.

DEFINITION OF DONE:

- Protocol is documented and references actual MVP outputs.

BLOCKER CONDITIONS:

- No Expert B smoke output exists.

TASK-05 RESULT:

- Created `docs/expert_b_qualitative_protocol.md`.
- Protocol distinguishes qualitative characterization from quantitative timbre-direction validation.
- Protocol records paper facts, verified repository facts, project decisions, unknowns, required inputs, review procedure, acceptance criteria, and stop conditions.
- Applied the protocol to the TASK-04 smoke JSON:
  - `D:\PDM_Data\MIMII\processed\expert_b_smoke_fan_id_00_minus6dB_task04.json`.
  - Input audio: `D:\PDM_Data\MIMII\fan_minus6dB\id_00\abnormal\00000002.wav`.
  - Selected references: `30/40`.
  - Rank-score review is qualitative only and keeps `direction=null`.
- No quantitative accuracy, diagnosis, confidence, or exact-reproduction claim was added.

### TASK 06

TASK ID: `TASK-06`

TITLE: Structured Health Context Schema And Translator

STATUS: `DONE`

GOAL:

- Implement a deterministic versioned context object combining machine metadata, Expert A output, Expert B output, and system limits.

WHY:

- LLM/RAG layers must receive structured evidence rather than raw audio or ambiguous text.

DEPENDENCIES:

- `TASK-04`.

PRIMARY SKILL: `$scientific-implementer`

FILES TO INSPECT:

- Expert A output structure.
- Expert B JSON structure.
- `CLAUDE.md`
- `src/config.py`

FILES TO CREATE:

- `src/context/__init__.py`
- `src/context/schemas.py`
- `src/context/translator.py`
- `tests/test_context_schema.py`

FILES TO MODIFY:

- `project_state.json`

IMPLEMENTATION:

- Define versioned schema.
- Preserve event identity and machine metadata.
- Include Expert A score/threshold/decision.
- Include Expert B method metadata, reference metadata, rank scores, warnings.
- Include required `system_limits`.

UNIT TESTS:

- Required fields.
- Reject/omit RUL fields.
- Reject/omit root-cause diagnosis.
- Same event identity preserved.

SMOKE TEST:

- Convert one Expert A/B output to context JSON.

RUNTIME GATE:

- No dataset loops.

SCIENTIFIC GUARDRAILS:

- Context is evidence, not diagnosis.
- No invented thresholds or labels.

REVIEW CHECKLIST:

- JSON validates.
- Limits are explicit.
- No legacy RUL/PRONOSTIA fields.

DEFINITION OF DONE:

- Context tests pass and one sample context is inspected.

BLOCKER CONDITIONS:

- Expert B output schema is unstable.

TASK-06 RESULT:

- Created `src/context/__init__.py`, `src/context/schemas.py`, and `src/context/translator.py`.
- Added `tests/test_context_schema.py`.
- Implemented schema version `0.1.0` with required `event`, `expert_a`, `expert_b`, and `system_limits` sections.
- Translator preserves event identity, machine metadata, Expert A score/threshold/decision, Expert B method metadata, reference metadata, timbre rank scores, warnings, and explicit limitations.
- Validator rejects unsupported claim keys such as `confidence_pct`, `diagnosis`, `root_cause`, `rul_prediction`, and `pronostia`.
- Smoke output: `D:\PDM_Data\MIMII\processed\structured_context_fan_id_00_minus6dB_task06.json`.
- Tests: `tests/test_context_schema.py` ran 5 tests OK; `tests/test_timbre_difference.py` ran 7 tests OK.

### TASK 07

TASK ID: `TASK-07`

TITLE: Guardrailed LLM Explanation Agent

STATUS: `DONE`

GOAL:

- Generate cautious technician-facing explanations from Structured Health Context.

WHY:

- The LLM must explain structured evidence and avoid unsupported fault/RUL claims.

DEPENDENCIES:

- `TASK-06`.

PRIMARY SKILL: `$scientific-implementer`

FILES TO INSPECT:

- `src/context/`
- `CLAUDE.md`
- `project_state.json`

FILES TO CREATE:

- `src/agents/diagnostic_agent.py`
- `tests/test_llm_guardrails.py`

FILES TO MODIFY:

- `src/agents/__init__.py`
- `project_state.json`

IMPLEMENTATION:

- Implement deterministic prompt construction or local mockable interface.
- Separate observations, limitations, and hypotheses.
- Keep LLM dependency optional/configurable if credentials/model are not available.

UNIT TESTS:

- No RUL.
- No exact component diagnosis.
- No confidence invention.
- Mentions limitations when Expert B is qualitative only.

SMOKE TEST:

- One static context input.

RUNTIME GATE:

- If a live model is used, measure one-call latency and stop if unavailable.

SCIENTIFIC GUARDRAILS:

- LLM does not see raw audio.
- LLM cannot promote rank score to probability.

REVIEW CHECKLIST:

- Actual explanation inspected.
- Guardrail tests pass.

DEFINITION OF DONE:

- One guarded explanation is produced or deterministic prompt/output wrapper is validated.

BLOCKER CONDITIONS:

- Required LLM credentials/model are unavailable and no mock/offline mode is approved.

TASK-07 RESULT:

- Created `src/agents/diagnostic_agent.py` and `tests/test_llm_guardrails.py`.
- Updated `src/agents/__init__.py` to expose the explanation agent interface.
- Implemented deterministic offline explanation generation plus an optional mockable generator interface.
- Guarded prompt construction uses Structured Health Context without passing raw audio paths.
- Output separates summary, observations, limitations, hypotheses, and inspection notes.
- Guardrails reject RUL/time-to-failure wording, component diagnosis wording, confidence wording, percentages, root-cause wording, and obvious failure assertions.
- Smoke output: `D:\PDM_Data\MIMII\processed\guarded_explanation_fan_id_00_minus6dB_task07.json`.
- Smoke result: `deterministic_offline`, 7 observations, 5 limitations, 2 hypotheses, 2 inspection notes, and no forbidden text hits.
- Tests: `tests/test_llm_guardrails.py` ran 4 tests OK; `tests/test_context_schema.py` ran 5 tests OK; `tests/test_timbre_difference.py` ran 7 tests OK.
- No live LLM credentials were required or used.

### TASK 08

TASK ID: `TASK-08`

TITLE: Maintenance Knowledge Base And Retriever

STATUS: `DONE`

GOAL:

- Create a small approved maintenance knowledge base and retrieval layer.

WHY:

- Maintenance recommendations must be grounded in approved documents, not LLM invention.

DEPENDENCIES:

- `TASK-06`.

PRIMARY SKILL: `$scientific-implementer`

FILES TO INSPECT:

- `src/config.py`
- Any approved manual/procedure files under `data/manuals` if present.

FILES TO CREATE:

- `src/rag/__init__.py`
- `src/rag/knowledge_base.py`
- `src/rag/retriever.py`
- `tests/test_rag_grounding.py`
- Optional `data/manuals/README.md`

FILES TO MODIFY:

- `project_state.json`

IMPLEMENTATION:

- Implement simple local retrieval with source IDs and snippets.
- Keep dependency footprint minimal.
- Use approved documents only.

UNIT TESTS:

- Retrieval returns source IDs.
- Empty knowledge base produces a safe unavailable result.
- Recommendation layer cannot cite missing sources.

SMOKE TEST:

- One query over one small approved document if available.

RUNTIME GATE:

- Measure indexing and retrieval time for small document set.

SCIENTIFIC GUARDRAILS:

- Retrieval evidence is not a diagnosis.
- No unsupported maintenance claim.

REVIEW CHECKLIST:

- Sources are preserved and visible.
- No unbounded web/data ingestion.

DEFINITION OF DONE:

- Retriever works on approved docs or blocks clearly if no docs are provided.

BLOCKER CONDITIONS:

- No approved maintenance documents are available and Yosef does not approve a placeholder document.

TASK-08 RESULT:

- Created `src/rag/__init__.py`, `src/rag/knowledge_base.py`, `src/rag/retriever.py`, and `tests/test_rag_grounding.py`.
- Created `data/manuals/README.md` documenting the approved-source manifest policy.
- Implemented local retrieval over explicitly approved `.md`/`.txt` documents only.
- Production indexing requires `data/manuals/approved_sources.json` with `approved: true`; loose files are ignored.
- Retrieval responses preserve source ID, title, version, chunk ID, snippet, score, and path.
- Empty or missing approved knowledge base returns a safe unavailable result rather than invented guidance.
- Citation guardrail rejects downstream recommendations that cite source IDs not returned by retrieval.
- Production smoke output: `D:\PDM_Data\MIMII\processed\rag_retrieval_smoke_task08.json`.
- Production smoke result: source_count=0, chunk_count=0, retrieval available=False, because no approved production manifest exists yet.
- Fixture runtime gate: one approved fixture source, one chunk, three retrieval queries, all returned `fixture_fan_procedure`, max retrieval time `0.000941s`.
- Tests: `tests/test_rag_grounding.py` ran 4 tests OK; `tests/test_llm_guardrails.py` ran 4 tests OK; `tests/test_context_schema.py` ran 5 tests OK; `tests/test_timbre_difference.py` ran 7 tests OK.
- No web ingestion, large crawl, diagnosis, or unsupported maintenance recommendation was added.

### TASK 09

TASK ID: `TASK-09`

TITLE: Grounded Maintenance Agent

STATUS: `DONE`

GOAL:

- Combine structured context, LLM explanation, and retrieved maintenance evidence into a grounded technician output.

WHY:

- The system's final value is cautious maintenance communication, not only anomaly/timbre scores.

DEPENDENCIES:

- `TASK-07`
- `TASK-08`

PRIMARY SKILL: `$scientific-implementer`

FILES TO INSPECT:

- `src/agents/diagnostic_agent.py`
- `src/rag/`
- `src/context/`

FILES TO CREATE:

- `src/agents/maintenance_agent.py`
- Tests for recommendation guardrails.

FILES TO MODIFY:

- `src/agents/__init__.py`
- `project_state.json`

IMPLEMENTATION:

- Build final structured technician response.
- Require retrieved sources for inspection recommendations.
- Include limitations and confidence wording guardrails.

UNIT TESTS:

- Recommendation requires source evidence.
- No root-cause certainty.
- No RUL.

SMOKE TEST:

- One static context and one retrieval result.

RUNTIME GATE:

- No data loops.

SCIENTIFIC GUARDRAILS:

- Maintenance advice is grounded, not inferred solely from timbre.

REVIEW CHECKLIST:

- Actual output inspected.
- Sources appear in output.

DEFINITION OF DONE:

- Grounded maintenance output passes guardrail tests.

BLOCKER CONDITIONS:

- RAG or LLM layer is blocked.

TASK-09 RESULT:

- Created `src/agents/maintenance_agent.py` and `tests/test_maintenance_agent.py`.
- Updated `src/agents/__init__.py` to expose the grounded maintenance agent interface.
- Implemented structured technician output combining Structured Health Context, guarded explanation, and retrieval response.
- Output separates observed ML evidence, technician explanation, retrieved maintenance guidance, recommendation, and limitations.
- Recommendation is available only when retrieved source evidence is available.
- Recommendation citations are validated against retrieved source IDs.
- Missing retrieval evidence returns `safe_unavailable` instead of invented maintenance advice.
- Smoke output: `D:\PDM_Data\MIMII\processed\grounded_maintenance_output_fan_id_00_minus6dB_task09.json`.
- Smoke result: `source_grounded`, one retrieved fixture source, citation `task09_fixture_fan_inspection`, no forbidden text hits, generation time `0.000860s`.
- Production maintenance documents remain unavailable; the smoke source is an approved local fixture, not a production manual.
- Tests: `tests/test_maintenance_agent.py` ran 5 tests OK; `tests/test_rag_grounding.py` ran 4 tests OK; `tests/test_llm_guardrails.py` ran 4 tests OK; `tests/test_context_schema.py` ran 5 tests OK; `tests/test_timbre_difference.py` ran 7 tests OK.

### TASK 10

TASK ID: `TASK-10`

TITLE: End-To-End Fan MVP Orchestrator

STATUS: `DONE`

GOAL:

- Provide one bounded command/API that runs the Fan MVP flow from audio event to final technician output.

WHY:

- The system must preserve same-event identity across all components.

DEPENDENCIES:

- `TASK-04`
- `TASK-06`
- `TASK-09`

PRIMARY SKILL: `$scientific-implementer`

FILES TO INSPECT:

- Expert A code.
- Expert B code.
- Context translator.
- Agents/RAG code.

FILES TO CREATE:

- `scripts/run_end_to_end_demo.py`
- End-to-end tests.

FILES TO MODIFY:

- `project_state.json`

IMPLEMENTATION:

- Load one audio event.
- Run Expert A.
- Conditionally run Expert B.
- Build context.
- Retrieve maintenance evidence.
- Generate technician output.
- Save one JSON artifact.

UNIT TESTS:

- Event identity preserved.
- Conditional Expert B behavior.
- No RUL/root-cause leakage.

SMOKE TEST:

- One abnormal Fan id_00 event.

RUNTIME GATE:

- One-sample smoke first.
- Three-sample timing before any larger demo.

SCIENTIFIC GUARDRAILS:

- End-to-end output does not exceed component evidence.

REVIEW CHECKLIST:

- Actual JSON inspected.
- Component timings recorded.
- Artifact path is machine/SNR-specific.

DEFINITION OF DONE:

- One end-to-end Fan MVP output exists and passes tests.

BLOCKER CONDITIONS:

- Any required upstream component is blocked.

TASK-10 RESULT:

- Created `scripts/run_end_to_end_demo.py` and `tests/test_end_to_end_orchestrator.py`.
- Implemented one bounded Fan MVP command that runs Expert A, conditionally runs Expert B on the same audio event, builds Structured Health Context, runs guarded explanation, retrieves maintenance evidence, and generates grounded technician output.
- Added end-to-end validation for event identity, Expert A anomaly gating before Expert B, retrieved-source citation grounding, and forbidden wording.
- Smoke output: `D:\PDM_Data\MIMII\processed\end_to_end_fan_id_00_minus6dB_task10.json`.
- Smoke input: `D:\PDM_Data\MIMII\fan_minus6dB\id_00\abnormal\00000002.wav`.
- Smoke result: event_id `fan_id_00_minus6dB_00000002`, Expert A is_anomaly=True, Expert B selected 30 references, maintenance mode `source_grounded`, citation `task10_fixture_fan_inspection`.
- Component timings were recorded; total one-sample runtime `15.792862s`.
- The smoke uses an approved local fixture maintenance source, not a production manual, because production approved documents remain absent.
- Tests: `tests/test_end_to_end_orchestrator.py` ran 4 tests OK; maintenance/RAG/LLM/context/Expert B regression tests all passed.

### TASK 11

TASK ID: `TASK-11`

TITLE: Dashboard MVP

STATUS: `DONE`

GOAL:

- Build a minimal dashboard to display Fan MVP evidence and limitations.

WHY:

- Academic/demo presentation needs technician-facing visibility.

DEPENDENCIES:

- `TASK-10`.

PRIMARY SKILL: `$scientific-implementer`

FILES TO INSPECT:

- `app/`
- End-to-end output JSON.

FILES TO CREATE:

- `app/dashboard.py`
- Minimal dashboard tests or smoke script.

FILES TO MODIFY:

- `project_state.json`

IMPLEMENTATION:

- Load an end-to-end JSON artifact.
- Display machine metadata, Expert A evidence, Expert B rank scores, explanation, retrieved sources, and limitations.

UNIT TESTS:

- Import/render helper tests if feasible.

SMOKE TEST:

- Start local dashboard or render one static output.

RUNTIME GATE:

- Dashboard must not trigger training or full dataset jobs.

SCIENTIFIC GUARDRAILS:

- UI must not hide limitations or claim diagnosis/RUL.

REVIEW CHECKLIST:

- Page inspected.
- Text does not overstate claims.

DEFINITION OF DONE:

- Dashboard MVP displays one Fan output.

BLOCKER CONDITIONS:

- Dashboard dependency unavailable or app cannot run locally.

TASK-11 RESULT:

- Created `app/dashboard.py` and `tests/test_dashboard.py`.
- Implemented a static standalone HTML dashboard renderer over the TASK-10 end-to-end JSON artifact.
- Dashboard displays event metadata, Expert A evidence, Expert B timbre ranks, explanation, retrieved source evidence, recommendation, and limitations.
- Dashboard explicitly marks fixture maintenance source mode when production manuals are absent.
- Smoke output: `D:\PDM_Data\MIMII\processed\dashboard_fan_id_00_minus6dB_task11.html`.
- Smoke result: HTML size 7561 bytes; required sections and citation `task10_fixture_fan_inspection` were present; forbidden text hits were empty.
- Tests: `tests/test_dashboard.py` ran 3 tests OK; end-to-end/maintenance/RAG/LLM/context/Expert B regression tests all passed.
- No training, dataset processing, model scoring, or Expert B recomputation is triggered by dashboard rendering.

### TASK 12

TASK ID: `TASK-12`

TITLE: Fan MVP Final Evaluation And Academic Report

STATUS: `DONE`

GOAL:

- Produce the final Fan id_00 MVP evidence package and academic claims report.

WHY:

- The project needs a defensible record of what is supported and what is not.

DEPENDENCIES:

- `TASK-10`
- `TASK-11`

PRIMARY SKILL: `$project-architect`

FILES TO INSPECT:

- SNR summary artifacts.
- Expert B qualitative outputs.
- End-to-end JSON.
- Dashboard output.
- Reports/docs.

FILES TO CREATE:

- `docs/fan_mvp_final_report.md`
- `docs/academic_claims.md`

FILES TO MODIFY:

- `project_state.json`

IMPLEMENTATION:

- Summarize verified Expert A/SNR results.
- Summarize Expert B qualitative limitations.
- Summarize LLM/RAG/dashboard status.
- Produce supported/unsupported claim table.

UNIT TESTS:

- Not required unless report helper code is added.

SMOKE TEST:

- Inspect referenced artifacts exist.

RUNTIME GATE:

- No model/data processing.

SCIENTIFIC GUARDRAILS:

- Expert B accuracy is not claimed without labels.
- Low SNR is "strongly indicated" limitation, not only limitation.
- No RUL or root-cause diagnosis.

REVIEW CHECKLIST:

- Every numeric result traces to artifact/report.
- Unsupported claims are explicit.

DEFINITION OF DONE:

- Fan MVP report is complete and project state records Fan MVP completion.

BLOCKER CONDITIONS:

- Required Fan MVP artifacts are missing.

TASK-12 RESULT:

- Created `docs/fan_mvp_final_report.md`.
- Created `docs/academic_claims.md`.
- Inspected required Fan MVP artifacts: SNR summary, Expert B smoke, Structured Health Context, guarded explanation, RAG retrieval smoke, maintenance output, end-to-end JSON, and dashboard HTML.
- Summarized verified Expert A/SNR results and bounded Expert B qualitative evidence.
- Recorded LLM/RAG/maintenance/dashboard status and production-source limitations.
- Produced a supported/unsupported academic claims register with paper facts, repository facts, project decisions, inferences, and unknowns separated.
- No model training, dataset preprocessing, Expert B indexing, or scoring was run.
- Fan MVP evidence package is complete for one bounded Fan `id_00` same-audio path through dashboard.
- Next task `TASK-13` is blocked because `D:\PDM_Data\MIMII\pump\id_00` is not present.

### TASK 13

TASK ID: `TASK-13`

TITLE: Pump Generalization

STATUS: `BLOCKED_DATA_MISSING`

GOAL:

- Extend and evaluate the same architecture on Pump data with machine-specific artifacts.

WHY:

- Generalization must be demonstrated per machine, not assumed.

DEPENDENCIES:

- `TASK-12`
- Pump data staged and verified.

PRIMARY SKILL: `$project-architect`

FILES TO INSPECT:

- Data staging layout.
- Config path strategy.
- Expert A/B artifact naming.

FILES TO CREATE:

- Pump evaluation notes/artifacts.

FILES TO MODIFY:

- Machine-aware config/scripts only after bounded plan.
- `project_state.json`

IMPLEMENTATION:

- Verify pump data metadata.
- Run machine-specific Expert A baseline only after timing gates.
- Build pump Expert B reference index only after timing gates.
- Run bounded end-to-end pump smoke.

UNIT TESTS:

- Machine metadata/path tests.

SMOKE TEST:

- One pump normal/abnormal path check and one bounded smoke after artifacts exist.

RUNTIME GATE:

- Per-machine one-sample and three-sample timing before larger runs.

SCIENTIFIC GUARDRAILS:

- No universal-model claim.
- Report pump separately.

REVIEW CHECKLIST:

- Pump artifacts cannot overwrite Fan artifacts.
- Claims are per-machine.

DEFINITION OF DONE:

- Pump bounded results exist or task is blocked by missing data.

BLOCKER CONDITIONS:

- Pump data unavailable.

CURRENT BLOCKER:

- `D:\PDM_Data\MIMII\pump\id_00` is not present as of TASK-12 review, so no Pump metadata, Expert A baseline, Expert B reference index, or end-to-end Pump smoke can be run.

### TASK 14

TASK ID: `TASK-14`

TITLE: Valve Generalization

STATUS: `PLANNED`

GOAL:

- Extend and evaluate the same architecture on Valve data with machine-specific artifacts.

WHY:

- Valve behavior must be measured independently.

DEPENDENCIES:

- `TASK-12`
- Valve data staged and verified.

PRIMARY SKILL: `$project-architect`

FILES TO INSPECT:

- Data staging layout.
- Config path strategy.
- Expert A/B artifact naming.

FILES TO CREATE:

- Valve evaluation notes/artifacts.

FILES TO MODIFY:

- Machine-aware config/scripts only after bounded plan.
- `project_state.json`

IMPLEMENTATION:

- Verify valve data metadata.
- Run machine-specific Expert A baseline only after timing gates.
- Build valve Expert B reference index only after timing gates.
- Run bounded end-to-end valve smoke.

UNIT TESTS:

- Machine metadata/path tests.

SMOKE TEST:

- One valve normal/abnormal path check and one bounded smoke after artifacts exist.

RUNTIME GATE:

- Per-machine one-sample and three-sample timing before larger runs.

SCIENTIFIC GUARDRAILS:

- Report valve separately.
- No universal threshold claim.

REVIEW CHECKLIST:

- Valve artifacts cannot overwrite Fan/Pump artifacts.

DEFINITION OF DONE:

- Valve bounded results exist or task is blocked by missing data.

BLOCKER CONDITIONS:

- Valve data unavailable.

### TASK 15

TASK ID: `TASK-15`

TITLE: Slide Rail Generalization

STATUS: `PLANNED`

GOAL:

- Extend and evaluate the same architecture on Slide Rail data with machine-specific artifacts.

WHY:

- Slide Rail is a target generalization machine and must be measured separately.

DEPENDENCIES:

- `TASK-12`
- Slide Rail data staged and verified.

PRIMARY SKILL: `$project-architect`

FILES TO INSPECT:

- Data staging layout.
- Config path strategy.
- Expert A/B artifact naming.

FILES TO CREATE:

- Slide Rail evaluation notes/artifacts.

FILES TO MODIFY:

- Machine-aware config/scripts only after bounded plan.
- `project_state.json`

IMPLEMENTATION:

- Verify slide rail data metadata.
- Run machine-specific Expert A baseline only after timing gates.
- Build slide rail Expert B reference index only after timing gates.
- Run bounded end-to-end slide rail smoke.

UNIT TESTS:

- Machine metadata/path tests.

SMOKE TEST:

- One slide rail normal/abnormal path check and one bounded smoke after artifacts exist.

RUNTIME GATE:

- Per-machine one-sample and three-sample timing before larger runs.

SCIENTIFIC GUARDRAILS:

- Report slide rail separately.
- No universal model claim.

REVIEW CHECKLIST:

- Slide rail artifacts cannot overwrite other machine artifacts.

DEFINITION OF DONE:

- Slide Rail bounded results exist or task is blocked by missing data.

BLOCKER CONDITIONS:

- Slide Rail data unavailable.

### TASK 16

TASK ID: `TASK-16`

TITLE: Cross-Machine Comparison

STATUS: `PLANNED`

GOAL:

- Compare Fan, Pump, Valve, and Slide Rail results without claiming unsupported universal generalization.

WHY:

- Academic reporting needs cross-machine synthesis after per-machine runs.

DEPENDENCIES:

- `TASK-13`
- `TASK-14`
- `TASK-15`

PRIMARY SKILL: `$project-architect`

FILES TO INSPECT:

- Per-machine reports/artifacts.
- Fan MVP report.

FILES TO CREATE:

- `docs/cross_machine_comparison.md`

FILES TO MODIFY:

- `project_state.json`

IMPLEMENTATION:

- Compare per-machine Expert A metrics, Expert B qualitative behavior, runtime, and limitations.
- Separate data availability from model performance.

UNIT TESTS:

- Not required unless helper code is added.

SMOKE TEST:

- Verify referenced per-machine artifacts exist.

RUNTIME GATE:

- No model/data processing.

SCIENTIFIC GUARDRAILS:

- Do not claim one universal model unless explicitly evaluated.
- Do not hide failed/missing machine results.

REVIEW CHECKLIST:

- Each claim points to per-machine evidence.

DEFINITION OF DONE:

- Cross-machine comparison document is complete.

BLOCKER CONDITIONS:

- Two or more required machine tasks are blocked by missing data.

### TASK 17

TASK ID: `TASK-17`

TITLE: MIMII DG Domain Robustness

STATUS: `PLANNED`

GOAL:

- Design and run a bounded domain-robustness evaluation using MIMII DG if available.

WHY:

- Domain shift robustness is a separate scientific question from Fan MVP integration.

DEPENDENCIES:

- `TASK-12`
- MIMII DG data staged.

PRIMARY SKILL: `$paper-forensics`

FILES TO INSPECT:

- MIMII DG official docs/assets.
- `docs/EXPERT_B_NISHIDA_METHOD_SPEC.md`
- Current machine-aware pipelines.

FILES TO CREATE:

- `docs/mimii_dg_robustness_protocol.md`
- Optional bounded evaluation script/artifacts after protocol approval.

FILES TO MODIFY:

- Machine/domain metadata code only after protocol approval.
- `project_state.json`

IMPLEMENTATION:

- Re-check primary dataset/paper requirements.
- Define source/target domain handling.
- Run one-section bounded evaluation only after timing gates.

UNIT TESTS:

- Domain metadata and reference filtering tests.

SMOKE TEST:

- One source-domain and one target-domain sample metadata check.

RUNTIME GATE:

- One-sample and three-sample timing before any domain batch.

SCIENTIFIC GUARDRAILS:

- Do not claim Nishida-equivalent timbre accuracy without labels.
- Do not use domain labels at inference if protocol forbids them.

REVIEW CHECKLIST:

- Dataset/paper facts separated from project choices.
- Robustness claims are bounded to executed protocol.

DEFINITION OF DONE:

- Protocol and bounded robustness result exist, or task is blocked by missing data/labels.

BLOCKER CONDITIONS:

- MIMII DG data unavailable.
- Required labels/assets unavailable for intended claim.

### TASK 18

TASK ID: `TASK-18`

TITLE: Optional MIMII-Agent-Inspired Evaluation

STATUS: `OPTIONAL_PLANNED`

GOAL:

- Evaluate relative robustness using approved synthetic anomaly transformations inspired by MIMII-Agent.

WHY:

- This is an optional extension, not required for the Fan MVP.

DEPENDENCIES:

- `TASK-12`
- Explicit Yosef approval to activate optional scope.

PRIMARY SKILL: `$paper-forensics`

FILES TO INSPECT:

- MIMII-Agent paper/assets.
- Current evaluation artifacts.

FILES TO CREATE:

- `docs/mimii_agent_inspired_evaluation_plan.md`
- Optional bounded transform/evaluation scripts after approval.

FILES TO MODIFY:

- `project_state.json`

IMPLEMENTATION:

- Inspect primary/official MIMII-Agent sources.
- Define approved audio transformations.
- Run bounded synthetic evaluation only if scientifically defensible.

UNIT TESTS:

- Transformation provenance and no-runtime-diagnosis guardrails.

SMOKE TEST:

- One transformation on one normal sample after approval.

RUNTIME GATE:

- One-sample and three-sample timing before synthetic batches.

SCIENTIFIC GUARDRAILS:

- Synthetic anomalies do not become physical-fault labels.
- Do not claim automatic model improvement.

REVIEW CHECKLIST:

- Optional nature and limits are explicit.

DEFINITION OF DONE:

- Optional evaluation plan/result exists or scope remains inactive.

BLOCKER CONDITIONS:

- Yosef does not activate optional scope.
- Primary source details or approved transformations are insufficient.

## Dependency Check

The task graph is linear with limited fan-out:

```text
TASK-00 -> TASK-00B -> TASK-02 -> TASK-03 -> TASK-04 -> TASK-05
TASK-04 -> TASK-06 -> TASK-07
TASK-06 -> TASK-08
TASK-07 + TASK-08 -> TASK-09
TASK-04 + TASK-06 + TASK-09 -> TASK-10 -> TASK-11 -> TASK-12
TASK-12 -> TASK-13
TASK-12 -> TASK-14
TASK-12 -> TASK-15
TASK-13 + TASK-14 + TASK-15 -> TASK-16
TASK-12 -> TASK-17
TASK-12 + explicit optional approval -> TASK-18
```

No task depends on a later task. Fan MVP is completed before multi-machine
generalization. Domain robustness and optional MIMII-Agent-inspired work are
deferred until after the Fan MVP.

## Real Intelligence Completion Addendum

Plan version: `real_intelligence_completion_v1_2026-07-09`

Status: `COMPLETE`

Scope:

- Fan `id_00` `minus6dB` bounded MVP only.
- Same-machine, same-audio Expert A -> Expert B architecture.
- Approved public Fan maintenance corpus.
- Live Gemini explanation and maintenance generation over structured context
  and retrieved source chunks.
- Static evidence dashboard.

Completed tasks:

| Task | Status | Evidence |
|---|---|---|
| `TASK-AI-01` Gemini secret/provider preflight | DONE | `src/agents/gemini_provider.py`, secure env-based config, tests |
| `TASK-AI-02` live Gemini text generator | DONE | live Gemini explanation smoke, guardrail tests |
| `TASK-RAG-01` approved public Fan corpus | DONE | `data/manuals/approved_sources.json`, `docs/RAG_SOURCE_REGISTER.md` |
| `TASK-RAG-02` section-aware chunking | DONE | `docs/RAG_CORPUS_CHUNKING_REVIEW.md`, RAG tests |
| `TASK-RAG-03` Gemini semantic retriever | DONE | external semantic embedding index, semantic retriever tests |
| `TASK-RAG-04` retrieval evaluation set | DONE | `data/manuals/fan_maintenance_retrieval_eval_v1.json` |
| `TASK-RAG-05` retrieval comparison/selection | DONE | `docs/RAG_RETRIEVAL_EVALUATION.md`; semantic selected |
| `TASK-MAINT-01` Gemini Maintenance Agent V2 | DONE | live citation-valid maintenance smoke, tests |
| `TASK-CTX-02` Structured Health Context v0.2 | DONE | v0.2 schema/tests/sample artifact |
| `TASK-FAN-13` one-event real Gemini + RAG smoke | DONE | `D:\PDM_Data\MIMII\processed\real_intelligence_end_to_end_fan_id_00_minus6dB_task_fan_13.json` |
| `TASK-FAN-14` bounded Fan system evaluation | DONE | `docs/FAN_SYSTEM_EVALUATION.md`, external 20-event evaluation artifact |
| `TASK-DASH-02` updated static evidence dashboard | DONE | `D:\PDM_Data\MIMII\processed\dashboard_real_intelligence_fan_id_00_minus6dB_task_dash_02.html` |
| `FINAL-DOCS` final report and record reconciliation | DONE | `docs/FAN_REAL_INTELLIGENCE_REPORT.md`, updated records |

Final verification:

- Artifact-independent repository tests passed: 76 tests OK.
- Compileall passed for `src`, `scripts`, `tests`, and `app`.
- `project_state.json` validates as JSON.
- `git diff --check` passed.
- Secret scans found no tracked Gemini API key pattern.
- Large/generated scientific artifact guard found no tracked WAV, NumPy array,
  model weight, generated dashboard HTML, embedding index, or processed output
  artifact.

Claims enabled:

- Bounded Fan `id_00` real Gemini + selected semantic RAG integration evidence.
- Bounded 20-event Fan integration evidence.
- Source/chunk-citation-valid maintenance communication over approved public Fan
  corpus chunks.
- Structured Health Context v0.2 provenance recording.

Claims still not enabled:

- production readiness,
- production maintenance validation,
- confirmed physical root cause,
- fault probability or confidence,
- severity percentage,
- RUL or exact time-to-failure,
- Expert B quantitative direction accuracy,
- Pump, Valve, Slide Rail, cross-machine, or MIMII DG generalization.

Do not mark the following complete from this phase:

- Pump
- Valve
- Slide Rail
- Cross-Machine
- MIMII DG
- Production API
- Persistence
- Async Worker
- Docker
- Cloud Deployment

## Fan Production MVP Addendum

Plan version: `fan_production_mvp_v1_2026-07-09`

Status: `IMPLEMENTING`

Scope:

- Fan `id_00` only.
- Preserve the completed Real Intelligence phase and all Expert A/B/RAG/Gemini
  semantics.
- Move the current bounded Fan scripts toward a deployable Fan Production MVP
  architecture with API ingestion, persistence, background processing,
  API-backed dashboard, observability, and containerized local deployment.
- Do not start Pump, Valve, Slide Rail, Cross-Machine, MIMII DG, Expert B
  timbre-label research, GitHub governance synchronization, GitHub Project
  cleanup, or release-history cleanup.

Ordered productionization tasks:

| Task | Status | Evidence |
|---|---|---|
| `TASK-PROD-01` Define Fan Production Architecture | DONE | `docs/PRODUCTION_ARCHITECTURE.md` |
| `TASK-PROD-02` Extract reusable AMHI Pipeline Service | DONE | `src/application/pipeline_service.py`, `tests/test_pipeline_service.py` |
| `TASK-PROD-03` Machine-aware Artifact Registry | DONE | `src/infrastructure/artifact_registry.py`, `tests/test_artifact_registry.py` |
| `TASK-PROD-04` Audio Storage abstraction | DONE | `src/infrastructure/audio_storage.py`, `tests/test_audio_storage.py` |
| `TASK-PROD-05` Event and Result Persistence | DONE | `src/application/repositories.py`, `src/infrastructure/persistence/sqlite_repository.py`, `src/infrastructure/persistence/migrations/001_initial_postgres.sql`, `tests/test_persistence.py` |
| `TASK-PROD-06` API v1 contract | DONE | `docs/API_CONTRACT_V1.md`, `tests/test_api_contract_doc.py` |
| `TASK-PROD-07` FastAPI Fan Event API | NEXT | pending |
| `TASK-PROD-08` Asynchronous Event Processing | PLANNED | pending |
| `TASK-PROD-09` API-backed Technician Dashboard | PLANNED | pending |
| `TASK-PROD-10` Structured Logging | PLANNED | pending |
| `TASK-PROD-11` Metrics and Observability | PLANNED | pending |
| `TASK-PROD-12` Health and Readiness | PLANNED | pending |
| `TASK-PROD-13` Containerize Fan Production MVP | PLANNED | pending |
| `TASK-PROD-14` Bounded Fan Production Integration Evaluation | PLANNED | pending |
| `TASK-PROD-15` Staging Architecture and Bounded Deployment | PLANNED | pending |
| `TASK-PROD-16` Final Fan Production MVP Report | PLANNED | pending |

TASK-PROD-01 result:

- Current script-owned orchestration responsibilities were inspected and
  documented.
- The approved target is a modular monolith, not appearance-driven
  microservices.
- Required boundaries are explicit for `AMHIPipelineService`,
  `ArtifactRegistry`, `AudioStorage`, `EventRepository`,
  `AnalysisRepository`, `EventProcessingService`, API, dashboard, and
  observability.
- Dependency direction keeps the scientific core independent from FastAPI,
  persistence, and dashboard rendering.
- Future multi-machine extension is described only as conceptual registry
  expansion, not as implemented support.

Claims still not enabled by TASK-PROD-01:

- accepted production operation,
- production maintenance validation,
- confirmed physical root cause,
- probability/confidence/severity claims,
- RUL or exact time-to-failure,
- Expert B timbre-direction accuracy,
- multi-machine or domain-robustness generalization.

TASK-PROD-02 result:

- Created `src/application/pipeline_service.py` and `src/application/__init__.py`.
- Added `AMHIPipelineService.process_event(audio_reference, machine_type,
  machine_id, snr_tag, task_id=...)` for the current Fan `id_00` scope.
- Added injectable dependencies so service behavior can be unit-tested without
  loading artifacts or calling Gemini.
- Refactored `scripts/run_real_intelligence_fan_smoke.py` so the CLI path calls
  the reusable service instead of owning a second orchestration implementation.
- Added `tests/test_pipeline_service.py` for unflagged gating, flagged full
  path, same-audio identity, fallback metadata propagation, retrieval metadata
  propagation, stage timing presence, and unsupported-machine rejection.
- Runtime gate on the existing Fan reference event preserved Expert A score,
  threshold, anomaly decision, Expert B k/distance/rank_threshold/null
  directions/rank scores, Structured Health Context v0.2, semantic retriever,
  corpus version, and retrieved chunks compared with `TASK-FAN-13`.
- During the runtime gate, Gemini returned `ClientError`; the strict live run
  therefore failed as expected, and the allowed-fallback probe completed with
  deterministic fallback metadata recorded for explanation and maintenance.

Claims still not enabled by TASK-PROD-02:

- accepted production operation,
- production maintenance validation,
- confirmed physical root cause,
- probability/confidence/severity claims,
- RUL or exact time-to-failure,
- Expert B timbre-direction accuracy,
- multi-machine or domain-robustness generalization.

TASK-PROD-03 result:

- Created `src/infrastructure/artifact_registry.py` and
  `src/infrastructure/__init__.py`.
- Added `ArtifactRegistry`, `ResolvedArtifactConfig`, and
  `ArtifactNotRegisteredError`.
- Registered Fan `id_00` `minus6dB` as the active full Real Intelligence
  configuration: Expert A model/norm stats, Expert B reference index,
  Expert A bottleneck embedding metadata, `k=30`, `distance=euclidean`,
  `rank_threshold=None`, selected semantic retriever, Fan corpus version, and
  semantic embedding index path.
- Registered Fan `id_00` `0dB` and `plus6dB` only as Expert-A artifact
  configurations; they are not marked as full Real Intelligence paths.
- Integrated `AMHIPipelineService` and `scripts/run_real_intelligence_fan_smoke.py`
  with registry-based default artifact resolution.
- Added `tests/test_artifact_registry.py` covering Fan resolution,
  Expert-A-only SNRs, unsupported machines, unknown machine IDs, unregistered
  SNRs, and no silent Fan fallback.

Claims still not enabled by TASK-PROD-03:

- accepted production operation,
- production maintenance validation,
- confirmed physical root cause,
- probability/confidence/severity claims,
- RUL or exact time-to-failure,
- Expert B timbre-direction accuracy,
- Pump, Valve, Slide Rail, cross-machine, or domain-robustness generalization.

TASK-PROD-04 result:

- Created `src/infrastructure/audio_storage.py`.
- Added `AudioStorage` protocol, `AudioStorageMetadata`, `LocalAudioStorage`,
  `AudioStorageError`, `AudioNotFoundError`, and `UnsupportedAudioTypeError`.
- Exported the storage boundary from `src/infrastructure/__init__.py`.
- Integrated `AMHIPipelineService` with `AudioStorage.resolve(...)` before Expert
  A scoring, so the scientific pipeline receives the resolved local processing
  path plus storage metadata.
- Added audio storage metadata to pipeline results for both flagged and
  unflagged paths.
- Added `tests/test_audio_storage.py` for valid local WAV references, missing
  path rejection, unsupported extension rejection, metadata shape, and no-copy
  behavior.
- Updated pipeline service tests to use fake storage and avoid external-file
  dependence in CI.
- Runtime smoke resolved the real Fan reference WAV through `LocalAudioStorage`
  with `copied=False`.

Claims still not enabled by TASK-PROD-04:

- accepted production operation,
- production maintenance validation,
- confirmed physical root cause,
- probability/confidence/severity claims,
- RUL or exact time-to-failure,
- Expert B timbre-direction accuracy,
- persistence/API/async/dashboard/observability/container deployment,
- Pump, Valve, Slide Rail, cross-machine, or domain-robustness generalization.

TASK-PROD-05 result:

- Created `src/application/repositories.py` with `EventRepository` and
  `AnalysisRepository` contracts plus record dataclasses for events, analysis
  runs, and structured analysis results.
- Created `src/infrastructure/persistence/sqlite_repository.py` for local
  development and unit tests.
- Created PostgreSQL migration
  `src/infrastructure/persistence/migrations/001_initial_postgres.sql` as the
  production-oriented persistence schema target.
- Stored audio references and structured JSON payloads, not raw WAV bytes,
  NumPy arrays, embeddings, model weights, or generated scientific artifacts.
- Added persistence tests for event create/read/list, machine filtering, status
  transitions, failed event persistence, analysis run failure persistence,
  structured result round trip, file-backed reconnect survival, invalid status
  rejection, and no raw binary database columns.
- Runtime gate wrote one Fan `id_00` event/result to a file-backed SQLite
  database, closed the connection, reopened it, and retrieved the completed
  event plus Expert B `k=30`, selected semantic retriever metadata, and
  Structured Health Context v0.2 marker.

Claims still not enabled by TASK-PROD-05:

- accepted production operation,
- production maintenance validation,
- confirmed physical root cause,
- probability/confidence/severity claims,
- RUL or exact time-to-failure,
- Expert B timbre-direction accuracy,
- API/async/dashboard/observability/container deployment,
- Pump, Valve, Slide Rail, cross-machine, or domain-robustness generalization.

TASK-PROD-06 result:

- Created `docs/API_CONTRACT_V1.md`.
- Defined `/api/v1` endpoints before route implementation:
  `POST /api/v1/events`, `GET /api/v1/events/{event_id}`,
  `GET /api/v1/events`, `GET /api/v1/machines/{machine_type}/{machine_id}/events`,
  `GET /api/v1/health`, and `GET /api/v1/ready`.
- Chose canonical `multipart/form-data` WAV upload for Fan Production MVP
  ingestion, with config-gated JSON registered-reference ingestion for local
  development and unit tests only.
- Documented `202 Accepted` queued event semantics so HTTP ingestion does not
  block on the full Gemini/pipeline path.
- Documented event summary, completed/failed result shapes, error schema,
  pagination, timestamp format, health, readiness, versioning, response safety,
  and scientific guardrails.
- Added `tests/test_api_contract_doc.py` to assert required endpoints, status
  values, ingestion decision, async boundary, claim guardrails, and absence of
  a staged local dataset path leak in the contract.

Claims still not enabled by TASK-PROD-06:

- accepted production operation,
- production maintenance validation,
- confirmed physical root cause,
- probability/confidence/severity claims,
- RUL or exact time-to-failure,
- Expert B timbre-direction accuracy,
- implemented API routes,
- async processing, dashboard, observability, or container deployment,
- Pump, Valve, Slide Rail, cross-machine, or domain-robustness generalization.
