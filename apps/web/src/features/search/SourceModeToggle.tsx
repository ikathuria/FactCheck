"use client";

import type { SourceMode } from "@/lib/types";

const OPTIONS: { value: SourceMode; label: string; hint: string }[] = [
  { value: "flexible", label: "All sources", hint: "Broadest coverage" },
  { value: "strict", label: "Strict", hint: "Gov / academic / major news" },
];

export function SourceModeToggle({
  value,
  onChange,
  disabled,
}: {
  value: SourceMode;
  onChange: (v: SourceMode) => void;
  disabled?: boolean;
}) {
  return (
    <div
      role="radiogroup"
      aria-label="Source mode"
      className="inline-flex rounded-lg border border-zinc-300 bg-zinc-50 p-1"
    >
      {OPTIONS.map((opt) => {
        const active = value === opt.value;
        return (
          <button
            key={opt.value}
            type="button"
            role="radio"
            aria-checked={active}
            disabled={disabled}
            onClick={() => onChange(opt.value)}
            title={opt.hint}
            className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors disabled:opacity-60 ${
              active
                ? "bg-white text-zinc-900 shadow-sm"
                : "text-zinc-500 hover:text-zinc-700"
            }`}
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}
