# Sprint 3 — Statistical Metadata Selection (Gate 3)

- Generated (UTC): 2026-10-23T20:21:32.216165+00:00

## USD

- Raw features: **89** | Surviving after VIF pruning: **32**
- Train cutoff (feature selection split): `2024-07-30`

### Stationarity (ADF) — features flagged for rolling Z-score

- **3** non-stationary features flagged (median p > 0.05):

`atr_pct_100`, `amihud_100`, `yangzhang_100`

### Collinearity pruning (VIF) — dropped features

| Feature | Reason | VIF |
| :--- | :--- | ---: |
| `di_spread_5` | VIF | 174.8844687022774 |
| `di_spread_10` | VIF | 162.7115238231568 |
| `vwap_zscore_10` | VIF | 8.000722433971784 |
| `obv_zscore_10` | VIF | 22.797362815195864 |
| `bb_pct_b_10` | VIF | 23.852515640471655 |
| `adx_5` | VIF | 5.688880896127812 |
| `kalman_spread_atr` | VIF | 108.64566982227001 |
| `bb_pct_b_5` | VIF | 14.625102247945996 |
| `macd_norm_hist` | VIF | 11.03543873343402 |
| `adx_10` | VIF | 7.022341418338685 |
| `bb_pct_b_20` | VIF | 19.953246722957346 |
| `range_width_f3` | VIF | 9.542537245889442 |
| `bb_pct_b_100` | VIF | 24.486189818241698 |
| `obv_zscore_50` | VIF | 51.63679218637348 |
| `range_width_f6` | VIF | 20.562231158934907 |
| `range_pos_f9` | VIF | 17.70901703668941 |
| `vwap_zscore_20` | VIF | 6.572656984153705 |
| `obv_zscore_20` | VIF | 16.851351484838606 |
| `rsi_14_slope_5` | VIF | 6.154773220423419 |
| `range_pos_f6` | VIF | 10.100966510097507 |
| `macd_norm_line` | VIF | 34.16197537365298 |
| `yangzhang_10` | VIF | 13.506259282149834 |
| `di_spread_100` | VIF | 37.088684201964384 |
| `di_spread_50` | VIF | 30.851229635383866 |
| `di_spread_20` | VIF | 11.929523514446114 |
| `range_pos_f3` | VIF | 5.665144023934391 |
| `rsi_5` | VIF | 24.880211452909535 |
| `bb_pct_b_50` | VIF | 17.588512761343356 |
| `bb_width_20` | VIF | 12.558684555092594 |
| `bb_width_100` | VIF | 10.389795595822239 |
| `atr_pct_5` | VIF | 266.4345779201407 |
| `atr_pct_10` | VIF | 263.6640694569489 |
| `range_width_f39` | VIF | 18.709559245822717 |
| `rsi_14` | VIF | 147.70070859548662 |
| `yangzhang_50` | VIF | 16.488031521316273 |
| `yangzhang_5` | VIF | 5.087471095964649 |
| `adx_50` | VIF | 7.674167134531785 |
| `bb_width_50` | VIF | 6.537727260878939 |
| `atr_pct_100` | VIF | 37.10600729458229 |
| `vwap_zscore_50` | VIF | 5.215480887038743 |
| `rsi_21` | VIF | 14.130858736395918 |
| `atr_pct_20` | VIF | 52.53037400032519 |
| `fib_dist_f102` | VIF | 37.12352407801865 |
| `atr_pct_50` | VIF | 13.351906561414685 |
| `range_width_f15` | VIF | 15.68185126326441 |
| `bb_width_10` | VIF | 10.513377007998045 |
| `range_pos_f15` | VIF | 40.28209647849269 |
| `yangzhang_20` | VIF | 6.136925393241002 |
| `range_width_f9` | VIF | 6.397940572776569 |
| `range_pos_f63` | VIF | 15.980341346811555 |
| `fib_dist_f39` | VIF | 37.109988161174996 |
| `range_pos_f102` | VIF | 10.659775270820308 |
| `fib_dist_f15` | VIF | 6.409395365615355 |
| `pct_from_high_f102` | VIF | 5.466918373604666 |
| `range_width_f63` | VIF | 10.48235657441547 |
| `range_pos_f24` | VIF | 6.172502720143721 |
| `range_width_f102` | VIF | 5.046213169500199 |

### Top features by Mutual Information (per target)

**y_15d_high**

- `range_compression_f15_102` — MI 0.0364
- `range_compression_f6_39` — MI 0.0127
- `entropy_10` — MI 0.0070
- `donchian_break_f6` — MI 0.0031
- `pct_from_low_f102` — MI 0.0027
- `range_width_f24` — MI 0.0025
- `range_width_f102` — MI 0.0025
- `range_pos_f24` — MI 0.0024
- `pct_from_high_f102` — MI 0.0023
- `range_width_f9` — MI 0.0021

**y_15d_low**

- `range_compression_f15_102` — MI 0.0352
- `range_compression_f6_39` — MI 0.0141
- `entropy_10` — MI 0.0077
- `range_width_f15` — MI 0.0034
- `range_width_f63` — MI 0.0029
- `pct_from_low_f102` — MI 0.0028
- `range_pos_f39` — MI 0.0027
- `fib_dist_f15` — MI 0.0025
- `bb_width_10` — MI 0.0025
- `range_width_f24` — MI 0.0023

**y_20d_up**

- `range_compression_f15_102` — MI 0.0575
- `range_compression_f6_39` — MI 0.0172
- `entropy_10` — MI 0.0078
- `pct_from_low_f102` — MI 0.0028
- `range_width_f102` — MI 0.0023
- `yangzhang_100` — MI 0.0023
- `donchian_break_f6` — MI 0.0019
- `yangzhang_20` — MI 0.0018
- `yangzhang_5` — MI 0.0018
- `range_pos_f15` — MI 0.0018

**y_20d_down**

- `range_compression_f15_102` — MI 0.0358
- `range_compression_f6_39` — MI 0.0115
- `entropy_10` — MI 0.0098
- `donchian_break_f15` — MI 0.0025
- `obv_zscore_100` — MI 0.0022
- `donchian_break_f6` — MI 0.0017
- `pct_from_low_f102` — MI 0.0016
- `macd_norm_line` — MI 0.0015
- `vwap_zscore_5` — MI 0.0014
- `yangzhang_100` — MI 0.0014


### Surviving whitelist (per target)

- **y_15d_high** (32 features): `bb_width_5`, `adx_20`, `adx_100`, `obv_zscore_5`, `obv_zscore_100`, `hurst_20`, `hurst_50`, `hurst_100`, `frac_diff_close`, `entropy_10`, `entropy_20`, `kama_er_5`, `kama_er_10`, `kama_er_20`, `kama_er_50`, `kama_er_100`, `vwap_zscore_5`, `vwap_zscore_100`, `amihud_5`, `amihud_10`, `amihud_20`, `amihud_50`, `amihud_100`, `yangzhang_100`, `donchian_break_f6`, `donchian_break_f15`, `range_width_f24`, `range_pos_f39`, `range_compression_f6_39`, `range_compression_f15_102`, `pct_from_low_f102`, `gap_z`

- **y_15d_low** (32 features): `bb_width_5`, `adx_20`, `adx_100`, `obv_zscore_5`, `obv_zscore_100`, `hurst_20`, `hurst_50`, `hurst_100`, `frac_diff_close`, `entropy_10`, `entropy_20`, `kama_er_5`, `kama_er_10`, `kama_er_20`, `kama_er_50`, `kama_er_100`, `vwap_zscore_5`, `vwap_zscore_100`, `amihud_5`, `amihud_10`, `amihud_20`, `amihud_50`, `amihud_100`, `yangzhang_100`, `donchian_break_f6`, `donchian_break_f15`, `range_width_f24`, `range_pos_f39`, `range_compression_f6_39`, `range_compression_f15_102`, `pct_from_low_f102`, `gap_z`

- **y_20d_up** (32 features): `bb_width_5`, `adx_20`, `adx_100`, `obv_zscore_5`, `obv_zscore_100`, `hurst_20`, `hurst_50`, `hurst_100`, `frac_diff_close`, `entropy_10`, `entropy_20`, `kama_er_5`, `kama_er_10`, `kama_er_20`, `kama_er_50`, `kama_er_100`, `vwap_zscore_5`, `vwap_zscore_100`, `amihud_5`, `amihud_10`, `amihud_20`, `amihud_50`, `amihud_100`, `yangzhang_100`, `donchian_break_f6`, `donchian_break_f15`, `range_width_f24`, `range_pos_f39`, `range_compression_f6_39`, `range_compression_f15_102`, `pct_from_low_f102`, `gap_z`

- **y_20d_down** (32 features): `bb_width_5`, `adx_20`, `adx_100`, `obv_zscore_5`, `obv_zscore_100`, `hurst_20`, `hurst_50`, `hurst_100`, `frac_diff_close`, `entropy_10`, `entropy_20`, `kama_er_5`, `kama_er_10`, `kama_er_20`, `kama_er_50`, `kama_er_100`, `vwap_zscore_5`, `vwap_zscore_100`, `amihud_5`, `amihud_10`, `amihud_20`, `amihud_50`, `amihud_100`, `yangzhang_100`, `donchian_break_f6`, `donchian_break_f15`, `range_width_f24`, `range_pos_f39`, `range_compression_f6_39`, `range_compression_f15_102`, `pct_from_low_f102`, `gap_z`

- Transformed feature matrix saved to `data/features/features_USD_metadata.parquet`

