# Fan MVP Final Evaluation Report

Date: 2026-07-08

Task: `TASK-12 - Fan MVP Final Evaluation And Academic Report`

Scope: MIMII Fan `id_00`, primary SNR tag `minus6dB`, one bounded same-audio end-to-end MVP path through dashboard.

## Verdict

The Fan MVP evidence package is complete for one bounded reference event:

```text
audio event
-> Expert A anomaly detection
-> Expert B same-audio timbre characterization
-> Structured Health Context
-> guarded explanation
-> approved-source retrieval layer
-> grounded maintenance output using fixture evidence
-> end-to-end JSON artifact
-> static dashboard HTML artifact
```

This is not a production validation and not a broad machine-generalization result. It supports a bounded Fan `id_00` integration claim with explicit scientific limits.

## Artifacts Inspected

| Artifact | Path | Status |
|---|---|---|
| SNR summary JSON | `D:\PDM_Data\MIMII\processed\snr_ad_summary.json` | present, 1838 bytes |
| Expert B same-audio smoke | `D:\PDM_Data\MIMII\processed\expert_b_smoke_fan_id_00_minus6dB_task04.json` | present, 12086 bytes |
| Structured Health Context | `D:\PDM_Data\MIMII\processed\structured_context_fan_id_00_minus6dB_task06.json` | present, 8913 bytes |
| Guarded explanation | `D:\PDM_Data\MIMII\processed\guarded_explanation_fan_id_00_minus6dB_task07.json` | present, 3094 bytes |
| RAG retrieval smoke | `D:\PDM_Data\MIMII\processed\rag_retrieval_smoke_task08.json` | present, 3955 bytes |
| Grounded maintenance output | `D:\PDM_Data\MIMII\processed\grounded_maintenance_output_fan_id_00_minus6dB_task09.json` | present, 4496 bytes |
| End-to-end Fan output | `D:\PDM_Data\MIMII\processed\end_to_end_fan_id_00_minus6dB_task10.json` | present, 31945 bytes |
| Dashboard HTML | `D:\PDM_Data\MIMII\processed\dashboard_fan_id_00_minus6dB_task11.html` | present, 7561 bytes |

## Expert A Evaluation

Verified repository fact: Expert A uses a normal-only Conv1D autoencoder and reconstruction error for Fan `id_00` anomaly detection.

Verified repository fact: the controlled SNR experiment used the same architecture and preprocessing across three Fan `id_00` SNR variants.

| SNR | AUC | Threshold | Normal Mean | Abnormal Mean | Recall | FPR | Specificity |
|---|---:|---:|---:|---:|---:|---:|---:|
| `minus6dB` | 0.6142 | 0.593284 | 0.436479 | 0.457600 | 0.14 | 0.135 | 0.865 |
| `0dB` | 0.8306 | 0.680019 | 0.458514 | 0.836641 | 0.52 | 0.130 | 0.870 |
| `plus6dB` | 0.9980 | 1.133451 | 0.706523 | 3.223253 | 1.00 | 0.050 | 0.950 |

Supported interpretation: low SNR is strongly indicated as the primary limitation of the weak `minus6dB` separation in this controlled experiment.

Unsupported interpretation: the autoencoder is perfect, noise is the only possible limitation, or the same performance holds for every machine.

## Expert B Evaluation

Paper fact: Nishida et al. motivate timbre-difference characterization using five timbre attributes: sharpness, roughness, boominess, brightness, and depth.

Project decision: the current Expert B is a Nishida-inspired adaptation, not an exact paper reproduction. It uses Expert A bottleneck embeddings and Euclidean distance as MVP choices.

Verified repository fact: TASK-03 created a bounded normal reference index for `fan/id_00/minus6dB` with 40 normal references. The default Expert B `k=30` selection was validated.

Verified repository fact: TASK-04 scored and characterized the same abnormal audio event:

```text
D:\PDM_Data\MIMII\fan_minus6dB\id_00\abnormal\00000002.wav
```

Expert A gate for the selected event:

```text
score=0.6220951080322266
threshold=0.5932844281196594
is_anomaly=true
```

Expert B reference scope:

```text
pool_size=40
selected_count=30
machine_type=fan
machine_id=id_00
snr_tag=minus6dB
normal_reference_only=true
```

Expert B rank scores:

| Attribute | Rank Score | Allowed qualitative reading |
|---|---:|---|
| boominess | 0.000000 | low relative rank among selected normal references |
| brightness | 0.933333 | high relative rank among selected normal references |
| depth | 0.666667 | above the local reference middle |
| roughness | 0.933333 | high relative rank among selected normal references |
| sharpness | 0.933333 | high relative rank among selected normal references |

Verified repository fact: `rank_threshold=null`, so all Expert B direction labels remain null by design.

Blocked scientific claim: Expert B timbre-direction accuracy cannot be quantified on the current Fan data because five-attribute timbre-difference labels are unavailable.

## Structured Context And Explanation

Verified repository fact: TASK-06 produced a Structured Health Context artifact with `schema_version=0.1.0`, event id `fan_id_00_minus6dB_00000002`, and six explicit system limitations.

Verified repository fact: TASK-07 produced a deterministic guarded explanation. It separates observations, hypotheses, inspection notes, and limitations.

Project decision: LLM-facing language is evidence-first and must not infer physical root cause, remaining useful life, exact time-to-failure, confidence percentage, or component diagnosis.

## RAG And Maintenance Output

Verified repository fact: TASK-08 implemented a manifest-gated local retriever that preserves source IDs, snippets, versions, chunk IDs, and paths.

Verified repository fact: the production maintenance knowledge base is empty because this file is absent:

```text
D:\IOT\data\manuals\approved_sources.json
```

Verified repository fact: TASK-08 fixture runtime gate indexed one approved fixture source and one chunk. The maximum measured fixture retrieval time was `0.000941s`.

Verified repository fact: TASK-09 produced a grounded maintenance output in `source_grounded` mode using a local approved fixture source, not a production manual.

Production limitation: production maintenance recommendations remain unavailable until approved production maintenance documents are supplied through the manifest.

## End-To-End Fan MVP Output

Verified repository fact: TASK-10 produced one end-to-end output:

```text
D:\PDM_Data\MIMII\processed\end_to_end_fan_id_00_minus6dB_task10.json
```

Actual end-to-end event summary:

```text
event_id=fan_id_00_minus6dB_00000002
audio=D:\PDM_Data\MIMII\fan_minus6dB\id_00\abnormal\00000002.wav
expert_a_score=0.6220951080322266
expert_a_threshold=0.5932844281196594
expert_a_is_anomaly=true
expert_b_selected=30
expert_b_pool=40
maintenance_mode=source_grounded
recommendation_available=true
citation=task10_fixture_fan_inspection
source_mode=approved_fixture_not_production_manual
total_seconds=15.792862000060268
```

Scientific interpretation: the same-event Fan MVP path works for one bounded abnormal event and preserves event identity across components.

Scientific limit: the successful maintenance recommendation is fixture-grounded, not production-manual-grounded.

## Dashboard Output

Verified repository fact: TASK-11 rendered:

```text
D:\PDM_Data\MIMII\processed\dashboard_fan_id_00_minus6dB_task11.html
```

Dashboard inspection:

```text
html_size_bytes=7561
required_sections_present=true
citation_visible=task10_fixture_fan_inspection
forbidden_hits=[]
```

Displayed sections:

- event metadata
- Expert A anomaly evidence
- Expert B timbre rank scores
- explanation observations and hypotheses
- retrieved source evidence
- recommendation and citations
- limitations

Dashboard limit: this is a static one-artifact MVP, not a full multi-event web application.

## Tests And Reviews

Verified task-log fact: the following tests passed during TASK-11 and upstream task execution:

| Test | Result |
|---|---|
| `python tests/test_dashboard.py` | 3 tests OK |
| `python tests/test_end_to_end_orchestrator.py` | 4 tests OK |
| `python tests/test_maintenance_agent.py` | 5 tests OK |
| `python tests/test_rag_grounding.py` | 4 tests OK |
| `python tests/test_llm_guardrails.py` | 4 tests OK |
| `python tests/test_context_schema.py` | 5 tests OK |
| `python tests/test_timbre_difference.py` | 7 tests OK |

TASK-12 added documentation only and did not run model training, dataset preprocessing, Expert B indexing, or scoring.

## Supported Claims

- Expert A detects anomalous Fan `id_00` sounds under the evaluated project split.
- Expert A performance is SNR-sensitive in the controlled Fan `id_00` experiment.
- Low SNR is strongly indicated as the primary limitation of weak `minus6dB` separation.
- A bounded Expert B reference index exists for Fan `id_00` `minus6dB`.
- Expert B can characterize one Expert A-flagged Fan event using same-machine normal references and five timbre rank scores.
- Structured Health Context, guarded explanation, local retrieval, grounded maintenance output, end-to-end orchestration, and static dashboard artifacts exist for the bounded Fan MVP.

## Unsupported Claims

- Expert B accurately predicts timbre direction on Fan `id_00`.
- Expert B diagnoses a physical fault or root cause.
- Rank scores are confidence, probability, or severity percentages.
- The system predicts remaining useful life or exact time to failure.
- Production maintenance recommendations are grounded in approved production manuals.
- The Fan result generalizes to Pump, Valve, Slide Rail, or MIMII DG domain-shift settings.
- The current implementation exactly reproduces Nishida et al.

## Current Blockers

| Blocker | Effect |
|---|---|
| No five-attribute timbre-difference labels for current Fan data | blocks quantitative Expert B direction accuracy |
| No approved production maintenance manifest | blocks production maintenance recommendations |
| Pump, Valve, Slide Rail data are not staged | blocks next generalization tasks |
| MIMII DG data/assets are not staged | blocks domain robustness evaluation |
| RUL/PRONOSTIA are outside active architecture | blocks any RUL claim by design |

## Final TASK-12 Decision

Project decision: mark the Fan `id_00` MVP evidence package complete through a static dashboard and final claims report, while keeping production maintenance grounding and multi-machine/domain generalization as future blocked/planned work.

Stop condition reached: final Fan MVP evidence package exists and every supported/unsupported claim is explicit.
