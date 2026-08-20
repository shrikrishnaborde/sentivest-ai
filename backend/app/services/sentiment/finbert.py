"""Finance-specific sentiment scoring using FinBERT (ProsusAI/finbert).

FinBERT is a BERT model fine-tuned on financial text, which outperforms
general-purpose sentiment models on financial news/filings because it
understands domain phrasing (e.g. "beat estimates" is positive, "guided
down" is negative — general models often miss this).

The pipeline is loaded once per process (it's a ~400MB model) and reused
across requests; loading is deferred to first use so `import`ing this
module doesn't pay the cost.
"""
from dataclasses import dataclass
from functools import lru_cache

from app.core.config import get_settings
from app.models.enums import SentimentLabel

_LABEL_MAP = {
    "positive": SentimentLabel.POSITIVE,
    "negative": SentimentLabel.NEGATIVE,
    "neutral": SentimentLabel.NEUTRAL,
}


@dataclass
class SentimentResult:
    label: SentimentLabel
    score: float  # signed, -1.0 (very negative) .. 1.0 (very positive)
    raw_scores: dict[str, float]  # {"positive": .., "negative": .., "neutral": ..}


class FinBertSentimentScorer:
    def __init__(self):
        self._pipeline = None

    def _load(self):
        if self._pipeline is not None:
            return self._pipeline

        from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline

        settings = get_settings()
        tokenizer = AutoTokenizer.from_pretrained(settings.FINBERT_MODEL_NAME)
        model = AutoModelForSequenceClassification.from_pretrained(settings.FINBERT_MODEL_NAME)
        device = 0 if settings.SENTIMENT_DEVICE == "cuda" else -1

        self._pipeline = pipeline(
            "text-classification",
            model=model,
            tokenizer=tokenizer,
            top_k=None,
            truncation=True,
            max_length=512,
            device=device,
        )
        return self._pipeline

    def score(self, text: str) -> SentimentResult:
        return self.score_batch([text])[0]

    def score_batch(self, texts: list[str]) -> list[SentimentResult]:
        if not texts:
            return []
        clf = self._load()
        raw_results = clf(texts)

        results = []
        for scores in raw_results:
            by_label = {item["label"].lower(): item["score"] for item in scores}
            top_label = max(by_label, key=by_label.get)
            # Signed score: positive contributes +, negative contributes -,
            # neutral is excluded so a strong neutral doesn't drag toward 0
            # more than a genuinely mixed positive/negative split would.
            signed = by_label.get("positive", 0.0) - by_label.get("negative", 0.0)
            results.append(
                SentimentResult(
                    label=_LABEL_MAP[top_label],
                    score=round(signed, 4),
                    raw_scores=by_label,
                )
            )
        return results


@lru_cache
def get_sentiment_scorer() -> FinBertSentimentScorer:
    return FinBertSentimentScorer()
