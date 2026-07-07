# CLAUDE.md — Explainable Acoustic Machine Health Monitoring System
## Master Project Context and Research Specification

**Project Lead:** Yosef  
**Domain:** Industrial acoustic condition monitoring  
**Core datasets:** MIMII, later MIMII DG  
**Prototype:** Fan, machine ID `id_00`

---

# 1. PROJECT IDEA

We are building one coherent system around the **same machine audio**.

```text
INDUSTRIAL MACHINE
        |
        v
   MACHINE AUDIO
        |
        v
     EXPERT A
Anomaly Detection
        |
   NORMAL / ANOMALY
               |
               v
            EXPERT B
 Acoustic Difference Characterization
               |
               v
       Structured Health Context
               |
               v
          LLM + RAG
               |
               v
 Explain + Risk + Maintenance Recommendation
```

The direct relationship between the experts is:

```text
Expert A:
Is the machine sound anomalous?

        ↓ if anomalous

Expert B:
How does this exact sound differ from comparable normal sounds?
```

The LLM does not detect anomalies and does not invent faults. It explains structured evidence produced by the audio experts.

---

# 2. THE PROBLEM

Traditional anomalous sound detection may return:

```text
ANOMALY
anomaly_score = 2.80
```

That is useful for an ML engineer, but a maintenance technician may still ask:

- What changed in the sound?
- Is it sharper or rougher?
- Is the acoustic change large?
- What evidence triggered the warning?
- What should be inspected next?

The project closes the gap between:

```text
DETECTION
```

and:

```text
UNDERSTANDABLE MAINTENANCE CONTEXT
```

---

# 3. WHY RUL IS REMOVED

The old architecture used:

```text
MIMII fan audio → Expert A anomaly detection
PRONOSTIA bearing vibration → Expert B RUL
```

This is not a coherent same-asset system.

The two outputs come from different machines, different datasets, different sensors, and different experimental timelines.

MIMII also does not provide chronological run-to-failure trajectories with known end-of-life times for each fan. Therefore it supports anomalous sound detection, but it does not directly provide supervised RUL targets.

The new project does **not invent RUL labels**.

Final scope:

```text
Anomaly Detection
+
Acoustic Difference Characterization
+
Explainable Maintenance Support
```

---

# 4. CORE PAPER STACK

## Paper 1 — MIMII

**Purohit et al. (2019)**  
**Title:** MIMII Dataset: Sound Dataset for Malfunctioning Industrial Machine Investigation and Inspection  
**arXiv:** 1909.09347

### Contribution

- Industrial machine sounds.
- Normal and anomalous conditions.
- Fans, pumps, valves, and slide rails.
- Realistic factory-noise mixtures.
- Autoencoder-based unsupervised anomalous sound detection baseline.

### Our use

```text
Dataset
+
Expert A anomaly-detection foundation
+
SNR experiment
```

Prototype:

```text
machine_type = fan
machine_id = id_00
```

Preprocessing constants currently used:

```text
sample rate = 16000 Hz
n_fft = 1024
hop_length = 512
n_mels = 64
segment duration = 10 seconds
Log-Mel shape = (313, 64)
```

---

## Paper 2 — Timbre Difference Capturing in Anomalous Sound Detection

**Nishida et al. (2024)**  
**arXiv:** 2410.22033

### Contribution

The paper addresses a question beyond anomaly detection:

```text
How does the anomalous sound differ from normal sound?
```

It explains differences through predefined timbre attributes instead of unrestricted free-text captions.

Relevant attributes include:

```text
Sharpness
Roughness
Boominess
Brightness
Depth
```

The framework also uses similar normal sounds in an audio embedding space as references.

### Our use

This is the core basis for **Expert B**.

```text
Anomalous test sound
        |
        v
Audio embedding
        |
        v
Nearest comparable normal sounds
        |
        v
Timbre comparison
        |
        v
INCREASED / DECREASED / UNCHANGED
```

Example output:

```json
{
  "sharpness": "INCREASED",
  "roughness": "INCREASED",
  "boominess": "UNCHANGED",
  "brightness": "INCREASED",
  "depth": "DECREASED"
}
```

Preferred academic wording:

> Expert B is adapted from the timbre-difference framework of Nishida et al.

Do not say `exact reproduction` until the implementation is verified against the paper.

---

## Paper 3 — MIMII DG

**Dohi et al. (2022)**  
**arXiv:** 2205.13879

### Contribution

MIMII DG studies anomalous sound detection under domain shifts.

Examples of practical problems:

- Different operating conditions.
- Different background noise.
- Environmental changes.

### Our use

MIMII DG is a later robustness and Expert B evaluation dataset.

Possible experiments:

```text
Does Expert A confuse domain shift with anomaly?

Does Expert B describe normal domain changes as fault-like changes?

Does the same explanation pipeline remain stable under shifted normal conditions?
```

MIMII DG is not required for the first working MVP.

---

## Paper 4 — MIMII-Agent

**Purohit et al. (2025)**  
**arXiv:** 2507.20666

### Contribution

MIMII-Agent uses an LLM with function calling to interpret fault descriptions and select audio transformations for creating machine-type-specific synthetic anomalies used in relative anomalous-sound-detector evaluation.

### Our use

Optional **offline robustness/evolution module**.

```text
Fault description
        |
        v
LLM selects approved audio transformations
        |
        v
Synthetic anomaly scenario
        |
        v
Challenge Expert A
        |
        v
Robustness report
```

MIMII-Agent is not Expert B and is not part of the MVP runtime path.

---

# 5. CURRENT DATA STATE

Verified MIMII fan `id_00` data exists for:

```text
minus6dB
0dB
plus6dB
```

For each checked SNR:

```text
1011 normal WAV files
407 abnormal WAV files
16000 Hz
8 channels
10-second clips
```

Expected data layout:

```text
D:\PDM_Data\MIMII\
├── fan_minus6dB\id_00\
│   ├── normal\
│   └── abnormal\
├── fan_0dB\id_00\
│   ├── normal\
│   └── abnormal\
├── fan_plus6dB\id_00\
│   ├── normal\
│   └── abnormal\
├── processed\
└── models_store\
```

Zip layout:

```text
D:\PDM_Data\Zips\
├── -6_dB_fan.zip
├── 0_dB_fan.zip
└── 6_dB_fan.zip
```

Large data must remain outside the Git repository.

---


# 5A. MULTI-MACHINE EXPANSION STRATEGY

The current `fan / id_00` work is the **reference implementation and MVP**, not the permanent limit of the project.

Additional MIMII machine types may be added later, including:

```text
fan
pump
valve
slide_rail
```

The project must therefore be implemented as a **machine-aware acoustic health platform**.

## Current development strategy

```text
NOW
↓
Fan id_00
↓
Complete Expert A
↓
Complete Expert B
↓
Complete Context Translation
↓
Complete LLM/RAG
↓
Complete end-to-end MVP

LATER
↓
Pump
Valve
Slide rail
↓
Apply the same system design
↓
Evaluate cross-machine generalization
```

Do not delay the Fan MVP while additional datasets are downloading.

The Fan pipeline is the reference path used to complete and validate the full system first.

## Critical implementation rule

Do not hardcode the new architecture as `fan-only`.

New code should be parameterized around concepts such as:

```python
machine_type = "fan"
machine_id = "id_00"
snr_tag = "plus6dB"
```

The same interfaces should later support:

```python
machine_type = "pump"
machine_id = "id_00"
```

and:

```python
machine_type = "valve"
machine_id = "id_00"
```

Where practical, paths, artifact names, metadata schemas, and experiment runners must include:

```text
machine_type
machine_id
SNR / domain tag
```

Example artifact naming direction:

```text
anomaly_detector_fan_id00_plus6dB.pt
anomaly_detector_pump_id00_plus6dB.pt
anomaly_detector_valve_id00_plus6dB.pt
```

Exact naming may be adjusted during migration, but artifacts from different machines must never silently overwrite each other.

## Expert A multi-machine policy

For the MVP and first generalization phase:

```text
same model architecture
different machine-specific training
different machine-specific artifacts
```

Preferred initial strategy:

```text
Fan normal sounds
↓
Fan Expert A model

Pump normal sounds
↓
Pump Expert A model

Valve normal sounds
↓
Valve Expert A model
```

Do **not** immediately mix all machine types into one Autoencoder.

Reason:

```text
Normal fan acoustics
≠
Normal pump acoustics
≠
Normal valve acoustics
```

A single model trained naively across unrelated machine acoustics may confuse normal machine-type differences with anomalies.

A shared multi-machine model, shared encoder, conditioning strategy, or machine-specific heads are future research options only after the machine-specific baseline is established.

## Expert B multi-machine policy

Expert B must use normal references from the **same relevant machine domain**.

Example:

```text
Fan anomalous sound
↓
Compare with comparable normal fan sounds
```

Not:

```text
Fan anomalous sound
↓
Compare with normal valve sounds
```

Reference retrieval must preserve, at minimum:

```text
machine_type
machine_id or approved machine-domain grouping
```

Any broader cross-machine reference strategy requires a separate experiment and explicit validation.

## Generalization phase

After the complete Fan end-to-end MVP works, additional MIMII machine types become a project generalization experiment.

Questions:

```text
1. Can the same system architecture support different industrial machine types?
2. Does Expert A require a separately trained model for each machine type?
3. Does Expert B preserve meaningful timbre-difference explanations across machine types?
4. Which timbre attributes are stable across machine domains?
5. How does SNR sensitivity differ between fans, pumps, valves, and slide rails?
6. Does the LLM remain grounded when machine type changes?
```

Recommended evaluation structure:

```text
Reference implementation:
Fan

Generalization:
Pump
Valve
Slide rail
```

## Correct project claim

Preferred wording:

> We first develop and validate the complete multi-expert acoustic health pipeline on MIMII fan data. We then extend the same machine-aware architecture to additional industrial machine types to evaluate system generalization.

Do not claim:

> One universal acoustic model works for every machine type.

unless such a model is explicitly trained and experimentally validated.

## Opus and Codex guardrail

During every new implementation task, Opus must review whether the proposed change accidentally assumes:

```text
machine_type == fan
```

Codex must avoid fan-specific hardcoding in reusable interfaces.

However, do not introduce unnecessary abstraction or a large plugin framework before the Fan MVP works.

Rule:

```text
Machine-aware
but simple.
```

Not:

```text
Fan-only.
```

And not:

```text
Overengineered universal framework.
```


# 6. DATA PIPELINE

Input:

```text
10-second 8-channel WAV
```

Current decision:

```python
librosa.load(..., mono=True)
```

The eight microphone channels are downmixed to mono for the current prototype.

Feature flow:

```text
WAV
↓
Mel Spectrogram
↓
Power-to-dB
↓
Transpose
↓
Pad/trim to 313 time frames
↓
float32
```

Per-clip output:

```text
(313, 64)
```

Saved array format:

```text
(B, 313, 64)
```

Model format:

```text
(B, 64, 313)
```

Current deterministic split:

```text
Train:
first 200 readable normal files

Test:
next 200 readable normal files
+
first 50 readable abnormal files
```

Normal train/test files must remain disjoint.

---

# 7. EXPERT A — ACOUSTIC ANOMALY DETECTOR

## Purpose

Answer:

```text
Does the current machine sound depart from learned normal behavior?
```

## Model

Current implementation:

```text
Convolutional Autoencoder
```

Encoder:

```text
64 → 128 → 256 → 256
Conv1D
stride 2
```

Bottleneck:

```text
Flatten
↓
Linear(flat_dim → 128)
↓
ReLU
↓
Linear(128 → flat_dim)
↓
ReLU
↓
Unflatten
```

Decoder:

```text
256 → 256 → 128 → 64
ConvTranspose1D
```

Training:

```text
normal sounds only
loss = MSE
optimizer = Adam
learning rate = 0.001
epochs = 250
batch size = 32
```

Anomaly score:

```text
per-sample reconstruction MSE
```

Threshold:

```text
mean(validation error) + 2 × std(validation error)
```

Concept:

```text
Normal sound
→ reconstructs well
→ lower error

Abnormal sound
→ reconstructs poorly
→ higher error
```

---

# 8. COMPLETED CONTROLLED SNR EXPERIMENT

The same Expert A architecture and pipeline were trained independently on:

```text
-6 dB
0 dB
+6 dB
```

The SNR condition was the primary changed variable.

Fixed:

- Architecture.
- Log-Mel preprocessing.
- Data counts.
- File-selection logic.
- Train/validation logic.
- Normalization.
- Loss.
- Optimizer.
- Learning rate.
- Epochs.
- Batch size.
- Random seed.
- Threshold rule.

Results:

| SNR | AUC | Threshold | Normal Mean | Abnormal Mean | Recall | FPR | Specificity |
|---|---:|---:|---:|---:|---:|---:|---:|
| -6 dB | 0.6142 | 0.593 | 0.436 | 0.458 | 0.14 | 0.135 | 0.865 |
| 0 dB | 0.8306 | 0.680 | 0.459 | 0.837 | 0.52 | 0.130 | 0.870 |
| +6 dB | 0.9980 | 1.133 | 0.707 | 3.223 | 1.00 | 0.050 | 0.950 |

Interpretation:

```text
AUC:
0.6142 → 0.8306 → 0.9980
```

The same model separates normal and abnormal sounds much more strongly as SNR improves.

Correct claim:

> The controlled experiment strongly indicates that low SNR is the primary limitation of the weak -6 dB anomaly separation.

Incorrect claim:

> The Autoencoder is perfect.

Do not use the incorrect claim.

---

# 9. EXPERT B — ACOUSTIC DIFFERENCE CHARACTERIZER

## Purpose

Expert B answers:

```text
How does this anomalous sound differ from comparable healthy operation?
```

Expert B does not decide whether a clip is anomalous.

Expert A owns anomaly detection.

## Trigger

MVP:

```text
Expert A anomaly_detected == True
        ↓
Run Expert B
```

## Inputs

```text
Current anomalous/test audio
+
normal reference library
```

## Planned flow

```text
Test audio
        |
        v
Audio embedding
        |
        v
Find nearest normal references
        |
        v
Compute timbre metrics for test audio
        |
        v
Compute/aggregate timbre metrics for references
        |
        v
Compare
        |
        v
Attribute-change profile
```

Planned attributes:

```text
Sharpness
Roughness
Boominess
Brightness
Depth
```

Output example:

```json
{
  "reference_count": 5,
  "attributes": {
    "sharpness": "INCREASED",
    "roughness": "INCREASED",
    "boominess": "UNCHANGED",
    "brightness": "INCREASED",
    "depth": "DECREASED"
  }
}
```

## Critical rule

Do not implement Expert B from guessed formulas.

Before implementation, Opus must inspect the paper and answer:

1. What embedding method is used?
2. Is public code available?
3. What exact timbre models/formulas are used?
4. Which Python implementations are reliable?
5. How many nearest normal references are used?
6. How are reference values aggregated?
7. How are continuous differences converted into increased/decreased/unchanged?
8. What evaluation method is used?
9. What data/annotations are required?
10. What can be reproduced and what must be adapted?

Paper inspection comes before Codex implementation.

---

# 10. UNIFIED HEALTH CONTEXT

The Context Translation Layer is deterministic Python.

It converts Expert outputs into a stable JSON schema.

Example:

```json
{
  "schema_version": "1.0",
  "asset": {
    "machine_type": "fan",
    "machine_id": "id_00"
  },
  "experiment": {
    "snr_condition": "plus6dB"
  },
  "anomaly_detection": {
    "detected": true,
    "score": 2.8,
    "threshold": 1.133
  },
  "acoustic_difference": {
    "reference_count": 5,
    "sharpness": "INCREASED",
    "roughness": "INCREASED",
    "boominess": "UNCHANGED",
    "brightness": "INCREASED",
    "depth": "DECREASED"
  },
  "system_limits": {
    "specific_fault_confirmed": false,
    "rul_available": false
  }
}
```

The `system_limits` section is mandatory.

It tells the LLM what the current evidence does not prove.

---

# 11. LLM + RAG LAYER

The LLM receives structured evidence.

It does not receive a raw spectrogram and guess a physical fault.

## Diagnostic Explanation Agent

Responsibilities:

- Explain the anomaly.
- Explain acoustic changes.
- State uncertainty.
- Separate observations from hypotheses.
- Avoid unsupported component-level fault claims.

## Maintenance Communication Agent

Responsibilities:

- Generate a technician-facing summary.
- Present inspection priority.
- Recommend grounded next actions.
- Format dashboard output.

## RAG knowledge base

Possible documents:

```text
Fan maintenance manuals
Inspection checklists
Manufacturer troubleshooting guides
Approved maintenance procedures
Acoustic-monitoring notes
```

Correct LLM statement:

> The fan sound is sharper and rougher than comparable normal operation. These acoustic changes do not confirm a specific failed component. A mechanical inspection is recommended.

Incorrect:

> The bearing is definitely broken.

---

# 12. DASHBOARD

The dashboard should present evidence in layers.

## Machine card

```text
Machine: Fan id_00
State: ANOMALOUS
Anomaly score: 2.80
Threshold: 1.13
```

## Acoustic difference card

```text
Sharpness   ↑ Increased
Roughness   ↑ Increased
Boominess   = Unchanged
Brightness  ↑ Increased
Depth       ↓ Decreased
```

## Explanation card

LLM explanation.

## Recommendation card

Example:

```text
Priority: INSPECTION RECOMMENDED

Reason:
The machine sound is outside learned normal behavior and is sharper and rougher than comparable healthy operation.

Action:
Perform a mechanical/acoustic inspection. Collect supporting vibration measurements before assigning a component-level diagnosis.
```

Optional evidence:

```text
Current Log-Mel spectrogram
Reference normal spectrogram
Anomaly score distribution
SNR comparison
Nearest normal references
```

---

# 13. EVALUATION

## Expert A

Metrics:

```text
ROC AUC
Recall
False Positive Rate
Specificity
Normal reconstruction-error mean
Abnormal reconstruction-error mean
Threshold
```

The controlled three-SNR experiment is complete.

## Expert B

Expert B is a different task.

Its metrics must be defined after primary-paper inspection.

Likely evaluation dimensions:

```text
Per-attribute direction agreement
Macro attribute agreement
Reference-selection sensitivity
Domain-shift robustness
```

Do not invent a target metric before reviewing the paper's evaluation protocol.

## End-to-end system

Evaluate:

```text
Does Expert B trigger correctly after Expert A?

Does the context preserve the model evidence?

Does the LLM avoid unsupported fault claims?

Does the LLM distinguish observation from hypothesis?

Are recommendations grounded in the knowledge base?

Is the explanation understandable?
```

Possible manual rubric:

```text
Groundedness
Evidence consistency
Unsupported-claim rate
Recommendation relevance
Explanation clarity
```

---

# 14. ACADEMIC GAPS

## Gap 1 — Expert A is not an exact MIMII baseline reproduction

The current Conv1D Autoencoder is a project architecture under the MIMII normal-only reconstruction paradigm.

Preferred wording:

> We use a convolutional autoencoder under the normal-only reconstruction-error paradigm demonstrated in MIMII.

Do not say:

> We exactly implement the original MIMII network.

## Gap 2 — Expert B source paper evaluates on MIMII DG

MVP:

```text
Integrate Expert B with current MIMII fan project
```

Later validation:

```text
Use MIMII DG for closer alignment with the source framework
```

## Gap 3 — Timbre differences do not prove physical root cause

Mitigation:

- Expert B outputs acoustic attributes.
- LLM uses cautious language.
- Root causes are inspection hypotheses.
- No confirmed component fault without a diagnosis model or supporting sensor evidence.

## Gap 4 — Exact SNR labels are experiment metadata

The current `-6/0/+6 dB` labels come from dataset variants.

Do not assume a real deployment always knows its exact SNR condition.

## Gap 5 — No RUL

The project must be described as:

```text
Explainable acoustic machine condition monitoring
```

or:

```text
Anomalous sound detection and acoustic health explanation
```

Do not claim full RUL prognostics.

---

# 15. ALLOWED PROJECT CLAIMS

Allowed:

> The system detects anomalous industrial machine sounds.

> The same anomaly detector was evaluated under three controlled SNR conditions.

> AUC increased from 0.6142 at -6 dB to 0.9980 at +6 dB.

> Expert B characterizes how an anomalous sound differs acoustically from comparable normal operation.

> The LLM explains structured anomaly and acoustic-difference evidence.

> The system avoids unsupported component-level fault claims by explicitly preserving system limits.

---

# 16. FORBIDDEN CLAIMS

Do not claim:

```text
The system predicts Remaining Useful Life.
```

Do not claim:

```text
The system predicts exact time to failure.
```

Do not claim:

```text
The bearing is definitely damaged.
```

Do not claim:

```text
The LLM diagnoses faults directly from raw audio.
```

Do not claim:

```text
Expert B finds the physical root cause.
```

Do not claim:

```text
Noise is the only limitation.
```

Preferred:

```text
Low SNR is strongly indicated as the primary limitation of the observed -6 dB separation.
```

---

# 17. PROPOSED REPOSITORY STRUCTURE

```text
IOT/
├── CLAUDE.md
├── REPORT.md
├── REPORT_PHASE1_2.md
├── requirements.txt
│
├── src/
│   ├── config.py
│   ├── data_loader.py
│   │
│   ├── models/
│   │   ├── anomaly_detector.py
│   │   └── timbre_difference.py
│   │
│   ├── context/
│   │   ├── schemas.py
│   │   └── translator.py
│   │
│   ├── agents/
│   │   ├── diagnostic_agent.py
│   │   ├── communicator_agent.py
│   │   └── robustness_agent.py
│   │
│   └── rag/
│       ├── knowledge_base.py
│       └── retriever.py
│
├── scripts/
│   ├── snr_stage1.py
│   ├── run_snr_experiments.py
│   ├── run_expert_b.py
│   └── run_end_to_end_demo.py
│
├── app/
│   └── dashboard.py
│
├── docs/
│   ├── project_proposal.md
│   ├── expert_a_results.md
│   ├── expert_b_method.md
│   └── evaluation_protocol.md
│
└── tests/
    ├── test_expert_a.py
    ├── test_timbre_difference.py
    ├── test_context_schema.py
    └── test_llm_guardrails.py
```

Large raw datasets, processed arrays, and trained weights stay under `D:\PDM_Data`.

---

# 18. MIGRATION FROM THE OLD RUL DESIGN

The repository still contains legacy PRONOSTIA/RUL assumptions.

Migration must be controlled.

## M1 — Preserve completed Expert A

Do not change without an approved experiment:

```text
Log-Mel preprocessing
SNR-specific paths
Current ConvAutoencoder architecture
Three trained SNR models
Three-SNR summary JSON/CSV
```

## M2 — Find legacy RUL references

Search for:

```text
PRONOSTIA
RUL
rul_predictor
RUL_INPUT_SHAPE
rul_seconds
rul_confidence
Bearing1_1
decision-level fusion
```

Return a file/line impact map.

No deletion during the first inspection.

## M3 — Remove RUL from the active architecture

Deprecate or remove active:

```text
PRONOSTIA pipeline assumptions
RUL model configuration
RUL context fields
RUL dashboard fields
RUL agent assumptions
```

Historical reports remain as project-evolution evidence.

## M4 — Implement Expert B

Required workflow:

```text
Read Nishida et al. 2024 carefully
↓
Extract exact method
↓
Check public code/assets
↓
Design minimal implementation
↓
Codex implements
↓
Opus reviews
↓
Evaluate
```

## M5 — Context Translation

Create stable versioned JSON.

## M6 — LLM + RAG

Build guarded explanation and maintenance recommendations.

## M7 — Dashboard

Show evidence, explanations, and actions.

## M8 — Optional robustness

MIMII DG and MIMII-Agent-inspired evaluation.

---

# 19. MILESTONES

## Milestone 1 — Acoustic Data Engineering

```text
DONE
```

## Milestone 2 — Expert A

```text
DONE
```

Results:

```text
-6 dB → AUC 0.6142
0 dB  → AUC 0.8306
+6 dB → AUC 0.9980
```

## Milestone 3 — Architecture Correction

```text
DECIDED
```

Change:

```text
PRONOSTIA/RUL Expert B
        ↓
Same-audio Acoustic Difference Expert B
```

## Milestone 4 — Expert B

```text
NEXT
```

Deliverables:

- Primary-paper inspection.
- Normal-reference strategy.
- Timbre metrics.
- Acoustic-change schema.
- Expert B evaluation.

## Milestone 5 — Unified Health Context

```text
TODO
```

## Milestone 6 — LLM + RAG

```text
TODO
```

## Milestone 7 — Dashboard

```text
TODO
```

## Milestone 8 — Robustness / Evolution

```text
OPTIONAL AFTER MVP
```

---

# 20. IMMEDIATE NEXT TASK

Do not ask Codex to guess and implement Expert B.

Opus first performs a focused primary-paper inspection of:

```text
Nishida et al. 2024
Timbre Difference Capturing in Anomalous Sound Detection
arXiv:2410.22033
```

Opus must determine:

- exact pipeline,
- audio embedding method,
- nearest-neighbor reference rule,
- timbre models,
- timbre-difference direction rule,
- evaluation protocol,
- datasets,
- public code/assets,
- reproducible parts,
- adaptation gaps.

Then Opus creates one bounded implementation task for Codex.

---

# 21. FINAL PROJECT STORY

> Industrial anomalous sound detectors identify when machine audio departs from normal behavior, but a raw anomaly score is difficult for a maintenance technician to interpret. Our system uses a sequential multi-expert architecture on the same machine audio. Expert A detects anomalous sounds using a normal-only convolutional autoencoder. When an anomaly is detected, Expert B compares the same sound with acoustically similar normal operation and characterizes the difference through interpretable timbre attributes. A deterministic context layer converts the experts' outputs into structured evidence for an LLM-based maintenance assistant. The assistant explains the observed acoustic changes and recommends inspection actions while explicitly avoiding unsupported component-level fault claims.

In simple terms:

```text
Expert A:
Is the machine sound abnormal?

Expert B:
How did the abnormal sound change?

LLM:
What does the evidence mean for the technician,
and what should be inspected next?
```

---

# 22. REFERENCES

[P1] H. Purohit et al., “MIMII Dataset: Sound Dataset for Malfunctioning Industrial Machine Investigation and Inspection,” 2019. arXiv:1909.09347.

[P2] T. Nishida et al., “Timbre Difference Capturing in Anomalous Sound Detection,” 2024. arXiv:2410.22033.

[P3] K. Dohi et al., “MIMII DG: Sound Dataset for Malfunctioning Industrial Machine Investigation and Inspection for Domain Generalization Task,” 2022. arXiv:2205.13879.

[P4] H. Purohit et al., “MIMII-Agent: Leveraging LLMs with Function Calling for Relative Evaluation of Anomalous Sound Detection,” 2025. arXiv:2507.20666.

---

# MASTER RULE

Every future project decision must preserve this core relationship:

```text
SAME MACHINE
SAME SOUND
        |
        v
EXPERT A DETECTS
        |
        v
EXPERT B CHARACTERIZES
        |
        v
STRUCTURED CONTEXT
        |
        v
LLM EXPLAINS AND RECOMMENDS
```

Do not reintroduce an unrelated Expert B from another machine or dataset unless the entire system architecture is intentionally redesigned and Yosef explicitly approves it.

The Fan is the current reference implementation. Future MIMII machine types must reuse the same machine-aware system interfaces without assuming one universal model or silently mixing normal sounds from unrelated machine domains.
