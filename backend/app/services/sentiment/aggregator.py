"""Aggregates per-document sentiment scores into a single stock-level score
and label — used both for the nightly `SentimentSnapshot` rollup and for
scoring the set of documents retrieved for a single RAG report.
"""
from dataclasses import dataclass

from app.models.enums import SentimentLabel

_POSITIVE_THRESHOLD = 0.15
_NEGATIVE_THRESHOLD = -0.15


@dataclass
class AggregatedSentiment:
    overall_score: float
    overall_label: SentimentLabel
    positive_count: int
    neutral_count: int
    negative_count: int


def classify(score: float) -> SentimentLabel:
    if score >= _POSITIVE_THRESHOLD:
        return SentimentLabel.POSITIVE
    if score <= _NEGATIVE_THRESHOLD:
        return SentimentLabel.NEGATIVE
    return SentimentLabel.NEUTRAL


def aggregate(document_scores: list[tuple[float, SentimentLabel]]) -> AggregatedSentiment:
    """`document_scores` is a list of (signed_score, label) per document/chunk."""
    if not document_scores:
        return AggregatedSentiment(0.0, SentimentLabel.NEUTRAL, 0, 0, 0)

    positive = sum(1 for _, label in document_scores if label == SentimentLabel.POSITIVE)
    negative = sum(1 for _, label in document_scores if label == SentimentLabel.NEGATIVE)
    neutral = len(document_scores) - positive - negative

    mean_score = sum(score for score, _ in document_scores) / len(document_scores)
    overall_score = round(mean_score, 4)

    return AggregatedSentiment(
        overall_score=overall_score,
        overall_label=classify(overall_score),
        positive_count=positive,
        neutral_count=neutral,
        negative_count=negative,
    )


def confidence_from_agreement(document_scores: list[tuple[float, SentimentLabel]]) -> float:
    """Confidence = how much the retrieved sources agree with the majority
    label, scaled by sample size (few sources -> lower ceiling on confidence).
    """
    if not document_scores:
        return 0.0

    agg = aggregate(document_scores)
    counts = {
        SentimentLabel.POSITIVE: agg.positive_count,
        SentimentLabel.NEUTRAL: agg.neutral_count,
        SentimentLabel.NEGATIVE: agg.negative_count,
    }
    majority_share = max(counts.values()) / len(document_scores)
    sample_factor = min(len(document_scores) / 8, 1.0)  # ramps up to full confidence at 8+ sources
    return round(majority_share * sample_factor, 4)
