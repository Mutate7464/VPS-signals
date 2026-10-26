# WI-014 step 2 — factor tearsheet renderer (evidence)

Plan `docs/plans/2026-10-26-WI-014-factor-screener-pdf.md` step 2 · goal G-001 · 2026-10-26.

## What was built

- `src/pdf_compiler_factor.py` (new): the E5-factor tearsheet renderer.
  - **Summary page** — title, scoring date, eligible universe size (and the stale
    count), the universe after the factor guard with the skipped-reason counts, the
    ranking rule, the top-N table (`#, symbol, mom_12_1, rev_1m, vol_20, amihud_20,
    log_dollar_vol_20`), the E5 single-factor IC table, and the NO_TRADE/cost caveat.
  - **Ticker page** (one per shortlist member) — panel 1 candles + 20d Bollinger Bands
    + 20d OLS trend channel, panel 2 volume + volume SMA20, panel 3 RSI-14 with 30/70
    levels, panel 4 all five E5 factor values with their same-date cross-section
    percentiles (bar + label), plus a one-line research/NO_TRADE footer.
  - **IC numbers are read, never invented** — `parse_e5_ic_table` parses the published
    `reports/wi012_e5_baseline_{market}_h15.md` single-factor section and raises if the
    report is missing or its factor set is not exactly the five E5 factors.
  - **Same-date percentiles** — `cross_section_percentiles` (`rank(pct=True)` over the
    scoring date's eligible rows, the WI-013 convention); descriptive context only.
  - **Batch lifecycle** — Agg backend set at import; each figure saved and closed
    immediately; `plt.close('all')` + `gc.collect()` after every batch of 10 pages
    (`reclaim_memory`), and once more at the end.
  - **Reuse, not copy** — `_candles`, `_trend_channel`, `_style_x`, `UP_COLOR`,
    `DOWN_COLOR`, `CHART_LOOKBACK`, `BATCH_GC_SIZE` are imported from the frozen
    `src/pdf_compiler.py` (they are decoupled from its predictions loader); its
    predictions/`draw_ticker_page` path is not reused and that file is byte-identical.

## Evidence

| # | Command | Result |
| :--- | :--- | :--- |
| 1 | `uv run pytest tests/test_pdf_compiler_factor.py -q` | **15 passed** in 4.76 s |
| 2 | read-only real-data smoke: real CAD top-3 → PDF into `/tmp/opencode` (no repo writes) | `bytes=101,537 pages=4 rendered=['MU','FDY','ARG'] skipped={} elapsed=3.9s peak_rss_mb=290` (1 summary + 3 ticker pages, `%PDF` header) |
| 3 | `git diff --stat -- src/pdf_compiler.py` | empty (frozen Sprint-5 compiler untouched) |

## Acceptance mapping

- *Summary contains the specified metadata and caveat without invented IC values* —
  `test_summary_content_has_required_metadata_and_caveat` (content) and
  `test_summary_page_actually_draws_the_metadata_caveat_and_ic_table` (the drawn figure
  carries scoring date, eligible universe, ranking rule, caveat and the published
  `+0.0209` mom IC), plus the parse tests (missing/drifted report → error, multivariate
  rows excluded).
- *Ticker pages show all required panels/context* —
  `test_ticker_page_actually_draws_all_panels_and_factor_context` (4 panels; all five
  factor names with `pct=` labels on the factor panel) and `test_ticker_content_...`.
- *A smoke PDF is non-empty* — evidence row 2 (101 KB, 4 pages, `%PDF`) and
  `test_render_tearsheet_writes_summary_plus_one_page_per_name` (`pages == 1 + N`).
- *Frozen compiler remains unchanged* —
  `test_rendering_leaves_the_frozen_compiler_and_existing_files_untouched` (sha256 of
  `src/pdf_compiler.py` and of a pre-existing legacy-named PDF in the reports dir both
  unchanged; exactly one new file written).

## Notes / concerns

- Ticker pages use a point-in-time 120-bar window cut at the scoring date
  (`test_raw_window_stops_at_the_scoring_date`), so an older-date tearsheet cannot chart
  later bars.
- `MIN_CHART_BARS = 30`: a name with no/incomplete raw window is recorded in
  `TearsheetResult.skipped_tickers` and gets no page rather than an empty chart.
- Peak RSS 290 MB for the render (well inside the 8 GB / no-swap host limit); page text
  is drawn as matplotlib vector text, so the PDF has no searchable-text layer to grep —
  content is verified from the drawn figure artists instead.
