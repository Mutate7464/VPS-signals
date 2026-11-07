# Learnings from the Daily OHLCV Dataset (USD+CAD, ~950 tickers, 2006–2026)

One-page reconfirmation brief. Every number traces to a file in this directory
(see DATA_INDEX.md). Generated 2026-11-06 after passes 1–4.

## L1. Swing anatomy (centered windows, research basis)
- A confirmed w=39 bottom historically rallies **+25% off the low** (p25–p75: 17–40%)
  within 39 bars; drops from w=39 peaks run −18.7%. Rallies beat drops ~1.3–1.6×
  in magnitude and velocity at every window (long-bias universes).
- Swing frequency scales ~2.6× the window: w=15 swings every ~41 days,
  w=39 every ~105, w=63 every ~172. Velocity decays from 2.0%/day (w=3)
  to 0.45%/day (w=102). → `window_summary.csv`, `ticker_swing_metadata.csv`
- **Per-ticker targets differ hugely from the universe median** (median rally 10.4%,
  but 903-ticker priors range 0→70% P(med+ rally)) → never quote universe medians
  for a specific name; use `rally_grade_priors.csv`.

## L2. What aligns with turns (and what doesn't)
- Short-window RSI separates tops/bottoms (AUC 0.98+) but **mechanically** — it is
  high at highs by construction. Calibration value only.
- Genuinely predictive: **long-window RSI oversold** (rsi_f63 < ~42 → 3.7× lift
  locating w=63 bottoms, in-sample) and long-window ATR%/BB-width as regime features.
- Short-window oversold/vol-compression screens = noise (lift ~1.1×).

## L3. Meta-features (420 permutations: ratio/diff across windows & families)
- **`rsi_f63/atrp_f63`** strongest (ρ −0.088 vs fwd returns; +0.075 vs "touch +5%
  in 15d") → a *volatility-regime* feature: excursion probability up, drift down.
- **`rsi_f15 − rsi_f39`** best non-mechanical turn detector (AUC 0.986; thresholds
  −10.8 bottom / +10.2 top) but weak drift prediction (|ρ|≈0.03) → pair the two.
- **`bbw_f3/bbw_f39`** > ~0.7 = vol release → elevated P(20d up) (biserial +0.05).
- Ratios beat diffs for unbounded indicators (bbw, atrp); RSI diffs/ratios mirror.
- Panel families (ADX/KAMA/OBV) add ~nothing; VWAP-z term structure marginal.

## L4. Out-of-time validation (trailing windows, split 2022-07, thresholds frozen)
- Bottom screen `rsi_f63<42 & rsi_f15−rsi_f39<−8`: **survives, decays ~5×**
  (+11.1pp in-sample → +2.0pp out-of-sample grade precision; +1.5pp fwd 39d return).
- **Top screen: no edge out-of-sample** — sizing/avoid only.
- Ranking flagged bottoms by deepest oversold adds **no** skill (28.8% vs 29.6%).
- **Regime risk: 2021 and 2026 screen precision fell below base rate** — a regime
  overlay is mandatory before shortlist integration.

## L5. Dataset/process learnings
- Raw files are `symbol=<T>.parquet`; naive basename-as-symbol silently yields empty
  feature joins. Always strip the `symbol=` prefix (and try space variants).
- ~157/977 tickers lack feature/target rows (stale feature panel) — NaN-safe
  aggregation required; report n_tickers per result.
- Centered-window events carry a w-bar confirmation lag → tradable definitions
  must be trailing (pass-4 style).
- All screens are in both-markets pooled; no CAD/USD split has been run yet.

## Open gates before production
Full prioritized plan (models, features, frozen thresholds, CV practices):
see **IMPROVEMENT_PLAN.md**. Summary:
1. Regime overlay on the bottom screen (candidates: bbw_f3/bbw_f39, market breadth).
2. CAD/USD split + per-year stability for the 2–3 surviving features.
3. Learned ranker (precision@10 is where the value is, oversold ranking is saturated).
4. 3-class rally grade model (weak/med/strong) rather than binary flags.
