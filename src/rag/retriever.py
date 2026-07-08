"""Deterministic local retriever over approved maintenance source chunks."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import math
from pathlib import Path
import re
from typing import Any, Iterable

from .knowledge_base import KnowledgeBase, KnowledgeChunk, build_knowledge_base


TOKEN_PATTERN = re.compile(r"[a-z0-9][a-z0-9_-]*", re.IGNORECASE)
SAFE_UNAVAILABLE_MESSAGE = (
    "No approved maintenance source was retrieved; maintenance recommendations "
    "must remain unavailable."
)


class RetrievalGroundingError(ValueError):
    """Raised when downstream output cites a source that was not retrieved."""


@dataclass(frozen=True)
class RetrievalResult:
    """One retrieved source chunk."""

    source_id: str
    title: str
    version: str
    chunk_id: str
    snippet: str
    score: float
    path: Path

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""
        return {
            "source_id": self.source_id,
            "title": self.title,
            "version": self.version,
            "chunk_id": self.chunk_id,
            "snippet": self.snippet,
            "score": self.score,
            "path": str(self.path),
        }


@dataclass(frozen=True)
class RetrievalResponse:
    """Source-preserving retrieval response."""

    query: str
    available: bool
    results: tuple[RetrievalResult, ...]
    message: str
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation."""
        return {
            "query": self.query,
            "available": self.available,
            "message": self.message,
            "warnings": list(self.warnings),
            "results": [result.to_dict() for result in self.results],
        }

    @property
    def source_ids(self) -> tuple[str, ...]:
        """Source IDs in retrieval order."""
        return tuple(result.source_id for result in self.results)


class LocalRetriever:
    """Lexical retriever that never invents missing source evidence."""

    def __init__(self, knowledge_base: KnowledgeBase | None = None) -> None:
        self.knowledge_base = knowledge_base or build_knowledge_base()

    def retrieve(
        self,
        query: str,
        *,
        top_k: int = 3,
        min_score: float = 0.0001,
        snippet_chars: int = 320,
    ) -> RetrievalResponse:
        """Retrieve approved source chunks for a maintenance query."""
        query = query.strip()
        if not query:
            return _unavailable_response(query, "empty retrieval query")
        if not self.knowledge_base.is_available:
            return _unavailable_response(query, SAFE_UNAVAILABLE_MESSAGE, self.knowledge_base.warnings)

        query_terms = _token_counts(query)
        if not query_terms:
            return _unavailable_response(query, "retrieval query contains no searchable terms")

        scored: list[tuple[float, KnowledgeChunk]] = []
        for chunk in self.knowledge_base.chunks:
            score = _cosine_score(query_terms, _token_counts(chunk.text))
            if score >= min_score:
                scored.append((score, chunk))
        scored.sort(key=lambda item: (-item[0], item[1].source_id, item[1].chunk_id))
        results = tuple(
            RetrievalResult(
                source_id=chunk.source_id,
                title=chunk.title,
                version=chunk.version,
                chunk_id=chunk.chunk_id,
                snippet=_make_snippet(chunk.text, query_terms.keys(), snippet_chars),
                score=round(score, 6),
                path=chunk.path,
            )
            for score, chunk in scored[:top_k]
        )
        if not results:
            return _unavailable_response(
                query,
                "No approved maintenance source matched the retrieval query.",
                self.knowledge_base.warnings,
            )
        return RetrievalResponse(
            query=query,
            available=True,
            results=results,
            message=f"Retrieved {len(results)} approved maintenance source chunk(s).",
            warnings=self.knowledge_base.warnings,
        )


def validate_citations(response: RetrievalResponse, cited_source_ids: Iterable[str]) -> None:
    """Ensure downstream recommendations cite only retrieved source IDs."""
    retrieved = set(response.source_ids)
    missing = sorted(set(cited_source_ids) - retrieved)
    if missing:
        raise RetrievalGroundingError(
            "Recommendation cited source IDs that were not retrieved: "
            + ", ".join(missing)
        )


def _unavailable_response(
    query: str,
    message: str,
    warnings: tuple[str, ...] | Iterable[str] = (),
) -> RetrievalResponse:
    return RetrievalResponse(
        query=query,
        available=False,
        results=(),
        message=message,
        warnings=tuple(warnings),
    )


def _token_counts(text: str) -> Counter[str]:
    return Counter(token.lower() for token in TOKEN_PATTERN.findall(text))


def _cosine_score(query_terms: Counter[str], chunk_terms: Counter[str]) -> float:
    overlap = set(query_terms) & set(chunk_terms)
    if not overlap:
        return 0.0
    numerator = sum(query_terms[token] * chunk_terms[token] for token in overlap)
    query_norm = math.sqrt(sum(value * value for value in query_terms.values()))
    chunk_norm = math.sqrt(sum(value * value for value in chunk_terms.values()))
    if query_norm == 0.0 or chunk_norm == 0.0:
        return 0.0
    return numerator / (query_norm * chunk_norm)


def _make_snippet(text: str, query_terms: Iterable[str], snippet_chars: int) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    if len(compact) <= snippet_chars:
        return compact
    lowered = compact.lower()
    first_hit = min(
        (lowered.find(term) for term in query_terms if lowered.find(term) >= 0),
        default=0,
    )
    start = max(0, first_hit - snippet_chars // 4)
    end = min(len(compact), start + snippet_chars)
    return compact[start:end].strip()
