# WI-011 Step 2 — trailing condition definitions (CAD)

- Generated (UTC): 2026-10-25T21:42:53Z
- Panel: 707,899 rows · 315 symbols · 2711 dates (2016-01-04 → 2026-10-21)
- Analysis window: `date >= 2016-01-04` (the CAD feature/target panel start, `reports/wi011_preflight.md`); raw history is read in full so long lookbacks warm up first.
- Built by sequential per-symbol iteration (`src/wi011/panel.py`); no all-ticker uncompressed frame; calculated columns cast to float32 immediately.

## Condition vocabulary

CONDITION_COUNT: 38
- declared atomic conditions: 18
- declared cross conditions: 8
- Step-3-selected indicator conditions: 12 (from `reports/wi011_selected_indicators.json`: pct_from_high_f102, fib_dist_f102, di_spread_100, vwap_zscore_50, atr_pct_100, vwap_zscore_100)
- total condition firings in the panel: 7,463,640

Three-valued semantics: `1.0` fires, `0.0` defined and does not fire, **`NaN` = undefined** (warm-up / insufficient history). Warm-up rows are preserved — never coerced to 0 — and every downstream step masks on `isfinite` per condition.

| Condition | Formula (all trailing, point-in-time) | Lookback | Firings | Defined rows | Fire rate |
| :--- | :--- | ---: | ---: | ---: | ---: |
| `trend_up` | trailing OLS slope of log close > 0 and R^2 >= 0.30 | 20d | 253,284 | 706,082 | 35.9% |
| `trend_down` | trailing OLS slope of log close < 0 and R^2 >= 0.30 | 20d | 183,256 | 706,082 | 26.0% |
| `trend_chop` | trailing OLS R^2 < 0.30 (no explained direction) | 20d | 269,542 | 706,082 | 38.2% |
| `er_trending` | KAMA efficiency ratio >= 0.50 | 20d | 63,093 | 706,039 | 8.9% |
| `er_choppy` | KAMA efficiency ratio < 0.30 | 20d | 479,156 | 706,039 | 67.9% |
| `vol_low` | trailing percentile of ATR% <= 0.33 | 252d | 263,570 | 683,814 | 38.5% |
| `vol_high` | trailing percentile of ATR% >= 0.67 | 252d | 224,699 | 683,814 | 32.9% |
| `liq_illiquid` | trailing percentile of E5 amihud_20 >= 0.67 | 252d | 194,822 | 683,814 | 28.5% |
| `liq_liquid` | trailing percentile of E5 amihud_20 <= 0.33 | 252d | 303,902 | 683,814 | 44.4% |
| `dollarvol_high` | trailing percentile of E5 log_dollar_vol_20 >= 0.67 | 252d | 298,820 | 683,814 | 43.7% |
| `above_ma_50` | close > trailing 50d simple moving average | 50d | 403,648 | 703,332 | 57.4% |
| `below_ma_50` | close < trailing 50d simple moving average | 50d | 299,656 | 703,332 | 42.6% |
| `ch52_high` | position in 52-week high/low channel >= 0.80 | 252d | 229,411 | 683,813 | 33.5% |
| `ch52_low` | position in 52-week high/low channel <= 0.20 | 252d | 96,852 | 683,813 | 14.2% |
| `mom_pos` | E5 mom_12_1 > 0 (252d/21d trailing momentum) | 252d | 442,763 | 683,715 | 64.8% |
| `mom_neg` | E5 mom_12_1 < 0 | 252d | 240,091 | 683,715 | 35.1% |
| `rev1m_pos` | E5 rev_1m > 0 (21d trailing return) | 21d | 392,947 | 705,946 | 55.7% |
| `rev1m_neg` | E5 rev_1m < 0 | 21d | 308,925 | 705,946 | 43.8% |
| `trend_up_vol_high` | trend_up AND vol_high | 20d + 252d | 54,991 | 683,764 | 8.0% |
| `trend_up_vol_low` | trend_up AND vol_low | 20d + 252d | 121,836 | 683,764 | 17.8% |
| `trend_down_vol_high` | trend_down AND vol_high | 20d + 252d | 82,437 | 683,764 | 12.1% |
| `trend_down_vol_low` | trend_down AND vol_low | 20d + 252d | 44,968 | 683,764 | 6.6% |
| `ch52_high_vol_low` | ch52_high AND vol_low | 252d | 118,862 | 683,813 | 17.4% |
| `ch52_low_vol_high` | ch52_low AND vol_high | 252d | 52,306 | 683,813 | 7.6% |
| `above_ma_50_liq_illiquid` | above_ma_50 AND liq_illiquid | 50d + 252d | 86,031 | 683,814 | 12.6% |
| `mom_pos_liq_illiquid` | mom_pos AND liq_illiquid | 252d | 87,674 | 683,715 | 12.8% |
| `ind_atr_pct_100_high` | Step 3-selected indicator in its own-history extreme tail | 252d | 147,220 | 664,703 | 22.1% |
| `ind_atr_pct_100_low` | Step 3-selected indicator in its own-history extreme tail | 252d | 221,504 | 664,703 | 33.3% |
| `ind_di_spread_100_high` | Step 3-selected indicator in its own-history extreme tail | 252d | 176,574 | 664,703 | 26.6% |
| `ind_di_spread_100_low` | Step 3-selected indicator in its own-history extreme tail | 252d | 159,486 | 664,703 | 24.0% |
| `ind_fib_dist_f102_high` | Step 3-selected indicator in its own-history extreme tail | 252d | 156,686 | 664,701 | 23.6% |
| `ind_fib_dist_f102_low` | Step 3-selected indicator in its own-history extreme tail | 252d | 151,528 | 664,701 | 22.8% |
| `ind_pct_from_high_f102_high` | Step 3-selected indicator in its own-history extreme tail | 252d | 157,386 | 664,701 | 23.7% |
| `ind_pct_from_high_f102_low` | Step 3-selected indicator in its own-history extreme tail | 252d | 152,602 | 664,701 | 23.0% |
| `ind_vwap_zscore_100_high` | Step 3-selected indicator in its own-history extreme tail | 252d | 135,871 | 658,431 | 20.6% |
| `ind_vwap_zscore_100_low` | Step 3-selected indicator in its own-history extreme tail | 252d | 141,311 | 658,431 | 21.5% |
| `ind_vwap_zscore_50_high` | Step 3-selected indicator in its own-history extreme tail | 252d | 132,639 | 664,704 | 20.0% |
| `ind_vwap_zscore_50_low` | Step 3-selected indicator in its own-history extreme tail | 252d | 133,291 | 664,704 | 20.1% |

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

- `AAPL` @ 2026-10-16: conditions match, state columns match
- `AAUC` @ 2026-10-16: conditions match, state columns match
- `AAV` @ 2026-10-16: conditions match, state columns match
- `ABT` @ 2026-10-16: conditions match, state columns match
- `ABX` @ 2026-10-16: conditions match, state columns match

Plus `tests/test_wi011_conditions.py` (15 tests): future-bar perturbation leaves earlier conditions bit-identical; truncated recomputation reproduces the live row; the last bar is condition-defined from history alone; forward labels *do* change when the future changes (harness sanity); the Corwin-Schultz cost input is lagged to bars (t-1, t).

## Dtypes / build discipline

- every condition column float32: **PASS**
- every calculated label/state/cost column float32: **PASS**
- horizons available as labels: `1d`, `2d`, `5d`, `10d`, `15d`, `20d`, `60d`, `120d`

## Status

Data-only condition definitions — no trade labels, no model, no threshold tuned against forward returns. Step 3 consumes this vocabulary for the indicator-association pass.
