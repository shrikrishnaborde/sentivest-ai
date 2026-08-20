from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from app.models.document import Document
from app.models.enums import SentimentLabel, SourceType
from app.models.stock import Stock
from app.services.ingestion import orchestrator as orchestrator_module
from app.services.ingestion.base import RawDocument, SourceAdapter
from app.services.ingestion.claude_news_search_source import ClaudeNewsSearchAdapter
from app.services.ingestion.orchestrator import IngestionOrchestrator
from app.services.sentiment.finbert import SentimentResult


def test_claude_search_is_the_default_news_adapter():
    assert orchestrator_module._resolve_news_adapter_cls() is ClaudeNewsSearchAdapter


class _MultiItemNewsAdapter(SourceAdapter):
    source_type = SourceType.NEWS

    async def fetch(self, ticker, company_name, lookback_days):
        return [
            RawDocument(
                title=f"{company_name} item {i}",
                content=f"Sentiment-relevant content {i}.",
                published_at=datetime.now(timezone.utc),
                source_type=SourceType.NEWS,
                source_name="Web (via Claude search)",
                url=None,
                metadata={"search_synthesized": True},
            )
            for i in range(3)
        ]


class _FakeVectorStore:
    async def upsert(self, ids, embeddings, texts, metadatas):
        pass

    async def query(self, embedding, top_k, filters=None):
        return []

    async def delete(self, ids):
        pass


class _FakeEmbeddingProvider:
    async def embed_documents(self, texts):
        return [[0.0, 0.0, 0.0] for _ in texts]

    async def embed_query(self, text):
        return [0.0, 0.0, 0.0]


class _FakeSentimentScorer:
    def score_batch(self, texts):
        return [SentimentResult(label=SentimentLabel.NEUTRAL, score=0.0, raw_scores={}) for _ in texts]


@pytest.mark.asyncio
async def test_ingest_persists_multiple_documents_from_search_adapter(db_session, monkeypatch):
    monkeypatch.setitem(orchestrator_module._ALL_ADAPTERS, SourceType.NEWS, _MultiItemNewsAdapter)

    stock = Stock(ticker="INFY", company_name="Infosys Ltd", exchange="NSE")
    db_session.add(stock)
    await db_session.commit()
    await db_session.refresh(stock)

    orchestrator = IngestionOrchestrator(
        vector_store=_FakeVectorStore(),
        embedding_provider=_FakeEmbeddingProvider(),
        sentiment_scorer=_FakeSentimentScorer(),
    )

    count = await orchestrator.ingest(db_session, stock, source_types=[SourceType.NEWS], lookback_days=14)

    assert count == 3
    result = await db_session.execute(select(Document).where(Document.stock_id == stock.id))
    documents = result.scalars().all()
    assert len(documents) == 3
    assert all(d.source_name == "Web (via Claude search)" for d in documents)
