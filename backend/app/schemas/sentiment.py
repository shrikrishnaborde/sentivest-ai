import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import SentimentLabel, SourceType


class Citation(BaseModel):
    document_id: uuid.UUID
    title: str
    url: str | None = None
    source_type: SourceType
    source_name: str
    published_at: datetime
    relevance_score: float = Field(ge=0.0, le=1.0)
    snippet: str


class SentimentReportRequest(BaseModel):
    """Body for POST /sentiment/{ticker}/analyze and the chat endpoint."""

    query: str = Field(
        default="What is the current market sentiment and why?",
        min_length=3,
        max_length=1000,
        examples=["Why did Tata Motors fall this week?"],
    )
    lookback_days: int = Field(default=30, ge=1, le=365)
    top_k: int | None = Field(default=None, ge=1, le=50)


class SentimentReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    stock_id: uuid.UUID
    ticker: str
    query: str

    overall_score: float = Field(ge=-1.0, le=1.0)
    overall_label: SentimentLabel
    confidence: float = Field(ge=0.0, le=1.0)

    summary: str
    positive_drivers: list[str]
    negative_drivers: list[str]
    key_themes: list[str]
    citations: list[Citation]

    llm_model: str
    generated_at: datetime


class SentimentSnapshotRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    snapshot_date: date
    overall_score: float
    overall_label: SentimentLabel
    positive_count: int
    neutral_count: int
    negative_count: int
    document_count: int


class SentimentTrendResponse(BaseModel):
    ticker: str
    from_date: date
    to_date: date
    points: list[SentimentSnapshotRead]
