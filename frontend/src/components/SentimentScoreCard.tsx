import clsx from "clsx";
import type { SentimentLabel } from "@/lib/types";

const LABEL_STYLES: Record<SentimentLabel, string> = {
  positive: "bg-positive/10 text-positive border-positive/30",
  neutral: "bg-neutral/10 text-neutral border-neutral/30",
  negative: "bg-negative/10 text-negative border-negative/30",
};

const LABEL_TEXT: Record<SentimentLabel, string> = {
  positive: "Positive",
  neutral: "Neutral",
  negative: "Negative",
};

interface Props {
  score: number; // -1.0 .. 1.0
  label: SentimentLabel;
  confidence: number; // 0.0 .. 1.0
}

export function SentimentScoreCard({ score, label, confidence }: Props) {
  const pct = Math.round(((score + 1) / 2) * 100);

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-800 dark:bg-gray-900">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Overall Sentiment</h3>
        <span
          className={clsx(
            "rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-wide",
            LABEL_STYLES[label]
          )}
        >
          {LABEL_TEXT[label]}
        </span>
      </div>

      <div className="mt-4 flex items-baseline gap-2">
        <span className="text-4xl font-bold tabular-nums">{score.toFixed(2)}</span>
        <span className="text-sm text-gray-400">/ 1.00</span>
      </div>

      <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-gray-100 dark:bg-gray-800">
        <div
          className={clsx(
            "h-full rounded-full transition-all",
            label === "positive" && "bg-positive",
            label === "neutral" && "bg-neutral",
            label === "negative" && "bg-negative"
          )}
          style={{ width: `${pct}%` }}
        />
      </div>

      <p className="mt-3 text-xs text-gray-500 dark:text-gray-400">
        Confidence: <span className="font-semibold">{Math.round(confidence * 100)}%</span> — based on
        source agreement and volume
      </p>
    </div>
  );
}
