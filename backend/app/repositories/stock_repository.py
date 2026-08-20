from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.stock import Stock
from app.schemas.stock import StockCreate


class StockRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def get_by_ticker(self, ticker: str) -> Stock | None:
        result = await self._db.execute(select(Stock).where(Stock.ticker == ticker.upper()))
        return result.scalar_one_or_none()

    async def list_all(self, limit: int = 100, offset: int = 0) -> list[Stock]:
        result = await self._db.execute(select(Stock).order_by(Stock.ticker).limit(limit).offset(offset))
        return list(result.scalars().all())

    async def create(self, payload: StockCreate) -> Stock:
        data = payload.model_dump()
        data["ticker"] = data["ticker"].upper()
        stock = Stock(**data)
        self._db.add(stock)
        await self._db.commit()
        await self._db.refresh(stock)
        return stock
