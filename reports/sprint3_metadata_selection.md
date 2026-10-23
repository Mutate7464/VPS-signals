# Sprint 3 — Statistical Metadata Selection (Gate 3)

- Generated (UTC): 2026-10-23T19:47:26.890842+00:00

## USD

- Raw features: **89** | Surviving after VIF pruning: **32**
- Train cutoff (feature selection split): `2024-07-30`

### Stationarity (ADF) — features flagged for rolling Z-score

- **13** non-stationary features flagged (median p > 0.05):

`adx_50`, `adx_100`, `di_spread_100`, `atr_pct_20`, `atr_pct_50`, `atr_pct_100`, `hurst_100`, `amihud_50`, `amihud_100`, `yangzhang_50`, `yangzhang_100`, `range_width_f102`, `pct_from_low_f102`

### Collinearity pruning (VIF) — dropped features

| Feature | Reason | VIF |
| :--- | :--- | ---: |
| `vwap_zscore_20` | VIF | 8.32769258861082 |
| `vwap_zscore_100` | VIF | 5.927713583580401 |
| `kalman_spread_atr` | VIF | 117.98648980461395 |
| `di_spread_5` | VIF | 158.13088232996517 |
| `bb_pct_b_5` | VIF | 14.73947358256495 |
| `atr_pct_10` | VIF | 1959.2040354871833 |
| `obv_zscore_5` | VIF | 9.07347663422001 |
| `bb_pct_b_10` | VIF | 23.230591442376333 |
| `di_spread_10` | VIF | 141.55635477346596 |
| `bb_pct_b_100` | VIF | 22.384551416170204 |
| `adx_10` | VIF | 14.398081722118677 |
| `di_spread_100` | VIF | 32.648624557795 |
| `vwap_zscore_50` | VIF | 7.69518750385718 |
| `obv_zscore_10` | VIF | 15.163927820687618 |
| `di_spread_50` | VIF | 25.25514059276264 |
| `obv_zscore_20` | VIF | 16.87972665537684 |
| `bb_pct_b_50` | VIF | 16.62990054455237 |
| `bb_pct_b_20` | VIF | 17.676013452661742 |
| `yangzhang_20` | VIF | 18.15281959602657 |
| `range_pos_f6` | VIF | 15.657658456420322 |
| `yangzhang_10` | VIF | 13.702526484005178 |
| `bb_width_20` | VIF | 12.80464942798581 |
| `adx_50` | VIF | 7.755081982997211 |
| `macd_norm_line` | VIF | 43.249697479581016 |
| `bb_width_10` | VIF | 14.232006592214388 |
| `yangzhang_5` | VIF | 9.956764643115521 |
| `vwap_zscore_10` | VIF | 6.1666643847858555 |
| `range_pos_f3` | VIF | 6.30216856377062 |
| `atr_pct_5` | VIF | 53.08575607880792 |
| `di_spread_20` | VIF | 11.234602479286728 |
| `obv_zscore_100` | VIF | 29.98627406556098 |
| `macd_norm_hist` | VIF | 7.139483712187612 |
| `bb_width_50` | VIF | 11.708674001102057 |
| `atr_pct_50` | VIF | 192.10487229983084 |
| `range_width_f9` | VIF | 12.610007847716778 |
| `bb_width_100` | VIF | 12.765717144431923 |
| `range_width_f6` | VIF | 12.3912310297273 |
| `fib_dist_f15` | VIF | 38.43663035978387 |
| `atr_pct_20` | VIF | 31.712004789569832 |
| `atr_pct_100` | VIF | 6.420502968031077 |
| `range_width_f3` | VIF | 5.156470522164952 |
| `range_pos_f15` | VIF | 14.355490605883285 |
| `yangzhang_50` | VIF | 13.04540243931014 |
| `range_width_f15` | VIF | 12.0446651455876 |
| `rsi_21` | VIF | 213.09720758126056 |
| `range_pos_f24` | VIF | 10.540110729749836 |
| `range_width_f24` | VIF | 8.863106485243167 |
| `range_pos_f9` | VIF | 8.754251007574466 |
| `rsi_5` | VIF | 15.451369877733985 |
| `yangzhang_100` | VIF | 7.44066190095681 |
| `rsi_14` | VIF | 9.039927289510462 |
| `range_width_f39` | VIF | 8.469340923111478 |
| `fib_dist_f39` | VIF | 36.36822452478788 |
| `range_pos_f63` | VIF | 14.417175731914936 |
| `range_pos_f102` | VIF | 37.29999569559515 |
| `fib_dist_f102` | VIF | 8.725086237293716 |
| `range_width_f102` | VIF | 10.268561897434989 |

### Top features by Mutual Information (per target)

**y_15d_high**

- `range_compression_f15_102` — MI 0.0665
- `range_compression_f6_39` — MI 0.0274
- `entropy_10` — MI 0.0083
- `pct_from_low_f102` — MI 0.0039
- `range_width_f63` — MI 0.0034
- `pct_from_high_f102` — MI 0.0027
- `range_width_f39` — MI 0.0026
- `range_pos_f24` — MI 0.0025
- `range_width_f102` — MI 0.0025
- `rsi_14` — MI 0.0021

**y_15d_low**

- `range_compression_f15_102` — MI 0.0688
- `range_compression_f6_39` — MI 0.0271
- `entropy_10` — MI 0.0064
- `range_width_f102` — MI 0.0040
- `pct_from_high_f102` — MI 0.0036
- `rsi_14` — MI 0.0033
- `donchian_break_f6` — MI 0.0031
- `rsi_5` — MI 0.0031
- `range_pos_f39` — MI 0.0030
- `range_width_f63` — MI 0.0028

**y_20d_up**

- `range_compression_f15_102` — MI 0.1055
- `range_compression_f6_39` — MI 0.0377
- `entropy_10` — MI 0.0095
- `pct_from_low_f102` — MI 0.0050
- `range_pos_f63` — MI 0.0042
- `pct_from_high_f102` — MI 0.0041
- `yangzhang_100` — MI 0.0039
- `fib_dist_f102` — MI 0.0039
- `range_pos_f102` — MI 0.0039
- `range_width_f63` — MI 0.0038

**y_20d_down**

- `range_compression_f15_102` — MI 0.0766
- `range_compression_f6_39` — MI 0.0270
- `entropy_10` — MI 0.0101
- `donchian_break_f6` — MI 0.0035
- `pct_from_low_f102` — MI 0.0032
- `pct_from_high_f102` — MI 0.0032
- `range_pos_f39` — MI 0.0028
- `fib_dist_f39` — MI 0.0025
- `range_pos_f63` — MI 0.0024
- `yangzhang_100` — MI 0.0022


### Surviving whitelist (per target)

- **y_15d_high** (32 features): `rsi_14_slope_5`, `bb_width_5`, `adx_5`, `adx_20`, `adx_100`, `obv_zscore_50`, `hurst_20`, `hurst_50`, `hurst_100`, `frac_diff_close`, `entropy_10`, `entropy_20`, `kama_er_5`, `kama_er_10`, `kama_er_20`, `kama_er_50`, `kama_er_100`, `vwap_zscore_5`, `amihud_5`, `amihud_10`, `amihud_20`, `amihud_50`, `amihud_100`, `donchian_break_f6`, `donchian_break_f15`, `range_pos_f39`, `range_width_f63`, `range_compression_f6_39`, `range_compression_f15_102`, `pct_from_high_f102`, `pct_from_low_f102`, `gap_z`

- **y_15d_low** (32 features): `rsi_14_slope_5`, `bb_width_5`, `adx_5`, `adx_20`, `adx_100`, `obv_zscore_50`, `hurst_20`, `hurst_50`, `hurst_100`, `frac_diff_close`, `entropy_10`, `entropy_20`, `kama_er_5`, `kama_er_10`, `kama_er_20`, `kama_er_50`, `kama_er_100`, `vwap_zscore_5`, `amihud_5`, `amihud_10`, `amihud_20`, `amihud_50`, `amihud_100`, `donchian_break_f6`, `donchian_break_f15`, `range_pos_f39`, `range_width_f63`, `range_compression_f6_39`, `range_compression_f15_102`, `pct_from_high_f102`, `pct_from_low_f102`, `gap_z`

- **y_20d_up** (27 features): `rsi_14_slope_5`, `bb_width_5`, `adx_20`, `adx_100`, `obv_zscore_50`, `hurst_20`, `hurst_100`, `frac_diff_close`, `entropy_10`, `entropy_20`, `kama_er_5`, `kama_er_10`, `kama_er_20`, `kama_er_50`, `kama_er_100`, `vwap_zscore_5`, `amihud_20`, `amihud_50`, `amihud_100`, `donchian_break_f6`, `donchian_break_f15`, `range_pos_f39`, `range_width_f63`, `range_compression_f6_39`, `range_compression_f15_102`, `pct_from_high_f102`, `pct_from_low_f102`

- **y_20d_down** (32 features): `rsi_14_slope_5`, `bb_width_5`, `adx_5`, `adx_20`, `adx_100`, `obv_zscore_50`, `hurst_20`, `hurst_50`, `hurst_100`, `frac_diff_close`, `entropy_10`, `entropy_20`, `kama_er_5`, `kama_er_10`, `kama_er_20`, `kama_er_50`, `kama_er_100`, `vwap_zscore_5`, `amihud_5`, `amihud_10`, `amihud_20`, `amihud_50`, `amihud_100`, `donchian_break_f6`, `donchian_break_f15`, `range_pos_f39`, `range_width_f63`, `range_compression_f6_39`, `range_compression_f15_102`, `pct_from_high_f102`, `pct_from_low_f102`, `gap_z`

- Transformed feature matrix saved to `data/features/features_USD_metadata.parquet`

