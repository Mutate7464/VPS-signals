# Tiered-workflow status summary (grounded inventory, 2026-11-10)

> Input to D-025. Every fact below is tool-verified this session (reports on disk, manifest, BOARD).

## Tier 1 — Features + metafeatures (predictive inputs)

- Panel: WI-016 grid + WI-036 expansion (raw volume/VWAP/barCount, cross-sectional ranks, sector one-hots + ranks, event-quality metafeatures `swing_depth_atr`/`bars_since_opp`/`dd_age`, calendar, breadth); ~100+ columns at the detection bar (USD 40 design cols / CAD 38 in the WI-042 join).
- Alignment with target (WI-040 permutation attribution, winner cell): ~8–10 features carry essentially all signal — `atr_pct_3` (top-1 both markets), entropy family (`cs_entropy_102`, `entropy_24/39`), `hurst_15/39`, ADX family (`adx_21/144`, `di_spread_3/233`), `kama_er_15`, `range_compression_8_55`, `swing_depth_atr`, `bars_since_opp` (TreeSHAP/linear). Sector one-hots, `k`, most calendar/cross-sectional ranks ≈ 0 AUC drop.
- Old univariate meta-scan (`reports/fib_swings/meta_*.csv`, ~1,260 combos): nearly all |r|<0.05; a few RSI/BBW ratio combos reach AUC 0.85–0.97 uncorrected.
- Gaps (candidates for research): realized-vol forecasting family, volume/liquidity profile, seasonality beyond month/dow, cross-asset/market-level context, options-implied (data availability TBD).

## Tier 2 — Predictions (L1 library, D-023 Layer 1)

- Library: `data/models/wi040/manifest.parquet` (9,745 rows) = WI-036 (96) + WI-038 (6,838) + WI-044 (2,811) fold pickles, 100% path-resolved.
- Coverage TODAY: only `b_hold` binary (hold-vs-exit on swing events); horizons 5–89 (233/144 truncated by cap); learners xgboost, logistic_l2, hist_gbm, mlp_torch + lightgbm, catboost, random_forest, extra_trees, xgboost_isotonic, elasticnet_logistic (WI-044 RATIFIED).
- Best cells: xgboost/b_hold/h13 AUC 0.7836 USD / 0.7207 CAD (Brier skill +0.327 USD, ECE 0.0009); random_forest/b_hold/h21 min AUC 0.7341. WI-039: b_hold robust across regimes (top-regime AUC share 0.36/0.45 < 0.60 bar).
- NOT covered: directional (up/down, high/low touch), volatility-expansion/contraction, magnitude (WI-025 quantile REJECT lineage) — the admin's Tier-2 families.

## Tier 3 — Trade action / strategy (L2, D-024)

- All seven L2 overlay questions closed permanently under the ratified D-024 harness (WI-042 + WI-043): 4 modern (037/033/030/028) + 3 legacy (012/018/011). Every tested overlay: statistical signal (placebo z to +5.88) but EVAL edges ~0.00000 vs 25 bps costs. Cross-market transfer REJECTed (wi012: CAD edge −0.46 bps).
- Frozen baseline: fib rule `frozen_fib_w28entry_w30exit_t15_s10_d39_close`, cost 25 bps.
- Open question (the remaining probe): WHERE the CALIB edge dies before EVAL — tau-mass concentration vs fold concentration vs cost floor. L2 pause policy stands: no new L2 WIs until answered.

## Constraints that carry into the sprint

- Core-hour budget on Hostinger VPS (2 vCPU, measured burn); correctness invariants non-negotiable (purged/embargoed CV, CALIB-only selection, float32, symbol-sequential, n_jobs caps).
- Grids must offer only deps already in the manifest (grep pyproject) — new deps need their own adoption decision.
- Every prediction expansion = one BH-FDR family; loosened axes are variant grids, never merged configs (kanban skill).
