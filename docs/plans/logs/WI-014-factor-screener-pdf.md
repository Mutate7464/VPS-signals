# WI-014 — factor screener shortlist CSV + tearsheet PDF (both markets)

Log for plan `docs/plans/2026-10-26-WI-014-factor-screener-pdf.md` (brief `docs/workflow/briefs/2026-10-26-WI-014-factor-screener-pdf.md`, b9fa22e).

## STEP REPORT ARTIFACTS

- `reports/wi014_step1_shortlist.md` — step 1 (generator, evidence, DEVIATION on factor source).
- `reports/wi014_step2_renderer.md` — step 2 (renderer, panel/IC/caveat evidence, frozen-compiler hash check).
- `logs/wi014_frozen_hashes_pre.txt` — sha256 of every pre-existing `reports/` file + `src/pdf_compiler.py`, taken before any step ran (step 4 compares against it).

## ROWS

23:25 | step 1 | done | `scripts/wi014_screener.py`: market_cli routing (default USD→CAD, invalid rejected pre-write), batched feature-spine scan (symbol+date only) → scoring date + eligible universe, per-symbol raw-bar factor computation of the five E5 factors, mom_12_1-desc ranking, suffixed CSV with rank/symbol/factors/scoring_date. `tests/test_wi014_screener.py` 14 passed; E5 regression 6 passed; real CAD read-only smoke 2.4 s, 315 eligible. Concern: DEVIATION 1.

23:27 | step 2 | done | New `src/pdf_compiler_factor.py`: summary page (date, eligible size, ranking rule, top-N table, IC table parsed from `reports/wi012_e5_baseline_{market}_h15.md`, NO_TRADE/cost caveat) + per-name page (candles/BB/trend, volume, RSI-14, five factors with same-date percentiles); batch-10 close('all')+gc; legacy drawing helpers imported, `src/pdf_compiler.py` byte-identical. `tests/test_pdf_compiler_factor.py` 15 passed; real CAD top-3 smoke 4 pages 101 KB, peak RSS 290 MB. Concern: none.

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

STATUS: IN PROGRESS (steps 1/4 done)
