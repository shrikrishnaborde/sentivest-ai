"""Dev helper: run ingestion for one ticker directly, bypassing Celery/Redis.

Production ingestion goes through the Celery task (app.worker.tasks.ingest_ticker),
triggered via POST /api/v1/ingestion/{ticker}/trigger. This script calls the same
orchestrator in-process, for local/offline development where a broker isn't running.

Usage:
    DATABASE_URL=sqlite+aiosqlite:///./dev.db PYTHONPATH=. python scripts/run_ingestion.py INFY
"""
import asyncio
import sys

from sqlalchemy import select

from app.db.session import session_scope
from app.models.stock import Stock
from app.services.ingestion.orchestrator import IngestionOrchestrator
from app.worker.tasks import _refresh_snapshot


async def main(ticker: str, lookback_days: int = 14) -> None:
    async with session_scope() as db:
        result = await db.execute(select(Stock).where(Stock.ticker == ticker))
        stock = result.scalar_one_or_none()
        if stock is None:
            print(f"Unknown ticker: {ticker}")
            return

        orchestrator = IngestionOrchestrator()
        count = await orchestrator.ingest(db, stock, lookback_days=lookback_days)
        await _refresh_snapshot(db, stock)
        print(f"Ingested {count} new documents for {ticker}")


if __name__ == "__main__":
    ticker = sys.argv[1] if len(sys.argv) > 1 else "INFY"
    asyncio.run(main(ticker))
