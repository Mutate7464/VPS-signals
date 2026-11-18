# WI-015 — Enriched features and run-target alignment

## GOAL
Produce point-in-time T1–T4 run-target datasets and Fibonacci-window enriched feature panels for CAD and USD, plus a held-out per-target alignment matrix (G-PA2, then G-PA1), all as research artifacts.

## CONSTRAINTS
- WI-015 complements WI-014: do not alter its shortlist CSV/PDF, scripts, or shipped artifacts; no trading logic, model training, or automatic order execution.
- Targets evaluate only `[t+1, t+k]`, `k ∈ {15,20}`; every threshold is trailing-only. Assume a qualifying run is a close-to-close rise of at least `2 × ATR(t)` (2× follows the existing target pattern); report low-to-high amplitude only as a diagnostic.
- For T1/T2, examine bottom/peak pairs within each forward window: bottom is a session with the minimum low preceding a later peak; rank pairs by close-to-close return from bottom close to peak close. Keep the best qualifying pair. T1 is its fractional return; T2 is that return divided by elapsed trading sessions (minimum one); if none qualifies, T1/T2/T4 are zero. T4 is 1 iff a qualifying pair exists. T3 is the longest consecutive positive close-to-close streak. Preserve NaN for incomplete forward windows. Record low-to-high return for the selected pair as a diagnostic.
- Fib grid is exactly `3,5,8,13,21,34,55,89,144,233`, over the existing normalized feature families specified below. No partial windows: values are NaN until full history is available.
- `--market {CAD,USD,BOTH}` defaults to BOTH; BOTH processes CAD then USD sequentially. Keep all-ticker uncompressed frames out of memory, cast computed feature frames to `float32` immediately, and use `n_jobs<=2` if parallel work is introduced. No secrets.
- Store datasets as market-suffixed Parquet datasets under `data/perfanalytics/`; write reports only under `reports/perfanalytics/` with market suffixes. Process/write one symbol at a time (or use `pyarrow.dataset`); never retain an all-ticker uncompressed frame. Do not overwrite frozen reports.
- Alignment uses five chronological held-out folds with 20-session embargo (E5 split shape). For each feature and each fold, compute per-date cross-sectional Spearman IC on held-out rows, then its mean over held-out dates. Compute the same E5 five-factor baseline against the same target/horizon and use its best factor's held-out IC sign as the sign reference. For each candidate, resample the paired daily IC series in circular contiguous blocks of 20 dates, with replacement to the original series length, 1,000 times, seed `42`; define the noise margin as the 95th percentile of absolute deviations of bootstrap means from the observed held-out mean. Pass only when the candidate sign matches the baseline and `abs(observed mean) > noise margin`. Report the best family×window per target and horizon with held-out IC, baseline sign, and noise margin.
- Implementation references (only): `docs/tech_approach/perfanalytics/README.md`, `docs/tech_approach/perfanalytics/targets-research.md`, `docs/tech_approach/perfanalytics/features-research.md`, `src/targets.py`, `src/factors/e5_baseline.py`.

## STEPS
1. **Implement T1–T4 labelers and leakage tests.** Add pure per-symbol labelers under `src/perfanalytics/targets/` for both horizons, following `src/targets.py`'s trailing ATR and forward-window alignment; include selected bottom/peak and low-to-high diagnostic outputs. Test shift-1 alignment, incomplete horizons, trailing-threshold behavior, no-run cases, and T3 streaks using synthetic OHLCV.
   - Acceptance: labels are aligned to t, never use data after t to construct the threshold, and match the definitions/NaN policy above.
   - Verify: `uv run pytest tests/perfanalytics/test_targets.py -q`
2. **Build market-specific run-target datasets.** Add a sequential symbol iterator/build entry point in `src/perfanalytics/targets/`; write T1–T4 plus diagnostics to `data/perfanalytics/run_targets_{market}/` as a Parquet dataset. Implement `--market {CAD,USD,BOTH}` (default BOTH), preserving symbols/dates and processing CAD before USD.
   - Acceptance: each requested market produces a readable market-suffixed Parquet dataset with documented schema; execution does not assemble an all-ticker uncompressed frame.
   - Verify: `uv run pytest tests/perfanalytics/test_target_dataset.py -q`
3. **Build the enriched feature panels.** In `src/perfanalytics/features/`, reuse the existing normalized family definitions (`rsi`, `bb_pct_b`, `bb_width`, `adx`, `di_spread`, `atr_pct`, `obv_zscore`, `hurst`, `kama_er`, `vwap_zscore`, `amihud`, `yangzhang`, `range_pos`, `range_width`, `donchian_break`) on the exact fib grid. Check per-symbol history before 144/233 windows; write `data/perfanalytics/features_{market}/` as a Parquet dataset and document its schema.
   - Acceptance: panel has the requested family/window columns (retaining existing `f<W>` naming for range/Donchian families), causal full-window warm-up NaNs, `float32` feature columns, and symbol-sequential bounded-memory construction for both markets.
   - Verify: `uv run pytest tests/perfanalytics/test_features.py -q`
4. **Produce the per-target alignment matrix.** Add `src/perfanalytics/correlation/` analysis using the E5 baseline machinery shape; compare each horizon's target to each available family×window feature on five chronological held-out folds with 20-session embargo. Compute per-date cross-sectional Spearman IC, use the best same-target/horizon E5 factor's held-out IC sign, and apply the seeded 20-session circular block-bootstrap rule above. Aggregate per-symbol contributions without constructing an all-ticker uncompressed frame; write `reports/perfanalytics/alignment_{market}.csv` and `.md`.
   - Acceptance: CAD and USD reports each contain one best family×window result per T1–T4/horizon, held-out IC, baseline sign, noise margin, and pass/fail; bootstrap output is reproducible with seed 42 and no in-sample result is represented as held-out.
   - Verify: `uv run pytest tests/perfanalytics/test_correlation.py -q`
5. **Verify end-to-end behavior and regressions.** Add/complete integration coverage for market selection, market-suffixed paths, schema, and deterministic alignment; run the focused package suite and repository suite.
   - Acceptance: all WI-015 tests pass, both market modes and BOTH are covered without touching WI-014, and the full existing suite is green.
   - Verify: `uv run pytest tests/perfanalytics -q && uv run pytest -q`

## OUT OF SCOPE
- G-PA3/G-PA5, meta-labeling, trading applications, shortlist integration/ranking changes, new model training, composite scores, and cost overlays.
- Any modification to WI-014 files or outputs, live trading, or a new signal/auto-execution path.
- Additional targets beyond T1–T4, other horizons, non-confirmed feature families/windows, partial warm-up windows, or a decision to promote any association into a trading system.

## EXECUTION LOG
