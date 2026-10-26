# WI-014 step 3 — end-to-end CLI, dry-run and integration (evidence)

Plan `docs/plans/2026-10-26-WI-014-factor-screener-pdf.md` step 3 · goal G-001 · 2026-10-26.

## What was wired

`scripts/wi014_screener.py` now produces **both** outputs in one invocation, per market:

1. `run_one_market` resolves the cross-section *and* the published IC table first
   (`parse_e5_ic_table(ic_report_path(market, reports_dir=REPORTS))`), so every failure
   happens before the first write — a market either writes its CSV + PDF or writes nothing.
2. It writes `reports/wi014_shortlist_{market}_{topN}.csv`, then renders
   `reports/screener_factor_{market}_{YYYYMMDD}.pdf` (market + scoring date in the name)
   and prints both paths with byte sizes, page count and the tickers that got a page.
3. `--dry-run` prints the plan line, then one line per market in execution order with the
   resolved scoring date and the resolved **suffixed** CSV/PDF paths, and writes nothing
   (`dry_run_lines`; it only reads the panel's date column, column-pruned and batched).
   A dry run returns non-zero if a market cannot be resolved.
4. `RANK_FACTOR`/`RANKING_RULE` now come from `src/pdf_compiler_factor.py`, so the rule
   printed by the CLI/page cannot drift from the rule the CSV was ranked by.

## Evidence

| # | Command | Result |
| :--- | :--- | :--- |
| 1 | `uv run pytest tests/test_wi014_screener.py tests/test_pdf_compiler_factor.py -q` | **36 passed** in 11.94 s |
| 2 | `uv run python scripts/wi014_screener.py --dry-run` (real data, `logs/wi014_step3_cli.out`) | exit 0; `dry-run 1/2 market=USD scoring_date=2026-09-23 csv=reports/wi014_shortlist_USD_10.csv pdf=reports/screener_factor_USD_20260923.pdf (nothing written)` then `dry-run 2/2 market=CAD scoring_date=2026-09-22 csv=reports/wi014_shortlist_CAD_10.csv pdf=reports/screener_factor_CAD_20260922.pdf` |
| 3 | `uv run python scripts/wi014_screener.py --market XYZ` (and with `--dry-run`) | exit 2, `invalid market 'XYZ': choose USD/CAD…` on stderr, **no file written** |
| 4 | `git status --porcelain reports/` after 2 and 3 | no new or modified report file (dry run / rejection wrote nothing) |

## Acceptance mapping

- *`--dry-run` reports USD then CAD and only suffixed paths* — evidence row 2; the test
  `test_dry_run_prints_both_markets_in_order_and_writes_nothing` also asserts no unsuffixed
  `wi014_shortlist_`/`screener_factor_` token appears in any printed line.
- *`--market XYZ` exits non-zero before writes* — evidence row 3; tests
  `test_invalid_market_writes_nothing` and `test_invalid_market_dry_run_writes_nothing`
  assert the reports dir holds no run output.
- *Integration smoke creates both output types for the requested market/top-N* —
  `test_default_run_writes_csv_and_pdf_for_both_markets` (2 CSVs + 2 non-empty `%PDF`
  files, 4/3 pages) and `test_small_top_n_writes_both_output_types` (top-n 2).
- Also covered: `test_run_fails_before_writing_when_the_ic_report_is_missing` (no CSV
  without the published IC table) and `test_ranking_rule_comes_from_the_renderer`.

## Notes / concerns

- Integration tests run on the synthetic two-market fixture with a per-test `reports/`
  seeded only with copies of the frozen IC reports, so every other file in that directory
  is the run's own output and "wrote nothing" is a real assertion, not a guess.
- Step 4 is the first real-data write into `reports/` (the two top-10 CSVs and the two
  date-stamped PDFs).
