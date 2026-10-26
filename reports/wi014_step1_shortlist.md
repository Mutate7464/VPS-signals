# WI-014 step 1 — latest-date E5 shortlist generation (evidence)

Plan `docs/plans/2026-10-26-WI-014-factor-screener-pdf.md` step 1 · goal G-001 · 2026-10-26.

## What was built

- `scripts/wi014_screener.py` (new): market routing via `src/market_cli.py` (default
  BOTH = USD then CAD, explicit single, invalid rejected before any write), scoring-date
  resolution, eligible cross-section, ranking, CSV release.
  - `resolve_market_cross` / `latest_feature_date_per_symbol` / `resolve_scoring_date`
    read `data/features/features_{market}.parquet` **column-pruned and batched**
    (`symbol`+`date` only, 131,072 rows/batch) and keep a per-symbol max-date map —
    no all-ticker full-history frame is ever materialised. About 2.4 s per market.
  - `build_cross_section` streams raw bars one symbol at a time
    (`data/raw_ohlcv/market={market}/symbol={SYM}.parquet`, cut at the scoring date)
    and keeps only the latest complete factor row.
  - `rank_shortlist` ranks by `mom_12_1` descending (ties break on symbol for
    reproducibility) and takes top-N; every row carries `scoring_date`.
  - `write_shortlist_csv` writes `reports/wi014_shortlist_{market}_{topN}.csv`
    (via `market_cli.report_path`, so the path can never be an unsuffixed frozen file).
  - Schema: `rank, symbol, mom_12_1, rev_1m, vol_20, amihud_20, log_dollar_vol_20, scoring_date`.
- `src/factors/e5_baseline.py`: extracted `factor_frame(g)` (the five factor formulas)
  and pointed `build_e5_panel` at it, so the screener ranks on the *same* definition
  the WI-009/WI-012 baseline was validated on instead of a second copy.

## DEVIATION recorded during execution (also in the execution log)

The plan's step 1 says to read the five E5 factor *values* from
`data/features/features_{market}.parquet`. That panel has no such columns — verified:
`pyarrow` schema of `features_USD.parquet`/`features_CAD.parquet` (92 columns) contains
`amihud_20` but **no** `mom_12_1`, `rev_1m`, `vol_20` or `log_dollar_vol_20`, and a scan
of every parquet under `data/` finds no precomputed E5 column anywhere. The panel is
therefore used exactly as specified for the bounded-memory part it can serve (latest row
per symbol → scoring date + eligible universe), and the factor values are computed per
symbol from raw OHLCV with the shared existing definition. No new factor, no composite,
no modeling was introduced.

## Evidence

| # | Command | Result |
| :--- | :--- | :--- |
| 1 | `uv run pytest tests/test_wi014_screener.py -q` | **14 passed** in 0.72 s (synthetic two-market fixture: freshness spine, stale/missing/short-history exclusion, ranking, schema, suffixed paths, invalid market writes nothing) |
| 2 | `uv run pytest tests/test_e5_baseline_horizon_nans.py tests/test_e5_split_no_leak.py -q` | **6 passed** in 28.28 s (E5 refactor regression: panel unchanged, 772,527 CAD rows) |
| 3 | one-off bit-exactness check, 40 CAD symbols, `factor_frame` vs the pre-refactor inline formulas | `assert_frame_equal(check_exact=True)` on all 40 → identical |
| 4 | read-only real-data smoke, CAD `generate_shortlist(top_n=5)` (no writes) | `scoring_date=2026-09-22 eligible=315 stale=0 skipped={'no_raw_file': 0, 'stale_bar': 0, 'short_history': 2, 'nan_factor': 0} cross_rows=313 elapsed=2.4s`; top-5 = MU, FDY, ARG, MAU, AMD (mom_12_1 descending) |

Test 1 covers the step-1 acceptance bullets: default selection is USD then CAD
(`resolve_markets(None)`), explicit market selects one, invalid market exits non-zero
writing nothing, CSV schema/ranking/latest-date behaviour, and suffixed output paths.

## Notes / concerns

- Bounded memory holds: the feature spine is reduced per batch and only a
  `{symbol: date}` map survives; raw bars are read one symbol at a time.
- `--date` is point-in-time: raw bars are cut at the scoring date, so a pinned older
  date cannot see later bars (test `test_date_flag_pins_the_scoring_date`).
- No PDF is produced yet (step 2/3), no `--dry-run` flag yet (step 3), and no run has
  written into `reports/` (real-data smoke was read-only).
