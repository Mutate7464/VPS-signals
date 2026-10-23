# Sprint 3 — Statistical Metadata Selection (Gate 3)

- Generated (UTC): 2026-10-23T08:49:03.197724+00:00

## USD

- Raw features: **63** | Surviving after VIF pruning: **28**
- Train cutoff (feature selection split): `2024-07-30`

### Stationarity (ADF) — features flagged for rolling Z-score

- **11** non-stationary features flagged (median p > 0.05):

`adx_50`, `adx_100`, `di_spread_100`, `atr_pct_20`, `atr_pct_50`, `atr_pct_100`, `hurst_100`, `amihud_50`, `amihud_100`, `yangzhang_50`, `yangzhang_100`

### Collinearity pruning (VIF) — dropped features

| Feature | Reason | VIF |
| :--- | :--- | ---: |
| `vwap_zscore_20` | VIF | 7.454703264569209 |
| `vwap_zscore_100` | VIF | 5.651988795647824 |
| `bb_pct_b_5` | VIF | 11.664004375782685 |
| `di_spread_5` | VIF | 145.90560873961303 |
| `kalman_spread_atr` | VIF | 101.90243561617994 |
| `obv_zscore_5` | VIF | 8.931105352832162 |
| `atr_pct_10` | VIF | 1511.824726820147 |
| `bb_pct_b_10` | VIF | 14.792760256784156 |
| `di_spread_10` | VIF | 118.2545504798335 |
| `bb_pct_b_100` | VIF | 11.568450141790878 |
| `adx_10` | VIF | 13.70302670264891 |
| `di_spread_100` | VIF | 31.58302604626225 |
| `vwap_zscore_50` | VIF | 5.994607320073719 |
| `obv_zscore_10` | VIF | 14.749379271382567 |
| `di_spread_50` | VIF | 22.05400918698921 |
| `obv_zscore_20` | VIF | 16.3690241035523 |
| `bb_pct_b_50` | VIF | 9.809001030498445 |
| `bb_pct_b_20` | VIF | 9.682220817499115 |
| `adx_50` | VIF | 7.6195742465586145 |
| `yangzhang_20` | VIF | 16.62720300608797 |
| `yangzhang_10` | VIF | 12.303470891560032 |
| `bb_width_20` | VIF | 5.509176686322574 |
| `macd_norm_line` | VIF | 38.340366729664154 |
| `yangzhang_5` | VIF | 8.89201388203245 |
| `atr_pct_5` | VIF | 28.30343355455518 |
| `obv_zscore_100` | VIF | 28.956983202056726 |
| `di_spread_20` | VIF | 9.964325101451179 |
| `macd_norm_hist` | VIF | 5.726570650908276 |
| `bb_width_50` | VIF | 6.332890421644693 |
| `atr_pct_50` | VIF | 117.36702624560807 |
| `bb_width_100` | VIF | 5.20819452076719 |
| `atr_pct_20` | VIF | 15.711061369795571 |
| `yangzhang_50` | VIF | 9.944249308492946 |
| `rsi_21` | VIF | 84.96559617546333 |
| `rsi_5` | VIF | 14.037881609513013 |

### Top features by Mutual Information (per target)

**y_15d_high**

- `entropy_10` — MI 0.0082
- `rsi_14` — MI 0.0021
- `rsi_5` — MI 0.0018
- `adx_5` — MI 0.0016
- `frac_diff_close` — MI 0.0014
- `kama_er_10` — MI 0.0013
- `macd_norm_line` — MI 0.0013
- `vwap_zscore_10` — MI 0.0013
- `amihud_50` — MI 0.0013
- `yangzhang_50` — MI 0.0013

**y_15d_low**

- `entropy_10` — MI 0.0060
- `rsi_14` — MI 0.0032
- `rsi_5` — MI 0.0031
- `obv_zscore_100` — MI 0.0024
- `bb_width_5` — MI 0.0019
- `rsi_21` — MI 0.0019
- `kama_er_5` — MI 0.0017
- `obv_zscore_50` — MI 0.0017
- `bb_width_100` — MI 0.0015
- `atr_pct_20` — MI 0.0014

**y_20d_up**

- `entropy_10` — MI 0.0080
- `yangzhang_100` — MI 0.0040
- `adx_100` — MI 0.0021
- `rsi_21` — MI 0.0020
- `bb_width_5` — MI 0.0018
- `rsi_14` — MI 0.0016
- `kama_er_20` — MI 0.0015
- `adx_20` — MI 0.0014
- `rsi_5` — MI 0.0014
- `bb_width_50` — MI 0.0014

**y_20d_down**

- `entropy_10` — MI 0.0102
- `yangzhang_100` — MI 0.0022
- `atr_pct_100` — MI 0.0015
- `obv_zscore_50` — MI 0.0013
- `kama_er_50` — MI 0.0013
- `macd_norm_hist` — MI 0.0013
- `rsi_5` — MI 0.0013
- `entropy_20` — MI 0.0013
- `rsi_21` — MI 0.0013
- `bb_width_20` — MI 0.0012


### Surviving whitelist (per target)

- **y_15d_high** (19 features): `rsi_14`, `rsi_14_slope_5`, `bb_width_5`, `bb_width_10`, `adx_5`, `adx_20`, `obv_zscore_50`, `frac_diff_close`, `entropy_10`, `entropy_20`, `kama_er_5`, `kama_er_10`, `kama_er_50`, `kama_er_100`, `vwap_zscore_5`, `vwap_zscore_10`, `amihud_20`, `amihud_50`, `yangzhang_100`

- **y_15d_low** (19 features): `rsi_14`, `rsi_14_slope_5`, `bb_width_5`, `bb_width_10`, `adx_20`, `adx_100`, `atr_pct_100`, `obv_zscore_50`, `entropy_10`, `entropy_20`, `kama_er_5`, `kama_er_10`, `kama_er_20`, `kama_er_50`, `kama_er_100`, `vwap_zscore_5`, `vwap_zscore_10`, `amihud_20`, `yangzhang_100`

- **y_20d_up** (19 features): `rsi_14`, `rsi_14_slope_5`, `bb_width_5`, `adx_20`, `adx_100`, `atr_pct_100`, `obv_zscore_50`, `hurst_20`, `frac_diff_close`, `entropy_10`, `entropy_20`, `kama_er_5`, `kama_er_10`, `kama_er_20`, `kama_er_50`, `kama_er_100`, `vwap_zscore_5`, `amihud_10`, `yangzhang_100`

- **y_20d_down** (19 features): `rsi_14`, `rsi_14_slope_5`, `bb_width_5`, `bb_width_10`, `adx_100`, `atr_pct_100`, `obv_zscore_50`, `hurst_20`, `frac_diff_close`, `entropy_10`, `entropy_20`, `kama_er_5`, `kama_er_10`, `kama_er_20`, `kama_er_50`, `kama_er_100`, `vwap_zscore_5`, `vwap_zscore_10`, `yangzhang_100`

- Transformed feature matrix saved to `data/features/features_USD_metadata.parquet`

