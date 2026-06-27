"""Agent 1: ClaimDecomposer — break a claim into 1-4 verifiable sub-claims."""

from ..lib import gemini

_PROMPT = """You are a fact-checking assistant. Break the following claim into 1 to 4 specific, \
verifiable sub-claims that can each be searched independently on the web.

Claim: "{claim}"

Return ONLY a JSON array of strings — no other text, no markdown, no explanation.
Example: ["sub-claim 1", "sub-claim 2"]

Each sub-claim must be:
- A complete, self-contained statement
- Specific enough to search for directly
- No more than 15 words"""


def decompose(claim: str) -> list[str]:
    """Return 1-4 sub-claims. Falls back to [claim] on any parse failure."""
    try:
        data = gemini.invoke_json(_PROMPT.format(claim=claim))
        if not isinstance(data, list):
            return [claim]
        sub_claims = [s.strip() for s in data if isinstance(s, str) and s.strip()][:4]
        return sub_claims or [claim]
    except Exception:  # noqa: BLE001 — any failure degrades to the whole claim
        return [claim]
