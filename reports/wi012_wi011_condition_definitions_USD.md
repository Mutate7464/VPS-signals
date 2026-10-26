# WI-011 Step 2 — trailing condition definitions (CAD)

- Generated (UTC): 2026-10-26T06:43:20Z
- Panel: 1,314,936 rows · 533 symbols · 2716 dates (2016-01-04 → 2026-10-21)
- Analysis window: `date >= 2016-01-04` (the CAD feature/target panel start, `reports/wi011_preflight.md`); raw history is read in full so long lookbacks warm up first.
- Built by sequential per-symbol iteration (`src/wi011/panel.py`); no all-ticker uncompressed frame; calculated columns cast to float32 immediately.

## Condition vocabulary

CONDITION_COUNT: 38
- declared atomic conditions: 18
- declared cross conditions: 8
- Step-3-selected indicator conditions: 12 (from `reports/wi011_selected_indicators.json`: pct_from_high_f102, fib_dist_f102, di_spread_100, vwap_zscore_50, atr_pct_100, vwap_zscore_100)
- total condition firings in the panel: 13,835,986

Three-valued semantics: `1.0` fires, `0.0` defined and does not fire, **`NaN` = undefined** (warm-up / insufficient history). Warm-up rows are preserved — never coerced to 0 — and every downstream step masks on `isfinite` per condition.

| Condition | Formula (all trailing, point-in-time) | Lookback | Firings | Defined rows | Fire rate |
| :--- | :--- | ---: | ---: | ---: | ---: |
| `trend_up` | trailing OLS slope of log close > 0 and R^2 >= 0.30 | 20d | 481,554 | 1,312,766 | 36.7% |
| `trend_down` | trailing OLS slope of log close < 0 and R^2 >= 0.30 | 20d | 339,545 | 1,312,766 | 25.9% |
| `trend_chop` | trailing OLS R^2 < 0.30 (no explained direction) | 20d | 491,667 | 1,312,766 | 37.5% |
| `er_trending` | KAMA efficiency ratio >= 0.50 | 20d | 114,346 | 1,312,651 | 8.7% |
| `er_choppy` | KAMA efficiency ratio < 0.30 | 20d | 887,069 | 1,312,651 | 67.6% |
| `vol_low` | trailing percentile of ATR% <= 0.33 | 252d | 495,306 | 1,284,641 | 38.6% |
| `vol_high` | trailing percentile of ATR% >= 0.67 | 252d | 420,964 | 1,284,641 | 32.8% |
| `liq_illiquid` | trailing percentile of E5 amihud_20 >= 0.67 | 252d | 396,819 | 1,284,641 | 30.9% |
| `liq_liquid` | trailing percentile of E5 amihud_20 <= 0.33 | 252d | 528,185 | 1,284,641 | 41.1% |
| `dollarvol_high` | trailing percentile of E5 log_dollar_vol_20 >= 0.67 | 252d | 517,552 | 1,284,641 | 40.3% |
| `above_ma_50` | close > trailing 50d simple moving average | 50d | 752,784 | 1,309,296 | 57.5% |
| `below_ma_50` | close < trailing 50d simple moving average | 50d | 555,918 | 1,309,296 | 42.5% |
| `ch52_high` | position in 52-week high/low channel >= 0.80 | 252d | 432,377 | 1,284,641 | 33.7% |
| `ch52_low` | position in 52-week high/low channel <= 0.20 | 252d | 177,382 | 1,284,641 | 13.8% |
| `mom_pos` | E5 mom_12_1 > 0 (252d/21d trailing momentum) | 252d | 829,050 | 1,284,513 | 64.5% |
| `mom_neg` | E5 mom_12_1 < 0 | 252d | 454,850 | 1,284,513 | 35.4% |
| `rev1m_pos` | E5 rev_1m > 0 (21d trailing return) | 21d | 736,487 | 1,312,536 | 56.1% |
| `rev1m_neg` | E5 rev_1m < 0 | 21d | 573,477 | 1,312,536 | 43.7% |
| `trend_up_vol_high` | trend_up AND vol_high | 20d + 252d | 98,610 | 1,284,641 | 7.7% |
| `trend_up_vol_low` | trend_up AND vol_low | 20d + 252d | 239,779 | 1,284,641 | 18.7% |
| `trend_down_vol_high` | trend_down AND vol_high | 20d + 252d | 159,506 | 1,284,641 | 12.4% |
| `trend_down_vol_low` | trend_down AND vol_low | 20d + 252d | 81,786 | 1,284,641 | 6.4% |
| `ch52_high_vol_low` | ch52_high AND vol_low | 252d | 238,727 | 1,284,641 | 18.6% |
| `ch52_low_vol_high` | ch52_low AND vol_high | 252d | 105,706 | 1,284,641 | 8.2% |
| `above_ma_50_liq_illiquid` | above_ma_50 AND liq_illiquid | 50d + 252d | 180,878 | 1,284,641 | 14.1% |
| `mom_pos_liq_illiquid` | mom_pos AND liq_illiquid | 252d | 191,370 | 1,284,513 | 14.9% |
| `ind_atr_pct_100_high` | Step 3-selected indicator in its own-history extreme tail | 252d | 273,401 | 1,187,984 | 23.0% |
| `ind_atr_pct_100_low` | Step 3-selected indicator in its own-history extreme tail | 252d | 398,677 | 1,187,984 | 33.6% |
| `ind_di_spread_100_high` | Step 3-selected indicator in its own-history extreme tail | 252d | 329,012 | 1,187,984 | 27.7% |
| `ind_di_spread_100_low` | Step 3-selected indicator in its own-history extreme tail | 252d | 275,815 | 1,187,984 | 23.2% |
| `ind_fib_dist_f102_high` | Step 3-selected indicator in its own-history extreme tail | 252d | 282,914 | 1,187,982 | 23.8% |
| `ind_fib_dist_f102_low` | Step 3-selected indicator in its own-history extreme tail | 252d | 268,150 | 1,187,982 | 22.6% |
| `ind_pct_from_high_f102_high` | Step 3-selected indicator in its own-history extreme tail | 252d | 282,890 | 1,187,982 | 23.8% |
| `ind_pct_from_high_f102_low` | Step 3-selected indicator in its own-history extreme tail | 252d | 274,403 | 1,187,982 | 23.1% |
| `ind_vwap_zscore_100_high` | Step 3-selected indicator in its own-history extreme tail | 252d | 247,999 | 1,177,906 | 21.1% |
| `ind_vwap_zscore_100_low` | Step 3-selected indicator in its own-history extreme tail | 252d | 249,338 | 1,177,906 | 21.2% |
| `ind_vwap_zscore_50_high` | Step 3-selected indicator in its own-history extreme tail | 252d | 237,325 | 1,187,985 | 20.0% |
| `ind_vwap_zscore_50_low` | Step 3-selected indicator in its own-history extreme tail | 252d | 234,368 | 1,187,985 | 19.7% |

## Inputs

- E5 primitives, byte-for-byte the `src/factors/e5_baseline` definitions: `mom_12_1`, `rev_1m`, `vol_20`, `amihud_20`, `log_dollar_vol_20`.
- `src/targets.wilder_atr(20)` for ATR% and the ATR-multiple forward label.
- Trailing OLS slope/R² of log close over 20d, KAMA efficiency ratio over 20d (`src/feature_engine._efficiency_ratio` semantics), trailing 50d MA, 52-week (252d) high/low channel from daily high/low.
- Own-history percentiles (`vol_low`, `vol_high`, `liq_*`, `dollarvol_high`): percentile rank of the current value inside its trailing 252-day window, requiring a full window and at least 60 finite observations inside it.
- Fixed thresholds declared before evaluation (never tuned on forward returns): R² floor 0.30, efficiency ratio 0.50/0.30, percentile thirds 0.33/0.67, channel 0.20/0.80.

## Warm-up handling

- Conditions depending on a 252-day window are undefined for a symbol's first 251 bars; `mom_12_1` needs 252 bars + 21 for its skip, so momentum conditions warm up later still.
- Effects are visible in the `Defined rows` column above and are reported, not imputed. Symbols whose raw history starts in 2021 contribute their first usable condition rows only from ~2022 onward.
- Forward labels (`fwd_ret_h`, `fwd_atr_ret_h`) are NaN for the last h bars of each symbol; they are labels measured by the expectancy step and are never an input to any condition.

## Causality evidence

POINT_IN_TIME: PASS

Runtime spot-check — recompute each symbol's conditions from a frame truncated 3 bars early and compare the cut row element-wise:

- `A` @ 2026-10-16: conditions match, state columns match
- `AA` @ 2026-10-16: conditions match, state columns match
- `AAPL` @ 2026-10-16: conditions match, state columns match
- `ABBV` @ 2026-10-16: conditions match, state columns match
- `ABEV` @ 2026-10-16: conditions match, state columns match

Plus `tests/test_wi011_conditions.py` (15 tests): future-bar perturbation leaves earlier conditions bit-identical; truncated recomputation reproduces the live row; the last bar is condition-defined from history alone; forward labels *do* change when the future changes (harness sanity); the Corwin-Schultz cost input is lagged to bars (t-1, t).

## Dtypes / build discipline

- every condition column float32: **PASS**
- every calculated label/state/cost column float32: **PASS**
- horizons available as labels: `1d`, `2d`, `5d`, `10d`, `15d`, `20d`, `60d`, `120d`

## Status

Data-only condition definitions — no trade labels, no model, no threshold tuned against forward returns. Step 3 consumes this vocabulary for the indicator-association pass.
