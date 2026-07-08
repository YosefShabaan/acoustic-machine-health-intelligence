"""Source-preserving local retrieval for approved maintenance documents."""

from .knowledge_base import (
    ApprovedSource,
    KnowledgeBase,
    KnowledgeChunk,
    build_knowledge_base,
    load_approved_sources,
)
from .retriever import (
    LocalRetriever,
    RetrievalGroundingError,
    RetrievalResponse,
    RetrievalResult,
    validate_citations,
)

__all__ = [
    "ApprovedSource",
    "KnowledgeBase",
    "KnowledgeChunk",
    "LocalRetriever",
    "RetrievalGroundingError",
    "RetrievalResponse",
    "RetrievalResult",
    "build_knowledge_base",
    "load_approved_sources",
    "validate_citations",
]
