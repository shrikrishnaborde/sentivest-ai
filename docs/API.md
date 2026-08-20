# API Reference

Base URL: `/api/v1` (interactive docs at `/docs` when the backend is running).

## Health

`GET /health` → `{"status": "ok"}`

## Stocks

| Method | Path             | Description                          |
| ------ | ---------------- | ------------------------------------- |
| GET    | `/stocks`         | List tracked stocks                   |
| POST   | `/stocks`         | Add a stock to track                  |
| GET    | `/stocks/{ticker}` | Get one tracked stock (404 if unknown) |

`POST /stocks` body:

```json
{
  "ticker": "INFY",
  "company_name": "Infosys Ltd",
  "exchange": "NSE",
  "sector": "IT Services"
}
```

## Sentiment

### `POST /sentiment/{ticker}/analyze`

Runs the full RAG pipeline and returns an evidence-backed sentiment report.

Request:

```json
{
  "query": "What is the current sentiment around Infosys?",
  "lookback_days": 30,
  "top_k": 8
}
```

Response (`SentimentReportResponse`):

```json
{
  "id": "…",
  "ticker": "INFY",
  "query": "What is the current sentiment around Infosys?",
  "overall_score": 0.42,
  "overall_label": "positive",
  "confidence": 0.78,
  "summary": "Infosys sentiment is broadly positive this month, driven primarily by...[1][3]",
  "positive_drivers": ["Strong Q2 earnings beat", "Large deal wins in BFSI"],
  "negative_drivers": ["Margin pressure from wage hikes"],
  "key_themes": ["AI services demand", "Client budget caution in Europe"],
  "citations": [
    {
      "document_id": "…",
      "title": "Infosys beats Street estimates in Q2",
      "url": "https://…",
      "source_type": "news",
      "source_name": "Economic Times",
      "published_at": "2026-08-01T09:00:00Z",
      "relevance_score": 0.91,
      "snippet": "Infosys reported…"
    }
  ],
  "llm_model": "gpt-5.5",
  "generated_at": "2026-08-14T10:00:00Z"
}
```

Returns `404` if no relevant, recent documents exist for the stock — trigger
ingestion first.

### `GET /sentiment/{ticker}/trend?days=30`

Returns daily `SentimentSnapshot` points for the trend chart.

## Chat

### `POST /chat`

Natural-language Q&A. Resolves the mentioned company to a tracked ticker
(explicit `ticker` field takes priority), then runs the same pipeline as
`/sentiment/{ticker}/analyze`.

```json
{ "message": "Why did Tata Motors fall this week?" }
```

Returns `422` if no tracked stock can be identified in the message.

## Ingestion

### `POST /ingestion/{ticker}/trigger`

Requires header `X-API-Key: <APP_SECRET_KEY>`. Enqueues an async ingestion
job across the requested source types.

```json
{
  "source_types": ["news", "regulatory_filing"],
  "lookback_days": 7
}
```

Response: `{"task_id": "…", "ticker": "INFY", "status": "queued"}`
