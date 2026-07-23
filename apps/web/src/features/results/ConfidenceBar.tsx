import { Meter } from "@/components/Meter";
import { confidenceLabel } from "@/lib/verdict";

export function ConfidenceBar({ confidence }: { confidence: number }) {
  const pct = Math.round(Math.max(0, Math.min(1, confidence)) * 100);
  return (
    <div data-testid="confidence-bar">
      <Meter
        value={confidence}
        label={`Confidence: ${confidenceLabel(confidence)}`}
        valueLabel={`${pct}%`}
        progressLabel="Confidence"
        progressValueText={`${confidenceLabel(confidence)}, ${pct}%`}
      />
    </div>
  );
}
