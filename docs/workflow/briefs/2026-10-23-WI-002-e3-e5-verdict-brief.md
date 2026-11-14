# Brief — WI-002 Steps 7–8: E5 unpredictability floor + combined verdict

> For the opencode Build agent. Plan: `docs/plans/2026-10-23-WI-002-e3-e5-features-alignment-floor.md`.
> Run ONLY after the E3 chain (`scripts/e3_chain.sh`, log `logs/e3_runs.out`) prints
> `=== E3 CHAIN COMPLETE ===`. Check that first; if still running, wait or report BLOCKED.

## Context (verified 2026-10-23, PM cycle 1)

- Data fixed: features parquet = 1,240,275 rows × 89 float32 features (fib/range block
  included, windows [3,6,9,15,24,39,63,102]). Whitelists 32/32/32/32 (VIF 10, MI pct 15).
- E4 (Step 5) done: **H3 SUPPORTED** — continuous Spearman IC of model prob vs fwd ATR
  return significant on 15d targets (t +4.31 / +3.27) while binary gates fail;
  ticker-prior AUC beats model on all targets (identity-signal component).
- E3 chain in flight: 5 feature-sets (full, no_static, fib_only, legacy19, cs_pct_only)
  × 4 targets × (1 real + 3 placebo) × 5 folds + final, `--resume` per set.
- Training panel is SLIM (mask union only) and panel is freed before training — keep it
  that way; the first E3 attempt died OOM at ~3.7 GB MemAvailable. n_jobs=2 everywhere.

## Your tasks

0. **Step 6 report — E3 ablation summary (generator does NOT exist yet).**
   `scripts/diag_signal.py` only implements `--exp e2|e4|e5`; `--exp e3` must be
   written (plan Step 6 Change section). It reads the per-set artifacts the chain
   produced — `data/oof_USD.parquet` (full), `data/oof_USD_no_static.parquet`,
   `data/oof_USD_fib_only.parquet`, `data/oof_USD_legacy19.parquet`,
   `data/oof_USD_cs_pct_only.parquet`, each with `train_meta_USD[_<set>].json` —
   and produces `reports/diag_D002_e3.md`: per set × target ROC-AUC, PR-AUC lift,
   P@K lift, deflated IC t, placebo z; H2 verdict (any set reaches deflated t > 2.5
   where the legacy19/full baseline doesn't). Follow the existing `run_e4` structure
   and the report-parsing conventions already in the file. Keep memory slim: load
   oof parquets one at a time, cast float32, drop each before the next.
1. **Step 7 — E5:** `uv run python scripts/diag_signal.py --exp e5 --market USD`
   (code committed at 27ae4d5: ridge/logistic on 5 classic factors — mom_12_1, rev_1m,
   vol_20, amihud, size-proxy — vs `fwd_atr_ret_15/20`, purged WF t-stats, n_jobs=2).
   Acceptance: `reports/diag_D002_e5.md` with H4 verdict (rank-IC < 0.01 and t < 2 with
   E3/E4 null ⇒ H4).
2. **Step 8 — Combined verdict:** write `reports/diag_D002_summary.md` — one-line
   verdict per hypothesis (H2 from E3 report, H3 from E4, H4 from E5), each traced to
   its report file; append the verdict matrix to `reports/diag_D002_e2.md` ADR section.
   Update BOARD.md WI-002 row → QA/GATE (STOP for admin).
3. **Final line in the plan file:** `STATUS: DONE|BLOCKED|ERROR` plus a one-line summary.
   Add EXECUTION LOG rows (Time | Step | Outcome | Concern?) for each step as you go.

## Constraints

- E2 hyper-parameters stay frozen (E3–E5 are ablation/diagnostics, not tuning).
- CAD market, WI-008 reinstatement, ELE re-download: out of scope (separate approvals).
- If E5 crashes for memory reasons, run it on a sample of dates and note the deviation.
- Commit step-scoped files only with explicit paths (script/report changes, plan, board).

## QA hooks (PM will run these)

- `grep -E "Verdict|H2" reports/diag_D002_e3.md`
- `grep -E "Verdict|H4" reports/diag_D002_e5.md`
- `grep -E "H2|H3|H4" reports/diag_D002_summary.md`
- Plan file ends with a STATUS line.
