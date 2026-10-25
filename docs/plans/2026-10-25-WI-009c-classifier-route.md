# PLAN — WI-009c — Continuous-first classifier route

Board item: WI-009c · Goal: G-001 · Dataset: CAD

## GOAL
Produce a leakage-safe CAD 20-trading-day continuous forecast whose distribution yields up/down/stay probabilities and a daily shortlist ranked by a declared probability composite, with the five-factor label probe and factor-relative skill reported.

## CONSTRAINTS
- Follow `AGENTS.md`: `n_jobs<=2`; cast feature frames to `float32` immediately; bounded/streamed memory; no secrets; daily shortlist only; no live trading or order execution; human gate before any execution use.
- CAD inputs are `data/features/features_CAD.parquet` (89 float32 features) and `data/features/targets_CAD.parquet` (701,599 aligned rows); `y_20d_stay` base rate is approximately 44.8%. Do not rebuild features or targets in this work item.
- Preserve the established 20-trading-day purge/embargo and chronological walk-forward discipline from WI-009. Reuse the existing splitter/skill-bar semantics; never use factorized date codes as positional split indices.
- Fixed admin design: continuous 20d move regression is the route; logistic on the five E5 factors for existing binary labels is only the cheap first probe. Do not train three independent binary classifiers or use them for final ranking.
- Use a split-calibration residual empirical CDF for forecast probabilities (ADR D-010). It is a marginal forecast distribution, not a guarantee of conditional calibration; report calibration diagnostics and limitations. Map each row's `2×ATR-dollar` up/down and `±5% relative` stay event into the continuous-target units; events may overlap under the specified thresholds.
- The contrastive score (`models/contrastive_ranker_wi009b.pt`, `score_numpy`) is a candidate stacked input, never the ranker. Generate it fold-safely (training dates only); do not assume the saved artifact is leakage-safe without proving its training cutoff. Rank by `P(up) - P(down)`; report `P(stay)` alongside it, but do not use it as a hidden tie-break.
- Skill-bar clause (a) is mandatory: same sign as the best factor and `|IC|` at least the existing WI-009b threshold. Reuse `src/models/skill_bar.py`; do not weaken or redefine the threshold. Any failure is a documented negative result, not a hidden FAIL.
- Cheap probe first. Full-feature/regime/stacking/selection spend is gated by its recorded evidence. One detached regressor chain only, capped at 1–2 hours; regenerate `reports/wi009c_*.md` per run.

## STEPS

### Step 0 — [x] Verify inputs and target definitions
(a) Add `scripts/check_wi009c_inputs.py` to assert feature/target alignment, 701,599 target rows, 89 feature columns of `float32`, all five existing binary target columns, and `y_20d_stay` base rate within 0.5 percentage points of 44.8%; print the continuous 20d target and ATR/price columns used by the route. Do not alter source data.
(b) Acceptance: the checker passes on the stated CAD artifacts and explicitly names the continuous target and threshold inputs used by later steps.
(c) Verify: `uv run python scripts/check_wi009c_inputs.py && grep -E "701599|y_20d_stay|continuous target|ATR" reports/wi009c_inputs.txt`
(d) STOP: if counts, alignment, dtype, base rate, or target/threshold definitions differ, record the observed values and stop; do not rebuild or silently substitute targets.

### Step 1 — [x] Cheap five-factor logistic probe
(a) Add `scripts/probe_wi009c.py`: score only E5 `mom_12_1`, `rev_1m`, `vol_20`, `amihud_20`, and `log_dollar_vol_20` against each existing binary target (`y_20d_up`, `y_20d_down`, `y_20d_stay`, `y_20d_high`, `y_20d_low`) using purged chronological CV with the 20td gap. Compare score-based within-date IC to the best single-factor baseline and apply the existing skill-bar threshold/same-sign clause. Write `reports/wi009c_probe.md`; no 89-feature model or robustness variant here.
(b) Acceptance: report contains all five targets, fold/date counts, per-factor and logistic metrics, leakage-safe split evidence, and an explicit pass/negative result per target; no class-label scores substitute for probabilities.
(c) Verify: `uv run python scripts/probe_wi009c.py --market CAD && grep -E "y_20d_(up|down|stay|high|low)|same-sign|negative result|purge" reports/wi009c_probe.md`
(d) STOP: if the probe has a split/leakage defect or cannot reproduce the five target results, stop before any feature spend. If no target clears the unchanged skill bar, record labels as not demonstrated learnable, do not use the 89 features or run optional candidates, and limit the continuous baseline to the same five factors. If at least one target passes, one 89-feature continuous run is eligible within the stated budget; this is permission, not a claim of skill.

### Step 2 — Continuous regressor and distribution-derived probabilities
(a) Add `src/models/continuous_targets.py` and `scripts/train_wi009c.py`. First train the CAD 20td continuous-move baseline using only the five E5 factors, in chronological purged folds and against the target identified in Step 0. Use the Step-1 gate above before any 89-feature run. Fit a split-calibration residual empirical CDF from held-out predictions only, then compute row-level `P(up)`, `P(down)`, and `P(stay)` from the specified event thresholds after converting them into the target's units. Keep features float32, bound memory, set `n_jobs=2`, and cap the detached production run at 1–2 hours. Emit fold predictions, calibration diagnostics, and `reports/wi009c_regression.md`.
(b) Acceptance: tests prove calibration residuals are disjoint from each model's training dates, purge/embargo is 20td, probabilities are finite/in [0,1], event calculations use the proper units, and overlap is not silently forced into a partition. The report includes calibration limits and the continuous baseline's same-sign/|IC| skill result.
(c) Verify: `uv run pytest tests/test_wi009c_continuous.py -q && uv run python scripts/train_wi009c.py --market CAD --max-dates 60 --smoke && grep -E "P\(up\)|P\(down\)|P\(stay\)|calibration|same-sign" reports/wi009c_regression.md`
(d) STOP: do not run the full detached chain unless the smoke test and leakage tests pass. On a >1–2h estimate, resource breach, non-finite probabilities, or failed skill clause, stop and report; do not tune repeatedly or suppress the negative result.

### Step 3 — Fold-safe contrastive stacked-input candidate and shortlist composite
(a) If Step 1 permits feature spend and Step 2 passes its smoke/leakage checks, extend `scripts/train_wi009c.py` to accept `models/contrastive_ranker_wi009b.pt` through `score_numpy` as one candidate regressor input. Produce training scores from fold-training-only weights (or establish and test an equivalent training cutoff); evaluate against the same folds without replacing the continuous model or final probability ranking. Add the deterministic shortlist output with score `P(up)-P(down)` and report `P(stay)`.
(b) Acceptance: a regression test demonstrates no held-out date contributes to its score model; baseline and stacked results are comparable on identical folds; output probabilities/composite are finite and shortlist ordering matches the declared formula.
(c) Verify: `uv run pytest tests/test_wi009c_stacking.py -q && uv run python scripts/train_wi009c.py --market CAD --max-dates 60 --smoke --contrastive && grep -E "score_numpy|fold-safe|P\(up\)-P\(down\)" reports/wi009c_regression.md`
(d) STOP: if fold-safe scoring cannot be established, omit the candidate and document why; never feed an in-sample score or promote the contrastive ranker to final ranking.

### Step 4 — Evidence-gated robustness options (optional)
(a) In `scripts/train_wi009c.py`, expose separate optional switches for (1) trailing market-state/regime features, (2) factor + contrastive + regressor stacking, and (3) dynamic feature selection. Implement/run only an option justified by Step 1 evidence and a documented weakness in the core continuous baseline; compare one option at a time on identical purged folds. Leave other candidates unbuilt when their gate is unmet.
(b) Acceptance: each attempted option records its Step-1 go/no-go rationale, feature provenance, and same-sign/|IC| comparison; no option is accepted unless it passes the unchanged skill bar. Unattempted options are explicitly marked NOT RUN with reason.
(c) Verify: `uv run pytest tests/test_wi009c_robustness_gates.py -q && uv run python scripts/train_wi009c.py --market CAD --max-dates 60 --smoke --robustness-report && grep -E "regime|stacking|dynamic feature|NOT RUN|go/no-go" reports/wi009c_robustness.md`
(d) STOP: do not build all candidates by default, expand the feature set after a failed probe, or run a gated option without its written go decision.

### Step 5 — Final evaluation, reports, and human gate package
(a) Add/update `scripts/evaluate_wi009c.py` and tests to regenerate `reports/wi009c_*.md` from the fixed run outputs: probe, continuous baseline, accepted candidate comparisons, calibration, skill-bar result, event-unit/overlap note, and shortlist. Clearly distinguish negative results from execution/test failures. No live-use integration.
(b) Acceptance: all WI-009c tests and the full suite pass; reports are reproducible from saved outputs, list the exact model/fold/run, show `P(up)`, `P(down)`, `P(stay)` and the declared composite, and leave any claim/use decision to the human gate.
(c) Verify: `uv run pytest tests/test_wi009c_*.py -q && uv run python scripts/evaluate_wi009c.py --market CAD && grep -E "P\(up\)|P\(down\)|P\(stay\)|same-sign|human gate" reports/wi009c_summary.md && uv run pytest -q`
(d) STOP: do not mark a sprint gate passed or wire the shortlist to orders; present the report for human review.

## OUT OF SCOPE
- Independent binary classifiers as final models; live trading, orders, or automated execution.
- Rebuilding CAD features/targets, changing thresholds, changing the 20td purge/embargo, or changing skill-bar criteria.
- Running all robustness options, broad hyperparameter search, or exceeding one detached 1–2h regressor chain.
- Treating probability calibration as a guarantee of conditional calibration or the shortlist as trade advice.

## EXECUTION LOG
| Time | Step | Outcome | Concerns |
|---|---:|---|---|
| 06:19 | step 0 | PASS — added `scripts/check_wi009c_inputs.py`; wrote `reports/wi009c_inputs.txt`. Verify ran clean (exit 0): `features_CAD.parquet` 701599 rows / 89 float32 feature cols; `targets_CAD.parquet` 701599 rows / 5 int8 labels; (date,symbol) alignment dates identical=True, symbols identical=True, 0 dup keys; `y_20d_stay` base rate 44.84% (0.04pp from 44.8%, tolerance 0.5pp). Checker names the route inputs: continuous target `fwd_atr_ret_20 = (close.shift(-20) - close) / wilder_atr_20` (derived per symbol from raw OHLCV, not a parquet column) and ATR/price col `atr_pct_20` = wilder_atr_20/close (99.75% finite); thresholds TREND_ATR_MULT=2.0 (ATR-dollar), STAY_RET_MAX=0.05 (relative). No source data altered. | Plan Step 1(a) names the 20d labels `y_20d_high`/`y_20d_low`; the artifacts actually contain `y_15d_high`/`y_15d_low` (schema + `src.targets.TARGET_COLUMNS`). Used the real columns; the plan's `y_20d_high/low` grep alternates match nothing (steps 0/1 greps still exit 0). |
| 06:21 | step 1 | NEGATIVE RESULT (recorded, not hidden) — added `scripts/probe_wi009c.py`; full CAD run wrote `reports/wi009c_probe.md`. Verify ran clean (exit 0). Panel 677,313 rows · 2691 dates · 313 symbols; five E5 factors only, logistic OOF probabilities via `PurgedWalkForwardSplit(5, embargo_td=20)` keyed by `date_positions`. OOF logit IC vs best single factor (same rows/dates, same-sign + |IC|≥ clause): `y_15d_high` +0.0001 vs `vol_20` +0.0288; `y_15d_low` +0.0304 vs +0.0288 (sign NO); `y_20d_up` +0.0123 vs `vol_20` +0.0307 (sign NO); `y_20d_down` -0.0231 vs +0.0307 (sign NO); `y_20d_stay` -0.0355 vs `rev_1m` +0.0669. **0/5 targets clear the bar** → labels not demonstrated learnable. Fold evidence: all 15 folds gap=20td, `purge_ok` OK. | (1) Per Step 1(d) STOP clause: no 89-feature spend, no optional candidates; the continuous baseline is limited to the same five factors. (2) Build assumption documented in the report: binary labels are scored against the aligned continuous forward move with `TARGET_DIRECTION` sign, and `y_20d_stay` against `-|fwd_atr_ret_20|` (the plan fixes the bar, not the per-label reference); class-label IC is never used. (3) Admin-adopted clause (a) is `same sign AND |IC| ≥`; `src.models.skill_bar` implements the strict-|IC| magnitude test, so `≥` is applied on top in the probe without editing the module (reuse preserved; differs only on exact ties). |

## Deviations

- **Target names.** The plan's Step 1(a) lists `y_20d_high`/`y_20d_low`; the CAD artifact carries `y_15d_high`/`y_15d_low` (`TARGET_COLUMNS`, and WI-009c research doc line 25 lists the same five labels). Treated as a naming slip in the plan, not a missing artifact — the real five columns were probed. Step 0 was NOT stopped because the actual artifacts match the plan's Step 0 acceptance criteria (five existing binary target columns, counts, dtype, base rate) exactly.
- **Probe reference metric (Build assumption).** The plan fixes the skill-bar bar but not how a *binary* label maps onto the score-based IC. Chosen mapping, documented in `reports/wi009c_probe.md`: `TARGET_DIRECTION`-signed `fwd_atr_ret_{15,20}` per label, `-|fwd_atr_ret_20|` for `y_20d_stay`. Flagged for the Planner in case Step 2's reference must follow a different convention.
- **Board state.** `docs/workflow/BOARD.md` has WI-009c in READY, not EXECUTING; this session executed steps 0–1 on explicit admin instruction and did not touch the board (PM owns board updates).

STATUS: DONE (steps 0-1) | evidence: `uv run python scripts/check_wi009c_inputs.py && grep -E "701599|y_20d_stay|continuous target|ATR" reports/wi009c_inputs.txt` (exit 0, STEP 0 CHECKER: PASS) and `uv run python scripts/probe_wi009c.py --market CAD && grep -E "y_20d_(up|down|stay|high|low)|same-sign|negative result|purge" reports/wi009c_probe.md` (exit 0, 0/5 targets clear the skill bar — documented negative result, Step 1(d) STOP clause applies: no 89-feature spend)
