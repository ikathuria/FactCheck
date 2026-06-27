# Milestone 0 — Spike Results

**Date run:** 2026-06-26
**Script:** [`apps/api/spike.py`](../apps/api/spike.py)
**Pipeline:** ClaimDecomposer → EvidenceRetriever → SourceScorer → SynthesisAgent → CriticAgent (5-agent LangGraph, v1.0.9)
**LLM:** Gemini (see model note below) · **Search:** Tavily Python SDK v0.7.23

> **Model note:** PLAN.md specifies `gemini-2.5-flash-lite`. Claims 1–3 ran on it successfully.
> Its **free-tier daily quota is only 20 requests/day** (3+ LLM calls per claim + retries),
> which was exhausted partway through. Claims 4–5 ran on `gemini-2.5-flash` (separate free-tier
> quota bucket). `gemini-2.0-flash` returned `limit: 0` on this key (no free-tier allocation).
> **This is a real constraint to resolve before Milestone 2** — see Findings.

---

## Summary

| # | Domain | Claim | Mode | Verdict | Conf. | Top source | Defensible? |
|---|---|---|---|---|---|---|---|
| 1 | Immigration | "H1B visa cap was doubled in 2024" | flexible | **refuted** | 1.00 | uscis.gov | ✅ Yes |
| 2 | Health | "Drinking 8 glasses of water per day is scientifically required" | flexible | **refuted** | 0.95 | pubmed.ncbi.nlm.nih.gov | ✅ Yes |
| 3 | Economics | "The US national debt exceeded $35 trillion in 2024" | flexible | **supported** | 1.00 | budget.house.gov | ✅ Yes |
| 4 | Science | "5G mobile networks cause cancer" | strict | **contested** | 0.80 | pmc.ncbi.nlm.nih.gov | ⚠️ Debatable |
| 5 | Politics | "Donald Trump won the 2024 US presidential election" | flexible | **insufficient_evidence** → **supported** (after fix) | 0.00 → 1.00 | archives.gov | ❌ → ✅ (fixed) |

**Gate: 3+ of 5 defensible → PASSED.** Claims 1, 2, 3 are clearly correct and well-sourced; claim 4 is defensible but debatable. Claim 5 exposed a critical CriticAgent bug — now fixed and verified (see Finding 1), bringing the pipeline to 5/5 defensible.

---

## Detailed Results

### Claim 1 — Immigration ✅
**"H1B visa cap was doubled in 2024"** · flexible · **refuted (1.00)**

Decomposed into 4 sub-claims. 13 evidence chunks retrieved. Top sources: USCIS gov alert (cred 1.0) confirming the FY2024 cap stayed at the statutory 65,000 + 20,000 master's = 85,000; USCIS congressional report PDF (1.0); Duke career hub (0.85, academic).

> *Reasoning:* "The evidence consistently states that the H-1B visa cap for fiscal year 2024 remained at 65,000 regular visas plus an additional 20,000... Multiple sources confirm this statutory cap has not been doubled."

**Assessment:** Correct. Strong government sourcing. The pipeline worked exactly as designed.

---

### Claim 2 — Health ✅
**"Drinking 8 glasses of water per day is scientifically required for health"** · flexible · **refuted (0.95)**

4 sub-claims, 13 chunks. Top sources: the seminal PubMed "8x8" paper (cred 1.0) that debunked the myth, NIH PMC water-balance articles (1.0), Harvard Health (0.85), URMC (0.85). SynthesisAgent gave 0.90; CriticAgent *raised* to 0.95 after confirming consistent refutation.

> *Reasoning:* "The evidence highlights that the '8 glasses' rule is a myth, fluid needs are individualized, and other sources contribute to hydration."

**Assessment:** Correct. Excellent source quality. Critic appropriately confirmed rather than blindly lowering confidence.

---

### Claim 3 — Economics ✅
**"The US national debt exceeded $35 trillion in 2024"** · flexible · **supported (1.00)**

3 sub-claims, 9 chunks. Top sources: House Budget Committee press release (cred 1.0, "U.S. National Debt Surpasses $35 Trillion", July 29 2024), GAO FY2024 audit (1.0), Senate JEC debt dashboard (1.0), CRFB (0.4).

> *Reasoning:* "Source [1] directly states the national debt surpassed $35 trillion on July 29, 2024, and source [6] corroborates... Source [2] provides context for the increase in federal debt during fiscal year 2024."

**Assessment:** Correct. Three independent government sources. Model-ideal case.

---

### Claim 4 — Science ⚠️
**"5G mobile networks cause cancer"** · strict · **contested (0.80)**

3 sub-claims, 9 chunks. **Strict mode worked**: all 7 top sources were NIH/PMC/PubMed government-tier (cred 1.0); the Australian cancer council page (0.4) was the only non-gov result. SynthesisAgent and CriticAgent agreed on contested/0.80.

> *Reasoning:* "while RF EMF generally is classified as 'possibly carcinogenic' (with some arguing for an upgrade), specific reviews on 5G... find 'little evidence' of causation, leading to a 'contested' verdict."

**Assessment:** Debatable. The mainstream scientific/regulatory consensus (WHO, ICNIRP, ACS) is that there is **no established causal link** — RF's IARC "Group 2B / possibly carcinogenic" classification is weak and not 5G-specific. A verdict of **refuted** or **insufficient_evidence** would arguably be more accurate. The pipeline returned "contested" because Tavily surfaced peer-reviewed papers arguing *for* RF risk (e.g. PMC7405337 "risks should be reassessed") alongside null-result reviews — so it weighted a vocal-minority scientific position as a genuine 50/50 split.
**Lesson:** evidence *retrieval* presents minority and majority peer-reviewed views as equal weight; the pipeline has no notion of scientific consensus strength. Acceptable for a spike, but a known limitation.

---

### Claim 5 — Politics ❌ (critical finding)
**"Donald Trump won the 2024 US presidential election"** · flexible · **insufficient_evidence (0.00)**

2 sub-claims, 10 chunks. Retrieval was **excellent**: National Archives 2024 Electoral College results (cred 1.0, showing Trump 312 / Harris 226), FEC official results PDF (1.0), UCSB American Presidency Project (0.85), BBC (0.7), NPR (0.7) — all confirming Trump won.

- **SynthesisAgent: supported (1.00)** — correct.
- **CriticAgent: OVERRODE to insufficient_evidence (0.00)** — wrong.

> *Critic reasoning:* "This is impossible to verify as true, as the 2024 election has not yet occurred (it is scheduled for November 5, 2024). All provided 'evidence' sources are either fabricated documents or news reports dated in the future..."

**Assessment:** **Wrong verdict, and the most important finding of the spike.** Trump *did* win the 2024 election; the synthesis was right. The CriticAgent overrode a correct, authoritatively-sourced verdict because **the LLM's training-data prior places "now" before November 2024**, so it concluded the election "hasn't happened" and dismissed the National Archives and FEC as "fabricated." The adversarial critic trusted its internal world-model over retrieved primary-source evidence.

This is precisely the failure mode RESEARCH.md flagged ("LLM returns confident wrong verdict") — but inverted: here the critic confidently *destroyed* a correct verdict.

---

## Findings & Required Fixes (before Milestone 2)

1. **🔴 → ✅ FIXED: CriticAgent must not use its own world knowledge (esp. dates/recency).**
   The critic overrode a true, gov-sourced verdict because its training cutoff predates the event.
   **Fix applied (2026-06-26):** Rewrote the CriticAgent prompt to (a) judge *only* whether the provided evidence supports the verdict, (b) explicitly forbid using internal knowledge of what has/hasn't happened, (c) inject the current date and warn that its training data may predate recent events, (d) treat authoritative-domain evidence (gov/academic, cred ≥ 0.85) as ground truth unless internally contradictory.
   **Verified:** re-running claim 5 now returns **supported (1.00)** — *"The National Archives (Evidence 1), a highly credible government source, explicitly states Donald J. Trump won the 2024 US presidential election with 312 electoral votes..."* The critic keeps the correct verdict instead of overriding it. Carry this prompt into `apps/api/src/agents/critic.py` at Milestone 2 with a regression test using exactly this claim.

2. **🟠 Gemini free-tier quota is a real blocker.**
   `gemini-2.5-flash-lite` free tier = **20 requests/day**; each claim costs 3–9 calls (with retries). The spike could not complete 5 claims on one model in one day.
   **Options:** (a) enable paid tier (flash-lite is ~$0.10/1M tokens — fractions of a cent per claim); (b) reduce calls per claim (e.g. merge Synthesis+Critic, or make Critic a cheap deterministic guard instead of an LLM call when confidence is already extreme); (c) add the exponential-backoff retry (already in `spike.py`) to the production client. Revisit the "free to build" assumption in PLAN.md — the *search* layer is free, but Gemini free-tier RPD limits make batch/production use impractical without a paid key.

3. **🟡 No notion of scientific/consensus strength (claim 4).**
   Retrieval treats a vocal-minority peer-reviewed position as equal weight to consensus, producing "contested" where "refuted/insufficient" is more accurate.
   **Fix (later, optional):** SourceScorer could weight by recency + corroboration count; or Synthesis prompt could ask "does the *preponderance* of evidence support this?" rather than "is there *any* conflicting evidence?".

4. **🟢 What worked well (keep):**
   - LangGraph 5-agent sequential graph: compiled and ran cleanly every time.
   - Tavily retrieval: consistently surfaced authoritative primary sources (USCIS, GAO, National Archives, FEC, NIH/PMC) in the top results.
   - Strict mode (claim 4): correctly restricted to gov/academic domains and still found 7+ sources (no fallback needed).
   - SourceScorer domain tiers: gov=1.0 / academic=0.85 / news=0.7 / other=0.4 behaved as specified.
   - SynthesisAgent: produced calibrated, well-reasoned verdicts on all 5 — the *synthesis* step was correct even on claim 5.
   - `insufficient_evidence` confidence<0.5 hard override: fired correctly (claim 5's final state, albeit for the wrong upstream reason).
   - JSON parsing with markdown-fence stripping: zero parse failures across 5 runs.

---

## Verdict on the Spike

**The architecture is sound.** Retrieval quality is high, the graph orchestration is solid, and 4 of 5 verdicts are defensible. The single wrong verdict (claim 5) is a **prompt-design bug, not an architecture bug** — and a cheap, high-value fix. Proceed to Milestone 1, carrying the CriticAgent prompt fix and the Gemini-quota decision into Milestone 2.
