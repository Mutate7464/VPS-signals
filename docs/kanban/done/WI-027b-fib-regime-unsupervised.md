---
wi_id: WI-027b
title: Unsupervised regime detection (GMM → HMM) with soft state probabilities as downstream ML features
status: draft
agent: surgical-builder
depends_on: [WI-027, WI-022]
board_row: "BOARD.md ACTIVE — DESIGN (admin direction 2026-11-07, research ladder stage 1b)"
write_files:
  - scripts/fib_regime_unsupervised.py:new
  - tests/test_fib_regime_unsupervised.py:new
read_only_files:
  - scripts/fib_regime_labels.py
  - scripts/fib_regime_overlay.py
  - reports/fib_swings/regime_daily_extended.csv
  - reports/fib_swings/REGIME_LABELS.md
test_command: uv run pytest tests/test_fib_regime_unsupervised.py -q --tb=short --maxfail=1
---

## 1. OBJECTIVE & ARCHITECTURAL INVARIANT
- Fit an unsupervised regime model (sklearn GMM, 3–4 components) on the same feature set WI-027 used for rule-based labels, PLUS trailing market return features (63d ret, 126d ret, 63d realized vol from per-market cross-sectional medians). Output soft state membership probabilities per (market, date) — continuous vectors that avoid the hard-boundary artifacts of rule-based labels. Compare against WI-027's rule-based regime: which labeling produces better fold-stability + fold5 isolation? float32 outputs, CALIB-only fit (< 2022-05-02), EVAL predicted once with frozen model. No hmmlearn — sklearn only. n_jobs=2.

## 2. SURGICAL IMPLEMENTATION BLUEPRINT

### 2a. Input features
- Read `reports/fib_swings/regime_daily_extended.csv` (WI-027 output) for existing r1, r1_s5, r2, n_tickers, trend, vol_cat, regime columns.
- Compute per-market trailing return features from raw OHLCV: `ret63` (63-trading-day log return, cross-sectional median close), `ret126`, `realized_vol63` (std of 63-bar log returns × √252, cross-sectional median). Reuse the `cross_section()` function from `scripts/fib_regime_labels.py` (already symbol-sequential, outputs per-market per-date DataFrame).
- Join these 3 new columns to the daily frame.
- Feature columns for GMM: `[r1, r1_s5, r2, ret63, ret126, realized_vol63]` — 6 features, float32, standardized before fitting.

### 2b. GMM fit + prediction
- Fit `sklearn.mixture.GaussianMixture(n_components=3, random_state=0, n_init=10, covariance_type='full')` on CALIB dates only (date < '2022-05-02'). Fit on ALL-market data pooled (market column ignored — one GMM for the whole universe; per-market is descriptive in the report).
- Predict soft probabilities (`predict_proba`) for all dates (CALIB + EVAL). Output shape: N_dates × 3.
- Also hard label per date = `argmax` of soft probabilities for summary tables.
- Fit a 4-component variant (n_components=4) and include both in the comparison report.

### 2c. Output 1: `reports/fib_swings/regime_daily_soft.csv`
- Same row structure as `regime_daily_extended.csv` (market, date), with new columns: `gmm3_s0_prob, gmm3_s1_prob, gmm3_s2_prob, gmm3_label` (int 0/1/2), `gmm4_s0_prob..gmm4_s3_prob, gmm4_label`. Append-only — existing columns untouched.

### 2d. Output 2: `reports/fib_swings/GMM_STATES.md`
- Per-state characterization (CALIB dates only): mean of each raw feature, n_dates, and a human-readable label suggestion (e.g., state 0 = "calm bull" if ret63 > 0 and realized_vol63 low). Mark these labels as SUGGESTIONS ONLY — downstream stages use the raw probability vector, never the name.
- Per-state conditional edge table (same format as WI-027's REGIME_LABELS.md): n_events, screened rate, edge_pp, n_folds_pos for ALL pooled screened bottoms in that state on CALIB. Repeat for 3-state and 4-state GMM.
- Fold5 callout: how many fold5 dates fall in each GMM state? Which states show n_folds_pos==5? Compare against WI-027's rule-based result (up_high/USD + chop_normal/ALL both n_folds_pos=5).
- VERDICT: PASS if any GMM state (3-state or 4-state) has n_folds_pos==5 for pooled ALL screened bottoms AND fold5 is isolated (a majority of fold5 dates fall in states that FAIL). VERDICT: FAIL if no GMM state clears. Print EXIT:0 regardless (descriptive result).

### 2e. CLI
- `--out` (default `reports/fib_swings`), `--smoke` (comma-separated symbols, fallback to FIB_SMOKE env var). Read inputs from `reports/fib_swings/` (data_dir constant, same pattern as the PM-fixed WI-027). Symbol-sequential OHLCV reads for the return features.

### 2f. Tests (synthetic only, no data/ or reports/ reads)
- `test_gmm_fit_reproducible`: fit GMM on a small random matrix with fixed seed → assert component means and predict_proba are deterministic across two fits with same seed.
- `test_soft_probs_sum_to_one`: predict_proba output sums to 1.0 per row within float32 tolerance (1e-6).
- `test_state_ordering_stable`: fit different random_state values → component order may permute but cluster assignments (via Hungarian matching on means) are consistent across seeds (within tolerance). Test that labels from seed=0 and seed=1 assign the same patterns to the same elements after mean-matching.
- `test_fold5_isolation_pass`: synthetic daily frame where fold5 dates are concentrated in one GMM state and that state fails fold-stability while another state passes → VERDICT: PASS detection.

## 3. BINARY DEFINITION OF DONE (DoD)
- [ ] Zero edits outside `write_files`.
- [ ] `test_command` exits 0.
- [ ] Do NOT run the full-universe job and do NOT read files under `data/` — tests use synthetic data only.

## 4. EXECUTION TELEMETRY (Appended on Completion/Block)
- **Attempts:** 1/2 | **Commit:** PENDING | **Status:** DONE
- **Notes / Error Trace:** `uv run pytest tests/test_fib_regime_unsupervised.py -q --tb=short --maxfail=1` → `4 passed in 5.11s` (exit 0, first attempt, zero fix attempts used). New files only: `scripts/fib_regime_unsupervised.py` (242 lines — `cross_section()` reused for ret63/ret126/realized_vol63 on the per-(market, date) close series; CALIB-only pooled `GaussianMixture(n_components∈{3,4}, random_state=0, n_init=10, covariance_type='full')` with CALIB-fit StandardScaler, one frozen predict for CALIB+EVAL; gmm{3,4}_s*_prob float32 + gmm{3,4}_label Int64 appended to regime_daily_soft.csv; per-state edge via WI-023 group_stats + fold5 callout + WI-027 comparison + VERDICT in GMM_STATES.md; --out/--smoke CLI) and `tests/test_fib_regime_unsupervised.py` (4 synthetic-only tests: fit reproducibility, probs sum to 1 @ 1e-6, Hungarian-matched seed stability, fold5-isolation PASS detection). Full-universe job NOT run; no data/ reads and no writes outside write_files (full in-memory chain verified with a synthetic sanity run in /tmp/opencode). regime_daily_soft.csv + GMM_STATES.md materialize when Hermes runs the driver. DoD: all 3 boxes met.