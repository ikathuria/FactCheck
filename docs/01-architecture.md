# Architecture

## Request / Data Flow

```
User (Next.js)
  │ POST /verify { claim, source_mode }
  ▼
FastAPI (Render)
  │ Cache key: SHA-256("{claim.lower().strip()}:{source_mode}")
  ├─ Redis HIT → return VerifyResponse { cached: true }
  └─ Redis MISS
       │
       ▼
  LangGraph pipeline (5 agents, sequential)
       │
       ├─ ClaimDecomposer   → 1–4 verifiable sub-claims
       ├─ EvidenceRetriever → Tavily search per sub-claim (strict/flexible filter)
       ├─ SourceScorer      → credibility scores; filter < 0.4
       ├─ SynthesisAgent    → Gemini: verdict + confidence + reasoning
       └─ CriticAgent       → Gemini: override if confidence < 0.5 or evidence contradicts
       │
       ▼
  Store → Redis (TTL 7d) + Supabase `searches` row
       │
       ▼
  return VerifyResponse { cached: false }
```

---

## Sift Reuse Notes

Source: https://dev.to/ashg2099/i-built-an-open-source-multi-agent-fact-checker-heres-how-it-works-5eah  
Studied: 2026-06-26

### What Sift uses (5 agents)

| Sift Agent | Role | Our Analog |
|---|---|---|
| Claim Extractor | Extract typed list of claims from raw text | ClaimDecomposer (sub-claims from a single input claim) |
| Evidence Hunter | HyDE retrieval (pgvector) + Tavily live web | EvidenceRetriever (Tavily only — no pre-indexed embeddings; real-time RAG) |
| Synthesis Agent | TRUE/FALSE/UNCERTAIN verdict + confidence | SynthesisAgent (supported/refuted/contested/insufficient_evidence) |
| Critic Agent | Adversarial check; flags overconfidence | CriticAgent (same purpose; also overrides if confidence < 0.5) |
| Correction Agent | Corrects FALSE/UNCERTAIN with cited sources | Merged into CriticAgent; we surface sources directly from EvidenceRetriever |

### Patterns we reuse

- **Sequential 5-agent pipeline** as LangGraph `StateGraph` with explicit ordering
- **Shared TypedDict state** — every agent reads from and writes to the same state object; no inter-agent message passing
- **Conditional routing principle** — Sift skips Correction Agent for TRUE verdicts; we apply same idea: CriticAgent conditionally overrides vs. passes through SynthesisAgent output
- **Epistemic humility prompt pattern** — explicit instruction to return `insufficient_evidence` / UNCERTAIN rather than confabulate; validated with Pydantic confidence < 0.5 override
- **Pydantic structured output** from the LLM to get typed verdict + confidence + reasoning in one call
- **Tavily for live web search** — Sift confirmed this works well for recent claims; we use the same integration

### What we adapt / drop

| Sift | Our version | Reason |
|---|---|---|
| LLaMA 3.3 70B via Groq | Gemini 2.5 Flash-Lite via langchain-google-genai | User has Gemini API key; free tier; $0.10/1M tokens |
| pgvector + HyDE | Removed — no pre-indexed embeddings | We do real-time RAG only; no corpus to pre-index |
| Celery background workers | Removed — FastAPI async | Prototype scale; Celery is over-engineering for now |
| Correction Agent (5th) | Merged into CriticAgent | Sift's Correction Agent cited sources that EvidenceRetriever already has; we surface them directly |
| TRUE/FALSE/UNCERTAIN | supported/refuted/contested/insufficient_evidence | Richer enum; PNAS/MIT research shows binary labels mislead users |

---

## LangGraph API Patterns (v1.0.9, verified 2026-06-26)

```python
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
import operator

# 1. Define shared state with TypedDict
class PipelineState(TypedDict):
    claim: str
    sub_claims: list[str]
    evidence: list[dict]
    scored_sources: list[dict]
    verdict: str
    confidence: float
    reasoning: str

# 2. Build graph
builder = StateGraph(PipelineState)

# 3. Add nodes (each is a plain function state_in → state_out_partial)
builder.add_node("decomposer", decompose_claim)
builder.add_node("retriever", retrieve_evidence)
builder.add_node("scorer", score_sources)
builder.add_node("synthesizer", synthesize)
builder.add_node("critic", critique)

# 4. Add edges (sequential)
builder.add_edge(START, "decomposer")
builder.add_edge("decomposer", "retriever")
builder.add_edge("retriever", "scorer")
builder.add_edge("scorer", "synthesizer")
builder.add_edge("synthesizer", "critic")
builder.add_edge("critic", END)

# 5. Compile and invoke
graph = builder.compile()
result = graph.invoke({"claim": "...", "source_mode": "flexible", ...})
```

Key: each node function receives the full state dict and returns a **partial dict** — only the keys it updates. LangGraph merges it.

---

## Tavily Python SDK Patterns (v0.7.23, verified 2026-06-26)

```python
from tavily import TavilyClient

client = TavilyClient(api_key="tvly-...")

# Basic search
response = client.search(
    query="H1B visa cap 2024",
    search_depth="advanced",   # "basic" (1 credit) or "advanced" (2 credits)
    max_results=5,
    include_domains=[],        # allowlist (empty = no filter)
    exclude_domains=[],
    topic="general",           # "general" | "news" | "finance"
    time_range=None,           # "day" | "week" | "month" | "year" | None
    include_answer=False,
)

# Response structure
response["query"]          # str — echoed query
response["results"]        # list[dict] — ranked by relevance
response["response_time"]  # float

# Each result:
result["title"]            # str
result["url"]              # str
result["content"]          # str — snippet (main text to use for evidence)
result["score"]            # float — Tavily relevance score 0–1
result["published_date"]   # str | None
```

### Strict mode filter (our implementation)

```python
STRICT_DOMAINS = [
    "*.gov", "*.edu", "*.ac.uk", "*.gc.ca",
    "who.int", "cdc.gov", "nih.gov",
    "apnews.com", "reuters.com", "bbc.com", "bbc.co.uk", "npr.org", "pbs.org",
]
# Use include_domains param in TavilyClient.search() for allowlisting
```

Async client available via `from tavily import AsyncTavilyClient` — same interface, awaitable.

---

## SourceScorer Domain Scoring

| Domain pattern | Score | Category |
|---|---|---|
| `*.gov`, `*.gc.ca`, `who.int`, `cdc.gov`, `nih.gov` | 1.0 | government |
| `*.edu`, `*.ac.uk`, `*.ac.*` | 0.85 | academic |
| `apnews.com`, `reuters.com`, `bbc.com`, `bbc.co.uk`, `npr.org`, `pbs.org` | 0.7 | established_news |
| everything else | 0.4 | other |

Sources with score < 0.4 are filtered out. In current scoring, minimum is 0.4 (the "other" floor), so in practice nothing is filtered by score alone — the floor is the credibility floor.

---

## Gemini 2.5 Flash-Lite via langchain-google-genai (v4.2.1)

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    google_api_key=GEMINI_API_KEY,
    temperature=0.1,
)

# For structured output (Pydantic)
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel

class VerdictOutput(BaseModel):
    verdict: str
    confidence: float
    reasoning: str

parser = JsonOutputParser(pydantic_object=VerdictOutput)
chain = llm | parser
result = chain.invoke([HumanMessage(content=prompt)])
```
