"""Agent 2: EvidenceRetriever — Tavily search per sub-claim.

strict mode applies the domain allowlist. If strict yields fewer than 3 unique
sources, it auto-falls back to flexible (flagged), per the Source Mode spec.
"""

from ..lib import tavily
from ..lib.types import SourceMode

MIN_STRICT_SOURCES = 3


def _collect(sub_claims: list[str], mode: SourceMode, seen: set[str]) -> list[dict]:
    results: list[dict] = []
    for sub_claim in sub_claims:
        try:
            hits = tavily.search(sub_claim, mode)
        except Exception:  # noqa: BLE001 — a single failed search shouldn't abort retrieval
            hits = []
        for hit in hits:
            url = hit["url"]
            if url not in seen:
                seen.add(url)
                results.append({**hit, "sub_claim": sub_claim})
    return results


def retrieve(sub_claims: list[str], source_mode: SourceMode) -> tuple[list[dict], bool]:
    """Return (evidence_chunks, source_mode_fallback).

    Each chunk: url, title, snippet, tavily_score, published_date, sub_claim.
    """
    seen: set[str] = set()
    evidence = _collect(sub_claims, source_mode, seen)

    fallback = False
    if source_mode == SourceMode.strict and len(evidence) < MIN_STRICT_SOURCES:
        fallback = True
        evidence += _collect(sub_claims, SourceMode.flexible, seen)

    return evidence, fallback
