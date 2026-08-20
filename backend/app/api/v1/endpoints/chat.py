"""Natural-language Q&A endpoint. Answers questions like "Why did Tata
Motors fall this week?" by resolving the mentioned company to a ticker,
then delegating to the same ReportGenerator the /sentiment endpoints use —
chat is a convenience layer over the sentiment pipeline, not a separate one.
"""
import re

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.repositories.stock_repository import StockRepository
from app.schemas.chat import ChatQueryRequest, ChatQueryResponse
from app.services.report_generator import NoEvidenceFoundError, ReportGenerator

router = APIRouter(prefix="/chat", tags=["chat"])

_TICKER_PATTERN = re.compile(r"\b[A-Z]{2,15}\b")


async def _resolve_ticker(db: AsyncSession, message: str, explicit_ticker: str | None) -> str | None:
    repo = StockRepository(db)
    if explicit_ticker:
        stock = await repo.get_by_ticker(explicit_ticker)
        return stock.ticker if stock else None

    # Naive fallback: try matching any known ticker or company-name token
    # mentioned in the message. Production would use a proper NER/entity
    # linker; this keeps the reference implementation dependency-free.
    candidates = _TICKER_PATTERN.findall(message.upper())
    for candidate in candidates:
        stock = await repo.get_by_ticker(candidate)
        if stock:
            return stock.ticker

    all_stocks = await repo.list_all(limit=500)
    lowered = message.lower()
    for stock in all_stocks:
        if stock.company_name.lower() in lowered:
            return stock.ticker
    return None


@router.post("", response_model=ChatQueryResponse)
async def chat_query(payload: ChatQueryRequest, db: AsyncSession = Depends(get_db)):
    ticker = await _resolve_ticker(db, payload.message, payload.ticker)
    if ticker is None:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not identify a tracked stock in your question. "
            "Try including the ticker explicitly, e.g. {\"ticker\": \"TATAMOTORS\"}.",
        )

    stock = await StockRepository(db).get_by_ticker(ticker)
    try:
        report = await ReportGenerator().generate(
            db=db, stock=stock, query=payload.message, lookback_days=payload.lookback_days
        )
    except NoEvidenceFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    from app.api.v1.endpoints.sentiment import _to_response

    return ChatQueryResponse(ticker=ticker, report=_to_response(report, ticker))
