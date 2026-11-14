# D-022 — three-binary first-touch decomposition (swing events)

- Opened: 2026-11-09, admin direction in chat (after WI-033 REJECT closed D-021).
- Status: DRAFT — pending admin approval of the WI batch.

## 1. Context and structural change (required after WI-033 REJECT)
D-021's joint `multi:softprob` model REJECTed both markets. Its failure mode was
degenerate fold selection (fold 2 USD: 22 of 6,917 events selected; fold 3 CAD: 50)
— one shared probability vector, one threshold on P(BUY), no independent control of
the stop side.

**Structural change in D-022:** decompose the same first-touch outcome into three
*mutually exclusive binary targets*, each with its own independently trained
`XGBClassifier(objective="binary:logistic")` and per-fold isotonic calibration:

- `b_profit` — profit barrier touched first (true/false);
- `b_stop` — stop barrier touched first (true/false);
- `b_hold` — vertical barrier reached untouched (true/false).

Labels come from the identical `src/swing_bsh/events.py` geometry (k∈{1.5,2.0},
h∈{21,55}); only the encoding changes (one 3-class y → three 0/1 columns). Entry
rule becomes **asymmetric and two-sided**: take an at-bottom event iff
`P̂_profit ≥ τ_p AND P̂_stop ≤ τ_s`, thresholds grid-tuned on CALIB folds only and
frozen before EVAL. This directly attacks the WI-033 failure mode: the stop-side
probability can veto an entry even when the profit side is confident.

Probabilities are intentionally NOT renormalized (they need not sum to 1); the rule
is a threshold filter, not a distribution estimate.

## 2. Probe-first gating (re-proposing rule)
WI-034 (probe, cheap): per-binary univariate screen reusing the WI-032 harness —
class balance per (state,k,h) for each binary target, Spearman IC of the whitelisted
feature universe vs each binary target, **|ρ|>0.4 prune (admin-loosened 2026-11-09;
was 0.7 → expect >41 kept)**, BH-FDR α=0.05, 5-seed permutation placebo.
CLEAR (≥1 FDR-sig same-sign cross-market feature per binary target, placebo clear)
gates WI-035 (model). If the stop/hold sides show no signal the decomposition is
closed negative before spend.

## 3. WI-035 model and gate (unchanged from WI-033 unless noted)
- 3 × learner per binary target (learner grid, §3b), feature grid = WI-034 kept set
  + state/k/horizon, same `PurgedWalkForwardSplit`
  (embargo = max(20, h)).
- Per-fold isotonic per binary, sigmoid fallback <25 positives (CB-04).
- Baseline: frozen fib rules (WI-028 entry + WI-030 exit, 25 bps); placebo CB-05.
- Gate: ADOPT_LOOSE_4OF5 (≥4/5 folds, pooled edge > 0, placebo z ≥ 2.0). No pickle
  unless ADOPT.

## 3b. Learner grid (admin direction 2026-11-09: test other ML alongside XGB)
All three binary targets are trained under **each** learner; one learner (and one
threshold pair) is selected on CALIB folds only, frozen before EVAL — no post-hoc
learner cherry-picking, single placebo run on the selected configuration. All
learners `n_jobs=2`:
1. `xgboost` — `XGBClassifier(binary:logistic, hist)` (incumbent).
2. `logistic_l2` — sklearn `LogisticRegression(penalty="l2")` on standardized
   features; cheap linear calibration benchmark — if it matches XGB, the edge is
   linear and the tree learners add cost, not signal.
3. `hist_gbm` — sklearn `HistGradientBoostingClassifier` (different
   boosting implementation: native histogram, different regularization;
   guards against XGB-specific overfit).
4. `mlp_torch` (torch already a project dep, CPU): 2-layer MLP,
   early-stopped; tests nonlinearity beyond trees.

### 3c. Extended-run loosening (admin direction 2026-11-09, after WI-035)
Measured: WI-035 burned only ~0.3 of 8,640 credits (balance 100% post-run);
cap was the binding constraint, not capacity. Loosened for WI-036:
- Core-hour cap 1.0 → **2.5** (burst budget: 2.5 core-h ≈ 83% of full balance,
  recoverable ~2 h idle; sustained <60% rule unchanged).
- `mlp_torch` restored (full 4-learner grid) — the drop rule fired against a
  cap we never approached.
- ρ prune 0.4 → **0.3** — more correlated features admitted.
- **Feature expansion** ("integrate all that has information"): unused raw
  columns (volume z/trend, VWAP `average` distance, `barCount`), cross-sectional
  same-date percentile ranks, sector one-hots + sector-relative ranks
  (`config/sector_map.csv`), event-quality (swing depth in ATRs, bars since
  opposite swing), calendar, market breadth (% universe at_bottom/at_top).
  All trailing/causal.
- **Horizon loosening** ("trade days before and after accepted"): vertical
  barrier ladder {21,55} → **{5, 8, 13, 21, 34, 55, 89, 144, 233}** — short
  AND long fib horizons; verdict grid learner × binary × horizon × market with
  BH-FDR α=0.05 across all cells (216 tests), headline = FDR-surviving
  cross-market same-sign cells.
- **Entry-rule layer retired from the verdict** (admin 2026-11-09: "entry rules
  should not play a factor"): WI-036 measures pure model signal — OOF AUC and
  rank-IC per learner × binary × market over the same purged CV — no τ grid,
  no `frozen_selection`, no portfolio returns, no costs. The τ/entry machinery
  stays in the code for the (hypothetical) deployment gate but is not part of
  the confirmatory statistic.
- Placebo stays 5-seed (cheap; the waiver is retired), re-pointed at AUC/IC.
- NOT loosened (correctness, not budget): n_jobs=2, float32, symbol-sequential
  reads, purged embargo CV, no renormalized probabilities.

## 4. Risks
- R-a: 3× model fits ≈ 3× WI-033 runtime (USD ~23 min, CAD ~13 min, n_jobs=2) —
  core-hour cap 1.0 in the WI spec; checkpoint per market.
- R-b: OvR-calibrated softprob already ≈ per-class probabilities; if the probe and
  the two-threshold rule do not beat baseline, the residual hypothesis is the
  threshold structure itself and the thread closes negative (frozen rules stand).
- R-c: binary classes are imbalanced per (k,h) cell — calibration fallbacks and
  per-cell positive counts must be reported.

## 5. WIs
- WI-034 `docs/kanban/draft/WI-034-binary-decompose-probe.md` (gates WI-035).
- WI-035 `docs/kanban/draft/WI-035-three-binary-xgb-gate.md`.
