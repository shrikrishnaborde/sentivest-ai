from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.deps import get_stock_or_404
from app.db.session import get_db
from app.models.stock import Stock
from app.repositories.stock_repository import StockRepository
from app.schemas.stock import StockCreate, StockRead

router = APIRouter(prefix="/stocks", tags=["stocks"])


@router.get("", response_model=list[StockRead])
async def list_stocks(limit: int = 100, offset: int = 0, db: AsyncSession = Depends(get_db)):
    return await StockRepository(db).list_all(limit=limit, offset=offset)


@router.post("", response_model=StockRead, status_code=status.HTTP_201_CREATED)
async def add_stock(payload: StockCreate, db: AsyncSession = Depends(get_db)):
    repo = StockRepository(db)
    if await repo.get_by_ticker(payload.ticker) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=f"{payload.ticker} is already tracked")
    return await repo.create(payload)


@router.get("/{ticker}", response_model=StockRead)
async def get_stock(stock: Stock = Depends(get_stock_or_404)):
    return stock
