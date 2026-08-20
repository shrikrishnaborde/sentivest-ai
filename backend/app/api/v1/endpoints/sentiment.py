from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.deps import get_stock_or_404
from app.db.session import get_db
from app.models.stock import Stock
from app.repositories.sentiment_repository import SentimentRepository
from app.schemas.sentiment import (
    SentimentReportRequest,
    SentimentReportResponse,
    SentimentTrendResponse,
)
from app.services.report_generator import NoEvidenceFoundError, ReportGenerator

router = APIRouter(prefix="/sentiment", tags=["sentiment"])


def _to_response(report, ticker: str) -> SentimentReportResponse:
    return SentimentReportResponse(
        id=report.id,
        stock_id=report.stock_id,
        ticker=ticker,
        query=report.query,
        overall_score=report.overall_score,
        overall_label=report.overall_label,
        confidence=report.confidence,
        summary=report.summary,
        positive_drivers=report.positive_drivers,
        negative_drivers=report.negative_drivers,
        key_themes=report.key_themes,
        citations=report.citations,
        llm_model=report.llm_model,
        generated_at=report.created_at,
    )


@router.post("/{ticker}/analyze", response_model=SentimentReportResponse)
async def analyze_sentiment(
    payload: SentimentReportRequest,
    stock: Stock = Depends(get_stock_or_404),
    db: AsyncSession = Depends(get_db),
):
    """Runs the full RAG pipeline and returns an evidence-backed sentiment report."""
    try:
        report = await ReportGenerator().generate(
            db=db,
            stock=stock,
            query=payload.query,
            lookback_days=payload.lookback_days,
            top_k=payload.top_k,
        )
    except NoEvidenceFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return _to_response(report, stock.ticker)


@router.get("/{ticker}/trend", response_model=SentimentTrendResponse)
async def sentiment_trend(
    days: int = 30,
    stock: Stock = Depends(get_stock_or_404),
    db: AsyncSession = Depends(get_db),
):
    """Historical daily sentiment snapshots — powers the trend chart."""
    snapshots = await SentimentRepository(db).get_trend(stock.id, days=days)
    return SentimentTrendResponse(
        ticker=stock.ticker,
        from_date=date.today() - timedelta(days=days),
        to_date=date.today(),
        points=snapshots,
    )
