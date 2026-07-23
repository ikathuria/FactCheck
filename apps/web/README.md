# FactCheck — web

Next.js 16 frontend for [FactCheck](../../README.md). Submits claims to the FastAPI backend's `POST /verify` and renders the verdict, confidence, reasoning, and credibility-scored sources, plus the public recent-searches feed and a metrics dashboard.

> ⚠️ Next.js 16 has breaking changes vs. earlier versions — read the bundled docs in `node_modules/next/dist/docs/` before changing app-router code (see [AGENTS.md](AGENTS.md)).

## Develop

```bash
npm install
npm run dev        # http://localhost:3000
```

Set `NEXT_PUBLIC_API_URL` if the backend isn't at `http://localhost:8000` (create `.env.local`). The backend must be running — see the [root README](../../README.md) for backend setup.

## Scripts

| Command | What it does |
|---|---|
| `npm run dev` | Dev server (Turbopack) |
| `npm run build` | Production build |
| `npm run lint` | ESLint |
| `npm run typecheck` | `tsc --noEmit` |
| `npm run test` | Vitest unit tests |
| `npm run test:e2e` | Playwright E2E (network-mocked; no backend needed) |

## Structure

```
src/
  app/                Next.js App Router (layout, page, globals)
  features/
    search/           ClaimInput, SourceModeToggle, SearchForm, SearchProgress
    results/          VerdictBadge, ConfidenceBar, ReasoningCard, SourceCard, ResultsPanel
    metrics/          MetricsDashboard
    recent/           RecentSearches
  lib/                api client, types, verdict/domain metadata, time helpers
```
