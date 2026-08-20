"use client";

import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { SentimentSnapshotPoint } from "@/lib/types";

interface Props {
  points: SentimentSnapshotPoint[];
}

export function SentimentTrendChart({ points }: Props) {
  if (points.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center rounded-xl border border-dashed border-gray-300 text-sm text-gray-400 dark:border-gray-700">
        No historical sentiment data yet — trigger ingestion to build a trend.
      </div>
    );
  }

  const data = points.map((p) => ({ date: p.snapshot_date, score: p.overall_score }));

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-800 dark:bg-gray-900">
      <h3 className="mb-4 text-sm font-medium text-gray-500 dark:text-gray-400">
        30-Day Sentiment Trend
      </h3>
      <ResponsiveContainer width="100%" height={240}>
        <LineChart data={data} margin={{ top: 5, right: 12, left: -12, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" className="stroke-gray-100 dark:stroke-gray-800" />
          <XAxis dataKey="date" tick={{ fontSize: 11 }} minTickGap={24} />
          <YAxis domain={[-1, 1]} tick={{ fontSize: 11 }} />
          <ReferenceLine y={0} stroke="#9ca3af" strokeDasharray="3 3" />
          <Tooltip
            formatter={(value: number) => value.toFixed(2)}
            contentStyle={{ fontSize: 12, borderRadius: 8 }}
          />
          <Line
            type="monotone"
            dataKey="score"
            stroke="#4f46e5"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
