# Expert B Qualitative Evidence Protocol

Date: 2026-07-07

Scope: Fan `id_00` MVP, `minus6dB`, same-audio Expert A -> Expert B outputs.

## Purpose

Define a repeatable qualitative review protocol for Expert B outputs when no
five-attribute timbre-difference labels are available.

This protocol supports:

- integration review,
- schema and event-identity review,
- same-machine reference review,
- qualitative timbre-rank characterization.

This protocol does not support:

- quantitative timbre-direction accuracy,
- physical root-cause diagnosis,
- failure probability or confidence,
- exact Nishida reproduction claims.

## Fact Register

PAPER FACT:

- Nishida et al. use five timbre attributes: sharpness, roughness, boominess,
  brightness, and depth.
- The method ranks a test timbre value relative to `k` selected normal
  reference values.
- The paper experiments use `k=30` and convert rank scores to directions only
  with an inference threshold.

VERIFIED REPOSITORY FACT:

- The current Fan `id_00` data do not include five-attribute timbre-difference
  ground-truth labels.
- The current MVP uses `rank_threshold=None`; therefore `direction` and
  `direction_code` are intentionally `null`.
- TASK-03 produced a loadable 40-reference normal index for
  `fan/id_00/minus6dB`.
- TASK-04 produced one same-audio abnormal Expert A -> Expert B smoke JSON:

```text
D:\PDM_Data\MIMII\processed\expert_b_smoke_fan_id_00_minus6dB_task04.json
```

PROJECT DECISION:

- Expert B is a Nishida-inspired adaptation, not an exact reproduction.
- Expert A bottleneck embeddings are used as the current MVP embedding adapter.
- Qualitative review can describe a rank score as low, middle, or high relative
  to selected same-machine normal references, but must not call that a validated
  direction label.

UNKNOWN:

- Paper-equivalent Expert B accuracy on this Fan dataset.
- The correct inference threshold for validated direction labels.
- Whether the current Expert A bottleneck embedding is the best neighbor space
  for timbre-difference evaluation.

## Required Inputs

For every qualitative review record:

- Expert B JSON output path.
- Input audio path.
- Expert A score, threshold, and anomaly boolean.
- Expert B method metadata.
- Reference filter and selected neighbor list.
- Five timbre rank scores.
- Warnings/limitations emitted by Expert B.

Optional controls:

- A normal/control audio event scored by Expert A.
- If Expert A does not flag the normal/control audio, Expert B should not run in
  the default runtime path; record this as a skip/refusal, not as missing data.
- If Expert A flags a normal-labeled clip, review it as a detector false-positive
  or borderline case, not as physical abnormality ground truth.

## Review Procedure

1. Event identity check

Confirm the same `input_audio.path` is the audio event scored by Expert A and
characterized by Expert B.

2. Expert A gate check

Expert B may be reviewed only when:

```text
expert_a.is_anomaly == true
expert_a.anomaly_score > expert_a.threshold
```

3. Reference policy check

Confirm:

```text
references.pool_size >= method.k
references.selected_count == method.k
references.filter.machine_type == input_audio.machine_type
references.filter.machine_id == input_audio.machine_id
references.filter.snr_tag == input_audio.snr_tag
all neighbor paths are normal reference clips
```

4. Timbre score check

For each of the five attributes:

```text
test_value is finite
all reference_values are finite
rank_score is in [0, 1]
direction is null when rank_threshold is null
direction_code is null when rank_threshold is null
```

5. Qualitative interpretation

Use rank-score language only:

- score near `0`: low relative rank among selected normal references.
- score near `0.5`: near the local reference middle.
- score near `1`: high relative rank among selected normal references.

Allowed phrasing:

```text
sharpness has a high relative rank among the selected normal references.
boominess has a low relative rank among the selected normal references.
```

Forbidden phrasing:

```text
sharpness increased with validated accuracy.
boominess proves the fault cause.
rank_score is confidence.
rank_score is failure probability.
```

6. Neighbor inspection

Record:

- selected reference count,
- closest 3 to 5 normal reference paths,
- distance range among selected references,
- whether all references are from the same machine/SNR scope.

7. Limitations check

Confirm the output or review notes state:

- no paper-specific timbre labels are available,
- Expert A bottleneck is a project adaptation,
- no direction threshold is configured,
- no diagnosis/root-cause/confidence claim is made.

## MVP Review Record

Source output:

```text
D:\PDM_Data\MIMII\processed\expert_b_smoke_fan_id_00_minus6dB_task04.json
```

Input audio:

```text
D:\PDM_Data\MIMII\fan_minus6dB\id_00\abnormal\00000002.wav
```

Expert A gate:

```text
score=0.6220951080322266
threshold=0.5932844281196594
is_anomaly=true
```

Reference review:

```text
pool_size=40
selected_count=30
filter=fan/id_00/minus6dB
closest_neighbor=D:\PDM_Data\MIMII\fan_minus6dB\id_00\normal\00000029.wav
closest_distance=1.2268335819244385
farthest_selected_distance=47.867679595947266
```

Rank-score review:

| Attribute | Rank Score | Qualitative Review Phrase |
|---|---:|---|
| boominess | 0.000000 | low relative rank among selected normal references |
| brightness | 0.933333 | high relative rank among selected normal references |
| depth | 0.666667 | above the local reference middle |
| roughness | 0.933333 | high relative rank among selected normal references |
| sharpness | 0.933333 | high relative rank among selected normal references |

Interpretation allowed:

- The selected abnormal event has high relative rank scores for sharpness,
  roughness, and brightness compared with its selected local normal references.
- Boominess has a low relative rank score for this selected event.
- Depth is above the local reference middle.

Interpretation not allowed:

- The event is diagnosed as a specific mechanical fault.
- The rank scores are confidence percentages.
- Expert B direction accuracy is validated.
- The output is an exact Nishida reproduction.

## Acceptance Criteria

A qualitative Expert B review is acceptable when:

- the same audio event is preserved,
- Expert A flagged the event before Expert B ran,
- references are normal and same machine/id/SNR,
- all five rank scores are finite and in `[0, 1]`,
- limitations are stated,
- no unsupported confidence, diagnosis, root-cause, RUL, or direction-accuracy
  claim appears.

## Stop Conditions

Stop and mark the review blocked if:

- no Expert B JSON exists,
- input audio identity is ambiguous,
- reference scope mixes machine ID or SNR without explicit approval,
- any rank score is non-finite or outside `[0, 1]`,
- the output contains diagnosis, confidence, root-cause, or RUL fields,
- the review requires quantitative accuracy claims without labels.

## Next Use

TASK-06 should translate Expert A and Expert B outputs into structured context
while preserving this protocol's limitations and claim boundaries.
