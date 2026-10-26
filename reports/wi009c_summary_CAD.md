# WI-009c — final evaluation and human gate package (CAD)

- Generated (UTC): 2026-10-26T16:51:48Z from the fixed run outputs (no model was re-fit, no fold re-run).
- **Run identity**: `reports/wi009c_regression_CAD.json` · generated 2026-10-26T16:51:47.315727+00:00 · smoke=False · market CAD.
- **Model**: `StandardScaler` + `Ridge(alpha=100.0)` on the 5 E5 factors (`e5_mom_12_1`, `e5_rev_1m`, `e5_vol_20`, `e5_amihud_20`, `e5_log_dollar_vol_20`), target `fwd_atr_ret_20`, ATR/price column `atr_pct_20`.
- **CV**: `PurgedWalkForwardSplit(n_splits=5, embargo_td=20)` over unique dates keyed by positions; per-fold split-calibration block of the last 20% of the training dates (purged 20td from the fit block). 5 of 5 folds viable.
- **Panel**: 677,313 rows · 313 symbols · 2691 dates (2016-01-04 → 2026-09-22); **434,470 out-of-fold rows** scored across folds [0, 1, 2, 3, 4] (1615 dates).
- **Event units** (ADR D-010): up = `fwd_atr_ret_20 >= +2.0` (2×ATR, dollar); down = `fwd_atr_ret_20 <= -2.0`; stay = `|fwd_atr_ret_20| <= 0.05 / atr_pct_20` (row-specific ±5%, relative). The events **overlap** (mean up∩stay 0.0299, down∩stay 0.0262); each probability is integrated independently from the residual ECDF and the overlap is reported, never forced into a partition.

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
- Recorded probabilities (mean predicted) vs realized rate on the same 434,470 OOF rows:

| Event | mean predicted | realized rate | bias | Brier |
| :--- | ---: | ---: | ---: | ---: |
| P(up) | 0.2840 | 0.3050 | -0.0209 | 0.2138 |
| P(down) | 0.2132 | 0.1848 | +0.0285 | 0.1565 |
| P(stay) | 0.4634 | 0.4674 | -0.0039 | 0.2247 |
| P(stay) exclusive | 0.4073 | 0.4083 | -0.0010 | 0.2348 |

- Mean `P(up) + P(down) + P(stay)` = 0.9607 (may exceed 1 — the events overlap by design); all probabilities finite and within [0, 1] on every scored row.
- Shortlist: 20 names as of **2026-09-22** (of 313 candidates); ordering by the declared composite verified (True), symbol tie-break verified (True), max |composite - (P(up)-P(down))| = 1.11e-16.

| rank | symbol | `P(up)` | `P(down)` | `P(up)-P(down)` | `P(stay)` |
| ---: | :--- | ---: | ---: | ---: | ---: |
| 1 | `IE` | 0.3428 | 0.1725 | +0.1703 | 0.2082 |
| 2 | `FISV` | 0.3426 | 0.1727 | +0.1699 | 0.3537 |
| 3 | `STC` | 0.3411 | 0.1739 | +0.1672 | 0.4022 |
| 4 | `PYPL` | 0.3370 | 0.1767 | +0.1602 | 0.4063 |
| 5 | `PRU` | 0.3357 | 0.1778 | +0.1579 | 0.2524 |
| 6 | `ET` | 0.3343 | 0.1788 | +0.1555 | 0.3206 |
| 7 | `F` | 0.3321 | 0.1805 | +0.1516 | 0.4185 |
| 8 | `BKNG` | 0.3319 | 0.1806 | +0.1513 | 0.3594 |
| 9 | `BX` | 0.3305 | 0.1815 | +0.1490 | 0.4385 |
| 10 | `EPRX` | 0.3301 | 0.1819 | +0.1482 | 0.2838 |

### Skill result — same-sign and |IC| against the five E5 factors

Score-based within-date Spearman rank-IC of the continuous forecast vs `fwd_atr_ret_20`, on exactly the same out-of-fold rows and dates as every factor.

| Score | mean IC | \|IC\| | t | dates |
| :--- | ---: | ---: | ---: | ---: |
| **continuous baseline (5 E5 factors)** | +0.0001 | +0.0001 | +0.03 | 1615 |
| `e5_vol_20` (factor) | -0.0307 | 0.0307 | -5.86 | 1615 |
| `e5_mom_12_1` (factor) | +0.0135 | 0.0135 | +2.77 | 1615 |
| `e5_rev_1m` (factor) | +0.0098 | 0.0098 | +2.53 | 1615 |
| `e5_amihud_20` (factor) | -0.0052 | 0.0052 | -1.73 | 1615 |
| `e5_log_dollar_vol_20` (factor) | -0.0034 | 0.0034 | -1.39 | 1615 |

- Clause (a) — same sign as the best factor AND |IC| ≥ its |IC|: **FAIL** (baseline |IC| +0.0001 vs `e5_vol_20` |IC| +0.0307; same-sign **False**).
- Clause (b) — |t| > 2 with the same sign in ≥ 2 disjoint sub-windows: **FAIL**.
- **SKILL BAR: FAIL** — the five-factor continuous forecast does not beat the best single E5 factor on this window.
- Calibration is a **marginal** distribution from held-out residuals pooled across folds: it is not a guarantee of conditional calibration per row, symbol or regime, and the ECDF tails are limited by the calibration sample size.

## 3. Robustness options and the fold-safe stacked-input candidate (Steps 3–4)

- Fold-safe contrastive stacked input (`models/contrastive_ranker_wi009b.pt`, `score_numpy`): **not attempted** — not attempted in the production chain.
- Step-4 robustness record missing: gates were not evaluated in this checkout.

## 4. Route verdict as a whole

| Question | Verdict | Basis |
| :--- | :--- | :--- |
| Are the existing binary labels learnable from the five E5 factors? | **NO — 0/5 clear the unchanged skill bar** | Step 1 probe, purged OOF, score-based within-date IC |
| Does the five-factor continuous 20td forecast beat the best single factor? | **NO — skill bar FAIL** (IC +0.0001 vs |IC| +0.0307, same-sign False) | Step 2, 434,470 OOF rows, 5/5 folds |
| Are the distribution-derived probabilities usable? | **Numerically yes, skilfully unproven** — finite, in [0, 1], marginal calibration reported (mean P(stay) 0.4634 vs realized 0.4674) | Step 2 calibration diagnostics |
| May the fold-safe contrastive stacked input be used? | **NO (NOT RUN, gated)** | Step 1(d) gate + fold-safety not establishable (Step 3) |
| Do any robustness options qualify? | **NO (NOT RUN, gated)** | Step 4 evidence gates |
| Is the route usable for trading? | **No — human gate decision required** | this report |

**The continuous route is not demonstrated to have skill on this CAD window.** The probabilities have the right units, are finite and bounded, and their marginal calibration is reported — but the forecast is statistically indistinguishable from (and slightly weaker than) the best single E5 factor, and the binary labels are not demonstrated learnable. Nothing here is a claim of skill.

## 5. Negative results vs execution/test failures

- **Negative results** (content, not failures): 0/5 labels clear the skill bar; the continuous baseline fails the skill bar; the contrastive stacked input is omitted (gated); all three robustness options are NOT RUN (gated). Each is recorded with its reason and evidence, and none was tuned away, suppressed or substituted by a different model.
- **Execution/test failures**: none. This report is written only after every internal consistency check below passes; a failed check aborts the run with a non-zero exit instead of printing a verdict.

## 6. Reproducibility check (recomputed from the saved per-row outputs)

- Source: `data/wi009c_oof_CAD.parquet` — 434,470 OOF rows re-reduced; nothing re-fit.
- Recorded (run JSON) vs recomputed (parquet) masses agree within 2e-05 absolute; every probability is finite and inside [0, 1]; the shortlist ordering matches the declared composite.

- `mean_p_up`: recorded 0.284027 · recomputed 0.284027
- `mean_p_down`: recorded 0.213246 · recomputed 0.213246
- `mean_p_stay`: recorded 0.463438 · recomputed 0.463438
- `mean_p_stay_exclusive`: recorded 0.407276 · recomputed 0.407276
- `realized_rate_up`: recorded 0.304958 · recomputed 0.304958
- `realized_rate_down`: recorded 0.184756 · recomputed 0.184756
- `realized_rate_stay`: recorded 0.467381 · recomputed 0.467381
- `mean_overlap_up_stay`: recorded 0.029914 · recomputed 0.029914
- `mean_overlap_down_stay`: recorded 0.026248 · recomputed 0.026248
- `mean_sum_up_down_stay`: recorded 0.960711 · recomputed 0.960711

Re-run this package with:

```bash
uv run python scripts/evaluate_wi009c.py --market CAD
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

