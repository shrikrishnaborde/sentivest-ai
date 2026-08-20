"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

export function StockSearchBar() {
  const [ticker, setTicker] = useState("");
  const router = useRouter();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = ticker.trim().toUpperCase();
    if (trimmed) router.push(`/stock/${trimmed}`);
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <input
        value={ticker}
        onChange={(e) => setTicker(e.target.value)}
        placeholder="Enter a ticker, e.g. INFY"
        className="w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500 dark:border-gray-700 dark:bg-gray-900"
      />
      <button
        type="submit"
        className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
      >
        Analyze
      </button>
    </form>
  );
}
