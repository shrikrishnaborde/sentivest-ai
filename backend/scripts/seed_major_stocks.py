"""Dev helper: track a batch of major stocks, ingest real news for each via
Claude web search (NEWS only — the SEC EDGAR filings adapter doesn't work
for non-US-listed tickers), and generate a sentiment report for each.

Runs everything in a single process so the Chroma PersistentClient stays
consistent (splitting this across separate script invocations causes the
same multi-process vector-store desync seen with the standalone ingestion
script).

Usage:
    DATABASE_URL=sqlite+aiosqlite:///./dev.db PYTHONPATH=. python scripts/seed_major_stocks.py
"""
import asyncio

from sqlalchemy import select

from app.db.session import session_scope
from app.models.enums import SourceType
from app.models.stock import Stock
from app.services.ingestion.orchestrator import IngestionOrchestrator
from app.services.report_generator import NoEvidenceFoundError, ReportGenerator
from app.worker.tasks import _refresh_snapshot

STOCKS = [
    ("TCS", "Tata Consultancy Services Ltd", "IT Services"),
    ("RELIANCE", "Reliance Industries Ltd", "Energy & Conglomerate"),
    ("HDFCBANK", "HDFC Bank Ltd", "Banking"),
    ("ICICIBANK", "ICICI Bank Ltd", "Banking"),
    ("HINDUNILVR", "Hindustan Unilever Ltd", "FMCG"),
    ("SBIN", "State Bank of India", "Banking"),
    ("BHARTIARTL", "Bharti Airtel Ltd", "Telecom"),
    ("ITC", "ITC Ltd", "FMCG & Conglomerate"),
    ("TATAMOTORS", "Tata Motors Ltd", "Automobile"),
    ("WIPRO", "Wipro Ltd", "IT Services"),
]

DEFAULT_QUERY = "What is the current market sentiment and why?"


async def get_or_create_stock(db, ticker: str, company_name: str, sector: str) -> Stock:
    result = await db.execute(select(Stock).where(Stock.ticker == ticker))
    stock = result.scalar_one_or_none()
    if stock is not None:
        return stock
    stock = Stock(ticker=ticker, company_name=company_name, exchange="NSE", sector=sector)
    db.add(stock)
    await db.flush()
    return stock


async def main() -> None:
    orchestrator = IngestionOrchestrator()
    report_generator = ReportGenerator()
    summary = []

    for ticker, company_name, sector in STOCKS:
        async with session_scope() as db:
            stock = await get_or_create_stock(db, ticker, company_name, sector)
            count = await orchestrator.ingest(
                db, stock, source_types=[SourceType.NEWS], lookback_days=14
            )
            await _refresh_snapshot(db, stock)
            print(f"{ticker}: ingested {count} documents")

        async with session_scope() as db:
            result = await db.execute(select(Stock).where(Stock.ticker == ticker))
            stock = result.scalar_one()
            try:
                report = await report_generator.generate(db, stock, DEFAULT_QUERY, lookback_days=14)
                summary.append(
                    (ticker, report.overall_label.value, report.overall_score, report.confidence, len(report.citations))
                )
            except NoEvidenceFoundError:
                summary.append((ticker, "NO_EVIDENCE", None, None, 0))

    print("\n=== Summary ===")
    for ticker, label, score, confidence, n_citations in summary:
        if score is None:
            print(f"{ticker:12} {label}")
        else:
            print(f"{ticker:12} {label:8} score={score:+.3f}  confidence={confidence:.0%}  sources={n_citations}")


if __name__ == "__main__":
    asyncio.run(main())
