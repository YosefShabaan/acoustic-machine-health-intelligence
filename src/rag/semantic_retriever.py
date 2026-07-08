"""Gemini semantic retrieval over approved maintenance chunks."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import json
import math
from pathlib import Path
from time import perf_counter
from typing import Any, Protocol

import config as cfg

from .knowledge_base import KnowledgeBase, KnowledgeChunk, build_knowledge_base
from .retriever import RetrievalResponse, RetrievalResult


EMBEDDING_ARTIFACT_SCHEMA_VERSION = "1.0.0"
EMBEDDING_PROVIDER = "gemini"


class EmbeddingProvider(Protocol):
    """Minimal embedding provider protocol."""

    def embed_text(self, text: str, *, purpose: str) -> list[float]:
        """Return one embedding vector for text."""

    def metadata(self) -> dict[str, Any]:
        """Return non-secret embedding provider metadata."""


@dataclass(frozen=True)
class EmbeddingRecord:
    """One embedded approved maintenance chunk."""

    source_id: str
    title: str
    version: str
    publisher: str
    corpus_version: str
    chunk_id: str
    section_id: str
    section_heading: str
    text_hash_sha256: str
    text: str
    path: Path
    source_url: str | None
    embedding: tuple[float, ...]

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-serializable record."""
        return {
            "source_id": self.source_id,
            "title": self.title,
            "version": self.version,
            "publisher": self.publisher,
            "corpus_version": self.corpus_version,
            "chunk_id": self.chunk_id,
            "section_id": self.section_id,
            "section_heading": self.section_heading,
            "text_hash_sha256": self.text_hash_sha256,
            "text": self.text,
            "path": str(self.path),
            "source_url": self.source_url,
            "embedding": list(self.embedding),
        }


@dataclass(frozen=True)
class SemanticEmbeddingIndex:
    """Cached semantic embedding index for approved maintenance chunks."""

    corpus_version: str
    embedding_provider: str
    embedding_model: str
    embedding_dimension: int
    created_at: str
    records: tuple[EmbeddingRecord, ...]
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-serializable index payload."""
        return {
            "schema_version": EMBEDDING_ARTIFACT_SCHEMA_VERSION,
            "artifact_type": "rag_semantic_embedding_index",
            "corpus_version": self.corpus_version,
            "embedding_provider": self.embedding_provider,
            "embedding_model": self.embedding_model,
            "embedding_dimension": self.embedding_dimension,
            "created_at": self.created_at,
            "source_count": len({record.source_id for record in self.records}),
            "chunk_count": len(self.records),
            "metadata": self.metadata,
            "chunks": [record.to_dict() for record in self.records],
        }


class GeminiEmbeddingProvider:
    """Gemini-backed embedding provider for approved text chunks."""

    def __init__(
        self,
        *,
        config: Any | None = None,
        output_dimensionality: int = cfg.GEMINI_EMBEDDING_DIMENSION,
        client: Any | None = None,
    ) -> None:
        if config is None:
            from agents.gemini_provider import GeminiProviderConfig

            config = GeminiProviderConfig(model=cfg.GEMINI_EMBEDDING_MODEL)
        self.config = config
        self.output_dimensionality = output_dimensionality
        self._client = client

    def metadata(self) -> dict[str, Any]:
        """Return non-secret provider metadata."""
        return {
            "embedding_provider": EMBEDDING_PROVIDER,
            "embedding_model": self.config.model,
            "embedding_dimension": self.output_dimensionality,
        }

    def _build_client(self) -> Any:
        """Build official Google GenAI SDK client using environment secrets."""
        from google import genai
        from google.genai import types

        return genai.Client(
            api_key=self.config.load_api_key(),
            http_options=types.HttpOptions(
                timeout=int(self.config.request_timeout_seconds * 1000)
            ),
        )

    def embed_text(self, text: str, *, purpose: str) -> list[float]:
        """Return one Gemini embedding vector."""
        from google.genai import types

        client = self._client or self._build_client()
        response = client.models.embed_content(
            model=self.config.model,
            contents=_format_embedding_input(text, purpose=purpose),
            config=types.EmbedContentConfig(
                outputDimensionality=self.output_dimensionality,
                httpOptions=types.HttpOptions(
                    timeout=int(self.config.request_timeout_seconds * 1000)
                ),
            ),
        )
        return _response_to_vector(response)


class SemanticRetriever:
    """Cosine semantic retriever over a cached embedding index."""

    def __init__(
        self,
        embedding_index: SemanticEmbeddingIndex,
        embedding_provider: EmbeddingProvider,
    ) -> None:
        self.embedding_index = embedding_index
        self.embedding_provider = embedding_provider

    def retrieve(
        self,
        query: str,
        *,
        top_k: int = 3,
        min_score: float = -1.0,
        snippet_chars: int = 320,
    ) -> RetrievalResponse:
        """Retrieve source-preserving chunks by semantic cosine similarity."""
        query = query.strip()
        if not query:
            return RetrievalResponse(
                query=query,
                available=False,
                results=(),
                message="empty retrieval query",
            )
        if not self.embedding_index.records:
            return RetrievalResponse(
                query=query,
                available=False,
                results=(),
                message="Semantic embedding index is empty.",
            )

        query_vector = self.embedding_provider.embed_text(query, purpose="query")
        scored = [
            (_cosine_similarity(query_vector, record.embedding), record)
            for record in self.embedding_index.records
        ]
        scored = [
            (score, record)
            for score, record in scored
            if score >= min_score
        ]
        scored.sort(key=lambda item: (-item[0], item[1].source_id, item[1].chunk_id))
        results = tuple(
            RetrievalResult(
                source_id=record.source_id,
                title=record.title,
                version=record.version,
                publisher=record.publisher,
                corpus_version=record.corpus_version,
                chunk_id=record.chunk_id,
                section_id=record.section_id,
                section_heading=record.section_heading,
                snippet=record.text[:snippet_chars].strip(),
                score=round(score, 6),
                path=record.path,
                source_url=record.source_url,
            )
            for score, record in scored[:top_k]
        )
        if not results:
            return RetrievalResponse(
                query=query,
                available=False,
                results=(),
                message="No semantic maintenance source matched the retrieval query.",
            )
        return RetrievalResponse(
            query=query,
            available=True,
            results=results,
            message=f"Semantic retrieval returned {len(results)} approved source chunk(s).",
        )


def default_embedding_index_path(
    corpus_version: str,
    *,
    embedding_model: str = cfg.GEMINI_EMBEDDING_MODEL,
    embedding_dimension: int = cfg.GEMINI_EMBEDDING_DIMENSION,
) -> Path:
    """Return the external generated embedding-index path."""
    safe_corpus = _safe_token(corpus_version)
    safe_model = _safe_token(embedding_model)
    return (
        cfg.PROCESSED_DIR
        / f"rag_semantic_embeddings_{safe_corpus}_{safe_model}_{embedding_dimension}.json"
    )


def build_semantic_embedding_index(
    knowledge_base: KnowledgeBase,
    embedding_provider: EmbeddingProvider,
    *,
    created_at: str | None = None,
) -> SemanticEmbeddingIndex:
    """Embed every approved knowledge chunk into a cacheable semantic index."""
    if not knowledge_base.chunks:
        raise ValueError("Cannot build semantic embedding index from an empty knowledge base")
    provider_metadata = embedding_provider.metadata()
    records: list[EmbeddingRecord] = []
    expected_dimension: int | None = None
    start = perf_counter()
    for chunk in knowledge_base.chunks:
        vector = embedding_provider.embed_text(
            _document_embedding_text(chunk),
            purpose="document",
        )
        if not vector:
            raise ValueError(f"embedding provider returned empty vector for {chunk.chunk_id}")
        if expected_dimension is None:
            expected_dimension = len(vector)
        if len(vector) != expected_dimension:
            raise ValueError(
                f"inconsistent embedding dimension for {chunk.chunk_id}: "
                f"{len(vector)} != {expected_dimension}"
            )
        records.append(_record_from_chunk(chunk, vector))

    corpus_versions = {record.corpus_version for record in records}
    corpus_version = sorted(corpus_versions)[0] if len(corpus_versions) == 1 else "mixed"
    embedding_dimension = int(
        provider_metadata.get("embedding_dimension") or expected_dimension or 0
    )
    if expected_dimension and embedding_dimension != expected_dimension:
        raise ValueError(
            f"provider metadata dimension {embedding_dimension} does not match "
            f"actual vector length {expected_dimension}"
        )
    metadata = {
        **provider_metadata,
        "source_count": knowledge_base.source_count,
        "chunk_count": len(records),
        "build_seconds": round(perf_counter() - start, 6),
    }
    return SemanticEmbeddingIndex(
        corpus_version=corpus_version,
        embedding_provider=str(provider_metadata.get("embedding_provider") or "unknown"),
        embedding_model=str(provider_metadata.get("embedding_model") or "unknown"),
        embedding_dimension=embedding_dimension,
        created_at=created_at or datetime.now(UTC).isoformat(),
        records=tuple(records),
        metadata=metadata,
    )


def write_embedding_index(index: SemanticEmbeddingIndex, output_path: Path) -> Path:
    """Write the generated semantic embedding index JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(index.to_dict(), indent=2), encoding="utf-8")
    return output_path


def load_embedding_index(path: Path) -> SemanticEmbeddingIndex:
    """Load a generated semantic embedding index JSON."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    records = tuple(_record_from_payload(row) for row in payload.get("chunks", []))
    return SemanticEmbeddingIndex(
        corpus_version=str(payload["corpus_version"]),
        embedding_provider=str(payload["embedding_provider"]),
        embedding_model=str(payload["embedding_model"]),
        embedding_dimension=int(payload["embedding_dimension"]),
        created_at=str(payload["created_at"]),
        records=records,
        metadata=dict(payload.get("metadata") or {}),
    )


def build_default_semantic_index(
    *,
    manuals_dir: Path | str = cfg.RAG_MANUALS_DIR,
    embedding_provider: EmbeddingProvider | None = None,
    output_path: Path | None = None,
) -> tuple[SemanticEmbeddingIndex, Path]:
    """Build and write the default approved corpus semantic index."""
    knowledge_base = build_knowledge_base(manuals_dir)
    provider = embedding_provider or GeminiEmbeddingProvider()
    index = build_semantic_embedding_index(knowledge_base, provider)
    output = output_path or default_embedding_index_path(
        index.corpus_version,
        embedding_model=index.embedding_model,
        embedding_dimension=index.embedding_dimension,
    )
    write_embedding_index(index, output)
    return index, output


def _format_embedding_input(text: str, *, purpose: str) -> str:
    if purpose == "query":
        return (
            "Retrieval query: find approved fan maintenance inspection guidance "
            "relevant to this request.\n"
            f"Query: {text}"
        )
    if purpose == "document":
        return (
            "Retrieval document: approved fan maintenance inspection guidance. "
            "Use for source-grounded retrieval only.\n"
            f"Document: {text}"
        )
    raise ValueError(f"unsupported embedding purpose: {purpose}")


def _document_embedding_text(chunk: KnowledgeChunk) -> str:
    return "\n".join(
        [
            f"Title: {chunk.title}",
            f"Publisher: {chunk.publisher}",
            f"Section: {chunk.section_heading}",
            f"Corpus: {chunk.corpus_version}",
            f"Text: {chunk.text}",
        ]
    )


def _response_to_vector(response: Any) -> list[float]:
    embeddings = getattr(response, "embeddings", None)
    if embeddings:
        embedding = embeddings[0]
    else:
        embedding = getattr(response, "embedding", None)
    if embedding is None:
        raise ValueError("embedding response did not contain embeddings")
    values = getattr(embedding, "values", embedding)
    vector = [float(value) for value in values]
    if not vector:
        raise ValueError("embedding response contained an empty vector")
    return vector


def _record_from_chunk(chunk: KnowledgeChunk, vector: Sequence[float]) -> EmbeddingRecord:
    return EmbeddingRecord(
        source_id=chunk.source_id,
        title=chunk.title,
        version=chunk.version,
        publisher=chunk.publisher,
        corpus_version=chunk.corpus_version,
        chunk_id=chunk.chunk_id,
        section_id=chunk.section_id,
        section_heading=chunk.section_heading,
        text_hash_sha256=_sha256_text(chunk.text),
        text=chunk.text,
        path=chunk.path,
        source_url=chunk.source_url,
        embedding=tuple(float(value) for value in vector),
    )


def _record_from_payload(payload: dict[str, Any]) -> EmbeddingRecord:
    return EmbeddingRecord(
        source_id=str(payload["source_id"]),
        title=str(payload["title"]),
        version=str(payload["version"]),
        publisher=str(payload.get("publisher") or ""),
        corpus_version=str(payload["corpus_version"]),
        chunk_id=str(payload["chunk_id"]),
        section_id=str(payload["section_id"]),
        section_heading=str(payload["section_heading"]),
        text_hash_sha256=str(payload["text_hash_sha256"]),
        text=str(payload["text"]),
        path=Path(str(payload["path"])),
        source_url=str(payload["source_url"]) if payload.get("source_url") else None,
        embedding=tuple(float(value) for value in payload["embedding"]),
    )


def _cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right):
        raise ValueError(f"embedding dimensions differ: {len(left)} != {len(right)}")
    numerator = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return numerator / (left_norm * right_norm)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _safe_token(value: str) -> str:
    safe = "".join(character if character.isalnum() else "_" for character in value)
    return "_".join(part for part in safe.split("_") if part).lower()
