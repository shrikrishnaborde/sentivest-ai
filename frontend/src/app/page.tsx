import Link from "next/link";
import { api } from "@/lib/api";
import { StockSearchBar } from "@/components/StockSearchBar";

export default async function DashboardPage() {
  const stocks = await api.listStocks().catch(() => []);

  return (
    <div className="space-y-10">
      <section className="space-y-3">
        <h1 className="text-2xl font-bold">Turn financial noise into investment insights.</h1>
        <p className="max-w-2xl text-sm text-gray-500 dark:text-gray-400">
          SentiVest AI retrieves and grounds sentiment analysis in real financial news, filings,
          earnings calls, and analyst reports — no unsupported AI opinions.
        </p>
        <StockSearchBar />
      </section>

      <section>
        <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-gray-400">
          Tracked Stocks
        </h2>
        {stocks.length === 0 ? (
          <div className="rounded-xl border border-dashed border-gray-300 p-8 text-center text-sm text-gray-400 dark:border-gray-700">
            No stocks tracked yet. Add one via <code className="font-mono">POST /api/v1/stocks</code>{" "}
            or search for a ticker above.
          </div>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {stocks.map((stock) => (
              <Link
                key={stock.id}
                href={`/stock/${stock.ticker}`}
                className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm transition hover:border-brand-500 hover:shadow-md dark:border-gray-800 dark:bg-gray-900"
              >
                <p className="font-semibold">{stock.ticker}</p>
                <p className="text-sm text-gray-500 dark:text-gray-400">{stock.company_name}</p>
                <p className="mt-1 text-xs text-gray-400">
                  {stock.exchange}
                  {stock.sector ? ` · ${stock.sector}` : ""}
                </p>
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
