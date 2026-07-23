import { Meter } from "@/components/Meter";
import type { Source } from "@/lib/types";
import { DOMAIN_META } from "@/lib/verdict";

function hostname(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}

export function SourceCard({ source }: { source: Source }) {
  const domain = DOMAIN_META[source.domain_type];
  const pct = Math.round(source.credibility_score * 100);
  const lowCredibility = source.credibility_score < 0.4;

  return (
    <article
      data-testid="source-card"
      className="rounded-lg border border-zinc-200 bg-white p-4 shadow-sm"
    >
      <div className="mb-1 flex items-center justify-between gap-2">
        <span className={`rounded px-2 py-0.5 text-xs font-medium ${domain.classes}`}>
          {domain.label}
        </span>
        {lowCredibility && (
          <span className="rounded bg-orange-100 px-2 py-0.5 text-xs font-medium text-orange-700">
            Low credibility
          </span>
        )}
      </div>
      <a
        href={source.url}
        target="_blank"
        rel="noopener noreferrer"
        className="block font-medium text-zinc-900 hover:underline"
      >
        {source.title || hostname(source.url)}
      </a>
      <p className="text-xs text-zinc-500">{hostname(source.url)}</p>
      <p className="mt-2 line-clamp-3 text-sm text-zinc-600">{source.snippet}</p>
      <div className="mt-3">
        <Meter
          value={source.credibility_score}
          label="Credibility"
          valueLabel={`${pct}%`}
          trackHeight="h-1.5"
          fillClass="bg-zinc-500"
          captionClass="text-xs text-zinc-500"
        />
      </div>
    </article>
  );
}
