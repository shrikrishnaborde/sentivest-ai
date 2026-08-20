export type SentimentLabel = "positive" | "neutral" | "negative";

export type SourceType =
  | "news"
  | "earnings_call"
  | "annual_report"
  | "analyst_report"
  | "company_announcement"
  | "regulatory_filing";

export interface Stock {
  id: string;
  ticker: string;
  company_name: string;
  exchange: string;
  sector: string | null;
  isin: string | null;
}

export interface Citation {
  document_id: string;
  title: string;
  url: string | null;
  source_type: SourceType;
  source_name: string;
  published_at: string;
  relevance_score: number;
  snippet: string;
}

export interface SentimentReport {
  id: string;
  stock_id: string;
  ticker: string;
  query: string;
  overall_score: number;
  overall_label: SentimentLabel;
  confidence: number;
  summary: string;
  positive_drivers: string[];
  negative_drivers: string[];
  key_themes: string[];
  citations: Citation[];
  llm_model: string;
  generated_at: string;
}

export interface SentimentSnapshotPoint {
  snapshot_date: string;
  overall_score: number;
  overall_label: SentimentLabel;
  positive_count: number;
  neutral_count: number;
  negative_count: number;
  document_count: number;
}

export interface SentimentTrend {
  ticker: string;
  from_date: string;
  to_date: string;
  points: SentimentSnapshotPoint[];
}

export interface ChatResponse {
  ticker: string;
  report: SentimentReport;
}

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number
  ) {
    super(message);
    this.name = "ApiError";
  }
}
