# WI-040 — Layer-1 pickle library manifest (D-023 L1)

- Generated (UTC): 2026-11-10T02:11:48Z
- Scanned `wi035`, `wi036`, `wi038` -> **9745 fold pickles / 1580 cells** (one row per pickle)
- Rows: `manifest_id, library, pickle_path, market, learner, variant, event, window, k, h, binary, fold, cell_id, auc, ic, auc_report, z, p, stats_source`
- Layer 1 only: predictive stats, no threshold / entry filter / trading claim; attribution is permutation-based.

## 1. Coverage per library

| library | pickles | cells | markets | learners | horizons | variants |
| --- | --- | --- | --- | --- | --- | --- |
| `wi035` | 96 | 18 | CAD/USD | hist_gbm/logistic_l2/xgboost | — | 0 |
| `wi036` | 6838 | 1466 | CAD/USD | hist_gbm/logistic_l2/mlp_torch/xgboost | 5,8,13,21,34,55,89,144,233 | 8 |
| `wi038` | 2811 | 567 | CAD/USD | hist_gbm/logistic_l2/mlp_torch/xgboost | 34,55,89,144 | 8 |

## 2. Winner cell (frozen WI-036 ranking) and stats source

- `exact_full_k0.8` / `b_hold` / xgboost / h13.
- WI-035/-036/-038 persist fold models only (`data/models/*` holds `*.pkl`, no per-cell OOF store), so `auc`/`ic` are recomputed **for the winner cell alone** (`wi040_calibration.md`); `auc_report` is the value printed in the WI-036/-038 FDR table for that exact cell, hence survivors only.
- `stats_source`: 10 rows refit (winner cell, both markets), 369 rows carry only the printed AUC, 9366 rows have neither (the frozen tables list FDR survivors plus the ranking, not every cell).

| market | winner rows | fold range | pickle resolves | auc (refit) | auc_report |
| --- | --- | --- | --- | --- | --- |
| USD | 5 | 0–4 | yes | 0.7836 | 0.7836 |
| CAD | 5 | 0–4 | yes | 0.7207 | 0.7207 |

## 3. Spot-check — manifest `auc_report` vs the printed report value

| manifest_id | cell_id | manifest | printed | match |
| --- | --- | --- | --- | --- |
| `wi036:CAD_hist_gbm_exact_full_k0.8_b_hold_h13_f0` | `CAD|hist_gbm|exact_full_k0.8|b_hold|h13` | 0.6864 | 0.6864 | yes |
| `wi036:CAD_hist_gbm_exact_full_k0.8_b_hold_h13_f1` | `CAD|hist_gbm|exact_full_k0.8|b_hold|h13` | 0.6864 | 0.6864 | yes |
| `wi036:CAD_hist_gbm_exact_full_k0.8_b_hold_h13_f2` | `CAD|hist_gbm|exact_full_k0.8|b_hold|h13` | 0.6864 | 0.6864 | yes |
