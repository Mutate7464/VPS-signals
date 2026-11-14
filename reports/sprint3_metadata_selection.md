# Sprint 3 — Statistical Metadata Selection (Gate 3)

- Generated (UTC): 2026-10-25T00:14:07.596817+00:00

## CAD

- Raw features: **89** | Surviving after VIF pruning: **42**
- Train cutoff (feature selection split): `2024-07-30`

### Stationarity (ADF) — features flagged for rolling Z-score

- **3** non-stationary features flagged (median p > 0.05):

`adx_100`, `atr_pct_100`, `amihud_100`

### Collinearity pruning (VIF) — dropped features

| Feature | Reason | VIF |
| :--- | :--- | ---: |
| `bb_pct_b_20` | VIF | 21.68857194534212 |
| `vwap_zscore_20` | VIF | 7.224452901287651 |
| `vwap_zscore_50` | VIF | 7.409723272808069 |
| `amihud_10` | VIF | 23.96120782437535 |
| `kalman_spread_atr` | VIF | 91.42321360583476 |
| `macd_norm_hist` | VIF | 9.788584490925091 |
| `vwap_zscore_10` | VIF | 6.4988151212129335 |
| `amihud_20` | VIF | 17.27783215882691 |
| `macd_norm_line` | VIF | 39.09919051045442 |
| `adx_10` | VIF | 11.566609997771652 |
| `bb_pct_b_5` | VIF | 12.444958861284201 |
| `obv_zscore_5` | VIF | 7.992730648326746 |
| `adx_50` | VIF | 7.169037859416356 |
| `obv_zscore_50` | VIF | 37.89846279802905 |
| `amihud_50` | VIF | 17.592688660039578 |
| `bb_pct_b_100` | VIF | 21.381714736616683 |
| `obv_zscore_10` | VIF | 12.464445071094184 |
| `obv_zscore_100` | VIF | 7.814388784894825 |
| `bb_pct_b_10` | VIF | 17.283113050343992 |
| `bb_pct_b_50` | VIF | 14.604718761308522 |
| `atr_pct_50` | VIF | 742.9576478653098 |
| `atr_pct_5` | VIF | 186.97147354594568 |
| `range_pos_f3` | VIF | 7.107658789061991 |
| `bb_width_50` | VIF | 5.620477696732693 |
| `di_spread_10` | VIF | 289.6518394107456 |
| `di_spread_5` | VIF | 15.184280102110701 |
| `bb_width_20` | VIF | 5.27252883961463 |
| `atr_pct_10` | VIF | 269.9413824660212 |
| `di_spread_50` | VIF | 60.512015421627865 |
| `atr_pct_20` | VIF | 124.44064386903605 |
| `di_spread_20` | VIF | 9.60000134109343 |
| `range_pos_f6` | VIF | 11.765370388420672 |
| `atr_pct_100` | VIF | 9.481030561621736 |
| `range_pos_f9` | VIF | 10.709771471335772 |
| `range_pos_f15` | VIF | 40.099628759965256 |
| `fib_dist_f15` | VIF | 10.095799934792252 |
| `range_pos_f24` | VIF | 11.055092870731118 |
| `rsi_14` | VIF | 236.24746578269574 |
| `range_width_f15` | VIF | 5.394264827871504 |
| `rsi_5` | VIF | 9.782319958181613 |
| `range_width_f24` | VIF | 5.026047568449472 |
| `rsi_21` | VIF | 12.783277780014902 |
| `range_pos_f39` | VIF | 37.384314825539334 |
| `range_pos_f63` | VIF | 14.492741186174898 |
| `range_pos_f102` | VIF | 35.00134477486356 |
| `fib_dist_f102` | VIF | 7.220366162441899 |
| `range_width_f63` | VIF | 5.9153784479769 |

### Top features by Mutual Information (per target)

**y_15d_high**

- `range_compression_f15_102` — MI 0.0632
- `range_compression_f6_39` — MI 0.0256
- `range_width_f102` — MI 0.0123
- `fib_dist_f102` — MI 0.0118
- `pct_from_high_f102` — MI 0.0112
- `range_pos_f102` — MI 0.0104
- `pct_from_low_f102` — MI 0.0099
- `fib_dist_f39` — MI 0.0098
- `range_width_f63` — MI 0.0094
- `range_pos_f63` — MI 0.0091

**y_15d_low**

- `range_compression_f15_102` — MI 0.0649
- `range_compression_f6_39` — MI 0.0272
- `pct_from_high_f102` — MI 0.0124
- `range_width_f102` — MI 0.0120
- `range_width_f63` — MI 0.0105
- `range_width_f39` — MI 0.0097
- `range_pos_f102` — MI 0.0096
- `fib_dist_f102` — MI 0.0094
- `rsi_21` — MI 0.0089
- `range_width_f24` — MI 0.0082

**y_20d_up**

- `range_compression_f15_102` — MI 0.0906
- `range_compression_f6_39` — MI 0.0329
- `range_width_f102` — MI 0.0110
- `pct_from_high_f102` — MI 0.0106
- `range_width_f63` — MI 0.0102
- `pct_from_low_f102` — MI 0.0097
- `range_width_f39` — MI 0.0096
- `range_pos_f102` — MI 0.0089
- `fib_dist_f102` — MI 0.0088
- `range_pos_f63` — MI 0.0084

**y_20d_down**

- `range_compression_f15_102` — MI 0.0650
- `range_compression_f6_39` — MI 0.0228
- `pct_from_high_f102` — MI 0.0086
- `entropy_10` — MI 0.0078
- `range_width_f102` — MI 0.0072
- `range_width_f63` — MI 0.0066
- `fib_dist_f39` — MI 0.0060
- `pct_from_low_f102` — MI 0.0059
- `range_width_f39` — MI 0.0055
- `range_pos_f39` — MI 0.0055


### Surviving whitelist (per target)

- **y_15d_high** (35 features): `rsi_14_slope_5`, `bb_width_5`, `bb_width_10`, `bb_width_100`, `adx_100`, `di_spread_100`, `obv_zscore_20`, `hurst_50`, `frac_diff_close`, `entropy_10`, `entropy_20`, `kama_er_5`, `kama_er_10`, `kama_er_20`, `kama_er_50`, `kama_er_100`, `vwap_zscore_5`, `amihud_5`, `yangzhang_5`, `yangzhang_10`, `yangzhang_50`, `yangzhang_100`, `range_width_f3`, `range_width_f6`, `donchian_break_f6`, `range_width_f9`, `donchian_break_f15`, `range_width_f39`, `range_width_f102`, `range_compression_f6_39`, `range_compression_f15_102`, `pct_from_high_f102`, `pct_from_low_f102`, `fib_dist_f39`, `gap_z`

- **y_15d_low** (35 features): `rsi_14_slope_5`, `bb_width_5`, `bb_width_10`, `bb_width_100`, `adx_5`, `adx_20`, `di_spread_100`, `hurst_100`, `entropy_10`, `kama_er_5`, `kama_er_10`, `kama_er_20`, `kama_er_50`, `kama_er_100`, `vwap_zscore_100`, `amihud_5`, `amihud_100`, `yangzhang_5`, `yangzhang_10`, `yangzhang_20`, `yangzhang_50`, `yangzhang_100`, `range_width_f3`, `range_width_f6`, `donchian_break_f6`, `range_width_f9`, `donchian_break_f15`, `range_width_f39`, `range_width_f102`, `range_compression_f6_39`, `range_compression_f15_102`, `pct_from_high_f102`, `pct_from_low_f102`, `fib_dist_f39`, `gap_z`

- **y_20d_up** (35 features): `rsi_14_slope_5`, `bb_width_5`, `bb_width_10`, `bb_width_100`, `adx_20`, `adx_100`, `di_spread_100`, `hurst_50`, `frac_diff_close`, `entropy_10`, `entropy_20`, `kama_er_5`, `kama_er_10`, `kama_er_20`, `kama_er_50`, `kama_er_100`, `vwap_zscore_100`, `amihud_100`, `yangzhang_10`, `yangzhang_20`, `yangzhang_50`, `yangzhang_100`, `range_width_f3`, `range_width_f6`, `donchian_break_f6`, `range_width_f9`, `donchian_break_f15`, `range_width_f39`, `range_width_f102`, `range_compression_f6_39`, `range_compression_f15_102`, `pct_from_high_f102`, `pct_from_low_f102`, `fib_dist_f39`, `gap_z`

- **y_20d_down** (35 features): `rsi_14_slope_5`, `bb_width_5`, `bb_width_10`, `adx_20`, `adx_100`, `di_spread_100`, `obv_zscore_20`, `hurst_50`, `entropy_10`, `entropy_20`, `kama_er_5`, `kama_er_10`, `kama_er_20`, `kama_er_50`, `kama_er_100`, `amihud_5`, `amihud_100`, `yangzhang_5`, `yangzhang_10`, `yangzhang_20`, `yangzhang_50`, `yangzhang_100`, `range_width_f3`, `range_width_f6`, `donchian_break_f6`, `range_width_f9`, `donchian_break_f15`, `range_width_f39`, `range_width_f102`, `range_compression_f6_39`, `range_compression_f15_102`, `pct_from_high_f102`, `pct_from_low_f102`, `fib_dist_f39`, `gap_z`

- Transformed feature matrix saved to `data/features/features_CAD_metadata.parquet`

