# WI-018 execution log — condition-first first_touch @ w≈34 (USD)

Plan: `docs/plans/26-W45-WI-018-condition-first-first-touch.md` (frozen)
ADR: `docs/workflow/designs/D-018-condition-first-first-touch.md` (accepted)

## EXECUTION LOG

Rows are `HH:MM | step N | outcome | concern?` — one self-contained row per step, ≤50 words.

| row | outcome | concern / evidence |
|---|---|---|
| — | STATUS: PLAN — awaiting admin plan approval → Build dispatch | contract-checked by PM 2026-11-01: 5 steps, verify commands reference real helpers (fold_blocks/benjamini_hochberg/cost_overlay/block_bootstrap_margin all grep-verified) |
| 02:54 \| step 1 | preflight PASS on disk | 593 USD symbols in both dirs, 2,340,073 rows, `first_touch_34` finite 2,319,911 (== WI-017 run2_summary n_rows) shares 37.6/29.7/32.7, keep-cell coverage 98.06%; `reports/wi018/preflight_USD.json` written; 29 tests pass (`uv run pytest tests/test_wi018_data_probe.py -q` EXIT:0) |
| 02:54 \| step 1 (assumption) | "264 feature columns" read as 264 non-`date` columns | file has 265 columns including `date`; consistent with run5 `n_features=264` and keep+drop=264 |
| 03:08 \| step 2 | G1 atlas PASS: 704 cells (88 features × 8 states), 702 estimable, 2 unevaluable (`donchian_break_13` q2 n_dates=1; `donchian_break_55` q2 n=0) | top lifts are amplitude-mechanical (atr_pct_34 q1 up_lift −0.160, q5 +0.133: touch-rate shift, not direction); family check: atr_pct representative (share 0.973), fib_dist NOT (0.694, best fib_dist_21), range_pos NOT (0.805, best range_pos_102) → those two families are single-window evidence; 19 tests + `--check-report` PASS; 8m37s run; new shared modules `src/wi018/streaming.py`, `src/wi018/rates.py` (state binning + rate/CI estimators reused by G2) |

INTERIM (not a final status): steps 1–2/5 verified, session active — an interrupted session means the remaining steps were not executed, not that a step is blocked.
