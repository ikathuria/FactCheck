"use client";

import type { SourceMode } from "@/lib/types";

const OPTIONS: { value: SourceMode; label: string; hint: string }[] = [
  { value: "flexible", label: "All sources", hint: "Broadest coverage" },
  { value: "strict", label: "Strict sources", hint: "Gov / academic / major news" },
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
  // Radio-group keyboard pattern: arrow keys move (and change) the selection,
  // and only the checked radio is in the tab order (roving tabindex).
  function onKeyDown(e: React.KeyboardEvent) {
    if (disabled) return;
    if (!["ArrowRight", "ArrowDown", "ArrowLeft", "ArrowUp"].includes(e.key))
      return;
    e.preventDefault();
    const idx = OPTIONS.findIndex((o) => o.value === value);
    const forward = e.key === "ArrowRight" || e.key === "ArrowDown";
    const next = (idx + (forward ? 1 : -1) + OPTIONS.length) % OPTIONS.length;
    onChange(OPTIONS[next].value);
    // Move focus to the newly selected radio (roving tabindex pattern).
    const radios = e.currentTarget.querySelectorAll<HTMLButtonElement>(
      '[role="radio"]',
    );
    radios[next]?.focus();
  }

  return (
    <div
      role="radiogroup"
      aria-label="Source mode"
      onKeyDown={onKeyDown}
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
            tabIndex={active ? 0 : -1}
            disabled={disabled}
            onClick={() => onChange(opt.value)}
            title={opt.hint}
            className={`rounded-md px-3 py-2 text-sm font-medium transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-zinc-700 disabled:opacity-60 ${
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
