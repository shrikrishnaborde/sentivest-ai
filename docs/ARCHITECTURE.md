# Architecture

## Overview

SentiVest AI has two independent data flows that meet at one place — the
`ReportGenerator` service:

1. **Ingestion (write path)** — pulls raw documents from external sources,
   persists them to Postgres, scores their sentiment with FinBERT, chunks and
   embeds them, and upserts the chunks into the vector store.
2. **Query (read path)** — takes a user's natural-language question, retrieves
   relevant recent chunks for the stock, aggregates their sentiment, and asks
   an LLM to synthesize a grounded narrative from the same evidence.

Both paths depend on the same `Document` model, so a chunk retrieved during
query can always be resolved back to its full source metadata (title, URL,
publish date, source type) for citations.

## Ingestion pipeline

```
IngestionOrchestrator.ingest(stock)
  │
  ├─ fetch from each SourceAdapter (news, filings, earnings, analyst) ──▶ RawDocument[]
  ├─ dedupe against existing Document.url, persist new Document rows
  ├─ score each new document's sentiment with FinBERT ──▶ Document.sentiment_score/label
  ├─ chunk each document's content (rag/chunking.py)
  ├─ embed chunks (OpenAI text-embedding-3-large)
  └─ upsert {id, embedding, text, metadata} into the vector store
```

`SourceAdapter` is the only contract the orchestrator depends on
(`app/services/ingestion/base.py`), so adding a new source (e.g. Twitter,
StockTwits, a paid transcript vendor) means implementing one `fetch()` method
— the rest of the pipeline (persistence, scoring, indexing) is unchanged.

**News source: Claude web search by default.** `NEWS_SOURCE_PROVIDER`
(`app/core/config.py`) selects which adapter fills the `NEWS` slot in
`IngestionOrchestrator._ALL_ADAPTERS`:

- `claude_search` (default) — `ClaudeNewsSearchAdapter`
  (`app/services/ingestion/claude_news_search_source.py`) asks Claude
  (`claude-opus-5`, with the server-side `web_search` tool) to search the web
  and return a **structured list of distinct news items** (title, outlet,
  date, url, summary) via `output_config.format` (JSON-schema-constrained
  output). Each item becomes its own `RawDocument` — deliberately not one
  merged blob — because `confidence_from_agreement` scores confidence off
  how many independent sources agree; collapsing everything into a single
  document would silently cap every report's confidence. No `NEWS_API_KEY`
  required, only `ANTHROPIC_API_KEY`.
- `newsapi` — the traditional `NewsSourceAdapter`, backed by newsapi.org.

Either way, the result flows through the same chunk/embed/score pipeline as
any other source — the news provider never bypasses FinBERT scoring or
citation tracking.

Ingestion runs two ways:

- **On-demand**: `POST /api/v1/ingestion/{ticker}/trigger` enqueues a Celery
  task (`app.worker.tasks.ingest_ticker`).
- **Scheduled**: Celery Beat runs `ingest_all_tracked_stocks` nightly
  (01:00 UTC), which fans out `ingest_ticker` for every tracked stock and
  recomputes that day's `SentimentSnapshot` — the row the trend chart reads.

## Query / RAG pipeline

```
ReportGenerator.generate(stock, query)
  │
  ├─ Retriever.retrieve(query, ticker)
  │    ├─ embed the query
  │    ├─ vector_store.query(embedding, filters={ticker}) ──▶ over-fetch top_k*3
  │    ├─ filter by RAG_MIN_RELEVANCE_SCORE and lookback_days
  │    └─ resolve matches back to Document rows, sorted by relevance
  │
  ├─ FinBERT.score_batch(chunk texts) ──▶ per-chunk (score, label)
  ├─ aggregate(scores) ──▶ overall_score, overall_label
  ├─ confidence_from_agreement(scores) ──▶ confidence (agreement × sample size)
  │
  ├─ LLMClient.generate_structured(system_prompt, user_prompt)
  │    → strict system prompt: cite only from numbered excerpts, no outside
  │      knowledge, flag thin evidence explicitly
  │    → returns {summary, positive_drivers, negative_drivers, key_themes}
  │
  └─ persist SentimentReport (cached for repeat queries) + return citations
```

If retrieval finds no relevant, recent documents, `NoEvidenceFoundError` is
raised and surfaced as a 404 — the platform never lets the LLM answer from
its own pretrained knowledge about a company.

## Why these choices

- **FinBERT over a general sentiment model** — financial phrasing ("guided
  down", "beat estimates") is often misread by general-purpose sentiment
  models; FinBERT is fine-tuned specifically on financial text.
- **Aggregation is separate from generation** — the numeric sentiment score
  comes from FinBERT scoring the actual retrieved evidence, not from the
  LLM's self-reported opinion, so the score is reproducible and auditable
  independent of LLM sampling variance.
- **Config-driven vector store / LLM provider** — `VECTOR_STORE_PROVIDER` and
  `LLM_PROVIDER` select an implementation of a small interface
  (`VectorStore`, `LLMClient`) at runtime, so moving from local dev (Chroma)
  to managed production (Pinecone/Qdrant) is a config change.
- **Cross-dialect UUID type** (`app/db/types.py`) — production runs Postgres;
  the test suite runs in-memory SQLite for speed. A single `GUID` type
  decorator keeps model definitions identical across both.
