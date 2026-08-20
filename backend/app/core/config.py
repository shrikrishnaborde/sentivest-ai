"""Centralized application settings, loaded from environment variables / .env.

Uses pydantic-settings so config is validated once at startup and injected
everywhere via `get_settings()` (cached) rather than re-read ad hoc.
"""
from functools import lru_cache
from typing import List, Literal

from pydantic import AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- App ---
    APP_NAME: str = "SentiVest AI"
    APP_ENV: Literal["development", "staging", "production"] = "development"
    APP_DEBUG: bool = True
    APP_SECRET_KEY: str = "change-me"
    API_V1_PREFIX: str = "/api/v1"
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # --- Database ---
    DATABASE_URL: str = "postgresql+asyncpg://sentivest:sentivest@localhost:5432/sentivest"

    # --- Vector store ---
    VECTOR_STORE_PROVIDER: Literal["chroma", "pinecone", "qdrant"] = "chroma"
    # If CHROMA_HOST is set, ChromaVectorStore connects to that server over
    # HTTP instead of using a local PersistentClient — required whenever
    # more than one process/container needs to see the same embeddings
    # (e.g. ingestion from a worker, queries from the API).
    CHROMA_HOST: str | None = None
    CHROMA_PORT: int = 8000
    CHROMA_PERSIST_DIR: str = "./chroma_data"
    CHROMA_COLLECTION_NAME: str = "sentivest_documents"
    PINECONE_API_KEY: str | None = None
    PINECONE_ENVIRONMENT: str | None = None
    PINECONE_INDEX_NAME: str = "sentivest-documents"
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str | None = None
    QDRANT_COLLECTION_NAME: str = "sentivest_documents"

    # --- LLM ---
    LLM_PROVIDER: Literal["openai", "azure_openai", "anthropic"] = "openai"
    OPENAI_API_KEY: str | None = None
    OPENAI_CHAT_MODEL: str = "gpt-5.5"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-large"
    ANTHROPIC_API_KEY: str | None = None

    # --- Sentiment ---
    FINBERT_MODEL_NAME: str = "ProsusAI/finbert"
    SENTIMENT_DEVICE: Literal["cpu", "cuda"] = "cpu"

    # --- Redis / Celery ---
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # --- Data source APIs ---
    # "claude_search" asks Claude to search the web directly (server-side
    # web_search tool) for news — no NewsAPI subscription required. Set to
    # "newsapi" to use the traditional NewsSourceAdapter instead.
    NEWS_SOURCE_PROVIDER: Literal["claude_search", "newsapi"] = "claude_search"
    NEWS_API_KEY: str | None = None
    ALPHA_VANTAGE_API_KEY: str | None = None
    SEC_EDGAR_USER_AGENT: str = "SentiVest AI contact@sentivest.ai"

    # --- RAG tuning ---
    RAG_TOP_K: int = 8
    RAG_CHUNK_SIZE: int = 800
    RAG_CHUNK_OVERLAP: int = 120
    RAG_MIN_RELEVANCE_SCORE: float = 0.3

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def _split_cors(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [origin.strip() for origin in v.split(",")]
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()
