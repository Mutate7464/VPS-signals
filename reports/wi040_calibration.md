# WI-040 — winner-cell OOF calibration + permutation attribution (D-023 L1)

- Generated (UTC): 2026-11-10T02:11:48Z
- Cell `exact_full_k0.8` / `b_hold` / xgboost / h13 (cross-market WI-036 winner); 5-fold `PurgedWalkForwardSplit`, embargo `max(20, h)`, OOF probabilities re-fit through `binary_grid.cell_cv`
- Layer 1 predictive stats only: no threshold, no entry rule, no return claim.

## USD — calibration

- OOF rows 75202; positive rate (no-skill probability) 0.0039; per-fold AUC 0.6973, 0.8941, 0.9199, 0.8553, 0.6214
- Pooled OOF AUC **0.7836** (rank-IC +0.0620); WI-036 printed AUC for the same cell 0.7836
- Brier **0.0026** vs no-skill Brier 0.0039 (skill +0.327); ECE 0.0009
- Honest read: calibration is usable: Brier skill +0.327, ECE 0.0009 — reported as-is; predictive only, no threshold or trading claim follows.

| bin | n | mean predicted | observed rate | gap |
| --- | --- | --- | --- | --- |
| 0 | 15041 | 0.0001 | 0.0017 | -0.0016 |
| 1 | 8850 | 0.0007 | 0.0023 | -0.0015 |
| 2 | 6190 | 0.0008 | 0.0011 | -0.0003 |
| 3 | 13696 | 0.0010 | 0.0013 | -0.0004 |
| 4 | 1344 | 0.0010 | 0.0022 | -0.0012 |
| 5 | 13118 | 0.0014 | 0.0014 | -0.0000 |
| 6 | 2199 | 0.0015 | 0.0036 | -0.0021 |
| 7 | 7609 | 0.0021 | 0.0029 | -0.0008 |
| 8 | 7155 | 0.0232 | 0.0245 | -0.0012 |

## USD — top-20 OOF permutation importance (3 seed(s) × 5 folds)

| rank | feature | mean AUC drop | sd |
| --- | --- | --- | --- |
| 1 | `cs_entropy_102` | 0.0292 | 0.0016 |
| 2 | `entropy_24` | 0.0130 | 0.0035 |
| 3 | `atr_pct_3` | 0.0094 | 0.0019 |
| 4 | `hurst_15` | 0.0072 | 0.0038 |
| 5 | `kama_er_15` | 0.0065 | 0.0070 |
| 6 | `hurst_39` | 0.0053 | 0.0011 |
| 7 | `adx_144` | 0.0050 | 0.0060 |
| 8 | `month` | 0.0017 | 0.0010 |
| 9 | `di_spread_233` | 0.0008 | 0.0021 |
| 10 | `adx_21` | 0.0006 | 0.0014 |
| 11 | `entropy_9` | 0.0005 | 0.0004 |
| 12 | `adx_3` | 0.0002 | 0.0006 |
| 13 | `dow` | 0.0001 | 0.0006 |
| 14 | `state_is_bottom` | 0.0001 | 0.0000 |
| 15 | `sec_Capital Markets` | 0.0000 | 0.0000 |
| 16 | `sec_Consumer Cyclical` | 0.0000 | 0.0000 |
| 17 | `sec_Retail - Cyclical` | 0.0000 | 0.0000 |
| 18 | `sec_Software` | 0.0000 | 0.0000 |
| 19 | `sec_Oil & Gas` | 0.0000 | 0.0000 |
| 20 | `sec_Hardware` | 0.0000 | 0.0000 |

## CAD — calibration

- OOF rows 41296; positive rate (no-skill probability) 0.0048; per-fold AUC 0.8344, 0.7339, 0.8433, 0.7026, 0.5818
- Pooled OOF AUC **0.7207** (rank-IC +0.0529); WI-036 printed AUC for the same cell 0.7207
- Brier **0.0044** vs no-skill Brier 0.0048 (skill +0.084); ECE 0.0013
- Honest read: calibration is modest: Brier skill +0.084, ECE 0.0013 — reported as-is; predictive only, no threshold or trading claim follows.

| bin | n | mean predicted | observed rate | gap |
| --- | --- | --- | --- | --- |
| 0 | 6014 | 0.0001 | 0.0012 | -0.0010 |
| 1 | 2246 | 0.0006 | 0.0045 | -0.0038 |
| 2 | 5646 | 0.0010 | 0.0023 | -0.0013 |
| 3 | 2613 | 0.0011 | 0.0031 | -0.0019 |
| 4 | 4129 | 0.0014 | 0.0039 | -0.0025 |
| 5 | 4130 | 0.0018 | 0.0029 | -0.0011 |
| 6 | 5139 | 0.0026 | 0.0029 | -0.0003 |
| 7 | 3782 | 0.0029 | 0.0026 | +0.0003 |
| 8 | 3467 | 0.0036 | 0.0046 | -0.0010 |
| 9 | 4130 | 0.0203 | 0.0220 | -0.0017 |

## CAD — top-20 OOF permutation importance (3 seed(s) × 5 folds)

| rank | feature | mean AUC drop | sd |
| --- | --- | --- | --- |
| 1 | `atr_pct_3` | 0.0469 | 0.0039 |
| 2 | `di_spread_3` | 0.0163 | 0.0023 |
| 3 | `range_compression_8_55` | 0.0106 | 0.0026 |
| 4 | `entropy_39` | 0.0059 | 0.0034 |
| 5 | `hurst_39` | 0.0030 | 0.0057 |
| 6 | `adx_21` | 0.0029 | 0.0075 |
| 7 | `kama_er_15` | 0.0017 | 0.0069 |
| 8 | `swing_depth_atr` | 0.0002 | 0.0019 |
| 9 | `cs_di_spread_144` | 0.0001 | 0.0047 |
| 10 | `donchian_break_233` | 0.0000 | 0.0000 |
| 11 | `cs_hurst_9` | 0.0000 | 0.0000 |
| 12 | `k` | 0.0000 | 0.0000 |
| 13 | `sec_Consumer Defensive` | 0.0000 | 0.0000 |
| 14 | `hurst_9` | 0.0000 | 0.0000 |
| 15 | `sec_Asset Management` | 0.0000 | 0.0000 |
| 16 | `sec_Metals & Mining` | 0.0000 | 0.0000 |
| 17 | `sec_Industrials` | 0.0000 | 0.0000 |
| 18 | `sec_Energy` | 0.0000 | 0.0000 |
| 19 | `sec_Oil & Gas` | 0.0000 | 0.0000 |
| 20 | `sec_REITs` | 0.0000 | 0.0000 |

