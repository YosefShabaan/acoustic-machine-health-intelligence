# TASK-04 Same-Audio Expert A To Expert B Smoke

Date: 2026-07-07

Task: `TASK-04 - Expert A To Expert B Same-Audio Integration`

## Output Artifact

```text
D:\PDM_Data\MIMII\processed\expert_b_smoke_fan_id_00_minus6dB_task04.json
```

This artifact is external to the Git repository.

## Command

```text
python scripts\run_expert_b_smoke.py --machine-type fan --machine-id id_00 --snr-tag minus6dB --max-scan 10 --output D:\PDM_Data\MIMII\processed\expert_b_smoke_fan_id_00_minus6dB_task04.json
```

## Actual Output

```text
Expert B: AcousticTimbreDifferenceExpert
Status: adaptation_not_exact_reproduction
Audio: D:\PDM_Data\MIMII\fan_minus6dB\id_00\abnormal\00000002.wav
Expert A: score=0.622095 threshold=0.593284 is_anomaly=True
References: 30/40
Top timbre rank deviations: boominess=0.000, sharpness=0.933, roughness=0.933, brightness=0.933, depth=0.667
Warnings: 3
OUTPUT=D:\PDM_Data\MIMII\processed\expert_b_smoke_fan_id_00_minus6dB_task04.json
```

## JSON Validation

```text
OUTPUT=D:\PDM_Data\MIMII\processed\expert_b_smoke_fan_id_00_minus6dB_task04.json
INPUT_AUDIO=D:\PDM_Data\MIMII\fan_minus6dB\id_00\abnormal\00000002.wav
EXPERT_A_SCORE=0.622095
THRESHOLD=0.593284
POOL_SIZE=40
SELECTED_COUNT=30
RANK_SCORES=boominess:0.000000,brightness:0.933333,depth:0.666667,roughness:0.933333,sharpness:0.933333
SMOKE_JSON_VALIDATION=OK
```

## Checks Performed

- Expert A marked the same abnormal audio path as anomalous.
- Expert B characterized that same path.
- Reference filter remained `fan/id_00/minus6dB`.
- Reference pool size was 40 and selected kNN count was 30.
- Five timbre rank scores were finite and in `[0, 1]`.
- `rank_threshold` was `null`.
- `direction` and `direction_code` were `null` for every timbre attribute.
- No `confidence_pct`, `root_cause`, or `diagnosis` keys were present.

## Scientific Review

- This is one bounded same-audio smoke, not a quantitative Expert B accuracy evaluation.
- Expert B remains a Nishida-inspired project adaptation using Expert A bottleneck embeddings.
- No physical root-cause, diagnosis, confidence, or maintenance recommendation claim is made.
- Quantitative timbre-direction validation remains blocked by missing five-attribute labels.

## Result

`TASK-04` is `DONE`: one abnormal Fan `id_00` minus6dB event was scored by Expert A, passed to Expert B using the same audio path, saved as JSON, and inspected.
