"""Re-embed existing `documents` rows into the currently configured vector
store, without re-fetching anything from source adapters.

Useful after switching VECTOR_STORE_PROVIDER (or Chroma's storage backend,
e.g. moving from an embedded PersistentClient to a shared HTTP server) —
the documents already exist in Postgres, but the new vector store starts
empty, so retrieval finds nothing until this runs once.

Usage:
    PYTHONPATH=. python scripts/reindex_documents.py
"""
import asyncio

from sqlalchemy import select

from app.db.session import session_scope
from app.models.document import Document
from app.models.stock import Stock
from app.services.rag.chunking import split_into_chunks
from app.services.rag.embeddings import get_embedding_provider
from app.services.rag.vector_store import get_vector_store


async def main() -> None:
    vector_store = get_vector_store()
    embeddings = get_embedding_provider()

    async with session_scope() as db:
        result = await db.execute(select(Document).join(Stock))
        documents = result.scalars().all()
        stocks_by_id = {
            stock.id: stock for stock in (await db.execute(select(Stock))).scalars().all()
        }

        for document in documents:
            stock = stocks_by_id[document.stock_id]
            ids, texts, metadatas = [], [], []
            for i, chunk in enumerate(split_into_chunks(document.content)):
                ids.append(f"{document.id}:{i}")
                texts.append(chunk)
                metadatas.append(
                    {
                        "document_id": str(document.id),
                        "ticker": stock.ticker,
                        "source_type": document.source_type.value,
                        "published_at": document.published_at.isoformat(),
                    }
                )
            if not texts:
                continue
            vectors = await embeddings.embed_documents(texts)
            await vector_store.upsert(ids=ids, embeddings=vectors, texts=texts, metadatas=metadatas)
            document.is_indexed = True
            print(f"{stock.ticker}: reindexed {len(texts)} chunks from 1 document")

        await db.commit()

    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
