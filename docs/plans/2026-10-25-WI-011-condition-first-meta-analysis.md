# PLAN — 2026-10-25 — WI-011: Condition-first meta-analysis

## GOAL
For G-001, identify point-in-time conditions with measurable net expectancy and a usable daily frequency on CAD, then deliver data-only decision-rule specifications for the human gate.

## CONSTRAINTS
- Scope fixed by admin direction (2026-10-25): descriptive analysis only; no ML, trained models, or binary-target rebuild. No reopening this choice.
- CAD universe only. Conditions are trailing, point-in-time, per-symbol, using `src/targets.py`/E5 primitives and only the empirically selected indicator subset from Step 1b—not the full 89-feature panel.
- Step 2 horizons are exactly `{1, 2, 5, 10, 15, 20, 60, 120}` trading days. Use chronological walk-forward evaluation and the WI-009 20-trading-day purge discipline; for a horizon longer than 20 days, purge at least that horizon so overlapping forward labels cannot cross a fold boundary.
- A “stable-sign” finding must have the same sign in both disjoint evaluation sub-windows (WI-009b/c standing clause); report sign disagreement as unstable, never select a favorable sign after observing results.
- Step 3 is per-symbol time-series momentum, not cross-sectional ranking. Step 4 uses estimated CAD costs and the 100–400 total annual firings preference (not a cap), with a 4–12 position concurrency envelope for 5–15 trading-day holds. “None survive costs at this universe size” is a valid result.
- Step 5 is a descriptive data specification only. STOP at the human gate; no backtest optimization or screener implementation.
- Host: 2 vCPU / 8 GB / no swap; `n_jobs<=2`; cast calculated feature frames to `float32` immediately; iterate symbols sequentially; never materialize an all-ticker uncompressed frame. No secrets, live trading, or order execution. Any charts: batch 10, then `matplotlib.pyplot.close('all')` and `gc.collect()`.
- Budget: each analysis is minutes-scale; no training runs. Keep artifacts under `reports/wi011_*.md` and scripts under `scripts/`.

## STEPS

### Step 1 — Preflight inputs (Step 0; must pass before analysis)
(a) Add `scripts/wi011_preflight.py` to inspect the existing CAD feature and target parquet inputs (including `data/features/features_CAD.parquet` and `data/features/targets_CAD.parquet`), reporting row counts, columns, symbol/date coverage, duplicate keys, and key alignment. Do not rebuild the data. Write `reports/wi011_preflight.md` with observed counts and PASS/FAIL markers. Fail before subsequent steps if inputs are absent, keys are duplicated, or feature/target keys do not align.
(b) Acceptance: the report records both parquet row counts and aligned `(date, symbol, market)` coverage; no duplicate keys; exact key-set alignment is PASS. Any row count may be reported as observed rather than hard-coded, but unexplained mismatch is a failure.
(c) Verify: `uv run python scripts/wi011_preflight.py && grep -E 'FEATURE_ROWS|TARGET_ROWS|KEY_ALIGNMENT: PASS|DUPLICATE_KEYS: 0' reports/wi011_preflight.md`.
Do NOT regenerate features/targets, concatenate all symbols into one in-memory frame, or continue analysis after a failed preflight.

### Step 2 — Trailing condition definitions (draft Step 1)
(a) Add `scripts/wi011_conditions.py` and point-in-time unit tests. Define candidate per-symbol state columns using existing `src/targets.py`/E5 primitives: trend state (efficiency ratio or trailing OLS slope plus R²), own-history volatility regime (ATR/volatility percentile), liquidity regime (Amihud percentile), and own-history TS state (price vs trailing MA / 52-week channel). Use only the compact primitives/candidate indicators later retained by Step 1b. All rolling thresholds use data available at or before the observation date; preserve null warm-up rows.
(b) Acceptance: conditions are generated sequentially per symbol, calculated columns are `float32`, and tests prove that changing future observations does not change any earlier condition and that no forward-window input is used. Output `reports/wi011_condition_definitions.md` listing formulas, lookbacks, and warm-up handling.
(c) Verify: `uv run pytest tests/test_wi011_conditions.py -q && uv run python scripts/wi011_conditions.py && grep -E 'POINT_IN_TIME: PASS|CONDITION_COUNT: [1-9]' reports/wi011_condition_definitions.md`.
Do NOT add indicators from the full 89-feature set indiscriminately, tune thresholds against forward returns, or create trade labels.

### Step 3 — Indicator association and empirical subset (draft Step 1b)
(a) Add `scripts/wi011_indicator_association.py` to analyze the available indicator panel against trailing, contemporaneous state descriptors only: values associated with local peak/bottom extremes versus upward/downward trend states. Report redundancy clusters and select the compact indicator subset that informs Step 2 condition vocabulary. No forward returns enter this analysis; update the Step 2 condition configuration to use only this selected subset plus the specified E5 primitives. Write `reports/wi011_indicator_association.md`.
(b) Acceptance: report includes indicator × state associations for extreme/trend states, redundancy clusters, and an explicit selected candidate-condition/indicator list used downstream. Result is descriptive and documents missing/undefined values.
(c) Verify: `uv run python scripts/wi011_indicator_association.py && grep -E 'EXTREME_ASSOCIATION|TREND_ASSOCIATION|REDUNDANCY_CLUSTERS|SELECTED_INDICATORS' reports/wi011_indicator_association.md`.
Do NOT infer predictive power from association, use forward-return data, or retain the whole 89-feature panel by default.

### Step 4 — Conditional expectancy and horizon sweep (draft Step 2)
(a) Add `scripts/wi011_condition_expectancy.py` to compute forward-return distributions for each condition bucket at exactly 1, 2, 5, 10, 15, 20, 60, and 120 trading days. Use chronological walk-forward folds, purge at least 20 trading days and at least the evaluated horizon, and report mean, standard deviation, hit rate, 5% tails, observation counts, and t-statistics. Compare two disjoint chronological sub-windows; write `reports/wi011_condition_expectancy.md`.
(b) Acceptance: all eight horizons and condition buckets are represented with sample counts and distribution statistics; stable-sign findings agree in sign across both sub-windows, with disagreement explicitly marked unstable. Report boundary/purge details and insufficient-sample cases; no claim of stability when a sub-window cannot be evaluated.
(c) Verify: `uv run python scripts/wi011_condition_expectancy.py && grep -E 'HORIZONS: 1,2,5,10,15,20,60,120|PURGE_TD:|SUBWINDOWS: 2|STABLE_SIGN|UNSTABLE_SIGN' reports/wi011_condition_expectancy.md`.
Do NOT random-split, let overlapping forward returns cross fold boundaries, select a sign based on the better sub-window, or optimize condition thresholds on evaluated returns.

### Step 5 — Time-series momentum probe (draft Step 3)
(a) Add `scripts/wi011_ts_momentum.py` to evaluate per-symbol own-past return-sign/trend conditions, including a volatility-scaled variant, over the same eight horizons. Compare condition-level TS results with the Step 4 cross-sectional/element results and report the TS-versus-CS decomposition in `reports/wi011_ts_momentum.md`.
(b) Acceptance: report identifies the per-symbol TS rules and horizons, provides counts/expectancy and a TS-vs-CS comparison per selected element, and explicitly records insufficient or null results. Evaluation retains chronological folds and horizon-appropriate purge.
(c) Verify: `uv run python scripts/wi011_ts_momentum.py && grep -E 'TS_RULES|HORIZONS: 1,2,5,10,15,20,60,120|TS_VS_CS_DECOMPOSITION|PURGE_TD:' reports/wi011_ts_momentum.md`.
Do NOT convert per-symbol momentum into cross-sectional ranks, introduce a trained model, or use future data in condition construction.

### Step 6 — Costs, frequency, and decision-rule specifications (draft Steps 4/5)
(a) Add `scripts/wi011_tradeable_conditions.py` to apply documented per-name spread/Amihud-proportional cost estimates and the IBKR CAD commission schedule to candidates from Steps 4–5. Report net expectancy, annual firing counts across the universe, and implied concurrency for 5–15 trading-day holds. Keep candidates only when net expectancy survives, aggregate frequency is 100–400 firings/year, and concurrency is within 4–12 positions. Write `reports/wi011_tradeable_conditions.md`; if none qualify, state exactly “none survive costs at this universe size.” Always emit `reports/wi011_decision_rules.md`: for survivors, include entry condition, hold window, exit/invalidation, condition flags, factor tilts, no-trade default, and a worked recent-data example; with no survivors, mark rules/example N/A. Stop at the human gate.
(b) Acceptance: costs and their assumptions are disclosed; every retained candidate meets all three cost/frequency/concurrency criteria; either a compliant shortlist or the explicit valid no-survivor conclusion is present. Rule specs are derived from findings, are not optimized/backtested, and include a worked example only when a survivor exists. Report the human-gate stop; no implementation/backtest follows.
(c) Verify: `uv run python scripts/wi011_tradeable_conditions.py && grep -E 'COST_ASSUMPTIONS|ANNUAL_FIRINGS|CONCURRENCY|NET_EXPECTANCY|none survive costs at this universe size' reports/wi011_tradeable_conditions.md && grep -E 'ENTRY|HOLD_WINDOW|EXIT_INVALIDATION|NO_TRADE_DEFAULT|HUMAN_GATE: STOP' reports/wi011_decision_rules.md`.
Do NOT treat 200/year as a hard cap, relax thresholds to force a survivor, add portfolio sizing, optimize/backtest the rules, or proceed past the human gate.

## OUT OF SCOPE
- Trained models, ML, binary-target rebuilds, and any full-feature-pile analysis.
- Live trading, order execution, portfolio construction/sizing, and production screener implementation.
- Backtest optimization or any work after the Step 5 human gate.
- Rebuilding CAD source parquets or unrelated pipeline/data repairs.

## EXECUTION LOG
Build appends one ≤50-word row per completed step to `docs/plans/logs/WI-011-condition-first-meta-analysis.md`; do not edit that sibling log as Planner.

## STATUS
STATUS: PLAN — awaiting admin approval before execution.
