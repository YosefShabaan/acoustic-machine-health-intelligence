# RAG Retrieval Evaluation

Task: `TASK-RAG-05`

Date: 2026-07-09

Evaluation set: `AMHI-FAN-MAINT-RETRIEVAL-EVAL-v1`

Corpus version: `AMHI-FAN-MAINT-KB-v1`

External result artifact:

```text
D:\PDM_Data\MIMII\processed\rag_retrieval_evaluation_amhi_fan_maint_kb_v1_task_rag_05.json
```

## Purpose

Compare the current lexical retriever, Gemini semantic retriever, and a simple
reciprocal-rank-fusion hybrid on the bounded Fan maintenance retrieval
evaluation set.

This is a project retrieval evaluation. It is not paper ground truth and does
not validate maintenance correctness.

## Retrievers

| Retriever | Implementation | Runtime dependency |
|---|---|---|
| Lexical | `LocalRetriever` cosine over token counts | local only |
| Semantic | `SemanticRetriever` over external `gemini-embedding-2` chunk index | Gemini query embedding call |
| Hybrid | Reciprocal-rank fusion of lexical and semantic ranks | lexical plus semantic |

Semantic index:

```text
D:\PDM_Data\MIMII\processed\rag_semantic_embeddings_amhi_fan_maint_kb_v1_gemini_embedding_2_768.json
```

## Runtime Gate

Small timing run:

```text
python scripts\evaluate_rag_retrieval.py --limit 3 --output D:\PDM_Data\MIMII\processed\rag_retrieval_evaluation_task_rag_05_limit3.json
QUERY_COUNT=3
LEXICAL HIT_AT_3=1.0 MEAN_LATENCY_SECONDS=0.001915
SEMANTIC HIT_AT_3=1.0 MEAN_LATENCY_SECONDS=4.094736
HYBRID HIT_AT_3=1.0 MEAN_LATENCY_SECONDS=4.096726
```

Full bounded run:

```text
python scripts\evaluate_rag_retrieval.py
QUERY_COUNT=24
TOP_K=15
```

## Metrics

| Retriever | Hit@1 | Hit@3 | MRR | Mean latency seconds | Max latency seconds | Failures |
|---|---:|---:|---:|---:|---:|---:|
| Lexical | 0.875000 | 0.958333 | 0.918056 | 0.000793 | 0.001485 | 1 |
| Semantic | 0.958333 | 1.000000 | 0.979167 | 1.889571 | 6.188017 | 0 |
| Hybrid | 0.916667 | 1.000000 | 0.958333 | 1.890422 | 6.189254 | 0 |

Primary metric: Hit@3.

Secondary metrics: MRR, Hit@1, and latency.

## Failure Analysis

Lexical had one Hit@3 failure:

```text
query_id=fan_eval_022
query=What source supports using maintenance logs to trend fan acoustic and inspection changes?
failure_reason=expected_source_absent_top3
expected_chunk=doe_fan_sourcebook_2003#DOE-FAN-2003-RECORDS
top1=doe_om_best_practices_release_3_fans#DOE-OM-R3-MAINTENANCE-PROGRAMS
top2=doe_om_best_practices_release_3_fans#DOE-OM-R3-FAN-CHECKLIST-VISUAL
top3=doe_om_best_practices_release_3_fans#DOE-OM-R3-PREDICTIVE-MAINTENANCE
```

Top-1 expected-chunk mismatch count:

| Retriever | Top-1 mismatches | Notes |
|---|---:|---|
| Lexical | 3 | Records and duct/electrical wording were vulnerable to broad lexical overlap. |
| Semantic | 1 | `fan_eval_002` returned a broader Fan Sourcebook maintenance chunk before vibration monitoring. |
| Hybrid | 2 | Fusion fixed the lexical top-3 failure but kept two top-1 mismatches. |

## Project Decision

Selected Fan MVP retriever:

```text
semantic
```

Decision policy:

```text
Choose highest Hit@3, then MRR, then Hit@1, then lower mean latency, then
simpler runtime dependency.
```

Reason:

- Semantic achieved the best Hit@3, MRR, and Hit@1 on the bounded 24-query
  project evaluation set.
- Hybrid matched semantic on Hit@3 but trailed on MRR and Hit@1.
- Lexical was much faster but had one Hit@3 failure and weaker MRR.

This is a `PROJECT DECISION`, not a paper fact or production validation claim.

## Limitations

- The evaluation set is a project annotation artifact, not external ground truth.
- The corpus has 15 chunks from two approved public DOE-derived Fan maintenance
  notes.
- Semantic retrieval needs a live Gemini query embedding call unless query
  embeddings are cached later.
- Retrieval quality does not validate maintenance recommendation correctness.
- This result does not enable RUL, physical root-cause, probability/confidence,
  production maintenance grounding, or multi-machine generalization claims.

## Next

`TASK-MAINT-01` can use the selected semantic retriever for bounded
Gemini-backed grounded maintenance actions, while preserving source citations
and all scientific guardrails.
