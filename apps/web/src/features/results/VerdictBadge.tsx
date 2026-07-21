import type { Verdict } from "@/lib/types";
import { VERDICT_META } from "@/lib/verdict";

export function VerdictBadge({ verdict }: { verdict: Verdict }) {
  const meta = VERDICT_META[verdict];
  return (
    <span
      data-testid="verdict-badge"
      data-verdict={verdict}
      className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-sm font-semibold ${meta.classes}`}
    >
      <span className={`h-2 w-2 rounded-full ${meta.dot}`} aria-hidden />
      {meta.label}
    </span>
  );
}
