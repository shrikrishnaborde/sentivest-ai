"""Orchestrates a single end-to-end RAG sentiment report:

  1. Retrieve relevant, recent document chunks for the stock (Retriever).
  2. Score each chunk's sentiment with FinBERT and aggregate into an
     overall score/label/confidence (sentiment.aggregator).
  3. Ask the LLM to synthesize a grounded narrative summary + drivers/themes
     from the same retrieved chunks (llm.client + llm.prompts).
  4. Persist the result as a `SentimentReport` row and return it.

This is the one place all three pillars — retrieval, sentiment, generation
— meet, so callers (API endpoints, chat) never talk to the sub-services
directly.
"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sentiment import SentimentReport
from app.models.stock import Stock
from app.services.llm.client import LLMClient, get_llm_client
from app.services.llm.prompts import SYSTEM_PROMPT, build_user_prompt
from app.services.rag.retriever import Retriever, RetrievedChunk
from app.services.sentiment.aggregator import aggregate, confidence_from_agreement
from app.services.sentiment.finbert import FinBertSentimentScorer, get_sentiment_scorer


class NoEvidenceFoundError(Exception):
    """Raised when retrieval returns no relevant, recent documents for the stock."""


class ReportGenerator:
    def __init__(
        self,
        retriever: Retriever | None = None,
        sentiment_scorer: FinBertSentimentScorer | None = None,
        llm_client: LLMClient | None = None,
    ):
        self._retriever = retriever or Retriever()
        self._sentiment = sentiment_scorer or get_sentiment_scorer()
        self._llm = llm_client or get_llm_client()

    async def generate(
        self,
        db: AsyncSession,
        stock: Stock,
        query: str,
        lookback_days: int = 30,
        top_k: int | None = None,
    ) -> SentimentReport:
        chunks = await self._retriever.retrieve(
            db=db,
            query=query,
            stock_id=str(stock.id),
            ticker=stock.ticker,
            top_k=top_k,
            lookback_days=lookback_days,
            company_name=stock.company_name,
        )
        if not chunks:
            raise NoEvidenceFoundError(
                f"No relevant documents found for {stock.ticker} in the last {lookback_days} days."
            )

        sentiment_results = self._sentiment.score_batch([c.chunk_text for c in chunks])
        document_scores = [(r.score, r.label) for r in sentiment_results]
        agg = aggregate(document_scores)
        confidence = confidence_from_agreement(document_scores)

        generation = await self._llm.generate_structured(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=build_user_prompt(
                company_name=stock.company_name,
                ticker=stock.ticker,
                query=query,
                context_chunks=[c.chunk_text for c in chunks],
            ),
        )

        citations = [
            {
                "document_id": str(chunk.document.id),
                "title": chunk.document.title,
                "url": chunk.document.url,
                "source_type": chunk.document.source_type.value,
                "source_name": chunk.document.source_name,
                "published_at": chunk.document.published_at.isoformat(),
                "relevance_score": round(chunk.relevance_score, 4),
                "snippet": chunk.chunk_text[:280],
            }
            for chunk in chunks
        ]

        report = SentimentReport(
            stock_id=stock.id,
            query=query,
            overall_score=agg.overall_score,
            overall_label=agg.overall_label,
            confidence=confidence,
            summary=generation.summary,
            positive_drivers=generation.positive_drivers,
            negative_drivers=generation.negative_drivers,
            key_themes=generation.key_themes,
            citations=citations,
            llm_model=generation.model,
        )
        db.add(report)
        await db.commit()
        await db.refresh(report)
        return report
