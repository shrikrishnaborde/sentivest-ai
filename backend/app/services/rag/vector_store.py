"""Vector store abstraction.

`VectorStore` is the only interface the rest of the app depends on. Three
backends are provided (Chroma for local/dev, Pinecone and Qdrant for
managed/production deployments); which one is active is chosen at runtime
by `VECTOR_STORE_PROVIDER` in settings, so switching backends is a config
change, not a code change.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from app.core.config import get_settings


@dataclass
class VectorMatch:
    chunk_id: str
    document_id: str
    text: str
    score: float
    metadata: dict[str, Any]


class VectorStore(ABC):
    @abstractmethod
    async def upsert(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        texts: list[str],
        metadatas: list[dict[str, Any]],
    ) -> None: ...

    @abstractmethod
    async def query(
        self,
        embedding: list[float],
        top_k: int,
        filters: dict[str, Any] | None = None,
    ) -> list[VectorMatch]: ...

    @abstractmethod
    async def delete(self, ids: list[str]) -> None: ...


class ChromaVectorStore(VectorStore):
    """Vector store backed by ChromaDB.

    Connects to a standalone Chroma server over HTTP when `CHROMA_HOST` is
    set — required whenever more than one process/container needs to see
    the same embeddings (e.g. a Celery worker ingesting documents that the
    API process then has to retrieve). Falls back to an on-disk
    PersistentClient for single-process local/offline dev.
    """

    def __init__(self):
        import chromadb

        settings = get_settings()
        if settings.CHROMA_HOST:
            self._client = chromadb.HttpClient(host=settings.CHROMA_HOST, port=settings.CHROMA_PORT)
        else:
            self._client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
        self._collection = self._client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    async def upsert(self, ids, embeddings, texts, metadatas) -> None:
        self._collection.upsert(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)

    async def query(self, embedding, top_k, filters=None) -> list[VectorMatch]:
        result = self._collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
            where=filters or None,
        )
        matches: list[VectorMatch] = []
        ids = result.get("ids", [[]])[0]
        docs = result.get("documents", [[]])[0]
        metas = result.get("metadatas", [[]])[0]
        dists = result.get("distances", [[]])[0]
        for chunk_id, text, meta, distance in zip(ids, docs, metas, dists):
            similarity = 1.0 - distance  # cosine distance -> similarity
            matches.append(
                VectorMatch(
                    chunk_id=chunk_id,
                    document_id=str(meta.get("document_id")),
                    text=text,
                    score=similarity,
                    metadata=meta,
                )
            )
        return matches

    async def delete(self, ids: list[str]) -> None:
        self._collection.delete(ids=ids)


class PineconeVectorStore(VectorStore):
    """Managed, horizontally-scalable vector store for production deployments."""

    def __init__(self):
        from pinecone import Pinecone

        settings = get_settings()
        self._client = Pinecone(api_key=settings.PINECONE_API_KEY)
        self._index = self._client.Index(settings.PINECONE_INDEX_NAME)

    async def upsert(self, ids, embeddings, texts, metadatas) -> None:
        vectors = [
            {"id": i, "values": e, "metadata": {**m, "text": t}}
            for i, e, t, m in zip(ids, embeddings, texts, metadatas)
        ]
        self._index.upsert(vectors=vectors)

    async def query(self, embedding, top_k, filters=None) -> list[VectorMatch]:
        result = self._index.query(
            vector=embedding, top_k=top_k, filter=filters or None, include_metadata=True
        )
        matches = []
        for match in result.get("matches", []):
            meta = match.get("metadata", {})
            matches.append(
                VectorMatch(
                    chunk_id=match["id"],
                    document_id=str(meta.get("document_id")),
                    text=meta.get("text", ""),
                    score=match["score"],
                    metadata=meta,
                )
            )
        return matches

    async def delete(self, ids: list[str]) -> None:
        self._index.delete(ids=ids)


class QdrantVectorStore(VectorStore):
    """Self-hostable managed-style vector store; a middle ground between
    Chroma (embedded) and Pinecone (fully managed SaaS)."""

    def __init__(self):
        from qdrant_client import QdrantClient

        settings = get_settings()
        self._collection_name = settings.QDRANT_COLLECTION_NAME
        self._client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)

    async def upsert(self, ids, embeddings, texts, metadatas) -> None:
        from qdrant_client.models import PointStruct

        points = [
            PointStruct(id=i, vector=e, payload={**m, "text": t})
            for i, e, t, m in zip(ids, embeddings, texts, metadatas)
        ]
        self._client.upsert(collection_name=self._collection_name, points=points)

    async def query(self, embedding, top_k, filters=None) -> list[VectorMatch]:
        results = self._client.search(
            collection_name=self._collection_name,
            query_vector=embedding,
            limit=top_k,
            query_filter=filters or None,
        )
        matches = []
        for point in results:
            payload = point.payload or {}
            matches.append(
                VectorMatch(
                    chunk_id=str(point.id),
                    document_id=str(payload.get("document_id")),
                    text=payload.get("text", ""),
                    score=point.score,
                    metadata=payload,
                )
            )
        return matches

    async def delete(self, ids: list[str]) -> None:
        self._client.delete(collection_name=self._collection_name, points_selector=ids)


_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    """Returns the process-wide vector store instance for the configured provider."""
    global _store
    if _store is not None:
        return _store

    settings = get_settings()
    if settings.VECTOR_STORE_PROVIDER == "chroma":
        _store = ChromaVectorStore()
    elif settings.VECTOR_STORE_PROVIDER == "pinecone":
        _store = PineconeVectorStore()
    elif settings.VECTOR_STORE_PROVIDER == "qdrant":
        _store = QdrantVectorStore()
    else:
        raise ValueError(f"Unsupported VECTOR_STORE_PROVIDER: {settings.VECTOR_STORE_PROVIDER}")
    return _store
