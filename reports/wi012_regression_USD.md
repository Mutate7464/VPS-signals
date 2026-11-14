# WI-009c Steps 2–3 — continuous 20td regressor, band probabilities and shortlist (USD)

- Generated (UTC): 2026-10-26T06:39:17Z
- Panel: 1,210,402 rows · 508 symbols · 2696 dates (2016-01-04 → 2026-09-23)
- Continuous target: `fwd_atr_ret_20` (the Step-0 named target), ATR/price column `atr_pct_20`.
- Features: the five E5 factors only (`e5_mom_12_1`, `e5_rev_1m`, `e5_vol_20`, `e5_amihud_20`, `e5_log_dollar_vol_20`). Step 1 cleared the skill bar for 0/5 labels, so plan Step 1(d) gates all 89-feature and optional-candidate spend — this baseline is limited to the same five factors.
- Model: `StandardScaler` + `Ridge(alpha=100)`, float32 features, BLAS/OMP threads pinned to 2. Wall clock 1.6s.
- CV: `PurgedWalkForwardSplit(n_splits=5, embargo_td=20)` over unique dates keyed by *positions* (`src.factors.e5_baseline.date_positions`).
- Split calibration (ADR D-010): per fold the last 20% of the training dates (purged 20td from the fit block) supplies the held-out residual empirical CDF; the model is fit on the remaining training dates only.

## Fold plan and leakage evidence

Calibration residuals are drawn from the `cal` block, which is disjoint from the `fit` block that trained that fold's model, and both are separated from the `val` block by the 20td purge. `purge_ok` asserts `gap(fit→cal) >= 20td` and `gap(fit→val) >= 20td` and `gap(cal→val) >= 0`.

| Fold | fit dates | fit rows | cal dates | cal rows | val dates | val rows | gap fit→cal | gap fit→val | gap cal→val | purge ok |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- |
| 0 | 826 (2016-01-04→2019-04-15) | 332,193 | 212 (2019-05-15→2020-03-17) | 91,968 | 323 (2020-04-16→2021-07-27) | 144,087 | 20 | 252 | 20 | OK |
| 1 | 1084 (2016-01-04→2020-04-23) | 444,129 | 277 (2020-05-22→2021-06-28) | 123,614 | 324 (2021-07-28→2022-11-07) | 150,134 | 20 | 317 | 20 | OK |
| 2 | 1344 (2016-01-04→2021-05-05) | 559,995 | 341 (2021-06-04→2022-10-10) | 157,250 | 323 (2022-11-08→2024-02-22) | 154,885 | 20 | 381 | 20 | OK |
| 3 | 1602 (2016-01-04→2022-05-12) | 677,668 | 406 (2022-06-13→2024-01-24) | 193,922 | 324 (2024-02-23→2025-06-09) | 157,549 | 20 | 446 | 20 | OK |
| 4 | 1861 (2016-01-04→2023-05-24) | 800,769 | 471 (2023-06-26→2025-05-09) | 227,912 | 324 (2025-06-10→2026-09-23) | 162,262 | 20 | 511 | 20 | OK |

- Viable folds: 5 of 5; out-of-fold rows scored: 768,917.

## Event thresholds in the continuous target's units

| Event | definition (raw) | in `fwd_atr_ret_20` units |
| :--- | :--- | :--- |
| up | forward dollar move >= +2.0×ATR | `fwd_atr_ret_20 >= +2.0` |
| down | forward dollar move <= -2.0×ATR | `fwd_atr_ret_20 <= -2.0` |
| stay | forward return within ±5% (relative) | `\|fwd_atr_ret_20\| <= 0.05 / atr_pct_20` (row-specific) |

The up/down events are ATR-dollar based and the stay event is relative; the conversion uses the Step-0 named ratio `atr_pct_20`. **The events overlap** under these thresholds (a small ATR/price makes 2×ATR smaller than ±5%), so each probability is integrated independently and the overlap is reported — it is never forced into a partition.

## Probabilities P(up), P(down), P(stay) and the declared composite

- Declared shortlist composite: `P(up) - P(down)` (ADR D-010). `P(stay)` is reported alongside it and is never used as a hidden tie-break.
- Mean P(up) = 0.3012 (realized 0.3062) · mean P(down) = 0.2301 (realized 0.2105) · mean P(stay) = 0.4209 (realized 0.4260)
- Mean P(stay) exclusive of up/down = 0.3821 (realized 0.3883) — this is the `y_20d_stay` definition; the raw `P(stay)` above is the ±5% event without that exclusion.
- Mean overlap mass: up∩stay 0.0203, down∩stay 0.0185; mean P(up)+P(down)+P(stay) = 0.9521 (may exceed 1 — overlap preserved by design).
- All probabilities finite and within [0, 1] on all 768,917 scored rows.

## Calibration diagnostics

- Residual ECDF sample: 794,666 held-out residuals (pooled across folds), mean -0.1645, std +3.7064, q01 -9.7633, q05 -5.6573, q50 -0.1421, q95 +5.4462, q99 +8.8343.

| Event | n | mean predicted | realized rate | bias | Brier |
| :--- | ---: | ---: | ---: | ---: | ---: |
| P(up) | 768,917 | 0.3012 | 0.3062 | -0.0051 | 0.2149 |
| P(down) | 768,917 | 0.2301 | 0.2105 | +0.0195 | 0.1731 |
| P(stay) | 768,917 | 0.4209 | 0.4260 | -0.0051 | 0.2322 |
| P(stay) exclusive | 768,917 | 0.3821 | 0.3883 | -0.0061 | 0.2338 |

Reliability (equal-count deciles of the predicted probability):

`P(up)`:

| bin | n | predicted | realized |
| ---: | ---: | ---: | ---: |
| 1 | 76,758 | 0.2266 | 0.3150 |
| 2 | 77,026 | 0.2437 | 0.3170 |
| 3 | 76,840 | 0.2926 | 0.3146 |
| 4 | 76,878 | 0.3030 | 0.3172 |
| 5 | 76,905 | 0.3078 | 0.3200 |
| 6 | 76,891 | 0.3121 | 0.3139 |
| 7 | 76,941 | 0.3169 | 0.3173 |
| 8 | 76,867 | 0.3231 | 0.3063 |
| 9 | 76,918 | 0.3321 | 0.2913 |
| 10 | 76,893 | 0.3539 | 0.2499 |

`P(down)`:

| bin | n | predicted | realized |
| ---: | ---: | ---: | ---: |
| 1 | 76,640 | 0.1239 | 0.2662 |
| 2 | 77,143 | 0.1425 | 0.2715 |
| 3 | 76,890 | 0.2153 | 0.1864 |
| 4 | 76,802 | 0.2259 | 0.2185 |
| 5 | 76,958 | 0.2303 | 0.2284 |
| 6 | 76,858 | 0.2346 | 0.2369 |
| 7 | 76,951 | 0.2614 | 0.1373 |
| 8 | 76,885 | 0.2771 | 0.1441 |
| 9 | 76,843 | 0.2876 | 0.1906 |
| 10 | 76,947 | 0.3019 | 0.2256 |

`P(stay)`:

| bin | n | predicted | realized |
| ---: | ---: | ---: | ---: |
| 1 | 76,889 | 0.1825 | 0.2327 |
| 2 | 76,894 | 0.2582 | 0.2971 |
| 3 | 76,891 | 0.3075 | 0.3417 |
| 4 | 76,893 | 0.3513 | 0.3692 |
| 5 | 76,890 | 0.3933 | 0.4111 |
| 6 | 76,888 | 0.4345 | 0.4409 |
| 7 | 76,896 | 0.4775 | 0.4772 |
| 8 | 76,890 | 0.5260 | 0.5130 |
| 9 | 76,893 | 0.5850 | 0.5527 |
| 10 | 76,893 | 0.6932 | 0.6244 |

**Calibration limits (read before using these numbers):**

- This is a **marginal** forecast distribution, not a guarantee of conditional calibration: residuals are pooled across folds and regimes, so a row's true event probability may differ from the reported value.
- The tails are data-limited (the ECDF cannot exceed the largest observed residual), so extreme up/down probabilities are bounded by the calibration sample size.
- The residual sample is drawn from dates before each fold's validation block; regime drift between the calibration block and the validation block is not corrected.
- No independent binary classifiers were fit, and none were substituted when diagnostics are imperfect (ADR D-010).

## Skill result — same-sign and |IC| against the five E5 factors

Score-based within-date Spearman rank-IC of the continuous forecast vs `fwd_atr_ret_20`, on exactly the same out-of-fold rows and dates as every factor. Class-label IC is never used (WI-002 lesson).

| Score | mean IC | \|IC\| | t | dates |
| :--- | ---: | ---: | ---: | ---: |
| **continuous baseline (5 E5 factors)** | +0.0016 | +0.0016 | +0.38 | 1618 |
| `e5_amihud_20` (factor) | +0.0154 | 0.0154 | +5.91 | 1618 |
| `e5_log_dollar_vol_20` (factor) | -0.0145 | 0.0145 | -5.63 | 1618 |
| `e5_mom_12_1` (factor) | +0.0121 | 0.0121 | +2.70 | 1618 |
| `e5_rev_1m` (factor) | +0.0026 | 0.0026 | +0.76 | 1618 |
| `e5_vol_20` (factor) | +0.0015 | 0.0015 | +0.37 | 1618 |

- **Clause (a)** — same sign as the best factor AND |IC| >= its |IC|: **FAIL** (baseline |IC| +0.0016 vs `e5_amihud_20` |IC| +0.0154, same-sign True, margin -0.0138)
- **Clause (b)** — |t| > 2 with the same sign in >= 2 disjoint sub-windows: **FAIL** (t +0.38, 2 sub-windows, same sign all: False, |t|>2 all: False)
- **SKILL BAR: FAIL**

| Sub-window | dates | baseline mean IC | t | sign matches full window |
| ---: | ---: | ---: | ---: | :--- |
| 1 | 809 | +0.0061 | +0.92 | True |
| 2 | 809 | -0.0030 | -0.60 | False |

**This is a documented negative result, not an execution failure.** Per plan Step 2(d) a failed skill clause is reported and is not tuned away or suppressed, and no independent binary classifier is substituted.

## Shortlist — deterministic daily ranking by `P(up)-P(down)`

- As-of date: **2026-09-23** (latest scored out-of-fold date) · shortlist length 20 of 508 candidates · declared composite `P(up)-P(down)` with `symbol` ascending as the deterministic tie-break; `P(stay)` is reported alongside and is never a tie-break.
- Research output only: this is a daily shortlist for human review, not trade advice and not wired to orders.

| rank | symbol | `P(up)` | `P(down)` | `P(up)-P(down)` | `P(stay)` | forecast |
| ---: | :--- | ---: | ---: | ---: | ---: | ---: |
| 1 | `EIX` | 0.3603 | 0.1912 | +0.1691 | 0.2481 | +0.8112 |
| 2 | `ANF` | 0.3532 | 0.1966 | +0.1566 | 0.2483 | +0.7480 |
| 3 | `CRDO` | 0.3531 | 0.1968 | +0.1563 | 0.1529 | +0.7464 |
| 4 | `PATH` | 0.3498 | 0.1993 | +0.1505 | 0.1813 | +0.7182 |
| 5 | `CRCL` | 0.3472 | 0.2015 | +0.1457 | 0.1652 | +0.6949 |
| 6 | `FIGR` | 0.3450 | 0.2033 | +0.1417 | 0.1632 | +0.6745 |
| 7 | `LULU` | 0.3440 | 0.2041 | +0.1399 | 0.2610 | +0.6651 |
| 8 | `COO` | 0.3438 | 0.2043 | +0.1395 | 0.3066 | +0.6631 |
| 9 | `CHTR` | 0.3438 | 0.2043 | +0.1395 | 0.1909 | +0.6630 |
| 10 | `BURL` | 0.3386 | 0.2087 | +0.1299 | 0.2835 | +0.6144 |
| 11 | `BZ` | 0.3376 | 0.2094 | +0.1282 | 0.2693 | +0.6063 |
| 12 | `HMY` | 0.3375 | 0.2095 | +0.1279 | 0.2491 | +0.6049 |
| 13 | `COIN` | 0.3371 | 0.2098 | +0.1273 | 0.2027 | +0.6016 |
| 14 | `HUBS` | 0.3371 | 0.2098 | +0.1273 | 0.1865 | +0.6016 |
| 15 | `RELY` | 0.3371 | 0.2099 | +0.1272 | 0.2170 | +0.6008 |
| 16 | `IT` | 0.3360 | 0.2109 | +0.1251 | 0.2475 | +0.5905 |
| 17 | `EXPE` | 0.3358 | 0.2111 | +0.1247 | 0.2384 | +0.5885 |
| 18 | `HIMS` | 0.3356 | 0.2112 | +0.1244 | 0.1808 | +0.5869 |
| 19 | `SIMO` | 0.3352 | 0.2116 | +0.1236 | 0.1683 | +0.5830 |
| 20 | `ADSK` | 0.3350 | 0.2118 | +0.1233 | 0.2834 | +0.5813 |

## Fold-safe contrastive stacked-input candidate (`score_numpy`)

Not attempted in this run (`--contrastive` was not passed). The candidate is optional and is gated by the Step-1 evidence.

## Reading notes

- The five-factor probe (Step 1) is a statement about the *binary labels*; this baseline is the continuous route, so a negative result here is a statement about the five-factor continuous forecast on this window.
- `fwd_atr_ret_20` is derived from raw OHLCV by the E5 harness (`wilder_atr`, trailing); the forward window is the thing being predicted, and every feature is trailing.
- No live-use integration: the shortlist and probabilities are research output pending the human gate.

