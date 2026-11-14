# Fib-Window Swing Anatomy, Indicator Alignment & Screener Thresholds

> **Update 2026-11-06 (pass 4):** out-of-time validation of these screens is in
> `WF_VALIDATION.md`. In short: the `rsi_f63 < ~42` bottom screen survives out-of-sample
> (+1.5pp fwd-return edge on trailing 39d lows, ≥2022-07) but decays ~5× vs its in-sample
> precision; the top screen has no edge out-of-sample. Trailing-window (tradable) event
> data: `trailing_events_w39.csv`; per-ticker rally priors: `rally_grade_priors.csv`.
> All numbers below are **centered-window research values** (w-bar confirmation lag).

Run: 2026-11-06 · Universe: 608 USD + 378 CAD daily OHLCV (≈950 tickers ≥300 bars) ·
Method: centered swing extremes (high = max over ±w bars, w ∈ {3,6,9,15,24,39,63,102}),
alternating top/bottom pairing, indicator snapshots at events, threshold hit-rate backtest.
Constraints respected: symbol-sequential, float32, no all-ticker uncompressed frames.

## 1. Realistic expectations — magnitude / velocity / frequency by Fib window

| w (bars) | Days between swings (med) | Rally from bottom med (p25–p75) | Drop from peak med (p25–p75) | Vel. from bottom | Vel. from peak | Fwd w-day ret at bottom | at top |
|---|---|---|---|---|---|---|---|
| 3 | 9.1 | +6.0% (3.9–9.6) | −5.4% (−8.4…−3.5) | 2.00%/d | −1.81%/d | +2.3% | −2.1% |
| 6 | 17.0 | +8.6% (5.6–13.7) | −7.5% (−11.5…−5.0) | 1.44%/d | −1.26%/d | +3.9% | −3.4% |
| 9 | 25.0 | +10.8% (7.0–16.9) | −9.2% (−13.9…−6.1) | 1.19%/d | −1.02%/d | +5.2% | −4.4% |
| 15 | 41.0 | +14.3% (9.5–22.5) | −11.9% (−17.7…−8.0) | 0.96%/d | −0.79%/d | +7.6% | −6.2% |
| 24 | 65.4 | +18.8% (12.5–29.7) | −14.8% (−21.6…−10.2) | 0.78%/d | −0.62%/d | +10.6% | −8.2% |
| 39 | 105.3 | +25.3% (16.8–40.5) | −18.7% (−27.0…−13.1) | 0.65%/d | −0.48%/d | +14.6% | −10.8% |
| 63 | 172.1 | +34.0% (22.8–54.5) | −23.3% (−33.1…−16.5) | 0.54%/d | −0.37%/d | +20.3% | −13.8% |
| 102 | 274.7 | +46.1% (30.8–76.4) | −29.0% (−40.6…−20.9) | 0.45%/d | −0.28%/d | +27.7% | −16.9% |

Asymmetry: rallies off bottoms run ~1.3–1.6× the magnitude and velocity of drops from peaks
at every window (long-bias universes). Practical targets: a confirmed w=39 bottom historically
delivers ~25% off the low within 39 bars; a w=39 top ~−19% off the high.

## 2. Which Fib duration aligns with turns (indicator separation)

- Short-window RSI separates tops/bottoms near-perfectly (rsi_f15 at w=39: AUC 0.998)
  but this is largely mechanical — RSI is high at swing highs by construction. Calibration
  value only.
- Genuinely predictive of forward returns (per-ticker Spearman, all bars):
  **ATR% and BB-width at long windows** — atrp_f102 vs 102-day fwd return: mean +0.095
  (regime/vol~momentum); long-window RSI is mildly mean-reverting (rsi_f102: −0.047).

## 3. Screener thresholds with honest hit-rates (vs random & vs base rate)

Bottom screens, best per window (threshold = percentile of event-value distribution):

| w | Screen | Flag rate | Near-bottom precision | Random baseline | Lift | Fwd w-day ret (flagged vs base) |
|---|---|---|---|---|---|---|
| 3 | bbw_f102 < p25 | 25% | 30.1% | 27.5% | 1.1× | +0.16% vs +0.15% (no edge) |
| 15 | rsi_f102 < p25 | 13% | 11.4% | 6.1% | 1.9× | +1.07% vs +0.78% (+0.29pp) |
| 24 | rsi_f102 < p25 | 11% | 10.9% | 5.4% | 2.0× | +1.62% vs +1.18% (+0.44pp) |
| 39 | rsi_f63 < p40 | 10% | 12.8% | 4.3% | 3.0× | +2.61% vs +1.87% (+0.74pp) |
| **63** | **rsi_f63 < p40** | **7.5%** | **16.3%** | **4.4%** | **3.7×** | **+3.81% vs +3.04% (+0.77pp)** |
| 102 | rsi_f6 < p40 | 4.7% | 12.7% | 4.6% | 2.8× | +5.18% vs +4.79% (+0.39pp) |

Top screens ("avoid/exhaustion" flags): rsi_f24 > p40 at w=63 — lift 2.6× but forward
return only −0.12pp below base: tops are better detected for risk-sizing than for alpha.

**Bottom line:** short-window RSI extremes (classic 3–9 day oversold) are noise —
lift ≈ 1.0×, no forward edge. The real signal is **long-window RSI oversold**
(63-day RSI in its bottom-40 percentile of event values ≈ RSI < ~42, 102-day RSI < ~45):
3–4× lift on locating true bottoms and +0.4–0.8pp median forward-return edge.

## 4. Files (metadata produced)

- `ticker_swing_metadata.csv` — per ticker × window: event counts, days between swings,
  median down/up swing magnitude, median duration → per-ticker realistic targets.
- `window_summary.csv` — cross-sectional table above.
- `indicator_alignment.csv` — per window × ~60 indicators: median at tops/bottoms + AUC.
- `fib_indicator_fwdret_corr.csv` — fib-window RSI/BBW/ATRP vs fwd-return Spearman (mean over tickers).
- `screener_hit_rates.csv` — full threshold backtest (all candidates, both sides).
- `events_all.csv.gz` — ~700k events with excursions, velocity, fwd returns.

## Caveats

- Event thresholds derived and evaluated on the same history (in-sample); no train/test split
  yet — treat lift/edge as upper bounds pending a walk-forward check.
- Both markets pooled; per-market splits available on request.
- Screen "rsi_f63 < p40" literal value: 40th pctile of bottom-event rsi_f63 values
  (median at confirmed w=63 bottoms was 41.9).
