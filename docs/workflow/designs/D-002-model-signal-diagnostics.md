# D-002 — Model signal diagnostics (WI-002, goal G-001)

> Status: **proposed** (awaiting admin acceptance). Executable plan for E2: `docs/plans/2026-10-22-WI-002-e2-full-universe-rerun.md`.

## Context

Gate 4 failed on all 4 USD targets (ROC-AUC 0.43–0.51, BSS < 0, P@K lift 0.79–1.08 vs ≥1.5). CAD is no better.
Placebo runs are clean, so the pipeline is not leaking — it just finds nothing.

Artifact findings (read-only inspection, 2026-10-22):

- **The Gate 4 run used the 5-ticker test fixture, not the real universe.**
  `data/features/features_USD.parquet` and `data/oof_USD.parquet` have 1,400 rows = 5 symbols × 280 dates
  (2025-08-28 → 2026-09-23). `load_market_frame()` falls back to `data/raw_ohlcv_test` when
  `data/raw_ohlcv/market=USD` has no parquet; the 546 real USD files were synced only after the run (WI-003).
  `sprint4_model_qa.md` never states universe size.
- Fold `n_fit` was 265–800 rows; many folds have `best_iteration = -1` (early stop at round 0 → nothing learned).
- P@K was effectively K = 1 (`min(30, 10% of 5, >=1)`).
- The Gate 3 catalog was built on the same 1,400 rows: 63 → 10 features by VIF; 7 whitelisted per target
  (amihud/entropy/hurst/kama_er-type features survive; RSI/MACD/ATR%/ADX/VWAP/OBV families all pruned).
- Mutual-information values are impossible: `y_20d_up` MI = 0.47 nats but label entropy at 16.5% base rate ≈ 0.45 nats.
  kNN-MI artifact. `amihud_50` ticker-mean R² = 0.49 (ticker identity); per-ticker base rate of `y_20d_up` spans 2%–33%.
  Below-chance AUC on `y_20d_down` (0.426) fits an identity signal that flips across folds.

## Ranked hypotheses

| # | Hypothesis | Evidence | Prior |
|---|---|---|---|
| H1 | Invalid experiment: wrong universe / sample size (5 tickers, 1,400 rows) | fixture fallback, tiny folds, best_iteration −1, K = 1 | very high |
| H2 | Feature selection corrupt: MI/VIF computed on ticker-identity-dominated data → 7 near-static features | MI > label entropy; amihud_50 ticker R² 0.49; 63 → 10 | high (depends on H1) |
| H3 | Target/metric mismatch: absolute, regime-driven, path-dependent ATR labels scored with within-date ranking gates | base rate swings by regime (y_15d_low 56% Bear vs 24% Bull) | medium |
| H4 | Genuinely little signal in OHLCV-only features at 15–20d horizons | testable only after H1–H3 cleared | medium (residual) |

Target/feature misalignment is treated as a CONTROL (E1), not a hypothesis: by code reading, features use ≤ t, labels use
[t+1, t+h], `fwd_atr_ret_h` is aligned identically.

## Options

- A. Tune hyper-parameters/features now — rejected (tuning on 1,400 rows is noise-fitting and would hide H1).
- B. Re-run the whole pipeline on the real universe, then decide — chosen first step.
- C. Redesign targets now (cross-sectional ranks) — premature; needs E4/E5 evidence.

## Decision

Option B, then controlled ablations with stop rules. No fix is selected until E2 results exist.

## Experiments (diagnostics in read-only `scripts/diag_signal.py` unless noted; n_jobs=2, float32, symbol-sequential)

| ID | Experiment | Acceptance | Verification |
|---|---|---|---|
| E0 | Provenance: tickers/rows/date range per source; apply WI-008 quarantine | USD ≥ 500 tickers, median history ≥ 1,000 dates, real source asserted | `uv run python scripts/diag_signal.py --exp e0` |
| E1 | Controls: (a) shifted-label feature → AUC > 0.95; (b) planted AUC≈0.60 signal recovered ≥ 0.57 | both pass, else fix trainer/CV first | `uv run pytest tests/test_diag_controls.py -q` |
| **E2** | **Faithful re-run on real universe** (see E2 plan) | all Gate 4 metrics recorded with universe header; ≥3/5 gates on any target ⇒ H1 primary | see E2 plan |
| E3 | Feature-set ablation: 63 / 10 VIF / 7 MI / cs_pct-only / minus ticker-static; corrected MI (binned/per-date) | some set reaches deflated t > 2.5 where baseline does not ⇒ H2 | `uv run python scripts/diag_signal.py --exp e3 --market USD` |
| E4 | Metric/target alignment: within-date vs pooled AUC; ticker-prior baseline; continuous `fwd_atr_ret` IC & decile spread; effective K | ticker-prior ≈ model AUC ⇒ identity signal; continuous IC sig. while binary not ⇒ H3 | `uv run python scripts/diag_signal.py --exp e4 --market USD` |
| E5 | Unpredictability floor: ridge/logit on 5 classic factors vs `fwd_atr_ret_15/20` | rank-IC < 0.01, t < 2 with E3/E4 null ⇒ H4 | `uv run python scripts/diag_signal.py --exp e5 --market USD` |

Decision matrix: E2 passes → H1, tune. E3 fixes → H2, replace MI/VIF selection, rebuild catalog. E4 flags labels → H3, new ADR on targets.
All null → H4: pivot horizon/cross-sectional-rank targets or accept no edge (PDFs remain structural demo).

## Consequences

- Positive: cheap, falsifiable; resolves the most probable cause (H1) before any model change; adds permanent guards (fixture refusal, universe header, logging, checkpointing).
- Negative: E2 needs infra changes first (loader, logging, memory) and 1–2.5 h of compute with Hermes/opencode stopped; Gate 4 stays FAILED; WI-001 QA exception stands.
- Survivorship caveat: watchlists are current constituents → full-universe results may overstate signal; state it in the report.
- WI-008 dependency: dead-letter list (72 rows; 70 CB-01) is NOT currently honored by `load_market_frame` — E2 plan fixes this.
