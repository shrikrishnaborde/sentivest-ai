"""Semantic retrieval: embed a query, search the vector store, filter by
relevance and recency, and resolve matches back to `Document` rows for
full metadata (source, URL, publish date) used in citations.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.document import Document
from app.services.rag.embeddings import EmbeddingProvider, get_embedding_provider
from app.services.rag.vector_store import VectorStore, get_vector_store


@dataclass
class RetrievedChunk:
    document: Document
    chunk_text: str
    relevance_score: float


class Retriever:
    def __init__(
        self,
        vector_store: VectorStore | None = None,
        embedding_provider: EmbeddingProvider | None = None,
    ):
        self._vector_store = vector_store or get_vector_store()
        self._embeddings = embedding_provider or get_embedding_provider()
        self._settings = get_settings()

    async def retrieve(
        self,
        db: AsyncSession,
        query: str,
        stock_id: str,
        ticker: str,
        top_k: int | None = None,
        lookback_days: int = 30,
        company_name: str | None = None,
    ) -> list[RetrievedChunk]:
        top_k = top_k or self._settings.RAG_TOP_K
        # The vector store query already scopes to this ticker via metadata
        # filtering, but the relevance-score cutoff below is pure semantic
        # similarity — a generic question ("What's the sentiment and why?")
        # doesn't mention the company at all, so it can under-score against
        # company-specific chunks even when they're exactly what should
        # match. Anchoring the embedded text to the company name fixes that
        # without touching the threshold itself.
        embed_text = f"{company_name} ({ticker}): {query}" if company_name else f"{ticker}: {query}"
        query_embedding = await self._embeddings.embed_query(embed_text)

        matches = await self._vector_store.query(
            embedding=query_embedding,
            top_k=top_k * 3,  # over-fetch; we filter by relevance + recency below
            filters={"ticker": ticker},
        )

        cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)
        min_score = self._settings.RAG_MIN_RELEVANCE_SCORE

        relevant = [m for m in matches if m.score >= min_score]
        if not relevant:
            return []

        document_ids = list({m.document_id for m in relevant})
        result = await db.execute(select(Document).where(Document.id.in_(document_ids)))
        documents_by_id = {str(doc.id): doc for doc in result.scalars().all()}

        chunks: list[RetrievedChunk] = []
        for match in relevant:
            document = documents_by_id.get(match.document_id)
            if document is None:
                continue
            # SQLite (used in local/offline dev) doesn't preserve tzinfo on
            # DateTime columns the way Postgres does, so a value written as
            # UTC comes back naive — treat a naive published_at as UTC.
            published_at = document.published_at
            if published_at.tzinfo is None:
                published_at = published_at.replace(tzinfo=timezone.utc)
            if published_at < cutoff:
                continue
            chunks.append(
                RetrievedChunk(document=document, chunk_text=match.text, relevance_score=match.score)
            )

        chunks.sort(key=lambda c: c.relevance_score, reverse=True)
        return chunks[:top_k]
