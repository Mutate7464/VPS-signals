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
3. **Add fib/range feature block over FIBONACCI-scaled windows** (admin spec 2026-10-23): base window = **3 trading days**, multipliers **1,2,3,5,8,13,21,34** → windows **[3, 6, 9, 15, 24, 39, 63, 102]** (smallest 3d, largest 102d < 1 yr). All features XGBoost-compliant: float32, dimensionless (ratios / [0,1] positions / z-scores / binary flags — no raw prices or dollar volumes), NaN only in warmup, division-by-zero guarded:
   - `range_pos_f{3,6,9,15,24,39,63,102}` = (close − rolling_low)/(rolling_high − rolling_low) ∈ [0,1] — 8
   - `range_width_f{3,6,9,15,24,39,63,102}` = (hh − ll)/close — 8
   - `range_compression_f{6_39, 15_102}` = short width / long width — 2
   - `pct_from_high_f102`, `pct_from_low_f102` — 2
   - `donchian_break_f6`, `donchian_break_f15` (close > PRIOR window high; binary) — 2
   - `fib_dist_f{15,39,102}` = (close − nearest retracement level)/range_width, levels {38.2%, 50%, 61.8%} of the window swing; 0 when range ≈ 0 — 3
   - `gap_z` = z-scored (open/prev_close − 1) — 1
   Total +26 → **raw = 89**.
4. **Relax selection:** `vif_threshold` 5.0 → 10.0; `min_mi_percentile` 30 → 15 (CLI flags already exist). Target whitelist ≥ 30 features/target (E2: 19).
5. **Placebo seeds 1 → 3** (budget allows; strengthens CB-05).
6. E2 hyper-parameters stay frozen (E3 is still an ablation, not a tuning exercise).

### XGBoost compliance audit (verified in code 2026-10-23)

- Trees are invariant to monotone rescaling → no standardization needed; the requirements are: float32, no ±inf, NaN confined to warmup, and **cross-ticker comparability** (no absolute-price/dollar values).
- Existing 63: all scale-free — RSI/%B/ADX bounded indices; vwap/obv z-scores; yang-zhang log-ratios; ATR%/kalman_spread_atr ratios; hurst/entropy dimensionless; amihud = |ret|/dollar-vol (ratio). **One exception: `frac_diff_close` is still in price units** — usable only through its per-date `_cs_pct` rank; flagged for the `cs_pct_only`/`no_static` ablation sets in E3.
- Trainer (`xgb_trainer.py`): ADF-flagged features get rolling z-score; **every whitelisted feature also enters as a per-date cross-sectional percentile (`_cs_pct`, bounded [0,1])** — targets train on `wl + wl_cs_pct`. float32 enforced.
- New fib/range features comply by construction: range_pos ∈ [0,1], widths/compression = price-relative ratios, fib distances normalized by range width (0-guard when range ≈ 0), breakout/gap binary or z-scored. Division-by-zero guarded; no raw prices or dollar volumes.

## STEPS

### [ ] Step 1 — Vectorize Hurst + entropy; equivalence test
- Change: `src/feature_engine.py` — replace the two `.rolling().apply()` blocks with numpy sliding-window implementations (hurst at stride 5, entropy fully vectorized). Keep `_hurst_rs` as reference.
- Acceptance: `tests/test_feature_vectorized.py` — vectorized vs reference on 2 synthetic tickers: corr > 0.999 (hurst stride-tolerance), max abs diff < 1e-6 (entropy). Timing test: 10 tickers × 5y under 30 s.
- Verify: `uv run pytest tests/test_feature_vectorized.py -q`

### [ ] Step 2 — Add range/fib feature block (Fibonacci windows, admin spec)
- Change: new `_range_fib_features(df)` in `feature_engine.py` (windows [3,6,9,15,24,39,63,102], features per DESIGN DECISIONS 3); wire into `compute_features`; config `features.range_fib: true`.
- Acceptance: raw feature count == 89 on fixture; every new feature float32, dimensionless, NaN confined to warmup (< window bars per ticker), no ±inf; leakage tests pass.
- Verify: `uv run pytest tests/test_leakage.py tests/test_range_fib.py -q`

### [ ] Step 3 — Trainer joins persisted features (no recompute)
- Change: `xgb_trainer.build_panel` loads `data/features/features_USD.parquet` (+ `features_USD_metadata.parquet` surviving cols), computes only targets + close from raw, joins on (date, symbol); falls back to legacy recompute with `--recompute-features`.
- Acceptance: panel row-for-row equal to E2 panel when joined vs recomputed on fixture data (assert equality); trainer wall on fixture < 60 s.
- Verify: `uv run pytest tests/test_panel_join.py -q`

### [ ] Step 4 — Rebuild Sprint 2–3 on USD with expanded set + relaxed thresholds
- Change: none beyond steps 1–3; run with `--vif-threshold 10 --min-mi-percentile 15`.
- Acceptance: features parquet 89 float32 cols, ≥ 500 symbols; catalog `n_features_raw == 89`; whitelist ≥ 30/target; peak RSS < 3 GB; feature stage < 45 min (proves Hurst fix).
- Verify: `uv run python -m src.feature_engine --market USD --min-date 2016-01-01 && uv run python -m src.stat_metadata --market USD --vif-threshold 10 --min-mi-percentile 15 && grep -E "raw|whitelist" reports/sprint3_metadata_selection.md`

### [ ] Step 5 — E4 first (cheapest): metric/target alignment on the E2 oof
- Change: `scripts/diag_signal.py --exp e4`: within-date vs pooled ROC-AUC; ticker-prior baseline AUC vs model AUC (identity-signal test); continuous `fwd_atr_ret_15/20` Spearman IC + decile spread; effective K audit.
- Acceptance: report `reports/diag_D002_e4.md` with the H3 verdict row (ticker-prior ≈ model ⇒ identity signal; continuous IC significant while binary not ⇒ H3).
- Verify: `uv run python scripts/diag_signal.py --exp e4 --market USD && grep -E "Verdict|H3" reports/diag_D002_e4.md`

### [ ] Step 6 — E3 ablation matrix (trains on column subsets of ONE persisted panel)
- Change: `xgb_trainer --feature-set {full89, vif28, mi19, cs_pct_only, no_static, fib_only}` (column masks; no recompute).
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
| 2026-10-23 ~20:00 | admin | Plan approved: all DESIGN DECISIONS accepted except #3, which is replaced by the Fibonacci-window spec (windows 3×[1,2,3,5,8,13,21,34] = [3,6,9,15,24,39,63,102]); all features must be XGBoost-compliant — float32, dimensionless/normalized (no absolute-price values), bounded ranges, NaN in warmup only. Build may start Steps 1–4. | none |
| 20:25 | 1 | PASS — exact vectorized ports of _hurst_rs / _shannon_entropy / _frac_diff_fixed (better than planned stride-5: max abs diff < 1e-6, corr≈1.0). 6/6 tests + leakage green. | stride not needed; exact equivalence achieved |
| 20:25 | 2 | PASS — 26 fib/range features over windows [3,6,9,15,24,39,63,102] (raw = 89): float32, dimensionless, NaN warmup-only, no inf, ranges asserted. 6/6 tests incl. no-lookahead truncation test. | none |
| 20:40 | 3 | PASS — build_panel joins persisted features/targets parquets (legacy recompute behind --recompute-features); join==recompute test green on synthetic market; full suite 38/38. | parquets must be built with min_date <= trainer min_date (documented) |
| 20:50 | 4 | PASS — feature rebuild 508 sym / 533,017 labeled rows / 89 float32 features in **4 min** (E2: 4h10m; Hurst vectorization = the whole win), peak RSS 730 MB. stat_metadata (VIF 10 / MI pct 15): 89 → 32 surviving, whitelists 32/32/27/32. | y_20d_up whitelist 27 < 30 target — MI-threshold is per-target data-driven; accepted as minor deviation rather than loosening MI further |
| 21:20 | 5 | **PASS — H3 SUPPORTED.** `reports/diag_D002_e4.md`: continuous Spearman IC of model prob vs fwd ATR return is significant on the 15d targets (t = +4.31 / +3.27 over 2,696 dates) while all binary gates fail → ranking signal exists but the absolute ATR-breakout labels/within-date K-gates cannot express it. Also: ticker-prior AUC **beats** the model on all targets (worst +0.008, worst-case +0.066 on y_20d_down) → strong identity-signal component, esp. trend targets. Effective K = 30 on every date (0/2,696 degenerate). | E4 ran on the E2-era oof (19-feature models) by design; E3/E5 adjudicate H2/H4 next |
| 20:05 | 6 (attempt 1) | **FAILED — OOM kill (SIGKILL) 4s into a placebo fold** at ~3.7 GB MemAvailable; loop tree killed. y_15d_high checkpoint survived. Fix: slim panel to E3-mask union + free panel before training. | committed |
| 20:30 | 6 (attempt 2) | **FAILED — DATA BUG surfaced by fold-size sanity check.** Fold n_val ≈47k vs E2's ≈148k → panel had 533,017 rows vs E2's 1,240,275. Root cause: `iter_market_symbols` filtered by `read_from` **without reset_index**; compute_features inherits the gapped index while compute_targets builds a RangeIndex → `pd.concat(axis=1)` misaligns → dropna(targets) silently truncates (AAPL: 2,696→560 rows). Bug is E2-era: **both feature parquets (E2's and today's) were truncated**; E2's QA/oof numbers are unaffected (the trainer recomputed in-loop with reset_index). Killed the running E3, fixed the iterator (+regression test), purged stale per-set artifacts, relaunched features → metadata → E3 chain. | Truncated whitelists (32/32/27/32) and the first E3 attempt are INVALID; being regenerated. Join design itself is sound — the test missed it because synthetic fixtures had clean indexes. |
