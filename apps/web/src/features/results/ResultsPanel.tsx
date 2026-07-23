import type { VerifyResponse } from "@/lib/types";
import { formatDate, timeAgo } from "@/lib/time";
import { ConfidenceBar } from "./ConfidenceBar";
import { ReasoningCard } from "./ReasoningCard";
import { SourceCard } from "./SourceCard";
import { VerdictBadge } from "./VerdictBadge";

export function ResultsPanel({ result }: { result: VerifyResponse }) {
  return (
    <section
      data-testid="results-panel"
      className="flex flex-col gap-4 rounded-xl border border-zinc-200 bg-white p-5 shadow-sm"
    >
      <h2 className="sr-only">Fact-check result</h2>
      <div>
        <p className="mb-2 text-sm text-zinc-500">Claim</p>
        <p className="text-lg font-medium text-zinc-900">{result.claim}</p>
      </div>

      <div className="flex flex-wrap items-center gap-4">
        <VerdictBadge verdict={result.verdict} />
        <div className="min-w-[180px] flex-1">
          <ConfidenceBar confidence={result.confidence} />
        </div>
      </div>

      <ReasoningCard reasoning={result.reasoning} />

      {result.source_mode_fallback && (
        <p className="rounded-md bg-amber-50 px-3 py-2 text-xs text-amber-800">
          Strict mode found too few sources, so results include all sources.
        </p>
      )}

      {result.sources.length > 0 && (
        <div>
          <h3 className="mb-2 text-sm font-semibold text-zinc-700">
            Sources ({result.sources.length})
          </h3>
          <div className="grid gap-3 sm:grid-cols-2">
            {result.sources.map((s) => (
              <SourceCard key={s.url} source={s} />
            ))}
          </div>
        </div>
      )}

      {result.cached_at && (
        <p className="text-xs text-zinc-400">
          {result.cached ? "Cached result from" : "Checked"} {timeAgo(result.cached_at)}
          {result.ttl_expires_at &&
            ` — refreshes after ${formatDate(result.ttl_expires_at)}`}
        </p>
      )}
    </section>
  );
}
