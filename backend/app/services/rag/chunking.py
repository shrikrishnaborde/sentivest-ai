"""Text splitting for ingestion — turns long documents into overlapping
chunks sized for the embedding model's context window while keeping
sentences intact where possible.
"""
import re

from app.core.config import get_settings

_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")


def split_into_chunks(text: str, chunk_size: int | None = None, overlap: int | None = None) -> list[str]:
    settings = get_settings()
    chunk_size = chunk_size or settings.RAG_CHUNK_SIZE
    overlap = overlap or settings.RAG_CHUNK_OVERLAP

    sentences = _SENTENCE_BOUNDARY.split(text.strip())
    chunks: list[str] = []
    current = ""

    for sentence in sentences:
        candidate = f"{current} {sentence}".strip()
        if len(candidate) <= chunk_size:
            current = candidate
            continue

        if current:
            chunks.append(current)
        # Start the next chunk with a trailing overlap of the previous chunk
        # so retrieval doesn't lose context at chunk boundaries.
        tail = current[-overlap:] if overlap and current else ""
        current = f"{tail} {sentence}".strip()

    if current:
        chunks.append(current)

    return [c for c in chunks if c]
