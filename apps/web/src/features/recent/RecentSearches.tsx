"use client";

import { useEffect, useState } from "react";

import { VerdictBadge } from "@/features/results/VerdictBadge";
import { getRecentSearches } from "@/lib/api";
import type { RecentSearch, SourceMode } from "@/lib/types";
import { timeAgo } from "@/lib/time";
import { confidenceLabel } from "@/lib/verdict";

const PAGE_SIZE = 10;

export function RecentSearches({
  reloadToken = 0,
  onSelect,
}: {
  reloadToken?: number;
  onSelect: (claim: string, sourceMode: SourceMode) => void;
}) {
  const [items, setItems] = useState<RecentSearch[]>([]);
  const [total, setTotal] = useState(0);
  const [loadingMore, setLoadingMore] = useState(false);
  const [loaded, setLoaded] = useState(false);

  // Reload the first page whenever a new search completes (reloadToken bumps).
  useEffect(() => {
    const ctrl = new AbortController();
    getRecentSearches(PAGE_SIZE, 0, ctrl.signal)
      .then((res) => {
        if (ctrl.signal.aborted) return;
        setTotal(res.total);
        setItems(res.searches);
        setLoaded(true);
      })
      .catch(() => {
        if (ctrl.signal.aborted) return;
        setItems([]);
        setLoaded(true);
      });
    return () => ctrl.abort();
  }, [reloadToken]);

  function loadMore() {
    setLoadingMore(true);
    getRecentSearches(PAGE_SIZE, items.length)
      .then((res) => {
        setTotal(res.total);
        setItems((prev) => [...prev, ...res.searches]);
      })
      .catch(() => {})
      .finally(() => setLoadingMore(false));
  }

  const hasMore = items.length < total;

  return (
    <section aria-label="Recent searches" className="mt-10">
      <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-zinc-500">
        Recent checks
      </h2>

      {loaded && items.length === 0 && (
        <p className="rounded-lg border border-dashed border-zinc-300 p-4 text-sm text-zinc-500">
          No checks yet — be the first to verify a claim.
        </p>
      )}

      <ul className="flex flex-col gap-2">
        {items.map((item) => (
          <li key={item.id}>
            <button
              type="button"
              onClick={() => onSelect(item.claim, item.source_mode)}
              className="flex w-full flex-col gap-1 rounded-lg border border-zinc-200 bg-white p-3 text-left transition-colors hover:border-zinc-300 hover:bg-zinc-50"
            >
              <span className="line-clamp-2 text-sm text-zinc-800">
                {item.claim}
              </span>
              <span className="flex flex-wrap items-center gap-2 text-xs text-zinc-500">
                <VerdictBadge verdict={item.verdict} />
                <span>{confidenceLabel(item.confidence)} confidence</span>
                <span aria-hidden>·</span>
                <span>{timeAgo(item.searched_at)}</span>
              </span>
            </button>
          </li>
        ))}
      </ul>

      {hasMore && (
        <button
          type="button"
          onClick={loadMore}
          disabled={loadingMore}
          className="mt-3 w-full rounded-lg border border-zinc-200 py-2 text-sm font-medium text-zinc-600 transition-colors hover:bg-zinc-50 disabled:opacity-50"
        >
          {loadingMore ? "Loading…" : "Load more"}
        </button>
      )}
    </section>
  );
}
