# TASK-02 Performance Forensics

Task: `TASK-02`

Date: 2026-07-07

Scope: Expert B normal-reference index runtime for MIMII Fan `id_00`,
`minus6dB`. No model training, abnormal Expert B smoke, or full-dataset Expert B
index build was run.

## Process

Command under diagnosis:

```text
python scripts/build_timbre_reference_index.py --machine-type fan --machine-id id_00 --snr-tag minus6dB --limit 40
```

## Call Graph

```text
build_timbre_reference_index.py
-> ExpertABottleneckEmbedder.embed_audio(path)
   -> data_loader._extract_logmel(path)
   -> Expert A encoder + bottleneck
-> compute_timbre_values_timed(path)
   -> timbral_models.timbral_sharpness
   -> timbral_models.timbral_roughness
   -> timbral_models.timbral_booming
   -> timbral_models.timbral_brightness
   -> timbral_models.timbral_depth
      -> timbral_models.timbral_util.file_read
      -> librosa resample/onset helpers
```

## Root Cause

The installed AudioCommons `timbral_models` package uses legacy positional API
calls that are incompatible with the currently installed NumPy/librosa stack:

- `librosa.core.resample(audio, fs, target_fs)`
- `librosa.onset.onset_detect(audio, fs, ...)`
- `librosa.onset.onset_strength(audio, fs)`
- `np.lib.pad(...)`

Current librosa requires keyword-only `orig_sr`, `target_sr`, `y`, and `sr`.
Current NumPy exposes `np.pad` rather than the old `np.lib.pad` alias.

The pre-fix one-sample path and array runs failed before completing the first
reference:

```text
TypeError: resample() takes 1 positional argument but 3 were given
AttributeError: module 'numpy.lib' has no attribute 'pad'
TypeError: onset_detect() takes 0 positional arguments ...
TypeError: onset_strength() takes 0 positional arguments ...
```

## Change

- Added a compatibility shim in `src/models/timbre_difference.py` that delegates
  legacy positional calls to the current NumPy/librosa APIs.
- Kept AudioCommons timbral metric formulas and functions unchanged.
- Changed `compute_timbre_values()` and
  `scripts/build_timbre_reference_index.py` to prefer the official
  AudioCommons array+`fs` API by default.
- Kept `--timbre-input path` available for explicit comparison.
- Changed generated Expert B default artifacts to use `D:\PDM_Data\MIMII\processed`
  instead of repo-local `data/processed`.
- Added per-file and summary timing labels.

## One-Sample Results

### Pre-Fix

Both modes failed:

```text
path limit=1: TypeError in timbral_util.check_upsampling -> librosa.core.resample
array limit=1: TypeError in timbral_util.check_upsampling -> librosa.core.resample
```

### Post-Fix, Array Mode

```text
AUDIO LOAD: 0.009135s
EMBEDDING: 3.949389s
METRIC/MODEL STAGES: 4.951025s
SERIALIZATION: 0.003073s
TOTAL: 9.100111s
```

### Post-Fix, Path Mode

```text
AUDIO LOAD: 0.000000s
EMBEDDING: 3.682394s
METRIC/MODEL STAGES: 5.773210s
SERIALIZATION: 0.002157s
TOTAL: 9.644822s
```

## Three-Sample Results

Post-fix array mode:

```text
AUDIO LOAD: mean=0.009838s
EMBEDDING: mean=1.691468s
METRIC/MODEL STAGES: mean=5.495459s
SERIALIZATION: 0.005166s
TOTAL PER FILE: mean=7.261207s
TOTAL: 21.789717s
```

Projected 40-file runtime from the three-sample mean:

```text
7.261207s * 40 = 290.448280s ~= 4.84 minutes
```

This was reasonable enough to run the bounded 40-file benchmark.

## Forty-File Bounded Benchmark

Post-fix array mode:

```text
AUDIO LOAD: mean=0.006413s
EMBEDDING: mean=0.156165s
METRIC/MODEL STAGES: mean=4.141237s
SERIALIZATION: 0.025348s
TOTAL PER FILE: mean=4.304610s
TOTAL: 172.222937s
```

Output artifact:

```text
D:\PDM_Data\MIMII\processed\task02_benchmarks\array_limit40_post.json
```

The output contains `40` normal reference items and metadata
`timbre_input=array`.

## Scaling

Observed 40-file total runtime:

```text
172.222937s ~= 2.87 minutes
```

Estimated full 1011-normal-reference runtime from observed 40-file mean:

```text
4.304610s * 1011 = 4352.961s ~= 72.55 minutes
```

This is operationally bounded for a planned offline build, but TASK-03 should
still decide whether the MVP needs all 1011 references or a bounded approved
normal-reference subset.

## Scientific Behavior Changed

No.

The change restores compatibility with current dependency APIs and uses the
official AudioCommons array+sample-rate input mode. It does not replace
AudioCommons metrics, change Nishida rank semantics, change `k=30`, alter Expert
A, or change SNR artifacts.

## Stop

TASK-02 stop condition is satisfied: root cause was measured, the equivalent
compatibility/array-path optimization was implemented, one-sample, three-sample,
and 40-file bounded timings were collected, and the reference-index build is no
longer pathological for the planned bounded job.
