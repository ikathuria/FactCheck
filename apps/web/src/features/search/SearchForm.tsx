"use client";

import type { SourceMode } from "@/lib/types";
import { ClaimInput } from "./ClaimInput";
import { SourceModeToggle } from "./SourceModeToggle";

export function SearchForm({
  claim,
  sourceMode,
  onClaimChange,
  onModeChange,
  onSubmit,
  loading = false,
}: {
  claim: string;
  sourceMode: SourceMode;
  onClaimChange: (v: string) => void;
  onModeChange: (v: SourceMode) => void;
  onSubmit: () => void;
  loading?: boolean;
}) {
  const canSubmit = claim.trim().length > 0 && !loading;

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        if (canSubmit) onSubmit();
      }}
      className="flex flex-col gap-3"
    >
      <ClaimInput value={claim} onChange={onClaimChange} disabled={loading} />
      <div className="flex flex-wrap items-center justify-between gap-3">
        <SourceModeToggle
          value={sourceMode}
          onChange={onModeChange}
          disabled={loading}
        />
        <button
          type="submit"
          disabled={!canSubmit}
          className="rounded-lg bg-zinc-900 px-5 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-zinc-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-zinc-700 disabled:cursor-not-allowed disabled:opacity-40"
        >
          {loading ? "Checking…" : "Fact-check"}
        </button>
      </div>
    </form>
  );
}
