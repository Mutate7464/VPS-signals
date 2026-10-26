# WI-013 — metadata panel rebuild verification (F-4)

- Generated (UTC): 2026-10-26T16:50:47Z
- Rebuild recipe: `data/metadata_catalog_{market}.json` (surviving features + ADF stationarity flags) applied to `features_{market}.parquet` — the same 60-row per-symbol Z-score and per-date `rank(pct=True)` construction as `src/stat_metadata.py`, not the legacy `load_market_frame` path.
- Comparison: every surviving column checked with `pandas.testing.assert_frame_equal(check_dtype=True, check_exact=True)`, one column at a time (same assertion, bounded memory), plus row count and column order.
- Swap performed: **YES**
- Staging directory: `/home/yycuser/.hermes/cache/scratch/wi013_rebuild_8djhei0q`

## Per-market result

| Market | Old rows | New rows | Rows equal | Cols old → new | Labels dropped | Labels left | Column order | Columns compared | Columns unequal | Verdict |
| :--- | ---: | ---: | :--- | :--- | :--- | :--- | :--- | ---: | :--- | :--- |
| USD | 1,240,275 | 1,240,275 | yes | 71 → 67 | `y_15d_high`, `y_15d_low`, `y_20d_down`, `y_20d_up` | (none) | ok | 67 | none | **PASS** |
| CAD | 701,599 | 701,599 | yes | 91 → 87 | `y_15d_high`, `y_15d_low`, `y_20d_down`, `y_20d_up` | (none) | ok | 87 | none | **PASS** |

## USD — per-column equality (old vs new, exact)

- Comparison reference: `data/features/features_USD_metadata_pre_wi013.parquet (pre-swap backup)`
- Old panel columns: 71 · new: 67 · labels removed: `y_15d_high`, `y_15d_low`, `y_20d_down`, `y_20d_up`
- Surviving-column order equals the catalog order: **yes**; equals the old order minus labels: **yes**
- Backups: `data/features/features_USD_metadata_pre_wi013.parquet`

| Column | Rows old | Rows new | dtype old | dtype new | exact equal |
| :--- | ---: | ---: | :--- | :--- | :--- |
| `date` | 1,240,275 | 1,240,275 | datetime64[ns] | datetime64[ns] | yes |
| `symbol` | 1,240,275 | 1,240,275 | str | str | yes |
| `market` | 1,240,275 | 1,240,275 | str | str | yes |
| `bb_width_5` | 1,240,275 | 1,240,275 | float32 | float32 | yes |
| `adx_20` | 1,240,275 | 1,240,275 | float32 | float32 | yes |
| `adx_100` | 1,240,275 | 1,240,275 | float32 | float32 | yes |
| `obv_zscore_5` | 1,240,275 | 1,240,275 | float32 | float32 | yes |
| `obv_zscore_100` | 1,240,275 | 1,240,275 | float32 | float32 | yes |
| `hurst_20` | 1,240,275 | 1,240,275 | float32 | float32 | yes |
| `hurst_50` | 1,240,275 | 1,240,275 | float32 | float32 | yes |
| `hurst_100` | 1,240,275 | 1,240,275 | float32 | float32 | yes |
| `frac_diff_close` | 1,240,275 | 1,240,275 | float32 | float32 | yes |
| `entropy_10` | 1,240,275 | 1,240,275 | float32 | float32 | yes |
| `entropy_20` | 1,240,275 | 1,240,275 | float32 | float32 | yes |
| `kama_er_5` | 1,240,275 | 1,240,275 | float32 | float32 | yes |
| `kama_er_10` | 1,240,275 | 1,240,275 | float32 | float32 | yes |
| `kama_er_20` | 1,240,275 | 1,240,275 | float32 | float32 | yes |
| `kama_er_50` | 1,240,275 | 1,240,275 | float32 | float32 | yes |
| `kama_er_100` | 1,240,275 | 1,240,275 | float32 | float32 | yes |
| `vwap_zscore_5` | 1,240,275 | 1,240,275 | float32 | float32 | yes |
| `vwap_zscore_100` | 1,240,275 | 1,240,275 | float32 | float32 | yes |
| `amihud_5` | 1,240,275 | 1,240,275 | float32 | float32 | yes |
| `amihud_10` | 1,240,275 | 1,240,275 | float32 | float32 | yes |
| `amihud_20` | 1,240,275 | 1,240,275 | float32 | float32 | yes |
| `amihud_50` | 1,240,275 | 1,240,275 | float32 | float32 | yes |
| `amihud_100` | 1,240,275 | 1,240,275 | float64 | float64 | yes |
| `yangzhang_100` | 1,240,275 | 1,240,275 | float64 | float64 | yes |
| `donchian_break_f6` | 1,240,275 | 1,240,275 | float32 | float32 | yes |
| `donchian_break_f15` | 1,240,275 | 1,240,275 | float32 | float32 | yes |
| `range_width_f24` | 1,240,275 | 1,240,275 | float32 | float32 | yes |
| `range_pos_f39` | 1,240,275 | 1,240,275 | float32 | float32 | yes |
| `range_compression_f6_39` | 1,240,275 | 1,240,275 | float32 | float32 | yes |
| `range_compression_f15_102` | 1,240,275 | 1,240,275 | float32 | float32 | yes |
| `pct_from_low_f102` | 1,240,275 | 1,240,275 | float32 | float32 | yes |
| `gap_z` | 1,240,275 | 1,240,275 | float32 | float32 | yes |
| `bb_width_5_cs_pct` | 1,240,275 | 1,240,275 | float32 | float32 | yes |
| `adx_20_cs_pct` | 1,240,275 | 1,240,275 | float32 | float32 | yes |
| `adx_100_cs_pct` | 1,240,275 | 1,240,275 | float32 | float32 | yes |
| `obv_zscore_5_cs_pct` | 1,240,275 | 1,240,275 | float32 | float32 | yes |
| `obv_zscore_100_cs_pct` | 1,240,275 | 1,240,275 | float32 | float32 | yes |
| `hurst_20_cs_pct` | 1,240,275 | 1,240,275 | float32 | float32 | yes |
| `hurst_50_cs_pct` | 1,240,275 | 1,240,275 | float32 | float32 | yes |
| `hurst_100_cs_pct` | 1,240,275 | 1,240,275 | float32 | float32 | yes |
| `frac_diff_close_cs_pct` | 1,240,275 | 1,240,275 | float32 | float32 | yes |
| `entropy_10_cs_pct` | 1,240,275 | 1,240,275 | float32 | float32 | yes |
| `entropy_20_cs_pct` | 1,240,275 | 1,240,275 | float32 | float32 | yes |
| `kama_er_5_cs_pct` | 1,240,275 | 1,240,275 | float32 | float32 | yes |
| `kama_er_10_cs_pct` | 1,240,275 | 1,240,275 | float32 | float32 | yes |
| `kama_er_20_cs_pct` | 1,240,275 | 1,240,275 | float32 | float32 | yes |
| `kama_er_50_cs_pct` | 1,240,275 | 1,240,275 | float32 | float32 | yes |
| `kama_er_100_cs_pct` | 1,240,275 | 1,240,275 | float32 | float32 | yes |
| `vwap_zscore_5_cs_pct` | 1,240,275 | 1,240,275 | float32 | float32 | yes |
| `vwap_zscore_100_cs_pct` | 1,240,275 | 1,240,275 | float32 | float32 | yes |
| `amihud_5_cs_pct` | 1,240,275 | 1,240,275 | float32 | float32 | yes |
| `amihud_10_cs_pct` | 1,240,275 | 1,240,275 | float32 | float32 | yes |
| `amihud_20_cs_pct` | 1,240,275 | 1,240,275 | float32 | float32 | yes |
| `amihud_50_cs_pct` | 1,240,275 | 1,240,275 | float32 | float32 | yes |
| `amihud_100_cs_pct` | 1,240,275 | 1,240,275 | float32 | float32 | yes |
| `yangzhang_100_cs_pct` | 1,240,275 | 1,240,275 | float32 | float32 | yes |
| `donchian_break_f6_cs_pct` | 1,240,275 | 1,240,275 | float32 | float32 | yes |
| `donchian_break_f15_cs_pct` | 1,240,275 | 1,240,275 | float32 | float32 | yes |
| `range_width_f24_cs_pct` | 1,240,275 | 1,240,275 | float32 | float32 | yes |
| `range_pos_f39_cs_pct` | 1,240,275 | 1,240,275 | float32 | float32 | yes |
| `range_compression_f6_39_cs_pct` | 1,240,275 | 1,240,275 | float32 | float32 | yes |
| `range_compression_f15_102_cs_pct` | 1,240,275 | 1,240,275 | float32 | float32 | yes |
| `pct_from_low_f102_cs_pct` | 1,240,275 | 1,240,275 | float32 | float32 | yes |
| `gap_z_cs_pct` | 1,240,275 | 1,240,275 | float32 | float32 | yes |

## CAD — per-column equality (old vs new, exact)

- Comparison reference: `data/features/features_CAD_metadata_pre_wi013.parquet (pre-swap backup)`
- Old panel columns: 91 · new: 87 · labels removed: `y_15d_high`, `y_15d_low`, `y_20d_down`, `y_20d_up`
- Surviving-column order equals the catalog order: **yes**; equals the old order minus labels: **yes**
- Backups: `data/features/features_CAD_metadata_pre_wi013.parquet`

| Column | Rows old | Rows new | dtype old | dtype new | exact equal |
| :--- | ---: | ---: | :--- | :--- | :--- |
| `date` | 701,599 | 701,599 | datetime64[ns] | datetime64[ns] | yes |
| `symbol` | 701,599 | 701,599 | str | str | yes |
| `market` | 701,599 | 701,599 | str | str | yes |
| `rsi_14_slope_5` | 701,599 | 701,599 | float32 | float32 | yes |
| `bb_width_5` | 701,599 | 701,599 | float32 | float32 | yes |
| `bb_width_10` | 701,599 | 701,599 | float32 | float32 | yes |
| `bb_width_100` | 701,599 | 701,599 | float32 | float32 | yes |
| `adx_5` | 701,599 | 701,599 | float32 | float32 | yes |
| `adx_20` | 701,599 | 701,599 | float32 | float32 | yes |
| `adx_100` | 701,599 | 701,599 | float64 | float64 | yes |
| `di_spread_100` | 701,599 | 701,599 | float32 | float32 | yes |
| `obv_zscore_20` | 701,599 | 701,599 | float32 | float32 | yes |
| `hurst_20` | 701,599 | 701,599 | float32 | float32 | yes |
| `hurst_50` | 701,599 | 701,599 | float32 | float32 | yes |
| `hurst_100` | 701,599 | 701,599 | float32 | float32 | yes |
| `frac_diff_close` | 701,599 | 701,599 | float32 | float32 | yes |
| `entropy_10` | 701,599 | 701,599 | float32 | float32 | yes |
| `entropy_20` | 701,599 | 701,599 | float32 | float32 | yes |
| `kama_er_5` | 701,599 | 701,599 | float32 | float32 | yes |
| `kama_er_10` | 701,599 | 701,599 | float32 | float32 | yes |
| `kama_er_20` | 701,599 | 701,599 | float32 | float32 | yes |
| `kama_er_50` | 701,599 | 701,599 | float32 | float32 | yes |
| `kama_er_100` | 701,599 | 701,599 | float32 | float32 | yes |
| `vwap_zscore_5` | 701,599 | 701,599 | float32 | float32 | yes |
| `vwap_zscore_100` | 701,599 | 701,599 | float32 | float32 | yes |
| `amihud_5` | 701,599 | 701,599 | float32 | float32 | yes |
| `amihud_100` | 701,599 | 701,599 | float64 | float64 | yes |
| `yangzhang_5` | 701,599 | 701,599 | float32 | float32 | yes |
| `yangzhang_10` | 701,599 | 701,599 | float32 | float32 | yes |
| `yangzhang_20` | 701,599 | 701,599 | float32 | float32 | yes |
| `yangzhang_50` | 701,599 | 701,599 | float32 | float32 | yes |
| `yangzhang_100` | 701,599 | 701,599 | float32 | float32 | yes |
| `range_width_f3` | 701,599 | 701,599 | float32 | float32 | yes |
| `range_width_f6` | 701,599 | 701,599 | float32 | float32 | yes |
| `donchian_break_f6` | 701,599 | 701,599 | float32 | float32 | yes |
| `range_width_f9` | 701,599 | 701,599 | float32 | float32 | yes |
| `donchian_break_f15` | 701,599 | 701,599 | float32 | float32 | yes |
| `range_width_f39` | 701,599 | 701,599 | float32 | float32 | yes |
| `range_width_f102` | 701,599 | 701,599 | float32 | float32 | yes |
| `range_compression_f6_39` | 701,599 | 701,599 | float32 | float32 | yes |
| `range_compression_f15_102` | 701,599 | 701,599 | float32 | float32 | yes |
| `pct_from_high_f102` | 701,599 | 701,599 | float32 | float32 | yes |
| `pct_from_low_f102` | 701,599 | 701,599 | float32 | float32 | yes |
| `fib_dist_f39` | 701,599 | 701,599 | float32 | float32 | yes |
| `gap_z` | 701,599 | 701,599 | float32 | float32 | yes |
| `rsi_14_slope_5_cs_pct` | 701,599 | 701,599 | float32 | float32 | yes |
| `bb_width_5_cs_pct` | 701,599 | 701,599 | float32 | float32 | yes |
| `bb_width_10_cs_pct` | 701,599 | 701,599 | float32 | float32 | yes |
| `bb_width_100_cs_pct` | 701,599 | 701,599 | float32 | float32 | yes |
| `adx_5_cs_pct` | 701,599 | 701,599 | float32 | float32 | yes |
| `adx_20_cs_pct` | 701,599 | 701,599 | float32 | float32 | yes |
| `adx_100_cs_pct` | 701,599 | 701,599 | float32 | float32 | yes |
| `di_spread_100_cs_pct` | 701,599 | 701,599 | float32 | float32 | yes |
| `obv_zscore_20_cs_pct` | 701,599 | 701,599 | float32 | float32 | yes |
| `hurst_20_cs_pct` | 701,599 | 701,599 | float32 | float32 | yes |
| `hurst_50_cs_pct` | 701,599 | 701,599 | float32 | float32 | yes |
| `hurst_100_cs_pct` | 701,599 | 701,599 | float32 | float32 | yes |
| `frac_diff_close_cs_pct` | 701,599 | 701,599 | float32 | float32 | yes |
| `entropy_10_cs_pct` | 701,599 | 701,599 | float32 | float32 | yes |
| `entropy_20_cs_pct` | 701,599 | 701,599 | float32 | float32 | yes |
| `kama_er_5_cs_pct` | 701,599 | 701,599 | float32 | float32 | yes |
| `kama_er_10_cs_pct` | 701,599 | 701,599 | float32 | float32 | yes |
| `kama_er_20_cs_pct` | 701,599 | 701,599 | float32 | float32 | yes |
| `kama_er_50_cs_pct` | 701,599 | 701,599 | float32 | float32 | yes |
| `kama_er_100_cs_pct` | 701,599 | 701,599 | float32 | float32 | yes |
| `vwap_zscore_5_cs_pct` | 701,599 | 701,599 | float32 | float32 | yes |
| `vwap_zscore_100_cs_pct` | 701,599 | 701,599 | float32 | float32 | yes |
| `amihud_5_cs_pct` | 701,599 | 701,599 | float32 | float32 | yes |
| `amihud_100_cs_pct` | 701,599 | 701,599 | float32 | float32 | yes |
| `yangzhang_5_cs_pct` | 701,599 | 701,599 | float32 | float32 | yes |
| `yangzhang_10_cs_pct` | 701,599 | 701,599 | float32 | float32 | yes |
| `yangzhang_20_cs_pct` | 701,599 | 701,599 | float32 | float32 | yes |
| `yangzhang_50_cs_pct` | 701,599 | 701,599 | float32 | float32 | yes |
| `yangzhang_100_cs_pct` | 701,599 | 701,599 | float32 | float32 | yes |
| `range_width_f3_cs_pct` | 701,599 | 701,599 | float32 | float32 | yes |
| `range_width_f6_cs_pct` | 701,599 | 701,599 | float32 | float32 | yes |
| `donchian_break_f6_cs_pct` | 701,599 | 701,599 | float32 | float32 | yes |
| `range_width_f9_cs_pct` | 701,599 | 701,599 | float32 | float32 | yes |
| `donchian_break_f15_cs_pct` | 701,599 | 701,599 | float32 | float32 | yes |
| `range_width_f39_cs_pct` | 701,599 | 701,599 | float32 | float32 | yes |
| `range_width_f102_cs_pct` | 701,599 | 701,599 | float32 | float32 | yes |
| `range_compression_f6_39_cs_pct` | 701,599 | 701,599 | float32 | float32 | yes |
| `range_compression_f15_102_cs_pct` | 701,599 | 701,599 | float32 | float32 | yes |
| `pct_from_high_f102_cs_pct` | 701,599 | 701,599 | float32 | float32 | yes |
| `pct_from_low_f102_cs_pct` | 701,599 | 701,599 | float32 | float32 | yes |
| `fib_dist_f39_cs_pct` | 701,599 | 701,599 | float32 | float32 | yes |
| `gap_z_cs_pct` | 701,599 | 701,599 | float32 | float32 | yes |
