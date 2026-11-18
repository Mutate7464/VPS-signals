# WI-011 gate brief + decision (human stream)

## GATE DECISION — 2026-10-25 (admin: "accept results")
**WI-011 CLOSED — accepted as documented negative result.**

## What shipped
- Full loop-v2 run (planner → Build, headless) on CAD: preflight, 38 trailing
  point-in-time conditions (15 unit tests), indicator association (89 → 6
  non-redundant), horizon sweep {1,2,5,10,15,20,60,120}d purged ≥ horizon,
  first-ever time-series momentum probe, cost overlay.
- **Verdict: "none survive costs at this universe size"** → screener keeps
  **NO_TRADE default**. Conditions remain descriptive context (annotation,
  attribution), never entries. Valid publishable negative per plan.
- PM verification: 15/15 new tests + **full suite 191 passed (EXIT:0)**,
  step verify greps all green.

## What doesn't ship
- No tradeable rules, no backtest, no optimization (STOP honored).
- IBKR commission params in the cost model are assumptions (repo has no CAD
  schedule; VPS has no web access) — flagged in
  `reports/wi011_tradeable_conditions.md` for admin confirmation.

## Carries forward
- WI-009-series conclusion now quadruple-confirmed: this universe supports
  description, not tradeable rules; future model work needs a new
  target/data spec, probe-first.
- Board/docs: WI-010 classifier consolidation + ELE re-download unchanged
  (admin/Mac-owned).

## Admin doc directives (same session — recorded in WORKFLOW.md §4)
1. Plans + tech files → `YY-WW-…` naming (e.g. `26-W43-WI-011-…`);
   `docs/ingest/CHANGELOG.md` absorbs `ib4-changelog.md`.
2. Keep files small + flat (token discipline).
3. Ingestion workflow question answered: Mac (IB Gateway) downloads →
   `sync_back.py` rsync → VPS `data/raw_ohlcv/market=<CAD|USD>/` → feature
   parquets. Mac remains the download host (ib_async requirement).