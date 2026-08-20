import json
from datetime import datetime, timezone

import pytest

from app.services.ingestion.claude_news_search_source import ClaudeNewsSearchAdapter


class _FakeTextBlock:
    def __init__(self, text: str):
        self.type = "text"
        self.text = text


class _FakeResponse:
    def __init__(self, stop_reason: str, content: list):
        self.stop_reason = stop_reason
        self.content = content


class _FakeMessages:
    def __init__(self, responses: list[_FakeResponse]):
        self._responses = list(responses)
        self.calls: list[dict] = []

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        return self._responses.pop(0)


class _FakeClient:
    def __init__(self, responses: list[_FakeResponse]):
        self.messages = _FakeMessages(responses)


@pytest.mark.asyncio
async def test_returns_one_document_per_item():
    payload = {
        "items": [
            {
                "title": "Infosys wins large BFSI deal",
                "source_name": "Economic Times",
                "url": "https://example.com/a",
                "published_date": "2026-08-15",
                "summary": "Infosys announced a multi-year BFSI deal.",
            },
            {
                "title": "Infosys margin pressure",
                "source_name": "Mint",
                "summary": "Wage hikes weighed on margins this quarter.",
            },
        ]
    }
    fake_client = _FakeClient([_FakeResponse("end_turn", [_FakeTextBlock(json.dumps(payload))])])
    adapter = ClaudeNewsSearchAdapter(client=fake_client)

    docs = await adapter.fetch("INFY", "Infosys Ltd", lookback_days=14)

    assert len(docs) == 2
    assert docs[0].title == "Infosys wins large BFSI deal"
    assert docs[0].source_name == "Economic Times"
    assert docs[0].published_at == datetime(2026, 8, 15, tzinfo=timezone.utc)
    assert docs[1].url is None
    assert docs[1].source_name == "Mint"


@pytest.mark.asyncio
async def test_resumes_on_pause_turn():
    responses = [
        _FakeResponse("pause_turn", [_FakeTextBlock("")]),
        _FakeResponse("end_turn", [_FakeTextBlock(json.dumps({"items": []}))]),
    ]
    fake_client = _FakeClient(responses)
    adapter = ClaudeNewsSearchAdapter(client=fake_client)

    docs = await adapter.fetch("INFY", "Infosys Ltd", lookback_days=14)

    assert docs == []
    assert len(fake_client.messages.calls) == 2


@pytest.mark.asyncio
async def test_refusal_returns_empty_list():
    fake_client = _FakeClient([_FakeResponse("refusal", [])])
    adapter = ClaudeNewsSearchAdapter(client=fake_client)

    docs = await adapter.fetch("INFY", "Infosys Ltd", lookback_days=14)

    assert docs == []


@pytest.mark.asyncio
async def test_malformed_json_returns_empty_list():
    fake_client = _FakeClient([_FakeResponse("end_turn", [_FakeTextBlock("not json")])])
    adapter = ClaudeNewsSearchAdapter(client=fake_client)

    docs = await adapter.fetch("INFY", "Infosys Ltd", lookback_days=14)

    assert docs == []


@pytest.mark.asyncio
async def test_no_api_key_returns_empty_list(monkeypatch):
    import app.services.ingestion.claude_news_search_source as mod

    monkeypatch.setattr(mod, "get_settings", lambda: type("Settings", (), {"ANTHROPIC_API_KEY": None})())
    adapter = ClaudeNewsSearchAdapter()

    docs = await adapter.fetch("INFY", "Infosys Ltd", lookback_days=14)

    assert docs == []
