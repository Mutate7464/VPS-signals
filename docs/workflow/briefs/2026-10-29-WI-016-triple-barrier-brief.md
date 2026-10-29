# WI-016 planner brief — Triple-barrier fib-ladder labeling + E5 meta-labeling

## Mission

Write the execution plan for WI-016 per the ACCEPTED design `docs/workflow/designs/D-016-triple-barrier-fib-labeling.md`. The design is authoritative — do not re-open answered questions (its "Definition gate — answered" table is final spec).

## Deliverable

Plan file `docs/plans/26-W44-WI-016-triple-barrier-fib-labels.md` with: GOAL / CONSTRAINTS / STEPS (≤6, each = change + acceptance criterion + deterministic verification command) / OUT OF SCOPE. Standard headers (ID, Title, Goal, Status, Date). Sizing: one Build session (≈150 steps) — if it does not fit, split at the natural seam (labels+probe vs model+actions) and say so explicitly with two plan files.

## READ SCOPE (these files only)

1. `docs/workflow/designs/D-016-triple-barrier-fib-labeling.md` — the spec
2. `src/targets.py` — legacy label machinery (wilder_atr, forward rolls) that triple-barrier REUSES
3. `src/xgb_trainer.py` — PurgedWalkForwardSplit (needs per-target embargo = max(20, horizon)) + CalibratedXGB
4. `config/settings.yaml` — windows/params registry
5. `src/factors/e5_baseline.py` — E5 factor_frame (single source of truth for primary events)

## What the plan must cover (order matters — probe gates model spend)

1. **Embargo precondition:** parameterize `PurgedWalkForwardSplit`/`purged_holdout` embargo per horizon (max(20, h)); regression test asserting no train date within h bars of any val date at h=144/233.
2. **Triple-barrier label module** (`src/` new topic package per D-016 folder shape): barriers ±k·ATR (k∈{1.5,2.0}), vertical ∈ {8,21,55,144,233}, 3-class sign-of-return vertical outcome; reuses `src/targets.py` machinery; float32, symbol-sequential, `--market` parametrized. NaN-mask incomplete windows. Log per-horizon density stats (class balance per k, events per fold) to `reports/wi016_*`.
3. **Window-grid unification:** feature families on the accepted grids (smooth: {3,8,21,55,144,233}; fast: dense fib), kill cross-grid near-duplicates; ADF/VIF/MI rebuild with looser admission (VIF 8.0) + ρ>0.7 uniqueness prune (one representative per cluster by same-sign IC) + ≥500 events-per-feature cap.
4. **Legacy comparative probe (one run):** old 5-labels vs new triple-barrier on the same panel, rank-IC report; legacy generation stops after (retired, rebuildable).
5. **Probe gate:** per-horizon within-date rank-IC of unified features + E5 vs barrier outcomes; BH-FDR across grid; 5-seed placebo; same-sign clause bar (WI-009b re-spec wording). STOP row after this step for PM/admin read of the probe report — model steps only proceed if a target clears.
6. **Meta-labeler + actions (conditional on step 5):** E5 top-decile events per date/market (long side), TRAINING on top-2-decile expansion with decile flag per event; XGB via existing trainer machinery predicts bet P&L>0; decision-rule synthesis → entry/exit(time stop)/size(meta-prob)/abstain with cost overlay; emits into WI-014 shortlist artifact path (NEW file — never overwrite frozen `reports/wi014_*`).

## Constraints (hard)

n_jobs=2 never -1 · float32 immediately after calc · no all-ticker uncompressed frame (pyarrow.dataset or symbol iteration) · matplotlib close('all')+gc per batch of 10 · no secrets · no live trading · daily shortlist only · point-in-time trailing-only · all new report paths prefixed `wi016_` (frozen artifacts untouched) · test suite must stay green (`uv run pytest`).

## OUT OF SCOPE (state in plan)

Auto-execution of orders · ELE/Mac re-downloads · WI-014/WI-015 frozen artifacts · replacing the shipped screener before gate approval.
