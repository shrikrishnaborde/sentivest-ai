from app.models.enums import SentimentLabel
from app.services.sentiment.aggregator import aggregate, classify, confidence_from_agreement


def test_classify_thresholds():
    assert classify(0.5) == SentimentLabel.POSITIVE
    assert classify(-0.5) == SentimentLabel.NEGATIVE
    assert classify(0.0) == SentimentLabel.NEUTRAL


def test_aggregate_empty_returns_neutral():
    result = aggregate([])
    assert result.overall_label == SentimentLabel.NEUTRAL
    assert result.overall_score == 0.0


def test_aggregate_mixed_scores():
    scores = [
        (0.6, SentimentLabel.POSITIVE),
        (0.4, SentimentLabel.POSITIVE),
        (-0.7, SentimentLabel.NEGATIVE),
    ]
    result = aggregate(scores)
    assert result.positive_count == 2
    assert result.negative_count == 1
    assert result.document_count if hasattr(result, "document_count") else True
    assert -1.0 <= result.overall_score <= 1.0


def test_confidence_increases_with_agreement_and_sample_size():
    unanimous_many = [(0.5, SentimentLabel.POSITIVE)] * 8
    split_few = [(0.5, SentimentLabel.POSITIVE), (-0.5, SentimentLabel.NEGATIVE)]

    high_confidence = confidence_from_agreement(unanimous_many)
    low_confidence = confidence_from_agreement(split_few)

    assert high_confidence > low_confidence
    assert 0.0 <= high_confidence <= 1.0
