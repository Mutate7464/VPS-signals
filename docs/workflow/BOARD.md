# BOARD.md — Kanban (single source for "what now / what next")

> Rules & policies: `WORKFLOW.md` §2. Agents read this board at task start and update rows they touch. Admin orders READY top-down; the top row is "do next". Expedite rows (⚡) jump the queue.

**Last updated:** 2026-10-24 (PM cycle 5)

## ACTIVE

| WI | Title | Goal | Column | Since | Blocker / owner | Evidence |
|---|---|---|---|---|---|---|
| WI-009 | Implement Technical Trading Approach (D-003 Option 2 — hybrid technical-factor; contrastive pairwise ranking first) | G-001 | **PLAN** — do-next | 2026-10-24 | Admin approved direction 2026-10-24 (pivot from WI-002 gate). Planner pass pending: refine draft plan to workflow-contract format — per-step verification commands, D-003 Option-2 scope reconciliation (plan is contrastive-only; D-003 selects the hybrid), reuse the existing 89 features in `src/feature_engine.py` (draft Step 2 rebuilds RSI/MACD/BB/ATR that already exist), and an explicit PyTorch-on-8GB-VPS decision (repo is sklearn/xgboost; guardrails n_jobs≤2, float32, bounded memory). Then EXECUTING. | `docs/workflow/designs/D-003-technical-trading-approach.md`, `docs/tech_approach/2026-W44/briefs/contrastive-learning-brief.md`, `docs/tech_approach/2026-W44/plans/contrastive-learning-plan.md` |

## DONE

| WI | Title | Goal | Done | Evidence |
|---|---|---|---|---|
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
| WI-008 | Quarantine triage (72 tickers: 70 CB-01 extreme returns, 2 CB-02 short history) + BRK.B/ELE empty-response fix | G-002 | S/M | before next training run — **triage analysis DONE 2026-10-23**: 2 rows already clean (stale), ~44 corp-action level-step artifacts, ~26 flagged genuine-vol (several actually restructuring artifacts — needs per-case verification); BRK.B resolved (downloads as `BRK B`, in universe); ELE missing — needs Mac re-download. Execution plan pending admin decision. | `reports/wi008_quarantine_triage.md` |
| WI-005 | Post-MVP: EP-06 index scraper · EP-07 Telegram digest · EP-08 regime-conditional tuning | G-001 | L — decompose | signal direction pivoted to WI-009 (2026-10-24) |

## Column policies
BACKLOG → unprioritized ideas, size-tagged · READY → meets Definition of Ready, admin-ordered · DESIGN/PLAN → Plan agent working (WIP 2) · EXECUTING → Build active (WIP 1) · QA/GATE → reviewer + human gate · DONE → DoD met · BLOCKED → named owner + reason; aging >7d flagged weekly.

**Risks:** `RISKS.md` (reviewed weekly). **Retros:** `retros/YYYY-WW.md`.
