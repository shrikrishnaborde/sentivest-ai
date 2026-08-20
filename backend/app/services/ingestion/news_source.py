"""Financial news adapter, backed by NewsAPI.org.

Swap the HTTP call in `_fetch_raw` to any provider (Benzinga, Finnhub,
Alpha Vantage News Sentiment, etc.) without changing the adapter contract.
"""
from datetime import datetime, timedelta, timezone

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.enums import SourceType
from app.services.ingestion.base import RawDocument, SourceAdapter

logger = get_logger(__name__)

_NEWSAPI_URL = "https://newsapi.org/v2/everything"


class NewsSourceAdapter(SourceAdapter):
    source_type = SourceType.NEWS

    def __init__(self, api_key: str | None = None):
        settings = get_settings()
        self._api_key = api_key or settings.NEWS_API_KEY

    async def fetch(self, ticker: str, company_name: str, lookback_days: int) -> list[RawDocument]:
        if not self._api_key:
            logger.warning("NEWS_API_KEY not configured; skipping news ingestion for %s", ticker)
            return []

        from_date = (datetime.now(timezone.utc) - timedelta(days=lookback_days)).date().isoformat()
        params = {
            "q": f'"{company_name}" OR "{ticker}"',
            "from": from_date,
            "language": "en",
            "sortBy": "relevancy",
            "pageSize": 50,
            "apiKey": self._api_key,
        }

        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(_NEWSAPI_URL, params=params)
            response.raise_for_status()
            payload = response.json()

        documents = []
        for article in payload.get("articles", []):
            published_at = self._parse_datetime(article.get("publishedAt"))
            if published_at is None:
                continue
            body = " ".join(filter(None, [article.get("description"), article.get("content")]))
            if not body:
                continue
            documents.append(
                RawDocument(
                    title=article.get("title", "Untitled"),
                    content=body,
                    published_at=published_at,
                    source_type=self.source_type,
                    source_name=(article.get("source") or {}).get("name", "Unknown"),
                    url=article.get("url"),
                    metadata={"author": article.get("author")},
                )
            )
        return documents

    @staticmethod
    def _parse_datetime(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
