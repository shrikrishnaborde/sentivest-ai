# SentiVest AI

**RAG-Powered Stock Sentiment Intelligence Platform**

> "Turn financial noise into investment insights."

SentiVest AI combines Retrieval-Augmented Generation (RAG) with finance-specific
sentiment analysis to help investors understand the market narrative behind a
stock. Instead of relying on a single article or an LLM's internal knowledge,
it retrieves relevant evidence from multiple trusted sources — news, earnings
call transcripts, annual reports, analyst reports, and company announcements —
and generates a transparent, source-cited sentiment report.

Ask it things like:

- "What is the current sentiment around Infosys?"
- "Why did Tata Motors fall this week?"
- "Summarize the market sentiment for HDFC Bank over the last month."

Every answer ships with an overall sentiment score, confidence level, positive
and negative drivers, key themes, and the exact source excerpts it was
generated from.

## Key Features

- 🔍 RAG-powered semantic retrieval over financial documents
- 📰 Multi-source sentiment analysis (news, earnings calls, filings, analyst reports)
- 📈 Stock-wise sentiment dashboard
- 📊 Historical sentiment trend visualization
- 💬 Natural-language Q&A for stocks
- 📑 Evidence-backed responses with inline source citations
- 🎯 Finance-specific sentiment scoring using FinBERT
- 🤖 AI-generated, strictly evidence-grounded executive summaries

## Tech Stack

| Layer            | Technology                                                        |
| ----------------- | ------------------------------------------------------------------ |
| Frontend          | Next.js 14 (App Router) + TypeScript + Tailwind CSS + Recharts     |
| Backend API       | FastAPI (async, Python 3.11)                                       |
| LLM               | GPT-5.5 (OpenAI) — pluggable, Anthropic Claude also supported       |
| RAG Orchestration | Custom retriever + prompt pipeline (LangChain-compatible interfaces) |
| Vector Database   | Chroma (default/local) — Pinecone / Qdrant pluggable for production |
| Embeddings        | OpenAI `text-embedding-3-large`                                    |
| Sentiment Model   | FinBERT (`ProsusAI/finbert`)                                       |
| Relational DB     | PostgreSQL 16 (async via SQLAlchemy 2.0 + asyncpg)                  |
| Task Queue        | Celery + Redis (scheduled ingestion, nightly sentiment rollups)     |
| Data Sources      | Claude web search (default news source) or NewsAPI, SEC EDGAR full-text search, pluggable earnings/analyst feeds |

## Architecture

```
┌────────────┐      ┌──────────────────┐      ┌─────────────────────┐
│  Frontend   │─────▶│   FastAPI (v1)   │─────▶│   Report Generator   │
│  Next.js    │      │  /stocks /chat   │      │  (RAG orchestrator)  │
└────────────┘      │  /sentiment      │      └──────┬───────┬───────┘
                      └──────────────────┘             │       │
                                                         ▼       ▼
                                              ┌────────────┐ ┌────────────┐
                                              │  Retriever  │ │  FinBERT    │
                                              │ (embeddings │ │  sentiment  │
                                              │ + vector DB)│ │  scorer     │
                                              └──────┬──────┘ └────────────┘
                                                      ▼
                                        ┌─────────────────────────┐
                                        │ Chroma / Pinecone/Qdrant │
                                        └─────────────────────────┘

┌───────────────┐      ┌────────────────────┐      ┌──────────────┐
│ Celery worker  │◀────▶│  Ingestion sources  │      │  PostgreSQL   │
│ (nightly cron) │      │  news / filings /   │─────▶│  documents,   │
│                │      │  earnings / analyst │      │  sentiment    │
└───────────────┘      └────────────────────┘      └──────────────┘
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full data flow and
design rationale, and [docs/API.md](docs/API.md) for the endpoint reference.

## Project Structure

```
sentivest-ai/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/   # HTTP routes (stocks, sentiment, chat, ingestion, health)
│   │   ├── core/               # settings, logging, security
│   │   ├── db/                 # SQLAlchemy engine/session, base, cross-dialect types
│   │   ├── models/              # ORM models (Stock, Document, SentimentSnapshot, SentimentReport)
│   │   ├── schemas/             # Pydantic request/response models
│   │   ├── repositories/        # DB access layer
│   │   ├── services/
│   │   │   ├── rag/             # embeddings, vector store, retriever, chunking
│   │   │   ├── sentiment/       # FinBERT scorer, aggregation
│   │   │   ├── llm/             # LLM client + prompts
│   │   │   ├── ingestion/       # source adapters + orchestrator
│   │   │   └── report_generator.py  # ties RAG + sentiment + LLM together
│   │   └── worker/              # Celery app + tasks (ingestion, nightly rollup)
│   ├── tests/
│   └── alembic/                 # DB migrations
├── frontend/
│   └── src/
│       ├── app/                 # dashboard, /stock/[ticker], /chat
│       ├── components/          # score card, trend chart, citations, chat UI
│       └── lib/                 # typed API client
└── docker-compose.yml            # postgres, redis, chroma, backend, worker, frontend
```

## Getting Started

### Option A — Docker Compose (recommended)

```bash
cp .env.example .env
# fill in OPENAI_API_KEY (and NEWS_API_KEY to enable live news ingestion)
docker compose up --build
```

- Frontend: http://localhost:3000
- API docs (Swagger): http://localhost:8000/docs

### Option B — Run locally

**Backend**

```bash
cd backend
python -m venv .venv && .venv/Scripts/activate   # or `source .venv/bin/activate` on macOS/Linux
pip install -r requirements-dev.txt
cp ../.env.example ../.env   # edit values
alembic upgrade head
uvicorn app.main:app --reload
```

**Frontend**

```bash
cd frontend
npm install
npm run dev
```

**Worker (for ingestion)**

```bash
cd backend
celery -A app.worker.celery_app worker --loglevel=info
celery -A app.worker.celery_app beat --loglevel=info   # nightly ingestion schedule
```

### Seed a stock and generate a report

```bash
# Track a stock
curl -X POST http://localhost:8000/api/v1/stocks \
  -H "Content-Type: application/json" \
  -d '{"ticker": "INFY", "company_name": "Infosys Ltd", "exchange": "NSE", "sector": "IT Services"}'

# Trigger ingestion (requires X-API-Key: your APP_SECRET_KEY)
curl -X POST http://localhost:8000/api/v1/ingestion/INFY/trigger \
  -H "Content-Type: application/json" -H "X-API-Key: $APP_SECRET_KEY" \
  -d '{"lookback_days": 14}'

# Ask a question
curl -X POST http://localhost:8000/api/v1/sentiment/INFY/analyze \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the current sentiment around Infosys?"}'
```

## Testing

```bash
cd backend
pytest -q
```

The backend test suite runs against an in-memory SQLite database, so it needs
no external services — only the lightweight Python dependencies
(`requirements-dev.txt`).

## Design Principles

- **Evidence over opinion** — the LLM is instructed to synthesize only from
  retrieved excerpts and to say so explicitly when evidence is thin, rather
  than fill gaps with pretrained knowledge.
- **Swappable infrastructure** — vector store (`VECTOR_STORE_PROVIDER`) and
  LLM provider (`LLM_PROVIDER`) are both config-driven; adding a backend
  means adding one class, not rewiring the app.
- **Sync-safe write path** — ingestion is the single place documents are
  written to Postgres *and* indexed into the vector store, so the two never
  drift out of sync.
