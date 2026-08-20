import type { ChatResponse, SentimentReport, SentimentTrend, Stock } from "./types";
import { ApiError } from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
    cache: "no-store",
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new ApiError(body.detail ?? response.statusText, response.status);
  }
  return response.json() as Promise<T>;
}

export const api = {
  listStocks: () => request<Stock[]>("/stocks"),

  getStock: (ticker: string) => request<Stock>(`/stocks/${ticker}`),

  addStock: (payload: { ticker: string; company_name: string; exchange?: string; sector?: string }) =>
    request<Stock>("/stocks", { method: "POST", body: JSON.stringify(payload) }),

  analyzeSentiment: (ticker: string, query: string, lookbackDays = 30) =>
    request<SentimentReport>(`/sentiment/${ticker}/analyze`, {
      method: "POST",
      body: JSON.stringify({ query, lookback_days: lookbackDays }),
    }),

  getSentimentTrend: (ticker: string, days = 30) =>
    request<SentimentTrend>(`/sentiment/${ticker}/trend?days=${days}`),

  chat: (message: string, ticker?: string) =>
    request<ChatResponse>("/chat", { method: "POST", body: JSON.stringify({ message, ticker }) }),
};
