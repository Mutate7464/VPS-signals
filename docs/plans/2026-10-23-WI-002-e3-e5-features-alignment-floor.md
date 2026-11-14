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

### [x] Step 1 — Vectorize Hurst + entropy; equivalence test
- Change: `src/feature_engine.py` — replace the two `.rolling().apply()` blocks with numpy sliding-window implementations (hurst at stride 5, entropy fully vectorized). Keep `_hurst_rs` as reference.
- Acceptance: `tests/test_feature_vectorized.py` — vectorized vs reference on 2 synthetic tickers: corr > 0.999 (hurst stride-tolerance), max abs diff < 1e-6 (entropy). Timing test: 10 tickers × 5y under 30 s.
- Verify: `uv run pytest tests/test_feature_vectorized.py -q`

### [x] Step 2 — Add range/fib feature block (Fibonacci windows, admin spec)
- Change: new `_range_fib_features(df)` in `feature_engine.py` (windows [3,6,9,15,24,39,63,102], features per DESIGN DECISIONS 3); wire into `compute_features`; config `features.range_fib: true`.
- Acceptance: raw feature count == 89 on fixture; every new feature float32, dimensionless, NaN confined to warmup (< window bars per ticker), no ±inf; leakage tests pass.
- Verify: `uv run pytest tests/test_leakage.py tests/test_range_fib.py -q`

### [x] Step 3 — Trainer joins persisted features (no recompute)
- Change: `xgb_trainer.build_panel` loads `data/features/features_USD.parquet` (+ `features_USD_metadata.parquet` surviving cols), computes only targets + close from raw, joins on (date, symbol); falls back to legacy recompute with `--recompute-features`.
- Acceptance: panel row-for-row equal to E2 panel when joined vs recomputed on fixture data (assert equality); trainer wall on fixture < 60 s.
- Verify: `uv run pytest tests/test_panel_join.py -q`

### [x] Step 4 — Rebuild Sprint 2–3 on USD with expanded set + relaxed thresholds
- Change: none beyond steps 1–3; run with `--vif-threshold 10 --min-mi-percentile 15`.
- Acceptance: features parquet 89 float32 cols, ≥ 500 symbols; catalog `n_features_raw == 89`; whitelist ≥ 30/target; peak RSS < 3 GB; feature stage < 45 min (proves Hurst fix).
- Verify: `uv run python -m src.feature_engine --market USD --min-date 2016-01-01 && uv run python -m src.stat_metadata --market USD --vif-threshold 10 --min-mi-percentile 15 && grep -E "raw|whitelist" reports/sprint3_metadata_selection.md`

### [x] Step 5 — E4 first (cheapest): metric/target alignment on the E2 oof
- Change: `scripts/diag_signal.py --exp e4`: within-date vs pooled ROC-AUC; ticker-prior baseline AUC vs model AUC (identity-signal test); continuous `fwd_atr_ret_15/20` Spearman IC + decile spread; effective K audit.
- Acceptance: report `reports/diag_D002_e4.md` with the H3 verdict row (ticker-prior ≈ model ⇒ identity signal; continuous IC significant while binary not ⇒ H3).
- Verify: `uv run python scripts/diag_signal.py --exp e4 --market USD && grep -E "Verdict|H3" reports/diag_D002_e4.md`

### [x] Step 6 — E3 ablation matrix (trains on column subsets of ONE persisted panel)
- Change: `xgb_trainer --feature-set {full89, vif28, mi19, cs_pct_only, no_static, fib_only}` (column masks; no recompute).
- Runs: 6 sets × 4 targets × (1 real + 3 placebo) × 5 folds + final ≈ 6× E2 fit cost ≈ 1.5–2 h.
- Acceptance: `reports/diag_D002_e3.md` — per set × target: ROC-AUC, PR-AUC lift, P@K lift, deflated IC t, placebo z; H2 verdict (any set reaches deflated t > 2.5 where baseline doesn't).
- Verify: `uv run python scripts/diag_signal.py --exp e3 --market USD && grep -E "Verdict|H2" reports/diag_D002_e3.md`

### [x] Step 7 — E5 unpredictability floor
- Change: `scripts/diag_signal.py --exp e5`: ridge/logistic (sklearn, n_jobs=2) on 5 classic factors (mom_12_1, rev_1m, vol_20, amihud, size-proxy) → continuous IC vs `fwd_atr_ret_15/20`, purged WF t-stats.
- Acceptance: `reports/diag_D002_e5.md` with H4 verdict (rank-IC < 0.01 and t < 2 with E3/E4 null ⇒ H4).
- Verify: `uv run python scripts/diag_signal.py --exp e5 --market USD && grep -E "Verdict|H4" reports/diag_D002_e5.md`

### [x] Step 8 — Combined verdict + board update
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
| 21:13 | 7 (precheck) | **BLOCKED — precondition not met.** `grep -c "=== E3 CHAIN COMPLETE ===" logs/e3_runs.out` = 0; E3 chain (PID 644113, `scripts/e3_chain.sh`) still running (~30 min elapsed, on `full` set / `y_20d_down`, 3 checkpoints saved of 20). E5 not started: shares panel/RAM with the live chain — OOM risk. Steps 7–8 not executed. | not a failure — retry after chain completes |
| 21:25 | PM (cycle 1) | No opencode session since cursor — today's work was manual (admin). PM independently verified Steps 1–5: 10/10 targeted tests green; features parquet 1,240,275 rows × 89 float32 + fib cols present; whitelists 32/32/32/32; E4 report verdict H3 SUPPORTED. Step 6 chain live (PID 644113, val folds ≈148–164k = correct full-data panel). Steps 1–5 marked [x]. | chain in flight; E5 + combined verdict pending |
| 00:28 | 6 (attempt 3) | **Bug found by PM (cycle 3): trainer slim-mask `keep_cols` dropped all `_cs_pct` columns.** Two effects: (a) `cs_pct_only` resolved to zero features → chain printed "no valid features" ×4 and `FAILED: cs_pct_only` 37 s in (the `FAILED: full` at the top of the old log was stale output from the OOM-killed pre-relaunch attempt); (b) the 4 completed sets (full/no_static/fib_only/legacy19) silently trained **raw-only** (32 cols) instead of the approved `wl + wl_cs_pct` (64 cols) — internally consistent with each other but not E2-faithful. Fix: add `_cs_pct` of surviving features to `keep_cols` (src/xgb_trainer.py:462); regression test `tests/test_feature_masks.py` (all masks non-empty, full = wl+wl_cs_pct, cs_pct_only = ranks-only). Full suite 42/42. Admin chose **full 5-set rerun** (~3.2 h detached overnight); all raw-only artifacts purged, old log kept as `logs/e3_runs_rawonly_invalid.out`, chain relaunched 00:28 on fixed code. | prior 4 set-runs INVALID as E2-faithful baselines; E3 verdict must come from the rerun |
| 00:43 | 6 (task 0) | **PASS — `--exp e3` report generator written and committed (d957d43).** `scripts/diag_signal.py` `run_e3`: reads per-set oof parquets one at a time (float32, `del` + `gc` between sets), reports per set × target ROC-AUC, PR-AUC lift, P@K lift, deflated IC t (real − mean placebo IC, / se), placebo AUC z; H2 verdict = non-baseline set reaches deflated t > 2.5 where full/legacy19 don't. Smoke-tested against a snapshot of the in-flight `full` oof (only y_15d_high cols present — trainer writes oof per-target): rc 0, sensible row (AUC 0.546, deflated t +1.98), missing-set warning works; targets with absent columns are skipped. | smoke-test snapshot was mid-chain; final run MUST be after chain completes |
| 00:44 | 7–8 | **BLOCKED — precondition not met.** `grep -c "=== E3 CHAIN COMPLETE ===" logs/e3_runs.out` = 0: chain (PID 671889) still on feature-set 1/5 (`full`, y_15d_high done, y_15d_low in progress, ~16 min elapsed of ~3.2 h; ETA ≈ 03:40 UTC). E5 not started (shares panel/RAM with the live chain — OOM risk, same failure mode as attempt 1). Board row NOT moved to QA/GATE (step 8 requires the verdicts). Retry when the completion marker appears. | not a failure — rerun brief tasks 1–3 after chain completes |
| 07:10 | 6 | **PASS — E3 chain COMPLETE 07:02:11 UTC** (marker contains a timestamp, so the plain-grep precondition needed a tail check). All 5 sets × 4 targets trained on the fixed 64-col masks (7,202 s). `--exp e3 --market USD` run detached (logs/e3_report.out, EXIT=0, ~6 min, peak RSS ~0.9 GB): `reports/diag_D002_e3.md` written. Result: **H2 PARTIALLY OBSERVED → NOT SUPPORTED as a fix** — deflated IC t > 2.5 on 15d targets is reached by the baselines too (`full` +3.54 y_15d_low, `legacy19` +4.11/+3.78), so no ablation set isolates a feature-set win; 20d targets flat everywhere. | 15d targets DO show significant deflated continuous IC — consistent with E4 |
| 07:21 | 7 | **PASS — E5 floor report written** (`reports/diag_D002_e5.md`, EXIT=0). Attempt 1 crashed instantly: `ModuleNotFoundError: No module named 'src'` (script run as `python scripts/diag_signal.py`; `src` never on sys.path — run_e5 had never been executed). Fixed 4 latent bugs by inspection (see Deviations), committed d5c5441, rerun succeeded. Verdict: **H4 NOT SUPPORTED — FLOOR BREACHED**: mom_12_1 t +5.54, vol_20 t −4.72, amihud_20 t −3.37, ridge oof IC t +2.25/+2.05 on the continuous fwd ATR return — classic-factor structure IS present at 15–20d. | E5 ran <1 min; logit median-split IC is negative while ridge positive — sign flip unexplained, noted in report; admin gate should treat ridge/single-factor numbers as primary |
| 07:30 | 8 | **PASS — combined verdict + board updated.** `reports/diag_D002_summary.md` (one-line verdict per hypothesis, each traced to its report); ADR matrix in `reports/diag_D002_e2.md` updated with adjudicated E3/E4/E5 rows; `docs/workflow/BOARD.md` WI-002 row → **QA/GATE — STOP for admin**. Synthesis: signal exists in continuous fwd-ATR-return space (E4 + E5 agree), binary absolute-breakout labels + within-date K-gates are blind to it (H3 fires), features not the constraint (H2 no), no unpredictability floor (H4 no). Gate decision: target/metric redesign (factor-controlled) vs stop — admin's. | none |

## Deviations

- **Step 6 acceptance wording** (committed d957d43): the plan's verify line greps `Verdict|H2` — satisfied; but the plan's Step 6 list of sets said `{full89, vif28, mi19, cs_pct_only, no_static, fib_only}` while the chain (admin-approved rerun, EXECUTION LOG 00:28) runs `{full, no_static, fib_only, legacy19, cs_pct_only}`. The generator follows the chain's 5 sets.
- **Step 7, E5 latent bugs fixed by inspection before the single faithful retry** (attempt 1: `ModuleNotFoundError`): (a) `src` package not importable when the script is run from repo root → `sys.path.insert(0, str(ROOT))`; (b) `wilder_atr` imported from `src.feature_engine` but lives in `src.targets`; (c) `results` dict keyed by target only → the ridge `fwd_atr_ret_15` entry was overwritten by the logit run and the verdict then used the logit t as "ridge t" → keys now `"{model_kind}:{target_name}"`; (d) `min_date="2016-01-01"` gave only ~150 trading days of warmup for the 252-day `mom_12_1` lookback, silently trimming the panel to ~mid-2016 → read from `2015-01-01`. All four are bug fixes to never-executed committed code (27ae4d5), not redesigns. Committed d5c5441.
- **E5 runtime:** < 1 min vs plan's ~30 min estimate — no RAM measures needed; brief's "sample of dates on OOM" contingency unused.

STATUS: DONE (PM-set, 2026-10-24 07:30 UTC) | evidence: `=== E3 CHAIN COMPLETE 07:02:11 ===` in logs/e3_runs.out; `uv run python scripts/diag_signal.py --exp e3 --market USD` → EXIT=0, reports/diag_D002_e3.md (H2 partially observed → not the fix); `--exp e5 --market USD` → EXIT=0 after d5c5441 fixes, reports/diag_D002_e5.md (H4 NOT supported, floor breached); `--exp e4` H3 SUPPORTED (earlier, Step 5); grep -E "H2|H3|H4" reports/diag_D002_summary.md shows all verdict rows; reports/diag_D002_e2.md ADR matrix updated; BOARD.md WI-002 → QA/GATE, stopped for admin gate.
