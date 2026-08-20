import uuid
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sentiment import SentimentSnapshot


class SentimentRepository:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def get_trend(
        self, stock_id: uuid.UUID, days: int = 30
    ) -> list[SentimentSnapshot]:
        since = date.today() - timedelta(days=days)
        result = await self._db.execute(
            select(SentimentSnapshot)
            .where(SentimentSnapshot.stock_id == stock_id, SentimentSnapshot.snapshot_date >= since)
            .order_by(SentimentSnapshot.snapshot_date)
        )
        return list(result.scalars().all())
