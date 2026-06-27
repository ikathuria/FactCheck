"""Agent 5: CriticAgent — adversarial review of the synthesis verdict.

Carries the Milestone 0 fix: the critic judges ONLY the provided evidence and
must never use its own training-cutoff world-knowledge (which previously made it
override a true, gov-sourced "Trump won 2024" verdict). See docs/02-spike-results.md.
"""

import time

from ..lib import gemini
from ..lib.types import VerdictEnum

_VALID = {v.value for v in VerdictEnum}
CONFIDENCE_FLOOR = 0.5

_PROMPT = """You are an adversarial critic reviewing a fact-check. Your job: catch overconfident or
unsupported verdicts by checking them AGAINST THE PROVIDED EVIDENCE ONLY.

Today's date is {today}.

CRITICAL RULES ABOUT YOUR OWN KNOWLEDGE (read carefully):
- Judge ONLY whether the provided evidence supports the synthesis verdict. Do NOT use your own
  memory of world events, dates, election results, statistics, or "what has or hasn't happened."
- Your training data may be OLDER than today's date. Events you believe are in the "future" may
  have already occurred. NEVER reject evidence because you think the event hasn't happened yet.
- NEVER call a source "fabricated," "fake," or "future-dated" based on your own prior. The evidence
  was retrieved live from the web today; treat it as real.
- Authoritative sources (domain_type "government" or "academic", credibility >= 0.85) are ground
  truth unless they internally contradict each other. If they support the claim, the verdict is
  "supported" even if that surprises you.

CLAIM: "{claim}"

SYNTHESIS VERDICT: {verdict}
SYNTHESIS CONFIDENCE: {confidence:.2f}
SYNTHESIS REASONING: {reasoning}

KEY EVIDENCE (retrieved live today):
{evidence}

Respond with ONLY valid JSON (no markdown):
{{
  "verdict": "supported" | "refuted" | "contested" | "insufficient_evidence",
  "confidence": <float 0.0 to 1.0>,
  "reasoning": "<2-4 sentences — explain if you changed anything and why, citing the evidence>"
}}

Override rules (apply strictly, based ONLY on the evidence above):
1. If the evidence does NOT clearly support the verdict -> lower confidence or change the verdict
2. If sources genuinely contradict each other -> verdict MUST be "contested"
3. If evidence is absent or thin -> verdict MUST be "insufficient_evidence"
4. If confidence < 0.5 -> verdict MUST be "insufficient_evidence"
5. If the synthesis is well-supported by the evidence -> KEEP it. Your job is to catch errors
   against the evidence, not to inject doubt from your own knowledge."""


def _format_evidence(sources: list[dict], limit: int = 6) -> str:
    if not sources:
        return "(No evidence)"
    lines = []
    for i, s in enumerate(sources[:limit], 1):
        domain_type = getattr(s["domain_type"], "value", s["domain_type"])
        lines.append(
            f"[{i}] ({domain_type}, credibility={s['credibility_score']}) {s['title']}\n"
            f"{s['snippet'][:400]}"
        )
    return "\n".join(lines)


def critique(
    claim: str,
    verdict: str,
    confidence: float,
    reasoning: str,
    sources: list[dict],
) -> dict:
    """Return the final {verdict, confidence, reasoning} after adversarial review."""
    # Hard guard: confidence below floor resolves to insufficient_evidence without an LLM call.
    if confidence < CONFIDENCE_FLOOR and verdict != VerdictEnum.insufficient_evidence.value:
        return {
            "verdict": VerdictEnum.insufficient_evidence.value,
            "confidence": confidence,
            "reasoning": f"[CriticAgent: confidence below threshold] {reasoning}",
        }

    prompt = _PROMPT.format(
        today=time.strftime("%Y-%m-%d"),
        claim=claim,
        verdict=verdict,
        confidence=confidence,
        reasoning=reasoning,
        evidence=_format_evidence(sources),
    )
    try:
        data = gemini.invoke_json(prompt)
        final_verdict = data.get("verdict", verdict)
        final_confidence = float(data.get("confidence", confidence))
        final_reasoning = data.get("reasoning", reasoning)
    except Exception:  # noqa: BLE001 — keep synthesis output if the critic call fails
        final_verdict, final_confidence, final_reasoning = verdict, confidence, reasoning

    if final_verdict not in _VALID:
        final_verdict = VerdictEnum.insufficient_evidence.value
    final_confidence = max(0.0, min(1.0, final_confidence))

    # Enforce the confidence floor on the critic's own output too.
    if final_confidence < CONFIDENCE_FLOOR:
        final_verdict = VerdictEnum.insufficient_evidence.value

    return {"verdict": final_verdict, "confidence": final_confidence, "reasoning": final_reasoning}
