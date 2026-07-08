"""Build a Gemini semantic embedding index for approved RAG manuals."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import config as cfg  # noqa: E402
from rag import (  # noqa: E402
    GeminiEmbeddingProvider,
    build_default_semantic_index,
    default_embedding_index_path,
)


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manuals-dir", type=Path, default=cfg.RAG_MANUALS_DIR)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    """Build and write the default semantic embedding index."""
    args = parse_args()
    provider = GeminiEmbeddingProvider()
    output = args.output or default_embedding_index_path(
        "AMHI-FAN-MAINT-KB-v1",
        embedding_model=provider.metadata()["embedding_model"],
        embedding_dimension=provider.metadata()["embedding_dimension"],
    )
    index, output_path = build_default_semantic_index(
        manuals_dir=args.manuals_dir,
        embedding_provider=provider,
        output_path=output,
    )
    print("RAG_SEMANTIC_INDEX_BUILD=OK")
    print(f"CORPUS_VERSION={index.corpus_version}")
    print(f"EMBEDDING_PROVIDER={index.embedding_provider}")
    print(f"EMBEDDING_MODEL={index.embedding_model}")
    print(f"EMBEDDING_DIMENSION={index.embedding_dimension}")
    print(f"SOURCE_COUNT={index.to_dict()['source_count']}")
    print(f"CHUNK_COUNT={len(index.records)}")
    print(f"BUILD_SECONDS={index.metadata['build_seconds']}")
    print(f"OUTPUT={output_path}")


if __name__ == "__main__":
    main()
