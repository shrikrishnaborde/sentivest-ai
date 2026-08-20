import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.types import GUID
from app.models.enums import SentimentLabel, SourceType


class Document(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A single ingested source document (news article, filing excerpt, etc.).

    The full text lives here (Postgres); its chunk embeddings live in the
    vector store, linked back by `id` so retrieval results can be resolved
    to this row for citations and metadata.
    """

    __tablename__ = "documents"

    stock_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_type: Mapped[SourceType] = mapped_column(Enum(SourceType), nullable=False, index=True)
    source_name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    # Document-level sentiment, produced by FinBERT at ingestion time.
    sentiment_label: Mapped[SentimentLabel | None] = mapped_column(Enum(SentimentLabel), nullable=True)
    sentiment_score: Mapped[float | None] = mapped_column(Float, nullable=True)  # -1.0 .. 1.0

    doc_metadata: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    is_indexed: Mapped[bool] = mapped_column(default=False, nullable=False)

    stock = relationship("Stock", back_populates="documents")

    def __repr__(self) -> str:
        return f"<Document {self.title[:40]!r} ({self.source_type})>"
