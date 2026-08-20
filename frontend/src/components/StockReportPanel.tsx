"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { ApiError } from "@/lib/types";
import type { SentimentReport } from "@/lib/types";
import { SentimentScoreCard } from "./SentimentScoreCard";
import { SourceCitationList } from "./SourceCitationList";
import { ThemeSummary } from "./ThemeSummary";

const DEFAULT_QUERY = "What is the current market sentiment and why?";

export function StockReportPanel({ ticker }: { ticker: string }) {
  const [query, setQuery] = useState(DEFAULT_QUERY);
  const [report, setReport] = useState<SentimentReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const runAnalysis = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const result = await api.analyzeSentiment(ticker, query);
      setReport(result);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Failed to generate report. Is the backend running and has this stock been ingested?"
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <form onSubmit={runAnalysis} className="flex flex-col gap-2 sm:flex-row">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="flex-1 rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 dark:border-gray-700 dark:bg-gray-900"
        />
        <button
          type="submit"
          disabled={loading}
          className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50"
        >
          {loading ? "Analyzing…" : "Generate Report"}
        </button>
      </form>

      {error && (
        <p className="rounded-lg border border-negative/30 bg-negative/10 p-3 text-sm text-negative">
          {error}
        </p>
      )}

      {report && (
        <div className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-[280px_1fr]">
            <SentimentScoreCard
              score={report.overall_score}
              label={report.overall_label}
              confidence={report.confidence}
            />
            <div className="rounded-xl border border-gray-200 bg-white p-6 text-sm leading-relaxed shadow-sm dark:border-gray-800 dark:bg-gray-900">
              {report.summary}
            </div>
          </div>
          <ThemeSummary
            positiveDrivers={report.positive_drivers}
            negativeDrivers={report.negative_drivers}
            keyThemes={report.key_themes}
          />
          <SourceCitationList citations={report.citations} />
        </div>
      )}
    </div>
  );
}
