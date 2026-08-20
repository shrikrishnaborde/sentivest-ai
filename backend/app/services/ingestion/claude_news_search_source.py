"""News source backed by Claude's server-side `web_search` tool.

Replaces a traditional news-API integration: instead of polling NewsAPI,
this adapter asks Claude to search the web directly and return a structured
list of distinct, sentiment-relevant news items (each with its own title,
outlet, date, and summary). Returning multiple discrete items — rather than
one merged research blob — matters here: the platform's confidence scoring
(`sentiment.aggregator.confidence_from_agreement`) is a function of how many
independent sources agree, so collapsing everything into a single document
would silently cap every report's confidence.

Selected as the default NEWS source (`NEWS_SOURCE_PROVIDER=claude_search`);
set that to `newsapi` to use `NewsSourceAdapter` instead.
"""
import json
from datetime import datetime, timezone

from anthropic import AsyncAnthropic

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.enums import SourceType
from app.services.ingestion.base import RawDocument, SourceAdapter

logger = get_logger(__name__)

# Claude Opus 5 — see the claude-api skill: default to Opus 5 unless a task's
# cost/latency profile calls for a cheaper tier.
_MODEL = "claude-opus-5"
_MAX_TOKENS = 4096

_SYSTEM_PROMPT = """\
You are a financial news research assistant. Use web search to find \
distinct, sentiment-relevant news items about the given company from the \
last {lookback_days} days — earnings, guidance, price moves, analyst \
actions, regulatory or leadership changes, major announcements.

Return each item as a separate entry — do not merge multiple stories into \
one. Prefer primary sources (wire services, exchange filings, the \
company's own announcements) and named publications. If you find nothing \
relevant, return an empty list rather than inventing items.
"""

_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Headline or short title"},
                    "source_name": {"type": "string", "description": "Publication or outlet name"},
                    "url": {"type": "string", "description": "Source URL, if known"},
                    "published_date": {
                        "type": "string",
                        "description": "ISO 8601 date (YYYY-MM-DD) the item was published, if known",
                    },
                    "summary": {
                        "type": "string",
                        "description": "2-4 sentence factual summary of what happened and why it matters",
                    },
                },
                "required": ["title", "source_name", "summary"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["items"],
    "additionalProperties": False,
}

_TOOLS = [{"type": "web_search_20260209", "name": "web_search", "max_uses": 8}]


class ClaudeNewsSearchAdapter(SourceAdapter):
    """News source that asks Claude to research the company via web search."""

    source_type = SourceType.NEWS

    def __init__(self, api_key: str | None = None, client: AsyncAnthropic | None = None):
        if client is not None:
            self._client = client
        else:
            settings = get_settings()
            key = api_key or settings.ANTHROPIC_API_KEY
            self._client = AsyncAnthropic(api_key=key) if key else None

    async def fetch(self, ticker: str, company_name: str, lookback_days: int) -> list[RawDocument]:
        if self._client is None:
            logger.warning(
                "ANTHROPIC_API_KEY not configured; skipping Claude news search for %s", ticker
            )
            return []

        try:
            items = await self._search(company_name, ticker, lookback_days)
        except Exception:
            logger.exception("Claude news search failed for %s", ticker)
            return []

        documents = []
        for item in items:
            documents.append(
                RawDocument(
                    title=item.get("title") or "Untitled",
                    content=item.get("summary") or "",
                    published_at=self._parse_date(item.get("published_date")),
                    source_type=self.source_type,
                    source_name=item.get("source_name") or "Web (via Claude search)",
                    url=item.get("url") or None,
                    metadata={"generated_by": _MODEL, "search_synthesized": True},
                )
            )
        return documents

    async def _search(self, company_name: str, ticker: str, lookback_days: int) -> list[dict]:
        system = _SYSTEM_PROMPT.format(lookback_days=lookback_days)
        messages = [{"role": "user", "content": f"Company: {company_name} (ticker: {ticker})"}]
        request_kwargs = dict(
            model=_MODEL,
            max_tokens=_MAX_TOKENS,
            system=system,
            tools=_TOOLS,
            output_config={
                "effort": "medium",
                "format": {"type": "json_schema", "schema": _OUTPUT_SCHEMA},
            },
        )

        response = await self._client.messages.create(messages=messages, **request_kwargs)

        # The server-side web-search loop caps at 10 internal iterations; if it
        # pauses, resend the same turn (no extra "continue" message needed —
        # the API detects the trailing server-tool use and resumes) so Claude
        # finishes the search instead of returning a truncated result.
        while response.stop_reason == "pause_turn":
            messages.append({"role": "assistant", "content": response.content})
            response = await self._client.messages.create(messages=messages, **request_kwargs)

        if response.stop_reason == "refusal":
            logger.warning("Claude news search refused for %s", company_name)
            return []

        text = "".join(block.text for block in response.content if block.type == "text")
        if not text.strip():
            return []

        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            logger.warning("Claude news search returned non-JSON output for %s", company_name)
            return []

        return payload.get("items", [])

    @staticmethod
    def _parse_date(value: str | None) -> datetime:
        if value:
            try:
                return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)
            except ValueError:
                pass
        return datetime.now(timezone.utc)
