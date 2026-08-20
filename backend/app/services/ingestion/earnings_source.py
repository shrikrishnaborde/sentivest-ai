"""Earnings call transcript and analyst report adapter.

These sources typically come from a licensed data vendor (e.g. AlphaSense,
Refinitiv, Tegus) rather than a free public API, so this adapter is a thin
interface over a pluggable transcript provider — wire in a real vendor
client in `_provider` once credentials are available. Left as an explicit
stub (returns []) rather than a fake implementation so ingestion runs
cleanly without a vendor contract in place.
"""
from app.core.logging import get_logger
from app.models.enums import SourceType
from app.services.ingestion.base import RawDocument, SourceAdapter

logger = get_logger(__name__)


class EarningsCallSourceAdapter(SourceAdapter):
    source_type = SourceType.EARNINGS_CALL

    async def fetch(self, ticker: str, company_name: str, lookback_days: int) -> list[RawDocument]:
        logger.info(
            "Earnings call transcript provider not configured; skipping for %s. "
            "Wire a vendor client (e.g. AlphaSense/Refinitiv) into EarningsCallSourceAdapter.",
            ticker,
        )
        return []


class AnalystReportSourceAdapter(SourceAdapter):
    source_type = SourceType.ANALYST_REPORT

    async def fetch(self, ticker: str, company_name: str, lookback_days: int) -> list[RawDocument]:
        logger.info(
            "Analyst report provider not configured; skipping for %s. "
            "Wire a vendor client into AnalystReportSourceAdapter.",
            ticker,
        )
        return []
