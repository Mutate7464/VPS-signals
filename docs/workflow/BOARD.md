# BOARD.md — Kanban (single source for "what now / what next")

> Rules & policies: `WORKFLOW.md` §2. Agents read this board at task start and update rows they touch. Admin orders READY top-down; the top row is "do next". Expedite rows (⚡) jump the queue.

**Last updated:** 2026-10-22 (v2 board)

## ACTIVE

| WI | Title | Goal | Column | Since | Blocker / owner | Evidence |
|---|---|---|---|---|---|---|
| WI-002 | Diagnose & fix model signal (Gate 4 FAIL: all 4 USD targets ≈ random) | G-001 | **EXECUTING** — Steps 1–7 done, Step 4 running in bg (feature_engine PID 557122); Step 8 pending human launch | 2026-10-22 | Build agent completed Steps 1–7 (7 commits). Human launching Step 8 when Step 4 finishes. | `reports/sprint4_model_qa.md`, `docs/plans/2026-10-22-WI-002-e2-full-universe-rerun.md` |
| WI-003 | Ingest Phase 1 validation runs + CAD download | G-002 | **DONE** | 2026-10-22 | 546 USD + 350 CAD synced (~97-98% coverage); verifier PASS (824/896 ok, leakage PASS, 72 quarantined); audit CSVs are failure-log style, true failure rate ≈1-2.5% from coverage | `reports/sprint1_ingestion_audit.md` (regenerated 2026-10-22) |

## DONE

| WI | Title | Goal | Done | Evidence |
|---|---|---|---|---|
| WI-001 | Build & run pipeline v1 end-to-end (Sprints 1–5) | G-001 | 2026-10-22 ⚠ QA exception | Gate 4 FAILED; PDFs = structural demo only (`reports/`, `screener_*_20261021.pdf`) |
| WI-000 | Adopt goal→design→plan→execute→QA workflow framework | G-003 | 2026-10-22 | `workflow/WORKFLOW.md`, `RISKS.md` |
| WI-007 | Two-stream docs + human guide + guide/scribe agents | G-001 | DONE | `docs/human/GUIDE.md`; agents verified loaded (`debug agents`) |
| WI-006 | Enforce blocking QA gates in agent workflow | G-003 | DONE | reviewer prompt gate check + WORKFLOW.md §1 rule 4 |

## BACKLOG

| WI | Title | Goal | Size | Gate |
|---|---|---|---|---|
| WI-004 | Ingest Phase 2 pacing restore (aggressive targets) | G-002 | S | deferred to next week by admin (2026-10-22); gate 1/3 clean runs |
| WI-008 | Quarantine triage (72 tickers: 70 CB-01 extreme returns, 2 CB-02 short history) + BRK.B/ELE empty-response fix | G-002 | S/M | before next training run |
| WI-005 | Post-MVP: EP-06 index scraper · EP-07 Telegram digest · EP-08 regime-conditional tuning | G-001 | L — decompose | model signal restored (WI-002) |

## Column policies
BACKLOG → unprioritized ideas, size-tagged · READY → meets Definition of Ready, admin-ordered · DESIGN/PLAN → Plan agent working (WIP 2) · EXECUTING → Build active (WIP 1) · QA/GATE → reviewer + human gate · DONE → DoD met · BLOCKED → named owner + reason; aging >7d flagged weekly.

**Risks:** `RISKS.md` (reviewed weekly). **Retros:** `retros/YYYY-WW.md`.
