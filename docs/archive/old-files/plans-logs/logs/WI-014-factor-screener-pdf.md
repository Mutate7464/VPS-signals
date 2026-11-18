# WI-014 — factor screener shortlist CSV + tearsheet PDF (both markets)

Log for plan `docs/plans/2026-10-26-WI-014-factor-screener-pdf.md` (brief `docs/workflow/briefs/2026-10-26-WI-014-factor-screener-pdf.md`, b9fa22e).

## STEP REPORT ARTIFACTS

- `reports/wi014_step1_shortlist.md` — step 1 (generator, evidence, DEVIATION on factor source).
- `reports/wi014_step2_renderer.md` — step 2 (renderer, panel/IC/caveat evidence, frozen-compiler hash check).
- `reports/wi014_step3_cli.md` — step 3 (CLI wiring, dry-run/no-write evidence, integration tests).
- `logs/wi014_step3_cli.out` — real-data `--dry-run` + invalid-market output (steps 2–3 verifies).
- `reports/wi014_step4_e2e.md` — step 4 (real end-to-end run, artifact table, frozen-hash comparison, full-suite marker).
- `logs/wi014_frozen_hashes_pre.txt` — sha256 of every pre-existing `reports/` file + `src/pdf_compiler.py`, taken before any step ran (step 4 compares against it).
- `logs/wi014_e2e_run.out` — default BOTH run, `/usr/bin/time -v` (25.78 s, peak RSS 342 MB, `EXIT:0`).
- `logs/wi014_full_suite.out` — full suite detached log with the polled `EXIT:0` marker.

## ROWS

23:25 | step 1 | done | `scripts/wi014_screener.py`: market_cli routing (default USD→CAD, invalid rejected pre-write), batched feature-spine scan (symbol+date only) → scoring date + eligible universe, per-symbol raw-bar factor computation of the five E5 factors, mom_12_1-desc ranking, suffixed CSV with rank/symbol/factors/scoring_date. `tests/test_wi014_screener.py` 14 passed; E5 regression 6 passed; real CAD read-only smoke 2.4 s, 315 eligible. Concern: DEVIATION 1.

23:27 | step 2 | done | New `src/pdf_compiler_factor.py`: summary page (date, eligible size, ranking rule, top-N table, IC table parsed from `reports/wi012_e5_baseline_{market}_h15.md`, NO_TRADE/cost caveat) + per-name page (candles/BB/trend, volume, RSI-14, five factors with same-date percentiles); batch-10 close('all')+gc; legacy drawing helpers imported, `src/pdf_compiler.py` byte-identical. `tests/test_pdf_compiler_factor.py` 15 passed; real CAD top-3 smoke 4 pages 101 KB, peak RSS 290 MB. Concern: none.

23:29 | step 3 | done | CLI wired end-to-end: one invocation writes CSV then PDF per market; all resolvable failures (cross-section + published IC table) happen before the first write; `--dry-run` prints USD→CAD with resolved scoring dates and suffixed CSV/PDF paths and writes nothing; RANK_FACTOR/RANKING_RULE now imported from the renderer. Verify: 36 passed; real `--dry-run` exit 0 (logs/wi014_step3_cli.out), `--market XYZ` exit 2 with no writes; `git status reports/` clean. Concern: none.

23:41 | step 4 | done | Default run (`uv run python scripts/wi014_screener.py`, detached `logs/wi014_e2e_run.out`) exit 0 in 25.8 s, peak RSS 342 MB: USD scoring_date=2026-09-23 (508 eligible, 10 rows, 11-page PDF 259 KB) then CAD 2026-09-22 (315 eligible, 10 rows, 11-page PDF 256 KB); all top-10 names charted. Frozen check: sha256 of all pre-existing `reports/` files + `src/pdf_compiler.py` unchanged (0 diffs, compared pre-run and post-suite); `git status reports/` shows only the two new CSVs (new PDFs are covered by the repo's `reports/*.pdf` ignore rule, like the legacy demo PDFs). Full suite detached `logs/wi014_full_suite.out`: 396 passed (360 + 36 new), EXIT:0. Stop at PM verification/admin gate. Concern: none.

## DEVIATIONS

1. **E5 factor values are computed from raw OHLCV, not read from `data/features/{features}_{market}.parquet` (step 1).**
   The plan says to read the five E5 factors from the feature panel. That panel has no
   such columns: `features_{USD,CAD}.parquet` (92 columns) carries `amihud_20` but no
   `mom_12_1`/`rev_1m`/`vol_20`/`log_dollar_vol_20`, and no parquet under `data/` holds a
   precomputed E5 factor (scanned all of them). So the panel is used for exactly the
   bounded-memory job it can do — per-symbol latest feature row → scoring date + eligible
   universe — and factor values come from the existing E5 definition applied to that
   symbol's raw bars up to the scoring date. To avoid a second copy of the formulas,
   `src/factors/e5_baseline.py` gained `factor_frame(g)` (extraction only; `build_e5_panel`
   now calls it) and a 40-symbol `check_exact=True` comparison plus the two E5 regression
   tests confirm the panel is unchanged. No new factor/composite/model. Step 1 is safe to
   continue; flagging for PM in case the intent was different (e.g. wanting the E5 factors
   materialised into the feature panel first — that would be new feature work, out of scope).

STATUS: DONE | evidence: `uv run pytest tests/test_wi014_screener.py tests/test_pdf_compiler_factor.py -q` → 36 passed; `uv run pytest tests/ -q` → 396 passed, EXIT:0 (detached `logs/wi014_full_suite.out`); `uv run python scripts/wi014_screener.py` → exit 0 in 25.8 s, peak RSS 342 MB, producing `reports/wi014_shortlist_USD_10.csv` + `reports/wi014_shortlist_CAD_10.csv` (10 rows each) and `reports/screener_factor_USD_20260923.pdf` + `reports/screener_factor_CAD_20260922.pdf` (11 pages, non-empty, `%PDF`) — `logs/wi014_e2e_run.out`; frozen check: sha256 of all 66 pre-existing `reports/` files + `src/pdf_compiler.py` identical before run and after suite (0 diffs), `git diff --exit-code -- src/pdf_compiler.py reports/screener_CAD_20261021.pdf reports/screener_USD_20261021.pdf` exit 0. Plan step 4 stops at PM verification / admin gate (human gate open; BOARD.md untouched by Build).
