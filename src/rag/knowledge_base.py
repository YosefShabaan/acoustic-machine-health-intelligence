"""Approved-document knowledge base for maintenance retrieval."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any, Iterable

from config import RAG_MANUALS_DIR


MANIFEST_NAME = "approved_sources.json"
SUPPORTED_EXTENSIONS = {".md", ".txt"}


@dataclass(frozen=True)
class ApprovedSource:
    """One explicitly approved local document entry."""

    source_id: str
    title: str
    version: str
    path: Path

    def to_dict(self) -> dict[str, str]:
        """Return a JSON-serializable representation."""
        return {
            "source_id": self.source_id,
            "title": self.title,
            "version": self.version,
            "path": str(self.path),
        }


@dataclass(frozen=True)
class KnowledgeChunk:
    """One retrievable source-preserving text chunk."""

    source_id: str
    title: str
    version: str
    path: Path
    chunk_id: str
    text: str

    def to_dict(self) -> dict[str, str]:
        """Return a JSON-serializable representation."""
        return {
            "source_id": self.source_id,
            "title": self.title,
            "version": self.version,
            "path": str(self.path),
            "chunk_id": self.chunk_id,
            "text": self.text,
        }


@dataclass(frozen=True)
class KnowledgeBase:
    """Immutable set of approved maintenance source chunks."""

    chunks: tuple[KnowledgeChunk, ...]
    source_count: int
    manifest_path: Path | None
    warnings: tuple[str, ...] = ()

    @property
    def is_available(self) -> bool:
        """Whether at least one approved source chunk is indexed."""
        return bool(self.chunks)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable summary."""
        return {
            "available": self.is_available,
            "source_count": self.source_count,
            "chunk_count": len(self.chunks),
            "manifest_path": str(self.manifest_path) if self.manifest_path else None,
            "warnings": list(self.warnings),
            "chunks": [chunk.to_dict() for chunk in self.chunks],
        }


def load_approved_sources(
    manuals_dir: Path | str = RAG_MANUALS_DIR,
    *,
    manifest_name: str = MANIFEST_NAME,
) -> tuple[list[ApprovedSource], list[str], Path | None]:
    """Load explicitly approved source entries from a local manifest.

    Documents are indexed only when they appear in ``approved_sources.json`` with
    ``approved: true``. Files merely present in the directory are ignored.
    """
    root = Path(manuals_dir)
    manifest_path = root / manifest_name
    if not root.exists():
        return [], [f"manuals directory not found: {root}"], manifest_path
    if not manifest_path.exists():
        return [], [f"approved source manifest not found: {manifest_path}"], manifest_path

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows = payload.get("sources", [])
    if not isinstance(rows, list):
        raise ValueError("approved_sources.json must contain a 'sources' list")

    approved: list[ApprovedSource] = []
    warnings: list[str] = []
    seen_ids: set[str] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            warnings.append(f"source row {index} is not an object")
            continue
        if row.get("approved") is not True:
            warnings.append(f"source row {index} is not explicitly approved")
            continue

        source_id = _required_text(row, "source_id", index)
        if source_id in seen_ids:
            raise ValueError(f"duplicate source_id in approved manifest: {source_id}")
        seen_ids.add(source_id)

        relative_path = Path(_required_text(row, "path", index))
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise ValueError(f"source path must stay inside manuals directory: {relative_path}")
        source_path = (root / relative_path).resolve()
        if not _is_within(source_path, root.resolve()):
            raise ValueError(f"source path escaped manuals directory: {source_path}")
        if source_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            warnings.append(f"unsupported source extension for {source_id}: {source_path.suffix}")
            continue
        if not source_path.exists():
            warnings.append(f"approved source missing on disk: {source_path}")
            continue

        approved.append(
            ApprovedSource(
                source_id=source_id,
                title=str(row.get("title") or source_id),
                version=str(row.get("version") or "unversioned"),
                path=source_path,
            )
        )

    return approved, warnings, manifest_path


def build_knowledge_base(
    manuals_dir: Path | str = RAG_MANUALS_DIR,
    *,
    manifest_name: str = MANIFEST_NAME,
    max_chunk_chars: int = 1200,
) -> KnowledgeBase:
    """Build a local knowledge base from approved maintenance documents."""
    sources, warnings, manifest_path = load_approved_sources(
        manuals_dir,
        manifest_name=manifest_name,
    )
    chunks: list[KnowledgeChunk] = []
    for source in sources:
        text = source.path.read_text(encoding="utf-8")
        for chunk_index, chunk_text in enumerate(_chunk_text(text, max_chunk_chars)):
            chunks.append(
                KnowledgeChunk(
                    source_id=source.source_id,
                    title=source.title,
                    version=source.version,
                    path=source.path,
                    chunk_id=f"{source.source_id}#chunk-{chunk_index + 1}",
                    text=chunk_text,
                )
            )
    return KnowledgeBase(
        chunks=tuple(chunks),
        source_count=len(sources),
        manifest_path=manifest_path,
        warnings=tuple(warnings),
    )


def _required_text(row: dict[str, Any], key: str, index: int) -> str:
    value = row.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"source row {index} missing required text key: {key}")
    return value.strip()


def _chunk_text(text: str, max_chunk_chars: int) -> Iterable[str]:
    compact = _normalize_whitespace(text)
    if not compact:
        return
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    current = ""
    for paragraph in paragraphs or [compact]:
        paragraph = _normalize_whitespace(paragraph)
        if not current:
            current = paragraph
            continue
        if len(current) + 1 + len(paragraph) <= max_chunk_chars:
            current = f"{current} {paragraph}"
        else:
            yield current[:max_chunk_chars]
            current = paragraph
    if current:
        yield current[:max_chunk_chars]


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True
