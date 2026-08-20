import type { Citation } from "@/lib/types";

const SOURCE_LABELS: Record<string, string> = {
  news: "News",
  earnings_call: "Earnings Call",
  annual_report: "Annual Report",
  analyst_report: "Analyst Report",
  company_announcement: "Company Announcement",
  regulatory_filing: "Regulatory Filing",
};

export function SourceCitationList({ citations }: { citations: Citation[] }) {
  if (citations.length === 0) return null;

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-800 dark:bg-gray-900">
      <h3 className="mb-4 text-sm font-medium text-gray-500 dark:text-gray-400">
        Sources ({citations.length})
      </h3>
      <ol className="space-y-3">
        {citations.map((citation, i) => (
          <li key={citation.document_id} className="border-l-2 border-brand-500 pl-3 text-sm">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-mono text-xs text-gray-400">[{i + 1}]</span>
              {citation.url ? (
                <a
                  href={citation.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-medium text-brand-600 hover:underline dark:text-brand-500"
                >
                  {citation.title}
                </a>
              ) : (
                <span className="font-medium">{citation.title}</span>
              )}
              <span className="rounded bg-gray-100 px-1.5 py-0.5 text-[10px] uppercase text-gray-500 dark:bg-gray-800">
                {SOURCE_LABELS[citation.source_type] ?? citation.source_type}
              </span>
            </div>
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              {citation.source_name} · {new Date(citation.published_at).toLocaleDateString()} · relevance{" "}
              {Math.round(citation.relevance_score * 100)}%
            </p>
            <p className="mt-1 text-xs text-gray-600 dark:text-gray-300">{citation.snippet}</p>
          </li>
        ))}
      </ol>
    </div>
  );
}
