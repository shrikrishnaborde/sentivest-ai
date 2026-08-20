from pydantic import BaseModel, Field

from app.schemas.sentiment import SentimentReportResponse


class ChatQueryRequest(BaseModel):
    """Free-form natural-language question, optionally scoped to a ticker.

    If `ticker` is omitted, the router does lightweight NER-style ticker
    extraction from `message` before running the RAG pipeline.
    """

    message: str = Field(min_length=3, max_length=1000, examples=["Why did Tata Motors fall this week?"])
    ticker: str | None = Field(default=None, examples=["TATAMOTORS"])
    lookback_days: int = Field(default=30, ge=1, le=365)


class ChatQueryResponse(BaseModel):
    ticker: str
    report: SentimentReportResponse
