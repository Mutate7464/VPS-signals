STATUS: DONE — steps 1–5 complete (PM-set; Build exited 0 without writing step-4/5 rows or final STATUS). Steps 4–5 evidence: `logs/wi013_step4.out` (probe/train/eval CAD all exit 0; suffixed regression/summary/shortlist non-empty), `logs/wi013_step5.out` (preflight BOTH → `wi011_preflight_USD.md`+`_CAD.md`; full suite **360 passed in 7:38**). PM restore: regenerated `wi009c_{regression,summary}_CAD.json` (frozen, suffixed) reverted via `git checkout --` — timestamp + dropped robustness block only; 58-file frozen-hash baseline otherwise intact (`logs/wi013_frozen_hashes.txt`, PM re-verified). PM re-ran targeted `tests/test_wi013_*.py`: 126 passed.
# WI-013 execution log — pipeline hygiene + two-market parametrization

Step report artifacts (plan names only one; step evidence lives here):
- `logs/wi013_frozen_hashes.txt` — sha256 baseline of every pre-existing `reports/` file (step 0).
- `logs/wi013_step1.out` … `logs/wi013_step5.out` — full verify-command output per step.
- `reports/wi013_rebuild_verification.md` — F-4 old/new per-market equality table (step 3).

## ROWS

16:39 | step 1 | done | Added `src/market_cli.py` (default BOTH = USD then CAD; explicit single; invalid rejected before any write; suffix/idempotent/override guards). Refactored 6 `wi011_*` scripts + `src/wi011` (dropped `MARKET = "CAD"`, market is a parameter; selection JSON now `wi011_selected_indicators_{market}.json`). New `tests/test_wi013_pipeline_hygiene.py`. Verify `-k 'market_cli or wi011_report_paths'` 41 passed, wi011 conditions 15 passed (logs/wi013_step1.out). Smoke: preflight CAD wrote `reports/wi011_preflight_CAD.md`. Concern: none.

16:43 | step 2 | done | Market CLI + suffixed writers applied to probe/train/evaluate_wi009c, wi009b_launch, rank_assets, train_contrastive, check_wi009c_inputs (F-5: `wi009c_regression.md`/`wi009c_summary.md`/launcher log+pid now suffixed). F-2 fixed in `write_report` (names `market`). Verify `-k 'market_cli or report_paths or e5_report_market'` 102 passed; targeted 81 passed (logs/wi013_step2.out). Concern: DEVIATION — see below.

16:50 | step 3 | done | Added bounded-memory `scripts/rebuild_wi013_metadata.py` (catalog + `features_{market}.parquet` streaming; identical 60-row Z-score + date-group `rank(pct=True)`; per-column `assert_frame_equal(check_dtype=True, check_exact=True)`) + `tests/test_wi013_metadata.py`. F-4 SWAPPED: USD 71→67 cols, CAD 91→87, rows unchanged, all surviving columns exact-equal, `y_*` labels gone, backups `features_*_metadata_pre_wi013.parquet` (original hashes) retained. Verify both commands exit 0 (logs/wi013_step3.out); swap evidence `logs/wi013_step3_swap_report.md` + `reports/wi013_rebuild_verification.md`. Concern: peak RSS 936 MB / 42 s for both markets (under 8 GB, no swap; percentile arrays are the resident cost).

## DEVIATIONS

1. **`scripts/check_wi009c_inputs.py` — declared expectations are now CAD-only (step 2).**
   The step-0 checker asserted `EXPECTED_ROWS = 701_599` and `y_20d_stay = 44.8% ± 0.5pp`
   unconditionally. Those are CAD artifacts; a default BOTH run failed on USD
   (1,240,275 rows; stay rate 43.06%). WI-013 asks for a working both-market default, so
   the checker now reads `EXPECTED_ROWS_BY_MARKET` / `STAY_BASE_RATE_BY_MARKET`
   (`{"CAD": ...}` — CAD keeps the exact frozen assertions, verified exit 0) and for a
   market with no declared baseline it **reports** the observed value and says no baseline
   was declared, instead of asserting a number no plan ever agreed to. No threshold was
   invented for USD; no CAD assertion was weakened. Flagged for the PM: if a USD Step-0
   baseline is wanted, it needs an explicit plan decision.
2. **`src/factors/e5_baseline.py` CLI default left at `CAD` (step 2).** Plan step 2 scopes
   this file to the F-2 `write_report` fix ("retain its already suffixed report path"); its
   CLI default was therefore not converted to BOTH. Its report path and body are both
   market-correct. Flagged for the PM in case the intent was a BOTH default here too.
