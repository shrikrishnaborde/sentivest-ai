import uuid

from pydantic import BaseModel, ConfigDict


class StockBase(BaseModel):
    ticker: str
    company_name: str
    exchange: str = "NSE"
    sector: str | None = None
    isin: str | None = None


class StockCreate(StockBase):
    pass


class StockRead(StockBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
