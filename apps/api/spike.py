"""
Milestone 0 spike: 5-agent LangGraph fact-checking pipeline.

Usage:
    python apps/api/spike.py "H1B visa cap was doubled in 2024"
    python apps/api/spike.py "claim text" --mode flexible   (default: flexible)
    python apps/api/spike.py "claim text" --mode strict

Requires a .env file at apps/api/.env (or set env vars directly):
    GEMINI_API_KEY=...
    TAVILY_API_KEY=...
"""

import sys
import os
import json
import re
import argparse
from pathlib import Path
from typing import TypedDict

# Load .env from apps/api/.env or repo root, whichever exists
from dotenv import load_dotenv
for env_file in (Path(__file__).parent / ".env", Path(__file__).parents[2] / ".env"):
    if env_file.exists():
        load_dotenv(env_file)
        break

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")

if not GEMINI_API_KEY or not TAVILY_API_KEY:
    print("ERROR: Set GEMINI_API_KEY and TAVILY_API_KEY in apps/api/.env or environment.")
    sys.exit(1)

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END
from tavily import TavilyClient

# ---------------------------------------------------------------------------
# Clients
# ---------------------------------------------------------------------------

import time

# Model is overridable via GEMINI_MODEL env var or --model CLI flag.
# Note: gemini-2.5-flash-lite free-tier daily quota is only 20 requests/day,
# which is exhausted quickly (3+ LLM calls per claim). gemini-2.0-flash has a
# more generous free-tier daily limit — useful for running the spike batch.
DEFAULT_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash-lite")

llm = ChatGoogleGenerativeAI(
    model=DEFAULT_MODEL,
    google_api_key=GEMINI_API_KEY,
    temperature=0.1,
)

tavily = TavilyClient(api_key=TAVILY_API_KEY)


def llm_invoke(prompt: str, max_attempts: int = 5) -> str:
    """Call Gemini with exponential backoff on transient 429/503 errors."""
    for attempt in range(max_attempts):
        try:
            return llm.invoke([HumanMessage(content=prompt)]).content.strip()
        except Exception as e:
            msg = str(e)
            transient = "503" in msg or "UNAVAILABLE" in msg or "429" in msg or "RESOURCE_EXHAUSTED" in msg
            if transient and attempt < max_attempts - 1:
                wait = 2 ** attempt
                print(f"  [llm] transient error ({msg[:60]}...) — retry in {wait}s")
                time.sleep(wait)
                continue
            raise

# ---------------------------------------------------------------------------
# Domain scoring
# ---------------------------------------------------------------------------

GOVERNMENT_DOMAINS = {
    "who.int", "cdc.gov", "nih.gov", "whitehouse.gov", "usa.gov",
    "congress.gov", "senate.gov", "hhs.gov", "dol.gov", "uscis.gov",
}
NEWS_DOMAINS = {
    "apnews.com", "reuters.com", "bbc.com", "bbc.co.uk",
    "npr.org", "pbs.org", "theguardian.com",
}
STRICT_INCLUDE_DOMAINS = list(GOVERNMENT_DOMAINS | NEWS_DOMAINS) + []

# Patterns for gov/edu/academic
GOV_PATTERNS = [".gov", ".gc.ca"]
EDU_PATTERNS = [".edu", ".ac.uk", ".ac."]


def score_domain(url: str) -> tuple[float, str]:
    """Return (credibility_score, domain_type) for a URL."""
    try:
        from urllib.parse import urlparse
        domain = urlparse(url).netloc.lower()
    except Exception:
        domain = url.lower()

    if any(domain == d or domain.endswith("." + d) for d in GOVERNMENT_DOMAINS):
        return 1.0, "government"
    if any(p in domain for p in GOV_PATTERNS):
        return 1.0, "government"
    if any(p in domain for p in EDU_PATTERNS):
        return 0.85, "academic"
    if any(domain == d or domain.endswith("." + d) for d in NEWS_DOMAINS):
        return 0.7, "established_news"
    return 0.4, "other"


# ---------------------------------------------------------------------------
# Shared pipeline state
# ---------------------------------------------------------------------------

class PipelineState(TypedDict):
    claim: str
    source_mode: str
    sub_claims: list[str]
    raw_evidence: list[dict]      # list of Tavily result dicts
    scored_sources: list[dict]    # with credibility_score + domain_type added
    verdict: str
    confidence: float
    reasoning: str


# ---------------------------------------------------------------------------
# Agent 1: ClaimDecomposer
# ---------------------------------------------------------------------------

def claim_decomposer(state: PipelineState) -> dict:
    claim = state["claim"]
    prompt = f"""You are a fact-checking assistant. Break the following claim into 1 to 4 specific, verifiable sub-claims that can each be searched independently on the web.

Claim: "{claim}"

Return ONLY a JSON array of strings — no other text, no markdown, no explanation.
Example: ["sub-claim 1", "sub-claim 2"]

Each sub-claim must be:
- A complete, self-contained statement
- Specific enough to search for directly
- No more than 15 words"""

    text = llm_invoke(prompt)

    # Parse JSON array from response
    try:
        # Strip markdown code fences if present
        text = re.sub(r"```(?:json)?", "", text).strip().rstrip("`").strip()
        sub_claims = json.loads(text)
        if not isinstance(sub_claims, list):
            sub_claims = [claim]
    except Exception:
        # Fallback: treat the original claim as the only sub-claim
        sub_claims = [claim]

    # Ensure at least 1, at most 4
    sub_claims = [s for s in sub_claims if isinstance(s, str) and s.strip()][:4]
    if not sub_claims:
        sub_claims = [claim]

    print(f"  [ClaimDecomposer] -> {len(sub_claims)} sub-claim(s): {sub_claims}")
    return {"sub_claims": sub_claims}


# ---------------------------------------------------------------------------
# Agent 2: EvidenceRetriever
# ---------------------------------------------------------------------------

def evidence_retriever(state: PipelineState) -> dict:
    sub_claims = state["sub_claims"]
    source_mode = state["source_mode"]
    all_results: list[dict] = []
    seen_urls: set[str] = set()

    for sub_claim in sub_claims:
        search_kwargs: dict = {
            "query": sub_claim,
            "search_depth": "advanced",
            "max_results": 5,
        }

        if source_mode == "strict":
            search_kwargs["include_domains"] = STRICT_INCLUDE_DOMAINS

        try:
            response = tavily.search(**search_kwargs)
            results = response.get("results", [])
        except Exception as e:
            print(f"  [EvidenceRetriever] Tavily error for '{sub_claim}': {e}")
            results = []

        # Deduplicate by URL across sub-claims
        for r in results:
            url = r.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                all_results.append({
                    "url": url,
                    "title": r.get("title", ""),
                    "snippet": r.get("content", ""),
                    "tavily_score": r.get("score", 0.0),
                    "published_date": r.get("published_date"),
                    "sub_claim": sub_claim,
                })

    # Strict mode fallback: if fewer than 3 sources, re-run flexible
    if source_mode == "strict" and len(all_results) < 3:
        print("  [EvidenceRetriever] Strict mode returned < 3 sources — falling back to flexible")
        for sub_claim in sub_claims:
            try:
                response = tavily.search(
                    query=sub_claim,
                    search_depth="advanced",
                    max_results=5,
                )
                for r in response.get("results", []):
                    url = r.get("url", "")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        all_results.append({
                            "url": url,
                            "title": r.get("title", ""),
                            "snippet": r.get("content", ""),
                            "tavily_score": r.get("score", 0.0),
                            "published_date": r.get("published_date"),
                            "sub_claim": sub_claim,
                        })
            except Exception as e:
                print(f"  [EvidenceRetriever] Flexible fallback error: {e}")

    print(f"  [EvidenceRetriever] -> {len(all_results)} evidence chunk(s)")
    return {"raw_evidence": all_results}


# ---------------------------------------------------------------------------
# Agent 3: SourceScorer
# ---------------------------------------------------------------------------

def source_scorer(state: PipelineState) -> dict:
    evidence = state["raw_evidence"]
    scored: list[dict] = []

    for item in evidence:
        score, domain_type = score_domain(item["url"])
        if score >= 0.4:  # filter threshold
            scored.append({
                **item,
                "credibility_score": score,
                "domain_type": domain_type,
            })

    # Sort by credibility, then Tavily score
    scored.sort(key=lambda x: (x["credibility_score"], x["tavily_score"]), reverse=True)

    print(f"  [SourceScorer] -> {len(scored)} scored source(s) (filtered from {len(evidence)})")
    return {"scored_sources": scored}


# ---------------------------------------------------------------------------
# Agent 4: SynthesisAgent
# ---------------------------------------------------------------------------

def synthesis_agent(state: PipelineState) -> dict:
    claim = state["claim"]
    sources = state["scored_sources"]

    # Build evidence text (top 8 sources)
    evidence_text = ""
    for i, s in enumerate(sources[:8], 1):
        evidence_text += (
            f"\n[{i}] {s['title']} ({s['domain_type']}, credibility={s['credibility_score']})\n"
            f"URL: {s['url']}\n"
            f"Snippet: {s['snippet'][:600]}\n"
        )

    if not evidence_text:
        evidence_text = "(No evidence found)"

    prompt = f"""You are a careful, calibrated fact-checker. Analyze the following claim against the provided evidence.

CLAIM: "{claim}"

EVIDENCE:
{evidence_text}

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

    text = llm_invoke(prompt)

    try:
        text = re.sub(r"```(?:json)?", "", text).strip().rstrip("`").strip()
        data = json.loads(text)
        verdict = data.get("verdict", "insufficient_evidence")
        confidence = float(data.get("confidence", 0.0))
        reasoning = data.get("reasoning", "")
    except Exception as e:
        print(f"  [SynthesisAgent] Parse error: {e} — defaulting to insufficient_evidence")
        verdict = "insufficient_evidence"
        confidence = 0.0
        reasoning = "Could not parse synthesis output."

    # Enforce valid verdict enum
    valid_verdicts = {"supported", "refuted", "contested", "insufficient_evidence"}
    if verdict not in valid_verdicts:
        verdict = "insufficient_evidence"

    print(f"  [SynthesisAgent] -> verdict={verdict}, confidence={confidence:.2f}")
    return {"verdict": verdict, "confidence": confidence, "reasoning": reasoning}


# ---------------------------------------------------------------------------
# Agent 5: CriticAgent
# ---------------------------------------------------------------------------

def critic_agent(state: PipelineState) -> dict:
    claim = state["claim"]
    verdict = state["verdict"]
    confidence = state["confidence"]
    reasoning = state["reasoning"]
    sources = state["scored_sources"]

    # Hard override: confidence < 0.5 -> insufficient_evidence
    if confidence < 0.5 and verdict not in ("insufficient_evidence",):
        print(f"  [CriticAgent] Confidence {confidence:.2f} < 0.5 — overriding to insufficient_evidence")
        return {
            "verdict": "insufficient_evidence",
            "confidence": confidence,
            "reasoning": f"[CriticAgent override: confidence below threshold] {reasoning}",
        }

    evidence_text = ""
    for i, s in enumerate(sources[:6], 1):
        evidence_text += (
            f"\n[{i}] ({s['domain_type']}, credibility={s['credibility_score']}) "
            f"{s['title']}\n{s['snippet'][:400]}"
        )

    today = time.strftime("%Y-%m-%d")

    prompt = f"""You are an adversarial critic reviewing a fact-check. Your job: catch overconfident or
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
{evidence_text if evidence_text else "(No evidence)"}

Respond with ONLY valid JSON (no markdown):
{{
  "verdict": "supported" | "refuted" | "contested" | "insufficient_evidence",
  "confidence": <float 0.0 to 1.0>,
  "reasoning": "<2-4 sentences — explain if you changed anything and why, citing the evidence>"
}}

Override rules (apply strictly, based ONLY on the evidence above):
1. If the evidence does NOT clearly support the synthesis verdict -> lower confidence or change verdict
2. If sources genuinely contradict each other -> verdict MUST be "contested"
3. If evidence is absent or thin -> verdict MUST be "insufficient_evidence"
4. If confidence < 0.5 -> verdict MUST be "insufficient_evidence"
5. If the synthesis is well-supported by the evidence -> KEEP it. Your job is to catch errors against
   the evidence, not to inject doubt from your own knowledge."""

    text = llm_invoke(prompt)

    try:
        text = re.sub(r"```(?:json)?", "", text).strip().rstrip("`").strip()
        data = json.loads(text)
        final_verdict = data.get("verdict", verdict)
        final_confidence = float(data.get("confidence", confidence))
        final_reasoning = data.get("reasoning", reasoning)
    except Exception as e:
        print(f"  [CriticAgent] Parse error: {e} — keeping synthesis output")
        final_verdict = verdict
        final_confidence = confidence
        final_reasoning = reasoning

    valid_verdicts = {"supported", "refuted", "contested", "insufficient_evidence"}
    if final_verdict not in valid_verdicts:
        final_verdict = "insufficient_evidence"

    # Enforce confidence < 0.5 rule
    if final_confidence < 0.5:
        final_verdict = "insufficient_evidence"

    print(f"  [CriticAgent] -> verdict={final_verdict}, confidence={final_confidence:.2f}")
    return {"verdict": final_verdict, "confidence": final_confidence, "reasoning": final_reasoning}


# ---------------------------------------------------------------------------
# Build LangGraph pipeline
# ---------------------------------------------------------------------------

def build_pipeline() -> object:
    builder: StateGraph = StateGraph(PipelineState)

    builder.add_node("decomposer", claim_decomposer)
    builder.add_node("retriever", evidence_retriever)
    builder.add_node("scorer", source_scorer)
    builder.add_node("synthesizer", synthesis_agent)
    builder.add_node("critic", critic_agent)

    builder.add_edge(START, "decomposer")
    builder.add_edge("decomposer", "retriever")
    builder.add_edge("retriever", "scorer")
    builder.add_edge("scorer", "synthesizer")
    builder.add_edge("synthesizer", "critic")
    builder.add_edge("critic", END)

    return builder.compile()


# ---------------------------------------------------------------------------
# Run pipeline on a claim
# ---------------------------------------------------------------------------

def run(claim: str, source_mode: str = "flexible") -> dict:
    pipeline = build_pipeline()

    initial_state: PipelineState = {
        "claim": claim,
        "source_mode": source_mode,
        "sub_claims": [],
        "raw_evidence": [],
        "scored_sources": [],
        "verdict": "",
        "confidence": 0.0,
        "reasoning": "",
    }

    final_state = pipeline.invoke(initial_state)

    # Build structured output
    sources_out = [
        {
            "url": s["url"],
            "title": s["title"],
            "snippet": s["snippet"][:300],
            "credibility_score": s["credibility_score"],
            "domain_type": s["domain_type"],
        }
        for s in final_state["scored_sources"][:8]
    ]

    return {
        "claim": claim,
        "source_mode": source_mode,
        "verdict": final_state["verdict"],
        "confidence": round(final_state["confidence"], 3),
        "reasoning": final_state["reasoning"],
        "sub_claims": final_state["sub_claims"],
        "sources": sources_out,
    }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FactCheck spike — 5-agent LangGraph pipeline")
    parser.add_argument("claim", help="The claim to fact-check")
    parser.add_argument(
        "--mode",
        choices=["flexible", "strict"],
        default="flexible",
        help="Source mode: flexible (all sources) or strict (gov/academic/established news only)",
    )
    args = parser.parse_args()

    print(f"\nFact-checking: \"{args.claim}\"")
    print(f"Source mode: {args.mode}")
    print("-" * 60)

    result = run(args.claim, args.mode)

    print("\n" + "=" * 60)
    print("RESULT")
    print("=" * 60)
    print(json.dumps(result, indent=2))
