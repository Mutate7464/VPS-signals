# WI-013 — Pipeline hygiene + two-market parametrization

## GOAL
All listed report-writing stages run USD then CAD by default or one market via `--market`, never overwrite unsuffixed frozen reports, and both metadata panels are rebuilt without labels and verified unchanged on surviving columns.

## CONSTRAINTS
- Follow `docs/workflow/briefs/2026-10-26-WI-013-pipeline-hygiene.md`; F-1 is done and out of scope.
- Never rename, delete, or rewrite existing unsuffixed `reports/wi009*`, `reports/wi011_*`, `reports/diag_*`, or sprint reports. New outputs are market-suffixed. Do not commit regenerated frozen reports; stage files by explicit path only.
- No factor/target/split/skill-bar changes. No secrets or live trading. `n_jobs=2`; cast calculated feature frames to `float32` immediately; bounded memory via `pyarrow.dataset`/sequential symbol processing, never an all-ticker uncompressed frame.
- Process USD then CAD sequentially for implicit BOTH; `--market USD|CAD` runs only that market. Fail before writing on invalid values. The WI-013 F-4 swap is gated on exact pre-swap verification; any mismatch means no swap and stop/escalate.

## STEPS
1. Add a shared market-selection/report-path helper (e.g. `src/market_cli.py`) and refactor the six `scripts/wi011_*.py` entry points plus `src/wi011` to accept the selected market rather than import/use `MARKET = "CAD"`. The helper must implement default BOTH in USD-then-CAD order and explicit single-market selection. Thread market through all WI-011 feature/target inputs and generated reports/sidecars; in `scripts/wi011_preflight.py`, print a plan line naming both markets for default invocation. Suffix every output, including definitions, association selection JSON, tradeable rules, and reports.
   - Acceptance: default invocation selects exactly USD then CAD; explicit USD/CAD selects only itself; invalid market is rejected; no WI-011 writer resolves an unsuffixed output.
   - Verify: `uv run pytest tests/test_wi013_pipeline_hygiene.py -q -k 'market_cli or wi011_report_paths'`.
2. Apply the same market CLI/default-both behavior and market-specific output routing to `scripts/probe_wi009c.py`, `train_wi009c.py`, `evaluate_wi009c.py`, `wi009b_launch.py`, `rank_assets.py`, `train_contrastive.py`, and `check_wi009c_inputs.py`. Make all writes (reports, JSON/CSV/Parquet, input-check output, launcher PID/sidecar) market-suffixed, and resolve market-specific inputs in the same market context. Any explicit output override must also resolve to a suffixed path or be rejected before writing. Fix `src/factors/e5_baseline.py::write_report` to name its `market` argument instead of hardcoded CAD; retain its already suffixed report path.
   - Acceptance: every listed script has a tested BOTH default, accepts only USD/CAD, and every reachable default/override writer path is market-suffixed; existing unsuffixed artifacts remain untouched.
   - Verify: `uv run pytest tests/test_wi013_pipeline_hygiene.py -q -k 'market_cli or report_paths or e5_report_market'`.
3. Add a bounded-memory `scripts/rebuild_wi013_metadata.py` and regression tests. For each market, reconstruct from `features_{market}.parquet` plus the catalog/source construction used by `src/stat_metadata.py` (surviving features, stationarity flags, 60-row transform and date-group percentile), not the legacy full-history `load_market_frame` path. Write a staging Parquet, remove `y_15d_high`, `y_15d_low`, `y_20d_up`, `y_20d_down`, and assert row count, column order, and every remaining value/dtype exactly equal to the pre-swap panel (`pandas.testing.assert_frame_equal(check_dtype=True, check_exact=True)`). Only after both markets pass, retain pre-swap backups and atomically replace the two panels; write the per-market old/new equality table to `reports/wi013_rebuild_verification.md`. Test both USD/CAD metadata-panel schemas for absence of all `y_*` labels.
   - Acceptance: USD and CAD verification table reports equal row counts and exact equality for every surviving column; backups exist; labels are absent; a mismatch prevents all swaps.
   - Verify: `uv run pytest tests/test_wi013_metadata.py -q` and `uv run python scripts/rebuild_wi013_metadata.py --markets USD CAD`.
4. Backfill the canonical WI-009c CAD regression, summary, and shortlist under suffixed paths using the new market-aware scripts; do not touch the frozen unsuffixed files. Confirm the shared report-path helper covers every writer from steps 1–2 and that no output from a both-market invocation can resolve to an unsuffixed path.
   - Acceptance: the CAD regression/summary/shortlist suffixed files exist and are non-empty; existing frozen report hashes are unchanged; path tests cover every listed writer.
   - Verify: `uv run python scripts/probe_wi009c.py --market CAD && uv run python scripts/train_wi009c.py --market CAD && uv run python scripts/evaluate_wi009c.py --market CAD && test -s reports/wi009c_regression_CAD.md && test -s reports/wi009c_summary_CAD.md && test -s reports/wi009c_shortlist_CAD.csv`.
5. Run final cross-market, regression, and frozen-artifact checks. The default preflight must report BOTH and create separate USD/CAD reports; then run the full test suite and inspect report status against the pre-run frozen set.
   - Acceptance: all new tests and `uv run pytest tests/ -q` pass; default preflight writes `wi011_preflight_USD.md` and `wi011_preflight_CAD.md`; `git status --short reports/` shows no modification to any pre-existing unsuffixed report.
   - Verify: `uv run python scripts/wi011_preflight.py && test -s reports/wi011_preflight_USD.md && test -s reports/wi011_preflight_CAD.md && uv run pytest tests/ -q && git status --short reports/`.

## OUT OF SCOPE
- F-1, P-1 verifier dedupe, P-2 gitignore audit, P-3 doc rotation, WI-004/WI-005, model/target/feature research, USD screener wiring, and any human-gate decision or auto-merge.

## EXECUTION LOG
