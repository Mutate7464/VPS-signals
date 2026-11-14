# WI-009c Step 1 — cheap five-factor logistic probe (CAD)

- Generated (UTC): 2026-10-25T06:25:37Z
- Panel: 677,313 rows · 313 symbols · 2691 dates (2016-01-04 → 2026-09-22)
- Features: the five E5 factors only (`e5_mom_12_1`, `e5_rev_1m`, `e5_vol_20`, `e5_amihud_20`, `e5_log_dollar_vol_20`) — no 89-feature model, no robustness variant.
- E5 factors are computed from raw OHLCV by `src.factors.e5_baseline.build_e5_panel` (the WI-009b harness) and joined to `targets_CAD.parquet` on (date, symbol). Features and targets are not rebuilt.
- CV: `PurgedWalkForwardSplit(n_splits=5, embargo_td=20)`, chronological expanding folds over unique dates, keyed by *positions* (`src.factors.e5_baseline.date_positions`) — never `pd.factorize` codes (the WI-009 leak). Score-based within-date Spearman rank-IC only; class-label IC is never used. Wall clock 38.0s.

## Metric mapping (documented Build assumption)

Each binary label is scored against the aligned continuous forward move with its established direction sign (`src.xgb_trainer.TARGET_DIRECTION`); `y_20d_stay` uses the magnitude reference `-|fwd_atr_ret_20|` (stay ≈ small |move|). The same reference is used for the logistic probability and for every factor, on identical rows and dates.

| Target | continuous reference |
| :--- | :--- |
| `y_15d_high` | `-1 × fwd_atr_ret_15` |
| `y_15d_low` | `+1 × fwd_atr_ret_15` |
| `y_20d_up` | `+1 × fwd_atr_ret_20` |
| `y_20d_down` | `-1 × fwd_atr_ret_20` |
| `y_20d_stay` | `-|fwd_atr_ret_20| (stay ≈ small |move|)` |

## Verdict summary (skill bar: clause a = same-sign AND |IC| >=, clause b = |t|>2 with stable sub-window sign)

| Target | OOF logit IC | t | same sign | clause (a) | clause (b) | skill bar |
| :--- | ---: | ---: | :--- | :--- | :--- | :--- |
| `y_15d_high` | +0.0001 | +0.04 | yes | FAIL | FAIL | **NEGATIVE RESULT** |
| `y_15d_low` | +0.0304 | +6.86 | NO | FAIL | PASS | **NEGATIVE RESULT** |
| `y_20d_up` | +0.0123 | +3.15 | NO | FAIL | FAIL | **NEGATIVE RESULT** |
| `y_20d_down` | -0.0231 | -5.19 | NO | FAIL | FAIL | **NEGATIVE RESULT** |
| `y_20d_stay` | -0.0355 | -10.06 | yes | FAIL | PASS | **NEGATIVE RESULT** |

- 0/5 targets clear the unchanged skill bar
- **Step 2 gate:** no label demonstrated learnable — no 89-feature spend; limit the continuous baseline to the same five factors.

## `y_15d_high`

- Reference: `-1 × fwd_atr_ret_15` · scored rows 434,470 · scored dates 1615 · class base rate 29.44%
- OOF logistic: IC +0.0001 (t +0.04), PR-AUC +0.3296 (descriptive only — the skill metric is the score-based IC).
- Skill bar: clause (a) FAIL (same sign as best factor: True; logit |IC| +0.0001 vs `vol_20` |IC| +0.0288) · clause (b) FAIL (sub-windows same sign: False, |t|>2 in all: False) · **negative result**.

| Score | mean IC | \|IC\| | t | dates |
| :--- | ---: | ---: | ---: | ---: |
| **OOF logit (5 E5 factors)** | +0.0001 | +0.0001 | +0.04 | 1615 |
| `e5_vol_20` (factor) | +0.0288 | 0.0288 | +5.55 | 1615 |
| `e5_mom_12_1` (factor) | -0.0132 | 0.0132 | -2.69 | 1615 |
| `e5_amihud_20` (factor) | +0.0077 | 0.0077 | +2.56 | 1615 |
| `e5_rev_1m` (factor) | -0.0070 | 0.0070 | -1.77 | 1615 |
| `e5_log_dollar_vol_20` (factor) | +0.0000 | 0.0000 | +0.01 | 1615 |

Sub-window stability (purged OOF rows only; 2 disjoint contiguous blocks):

| Sub-window | dates | logit mean IC | t | sign matches full window |
| :--- | ---: | ---: | ---: | :--- |
| 1 | 808 | +0.0075 | +1.54 | True |
| 2 | 807 | -0.0073 | -1.71 | False |

## `y_15d_low`

- Reference: `+1 × fwd_atr_ret_15` · scored rows 434,470 · scored dates 1615 · class base rate 32.38%
- OOF logistic: IC +0.0304 (t +6.86), PR-AUC +0.3400 (descriptive only — the skill metric is the score-based IC).
- Skill bar: clause (a) FAIL (same sign as best factor: False; logit |IC| +0.0304 vs `vol_20` |IC| +0.0288) · clause (b) PASS (sub-windows same sign: True, |t|>2 in all: True) · **negative result**.

| Score | mean IC | \|IC\| | t | dates |
| :--- | ---: | ---: | ---: | ---: |
| **OOF logit (5 E5 factors)** | +0.0304 | +0.0304 | +6.86 | 1615 |
| `e5_vol_20` (factor) | -0.0288 | 0.0288 | -5.55 | 1615 |
| `e5_mom_12_1` (factor) | +0.0132 | 0.0132 | +2.69 | 1615 |
| `e5_amihud_20` (factor) | -0.0077 | 0.0077 | -2.56 | 1615 |
| `e5_rev_1m` (factor) | +0.0070 | 0.0070 | +1.77 | 1615 |
| `e5_log_dollar_vol_20` (factor) | -0.0000 | 0.0000 | -0.01 | 1615 |

Sub-window stability (purged OOF rows only; 2 disjoint contiguous blocks):

| Sub-window | dates | logit mean IC | t | sign matches full window |
| :--- | ---: | ---: | ---: | :--- |
| 1 | 808 | +0.0189 | +3.18 | True |
| 2 | 807 | +0.0419 | +6.39 | True |

Caveats:

- SIGN INVERTED — the model's val IC has the opposite sign to the best factor (+0.0304 vs `vol_20` -0.0288). Clause (a) is a |IC| comparison, so it is met in MAGNITUDE only: the model is anti-correlated with forward returns on this window, and a sign flip (which would make the sign positive) is not claimed here because it would be chosen on this same window.
- THIN MARGIN — |IC| exceeds the best factor by only 5.6% relative; a margin this small is not robust to a different window or seed.

## `y_20d_up`

- Reference: `+1 × fwd_atr_ret_20` · scored rows 434,470 · scored dates 1615 · class base rate 19.10%
- OOF logistic: IC +0.0123 (t +3.15), PR-AUC +0.2023 (descriptive only — the skill metric is the score-based IC).
- Skill bar: clause (a) FAIL (same sign as best factor: False; logit |IC| +0.0123 vs `vol_20` |IC| +0.0307) · clause (b) FAIL (sub-windows same sign: True, |t|>2 in all: False) · **negative result**.

| Score | mean IC | \|IC\| | t | dates |
| :--- | ---: | ---: | ---: | ---: |
| **OOF logit (5 E5 factors)** | +0.0123 | +0.0123 | +3.15 | 1615 |
| `e5_vol_20` (factor) | -0.0307 | 0.0307 | -5.86 | 1615 |
| `e5_mom_12_1` (factor) | +0.0135 | 0.0135 | +2.77 | 1615 |
| `e5_rev_1m` (factor) | +0.0098 | 0.0098 | +2.53 | 1615 |
| `e5_amihud_20` (factor) | -0.0052 | 0.0052 | -1.73 | 1615 |
| `e5_log_dollar_vol_20` (factor) | -0.0034 | 0.0034 | -1.39 | 1615 |

Sub-window stability (purged OOF rows only; 2 disjoint contiguous blocks):

| Sub-window | dates | logit mean IC | t | sign matches full window |
| :--- | ---: | ---: | ---: | :--- |
| 1 | 808 | +0.0162 | +2.58 | True |
| 2 | 807 | +0.0084 | +1.82 | True |

Caveats:

- SIGN INVERTED — the model's val IC has the opposite sign to the best factor (+0.0123 vs `vol_20` -0.0307). Clause (a) is a |IC| comparison, so it is met in MAGNITUDE only: the model is anti-correlated with forward returns on this window, and a sign flip (which would make the sign positive) is not claimed here because it would be chosen on this same window.

## `y_20d_down`

- Reference: `-1 × fwd_atr_ret_20` · scored rows 434,470 · scored dates 1615 · class base rate 10.35%
- OOF logistic: IC -0.0231 (t -5.19), PR-AUC +0.0964 (descriptive only — the skill metric is the score-based IC).
- Skill bar: clause (a) FAIL (same sign as best factor: False; logit |IC| +0.0231 vs `vol_20` |IC| +0.0307) · clause (b) FAIL (sub-windows same sign: True, |t|>2 in all: False) · **negative result**.

| Score | mean IC | \|IC\| | t | dates |
| :--- | ---: | ---: | ---: | ---: |
| **OOF logit (5 E5 factors)** | -0.0231 | +0.0231 | -5.19 | 1615 |
| `e5_vol_20` (factor) | +0.0307 | 0.0307 | +5.86 | 1615 |
| `e5_mom_12_1` (factor) | -0.0135 | 0.0135 | -2.77 | 1615 |
| `e5_rev_1m` (factor) | -0.0098 | 0.0098 | -2.53 | 1615 |
| `e5_amihud_20` (factor) | +0.0052 | 0.0052 | +1.73 | 1615 |
| `e5_log_dollar_vol_20` (factor) | +0.0034 | 0.0034 | +1.39 | 1615 |

Sub-window stability (purged OOF rows only; 2 disjoint contiguous blocks):

| Sub-window | dates | logit mean IC | t | sign matches full window |
| :--- | ---: | ---: | ---: | :--- |
| 1 | 808 | -0.0011 | -0.18 | True |
| 2 | 807 | -0.0450 | -7.45 | True |

Caveats:

- SIGN INVERTED — the model's val IC has the opposite sign to the best factor (-0.0231 vs `vol_20` +0.0307). Clause (a) is a |IC| comparison, so it is met in MAGNITUDE only: the model is anti-correlated with forward returns on this window, and a sign flip (which would make the sign positive) is not claimed here because it would be chosen on this same window.

## `y_20d_stay`

- Reference: `-|fwd_atr_ret_20| (stay ≈ small |move|)` · scored rows 434,470 · scored dates 1615 · class base rate 44.09%
- OOF logistic: IC -0.0355 (t -10.06), PR-AUC +0.5519 (descriptive only — the skill metric is the score-based IC).
- Skill bar: clause (a) FAIL (same sign as best factor: True; logit |IC| +0.0355 vs `rev_1m` |IC| +0.0669) · clause (b) PASS (sub-windows same sign: True, |t|>2 in all: True) · **negative result**.

| Score | mean IC | \|IC\| | t | dates |
| :--- | ---: | ---: | ---: | ---: |
| **OOF logit (5 E5 factors)** | -0.0355 | +0.0355 | -10.06 | 1615 |
| `e5_rev_1m` (factor) | -0.0669 | 0.0669 | -24.37 | 1615 |
| `e5_vol_20` (factor) | +0.0327 | 0.0327 | +9.25 | 1615 |
| `e5_amihud_20` (factor) | +0.0190 | 0.0190 | +8.01 | 1615 |
| `e5_log_dollar_vol_20` (factor) | -0.0153 | 0.0153 | -7.04 | 1615 |
| `e5_mom_12_1` (factor) | -0.0071 | 0.0071 | -2.01 | 1615 |

Sub-window stability (purged OOF rows only; 2 disjoint contiguous blocks):

| Sub-window | dates | logit mean IC | t | sign matches full window |
| :--- | ---: | ---: | ---: | :--- |
| 1 | 808 | -0.0285 | -5.56 | True |
| 2 | 807 | -0.0425 | -8.77 | True |

## Leakage-safe split evidence

Per fold: training dates end at `train_max_date`; validation starts at `val_min_date`; the gap in unique-date positions is the purge. `purge_ok` asserts `max_train_pos + 20 < min_val_pos`, so no training label's 20td forward window reaches the validation block.

| Target | Fold | train rows | val rows | train dates | val dates | train max | val min | gap (td) | purge ok |
| :--- | ---: | ---: | ---: | ---: | ---: | :--- | :--- | ---: | :--- |
| `y_15d_high` | 0 | 238,123 | 76,713 | 1056 | 323 | 2020-03-17 | 2020-04-16 | 20 | OK |
| `y_15d_high` | 1 | 314,776 | 79,109 | 1379 | 323 | 2021-06-29 | 2021-07-29 | 20 | OK |
| `y_15d_high` | 2 | 393,530 | 88,365 | 1702 | 323 | 2022-10-13 | 2022-11-11 | 20 | OK |
| `y_15d_high` | 3 | 481,470 | 92,040 | 2025 | 323 | 2024-01-26 | 2024-02-27 | 20 | OK |
| `y_15d_high` | 4 | 573,230 | 98,243 | 2348 | 323 | 2025-05-09 | 2025-06-10 | 20 | OK |
| `y_15d_low` | 0 | 238,123 | 76,713 | 1056 | 323 | 2020-03-17 | 2020-04-16 | 20 | OK |
| `y_15d_low` | 1 | 314,776 | 79,109 | 1379 | 323 | 2021-06-29 | 2021-07-29 | 20 | OK |
| `y_15d_low` | 2 | 393,530 | 88,365 | 1702 | 323 | 2022-10-13 | 2022-11-11 | 20 | OK |
| `y_15d_low` | 3 | 481,470 | 92,040 | 2025 | 323 | 2024-01-26 | 2024-02-27 | 20 | OK |
| `y_15d_low` | 4 | 573,230 | 98,243 | 2348 | 323 | 2025-05-09 | 2025-06-10 | 20 | OK |
| `y_20d_up` | 0 | 238,123 | 76,713 | 1056 | 323 | 2020-03-17 | 2020-04-16 | 20 | OK |
| `y_20d_up` | 1 | 314,776 | 79,109 | 1379 | 323 | 2021-06-29 | 2021-07-29 | 20 | OK |
| `y_20d_up` | 2 | 393,530 | 88,365 | 1702 | 323 | 2022-10-13 | 2022-11-11 | 20 | OK |
| `y_20d_up` | 3 | 481,470 | 92,040 | 2025 | 323 | 2024-01-26 | 2024-02-27 | 20 | OK |
| `y_20d_up` | 4 | 573,230 | 98,243 | 2348 | 323 | 2025-05-09 | 2025-06-10 | 20 | OK |
| `y_20d_down` | 0 | 238,123 | 76,713 | 1056 | 323 | 2020-03-17 | 2020-04-16 | 20 | OK |
| `y_20d_down` | 1 | 314,776 | 79,109 | 1379 | 323 | 2021-06-29 | 2021-07-29 | 20 | OK |
| `y_20d_down` | 2 | 393,530 | 88,365 | 1702 | 323 | 2022-10-13 | 2022-11-11 | 20 | OK |
| `y_20d_down` | 3 | 481,470 | 92,040 | 2025 | 323 | 2024-01-26 | 2024-02-27 | 20 | OK |
| `y_20d_down` | 4 | 573,230 | 98,243 | 2348 | 323 | 2025-05-09 | 2025-06-10 | 20 | OK |
| `y_20d_stay` | 0 | 238,123 | 76,713 | 1056 | 323 | 2020-03-17 | 2020-04-16 | 20 | OK |
| `y_20d_stay` | 1 | 314,776 | 79,109 | 1379 | 323 | 2021-06-29 | 2021-07-29 | 20 | OK |
| `y_20d_stay` | 2 | 393,530 | 88,365 | 1702 | 323 | 2022-10-13 | 2022-11-11 | 20 | OK |
| `y_20d_stay` | 3 | 481,470 | 92,040 | 2025 | 323 | 2024-01-26 | 2024-02-27 | 20 | OK |
| `y_20d_stay` | 4 | 573,230 | 98,243 | 2348 | 323 | 2025-05-09 | 2025-06-10 | 20 | OK |

## Reading notes

- The probe bounds the *existing labels*: a negative result here is a statement about these binary labels and this five-factor probe, not about the continuous route.
- The E5 baseline moves with the window (WI-009b); the per-label factor table above is the bar for the rows actually scored, not a constant.
- No class-label score is used anywhere; PR-AUC is descriptive colour only.

