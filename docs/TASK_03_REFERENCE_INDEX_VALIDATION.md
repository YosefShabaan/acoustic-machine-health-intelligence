# TASK-03 Reference Index Validation

Date: 2026-07-07

Task: `TASK-03 - Expert B Reference Index Completion`

## Artifact

```text
D:\PDM_Data\MIMII\processed\timbre_reference_index_fan_id_00_minus6dB.json
```

This artifact is external to the Git repository.

## Build Commands

One-sample smoke:

```text
python scripts\build_timbre_reference_index.py --machine-type fan --machine-id id_00 --snr-tag minus6dB --limit 1 --output D:\PDM_Data\MIMII\processed\task03_benchmarks\timbre_reference_index_fan_id_00_minus6dB_limit1_task03.json
```

Three-sample timing:

```text
python scripts\build_timbre_reference_index.py --machine-type fan --machine-id id_00 --snr-tag minus6dB --limit 3 --output D:\PDM_Data\MIMII\processed\task03_benchmarks\timbre_reference_index_fan_id_00_minus6dB_limit3_task03.json
```

Final bounded index:

```text
python scripts\build_timbre_reference_index.py --machine-type fan --machine-id id_00 --snr-tag minus6dB --limit 40
```

## Actual Timings

```text
one sample:  TOTAL=11.351220s
three sample: TOTAL=21.175939s
40 sample:   TOTAL=162.762365s
40 sample mean total/file: 4.067785s
```

## Validation Output

```text
INDEX=D:\PDM_Data\MIMII\processed\timbre_reference_index_fan_id_00_minus6dB.json
REFERENCES=40
FILTERED=40
KNN_SELECTED=30
METADATA_K=30
TIMBRE_MODEL=AudioCommons timbral_models
TIMING_MEAN_TOTAL=4.067785
VALIDATION=OK
```

## Metadata Included

- `machine_type`: `fan`
- `machine_id`: `id_00`
- `snr_tag`: `minus6dB`
- `embedding_model`: `expert_a_bottleneck_adaptation`
- `timbre_model`: `AudioCommons timbral_models`
- `method_status`: `adaptation_not_exact_reproduction`
- `k`: `30`
- `distance`: `euclidean`
- `reference_count`: `40`
- `usable_for_default_k`: `true`
- `normal_reference_only`: `true`
- `timbre_input`: `array`
- `timing_summary`: present
- per-file `timings`: present

## Scientific Review

- All references are normal WAVs under `D:\PDM_Data\MIMII\fan_minus6dB\id_00\normal`.
- No abnormal clip path was included.
- All reference items match `fan/id_00/minus6dB`.
- Expert A bottleneck remains labeled as a project MVP adaptation.
- No paper-equivalent Expert B accuracy claim is made.
- No quantitative timbre-direction claim is made because current Fan data do not include five-attribute timbre labels.

## Result

`TASK-03` is `DONE`: the usable Fan `id_00` minus6dB Expert B reference index exists, is loadable, has at least `k=30` references, and passes same-machine filtering and kNN validation.
