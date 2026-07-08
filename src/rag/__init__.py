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
from .semantic_retriever import (
    GeminiEmbeddingProvider,
    SemanticEmbeddingIndex,
    SemanticRetriever,
    build_default_semantic_index,
    build_semantic_embedding_index,
    default_embedding_index_path,
    load_embedding_index,
    write_embedding_index,
)

__all__ = [
    "ApprovedSource",
    "GeminiEmbeddingProvider",
    "KnowledgeBase",
    "KnowledgeChunk",
    "LocalRetriever",
    "RetrievalGroundingError",
    "RetrievalResponse",
    "RetrievalResult",
    "SemanticEmbeddingIndex",
    "SemanticRetriever",
    "build_knowledge_base",
    "build_default_semantic_index",
    "build_semantic_embedding_index",
    "default_embedding_index_path",
    "load_approved_sources",
    "load_embedding_index",
    "validate_citations",
    "write_embedding_index",
]
