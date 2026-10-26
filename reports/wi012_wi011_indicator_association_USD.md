# WI-011 Step 3 — indicator association and empirical subset (CAD)

- Generated (UTC): 2026-10-26T06:44:25Z
- Indicator panel: 1,240,275 rows · 89 indicators · 2696 dates (2016-01-04 → 2026-09-23)
- Condition-state table aligned positionally: 1,240,275 of 1,240,275 panel rows carry a state (0 unmatched — symbols/dates outside the condition panel, reported not imputed).
- Association is **contemporaneous and within-date only**: per-date cross-sectional z-score (`z = (x - mean_date)/std_date`), then state-fired mean minus state-defined-but-not-fired mean, with a t-stat across dates. **No forward return enters this analysis** — no predictive claim follows.

States used (all trailing, from `src/wi011/conditions.py`): `ch52_high`, `ch52_low`, `trend_up`, `trend_down`

## EXTREME_ASSOCIATION (local peak/bottom states: ch52_high, ch52_low)

Δz = mean z when the state fires − mean z when it is defined and does not fire; (t over dates, number of dated cross-sections used). Sorted by the larger |Δz| of the two states.

| Indicator | ch52_high: Δz (t, dates) | ch52_low: Δz (t, dates) |
| :--- | ---:  | ---: |
| `pct_from_high_f102` | +1.064 (+425.17, 2687) | -1.434 (-220.67, 2667) |
| `fib_dist_f102` | +1.333 (+274.62, 2687) | -1.389 (-315.24, 2667) |
| `range_pos_f102` | +1.305 (+237.18, 2687) | -1.382 (-279.72, 2667) |
| `di_spread_100` | +1.279 (+343.23, 2687) | -1.347 (-404.13, 2667) |
| `bb_pct_b_100` | +1.233 (+222.76, 2687) | -1.247 (-284.30, 2667) |
| `di_spread_50` | +1.202 (+299.53, 2687) | -1.231 (-332.76, 2667) |
| `range_pos_f63` | +1.195 (+201.45, 2687) | -1.188 (-223.87, 2667) |
| `rsi_21` | +1.092 (+216.32, 2687) | -1.084 (-265.96, 2667) |
| `macd_norm_line` | +1.072 (+232.85, 2687) | -1.080 (-250.30, 2667) |
| `range_pos_f39` | +1.048 (+164.61, 2687) | -1.005 (-191.39, 2667) |
| `bb_pct_b_50` | +1.035 (+158.44, 2687) | -0.974 (-194.45, 2667) |
| `fib_dist_f39` | +1.023 (+180.42, 2687) | -0.988 (-201.01, 2667) |
| `rsi_14` | +0.986 (+184.55, 2687) | -0.955 (-210.89, 2667) |
| `di_spread_20` | +0.979 (+205.90, 2687) | -0.952 (-216.21, 2667) |
| `kalman_spread_atr` | +0.891 (+161.35, 2687) | -0.852 (-176.55, 2667) |
| `range_pos_f24` | +0.882 (+134.90, 2687) | -0.829 (-153.60, 2667) |
| `atr_pct_100` | -0.573 (-257.95, 2687) | +0.830 (+112.41, 2667) |
| `kama_er_100` | +0.822 (+122.03, 2687) | +0.459 (+31.49, 2667) |
| `range_width_f102` | -0.286 (-83.18, 2687) | +0.808 (+110.31, 2667) |
| `di_spread_10` | +0.787 (+146.74, 2687) | -0.740 (-148.80, 2667) |
| `atr_pct_50` | -0.534 (-212.26, 2687) | +0.740 (+105.40, 2667) |
| `bb_pct_b_20` | +0.733 (+110.93, 2687) | -0.662 (-119.28, 2667) |
| `range_pos_f15` | +0.724 (+110.33, 2687) | -0.676 (-120.27, 2667) |
| `range_width_f63` | -0.276 (-79.01, 2687) | +0.718 (+101.16, 2667) |
| `fib_dist_f15` | +0.712 (+114.33, 2687) | -0.670 (-121.99, 2667) |
| `rsi_5` | +0.668 (+109.83, 2687) | -0.624 (-111.05, 2667) |
| `range_width_f39` | -0.278 (-74.08, 2687) | +0.634 (+94.40, 2667) |
| `atr_pct_20` | -0.450 (-148.27, 2687) | +0.627 (+92.94, 2667) |
| `pct_from_low_f102` | +0.622 (+100.06, 2687) | -0.603 (-139.27, 2667) |
| `vwap_zscore_100` | +0.610 (+100.54, 2687) | -0.350 (-65.00, 2667) |
| `di_spread_5` | +0.602 (+103.61, 2687) | -0.554 (-100.21, 2667) |
| `range_pos_f9` | +0.571 (+89.55, 2687) | -0.535 (-91.01, 2667) |
| `kama_er_50` | +0.569 (+67.42, 2687) | +0.326 (+18.86, 2667) |
| `atr_pct_10` | -0.392 (-116.69, 2687) | +0.565 (+85.35, 2667) |
| `range_width_f24` | -0.281 (-71.39, 2687) | +0.562 (+83.46, 2667) |
| `frac_diff_close` | +0.464 (+122.08, 2687) | -0.544 (-101.63, 2667) |
| `bb_pct_b_10` | +0.525 (+81.43, 2687) | -0.473 (-78.93, 2667) |
| `atr_pct_5` | -0.343 (-96.95, 2687) | +0.515 (+79.49, 2667) |
| `range_width_f15` | -0.281 (-71.70, 2687) | +0.502 (+76.70, 2667) |
| `adx_50` | +0.482 (+57.39, 2687) | +0.277 (+24.91, 2667) |
| `range_pos_f6` | +0.468 (+74.97, 2687) | -0.441 (-72.57, 2667) |
| `bb_width_50` | -0.052 (-15.89, 2687) | +0.468 (+64.71, 2667) |
| `bb_width_100` | +0.040 (+2.27, 2687) | +0.466 (+60.43, 2667) |
| `yangzhang_20` | -0.308 (-81.84, 2687) | +0.463 (+75.93, 2667) |
| `yangzhang_50` | -0.327 (-86.51, 2687) | +0.462 (+76.04, 2667) |
| `range_width_f9` | -0.275 (-70.81, 2687) | +0.455 (+72.36, 2667) |
| `yangzhang_10` | -0.287 (-76.98, 2687) | +0.439 (+72.77, 2667) |
| `range_width_f6` | -0.265 (-68.60, 2687) | +0.425 (+68.69, 2667) |
| `yangzhang_100` | -0.312 (-83.77, 2687) | +0.424 (+71.13, 2667) |
| `bb_width_20` | -0.158 (-35.73, 2687) | +0.419 (+60.09, 2667) |
| `adx_20` | +0.416 (+49.09, 2687) | +0.232 (+18.33, 2667) |
| `yangzhang_5` | -0.264 (-71.74, 2687) | +0.407 (+67.85, 2667) |
| `range_width_f3` | -0.248 (-65.74, 2687) | +0.391 (+64.55, 2667) |
| `bb_width_10` | -0.198 (-45.26, 2687) | +0.376 (+60.28, 2667) |
| `adx_100` | +0.361 (+47.34, 2687) | +0.138 (+14.27, 2667) |
| `bb_pct_b_5` | +0.358 (+57.57, 2687) | -0.326 (-51.84, 2667) |
| `bb_width_5` | -0.200 (-47.05, 2687) | +0.334 (+55.38, 2667) |
| `range_pos_f3` | +0.334 (+54.72, 2687) | -0.317 (-50.54, 2667) |
| `vwap_zscore_50` | +0.331 (+55.01, 2687) | -0.177 (-26.97, 2667) |
| `range_compression_f15_102` | -0.068 (-6.65, 2687) | -0.289 (-31.14, 2667) |
| `donchian_break_f15` | +0.286 (+52.25, 2687) | -0.214 (-77.20, 2667) |
| `adx_10` | +0.267 (+30.58, 2687) | +0.127 (+6.73, 2667) |
| `donchian_break_f6` | +0.243 (+42.55, 2687) | -0.201 (-58.44, 2667) |
| `kama_er_20` | +0.226 (+21.92, 2687) | +0.129 (+4.60, 2667) |
| `macd_norm_hist` | +0.216 (+34.40, 2687) | -0.120 (-16.24, 2667) |
| `range_compression_f6_39` | -0.040 (-1.01, 2687) | -0.164 (-14.68, 2667) |
| `adx_5` | +0.125 (+14.60, 2687) | +0.049 (+0.36, 2667) |
| `rsi_14_slope_5` | +0.116 (+20.01, 2687) | -0.071 (-11.32, 2667) |
| `amihud_5` | -0.083 (-49.89, 2687) | +0.113 (+18.80, 2667) |
| `amihud_10` | -0.078 (-46.38, 2687) | +0.112 (+18.19, 2667) |
| `amihud_20` | -0.071 (-41.42, 2687) | +0.108 (+17.91, 2667) |
| `vwap_zscore_20` | +0.105 (+18.12, 2687) | -0.052 (-6.40, 2667) |
| `amihud_50` | -0.059 (-33.14, 2687) | +0.103 (+16.78, 2667) |
| `obv_zscore_100` | +0.089 (+18.28, 2687) | -0.073 (-10.95, 2667) |
| `kama_er_10` | +0.082 (+7.79, 2687) | +0.041 (+0.42, 2667) |
| `amihud_100` | -0.044 (-21.02, 2687) | +0.081 (+14.77, 2667) |
| `entropy_20` | +0.014 (-1.00, 2687) | -0.070 (-19.16, 2667) |
| `obv_zscore_50` | +0.064 (+13.21, 2687) | -0.053 (-8.10, 2667) |
| `obv_zscore_20` | +0.039 (+8.30, 2687) | -0.035 (-5.39, 2667) |
| `vwap_zscore_10` | +0.030 (+5.97, 2687) | -0.013 (-1.54, 2667) |
| `entropy_10` | +0.008 (-0.60, 2687) | -0.029 (-9.10, 2667) |
| `obv_zscore_10` | +0.028 (+5.93, 2687) | -0.028 (-4.52, 2667) |
| `obv_zscore_5` | +0.026 (+5.39, 2687) | -0.027 (-4.36, 2667) |
| `kama_er_5` | +0.027 (+1.94, 2687) | +0.016 (-0.23, 2667) |
| `gap_z` | +0.022 (+4.58, 2687) | -0.011 (-1.47, 2667) |
| `hurst_100` | +0.014 (+3.69, 2687) | -0.019 (+2.07, 2667) |
| `hurst_50` | +0.002 (-2.32, 2687) | -0.008 (-0.11, 2667) |
| `vwap_zscore_5` | +0.006 (+1.51, 2687) | +0.000 (-0.06, 2667) |
| `hurst_20` | +0.004 (-0.56, 2687) | +0.006 (+1.40, 2667) |

## TREND_ASSOCIATION (directional states: trend_up, trend_down)

| Indicator | trend_up: Δz (t, dates) | trend_down: Δz (t, dates) |
| :--- | ---:  | ---: |
| `range_pos_f24` | +1.195 (+240.17, 2689) | -1.245 (-246.62, 2695) |
| `macd_norm_line` | +1.234 (+298.86, 2689) | -1.240 (-383.26, 2695) |
| `range_pos_f39` | +1.130 (+221.96, 2689) | -1.195 (-281.48, 2695) |
| `bb_pct_b_50` | +1.134 (+209.96, 2689) | -1.176 (-299.58, 2695) |
| `rsi_14` | +1.168 (+282.72, 2689) | -1.170 (-342.77, 2695) |
| `fib_dist_f39` | +1.124 (+259.27, 2689) | -1.168 (-306.77, 2695) |
| `rsi_21` | +1.129 (+260.81, 2689) | -1.130 (-338.23, 2695) |
| `di_spread_20` | +1.124 (+256.17, 2689) | -1.119 (-348.90, 2695) |
| `bb_pct_b_20` | +1.081 (+187.63, 2689) | -1.122 (-226.40, 2695) |
| `kalman_spread_atr` | +1.105 (+277.33, 2689) | -1.105 (-318.87, 2695) |
| `di_spread_10` | +1.082 (+256.69, 2689) | -1.085 (-316.82, 2695) |
| `range_pos_f63` | +0.998 (+198.55, 2689) | -1.059 (-271.83, 2695) |
| `range_pos_f15` | +0.985 (+186.95, 2689) | -1.026 (-204.82, 2695) |
| `fib_dist_f15` | +0.952 (+197.09, 2689) | -0.988 (-219.46, 2695) |
| `vwap_zscore_50` | +0.979 (+201.56, 2689) | -0.944 (-204.92, 2695) |
| `bb_pct_b_100` | +0.949 (+193.85, 2689) | -0.974 (-242.24, 2695) |
| `vwap_zscore_100` | +0.960 (+198.09, 2689) | -0.929 (-224.27, 2695) |
| `fib_dist_f102` | +0.901 (+204.19, 2689) | -0.940 (-233.78, 2695) |
| `di_spread_50` | +0.920 (+189.40, 2689) | -0.917 (-250.13, 2695) |
| `range_pos_f102` | +0.850 (+172.86, 2689) | -0.906 (-208.19, 2695) |
| `macd_norm_hist` | +0.826 (+168.59, 2689) | -0.832 (-189.32, 2695) |
| `rsi_5` | +0.807 (+168.80, 2689) | -0.816 (-202.74, 2695) |
| `di_spread_5` | +0.781 (+167.25, 2689) | -0.790 (-203.42, 2695) |
| `pct_from_high_f102` | +0.653 (+177.85, 2689) | -0.738 (-143.42, 2695) |
| `kama_er_20` | +0.730 (+77.62, 2689) | +0.399 (+31.33, 2695) |
| `di_spread_100` | +0.725 (+141.49, 2689) | -0.727 (-169.91, 2695) |
| `range_pos_f9` | +0.599 (+109.77, 2689) | -0.609 (-133.10, 2695) |
| `adx_10` | +0.581 (+76.17, 2689) | +0.272 (+28.72, 2695) |
| `bb_pct_b_10` | +0.562 (+99.23, 2689) | -0.564 (-120.30, 2695) |
| `pct_from_low_f102` | +0.478 (+74.68, 2689) | -0.458 (-108.28, 2695) |
| `adx_5` | +0.451 (+55.12, 2689) | +0.244 (+23.18, 2695) |
| `kama_er_50` | +0.405 (+50.72, 2689) | -0.090 (-10.00, 2695) |
| `range_pos_f6` | +0.386 (+68.54, 2689) | -0.388 (-81.78, 2695) |
| `vwap_zscore_10` | -0.361 (-63.45, 2689) | +0.384 (+76.66, 2695) |
| `range_width_f24` | +0.058 (+8.16, 2689) | +0.376 (+59.57, 2695) |
| `adx_20` | +0.361 (+52.22, 2689) | +0.053 (+8.15, 2695) |
| `bb_width_20` | +0.299 (+54.30, 2689) | +0.354 (+54.66, 2695) |
| `range_width_f15` | +0.036 (+4.55, 2689) | +0.348 (+59.50, 2695) |
| `donchian_break_f15` | +0.333 (+74.93, 2689) | -0.325 (-110.03, 2695) |
| `kama_er_100` | +0.314 (+49.37, 2689) | -0.191 (-27.92, 2695) |
| `vwap_zscore_20` | +0.310 (+54.59, 2689) | -0.293 (-59.73, 2695) |
| `atr_pct_50` | -0.267 (-62.16, 2689) | +0.298 (+58.02, 2695) |
| `range_width_f39` | -0.023 (-5.93, 2689) | +0.297 (+49.57, 2695) |
| `atr_pct_100` | -0.252 (-62.66, 2689) | +0.283 (+57.78, 2695) |
| `atr_pct_20` | -0.240 (-49.23, 2689) | +0.272 (+52.53, 2695) |
| `frac_diff_close` | +0.247 (+53.91, 2689) | -0.267 (-60.74, 2695) |
| `range_width_f63` | -0.088 (-20.09, 2689) | +0.253 (+46.71, 2695) |
| `kama_er_10` | +0.252 (+25.19, 2689) | +0.109 (+6.64, 2695) |
| `range_compression_f6_39` | -0.235 (-38.40, 2689) | -0.243 (-37.59, 2695) |
| `bb_pct_b_5` | +0.239 (+42.72, 2689) | -0.235 (-47.78, 2695) |
| `range_width_f102` | -0.126 (-30.51, 2689) | +0.232 (+44.80, 2695) |
| `atr_pct_10` | -0.194 (-36.07, 2689) | +0.226 (+44.60, 2695) |
| `vwap_zscore_5` | -0.222 (-39.89, 2689) | +0.226 (+44.55, 2695) |
| `donchian_break_f6` | +0.179 (+43.09, 2689) | -0.213 (-68.70, 2695) |
| `range_compression_f15_102` | +0.198 (+31.52, 2689) | +0.191 (+30.15, 2695) |
| `range_pos_f3` | +0.186 (+31.90, 2689) | -0.188 (-38.20, 2695) |
| `atr_pct_5` | -0.150 (-26.16, 2689) | +0.165 (+34.38, 2695) |
| `obv_zscore_10` | -0.162 (-31.98, 2689) | +0.163 (+35.47, 2695) |
| `range_width_f9` | -0.091 (-16.09, 2689) | +0.160 (+30.36, 2695) |
| `obv_zscore_20` | -0.145 (-28.82, 2689) | +0.148 (+31.34, 2695) |
| `bb_width_50` | +0.142 (+27.90, 2689) | +0.082 (+15.70, 2695) |
| `yangzhang_10` | -0.087 (-11.36, 2689) | +0.135 (+30.28, 2695) |
| `yangzhang_20` | -0.093 (-10.93, 2689) | +0.127 (+28.69, 2695) |
| `adx_50` | +0.127 (+27.71, 2689) | -0.056 (-10.13, 2695) |
| `range_width_f6` | -0.124 (-22.21, 2689) | +0.091 (+20.55, 2695) |
| `range_width_f3` | -0.118 (-23.32, 2689) | +0.065 (+16.72, 2695) |
| `bb_width_10` | -0.016 (-2.97, 2689) | +0.118 (+20.31, 2695) |
| `bb_width_5` | -0.118 (-23.56, 2689) | +0.030 (+8.58, 2695) |
| `gap_z` | -0.101 (-17.79, 2689) | +0.107 (+22.09, 2695) |
| `yangzhang_5` | -0.094 (-15.37, 2689) | +0.097 (+22.83, 2695) |
| `yangzhang_50` | -0.073 (-8.68, 2689) | +0.090 (+21.31, 2695) |
| `obv_zscore_5` | -0.082 (-16.53, 2689) | +0.079 (+17.53, 2695) |
| `yangzhang_100` | -0.056 (-5.62, 2689) | +0.070 (+17.44, 2695) |
| `adx_100` | +0.056 (+14.80, 2689) | -0.050 (-11.81, 2695) |
| `kama_er_5` | +0.007 (+0.54, 2689) | -0.056 (-12.48, 2695) |
| `bb_width_100` | +0.051 (+14.61, 2689) | +0.010 (+5.14, 2695) |
| `entropy_20` | +0.021 (+0.42, 2689) | -0.049 (-23.18, 2695) |
| `amihud_5` | -0.043 (-19.25, 2689) | +0.025 (+11.64, 2695) |
| `hurst_100` | +0.043 (+23.14, 2689) | +0.029 (+18.19, 2695) |
| `obv_zscore_100` | +0.038 (+7.12, 2689) | -0.036 (-7.75, 2695) |
| `amihud_10` | -0.035 (-15.30, 2689) | +0.023 (+10.92, 2695) |
| `hurst_50` | +0.035 (+9.80, 2689) | +0.014 (+1.77, 2695) |
| `rsi_14_slope_5` | -0.008 (-4.11, 2689) | +0.032 (+3.97, 2695) |
| `amihud_20` | -0.021 (-8.49, 2689) | +0.013 (+8.43, 2695) |
| `entropy_10` | +0.008 (-0.21, 2689) | -0.012 (-9.73, 2695) |
| `amihud_50` | -0.010 (-2.32, 2689) | +0.004 (+5.24, 2695) |
| `obv_zscore_50` | -0.006 (-1.92, 2689) | +0.009 (+1.73, 2695) |
| `hurst_20` | +0.001 (-0.25, 2689) | -0.007 (-3.80, 2695) |
| `amihud_100` | -0.004 (+1.13, 2689) | -0.003 (+3.51, 2695) |

## REDUNDANCY_CLUSTERS

Pooled within-date correlation of the z-scores over a deterministic stride-5 subsample (248,056 rows); connected components at |corr| >= 0.90. 7 redundant cluster(s) with >1 member:

- **cluster 1** (22): `rsi_5`, `rsi_14`, `rsi_21`, `bb_pct_b_10`, `bb_pct_b_20`, `bb_pct_b_50`, `bb_pct_b_100`, `macd_norm_line`, `di_spread_5`, `di_spread_10`, `di_spread_20`, `kalman_spread_atr`, `range_pos_f6`, `range_pos_f9` … (+8 more)
- **cluster 2** (8): `atr_pct_5`, `atr_pct_10`, `atr_pct_20`, `atr_pct_50`, `atr_pct_100`, `yangzhang_5`, `yangzhang_10`, `yangzhang_20`
- **cluster 3** (5): `obv_zscore_5`, `obv_zscore_10`, `obv_zscore_20`, `obv_zscore_50`, `obv_zscore_100`
- **cluster 4** (3): `amihud_5`, `amihud_10`, `amihud_20`
- **cluster 5** (2): `bb_width_10`, `range_width_f9`
- **cluster 6** (2): `di_spread_50`, `di_spread_100`
- **cluster 7** (2): `yangzhang_50`, `yangzhang_100`

## SELECTED_INDICATORS

Pre-declared selection rule: drop indicators already represented by a Step 2 primitive (`kama_er_20`, `atr_pct_20`, `amihud_20`), require |t| >= 2.0 in at least one state, collapse redundancy clusters to their strongest-associated member (|Δz|), keep at most 6. The rule was fixed before the numbers were seen.

SELECTED_INDICATORS: pct_from_high_f102, fib_dist_f102, di_spread_100, vwap_zscore_50, vwap_zscore_100, macd_norm_hist

| Selected indicator | Best state | Δz | t | Cluster size | Why it is not already covered |
| :--- | :--- | ---: | ---: | ---: | :--- |
| `pct_from_high_f102` | `ch52_low` | -1.434 | -220.67 | 1 | distinct from the E5 primitives and from the retained representatives |
| `fib_dist_f102` | `ch52_low` | -1.389 | -315.24 | 22 | distinct from the E5 primitives and from the retained representatives |
| `di_spread_100` | `ch52_low` | -1.347 | -404.13 | 2 | distinct from the E5 primitives and from the retained representatives |
| `vwap_zscore_50` | `trend_up` | +0.979 | +201.56 | 1 | distinct from the E5 primitives and from the retained representatives |
| `vwap_zscore_100` | `trend_up` | +0.960 | +198.09 | 1 | distinct from the E5 primitives and from the retained representatives |
| `macd_norm_hist` | `trend_down` | -0.832 | -189.32 | 1 | distinct from the E5 primitives and from the retained representatives |

### Distinctness vs the Step 2 vocabulary (disclosure, not a re-selection)

Some indicators are *near-mechanical restatements* of the state they are associated with (a channel-distance or volatility measure vs a channel/volatility state). The selection rule was fixed before these numbers were seen, so nothing is re-selected here — but the overlap is reported for the human gate, and Step 4 additionally reports the joint firing rate between each `ind_*` condition and the base state it shadows.

| Selected indicator | max abs corr with a Step 2-vocabulary indicator | Analogue |
| :--- | ---: | :--- |
| `pct_from_high_f102` | 0.812 | `range_pos_f102` (position in a 102d high/low channel (Step 2 uses 252d)) |
| `fib_dist_f102` | 0.980 | `range_pos_f102` (position in a 102d high/low channel (Step 2 uses 252d)) |
| `di_spread_100` | 0.766 | `range_pos_f102` (position in a 102d high/low channel (Step 2 uses 252d)) |
| `vwap_zscore_50` | 0.267 | `range_pos_f102` (position in a 102d high/low channel (Step 2 uses 252d)) |
| `vwap_zscore_100` | 0.589 | `range_pos_f102` (position in a 102d high/low channel (Step 2 uses 252d)) |
| `macd_norm_hist` | 0.168 | `range_pos_f102` (position in a 102d high/low channel (Step 2 uses 252d)) |

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
