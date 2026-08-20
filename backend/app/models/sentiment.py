import uuid
from datetime import date

from sqlalchemy import Date, Enum, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.types import GUID
from app.models.enums import SentimentLabel


class SentimentSnapshot(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Daily aggregated sentiment for a stock — powers the trend chart.

    One row per (stock, date). Recomputed by the nightly aggregation job
    from that day's ingested documents.
    """

    __tablename__ = "sentiment_snapshots"
    __table_args__ = (
        # one snapshot per stock per day
        {"sqlite_autoincrement": True},
    )

    stock_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    overall_score: Mapped[float] = mapped_column(Float, nullable=False)  # -1.0 .. 1.0
    overall_label: Mapped[SentimentLabel] = mapped_column(Enum(SentimentLabel), nullable=False)
    positive_count: Mapped[int] = mapped_column(Integer, default=0)
    neutral_count: Mapped[int] = mapped_column(Integer, default=0)
    negative_count: Mapped[int] = mapped_column(Integer, default=0)
    document_count: Mapped[int] = mapped_column(Integer, default=0)

    stock = relationship("Stock", back_populates="sentiment_snapshots")


class SentimentReport(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A generated, evidence-backed RAG report answering a user query about a stock.

    Cached so repeat questions (or the dashboard's "latest summary" widget)
    don't re-run retrieval + LLM generation unnecessarily.
    """

    __tablename__ = "sentiment_reports"

    stock_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    query: Mapped[str] = mapped_column(Text, nullable=False)

    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    overall_label: Mapped[SentimentLabel] = mapped_column(Enum(SentimentLabel), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)  # 0.0 .. 1.0

    summary: Mapped[str] = mapped_column(Text, nullable=False)
    positive_drivers: Mapped[list[str]] = mapped_column(JSON, default=list)
    negative_drivers: Mapped[list[str]] = mapped_column(JSON, default=list)
    key_themes: Mapped[list[str]] = mapped_column(JSON, default=list)

    # Ordered list of {document_id, title, url, source_type, relevance_score}
    citations: Mapped[list[dict]] = mapped_column(JSON, default=list)

    llm_model: Mapped[str] = mapped_column(String(120), nullable=False)

    stock = relationship("Stock", back_populates="sentiment_reports")
