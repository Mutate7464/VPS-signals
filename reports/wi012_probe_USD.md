# WI-009c Step 1 — cheap five-factor logistic probe (USD)

- Generated (UTC): 2026-10-26T06:37:20Z
- Panel: 1,210,402 rows · 508 symbols · 2696 dates (2016-01-04 → 2026-09-23)
- Features: the five E5 factors only (`e5_mom_12_1`, `e5_rev_1m`, `e5_vol_20`, `e5_amihud_20`, `e5_log_dollar_vol_20`) — no 89-feature model, no robustness variant.
- E5 factors are computed from raw OHLCV by `src.factors.e5_baseline.build_e5_panel` (the WI-009b harness) and joined to `targets_USD.parquet` on (date, symbol). Features and targets are not rebuilt.
- CV: `PurgedWalkForwardSplit(n_splits=5, embargo_td=20)`, chronological expanding folds over unique dates, keyed by *positions* (`src.factors.e5_baseline.date_positions`) — never `pd.factorize` codes (the WI-009 leak). Score-based within-date Spearman rank-IC only; class-label IC is never used. Wall clock 47.1s.

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
| `y_15d_high` | -0.0105 | -3.05 | yes | FAIL | FAIL | **NEGATIVE RESULT** |
| `y_15d_low` | -0.0048 | -1.39 | NO | FAIL | FAIL | **NEGATIVE RESULT** |
| `y_20d_up` | -0.0130 | -3.59 | NO | FAIL | FAIL | **NEGATIVE RESULT** |
| `y_20d_down` | +0.0002 | +0.06 | NO | FAIL | FAIL | **NEGATIVE RESULT** |
| `y_20d_stay` | -0.0541 | -20.28 | yes | FAIL | PASS | **NEGATIVE RESULT** |

- 0/5 targets clear the unchanged skill bar
- **Step 2 gate:** no label demonstrated learnable — no 89-feature spend; limit the continuous baseline to the same five factors.

## `y_15d_high`

- Reference: `-1 × fwd_atr_ret_15` · scored rows 768,917 · scored dates 1618 · class base rate 30.89%
- OOF logistic: IC -0.0105 (t -3.05), PR-AUC +0.3315 (descriptive only — the skill metric is the score-based IC).
- Skill bar: clause (a) FAIL (same sign as best factor: True; logit |IC| +0.0105 vs `mom_12_1` |IC| +0.0131) · clause (b) FAIL (sub-windows same sign: True, |t|>2 in all: False) · **negative result**.

| Score | mean IC | \|IC\| | t | dates |
| :--- | ---: | ---: | ---: | ---: |
| **OOF logit (5 E5 factors)** | -0.0105 | +0.0105 | -3.05 | 1618 |
| `e5_mom_12_1` (factor) | -0.0131 | 0.0131 | -2.88 | 1618 |
| `e5_amihud_20` (factor) | -0.0124 | 0.0124 | -4.72 | 1618 |
| `e5_log_dollar_vol_20` (factor) | +0.0119 | 0.0119 | +4.59 | 1618 |
| `e5_rev_1m` (factor) | -0.0040 | 0.0040 | -1.12 | 1618 |
| `e5_vol_20` (factor) | -0.0007 | 0.0007 | -0.18 | 1618 |

Sub-window stability (purged OOF rows only; 2 disjoint contiguous blocks):

| Sub-window | dates | logit mean IC | t | sign matches full window |
| :--- | ---: | ---: | ---: | :--- |
| 1 | 809 | -0.0053 | -1.04 | True |
| 2 | 809 | -0.0157 | -3.40 | True |

## `y_15d_low`

- Reference: `+1 × fwd_atr_ret_15` · scored rows 768,917 · scored dates 1618 · class base rate 33.61%
- OOF logistic: IC -0.0048 (t -1.39), PR-AUC +0.3451 (descriptive only — the skill metric is the score-based IC).
- Skill bar: clause (a) FAIL (same sign as best factor: False; logit |IC| +0.0048 vs `mom_12_1` |IC| +0.0131) · clause (b) FAIL (sub-windows same sign: False, |t|>2 in all: False) · **negative result**.

| Score | mean IC | \|IC\| | t | dates |
| :--- | ---: | ---: | ---: | ---: |
| **OOF logit (5 E5 factors)** | -0.0048 | +0.0048 | -1.39 | 1618 |
| `e5_mom_12_1` (factor) | +0.0131 | 0.0131 | +2.88 | 1618 |
| `e5_amihud_20` (factor) | +0.0124 | 0.0124 | +4.72 | 1618 |
| `e5_log_dollar_vol_20` (factor) | -0.0119 | 0.0119 | -4.59 | 1618 |
| `e5_rev_1m` (factor) | +0.0040 | 0.0040 | +1.12 | 1618 |
| `e5_vol_20` (factor) | +0.0007 | 0.0007 | +0.18 | 1618 |

Sub-window stability (purged OOF rows only; 2 disjoint contiguous blocks):

| Sub-window | dates | logit mean IC | t | sign matches full window |
| :--- | ---: | ---: | ---: | :--- |
| 1 | 809 | +0.0043 | +0.83 | False |
| 2 | 809 | -0.0139 | -3.00 | True |

Caveats:

- SIGN INVERTED — the model's val IC has the opposite sign to the best factor (-0.0048 vs `mom_12_1` +0.0131). Clause (a) is a |IC| comparison, so it is met in MAGNITUDE only: the model is anti-correlated with forward returns on this window, and a sign flip (which would make the sign positive) is not claimed here because it would be chosen on this same window.

## `y_20d_up`

- Reference: `+1 × fwd_atr_ret_20` · scored rows 768,917 · scored dates 1618 · class base rate 18.99%
- OOF logistic: IC -0.0130 (t -3.59), PR-AUC +0.1857 (descriptive only — the skill metric is the score-based IC).
- Skill bar: clause (a) FAIL (same sign as best factor: False; logit |IC| +0.0130 vs `amihud_20` |IC| +0.0154) · clause (b) FAIL (sub-windows same sign: False, |t|>2 in all: False) · **negative result**.

| Score | mean IC | \|IC\| | t | dates |
| :--- | ---: | ---: | ---: | ---: |
| **OOF logit (5 E5 factors)** | -0.0130 | +0.0130 | -3.59 | 1618 |
| `e5_amihud_20` (factor) | +0.0154 | 0.0154 | +5.91 | 1618 |
| `e5_log_dollar_vol_20` (factor) | -0.0145 | 0.0145 | -5.63 | 1618 |
| `e5_mom_12_1` (factor) | +0.0121 | 0.0121 | +2.70 | 1618 |
| `e5_rev_1m` (factor) | +0.0026 | 0.0026 | +0.76 | 1618 |
| `e5_vol_20` (factor) | +0.0015 | 0.0015 | +0.37 | 1618 |

Sub-window stability (purged OOF rows only; 2 disjoint contiguous blocks):

| Sub-window | dates | logit mean IC | t | sign matches full window |
| :--- | ---: | ---: | ---: | :--- |
| 1 | 809 | +0.0094 | +1.73 | False |
| 2 | 809 | -0.0355 | -7.53 | True |

Caveats:

- SIGN INVERTED — the model's val IC has the opposite sign to the best factor (-0.0130 vs `amihud_20` +0.0154). Clause (a) is a |IC| comparison, so it is met in MAGNITUDE only: the model is anti-correlated with forward returns on this window, and a sign flip (which would make the sign positive) is not claimed here because it would be chosen on this same window.

## `y_20d_down`

- Reference: `-1 × fwd_atr_ret_20` · scored rows 768,917 · scored dates 1618 · class base rate 11.67%
- OOF logistic: IC +0.0002 (t +0.06), PR-AUC +0.1215 (descriptive only — the skill metric is the score-based IC).
- Skill bar: clause (a) FAIL (same sign as best factor: False; logit |IC| +0.0002 vs `amihud_20` |IC| +0.0154) · clause (b) FAIL (sub-windows same sign: False, |t|>2 in all: False) · **negative result**.

| Score | mean IC | \|IC\| | t | dates |
| :--- | ---: | ---: | ---: | ---: |
| **OOF logit (5 E5 factors)** | +0.0002 | +0.0002 | +0.06 | 1618 |
| `e5_amihud_20` (factor) | -0.0154 | 0.0154 | -5.91 | 1618 |
| `e5_log_dollar_vol_20` (factor) | +0.0145 | 0.0145 | +5.63 | 1618 |
| `e5_mom_12_1` (factor) | -0.0121 | 0.0121 | -2.70 | 1618 |
| `e5_rev_1m` (factor) | -0.0026 | 0.0026 | -0.76 | 1618 |
| `e5_vol_20` (factor) | -0.0015 | 0.0015 | -0.37 | 1618 |

Sub-window stability (purged OOF rows only; 2 disjoint contiguous blocks):

| Sub-window | dates | logit mean IC | t | sign matches full window |
| :--- | ---: | ---: | ---: | :--- |
| 1 | 809 | -0.0001 | -0.03 | False |
| 2 | 809 | +0.0006 | +0.11 | True |

Caveats:

- SIGN INVERTED — the model's val IC has the opposite sign to the best factor (+0.0002 vs `amihud_20` -0.0154). Clause (a) is a |IC| comparison, so it is met in MAGNITUDE only: the model is anti-correlated with forward returns on this window, and a sign flip (which would make the sign positive) is not claimed here because it would be chosen on this same window.

## `y_20d_stay`

- Reference: `-|fwd_atr_ret_20| (stay ≈ small |move|)` · scored rows 768,917 · scored dates 1618 · class base rate 41.28%
- OOF logistic: IC -0.0541 (t -20.28), PR-AUC +0.5021 (descriptive only — the skill metric is the score-based IC).
- Skill bar: clause (a) FAIL (same sign as best factor: True; logit |IC| +0.0541 vs `rev_1m` |IC| +0.0568) · clause (b) PASS (sub-windows same sign: True, |t|>2 in all: True) · **negative result**.

| Score | mean IC | \|IC\| | t | dates |
| :--- | ---: | ---: | ---: | ---: |
| **OOF logit (5 E5 factors)** | -0.0541 | +0.0541 | -20.28 | 1618 |
| `e5_rev_1m` (factor) | -0.0568 | 0.0568 | -22.70 | 1618 |
| `e5_vol_20` (factor) | +0.0484 | 0.0484 | +17.90 | 1618 |
| `e5_log_dollar_vol_20` (factor) | +0.0098 | 0.0098 | +5.31 | 1618 |
| `e5_mom_12_1` (factor) | -0.0046 | 0.0046 | -1.46 | 1618 |
| `e5_amihud_20` (factor) | +0.0008 | 0.0008 | +0.44 | 1618 |

Sub-window stability (purged OOF rows only; 2 disjoint contiguous blocks):

| Sub-window | dates | logit mean IC | t | sign matches full window |
| :--- | ---: | ---: | ---: | :--- |
| 1 | 809 | -0.0582 | -14.11 | True |
| 2 | 809 | -0.0501 | -14.79 | True |

## Leakage-safe split evidence

Per fold: training dates end at `train_max_date`; validation starts at `val_min_date`; the gap in unique-date positions is the purge. `purge_ok` asserts `max_train_pos + 20 < min_val_pos`, so no training label's 20td forward window reaches the validation block.

| Target | Fold | train rows | val rows | train dates | val dates | train max | val min | gap (td) | purge ok |
| :--- | ---: | ---: | ---: | ---: | ---: | :--- | :--- | ---: | :--- |
| `y_15d_high` | 0 | 432,693 | 144,087 | 1058 | 323 | 2020-03-17 | 2020-04-16 | 20 | OK |
| `y_15d_high` | 1 | 576,572 | 150,134 | 1381 | 324 | 2021-06-28 | 2021-07-28 | 20 | OK |
| `y_15d_high` | 2 | 726,186 | 154,885 | 1705 | 323 | 2022-10-10 | 2022-11-08 | 20 | OK |
| `y_15d_high` | 3 | 880,951 | 157,549 | 2028 | 324 | 2024-01-24 | 2024-02-23 | 20 | OK |
| `y_15d_high` | 4 | 1,038,260 | 162,262 | 2352 | 324 | 2025-05-09 | 2025-06-10 | 20 | OK |
| `y_15d_low` | 0 | 432,693 | 144,087 | 1058 | 323 | 2020-03-17 | 2020-04-16 | 20 | OK |
| `y_15d_low` | 1 | 576,572 | 150,134 | 1381 | 324 | 2021-06-28 | 2021-07-28 | 20 | OK |
| `y_15d_low` | 2 | 726,186 | 154,885 | 1705 | 323 | 2022-10-10 | 2022-11-08 | 20 | OK |
| `y_15d_low` | 3 | 880,951 | 157,549 | 2028 | 324 | 2024-01-24 | 2024-02-23 | 20 | OK |
| `y_15d_low` | 4 | 1,038,260 | 162,262 | 2352 | 324 | 2025-05-09 | 2025-06-10 | 20 | OK |
| `y_20d_up` | 0 | 432,693 | 144,087 | 1058 | 323 | 2020-03-17 | 2020-04-16 | 20 | OK |
| `y_20d_up` | 1 | 576,572 | 150,134 | 1381 | 324 | 2021-06-28 | 2021-07-28 | 20 | OK |
| `y_20d_up` | 2 | 726,186 | 154,885 | 1705 | 323 | 2022-10-10 | 2022-11-08 | 20 | OK |
| `y_20d_up` | 3 | 880,951 | 157,549 | 2028 | 324 | 2024-01-24 | 2024-02-23 | 20 | OK |
| `y_20d_up` | 4 | 1,038,260 | 162,262 | 2352 | 324 | 2025-05-09 | 2025-06-10 | 20 | OK |
| `y_20d_down` | 0 | 432,693 | 144,087 | 1058 | 323 | 2020-03-17 | 2020-04-16 | 20 | OK |
| `y_20d_down` | 1 | 576,572 | 150,134 | 1381 | 324 | 2021-06-28 | 2021-07-28 | 20 | OK |
| `y_20d_down` | 2 | 726,186 | 154,885 | 1705 | 323 | 2022-10-10 | 2022-11-08 | 20 | OK |
| `y_20d_down` | 3 | 880,951 | 157,549 | 2028 | 324 | 2024-01-24 | 2024-02-23 | 20 | OK |
| `y_20d_down` | 4 | 1,038,260 | 162,262 | 2352 | 324 | 2025-05-09 | 2025-06-10 | 20 | OK |
| `y_20d_stay` | 0 | 432,693 | 144,087 | 1058 | 323 | 2020-03-17 | 2020-04-16 | 20 | OK |
| `y_20d_stay` | 1 | 576,572 | 150,134 | 1381 | 324 | 2021-06-28 | 2021-07-28 | 20 | OK |
| `y_20d_stay` | 2 | 726,186 | 154,885 | 1705 | 323 | 2022-10-10 | 2022-11-08 | 20 | OK |
| `y_20d_stay` | 3 | 880,951 | 157,549 | 2028 | 324 | 2024-01-24 | 2024-02-23 | 20 | OK |
| `y_20d_stay` | 4 | 1,038,260 | 162,262 | 2352 | 324 | 2025-05-09 | 2025-06-10 | 20 | OK |

## Reading notes

- The probe bounds the *existing labels*: a negative result here is a statement about these binary labels and this five-factor probe, not about the continuous route.
- The E5 baseline moves with the window (WI-009b); the per-label factor table above is the bar for the rows actually scored, not a constant.
- No class-label score is used anywhere; PR-AUC is descriptive colour only.

