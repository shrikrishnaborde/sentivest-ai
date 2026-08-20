from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Stock(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A tracked equity, e.g. INFY / NSE:INFY / Infosys Ltd."""

    __tablename__ = "stocks"

    ticker: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    exchange: Mapped[str] = mapped_column(String(20), nullable=False, default="NSE")
    sector: Mapped[str | None] = mapped_column(String(120), nullable=True)
    isin: Mapped[str | None] = mapped_column(String(20), nullable=True, unique=True)

    documents = relationship("Document", back_populates="stock", cascade="all, delete-orphan")
    sentiment_snapshots = relationship(
        "SentimentSnapshot", back_populates="stock", cascade="all, delete-orphan"
    )
    sentiment_reports = relationship(
        "SentimentReport", back_populates="stock", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Stock {self.ticker}>"
