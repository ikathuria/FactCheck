"use client";

import { useCallback, useRef, useState } from "react";

import { MetricsDashboard } from "@/features/metrics/MetricsDashboard";
import { RecentSearches } from "@/features/recent/RecentSearches";
import { ResultsPanel } from "@/features/results/ResultsPanel";
import { SearchForm } from "@/features/search/SearchForm";
import { SearchProgress } from "@/features/search/SearchProgress";
import { ApiError, verifyClaim } from "@/lib/api";
import type { SourceMode, VerifyResponse } from "@/lib/types";

type Status = "idle" | "loading" | "done" | "error";

export default function Home() {
  const [claim, setClaim] = useState("");
  const [sourceMode, setSourceMode] = useState<SourceMode>("flexible");
  const [status, setStatus] = useState<Status>("idle");
  const [result, setResult] = useState<VerifyResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState("");
  const [reloadToken, setReloadToken] = useState(0);
  const abortRef = useRef<AbortController | null>(null);

  const runSearch = useCallback(async (text: string, mode: SourceMode) => {
    const trimmed = text.trim();
    if (!trimmed) return;

    abortRef.current?.abort();
    const ctrl = new AbortController();
    abortRef.current = ctrl;

    setClaim(trimmed);
    setSourceMode(mode);
    setStatus("loading");
    setErrorMsg("");
    setResult(null);

    try {
      const res = await verifyClaim(trimmed, mode, ctrl.signal);
      if (ctrl.signal.aborted) return;
      setResult(res);
      setStatus("done");
      setReloadToken((t) => t + 1);
    } catch (err) {
      if (ctrl.signal.aborted) return;
      setErrorMsg(
        err instanceof ApiError
          ? err.message
          : "Couldn't reach the fact-check service. Is the API running?",
      );
      setStatus("error");
    }
  }, []);

  return (
    <main className="mx-auto w-full max-w-3xl flex-1 px-4 py-10 sm:py-14">
      <header className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight text-zinc-900">
          FactCheck
        </h1>
        <p className="mt-1 text-zinc-600">
          Verify any claim against credibility-scored sources. You get a
          calibrated verdict, confidence, reasoning, and the evidence — never a
          bare true/false.
        </p>
      </header>

      <MetricsDashboard reloadToken={reloadToken} />

      <div className="mt-8">
        <SearchForm
          claim={claim}
          sourceMode={sourceMode}
          onClaimChange={setClaim}
          onModeChange={setSourceMode}
          onSubmit={() => runSearch(claim, sourceMode)}
          loading={status === "loading"}
        />
      </div>

      {status === "loading" && <SearchProgress />}

      {status === "error" && (
        <p
          role="alert"
          className="mt-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800"
        >
          {errorMsg}
        </p>
      )}

      {status === "done" && result && (
        <div className="mt-6">
          <ResultsPanel result={result} />
        </div>
      )}

      <RecentSearches reloadToken={reloadToken} onSelect={runSearch} />
    </main>
  );
}
