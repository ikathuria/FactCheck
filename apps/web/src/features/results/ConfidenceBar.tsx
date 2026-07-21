import { confidenceLabel } from "@/lib/verdict";

export function ConfidenceBar({ confidence }: { confidence: number }) {
  const pct = Math.round(Math.max(0, Math.min(1, confidence)) * 100);
  return (
    <div data-testid="confidence-bar" className="w-full">
      <div className="mb-1 flex items-center justify-between text-xs text-zinc-600">
        <span>Confidence: {confidenceLabel(confidence)}</span>
        <span>{pct}%</span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-zinc-200">
        <div
          className="h-full rounded-full bg-zinc-700 transition-all"
          style={{ width: `${pct}%` }}
          role="progressbar"
          aria-valuenow={pct}
          aria-valuemin={0}
          aria-valuemax={100}
        />
      </div>
    </div>
  );
}
