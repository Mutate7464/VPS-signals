# WI-009c Steps 2–3 — continuous 20td regressor, band probabilities and shortlist (CAD)

- Generated (UTC): 2026-10-26T16:51:46Z
- Panel: 677,313 rows · 313 symbols · 2691 dates (2016-01-04 → 2026-09-22)
- Continuous target: `fwd_atr_ret_20` (the Step-0 named target), ATR/price column `atr_pct_20`.
- Features: the five E5 factors only (`e5_mom_12_1`, `e5_rev_1m`, `e5_vol_20`, `e5_amihud_20`, `e5_log_dollar_vol_20`). Step 1 cleared the skill bar for 0/5 labels, so plan Step 1(d) gates all 89-feature and optional-candidate spend — this baseline is limited to the same five factors.
- Model: `StandardScaler` + `Ridge(alpha=100)`, float32 features, BLAS/OMP threads pinned to 2. Wall clock 0.8s.
- CV: `PurgedWalkForwardSplit(n_splits=5, embargo_td=20)` over unique dates keyed by *positions* (`src.factors.e5_baseline.date_positions`).
- Split calibration (ADR D-010): per fold the last 20% of the training dates (purged 20td from the fit block) supplies the held-out residual empirical CDF; the model is fit on the remaining training dates only.

## Fold plan and leakage evidence

Calibration residuals are drawn from the `cal` block, which is disjoint from the `fit` block that trained that fold's model, and both are separated from the `val` block by the 20td purge. `purge_ok` asserts `gap(fit→cal) >= 20td` and `gap(fit→val) >= 20td` and `gap(cal→val) >= 0`.

| Fold | fit dates | fit rows | cal dates | cal rows | val dates | val rows | gap fit→cal | gap fit→val | gap cal→val | purge ok |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- |
| 0 | 824 (2016-01-04→2019-04-12) | 183,918 | 212 (2019-05-14→2020-03-17) | 49,545 | 323 (2020-04-16→2021-07-28) | 76,713 | 20 | 252 | 20 | OK |
| 1 | 1083 (2016-01-04→2020-04-24) | 244,495 | 276 (2020-05-26→2021-06-29) | 65,561 | 323 (2021-07-29→2022-11-10) | 79,109 | 20 | 316 | 20 | OK |
| 2 | 1341 (2016-01-04→2021-05-05) | 305,694 | 341 (2021-06-04→2022-10-13) | 83,056 | 323 (2022-11-11→2024-02-26) | 88,365 | 20 | 381 | 20 | OK |
| 3 | 1600 (2016-01-04→2022-05-17) | 368,182 | 405 (2022-06-16→2024-01-26) | 108,372 | 323 (2024-02-27→2025-06-09) | 92,040 | 20 | 445 | 20 | OK |
| 4 | 1858 (2016-01-04→2023-05-29) | 435,335 | 470 (2023-06-27→2025-05-09) | 132,437 | 323 (2025-06-10→2026-09-22) | 98,243 | 20 | 510 | 20 | OK |

- Viable folds: 5 of 5; out-of-fold rows scored: 434,470.

## Event thresholds in the continuous target's units

| Event | definition (raw) | in `fwd_atr_ret_20` units |
| :--- | :--- | :--- |
| up | forward dollar move >= +2.0×ATR | `fwd_atr_ret_20 >= +2.0` |
| down | forward dollar move <= -2.0×ATR | `fwd_atr_ret_20 <= -2.0` |
| stay | forward return within ±5% (relative) | `\|fwd_atr_ret_20\| <= 0.05 / atr_pct_20` (row-specific) |

The up/down events are ATR-dollar based and the stay event is relative; the conversion uses the Step-0 named ratio `atr_pct_20`. **The events overlap** under these thresholds (a small ATR/price makes 2×ATR smaller than ±5%), so each probability is integrated independently and the overlap is reported — it is never forced into a partition.

## Probabilities P(up), P(down), P(stay) and the declared composite

- Declared shortlist composite: `P(up) - P(down)` (ADR D-010). `P(stay)` is reported alongside it and is never used as a hidden tie-break.
- Mean P(up) = 0.2840 (realized 0.3050) · mean P(down) = 0.2132 (realized 0.1848) · mean P(stay) = 0.4634 (realized 0.4674)
- Mean P(stay) exclusive of up/down = 0.4073 (realized 0.4083) — this is the `y_20d_stay` definition; the raw `P(stay)` above is the ±5% event without that exclusion.
- Mean overlap mass: up∩stay 0.0299, down∩stay 0.0262; mean P(up)+P(down)+P(stay) = 0.9607 (may exceed 1 — overlap preserved by design).
- All probabilities finite and within [0, 1] on all 434,470 scored rows.

## Calibration diagnostics

- Residual ECDF sample: 438,971 held-out residuals (pooled across folds), mean +0.0066, std +3.8417, q01 -8.9340, q05 -5.0693, q50 -0.0321, q95 +5.4481, q99 +8.7849.

| Event | n | mean predicted | realized rate | bias | Brier |
| :--- | ---: | ---: | ---: | ---: | ---: |
| P(up) | 434,470 | 0.2840 | 0.3050 | -0.0209 | 0.2138 |
| P(down) | 434,470 | 0.2132 | 0.1848 | +0.0285 | 0.1565 |
| P(stay) | 434,470 | 0.4634 | 0.4674 | -0.0039 | 0.2247 |
| P(stay) exclusive | 434,470 | 0.4073 | 0.4083 | -0.0010 | 0.2348 |

Reliability (equal-count deciles of the predicted probability):

`P(up)`:

| bin | n | predicted | realized |
| ---: | ---: | ---: | ---: |
| 1 | 43,394 | 0.2300 | 0.2887 |
| 2 | 43,498 | 0.2449 | 0.2886 |
| 3 | 43,409 | 0.2625 | 0.3188 |
| 4 | 43,443 | 0.2718 | 0.3102 |
| 5 | 43,479 | 0.2789 | 0.3226 |
| 6 | 43,459 | 0.2874 | 0.3323 |
| 7 | 43,406 | 0.2985 | 0.3442 |
| 8 | 43,437 | 0.3088 | 0.3145 |
| 9 | 43,489 | 0.3189 | 0.2731 |
| 10 | 43,456 | 0.3383 | 0.2566 |

`P(down)`:

| bin | n | predicted | realized |
| ---: | ---: | ---: | ---: |
| 1 | 43,289 | 0.1220 | 0.2229 |
| 2 | 43,604 | 0.1472 | 0.2315 |
| 3 | 43,432 | 0.1918 | 0.1746 |
| 4 | 43,424 | 0.2021 | 0.1734 |
| 5 | 43,390 | 0.2083 | 0.1923 |
| 6 | 43,538 | 0.2150 | 0.1803 |
| 7 | 43,436 | 0.2302 | 0.1923 |
| 8 | 43,413 | 0.2474 | 0.2105 |
| 9 | 43,489 | 0.2702 | 0.1303 |
| 10 | 43,455 | 0.2983 | 0.1395 |

`P(stay)`:

| bin | n | predicted | realized |
| ---: | ---: | ---: | ---: |
| 1 | 43,443 | 0.1878 | 0.2335 |
| 2 | 43,449 | 0.2665 | 0.2938 |
| 3 | 43,449 | 0.3214 | 0.3446 |
| 4 | 43,445 | 0.3713 | 0.3779 |
| 5 | 43,449 | 0.4205 | 0.4164 |
| 6 | 43,445 | 0.4723 | 0.4756 |
| 7 | 43,448 | 0.5280 | 0.5385 |
| 8 | 43,447 | 0.5889 | 0.6010 |
| 9 | 43,448 | 0.6663 | 0.6472 |
| 10 | 43,447 | 0.8114 | 0.7453 |

**Calibration limits (read before using these numbers):**

- This is a **marginal** forecast distribution, not a guarantee of conditional calibration: residuals are pooled across folds and regimes, so a row's true event probability may differ from the reported value.
- The tails are data-limited (the ECDF cannot exceed the largest observed residual), so extreme up/down probabilities are bounded by the calibration sample size.
- The residual sample is drawn from dates before each fold's validation block; regime drift between the calibration block and the validation block is not corrected.
- No independent binary classifiers were fit, and none were substituted when diagnostics are imperfect (ADR D-010).

## Skill result — same-sign and |IC| against the five E5 factors

Score-based within-date Spearman rank-IC of the continuous forecast vs `fwd_atr_ret_20`, on exactly the same out-of-fold rows and dates as every factor. Class-label IC is never used (WI-002 lesson).

| Score | mean IC | \|IC\| | t | dates |
| :--- | ---: | ---: | ---: | ---: |
| **continuous baseline (5 E5 factors)** | +0.0001 | +0.0001 | +0.03 | 1615 |
| `e5_vol_20` (factor) | -0.0307 | 0.0307 | -5.86 | 1615 |
| `e5_mom_12_1` (factor) | +0.0135 | 0.0135 | +2.77 | 1615 |
| `e5_rev_1m` (factor) | +0.0098 | 0.0098 | +2.53 | 1615 |
| `e5_amihud_20` (factor) | -0.0052 | 0.0052 | -1.73 | 1615 |
| `e5_log_dollar_vol_20` (factor) | -0.0034 | 0.0034 | -1.39 | 1615 |

- **Clause (a)** — same sign as the best factor AND |IC| >= its |IC|: **FAIL** (baseline |IC| +0.0001 vs `e5_vol_20` |IC| +0.0307, same-sign False, margin -0.0306)
- **Clause (b)** — |t| > 2 with the same sign in >= 2 disjoint sub-windows: **FAIL** (t +0.03, 2 sub-windows, same sign all: False, |t|>2 all: True)
- **SKILL BAR: FAIL**

Caveats (emitted verbatim by the reused `src/models/skill_bar.py`):

- SIGN INVERTED — the model's val IC has the opposite sign to the best factor (+0.0001 vs `vol_20` -0.0307). Clause (a) is a |IC| comparison, so it is met in MAGNITUDE only: the model is anti-correlated with forward returns on this window, and a sign flip (which would make the sign positive) is not claimed here because it would be chosen on this same window.

- **Correction for this run:** clause (a) also FAILS on magnitude (baseline |IC| +0.0001 < `e5_vol_20` |IC| +0.0307), so the "met in MAGNITUDE only" phrasing in the caveat above does **not** apply here — the bar fails on both clauses.

| Sub-window | dates | baseline mean IC | t | sign matches full window |
| ---: | ---: | ---: | ---: | :--- |
| 1 | 808 | +0.0268 | +4.18 | True |
| 2 | 807 | -0.0266 | -5.28 | False |

**This is a documented negative result, not an execution failure.** Per plan Step 2(d) a failed skill clause is reported and is not tuned away or suppressed, and no independent binary classifier is substituted.

## Shortlist — deterministic daily ranking by `P(up)-P(down)`

- As-of date: **2026-09-22** (latest scored out-of-fold date) · shortlist length 20 of 313 candidates · declared composite `P(up)-P(down)` with `symbol` ascending as the deterministic tie-break; `P(stay)` is reported alongside and is never a tie-break.
- Research output only: this is a daily shortlist for human review, not trade advice and not wired to orders.

| rank | symbol | `P(up)` | `P(down)` | `P(up)-P(down)` | `P(stay)` | forecast |
| ---: | :--- | ---: | ---: | ---: | ---: | ---: |
| 1 | `IE` | 0.3428 | 0.1725 | +0.1703 | 0.2082 | +0.6282 |
| 2 | `FISV` | 0.3426 | 0.1727 | +0.1699 | 0.3537 | +0.6266 |
| 3 | `STC` | 0.3411 | 0.1739 | +0.1672 | 0.4022 | +0.6143 |
| 4 | `PYPL` | 0.3370 | 0.1767 | +0.1602 | 0.4063 | +0.5790 |
| 5 | `PRU` | 0.3357 | 0.1778 | +0.1579 | 0.2524 | +0.5674 |
| 6 | `ET` | 0.3343 | 0.1788 | +0.1555 | 0.3206 | +0.5556 |
| 7 | `F` | 0.3321 | 0.1805 | +0.1516 | 0.4185 | +0.5355 |
| 8 | `BKNG` | 0.3319 | 0.1806 | +0.1513 | 0.3594 | +0.5343 |
| 9 | `BX` | 0.3305 | 0.1815 | +0.1490 | 0.4385 | +0.5226 |
| 10 | `EPRX` | 0.3301 | 0.1819 | +0.1482 | 0.2838 | +0.5191 |
| 11 | `BOFA` | 0.3297 | 0.1823 | +0.1474 | 0.6008 | +0.5157 |
| 12 | `VZ` | 0.3283 | 0.1832 | +0.1451 | 0.5588 | +0.5044 |
| 13 | `DIS` | 0.3275 | 0.1839 | +0.1436 | 0.5796 | +0.4973 |
| 14 | `SFC` | 0.3274 | 0.1839 | +0.1435 | 0.3996 | +0.4967 |
| 15 | `LULU` | 0.3272 | 0.1841 | +0.1431 | 0.2956 | +0.4953 |
| 16 | `MNO` | 0.3272 | 0.1841 | +0.1431 | 0.2827 | +0.4952 |
| 17 | `ABT` | 0.3264 | 0.1846 | +0.1418 | 0.5425 | +0.4892 |
| 18 | `ADBE` | 0.3260 | 0.1849 | +0.1411 | 0.3110 | +0.4859 |
| 19 | `GE` | 0.3259 | 0.1852 | +0.1407 | 0.4743 | +0.4841 |
| 20 | `WGX` | 0.3255 | 0.1853 | +0.1402 | 0.3442 | +0.4817 |

## Fold-safe contrastive stacked-input candidate (`score_numpy`)

Not attempted in this run (`--contrastive` was not passed). The candidate is optional and is gated by the Step-1 evidence.

## Reading notes

- The five-factor probe (Step 1) is a statement about the *binary labels*; this baseline is the continuous route, so a negative result here is a statement about the five-factor continuous forecast on this window.
- `fwd_atr_ret_20` is derived from raw OHLCV by the E5 harness (`wilder_atr`, trailing); the forward window is the thing being predicted, and every feature is trailing.
- No live-use integration: the shortlist and probabilities are research output pending the human gate.

