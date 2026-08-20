import enum


class SourceType(str, enum.Enum):
    NEWS = "news"
    EARNINGS_CALL = "earnings_call"
    ANNUAL_REPORT = "annual_report"
    ANALYST_REPORT = "analyst_report"
    COMPANY_ANNOUNCEMENT = "company_announcement"
    REGULATORY_FILING = "regulatory_filing"


class SentimentLabel(str, enum.Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
