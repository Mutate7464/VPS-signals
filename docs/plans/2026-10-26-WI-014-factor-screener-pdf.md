# WI-014 Plan — E5 factor screener and PDF

## GOAL
One command produces the validated E5-factor top-N daily shortlist CSV and research tearsheet PDF for USD then CAD (or one selected market), without touching frozen artifacts.

## CONSTRAINTS
- Trace to G-001; follow `src/market_cli.py` routing: default USD→CAD, reject invalid markets before writes, and keep every output market-suffixed.
- Use only existing E5 factors; rank by `mom_12_1` descending, show all five factors (`mom_12_1`, `rev_1m`, `vol_20`, `amihud_20`, `log_dollar_vol_20`); no composite, modeling, trade instructions, or research claims.
- Default top-N=10 and latest available feature date per market; support `--top-n`, `--market`, `--date`, and non-writing `--dry-run`.
- Read `data/features/features_{market}.parquet` with bounded memory: resolve latest row per symbol without materializing an all-ticker full-history DataFrame. Cast newly calculated feature DataFrames to `float32` immediately; `n_jobs<=2`.
- New outputs only: `reports/wi014_shortlist_{market}_{topN}.csv` and `reports/screener_factor_{market}_{YYYYMMDD}.pdf`. Keep `src/pdf_compiler.py`, legacy `reports/screener_{CAD,USD}_20261021.pdf`, and all frozen WI-009/011/012, diagnostic, and sprint artifacts read-only.
- PDF uses Agg; render pages in batches of 10 and call `matplotlib.pyplot.close('all')` plus `gc.collect()` after each batch. No secrets, live trading, or auto-execution.
- Human gate remains after execution; no auto-publish/distribution.

## STEPS
1. **Implement latest-date E5 shortlist generation** in `scripts/wi014_screener.py`, using shared market selection from `src/market_cli.py`. Resolve market/date/top-N before writes; select each symbol's latest eligible feature row, rank eligible rows by `mom_12_1` descending, and write only the suffixed CSV with rank, symbol, five factor values, and scoring date. Add focused generator/schema and invalid-market-before-write tests.
   - **Acceptance:** default selection is USD then CAD; explicit USD/CAD selects one; invalid market writes nothing; CSV schema and latest-date/ranking behavior match the contract; output paths are suffixed.
   - **Verify:** `uv run pytest tests/test_wi014_screener.py -q`
2. **Add the factor tearsheet renderer** in new `src/pdf_compiler_factor.py`; leave `src/pdf_compiler.py` unchanged. Render a summary page (scoring date, eligible universe size, ranking rule, top-N table, E5 single-factor IC table sourced from `reports/wi012_e5_baseline_{market}_h15.md`, and NO_TRADE/cost caveat) followed by one ticker page per shortlist member (candles/BB/trend channel, volume, RSI-14, and five-factor values with same-date cross-section percentiles). Reuse legacy drawing logic where decoupled; copy the required drawing logic if its predictions loader is entangled. Apply the required batch-10/Agg/cleanup lifecycle. Add renderer tests using a small synthetic fixture.
   - **Acceptance:** summary contains the specified metadata and caveat without invented IC values; ticker pages show all required panels/context; a smoke PDF is non-empty; frozen compiler remains unchanged.
   - **Verify:** `uv run pytest tests/test_pdf_compiler_factor.py -q`
3. **Wire end-to-end CLI and dry-run** in `scripts/wi014_screener.py`: one invocation writes CSV and PDF per selected market; PDF names use the market and scoring date; `--dry-run` prints selected markets in execution order and resolved suffixed paths without writing. Add integration tests for default order, single-market behavior, invalid market/no writes, dry-run/no writes, and small-top-N CSV+PDF output.
   - **Acceptance:** `uv run python scripts/wi014_screener.py --dry-run` reports USD then CAD and only suffixed paths; `uv run python scripts/wi014_screener.py --market XYZ` exits non-zero before writes; integration smoke creates both output types for the requested market/top-N.
   - **Verify:** `uv run pytest tests/test_wi014_screener.py tests/test_pdf_compiler_factor.py -q`
4. **Run final end-to-end and regression checks.** Execute the default command against available project data, confirm both markets' top-10 CSVs and non-empty date-stamped PDFs exist, verify no pre-existing report/source artifact changed, and run the complete suite.
   - **Acceptance:** `reports/wi014_shortlist_USD_10.csv`, `reports/wi014_shortlist_CAD_10.csv`, and non-empty `reports/screener_factor_{USD,CAD}_*.pdf` exist; frozen artifacts remain unchanged; full tests pass. Stop at PM verification/admin gate.
   - **Verify:** `uv run python scripts/wi014_screener.py` then `uv run pytest tests/ -q` (also check `git diff --exit-code -- src/pdf_compiler.py reports/screener_CAD_20261021.pdf reports/screener_USD_20261021.pdf`).

## OUT OF SCOPE
- Indicator learning/combination, feature research, new metrics, composites, model training, target/skill-bar changes, and any further research.
- WI-004/WI-005 backlog, portfolio construction, sizing, backtests, cost modeling, trade instructions, order execution, publishing, or PDF distribution.
- Modifying/deleting any frozen artifact or changing the legacy predictions-based compiler/output path.

## EXECUTION LOG
