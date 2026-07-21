// Presentation metadata for verdicts and domain types.
// Verdicts are never shown as binary TRUE/FALSE (see PROJECT.md decision log).

import type { DomainType, Verdict } from "./types";

export const VERDICT_META: Record<
  Verdict,
  { label: string; classes: string; dot: string }
> = {
  supported: {
    label: "Supported",
    classes: "bg-green-50 text-green-800 border-green-300",
    dot: "bg-green-500",
  },
  refuted: {
    label: "Refuted",
    classes: "bg-red-50 text-red-800 border-red-300",
    dot: "bg-red-500",
  },
  contested: {
    label: "Contested",
    classes: "bg-amber-50 text-amber-800 border-amber-300",
    dot: "bg-amber-500",
  },
  insufficient_evidence: {
    label: "Insufficient evidence",
    classes: "bg-zinc-100 text-zinc-700 border-zinc-300",
    dot: "bg-zinc-400",
  },
};

export const DOMAIN_META: Record<DomainType, { label: string; classes: string }> = {
  government: { label: "Government", classes: "bg-blue-100 text-blue-800" },
  academic: { label: "Academic", classes: "bg-purple-100 text-purple-800" },
  established_news: { label: "News", classes: "bg-teal-100 text-teal-800" },
  other: { label: "Other", classes: "bg-zinc-100 text-zinc-600" },
};

export function confidenceLabel(confidence: number): string {
  if (confidence >= 0.8) return "High";
  if (confidence >= 0.5) return "Moderate";
  if (confidence > 0) return "Low";
  return "None";
}
