# Fan System Evaluation

Date: 2026-07-09

Task: `TASK-FAN-14`

Artifact:

```text
D:\PDM_Data\MIMII\processed\fan_system_evaluation_fan_id_00_minus6dB_task_fan_14.json
```

## Scope

This is a bounded Fan `id_00` integration evaluation for the real Gemini +
semantic RAG pipeline. It is not Expert A retraining, Expert B direction
accuracy validation, fault-diagnosis accuracy, production maintenance
validation, or multi-machine generalization.

## Event Selection

The evaluation used 20 Fan `id_00` `minus6dB` events:

- 10 normal events: first 10 lexicographic normal WAV files.
- 10 abnormal events: first 10 Expert A-flagged abnormal WAV files found by
  lexicographic scan, excluding the `TASK-FAN-13` reference event
  `00000002.wav` to avoid duplicate Gemini calls.

This abnormal-event policy is intentionally an integration stress set so that
the downstream Expert B -> context -> RAG -> Gemini -> maintenance path is
exercised multiple times. It must not be used as an Expert A recall estimate.

Abnormal candidates scanned: 59.

Selected abnormal events:

```text
00000012.wav
00000013.wav
00000015.wav
00000022.wav
00000036.wav
00000048.wav
00000050.wav
00000055.wav
00000057.wav
00000058.wav
```

## Preflight

Required preflight checks before live generation:

- Unit tests passed before the live run: 75 tests OK.
- One-event timing source: `TASK-FAN-13` artifact.
- First three evaluation events contained 1 Expert A-flagged continuation.
- First three estimated Gemini calls: 3.
- Full evaluation Expert A-flagged continuations: 10.
- Full evaluation estimated Gemini calls: 30.
- The run was sequential with no parallel Gemini burst.
- The `TASK-FAN-13` reference event was excluded to avoid duplicate live calls.

The estimated run was considered reasonable under the bounded `max_live_continuations=10` gate.

## Results

| Metric | Value |
|---|---:|
| Total events | 20 |
| Normal events | 10 |
| Abnormal events | 10 |
| Expert A flagged count | 10 |
| Expert B execution count | 10 |
| Same-audio identity successes | 10 |
| Context validation successes | 10 |
| Retrieval available | 10 |
| Gemini explanation successes | 10 |
| Gemini explanation fallbacks | 0 |
| Maintenance generation successes | 10 |
| Maintenance fallbacks | 0 |
| Citation validation failures | 0 |
| Pipeline failures | 0 |
| Forbidden claim failures | 0 |

Top retrieved source distribution:

```text
doe_fan_sourcebook_2003: 10
```

Maintenance actions per completed continuation ranged from 3 to 5.

## Latency

Pipeline continuation latency:

| Stage | Count | Mean seconds | Min seconds | Max seconds |
|---|---:|---:|---:|---:|
| Expert B | 10 | 2.337851 | 2.122480 | 3.022462 |
| Gemini explanation | 10 | 8.050632 | 6.923133 | 9.812262 |
| Semantic retrieval | 10 | 1.556154 | 1.334269 | 2.028216 |
| Gemini maintenance | 10 | 11.398627 | 6.655848 | 20.786967 |
| Completed pipeline total | 10 | 23.444230 | 18.117228 | 31.403587 |

Total evaluation wall time:

```text
242.509219 seconds
```

## Failure Analysis

No pipeline failures were observed.

No Gemini explanation fallback occurred.

No maintenance-generation fallback occurred.

No citation validation failure occurred.

No forbidden claim pattern was found in generated user-facing explanation or
maintenance output.

The main observed runtime cost is live Gemini maintenance generation latency.
The slowest maintenance generation stage took 20.786967 seconds.

## Scientific Guardrails

This evaluation supports only bounded Fan integration evidence:

- Expert A gates downstream processing.
- Expert B only runs for Expert A-flagged events.
- Same-audio identity is preserved for completed continuations.
- Structured Health Context v0.2 is generated and validated.
- Selected semantic RAG returns approved Fan maintenance chunks.
- Gemini explanation and maintenance outputs can complete without fallback for
  this bounded event set.
- Maintenance actions cite retrieved source_id/chunk_id pairs.

This evaluation still does not support:

- physical root-cause diagnosis,
- fault probability or confidence,
- severity percentage,
- remaining useful life,
- time-to-failure,
- Expert B quantitative timbre-direction accuracy,
- production maintenance validation,
- Pump, Valve, Slide Rail, cross-machine, or MIMII DG generalization.
