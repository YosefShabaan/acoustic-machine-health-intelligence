# Repository Audit

Generated after TASK-00B local artifact reconciliation and Git baseline preparation. This audit records the cleaned repository state. No full audio processing, model training, or Expert B reference-index job was run.

## Current Repository State

- Repo-local `data/` and `models_store/` large artifact directories have been removed.
- Active large MIMII raw data, processed arrays, SNR summaries, and trained model weights live under `D:\PDM_Data\MIMII`.
- The unique legacy repo-local model was moved to `D:\PDM_Data\MIMII\models_store\anomaly_detector_legacy_repo_2026-06-29.pt`.
- `TASK-02` remains the next implementation task; it was not started.

## Classification Counts

| CLASSIFICATION | COUNT |
|---|---:|
| ACTIVE_CODE | 13 |
| ACTIVE_DOCUMENTATION | 11 |
| ACTIVE_SUPPORT | 11 |
| ARCHIVED_SUPERSEDED | 1 |
| TEST_CODE | 1 |
| TODO_PLACEHOLDER | 2 |

## Inventory Summary

- Total audited files: 39
- Source/script files: 13
- Test files: 1
- Documentation files: 11
- Local large artifact files (.wav, .npy, .npz, .pt, .pth): 0
- Unknown files requiring later review: 0

## TASK-00B Artifact Reconciliation

| GROUP | REPO PATH | EXTERNAL PATH | FILE COUNT | SIZE | CLASSIFICATION | ACTION |
|---|---|---|---:|---:|---|---|
| MIMII Fan id_00 raw WAV mirror | `D:\IOT\data\raw\mimii\fan\id_00` | `D:\PDM_Data\MIMII\fan_minus6dB\id_00` | 1418 | 3,630,193,440 bytes | VERIFIED_DUPLICATE_EXTERNAL | Removed repo-local duplicate. |
| Expert A legacy unsuffixed processed arrays | `D:\IOT\data\processed` | `D:\PDM_Data\MIMII\processed\*_minus6dB.*` | 4 | 36,060,996 bytes | VERIFIED_DUPLICATE_EXTERNAL | Removed repo-local duplicate arrays/stat file and placeholder tree. |
| Legacy unsuffixed Expert A model | `D:\IOT\models_store\anomaly_detector.pt` | `D:\PDM_Data\MIMII\models_store\anomaly_detector_legacy_repo_2026-06-29.pt` | 1 | 13,108,435 bytes | UNIQUE_LOCAL_ARTIFACT | Moved externally without overwrite; hash/mtime preserved. |

Detailed evidence is in `docs/LOCAL_ARTIFACT_RECONCILIATION.md`.

## Current File Inventory

| PATH | CLASSIFICATION | DESCRIPTION | WHY / ROLE | RISK | KEEP | HISTORICAL | TODO | REWRITTEN | LOCAL ARTIFACT | ACTIVE RUNTIME | ACTION |
|---|---|---|---|---|---|---|---|---|---|---|---|
| .agents\skills\paper-forensics\agents\openai.yaml | ACTIVE_SUPPORT | Repository support, routing, dependency, package, or skill metadata. | Used by tooling, dependency install, or workflow. | Low to Medium | YES | NO | NO | NO | NO | NO | Keep in cleaned repository. |
| .agents\skills\paper-forensics\SKILL.md | ACTIVE_SUPPORT | Repository support, routing, dependency, package, or skill metadata. | Used by tooling, dependency install, or workflow. | Low to Medium | YES | NO | NO | NO | NO | NO | Keep in cleaned repository. |
| .agents\skills\performance-forensics\agents\openai.yaml | ACTIVE_SUPPORT | Repository support, routing, dependency, package, or skill metadata. | Used by tooling, dependency install, or workflow. | Low to Medium | YES | NO | NO | NO | NO | NO | Keep in cleaned repository. |
| .agents\skills\performance-forensics\SKILL.md | ACTIVE_SUPPORT | Repository support, routing, dependency, package, or skill metadata. | Used by tooling, dependency install, or workflow. | Low to Medium | YES | NO | NO | NO | NO | NO | Keep in cleaned repository. |
| .agents\skills\project-architect\agents\openai.yaml | ACTIVE_SUPPORT | Repository support, routing, dependency, package, or skill metadata. | Used by tooling, dependency install, or workflow. | Low to Medium | YES | NO | NO | NO | NO | NO | Keep in cleaned repository. |
| .agents\skills\project-architect\SKILL.md | ACTIVE_SUPPORT | Repository support, routing, dependency, package, or skill metadata. | Used by tooling, dependency install, or workflow. | Low to Medium | YES | NO | NO | NO | NO | NO | Keep in cleaned repository. |
| .agents\skills\scientific-implementer\agents\openai.yaml | ACTIVE_SUPPORT | Repository support, routing, dependency, package, or skill metadata. | Used by tooling, dependency install, or workflow. | Low to Medium | YES | NO | NO | NO | NO | NO | Keep in cleaned repository. |
| .agents\skills\scientific-implementer\SKILL.md | ACTIVE_SUPPORT | Repository support, routing, dependency, package, or skill metadata. | Used by tooling, dependency install, or workflow. | Low to Medium | YES | NO | NO | NO | NO | NO | Keep in cleaned repository. |
| .gitignore | ACTIVE_SUPPORT | Repository support, routing, dependency, package, or skill metadata. | Used by tooling, dependency install, or workflow. | Low to Medium | YES | NO | NO | DONE | NO | NO | Keep in cleaned repository. |
| AGENTS.md | ACTIVE_DOCUMENTATION | Current project, method, audit, report, roadmap, reconciliation, or verified historical report. | Read by project workflow and human reviewers. | High for claims and execution context | YES | NO | NO | NO | NO | NO | Keep synchronized with project_state and task log. |
| app\.gitkeep | TODO_PLACEHOLDER | Empty placeholder for future app/notebook area. | Directory reservation only. | Low | YES | NO | YES | NO | NO | NO | Keep only until real implementation exists. |
| CLAUDE.md | ACTIVE_DOCUMENTATION | Current project, method, audit, report, roadmap, reconciliation, or verified historical report. | Read by project workflow and human reviewers. | High for claims and execution context | YES | NO | NO | DONE | NO | NO | Keep synchronized with project_state and task log. |
| docs\archive\CLAUDE_superseded_draft_2026-07-06.md | ARCHIVED_SUPERSEDED | Historical/superseded context kept for traceability. | Not active source of truth. | Low if clearly labeled | YES | YES | NO | NO | NO | NO | Do not treat as active architecture. |
| docs\EXPERT_B_NISHIDA_METHOD_SPEC.md | ACTIVE_DOCUMENTATION | Current project, method, audit, report, roadmap, reconciliation, or verified historical report. | Read by project workflow and human reviewers. | High for claims and execution context | YES | NO | NO | NO | NO | NO | Keep synchronized with project_state and task log. |
| docs\LOCAL_ARTIFACT_RECONCILIATION.md | ACTIVE_DOCUMENTATION | Current project, method, audit, report, roadmap, reconciliation, or verified historical report. | Read by project workflow and human reviewers. | High for claims and execution context | YES | NO | NO | DONE | NO | NO | Keep synchronized with project_state and task log. |
| docs\MASTER_EXECUTION_PLAN.md | ACTIVE_DOCUMENTATION | Current project, method, audit, report, roadmap, reconciliation, or verified historical report. | Read by project workflow and human reviewers. | High for claims and execution context | YES | NO | NO | DONE | NO | NO | Keep synchronized with project_state and task log. |
| docs\MASTER_PROJECT_ROADMAP.md | ACTIVE_DOCUMENTATION | Current project, method, audit, report, roadmap, reconciliation, or verified historical report. | Read by project workflow and human reviewers. | High for claims and execution context | YES | NO | NO | NO | NO | NO | Keep synchronized with project_state and task log. |
| docs\REPOSITORY_AUDIT.md | ACTIVE_DOCUMENTATION | Current project, method, audit, report, roadmap, reconciliation, or verified historical report. | Read by project workflow and human reviewers. | High for claims and execution context | YES | NO | NO | DONE | NO | NO | Keep synchronized with project_state and task log. |
| docs\TASK_EXECUTION_LOG.md | ACTIVE_DOCUMENTATION | Current project, method, audit, report, roadmap, reconciliation, or verified historical report. | Read by project workflow and human reviewers. | High for claims and execution context | YES | NO | NO | DONE | NO | NO | Keep synchronized with project_state and task log. |
| notebooks\.gitkeep | TODO_PLACEHOLDER | Empty placeholder for future app/notebook area. | Directory reservation only. | Low | YES | NO | YES | NO | NO | NO | Keep only until real implementation exists. |
| project_state.json | ACTIVE_SUPPORT | Machine-readable project scheduler/state file. | Controls continuation workflow and next task. | High for execution order | YES | NO | NO | DONE | NO | NO | Validate with json.tool after edits. |
| README.md | ACTIVE_DOCUMENTATION | Current project, method, audit, report, roadmap, reconciliation, or verified historical report. | Read by project workflow and human reviewers. | High for claims and execution context | YES | NO | NO | DONE | NO | NO | Keep synchronized with project_state and task log. |
| REPORT.md | ACTIVE_DOCUMENTATION | Current project, method, audit, report, roadmap, reconciliation, or verified historical report. | Read by project workflow and human reviewers. | High for claims and execution context | YES | NO | NO | DONE | NO | NO | Keep synchronized with project_state and task log. |
| REPORT_PHASE1_2.md | ACTIVE_DOCUMENTATION | Current project, method, audit, report, roadmap, reconciliation, or verified historical report. | Read by project workflow and human reviewers. | High for claims and execution context | YES | NO | NO | NO | NO | NO | Keep synchronized with project_state and task log. |
| requirements.txt | ACTIVE_SUPPORT | Repository support, routing, dependency, package, or skill metadata. | Used by tooling, dependency install, or workflow. | Low to Medium | YES | NO | NO | DONE | NO | NO | Keep in cleaned repository. |
| scripts\build_timbre_reference_index.py | ACTIVE_CODE | Bounded executable script for experiments, Expert A/SNR, or Expert B indexing/smoke. | Run manually by project workflow. | High for runtime/scientific output | YES | NO | NO | NO | NO | YES | Keep; require runtime gates before expensive data work. |
| scripts\run_expert_b_smoke.py | ACTIVE_CODE | Bounded executable script for experiments, Expert A/SNR, or Expert B indexing/smoke. | Run manually by project workflow. | High for runtime/scientific output | YES | NO | NO | NO | NO | YES | Keep; require runtime gates before expensive data work. |
| scripts\run_snr_experiments.py | ACTIVE_CODE | Bounded executable script for experiments, Expert A/SNR, or Expert B indexing/smoke. | Run manually by project workflow. | High for runtime/scientific output | YES | NO | NO | NO | NO | YES | Keep; require runtime gates before expensive data work. |
| scripts\snr_stage1.py | ACTIVE_CODE | Bounded executable script for experiments, Expert A/SNR, or Expert B indexing/smoke. | Run manually by project workflow. | High for runtime/scientific output | YES | NO | NO | NO | NO | YES | Keep; require runtime gates before expensive data work. |
| src\__init__.py | ACTIVE_CODE | Active Python package code for config, data loading, Expert A/B, and utilities. | Imported by scripts/tests or intended runtime. | High for behavior | YES | NO | NO | NO | NO | YES | Keep under active review and tests. |
| src\agents\__init__.py | ACTIVE_CODE | Active Python package code for config, data loading, Expert A/B, and utilities. | Imported by scripts/tests or intended runtime. | High for behavior | YES | NO | NO | NO | NO | YES | Keep under active review and tests. |
| src\config.py | ACTIVE_CODE | Active Python package code for config, data loading, Expert A/B, and utilities. | Imported by scripts/tests or intended runtime. | High for behavior | YES | NO | NO | DONE | NO | YES | Keep under active review and tests. |
| src\data_loader.py | ACTIVE_CODE | Active Python package code for config, data loading, Expert A/B, and utilities. | Imported by scripts/tests or intended runtime. | High for behavior | YES | NO | NO | NO | NO | YES | Keep under active review and tests. |
| src\models\__init__.py | ACTIVE_CODE | Active Python package code for config, data loading, Expert A/B, and utilities. | Imported by scripts/tests or intended runtime. | High for behavior | YES | NO | NO | NO | NO | YES | Keep under active review and tests. |
| src\models\anomaly_detector.py | ACTIVE_CODE | Active Python package code for config, data loading, Expert A/B, and utilities. | Imported by scripts/tests or intended runtime. | High for behavior | YES | NO | NO | NO | NO | YES | Keep under active review and tests. |
| src\models\timbre_difference.py | ACTIVE_CODE | Active Python package code for config, data loading, Expert A/B, and utilities. | Imported by scripts/tests or intended runtime. | High for behavior | YES | NO | NO | NO | NO | YES | Keep under active review and tests. |
| src\utils\__init__.py | ACTIVE_CODE | Active Python package code for config, data loading, Expert A/B, and utilities. | Imported by scripts/tests or intended runtime. | High for behavior | YES | NO | NO | NO | NO | YES | Keep under active review and tests. |
| src\utils\audio_reference_index.py | ACTIVE_CODE | Active Python package code for config, data loading, Expert A/B, and utilities. | Imported by scripts/tests or intended runtime. | High for behavior | YES | NO | NO | NO | NO | YES | Keep under active review and tests. |
| tests\test_timbre_difference.py | TEST_CODE | Automated test code. | Used to validate active behavior. | Medium | YES | NO | NO | NO | NO | NO | Keep and expand as implementation matures. |
