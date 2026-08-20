"""Embedding provider abstraction.

Wraps OpenAI's `text-embedding-3-large` behind a small interface so the
vector store and retriever never talk to the OpenAI SDK directly — swapping
embedding providers later only means adding a class here.
"""
from abc import ABC, abstractmethod

from openai import AsyncOpenAI

from app.core.config import get_settings


class EmbeddingProvider(ABC):
    @abstractmethod
    async def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    @abstractmethod
    async def embed_query(self, text: str) -> list[float]: ...


class OpenAIEmbeddingProvider(EmbeddingProvider):
    def __init__(self, model: str | None = None, api_key: str | None = None):
        settings = get_settings()
        self._model = model or settings.OPENAI_EMBEDDING_MODEL
        self._client = AsyncOpenAI(api_key=api_key or settings.OPENAI_API_KEY)

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        response = await self._client.embeddings.create(model=self._model, input=texts)
        return [item.embedding for item in response.data]

    async def embed_query(self, text: str) -> list[float]:
        embeddings = await self.embed_documents([text])
        return embeddings[0]


_provider: EmbeddingProvider | None = None


def get_embedding_provider() -> EmbeddingProvider:
    global _provider
    if _provider is None:
        _provider = OpenAIEmbeddingProvider()
    return _provider
