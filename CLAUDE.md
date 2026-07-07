# CLAUDE.md
# Explainable Multi-Expert Acoustic Machine Health Monitoring System
## Authoritative Current Project Context, Scientific Specification, and Execution Guardrails

> **STATUS:** ACTIVE SOURCE OF TRUTH  
> **PROJECT LEAD:** Yosef  
> **PRIMARY DOMAIN:** Industrial acoustic machine condition monitoring  
> **REFERENCE MVP:** MIMII Fan / `id_00`  
> **CURRENT ARCHITECTURE:** Expert A detects anomaly -> Expert B characterizes acoustic difference -> Structured Context -> LLM + RAG -> Dashboard  
> **RUL:** OUT OF ACTIVE SCOPE  
> **PRONOSTIA:** LEGACY PROJECT HISTORY ONLY  

---

# 0. DOCUMENT AUTHORITY

This file is the current authoritative project context.

When repository files disagree, use this order:

1. `CLAUDE.md` - current project architecture and scientific scope.
2. `project_state.json` - current execution phase and verified completion state, once created.
3. `docs/MASTER_PROJECT_ROADMAP.md` - project execution plan, once created.
4. `docs/EXPERT_B_NISHIDA_METHOD_SPEC.md` - Expert B paper-method analysis.
5. `REPORT_PHASE1_2.md` - verified Expert A and SNR experiment record.
6. `REPORT.md` - current authoritative technical report.
7. Archived legacy documentation - historical context only.

Old RUL / PRONOSTIA descriptions must never override the active architecture in this file.

If the old `CLAUDE.md` is preserved, archive it as:

```text
CLAUDE_LEGACY_RUL.md
```

Do not treat archived RUL material as active project instructions.

---

# 1. PROJECT TITLE

## Recommended academic title

**Explainable Multi-Expert Acoustic Machine Health Monitoring Using Anomalous Sound Detection and Timbre Difference Characterization**

## Short title

**Explainable Acoustic Machine Health Monitoring System**

## Product-style name

**Acoustic Machine Health Intelligence System**

---

# 2. PROJECT IDEA IN ONE SENTENCE

The system listens to industrial machine audio, uses **Expert A** to determine whether the sound departs from learned normal acoustic behavior, uses **Expert B** to characterize how the same anomalous sound differs from comparable normal machine sounds, and then uses a structured evidence layer, LLM, and maintenance RAG to produce a cautious technician-facing explanation and inspection recommendation.

---

# 3. THE CORE PROJECT RULE

Every active runtime decision must preserve:

```text
SAME MACHINE
SAME AUDIO EVENT
        |
        v
EXPERT A
DETECTS ANOMALY
        |
        v
EXPERT B
CHARACTERIZES ACOUSTIC DIFFERENCE
        |
        v
STRUCTURED HEALTH CONTEXT
        |
        v
LLM EXPLAINS THE EVIDENCE
        |
        v
RAG SUPPORTS MAINTENANCE RECOMMENDATIONS
        |
        v
DASHBOARD
```

The system is sequential.

Expert A and Expert B are not unrelated independent models.

Expert B analyzes the same audio event that Expert A has evaluated.

---

# 4. THE PROBLEM

Industrial anomalous sound detection often returns:

```text
NORMAL
```

or:

```text
ANOMALOUS
```

possibly with an anomaly score:

```text
anomaly_score = 2.80
threshold = 1.13
```

This is useful to an ML engineer but incomplete for a maintenance technician.

A technician may ask:

```text
What changed in the sound?
How is this sound different from normal operation?
Is the sound acoustically sharper?
Is it rougher?
Is the low-frequency character different?
Which normal sounds were used for comparison?
How strong is the departure from the local normal reference distribution?
What should be inspected next?
```

The project addresses the gap between:

```text
DETECTION
```

and:

```text
INTERPRETABLE MAINTENANCE CONTEXT
```

---

# 5. RESEARCH MOTIVATION

The project combines four research ideas.

## 5.1 Unsupervised anomalous sound detection

Industrial anomalies are difficult to collect exhaustively.

The active Expert A follows a normal-only reconstruction paradigm:

```text
Normal training sounds
        |
        v
Autoencoder learns normal acoustic structure
        |
        v
Reconstruction error
        |
        v
Anomaly score
```

## 5.2 Timbre-difference characterization

An anomaly flag does not describe how the sound changed.

The Nishida et al. framework motivates comparison along predefined perceptual timbre attributes:

```text
Sharpness
Roughness
Boominess
Brightness
Depth
```

## 5.3 Structured evidence before LLM reasoning

The LLM must not receive a raw spectrogram and invent a physical fault.

Signal-processing and ML blocks produce evidence first.

The LLM receives:

```text
machine metadata
+
Expert A anomaly result
+
Expert B acoustic-difference result
+
known system limitations
```

## 5.4 Grounded maintenance communication

Maintenance actions should be supported by approved manuals, inspection procedures, or troubleshooting guidance.

Therefore:

```text
Structured Health Context
        |
        v
LLM
        |
        +----> explanation of observed evidence
        |
        v
RAG
        |
        v
grounded maintenance recommendation
```

---

# 6. WHY RUL WAS REMOVED

The previous project architecture used:

```text
MIMII fan audio
-> Expert A anomaly detection

PRONOSTIA bearing vibration
-> Expert B RUL prediction
```

This created a scientific integration problem.

The two outputs described:

- different physical assets,
- different datasets,
- different sensor modalities,
- different experiments,
- different timelines,
- different degradation processes.

A MIMII fan anomaly score cannot be combined with a PRONOSTIA bearing RUL estimate and presented as the health state of one machine.

The project also considered predicting RUL directly from MIMII.

The current MIMII sound data do not provide chronological run-to-failure trajectories with known remaining lifetime targets for each monitored fan audio event.

Therefore the active project does not invent:

```text
rul_seconds
```

or:

```text
time_to_failure
```

from file indices.

## Correct active scope

```text
Condition monitoring
+
Anomalous sound detection
+
Acoustic difference characterization
+
Explainable maintenance support
```

## Outside active scope

```text
Remaining Useful Life prediction
Exact time-to-failure prediction
PRONOSTIA runtime inference
```

PRONOSTIA remains historical project exploration only.

---

# 7. RESEARCH CONTRIBUTION OF THIS PROJECT

The project does not claim that one paper already contains the complete final architecture.

The contribution is the integration of paper-backed technical blocks into one machine-aware workflow.

```text
MIMII-based normal-only anomaly detection
        |
        v
same-audio anomaly trigger
        |
        v
Nishida-inspired local normal-reference timbre comparison
        |
        v
versioned structured health evidence
        |
        v
grounded LLM maintenance communication
```

Preferred academic statement:

> We integrate normal-only acoustic anomaly detection with a paper-inspired timbre-difference characterization stage and translate the outputs into structured evidence for grounded maintenance explanation.

Do not say:

> We exactly reproduce one published paper.

unless a future experiment proves exact reproduction.

---

# 8. CORE PAPER STACK

---

## PAPER P1 - MIMII Dataset

**Authors:** Harsh Purohit et al.  
**Year:** 2019  
**Title:** MIMII Dataset: Sound Dataset for Malfunctioning Industrial Machine Investigation and Inspection  
**arXiv:** `1909.09347`  
**Primary source:** `https://arxiv.org/abs/1909.09347`  
**Dataset record:** `https://zenodo.org/records/3384388`

### Paper role

The MIMII work provides industrial machine audio under normal and anomalous conditions.

The original machine categories include:

```text
valve
pump
fan
slide rail
```

The MIMII paper also evaluates autoencoder-based unsupervised anomalous sound detection.

### Project use

```text
Core audio dataset
+
Expert A foundation
+
SNR/noise experiment
+
future multi-machine generalization
```

### Important project wording

Correct:

> Expert A uses a normal-only reconstruction-error anomaly-detection paradigm consistent with MIMII-style unsupervised anomalous sound detection.

Incorrect:

> Our current Conv1D Autoencoder is an exact implementation of the original MIMII baseline network.

The current architecture is a project implementation.

---

## PAPER P2 - Timbre Difference Capturing in Anomalous Sound Detection

**Authors:** Tomoya Nishida, Harsh Purohit, Kota Dohi, Takashi Endo, Yohei Kawaguchi  
**Year:** 2024  
**Title:** Timbre Difference Capturing in Anomalous Sound Detection  
**arXiv:** `2410.22033`  
**Primary source:** `https://arxiv.org/abs/2410.22033`

### Paper problem

UASD answers:

```text
normal or anomalous?
```

but it does not explain:

```text
how is the anomalous sound different?
```

Free-form audio-difference captioning may require anomalous training data and paired/captioned differences.

The paper instead defines a timbre-difference task based on predefined timbral attributes.

### Selected attributes

The paper uses:

```text
1. Sharpness
2. Roughness
3. Boominess
4. Brightness
5. Depth
```

Paper meanings:

```text
Sharpness
-> sharp / shrill sensation

Roughness
-> buzzing / harsh / raspy quality

Boominess
-> booming sensation, often associated with low-pitch vibration

Brightness
-> bright sensation

Depth
-> emphasized low-frequency component
```

### Paper task

For every timbre attribute, estimate:

```text
DECREASED
NO CHANGE
INCREASED
```

The task is therefore related to multi-label and ordinal classification.

### Proposed paper concept

```text
Normal training audio only
        |
        v
audio encoder
        |
        v
embedding space
        |
        v
k-nearest normal references for test audio
        |
        +------------------+
        |                  |
        v                  v
kNN anomaly logic     timbre metric comparison
                           |
                           v
                timbre difference scores
                           |
                           v
              threshold-based direction labels
```

### Similar-normal-reference hypothesis

The paper argues that anomaly-specific acoustic differences can be clearer when a test sample is compared with the most acoustically similar normal training samples instead of the entire normal distribution.

The similar normal sounds are found in an audio embedding space.

### Audio encoder policy in the paper

The framework permits an arbitrary audio encoder.

It may be:

```text
pretrained
```

or:

```text
trained from scratch on normal training data
```

or:

```text
pretrained and fine-tuned
```

The experiments study:

```text
MobileNetV2
PANNs
CLAP audio encoder
BEATs
```

### kNN setting

The paper experiments use:

```text
k = 30
```

and report similar behavior for a range around:

```text
k = 10 to 40
```

### Distance

The method defines a generic embedding distance and mentions examples such as:

```text
Euclidean distance
Cosine distance
```

Therefore the project must mark a selected metric as a project choice unless a specific paper experiment configuration is verified.

Current MVP choice:

```text
distance = Euclidean
status = PROJECT IMPLEMENTATION CHOICE
```

Do not claim:

> Nishida mandates Euclidean distance.

### Timbre score concept

Let the test sample's timbre metric be compared with the values of its `k` nearest normal references.

If the test value has rank `r` in the ordered local reference comparison, the paper's rank-style score is represented in the current method specification as:

```text
rank_score = (r - 1) / k
```

The score is bounded conceptually in:

```text
[0, 1]
```

Interpretation:

```text
near 0
-> test timbre value is low relative to similar normal references

near 0.5
-> test timbre value lies around the local normal middle

near 1
-> test timbre value is high relative to similar normal references
```

### Direction labels and threshold t

The paper uses a predefined inference threshold `t` to transform the timbre score into:

```text
decreased
no change
increased
```

The current project does not silently invent one final threshold.

Initial MVP policy:

```text
rank_threshold = None
```

Therefore the first Expert B output contains continuous rank scores and:

```json
{
  "direction": null,
  "direction_code": null
}
```

Direction labels are enabled only when an explicit, documented threshold policy is approved.

### Paper dataset/evaluation

The paper evaluates on a MIMII DG-based dataset with ground-truth timbre-difference labels.

The authors used access to originally recorded clean machine sounds and anomaly-cause/condition information to construct the labels.

This creates an important project limitation:

```text
Current MIMII fan SNR data
-> enough for integration and qualitative characterization

Current MIMII fan SNR data
-> NOT enough for paper-equivalent timbre-direction accuracy claims
```

### Project use

P2 is the main research basis for Expert B.

Preferred wording:

> Expert B is a Nishida-inspired adaptation of local normal-reference timbre difference characterization.

---

## PAPER P3 - MIMII DG

**Authors:** Kota Dohi et al.  
**Year:** 2022  
**Title:** MIMII DG: Sound Dataset for Malfunctioning Industrial Machine Investigation and Inspection for Domain Generalization Task  
**arXiv:** `2205.13879`  
**Primary source:** `https://arxiv.org/abs/2205.13879`  
**Dataset:** `https://zenodo.org/records/6529888`

### Paper problem

An acoustic model may observe distribution shifts caused by factors other than a physical anomaly.

Examples:

```text
operating-condition changes
environment changes
background-noise changes
```

These domain shifts can degrade anomaly-detection performance.

### Dataset role

MIMII DG was designed for domain-generalization benchmarking.

The dataset contains:

```text
five machine types
three domain-shift scenarios for each machine type
```

### Project use

MIMII DG is not required to complete the Fan MVP.

It is a later scientific robustness phase.

Potential questions:

```text
Does Expert A confuse domain shift with anomaly?

Does Expert B report normal domain changes as anomaly-related timbre changes?

Does reference selection remain meaningful under source/target domain changes?

Does LLM wording remain cautious under uncertain domain conditions?
```

---

## PAPER P4 - MIMII-Agent

**Authors:** Harsh Purohit, Tomoya Nishida, Kota Dohi, Takashi Endo, Yohei Kawaguchi  
**Year:** 2025  
**Title:** MIMII-Agent: Leveraging LLMs with Function Calling for Relative Evaluation of Anomalous Sound Detection  
**arXiv:** `2507.20666`  
**Primary source:** `https://arxiv.org/abs/2507.20666`

### Paper problem

Real anomalous machine sounds can be scarce.

Relative ASD evaluation across machine types is therefore difficult.

### Main idea

The paper uses an LLM to interpret textual fault descriptions and select audio-transformation functions that convert normal machine sounds into machine-type-specific synthetic anomalies.

### Project use

Optional offline robustness/evolution phase.

```text
textual anomaly/fault description
        |
        v
LLM selects approved transformation functions
        |
        v
synthetic anomaly scenario
        |
        v
challenge Expert A
        |
        v
relative robustness report
```

MIMII-Agent is:

```text
NOT Expert B
NOT runtime root-cause diagnosis
NOT automatic self-training
```

Do not claim that the system automatically improves model weights unless an evaluated learning loop is later implemented.

---

# 9. SUPPORTING IMPLEMENTATION ASSETS

## AudioCommons Timbral Models

**Official repository:**

```text
https://github.com/AudioCommons/timbral_models
```

The package/repository provides models for timbral characteristics including:

```text
depth
brightness
roughness
sharpness
booming
```

These align with the five attributes used by the Expert B research direction.

The project must use the timbral-model outputs as timbral metrics.

Do not replace them silently with similarly named generic features such as:

```text
spectral centroid
spectral rolloff
MFCC
```

unless a separate adaptation experiment is explicitly designed and disclosed.

## Future embedding baselines

The Nishida experiments study encoders including:

```text
PANNs
CLAP
BEATs
```

Official/public implementation assets include:

```text
PANNs:
https://github.com/qiuqiangkong/audioset_tagging_cnn

Microsoft CLAP:
https://github.com/microsoft/CLAP

BEATs:
https://github.com/microsoft/unilm/tree/master/beats
```

These are future scientific embedding comparisons.

They are not required for the first Expert B MVP.

---

# 10. CURRENT DATA STRATEGY

## Reference MVP

```text
machine_type = fan
machine_id = id_00
```

Current verified SNR conditions:

```text
minus6dB
0dB
plus6dB
```

Known staged data for each checked Fan `id_00` SNR variant:

```text
1011 normal WAV files
407 abnormal WAV files
16000 Hz
8 channels
10-second clips
```

Current external data root:

```text
D:\PDM_Data\MIMII
```

Expected current layout:

```text
D:\PDM_Data\MIMII\
|-- fan_minus6dB\
|   \-- id_00\
|       |-- normal\
|       \-- abnormal\
|
|-- fan_0dB\
|   \-- id_00\
|       |-- normal\
|       \-- abnormal\
|
|-- fan_plus6dB\
|   \-- id_00\
|       |-- normal\
|       \-- abnormal\
|
|-- processed\
\-- models_store\
```

Zip root:

```text
D:\PDM_Data\Zips
```

Large datasets and generated model artifacts must stay outside the Git repository.

---

# 11. MULTI-MACHINE STRATEGY

The project is not permanently Fan-only.

The Fan is the current:

```text
REFERENCE MVP
```

Future MIMII machine generalization targets:

```text
pump
valve
slide rail
```

## Development order

```text
NOW
v
complete Fan end-to-end system

LATER
v
stage additional machine datasets
v
verify counts and metadata
v
run machine-specific Expert A baseline
v
build machine-specific Expert B references
v
run same structured context
v
compare system generalization
```

Do not stop Fan development while Pump, Valve, or Slide Rail datasets are downloading.

## Machine-aware interfaces

Reusable code should carry metadata such as:

```python
machine_type = "fan"
machine_id = "id_00"
snr_tag = "plus6dB"
```

Future examples:

```python
machine_type = "pump"
machine_id = "id_00"
```

```python
machine_type = "valve"
machine_id = "id_00"
```

## Artifact isolation

Artifacts must never silently overwrite another machine or acoustic condition.

Preferred naming direction:

```text
anomaly_detector_fan_id00_plus6dB.pt
anomaly_detector_pump_id00_plus6dB.pt
anomaly_detector_valve_id00_plus6dB.pt
```

Exact naming may evolve, but identity metadata must remain explicit.

---

# 12. EXPERT A - ACOUSTIC ANOMALY DETECTION EXPERT

## Responsibility

Expert A answers:

```text
Does this machine audio depart from learned normal acoustic behavior?
```

## Not responsible for

Expert A does not:

```text
predict RUL
identify an exact damaged component
generate maintenance advice
describe the timbral difference
```

## Input

Current prototype input:

```text
10-second MIMII WAV
8 source channels
16000 Hz
```

## Current channel policy

Current data loading downmixes to mono.

Conceptually:

```python
librosa.load(..., mono=True)
```

This is an existing prototype decision.

A future multichannel experiment is outside the current MVP.

---

# 13. EXPERT A PREPROCESSING

Current feature constants:

```text
sample rate = 16000 Hz
n_fft = 1024
hop_length = 512
n_mels = 64
segment duration = 10 seconds
```

Feature pipeline:

```text
WAV
v
mono loading/downmix
v
Mel spectrogram
v
power-to-dB
v
transpose
v
pad/trim
v
float32
```

Per-clip feature shape:

```text
(313, 64)
```

Saved array shape:

```text
(B, 313, 64)
```

Model input shape:

```text
(B, 64, 313)
```

---

# 14. EXPERT A DATA SPLIT

Current deterministic prototype split:

```text
Training:
first 200 readable normal files

Testing:
next 200 readable normal files
+
first 50 readable abnormal files
```

The normal train and test slices are disjoint.

The file ordering is deterministic.

Do not silently change the split in a result-comparison experiment.

If the split is changed, it becomes a new experiment.

---

# 15. EXPERT A MODEL

## Model name

```text
ConvAutoencoder
```

## Encoder

```text
64 -> 128 -> 256 -> 256
Conv1D
stride = 2
```

## Bottleneck

Current dense bottleneck:

```text
Flatten
v
Linear(flat_dim -> 128)
v
ReLU
v
Linear(128 -> flat_dim)
v
ReLU
v
Unflatten
```

The first `128`-dimensional compressed activation is currently considered for the MVP Expert B embedding adaptation.

## Decoder

```text
256 -> 256 -> 128 -> 64
ConvTranspose1D
```

## Training

```text
training data = normal sounds only
loss = MSE
optimizer = Adam
learning rate = 0.001
epochs = 250
batch size = 32
random seed = 42
```

## Anomaly score

Per-sample reconstruction MSE.

Concept:

```text
normal sound
-> model reconstructs learned normal structure well
-> lower reconstruction error

anomalous sound
-> reconstruction mismatch
-> higher reconstruction error
```

## Threshold

Current validation-derived rule:

```text
threshold =
mean(validation reconstruction error)
+
2 Ã— std(validation reconstruction error)
```

This threshold belongs to Expert A.

Do not reuse it as the Expert B timbre-direction threshold.

---

# 16. COMPLETED EXPERT A CONTROLLED SNR EXPERIMENT

## Research question

Was weak `-6 dB` performance mainly caused by the Autoencoder architecture/pipeline, or by low acoustic SNR?

## Controlled design

The same Expert A architecture and pipeline were trained independently on:

```text
-6 dB
0 dB
+6 dB
```

Held fixed:

```text
architecture
Log-Mel preprocessing
file-selection logic
data counts
train/validation logic
normalization logic
loss
optimizer
learning rate
epochs
batch size
latent dimension
seed
threshold rule
```

The SNR dataset was the primary changed variable.

## Results

| SNR | ROC AUC | Threshold | Normal Mean Error | Abnormal Mean Error | Recall | FPR | Specificity |
|---|---:|---:|---:|---:|---:|---:|---:|
| -6 dB | 0.6142 | 0.593 | 0.436 | 0.458 | 0.14 | 0.135 | 0.865 |
| 0 dB | 0.8306 | 0.680 | 0.459 | 0.837 | 0.52 | 0.130 | 0.870 |
| +6 dB | 0.9980 | 1.133 | 0.707 | 3.223 | 1.00 | 0.050 | 0.950 |

AUC trend:

```text
0.6142
v
0.8306
v
0.9980
```

Error-gap trend:

```text
approximately 0.021
v
approximately 0.378
v
approximately 2.517
```

## Validity point

The `-6 dB` controlled rerun reproduced the previous AUC:

```text
0.6142
```

This supports pipeline determinism for the compared experiment.

## Correct interpretation

> Under a controlled SNR-only comparison, the same Expert A pipeline improved from AUC 0.6142 at -6 dB to 0.8306 at 0 dB and 0.9980 at +6 dB. Low SNR is strongly indicated as the primary limitation of the observed weak -6 dB anomaly separation.

## Forbidden interpretation

Do not say:

```text
The Autoencoder is perfect.
```

Do not say:

```text
Noise is the only possible limitation.
```

Do not say:

```text
The model is production-ready because +6 dB AUC is 0.998.
```

---

# 17. EXPERT A ARTIFACTS

Current per-SNR artifact design includes:

```text
X_train_ad_<snr_tag>.npy
X_test_ad_<snr_tag>.npy
y_test_ad_<snr_tag>.npy
ad_norm_stats_<snr_tag>.npz
anomaly_detector_<snr_tag>.pt
```

Known summary artifacts:

```text
D:\PDM_Data\MIMII\processed\snr_ad_summary.json
D:\PDM_Data\MIMII\processed\snr_ad_summary.csv
```

Known model examples:

```text
anomaly_detector_minus6dB.pt
anomaly_detector_0dB.pt
anomaly_detector_plus6dB.pt
```

Expert A and completed SNR artifacts are protected.

Do not modify the Expert A architecture or overwrite its artifacts without an explicitly approved experiment.

---

# 18. EXPERT B - ACOUSTIC TIMBRE DIFFERENCE EXPERT

## Recommended class/system name

```text
AcousticTimbreDifferenceExpert
```

## Scientific status

```text
Nishida-inspired adaptation
NOT exact reproduction
```

## Responsibility

Expert B answers:

```text
How does the current anomalous audio differ acoustically from similar normal operation?
```

## Not responsible for

Expert B does not:

```text
decide the original anomaly score
predict RUL
confirm a physical failed component
identify an exact root cause
generate maintenance advice
invent confidence percentages
```

---

# 19. EXPERT B TRIGGER

MVP runtime policy:

```text
Expert A evaluates audio
        |
        v
if anomaly_detected == true
        |
        v
run Expert B on the SAME AUDIO EVENT
```

A later human-review mode may permit Expert B on borderline or normal samples.

That policy must be explicit.

Do not silently characterize unrelated audio.

---

# 20. EXPERT B INPUT

Conceptual input:

```json
{
  "audio_path": "path/to/test.wav",
  "machine_type": "fan",
  "machine_id": "id_00",
  "snr_tag": "minus6dB",
  "expert_a": {
    "anomaly_score": 0.0,
    "threshold": 0.0,
    "is_anomaly": true
  },
  "reference_policy": {
    "k": 30,
    "distance": "euclidean",
    "rank_threshold": null
  }
}
```

Current rule:

```text
same audio event
same machine type
same machine ID
same SNR tag for the first MVP reference policy
```

Cross-SNR or cross-machine reference comparison requires a separate experiment.

---

# 21. EXPERT B REFERENCE POLICY

## Core rule

```text
Fan anomalous audio
v
compare with normal Fan references
```

Not:

```text
Fan anomalous audio
v
compare with normal Valve references
```

## MVP filter

At minimum:

```text
machine_type
machine_id
snr_tag
```

Future MIMII DG metadata may include:

```text
section
domain
operating condition metadata when available
```

## k

Default:

```text
k = 30
```

This is aligned with the paper's experimental setting.

## Distance

Initial MVP:

```text
Euclidean
```

This is a project implementation choice supported by the paper's generic distance formulation.

Output metadata must record it.

---

# 22. EXPERT B EMBEDDING STRATEGY

## MVP embedding

Use the existing Expert A `128`-dimensional bottleneck as:

```text
expert_a_bottleneck_adaptation
```

Rationale:

- existing trained model,
- existing machine-specific normal-acoustic representation,
- no new encoder framework required for integration MVP,
- compatible with the paper's general allowance for an encoder trained on normal data.

## Scientific limitation

The Nishida experiments suggest embedding quality affects timbre-difference performance.

The paper reports experiments with:

```text
MobileNetV2
PANNs
CLAP
BEATs
```

The paper's results indicate that broad pretrained audio encoders can provide useful similarity spaces, and BEATs performed strongly in source-domain timbre MAE for several machine/section settings.

Therefore:

```text
Expert A bottleneck
= MVP adaptation
```

not:

```text
best scientific embedding proven
```

## Future embedding comparison

Possible experiment:

```text
Expert A bottleneck
vs
PANNs
vs
BEATs
```

Potential metrics require an appropriate labeled evaluation dataset.

Do not add these encoders before the MVP is stable.

---

# 23. EXPERT B TIMBRE METRICS

Use AudioCommons timbral models for:

```text
Sharpness
Roughness
Boominess
Brightness
Depth
```

Project naming must normalize AudioCommons naming differences carefully.

For example:

```text
paper attribute: Boominess
AudioCommons model naming may use: Booming
```

The output schema should preserve the project attribute name:

```text
boominess
```

while metadata records the underlying metric/model implementation.

## Critical scientific guardrail

Do not implement:

```text
sharpness = spectral centroid
brightness = spectral rolloff
depth = low-frequency energy
```

and call it Nishida/AudioCommons.

Those may be separate engineered features in another experiment, but they are not transparent substitutes for the selected timbral-model pipeline.

---

# 24. EXPERT B RANK SCORE

For each timbre attribute:

```text
1. compute test timbre value
2. compute timbre values of k selected normal references
3. evaluate the relative rank of the test value
4. produce rank score
```

Current method-spec representation:

```text
rank_score = (r - 1) / k
```

where:

```text
r = position/rank of the test timbre value relative to the local reference values
k = number of selected nearest normal references
```

The implementation must define tie handling explicitly and test it.

Do not invent undocumented tie behavior and describe it as a paper rule.

---

# 25. EXPERT B DIRECTION POLICY

Initial MVP:

```text
rank_threshold = None
```

Output:

```json
{
  "rank_score": 0.93,
  "direction": null,
  "direction_code": null
}
```

The MVP may explain the continuous rank semantically:

```text
high relative to selected normal references
middle relative to selected normal references
low relative to selected normal references
```

but must not convert to official:

```text
INCREASED
UNCHANGED
DECREASED
```

without an explicit threshold policy.

## Future direction policy

When threshold `t` is approved, the mapping must be:

- documented,
- versioned,
- included in output metadata,
- evaluated on appropriate timbre-difference labels.

Do not silently tune `t` on the same samples used for final reporting.

---

# 26. EXPERT B OUTPUT SCHEMA

Recommended MVP schema:

```json
{
  "expert": "AcousticTimbreDifferenceExpert",
  "method": {
    "paper": "Nishida et al. 2024, arXiv:2410.22033",
    "status": "adaptation_not_exact_reproduction",
    "embedding_model": "expert_a_bottleneck_adaptation",
    "timbre_model": "AudioCommons timbral_models",
    "k": 30,
    "distance": "euclidean",
    "distance_status": "project_choice",
    "rank_threshold": null
  },
  "input_audio": {
    "path": "string",
    "machine_type": "fan",
    "machine_id": "id_00",
    "snr_tag": "minus6dB"
  },
  "expert_a": {
    "anomaly_score": 0.0,
    "threshold": 0.0,
    "is_anomaly": true
  },
  "references": {
    "pool_size": 0,
    "selected_count": 30,
    "filter": {
      "machine_type": "fan",
      "machine_id": "id_00",
      "snr_tag": "minus6dB"
    },
    "neighbors": [
      {
        "path": "string",
        "distance": 0.0,
        "rank": 1
      }
    ]
  },
  "timbre_differences": {
    "sharpness": {
      "test_value": 0.0,
      "reference_values": [],
      "rank_score": 0.0,
      "direction": null,
      "direction_code": null
    },
    "roughness": {},
    "boominess": {},
    "brightness": {},
    "depth": {}
  },
  "warnings": [
    "No paper-style timbre ground-truth labels are available for the current Fan SNR dataset. Output is acoustic characterization, not validated root-cause diagnosis."
  ]
}
```

No field named:

```text
fault_confidence
root_cause_confidence
bearing_damage_probability
rul_seconds
```

may be invented in this stage.

---

# 27. EXPERT B CURRENT IMPLEMENTATION STATUS

Current project status at the time of this file:

```text
Paper forensic specification
-> DONE

Initial Expert B implementation
-> PARTIALLY IMPLEMENTED

Reference-index smoke job
-> PERFORMANCE BLOCKER IDENTIFIED

Scientific timbre accuracy evaluation
-> BLOCKED BY LABEL/DATA AVAILABILITY
```

Current proposed/observed Expert B files include:

```text
src/models/timbre_difference.py
src/utils/audio_reference_index.py
scripts/build_timbre_reference_index.py
scripts/run_expert_b_smoke.py
tests/test_timbre_difference.py
```

Repository reality must be inspected before marking each file complete.

---

# 28. CURRENT EXPERT B PERFORMANCE BLOCKER

Observed command:

```powershell
python scripts\build_timbre_reference_index.py `
  --machine-type fan `
  --machine-id id_00 `
  --snr-tag minus6dB `
  --limit 40
```

Observed runtime behavior:

```text
only 40 WAV files requested
process ran CPU-bound for hours
Python CPU increased by 9.53 CPU seconds over 10 wall-clock seconds
```

Interpretation:

```text
process was active
NOT frozen
BUT runtime was computationally pathological for the requested bounded job
```

The job was stopped before completion.

## Immediate technical rule

Do not rerun the 40-file reference-index job blindly.

Use:

```text
$performance-forensics
```

Required workflow:

```text
trace one-WAV call graph
v
profile one sample
v
time each stage
v
profile three samples
v
check scaling
v
identify measured bottleneck
v
optimize verified redundant work only
v
benchmark before/after
v
estimate 40-file runtime
v
run 40 only if reasonable
```

## Scientific behavior must remain unchanged

Performance optimization may use:

```text
load-once/reuse when supported
cache deterministic results
move reusable initialization outside loops
avoid duplicate embedding extraction
avoid duplicate timbre computation
safe batching when output-equivalent
```

Performance optimization must not:

```text
replace AudioCommons metrics with generic features
reduce k silently
mix SNR conditions
skip difficult files silently
change rank semantics
change Expert A architecture
```

---

# 29. REFERENCE INDEX ARTIFACT

Recommended artifact identity:

```text
timbre_reference_index_<machine_type>_<machine_id>_<snr_tag>
```

Example:

```text
D:\PDM_Data\MIMII\processed\
timbre_reference_index_fan_id00_minus6dB.npz
```

If one file format becomes awkward for:

```text
paths
metadata
embeddings
timbre values
```

a transparent paired design may be used:

```text
.npz
+
.json
```

The artifact must record:

```text
schema version
machine type
machine ID
SNR/domain tag
embedding model identity
model artifact identity/hash if practical
normalization artifact identity
distance policy
timbre model package/version
audio paths or stable IDs
embeddings
timbre values
creation timestamp
number of reference clips
```

Do not save only anonymous arrays with no machine metadata.

---

# 30. EXPERT B EVALUATION LEVELS

## Level 1 - integration and qualitative characterization

Current Fan SNR data are sufficient for:

```text
Expert A -> Expert B technical integration
same-audio validation
same-machine reference filtering
kNN reference retrieval
five timbre metric calculation
rank-score calculation
schema validation
qualitative inspection
```

Required assertions:

```text
reference pool >= k
all selected references match required machine metadata
five timbre attributes exist
metric values are finite
rank scores are in [0,1]
direction is null when threshold is null
no confidence percentage
no root-cause diagnosis
same audio event is preserved
```

## Level 2 - scientific timbre-difference accuracy

Current Fan SNR data alone are not sufficient for paper-equivalent claims such as:

```text
Expert B direction accuracy = X%
Expert B MAE = paper-comparable result
```

A suitable evaluation requires:

```text
ground-truth timbre difference labels
or
a transparent annotation-generation protocol with appropriate condition matching
```

Preferred future route:

```text
MIMII DG
+
Nishida-style timbre-difference annotations/assets when available
```

or a clearly disclosed local annotation study.

---

# 31. STRUCTURED HEALTH CONTEXT

## Purpose

The Context Translation Layer is deterministic Python.

It combines expert outputs into a stable machine-readable evidence object.

It is not an LLM.

## Responsibilities

```text
preserve machine identity
preserve audio-event identity
preserve Expert A numbers
preserve Expert B method metadata
preserve reference metadata
record scientific limitations
produce versioned JSON
```

## Example schema

```json
{
  "schema_version": "1.0",
  "event_id": "fan_id00_minus6dB_example",
  "asset": {
    "machine_type": "fan",
    "machine_id": "id_00"
  },
  "acoustic_context": {
    "snr_tag": "minus6dB"
  },
  "anomaly_detection": {
    "expert": "ExpertA",
    "detected": true,
    "score": 0.80,
    "threshold": 0.593
  },
  "acoustic_difference": {
    "expert": "AcousticTimbreDifferenceExpert",
    "method_status": "adaptation_not_exact_reproduction",
    "reference_count": 30,
    "embedding_model": "expert_a_bottleneck_adaptation",
    "distance": "euclidean",
    "rank_threshold": null,
    "sharpness": {
      "rank_score": 0.93,
      "direction": null
    },
    "roughness": {
      "rank_score": 0.84,
      "direction": null
    },
    "boominess": {
      "rank_score": 0.47,
      "direction": null
    },
    "brightness": {
      "rank_score": 0.90,
      "direction": null
    },
    "depth": {
      "rank_score": 0.12,
      "direction": null
    }
  },
  "system_limits": {
    "specific_fault_confirmed": false,
    "root_cause_diagnosis_available": false,
    "rul_available": false,
    "paper_equivalent_timbre_accuracy_validated": false
  }
}
```

The `system_limits` field is mandatory.

---

# 32. LLM LAYER

## Principle

The LLM interprets structured evidence.

The LLM does not replace Expert A or Expert B.

## LLM input

```text
Structured Health Context
+
retrieved maintenance knowledge
```

## LLM responsibilities

```text
explain anomaly evidence in plain language
explain relative timbre-rank behavior
state uncertainty
distinguish observations from hypotheses
produce technician-facing summary
recommend grounded inspection steps
```

## LLM must not

```text
invent a component fault
invent RUL
invent confidence percentages
pretend rank score is failure probability
claim a timbre metric proves root cause
claim a maintenance manual said something not retrieved
```

## Example acceptable wording

> The fan was flagged as acoustically anomalous by the anomaly detector. Relative to similar normal fan recordings from the same machine and SNR condition, the current sound has high sharpness and roughness rank scores. These are acoustic differences, not a confirmed component-level diagnosis. A mechanical and acoustic inspection is recommended.

## Example forbidden wording

> The bearing is 93% damaged and will fail in 600 seconds.

---

# 33. RAG LAYER

## Purpose

RAG supports maintenance recommendations with approved documents.

Possible knowledge sources:

```text
fan maintenance manuals
manufacturer inspection procedures
troubleshooting guides
preventive maintenance checklists
internal approved maintenance procedures
industrial acoustic-monitoring guidance
```

## Evidence separation

The final system must distinguish:

```text
OBSERVED ML EVIDENCE
```

from:

```text
RETRIEVED MAINTENANCE GUIDANCE
```

from:

```text
POSSIBLE INSPECTION HYPOTHESIS
```

Example:

```text
Observed:
Sharpness rank is high relative to selected normal references.

Retrieved guidance:
The manual recommends checking mounting and rotating components when abnormal mechanical noise is reported.

Recommendation:
Inspect mounting and rotating components.

Not claimed:
A specific component has been confirmed damaged.
```

## RAG requirements

Future RAG implementation should preserve:

```text
source document ID
retrieved section/chunk
retrieval score if supported
citation/reference in generated recommendation
document version
```

Do not use random web snippets as the production maintenance knowledge base.

---

# 34. LLM / AGENT DESIGN

Recommended minimum agents:

## Diagnostic Explanation Agent

Input:

```text
Structured Health Context
```

Output:

```text
plain-language explanation
uncertainty statement
evidence summary
```

## Maintenance Communication Agent

Input:

```text
Structured Health Context
+
RAG evidence
```

Output:

```text
inspection priority
recommended next actions
technician-facing summary
```

## Optional Robustness Agent

Offline only.

Inspired by MIMII-Agent.

Possible responsibilities:

```text
interpret approved anomaly scenario descriptions
select approved audio transformation functions
generate synthetic evaluation scenarios
run bounded Expert A robustness evaluation
summarize relative detection difficulty
```

The robustness agent must not silently:

```text
retrain Expert A
change thresholds
promote synthetic audio to real ground truth
```

---

# 35. DASHBOARD

The dashboard presents evidence in layers.

## Machine card

Example:

```text
Machine Type: Fan
Machine ID: id_00
State: ANOMALOUS
Anomaly Score: 0.80
Expert A Threshold: 0.593
Acoustic Condition: minus6dB experiment
```

## Acoustic difference card

When `rank_threshold = None`, do not display official directional arrows as validated direction classes.

Prefer:

```text
Sharpness   rank 0.93   High vs local normal references
Roughness   rank 0.84   High vs local normal references
Boominess   rank 0.47   Near local normal middle
Brightness  rank 0.90   High vs local normal references
Depth       rank 0.12   Low vs local normal references
```

If a validated threshold is later configured:

```text
Sharpness   Increased
Roughness   Increased
Boominess   Unchanged
Brightness  Increased
Depth       Decreased
```

The dashboard must clearly record the active method version.

## Explanation card

LLM explanation.

## Recommendation card

Grounded maintenance recommendation.

## Evidence views

Potential visualizations:

```text
current Log-Mel spectrogram
selected normal-reference spectrograms
Expert A reconstruction-error distribution
SNR AUC comparison
nearest-neighbor distances
five timbre rank scores
retrieved maintenance sources
```

---

# 36. SCIENTIFIC CLAIM MATRIX

## Supported now

### Claim

> Expert A detects anomalous Fan `id_00` sounds under the evaluated project split.

Evidence:

```text
three controlled SNR experiments
```

### Claim

> Expert A performance is strongly sensitive to SNR.

Evidence:

```text
AUC 0.6142 -> 0.8306 -> 0.9980
```

### Claim

> Low SNR is strongly indicated as the primary limitation of the weak -6 dB separation in the controlled experiment.

Evidence:

```text
same pipeline
same architecture
same experimental logic
large monotonic AUC improvement with SNR
```

## Integration claim enabled after Expert B smoke

> The system can characterize an Expert A-detected audio event using local same-machine normal references and five timbre metrics.

This is an integration/characterization claim.

## Not yet supported

> Expert B accurately predicts timbre direction.

Blocker:

```text
no paper-style timbre difference ground-truth labels in current Fan SNR data
```

> The system diagnoses exact physical root cause.

Blocker:

```text
no validated fault-diagnosis model
```

> LLM explanations are grounded.

Blocker:

```text
LLM + RAG evaluation not implemented
```

> Maintenance recommendations are grounded.

Blocker:

```text
approved maintenance knowledge base and retrieval evaluation not implemented
```

> Architecture generalizes to Pump.

Blocker:

```text
Pump end-to-end evaluation not complete
```

> Architecture generalizes to Valve.

Blocker:

```text
Valve end-to-end evaluation not complete
```

> Architecture generalizes to Slide Rail.

Blocker:

```text
Slide Rail end-to-end evaluation not complete
```

> System is robust to domain shift.

Blocker:

```text
MIMII DG robustness phase not complete
```

> System predicts RUL.

Status:

```text
OUTSIDE ACTIVE PROJECT SCOPE
```

---

# 37. ALLOWED CLAIMS

Allowed project wording:

> The system performs acoustic machine condition monitoring using anomalous sound detection.

> Expert A uses a normal-only convolutional autoencoder and reconstruction error to identify departures from learned normal Fan audio behavior.

> A controlled three-SNR experiment showed AUC values of 0.6142, 0.8306, and 0.9980 at -6, 0, and +6 dB respectively.

> The controlled SNR results strongly indicate low SNR as the primary limitation of the observed weak -6 dB anomaly separation.

> Expert B is designed to characterize acoustic differences relative to similar normal sounds from the same machine domain.

> Expert B uses five interpretable timbre attributes motivated by Nishida et al.

> The LLM layer is designed to explain structured acoustic evidence rather than diagnose faults directly from raw audio.

> RAG is intended to ground maintenance recommendations in approved maintenance documents.

---

# 38. FORBIDDEN CLAIMS

Do not say:

```text
The system predicts Remaining Useful Life.
```

Do not say:

```text
The system predicts exact time to failure.
```

Do not say:

```text
The bearing is definitely damaged.
```

Do not say:

```text
The fan motor has failed.
```

unless a future diagnosis model and labels support that exact claim.

Do not say:

```text
Expert B determines root cause.
```

Do not say:

```text
rank_score = failure probability
```

Do not say:

```text
rank_score = confidence
```

Do not say:

```text
The LLM diagnoses directly from raw audio.
```

Do not say:

```text
We exactly reproduce Nishida et al.
```

Do not say:

```text
The Autoencoder is perfect.
```

Do not say:

```text
Noise is the only limitation.
```

Do not say:

```text
One universal model works for all MIMII machines.
```

unless experimentally demonstrated.

---

# 39. TARGET REPOSITORY STRUCTURE

Target structure:

```text
IOT/
|-- AGENTS.md
|-- CLAUDE.md
|-- project_state.json
|-- requirements.txt
|-- REPORT.md
|-- REPORT_PHASE1_2.md
|
|-- .agents/
|   \-- skills/
|       |-- project-architect/
|       |   \-- SKILL.md
|       |-- paper-forensics/
|       |   \-- SKILL.md
|       |-- scientific-implementer/
|       |   \-- SKILL.md
|       \-- performance-forensics/
|           \-- SKILL.md
|
|-- src/
|   |-- __init__.py
|   |-- config.py
|   |-- data_loader.py
|   |
|   |-- models/
|   |   |-- __init__.py
|   |   |-- anomaly_detector.py
|   |   \-- timbre_difference.py
|   |
|   |-- utils/
|   |   \-- audio_reference_index.py
|   |
|   |-- context/
|   |   |-- __init__.py
|   |   |-- schemas.py
|   |   \-- translator.py
|   |
|   |-- agents/
|   |   |-- __init__.py
|   |   |-- diagnostic_agent.py
|   |   \-- maintenance_agent.py
|   |
|   \-- rag/
|       |-- __init__.py
|       |-- knowledge_base.py
|       \-- retriever.py
|
|-- scripts/
|   |-- snr_stage1.py
|   |-- run_snr_experiments.py
|   |-- build_timbre_reference_index.py
|   |-- run_expert_b_smoke.py
|   \-- run_end_to_end_demo.py
|
|-- app/
|   \-- dashboard.py
|
|-- docs/
|   |-- MASTER_PROJECT_ROADMAP.md
|   |-- EXPERT_B_NISHIDA_METHOD_SPEC.md
|   |-- expert_a_results.md
|   |-- expert_b_method.md
|   |-- evaluation_protocol.md
|   \-- academic_claims.md
|
\-- tests/
    |-- test_expert_a.py
    |-- test_timbre_difference.py
    |-- test_reference_index.py
    |-- test_context_schema.py
    |-- test_llm_guardrails.py
    \-- test_rag_grounding.py
```

Do not overengineer beyond this without a real need.

---

# 40. LEGACY RUL / PRONOSTIA POLICY

Legacy repository references may still exist in:

```text
src/config.py
REPORT.md
historical documentation
old comments
old RUL constants
```

They must be classified before removal.

Possible labels:

```text
HISTORICAL_RECORD
LEGACY_ACTIVE_CONFIG
LEGACY_DOCUMENTATION
OBSOLETE_ARCHITECTURE
STILL_VALID_SHARED_CONTEXT
```

Do not delete historical reports.

When source cleanup occurs:

```text
inspect references
v
produce impact map
v
remove active dead RUL wiring
v
run tests
v
confirm Expert A artifacts unchanged
```

Do not allow a legacy RUL constant to reappear in the active context schema, dashboard, or LLM prompt.

---

# 41. CODEX SKILL ROUTING

Repository-specific skills:

```text
$project-architect
$paper-forensics
$scientific-implementer
$performance-forensics
```

## project-architect

Use for:

```text
major architecture decision
project pivot
new expert/model
new dataset
ambiguous project-level task
```

Behavior:

```text
inspect
challenge assumptions
separate facts from decisions
identify risks
plan
define stop condition
STOP before coding unless implementation is explicitly approved
```

## paper-forensics

Use for:

```text
paper-based method
dataset paper
reproduction claim
research-method adaptation
```

Behavior:

```text
primary sources
exact task
dataset
labels
equations
models
training
inference
evaluation
assets
limitations
repo gap
bounded adaptation plan
STOP
```

## scientific-implementer

Use after an approved method/architecture plan.

Execution ladder:

```text
UNIT TEST
v
ONE-SAMPLE SMOKE
v
THREE-SAMPLE TIMING
v
SMALL BOUNDED RUN
v
RUNTIME ESTIMATE
v
FULL RUN ONLY IF REASONABLE
```

## performance-forensics

Use for:

```text
unexpectedly slow process
hang
high CPU
memory growth
slow preprocessing
slow indexing
unclear runtime bottleneck
```

Behavior:

```text
identify exact process
trace call graph
profile one sample
profile three samples
measure stages
find measured root cause
optimize equivalent redundant work only
benchmark before/after
estimate full runtime
STOP
```

---

# 42. EXECUTION PRINCIPLE

No future data/model task may jump directly from:

```text
code written
```

to:

```text
full dataset job
```

Mandatory ladder:

```text
UNIT TEST
v
ONE SAMPLE
v
THREE SAMPLES
v
SMALL BOUNDED JOB
v
RUNTIME ESTIMATE
v
FULL JOB
```

If a 40-file task unexpectedly estimates hours:

```text
STOP
v
$performance-forensics
```

Do not say:

```text
CPU is active, therefore wait forever.
```

Active computation can still be pathological.

---

# 43. PROJECT PHASES

## Phase 0 - Source-of-truth correction

Goal:

```text
replace old active CLAUDE.md with this file
archive old RUL CLAUDE context
ensure AGENTS.md points to current CLAUDE.md
```

Status:

```text
CURRENT DOCUMENT PREPARED
```

## Phase 1 - Expert B performance forensics

Goal:

```text
find why 40 reference WAV files took hours
```

Skill:

```text
$performance-forensics
```

Definition of done:

```text
one-file stage timing
three-file scaling
root cause
scientifically equivalent optimization
before/after benchmark
estimated 40-file runtime
```

## Phase 2 - Expert B integration MVP

Goal:

```text
build bounded normal reference index
run one anomalous same-audio Expert A -> Expert B smoke
produce actual JSON
```

Skill:

```text
$scientific-implementer
```

Definition of done:

```text
same machine
same audio
30 references
five timbre values
five rank scores
no direction without threshold
no root-cause claim
schema tests pass
```

## Phase 3 - Expert B qualitative evidence protocol

Goal:

```text
design repeatable qualitative characterization review
```

Potential outputs:

```text
normal control examples
abnormal examples
neighbor inspection
rank-score plots
reference-distance review
```

No quantitative direction-accuracy claim.

## Phase 4 - Structured Health Context

Goal:

```text
implement versioned deterministic context schema
```

Definition of done:

```text
Expert A result preserved
Expert B metadata preserved
event identity preserved
system_limits required
JSON schema tests pass
```

## Phase 5 - LLM explanation agent

Goal:

```text
explain structured evidence cautiously
```

Definition of done:

```text
no raw-audio diagnosis
no RUL
no confidence invention
observations separated from hypotheses
guardrail tests pass
```

## Phase 6 - Maintenance RAG

Goal:

```text
ground recommendations in approved documents
```

Definition of done:

```text
documents indexed
retrieval tested
retrieved sources preserved
recommendations cite/trace source evidence
no unsupported maintenance claim
```

## Phase 7 - End-to-end orchestration

Flow:

```text
audio
v
Expert A
v
conditional Expert B
v
context
v
RAG
v
LLM
v
final result
```

Definition of done:

```text
one command/API path
same event identity end-to-end
actual JSON saved
errors handled
tests pass
```

## Phase 8 - Dashboard

Goal:

```text
visualize state, evidence, explanation, recommendation
```

Definition of done:

```text
machine card
anomaly evidence
timbre rank view
LLM explanation
RAG recommendation
method limitations visible
```

## Phase 9 - Additional MIMII machine generalization

Targets:

```text
pump
valve
slide rail
```

Do not mix all normals into one universal model as the first baseline.

Initial policy:

```text
same architecture
machine-specific training/artifacts
machine-specific reference indexes
```

Research questions:

```text
Does same architecture transfer?
How does SNR sensitivity differ?
Are timbre attributes useful across machine types?
Does the LLM stay grounded?
```

## Phase 10 - MIMII DG robustness

Goal:

```text
evaluate domain-shift behavior
```

Questions:

```text
Expert A robustness?
Expert B reference robustness?
source vs target domain?
normal shift mistaken for anomaly?
```

## Phase 11 - Optional MIMII-Agent-inspired evaluation

Goal:

```text
relative robustness evaluation with approved synthetic anomaly transformations
```

This phase is optional and begins only after the core system works.

---

# 44. PROJECT STATE SUMMARY

## DONE

```text
MIMII Fan id_00 staging for three SNR variants
Log-Mel pipeline
Expert A ConvAutoencoder
normal-only training
Expert A anomaly scoring
Expert A thresholding
per-SNR artifacts
controlled three-SNR experiment
SNR summary JSON/CSV
Expert B primary-paper forensic analysis
Codex skill system
AGENTS.md skill routing
```

## PARTIAL

```text
Expert B implementation
normal-reference index
Expert B smoke pipeline
legacy RUL cleanup
```

## BLOCKED / REQUIRES INVESTIGATION

```text
Expert B reference-index runtime
paper-equivalent Expert B accuracy evaluation
```

## TODO

```text
Structured Health Context
LLM explanation agent
maintenance RAG
end-to-end orchestrator
dashboard
Pump generalization
Valve generalization
Slide Rail generalization
MIMII DG robustness
optional MIMII-Agent-inspired evaluation
```

---

# 45. IMMEDIATE NEXT TECHNICAL TASK

Use:

```text
$performance-forensics
```

Target:

```text
scripts/build_timbre_reference_index.py
```

Known bounded command:

```powershell
python scripts\build_timbre_reference_index.py `
  --machine-type fan `
  --machine-id id_00 `
  --snr-tag minus6dB `
  --limit 40
```

Do not immediately rerun it.

Required output:

```text
PROCESS:
CALL GRAPH:
ROOT CAUSE:
ONE-SAMPLE:
THREE-SAMPLE:
SCALING:
CHANGE:
BEFORE:
AFTER:
ESTIMATED FULL RUNTIME:
SCIENTIFIC BEHAVIOR CHANGED:
STOP:
```

Stop after the bounded benchmark.

Do not continue automatically into the abnormal Expert B smoke until the performance result is reviewed.

---

# 46. FINAL PRESENTATION STORY

Use this project story:

> Industrial anomalous sound detectors can identify when machine audio departs from normal behavior, but a raw anomaly score is difficult for maintenance technicians to interpret. Our system uses a sequential multi-expert architecture on the same machine audio. Expert A detects anomalous sounds using a normal-only convolutional autoencoder. A controlled SNR study showed that the same detector improved from AUC 0.6142 at -6 dB to 0.8306 at 0 dB and 0.9980 at +6 dB, strongly indicating that low SNR is the primary limitation of the observed weak -6 dB separation. When Expert A identifies an anomalous audio event, Expert B compares that same sound with acoustically similar normal recordings from the same machine domain and characterizes its relative timbre behavior using sharpness, roughness, boominess, brightness, and depth. The expert outputs are translated into structured evidence for an LLM-based maintenance assistant. The LLM explains the evidence and uses retrieved maintenance knowledge to recommend inspection actions while explicitly avoiding unsupported component-level diagnoses or Remaining Useful Life claims.

Simple version:

```text
Expert A:
Is the machine sound abnormal?

Expert B:
How is the same sound acoustically different from similar normal operation?

LLM + RAG:
What does the evidence mean to the technician, and what grounded inspection action is appropriate?
```

---

# 47. REFERENCES

## [P1] MIMII

H. Purohit, R. Tanabe, K. Ichige, T. Endo, Y. Nikaido, K. Suefusa, and Y. Kawaguchi.

**MIMII Dataset: Sound Dataset for Malfunctioning Industrial Machine Investigation and Inspection.**

2019.

```text
arXiv:1909.09347
https://arxiv.org/abs/1909.09347
https://zenodo.org/records/3384388
```

## [P2] Timbre Difference Capturing

T. Nishida, H. Purohit, K. Dohi, T. Endo, and Y. Kawaguchi.

**Timbre Difference Capturing in Anomalous Sound Detection.**

2024.

```text
arXiv:2410.22033
https://arxiv.org/abs/2410.22033
```

## [P3] MIMII DG

K. Dohi, T. Nishida, H. Purohit, R. Tanabe, T. Endo, M. Yamamoto, Y. Nikaido, and Y. Kawaguchi.

**MIMII DG: Sound Dataset for Malfunctioning Industrial Machine Investigation and Inspection for Domain Generalization Task.**

2022.

```text
arXiv:2205.13879
https://arxiv.org/abs/2205.13879
https://zenodo.org/records/6529888
```

## [P4] MIMII-Agent

H. Purohit, T. Nishida, K. Dohi, T. Endo, and Y. Kawaguchi.

**MIMII-Agent: Leveraging LLMs with Function Calling for Relative Evaluation of Anomalous Sound Detection.**

2025.

```text
arXiv:2507.20666
https://arxiv.org/abs/2507.20666
```

## [A1] AudioCommons Timbral Models

```text
https://github.com/AudioCommons/timbral_models
```

## [A2] PANNs public implementation

```text
https://github.com/qiuqiangkong/audioset_tagging_cnn
```

## [A3] Microsoft CLAP

```text
https://github.com/microsoft/CLAP
```

## [A4] Microsoft BEATs

```text
https://github.com/microsoft/unilm/tree/master/beats
```

---

# 48. MASTER GUARDRAILS

1. Same machine.
2. Same audio event.
3. Expert A detects.
4. Expert B characterizes acoustic difference.
5. Expert B does not diagnose physical root cause.
6. Expert B does not predict RUL.
7. Rank score is not a probability or confidence.
8. No direction label without an explicit threshold policy.
9. LLM reasons over structured evidence.
10. RAG grounds maintenance recommendations.
11. Fan `id_00` is the reference MVP.
12. Reusable interfaces remain machine-aware.
13. Additional machines are a later generalization phase.
14. Preserve completed Expert A and SNR artifacts.
15. Paper fact, repository fact, project choice, and inference must remain distinguishable.
16. Do not claim exact reproduction without proof.
17. Unit test before sample smoke.
18. One sample before three samples.
19. Three-sample timing before a larger data job.
20. Unexpected runtime routes to performance forensics.
21. Never silently wait hours on a bounded job with no timing estimate.
22. Never invent missing labels, thresholds, or formulas.
23. Never reintroduce PRONOSTIA/RUL into active runtime planning unless Yosef explicitly redesigns the project.

---

# 49. FINAL ACTIVE ARCHITECTURE

```text
                INDUSTRIAL MACHINE
                         |
                         v
                    AUDIO EVENT
                         |
                         v
                    EXPERT A
          CONVOLUTIONAL AUTOENCODER
                  ANOMALY SCORE
                         |
                 +-------+-------+
                 |               |
              NORMAL          ANOMALOUS
                 |               |
                 |               v
                 |            EXPERT B
                 |    LOCAL NORMAL-REFERENCE
                 |    TIMBRE CHARACTERIZATION
                 |               |
                 |               v
                 |      FIVE TIMBRE RANK SCORES
                 |               |
                 +-------+-------+
                         |
                         v
              STRUCTURED HEALTH CONTEXT
                         |
                         +------------------+
                         |                  |
                         v                  v
                     LLM AGENT             RAG
                    EXPLANATION      MAINTENANCE KNOWLEDGE
                         |                  |
                         +---------+--------+
                                   |
                                   v
                      GROUNDED TECHNICIAN OUTPUT
                                   |
                                   v
                              DASHBOARD
```

Optional future offline branch:

```text
MIMII-AGENT-INSPIRED ROBUSTNESS EVALUATION
                         |
                         v
SYNTHETIC MACHINE-SPECIFIC ANOMALY SCENARIOS
                         |
                         v
CHALLENGE EXPERT A
                         |
                         v
RELATIVE ROBUSTNESS REPORT
```

This is the active project.

RUL and PRONOSTIA are legacy history only.

