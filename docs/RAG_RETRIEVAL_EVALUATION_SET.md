# RAG Retrieval Evaluation Set

Task: `TASK-RAG-04`

Date: 2026-07-09

Evaluation set: `AMHI-FAN-MAINT-RETRIEVAL-EVAL-v1`

Corpus version: `AMHI-FAN-MAINT-KB-v1`

## Purpose

Create a transparent bounded retrieval evaluation set for Fan maintenance RAG.
The queries are project annotations grounded only in the approved corpus. They
are not paper ground truth and do not validate maintenance correctness.

Machine scope:

```text
machine_type=fan
machine_id=N/A for corpus evaluation
```

## Artifact

Tracked evaluation artifact:

```text
data/manuals/fan_maintenance_retrieval_eval_v1.json
```

It contains 24 manually reviewed queries. Each row records:

- `query_id`
- `query`
- `expected_source_ids`
- `expected_chunk_ids`
- `rationale`

## Query Theme Coverage

```text
abnormal fan acoustic noise
vibration monitoring and baseline comparison
inspection recordkeeping
belt wear, slippage, tension, and alignment
pulsing airflow noise and vibrating supports
system operating context
visual inspection and safety systems
sequencing / unnecessary equipment
pulley wheels, dampers, actuator linkage, fan blades
wiring, ductwork, filters, system integrity, duct insulation
predictive maintenance / condition review
AMHI limitation chunks
```

## Manual Review

All expected chunk IDs were checked against the section-aware corpus inventory.
No query was added for absent topics. Queries involving diagnosis, fault
probability, confidence, RUL, time-to-failure, or multi-machine claims were
excluded except for the final limitations query, whose expected chunks are the
corpus limitation sections.

## Runtime Gate

Validation is implemented in `tests/test_rag_evaluation_set.py`.

The test verifies:

- query count is between 20 and 30,
- query IDs are unique,
- every expected source ID and chunk ID exists in the approved corpus,
- required fields are nonempty,
- forbidden overclaim wording is absent from the query text and rationale,
- the artifact is explicitly marked as project annotation, not paper ground
  truth.

## Next

`TASK-RAG-05` should evaluate lexical, semantic, and then simple hybrid
retrieval against this set using Hit@1, Hit@3, MRR, latency, and failure
analysis.

Do not select the Fan MVP retriever before that comparison.
