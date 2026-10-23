# PLAN — WI-002 / E3–E5: richer feature set, relaxed selection, alignment + floor diagnostics

> Board row: WI-002 (admin fork decision 2026-10-23: proceed E3–E5; defer WI-008 execution + ELE re-download to admin/Mac).
> ADR: `docs/workflow/designs/D-002-model-signal-diagnostics.md` (E3/E4/E5 rows) + admin addendum below.
> Status: PLAN — awaiting admin go.

## Admin addendum (2026-10-23, verbatim constraints)

1. Add range/Fibonacci-retracement features ("range follow fib").
2. Less strict VIF/MI pruning (keep more features).
3. Budget is the binding constraint: ~8 h wall clock, ~5.5 GB RAM available. **Maximize what fits in it.**

## FINDINGS — where the 8 h actually goes (measured, E2 run 2026-10-23)

| Stage | Wall | Peak RSS | Note |
|---|---:|---:|---|
| feature_engine (Sprint 2) | 4h10m | 0.7 GB | Hurst `.rolling().apply()` dominates (3 windows × 508 tickers) |
| stat_metadata | 5m | 1.4 GB | fine |
| xgb_trainer | 4h17m | 2.3 GB | **`build_panel` = 3h58m — recomputes all 63 features from raw**; all 44 model fits together ≈ **15–20 min** |
| model_qa | 35s | 0.6 GB | fine |

Training is essentially free; **feature computation runs twice (~8 h of the 8.7 h)**. RAM headroom is large: panel at 1.24M rows × 63 cols × 4 B ≈ 310 MB; even 150 features ≈ 750 MB.

## Feature-set inventory (current 63, all classical technicals)

Windows [5,10,20,50,100] unless noted: RSI (5/14/21) + slope · BB %B ×5 · BB width ×5 · MACD norm line+hist · ADX ×5 · DI spread ×5 · ATR% ×5 · OBV z ×5 · Hurst (20/50/100) · frac-diff close · entropy (10/20) · Kalman spread/ATR · KAMA ER ×5 · VWAP z ×5 · Amihud ×5 · Yang-Zhang vol ×5.

**Gaps:** no range-structure/position features (Fib/Donchian/distance-from-extremes), no raw return momentum, no gap features, no volume shape, no benchmark-relative features. Admin's range/fib request targets the biggest gap.

## DESIGN DECISIONS (defaults; admin may veto at approval)

1. **Compute features once.** `xgb_trainer.build_panel` joins the persisted `data/features/features_USD.parquet` on (date, symbol) instead of recomputing. Saves ~4 h per full run.
2. **Vectorize the two `.rolling().apply()` blocks** (`hurst_{20,50,100}`, `entropy_{10,20}`) with stride-batched numpy per ticker (equivalent values within tolerance; stride=5 for hurst). Feature stage target: < 45 min.
3. **Add ~18 range/fib features** (all vectorized): swing high/low + range position `(c−ll)/(hh−ll)` for 20/50/100; range width `(hh−ll)/close` for 20/50/100; range compression `rw20/rw100`; pct-from-252d-high / low; Donchian breakout flag (close > prior hh20); fib distances to 38.2/50/61.8% retracement of the 50d swing (3 signed distance features); gap_% (open/prev_close−1) z-scored. Raw total ≈ **81**.
4. **Relax selection:** `vif_threshold` 5.0 → 10.0; `min_mi_percentile` 30 → 15 (CLI flags already exist). Target whitelist ≥ 30 features/target (E2: 19).
5. **Placebo seeds 1 → 3** (budget allows; strengthens CB-05).
6. E2 hyper-parameters stay frozen (E3 is still an ablation, not a tuning exercise).

## STEPS

### [ ] Step 1 — Vectorize Hurst + entropy; equivalence test
- Change: `src/feature_engine.py` — replace the two `.rolling().apply()` blocks with numpy sliding-window implementations (hurst at stride 5, entropy fully vectorized). Keep `_hurst_rs` as reference.
- Acceptance: `tests/test_feature_vectorized.py` — vectorized vs reference on 2 synthetic tickers: corr > 0.999 (hurst stride-tolerance), max abs diff < 1e-6 (entropy). Timing test: 10 tickers × 5y under 30 s.
- Verify: `uv run pytest tests/test_feature_vectorized.py -q`

### [ ] Step 2 — Add range/fib feature block
- Change: new `_range_fib_features(df)` in `feature_engine.py`; wire into `compute_features`; config `features.range_fib: true`.
- Acceptance: raw feature count == 81 on fixture; no NaN explosion (< 5% beyond warmup); leakage tests pass.
- Verify: `uv run pytest tests/test_leakage.py tests/test_range_fib.py -q`

### [ ] Step 3 — Trainer joins persisted features (no recompute)
- Change: `xgb_trainer.build_panel` loads `data/features/features_USD.parquet` (+ `features_USD_metadata.parquet` surviving cols), computes only targets + close from raw, joins on (date, symbol); falls back to legacy recompute with `--recompute-features`.
- Acceptance: panel row-for-row equal to E2 panel when joined vs recomputed on fixture data (assert equality); trainer wall on fixture < 60 s.
- Verify: `uv run pytest tests/test_panel_join.py -q`

### [ ] Step 4 — Rebuild Sprint 2–3 on USD with expanded set + relaxed thresholds
- Change: none beyond steps 1–3; run with `--vif-threshold 10 --min-mi-percentile 15`.
- Acceptance: features parquet 81 float32 cols, ≥ 500 symbols; catalog `n_features_raw == 81`; whitelist ≥ 30/target; peak RSS < 3 GB; feature stage < 45 min (proves Hurst fix).
- Verify: `uv run python -m src.feature_engine --market USD --min-date 2016-01-01 && uv run python -m src.stat_metadata --market USD --vif-threshold 10 --min-mi-percentile 15 && grep -E "raw|whitelist" reports/sprint3_metadata_selection.md`

### [ ] Step 5 — E4 first (cheapest): metric/target alignment on the E2 oof
- Change: `scripts/diag_signal.py --exp e4`: within-date vs pooled ROC-AUC; ticker-prior baseline AUC vs model AUC (identity-signal test); continuous `fwd_atr_ret_15/20` Spearman IC + decile spread; effective K audit.
- Acceptance: report `reports/diag_D002_e4.md` with the H3 verdict row (ticker-prior ≈ model ⇒ identity signal; continuous IC significant while binary not ⇒ H3).
- Verify: `uv run python scripts/diag_signal.py --exp e4 --market USD && grep -E "Verdict|H3" reports/diag_D002_e4.md`

### [ ] Step 6 — E3 ablation matrix (trains on column subsets of ONE persisted panel)
- Change: `xgb_trainer --feature-set {full81, vif28, mi19, cs_pct_only, no_static, fib_only}` (column masks; no recompute).
- Runs: 6 sets × 4 targets × (1 real + 3 placebo) × 5 folds + final ≈ 6× E2 fit cost ≈ 1.5–2 h.
- Acceptance: `reports/diag_D002_e3.md` — per set × target: ROC-AUC, PR-AUC lift, P@K lift, deflated IC t, placebo z; H2 verdict (any set reaches deflated t > 2.5 where baseline doesn't).
- Verify: `uv run python scripts/diag_signal.py --exp e3 --market USD && grep -E "Verdict|H2" reports/diag_D002_e3.md`

### [ ] Step 7 — E5 unpredictability floor
- Change: `scripts/diag_signal.py --exp e5`: ridge/logistic (sklearn, n_jobs=2) on 5 classic factors (mom_12_1, rev_1m, vol_20, amihud, size-proxy) → continuous IC vs `fwd_atr_ret_15/20`, purged WF t-stats.
- Acceptance: `reports/diag_D002_e5.md` with H4 verdict (rank-IC < 0.01 and t < 2 with E3/E4 null ⇒ H4).
- Verify: `uv run python scripts/diag_signal.py --exp e5 --market USD && grep -E "Verdict|H4" reports/diag_D002_e5.md`

### [ ] Step 8 — Combined verdict + board update
- Change: append E3/E4/E5 verdicts to `reports/diag_D002_e2.md` ADR matrix (or a new `reports/diag_D002_summary.md`); update board row; STOP for admin.
- Acceptance: one-line verdict per hypothesis (H2/H3/H4), each traced to its report.
- Verify: `grep -E "H2|H3|H4" reports/diag_D002_summary.md`

## BUDGET (projected)

| Stage | Est. wall |
|---|---:|
| Steps 1–4 (feature rebuild + metadata) | ~1 h |
| Step 5 (E4) | ~30 min |
| Step 6 (E3 matrix) | ~1.5–2 h |
| Step 7 (E5) | ~30 min |
| **Total** | **~3.5–4.5 h** (headroom vs 8 h) |

Peak RSS projected < 3 GB (vs 5.5 GB available). Riskiest step: 3 (join correctness) — guarded by equality assertion vs recompute.

## OUT OF SCOPE
- CAD market (separate approval after USD verdict).
- Hyper-parameter tuning (only if E3–E5 find signal — then new ADR).
- WI-008 reinstatement (deferred; quarantine list still honored).
- ELE re-download (admin, Mac side).

## EXECUTION LOG

| Time | Step | Outcome | Concern? |
|---|---|---|---|
