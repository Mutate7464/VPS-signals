# WI-011 Step 3 — indicator association and empirical subset (CAD)

- Generated (UTC): 2026-10-25T21:43:26Z
- Indicator panel: 701,599 rows · 89 indicators · 2691 dates (2016-01-04 → 2026-09-22)
- Condition-state table aligned positionally: 701,599 of 701,599 panel rows carry a state (0 unmatched — symbols/dates outside the condition panel, reported not imputed).
- Association is **contemporaneous and within-date only**: per-date cross-sectional z-score (`z = (x - mean_date)/std_date`), then state-fired mean minus state-defined-but-not-fired mean, with a t-stat across dates. **No forward return enters this analysis** — no predictive claim follows.

States used (all trailing, from `src/wi011/conditions.py`): `ch52_high`, `ch52_low`, `trend_up`, `trend_down`

## EXTREME_ASSOCIATION (local peak/bottom states: ch52_high, ch52_low)

Δz = mean z when the state fires − mean z when it is defined and does not fire; (t over dates, number of dated cross-sections used). Sorted by the larger |Δz| of the two states.

| Indicator | ch52_high: Δz (t, dates) | ch52_low: Δz (t, dates) |
| :--- | ---:  | ---: |
| `pct_from_high_f102` | +1.066 (+394.99, 2677) | -1.432 (-202.66, 2654) |
| `fib_dist_f102` | +1.360 (+304.86, 2677) | -1.405 (-252.96, 2654) |
| `range_pos_f102` | +1.324 (+262.93, 2677) | -1.385 (-234.88, 2654) |
| `bb_pct_b_100` | +1.228 (+235.05, 2677) | -1.229 (-222.96, 2654) |
| `range_pos_f63` | +1.217 (+230.94, 2677) | -1.200 (-209.02, 2654) |
| `rsi_21` | +1.103 (+251.48, 2677) | -1.039 (-194.34, 2654) |
| `macd_norm_line` | +1.081 (+264.82, 2677) | -1.034 (-187.80, 2654) |
| `range_pos_f39` | +1.075 (+196.51, 2677) | -1.019 (-174.18, 2654) |
| `di_spread_100` | +1.027 (+164.77, 2677) | -1.064 (-64.44, 2654) |
| `fib_dist_f39` | +1.052 (+210.59, 2677) | -1.003 (-175.11, 2654) |
| `bb_pct_b_50` | +1.046 (+180.51, 2677) | -0.965 (-162.28, 2654) |
| `di_spread_50` | +1.041 (+212.34, 2677) | -1.018 (-79.30, 2654) |
| `rsi_14` | +1.003 (+216.29, 2677) | -0.923 (-161.04, 2654) |
| `atr_pct_100` | -0.623 (-163.47, 2677) | +0.982 (+102.16, 2654) |
| `range_pos_f24` | +0.912 (+164.36, 2677) | -0.843 (-134.02, 2654) |
| `di_spread_20` | +0.902 (+207.19, 2677) | -0.825 (-110.87, 2654) |
| `kalman_spread_atr` | +0.900 (+187.82, 2677) | -0.818 (-136.26, 2654) |
| `atr_pct_50` | -0.608 (-148.40, 2677) | +0.868 (+101.76, 2654) |
| `range_width_f102` | -0.375 (-86.14, 2677) | +0.861 (+97.61, 2654) |
| `kama_er_100` | +0.849 (+108.71, 2677) | +0.364 (+22.81, 2654) |
| `range_width_f63` | -0.366 (-84.04, 2677) | +0.764 (+91.95, 2654) |
| `bb_pct_b_20` | +0.756 (+132.38, 2677) | -0.663 (-101.06, 2654) |
| `range_pos_f15` | +0.756 (+133.82, 2677) | -0.693 (-105.38, 2654) |
| `di_spread_10` | +0.745 (+160.02, 2677) | -0.662 (-103.19, 2654) |
| `fib_dist_f15` | +0.743 (+137.82, 2677) | -0.684 (-105.55, 2654) |
| `atr_pct_20` | -0.541 (-122.68, 2677) | +0.718 (+89.73, 2654) |
| `rsi_5` | +0.690 (+128.60, 2677) | -0.620 (-96.14, 2654) |
| `range_width_f39` | -0.363 (-76.09, 2677) | +0.670 (+82.60, 2654) |
| `frac_diff_close` | +0.507 (+142.66, 2677) | -0.657 (-101.88, 2654) |
| `atr_pct_10` | -0.485 (-105.24, 2677) | +0.637 (+79.23, 2654) |
| `kama_er_50` | +0.604 (+74.90, 2677) | +0.235 (+14.54, 2654) |
| `range_pos_f9` | +0.603 (+107.26, 2677) | -0.561 (-83.93, 2654) |
| `vwap_zscore_100` | +0.600 (+105.23, 2677) | -0.319 (-42.65, 2654) |
| `range_width_f24` | -0.362 (-74.48, 2677) | +0.595 (+74.22, 2654) |
| `di_spread_5` | +0.579 (+113.48, 2677) | -0.511 (-79.48, 2654) |
| `atr_pct_5` | -0.433 (-91.91, 2677) | +0.577 (+73.32, 2654) |
| `bb_pct_b_10` | +0.548 (+94.67, 2677) | -0.485 (-72.12, 2654) |
| `range_width_f15` | -0.355 (-71.61, 2677) | +0.541 (+67.24, 2654) |
| `adx_50` | +0.538 (+79.74, 2677) | +0.073 (+9.24, 2654) |
| `bb_width_100` | -0.080 (-17.91, 2677) | +0.534 (+60.93, 2654) |
| `bb_width_50` | -0.149 (-29.81, 2677) | +0.512 (+65.03, 2654) |
| `range_pos_f6` | +0.502 (+89.39, 2677) | -0.472 (-69.95, 2654) |
| `pct_from_low_f102` | +0.499 (+81.90, 2677) | -0.480 (-78.69, 2654) |
| `range_width_f9` | -0.347 (-70.87, 2677) | +0.498 (+63.58, 2654) |
| `yangzhang_20` | -0.379 (-81.02, 2677) | +0.483 (+66.79, 2654) |
| `yangzhang_50` | -0.385 (-62.06, 2677) | +0.474 (+65.43, 2654) |
| `range_width_f6` | -0.338 (-70.67, 2677) | +0.474 (+62.50, 2654) |
| `yangzhang_10` | -0.362 (-79.60, 2677) | +0.473 (+64.66, 2654) |
| `adx_20` | +0.467 (+71.18, 2677) | +0.101 (+8.54, 2654) |
| `yangzhang_5` | -0.342 (-76.89, 2677) | +0.453 (+63.10, 2654) |
| `bb_width_20` | -0.233 (-43.01, 2677) | +0.452 (+56.74, 2654) |
| `range_width_f3` | -0.322 (-69.79, 2677) | +0.448 (+60.60, 2654) |
| `yangzhang_100` | -0.364 (-49.52, 2677) | +0.443 (+60.60, 2654) |
| `bb_width_10` | -0.267 (-51.83, 2677) | +0.416 (+54.20, 2654) |
| `adx_100` | +0.407 (+64.72, 2677) | -0.042 (+4.41, 2654) |
| `bb_pct_b_5` | +0.384 (+67.23, 2677) | -0.345 (-51.20, 2654) |
| `bb_width_5` | -0.265 (-55.89, 2677) | +0.382 (+53.04, 2654) |
| `range_pos_f3` | +0.365 (+67.05, 2677) | -0.347 (-52.82, 2654) |
| `vwap_zscore_50` | +0.340 (+59.74, 2677) | -0.172 (-20.86, 2654) |
| `adx_10` | +0.313 (+44.68, 2677) | +0.059 (+1.92, 2654) |
| `donchian_break_f15` | +0.302 (+60.71, 2677) | -0.225 (-65.35, 2654) |
| `range_compression_f15_102` | -0.059 (-4.61, 2677) | -0.292 (-35.75, 2654) |
| `kama_er_20` | +0.273 (+31.60, 2677) | +0.069 (+1.54, 2654) |
| `donchian_break_f6` | +0.262 (+54.04, 2677) | -0.218 (-52.90, 2654) |
| `macd_norm_hist` | +0.230 (+39.37, 2677) | -0.120 (-13.48, 2654) |
| `adx_5` | +0.157 (+22.09, 2677) | +0.029 (+0.07, 2654) |
| `range_compression_f6_39` | -0.041 (-3.09, 2677) | -0.154 (-19.02, 2654) |
| `amihud_5` | -0.109 (-57.68, 2677) | +0.151 (+30.17, 2654) |
| `amihud_10` | -0.104 (-54.64, 2677) | +0.142 (+29.77, 2654) |
| `amihud_20` | -0.087 (-45.10, 2677) | +0.124 (+26.22, 2654) |
| `rsi_14_slope_5` | +0.124 (+22.21, 2677) | -0.090 (-12.22, 2654) |
| `entropy_20` | +0.047 (+14.37, 2677) | -0.120 (-28.01, 2654) |
| `vwap_zscore_20` | +0.118 (+20.71, 2677) | -0.069 (-7.60, 2654) |
| `kama_er_10` | +0.113 (+13.95, 2677) | +0.019 (-0.62, 2654) |
| `entropy_10` | +0.047 (+16.90, 2677) | -0.105 (-24.58, 2654) |
| `obv_zscore_100` | +0.104 (+21.99, 2677) | -0.078 (-10.93, 2654) |
| `obv_zscore_50` | +0.076 (+16.11, 2677) | -0.059 (-8.65, 2654) |
| `amihud_50` | -0.048 (-26.01, 2677) | +0.071 (+16.08, 2654) |
| `obv_zscore_20` | +0.047 (+9.77, 2677) | -0.041 (-6.22, 2654) |
| `vwap_zscore_10` | +0.044 (+8.02, 2677) | -0.032 (-4.01, 2654) |
| `kama_er_5` | +0.043 (+6.17, 2677) | -0.003 (-2.30, 2654) |
| `amihud_100` | -0.037 (-20.91, 2677) | +0.030 (+7.00, 2654) |
| `hurst_50` | +0.035 (+12.10, 2677) | -0.036 (-11.32, 2654) |
| `obv_zscore_10` | +0.034 (+7.15, 2677) | -0.035 (-5.09, 2654) |
| `hurst_100` | +0.035 (+17.46, 2677) | -0.012 (-4.63, 2654) |
| `obv_zscore_5` | +0.030 (+6.13, 2677) | -0.034 (-4.94, 2654) |
| `vwap_zscore_5` | +0.010 (+2.23, 2677) | -0.014 (-1.34, 2654) |
| `hurst_20` | +0.014 (+2.88, 2677) | +0.004 (-1.62, 2654) |
| `gap_z` | +0.013 (+2.29, 2677) | -0.002 (-0.54, 2654) |

## TREND_ASSOCIATION (directional states: trend_up, trend_down)

| Indicator | trend_up: Δz (t, dates) | trend_down: Δz (t, dates) |
| :--- | ---:  | ---: |
| `macd_norm_line` | +1.278 (+374.23, 2673) | -1.264 (-417.16, 2689) |
| `range_pos_f24` | +1.209 (+294.95, 2673) | -1.255 (-287.74, 2689) |
| `range_pos_f39` | +1.154 (+291.70, 2673) | -1.205 (-309.41, 2689) |
| `bb_pct_b_50` | +1.171 (+303.77, 2673) | -1.199 (-336.46, 2689) |
| `rsi_14` | +1.196 (+342.11, 2673) | -1.187 (-362.73, 2689) |
| `fib_dist_f39` | +1.146 (+316.88, 2673) | -1.182 (-317.62, 2689) |
| `rsi_21` | +1.162 (+310.87, 2673) | -1.148 (-339.42, 2689) |
| `bb_pct_b_20` | +1.101 (+232.04, 2673) | -1.147 (-261.20, 2689) |
| `kalman_spread_atr` | +1.128 (+308.37, 2673) | -1.116 (-331.84, 2689) |
| `di_spread_20` | +1.104 (+292.48, 2673) | -1.090 (-318.29, 2689) |
| `range_pos_f63` | +1.031 (+256.40, 2673) | -1.070 (-269.51, 2689) |
| `di_spread_10` | +1.063 (+289.07, 2673) | -1.067 (-311.23, 2689) |
| `range_pos_f15` | +1.002 (+215.11, 2673) | -1.027 (-221.14, 2689) |
| `bb_pct_b_100` | +0.990 (+241.39, 2673) | -0.991 (-240.19, 2689) |
| `fib_dist_f15` | +0.966 (+219.52, 2673) | -0.989 (-222.47, 2689) |
| `vwap_zscore_50` | +0.985 (+241.92, 2673) | -0.956 (-218.59, 2689) |
| `vwap_zscore_100` | +0.976 (+225.18, 2673) | -0.936 (-220.21, 2689) |
| `fib_dist_f102` | +0.938 (+232.80, 2673) | -0.953 (-225.55, 2689) |
| `range_pos_f102` | +0.884 (+207.79, 2673) | -0.916 (-204.48, 2689) |
| `di_spread_50` | +0.883 (+189.15, 2673) | -0.863 (-192.00, 2689) |
| `macd_norm_hist` | +0.846 (+182.76, 2673) | -0.845 (-205.78, 2689) |
| `rsi_5` | +0.820 (+180.76, 2673) | -0.825 (-190.53, 2689) |
| `di_spread_5` | +0.764 (+170.51, 2673) | -0.778 (-185.37, 2689) |
| `kama_er_20` | +0.747 (+90.09, 2673) | +0.384 (+36.10, 2689) |
| `pct_from_high_f102` | +0.658 (+154.69, 2673) | -0.707 (-121.44, 2689) |
| `di_spread_100` | +0.660 (+124.28, 2673) | -0.643 (-122.08, 2689) |
| `adx_10` | +0.623 (+89.07, 2673) | +0.191 (+20.17, 2689) |
| `range_pos_f9` | +0.610 (+118.41, 2673) | -0.612 (-124.70, 2689) |
| `bb_pct_b_10` | +0.567 (+105.94, 2673) | -0.576 (-114.81, 2689) |
| `adx_5` | +0.472 (+67.45, 2673) | +0.198 (+22.13, 2689) |
| `kama_er_50` | +0.432 (+54.73, 2673) | -0.097 (-11.48, 2689) |
| `pct_from_low_f102` | +0.400 (+67.55, 2673) | -0.378 (-77.18, 2689) |
| `range_pos_f6` | +0.399 (+75.39, 2673) | -0.396 (-77.93, 2689) |
| `adx_20` | +0.396 (+61.32, 2673) | -0.005 (-1.09, 2689) |
| `vwap_zscore_10` | -0.363 (-65.57, 2673) | +0.379 (+71.55, 2689) |
| `donchian_break_f15` | +0.344 (+72.99, 2673) | -0.330 (-124.10, 2689) |
| `kama_er_100` | +0.342 (+49.69, 2673) | -0.204 (-26.96, 2689) |
| `range_width_f24` | +0.014 (-0.56, 2673) | +0.337 (+50.08, 2689) |
| `vwap_zscore_20` | +0.324 (+58.33, 2673) | -0.316 (-61.96, 2689) |
| `range_width_f39` | -0.077 (-15.40, 2673) | +0.296 (+45.79, 2689) |
| `atr_pct_50` | -0.295 (-52.80, 2673) | +0.287 (+46.44, 2689) |
| `bb_width_20` | +0.279 (+39.12, 2673) | +0.289 (+40.19, 2689) |
| `range_width_f15` | +0.031 (+2.36, 2673) | +0.287 (+43.77, 2689) |
| `atr_pct_100` | -0.280 (-54.64, 2673) | +0.270 (+46.02, 2689) |
| `frac_diff_close` | +0.278 (+59.03, 2673) | -0.255 (-49.61, 2689) |
| `kama_er_10` | +0.269 (+31.13, 2673) | +0.091 (+7.01, 2689) |
| `range_compression_f15_102` | +0.266 (+47.75, 2673) | +0.118 (+16.42, 2689) |
| `range_width_f63` | -0.140 (-27.75, 2673) | +0.265 (+43.10, 2689) |
| `atr_pct_20` | -0.259 (-43.71, 2673) | +0.257 (+42.18, 2689) |
| `range_compression_f6_39` | -0.171 (-32.39, 2673) | -0.250 (-45.65, 2689) |
| `range_width_f102` | -0.176 (-36.58, 2673) | +0.249 (+41.16, 2689) |
| `bb_pct_b_5` | +0.244 (+44.24, 2673) | -0.242 (-46.19, 2689) |
| `vwap_zscore_5` | -0.226 (-42.41, 2673) | +0.221 (+42.76, 2689) |
| `donchian_break_f6` | +0.192 (+44.20, 2673) | -0.222 (-65.98, 2689) |
| `range_pos_f3` | +0.204 (+38.14, 2673) | -0.201 (-40.18, 2689) |
| `atr_pct_10` | -0.198 (-31.59, 2673) | +0.202 (+34.08, 2689) |
| `obv_zscore_10` | -0.167 (-34.82, 2673) | +0.163 (+34.22, 2689) |
| `adx_50` | +0.147 (+30.29, 2673) | -0.077 (-13.44, 2689) |
| `atr_pct_5` | -0.140 (-22.05, 2673) | +0.143 (+24.85, 2689) |
| `obv_zscore_20` | -0.143 (-30.22, 2673) | +0.141 (+29.28, 2689) |
| `range_width_f9` | -0.065 (-11.35, 2673) | +0.130 (+21.96, 2689) |
| `yangzhang_50` | -0.122 (-18.61, 2673) | +0.090 (+17.80, 2689) |
| `yangzhang_100` | -0.115 (-18.86, 2673) | +0.085 (+17.51, 2689) |
| `yangzhang_20` | -0.115 (-16.34, 2673) | +0.095 (+19.02, 2689) |
| `gap_z` | -0.097 (-19.17, 2673) | +0.105 (+21.13, 2689) |
| `range_width_f3` | -0.103 (-18.64, 2673) | +0.064 (+13.09, 2689) |
| `yangzhang_10` | -0.093 (-13.38, 2673) | +0.100 (+19.45, 2689) |
| `range_width_f6` | -0.096 (-16.54, 2673) | +0.079 (+14.84, 2689) |
| `bb_width_50` | +0.092 (+14.27, 2673) | +0.095 (+16.35, 2689) |
| `yangzhang_5` | -0.095 (-15.60, 2673) | +0.085 (+16.66, 2689) |
| `bb_width_5` | -0.093 (-17.75, 2673) | +0.014 (+3.57, 2689) |
| `obv_zscore_5` | -0.087 (-18.06, 2673) | +0.085 (+17.87, 2689) |
| `amihud_5` | -0.073 (-23.90, 2673) | +0.023 (+8.76, 2689) |
| `bb_width_10` | +0.007 (-0.15, 2673) | +0.071 (+10.78, 2689) |
| `amihud_10` | -0.070 (-23.76, 2673) | +0.024 (+8.94, 2689) |
| `adx_100` | +0.070 (+18.38, 2673) | -0.058 (-10.38, 2689) |
| `kama_er_5` | +0.024 (+4.50, 2673) | -0.069 (-13.22, 2689) |
| `amihud_20` | -0.056 (-19.10, 2673) | +0.019 (+7.23, 2689) |
| `obv_zscore_100` | +0.046 (+9.58, 2673) | -0.047 (-10.22, 2689) |
| `hurst_100` | +0.046 (+21.22, 2673) | +0.035 (+13.57, 2689) |
| `hurst_50` | +0.045 (+12.15, 2673) | +0.016 (+0.17, 2689) |
| `entropy_20` | +0.044 (+8.44, 2673) | -0.019 (-12.61, 2689) |
| `bb_width_100` | +0.000 (+0.52, 2673) | +0.040 (+9.09, 2689) |
| `entropy_10` | +0.040 (+13.04, 2673) | -0.006 (-6.57, 2689) |
| `amihud_50` | -0.032 (-9.48, 2673) | +0.004 (+2.54, 2689) |
| `hurst_20` | +0.011 (+2.12, 2673) | -0.024 (-7.86, 2689) |
| `rsi_14_slope_5` | -0.024 (-5.76, 2673) | +0.022 (+2.21, 2689) |
| `amihud_100` | -0.024 (-8.52, 2673) | -0.002 (+1.55, 2689) |
| `obv_zscore_50` | +0.001 (-0.38, 2673) | -0.003 (-0.78, 2689) |

## REDUNDANCY_CLUSTERS

Pooled within-date correlation of the z-scores over a deterministic stride-5 subsample (140,320 rows); connected components at |corr| >= 0.90. 6 redundant cluster(s) with >1 member:

- **cluster 1** (22): `rsi_5`, `rsi_14`, `rsi_21`, `bb_pct_b_10`, `bb_pct_b_20`, `bb_pct_b_50`, `bb_pct_b_100`, `macd_norm_line`, `di_spread_5`, `di_spread_10`, `di_spread_20`, `kalman_spread_atr`, `range_pos_f6`, `range_pos_f9` … (+8 more)
- **cluster 2** (8): `atr_pct_5`, `atr_pct_10`, `atr_pct_20`, `atr_pct_50`, `atr_pct_100`, `yangzhang_5`, `yangzhang_10`, `yangzhang_20`
- **cluster 3** (4): `obv_zscore_10`, `obv_zscore_20`, `obv_zscore_50`, `obv_zscore_100`
- **cluster 4** (3): `bb_width_10`, `range_width_f6`, `range_width_f9`
- **cluster 5** (2): `di_spread_50`, `di_spread_100`
- **cluster 6** (2): `yangzhang_50`, `yangzhang_100`

## SELECTED_INDICATORS

Pre-declared selection rule: drop indicators already represented by a Step 2 primitive (`kama_er_20`, `atr_pct_20`, `amihud_20`), require |t| >= 2.0 in at least one state, collapse redundancy clusters to their strongest-associated member (|Δz|), keep at most 6. The rule was fixed before the numbers were seen.

SELECTED_INDICATORS: pct_from_high_f102, fib_dist_f102, di_spread_100, vwap_zscore_50, atr_pct_100, vwap_zscore_100

| Selected indicator | Best state | Δz | t | Cluster size | Why it is not already covered |
| :--- | :--- | ---: | ---: | ---: | :--- |
| `pct_from_high_f102` | `ch52_low` | -1.432 | -202.66 | 1 | distinct from the E5 primitives and from the retained representatives |
| `fib_dist_f102` | `ch52_low` | -1.405 | -252.96 | 22 | distinct from the E5 primitives and from the retained representatives |
| `di_spread_100` | `ch52_low` | -1.064 | -64.44 | 2 | distinct from the E5 primitives and from the retained representatives |
| `vwap_zscore_50` | `trend_up` | +0.985 | +241.92 | 1 | distinct from the E5 primitives and from the retained representatives |
| `atr_pct_100` | `ch52_low` | +0.982 | +102.16 | 8 | distinct from the E5 primitives and from the retained representatives |
| `vwap_zscore_100` | `trend_up` | +0.976 | +225.18 | 1 | distinct from the E5 primitives and from the retained representatives |

### Distinctness vs the Step 2 vocabulary (disclosure, not a re-selection)

Some indicators are *near-mechanical restatements* of the state they are associated with (a channel-distance or volatility measure vs a channel/volatility state). The selection rule was fixed before these numbers were seen, so nothing is re-selected here — but the overlap is reported for the human gate, and Step 4 additionally reports the joint firing rate between each `ind_*` condition and the base state it shadows.

| Selected indicator | max abs corr with a Step 2-vocabulary indicator | Analogue |
| :--- | ---: | :--- |
| `pct_from_high_f102` | 0.784 | `range_pos_f102` (position in a 102d high/low channel (Step 2 uses 252d)) |
| `fib_dist_f102` | 0.980 | `range_pos_f102` (position in a 102d high/low channel (Step 2 uses 252d)) |
| `di_spread_100` | 0.625 | `range_pos_f102` (position in a 102d high/low channel (Step 2 uses 252d)) |
| `vwap_zscore_50` | 0.265 | `range_pos_f102` (position in a 102d high/low channel (Step 2 uses 252d)) |
| `atr_pct_100` | 0.853 | `atr_pct_20` (ATR%/close (Step 2 uses window 20)) |
| `vwap_zscore_100` | 0.565 | `range_pos_f102` (position in a 102d high/low channel (Step 2 uses 252d)) |

Step 2 hook: these names are written to `reports/wi011_selected_indicators.json`; re-running `scripts/wi011_conditions.py` adds `ind_<name>_low` (own-history percentile <= 0.20) and `ind_<name>_high` (>= 0.80) to the declared vocabulary — Step 3(a)'s mandated update of the Step 2 condition configuration.

## Duplicates of Step 2 primitives (excluded from selection)

| Indicator | Already represented by |
| :--- | :--- |
| `kama_er_20` | er_20 — Step 2 uses the identical KAMA efficiency ratio (window 20) |
| `atr_pct_20` | atr_pct_20 — identical ATR%/close primitive (window 20) |
| `amihud_20` | amihud_20 — identical E5 Amihud illiquidity (window 20) |

## Notes / limits

- Association is descriptive co-movement in the same row; it is **not** evidence of predictive power, and this step deliberately never touches `fwd_ret_*`.
- Missing/undefined indicator values are ignored inside the per-date moments (pairwise finite rows); counts in the tables are the dated cross-sections actually used.
- The whole 89-indicator panel is analysed here but is **not** retained downstream: only the selected subset enters the condition vocabulary, alongside the E5 primitives.
