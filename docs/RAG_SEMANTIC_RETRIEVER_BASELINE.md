# RAG Semantic Retriever Baseline

Task: `TASK-RAG-03`

Date: 2026-07-09

Corpus version: `AMHI-FAN-MAINT-KB-v1`

## Official Model Basis

The selected embedding model is:

```text
gemini-embedding-2
```

Reason:

- Google AI Gemini documentation lists `gemini-embedding-2` as the stable latest
  Gemini embedding model.
- It supports text input and information retrieval / RAG use cases.
- The configured output dimension is 768, which is in the documented
  recommended range.
- For text-only retrieval with Embedding 2, task intent is included in the
  prompt text instead of using a `task_type` field.

Project configuration:

```text
GEMINI_EMBEDDING_MODEL=gemini-embedding-2
GEMINI_EMBEDDING_DIMENSION=768
```

## Implementation

Added:

- `src/rag/semantic_retriever.py`
- `scripts/build_rag_semantic_index.py`
- `tests/test_semantic_retriever.py`

The lexical `LocalRetriever` remains the baseline and was not removed.

The semantic retriever:

- embeds approved knowledge chunks,
- writes a machine-readable external JSON artifact,
- loads cached vectors,
- embeds a query,
- ranks chunks by cosine similarity,
- returns the same source-preserving retrieval contract.

No vector database, FAISS, pgvector, Pinecone, Chroma, or new persistence service
was added.

## External Embedding Artifact

```text
D:\PDM_Data\MIMII\processed\rag_semantic_embeddings_amhi_fan_maint_kb_v1_gemini_embedding_2_768.json
```

Artifact metadata inspected:

```text
schema_version=1.0.0
artifact_type=rag_semantic_embedding_index
corpus_version=AMHI-FAN-MAINT-KB-v1
embedding_provider=gemini
embedding_model=gemini-embedding-2
embedding_dimension=768
chunk_count=15
first_vector_len=768
artifact_bytes=278680
```

The artifact is generated and must not be committed to Git.

## Runtime Gate

Unit tests:

```text
python -m unittest discover -s tests -p "test_semantic_retriever.py"
Ran 2 tests
OK

python -m unittest discover -s tests -p "test_rag_grounding.py"
Ran 6 tests
OK
```

Build command:

```powershell
python scripts\build_rag_semantic_index.py
```

Observed output:

```text
RAG_SEMANTIC_INDEX_BUILD=OK
CORPUS_VERSION=AMHI-FAN-MAINT-KB-v1
EMBEDDING_PROVIDER=gemini
EMBEDDING_MODEL=gemini-embedding-2
EMBEDDING_DIMENSION=768
SOURCE_COUNT=2
CHUNK_COUNT=15
BUILD_SECONDS=31.496806
```

Semantic retrieval smoke query:

```text
fan abnormal acoustic noise inspect vibration belts and maintenance records
```

Top returned chunks:

```text
1. doe_fan_sourcebook_2003#DOE-FAN-2003-COMMON-FAN-PROBLEMS score=0.844667
2. doe_om_best_practices_release_3_fans#DOE-OM-R3-MAINTENANCE-PROGRAMS score=0.827783
3. doe_fan_sourcebook_2003#DOE-FAN-2003-BASIC-MAINTENANCE score=0.826278
```

Manual inspection:

- Returned chunks are relevant to fan/motor assembly problems, maintenance
  program context, and basic maintenance.
- Returned results preserve source ID, chunk ID, section ID, section heading,
  source URL, and corpus version.
- No maintenance action is generated in this task.

## Limits

This task enables semantic retrieval plumbing and a generated embedding cache.
It does not prove that semantic retrieval is better than lexical retrieval.

The selected production retriever is not decided here. `TASK-RAG-04` and
`TASK-RAG-05` must create a retrieval evaluation set and compare lexical,
semantic, and hybrid retrieval before a project decision is made.

This task does not enable:

- root-cause diagnosis,
- RUL or time-to-failure prediction,
- confidence or probability claims,
- Expert B timbre-direction accuracy,
- production maintenance validation.
