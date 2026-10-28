# Fib-spacing features & target×feature alignment — research plan (WI-015)

Status: RESEARCH / PLAN-OUTLINE. No analysis run yet.

## Fib-spacing features (net-new)

The current 92-col pool (`data/features/features_{CAD,USD}.parquet`) has **no
fib columns** — verified by schema read 2026-10-28 (rsi/bb/adx/atr/obv/hurst/
kama/range_pos/donchian families only). Legacy fib artifacts exist in `data/`
(`oof_USD_fib_only.parquet`, `train_meta_USD_fib_only.json`) — from a pre-WI-009
experiment; treat as stale, don't inherit.

Draft feature set (trailing, causal, per t):

| Feature | Definition (draft) | Rationale |
|---|---|---|
| FIB_dist_382 | `close / fib(0.382 level of last swing) − 1` | Nearest retracement band distance |
| FIB_dist_618 | same at 0.618 | Deeper band — run continuation vs reversal |
| FIB_dist_100 | same at 1.0 (extension) | Extension = momentum continuation |
| FIB_spacing_238_382 | gap between 23.6% and 38.2% levels ÷ trailing ATR | **The admin-named "fib spacing"** — tight spacing = compressed swing = sharper runs? |
| FIB_spacing_382_618 | 38.2→61.8 gap ÷ ATR | Coarse spacing variant |
| SWING_age | days since the swing low/high defining the levels | Stale levels vs fresh |

Open: swing definition (Donchian pivot vs fractal pivot), ATR normalization window.

## Alignment analysis (target × feature)

Question per admin: **"at fib spacing, which aligns best with each target"** —
i.e. a per-target feature association table, not one global score.

Method (plan draft):
1. Build T1–T4 + brainstorm targets on both markets from `data/raw_ohlcv/`
   (symbol-sequential, float32).
2. Per target: Spearman rank IC of each feature vs the target at horizons
   t+k, on held-out folds — reuse the E5 factor-screener machinery shape
   (`src/factors/e5_baseline.py`).
3. Skill bar (carried from WI-009b re-spec): association must match the sign
   of the best univariate factor AND clear a noise margin (|t| from block
   bootstrap), held-out. Record which features survive per target.
4. Output: target×feature matrix in `reports/perfanalytics/`, market-suffixed
   (`*_CAD`, `*_USD`), one row per target, columns = top-5 aligned features
   + IC + t-stat.

Prior expectations to falsify (from WI-009 series): fib spacing will likely
land near noise like the rest of the 89-feature pool; the run targets' own
lagged values (T1→T1 at t−1) will likely be the strongest aligners — i.e.
persistence, not features. If that reproduces, the honest product is
run-target descriptive analytics + persistence baseline, not a feature-driven
shortlist.

## Sequencing

1. Plan step: implement run-target labelers (`src/perfanalytics/targets/`).
2. Plan step: fib feature builder + alignment report on CAD.
3. Gate: review matrix, decide USD replication + whether any association
   enters the daily shortlist. No pipeline changes before that gate.