export function ReasoningCard({ reasoning }: { reasoning: string }) {
  return (
    <div className="rounded-lg border border-zinc-200 bg-zinc-50 p-4">
      <h3 className="mb-1 text-sm font-semibold text-zinc-700">Reasoning</h3>
      <p className="text-sm leading-relaxed text-zinc-700">{reasoning}</p>
    </div>
  );
}
