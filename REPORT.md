# 1. Project Title

Explainable Multi-Expert Acoustic Machine Health Monitoring Using Anomalous Sound Detection and Timbre Difference Characterization

# 2. Executive Summary

This repository implements the foundation of an explainable acoustic machine health monitoring system. The current MVP uses MIMII Fan `id_00` audio. Expert A is a normal-only convolutional autoencoder that detects anomalous machine sounds by reconstruction error. Expert B is a Nishida-inspired acoustic timbre-difference component that is intended to characterize how the same Expert A-evaluated audio differs from similar normal operation.

VERIFIED RESULT: Expert A and the controlled SNR experiment are complete for Fan `id_00`. AUC improves from `0.6142` at `-6 dB` to `0.8306` at `0 dB` and `0.9980` at `+6 dB`.

IMPLEMENTED BUT UNVERIFIED: Expert B code and unit tests exist, but Expert B is not verified end-to-end because the reference-index build has a known performance blocker.

PLANNED: Structured Health Context, LLM explanation, RAG maintenance grounding, orchestration, dashboard, multi-machine generalization, and domain robustness.

BLOCKED: Expert B runtime profiling is the next technical blocker. Quantitative Expert B timbre-direction accuracy is blocked by missing five-attribute labels in the current Fan data.

# 3. Problem Statement

Industrial anomalous sound detection often returns only a class or score:

```text
normal / anomalous
anomaly_score
threshold
```

That is useful to an ML engineer but incomplete for maintenance work. A technician needs to know what changed acoustically, how the current sound compares with normal operation, and which evidence supports any inspection recommendation. This project addresses the interpretation gap between anomaly detection and technician-facing maintenance context.

# 4. Project Objectives

Primary objectives:

- Detect anomalous acoustic behavior from industrial machine audio.
- Characterize the acoustic/timbre difference of the same anomalous audio event.
- Preserve evidence in a structured, machine-aware context.
- Generate cautious technician-facing explanations.
- Ground maintenance recommendations in approved retrieval sources.
- Display evidence and limitations in a dashboard.

Secondary objectives:

- Keep Fan `id_00` as the reference MVP.
- Preserve machine-aware interfaces for Pump, Valve, and Slide Rail.
- Evaluate SNR sensitivity and later domain shift.
- Avoid unsupported RUL, root-cause, or confidence claims.

# 5. Scope

IN SCOPE:

- Acoustic condition monitoring.
- Anomaly detection.
- Acoustic/timbre characterization.
- Structured Health Context.
- LLM explanation over structured evidence.
- RAG-grounded maintenance recommendations.
- Dashboard.
- Multi-machine generalization after Fan MVP.

OUT OF SCOPE:

- Remaining Useful Life prediction.
- Exact time-to-failure prediction.
- Confirmed physical root-cause diagnosis.
- PRONOSTIA runtime inference.

# 6. Architecture Evolution

OLD SUPERSEDED DESIGN:

```text
MIMII Expert A acoustic anomaly detection
+
PRONOSTIA/RUL Expert B
+
decision-level fusion
```

This was scientifically inconsistent because it combined different machines, sensor modalities, datasets, physical processes, and timelines into one apparent machine health state.

CURRENT DESIGN:

```text
same machine
same audio event
-> Expert A detects anomaly
-> Expert B characterizes acoustic/timbre difference
-> Structured Health Context
-> LLM + RAG
-> Dashboard
```

PROJECT DECISION: RUL and PRONOSTIA remain historical context only.

# 7. Final System Architecture

Runtime architecture:

```text
audio event
-> Expert A
-> if anomalous: Expert B
-> Structured Health Context
-> RAG retrieval
-> LLM explanation and technician output
-> dashboard
```

Offline architecture:

```text
normal audio
-> Expert A training
-> model and normalization artifacts

normal audio
-> Expert B reference indexing
-> embeddings + timbre values

evaluation datasets
-> per-component and end-to-end validation
```

Component responsibilities:

| Component | Input | Process | Output | Responsibility | Limitation |
|---|---|---|---|---|---|
| Expert A | Log-Mel audio features | Conv1D autoencoder reconstruction | score, threshold, boolean | Detect acoustic departure | Does not explain timbre or root cause |
| Expert B | Same audio event, Expert A result, normal references | embedding kNN + timbre rank scores | five timbre rank scores and references | Characterize acoustic difference | No direction labels without threshold; no diagnosis |
| Structured Context | Expert A/B outputs | schema translation | deterministic JSON | Preserve evidence and limits | Not implemented yet |
| LLM | structured context | guarded explanation | technician explanation | Explain evidence | Not implemented yet |
| RAG | context query + approved docs | retrieval | source evidence | Ground recommendations | Not implemented yet |
| Dashboard | end-to-end JSON | UI rendering | evidence view | Display status and limits | Not implemented yet |

# 8. Research Foundation

## 8.1 MIMII

PAPER-BACKED METHOD: The MIMII dataset provides industrial machine audio for normal and anomalous operation. It includes machine categories such as fan, pump, valve, and slide rail. This project uses MIMII Fan `id_00` as the reference MVP and follows a normal-only acoustic anomaly detection paradigm.

PROJECT ADAPTATION: The current Expert A architecture is a project Conv1D autoencoder implementation. It is not claimed to be an exact reproduction of the original MIMII baseline network.

## 8.2 Nishida Timbre Difference

PAPER-BACKED METHOD: Nishida et al. define timbre-difference capturing for anomalous sound detection. The paper focuses on five attributes:

- sharpness
- roughness
- boominess
- brightness
- depth

The method compares a test sound with similar normal references in an embedding space. The paper experiments use `k=30` nearest normal references and a rank-style score:

```text
rank_score = (r - 1) / k
```

The paper uses a threshold `t` to convert scores into decreased/no-change/increased labels.

PROJECT ADAPTATION: This repository uses Expert A's bottleneck as the first embedding adapter and Euclidean distance as a project choice. `rank_threshold = None` in the MVP, so directions remain null.

BLOCKED: Exact reproduction is blocked by missing paper-specific labels/assets and some unreleased or unstated implementation details.

## 8.3 MIMII DG

MIMII DG is a future robustness dataset for domain-shift behavior. It is not required for the Fan MVP. It will be used later to ask whether Expert A and Expert B remain meaningful under source/target domain changes.

STATUS: not staged and not implemented.

## 8.4 MIMII-Agent

MIMII-Agent is an optional future robustness branch. It uses LLM-guided function calling for synthetic machine-specific anomaly transformations in evaluation. It is not the runtime Expert B, not root-cause diagnosis, and not part of the current Fan MVP.

STATUS: optional, not implemented.

## 8.5 AudioCommons Timbral Models

AudioCommons timbral models provide the timbral metrics aligned with the five Expert B attributes. Generic substitutes such as spectral centroid, rolloff, MFCCs, or other librosa features are not silently equivalent. Replacing AudioCommons would require a separate disclosed adaptation experiment.

# 9. Dataset and Data Organization

Current external data root:

```text
D:\PDM_Data\MIMII
```

Current Fan `id_00` staged data:

| SNR | Normal WAVs | Abnormal WAVs | Root |
|---|---:|---:|---|
| minus6dB | 1011 | 407 | `D:\PDM_Data\MIMII\fan_minus6dB\id_00` |
| 0dB | 1011 | 407 | `D:\PDM_Data\MIMII\fan_0dB\id_00` |
| plus6dB | 1011 | 407 | `D:\PDM_Data\MIMII\fan_plus6dB\id_00` |

Recording facts verified in project docs:

- 16 kHz sample rate.
- 8 channels.
- 10 seconds per clip.
- MIMII folder uses `abnormal/`, not `anomaly/`.

Future data:

- Pump: not staged.
- Valve: not staged.
- Slide Rail: not staged.
- MIMII DG: not staged.

# 10. Data Preprocessing

Expert A preprocessing:

- Load WAV at `sr=16000`.
- Downmix 8 channels to mono.
- Compute Mel spectrogram.
- Convert power to dB.
- Use `n_fft=1024`.
- Use `hop_length=512`.
- Use `n_mels=64`.
- Force final shape `(313, 64)`.
- Save arrays as `(N, 313, 64)`.

Deterministic split:

- train: first 200 readable normal files.
- test: next 200 readable normal files plus first 50 readable abnormal files.
- train/test normal files are disjoint.

# 11. Expert A - Acoustic Anomaly Detector

IMPLEMENTED AND VERIFIED.

Architecture:

- Input to model: `(B, 64, 313)`.
- Encoder: Conv1D layers over time with channels `64 -> 128 -> 256 -> 256`.
- Bottleneck: dense bottleneck to `128` latent dimensions.
- Decoder: ConvTranspose1D back to `(B, 64, 313)`.
- Loss: MSE reconstruction loss.
- Optimizer: Adam.
- Epochs: 250.
- Batch size: 32.
- Learning rate: 0.001.
- Threshold: validation reconstruction-error mean plus `2 * std`.

Training policy:

- normal-only training.
- per-band normalization fitted on train only.
- validation split rebuilt from training data for thresholding.

Anomaly score:

```text
mean squared reconstruction error
```

# 12. Expert A Controlled SNR Experiment

Research question:

Was weak `-6 dB` performance caused mainly by the model/pipeline or by low SNR?

Controlled variables:

- architecture
- Log-Mel preprocessing
- file selection
- train/test counts
- normalization
- loss
- optimizer
- learning rate
- epochs
- batch size
- latent dimension
- threshold rule
- random seed

Full results:

| SNR | AUC | Threshold | Normal Mean | Abnormal Mean | Recall | FPR | Specificity |
|---|---:|---:|---:|---:|---:|---:|---:|
| -6 dB | 0.6142 | 0.593 | 0.436 | 0.458 | 0.14 | 0.135 | 0.865 |
| 0 dB | 0.8306 | 0.680 | 0.459 | 0.837 | 0.52 | 0.130 | 0.870 |
| +6 dB | 0.9980 | 1.133 | 0.707 | 3.223 | 1.00 | 0.050 | 0.950 |

VERIFIED RESULT: The AUC improves monotonically with SNR. The reconstruction-error gap also widens substantially.

Correct interpretation:

Low SNR is strongly indicated as the primary limitation of the weak `-6 dB` separation.

Forbidden overclaim:

- Do not claim the autoencoder is perfect.
- Do not claim noise is the only possible limitation.
- Do not claim production readiness from the `+6 dB` result.

# 13. Expert B - Acoustic Timbre Difference Expert

Task:

Expert B answers: how does the same anomalous audio differ acoustically from similar normal operation?

Relationship to Expert A:

- Expert A evaluates an audio event.
- Expert B should run only when Expert A marks that same event anomalous, unless a future explicit review mode allows otherwise.
- Expert B does not decide the original anomaly score.

Reference policy:

- same machine type
- same machine ID
- same SNR tag for current MVP
- normal references only
- default `k=30`

Distance:

- Euclidean distance is the current project choice.

Embedding:

- Expert A bottleneck adaptation.
- Not a Nishida paper encoder.

Timbre metrics:

- AudioCommons sharpness.
- AudioCommons roughness.
- AudioCommons booming mapped to boominess.
- AudioCommons brightness.
- AudioCommons depth.

Rank score:

```text
rank_score = below_count / k
```

Current direction policy:

```text
rank_threshold = None
direction = null
direction_code = null
```

Expert B cannot claim:

- physical root cause
- RUL
- confidence percentage
- exact diagnosis
- paper-equivalent accuracy

# 14. Expert B Current Implementation State

Based on repository evidence after cleanup:

| Path | Purpose | Implemented | Tested | Verified | Missing |
|---|---|---|---|---|---|
| `src/models/timbre_difference.py` | Expert B timbre values, rank score, Expert A bottleneck embedder, characterization JSON | Yes | Unit-level | Partially | End-to-end smoke |
| `src/utils/audio_reference_index.py` | Reference item/index, metadata filtering, deterministic kNN, JSON save/load | Yes | Unit-level through Expert B tests | Partially | Performance-reviewed index artifact |
| `scripts/build_timbre_reference_index.py` | Build normal-reference index with timing/progress | Yes | Not fully | No | Performance root cause and bounded runtime |
| `scripts/run_expert_b_smoke.py` | Expert A -> Expert B smoke runner | Yes | Not fully | No | Requires usable reference index |
| `tests/test_timbre_difference.py` | Unit tests for guardrails | Yes | Yes | 5 tests OK | Does not validate scientific accuracy |

Current tests:

```text
Ran 5 tests in 0.001s
OK
```

What the tests prove:

- rank score bounds and monotonic cases.
- no direction without threshold.
- configured threshold conversion behavior.
- same-machine/SNR filtering rejects mismatches.
- JSON guardrails exclude confidence, root cause, and diagnosis keys.

What they do not prove:

- timbre direction accuracy.
- AudioCommons runtime feasibility.
- end-to-end same-audio integration.
- reference-index scalability.

# 15. Expert B Performance Blocker

MEASURED FACT:

Known slow command:

```text
python scripts/build_timbre_reference_index.py --machine-type fan --machine-id id_00 --snr-tag minus6dB --limit 40
```

Observed:

- 40 normal WAV clips requested.
- Process remained CPU-bound for hours.
- CPU delta was 9.53 CPU seconds over 10 wall-clock seconds.
- Process was active, not frozen.
- Run was manually stopped.
- One-file path-based benchmark exceeded 23 minutes before interruption.

CURRENT HYPOTHESIS:

The likely cause is repeated expensive work in `timbral_models` path-based calls:

- file read
- downmix
- loudness normalization
- resampling
- repeated metric calls for each timbre attribute

The build script already has a `--timbre-input array` option, but this has not yet been reviewed under the approved performance-forensics task.

Why the performance task is next:

Expert B cannot be trusted operationally until one-file and three-file timings establish a bounded runtime and a 40-file estimate.

# 16. Structured Health Context

PLANNED, NOT IMPLEMENTED.

Purpose:

Translate machine metadata, Expert A output, Expert B output, and explicit limitations into deterministic JSON before any LLM reasoning.

Example shape:

```json
{
  "schema_version": "0.1.0",
  "event": {
    "machine_type": "fan",
    "machine_id": "id_00",
    "snr_tag": "minus6dB",
    "audio_path": "..."
  },
  "expert_a": {
    "anomaly_score": 0.0,
    "threshold": 0.0,
    "is_anomaly": true
  },
  "expert_b": {
    "method_status": "adaptation_not_exact_reproduction",
    "rank_threshold": null,
    "timbre_differences": {}
  },
  "system_limits": [
    "No RUL.",
    "No root-cause diagnosis.",
    "Expert B is qualitative until labels are available."
  ]
}
```

# 17. LLM Explanation Layer

PLANNED, NOT IMPLEMENTED.

Intended role:

- Explain structured evidence cautiously.
- Separate observations from hypotheses.
- State limitations.

Inputs:

- Structured Health Context.
- Retrieved maintenance evidence when RAG exists.

Forbidden:

- raw-audio diagnosis
- RUL
- exact root cause
- invented confidence
- treating rank score as failure probability

# 18. Maintenance RAG

PLANNED, NOT IMPLEMENTED.

Purpose:

Ground maintenance recommendations in approved documents or procedures.

Planned output separation:

- observed acoustic evidence
- retrieved source evidence
- cautious inspection suggestion
- limitations

Current status:

No knowledge base, retriever, approved manuals, source IDs, or retrieval tests exist yet.

# 19. End-to-End Orchestration

PLANNED, NOT IMPLEMENTED.

Planned flow:

```text
audio event
-> Expert A score
-> conditional Expert B
-> Structured Health Context
-> RAG
-> LLM
-> final JSON
```

The repository does not currently contain `scripts/run_end_to_end_demo.py`.

# 20. Dashboard

PLANNED, NOT IMPLEMENTED.

Current app status:

`app/` contains only `.gitkeep`.

Planned dashboard cards:

- machine/event identity
- Expert A anomaly evidence
- Expert B timbre rank view
- explanation
- maintenance recommendation
- method limitations

# 21. Machine-Aware Generalization Strategy

Fan `id_00` is the reference MVP.

Future targets:

- pump
- valve
- slide rail

Policy:

- train/evaluate machine-specific Expert A artifacts first.
- build machine-specific Expert B reference indexes.
- do not assume one universal autoencoder.
- do not mix normals from unrelated machines as the first baseline.

Actual staged-data status:

- Fan `id_00`: staged.
- Pump: missing.
- Valve: missing.
- Slide Rail: missing.

# 22. MIMII DG Robustness Plan

PLANNED, NOT IMPLEMENTED.

Purpose:

Evaluate source/target domain shift and test whether Expert A or Expert B confuses domain shift with anomaly-related acoustic change.

Current blocker:

MIMII DG data and any required labels/assets are not staged.

# 23. Optional MIMII-Agent-Inspired Evaluation

OPTIONAL, NOT IMPLEMENTED.

Purpose:

Offline robustness exploration with approved synthetic anomaly transformations.

Limit:

This does not become runtime root-cause diagnosis and does not automatically improve model weights.

# 24. Repository Structure

Actual cleaned tree, summarized:

```text
IOT/
|-- .agents/
|   `-- skills/
|       |-- paper-forensics/
|       |-- performance-forensics/
|       |-- project-architect/
|       `-- scientific-implementer/
|-- AGENTS.md
|-- CLAUDE.md
|-- README.md
|-- REPORT.md
|-- REPORT_PHASE1_2.md
|-- project_state.json
|-- requirements.txt
|-- .gitignore
|-- app/
|   `-- .gitkeep
|-- docs/
|   |-- EXPERT_B_NISHIDA_METHOD_SPEC.md
|   |-- LOCAL_ARTIFACT_RECONCILIATION.md
|   |-- MASTER_EXECUTION_PLAN.md
|   |-- MASTER_PROJECT_ROADMAP.md
|   |-- REPOSITORY_AUDIT.md
|   |-- TASK_EXECUTION_LOG.md
|   `-- archive/
|-- notebooks/
|-- scripts/
|-- src/
`-- tests/
```

Directory responsibilities:

- `.agents/skills/`: repo-local skills.
- `src/`: active Python source.
- `scripts/`: bounded execution scripts.
- `tests/`: unit/guardrail tests.
- `docs/`: project, method, audit, and execution documentation.
- `app/`: future dashboard.

TASK-00B removed repo-local large artifacts from `data/` and `models_store/`.
The unique legacy unsuffixed model was preserved externally at
`D:\PDM_Data\MIMII\models_store\anomaly_detector_legacy_repo_2026-06-29.pt`.

# 25. Current Implementation Status

| Component | Status | Evidence | What works | What is missing | Next task |
|---|---|---|---|---|---|
| Data staging | DONE | external counts under `D:\PDM_Data\MIMII` | Fan SNR data available | other machines | later machine tasks |
| Preprocessing | DONE | `src/data_loader.py` | Log-Mel arrays | no context preprocessing | none |
| Expert A | DONE | `src/models/anomaly_detector.py` | training/eval/scoring | multi-machine models | later |
| SNR experiment | DONE | `snr_ad_summary.json/csv` | three-SNR comparison | DG robustness | later |
| Expert B code | PARTIAL | Expert B source files | unit-level logic | runtime proof | TASK-02/03/04 |
| Expert B tests | DONE for guardrails | 5 tests OK | rank/filter/schema checks | scientific accuracy | later labels |
| Expert B reference index | BLOCKED | slow command record | script exists | bounded runtime | TASK-02 |
| Expert A -> Expert B integration | TODO | smoke script exists | not verified | reference index | TASK-04 |
| Context layer | TODO | no `src/context` | none | schema/translator | TASK-06 |
| LLM | TODO | no agent implementation | none | guardrails/output | TASK-07 |
| RAG | TODO | no `src/rag` | none | approved docs/retriever | TASK-08 |
| Orchestrator | TODO | no end-to-end script | none | same-event pipeline | TASK-10 |
| Dashboard | TODO | `app/.gitkeep` | none | UI | TASK-11 |
| Pump | TODO | data missing | none | staging/evaluation | TASK-13 |
| Valve | TODO | data missing | none | staging/evaluation | TASK-14 |
| Slide Rail | TODO | data missing | none | staging/evaluation | TASK-15 |
| MIMII DG | TODO | data missing | paper docs only | staging/protocol | TASK-17 |
| MIMII-Agent extension | OPTIONAL | concept only | none | approval/protocol | TASK-18 |

# 26. Current Overall Project Progress

This is not a scientific completion percentage. It is an engineering status estimate derived from implemented components.

Core acoustic detection foundation:

```text
complete
```

Expert B integration:

```text
partial and performance-blocked
```

Explanation/RAG/application layers:

```text
not implemented
```

Generalization/robustness:

```text
future work
```

Core MVP implementation progress:

Approximately one third of the engineering foundation is complete: data staging, preprocessing, Expert A, SNR evaluation, and initial Expert B code exist. The user-facing system is not complete because Expert B runtime, context, LLM, RAG, orchestration, and dashboard remain.

Research validation progress:

Expert A validation is strong for Fan `id_00` SNR sensitivity. Expert B scientific validation is early because current Fan data do not include timbre-difference labels.

WHERE ARE WE NOW?

We have a verified acoustic anomaly detector and a partially implemented timbre-difference expert. The immediate blocker is making Expert B reference indexing operationally bounded.

WHAT REMAINS?

Performance-forensics for Expert B, one same-audio Expert A -> Expert B smoke, structured context, LLM/RAG, orchestrator, dashboard, and later machine/domain generalization.

# 27. Remaining Work

| Task ID | Title | Why | Dependency | Expected Result |
|---|---|---|---|---|
| TASK-02 | Expert B Reference-Index Performance Root Cause And Optimization | unblock Expert B runtime | TASK-00 complete | measured one/three/40-file runtime or blocker |
| TASK-03 | Expert B Reference Index Completion | provide same-machine normal references | TASK-02 | usable reference index |
| TASK-04 | Expert A To Expert B Same-Audio Integration | prove same-event characterization | TASK-03 | reviewed Expert B JSON |
| TASK-05 | Expert B Qualitative Evidence Protocol | define honest review without labels | TASK-04 | qualitative protocol |
| TASK-06 | Structured Health Context Schema And Translator | give LLM/RAG deterministic evidence | TASK-04 | schema/tests/sample context |
| TASK-07 | Guardrailed LLM Explanation Agent | explain evidence cautiously | TASK-06 | guardrailed explanation |
| TASK-08 | Maintenance Knowledge Base And Retriever | source-ground recommendations | TASK-06 | retriever/tests |
| TASK-09 | Grounded Maintenance Agent | combine explanation and retrieval | TASK-07 + TASK-08 | sourced technician output |
| TASK-10 | End-To-End Fan MVP Orchestrator | one bounded system path | TASK-04 + TASK-06 + TASK-09 | final JSON |
| TASK-11 | Dashboard MVP | show evidence and limits | TASK-10 | local dashboard |
| TASK-12 | Fan MVP Final Evaluation And Academic Report | summarize supported claims | TASK-10 + TASK-11 | Fan MVP evidence package |
| TASK-13 | Pump Generalization | test architecture transfer | TASK-12 + data | pump report/artifacts |
| TASK-14 | Valve Generalization | test architecture transfer | TASK-12 + data | valve report/artifacts |
| TASK-15 | Slide Rail Generalization | test architecture transfer | TASK-12 + data | slide rail report/artifacts |
| TASK-16 | Cross-Machine Comparison | synthesize per-machine evidence | TASK-13/14/15 | comparison doc |
| TASK-17 | MIMII DG Domain Robustness | evaluate domain shift | TASK-12 + DG data | bounded robustness result |
| TASK-18 | Optional MIMII-Agent-Inspired Evaluation | optional robustness branch | TASK-12 + explicit approval | optional plan/result |

TASK-01 was superseded by TASK-00 because repository normalization and active-scope cleanup were completed here.

# 28. Scientific Claim Matrix

| Claim | Supported | Evidence | Limitation |
|---|---|---|---|
| Expert A detects anomalous Fan `id_00` sounds | Yes | Expert A code, artifacts, SNR metrics | Fan `id_00` only |
| Expert A performance is SNR-sensitive | Yes | AUC 0.6142/0.8306/0.9980 | only evaluated on current Fan data |
| Low SNR is strongly indicated as primary limitation at -6 dB | Yes | controlled SNR-only comparison | not the only possible limitation |
| Expert B code implements rank/filter guardrails | Yes | 5 unit tests OK | code-level only |
| Expert B technically works end-to-end | Not yet | smoke not completed | performance blocker |
| Expert B accurately predicts timbre direction | No | labels unavailable | requires labels/protocol |
| Expert B diagnoses root cause | No | forbidden by architecture | no labels/model |
| LLM explanation is grounded | No | no LLM/context/RAG | planned |
| Maintenance recommendations are grounded | No | no retrieval layer | planned |
| Architecture generalizes to Pump/Valve/Slide Rail | No | data not staged/evaluated | future |
| System is robust to domain shift | No | MIMII DG not staged/evaluated | future |
| System predicts RUL | No | outside active scope | not planned |

# 29. Risks and Limitations

- Low SNR can hide acoustic fault cues.
- Expert B lacks five-attribute ground-truth labels in current Fan data.
- Expert A bottleneck embeddings are a project adaptation.
- AudioCommons timbral models may be computationally expensive.
- Reference selection must remain same-machine and same-condition.
- Domain shift may look like anomaly or timbre change.
- Machine-specific behavior cannot be assumed universal.
- LLM hallucination must be controlled with schema and tests.
- RAG quality depends on approved knowledge sources.
- No root-cause labels are available.
- No RUL target exists in active data.

# 30. Testing and Validation Strategy

Execution ladder:

```text
UNIT TEST
-> ONE SAMPLE
-> THREE SAMPLES
-> BOUNDED RUN
-> RUNTIME ESTIMATE
-> FULL RUN ONLY IF REASONABLE
```

Every implemented task requires:

- implementation review
- scientific review
- diff review
- actual output inspection

No full dataset processing, training, or slow indexing should run before small timing evidence.

# 31. Final Expected System

When complete, the system will accept one machine audio event, score it with Expert A, characterize it with Expert B if anomalous, translate evidence into structured context, retrieve approved maintenance guidance, generate a cautious technician-facing explanation, and display the result in a dashboard.

The final system should still avoid RUL, exact time-to-failure, and unsupported root-cause claims.

# 32. Conclusion

The project now has a coherent active architecture and a normalized report around same-machine acoustic health monitoring. Expert A and the SNR experiment are verified. Expert B is implemented at the code/guardrail level but remains runtime-blocked. The next technical blocker is Expert B reference-index performance forensics.

# 33. References

- Purohit et al., "MIMII Dataset: Sound Dataset for Malfunctioning Industrial Machine Investigation and Inspection", 2019, arXiv:1909.09347.
- Nishida et al., "Timbre Difference Capturing in Anomalous Sound Detection", 2024, arXiv:2410.22033.
- Dohi et al., "MIMII DG: Sound Dataset for Malfunctioning Industrial Machine Investigation and Inspection for Domain Generalization Task", 2022, arXiv:2205.13879.
- Purohit et al., "MIMII-Agent: Leveraging LLMs with Function Calling for Relative Evaluation of Anomalous Sound Detection", 2025, arXiv:2507.20666.
- AudioCommons timbral_models, https://github.com/AudioCommons/timbral_models.
