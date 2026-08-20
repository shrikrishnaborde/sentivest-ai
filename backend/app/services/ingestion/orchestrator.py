"""Ingestion orchestrator: fan out to every source adapter for a ticker,
persist new documents, score their sentiment, chunk + embed them, and
upsert the chunks into the vector store. This is the single write path
into both Postgres (`documents`) and the vector index, so the two never
drift out of sync.
"""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.document import Document
from app.models.enums import SourceType
from app.models.stock import Stock
from app.services.ingestion.base import RawDocument, SourceAdapter
from app.services.ingestion.claude_news_search_source import ClaudeNewsSearchAdapter
from app.services.ingestion.earnings_source import AnalystReportSourceAdapter, EarningsCallSourceAdapter
from app.services.ingestion.filings_source import FilingsSourceAdapter
from app.services.ingestion.news_source import NewsSourceAdapter
from app.services.rag.chunking import split_into_chunks
from app.services.rag.embeddings import EmbeddingProvider, get_embedding_provider
from app.services.rag.vector_store import VectorStore, get_vector_store
from app.services.sentiment.finbert import FinBertSentimentScorer, get_sentiment_scorer

logger = get_logger(__name__)


def _resolve_news_adapter_cls() -> type[SourceAdapter]:
    """NEWS_SOURCE_PROVIDER picks the NEWS adapter: Claude web search by
    default, or the traditional NewsAPI integration."""
    if get_settings().NEWS_SOURCE_PROVIDER == "newsapi":
        return NewsSourceAdapter
    return ClaudeNewsSearchAdapter


_ALL_ADAPTERS: dict[SourceType, type[SourceAdapter]] = {
    SourceType.NEWS: _resolve_news_adapter_cls(),
    SourceType.REGULATORY_FILING: FilingsSourceAdapter,
    SourceType.EARNINGS_CALL: EarningsCallSourceAdapter,
    SourceType.ANALYST_REPORT: AnalystReportSourceAdapter,
}


class IngestionOrchestrator:
    def __init__(
        self,
        vector_store: VectorStore | None = None,
        embedding_provider: EmbeddingProvider | None = None,
        sentiment_scorer: FinBertSentimentScorer | None = None,
    ):
        self._vector_store = vector_store or get_vector_store()
        self._embeddings = embedding_provider or get_embedding_provider()
        self._sentiment = sentiment_scorer or get_sentiment_scorer()

    async def ingest(
        self,
        db: AsyncSession,
        stock: Stock,
        source_types: list[SourceType] | None = None,
        lookback_days: int = 7,
    ) -> int:
        """Runs the full ingest-score-index pipeline for one stock. Returns
        the number of new documents persisted."""
        source_types = source_types or list(_ALL_ADAPTERS.keys())
        raw_documents = await self._fetch_all(stock, source_types, lookback_days)

        new_documents = await self._persist_new(db, stock, raw_documents)
        if not new_documents:
            logger.info("No new documents for %s", stock.ticker)
            return 0

        self._score_sentiment(new_documents)
        await db.commit()

        await self._index(stock, new_documents)
        for doc in new_documents:
            doc.is_indexed = True
        await db.commit()

        logger.info("Ingested %d new documents for %s", len(new_documents), stock.ticker)
        return len(new_documents)

    async def _fetch_all(
        self, stock: Stock, source_types: list[SourceType], lookback_days: int
    ) -> list[RawDocument]:
        results: list[RawDocument] = []
        for source_type in source_types:
            adapter_cls = _ALL_ADAPTERS.get(source_type)
            if adapter_cls is None:
                continue
            adapter = adapter_cls()
            try:
                docs = await adapter.fetch(stock.ticker, stock.company_name, lookback_days)
                results.extend(docs)
            except Exception:
                logger.exception("Source adapter %s failed for %s", source_type, stock.ticker)
        return results

    async def _persist_new(
        self, db: AsyncSession, stock: Stock, raw_documents: list[RawDocument]
    ) -> list[Document]:
        existing_urls = await self._existing_urls(db, stock.id)

        new_documents = []
        for raw in raw_documents:
            if raw.url and raw.url in existing_urls:
                continue
            document = Document(
                stock_id=stock.id,
                source_type=raw.source_type,
                source_name=raw.source_name,
                url=raw.url,
                title=raw.title,
                content=raw.content,
                published_at=raw.published_at,
                doc_metadata=raw.metadata or {},
            )
            db.add(document)
            new_documents.append(document)
            if raw.url:
                existing_urls.add(raw.url)

        if new_documents:
            await db.flush()  # assign IDs without committing yet
        return new_documents

    async def _existing_urls(self, db: AsyncSession, stock_id: uuid.UUID) -> set[str]:
        result = await db.execute(
            select(Document.url).where(Document.stock_id == stock_id, Document.url.is_not(None))
        )
        return {row[0] for row in result.all()}

    def _score_sentiment(self, documents: list[Document]) -> None:
        results = self._sentiment.score_batch([d.content for d in documents])
        for document, result in zip(documents, results):
            document.sentiment_label = result.label
            document.sentiment_score = result.score

    async def _index(self, stock: Stock, documents: list[Document]) -> None:
        ids, texts, metadatas = [], [], []
        for document in documents:
            for i, chunk in enumerate(split_into_chunks(document.content)):
                ids.append(f"{document.id}:{i}")
                texts.append(chunk)
                metadatas.append(
                    {
                        "document_id": str(document.id),
                        "ticker": stock.ticker,
                        "source_type": document.source_type.value,
                        "published_at": document.published_at.isoformat(),
                    }
                )

        if not texts:
            return

        embeddings = await self._embeddings.embed_documents(texts)
        await self._vector_store.upsert(ids=ids, embeddings=embeddings, texts=texts, metadatas=metadatas)
