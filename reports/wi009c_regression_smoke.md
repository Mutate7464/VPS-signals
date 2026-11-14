# WI-009c Steps 2–3 — continuous 20td regressor, band probabilities and shortlist (CAD)

- Generated (UTC): 2026-10-25T10:01:03Z  · **SMOKE RUN** (`--max-dates` cap, not the production chain)
- Panel: 18,780 rows · 313 symbols · 60 dates (2026-06-26 → 2026-09-22)
- Continuous target: `fwd_atr_ret_20` (the Step-0 named target), ATR/price column `atr_pct_20`.
- Features: the five E5 factors only (`e5_mom_12_1`, `e5_rev_1m`, `e5_vol_20`, `e5_amihud_20`, `e5_log_dollar_vol_20`). Step 1 cleared the skill bar for 0/5 labels, so plan Step 1(d) gates all 89-feature and optional-candidate spend — this baseline is limited to the same five factors.
- Model: `StandardScaler` + `Ridge(alpha=100)`, float32 features, BLAS/OMP threads pinned to 2. Wall clock 0.0s.
- CV: `PurgedWalkForwardSplit(n_splits=5, embargo_td=20)` over unique dates keyed by *positions* (`src.factors.e5_baseline.date_positions`).
- Split calibration (ADR D-010): per fold the last 20% of the training dates (purged 20td from the fit block) supplies the held-out residual empirical CDF; the model is fit on the remaining training dates only.

## Fold plan and leakage evidence

Calibration residuals are drawn from the `cal` block, which is disjoint from the `fit` block that trained that fold's model, and both are separated from the `val` block by the 20td purge. `purge_ok` asserts `gap(fit→cal) >= 20td` and `gap(fit→val) >= 20td` and `gap(cal→val) >= 0`.

| Fold | fit dates | fit rows | cal dates | cal rows | val dates | val rows | gap fit→cal | gap fit→val | gap cal→val | purge ok |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- |
| 0 | — | — | — | — | 7 | — | — | — | — | SKIPPED (purge emptied the fit or calibration block) |
| 1 | — | — | — | — | 7 | — | — | — | — | SKIPPED (purge emptied the fit or calibration block) |
| 2 | — | — | — | — | 7 | — | — | — | — | SKIPPED (purge emptied the fit or calibration block) |
| 3 | — | — | — | — | 7 | — | — | — | — | SKIPPED (purge emptied the fit or calibration block) |
| 4 | 5 (2026-06-26→2026-07-03) | 1,565 | 7 (2026-08-04→2026-08-12) | 2,191 | 8 (2026-09-11→2026-09-22) | 2,504 | 20 | 47 | 20 | OK |

- Viable folds: 1 of 5; out-of-fold rows scored: 2,504.

## Event thresholds in the continuous target's units

| Event | definition (raw) | in `fwd_atr_ret_20` units |
| :--- | :--- | :--- |
| up | forward dollar move >= +2.0×ATR | `fwd_atr_ret_20 >= +2.0` |
| down | forward dollar move <= -2.0×ATR | `fwd_atr_ret_20 <= -2.0` |
| stay | forward return within ±5% (relative) | `\|fwd_atr_ret_20\| <= 0.05 / atr_pct_20` (row-specific) |

The up/down events are ATR-dollar based and the stay event is relative; the conversion uses the Step-0 named ratio `atr_pct_20`. **The events overlap** under these thresholds (a small ATR/price makes 2×ATR smaller than ±5%), so each probability is integrated independently and the overlap is reported — it is never forced into a partition.

## Probabilities P(up), P(down), P(stay) and the declared composite

- Declared shortlist composite: `P(up) - P(down)` (ADR D-010). `P(stay)` is reported alongside it and is never used as a hidden tie-break.
- Mean P(up) = 0.3213 (realized 0.2376) · mean P(down) = 0.2473 (realized 0.2296) · mean P(stay) = 0.3838 (realized 0.4617)
- Mean P(stay) exclusive of up/down = 0.3417 (realized 0.4217) — this is the `y_20d_stay` definition; the raw `P(stay)` above is the ±5% event without that exclusion.
- Mean overlap mass: up∩stay 0.0245, down∩stay 0.0177; mean P(up)+P(down)+P(stay) = 0.9525 (may exceed 1 — overlap preserved by design).
- All probabilities finite and within [0, 1] on all 2,504 scored rows.

## Calibration diagnostics

- Residual ECDF sample: 2,191 held-out residuals (pooled across folds), mean -0.4996, std +3.2288, q01 -7.3544, q05 -5.3496, q50 -0.8368, q95 +4.8834, q99 +6.9296.

| Event | n | mean predicted | realized rate | bias | Brier |
| :--- | ---: | ---: | ---: | ---: | ---: |
| P(up) | 2,504 | 0.3213 | 0.2376 | +0.0837 | 0.1828 |
| P(down) | 2,504 | 0.2473 | 0.2296 | +0.0177 | 0.1670 |
| P(stay) | 2,504 | 0.3838 | 0.4617 | -0.0778 | 0.2158 |
| P(stay) exclusive | 2,504 | 0.3417 | 0.4217 | -0.0801 | 0.2316 |

Reliability (equal-count deciles of the predicted probability):

`P(up)`:

| bin | n | predicted | realized |
| ---: | ---: | ---: | ---: |
| 1 | 248 | 0.1650 | 0.0726 |
| 2 | 253 | 0.2311 | 0.0949 |
| 3 | 250 | 0.2694 | 0.1800 |
| 4 | 247 | 0.3027 | 0.2753 |
| 5 | 252 | 0.3271 | 0.2738 |
| 6 | 233 | 0.3460 | 0.3305 |
| 7 | 267 | 0.3655 | 0.3146 |
| 8 | 248 | 0.3846 | 0.3145 |
| 9 | 255 | 0.3997 | 0.2667 |
| 10 | 251 | 0.4190 | 0.2550 |

`P(down)`:

| bin | n | predicted | realized |
| ---: | ---: | ---: | ---: |
| 1 | 246 | 0.1247 | 0.1748 |
| 2 | 252 | 0.1443 | 0.1111 |
| 3 | 251 | 0.1634 | 0.1195 |
| 4 | 245 | 0.1851 | 0.0980 |
| 5 | 249 | 0.2095 | 0.1807 |
| 6 | 255 | 0.2353 | 0.2275 |
| 7 | 255 | 0.2647 | 0.2627 |
| 8 | 232 | 0.3083 | 0.2802 |
| 9 | 268 | 0.3592 | 0.4142 |
| 10 | 251 | 0.4716 | 0.4143 |

`P(stay)`:

| bin | n | predicted | realized |
| ---: | ---: | ---: | ---: |
| 1 | 251 | 0.1537 | 0.1833 |
| 2 | 250 | 0.1954 | 0.2400 |
| 3 | 248 | 0.2382 | 0.2863 |
| 4 | 251 | 0.2980 | 0.3745 |
| 5 | 252 | 0.3472 | 0.4325 |
| 6 | 249 | 0.3925 | 0.3976 |
| 7 | 252 | 0.4433 | 0.5317 |
| 8 | 250 | 0.4938 | 0.7280 |
| 9 | 249 | 0.5564 | 0.5944 |
| 10 | 252 | 0.7181 | 0.8452 |

**Calibration limits (read before using these numbers):**

- This is a **marginal** forecast distribution, not a guarantee of conditional calibration: residuals are pooled across folds and regimes, so a row's true event probability may differ from the reported value.
- The tails are data-limited (the ECDF cannot exceed the largest observed residual), so extreme up/down probabilities are bounded by the calibration sample size.
- The residual sample is drawn from dates before each fold's validation block; regime drift between the calibration block and the validation block is not corrected.
- No independent binary classifiers were fit, and none were substituted when diagnostics are imperfect (ADR D-010).

## Skill result — same-sign and |IC| against the five E5 factors

Score-based within-date Spearman rank-IC of the continuous forecast vs `fwd_atr_ret_20`, on exactly the same out-of-fold rows and dates as every factor. Class-label IC is never used (WI-002 lesson).

| Score | mean IC | \|IC\| | t | dates |
| :--- | ---: | ---: | ---: | ---: |
| **continuous baseline (5 E5 factors)** | +0.2759 | +0.2759 | +6.35 | 8 |
| `e5_vol_20` (factor) | -0.2893 | 0.2893 | -6.94 | 8 |
| `e5_mom_12_1` (factor) | -0.1132 | 0.1132 | -2.47 | 8 |
| `e5_rev_1m` (factor) | -0.0723 | 0.0723 | -3.24 | 8 |
| `e5_amihud_20` (factor) | -0.0460 | 0.0460 | -4.24 | 8 |
| `e5_log_dollar_vol_20` (factor) | -0.0440 | 0.0440 | -4.09 | 8 |

- **Clause (a)** — same sign as the best factor AND |IC| >= its |IC|: **FAIL** (baseline |IC| +0.2759 vs `e5_vol_20` |IC| +0.2893, same-sign False, margin -0.0134)
- **Clause (b)** — |t| > 2 with the same sign in >= 2 disjoint sub-windows: **PASS** (t +6.35, 2 sub-windows, same sign all: True, |t|>2 all: True)
- **SKILL BAR: FAIL**

Caveats (emitted verbatim by the reused `src/models/skill_bar.py`):

- SIGN INVERTED — the model's val IC has the opposite sign to the best factor (+0.2759 vs `vol_20` -0.2893). Clause (a) is a |IC| comparison, so it is met in MAGNITUDE only: the model is anti-correlated with forward returns on this window, and a sign flip (which would make the sign positive) is not claimed here because it would be chosen on this same window.

- **Correction for this run:** clause (a) also FAILS on magnitude (baseline |IC| +0.2759 < `e5_vol_20` |IC| +0.2893), so the "met in MAGNITUDE only" phrasing in the caveat above does **not** apply here — the bar fails on both clauses.

| Sub-window | dates | baseline mean IC | t | sign matches full window |
| ---: | ---: | ---: | ---: | :--- |
| 1 | 4 | +0.1824 | +3.56 | True |
| 2 | 4 | +0.3694 | +19.45 | True |

**This is a documented negative result, not an execution failure.** Per plan Step 2(d) a failed skill clause is reported and is not tuned away or suppressed, and no independent binary classifier is substituted.

## Shortlist — deterministic daily ranking by `P(up)-P(down)`

- As-of date: **2026-09-22** (latest scored out-of-fold date) · shortlist length 20 of 313 candidates · declared composite `P(up)-P(down)` with `symbol` ascending as the deterministic tie-break; `P(stay)` is reported alongside and is never a tie-break.
- Research output only: this is a daily shortlist for human review, not trade advice and not wired to orders.

| rank | symbol | `P(up)` | `P(down)` | `P(up)-P(down)` | `P(stay)` | forecast |
| ---: | :--- | ---: | ---: | ---: | ---: | ---: |
| 1 | `ABT` | 0.4345 | 0.1114 | +0.3231 | 0.4952 | +2.2171 |
| 2 | `LBS.PR.A` | 0.4345 | 0.1114 | +0.3231 | 0.9963 | +2.2189 |
| 3 | `BKNG` | 0.4340 | 0.1118 | +0.3222 | 0.3441 | +2.2162 |
| 4 | `MRG.UN` | 0.4340 | 0.1118 | +0.3222 | 0.6499 | +2.2158 |
| 5 | `PEP` | 0.4340 | 0.1118 | +0.3222 | 0.5874 | +2.2145 |
| 6 | `MA` | 0.4299 | 0.1136 | +0.3163 | 0.6134 | +2.1641 |
| 7 | `CRR.UN` | 0.4258 | 0.1182 | +0.3076 | 0.5924 | +2.1136 |
| 8 | `CGO` | 0.4231 | 0.1205 | +0.3026 | 0.4587 | +2.0940 |
| 9 | `HD` | 0.4226 | 0.1205 | +0.3021 | 0.4911 | +2.0903 |
| 10 | `MTY` | 0.4226 | 0.1209 | +0.3017 | 0.4719 | +2.0887 |
| 11 | `BX` | 0.4217 | 0.1228 | +0.2990 | 0.4153 | +2.0797 |
| 12 | `CRT.UN` | 0.4204 | 0.1241 | +0.2962 | 0.6385 | +2.0622 |
| 13 | `T` | 0.4185 | 0.1251 | +0.2935 | 0.4692 | +2.0521 |
| 14 | `XRE` | 0.4176 | 0.1260 | +0.2916 | 0.7668 | +2.0456 |
| 15 | `RSI` | 0.4176 | 0.1269 | +0.2907 | 0.7335 | +2.0398 |
| 16 | `COST` | 0.4172 | 0.1273 | +0.2898 | 0.6225 | +2.0332 |
| 17 | `PBH` | 0.4172 | 0.1273 | +0.2898 | 0.5007 | +2.0289 |
| 18 | `DIR.UN` | 0.4153 | 0.1283 | +0.2871 | 0.5742 | +2.0041 |
| 19 | `JWEL` | 0.4149 | 0.1283 | +0.2866 | 0.9325 | +1.9967 |
| 20 | `KMP.UN` | 0.4149 | 0.1283 | +0.2866 | 0.5687 | +1.9875 |

## Fold-safe contrastive stacked-input candidate (`score_numpy`)

Not attempted in this run (`--contrastive` was not passed). The candidate is optional and is gated by the Step-1 evidence.

## Reading notes

- The five-factor probe (Step 1) is a statement about the *binary labels*; this baseline is the continuous route, so a negative result here is a statement about the five-factor continuous forecast on this window.
- `fwd_atr_ret_20` is derived from raw OHLCV by the E5 harness (`wilder_atr`, trailing); the forward window is the thing being predicted, and every feature is trailing.
- No live-use integration: the shortlist and probabilities are research output pending the human gate.

