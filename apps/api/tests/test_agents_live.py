"""Live agent tests (skipped without API keys)."""

from src.agents import claim_decomposer, evidence_retriever, synthesis
from src.lib.types import SourceMode, VerdictEnum

from .conftest import requires_gemini, requires_tavily

_VALID_VERDICTS = {v.value for v in VerdictEnum}


@requires_gemini
def test_decompose_returns_subclaims():
    subs = claim_decomposer.decompose("The US national debt exceeded $35 trillion in 2024")
    assert 1 <= len(subs) <= 4
    assert all(isinstance(s, str) and s for s in subs)


@requires_tavily
def test_retriever_returns_evidence_per_subclaim():
    evidence, _fallback = evidence_retriever.retrieve(
        ["US national debt 2024", "US debt $35 trillion"], SourceMode.flexible
    )
    assert len(evidence) >= 1
    assert all("url" in e and "snippet" in e for e in evidence)


@requires_gemini
def test_synthesize_returns_valid_verdict():
    sources = [
        {
            "url": "https://budget.house.gov/debt",
            "title": "US National Debt Surpasses $35 Trillion",
            "snippet": "The national debt surpassed $35 trillion on July 29, 2024.",
            "credibility_score": 1.0,
            "domain_type": "government",
            "tavily_score": 0.95,
        }
    ]
    result = synthesis.synthesize("The US national debt exceeded $35 trillion in 2024", sources)
    assert result["verdict"] in _VALID_VERDICTS
    assert 0.0 <= result["confidence"] <= 1.0
