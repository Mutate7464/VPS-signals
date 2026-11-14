# WI-009c — final evaluation and human gate package (USD)

- Generated (UTC): 2026-10-26T06:41:36Z from the fixed run outputs (no model was re-fit, no fold re-run).
- **Run identity**: `reports/wi009c_regression_USD.json` · generated 2026-10-26T06:39:17.958421+00:00 · smoke=False · market USD.
- **Model**: `StandardScaler` + `Ridge(alpha=100.0)` on the 5 E5 factors (`e5_mom_12_1`, `e5_rev_1m`, `e5_vol_20`, `e5_amihud_20`, `e5_log_dollar_vol_20`), target `fwd_atr_ret_20`, ATR/price column `atr_pct_20`.
- **CV**: `PurgedWalkForwardSplit(n_splits=5, embargo_td=20)` over unique dates keyed by positions; per-fold split-calibration block of the last 20% of the training dates (purged 20td from the fit block). 5 of 5 folds viable.
- **Panel**: 1,210,402 rows · 508 symbols · 2696 dates (2016-01-04 → 2026-09-23); **768,917 out-of-fold rows** scored across folds [0, 1, 2, 3, 4] (1618 dates).
- **Event units** (ADR D-010): up = `fwd_atr_ret_20 >= +2.0` (2×ATR, dollar); down = `fwd_atr_ret_20 <= -2.0`; stay = `|fwd_atr_ret_20| <= 0.05 / atr_pct_20` (row-specific ±5%, relative). The events **overlap** (mean up∩stay 0.0203, down∩stay 0.0185); each probability is integrated independently from the residual ECDF and the overlap is reported, never forced into a partition.

## 1. Verdict table per target (Step 1 — five-factor logistic probe)

The unchanged skill bar: clause (a) = same sign as the best factor **AND** |IC| ≥ its |IC|; clause (b) = |t| > 2 with the same sign in ≥ 2 disjoint sub-windows. Class-label IC is never used.

| Target | OOF logit IC | t | same sign | clause (a) | clause (b) | skill bar |
| :--- | ---: | ---: | :--- | :--- | :--- | :--- |
| `y_15d_high` | +0.0001 | +0.04 | yes | FAIL | FAIL | **NEGATIVE RESULT** |
| `y_15d_low` | +0.0304 | +6.86 | NO | FAIL | PASS | **NEGATIVE RESULT** |
| `y_20d_up` | +0.0123 | +3.15 | NO | FAIL | FAIL | **NEGATIVE RESULT** |
| `y_20d_down` | -0.0231 | -5.19 | NO | FAIL | FAIL | **NEGATIVE RESULT** |
| `y_20d_stay` | -0.0355 | -10.06 | yes | FAIL | PASS | **NEGATIVE RESULT** |

- **0/5 targets clear the unchanged skill bar.** No label is demonstrated learnable on this window by the five E5 factors.
- Gate consequence (plan Step 1(d)): no label demonstrated learnable — no 89-feature spend; limit the continuous baseline to the same five factors.
- This is a **negative result about these binary labels**, not an execution failure.

## 2. Continuous 20td baseline (Step 2)

- Target: `fwd_atr_ret_20`; declared shortlist composite: **`P(up) - P(down)`** (ADR D-010). `P(stay)` is reported alongside it and is never used as a hidden tie-break.
- Recorded probabilities (mean predicted) vs realized rate on the same 768,917 OOF rows:

| Event | mean predicted | realized rate | bias | Brier |
| :--- | ---: | ---: | ---: | ---: |
| P(up) | 0.3012 | 0.3062 | -0.0051 | 0.2149 |
| P(down) | 0.2301 | 0.2105 | +0.0195 | 0.1731 |
| P(stay) | 0.4209 | 0.4260 | -0.0051 | 0.2322 |
| P(stay) exclusive | 0.3821 | 0.3883 | -0.0061 | 0.2338 |

- Mean `P(up) + P(down) + P(stay)` = 0.9521 (may exceed 1 — the events overlap by design); all probabilities finite and within [0, 1] on every scored row.
- Shortlist: 20 names as of **2026-09-23** (of 508 candidates); ordering by the declared composite verified (True), symbol tie-break verified (True), max |composite - (P(up)-P(down))| = 1.11e-16.

| rank | symbol | `P(up)` | `P(down)` | `P(up)-P(down)` | `P(stay)` |
| ---: | :--- | ---: | ---: | ---: | ---: |
| 1 | `EIX` | 0.3603 | 0.1912 | +0.1691 | 0.2481 |
| 2 | `ANF` | 0.3532 | 0.1966 | +0.1566 | 0.2483 |
| 3 | `CRDO` | 0.3531 | 0.1968 | +0.1563 | 0.1529 |
| 4 | `PATH` | 0.3498 | 0.1993 | +0.1505 | 0.1813 |
| 5 | `CRCL` | 0.3472 | 0.2015 | +0.1457 | 0.1652 |
| 6 | `FIGR` | 0.3450 | 0.2033 | +0.1417 | 0.1632 |
| 7 | `LULU` | 0.3440 | 0.2041 | +0.1399 | 0.2610 |
| 8 | `COO` | 0.3438 | 0.2043 | +0.1395 | 0.3066 |
| 9 | `CHTR` | 0.3438 | 0.2043 | +0.1395 | 0.1909 |
| 10 | `BURL` | 0.3386 | 0.2087 | +0.1299 | 0.2835 |

### Skill result — same-sign and |IC| against the five E5 factors

Score-based within-date Spearman rank-IC of the continuous forecast vs `fwd_atr_ret_20`, on exactly the same out-of-fold rows and dates as every factor.

| Score | mean IC | \|IC\| | t | dates |
| :--- | ---: | ---: | ---: | ---: |
| **continuous baseline (5 E5 factors)** | +0.0016 | +0.0016 | +0.38 | 1618 |
| `e5_amihud_20` (factor) | +0.0154 | 0.0154 | +5.91 | 1618 |
| `e5_log_dollar_vol_20` (factor) | -0.0145 | 0.0145 | -5.63 | 1618 |
| `e5_mom_12_1` (factor) | +0.0121 | 0.0121 | +2.70 | 1618 |
| `e5_rev_1m` (factor) | +0.0026 | 0.0026 | +0.76 | 1618 |
| `e5_vol_20` (factor) | +0.0015 | 0.0015 | +0.37 | 1618 |

- Clause (a) — same sign as the best factor AND |IC| ≥ its |IC|: **FAIL** (baseline |IC| +0.0016 vs `e5_amihud_20` |IC| +0.0154; same-sign **True**).
- Clause (b) — |t| > 2 with the same sign in ≥ 2 disjoint sub-windows: **FAIL**.
- **SKILL BAR: FAIL** — the five-factor continuous forecast does not beat the best single E5 factor on this window.
- Calibration is a **marginal** distribution from held-out residuals pooled across folds: it is not a guarantee of conditional calibration per row, symbol or regime, and the ECDF tails are limited by the calibration sample size.

## 3. Robustness options and the fold-safe stacked-input candidate (Steps 3–4)

- Fold-safe contrastive stacked input (`models/contrastive_ranker_wi009b.pt`, `score_numpy`): **not attempted** — not attempted in the production chain.
- Step-4 robustness record: `reports/wi009c_robustness.md` — 3 option(s) **NOT RUN**, 0 gate decision(s) GO. Candidates covered: regime, stacking, dynamic feature.
- Every robustness candidate needs the 89-feature spend that Step 1(d) withholds, so each is reported as NOT RUN with its specific unmet gate — a documented no-go, never a hidden FAIL and never built by default (plan Step 4(d)).

## 4. Route verdict as a whole

| Question | Verdict | Basis |
| :--- | :--- | :--- |
| Are the existing binary labels learnable from the five E5 factors? | **NO — 0/5 clear the unchanged skill bar** | Step 1 probe, purged OOF, score-based within-date IC |
| Does the five-factor continuous 20td forecast beat the best single factor? | **NO — skill bar FAIL** (IC +0.0016 vs |IC| +0.0154, same-sign True) | Step 2, 768,917 OOF rows, 5/5 folds |
| Are the distribution-derived probabilities usable? | **Numerically yes, skilfully unproven** — finite, in [0, 1], marginal calibration reported (mean P(stay) 0.4209 vs realized 0.4260) | Step 2 calibration diagnostics |
| May the fold-safe contrastive stacked input be used? | **NO (NOT RUN, gated)** | Step 1(d) gate + fold-safety not establishable (Step 3) |
| Do any robustness options qualify? | **NO (NOT RUN, gated)** | Step 4 evidence gates |
| Is the route usable for trading? | **No — human gate decision required** | this report |

**The continuous route is not demonstrated to have skill on this CAD window.** The probabilities have the right units, are finite and bounded, and their marginal calibration is reported — but the forecast is statistically indistinguishable from (and slightly weaker than) the best single E5 factor, and the binary labels are not demonstrated learnable. Nothing here is a claim of skill.

## 5. Negative results vs execution/test failures

- **Negative results** (content, not failures): 0/5 labels clear the skill bar; the continuous baseline fails the skill bar; the contrastive stacked input is omitted (gated); all three robustness options are NOT RUN (gated). Each is recorded with its reason and evidence, and none was tuned away, suppressed or substituted by a different model.
- **Execution/test failures**: none. This report is written only after every internal consistency check below passes; a failed check aborts the run with a non-zero exit instead of printing a verdict.

## 6. Reproducibility check (recomputed from the saved per-row outputs)

- Source: `data/wi009c_oof_USD.parquet` — 768,917 OOF rows re-reduced; nothing re-fit.
- Recorded (run JSON) vs recomputed (parquet) masses agree within 2e-05 absolute; every probability is finite and inside [0, 1]; the shortlist ordering matches the declared composite.

- `mean_p_up`: recorded 0.301167 · recomputed 0.301167
- `mean_p_down`: recorded 0.230058 · recomputed 0.230058
- `mean_p_stay`: recorded 0.420911 · recomputed 0.420911
- `mean_p_stay_exclusive`: recorded 0.382130 · recomputed 0.382130
- `realized_rate_up`: recorded 0.306244 · recomputed 0.306244
- `realized_rate_down`: recorded 0.210548 · recomputed 0.210548
- `realized_rate_stay`: recorded 0.425980 · recomputed 0.425980
- `mean_overlap_up_stay`: recorded 0.020328 · recomputed 0.020328
- `mean_overlap_down_stay`: recorded 0.018452 · recomputed 0.018452
- `mean_sum_up_down_stay`: recorded 0.952136 · recomputed 0.952136

Re-run this package with:

```bash
uv run python scripts/evaluate_wi009c.py --market USD
```

## 7. Human gate — decision requested

This is a **research output**. No sprint gate is marked passed here, the shortlist is **not** wired to orders, and no live-use integration exists (daily shortlist only; human gate before any execution use).

The decision requested from the human gate:

1. **Accept the route as a documented negative result** (labels not demonstrated learnable from the five E5 factors; five-factor continuous forecast fails the unchanged skill bar) and stop WI-009c, or
2. **Re-spec the target** (the Step-1 evidence points at the labels, not the model class) — a new work item, or
3. **Authorise one gated option** (regime features / priced-in contrastive stacking / dynamic feature selection) with a written go decision, since every one of them needs the 89-feature spend Step 1(d) withholds.

Reading notes:

- `P(up)`, `P(down)` and `P(stay)` are forecast *distribution* quantities, not guarantees; the overlap between the ±5% stay band and the 2×ATR up/down events is deliberate and reported.
- The skill verdict uses score-based within-date IC only; PR-AUC and class-label scores are never used as the skill metric (WI-002 lesson).
- The shortlist for public consumption is the daily shortlist in the human stream; this file is the evidence package behind it.

