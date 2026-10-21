# Sprint 3 — Statistical Metadata Selection (Gate 3)

- Generated (UTC): 2026-10-21T02:49:33.170620+00:00

## USD

- Raw features: **63** | Surviving after VIF pruning: **10**
- Train cutoff (feature selection split): `2026-07-08`

### Stationarity (ADF) — features flagged for rolling Z-score

- **25** non-stationary features flagged (median p > 0.05):

`bb_pct_b_50`, `bb_width_50`, `bb_pct_b_100`, `bb_width_100`, `macd_norm_line`, `adx_20`, `adx_50`, `di_spread_50`, `di_spread_100`, `atr_pct_50`, `atr_pct_100`, `hurst_20`, `hurst_50`, `hurst_100`, `kama_er_50`, `kama_er_100`, `vwap_zscore_50`, `amihud_10`, `amihud_20`, `amihud_50`, `amihud_100`, `yangzhang_10`, `yangzhang_20`, `yangzhang_50`, `yangzhang_100`

### Collinearity pruning (VIF) — dropped features

| Feature | Reason | VIF |
| :--- | :--- | ---: |
| `bb_pct_b_20` | VIF | 153.96075435329865 |
| `vwap_zscore_5` | VIF | 15.175437766729091 |
| `obv_zscore_100` | VIF | 2155.9998202670836 |
| `di_spread_5` | VIF | 6616.473093478285 |
| `obv_zscore_50` | VIF | 170.07187291935577 |
| `vwap_zscore_20` | VIF | 57.21949559148705 |
| `obv_zscore_20` | VIF | 80.95914331906386 |
| `hurst_50` | VIF | 8.813763124467597 |
| `macd_norm_hist` | VIF | 402.31076305196376 |
| `bb_pct_b_10` | VIF | 51.70128199511811 |
| `atr_pct_20` | VIF | 12932.277957232525 |
| `bb_width_5` | VIF | 5.023060609822584 |
| `bb_pct_b_5` | VIF | 38.33123652028174 |
| `obv_zscore_10` | VIF | 24.992266092354747 |
| `vwap_zscore_10` | VIF | 33.564125867589496 |
| `atr_pct_10` | VIF | 967.0790153116203 |
| `rsi_5` | VIF | 369.7332456291866 |
| `frac_diff_close` | VIF | 218.07152638093257 |
| `adx_10` | VIF | 789.9155441931669 |
| `di_spread_10` | VIF | 7444.702463801633 |
| `rsi_14_slope_5` | VIF | 11.445736693441127 |
| `kalman_spread_atr` | VIF | 1011.2664777943638 |
| `yangzhang_5` | VIF | 10.63929243583125 |
| `atr_pct_5` | VIF | 28.116630859476857 |
| `adx_5` | VIF | 13.872187257455616 |
| `yangzhang_50` | VIF | 64.46844305089462 |
| `amihud_5` | VIF | 5.550352371939229 |
| `kama_er_100` | VIF | 53.64557336764809 |
| `atr_pct_50` | VIF | 288.6956244762404 |
| `yangzhang_20` | VIF | 9.955705675221953 |
| `macd_norm_line` | VIF | 54.78730961281141 |
| `bb_pct_b_50` | VIF | 50.207399569433576 |
| `kama_er_20` | VIF | 5.961184546775641 |
| `yangzhang_10` | VIF | 7.905299816784567 |
| `hurst_100` | VIF | 15.867098911079612 |
| `kama_er_50` | VIF | 23.261448838565826 |
| `rsi_14` | VIF | 2884.7514554767567 |
| `bb_width_20` | VIF | 14.47257240774799 |
| `bb_pct_b_100` | VIF | 88.63887601771755 |
| `amihud_20` | VIF | 11.349885072933395 |
| `vwap_zscore_50` | VIF | 19.994102492608256 |
| `atr_pct_100` | VIF | 275.9055591743597 |
| `di_spread_20` | VIF | 655.8323846420634 |
| `yangzhang_100` | VIF | 11.558954834029066 |
| `vwap_zscore_100` | VIF | 58.56076693937629 |
| `bb_width_50` | VIF | 105.59762830315884 |
| `rsi_21` | VIF | 35.504868932899036 |
| `adx_20` | VIF | 75.04334030373639 |
| `di_spread_50` | VIF | 153.11039584669743 |
| `di_spread_100` | VIF | 28.549450564799287 |
| `bb_width_100` | VIF | 24.52288940661505 |
| `adx_50` | VIF | 15.71131370509272 |
| `amihud_100` | VIF | 11.76719250051802 |

### Top features by Mutual Information (per target)

**y_15d_high**

- `adx_100` — MI 0.2620
- `di_spread_100` — MI 0.1795
- `di_spread_50` — MI 0.1733
- `bb_pct_b_100` — MI 0.1514
- `macd_norm_line` — MI 0.1479
- `amihud_100` — MI 0.1464
- `amihud_10` — MI 0.1395
- `bb_pct_b_50` — MI 0.1339
- `bb_width_10` — MI 0.1270
- `bb_width_20` — MI 0.1266

**y_15d_low**

- `amihud_50` — MI 0.2949
- `adx_100` — MI 0.2539
- `bb_width_100` — MI 0.2210
- `di_spread_100` — MI 0.1882
- `rsi_14` — MI 0.1683
- `di_spread_50` — MI 0.1647
- `adx_50` — MI 0.1558
- `rsi_21` — MI 0.1468
- `adx_20` — MI 0.1425
- `kalman_spread_atr` — MI 0.1313

**y_20d_up**

- `adx_100` — MI 0.4719
- `amihud_100` — MI 0.3073
- `adx_50` — MI 0.2975
- `amihud_50` — MI 0.2191
- `bb_width_100` — MI 0.2152
- `bb_width_50` — MI 0.2097
- `yangzhang_10` — MI 0.1797
- `atr_pct_100` — MI 0.1656
- `yangzhang_100` — MI 0.1646
- `adx_20` — MI 0.1521

**y_20d_down**

- `bb_width_10` — MI 0.0569
- `kama_er_5` — MI 0.0543
- `atr_pct_5` — MI 0.0416
- `yangzhang_10` — MI 0.0405
- `hurst_100` — MI 0.0403
- `yangzhang_20` — MI 0.0350
- `yangzhang_100` — MI 0.0319
- `amihud_20` — MI 0.0315
- `rsi_14_slope_5` — MI 0.0273
- `hurst_20` — MI 0.0239


### Surviving whitelist (per target)

- **y_15d_high** (7 features): `bb_width_10`, `adx_100`, `hurst_20`, `entropy_20`, `kama_er_10`, `amihud_10`, `amihud_50`

- **y_15d_low** (7 features): `bb_width_10`, `adx_100`, `entropy_10`, `kama_er_5`, `kama_er_10`, `amihud_10`, `amihud_50`

- **y_20d_up** (7 features): `bb_width_10`, `adx_100`, `obv_zscore_5`, `entropy_20`, `kama_er_10`, `amihud_10`, `amihud_50`

- **y_20d_down** (7 features): `bb_width_10`, `hurst_20`, `entropy_10`, `entropy_20`, `kama_er_5`, `kama_er_10`, `amihud_10`

- Transformed feature matrix saved to `data/features/features_USD_metadata.parquet`

## CAD

- Raw features: **63** | Surviving after VIF pruning: **9**
- Train cutoff (feature selection split): `2026-07-08`

### Stationarity (ADF) — features flagged for rolling Z-score

- **27** non-stationary features flagged (median p > 0.05):

`rsi_14`, `rsi_21`, `bb_pct_b_50`, `bb_width_50`, `bb_pct_b_100`, `bb_width_100`, `macd_norm_line`, `adx_20`, `di_spread_20`, `adx_50`, `di_spread_50`, `di_spread_100`, `atr_pct_50`, `atr_pct_100`, `hurst_50`, `hurst_100`, `kalman_spread_atr`, `kama_er_50`, `kama_er_100`, `vwap_zscore_50`, `amihud_20`, `amihud_50`, `amihud_100`, `yangzhang_10`, `yangzhang_20`, `yangzhang_50`, `yangzhang_100`

### Collinearity pruning (VIF) — dropped features

| Feature | Reason | VIF |
| :--- | :--- | ---: |
| `obv_zscore_100` | VIF | 448.0923375313057 |
| `di_spread_10` | VIF | 45160.31327440553 |
| `bb_pct_b_20` | VIF | 165.97142668095898 |
| `obv_zscore_20` | VIF | 328.21513414669175 |
| `vwap_zscore_5` | VIF | 10.674534413708333 |
| `obv_zscore_10` | VIF | 87.11114185094684 |
| `kama_er_5` | VIF | 6.650986881815299 |
| `rsi_5` | VIF | 1415.149635771952 |
| `obv_zscore_5` | VIF | 22.43077855341108 |
| `di_spread_5` | VIF | 715.918296818159 |
| `bb_pct_b_5` | VIF | 20.534180606856175 |
| `kalman_spread_atr` | VIF | 7951.948760318977 |
| `vwap_zscore_50` | VIF | 114.26053476293617 |
| `yangzhang_10` | VIF | 13.9423332906349 |
| `bb_width_5` | VIF | 5.808651598493414 |
| `kama_er_10` | VIF | 7.790934561345975 |
| `vwap_zscore_10` | VIF | 21.507438709183635 |
| `bb_pct_b_10` | VIF | 36.90193790276556 |
| `rsi_14_slope_5` | VIF | 11.764499792303626 |
| `kama_er_50` | VIF | 31.868926148347917 |
| `kama_er_20` | VIF | 11.058220396131793 |
| `atr_pct_10` | VIF | 3207.420249531807 |
| `atr_pct_20` | VIF | 1347.1058405735455 |
| `rsi_21` | VIF | 36798.674611677925 |
| `atr_pct_5` | VIF | 28.157136281917296 |
| `rsi_14` | VIF | 683.5733787273954 |
| `yangzhang_5` | VIF | 5.084391667766388 |
| `di_spread_20` | VIF | 3056.9562490137187 |
| `bb_pct_b_50` | VIF | 322.223683006754 |
| `amihud_10` | VIF | 10.857675113681744 |
| `yangzhang_20` | VIF | 12.877059645397528 |
| `bb_width_10` | VIF | 10.052749273893033 |
| `vwap_zscore_20` | VIF | 20.245221527077973 |
| `adx_5` | VIF | 12.86612176689764 |
| `yangzhang_50` | VIF | 13.69588354915506 |
| `adx_10` | VIF | 33.20806682512059 |
| `entropy_20` | VIF | 5.442459341138246 |
| `yangzhang_100` | VIF | 43.31125138654483 |
| `kama_er_100` | VIF | 63.8170196849967 |
| `bb_width_20` | VIF | 10.993892235963541 |
| `bb_pct_b_100` | VIF | 101.2206273698532 |
| `macd_norm_line` | VIF | 84.71742135383595 |
| `frac_diff_close` | VIF | 206.10885338012235 |
| `adx_20` | VIF | 54.54090611705818 |
| `vwap_zscore_100` | VIF | 36.54129799589088 |
| `macd_norm_hist` | VIF | 12.030762790307618 |
| `amihud_20` | VIF | 9.412167355500884 |
| `amihud_100` | VIF | 134.52503464970988 |
| `di_spread_50` | VIF | 1262.2962006231528 |
| `atr_pct_50` | VIF | 89.59518813485289 |
| `amihud_50` | VIF | 10.481641298939891 |
| `bb_width_100` | VIF | 19.645380014346078 |
| `adx_100` | VIF | 16.77717443009649 |
| `di_spread_100` | VIF | 8.106095454560313 |

### Top features by Mutual Information (per target)

**y_15d_high**

- `di_spread_100` — MI 0.2054
- `adx_20` — MI 0.1650
- `adx_100` — MI 0.1623
- `atr_pct_100` — MI 0.1612
- `bb_width_100` — MI 0.1557
- `atr_pct_50` — MI 0.1520
- `adx_50` — MI 0.1494
- `amihud_50` — MI 0.1312
- `macd_norm_line` — MI 0.1279
- `bb_width_50` — MI 0.1149

**y_15d_low**

- `bb_width_100` — MI 0.1936
- `amihud_50` — MI 0.1888
- `atr_pct_100` — MI 0.1842
- `adx_100` — MI 0.1595
- `di_spread_100` — MI 0.1569
- `yangzhang_100` — MI 0.1562
- `entropy_10` — MI 0.1552
- `atr_pct_50` — MI 0.1546
- `entropy_20` — MI 0.1508
- `amihud_100` — MI 0.1437

**y_20d_up**

- `adx_50` — MI 0.4039
- `adx_100` — MI 0.3665
- `atr_pct_100` — MI 0.3639
- `di_spread_100` — MI 0.3216
- `di_spread_50` — MI 0.2998
- `atr_pct_50` — MI 0.2857
- `amihud_50` — MI 0.2796
- `frac_diff_close` — MI 0.2598
- `bb_width_100` — MI 0.2492
- `adx_20` — MI 0.2461

**y_20d_down**

- `bb_width_50` — MI 0.1726
- `bb_width_100` — MI 0.1063
- `amihud_100` — MI 0.0977
- `amihud_5` — MI 0.0953
- `amihud_50` — MI 0.0933
- `amihud_20` — MI 0.0763
- `atr_pct_100` — MI 0.0674
- `kama_er_100` — MI 0.0665
- `bb_width_10` — MI 0.0637
- `adx_10` — MI 0.0587


### Surviving whitelist (per target)

- **y_15d_high** (6 features): `bb_width_50`, `adx_50`, `atr_pct_100`, `hurst_50`, `hurst_100`, `amihud_5`

- **y_15d_low** (6 features): `bb_width_50`, `adx_50`, `atr_pct_100`, `hurst_100`, `entropy_10`, `amihud_5`

- **y_20d_up** (6 features): `bb_width_50`, `adx_50`, `atr_pct_100`, `hurst_50`, `hurst_100`, `entropy_10`

- **y_20d_down** (6 features): `bb_width_50`, `adx_50`, `atr_pct_100`, `hurst_20`, `hurst_50`, `amihud_5`

- Transformed feature matrix saved to `data/features/features_CAD_metadata.parquet`

