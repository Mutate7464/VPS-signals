# P1 — Regime overlay on the fib-swing bottom screen (design, status: PROPOSED)

> Source: `reports/fib_swings/IMPROVEMENT_PLAN.md` §P1 + §P6. Drafted 2026-11-06 by Hermes (PM)
> after verifying passes 1–4. Not approved. Executes via kanban WI-021 (prereq) → WI-022.

## Why
Bottom screen `rsi_f63<42 AND rsi_f15−rsi_f39<−8` (frozen, P5) has out-of-time edge, but
per-year precision falls below base in 2021 (18.4% vs 25.4%, n=103) and 2026
(24.4% vs 30.8% on resolved events, n=156). **2021 is inside calibration** — fixing it is
in-sample evidence. 2026 is the only out-of-sample failing year, partial, ~156 resolved
screened events (binomial SE ≈ 3.5pp). State this power limit in every result.

## Prerequisite (WI-021): pass-4 accounting fixes
1. `screen_rate_medplus` must use the same `fwd_mfe_pct.notna()` mask as `base_rate_medplus`
   (shipped code counts 49 unresolved 2026 screened events as failures).
2. `grade` = NaN (empty) when `fwd_mfe_pct` is NaN (1,871 unresolved events currently 'weak').
3. Persist `screen_bottom` / `screen_top` columns to `trailing_events_w39.csv`
   (computed after `to_csv` today; DATA_INDEX glossary claims they exist).
4. Top-side outcome = drop grade (`fwd_mae_pct <= −19.5`), not rally MFE.
5. `rally_grade_priors.p_medplus/p_strong` on resolved events only; CSV readers use
   `keep_default_na=False` (ticker `NA` reads as NaN).

## Candidate regime features (all trailing, point-in-time, computed per date)
Testing budget: **3 rules + baseline**, pre-registered, no additions without admin OK.

| ID | Feature | Definition | Source in plan |
|---|---|---|---|
| R1 | Universe vol term structure | cross-sectional geometric mean of `bbw_f3/bbw_f39` over active tickers that date (streamed as Σlog + count); also 5-day mean | P1 primary |
| R2 | Breadth63 | share of active tickers with close > SMA63 | P1 secondary |
| R1∧R2 | joint | both gates pass | combination |

Ticker-level `bbw_ratio` (already a column) is reported descriptively only, not a candidate rule.
Out of budget (needs admin OK): new-39d-low breadth ("systemic vs idiosyncratic bottom").

## Conditioning rule
- For each R: tercile cut points computed on **calibration dates only** (<2022-07-01), frozen.
- Gate = allowed set of terciles, chosen on calibration purged CV as the set maximizing
  mean fold edge, subject to: all 5 folds same sign, and gate keeps ≥30% of screened events.
- Final rule chosen on calibration ONLY; EVAL is scored once for all 3 rules (no selection on EVAL).
- Markets: compute R1/R2 pooled AND per market (CAD, USD); conditioning uses the event's own
  market regime. Pooled result is the headline; per-market is descriptive (markets assumed different).

## Validation recipe
- Split: CALIB < 2022-07-01, EVAL ≥ 2022-07-01 (unchanged).
- Purge/embargo: drop CALIB events within 39 trading days before 2022-07-01 (label window
  crosses the split); within CALIB, 5 contiguous time-block folds, purge train events whose
  39d label window overlaps the test block, 39-trading-day embargo after each test block.
- Metrics per (rule × period × year × market): n_events, n_screened, n_gated, keep rate,
  base_rate_medplus, screen_rate_medplus, gated_rate_medplus, edge_pp (vs same-period base),
  fwd_ret median (screened, gated, base), precision@10 (gated).
- Also score every rule on realized trade R from WI-023's chosen exit policy (TEST_PLAN rung 2),
  per market — the 10%/trade goal is judged on R, grade is secondary.
- Uncertainty: EVAL edge 90% CI by monthly block bootstrap (1,000 resamples, seed fixed).
- Per-year table 2006–2026 for every rule; 2021 and 2026 rows called out.

## Pass bar (pre-registered)
- PASS: chosen rule's EVAL gated edge ≥ ungated EVAL edge (+3.4pp corrected) AND 2026
  gated edge ≥ 0 AND keep rate ≥ 30% AND fold-sign stability on CALIB.
- FAIL → close P1 as documented negative; next lever is P3.4 (HMM) only if admin orders.
- Any result: no shortlist integration without the CAD/USD split pass (P6).

## Runtime (2 vCPU / 8 GB)
- Pass 4 observed ~1 min for 989 files (script mtime 22:09:53 → log EXIT 22:10:30).
- WI-021 regen: one symbol-sequential pass, same loop → est. 1–3 min, RAM < 300 MB.
- WI-022: one symbol-sequential pass for R1/R2 accumulators (per-date Σ/count dicts,
  ~5,200 dates) → 1–3 min; CV + bootstrap on ~190k event rows → < 1 min. No n_jobs needed
  (single process); any sklearn/joblib call uses n_jobs=2; float32 for derived columns.
- Targeted tests: seconds. Full suite (if gate requires): 7–8 min detached.
