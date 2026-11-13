## Recommendation

Adopt **volatility-regime and payoff-shape** as the governing thesis for the next round. The mean-reversion swing detector stays as the **event sampler** and the **meta-label primary**. It does not drive feature design.

Before any new run, dispatch a **Phase-0 hygiene batch**. It needs no new training (one 0.25 core-h timing probe aside) and does four things:

1. Verify the `vol_expand` window definition.
2. Run an "objective-inversion" diagnostic on the existing OOF scores.
3. Build the precision@k / top-decile harness.
4. Run a timing probe.

Then run **six net-new L0 blocks** and **four net-new L1 items**, ranked below. For the L1 layer, pursue **meta-labeling (swing-side primary, decomposed as P(touch)·P(profit | touch))** first, with **seed-averaging** as the cheap companion benchmark. Do not stack.

## Goal

Deliver a ranked, buildable L0/L1 extension plan with these properties:

- At least six net-new items, each with owner, core-h, one BH-FDR family, finish condition and EV-proxy rationale.
- Raises **precision@small-k** and **top-decile calibration** toward the ~10%/trade, ~200 trades/yr product objective.
- Stays **predictive-only** at L1 (D-023).

## Current conditions

- **L0:** 249 classified columns (coverage 1.000). Signal is concentrated in about 8–10 volatility, path-shape and event-geometry columns. Four families (volume, sector, mean-reversion, breadth) carry zero permutation evidence.
- **L1:** 9,745-row manifest. Within the three-binary family only `b_hold` survives. WI-048 T2 survivors are PROVISIONAL: `vol_expand` 24/24, `high_low` 24/24, `up` 11/24 at AUC ≈ 0.50.
- **L2:** closed. Statistical signal exists but EVAL edge is about 0 versus 25 bps.
- **Locks:** WI-048 d/e/f locks are not cleared. This is a human pre-dispatch action.
- **Compute:** 2 vCPU / 8 GB / credit model. Cap is 2.5 core-h per WI, checkpointed, with pacing footer.

## Ideal result

The 11 sections below, plus a phased dispatch plan, three risks with mitigations, open questions, and change-my-mind conditions.

---

## 1. Status assessment (confirm / correct)

**Confirmed**
- Panel build, causality and dimensionless design.
- Concentration of attribution in the volatility, path-shape and event-geometry axis.
- WI-048 ranking `vol_expand` > `high_low` > `up`.
- L2 closed.

**Corrections and missing distinctions**

1. **"249 columns" is the wrong unit for predictive capacity.**
   - Five are keys (`symbol/date/state/close/atr`). `close` and `atr` are absolute levels, and the design excludes absolute levels. That leaves **244 candidate predictors**.
   - 102 `cs_*` columns are same-date rank transforms of the ~111 grid features. 12 are sector dummies.
   - The effective count of independent base signals is roughly **110**, and fewer after collinearity.
   - Report future blocks as "base signals added" and "transformed columns added" separately.
   - **Phase-0 check:** confirm `close` and `atr` are excluded from every model's feature list in the manifest.

2. **`b_hold` is a finding about quietness, not a 10% engine.**
   - `b_hold` = neither the ±k·ATR profit nor stop barrier is touched within h. Its positive class is the *calm* outcome.
   - Its high AUC (0.78 USD) says the model can tell which events will stay inside a band. That is volatility-shaped, consistent with the thesis.
   - Its **direct product use is as a negative filter**: high P(b_hold) means drop the name.
   - Within the deployment window, only `b_hold` h∈{5..55} cells are eligible. The h89 cell is out of the ≤63-day window.

3. **`vol_expand` may select the wrong names for the objective.**
   - The label is self-relative ("next-window vol > this window's vol"). Volatility mean-reverts, so positives are plausibly concentrated in names that are *currently compressed*.
   - That is not the same as "high-vol name with room to run."
   - Its 0.7068 AUC is real predictive evidence but may be partly an inversion of the EV intent.
   - **Phase-0 diagnostic:** slice existing OOF top-decile scores by current `atr_pct_21` own-history tercile. This is descriptive only, with no new fits and no FDR.

4. **`vol_expand` window definition must be verified.**
   - The pack defines it as "realized vol of the h log-returns *ending at t*" > prior h-window.
   - Read literally, the label is computable at t and is not a forward target. An AUC of 0.70 rather than ~1.0 suggests the code actually uses `[t+1, t+h]` against a window ending at t.
   - This must be confirmed in `src/swing_bsh/targets_ext.py` before any item below builds on `vol_expand`.

5. **`up` survivors (11/24) at AUC ≈ 0.504** are correct under the no-effect-size-floor licence, because n ≈ 117k per cell gives large power. Their EV-proxy is nil. Rank them last for screener use, but leave them in the library.

6. **`high_low` has a base rate of 0.75–0.87.**
   - The precision@k lift ceiling is at most about 1/0.8 = 1.25×.
   - Its AUC (0.61) overstates its usefulness for a precision-first screen.
   - Report lift-over-base, not raw precision.

7. **The thesis tension is resolved here.**
   - Mean-reversion features are silent and mean-reversion *targets* (`b_profit`) have no survivors.
   - The evidence supports volatility-state and payoff-shape.
   - No new mean-reversion feature blocks are proposed. Mean-reversion survives as the event geometry and the meta-label primary's side.

---

## 2. Ranked extension items

**Common protocol for L0 blocks: Reference grid R12.**
- Each block is added to the panel and evaluated on one fixed grid:
  - 2 reference targets: `b_hold` (three-binary, `*_full_k0.8`) and `vol_expand` (T2).
  - × horizons {8, 13, 21} × lightgbm × 2 markets (USD `exact`, CAD `tol2`).
  - = **12 cells, one BH-FDR family (m = 12), α = 0.05**.
- The test statistic is the fold-paired OOF AUC delta against the baseline panel, under `PurgedWalkForwardSplit(embargo=max(20,h))`.
- Baseline OOF is reused from the manifest where fold IDs and seeds match; otherwise it is refit inside the same WI.
- Block permutation importance and precision@k lift (§8) are reported as diagnostics.
- Every block must pass a **truncation-invariance test**: the feature computed on data truncated at t equals the full-data value at t.

**Common protocol for L1 targets.**
- 6 horizons {5, 8, 13, 21, 34, 55} × {lightgbm, xgboost} × 2 markets = **24 cells per family (m = 24)**.
- Binary and continuous forms are separate families and separate WIs.
- If a 24-cell family exceeds 2.5 core-h in the Phase-0 timing probe, split it by market into two WIs. Each half keeps the **same pre-registered family (m = 24)**, and BH runs once after both halves finish.

Core-h figures are **projections pending the Phase-0 timing probe**. The pack gives no measured core-h for the WI-048 runs.

### 2a. L0 — features (net-new)

| rank | item | tier | mechanism | EV-proxy rationale (predictive) | cost core-h | BH-FDR family | finish condition | owner | depends |
|---|---|---|---|---|---|---|---|---|---|
| L0-1 | **Swing-structure history** (~6 base cols): current swing depth ÷ median of last 4 confirmed swing depths; swing-duration ratio; HH/HL vs LH/LL count over last 4 confirmed pivots; amplitude trend of last 3 swings; bars since last same-side pivot | L0 | Extends the event-geometry axis that already tops attribution (`swing_depth_atr`, `bars_since_opp`). Practitioner market-structure reading: expanding swing amplitudes mark a trending or volatile regime. Uses **only pivots whose confirmation bar is ≤ t**. | Larger prior swings mean a larger plausible next move. This targets the payoff ratio and top-decile separation directly. Plausibility toward ~10%: **high**. | 2.0 (detector re-pass, symbol-sequential) | `L0-SWINGHIST/R12`, m = 12 | BH table + ΔAUC + precision@k lift written; truncation test **and** pivot-confirmation-lag unit test pass; verdict PROVISIONAL | feature engineer (L0) | Phase 0 |
| L0-2 | **Realized-asymmetry block** (~6): upside/downside realized semivariance ratio (21, 63); realized skewness (21, 63); realized kurtosis 63; "good minus bad" vol share | L0 | Realized semivariance (Barndorff-Nielsen, Kinnebrock & Shephard 2010 *[verify]*) and signed jump variation (Patton & Sheppard 2015 *[verify]*) predict future vol differently by sign. Realized skewness is linked to subsequent return distribution (Amaya et al. 2015 *[verify]*). Distinct from WI-047 #2, which covers *levels* of range estimators, not return-distribution *shape*. | Speaks to avg_win ÷ avg_loss, the payoff half of EV, rather than p(win). Expected to separate fat-right-tail setups in the top decile. Plausibility: **medium-high**. | 1.5 | `L0-ASYM/R12`, m = 12 | as above | feature engineer (L0) | Phase 0 |
| L0-3 | **Regime age / run-length** (~5): bars since `atr_pct_21` last crossed its trailing-233 median; length of current range-compression run; bars since last 55-bar high and since last 55-bar low; count of compression→expansion transitions in 233 bars | L0 | A new meta type, **temporal duration**, absent from the meta-relation table. Squeeze-duration practice (Bollinger/Keltner "squeeze" *[verify]*) holds that long compressions precede large releases. | Duration discriminates "about to release" from "just released". This directly attacks the §1.3 inversion risk and sharpens top-k timing. Plausibility: **medium-high**. | 1.5 | `L0-AGE/R12`, m = 12 | as above; plus a collinearity report against WI-047 #1 percentiles if those have landed | feature engineer (L0) | Phase 0; soft on WI-047 #1 |
| L0-4 | **Jump-intensity block** (~5): bipower-variation jump share (BV/RV, 21 and 63); count of \|r\| > 3σ bars in 63; max \|r\|-z in 21; days since last jump | L0 | Barndorff-Nielsen & Shephard 2004 bipower variation *[verify]*. Jump-prone names have heavier tails, which is the plausibility condition for 10% moves. Distinct from `overnight_gap_z` (one bar) and from WI-047 level estimators. | Raises P(large excursion) in top-k. Risk: it also raises adverse excursion, so it should be read jointly with L1-2. Plausibility: **medium**. | 1.5 | `L0-JUMP/R12`, m = 12 | as above | feature engineer (L0) | Phase 0 |
| L0-5 | **Universe vol-regime dispersion** (~4, date-level, broadcast): cross-sectional return dispersion 21; fraction of universe with `atr_pct_21` in own top tercile; EW-index variance ÷ mean name variance (average-correlation proxy); 21-bar change in that fraction | L0 | `cs_entropy_102` attribution says the *market-wide* regime matters. Dispersion and correlation regimes are standard in quant practice. Distinct from `breadth_*` (swing breadth) and from WI-047 #3 (per-name beta/corr/residual). **Flag to admin:** it may be judged a WI-047 #3 variant; if so it moves to that WI and loses net-new status. | High dispersion with low correlation means stock-specific large moves are more available. It conditions the whole top-k list on date. Plausibility: **medium**. | 1.0 | `L0-DISP/R12`, m = 12 | as above; plus admin net-new ruling recorded | feature engineer (L0) | Phase 0 |
| L0-6 | **Effort-vs-result (Wyckoff) block** (~5): range-per-volume z at detection bar; detection-bar volume z ÷ mean volume z of the swing leg; up-volume ÷ down-volume 21; climax flag (top-5% volume and top-5% range in 233) | L0 | Wyckoff effort/result and climax concepts (practitioner *[verify]*). Volume is a zero-evidence family *as levels*; this tests a *relational* form. Distinct from WI-047 #4 (dollar-volume / Amihud percentiles). | Climax at an extreme is the classical "exhaustion → large reversal" setup. Payoff-ratio-relevant if it works. Plausibility: **low-medium** (volume has been silent). | 1.5 | `L0-WYCK/R12`, m = 12 | as above | feature engineer (L0) | Phase 0 |

### 2b. L1 — targets, conditioning and method (net-new)

| rank | item | tier | mechanism | EV-proxy rationale (predictive) | cost core-h | BH-FDR family | finish condition | owner | depends |
|---|---|---|---|---|---|---|---|---|---|
| L1-1 | **Forward cross-sectional vol rank**: same-date percentile of forward h realized vol across the universe. **Binary** = top decile; **continuous** = the rank. | L1 | Turns the self-relative `vol_expand` into a *universe-relative* target, matching the screener's job of picking the few names with the most room. Vol is the most forecastable quantity in finance (HAR lineage, Corsi 2009 *[verify]*). | Directly removes the §1.3 inversion: positives *are* the high-vol names. Precision@k against this label is nearly the product question. Plausibility: **high**. | 2.0 per form | `L1-FXVR-BIN` (m = 24); `L1-FXVR-CONT` (m = 24, rank-IC) | Both families' BH tables, AUC or rank-IC, precision@k lift, top-decile ECE written; label built per date with symbol-sequential reads; PROVISIONAL | L1 modeller | Phase 0 (vol_expand def. check) |
| L1-2 | **Payoff-ratio target (MFE/MAE)**: on swing-side direction, max favourable ÷ max adverse excursion in `[t+1, t+h]`, ATR-scaled. **Continuous** = log(MFE/MAE); **binary** = MFE ≥ 2·MAE. | L1 | Excursion-based labels are standard in trade research and are a continuous generalisation of triple-barrier (López de Prado 2018 *[verify]*). Distinct from magnitude buckets (size only) and time-to-touch (timing only). | This is the payoff-ratio term of EV made into a label. Predictive lift moves avg_win/avg_loss, not just p. Plausibility: **high**. | 2.0 per form | `L1-MFEMAE-CONT` (m = 24); `L1-MFEMAE-BIN` (m = 24) | as above; plus a unit test that the path window starts at t+1 | L1 modeller | Phase 0 |
| L1-3 | **Expansion-direction decomposition**: model A = P(vol_expand) (existing); model B = P(swing-side direction correct \| vol_expand = 1), trained and OOF-scored only on expanded events. Screener score = A·B as a **fixed product**, not learned weights. | L1 | `up` is chance unconditionally. Direction may be predictable *conditional on* a regime break (breakout follow-through practice *[verify]*). The fixed product has no fitted meta-weights, so it is not a stack. | Converts a regime signal into a sided call, which a trade needs. Plausibility: **medium**; B may also be near chance. | 1.5 | `L1-EXPDIR` (m = 24, B-model cells only) | B-model BH table written. Joint A·B precision@k is reported descriptively, since it is not a separate test. A and B use identical purged folds. | L1 modeller | L1 vol_expand def. check |
| L1-4 | **Sample-uniqueness weighting** (average label uniqueness from overlapping windows), re-running the `b_hold` and `vol_expand` reference cells | L1 method | Overlapping labels inflate effective n and overweight clustered events (López de Prado 2018 ch. 4 *[verify]*). Weighting should improve calibration out of sample. | Top-decile calibration is the target metric; this addresses its known bias source. Plausibility: indirect, **medium**. | 1.0 | `L1-UNIQW/R12` variant grid (m = 12), never merged into the originals | ΔAUC, Δtop-decile ECE and Brier written against unweighted reference | L1 modeller | Phase 0 |

### 2c. Already-planned or ratified items, re-ranked (not counted toward the six)

1. **WI-047 #1 regime percentiles.** Run first among WI-047 items; it is the ratified regime block.
2. **Ratified L1.5 meta-labeling.** See §9; Phase 3.
3. **Self-proposed magnitude buckets and time-to-touch.**
4. **WI-047 #2 vol estimators.**
5. **WI-047 #3 market-residual context.**
6. **Cross-feature interactions.**
7. **Volatility-state terciles.** Likely redundant with L1-1.
8. **Range-occupancy.**
9. **WI-047 #4 and #5.** Volume and seasonality are lowest prior.

### 2d. Plan (dispatch phases)

Every WI carries the following:
- `START_UTC`, projected core-h, `END_UTC` and `NEXT_ALLOWED_RUN_UTC`, with at least 30 min idle after any burst of 1 core-h or more.
- Named checkpoints per (market, target, horizon) cell.
- A pause when modeled credit falls below 25%, checked by running the credit monitor with `--state <path>` before dispatch.
- A resume command of the form `uv run python <runner> --resume <checkpoint_dir>`. The runner path is fixed in each WI spec.

The earliest clean run from the brief's reference point is **≥ 18:08Z, 2026-11-13**.

**Phase 0 — hygiene, no new training**
- **Owner:** human admin (locks) + L1 modeller.
- **Cost:** ≤ 0.5 core-h total.
- **Steps:**
  1. Clear or verify WI-048 d/e/f in `.hermes/locks.json`.
  2. Verify the `vol_expand` window.
  3. Verify `close` and `atr` are excluded from model features.
  4. Build the precision@k / top-decile harness (§8) and run it on existing manifest OOF.
  5. Run the §1.3 stratified diagnostic.
  6. Run a timing probe: replay one WI-048 cell for 0.25 core-h.
- **Done when:**
  - locks are empty;
  - a definition note is committed;
  - the harness report exists for `b_hold`, `vol_expand` and `high_low`;
  - the measured core-h per cell is recorded and used to rescale all estimates above.

**Phase 1 — L0 blocks, ranks 1→6**
- **Owner:** feature engineer (L0).
- **Cost:** 1.0–2.0 each; one WI per block; about 9 core-h total across six WIs.
- **Done when:** six R12 family verdicts are written PROVISIONAL and admin ratification is requested.

**Phase 2 — L1 targets, ranks 1→4**
- **Owner:** L1 modeller.
- **Cost:** 1.0–2.0 per family WI; about 10 core-h across seven family runs.
- **Done when:** every family verdict and its §7 head-to-head descriptive table is written.

**Phase 3 — L1.5 meta-label, swing-side primary**
- **Owner:** L1 modeller.
- **Cost:** 2.0–2.5.
- **Done when:** the family verdict and top-k precision report are written.
- The fib-primary family runs only after the open question on its T3-only status is answered (§11).

**Phase 4 — seed-averaging benchmark**
- **Owner:** L1 modeller.
- **Cost:** 1.0.
- **Done when:** the descriptive Δ(top-decile ECE, precision@k) table is written.

---

## 3. Quant-trader mindset

All points here are L2-forward observations for T3, not L1 claims.

- **Where costs bite.** High-vol, jump-prone and low-liquidity names (L0-2/4/6 positives) carry wider spreads and gap risk. A 25 bps flat cost will understate this for CAD small caps. T3 should test liquidity-tiered cost, not a flat 25 bps.
- **Regime switching.** L0-3 and L0-5 are regime-state inputs. T3 must test whether top-k precision decays in regime transitions. WI-045 edge-decay is the natural host.
- **Tail risk.** MFE/MAE (L1-2) is the bridge to sizing. T3 should test vol-target sizing (already in WI-049) against MAE-percentile stops.
- **Cross-asset and lead-lag.** USD↔CAD lead-lag on the same dates is plausible but untested. It is not proposed because the pack says nothing about cross-listed symbol mapping (§11).
- **Execution.** Detection-bar features read at close imply next-open or later entry at L2. T3 must test the open-gap slippage on high-ATR names specifically.

## 4. Technical-analyst mindset

- **Market structure.** HH/HL sequences and swing-amplitude expansion (L0-1) are the classical way to classify trend versus range. They also express "a 10% move is likely" as "the last swings were big and are growing".
- **Wyckoff phase.** Climax and effort-vs-result (L0-6) approximate the selling-climax and buying-climax phases at swing extremes. They are a low prior given volume's silence.
- **Squeeze → release.** Compression duration (L0-3) is the TA expression of vol mean-reversion and pairs with L1-1.
- **Support and resistance dynamics.** `high_low` (re-touch of the extreme) already encodes support/resistance tests. Its high base rate limits it, so prefer L1-2 for magnitude.
- **Classical patterns.** Flags and triangles are not proposed. Encoding them causally and dimensionlessly is costly, and their signal largely overlaps compression and swing-structure.
- **Cycle and seasonality.** These are covered by WI-047 #5; nothing is added.

## 5. ML-for-finance mindset

- **Label engineering.** Move from symmetric first-touch toward payoff-shaped (L1-2) and universe-relative (L1-1) labels. Note that the `b_profit` null implies a plain swing-side meta-label will likely also be null (§9).
- **Sample weighting.** Use label uniqueness (L1-4). Also consider time-decay weighting as a later variant grid; it is not proposed now.
- **Purged CV.** Keep `embargo=max(20,h)`. For date-level features (L0-5) and cross-sectional targets (L1-1), folds must split by **date across all symbols**, so that no same-date leakage occurs through ranks. Confirm `PurgedWalkForwardSplit` does this (§11).
- **Feature-selection discipline.** One block per family. Report the block's permutation importance against the existing top-10 columns. Drop a block, even if it survives, if it is fully absorbed by collinearity. This is the Q1 change-my-mind rule.
- **Calibration.** Use isotonic or Platt fitted inside each training fold only. Report top-decile ECE and calibration slope per family (§8).

## 6. Conditioning-axis design

| axis | best form | why | multiplicity consequence |
|---|---|---|---|
| **High / med / low vol regime** | **Feature** (ratified WI-047 #1 regime block, plus L0-3 duration) | Cheapest, and the family already carries signal. Stratification would spend 3× budget for a question the features answer. | Feature form: m stays 12 or 24. Stratified form: m × 3 (24 → 72) in one family, run **without** the regime feature. Never both in one run. Post-hoc OOF slicing (Phase 0) is descriptive only, with no p-values. |
| **Velocity of change** | **Target** (self-proposed velocity / time-to-touch family) | Velocity is an outcome property; feature-side slopes already exist (`rsi_14_slope_5`, trend ratios). | New family; binary and continuous as two families, m = 24 each. |
| **Peak/bottom vs middle 50%/75%** | **Stratification**, on two disjoint bands: outer 25% (top 12.5% + bottom 12.5%) vs middle 50% of `range_position`. The 75% split is a **separate variant grid**, never merged. | Swing events are by construction near extremes, so the axis mainly tests whether the signal differs by depth of extremity. The range-occupancy target (self-proposed) covers the outcome side. | m × 2 per family (24 → 48). Nested bands would double-count, so use disjoint bands only. If non-event mid-range bars are needed, that is a new sampling design (§11). |

## 7. Binary vs continuous target families

**Protocol**
- Each form is its own pre-registered family and its own WI.
- Both forms share identical purged folds and seeds.
- **Binary:** OOF AUC, BH on per-cell AUC p-values (the same test as WI-048).
- **Continuous:** per-date Spearman rank-IC, averaged, with t-stat over date blocks; BH within family. Learners are lightgbm and xgboost regression objectives (already available).

**Head-to-head (descriptive, not a gate)**
- Both scores are evaluated against the **binary event definition**, using precision@k and top-decile reliability.
- Both scores are also evaluated against the **continuous rank**, using rank-IC.
- The result is one table per target. L2 decides deployment.

**Expected favouring**
- MFE/MAE (L1-2) and forward CS vol rank (L1-1) likely favour **continuous**, because the information is graded and the binary cut discards it.
- Expansion direction (L1-3) and the ≥10% magnitude event are naturally **binary**.
- Time-to-touch is **continuous / survival**.

WI-025 is cited as prior only; there is no baseline reuse.

## 8. Precision-first evaluation addendum (predictive-only)

Reported for every family as predictive diagnostics with no economic verdict:

- **Per-date precision@k.**
  - Within each OOF fold, rank all events firing on a date. k ∈ {1, 3, 5} per date.
  - Also report pooled top {0.1%, 1%, 10%} of OOF scores.
  - Show precision, base rate and **lift = precision ÷ base rate**.
  - CIs come from a block bootstrap over dates, with block size ≥ max(20, h).
- **Top-decile calibration.** ECE restricted to the top score decile; calibration slope and intercept in the top decile; a reliability plot with 10 bins inside the top decile.
- **Selection-volume check.** Events per year passing each k, compared against the ~200/yr deployment intent. This is reported as a count only.
- **Payoff ratio implied by target construction.** For barrier targets this is k_profit ÷ k_stop. For L1-2 it is the median label value in the selected set. This is a label descriptor, not returns, PnL or costs.
- **Header line.** Every report states "PREDICTIVE DIAGNOSTIC — no economic claim (D-023)".

## 9. L1-layer options assessment (stacking deferred)

| option | expected lift | cost | finish condition | where it leaks | licence | verdict |
|---|---|---|---|---|---|---|
| Single per-cell model (status quo) | baseline | 0 | already met | none beyond fold design | L1 | keep as reference |
| Per-market horizon pooling (horizon as feature) | small-medium; more data per model | 1.5 | ΔAUC/ECE vs per-cell on the same cells | overlapping windows across horizons: embargo must be max(20, h_max = 55) | L1 | benchmark later |
| Cross-market pooling (USD+CAD + market flag) | medium for CAD (lower AUC, smaller panel) | 2.0 | CAD ΔAUC with USD unchanged | same-date cross-market info: split folds by date globally | L1 | second-in-line |
| Multi-task (mlp_torch, heads b_hold / vol_expand / high_low) | uncertain | high on 2 vCPU; likely > 2.5 | — | shared-trunk selection across heads | L1 | defer |
| **L1.5 meta-labeling, swing-side primary** (ratified) | **highest precision@k potential** | 2.0–2.5 | family verdict + §8 report | **using L1 OOF scores as meta-features = stacking → forbidden now**; use detection-bar features + side only | L1 (predictive) | **pursue first** |
| Seed / bagging averaging (same learner, same folds) | small AUC, better top-decile ECE stability | 1.0 | descriptive Δ table | mild if learners are chosen by OOF; fix the learner a priori | L1 | **pursue as companion** |
| Stacking | possibly medium | high (nested purged CV ≈ 2× compute) | — | severe: 9,745 pickles invite selection-on-OOF; top-decile calibration unstable | — | **do not build** |

**Meta-label design note.**
- A swing-side meta-label with "first touch at profit barrier" as the positive class is essentially `b_profit`, which had no survivors. Re-running it unchanged would likely reproduce the null.
- Recommended form: **P(not hold) · P(profit | touched)**, as a fixed product.
  - `1 − b_hold` comes from the existing survivor.
  - The new model is trained only on touched events, so the class balance and the question both differ.
- Alternative positive class, per the DECISIONS option: the magnitude event (MFE ≥ X·ATR before stop). It is a separate family, not merged.

**Stacking.** If stacking is ever revisited, the finish condition must include a leakage test:
- nested purged/embargoed CV;
- a permuted-label stack must return AUC ≈ 0.5;
- stacked top-decile ECE must not degrade out of fold.

## 10. Three biggest risks + cheapest mitigation

1. **Objective inversion.** Surviving signals (`b_hold` quiet, `vol_expand` self-relative) may rank *compressed* or *calm* names top, so precision is high on the wrong population.
   - *Mitigation:* the Phase-0 stratified OOF diagnostic, with zero fits, plus prioritising L1-1, whose positives are high-vol by construction.
2. **Leakage in new constructs.** Candidate sources:
   - pivot-confirmation lag (L0-1);
   - same-date cross-sectional ranks under fold splits (L0-5, L1-1);
   - label windows starting at t rather than t+1 (L1-2, `vol_expand`);
   - meta-features drifting into stacking.
   - *Mitigation:* a truncation-invariance unit test per block, a label-window unit test per target, and a date-global fold check. Each is a few minutes of CPU.
3. **Compute over-run and credit exhaustion.** Core-h estimates are unmeasured.
   - *Mitigation:* the 0.25 core-h Phase-0 timing probe rescales every WI before dispatch. Market-split WIs keep each run ≤ 2.5 core-h, and the pre-registered m is unchanged.

Secondary risk: **multiplicity sprawl** across about 15 new families. Mitigate by pre-registering the family ledger on BOARD.md before Phase 1.

## 11. Open questions

These are places where the pack is silent or unresolved. They are not guessed.

- Is `vol_expand`'s first window `[t+1, t+h]` or "ending at t" as written?
- Should the frozen fib rule serve as an L1.5 primary, given its recorded T3-only status? The fib meta family is held until this is answered.
- What does "swing side wins" mean operationally: first-touch barrier, horizon close, or both? The §9 decomposition assumes first-touch.
- Is EV-proxy ranking at L1 a selection criterion for screener eligibility, or a diagnostic only? This plan treats it as diagnostic.
- Is the 10% figure gross pre-cost at L2, with 25 bps applied only there?
- Should the d/e/f locks be cleared before dispatch? This is assumed yes, as a Phase-0 human step.
- What are the measured core-h of the WI-048 72-cell grid?
- Does `PurgedWalkForwardSplit` split by date across all symbols?
- Do cross-listed USD/CAD symbols exist, and is there a mapping? This affects lead-lag and cross-market pooling.
- Are non-event mid-range bars available or allowed as a sample for the peak-vs-mid axis?
- Is L0-5 net-new or a WI-047 #3 variant? This needs an admin ruling.
- Which literature citations survive verification? All are marked *[verify]*.

## What would change this plan

- **If Phase 0 shows `vol_expand` top deciles are *not* concentrated in compressed names:** drop L1-1 to rank 3 and promote L1-2.
- **If the `vol_expand` label proves to be computed at t:** quarantine all `vol_expand` survivors, and replace the reference target in R12 with `b_hold` plus L1-1.
- **If meta-labeling with the decomposed positive class has zero survivors:** pivot the L1-layer priority to cross-market pooling.
- **If any L0 block's survivors are fully absorbed by collinearity with the existing top-10 columns:** apply the Q1 rule. Drop the block and test that axis as stratification only.
- **If the timing probe shows a 24-cell family costs more than 5 core-h:** cut learners to lightgbm only (m = 12) rather than split further, and pre-register that change.