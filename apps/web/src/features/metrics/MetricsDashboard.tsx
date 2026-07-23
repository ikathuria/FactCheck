"use client";

import { useEffect, useState } from "react";

import { getRecentSearches } from "@/lib/api";
import type { Verdict } from "@/lib/types";
import { VERDICT_META } from "@/lib/verdict";

// Static stats sourced from published research (see PLAN.md frontend features).
const STATIC_STATS = [
  {
    value: "35%",
    label: "of AI chatbot responses contained misinformation",
    source: "NewsGuard, 2025",
  },
  {
    value: "80%",
    label: "of UK adults worry about political misinformation",
    source: "Full Fact, 2026",
  },
  {
    value: "6×",
    label: "faster that false news spreads than the truth",
    source: "MIT / Science, 2018",
  },
];

const VERDICT_ORDER: Verdict[] = [
  "supported",
  "refuted",
  "contested",
  "insufficient_evidence",
];

export function MetricsDashboard({ reloadToken = 0 }: { reloadToken?: number }) {
  const [total, setTotal] = useState<number | null>(null);
  const [breakdown, setBreakdown] = useState<Record<Verdict, number>>({
    supported: 0,
    refuted: 0,
    contested: 0,
    insufficient_evidence: 0,
  });

  useEffect(() => {
    const ctrl = new AbortController();
    getRecentSearches(50, 0, ctrl.signal)
      .then((res) => {
        setTotal(res.total);
        const counts: Record<Verdict, number> = {
          supported: 0,
          refuted: 0,
          contested: 0,
          insufficient_evidence: 0,
        };
        for (const s of res.searches) counts[s.verdict] += 1;
        setBreakdown(counts);
      })
      .catch(() => {
        // API unavailable — show zeroes rather than breaking the page.
        setTotal(0);
      });
    return () => ctrl.abort();
  }, [reloadToken]);

  return (
    <section aria-label="Statistics" className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      {STATIC_STATS.map((stat) => (
        <div
          key={stat.source}
          className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm"
        >
          <p className="text-2xl font-bold text-zinc-900">{stat.value}</p>
          <p className="mt-1 text-xs leading-snug text-zinc-600">{stat.label}</p>
          <p className="mt-2 text-[11px] text-zinc-500">{stat.source}</p>
        </div>
      ))}

      <div className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm">
        <p className="text-2xl font-bold text-zinc-900">{total ?? "—"}</p>
        <p className="mt-1 text-xs leading-snug text-zinc-600">
          claims checked on FactCheck
        </p>
        <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-[11px] text-zinc-500">
          {VERDICT_ORDER.filter((v) => breakdown[v] > 0).map((v) => (
            <span
              key={v}
              className="inline-flex items-center gap-1"
              title={`${breakdown[v]} ${VERDICT_META[v].label}`}
              aria-label={`${breakdown[v]} ${VERDICT_META[v].label}`}
            >
              <span
                className={`h-1.5 w-1.5 rounded-full ${VERDICT_META[v].dot}`}
                aria-hidden
              />
              {breakdown[v]}
            </span>
          ))}
        </div>
      </div>
    </section>
  );
}
