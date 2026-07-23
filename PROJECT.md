# FactCheck — Project Tracker

> Living context map. Any LLM or human should be able to read this file alone and understand
> what the project is, how it's built, and where things are. **Keep it in sync** — update it
> whenever the stack, structure, conventions, or status changes.

_Last updated: 2026-07-21_

---

## What it is

FactCheck is an open-source, domain-agnostic fact-checking platform for the general public. Users submit any claim or quote — immigration policy, political news, government statistics, anything — and get back a calibrated verdict (supported / refuted / contested / insufficient evidence) with cited, credibility-scored sources and a plain-English explanation. The platform runs a Python + LangGraph multi-agent pipeline (5 agents: decompose → retrieve → score → synthesize → critique) backed by Gemini 2.5 Flash and Tavily real-time web search. Results are cached in Turso (libSQL) with a 7-day TTL so repeated queries never re-run the pipeline. All searches are public — anyone can see what others have checked. The same FastAPI backend is designed to serve as the engine for future domain-specific chatbots (H1B visa checker, political news verifier, etc.) via the same `POST /verify` endpoint.

---

## Stack

| Layer | Choice | Version | Notes |
|---|---|---|---|
| Frontend framework | Next.js | 16.2.9 (React 19.2.4) | App Router, TypeScript, src-dir, Vercel free tier. NOTE: Next 16 has breaking changes — see apps/web/AGENTS.md (read node_modules/next/dist/docs/ before frontend coding) |
| Frontend styling | Tailwind CSS | 4.x (verify before coding) | |
| Backend framework | FastAPI | 0.115.x (verify before coding) | Python 3.12, async |
| Agent orchestration | LangGraph | 1.2.6 (confirmed June 2026) | v1.0 shipped Oct 2025 — avoid pre-1.0 tutorials |
| LLM | Gemini 2.5 Flash | latest (verify: ai.google.dev/gemini-api/docs/pricing) | via langchain-google-genai; free tier (~1.5k req/day). Model set by `GEMINI_MODEL` (default `gemini-2.5-flash`) — provider swap is a config change |
| Web search | Tavily | latest Python SDK (verify: docs.tavily.com) | 1,000 free searches/month, no card required |
| Cache + history DB | Turso (libSQL) | libsql-client 0.3.1 (verify: docs.turso.tech) | Single DB: result cache (app-enforced 7-day TTL) + recent-searches feed; free tier |
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
4. **Cache hit (Turso):** return stored VerifyResponse with `cached: true` (rows past `expires_at` are ignored — TTL is enforced in-app, not by the DB)
5. **Cache miss:** run LangGraph 5-agent pipeline:
   - **ClaimDecomposer** → breaks claim into 1–4 verifiable sub-claims
   - **EvidenceRetriever** → Tavily search per sub-claim (strict: gov/academic filter; flexible: all results)
   - **SourceScorer** → scores domains (gov=1.0, academic=0.85, news=0.7, other=0.4); filters < 0.4
   - **SynthesisAgent** (Gemini) → verdict + confidence (0–1) + reasoning; instructed to output `insufficient_evidence` when evidence is thin
   - **CriticAgent** (Gemini) → reviews synthesis; overrides to `insufficient_evidence` if confidence < 0.5; overrides to `contested` if evidence contradicts
6. Store result in Turso `cache` table (7-day TTL via `expires_at`) + insert row in Turso `searches` table
7. Return VerifyResponse to frontend
8. Frontend renders verdict badge, confidence bar, reasoning, source cards
9. Recent searches feed: `GET /recent-searches` reads Turso `searches` ordered by `searched_at desc`

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
│   │   │   │   ├── cache/            # Turso result cache (get/set, app-enforced TTL)
│   │   │   │   └── history/          # Turso recent-searches CRUD
│   │   │   ├── lib/
│   │   │   │   ├── gemini.py         # Gemini client singleton
│   │   │   │   ├── tavily.py         # Tavily client + source-mode filter
│   │   │   │   ├── turso.py          # shared libSQL client (cache + history)
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
| 0. Spike | ✅ done | Pipeline proven: 5/5 verdicts defensible after critic fix. See [docs/02-spike-results.md](docs/02-spike-results.md) |
| 1. Scaffold | ✅ done | Both apps run locally; CI configured; lint/typecheck/test/health all green |
| 2. Core Pipeline | ✅ done | 5-agent LangGraph wired; POST /verify end-to-end; 20/20 tests pass (live), CI-safe |
| 3. Cache + Storage | ✅ done | Turso (libSQL) cache + history + GET /recent-searches built; degrades gracefully. Turso DB `factcheck` provisioned, schema applied. **Verified live end-to-end 2026-07-23: two identical POSTs → 2nd `cached:true`; recent-searches feed populated.** |
| 4. Frontend | ✅ done | Next.js 16 full flow: metrics dashboard, search form (claim + strict/flexible), animated pipeline progress, results (verdict/confidence/reasoning/sources), paginated recent-searches feed. 13 Vitest units + 1 Playwright E2E pass; lint + `next build` clean. **Run live 2026-07-23 against real Gemini/Tavily/Turso — verdict, source scoring, cache hit, and history all confirmed in the UI.** |
| 5. Deploy | ☐ todo | Render (API) + Vercel (web) |
| 6. Polish | ☐ todo | Error states, mobile, source-scoring tiers |

**In progress now:** Milestones 0–4 done **and validated live end-to-end** (local, 2026-07-23) —
  real Gemini 2.5 Flash synthesis, Tavily sources, Turso cache (`cached:true` on repeat) and history,
  rendered in the Next.js UI. Docs updated to match.
**Next up:**
  1. Milestone 5 (deploy) — backend on Render (set GEMINI/TAVILY/TURSO/ALLOWED_ORIGINS env),
     frontend on Vercel (root dir `apps/web`, set NEXT_PUBLIC_API_URL). Render's Linux runtime
     avoids the local macOS cert quirk (see Notes).
  2. Milestone 6 (polish) — error states, mobile, source-scoring tiers (Wikipedia/Britannica > 0.4).

Notes / local-dev gotchas (full run guide in [README.md](README.md)):
  - Backend loads `apps/api/.env` (preferred over repo-root `.env`) — put all backend keys there.
  - `uvicorn --reload` does NOT reload `.env` (watches `.py` only) — restart uvicorn after editing env.
  - macOS python.org Python 3.14 has no CA bundle → libSQL's aiohttp transport fails Turso calls with
    `CERTIFICATE_VERIFY_FAILED`. Fix: `export SSL_CERT_FILE="$(python -c 'import certifi; print(certifi.where())')"`
    before uvicorn (or run the installer's `Install Certificates.command`). Linux/Render unaffected.
  - Turso URL in `.env` is the `libsql://` form from the CLI; `lib/turso.py` normalizes it to the
    `https://` HTTP transport (libsql-client 0.3.1's default `wss://` handshake is rejected by
    current Turso servers).

Open items / deferred:
  - ✅ LLM resolved (2026-07-22): default model is now `gemini-2.5-flash` (was `flash-lite`) —
    stronger instruction-following/calibration for the synthesis + critic agents, still on
    Gemini's free tier (~1.5k req/day, up from the drained key's ~20/day). Set via `GEMINI_MODEL`;
    the client stays provider-agnostic, so Claude/DeepSeek is a later config swap if quality
    demands it. Needs a clean free-tier `GEMINI_API_KEY` in `apps/api/.env`.

---

## Decision Log

- 2026-06-26 — **API over Python package** — frontend is Next.js (separate runtime), so FastAPI REST API is the right boundary. Domain-specific chatbots later are additional consumers of `POST /verify`.
- 2026-06-26 — **Verdict: never binary TRUE/FALSE** — PNAS and MIT research shows binary labels mislead users. Always surface: verdict enum + confidence + raw sources + reasoning. Let users judge.
- 2026-06-26 — **7-day cache TTL** — immigration/political facts change frequently; 7 days balances freshness vs. Tavily API usage.
- 2026-07-21 — **Turso (libSQL) for all storage** — replaced Upstash Redis (cache) + Supabase (history) with a single Turso database. One free service instead of two; libSQL is edge-friendly for the Render backend. Trade-off: SQLite has no native key expiry, so the 7-day cache TTL is emulated (each row carries `expires_at`; reads filter it, writes sweep it). Storage isolated behind `lib/turso.py` + per-layer `is_configured()` graceful degradation, so the swap touched only the cache/history modules, the migration, and env vars. Client is `libsql-client` 0.3.1; its default `libsql://`/`wss://` (WebSocket Hrana) handshake is rejected by current Turso servers, so `lib/turso.py` normalizes the URL to the `https://` HTTP transport, which works. Verified live against the provisioned cloud DB.
- 2026-07-22 — **LLM: Gemini 2.5 Flash (not Flash-Lite)** — bumped the default model for better instruction-following and calibration on the synthesis/critic agents (the verdict-quality-sensitive steps), while staying on Gemini's free tier (~1.5k req/day). One-line change (`DEFAULT_MODEL` in `lib/gemini.py`, overridable via `GEMINI_MODEL`) since the client already targets Gemini. Considered Claude Haiku 4.5 (best cheap-tier instruction-following) and DeepSeek-V4 (cheapest capable) but both need a client swap and break the $0/month goal; the client stays provider-agnostic so that remains a future config swap if verdict quality demands it. The earlier "~20 req/day" pain was a drained key, not a provider ceiling.
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
