# Walk-Forward Validation: Trailing-Window Swing Screens (Pass 4)

Run: 2026-11-06 · Method: trailing 39-day break events (new low/high, confirmable
same-day, 10-bar cluster gap — no look-ahead), forward 39-day outcomes,
thresholds **frozen a priori** from in-sample passes 2/3 (not re-fit):
bottom screen `rsi_f63 < 42 AND rsi_f15 − rsi_f39 < −8`; top screen
`rsi_f63 > 58 AND rsi_f15 − rsi_f39 > +7`. Rally grade fixed at w=39 terciles:
weak < +19.5% ≤ med < +33.9% ≤ strong (max favorable excursion within 39 days).
Calibration < 2022-07-01; evaluation ≥ 2022-07-01. Both markets, ~950 tickers.

## Bottom screen — the headline result

| Period | Events | Screened (flag rate) | P(rally ≥ med): screened vs base | Fwd MFE med: screened vs base | Fwd 39d ret med: screened vs base |
|---|---|---|---|---|---|
| Calibration (<2022-07) | 55,059 | 3,435 (6.2%) | **34.4% vs 23.3% (+11.1pp)** | 13.6% vs 9.9% | 1.85% vs 1.65% |
| **Evaluation (≥2022-07)** | 20,990 | 1,056 (5.0%) | **28.2% vs 26.2% (+2.0pp)** | 12.5% vs 11.0% | **4.76% vs 3.26% (+1.5pp)** |

The screen survives out-of-time, but the skill **decays ~5×** (grade precision
+11.1pp → +2.0pp). Fwd-return edge holds better (+1.5pp). Per-year
(`walkforward_validation.csv`): mostly positive 2007–2025, but **2021 and
2026 bottom-screen precision fell below base rate** — the screen is
regime-dependent and needs a regime filter before gating a shortlist.

## Top screen — confirmed not tradable
Grade precision screened vs base: CALIB 13.5% vs 15.1%, EVAL 20.6% vs 20.3% —
no edge in or out of sample. Tops are for risk sizing only.

## Precision@10 (`precision_at10.csv`)
Ranking flagged bottoms by lowest rsi_f63 does **not** add skill: EVAL top-10
grade precision 28.8% vs all-screened 29.6%; fwd ret 4.45% vs 4.76% median.
Simple oversold-ranking is saturated — a learned ranker (or confluence score)
is the next lever, not deeper oversold.

## Verdict
1. Use the bottom screen as a **calibration-checked candidate generator**
   (5% of new lows, +1.5pp fwd-return edge), not as alpha.
2. Do NOT deploy the top screen; use top flags only to size/avoid.
3. 2021/2026 failure years demand a regime overlay (e.g., market-level
   breadth or the bbw_f3/bbw_f39 vol-term-structure regime from META_SUMMARY)
   as the next work item.
4. All numbers above are trailing-window and out-of-time-verified; the
   centered-window numbers in SUMMARY.md remain research-only (15-bar lag).

## New data files
- `trailing_events_w39.csv` — 186,729 trailing events (76,049 bottoms / 110,680
  tops) with rsi_f63, RSI spread, bbw ratio, fwd MFE/MAE/return, rally grade
- `walkforward_validation.csv` — split + per-year stats both sides
- `precision_at10.csv` — daily top-10 ranking test
- `rally_grade_priors.csv` — per-ticker: n bottoms, median rally,
  P(med+), P(strong) → per-name realistic expectations for sizing
