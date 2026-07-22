"use client";

import { useEffect, useState } from "react";

// Mirrors the backend pipeline stages. The backend is a single POST (no
// streaming), so these advance on a timer to reassure the user during the wait
// rather than reflecting real per-stage progress.
const STEPS = [
  "Decomposing the claim…",
  "Searching sources…",
  "Scoring source credibility…",
  "Synthesizing a verdict…",
  "Reviewing for overconfidence…",
];

export function SearchProgress() {
  const [step, setStep] = useState(0);

  useEffect(() => {
    const id = setInterval(() => {
      setStep((s) => Math.min(s + 1, STEPS.length - 1));
    }, 1500);
    return () => clearInterval(id);
  }, []);

  return (
    <div
      data-testid="search-progress"
      role="status"
      aria-live="polite"
      className="mt-6 flex items-center gap-3 rounded-xl border border-zinc-200 bg-white p-5 text-sm text-zinc-600 shadow-sm"
    >
      <span
        className="h-4 w-4 animate-spin rounded-full border-2 border-zinc-300 border-t-zinc-700"
        aria-hidden
      />
      <span>{STEPS[step]}</span>
    </div>
  );
}
