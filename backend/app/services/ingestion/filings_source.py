"""Regulatory filings / annual report adapter (e.g. SEC EDGAR full-text
search for US-listed ADRs, or an equivalent BSE/NSE announcements feed for
Indian tickers). Implemented against SEC EDGAR's public full-text search
API as the reference integration; point `_search_url` at a different
registry to support other markets.
"""
from datetime import datetime, timedelta, timezone

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.enums import SourceType
from app.services.ingestion.base import RawDocument, SourceAdapter

logger = get_logger(__name__)

_EDGAR_FULL_TEXT_SEARCH_URL = "https://efts.sec.gov/LATEST/search-index"


class FilingsSourceAdapter(SourceAdapter):
    source_type = SourceType.REGULATORY_FILING

    def __init__(self, user_agent: str | None = None):
        settings = get_settings()
        self._user_agent = user_agent or settings.SEC_EDGAR_USER_AGENT

    async def fetch(self, ticker: str, company_name: str, lookback_days: int) -> list[RawDocument]:
        from_date = (datetime.now(timezone.utc) - timedelta(days=lookback_days)).date().isoformat()
        params = {"q": company_name, "dateRange": "custom", "startdt": from_date, "forms": "8-K,10-Q,10-K"}
        headers = {"User-Agent": self._user_agent}

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get(_EDGAR_FULL_TEXT_SEARCH_URL, params=params, headers=headers)
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPError as exc:
            logger.warning("EDGAR filings fetch failed for %s: %s", ticker, exc)
            return []

        documents = []
        for hit in payload.get("hits", {}).get("hits", []):
            source = hit.get("_source", {})
            published_at = self._parse_date(source.get("file_date"))
            if published_at is None:
                continue
            documents.append(
                RawDocument(
                    title=source.get("display_names", [company_name])[0],
                    content=source.get("summary", "") or source.get("display_names", [""])[0],
                    published_at=published_at,
                    source_type=self.source_type,
                    source_name="SEC EDGAR",
                    url=f"https://www.sec.gov/Archives/edgar/data/{hit.get('_id', '')}",
                    metadata={"form_type": source.get("root_forms")},
                )
            )
        return documents

    @staticmethod
    def _parse_date(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)
        except ValueError:
            return None
