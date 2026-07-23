# FactCheck

Open-source, domain-agnostic fact-checking for the general public. Submit any claim — a political statement, a government statistic, a news quote — and get back a **calibrated verdict** (`supported` / `refuted` / `contested` / `insufficient_evidence`) with **credibility-scored sources**, a **confidence** score, and **plain-English reasoning**. Never a bare true/false.

The engine is a Python + LangGraph **5-agent pipeline** (decompose → retrieve → score → synthesize → critique) on **Gemini 2.5 Flash** + **Tavily** real-time web search, with results cached in **Turso** (libSQL) for 7 days. All searches are public — the recent-searches feed shows what everyone has checked. The same `POST /verify` API is designed to power future domain-specific checkers (H1B visa, political news, etc.).

> Status: Milestones 0–4 done and validated live end-to-end. Deploy (M5) and polish (M6) are next. See [PROJECT.md](PROJECT.md) for the living status and [PLAN.md](PLAN.md) for the milestone plan.

---

## Architecture

```
Browser (Next.js)  ──POST /verify──▶  FastAPI  ──▶  Turso cache?
                                                     │ hit → return {cached:true}
                                                     │ miss ↓
                                        LangGraph 5-agent pipeline:
                                        decompose → retrieve → score → synthesize → critique
                                                     ↓
                                        store in Turso (cache + history)
                   ◀──VerifyResponse────────────────┘
```

Full request/data flow and agent details: [docs/01-architecture.md](docs/01-architecture.md).

| Layer | Choice |
|---|---|
| Frontend | Next.js 16 (App Router, React 19, TypeScript, Tailwind 4) → Vercel |
| Backend | FastAPI (Python 3.12) + LangGraph → Render |
| LLM | Gemini 2.5 Flash via `langchain-google-genai` (model set by `GEMINI_MODEL`) |
| Web search | Tavily |
| Cache + history | Turso (libSQL) — single DB; 7-day TTL cache (app-enforced) + recent-searches |
| Tests | pytest (api) · Vitest + Playwright (web) · GitHub Actions CI |

---

## Repo layout

```
apps/
  api/   FastAPI backend — src/agents (5 agents), src/features (verify, cache, history), src/lib
  web/   Next.js frontend — src/features (search, results, metrics, recent), src/lib
docs/    architecture + spike results
PROJECT.md   living status/context tracker
PLAN.md      milestone plan
```

---

## Local development

**Prerequisites:** Python 3.12+, Node 20+, a [Turso](https://turso.tech) account + CLI, and free-tier keys for [Google AI Studio](https://aistudio.google.com) (Gemini) and [Tavily](https://app.tavily.com).

### 1. Backend (`apps/api`)

```bash
cd apps/api
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Create **`apps/api/.env`** (this is the file the backend loads — see gotchas below):

```
GEMINI_API_KEY=your_google_ai_studio_key
TAVILY_API_KEY=your_tavily_key
TURSO_DATABASE_URL=libsql://<your-db>-<org>.turso.io
TURSO_AUTH_TOKEN=your_turso_token
# optional: GEMINI_MODEL (default gemini-2.5-flash), ALLOWED_ORIGINS (default http://localhost:3000)
```

Provision Turso once:

```bash
turso db create factcheck
turso db shell factcheck < apps/api/migrations/001_init.sql   # creates cache + searches tables
turso db show factcheck --url        # → TURSO_DATABASE_URL
turso db tokens create factcheck     # → TURSO_AUTH_TOKEN
```

Run it:

```bash
uvicorn src.main:app --reload      # serves http://localhost:8000
```

Smoke test:

```bash
curl -s localhost:8000/health
curl -s -X POST localhost:8000/verify -H 'content-type: application/json' \
  -d '{"claim":"The Eiffel Tower is in Paris","source_mode":"flexible"}'
```

Run the second `curl` twice — the second response should be `"cached":true`.

### 2. Frontend (`apps/web`)

```bash
cd apps/web
npm install
npm run dev                        # serves http://localhost:3000
```

The frontend defaults `NEXT_PUBLIC_API_URL` to `http://localhost:8000`. Open http://localhost:3000 and submit a claim.

### ⚠️ Local-dev gotchas (these cost real debugging time)

- **Env file location:** the backend loads `apps/api/.env` and ignores the repo-root `.env` when both exist. Put backend keys in `apps/api/.env`.
- **`uvicorn --reload` does not reload `.env`** — it only watches `.py` files. After editing env vars, fully restart uvicorn (Ctrl+C + rerun).
- **macOS + python.org Python 3.14 SSL error:** Turso calls fail with `CERTIFICATE_VERIFY_FAILED` because that Python build ships no CA bundle (Gemini/Tavily work — they bundle their own). Fix once per shell:
  ```bash
  export SSL_CERT_FILE="$(python -c 'import certifi; print(certifi.where())')"
  ```
  …then start uvicorn, or run the installer's `Install Certificates.command` for a permanent fix. Linux (and Render) are unaffected.
- **Turbopack "Could not find the module … in the React Client Manifest" error** (blank page / dev-overlay alert, can also fail `test:e2e`): a stale Turbopack cache. Clear it and restart:
  ```bash
  rm -rf apps/web/.next
  ```

---

## Testing

```bash
# backend
cd apps/api && source .venv/bin/activate && pytest      # live tests skip without keys

# frontend
cd apps/web
npm run lint
npm run typecheck
npm run test          # Vitest unit tests
npm run test:e2e      # Playwright E2E (network-mocked; no backend needed)
```

CI (GitHub Actions) runs lint + typecheck + tests + build on every push to `main`.

---

## API

- **`POST /verify`** — `{ claim, source_mode: "strict" | "flexible" }` → `{ claim, verdict, confidence, reasoning, sources[], cached, cached_at, ttl_expires_at, sub_claims[], source_mode, source_mode_fallback }`
- **`GET /recent-searches`** — `?limit&offset` → `{ searches[], total }`
- **`GET /health`** — `{ status: "ok" }`

---

## Deployment

Backend → Render (Python, start `uvicorn src.main:app --host 0.0.0.0 --port $PORT`, set all backend env vars). Frontend → Vercel (root dir `apps/web`, set `NEXT_PUBLIC_API_URL` to the Render URL). Set `ALLOWED_ORIGINS` on Render to the Vercel URL for CORS. (Milestone 5 — in progress.)
