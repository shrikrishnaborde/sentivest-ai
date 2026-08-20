"""Shared FastAPI dependencies for the v1 endpoints."""
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.stock import Stock
from app.repositories.stock_repository import StockRepository


async def get_stock_or_404(ticker: str, db: AsyncSession = Depends(get_db)) -> Stock:
    stock = await StockRepository(db).get_by_ticker(ticker)
    if stock is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock '{ticker}' is not tracked. POST /stocks to add it first.",
        )
    return stock
