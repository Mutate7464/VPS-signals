# Feature windows & target×feature alignment — research plan (WI-015)

Status: RESEARCH / PLAN-OUTLINE. **Spec confirmed by admin 2026-10-28** (see CONFIRMED below). No analysis run yet.

## CONFIRMED (admin, 2026-10-28): Fibonacci-scaled feature windows

Iterate the **existing normalized feature families** at Fibonacci-scaled
windows covering a range of **3 to 200 days**. Grid:

> **3, 5, 8, 13, 21, 34, 55, 89, 144** (fib sequence) **+ 200** (terminal cap;
> next fib 233 exceeds the requested range)

Families to iterate (from the current 92-col pool, `data/features/features_*.parquet`;
family names follow existing naming, `<W>` = window):

| Family | Column pattern | Note |
|---|---|---|
| RSI | `rsi_<W>` | |
| Bollinger | `bb_pct_b_<W>`, `bb_width_<W>` | |
| ADX / DI | `adx_<W>`, `di_spread_<W>` | |
| ATR% | `atr_pct_<W>` | |
| OBV z | `obv_zscore_<W>` | |
| Hurst | `hurst_<W>` | |
| KAMA ER | `kama_er_<W>` | |
| VWAP z | `vwap_zscore_<W>` | |
| Amihud / Yang-Zhang | `amihud_<W>`, `yangzhang_<W>` | illiquidity / range vol |
| Range pos / Donchian | `range_pos_f<W>`, `range_width_f<W>`, `donchian_break_f<W>` | existing fib windows f3..f39 subsume the short end |

Coverage vs current pool: windows 5/10/20/50/100 and f3/f6/f9/f15/f24/f39 exist
today; the fib grid adds 8, 13, 21, 34, 55, 89, 144, 200 and normalizes the rest
to the fib scale. Short windows (≤8) warm up fast; 144/200 need history length —
check per-symbol history coverage before computing (some CAD tickers may lack
200 trading days pre-window).

Estimate: ~10 families × ~10 windows ≈ 100 feature columns — well within host
limits if built symbol-sequential + float32 (matches the 89-feature pool
precedent in WI-009c).

## Alignment analysis (target × feature)

Question: **for each run target, which feature family × window correlates /
aligns best?** Per-target association table, not one global score.

Method (plan draft):
1. Build T1–T4 + brainstormed run targets (`docs/tech_approach/perfanalytics/targets-research.md`) on both markets from `data/raw_ohlcv/` (symbol-sequential, float32).
2. Build the fib-window feature grid above (trailing, causal, per t).
3. Per target: Spearman rank IC of each family×window feature vs the target at
   horizons t+k, held-out folds — reuse the E5 factor-screener machinery shape
   (`src/factors/e5_baseline.py`).
4. Skill bar (carried from WI-009b re-spec): association must match the sign of
   the best univariate factor AND clear a noise margin (|t| from block bootstrap),
   held-out. Record surviving features per target.
5. Output: target×feature matrix in `reports/perfanalytics/`, market-suffixed
   (`*_CAD`, `*_USD`) — one row per target, top-5 aligned family×window + IC + t.

Prior expectations to falsify (from WI-009 series): most family×window cells
land near noise; the run targets' own lagged values (persistence) likely beat
every feature. If that reproduces, the honest product is run-target descriptive
analytics + persistence baseline.

## Sequencing

1. Plan step: run-target labelers (`src/perfanalytics/targets/`).
2. Plan step: fib-window feature builder (`src/perfanalytics/features/`) + alignment report on CAD.
3. Gate: review matrix, decide USD replication + whether any association enters the daily shortlist. No pipeline changes before that gate.

## Superseded reading (2026-10-28)

The first draft read "fib spacing" as **Fibonacci retracement bands** (swing
level distances ÷ ATR). Admin clarification replaces that: fib scale applies to
**feature window durations**, not price levels. Retacement-band features stay
parked in this file's git history if ever wanted.