"""Ingestion trigger endpoint. Mutating and rate-limit-sensitive (it calls
paid third-party APIs), so it sits behind the shared API-key dependency
rather than being public like the read endpoints.
"""
from fastapi import APIRouter, Depends

from app.api.v1.endpoints.deps import get_stock_or_404
from app.core.security import require_api_key
from app.models.stock import Stock
from app.schemas.ingestion import IngestionTriggerRequest, IngestionTriggerResponse
from app.worker.tasks import ingest_ticker

router = APIRouter(prefix="/ingestion", tags=["ingestion"], dependencies=[Depends(require_api_key)])


@router.post("/{ticker}/trigger", response_model=IngestionTriggerResponse)
async def trigger_ingestion(payload: IngestionTriggerRequest, stock: Stock = Depends(get_stock_or_404)):
    task = ingest_ticker.delay(
        stock.ticker,
        [s.value for s in payload.source_types],
        payload.lookback_days,
    )
    return IngestionTriggerResponse(task_id=task.id, ticker=stock.ticker)
