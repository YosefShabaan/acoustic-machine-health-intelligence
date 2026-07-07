# Expert B Method Specification From Nishida et al. 2024

Primary paper inspected: Tomoya Nishida, Harsh Purohit, Kota Dohi, Takashi Endo, Yohei Kawaguchi, "Timbre Difference Capturing in Anomalous Sound Detection", arXiv:2410.22033, submitted 2024-10-29.

Repository inspected: `D:\IOT`

Scope of this document: forensic method inspection and minimum Expert B design only. No Expert B implementation is performed here.

## Sources Used

- Nishida et al. 2024 paper: https://arxiv.org/abs/2410.22033 and PDF https://arxiv.org/pdf/2410.22033
- MIMII DG paper: https://arxiv.org/abs/2205.13879
- AudioCommons timbral models repository: https://github.com/AudioCommons/timbral_models
- AudioCommons timbral model source files:
  - https://raw.githubusercontent.com/AudioCommons/timbral_models/master/timbral_models/Timbral_Sharpness.py
  - https://raw.githubusercontent.com/AudioCommons/timbral_models/master/timbral_models/Timbral_Roughness.py
  - https://raw.githubusercontent.com/AudioCommons/timbral_models/master/timbral_models/Timbral_Booming.py
  - https://raw.githubusercontent.com/AudioCommons/timbral_models/master/timbral_models/Timbral_Brightness.py
  - https://raw.githubusercontent.com/AudioCommons/timbral_models/master/timbral_models/Timbral_Depth.py
- DCASE 2022 Task 2 AE baseline repository: https://github.com/Kota-Dohi/dcase2022_task2_baseline_ae
- PANNs official repository, for public pretrained embedding availability: https://github.com/qiuqiangkong/audioset_tagging_cnn
- CLAP official repository, for public pretrained embedding availability: https://github.com/microsoft/CLAP
- BEATs official repository, for public pretrained embedding availability: https://github.com/microsoft/unilm/tree/master/beats

## 1. Exact Paper Task

PAPER TASK:

The paper defines joint unsupervised anomalous sound detection (UASD) and timbre difference capturing. UASD classifies a test sound as normal or anomalous. Timbre difference capturing then assigns, for each predefined timbre attribute, whether the anomalous sound increased, decreased, or did not change relative to comparable normal sounds.

The paper's key change from free-form explanation/captioning is that it restricts explanation to five timbre attributes: sharpness, roughness, boominess, brightness, and depth.

INPUT:

- Training phase: normal audio samples only, written in the paper as `{x_n^(tr)}_{n=1}^N`.
- Inference phase: test audio samples, which may be normal or anomalous. The paper assumes test-time additional attributes such as machine speed, recording condition, or domain labels are not available.
- Optional metadata may exist for training samples, but the proposed inference method is not built around requiring it.

OUTPUT:

- UASD anomaly score:

```text
A(x_te) = (1 / k) * sum_{i=1..k} d(E(x_te), E(x_ni^tr))
```

where `E(.)` is an audio encoder, `d(.)` is an embedding distance such as Euclidean or cosine distance, and `x_ni^tr` is the i-th nearest normal training sample.

- Timbre difference score per timbre attribute `l`:

```text
score_l(x_te) = (r - 1) / k
```

where `r` is the rank of the test timbre value `T_l(x_te)` among the set `{T_l(x_te), T_l(x_n1^tr), ..., T_l(x_nk^tr)}` when sorted ascending.

- Timbre difference label per attribute:

```text
label_l = -1  if score_l <= t
label_l =  0  if t < score_l < 1 - t
label_l =  1  if 1 - t <= score_l
```

with `-1 = decreased`, `0 = no change`, `1 = increased`.

TRAINING REQUIREMENTS:

- No anomalous audio is required for training the paper's proposed inference method.
- No timbre labels are required for training the proposed method.
- Timbral metric models are externally supplied objective/learned models from psychoacoustic timbre modeling, not trained on this project dataset by the Nishida method.
- The paper's experimental MobileNetV2 encoder is trained on normal MIMII DG data for a machine-attribute classification task, but the paper explicitly states the audio encoder can be pretrained, trained from scratch on normal data, or pretrained and fine-tuned.

INFERENCE FLOW:

```text
training normal audio + test audio
-> audio encoder E(.)
-> embeddings for normal training samples and test sample
-> kNN search in embedding space over normal training samples
-> anomaly score = mean kNN distance
-> timbral models compute five timbre values for test and normal references
-> rank test timbre value among k normal reference timbre values plus test value
-> rank score per attribute
-> threshold rank score into decreased / unchanged / increased
```

Important separation for this repository: Nishida et al. propose one joint kNN framework for both UASD and timbre difference capturing. Our current project already has Expert A as the UASD model. Therefore, the minimum repository Expert B should reuse Expert A's anomaly decision and implement only the same-audio difference characterization side as an adaptation, not as an exact full-paper reproduction.

## 2. Datasets And Labels

Exact datasets used:

- MIMII DG, not the original MIMII fan id_00 dataset currently used as the MVP reference implementation.
- MIMII DG contains five machine types: fan, gearbox, bearing, slide rail/slider, and valve.
- Each machine type has three sections: section 00, section 01, section 02.
- Each section includes source-domain and target-domain data.
- MIMII DG is noisy, created by mixing machine recordings with factory noise.
- The Nishida paper additionally used clean originally recorded machine sounds and anomaly-cause information owned by the authors to create timbre-difference ground-truth labels. These clean data and anomaly-cause mappings are not part of the normal public MIMII DG task interface as described in the paper.

Exact role of MIMII DG:

- MIMII DG supplies the UASD audio dataset and noisy test samples to which generated timbre-difference labels are assigned.
- It is the evaluation substrate for the paper's joint UASD and timbre-difference experiment.

Domain setup:

- MIMII DG has source and target domains per section.
- The MIMII DG paper states each section has 990 source-domain normal training samples and 10 target-domain normal training samples. Test data contain 50 normal and 50 anomalous samples for both source and target domains.
- DCASE 2022 Task 2 focuses on domain generalization where the domain of each test sample is not provided and one threshold is expected to work across domains.

Timbre-difference annotations:

- The paper's ground-truth timbre-difference labels are generated automatically, not manually written captions.
- For each clean-data section, condition `m`, anomaly cause `q`, and timbre attribute `l`, the paper computes:

```text
tilde_y_{m,q,l} = AUC(T_l(D_m^tr), T_l(D_{m,q}^anom))
```

where `D_m^tr` is clean normal data recorded under condition `m`, and `D_{m,q}^anom` is clean anomalous data recorded under the same condition and anomaly cause.

- It then applies the same three-way thresholding style as the inference rule, but with a separate ground-truth threshold `t'`.
- The paper states `t' = 0.05` after observing the generated scores.
- The same label vector is assigned to anomalous noisy MIMII DG samples that correspond to the same condition and anomaly cause.

Number/type of labels:

- Five labels per anomalous test sample, one for each attribute.
- Each label is ordinal: `{-1, 0, 1}` = decreased, unchanged, increased.
- Table I in the paper gives counts by machine and section. For Fan:
  - section 00: `#g=3`, `#u=2`, label ratio `-1/0/1 = 1/6/3`
  - section 01: `#g=7`, `#u=6`, label ratio `-1/0/1 = 7/6/17`
  - section 02: `#g=3`, `#u=3`, label ratio `-1/0/1 = 5/9/1`

Train/validation/test organization:

- The Nishida paper uses MIMII DG's normal training data for kNN reference selection and test data for UASD/timbre difference evaluation.
- The paper does not describe a separate validation split for selecting the inference timbre threshold `t`.
- The paper explicitly reports `k=30`; it also reports similar results for `k` around 10 to 40.
- The paper reports `t'=0.05` for ground-truth label creation. It does not explicitly state the value of the inference threshold `t` in the experimental conditions. This is a reproducibility blocker for exact label reproduction.

Whether our current MIMII fan id_00 data can evaluate the paper task:

- It can run an integration smoke test for "compute timbre values and compare an abnormal clip against normal references."
- It cannot scientifically evaluate the paper's timbre-difference task because it lacks MIMII DG sections/domains, clean-data condition/cause mappings, and the five-attribute timbre-difference ground-truth labels.

CURRENT MIMII FAN DIRECTLY USABLE:

- Same-audio Expert A -> Expert B integration.
- Normal-reference retrieval from available normal fan id_00 clips.
- Qualitative timbre rank-score output for abnormal clips.
- Regression/smoke tests that verify schema, nonempty references, deterministic kNN, and finite timbre values.

REQUIRES MIMII DG:

- Paper-like source/target-domain evaluation.
- Machine/section reporting for fan, gearbox, bearing, slider, valve.
- Public UASD evaluation matching the paper's dataset organization.

REQUIRES PAPER-SPECIFIC ANNOTATIONS:

- Per-anomalous-sample labels for sharpness, roughness, boominess, brightness, depth.
- Condition and anomaly-cause mappings used to assign identical labels to samples with the same condition/cause.
- Clean normal/anomalous audio grouped by identical condition and anomaly cause, used to generate ground truth.

NOT AVAILABLE:

- Official Nishida paper code.
- Official Nishida timbre annotation files.
- Official paper-specific pretrained embedding checkpoints or exact encoder extraction scripts.
- The exact inference threshold `t`, unless recovered from unreleased code or author correspondence.

## 3. Normal Reference Selection

EMBEDDING:

- The proposed method uses an audio encoder `E(x)` to map each audio sample to an embedding vector `z`.
- The paper does not mandate a single encoder. It says the encoder can be pretrained, trained from scratch with normal training data, or pretrained and fine-tuned.
- Experimental encoders:
  - MobileNetV2: DCASE 2022 baseline-style preprocessing, trained per machine type on MIMII DG machine-attribute classification using normal target-machine sounds. AdamW, learning rate `1e-4`, 50 epochs.
  - PANNs: public pretrained model, used without modification.
  - CLAP audio encoder: public pretrained model, used without modification.
  - BEATs: public pretrained model, used without modification.
- Embedding layer/output and dimensionality are not specified by the Nishida paper. PANNs official inference documentation shows an embedding of shape `(2048,)` for Cnn14, but Nishida et al. do not state which PANNs checkpoint/layer was used.

KNN:

- For a test sample, compute embedding distances to normal training embeddings.
- Sort by distance and select the first `k` normal training samples.
- Use the selected neighbor indices for both UASD scoring and timbre-difference scoring.

K:

- Paper experiment: `k = 30`.
- Paper note: similar results for `k` around 10 to 40.

DISTANCE:

- The method definition permits distances such as Euclidean distance or cosine distance.
- The paper does not state the exact distance used in the experiments. Exact reproduction therefore requires code or author clarification.

REFERENCE FILTER:

- Defined pool: normal training samples.
- The paper's evaluation is organized by MIMII DG machine type and section. It does not explicitly spell out a cross-machine vs per-machine/section filter in the method text.
- The scientifically defensible interpretation for this repository is: do not mix unrelated machines. Normal references should be selected from the same machine type and, when known, the same machine ID/section/domain/SNR condition.
- For our MVP, the reference filter should be same machine type `fan`, same machine ID `id_00`, and same SNR tag when SNR-specific data are used.

REFERENCE AGGREGATION:

- No mean/median aggregation of normal timbre values is used in the paper's difference rule.
- The test timbre value is ranked among the `k` normal reference timbre values plus the test value.
- UASD aggregation is the mean of the `k` embedding distances.

Supported pseudocode:

```python
def paper_knn_references(test_audio, normal_audio_pool, encoder, distance, k=30):
    z_test = encoder(test_audio)
    z_norm = [encoder(x) for x in normal_audio_pool]
    distances = [distance(z_test, z) for z in z_norm]
    neighbor_indices = argsort(distances)[:k]
    anomaly_score = mean([distances[i] for i in neighbor_indices])
    return neighbor_indices, anomaly_score
```

## 4. Timbre Attributes

The paper uses the five attributes listed in Ota and Unoki 2023 and points to that paper for further details. The concrete public implementation that matches the cited Audio Commons timbral-model family is `AudioCommons/timbral_models`.

Do not replace these with generic librosa spectral features. If the `timbral_models` package is not used, the implementation must be clearly marked as an adaptation and not a paper reproduction.

### Sharpness

ATTRIBUTE:

- `sharpness`

PERCEPTUAL MEANING:

- Sharp or shrill sensation.

EXACT MODEL OR METRIC:

- AudioCommons `timbral_sharpness`.

FORMULA OR MODEL ARCHITECTURE:

- Uses specific loudness and the Fastl sharpness weighting.
- Audio is windowed into 4096-sample sections.
- For each window, specific loudness is computed; `sharpness_Fastl` applies a Bark-scale weighting and computes:

```text
sharp = 0.11 * sum(loudness * g_z * z * 0.1) / sum(loudness * 0.1)
```

- Window values are RMS-squared weighted, log-transformed, and mapped through a linear regression:

```text
output = 102.50508921364404 * log10(rms_weighted_sharpness)
       + 34.432655185001735
```

INPUT:

- Audio file path or numpy audio array plus sample rate, per `timbral_models`.

OUTPUT:

- Scalar apparent sharpness. AudioCommons says regression-based timbral outputs were trained on subjective ratings ranging from 0 to 100, but outputs may exceed that range unless `clip_output=True`.

NORMALIZATION:

- Internal self loudness normalization in the AudioCommons implementation.
- Optional output clipping to 0..100 is available but not stated by Nishida et al.; use unclipped output unless a future reproduction verifies otherwise.

SOURCE / CITED METHOD:

- Nishida cites Audio Commons timbral models and Ota/Unoki for machine timbre attributes.
- AudioCommons implementation cites Fastl/psychoacoustic sharpness code and AudioCommons deliverables.

PUBLIC IMPLEMENTATION:

- `timbral_models.timbral_sharpness`

REPRODUCIBLE BY US:

- Yes, if `timbral_models` is installed and works in the Python environment.

ADAPTATION REQUIRED:

- Minimal wrapper only. No formula reimplementation should be done in the first Expert B.

RISKS:

- The AudioCommons repository states it is no longer maintained.
- The paper does not state package version or `clip_output` setting.

### Roughness

ATTRIBUTE:

- `roughness`

PERCEPTUAL MEANING:

- Buzzing, harsh, raspy sound quality.

EXACT MODEL OR METRIC:

- AudioCommons `timbral_roughness`.

FORMULA OR MODEL ARCHITECTURE:

- Implements the Vassilakis 2007 roughness model with a Plomp-based pairwise roughness term.
- Audio is segmented into 50 ms frames with Hamming windowing and peak picking.
- For peak pairs, the implementation computes a pairwise term using frequency spacing, amplitude interactions, and the Plomp function:

```text
pd = exp(-b1 * s * abs(f2 - f1)) - exp(-b2 * s * abs(f2 - f1))
rough_pair = (v1 * v2)^0.1 * 0.5 * ((2*v2)/(v1+v2))^3.11 * pd
```

- Mean frame roughness is log-transformed and linearly mapped:

```text
roughness = log10(mean_roughness) * 13.98779569 + 48.97606571545886
```

INPUT:

- Audio file path or numpy audio array plus sample rate.

OUTPUT:

- Scalar apparent roughness.

NORMALIZATION:

- Spectrogram normalized from peak time-frequency bin for peak picking.
- Optional output clipping is available but not specified by the paper.

SOURCE / CITED METHOD:

- Vassilakis 2007 roughness model as implemented by AudioCommons.

PUBLIC IMPLEMENTATION:

- `timbral_models.timbral_roughness`

REPRODUCIBLE BY US:

- Yes, if `timbral_models` is installed.

ADAPTATION REQUIRED:

- Wrapper only.

RISKS:

- Peak picking behavior can be sensitive to signal level and background factory noise.
- The paper does not report exact implementation version or parameters.

### Boominess

ATTRIBUTE:

- `boominess`

PERCEPTUAL MEANING:

- Booming sensation, often perceived as low-pitch vibration.

EXACT MODEL OR METRIC:

- AudioCommons `timbral_booming`. The paper calls the attribute "boominess"; the AudioCommons function is named "booming".

FORMULA OR MODEL ARCHITECTURE:

- Implements a Hashimoto/Hatano-style booming index.
- Uses specific loudness over a Bark scale, maps Bark to frequency, applies a third-octave-like weighting, emphasizes content below about 280 Hz, and combines low-frequency loudness ratio with a weighted loudness sum.
- Windowed booming indices are RMS-squared weighted, log-transformed, and combined with low-frequency level through linear regression:

```text
boominess = 43.67402696195865 * log10(rms_boom)
          - 10.90054738389845 * log10(low_frequency_level)
          + 26.836530575185435
```

INPUT:

- Audio file path or numpy audio array plus sample rate.

OUTPUT:

- Scalar apparent boominess/booming.

NORMALIZATION:

- Internal specific-loudness calculation and self loudness normalization.
- Optional output clipping available but not paper-specified.

SOURCE / CITED METHOD:

- Hatano and Hashimoto booming index family; AudioCommons implementation.

PUBLIC IMPLEMENTATION:

- `timbral_models.timbral_booming`

REPRODUCIBLE BY US:

- Yes, if `timbral_models` is installed.

ADAPTATION REQUIRED:

- Attribute naming adapter: output key should be `boominess`, implementation calls `timbral_booming`.

RISKS:

- Low-frequency factory noise may strongly affect this attribute.
- The AudioCommons source itself notes practical conversion/fudge factors around the booming index.

### Brightness

ATTRIBUTE:

- `brightness`

PERCEPTUAL MEANING:

- Bright sensation.

EXACT MODEL OR METRIC:

- AudioCommons `timbral_brightness`.

FORMULA OR MODEL ARCHITECTURE:

- Computes high-frequency energy ratio and high-pass spectral centroid after repeated high-pass filtering.
- Defaults in source include:
  - ratio crossover: 2000 Hz
  - centroid crossover: 100 Hz
  - FFT block size: 2048
  - step size parameter: 1024, with hop internally set to `3*nfft/4`
  - minimum high-pass frequency: 20 Hz
- Weighted log high-frequency ratio and weighted log high-pass centroid are mapped through linear regression:

```text
brightness = 4.613128018020465 * log10(weighted_hf_ratio)
           + 17.378889309312974 * log10(weighted_hp_centroid)
           + 17.434733750553022
```

INPUT:

- Audio file path or numpy audio array plus sample rate.

OUTPUT:

- Scalar apparent brightness.

NORMALIZATION:

- Audio is normalized to the maximum absolute value after filtering steps in the implementation.
- Optional output clipping is available but not paper-specified.

SOURCE / CITED METHOD:

- AudioCommons timbral brightness regression model.

PUBLIC IMPLEMENTATION:

- `timbral_models.timbral_brightness`

REPRODUCIBLE BY US:

- Yes, if `timbral_models` is installed.

ADAPTATION REQUIRED:

- Wrapper only.

RISKS:

- High-frequency noise can be interpreted as increased brightness.
- The model was trained on subjective ratings, not machine-fault labels.

### Depth

ATTRIBUTE:

- `depth`

PERCEPTUAL MEANING:

- Emphasized low-frequency component.

EXACT MODEL OR METRIC:

- AudioCommons `timbral_depth`.

FORMULA OR MODEL ARCHITECTURE:

- Computes multiple low-frequency and temporal descriptors:
  - limited weighted mean lower centroid with 2000 Hz lowpass path
  - weighted lower-frequency energy ratio with 500 Hz lowpass path
  - approximate duration/decay time from RMS envelope and onsets
  - peak-picking pitch estimate
  - interaction terms between lower ratio and duration
- Uses 4096-point spectrogram windows and threshold defaults in the source.
- Linear regression coefficients in the public implementation:

```text
[-0.0043703565847874465,
 32.83743202462131,
 4.750862716905235,
-14.217438690256062,
 3.8782339862813924,
-0.8544826091735516,
 66.69534393444391]
```

INPUT:

- Audio file path or numpy audio array plus sample rate.

OUTPUT:

- Scalar apparent depth.

NORMALIZATION:

- Repeated high-pass/low-pass filtering and normalization to maximum absolute signal value.
- Optional output clipping available but not paper-specified.

SOURCE / CITED METHOD:

- AudioCommons timbral depth regression model.

PUBLIC IMPLEMENTATION:

- `timbral_models.timbral_depth`

REPRODUCIBLE BY US:

- Yes, if `timbral_models` is installed.

ADAPTATION REQUIRED:

- Wrapper only.

RISKS:

- Low-frequency fan hum and low-frequency background noise may confound depth.
- Onset/duration logic was designed for general audio objects and may be brittle for steady machine sounds.

## 5. Timbre Difference Rule

TEST VALUE:

For each attribute `l`, compute:

```text
T_l(x_te)
```

using the timbral model for the test audio sample.

REFERENCE VALUE:

For each selected normal neighbor `x_ni^tr`, compute:

```text
T_l(x_ni^tr)
```

There is no mean reference value in the paper's inference rule. The reference set is the `k` selected normal timbre values.

DIFFERENCE:

Let `r` be the 1-based rank of `T_l(x_te)` among:

```text
{T_l(x_te), T_l(x_n1^tr), ..., T_l(x_nk^tr)}
```

sorted ascending. The timbre difference score is:

```text
score_l = (r - 1) / k
```

Interpretation:

- `score_l` near 0: test value is lower than almost all comparable normal references.
- `score_l` near 1: test value is higher than almost all comparable normal references.
- `score_l` near 0.5: test value lies inside the comparable normal range.

NORMALIZATION:

- The rank formula is nonparametric and already normalized to `[0, 1]`.
- No z-score, min-max scaling, or normal-reference averaging is described for timbre values.

DIRECTION RULE:

```text
decreased  if score_l <= t
unchanged  if t < score_l < 1 - t
increased  if 1 - t <= score_l
```

THRESHOLDS:

- Inference threshold `t`: defined as a predefined threshold in `[0,1]`, but the inspected paper text does not state its experimental value.
- Ground-truth generation threshold `t'`: explicitly stated as `0.05`.
- Do not silently use `t'=0.05` as the paper's inference `t` unless future official code or author clarification confirms it. If used in our implementation, mark it as an adaptation or smoke-test setting.

Tie handling:

- The paper says "r-th smallest" but does not specify tie handling. A reproducible implementation must define a deterministic policy. Recommended adaptation: use `rank = 1 + count(reference_values < test_value) + 0.5 * count(reference_values == test_value)` for a midrank-like score, or use stable sorted insertion. The choice must be documented as an adaptation because the paper does not specify ties.

## 6. Learned Models

### Anomalous Sound Detector

MODEL:

- In the paper's proposed joint method, the detector is the kNN distance score in embedding space.

PURPOSE:

- UASD anomaly scoring.

INPUT:

- Audio embedding of test sample and audio embeddings of normal training samples.

OUTPUT:

- Scalar anomaly score, mean distance to `k` nearest normal samples.

ARCHITECTURE:

- kNN over embeddings; no neural detector architecture is fixed by the paper.

LOSS:

- None for kNN itself.

TRAINING DATA:

- Normal training audio for fitting/storing reference embeddings.

LABELS:

- No anomaly labels.

OPTIMIZER:

- None for kNN.

HYPERPARAMETERS:

- `k = 30` in experiments.
- Distance metric not explicitly fixed in paper.

PRETRAINED:

- Depends on encoder.

FROZEN:

- kNN index is nonparametric. Pretrained encoders PANNs/CLAP/BEATs were used without modification.

PUBLIC WEIGHTS:

- Not for a Nishida-specific detector. Public encoder weights exist for PANNs, CLAP, and BEATs via their official projects.

### Audio Embedding Model

MODEL:

- MobileNetV2, PANNs, CLAP audio encoder, BEATs in experiments.

PURPOSE:

- Produce an embedding space where nearby normal samples are assumed to share operating/recording conditions with the test sample.

INPUT:

- Audio sample, with preprocessing depending on encoder.

OUTPUT:

- Embedding vector. Exact layer and dimensionality are not stated by Nishida et al.

ARCHITECTURE:

- MobileNetV2: DCASE 2022 baseline-style MobileNetV2.
- PANNs: public pretrained audio neural network.
- CLAP: public pretrained audio-language representation model.
- BEATs: public pretrained audio representation model.

LOSS:

- MobileNetV2 loss not explicitly stated by Nishida; classification task implies classification loss, but do not assert exact loss without code.
- PANNs/CLAP/BEATs losses are inherited from their original pretraining papers, not trained by Nishida for this method.

TRAINING DATA:

- MobileNetV2: MIMII DG normal target-machine sounds for machine-attribute classification, per machine type.
- PANNs: public pretrained model; official PANNs repo says trained on AudioSet.
- CLAP and BEATs: public pretrained models; Nishida used them without modification.

LABELS:

- MobileNetV2: machine attributes from MIMII DG.
- Public encoders: their original pretraining labels/objectives.

OPTIMIZER:

- MobileNetV2: AdamW.

HYPERPARAMETERS:

- MobileNetV2: learning rate `1e-4`, 50 epochs.
- kNN: `k=30`.

PRETRAINED:

- PANNs/CLAP/BEATs yes.
- MobileNetV2 no, trained for experiment.

FROZEN:

- PANNs/CLAP/BEATs used without modification, so effectively frozen feature extractors.
- MobileNetV2 trained then used as encoder.

PUBLIC WEIGHTS:

- PANNs: yes, official repo links Zenodo pretrained checkpoints.
- CLAP: yes, official Microsoft repo.
- BEATs: yes, official Microsoft/unilm BEATs repo.
- MobileNetV2 experiment weights: not found.

### Timbre Prediction / Model Components

MODEL:

- AudioCommons timbral models: sharpness, roughness, booming/boominess, brightness, depth.

PURPOSE:

- Compute objective timbre metric values used for rank-based difference labels.

INPUT:

- Audio file path or waveform array plus sample rate.

OUTPUT:

- Scalar timbre value per attribute.

ARCHITECTURE:

- Regression-style timbral models and psychoacoustic formulas, depending on attribute. Not a single neural architecture.

LOSS:

- Not trained in Nishida et al.; AudioCommons models were previously trained/fit against subjective ratings.

TRAINING DATA:

- AudioCommons subjective timbre-rating data, not MIMII/MIMII DG.

LABELS:

- Subjective ratings for timbral attributes, described by AudioCommons as 0..100 ratings for regression-based attributes.

OPTIMIZER:

- Not relevant to Nishida method; not stated in AudioCommons README for runtime use.

HYPERPARAMETERS:

- Function defaults in AudioCommons source; Nishida does not state overrides.

PRETRAINED:

- Yes, in the sense of fitted regression coefficients embedded in the public code.

FROZEN:

- Yes, used as fixed timbral metric calculators.

PUBLIC WEIGHTS:

- Coefficients are embedded in the open-source AudioCommons package.

## 7. Evaluation Protocol

TASK:

- Joint UASD and timbre difference capturing on the MIMII DG-based dataset with generated ground-truth timbre-difference labels.

METRICS:

- UASD: AUC.
- Timbre difference capturing: mean absolute error (MAE) for anomalous samples, normalized to compensate for ground-truth label imbalance.
- The paper's MAE formula is per timbre `l`:

```text
MAE_l = (1/3) * sum_{i=1..M} abs(pred_l(x_i^te) - y_{l,i}) / M_{l,y_{l,i}}
```

where `M_{l,y}` is the count of samples whose ground-truth label for timbre `l` equals `y`.

BASELINES:

- Baseline 1: compare anomalous timbre metrics with all normal training samples using the same rank-style formula, without kNN neighbor selection.
- Baseline 2: `Timbre-knn`, using the five timbre metrics themselves as the kNN feature vectors instead of audio-encoder embeddings.

ABLATIONS / REFERENCE-SELECTION EXPERIMENTS:

- Encoders compared: MobileNetV2, PANNs, CLAP, BEATs.
- `k=30` used; paper says similar results for `k` around 10 to 40.
- Comparison against all-normal baseline evaluates the value of selecting comparable normal references.
- Comparison against Timbre-knn evaluates the value of audio embeddings over timbre-metric-only neighbor search.

MAIN RESULTS:

- Table II reports AUC by machine/section/domain. Mean AUC:
  - Source domain: Timbre-knn 62.8, MobileNetV2 71.3, PANNs 66.1, CLAP 69.8, BEATs 71.3.
  - Target domain: Timbre-knn 51.4, MobileNetV2 58.8, PANNs 55.7, CLAP 57.5, BEATs 55.9.
- Fan AUC values in Table II:
  - Source section 00: Timbre-knn 47.3, MobileNetV2 62.9, PANNs 75.7, CLAP 67.7, BEATs 86.2.
  - Source section 01: 68.2, 74.5, 68.2, 71.3, 69.4.
  - Source section 02: 77.7, 68.2, 74.3, 70.1, 80.9.
  - Target fan mean: Timbre-knn 45.1, MobileNetV2 47.7, PANNs 48.2, CLAP 45.4, BEATs 54.8.
- Figure 3 contains MAE plots, not numeric tables in the text. The paper states PANNs, CLAP, and BEATs improved source-domain MAE over baselines; BEATs had the smallest overall MAE in source domain. In target domain, differences were small, possibly due to small data size.

ANNOTATION PROCESS:

- Labels are automatically generated from clean audio using the AudioCommons-style timbre metrics and AUC between condition-matched normal and anomaly groups.
- Labels are assigned to noisy MIMII DG anomalous samples by corresponding condition and anomaly cause.
- The paper suggests interviewing machine inspectors beforehand could connect label combinations to anomaly causes, but the proposed method does not perform root-cause diagnosis.

LIMITATIONS OF THE EVALUATION:

- Ground truth is generated by the same family of timbral metrics that the method predicts against. This evaluates consistency with metric-derived labels, not independent human labels.
- Target-domain MAE differences are small and the paper attributes this possibly to small data size.
- The exact inference threshold `t`, embedding distance metric, embedding extraction layer, and tie handling are not stated.
- Clean data and anomaly-cause mappings used to generate labels are not publicly available in the inspected sources.

## 8. Public Code And Assets

ASSET:

- Nishida et al. official implementation.

OFFICIAL SOURCE:

- None found in arXiv code/data listing or targeted web searches.

CONTENTS:

- Not available.

LICENSE IF STATED:

- Not available.

REQUIRED FOR OUR EXPERT B:

- Required only for exact reproduction.

AVAILABLE:

- No.

NOTES:

- Without official code, exact choices for distance metric, inference threshold `t`, embedding extraction layer, tie handling, and encoder checkpoints remain unresolved.

ASSET:

- Timbre annotation files for Nishida MIMII DG-based evaluation.

OFFICIAL SOURCE:

- None found.

CONTENTS:

- Would contain five ordinal labels per anomalous sample.

LICENSE IF STATED:

- Not available.

REQUIRED FOR OUR EXPERT B:

- Required for scientific Level 2 evaluation.

AVAILABLE:

- No.

NOTES:

- Current fan id_00 data cannot substitute for these labels.

ASSET:

- MIMII DG dataset.

OFFICIAL SOURCE:

- MIMII DG paper states the dataset is freely available at `https://zenodo.org/record/6529888`. DCASE 2022 baseline README links development data at `https://zenodo.org/record/6355122`.

CONTENTS:

- Five machine types, three sections per type, source and target domains, normal train data, normal/anomalous test data, attribute CSVs.

LICENSE IF STATED:

- Not determined from inspected accessible lines.

REQUIRED FOR OUR EXPERT B:

- Required for paper-like dataset organization and scientific evaluation.

AVAILABLE:

- Public dataset exists; not present in this repository.

NOTES:

- MIMII DG alone still does not provide Nishida's paper-specific timbre labels.

ASSET:

- AudioCommons `timbral_models`.

OFFICIAL SOURCE:

- https://github.com/AudioCommons/timbral_models

CONTENTS:

- Python scripts for hardness, depth, brightness, roughness, warmth, sharpness, booming, and reverberation.

LICENSE IF STATED:

- Apache-2.0.

REQUIRED FOR OUR EXPERT B:

- Yes, if we implement paper-faithful timbre metric extraction.

AVAILABLE:

- Yes. Install method documented as `pip install timbral_models`; repository notes it is no longer maintained.

NOTES:

- The repository says outputs for the regression attributes were trained on subjective ratings from 0 to 100 but may exceed that range unless clipped.

ASSET:

- PANNs public pretrained models.

OFFICIAL SOURCE:

- https://github.com/qiuqiangkong/audioset_tagging_cnn

CONTENTS:

- AudioSet-trained CNN models and inference code. The README reports Cnn14 embedding shape `(2048,)` and links Zenodo checkpoints.

LICENSE IF STATED:

- MIT license in repository.

REQUIRED FOR OUR EXPERT B:

- Optional. Needed for closer paper-style pretrained audio embeddings but not necessary for the smallest adaptation.

AVAILABLE:

- Yes.

NOTES:

- Adds dependency and checkpoint download burden.

ASSET:

- CLAP public pretrained model.

OFFICIAL SOURCE:

- https://github.com/microsoft/CLAP

CONTENTS:

- Audio-language representation model.

LICENSE IF STATED:

- See repository; not inspected deeply here.

REQUIRED FOR OUR EXPERT B:

- Optional.

AVAILABLE:

- Yes.

NOTES:

- Paper uses CLAP audio encoder without modification, but does not state exact checkpoint/layer.

ASSET:

- BEATs public pretrained model.

OFFICIAL SOURCE:

- https://github.com/microsoft/unilm/tree/master/beats

CONTENTS:

- Audio pretraining model with acoustic tokenizers.

LICENSE IF STATED:

- See repository; not inspected deeply here.

REQUIRED FOR OUR EXPERT B:

- Optional.

AVAILABLE:

- Yes.

NOTES:

- Paper reports BEATs as strongest overall for source-domain MAE, but exact extraction setup is not specified.

ASSET:

- DCASE 2022 Task 2 AE/MobileNetV2 baselines.

OFFICIAL SOURCE:

- AE: https://github.com/Kota-Dohi/dcase2022_task2_baseline_ae
- MobileNetV2: https://github.com/Kota-Dohi/dcase2022_task2_baseline_mobile_net_v2

CONTENTS:

- Baseline training/test scripts, dataset layout, metrics, and configuration.

LICENSE IF STATED:

- MIT for AE repo.

REQUIRED FOR OUR EXPERT B:

- Not for smallest adaptation.

AVAILABLE:

- Yes.

NOTES:

- Useful if we later move to MIMII DG and paper-like MobileNetV2 encoders.

## 9. Paper Limitations

LIMITATION:

- Predefined timbre vocabulary only.

IMPACT ON OUR PROJECT:

- Expert B can say how sound differs along five timbre axes, but cannot provide open-ended explanations.

MITIGATION:

- Keep Expert B output as acoustic characterization only. Let future LLM explanation consume this structured output, clearly separated from root-cause diagnosis.

LIMITATION:

- No physical fault interpretation.

IMPACT ON OUR PROJECT:

- Increased roughness or boominess is not automatically "bearing damage", "clogging", or any repair action.

MITIGATION:

- Forbid root-cause labels and recommended maintenance actions inside Expert B.

LIMITATION:

- Embedding dependence.

IMPACT ON OUR PROJECT:

- Bad embedding spaces select poor normal references, producing misleading differences.

MITIGATION:

- Log neighbor file IDs, distances, and metadata. Start with same machine ID/SNR references. Later evaluate PANNs/BEATs embeddings against labels.

LIMITATION:

- Reference quality and domain mismatch.

IMPACT ON OUR PROJECT:

- Comparing a +6 dB test clip with -6 dB normal references, or fan id_00 with another machine, can create spurious timbre differences.

MITIGATION:

- Require machine-aware reference filters. Include `machine_type`, `machine_id`, `snr_tag`, and optional `domain/section` in reference metadata.

LIMITATION:

- Annotation dependence for evaluation.

IMPACT ON OUR PROJECT:

- We can build and smoke-test Expert B, but cannot claim scientific timbre-difference accuracy without labels.

MITIGATION:

- Create Level 1 integration tests now; defer Level 2 claims until MIMII DG plus annotations or a locally created annotation protocol exists.

LIMITATION:

- Anomalous data scarcity.

IMPACT ON OUR PROJECT:

- The method is appealing because it does not require anomaly training data, but scientific evaluation still needs anomalous samples and labels.

MITIGATION:

- Keep training unsupervised/normal-only. Use anomalous clips only for evaluation and smoke tests.

LIMITATION:

- Timbre-model limitations.

IMPACT ON OUR PROJECT:

- AudioCommons models were developed for general audio timbre and subjective ratings, not industrial fan-fault semantics.

MITIGATION:

- Present outputs as "timbral metric changes", not validated physical diagnosis.

LIMITATION:

- Exact reproduction details missing.

IMPACT ON OUR PROJECT:

- Exact Nishida reproduction is blocked by missing `t`, distance metric, embedding layer/checkpoint choices, paper-specific labels, and code.

MITIGATION:

- Implement a transparent adaptation with all non-paper choices named in config and output metadata.

## 10. Repository Gap Map

DIRECTLY REUSABLE:

- `src/config.py`
  - Machine/audio constants: `SR=16000`, `MIMII_SNR_DIRS`, `MIMII_FAN_DIR`, `MIMII_NORMAL_FOLDER`, `MIMII_ABNORMAL_FOLDER`.
  - Artifact path helper: `ad_paths_for(snr_tag)`.
  - Existing model path constants: `ANOMALY_DETECTOR_PATH`, `MODELS_DIR`, `PROCESSED_DIR`.
- `src/data_loader.py`
  - `_sorted_wav_files(folder)` for deterministic reference listing.
  - Raw WAV directory conventions.
  - `_extract_logmel(file_path)` only for Expert A-style embeddings if we use the existing autoencoder. Do not use log-mel as a timbre substitute.
  - `load_mimii_dataset(...)` for rebuilding Expert A arrays, not for timbre metric extraction.
- `src/models/anomaly_detector.py`
  - `ConvAutoencoder` as existing Expert A architecture.
  - `_transpose_to_model_input`, `_normalize`, `_load_normalization`, `_resolve_ad_paths` can be reused by a wrapper if extracting Expert A latent embeddings.
  - `evaluate`, `compute_threshold`, `train_anomaly_detector` must remain unchanged.
- Existing artifacts:
  - `models_store/anomaly_detector.pt`
  - `data/processed/ad_norm_stats.npz`
  - SNR artifacts described in `REPORT_PHASE1_2.md`: `D:\PDM_Data\MIMII\processed\snr_ad_summary.{json,csv}` and per-SNR model/data artifacts.
- `requirements.txt`
  - Existing dependencies cover numpy/scipy/sklearn/soundfile/librosa/torch.

NEEDS ADAPTATION:

- Expert A latent embedding extraction:
  - Current `ConvAutoencoder` has no public `encode()` method.
  - Future code can either add a non-architectural helper/wrapper outside `anomaly_detector.py`, or register a forward hook/partial forward to obtain the 128-dimensional bottleneck activation.
  - Do not change Expert A architecture or training logic.
- Raw reference metadata:
  - Need a machine-aware metadata structure with `machine_type`, `machine_id`, `snr_tag`, `domain`, `section`, and path.
- Thresholding:
  - Need a configurable `rank_threshold` because the paper's inference `t` is not explicitly stated.

MISSING CODE:

- `src/models/timbre_difference.py`
- `src/utils/audio_reference_index.py` or equivalent
- `scripts/build_timbre_reference_index.py`
- `scripts/run_expert_b_smoke.py`
- Tests for reference filtering, rank scoring, and JSON schema.

MISSING DATA:

- MIMII DG dataset for paper-like evaluation.
- Clean originally recorded data and condition/anomaly-cause mappings used by Nishida to generate labels.
- Current repo does not show raw MIMII WAVs under `data/raw`; reports/config point to external `D:\PDM_Data\MIMII`.

MISSING MODELS:

- Official Nishida model/code.
- Official MobileNetV2 experiment checkpoint.
- Optional public pretrained encoder checkpoints if choosing PANNs/CLAP/BEATs.

MISSING ANNOTATIONS:

- Five-attribute timbre-difference labels for anomalous samples.
- Condition/cause label mapping.

DEPENDENCIES:

- Already present and verified in `requirements.txt`: `librosa`, `numpy`, `scipy`, `scikit-learn`, `soundfile`, `torch`.
- Required new dependency for paper-faithful timbre metrics: `timbral_models`, official AudioCommons package, Apache-2.0.
- No dependency should be installed during this specification task.

LEGACY RUL CODE:

- No active `src/models/rul_predictor.py` exists in the current file tree.
- RUL/PRONOSTIA legacy references remain in:
  - `CLAUDE.md`
  - `REPORT.md`
  - `src/config.py` constants: `PRONOSTIA_*`, `X_TRAIN_RUL_PATH`, `Y_TRAIN_RUL_PATH`, `RUL_SCALER_PATH`, `RUL_PREDICTOR_PATH`, `WINDOW_SIZE`, `RUL_*`, `CNN_*`
  - `requirements.txt` comments
- Do not delete or edit them in the next Expert B implementation task unless explicitly requested.

SCIENTIFIC RISKS:

- Exact paper reproduction is blocked.
- Existing Expert A embeddings are an adaptation and may not capture semantic similarity as well as BEATs/PANNs/CLAP.
- Current fan id_00 data lacks labels for timbre-difference evaluation.
- AudioCommons timbral models may be confounded by factory noise and steady fan hum.
- SNR-specific differences can dominate timbre differences if references are not filtered carefully.

## 11. Recommend The Minimum Expert B

EXPERT B NAME:

`AcousticTimbreDifferenceExpert`

Scientific status:

- This is a Nishida-inspired, paper-rule-compatible adaptation for the current repository.
- It is not an exact Nishida reproduction unless we later use MIMII DG, paper-specific labels, official/declared encoder setup, and recovered inference threshold/distance choices.

INPUT:

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

PIPELINE:

```text
INPUT
-> validate Expert A marked same audio as anomalous
-> load or build normal-reference index for same machine metadata
-> extract test embedding using selected embedding adapter
-> kNN over filtered normal reference embeddings
-> compute AudioCommons timbre values for test audio
-> retrieve or compute AudioCommons timbre values for k normal references
-> compute rank score per attribute using Nishida rule
-> if rank_threshold is supplied, convert rank score to decreased/unchanged/increased
-> OUTPUT
```

Recommended smallest embedding adapter:

- Use existing Expert A autoencoder bottleneck as the first implementation embedding adapter.
- Reason: it uses no new model framework, is trained on current normal fan audio, and the Nishida paper allows an audio encoder trained from scratch on normal data.
- Guardrail: label this as `embedding_model="expert_a_bottleneck_adaptation"`, not as a paper encoder. Add optional future adapters for PANNs/BEATs when scientific evaluation becomes available.

OUTPUT JSON SCHEMA:

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
    "selected_count": 0,
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
      "reference_values": [0.0],
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
    "No paper-specific timbre ground-truth labels available; output is characterization only."
  ]
}
```

REQUIRED ARTIFACTS:

- Existing Expert A model: `models_store/anomaly_detector.pt` or per-SNR model from `config.ad_paths_for(snr_tag)`.
- Existing Expert A normalization stats: `data/processed/ad_norm_stats.npz` or per-SNR stats.
- Normal reference index artifact:

```text
D:\PDM_Data\MIMII\processed\timbre_reference_index_<machine_type>_<machine_id>_<snr_tag>.npz
```

or JSON/NPZ pair containing paths, metadata, embeddings, and timbre values.

REQUIRED DEPENDENCIES:

- Existing: `numpy`, `scipy`, `scikit-learn`, `soundfile`, `librosa`, `torch`.
- New verified: `timbral_models`.

PROPOSED PYTHON FILES:

- `src/models/timbre_difference.py`
- `src/utils/audio_reference_index.py`
- `scripts/build_timbre_reference_index.py`
- `scripts/run_expert_b_smoke.py`
- `tests/test_timbre_difference.py` if a test framework is present or added later; otherwise a script-level smoke test.

Proposed functions/classes:

FILE:

- `src/models/timbre_difference.py`

FUNCTION / CLASS:

- `TimbreValues`

PURPOSE:

- Typed dataclass for five timbre metric values.

INPUT:

- `sharpness`, `roughness`, `boominess`, `brightness`, `depth` floats.

OUTPUT:

- Serializable mapping.

FUNCTION / CLASS:

- `compute_timbre_values(audio_path: Path) -> TimbreValues`

PURPOSE:

- Call AudioCommons exact timbral functions and normalize attribute names.

INPUT:

- WAV path.

OUTPUT:

- `TimbreValues`.

FUNCTION / CLASS:

- `rank_score(test_value: float, reference_values: Sequence[float]) -> float`

PURPOSE:

- Implement Nishida equation `(r - 1) / k`.

INPUT:

- Test scalar and k normal reference scalars.

OUTPUT:

- Rank score in `[0,1]`.

FUNCTION / CLASS:

- `direction_from_rank(score: float, threshold: float | None) -> tuple[str | None, int | None]`

PURPOSE:

- Convert rank score to `decreased/unchanged/increased` only when a threshold is explicitly supplied.

INPUT:

- Rank score and optional threshold.

OUTPUT:

- Direction string and code `-1/0/1`, or nulls.

FUNCTION / CLASS:

- `ExpertABottleneckEmbedder`

PURPOSE:

- Load existing Expert A and produce 128-dimensional bottleneck embeddings without changing Expert A architecture.

INPUT:

- Model path, normalization stats path, audio/logmel input.

OUTPUT:

- Embedding vector.

FUNCTION / CLASS:

- `AcousticTimbreDifferenceExpert`

PURPOSE:

- Orchestrate reference filtering, kNN, timbre extraction, rank scoring, and JSON output.

INPUT:

- Audio path, machine metadata, Expert A result, reference index, k, distance, optional threshold.

OUTPUT:

- JSON-serializable dict matching schema above.

FILE:

- `src/utils/audio_reference_index.py`

FUNCTION / CLASS:

- `ReferenceItem`

PURPOSE:

- Dataclass for path, machine metadata, embedding, and timbre values.

INPUT:

- Path and metadata fields.

OUTPUT:

- Serializable record.

FUNCTION / CLASS:

- `build_reference_index(normal_paths, metadata, embedder) -> ReferenceIndex`

PURPOSE:

- Compute embeddings and timbre values for normal reference clips.

INPUT:

- Normal WAV paths, metadata defaults, embedding adapter.

OUTPUT:

- In-memory index.

FUNCTION / CLASS:

- `filter_references(index, machine_type, machine_id=None, snr_tag=None, section=None, domain=None)`

PURPOSE:

- Enforce machine-aware reference pool selection.

INPUT:

- Reference index and metadata query.

OUTPUT:

- Filtered list of references.

FUNCTION / CLASS:

- `knn(query_embedding, references, k, distance) -> list[Neighbor]`

PURPOSE:

- Deterministic kNN over filtered normal references.

INPUT:

- Query embedding, reference embeddings, k, distance name.

OUTPUT:

- Sorted neighbors with distances.

FUNCTION / CLASS:

- `save_reference_index(index, path)` / `load_reference_index(path)`

PURPOSE:

- Cache expensive timbre and embedding computations.

INPUT:

- Index/path.

OUTPUT:

- File artifact or loaded index.

FILE:

- `scripts/build_timbre_reference_index.py`

FUNCTION / CLASS:

- `main()`

PURPOSE:

- Build reference index for a machine/SNR normal folder.

INPUT:

- CLI args: machine type, machine ID, SNR tag, normal dir, output path.

OUTPUT:

- Reference index artifact.

FILE:

- `scripts/run_expert_b_smoke.py`

FUNCTION / CLASS:

- `main()`

PURPOSE:

- Run one normal and one abnormal fan clip through Expert B using existing Expert A result or a supplied mock Expert A result.

INPUT:

- CLI paths.

OUTPUT:

- JSON file and concise console summary.

## 12. Evaluation Plan For Our Expert B

LEVEL 1 - INTEGRATION SMOKE TEST

Goal:

- Verify Expert A -> Expert B works technically on the same audio event.

Input clips:

- One abnormal fan id_00 WAV from the current MIMII abnormal folder.
- One normal fan id_00 WAV as a control.
- Use the same SNR tag as the chosen Expert A model/reference index.

Normal references:

- At least `k=30` normal fan id_00 clips from the same SNR tag and machine ID.
- If fewer than k exist, fail loudly; do not silently cross machine/SNR boundaries.

Assertions:

- Expert B refuses or warns when `expert_a.is_anomaly` is false, depending on chosen policy.
- Reference pool size >= k.
- Selected references all match machine type, machine ID, and SNR tag.
- All five timbre attributes are present.
- Test values and reference values are finite floats.
- Rank scores are in `[0,1]`.
- Direction labels are null if no threshold is configured.
- No confidence percentage is emitted.
- No root-cause diagnosis is emitted.
- Output JSON validates against expected schema.

Expected artifacts:

- Reference index artifact under processed data directory.
- Smoke output JSON, e.g. `D:\PDM_Data\MIMII\processed\expert_b_smoke_<tag>.json`.
- Console summary with selected neighbor count and top changed attributes by distance from 0.5 or by configured direction.

LEVEL 2 - SCIENTIFIC EVALUATION

Goal:

- Evaluate timbre-difference characterization accuracy.

Dataset:

- MIMII DG, preferably with Nishida-style five-attribute annotations.
- If official annotations are unavailable, a local reproduction requires clean condition-matched normal/anomalous audio and anomaly-cause metadata. Without those, do not claim paper-equivalent evaluation.

Required labels/annotations:

- For every anomalous test sample: labels for sharpness, roughness, boominess, brightness, depth in `{-1,0,1}`.
- Machine type, section, source/target domain, condition, anomaly cause if generating labels.

Split:

- Use MIMII DG train/test organization.
- Train/reference index from normal training data only.
- Evaluate on anomalous test samples for timbre MAE.
- Report UASD separately if using Expert A or a kNN detector.

Metrics:

- Per-attribute normalized MAE following Nishida equation.
- Macro-average across attributes.
- Per-machine and per-section reporting.
- Source-domain and target-domain reporting.
- Optional confusion matrices per attribute for `decreased/unchanged/increased`.

Domain handling:

- Build/report by machine and section.
- Do not use test-domain labels at inference if following DCASE setting.
- Record whether references include source only, source+target training normals, or another policy.

Baselines:

- All-normal rank baseline: compare test timbre value against all normal training timbre values in the same machine/section pool.
- Timbre-knn: kNN using the five timbre metric vectors as features.
- Optional pretrained embedding baseline: PANNs or BEATs if dependencies/checkpoints are approved.

Clearly stated sufficiency of current data:

- Current MIMII fan id_00 data alone are not sufficient for Level 2 scientific evaluation of timbre-difference characterization.
- Current data are sufficient only for Level 1 integration and qualitative demonstration.

## 13. Codex Implementation Task Draft

Do not execute this task during this specification run.

TASK:

Implement the minimum `AcousticTimbreDifferenceExpert` as a Nishida-inspired adaptation that characterizes how an Expert A-detected anomalous audio clip differs from same-machine normal reference clips along AudioCommons timbre attributes.

FILES TO INSPECT:

- `CLAUDE.md`
- `REPORT_PHASE1_2.md`
- `src/config.py`
- `src/data_loader.py`
- `src/models/anomaly_detector.py`
- `scripts/run_snr_experiments.py`
- `requirements.txt`

FILES TO CREATE:

- `src/models/timbre_difference.py`
- `src/utils/audio_reference_index.py`
- `scripts/build_timbre_reference_index.py`
- `scripts/run_expert_b_smoke.py`
- Optional if test framework exists: `tests/test_timbre_difference.py`

FILES TO MODIFY:

- `requirements.txt`: add `timbral_models` only.
- Do not modify source files unless needed for imports. Prefer new files.

EXACT FUNCTIONS / CLASSES:

- `TimbreValues`
- `compute_timbre_values(audio_path: Path) -> TimbreValues`
- `rank_score(test_value: float, reference_values: Sequence[float]) -> float`
- `direction_from_rank(score: float, threshold: float | None) -> tuple[str | None, int | None]`
- `ExpertABottleneckEmbedder`
- `ReferenceItem`
- `ReferenceIndex`
- `build_reference_index(...)`
- `filter_references(...)`
- `knn(...)`
- `save_reference_index(...)`
- `load_reference_index(...)`
- `AcousticTimbreDifferenceExpert.characterize(...)`

DEPENDENCIES:

- Existing verified: `numpy`, `scipy`, `scikit-learn`, `soundfile`, `librosa`, `torch`.
- New verified: `timbral_models` from AudioCommons.
- Do not add PANNs, CLAP, BEATs, Hugging Face, FAISS, LangChain, or any LLM dependency in this task.

TESTS:

- Unit test `rank_score` bounds and monotonic cases.
- Unit test `direction_from_rank` with threshold supplied and threshold null.
- Unit test reference filtering rejects cross-machine/cross-SNR references.
- Unit test JSON output has five attributes and no confidence/root-cause fields.

SMOKE TESTS:

- Build a normal reference index for `fan/id_00` same SNR.
- Run one abnormal clip through Expert B with mocked or actual Expert A anomaly result.
- Confirm selected `k` references and five finite rank scores.
- Run one normal clip and confirm Expert B can either warn/skip or characterize depending on explicit policy.

EXPECTED OUTPUT:

- JSON matching the schema in Section 11.
- Console summary:

```text
Expert B: AcousticTimbreDifferenceExpert
Status: adaptation_not_exact_reproduction
References: <k>/<pool_size>
Top timbre rank deviations: <attribute>=<score>, ...
Warnings: <count>
```

SCIENTIFIC GUARDRAILS:

- Do not claim exact Nishida reproduction.
- Do not invent or output confidence percentages.
- Do not output root-cause diagnosis.
- Do not replace AudioCommons timbral models with generic spectral centroid, rolloff, MFCC, or librosa features.
- Do not hardcode `fan`; require machine metadata and reference filters.
- Do not mix SNR tags or machine IDs unless explicitly configured and reported.
- Do not silently set the paper's missing inference threshold `t`; require a supplied threshold for direction labels or output rank scores only.
- Log embedding model name and mark Expert A bottleneck as an adaptation.

FILES NOT TO TOUCH:

- `src/models/anomaly_detector.py` architecture.
- Current Expert A training logic.
- Current SNR artifacts/models.
- `scripts/run_snr_experiments.py` behavior.
- PRONOSTIA/RUL legacy files during this task.

## Terminal Summary

PAPER VERDICT:

- Nishida et al. provide an explicit kNN/rank-based framework for joint UASD and timbre-difference capturing, but the paper leaves key exact reproduction choices unstated: inference threshold `t`, embedding distance, embedding layer, exact checkpoints, and tie handling.

REPRODUCIBLE:

- The timbre rank rule and AudioCommons timbre metrics are reproducible as an adaptation. Exact paper reproduction is not currently reproducible from public sources alone.

MAIN BLOCKER:

- Missing paper-specific timbre labels/assets and missing exact inference details, especially threshold `t`.

CURRENT FAN DATA SUFFICIENT:

- No for scientific timbre-difference evaluation. Yes for integration smoke tests and qualitative same-machine characterization.

RECOMMENDED EXPERT B:

- `AcousticTimbreDifferenceExpert`: AudioCommons timbre metrics + same-machine normal references + Nishida rank-score rule + existing Expert A bottleneck embeddings as a clearly marked adaptation.

NEXT TASK:

- Implement only the bounded Expert B adaptation and smoke tests after review, without changing Expert A, SNR pipeline, or legacy RUL files.
