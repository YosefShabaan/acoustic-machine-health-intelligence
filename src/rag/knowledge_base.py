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
    publisher: str = ""
    corpus_version: str = "unversioned"
    source_url: str | None = None

    def to_dict(self) -> dict[str, str]:
        """Return a JSON-serializable representation."""
        return {
            "source_id": self.source_id,
            "title": self.title,
            "version": self.version,
            "path": str(self.path),
            "publisher": self.publisher,
            "corpus_version": self.corpus_version,
            "source_url": self.source_url or "",
        }


@dataclass(frozen=True)
class KnowledgeChunk:
    """One retrievable source-preserving text chunk."""

    source_id: str
    title: str
    version: str
    publisher: str
    corpus_version: str
    path: Path
    chunk_id: str
    section_id: str
    section_heading: str
    text: str
    source_url: str | None = None

    def to_dict(self) -> dict[str, str]:
        """Return a JSON-serializable representation."""
        return {
            "source_id": self.source_id,
            "title": self.title,
            "version": self.version,
            "publisher": self.publisher,
            "corpus_version": self.corpus_version,
            "path": str(self.path),
            "chunk_id": self.chunk_id,
            "section_id": self.section_id,
            "section_heading": self.section_heading,
            "text": self.text,
            "source_url": self.source_url or "",
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
    manifest_corpus_version = str(payload.get("corpus_version") or "unversioned")
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
                publisher=str(row.get("publisher") or ""),
                corpus_version=str(row.get("corpus_version") or manifest_corpus_version),
                source_url=(
                    str(row["source_url"])
                    if isinstance(row.get("source_url"), str) and row["source_url"].strip()
                    else None
                ),
            )
        )

    return approved, warnings, manifest_path


def build_knowledge_base(
    manuals_dir: Path | str = RAG_MANUALS_DIR,
    *,
    manifest_name: str = MANIFEST_NAME,
    max_chunk_chars: int = 1800,
) -> KnowledgeBase:
    """Build a local knowledge base from approved maintenance documents."""
    sources, warnings, manifest_path = load_approved_sources(
        manuals_dir,
        manifest_name=manifest_name,
    )
    chunks: list[KnowledgeChunk] = []
    for source in sources:
        text = source.path.read_text(encoding="utf-8")
        for section in _section_chunks(text, max_chunk_chars):
            chunks.append(
                KnowledgeChunk(
                    source_id=source.source_id,
                    title=source.title,
                    version=source.version,
                    publisher=source.publisher,
                    corpus_version=source.corpus_version,
                    path=source.path,
                    chunk_id=f"{source.source_id}#{section['section_id']}",
                    section_id=section["section_id"],
                    section_heading=section["section_heading"],
                    text=section["text"],
                    source_url=source.source_url,
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


def _section_chunks(text: str, max_chunk_chars: int) -> Iterable[dict[str, str]]:
    """Yield section-aware chunks from markdown-like approved source text."""
    sections = _markdown_sections(text)
    if not sections:
        compact = _normalize_whitespace(text)
        if compact:
            yield {
                "section_id": "document",
                "section_heading": "Document",
                "text": compact[:max_chunk_chars],
            }
        return

    seen: dict[str, int] = {}
    for heading, body in sections:
        base_section_id = _section_id_from_heading(heading)
        seen[base_section_id] = seen.get(base_section_id, 0) + 1
        section_id = (
            base_section_id
            if seen[base_section_id] == 1
            else f"{base_section_id}-{seen[base_section_id]}"
        )
        chunk_text = _normalize_whitespace(f"{heading}\n\n{body}")
        if not chunk_text:
            continue
        if len(chunk_text) <= max_chunk_chars:
            yield {
                "section_id": section_id,
                "section_heading": heading,
                "text": chunk_text,
            }
            continue
        for part_index, part_text in enumerate(
            _split_section_text(heading, body, max_chunk_chars),
            start=1,
        ):
            yield {
                "section_id": f"{section_id}-part-{part_index}",
                "section_heading": heading,
                "text": part_text,
            }


def _markdown_sections(text: str) -> list[tuple[str, str]]:
    """Return second-level markdown sections with their body text."""
    sections: list[tuple[str, list[str]]] = []
    current_heading: str | None = None
    current_lines: list[str] = []
    for line in text.splitlines():
        if line.startswith("## "):
            if current_heading is not None:
                sections.append((current_heading, current_lines))
            current_heading = line[3:].strip()
            current_lines = []
        elif current_heading is not None:
            current_lines.append(line)
    if current_heading is not None:
        sections.append((current_heading, current_lines))
    return [
        (heading, "\n".join(lines).strip())
        for heading, lines in sections
        if _normalize_whitespace("\n".join(lines))
    ]


def _section_id_from_heading(heading: str) -> str:
    """Derive a stable section identifier from an approved-source heading."""
    first_token = heading.split(maxsplit=1)[0].strip()
    if re.fullmatch(r"[A-Z0-9][A-Z0-9-]{3,}", first_token):
        return first_token
    slug = re.sub(r"[^a-z0-9]+", "-", heading.lower()).strip("-")
    return slug or "section"


def _split_section_text(
    heading: str,
    body: str,
    max_chunk_chars: int,
) -> Iterable[str]:
    """Split an oversized section by paragraph while preserving the heading."""
    paragraphs = [
        _normalize_whitespace(paragraph)
        for paragraph in re.split(r"\n\s*\n", body)
        if _normalize_whitespace(paragraph)
    ]
    prefix = f"{heading} "
    current = prefix
    for paragraph in paragraphs:
        candidate = f"{current} {paragraph}".strip()
        if len(candidate) <= max_chunk_chars:
            current = candidate
            continue
        if current.strip() != prefix.strip():
            yield current[:max_chunk_chars]
        current = f"{prefix}{paragraph}"
    if current.strip() != prefix.strip():
        yield current[:max_chunk_chars]


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True
