# WI-009c Step 4 — evidence-gated robustness options (CAD)

- Generated (UTC): 2026-10-25T10:01:03Z  · **SMOKE INVOCATION**
- Gate evidence source: `reports/wi009c_regression_CAD.json` — production run record (smoke=False, generated 2026-10-25T09:37:29.623154+00:00), read so a `--smoke` invocation cannot record thinner gate evidence
- Step-1 evidence: 0/5 labels cleared the unchanged skill bar in `reports/wi009c_probe.md` → 89-feature/optional-candidate spend **NOT permitted** (fail-closed).
- Fixed purge/embargo reused unchanged: 20 trading days (`src.models.skill_bar.EMBARGO_TD`).
- Baseline limited to the same 5 E5 factors (plan Step 1(d)); the wider pool is 89 features and is not read.

## go/no-go gate table (Step 1 evidence + documented baseline weakness)

| Option | Switch | Gate decision | Gates (met / total) | Status | Specific unmet gate |
| :--- | :--- | :--- | ---: | :--- | :--- |
| Trailing market-state / regime features | `--robustness-regime` | **NO-GO** | 1 / 2 | **NOT RUN** | `step1_permits_feature_spend` |
| Factor + contrastive + continuous-regressor stacking | `--robustness-stacking` | **NO-GO** | 0 / 2 | **NOT RUN** | `step1_permits_feature_spend`, `contrastive_score_fold_safe` |
| Dynamic feature selection (per-fold subset of the 89-feature pool) | `--robustness-dynamic` | **NO-GO** | 1 / 2 | **NOT RUN** | `step1_permits_feature_spend` |

- Options attempted: **0** · options reported **NOT RUN**: **3** · options whose gate decision was GO: 0 of 3.
- No option is accepted unless it then passes the **unchanged** skill bar on identical purged folds; the bar is reused from `src.models.skill_bar`, never weakened or redefined.

## Baseline reference used for the go/no-go

- Continuous 20td baseline (5 E5 factors, `StandardScaler` + `Ridge`): IC +0.0001 (t +0.03) vs `e5_vol_20` |IC| +0.0307; same-sign False → **FAIL** the unchanged skill bar.

## Trailing market-state / regime features — NOT RUN

- Switch: `--robustness-regime` · gate decision **NO-GO**.
- Reason: gate(s) unmet — step1_permits_feature_spend: plan Step 1(d)/Step 4(d): 0/5 labels cleared the unchanged skill bar in `reports/wi009c_probe.md`, so the 89-feature spend and every optional candidate stay gated and the feature set may not be expanded after a failed probe. Optional candidate left unbuilt (plan Step 4(a)/(d)); this is a documented no-go, not an execution failure.
- Gates:

| Gate | Met | Evidence |
| :--- | :--- | :--- |
| `step1_permits_feature_spend` | NO | plan Step 1(d)/Step 4(d): 0/5 labels cleared the unchanged skill bar in `reports/wi009c_probe.md`, so the 89-feature spend and every optional candidate stay gated and the feature set may not be expanded after a failed probe. |
| `baseline_weakness_documented` | yes | continuous baseline skill bar FAIL: IC +0.0001 (t +0.03) vs `e5_vol_20` |IC| +0.0307, same-sign False — a documented weakness exists to aim an option at (necessary, not sufficient: the Step-1 gate above is also required). |

- Feature provenance: would add **trailing** market-state/regime columns computed from raw OHLCV through `src.factors.e5_baseline.build_e5_panel` (trailing windows only, so no forward-looking window enters a training row). Nothing is read from `data/features/features_CAD.parquet`, and no column is built in this work item: that is feature spend, gated by Step 1(d).
- What would have been compared: same-sign and |IC| of the option vs the five E5 factors on **identical purged folds** (same fold plan, same 20td purge, same out-of-fold rows); an option is accepted only if it then passes the **unchanged** skill bar — clause (a) same sign as the best factor AND |IC| >=, clause (b) |t| > 2 with a stable sign in >= 2 disjoint sub-windows.

## Factor + contrastive + continuous-regressor stacking — NOT RUN

- Switch: `--robustness-stacking` · gate decision **NO-GO**.
- Reason: gate(s) unmet — step1_permits_feature_spend: plan Step 1(d)/Step 4(d): 0/5 labels cleared the unchanged skill bar in `reports/wi009c_probe.md`, so the 89-feature spend and every optional candidate stay gated and the feature set may not be expanded after a failed probe.; contrastive_score_fold_safe: plan Step 3(a)/(d): fold-safe contrastive score — status NOT RUN, fold_safe None. Step 1 gate (plan Step 1(d)): no label cleared the unchanged skill bar, so the 89-feature spend and all optional candidates stay gated; the contrastive score is an 89-feature model output, so it is omitted and documented, not run. Optional candidate left unbuilt (plan Step 4(a)/(d)); this is a documented no-go, not an execution failure.
- Gates:

| Gate | Met | Evidence |
| :--- | :--- | :--- |
| `step1_permits_feature_spend` | NO | plan Step 1(d)/Step 4(d): 0/5 labels cleared the unchanged skill bar in `reports/wi009c_probe.md`, so the 89-feature spend and every optional candidate stay gated and the feature set may not be expanded after a failed probe. |
| `contrastive_score_fold_safe` | NO | plan Step 3(a)/(d): fold-safe contrastive score — status NOT RUN, fold_safe None. Step 1 gate (plan Step 1(d)): no label cleared the unchanged skill bar, so the 89-feature spend and all optional candidates stay gated; the contrastive score is an 89-feature model output, so it is omitted and documented, not run. |

- Feature provenance: would append the fold-safe `score_numpy` output of `models/contrastive_ranker_wi009b.pt` as **one** extra column on the five E5 factors (via `src.models.continuous_targets.stacked_input_matrix`), never replacing the continuous model and never becoming the final ranking. The score is an 89-feature model output, so using it is 89-feature spend — gated by Step 1(d) — and its fold-safety must be established first (Step 3(a)/(d)).
- What would have been compared: same-sign and |IC| of the option vs the five E5 factors on **identical purged folds** (same fold plan, same 20td purge, same out-of-fold rows); an option is accepted only if it then passes the **unchanged** skill bar — clause (a) same sign as the best factor AND |IC| >=, clause (b) |t| > 2 with a stable sign in >= 2 disjoint sub-windows.

## Dynamic feature selection (per-fold subset of the 89-feature pool) — NOT RUN

- Switch: `--robustness-dynamic` · gate decision **NO-GO**.
- Reason: gate(s) unmet — step1_permits_feature_spend: plan Step 1(d)/Step 4(d): 0/5 labels cleared the unchanged skill bar in `reports/wi009c_probe.md`, so the 89-feature spend and every optional candidate stay gated and the feature set may not be expanded after a failed probe. Optional candidate left unbuilt (plan Step 4(a)/(d)); this is a documented no-go, not an execution failure.
- Gates:

| Gate | Met | Evidence |
| :--- | :--- | :--- |
| `step1_permits_feature_spend` | NO | plan Step 1(d)/Step 4(d): 0/5 labels cleared the unchanged skill bar in `reports/wi009c_probe.md`, so the 89-feature spend and every optional candidate stay gated and the feature set may not be expanded after a failed probe. |
| `feature_pool_larger_than_baseline` | yes | plan Step 4(d): feature selection needs a candidate pool larger than the 5 baseline factors; the only larger pool is the 89-feature matrix, whose read is the gated 89-feature spend. |

- Feature provenance: would select a per-fold subset of the 89 `float32` columns of `data/features/features_CAD.parquet` (bounded, `pyarrow.dataset` date chunks). Reading that pool *is* the 89-feature spend gated by Step 1(d); with the baseline deliberately limited to the same five factors, there is no larger pool in scope to select from.
- What would have been compared: same-sign and |IC| of the option vs the five E5 factors on **identical purged folds** (same fold plan, same 20td purge, same out-of-fold rows); an option is accepted only if it then passes the **unchanged** skill bar — clause (a) same sign as the best factor AND |IC| >=, clause (b) |t| > 2 with a stable sign in >= 2 disjoint sub-windows.

## Gate semantics (why nothing was built)

- Each switch evaluates its gate **first** and refuses to build or run the candidate while the gate is unmet, so no feature spend occurs. Plan Step 4(d): do not build all candidates by default, do not expand the feature set after a failed probe, and do not run a gated option without its written go decision.
- No option body is implemented in WI-009c: the deliverable of this step is the recorded go/no-go per candidate, not a model. A GO decision would have to be authored by the Planner before any option runs.
- This is a **documented no-go**, not an execution failure: the gates were evaluated, the evidence is named per option, and the candidate was left unbuilt on purpose.
- Nothing here replaces the skill bar, the 20td purge/embargo, or the human gate.

## Reading notes

- The Step-1 negative result (0/5 labels clear the unchanged skill bar) is the single gate that blocks all three candidates: every one of them needs the 89-feature spend that Step 1(d) withholds.
- The stacking candidate is blocked twice — by the Step-1 gate and, independently, because fold-safe contrastive scoring could not be established (the saved artifact's recorded cutoff 2026-05-28 falls inside the last fold's validation window; a per-fold refit would itself be 89-feature spend).
- For dynamic feature selection there is nothing to select from while the baseline is deliberately limited to 5 factors — reading the 89-feature pool is the gated spend.
- Options are compared on identical purged folds whenever they do run, so a later GO cannot silently change the baseline's fold plan.

