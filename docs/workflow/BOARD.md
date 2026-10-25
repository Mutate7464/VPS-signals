# BOARD.md — Kanban (single source for "what now / what next")

> Rules & policies: `WORKFLOW.md` §2. Agents read this board at task start and update rows they touch. Admin orders READY top-down; the top row is "do next". Expedite rows (⚡) jump the queue.

**Last updated:** 2026-10-25 (PM cycle 7)

## ACTIVE

| WI | Title | Goal | Column | Since | Blocker / owner | Evidence |
|---|---|---|---|---|---|---|
| WI-008 | Quarantine triage execution (72 dead-letter tickers: per-case verification + reinstate/keep decisions) | G-002 | **PLAN** — do-next (admin order 2026-10-25); brief: `docs/workflow/briefs/2026-10-25-WI-008-quarantine-percase-brief.md` | 2026-10-25 | Build produces evidence per case; **reinstate/keep is a human gate, no auto-reinstatement**. ELE re-download is admin-owned (Mac/IBKR Gateway) — out of Build scope. Known input defect: 2020-03-09 cluster classified inconsistently (OVV/WES → GENUINE_VOL vs CVE/APA/OXY/MTDR/PR/SM same date → SPLIT_LOOKALIKE); classifier output is a hypothesis, not evidence. | `reports/wi008_quarantine_triage.md` |
| WI-009b | Make contrastive ranking beat the E5 factor baseline (WI-009 follow-up, admin APPROVED 2026-10-25) | G-001 | READY — queued after WI-008 | 2026-10-25 | Seed: gate brief APPROVE branch (`docs/human/briefings/2026-10-25-gate-WI-009-contrastive-ranking.md`). Open questions: model val rank-IC +0.043 vs rev_1m |IC| 0.157 (undertrained — 40 dates/2 epochs — or genuinely weaker); REIT concentration; shortlist lag (target-free inference path). | `reports/wi009_train_CAD.json`, `reports/wi009_top10_CAD.csv`, plan `docs/plans/2026-10-24-WI-009-contrastive-learning.md` |

## DONE

| WI | Title | Goal | Done | Evidence |
|---|---|---|---|---|
| WI-009 | Implement Technical Trading Approach (D-003 Option 2 — contrastive pairwise ranking on CAD) | G-001 | 2026-10-25 — gate decision: **APPROVED**, continue as WI-009b | Build commit 19795ac; PM cycle 6 verification (4acae0b): 11/11 leak+sampler tests, 56 full suite, top-10 CSV verified; gate brief `docs/human/briefings/2026-10-25-gate-WI-009-contrastive-ranking.md`; E5 split-leak found by reviewer #2, fixed and regression-locked (`tests/test_e5_split_no_leak.py`) |
| WI-002 | Diagnose & fix model signal (Gate 4 FAIL: all 4 USD targets ≈ random) | G-001 | 2026-10-24 — gate decision: **pivot to WI-009** (hybrid technical-factor, D-003); no separate target/metric redesign item | E3–E5 verdicts (H3 yes / H2 no / H4 no) in `reports/diag_D002_summary.md` + e2–e5 reports; PM cycle 4 verification (ee6f93e); `logs/e3_runs.out` |
| WI-003 | Ingest Phase 1 validation runs + CAD download | G-002 | 2026-10-22 | 546 USD + 350 CAD synced (~97-98% coverage); verifier PASS (824/896 ok, leakage PASS, 72 quarantined) — `reports/sprint1_ingestion_audit.md` |
| WI-001 | Build & run pipeline v1 end-to-end (Sprints 1–5) | G-001 | 2026-10-22 ⚠ QA exception | Gate 4 FAILED; PDFs = structural demo only (`reports/`, `screener_*_20261021.pdf`) |
| WI-000 | Adopt goal→design→plan→execute→QA workflow framework | G-003 | 2026-10-22 | `workflow/WORKFLOW.md`, `RISKS.md` |
| WI-007 | Two-stream docs + human guide + guide/scribe agents | G-001 | DONE | `docs/human/GUIDE.md`; agents verified loaded (`debug agents`) |
| WI-006 | Enforce blocking QA gates in agent workflow | G-003 | DONE | reviewer prompt gate check + WORKFLOW.md §1 rule 4 |

## BACKLOG

| WI | Title | Goal | Size | Gate |
|---|---|---|---|---|
| WI-004 | Ingest Phase 2 pacing restore (aggressive targets) | G-002 | S | deferred to next week by admin (2026-10-22); gate 1/3 clean runs |
| WI-005 | Post-MVP: EP-06 index scraper · EP-07 Telegram digest · EP-08 regime-conditional tuning | G-001 | L — decompose | signal direction pivoted to WI-009 (2026-10-24) |

## Column policies
BACKLOG → unprioritized ideas, size-tagged · READY → meets Definition of Ready, admin-ordered · DESIGN/PLAN → Plan agent working (WIP 2) · EXECUTING → Build active (WIP 1) · QA/GATE → reviewer + human gate · DONE → DoD met · BLOCKED → named owner + reason; aging >7d flagged weekly.

**Risks:** `RISKS.md` (reviewed weekly). **Retros:** `retros/YYYY-WW.md`.
