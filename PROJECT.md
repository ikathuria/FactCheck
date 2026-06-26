# FactCheck — Project Tracker

> Living context map. Any LLM or human should be able to read this file alone and understand
> what the project is, how it's built, and where things are. **Keep it in sync** — update it
> whenever the stack, structure, conventions, or status changes.

_Last updated: 2026-06-26_

---

## What it is

FactCheck is an open-source, domain-agnostic fact-checking platform for the general public. Users submit any claim or quote — immigration policy, political news, government statistics, anything — and get back a calibrated verdict (supported / refuted / contested / insufficient evidence) with cited, credibility-scored sources and a plain-English explanation. The platform runs a Python + LangGraph multi-agent pipeline (5 agents: decompose → retrieve → score → synthesize → critique) backed by Gemini 2.5 Flash-Lite and Tavily real-time web search. Results are cached in Redis with a 7-day TTL so repeated queries never re-run the pipeline. All searches are public — anyone can see what others have checked. The same FastAPI backend is designed to serve as the engine for future domain-specific chatbots (H1B visa checker, political news verifier, etc.) via the same `POST /verify` endpoint.

---

## Stack

| Layer | Choice | Version | Notes |
|---|---|---|---|
| Frontend framework | Next.js | 15.x (verify before coding) | App Router, TypeScript, Vercel free tier |
| Frontend styling | Tailwind CSS | 4.x (verify before coding) | |
| Backend framework | FastAPI | 0.115.x (verify before coding) | Python 3.12, async |
| Agent orchestration | LangGraph | 1.2.6 (confirmed June 2026) | v1.0 shipped Oct 2025 — avoid pre-1.0 tutorials |
| LLM | Gemini 2.5 Flash-Lite | latest (verify: ai.google.dev/gemini-api/docs/pricing) | via langchain-google-genai; free tier + $0.10/1M tokens |
| Web search | Tavily | latest Python SDK (verify: docs.tavily.com) | 1,000 free searches/month, no card required |
| Result cache | Upstash Redis | serverless (verify: upstash.com/docs) | 7-day TTL per query; free tier |
| Search history DB | Supabase (Postgres) | free tier | Persistent recent-searches feed |
| Frontend hosting | Vercel | free tier | Git-integrated auto-deploy |
| Backend hosting | Render | free tier | Cold starts expected; keep-alive pings via GitHub Actions |
| Testing (backend) | pytest | 8.x | |
| Testing (frontend) | Vitest + Playwright | latest | Unit tests colocated; Playwright for E2E happy path |
| CI/CD | GitHub Actions | — | lint + typecheck + test on every push |

> Versions verified against official docs on 2026-06-26. Re-verify before coding against any library.

---

## Architecture

Request/data flow:

1. User submits claim + source mode (strict/flexible) via Next.js frontend
2. Frontend calls `POST /verify` on FastAPI backend (Render)
3. Backend computes cache key: `SHA-256("{claim.lower().strip()}:{source_mode}")`
4. **Cache hit (Redis):** return stored VerifyResponse with `cached: true`
5. **Cache miss:** run LangGraph 5-agent pipeline:
   - **ClaimDecomposer** → breaks claim into 1–4 verifiable sub-claims
   - **EvidenceRetriever** → Tavily search per sub-claim (strict: gov/academic filter; flexible: all results)
   - **SourceScorer** → scores domains (gov=1.0, academic=0.85, news=0.7, other=0.4); filters < 0.4
   - **SynthesisAgent** (Gemini) → verdict + confidence (0–1) + reasoning; instructed to output `insufficient_evidence` when evidence is thin
   - **CriticAgent** (Gemini) → reviews synthesis; overrides to `insufficient_evidence` if confidence < 0.5; overrides to `contested` if evidence contradicts
6. Store result in Redis (7-day TTL) + insert row in Supabase `searches` table
7. Return VerifyResponse to frontend
8. Frontend renders verdict badge, confidence bar, reasoning, source cards
9. Recent searches feed: `GET /recent-searches` reads Supabase `searches` ordered by `searched_at desc`

---

## Project Structure

```
factcheck/
├── apps/
│   ├── api/                          # FastAPI backend (Python 3.12)
│   │   ├── src/
│   │   │   ├── agents/               # LangGraph agent definitions
│   │   │   │   ├── claim_decomposer.py
│   │   │   │   ├── evidence_retriever.py
│   │   │   │   ├── source_scorer.py
│   │   │   │   ├── synthesis.py
│   │   │   │   └── critic.py
│   │   │   ├── features/
│   │   │   │   ├── verify/           # pipeline orchestration + /verify endpoint
│   │   │   │   ├── cache/            # Redis cache layer (get/set with TTL)
│   │   │   │   └── history/          # Supabase recent-searches CRUD
│   │   │   ├── lib/
│   │   │   │   ├── gemini.py         # Gemini client singleton
│   │   │   │   ├── tavily.py         # Tavily client + source-mode filter
│   │   │   │   └── types.py          # shared Pydantic models
│   │   │   └── main.py               # FastAPI app, CORS, route registration
│   │   ├── tests/
│   │   ├── requirements.txt
│   │   └── pyproject.toml
│   └── web/                          # Next.js frontend (TypeScript, Tailwind)
│       ├── src/
│       │   ├── app/                  # Next.js App Router (pages + layouts)
│       │   ├── features/
│       │   │   ├── search/           # ClaimInput, SourceModeToggle, SearchForm
│       │   │   ├── results/          # VerdictBadge, ConfidenceBar, ReasoningCard, SourceCard
│       │   │   ├── metrics/          # MetricsDashboard (static stats + live counters)
│       │   │   └── recent/           # RecentSearches feed
│       │   └── lib/
│       │       ├── api.ts            # typed fetch client for FastAPI
│       │       └── types.ts          # TS types mirroring backend Pydantic models
│       └── package.json
├── docs/
│   ├── 01-architecture.md            # request/data flow diagram + Sift reuse notes
│   └── 02-spike-results.md           # M0 spike test results (5 claims)
├── PROJECT.md                        # this file
├── PLAN.md                           # build plan with milestones
├── RESEARCH.md                       # market + feasibility research (2026-06-26)
├── CLAUDE.md                         # "See PROJECT.md for project context."
├── .env.example                      # all required env vars
└── README.md
```

---

## Conventions

- **New backend feature** → `apps/api/src/features/<name>/`
- **New agent** → `apps/api/src/agents/<name>.py`
- **New frontend feature** → `apps/web/src/features/<name>/`
- **Tests:** backend in `apps/api/tests/test_<feature>.py`; frontend colocated as `<name>.test.ts`
- **Naming:** snake_case for Python files/functions; PascalCase for React components; kebab-case for docs filenames
- **Docs filenames:** zero-padded kebab-case (`01-architecture.md`), no spaces
- **Root package.json:** delegates to `apps/web` only — no workspaces until a second consumer exists
- **Before coding any library:** fetch its latest official docs — never code APIs from memory
- **Verdict design:** never output binary TRUE/FALSE; always verdict enum + confidence + sources + reasoning

---

## API Contract (summary)

**POST /verify**
- Request: `{ claim: string, source_mode: "strict" | "flexible" }`
- Response: `{ claim, verdict, confidence (0–1), reasoning, sources[], cached, cached_at, ttl_expires_at }`
- Verdict enum: `supported | refuted | insufficient_evidence | contested`
- Cache key: SHA-256 of `"{claim.lower().strip()}:{source_mode}"`, TTL 7 days

**GET /recent-searches**
- Query: `limit` (default 20, max 50), `offset` (default 0)
- Response: `{ searches[], total }`

**GET /health**
- Response: `{ status: "ok" }`

---

## Current Status

| Milestone | Status | Notes |
|---|---|---|
| 0. Spike | ✅ done | Pipeline proven: 4/5 verdicts defensible (gate: 3+). See [docs/02-spike-results.md](docs/02-spike-results.md) |
| 1. Scaffold | ☐ todo | Both apps running locally |
| 2. Core Pipeline | ☐ todo | POST /verify end-to-end |
| 3. Cache + Storage | ☐ todo | Redis + Supabase |
| 4. Frontend | ☐ todo | Next.js full flow |
| 5. Deploy | ☐ todo | Render + Vercel |
| 6. Polish | ☐ todo | Error states, mobile, README |

**In progress now:** Milestone 0 complete — spike validated the pipeline
**Next up:** Milestone 1 (Scaffold). Carry two spike findings into Milestone 2:
  (1) 🔴 Rewrite CriticAgent prompt so it judges only the provided evidence and never its own
      world-knowledge/recency prior (it wrongly overrode a true, gov-sourced 2024-election verdict);
  (2) 🟠 Resolve Gemini free-tier quota — flash-lite free tier is only 20 req/day; decide paid key
      vs. fewer LLM calls per claim. See [docs/02-spike-results.md](docs/02-spike-results.md).

---

## Decision Log

- 2026-06-26 — **API over Python package** — frontend is Next.js (separate runtime), so FastAPI REST API is the right boundary. Domain-specific chatbots later are additional consumers of `POST /verify`.
- 2026-06-26 — **Verdict: never binary TRUE/FALSE** — PNAS and MIT research shows binary labels mislead users. Always surface: verdict enum + confidence + raw sources + reasoning. Let users judge.
- 2026-06-26 — **7-day Redis TTL** — immigration/political facts change frequently; 7 days balances freshness vs. Tavily API usage.
- 2026-06-26 — **Strict mode fallback** — if strict mode finds < 3 sources, auto-fallback to flexible and flag `source_mode_fallback: true`. Don't leave users with empty results.
- 2026-06-26 — **No auth** — all searches public by design. The shared recent-searches feed is a feature.
- 2026-06-26 — **Study Sift at Milestone 0** — Sift (LangGraph + Tavily + 5-agent) is the nearest prior art; reading it first avoids re-inventing validated patterns.

---

## Glossary

- **Strict mode** — source filter: only `.gov`, `.edu`, `who.int`, `cdc.gov`, `nih.gov`, `apnews.com`, `reuters.com`, `bbc.com`, `npr.org`, `pbs.org`, `bbc.co.uk`, `*.gc.ca`, `*.ac.uk`
- **Flexible mode** — all Tavily results included; low-credibility sources (score < 0.4) excluded from reasoning but shown in UI
- **Verdict enum** — `supported` (evidence backs claim), `refuted` (evidence contradicts), `contested` (evidence conflicts), `insufficient_evidence` (evidence too thin or absent)
- **Cache key** — SHA-256 hash of the normalized claim + source mode; same claim with different casing maps to same key
- **TTL** — time-to-live; result cache expires after 7 days (604,800 seconds)
- **Sift** — nearest open-source analog; LangGraph + Tavily + 5-agent pattern, published May 2024 on dev.to; study before building agents
- **CriticAgent** — the final agent in the pipeline; overrides synthesis if confidence < 0.5 or evidence contradicts; prevents overconfident wrong verdicts
