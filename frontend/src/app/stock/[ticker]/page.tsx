import { notFound } from "next/navigation";
import { api } from "@/lib/api";
import { ApiError } from "@/lib/types";
import { SentimentTrendChart } from "@/components/SentimentTrendChart";
import { StockReportPanel } from "@/components/StockReportPanel";

interface Props {
  params: { ticker: string };
}

export default async function StockDetailPage({ params }: Props) {
  const ticker = params.ticker.toUpperCase();

  const stock = await api.getStock(ticker).catch((err) => {
    if (err instanceof ApiError && err.status === 404) return null;
    throw err;
  });

  if (!stock) notFound();

  const trend = await api.getSentimentTrend(ticker).catch(() => ({
    ticker,
    from_date: "",
    to_date: "",
    points: [],
  }));

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold">{stock.company_name}</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          {stock.ticker} · {stock.exchange}
          {stock.sector ? ` · ${stock.sector}` : ""}
        </p>
      </div>

      <SentimentTrendChart points={trend.points} />

      <StockReportPanel ticker={stock.ticker} />
    </div>
  );
}
