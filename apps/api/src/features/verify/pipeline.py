"""LangGraph 5-agent pipeline orchestration.

START -> decomposer -> retriever -> scorer -> synthesizer -> critic -> END

Each node reads from and writes to a shared TypedDict state (the Sift pattern).
`run()` returns a fully-populated VerifyResponse (cache fields left unset here;
the cache layer fills them in Milestone 3).
"""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from ...agents import (
    claim_decomposer,
    critic,
    evidence_retriever,
    source_scorer,
    synthesis,
)
from ...lib.types import Source, SourceMode, VerdictEnum, VerifyResponse


class PipelineState(TypedDict):
    claim: str
    source_mode: SourceMode
    sub_claims: list[str]
    raw_evidence: list[dict]
    scored_sources: list[dict]
    source_mode_fallback: bool
    verdict: str
    confidence: float
    reasoning: str


def _decomposer(state: PipelineState) -> dict:
    return {"sub_claims": claim_decomposer.decompose(state["claim"])}


def _retriever(state: PipelineState) -> dict:
    evidence, fallback = evidence_retriever.retrieve(state["sub_claims"], state["source_mode"])
    return {"raw_evidence": evidence, "source_mode_fallback": fallback}


def _scorer(state: PipelineState) -> dict:
    return {"scored_sources": source_scorer.score(state["raw_evidence"])}


def _synthesizer(state: PipelineState) -> dict:
    return synthesis.synthesize(state["claim"], state["scored_sources"])


def _critic(state: PipelineState) -> dict:
    return critic.critique(
        claim=state["claim"],
        verdict=state["verdict"],
        confidence=state["confidence"],
        reasoning=state["reasoning"],
        sources=state["scored_sources"],
    )


def build_graph():
    """Compile and return the LangGraph pipeline."""
    builder = StateGraph(PipelineState)
    builder.add_node("decomposer", _decomposer)
    builder.add_node("retriever", _retriever)
    builder.add_node("scorer", _scorer)
    builder.add_node("synthesizer", _synthesizer)
    builder.add_node("critic", _critic)

    builder.add_edge(START, "decomposer")
    builder.add_edge("decomposer", "retriever")
    builder.add_edge("retriever", "scorer")
    builder.add_edge("scorer", "synthesizer")
    builder.add_edge("synthesizer", "critic")
    builder.add_edge("critic", END)
    return builder.compile()


_graph = None


def _get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


def run(claim: str, source_mode: SourceMode = SourceMode.flexible) -> VerifyResponse:
    """Run the full pipeline and return a VerifyResponse (cache fields unset)."""
    initial: PipelineState = {
        "claim": claim,
        "source_mode": source_mode,
        "sub_claims": [],
        "raw_evidence": [],
        "scored_sources": [],
        "source_mode_fallback": False,
        "verdict": "",
        "confidence": 0.0,
        "reasoning": "",
    }
    final = _get_graph().invoke(initial)

    sources = [
        Source(
            url=s["url"],
            title=s["title"],
            snippet=s["snippet"][:300],
            credibility_score=s["credibility_score"],
            domain_type=s["domain_type"],
        )
        for s in final["scored_sources"][:8]
    ]

    return VerifyResponse(
        claim=claim,
        verdict=VerdictEnum(final["verdict"]),
        confidence=round(final["confidence"], 3),
        reasoning=final["reasoning"],
        sources=sources,
        sub_claims=final["sub_claims"],
        source_mode=source_mode,
        source_mode_fallback=final["source_mode_fallback"],
    )
