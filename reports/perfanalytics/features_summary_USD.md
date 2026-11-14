# WI-015 — enriched feature panel (USD)

- Generated (UTC): 2026-10-28T04:18:04Z
- Dataset: `data/perfanalytics/features_USD/` · 533 symbols · 2,128,588 rows
- Fib grid: 3, 5, 8, 13, 21, 34, 55, 89, 144, 233 · 15 families · 150 columns (all float32)
- Warm-up: NaN until the full window is available; no partial windows.
- `hurst_<W>` is all-NaN for W < 12 (R/S estimator floor).

## Family × window columns

| Family | Columns |
| :--- | :--- |
| `rsi` | `rsi_3`, `rsi_5`, `rsi_8`, `rsi_13`, `rsi_21`, `rsi_34`, `rsi_55`, `rsi_89`, `rsi_144`, `rsi_233` |
| `bb_pct_b` | `bb_pct_b_3`, `bb_pct_b_5`, `bb_pct_b_8`, `bb_pct_b_13`, `bb_pct_b_21`, `bb_pct_b_34`, `bb_pct_b_55`, `bb_pct_b_89`, `bb_pct_b_144`, `bb_pct_b_233` |
| `bb_width` | `bb_width_3`, `bb_width_5`, `bb_width_8`, `bb_width_13`, `bb_width_21`, `bb_width_34`, `bb_width_55`, `bb_width_89`, `bb_width_144`, `bb_width_233` |
| `adx` | `adx_3`, `adx_5`, `adx_8`, `adx_13`, `adx_21`, `adx_34`, `adx_55`, `adx_89`, `adx_144`, `adx_233` |
| `di_spread` | `di_spread_3`, `di_spread_5`, `di_spread_8`, `di_spread_13`, `di_spread_21`, `di_spread_34`, `di_spread_55`, `di_spread_89`, `di_spread_144`, `di_spread_233` |
| `atr_pct` | `atr_pct_3`, `atr_pct_5`, `atr_pct_8`, `atr_pct_13`, `atr_pct_21`, `atr_pct_34`, `atr_pct_55`, `atr_pct_89`, `atr_pct_144`, `atr_pct_233` |
| `obv_zscore` | `obv_zscore_3`, `obv_zscore_5`, `obv_zscore_8`, `obv_zscore_13`, `obv_zscore_21`, `obv_zscore_34`, `obv_zscore_55`, `obv_zscore_89`, `obv_zscore_144`, `obv_zscore_233` |
| `hurst` | `hurst_3`, `hurst_5`, `hurst_8`, `hurst_13`, `hurst_21`, `hurst_34`, `hurst_55`, `hurst_89`, `hurst_144`, `hurst_233` |
| `kama_er` | `kama_er_3`, `kama_er_5`, `kama_er_8`, `kama_er_13`, `kama_er_21`, `kama_er_34`, `kama_er_55`, `kama_er_89`, `kama_er_144`, `kama_er_233` |
| `vwap_zscore` | `vwap_zscore_3`, `vwap_zscore_5`, `vwap_zscore_8`, `vwap_zscore_13`, `vwap_zscore_21`, `vwap_zscore_34`, `vwap_zscore_55`, `vwap_zscore_89`, `vwap_zscore_144`, `vwap_zscore_233` |
| `amihud` | `amihud_3`, `amihud_5`, `amihud_8`, `amihud_13`, `amihud_21`, `amihud_34`, `amihud_55`, `amihud_89`, `amihud_144`, `amihud_233` |
| `yangzhang` | `yangzhang_3`, `yangzhang_5`, `yangzhang_8`, `yangzhang_13`, `yangzhang_21`, `yangzhang_34`, `yangzhang_55`, `yangzhang_89`, `yangzhang_144`, `yangzhang_233` |
| `range_pos_f` | `range_pos_f3`, `range_pos_f5`, `range_pos_f8`, `range_pos_f13`, `range_pos_f21`, `range_pos_f34`, `range_pos_f55`, `range_pos_f89`, `range_pos_f144`, `range_pos_f233` |
| `range_width_f` | `range_width_f3`, `range_width_f5`, `range_width_f8`, `range_width_f13`, `range_width_f21`, `range_width_f34`, `range_width_f55`, `range_width_f89`, `range_width_f144`, `range_width_f233` |
| `donchian_break_f` | `donchian_break_f3`, `donchian_break_f5`, `donchian_break_f8`, `donchian_break_f13`, `donchian_break_f21`, `donchian_break_f34`, `donchian_break_f55`, `donchian_break_f89`, `donchian_break_f144`, `donchian_break_f233` |

## Per-symbol history coverage (symbols with >= W bars)

| Window | Symbols with full window |
| ---: | ---: |
| 3 | 533 |
| 5 | 533 |
| 8 | 533 |
| 13 | 533 |
| 21 | 533 |
| 34 | 533 |
| 55 | 533 |
| 89 | 533 |
| 144 | 533 |
| 233 | 533 |
