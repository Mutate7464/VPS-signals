# WI-016 — Triple-Barrier Fib-Ladder Labels

**ID:** WI-016  
**Title:** Triple-barrier fib-ladder labeling + E5 meta-labeling  
**Goal:** G-001 — produce a gated, reproducible daily USD/CAD shortlist using fib-ladder triple-barrier outcomes and E5 meta-labeling.  
**Status:** Planned  
**Date:** 2026-10-29

## GOAL

Produce a probe-gated USD/CAD daily shortlist from triple-barrier labels and E5 meta-labeling; do not train or emit actions unless the probe gate clears.

## CONSTRAINTS

- Follow accepted design `docs/workflow/designs/D-016-triple-barrier-fib-labeling.md`; its definition-gate answers are final.
- `n_jobs=2` (never `-1`); cast calculated feature/label frames to `float32` immediately; stream by symbol / use `pyarrow.dataset`, never an all-ticker uncompressed frame.
- Point-in-time, trailing-only features; NaN-mask incomplete forward windows. Parametrize each run by `--market USD|CAD`.
- Daily shortlist only; no live trading or order execution; no secrets. Preserve human gate.
- All new reports/artifacts use `wi016_` names. Never overwrite frozen `reports/wi014_*` artifacts. Keep the test suite green (`uv run pytest`).
- Existing design is accepted; do not create a duplicate ADR. Stop for PM/admin review after the probe step; model/action work is conditional on an explicit clear result.

## STEPS

1. **Horizon-specific embargo.** In `src/xgb_trainer.py`, add a helper deriving `max(20, horizon)` and pass that per-target embargo to `PurgedWalkForwardSplit` and every `purged_holdout` call, including calibration/final holdouts. Keep the configured 20-bar floor and prevent an explicit CLI default from weakening the per-target horizon embargo. Add regression tests for horizons 144 and 233 asserting every fold/holdout train date is at least `h` trading-date positions before validation/calibration. **Accept:** no train date falls within the horizon embargo in either split path; existing 20-bar behavior remains for short targets. **Verify:** `uv run pytest tests/test_xgb_trainer.py -k 'embargo or purged_holdout'`.

2. **Triple-barrier label package.** Add `src/wi016/__init__.py` and `src/wi016/triple_barrier.py` (tests in `tests/test_triple_barrier.py`). Reuse `src.targets.wilder_atr` and compatible forward-window machinery; compute first touch of symmetric `±k·ATR_t` barriers for `k={1.5,2.0}` and vertical horizons `{8,21,55,144,233}`. Emit three classes: profit touch `+1`, stop touch `-1`, and vertical outcome as sign of realized return (`-1/0/+1`, per accepted design); mask unavailable trailing history and incomplete forward windows with NaN. Process one symbol at a time, expose `--market USD|CAD`, and report per-horizon/k barrier-touch density, class balance, and events per fold under `reports/wi016_*`. **Accept:** tests cover each touch, vertical sign/neutral, horizon tail mask, ATR causality, both markets' CLI parameterization, and float32 outputs; no future data enters ATR thresholds. **Verify:** `uv run pytest tests/test_triple_barrier.py`.

3. **Unified fib feature grid and admission.** Update `config/settings.yaml` and `src/feature_engine.py` to build smooth-family windows `{3,8,21,55,144,233}` and retain dense fib windows only for `kama_er`, `hurst`, `entropy`, and `vwap_zscore`; remove classic/fib/WI-015 cross-grid near-duplicates. Rebuild the ADF/VIF/MI admission stage with VIF threshold `8.0` and relaxed MI admission, then per-target prune feature clusters at absolute Spearman `ρ>0.7`, retaining the member with highest same-sign IC; admit only features with at least 500 labeled events. **Accept:** tests establish exact family grids, no duplicated window variants, VIF=8, one same-sign-IC representative per correlated cluster, and the 500-event minimum. **Verify:** `uv run pytest tests/test_wi016_features.py`.

4. **Single legacy comparison run.** Add `src/wi016/probe.py` to run old five-label generation versus triple-barrier labels once on the same market panel and produce a rank-IC comparison plus the label-density diagnostics in `reports/wi016_*`. Retain legacy label code in `src/targets.py` as rebuildable, but stop invoking legacy generation in the new primary pipeline after this comparison. **Accept:** comparison uses identical symbol/date rows and feature panel for both label sets, writes a `wi016_` report, and does not modify frozen artifacts. **Verify:** `uv run pytest tests/test_wi016_probe.py -k legacy_comparison`.

5. **Probe-first gate (mandatory stop).** In `src/wi016/probe.py`, compute within-date rank-IC by horizon for unified features and E5 (`src/factors/e5_baseline.py:factor_frame` is the sole E5 definition) versus barrier outcomes; apply Benjamini–Hochberg FDR across the target×feature grid, five-seed placebo, the WI-009b same-sign clause, and cost overlay/NO_TRADE default. Write complete per-market results and decision evidence to `reports/wi016_*`. **Accept:** reports include every horizon, feature/E5 IC, FDR, placebo, class/density and fold counts, cost result, and an unambiguous clear/not-clear decision using the accepted same-sign bar; tests cover FDR and decision logic. **Verify:** `uv run pytest tests/test_wi016_probe.py`. **STOP after verification and report paths; PM/admin must review the probe report. Do not start step 6 unless a target is explicitly cleared.**

6. **Conditional meta-labeler and actions.** Only after step 5 clears a target, implement `src/wi016/meta_labeler.py` and `src/wi016/actions.py`. Define primary events as E5 top-decile rank per date/market, long side; train on top-two-decile expansion and retain a decile flag for stratified analysis. Use existing `src.xgb_trainer` model/calibration machinery to predict bet P&L>0 with the horizon-specific embargo and five-seed placebo. Synthesize entry, barrier/time-stop exit, meta-probability size, and abstain/NO_TRADE decisions under the cost overlay. Emit a **new** WI-014-compatible shortlist artifact at `reports/wi016_shortlist_{market}.parquet`; never write to `reports/wi014_*`. **Accept:** tests verify event/decile semantics, leakage-safe folds, cost-aware action/abstention rules, and output schema/path; no order execution exists. **Verify:** `uv run pytest tests/test_wi016_meta_labeler.py tests/test_wi016_actions.py`.

## OUT OF SCOPE

- Auto-execution of orders; live trading.
- ELE/Mac re-downloads.
- Editing/replacing WI-014 or WI-015 frozen artifacts, or replacing the shipped screener before gate approval.
- Proceeding to model/actions when no probe target clears; that outcome is a stop, not permission to relax the gate.

## EXECUTION LOG
