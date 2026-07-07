# Explainable Acoustic Machine Health Monitoring

## One-Paragraph Overview

This project builds an explainable acoustic condition-monitoring system for industrial machine audio. Expert A detects whether a machine sound departs from learned normal acoustic behavior. Expert B then characterizes how the same audio event differs from comparable normal sounds using timbre attributes. Later layers translate those outputs into structured evidence for cautious LLM explanation, RAG-grounded maintenance recommendations, and a dashboard.

## Problem

Anomalous sound detection can tell a technician that a clip is abnormal, but a raw anomaly score does not explain what changed in the sound or what evidence should guide inspection. This project closes that gap by combining detection, timbre-difference characterization, structured evidence, and grounded maintenance communication.

## Final Architecture

```text
Machine Audio
-> Expert A
-> Expert B
-> Structured Health Context
-> LLM + RAG
-> Dashboard
```

The active rule is same machine, same audio event: Expert B characterizes the audio event that Expert A evaluated.

## Expert A

Expert A is a normal-only convolutional autoencoder trained on MIMII fan audio. It uses Log-Mel spectrograms and reconstruction error to score acoustic departures from normal operation. A controlled three-SNR experiment is complete for Fan `id_00`.

## Expert B

Expert B is a Nishida-inspired acoustic timbre-difference expert. It compares an Expert A-flagged audio event with same-machine normal references and reports five continuous timbre rank scores: sharpness, roughness, boominess, brightness, and depth. It is an adaptation, not an exact Nishida reproduction.

## Research Papers

- MIMII Dataset: source of industrial normal/anomalous machine audio and Expert A motivation.
- Nishida et al. 2024 Timbre Difference Capturing: main basis for Expert B's normal-reference timbre comparison.
- MIMII DG: future domain-shift robustness evaluation.
- MIMII-Agent: optional future synthetic-anomaly robustness branch.

AudioCommons timbral models provide the five timbre metrics used by Expert B.

## Current Status

DONE:

- Fan `id_00` MIMII SNR data staged externally under `D:\PDM_Data\MIMII`.
- Expert A preprocessing, training, scoring, thresholding, and three-SNR evaluation.
- Expert B method forensics and initial code-level implementation.
- Expert B unit tests for rank scoring, metadata filtering, null direction policy, and JSON guardrails.

PARTIAL:

- Expert B reference indexing and same-audio smoke pipeline.
- Repository/report normalization completed as `TASK-00`.

TODO:

- Structured Health Context.
- LLM explanation agent.
- Maintenance RAG.
- End-to-end orchestrator.
- Dashboard.
- Pump, valve, and slide rail generalization.

BLOCKED:

- Expert B reference-index performance must be profiled before larger runs.
- Quantitative Expert B timbre-direction accuracy needs labels not present in the current Fan data.

## Repository Structure

```text
IOT/
|-- AGENTS.md
|-- CLAUDE.md
|-- README.md
|-- REPORT.md
|-- REPORT_PHASE1_2.md
|-- project_state.json
|-- requirements.txt
|-- .agents/skills/
|-- src/
|-- scripts/
|-- tests/
|-- docs/
|-- app/
|-- notebooks/
```

`src/` contains active Python modules. `scripts/` contains executable workflows. `tests/` contains checks. `docs/` contains method, roadmap, audit, and execution documentation. Repo-local large data and model artifact directories were removed in `TASK-00B`.

## Data Storage

Repository code lives under `D:\IOT`.

Large active data and model artifacts live under:

```text
D:\PDM_Data\MIMII
```

Do not commit large WAV files, `.npy` arrays, `.npz` generated stats, model weights, reference indexes, or smoke outputs.

The unique legacy repo-local model was preserved externally at:

```text
D:\PDM_Data\MIMII\models_store\anomaly_detector_legacy_repo_2026-06-29.pt
```

## Quick Development Notes

Fan `id_00` is the current MVP/reference machine. Interfaces must stay machine-aware so later Pump, Valve, and Slide Rail work can reuse the same architecture without mixing artifacts.

Do not run the slow Expert B 40-file reference-index job before one-file and three-file performance timing.

## Scientific Limitations

- No Remaining Useful Life prediction.
- No exact time-to-failure prediction.
- No confirmed physical root-cause diagnosis.
- Expert B quantitative direction accuracy is not validated on current Fan data.
- Current Expert B embedding is an Expert A bottleneck adaptation, not a paper encoder.

## Where To Read More

- `CLAUDE.md`
- `REPORT.md`
- `REPORT_PHASE1_2.md`
- `docs/MASTER_EXECUTION_PLAN.md`
- `docs/REPOSITORY_AUDIT.md`
