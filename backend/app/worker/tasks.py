"""Celery tasks. Each task is a thin sync wrapper around an async
implementation, since the ingestion/orchestration stack (SQLAlchemy async
session, httpx.AsyncClient) is async end-to-end and Celery workers are
synchronous by default.
"""
import asyncio
from datetime import date

from sqlalchemy import select

from app.core.logging import configure_logging, get_logger
from app.db.session import session_scope
from app.models.enums import SourceType
from app.models.sentiment import SentimentSnapshot
from app.models.stock import Stock
from app.services.ingestion.orchestrator import IngestionOrchestrator
from app.services.sentiment.aggregator import aggregate
from app.worker.celery_app import celery_app

configure_logging()
logger = get_logger(__name__)


@celery_app.task(name="app.worker.tasks.ingest_ticker")
def ingest_ticker(ticker: str, source_types: list[str] | None = None, lookback_days: int = 7) -> int:
    return asyncio.run(_ingest_ticker(ticker, source_types, lookback_days))


async def _ingest_ticker(ticker: str, source_types: list[str] | None, lookback_days: int) -> int:
    async with session_scope() as db:
        result = await db.execute(select(Stock).where(Stock.ticker == ticker))
        stock = result.scalar_one_or_none()
        if stock is None:
            logger.error("Ingestion requested for unknown ticker %s", ticker)
            return 0

        types = [SourceType(t) for t in source_types] if source_types else None
        orchestrator = IngestionOrchestrator()
        count = await orchestrator.ingest(db, stock, source_types=types, lookback_days=lookback_days)
        await _refresh_snapshot(db, stock)
        return count


async def _refresh_snapshot(db, stock: Stock) -> None:
    """Recomputes today's `SentimentSnapshot` from the stock's documents
    scored in the last 24h. Kept simple (re-aggregate on every ingest)
    since document volume per stock per day is small."""
    from sqlalchemy import and_

    from app.models.document import Document

    today = date.today()
    result = await db.execute(
        select(Document.sentiment_score, Document.sentiment_label).where(
            and_(Document.stock_id == stock.id, Document.sentiment_score.is_not(None))
        )
    )
    rows = result.all()
    if not rows:
        return

    agg = aggregate([(score, label) for score, label in rows])

    existing = await db.execute(
        select(SentimentSnapshot).where(
            and_(SentimentSnapshot.stock_id == stock.id, SentimentSnapshot.snapshot_date == today)
        )
    )
    snapshot = existing.scalar_one_or_none()
    if snapshot is None:
        snapshot = SentimentSnapshot(stock_id=stock.id, snapshot_date=today)
        db.add(snapshot)

    snapshot.overall_score = agg.overall_score
    snapshot.overall_label = agg.overall_label
    snapshot.positive_count = agg.positive_count
    snapshot.neutral_count = agg.neutral_count
    snapshot.negative_count = agg.negative_count
    snapshot.document_count = len(rows)


@celery_app.task(name="app.worker.tasks.ingest_all_tracked_stocks")
def ingest_all_tracked_stocks() -> None:
    asyncio.run(_ingest_all_tracked_stocks())


async def _ingest_all_tracked_stocks() -> None:
    async with session_scope() as db:
        result = await db.execute(select(Stock.ticker))
        tickers = [row[0] for row in result.all()]

    for ticker in tickers:
        ingest_ticker.delay(ticker)
