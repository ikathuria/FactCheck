from src.agents import critic
from src.lib.types import VerdictEnum

from .conftest import requires_gemini


def test_low_confidence_overrides_to_insufficient_no_llm():
    """Confidence below the floor resolves deterministically — no LLM call needed."""
    result = critic.critique(
        claim="X happened",
        verdict=VerdictEnum.supported.value,
        confidence=0.3,
        reasoning="weak",
        sources=[],
    )
    assert result["verdict"] == VerdictEnum.insufficient_evidence.value


@requires_gemini
def test_contested_on_conflicting_evidence():
    sources = [
        {
            "url": "https://a.gov/study",
            "title": "Study A finds strong positive effect",
            "snippet": "Our randomized trial shows X clearly causes Y with high significance.",
            "credibility_score": 1.0,
            "domain_type": "government",
            "tavily_score": 0.9,
        },
        {
            "url": "https://b.edu/study",
            "title": "Study B finds no effect",
            "snippet": "Our larger replication found no evidence that X causes Y at all.",
            "credibility_score": 0.85,
            "domain_type": "academic",
            "tavily_score": 0.9,
        },
    ]
    result = critic.critique(
        claim="X causes Y",
        verdict=VerdictEnum.supported.value,
        confidence=0.8,
        reasoning="Study A supports it.",
        sources=sources,
    )
    assert result["verdict"] in {
        VerdictEnum.contested.value,
        VerdictEnum.insufficient_evidence.value,
    }
