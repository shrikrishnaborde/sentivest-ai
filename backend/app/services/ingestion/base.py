"""Shared contract for all data-source adapters.

Every source (news, filings, earnings calls, analyst reports) implements
`SourceAdapter.fetch()` and returns a list of `RawDocument`. The ingestion
orchestrator treats all sources identically after this point, which is
what lets us add a new source (e.g. Twitter/StockTwits) without touching
the pipeline itself.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from app.models.enums import SourceType


@dataclass
class RawDocument:
    title: str
    content: str
    published_at: datetime
    source_type: SourceType
    source_name: str
    url: str | None = None
    metadata: dict | None = None


class SourceAdapter(ABC):
    source_type: SourceType

    @abstractmethod
    async def fetch(self, ticker: str, company_name: str, lookback_days: int) -> list[RawDocument]:
        """Fetch raw documents for a ticker published within `lookback_days`."""
        ...
