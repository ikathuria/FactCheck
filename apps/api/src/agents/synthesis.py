"""Agent 4: SynthesisAgent — produce verdict + confidence + reasoning from evidence."""

from ..lib import gemini
from ..lib.types import VerdictEnum

_VALID = {v.value for v in VerdictEnum}

_PROMPT = """You are a careful, calibrated fact-checker. Analyze the following claim against the \
provided evidence.

CLAIM: "{claim}"

EVIDENCE:
{evidence}

Respond with ONLY valid JSON (no markdown, no explanation) in this exact format:
{{
  "verdict": "supported" | "refuted" | "contested" | "insufficient_evidence",
  "confidence": <float 0.0 to 1.0>,
  "reasoning": "<2-4 sentence plain English explanation citing the evidence>"
}}

Verdict definitions:
- "supported": evidence clearly backs the claim
- "refuted": evidence clearly contradicts the claim
- "contested": evidence is mixed or sources directly conflict
- "insufficient_evidence": evidence is thin, absent, or too ambiguous to judge

IMPORTANT rules:
- If evidence is thin, vague, or absent -> verdict MUST be "insufficient_evidence"
- Confidence < 0.5 -> verdict SHOULD be "insufficient_evidence"
- Never output TRUE/FALSE
- Base confidence strictly on evidence quality, not claim plausibility"""


def _format_evidence(sources: list[dict], limit: int = 8) -> str:
    if not sources:
        return "(No evidence found)"
    lines = []
    for i, s in enumerate(sources[:limit], 1):
        domain_type = getattr(s["domain_type"], "value", s["domain_type"])
        lines.append(
            f"[{i}] {s['title']} ({domain_type}, credibility={s['credibility_score']})\n"
            f"URL: {s['url']}\n"
            f"Snippet: {s['snippet'][:600]}"
        )
    return "\n\n".join(lines)


def synthesize(claim: str, sources: list[dict]) -> dict:
    """Return {verdict, confidence, reasoning}. Degrades to insufficient_evidence on failure."""
    prompt = _PROMPT.format(claim=claim, evidence=_format_evidence(sources))
    try:
        data = gemini.invoke_json(prompt)
        verdict = data.get("verdict", "insufficient_evidence")
        confidence = float(data.get("confidence", 0.0))
        reasoning = data.get("reasoning", "")
    except Exception:  # noqa: BLE001
        return {
            "verdict": "insufficient_evidence",
            "confidence": 0.0,
            "reasoning": "Could not parse synthesis output.",
        }

    if verdict not in _VALID:
        verdict = "insufficient_evidence"
    confidence = max(0.0, min(1.0, confidence))
    return {"verdict": verdict, "confidence": confidence, "reasoning": reasoning}
