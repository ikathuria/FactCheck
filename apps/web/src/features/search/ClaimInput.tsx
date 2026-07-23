"use client";

import { useId } from "react";

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
  const textareaId = useId();
  const counterId = useId();

  return (
    <div>
      <label htmlFor={textareaId} className="sr-only">
        Claim to fact-check
      </label>
      <textarea
        id={textareaId}
        aria-describedby={counterId}
        value={value}
        onChange={(e) => onChange(e.target.value.slice(0, MAX))}
        disabled={disabled}
        rows={3}
        placeholder="Enter a claim to fact-check, e.g. “The US national debt exceeded $35 trillion in 2024”"
        className="w-full resize-y rounded-lg border border-zinc-300 bg-white p-3 text-zinc-900 focus:border-zinc-500 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-zinc-700 disabled:opacity-60"
      />
      <div id={counterId} className="mt-1 text-right text-xs text-zinc-600">
        {value.length}/{MAX}
      </div>
    </div>
  );
}

export const CLAIM_MAX_LENGTH = MAX;
