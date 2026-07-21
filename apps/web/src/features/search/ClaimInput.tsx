"use client";

const MAX = 500;

export function ClaimInput({
  value,
  onChange,
  disabled,
}: {
  value: string;
  onChange: (v: string) => void;
  disabled?: boolean;
}) {
  return (
    <div>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value.slice(0, MAX))}
        disabled={disabled}
        rows={3}
        placeholder="Enter a claim to fact-check, e.g. “The US national debt exceeded $35 trillion in 2024”"
        className="w-full resize-y rounded-lg border border-zinc-300 bg-white p-3 text-zinc-900 outline-none focus:border-zinc-500 focus:ring-1 focus:ring-zinc-500 disabled:opacity-60"
      />
      <div className="mt-1 text-right text-xs text-zinc-400">
        {value.length}/{MAX}
      </div>
    </div>
  );
}

export const CLAIM_MAX_LENGTH = MAX;
