import type { ReactNode } from "react";

// Shared horizontal meter used for confidence and source-credibility bars.
// Pass `progressLabel` to expose it to assistive tech as a progressbar;
// omit it for a purely decorative bar whose value is already shown as text.
export function Meter({
  value,
  label,
  valueLabel,
  trackHeight = "h-2",
  fillClass = "bg-zinc-700",
  captionClass = "text-xs text-zinc-600",
  progressLabel,
  progressValueText,
}: {
  value: number; // 0..1
  label?: ReactNode;
  valueLabel?: ReactNode;
  trackHeight?: string;
  fillClass?: string;
  captionClass?: string;
  progressLabel?: string;
  progressValueText?: string;
}) {
  const pct = Math.round(Math.max(0, Math.min(1, value)) * 100);

  const progressProps = progressLabel
    ? {
        role: "progressbar" as const,
        "aria-label": progressLabel,
        "aria-valuenow": pct,
        "aria-valuemin": 0,
        "aria-valuemax": 100,
        ...(progressValueText ? { "aria-valuetext": progressValueText } : {}),
      }
    : {};

  return (
    <div className="w-full">
      {(label != null || valueLabel != null) && (
        <div className={`mb-1 flex items-center justify-between ${captionClass}`}>
          <span>{label}</span>
          <span>{valueLabel ?? `${pct}%`}</span>
        </div>
      )}
      <div
        className={`${trackHeight} w-full overflow-hidden rounded-full bg-zinc-200`}
      >
        <div
          className={`h-full rounded-full ${fillClass}`}
          style={{ width: `${pct}%` }}
          {...progressProps}
        />
      </div>
    </div>
  );
}
