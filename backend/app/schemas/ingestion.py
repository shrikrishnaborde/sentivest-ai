import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import SourceType


class IngestionTriggerRequest(BaseModel):
    ticker: str
    source_types: list[SourceType] = Field(default_factory=lambda: list(SourceType))
    lookback_days: int = Field(default=7, ge=1, le=365)


class IngestionTriggerResponse(BaseModel):
    task_id: str
    ticker: str
    status: str = "queued"


class DocumentRead(BaseModel):
    id: uuid.UUID
    title: str
    source_type: SourceType
    source_name: str
    url: str | None
    published_at: datetime
    sentiment_label: str | None
    sentiment_score: float | None
