# FactCheck

> A domain-agnostic fact-checking platform where anyone can submit a claim and get back a verified verdict with cited sources, powered by a Python + LangGraph multi-agent pipeline with real-time RAG. Open source.

---

## Viability Summary

| | |
|---|---|
| **Market** | crowded-with-gap — serious players (Full Fact, Factiverse) target journalists/enterprise only; no polished open-source consumer tool exists |
| **Feasibility** | medium — spike is LLM verdict reliability on uncurated live-web search; orchestration and retrieval are solved |
| **Free to build** | yes — $0/month prototype (Gemini free tier + Tavily 1k free searches + Upstash Redis free + Supabase free + Render free + Vercel free) |
| **Monetization** | portfolio / open source — not applicable |

See [RESEARCH.md](RESEARCH.md) for full competitor analysis, community signals, and feasibility audit.

---

## Research Findings

### Competitors
| Name | Pricing | Strength | Limitations |
|---|---|---|---|
| Full Fact AI | Enterprise only | 45+ orgs in 30 countries | No consumer product |
| Factiverse | Free: 30-word cap; Pro: €25/mo | Best for journalists | Free tier unusable; no self-serve API |
| Originality.ai | $14.95/mo | Integrated AI-detection + fact-check | English only; high false-positive rate |
| Webcite | Free: ~12/mo; $20/mo for 500 | Developer REST API | Not user-facing |
| Sift (OSS) | Free / self-hosted | Exact tech match: LangGraph + Tavily | GitHub repo only, no product |
| Parafact | $29/mo (no free trial) | Consumer-facing | Paywall before any value; minimal traction |

**Positioning:** Crowded-with-gap. The gap is the general public. All established players target professionals. No polished, open-source, general-audience tool with real-time RAG and source transparency exists.

### Feasibility
- **Hardest part:** LLM verdict reliability on uncurated live-web search — **approach:** multi-agent critic layer (study Sift's 5-agent pattern) + explicit "insufficient evidence" verdicts + source credibility scoring. Accept imperfection; design UX around calibrated uncertainty.
- **Cost flags:** none — every component has a free tier at prototype scale. See cost audit in RESEARCH.md.

### Sift Prior Art (Study and Reuse)
Sift (https://dev.to/ashg2099/i-built-an-open-source-multi-agent-fact-checker-heres-how-it-works-5eah) is the nearest open-source analog. Study before building:
- **Reuse:** 5-agent LangGraph pattern (ClaimDecomposer → EvidenceRetriever → SourceScorer → SynthesisAgent → CriticAgent)
- **Reuse:** LangGraph conditional branching for agent routing
- **Adapt:** swap LLaMA 3.3 70B → Gemini 2.5 Flash-Lite; remove Celery (use FastAPI async); remove pgvector (real-time RAG doesn't need pre-indexed embeddings); add Redis result caching layer; add source-mode toggle (strict vs. flexible)

### Monetization
Portfolio / open source — not applicable.

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| LLM returns confident wrong verdict | high | high | Never show binary TRUE/FALSE; always show confidence level + "insufficient evidence" option; always surface raw sources |
| Tavily free tier (1k/mo) exhausted quickly | medium | medium | Cache all results in Redis with 1-week TTL; same query never re-runs pipeline within TTL window |
| Gemini free tier rate-limited | medium | low | Implement retry with exponential backoff; Gemini 2.5 Flash-Lite is very cheap at pay-as-you-go ($0.10/1M tokens) |
| Render free tier cold starts (slow first load) | high | low | Show loading state on frontend; keep API warm with lightweight health-check pings |
| Political bias perception | medium | high | Never show verdict labels ("TRUE"/"FALSE"); show sources + confidence + reasoning; let users decide |
| Brave Search free tier killed in 2026 | already happened | — | Use Tavily (no card required, 1k free/mo) as primary |

---

## Tech Stack

> **Important:** Before coding against any library, fetch its latest official docs. Versions below were verified from research as of 2026-06-26 — re-verify at Milestone 0 before scaffolding.

| Layer | Choice | Version (verify before coding) | Reason |
|---|---|---|---|
| Frontend framework | Next.js | 15.x (verify: nextjs.org/docs) | Portfolio-grade, SSR for metrics SEO, Vercel free tier |
| Frontend language | TypeScript | 5.x | Type safety across frontend |
| Frontend styling | Tailwind CSS | 4.x (verify: tailwindcss.com) | Utility-first, fast prototyping |
| Backend framework | FastAPI | 0.115.x (verify: fastapi.tiangolo.com) | Python ecosystem, async, auto-docs |
| Backend language | Python | 3.12 | LangGraph requirement |
| Agent orchestration | LangGraph | 1.2.6 (confirmed June 2026) | Multi-agent conditional routing; v1.0 shipped Oct 2025 |
| LLM | Gemini 2.5 Flash-Lite via langchain-google-genai | latest (verify: ai.google.dev) | User has Gemini API key; free tier + cheap PAYG |
| Web search / RAG | Tavily Python SDK | latest (verify: docs.tavily.com) | No credit card for free tier; 1k free searches/mo; used in Sift |
| Result cache | Upstash Redis | serverless (verify: upstash.com/docs) | Native TTL support; free tier; serverless (no always-on host needed) |
| Search history DB | Supabase (Postgres) | free tier (verify: supabase.com/docs) | Persistent recent searches feed; free tier; easy setup |
| Frontend hosting | Vercel | free tier | Git-integrated auto-deploy for Next.js |
| Backend hosting | Render | free tier | Free web services; cold-start acceptable for prototype |
| Testing (backend) | pytest | 8.x (verify: docs.pytest.org) | Standard Python testing |
| Testing (frontend) | Vitest | latest (verify: vitest.dev) | Fast unit tests, colocated |
| CI/CD | GitHub Actions | — | Free; lint + test on every push |

**Skipped layers (deliberate):**
- Auth — no login needed; all searches are public by design
- Payments — open source portfolio
- Email — no notifications
- File storage — no file uploads
- Celery/background workers — FastAPI async handles pipeline; Redis for caching is sufficient at prototype scale

---

## Project Structure

```
factcheck/                    # repo root
├── apps/
│   ├── api/                  # FastAPI backend
│   │   ├── src/
│   │   │   ├── agents/       # LangGraph agent definitions
│   │   │   │   ├── claim_decomposer.py
│   │   │   │   ├── evidence_retriever.py
│   │   │   │   ├── source_scorer.py
│   │   │   │   ├── synthesis.py
│   │   │   │   └── critic.py
│   │   │   ├── features/
│   │   │   │   ├── verify/   # pipeline orchestration + /verify endpoint
│   │   │   │   ├── cache/    # Redis cache layer (get/set with TTL)
│   │   │   │   └── history/  # Supabase recent-searches CRUD
│   │   │   ├── lib/
│   │   │   │   ├── gemini.py     # Gemini client singleton
│   │   │   │   ├── tavily.py     # Tavily client + source-mode filter
│   │   │   │   └── types.py      # shared Pydantic models
│   │   │   └── main.py           # FastAPI app, CORS, route registration
│   │   ├── tests/
│   │   ├── requirements.txt
│   │   └── pyproject.toml
│   └── web/                  # Next.js frontend
│       ├── src/
│       │   ├── app/          # Next.js App Router (pages + layouts)
│       │   ├── features/
│       │   │   ├── search/   # claim input + source-mode toggle
│       │   │   ├── results/  # verdict display + citations
│       │   │   ├── metrics/  # misinformation stats dashboard
│       │   │   └── recent/   # public recent searches feed
│       │   └── lib/
│       │       ├── api.ts    # typed fetch client for FastAPI
│       │       └── types.ts  # shared TS types (mirrors backend Pydantic models)
│       └── package.json
├── docs/
│   └── 01-architecture.md    # request/data flow diagram
├── PROJECT.md                # living context tracker (keep in sync)
├── PLAN.md                   # this file
├── CLAUDE.md                 # one line: "See PROJECT.md for project context."
├── RESEARCH.md               # market + feasibility research
├── .env.example
└── README.md
```

**Conventions:**
- New backend feature → `apps/api/src/features/<name>/`
- New agent → `apps/api/src/agents/<name>.py`
- New frontend feature → `apps/web/src/features/<name>/`
- Tests colocate: `apps/api/tests/test_<feature>.py`, `apps/web/src/features/<name>/<name>.test.ts`
- `docs/` filenames: zero-padded kebab-case, no spaces
- Root `package.json` delegates to web only: `npm --prefix apps/web run <script>`
- Before coding any library: fetch its latest official docs — never code APIs from memory

---

## Environment Variables

```
# Backend (apps/api/.env)
GEMINI_API_KEY=           # Google AI Studio — aistudio.google.com
TAVILY_API_KEY=           # Tavily — app.tavily.com (no card required)
UPSTASH_REDIS_REST_URL=   # Upstash dashboard — upstash.com
UPSTASH_REDIS_REST_TOKEN= # Upstash dashboard
SUPABASE_URL=             # Supabase project settings
SUPABASE_SERVICE_KEY=     # Supabase project settings (service role key, not anon)
ALLOWED_ORIGINS=          # comma-separated: http://localhost:3000,https://your-vercel-url.vercel.app

# Frontend (apps/web/.env.local)
NEXT_PUBLIC_API_URL=      # http://localhost:8000 (dev) or your Render URL (prod)
```

---

## API Contract

The FastAPI backend exposes these endpoints. The Next.js frontend calls them.

### POST /verify
**Request:**
```json
{
  "claim": "string — the text to fact-check",
  "source_mode": "strict | flexible"
}
```
**Response:**
```json
{
  "claim": "string",
  "verdict": "supported | refuted | insufficient_evidence | contested",
  "confidence": 0.0–1.0,
  "reasoning": "string — 2–4 sentences explaining the verdict",
  "sources": [
    {
      "url": "string",
      "title": "string",
      "snippet": "string",
      "credibility_score": 0.0–1.0,
      "domain_type": "government | academic | established_news | other"
    }
  ],
  "cached": true | false,
  "cached_at": "ISO datetime | null",
  "ttl_expires_at": "ISO datetime | null"
}
```
**Cache key:** SHA-256 hash of `"{claim.lower().strip()}:{source_mode}"`. TTL: 7 days.
**Notes:** Never return a binary TRUE/FALSE. Confidence < 0.5 should always resolve to `insufficient_evidence` regardless of LLM preference.

### GET /recent-searches
**Query params:** `limit` (default 20, max 50), `offset` (default 0)
**Response:**
```json
{
  "searches": [
    {
      "id": "uuid",
      "claim": "string",
      "verdict": "supported | refuted | insufficient_evidence | contested",
      "confidence": 0.0–1.0,
      "source_mode": "strict | flexible",
      "searched_at": "ISO datetime"
    }
  ],
  "total": 123
}
```

### GET /health
Returns `{"status": "ok"}` — used for Render keep-alive and smoke testing.

---

## LangGraph Pipeline

The pipeline runs as a directed graph with conditional edges. Study Sift's implementation before building.

```
[START]
  │
  ▼
ClaimDecomposer
  │  Breaks the input claim into 1–4 verifiable sub-claims.
  │  Output: list of sub-claims + original claim.
  ▼
EvidenceRetriever
  │  Runs Tavily search per sub-claim.
  │  source_mode=strict: filters results to .gov, .edu, AP, Reuters, BBC, NPR, NIH, CDC, WHO
  │  source_mode=flexible: returns all Tavily results, scored but not filtered
  │  Output: evidence chunks per sub-claim, with source URLs.
  ▼
SourceScorer
  │  Scores each source: government=1.0, academic=0.85, established_news=0.7, other=0.4
  │  Filters out sources below 0.4 threshold.
  │  Output: scored + filtered evidence set.
  ▼
SynthesisAgent (Gemini)
  │  Given claim + evidence, produces: verdict, confidence (0–1), reasoning.
  │  Prompt explicitly instructs: output "insufficient_evidence" if evidence is thin or contradictory.
  │  Output: initial verdict object.
  ▼
CriticAgent (Gemini)
  │  Reviews SynthesisAgent output. Checks: is the verdict actually supported by the evidence?
  │  If confidence < 0.5, overrides verdict to "insufficient_evidence".
  │  If evidence strongly contradicts itself, overrides to "contested".
  │  Output: final verdict object (may be identical to synthesis, or corrected).
  ▼
[END] → return VerifyResponse
```

---

## Source Mode: Strict vs. Flexible

**Strict mode** (`source_mode=strict`):
- Tavily search runs normally
- Results filtered to allowlisted domain patterns: `*.gov`, `*.edu`, `*.ac.uk`, `*.gc.ca`, `who.int`, `cdc.gov`, `nih.gov`, `apnews.com`, `reuters.com`, `bbc.com`, `bbc.co.uk`, `npr.org`, `pbs.org`
- If fewer than 3 sources pass filter → automatically re-run with flexible mode and flag `source_mode_fallback: true` in response

**Flexible mode** (`source_mode=flexible`):
- All Tavily results included
- SourceScorer still runs and assigns credibility scores
- Low-credibility sources (score < 0.4) excluded from reasoning but shown in response with a low-credibility flag

---

## Result Caching (Redis, TTL = 7 days)

- **Cache key:** `SHA-256("{claim.strip().lower()}:{source_mode}")`
- **On request:** check Redis first. If hit and not expired, return cached result with `cached: true`
- **On miss:** run full pipeline, store result in Redis with 7-day TTL, store summary in Supabase `searches` table, return result with `cached: false`
- **Recent searches feed:** read from Supabase `searches` table (persists beyond Redis TTL for history display, but response content comes from Redis while valid)
- **Cache invalidation:** no manual invalidation — TTL handles staleness. 7 days chosen because immigration policy, political facts, and government metrics change frequently enough that older results should re-run.

---

## Supabase Schema

```sql
-- searches table: permanent record for recent-searches feed
create table searches (
  id uuid primary key default gen_random_uuid(),
  claim text not null,
  claim_hash text not null,         -- SHA-256 cache key
  verdict text not null,            -- supported | refuted | insufficient_evidence | contested
  confidence float not null,
  source_mode text not null,        -- strict | flexible
  searched_at timestamptz not null default now()
);

create index searches_searched_at_idx on searches (searched_at desc);
create index searches_claim_hash_idx on searches (claim_hash);
```

---

## Frontend Features

### 1. Metrics Dashboard (top of home page)
Static stats + any we can compute from our own `searches` table. Initial set:
- "35% of AI chatbot responses contained misinformation" (NewsGuard, August 2025)
- "80% of UK adults are concerned about political misinformation" (Full Fact, 2026)
- "3 fact-checking orgs closed for every 1 that opened in 2025" (Poynter, 2026)
- Live stats from our DB: total claims checked, % by verdict type (once we have data)

### 2. Claim Search
- Text input (multiline, max 500 chars)
- Source mode toggle: "Strict sources (gov/academic)" vs "All sources"
- Submit → loading state (stream-friendly: show "Decomposing claim…", "Searching sources…", "Synthesizing verdict…")
- Results: verdict badge (color-coded, never binary TRUE/FALSE), confidence bar, reasoning paragraph, source cards

### 3. Recent Searches Feed
- Public list of recent claims checked by anyone (paginated)
- Shows: claim snippet, verdict badge, confidence, how long ago
- Clicking a recent search loads cached result instantly (no re-run)
- "Searched X minutes ago — results valid until [date]" shown on cached results

### 4. Source Cards
Each source card shows: title, domain, URL, credibility score bar, snippet, domain type badge (Government / Academic / News / Other)

---

## Milestones

### Milestone 0: Spike
**Goal:** Prove the LangGraph pipeline returns calibrated verdicts with citations on 5 diverse test claims, before any scaffolding.

Tasks:
- [x] Read Sift's source (dev.to/ashg2099/i-built-an-open-source-multi-agent-fact-checker-heres-how-it-works-5eah) and note which patterns to reuse — Done: `docs/01-architecture.md` has "Sift Reuse Notes" section
- [x] Fetch latest LangGraph docs and Tavily Python SDK docs before writing any agent code — Done: LangGraph v1.0.9 + Tavily v0.7.23 API patterns noted in `docs/01-architecture.md`
- [x] Build standalone spike script `apps/api/spike.py`: 5-agent LangGraph pipeline (ClaimDecomposer → EvidenceRetriever → SourceScorer → SynthesisAgent → CriticAgent) with Gemini + Tavily, no FastAPI, runs from CLI — Done: prints structured verdict dict with cited sources
- [x] Run spike on 5 test claims spanning different domains (immigration, health, politics, science, economics); record output in `docs/02-spike-results.md` — Done: all 5 results, confidence scores, honest notes committed
- [x] Gate: if fewer than 3 of 5 claims return a reasonable verdict with sources — Done: 4/5 defensible (gate: 3+). Two findings carried to M2: CriticAgent recency-prior bug + Gemini free-tier quota

---

### Milestone 1: Scaffold
**Goal:** Both apps run locally, folder structure in place, all dependencies installed, context trackers created.

Tasks:
- [x] Create `apps/api/` Python project: `pyproject.toml`, `requirements.txt` (pinned current versions), `src/` layout per Project Structure — Done: `uvicorn src.main:app` serves `{"status":"ok"}` at `/health` (smoke-tested)
- [x] Create `apps/web/` Next.js project (TypeScript, Tailwind, App Router) — Done: Next.js **16.2.9** (current stable; PLAN said 15.x — used latest per verify rule), React 19.2.4. `localhost:3000` returns 200
- [x] Set up root `package.json` with delegating scripts (`dev`, `lint`, `typecheck`, `test`) — Done: `npm run dev/lint/typecheck/test` at root delegate to web
- [x] Create `.env.example` with all variables — Done: committed; `.env`/`.env.local` in `.gitignore`
- [x] Set up GitHub Actions CI: `.github/workflows/ci.yml` — Done: two jobs (api: ruff+pytest; web: lint+typecheck+build) on push/PR to main
- [x] Create `PROJECT.md` — Done: already present, kept in sync
- [x] Add root `CLAUDE.md` with content `See PROJECT.md for project context.` — Done: present
- [x] Gate: `npm run lint`, `npm run typecheck`, `npm run test` pass; ruff + pytest pass; `/health` returns 200; Next.js dev starts clean — **all pass**

---

### Milestone 2: Core Pipeline (FastAPI + LangGraph)
**Goal:** `POST /verify` runs the 5-agent pipeline end-to-end and returns a VerifyResponse. No caching yet.

Tasks:
- [x] Define shared Pydantic models in `apps/api/src/lib/types.py`: `VerifyRequest`, `VerifyResponse`, `Source`, `VerdictEnum` (+ `SourceMode`, `DomainType`) — Done: import + validation tests pass
- [x] Implement LLM client singleton in `apps/api/src/lib/gemini.py` — Done: provider-agnostic (env-driven model), `invoke()` with backoff + `invoke_json()`. Live test passes
- [x] Implement Tavily client in `apps/api/src/lib/tavily.py` with `search(query, source_mode)` — Done: strict applies allowlist, flexible all results; both modes return ≥1 (live test)
- [x] Build `ClaimDecomposer` — Done: returns 1–4 sub-claims, degrades to [claim] on failure (live test)
- [x] Build `EvidenceRetriever` — Done: Tavily per sub-claim, dedup, strict→flexible fallback flag (live test)
- [x] Build `SourceScorer` — Done: `.gov`=1.0, `.edu`=0.85, news=0.7, blog=0.4; filters <0.4; sorts (unit test, no keys)
- [x] Build `SynthesisAgent` — Done: returns valid VerdictEnum + confidence 0–1 on canned evidence (live test)
- [x] Build `CriticAgent` — Done: carries M0 recency-prior fix; confidence<0.5→insufficient (deterministic, unit-tested no keys); conflicting evidence→contested (live test)
- [x] Wire agents into LangGraph in `apps/api/src/features/verify/pipeline.py` — Done: `run()` returns VerifyResponse; graph compiles/invokes
- [x] Expose `POST /verify` in `features/verify/router.py`, registered in `main.py` — Done: e2e TestClient test returns 200 + valid VerifyResponse (refuted/insufficient for Eiffel-in-London), `cached: false`
- [x] Gate: pytest passes (20/20 live; CI-safe skips without keys); ruff passes; e2e endpoint validated — **all pass**

---

### Milestone 3: Cache + Storage
**Goal:** Results cached in Redis (7-day TTL). Recent searches stored in Supabase. `GET /recent-searches` works.

Tasks:
- [ ] Create Supabase project (free tier), run the schema from the Supabase Schema section in the SQL editor, verify table exists — Done when: Supabase dashboard shows `searches` table with correct columns
- [ ] Implement Redis cache layer in `apps/api/src/features/cache/redis_cache.py`: `get(key)`, `set(key, value, ttl_seconds=604800)` using Upstash REST API (fetch Upstash docs; use `upstash-redis` Python SDK) — Done when: pytest test sets and gets a value, and a key with 1-second TTL expires after 2 seconds
- [ ] Implement cache key generation: `SHA-256("{claim.strip().lower()}:{source_mode}")` — Done when: pytest test confirms same claim with different casing/whitespace produces same key; different claim produces different key
- [ ] Update `POST /verify` handler: check cache before pipeline; store result in Redis + insert row in Supabase `searches` table after pipeline; set `cached` and `cached_at` fields in response — Done when: two identical requests return same result; second response has `cached: true`; Supabase `searches` table has 1 row (deduplicated by cache, so only first request inserts)
- [ ] Implement `GET /recent-searches` endpoint: query Supabase `searches` ordered by `searched_at desc`, paginated — Done when: `curl localhost:8000/recent-searches?limit=5` returns JSON matching the API contract
- [ ] Gate: `pytest apps/api/tests/` passes; two identical POSTs: second returns `cached: true`; recent-searches returns the claim from the first POST

---

### Milestone 4: Frontend
**Goal:** A real user can submit a claim, see a verdict with sources, browse recent searches, and view the metrics dashboard.

Tasks:
- [ ] Build typed API client in `apps/web/src/lib/api.ts`: `verifyClaim(claim, sourceMode)` and `getRecentSearches(limit, offset)` typed to match backend responses — Done when: TypeScript compiles without errors; `tsc --noEmit` passes
- [ ] Build metrics dashboard section in `apps/web/src/features/metrics/MetricsDashboard.tsx`: static stat cards (NewsGuard 35%, Full Fact 80%, Poynter 3:1) + live counters from recent-searches endpoint (total claims, verdict breakdown) — Done when: component renders in browser with all 3 static stats visible; live counters show 0 when DB is empty
- [ ] Build claim search feature in `apps/web/src/features/search/`: `ClaimInput.tsx` (textarea, 500-char limit, char counter), `SourceModeToggle.tsx` (Strict / Flexible), `SearchForm.tsx` composing both — Done when: form renders, char limit enforced, toggle switches state, submit calls `verifyClaim` API
- [ ] Build results display in `apps/web/src/features/results/`: `VerdictBadge.tsx` (color-coded: green=supported, red=refuted, yellow=contested, grey=insufficient_evidence), `ConfidenceBar.tsx`, `ReasoningCard.tsx`, `SourceCard.tsx` (shows title, domain, credibility score bar, snippet, domain type badge), `ResultsPanel.tsx` composing all — Done when: manually passing a mock VerifyResponse renders all components without error
- [ ] Build recent searches feed in `apps/web/src/features/recent/RecentSearches.tsx`: paginated list, each item shows claim snippet + verdict badge + confidence + time ago; clicking loads cached result — Done when: feed renders with mocked data; click navigates to a pre-filled search result
- [ ] Wire home page in `apps/web/src/app/page.tsx`: MetricsDashboard → SearchForm → (on submit) ResultsPanel; RecentSearches in sidebar or below — Done when: full flow works in browser: type claim → click submit → see loading states → see results
- [ ] Add loading states: show step-by-step progress ("Decomposing claim…", "Searching sources…", "Synthesizing verdict…") using polling or a simple animated sequence timed to average pipeline duration — Done when: loading state visible for ≥2 seconds between submit and results
- [ ] Vitest unit tests for `VerdictBadge`, `ConfidenceBar`, `SourceCard` — Done when: `npm --prefix apps/web run test` passes
- [ ] E2E happy path test (Playwright): load page → type claim → toggle to Strict mode → submit → verify ResultsPanel renders with at least one source card — Done when: `npx playwright test` passes
- [ ] Gate: `npm --prefix apps/web run lint` passes; `npm --prefix apps/web run test` passes; Playwright E2E passes; full flow works manually in browser

---

### Milestone 5: Deploy
**Goal:** App is live at a public URL. Backend on Render, frontend on Vercel.

Tasks:
- [ ] Create `render.yaml` or configure Render web service manually: Python runtime, start command `uvicorn src.main:app --host 0.0.0.0 --port $PORT`, set all backend env vars in Render dashboard — Done when: `https://<your-app>.onrender.com/health` returns `{"status":"ok"}`
- [ ] Deploy Next.js to Vercel: connect GitHub repo, set `NEXT_PUBLIC_API_URL` to Render URL in Vercel env vars, set root directory to `apps/web` — Done when: `https://<your-app>.vercel.app` loads home page
- [ ] Update `ALLOWED_ORIGINS` in Render env vars to include the Vercel URL — Done when: CORS no longer blocks requests from the Vercel frontend
- [ ] Update `NEXT_PUBLIC_API_URL` in Vercel to production Render URL; re-deploy — Done when: submitting a claim on the Vercel URL calls the Render API and returns a result
- [ ] Smoke test: submit 3 claims on the live URL; verify Redis caching works (submit same claim twice, second should return `cached: true`); verify recent-searches feed populates — Done when: all 3 pass
- [ ] Add Render keep-alive: GitHub Actions scheduled workflow pings `/health` every 14 minutes to prevent Render free-tier cold starts — Done when: workflow committed; Render logs show regular pings
- [ ] Gate: public URL serves the full flow end-to-end; health endpoint returns 200; `/recent-searches` returns data

---

### Milestone 6: Polish
**Goal:** No obvious errors, edge cases handled, UI is clean enough for an open-source portfolio.

Tasks:
- [ ] Error states: API timeout → show "Fact-check timed out — try again"; empty Tavily results in strict mode → show "No government or academic sources found — switch to flexible mode?"; LLM error → show "Verification failed — please try again" — Done when: each error state renders correctly when the relevant error is simulated
- [ ] Empty state for recent searches (first load): show placeholder message and sample claims users can click to try — Done when: renders when DB is empty
- [ ] Mobile responsive layout: metrics dashboard stacks vertically; search form full-width; source cards stack — Done when: layout is usable at 375px viewport width (check in browser DevTools)
- [ ] Add `cached_at` and `ttl_expires_at` to the result display: "Results from [date] — refreshes after [date]" — Done when: visible on all results, including first-time (non-cached) results
- [ ] README.md: what it is, how to run locally, how to deploy, how to contribute, link to RESEARCH.md — Done when: a developer with zero context can follow the README to run the project locally
- [ ] Gate: mobile layout passes visual check at 375px; all error states reachable; README accurate

---

## Claude Code Commands

> In every session, fetch the latest official docs for any library before coding against it, and keep `PROJECT.md` in sync with what you build.

**Start (Milestone 0 — spike):**
```
claude "Read PLAN.md and PROJECT.md. Start Milestone 0: read Sift's architecture at https://dev.to/ashg2099/i-built-an-open-source-multi-agent-fact-checker-heres-how-it-works-5eah, then fetch latest LangGraph docs and Tavily Python SDK docs. Build the spike script as specified. Run it on all 5 test claims and commit the results. Fetch docs before writing any agent code."
```

**Resume from any milestone:**
```
claude "Read PLAN.md and PROJECT.md. Find the first incomplete task and continue, fetching the latest official docs for any library before using it. Keep PROJECT.md in sync. Mark tasks done as you go. Commit when a milestone is complete."
```

**Test current state:**
```
claude "Read PLAN.md and PROJECT.md. Without building anything new, test everything marked done. Report what works and what's broken."
```

---

## Notes & Decisions

- 2026-06-26 — **API over Python package** — frontend is Next.js (separate runtime from Python backend), so FastAPI REST API is the right boundary. Domain-specific chatbots later are just additional consumers of `POST /verify`.
- 2026-06-26 — **Verdict design: never binary TRUE/FALSE** — research (PNAS, MIT) shows binary labels mislead users. Always surface: verdict enum (supported/refuted/contested/insufficient_evidence) + confidence 0–1 + raw sources + reasoning. Let users judge.
- 2026-06-26 — **7-day TTL chosen** — immigration policy, political facts, and government metrics change frequently enough that 30-day cache is too stale; 7 days balances freshness and Tavily API usage.
- 2026-06-26 — **Strict mode fallback** — if strict mode finds < 3 sources, automatically re-run flexible mode and flag `source_mode_fallback: true`. Don't leave users with an empty result just because they chose strict mode.
- 2026-06-26 — **Study Sift first at Milestone 0** — Sift (LangGraph + Tavily + 5-agent pattern) is the nearest prior art. Reading it before building saves significant time and avoids re-inventing patterns it already validated.
- 2026-06-26 — **No auth** — all searches are public by design. The shared recent-searches feed is a feature, not a bug.
