"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { ApiError } from "@/lib/types";
import type { SentimentReport } from "@/lib/types";
import { SentimentScoreCard } from "./SentimentScoreCard";
import { SourceCitationList } from "./SourceCitationList";
import { ThemeSummary } from "./ThemeSummary";

interface ChatTurn {
  question: string;
  report?: SentimentReport;
  error?: string;
}

export function ChatInterface() {
  const [message, setMessage] = useState("");
  const [ticker, setTicker] = useState("");
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const question = message.trim();
    if (!question || loading) return;

    setMessage("");
    setLoading(true);
    try {
      const { report } = await api.chat(question, ticker.trim() || undefined);
      setTurns((prev) => [...prev, { question, report }]);
    } catch (err) {
      const detail = err instanceof ApiError ? err.message : "Something went wrong. Please try again.";
      setTurns((prev) => [...prev, { question, error: detail }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <form onSubmit={handleSubmit} className="flex flex-col gap-2 sm:flex-row">
        <input
          value={ticker}
          onChange={(e) => setTicker(e.target.value)}
          placeholder="Ticker (optional), e.g. TATAMOTORS"
          className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 dark:border-gray-700 dark:bg-gray-900 sm:w-56"
        />
        <input
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder='Ask e.g. "Why did Tata Motors fall this week?"'
          className="flex-1 rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 dark:border-gray-700 dark:bg-gray-900"
        />
        <button
          type="submit"
          disabled={loading}
          className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50"
        >
          {loading ? "Thinking…" : "Ask"}
        </button>
      </form>

      <div className="space-y-8">
        {turns.map((turn, i) => (
          <div key={i} className="space-y-4">
            <p className="text-sm font-medium text-gray-500">
              You asked: <span className="text-gray-800 dark:text-gray-200">{turn.question}</span>
            </p>

            {turn.error && (
              <p className="rounded-lg border border-negative/30 bg-negative/10 p-3 text-sm text-negative">
                {turn.error}
              </p>
            )}

            {turn.report && (
              <div className="space-y-4">
                <div className="grid gap-4 sm:grid-cols-[280px_1fr]">
                  <SentimentScoreCard
                    score={turn.report.overall_score}
                    label={turn.report.overall_label}
                    confidence={turn.report.confidence}
                  />
                  <div className="rounded-xl border border-gray-200 bg-white p-6 text-sm leading-relaxed shadow-sm dark:border-gray-800 dark:bg-gray-900">
                    {turn.report.summary}
                  </div>
                </div>
                <ThemeSummary
                  positiveDrivers={turn.report.positive_drivers}
                  negativeDrivers={turn.report.negative_drivers}
                  keyThemes={turn.report.key_themes}
                />
                <SourceCitationList citations={turn.report.citations} />
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
