interface Props {
  positiveDrivers: string[];
  negativeDrivers: string[];
  keyThemes: string[];
}

function Chip({ text, tone }: { text: string; tone: "positive" | "negative" | "neutral" }) {
  const toneClass =
    tone === "positive"
      ? "bg-positive/10 text-positive"
      : tone === "negative"
        ? "bg-negative/10 text-negative"
        : "bg-brand-50 text-brand-700 dark:bg-brand-500/10 dark:text-brand-500";

  return <span className={`rounded-full px-3 py-1 text-xs font-medium ${toneClass}`}>{text}</span>;
}

export function ThemeSummary({ positiveDrivers, negativeDrivers, keyThemes }: Props) {
  return (
    <div className="grid gap-4 rounded-xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-800 dark:bg-gray-900 sm:grid-cols-3">
      <div>
        <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
          Positive Drivers
        </h4>
        <div className="flex flex-wrap gap-2">
          {positiveDrivers.length > 0 ? (
            positiveDrivers.map((d) => <Chip key={d} text={d} tone="positive" />)
          ) : (
            <span className="text-xs text-gray-400">None identified</span>
          )}
        </div>
      </div>

      <div>
        <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-400">
          Negative Drivers
        </h4>
        <div className="flex flex-wrap gap-2">
          {negativeDrivers.length > 0 ? (
            negativeDrivers.map((d) => <Chip key={d} text={d} tone="negative" />)
          ) : (
            <span className="text-xs text-gray-400">None identified</span>
          )}
        </div>
      </div>

      <div>
        <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-400">Key Themes</h4>
        <div className="flex flex-wrap gap-2">
          {keyThemes.length > 0 ? (
            keyThemes.map((d) => <Chip key={d} text={d} tone="neutral" />)
          ) : (
            <span className="text-xs text-gray-400">None identified</span>
          )}
        </div>
      </div>
    </div>
  );
}
