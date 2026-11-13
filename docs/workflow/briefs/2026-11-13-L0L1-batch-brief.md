# L0/L1 Status + Extension Brief — batch-planner input (Opus review)

> **Purpose.** This is the *input pack* for a batch-planner (Opus 5.5) review. It confirms the
> current L0-feature / L1-prediction state of the `signals` repo, records what is already
> planned, states the **product objective in EV terms**, and asks Opus — reasoning as a **quant
> trader, a technical analyst, and an ML-for-finance practitioner** — to confirm the state and
> propose other buildable improvements. It is a *source document*, not the plan: the plan lands in
> `docs/plans/` after submission.
>
> **How to run it (operator):**
> ```bash
> python3 ~/.hermes/skills/autonomous-ai-agents/batch-planner/scripts/batch_brief.py \
>   --input docs/workflow/briefs/2026-11-13-L0L1-batch-brief.md --id 26-W46-L0L1-extension-review \
>   --model anthropic/claude-haiku-5.5
> # (editor MUST be a non-reasoning model — glm/deepseek reasoning variants return null content
> #  with finish_reason=length on a pack this large)
> python3 ~/.hermes/skills/autonomous-ai-agents/batch-planner/scripts/batch_plan.py \
>   --request ~/.hermes/batch-planner/requests/26-W46-L0L1-extension-review.json
> ```
> **Batch reality that shapes the ask:** a batch call is text-in/text-out with **no tools, no live
> web, no `:online`**. Opus must reason from its own trained knowledge of quant/TA/ML-finance
> practice; it cannot look anything up. Any concrete literature citation it produces is a
> *recollection to verify*, and the plan must say so.

---

## PRODUCT OBJECTIVE (read first — it defines "good")

The end product is a **manual screener**: the pipeline emits a *short list of names to act on*, a
human reviews each and decides. L2 (automated trading) comes later on the same L0/L1 foundation.
So L0/L1 are built to serve a human decision, and are judged by the quality of the recommendation
stream, not by classifier coverage.

**Target operating point (the objective function):**

| dimension | target | consequence |
|---|---|---|
| Edge per trade | **~10%** (gross, pre-cost, per completed trade; horizon **≤ 3 months (~63 trading days) max hold** — candidate ladder {5,8,13,21,34,55} daily bars) — **aspirational for ranking now; hard pass/fail bar at L2** | we want **high-volatility** setups with room to run — not 1–2% scalps |
| Frequency | **~200 trades / year** (whole universe) | **low recommendation volume**; ~<1 name/day — selectivity over coverage |
| Error asymmetry | **minimize false positives; tolerate false negatives** | **precision > recall** — a wrong recommendation burns a human decision and capital; a missed one costs only opportunity |
| Currency of judgement | **Expected Value (EV)** | EV = p(win)·avg_win − p(loss)·avg_loss − cost. At 10%/trade, a small lift in either *p* or the payoff ratio moves EV a lot |

**Implications the plan must honor:**

- **Conditioning on volatility regime is central, not incidental.** High-ATR / high-vol regimes are where a 10% move is possible at all. Both the surviving `b_hold` signal and the top T2 family (`vol_expand`) already point here — consistent with the objective.
- **A screener that fires ~200 high-conviction, high-vol names a year beats one that fires 20,000 medium ones** at the same AUC. Optimize for **precision at small k** and **calibration in the top decile**, not global AUC.
- **Universe = 1,068 symbols** (USD 674 + CAD 394; ~25 quarantined) → ~200 trades/yr ≈ **0.19 trades/name/yr**, genuinely rare. Statistical power does **not** come from the 200 recommendations; it comes from the **full event panel** (USD ~460k / CAD ~252k swing events; WI-048 scored ~117k USD events per cell). L1 trains and gates on the full panel; the 200/yr is the eventual *deployment selection*, evaluated at L2.
- **"High volatility" = a regime percentile, not an absolute threshold:** e.g. `atr_pct_21` (or a realized-vol estimator) in its own trailing top tercile/quartile. Exact window/threshold is for the plan to fix; the panel's dimensionless design means *ranks*, not levels, set the cut.
- **Magnitude-aware targets matter**: "a ≥10% move happens" (or "the ATR-scaled move continues") is closer to the objective than "close is up over h bars."
- **EV is the product north-star and the ranking criterion, but NOT the L1 gate.** Per D-023 the L1 verdict stays *predictive-only* (OOF AUC/IC + BH-FDR + calibration); the ~10%/200-trade EV bar is a **hard bar at T3 / Layer 2 only**. We may add **precision@k and top-decile calibration** as *predictive* diagnostics at L1 — but no economic verdict until L2.

---

## GOAL

Produce a ranked, buildable extension plan for tiers **L0 (features)** and **L1 (predictive
models)** that serves the product objective above — and that (a) confirms or corrects the recorded
status, and (b) proposes concrete new feature families, conditioning axes, and targets, plus an
assessment of **L1-layer options** (no stack — see DECISIONS), each with mechanism, cost, and
finish condition, drawn from quant-trading, technical-analysis, and ML-for-finance practice.

Falsifiable finish line: a single markdown plan naming **≥6 net-new extension items**, each with
owner / core-hour estimate / one-BH-FDR-family boundary / finish condition / EV rationale, ranked,
plus an L1-layer options assessment, the 3 biggest risks, and a list of open questions.

*Definition — "net-new": not on the WI-047 shortlist and not among the self-proposed ideas below (meta-relation generalization, cross-feature interactions, the four prediction targets). Opus may extend or re-rank those, but they do not count toward the ≥6.*

---

## CURRENT CONDITIONS (confirmed, with evidence)

### L0 — Features

The causal panel is built by `src/feature_engine.py` (`compute_features_wi016()`) and extended by
`src/swing_bsh/binary_features_ext.py`; `src/swing_bsh/feature_inventory.py` parses the builder
and classifies every column. **Confirmed: 249 panel columns, 249 classified, coverage 1.000**
(WI-047; evidence `reports/t1_feature_gap_report.md`). All features are read **at the detection
bar only** (causal), dimensionless (ratio / z-score / percentile / flag — no absolute price or
volume), float32.

| block | cols | content |
|---|---|---|
| WI-016 grid | 111 | the classic + frontier indicator families (below) |
| cross-sectional ranks (`cs_*`) | 102 | same-date percentile of every smooth-family feature across the universe |
| sector one-hots + `srel_*` | 18 | 12 sector dummies + same-date same-sector percentile rank of 6 features |
| raw-ext | 6 | `volume_z_{21,55}`, `volume_trend_21`, `vwap_dist`, `bar_count_z_55`, `bar_count_trend_21` |
| keys | 5 | symbol/date/state/close/atr |
| event-quality | 3 | `swing_depth_atr`, `bars_since_opp`, `dd_age` |
| calendar | 2 | `dow`, `month` |
| breadth | 2 | `breadth_bottom`, `breadth_top` |

**Feature families present** (WI-016 grid, `wi016_feature_names()`):

- **Trend / momentum** — ADX, DI spread, MACD (ATR-normalized line + hist), Donchian break, fib-retracement distance.
- **Mean-reversion / oscillator** — RSI (+ 5-bar slope), Bollinger %B, range position.
- **Volatility** — ATR% , Bollinger width, Yang-Zhang, range compression, overnight gap z.
- **Volume / liquidity** — OBV z-score, Amihud illiquidity, VWAP z-score.
- **Path-shape / frontier** — Hurst exponent, Shannon entropy, fractional differentiation (d=0.40), Kalman spread.
- **Range structure** — range width, fib distance, `pct_from_high/low`, range compression.
- **Cross-sectional / contextual** — cross-sectional ranks, sector ranks, breadth, calendar.

**Meta-relation layer (the axis the user asked about) — partially present:**

| meta type | status | example |
|---|---|---|
| Spatial percentile (vs peers, same date) | **present, heavy** | `cs_*` (102), `srel_*` (6) |
| Inter-window ratio (term structure of a feature) | **thin — 2** | `range_compression_8_55`, `range_compression_21_144` |
| Ratio-to-own-history (trend) | **a few** | `volume_trend_21`, `bar_count_trend_21`, `rsi_14_slope_5` |
| Rolling time-series percentile ("is today's ATR%/entropy in its own top decile?") | **MISSING** | gap **G5** in the gap report |
| Cross-feature interaction (feature-vs-feature ratio/diff) | **MISSING** | none |
| Absolute (un-normalized) level | **deliberately excluded** | by design |

**Feature→target alignment is concentrated.** WI-040 permutation attribution (winner cell
`exact_full_k0.8` / `b_hold` / xgboost / h13, `reports/wi040_calibration.md`) shows **~8–10 of
249 columns carry essentially all signal**: `atr_pct_3` (top-1 in BOTH markets), `cs_entropy_102`,
`entropy_24/39`, `hurst_15/39`, `adx_21/144`, `di_spread_3/233`, `kama_er_15`,
`range_compression_8_55`, `swing_depth_atr`, `bars_since_opp`. Read: the aligned axis is
*"is this bar a stretched, low-efficiency extreme in a market-wide stretched regime?"* — the
**volatility-regime axis the EV objective wants**.

**Families with ZERO permutation evidence yet:** `volume_liquidity` (26 cols), `sector` (18),
`mean_reversion` (17), `breadth` (2). Mean-reversion is silent *as features* even though
mean-reversion *targets* are the thesis driving the swing detector — worth an analyst's eye. **Design tension for Opus:** the detector is event/mean-reversion-shaped (buy bottoms, sell tops) but the surviving signal is volatility-regime — the plan should say which thesis governs the next round of features/targets.

### L1 — Predictions

Gated pickle library, **predictive-only license** (D-023 Layer 1: OOF AUC/IC + BH-FDR +
calibration; **no trading/economic claim**, no effect-size floor, FDR survivors are accepted).

- **Library manifest** `data/models/wi040/manifest.parquet` — **9,745 rows** = WI-036 (96) + WI-038 (6,838) + WI-044 (2,811) fold pickles.
- **WI-035/036 three-binaries** — `b_profit` / `b_stop` / `b_hold`, a mutually-exclusive/exhaustive decomposition of the first-touch 3-class label on swing events. **Within this three-binary family, the surviving signal = `b_hold` short-horizon only (h∈{5..89})**; the entry/exit targets (`b_profit`, `b_stop`) produced **no** FDR survivors in any variant. *(Family-scoped: the WI-048 T2 families below also write survivors to the same L1 library — 295 rows in `data/models/wi048/manifest.parquet`.)* Best: xgboost/b_hold/h13 AUC **0.7836 USD / 0.7207 CAD** (Brier skill +0.327 USD, ECE 0.0009); random_forest/b_hold/h21 min AUC 0.7341.
- **WI-048 T2 families** (`src/swing_bsh/targets_ext.py`, reports `reports/t2_grid_*_summary.md`, `reports/t2_targets_ext_summary.md`):
  - `up(t,h)` = `close[t+h] > close[t]` (directional)
  - `high_low(t,h)` = the event-window extreme is re-touched inside `[t+1, t+h]`
  - `vol_expand(t,h)` = realized vol of the h log-returns ending at `t` > 1.0× the prior h-window
  - Grid: 3 families × 6 horizons {5,8,13,21,34,55} × 2 learners {lightgbm, xgboost} × 2 markets = 72 cells; BH-FDR α=0.05, m=24 per family; 5-fold `PurgedWalkForwardSplit(embargo=max(20,h))`; geometry pinned per market (USD `exact`, CAD `tol2`, variant `*_full_k0.8`).
  - **Result ranking (cross-market min AUC):** `vol_expand` **0.7068** > `high_low` **0.6089** > `up` **0.5038**. FDR survivors: `vol_expand` 24/24, `high_low` 24/24, `up` 11/24. Survivors are **written to the L1 library pending admin ratification (PROVISIONAL)**. Winner cell `USD|lightgbm|vol_expand|h13`; attribution tops: `bars_since_opp` 0.192, `atr_pct_3` 0.152, `di_spread_3` 0.082, `cs_donchian_break_21` 0.081, `kama_er_15` 0.067, `entropy_24` 0.056.
  - **Interpretation (aligns with EV objective):** the strongest family (`vol_expand`) and the `b_hold` signal both point at *volatility / range regime*, not direction. Directional `up` is barely above chance (USD 0.5038). The discoverable edge is **volatility-state and path-shape** — where 10% moves live.
- **Learners available in the manifest:** xgboost, logistic_l2, hist_gbm, mlp_torch, lightgbm, catboost, random_forest, extra_trees, xgboost_isotonic, elasticnet_logistic.
- **Legacy 5-target set** (`src/targets.py`): `y_15d_high`, `y_15d_low`, `y_20d_up`, `y_20d_down`, `y_20d_stay` — retained for the shipped screener; `y_20d_up/down/stay` is already an ordered magnitude-ish decomposition, useful prior art for the continuous-target work.
- **Label density** (`reports/t2_label_density_probe.md`): `up` ~0.53–0.56, `high_low` 0.75–0.87+, `vol_expand` ~0.50 — all balanced enough (no sparse cells at ≥25 positives).

---

## ALREADY PLANNED — do NOT re-propose as novel

Opus should treat these as **taken**; it may critique or re-prioritize them, but new value is
elsewhere.

**WI-047 feature shortlist** (all OHLCV-only, causal, ≤~10 cols, one BH-FDR family each; lineage
already cited in-repo: Parkinson 1980, Garman-Klass 1980, Rogers-Satchell 1991, Yang-Zhang 2000,
Andersen-Bollerslev 1998, Corsi 2009 HAR-RV, Amihud 2002, Kyle 1985, Easley VPIN 2012):

1. **Regime percentiles** — rolling 233-bar percentile of `atr_pct_21`, `bb_width_21`, `entropy_39`, `hurst_39`.
2. **Volatility-forecast estimators** — Parkinson / Garman-Klass / Rogers-Satchell levels + estimator ratios (fills gap G1: vol family present in *name only*).
3. **Market-residual context** — `mkt_resid_mom`, rolling `beta_mkt`/`corr_mkt` vs equal-weighted ingested universe, breadth divergence (fills G4).
4. **Dollar-volume & Amihud percentiles** — the untried version of the 26-col zero-evidence volume family (fills G2).
5. **Seasonality dummies** — turn-of-month, half-month, holiday (fills G3).

Held/blocked (no new ingestion allowed): FOMC dummies (external calendar), turnover velocity
(shares outstanding), options-implied / IV skew (no chain — G6).

**My added feature ideas (from the meta-relation scan above)** — generalize the regime-percentile
transform to *every* aligned family, and add a **cross-feature interaction block**
(`entropy/kama_er`, `adx − entropy`, vol-adjusted momentum).

**Prediction targets already proposed by me:** volatility-state terciles (high/med/low),
time-to-touch (survival on the already-computed first-touch offsets), move-magnitude / velocity
buckets, range-occupancy / extreme-holds-vs-breaks.

**Tier-3 (out of scope here, listed so Opus doesn't drift in):** mechanism survey WI-049
(time exits, relative-value ranking, vol-target sizing, L/S pairs) on the frozen baseline.

---

## DECISIONS ALREADY MADE (admin, this session)

- **Continuous vs binary targets:** test **both**; each form is emitted as its **own BH-FDR family** (separate run/verdict). The head-to-head between the two forms is **descriptive only — not a gate**; which family feeds the screener is a **deferred L2 decision**. Re-test continuous targets **fresh** (WI-025 REJECT lineage is cited as prior only, not reused as baseline).
- **Ensembling/stacking:** **do NOT build a stack for now.** Instead, the plan must **explore L1-layer options** — survey and trade off the plausible L1 architectures (single per-cell model, per-market pooling, multi-target multi-task, meta-labeling, simple ensembles) and recommend which to pursue/benchmark next, with the cost/finish conditions. If stacking is ever revisited, a **mandatory leakage test under purged/embargoed CV** is a finish condition.
- **Conditioning/regime features:** **RATIFIED (admin, 2026-11-13)** — a small named regime-feature block is allowed in L0; conditioning may also be expressed as target stratification, but never both for the same axis in one run (see SCQA Q1).
- **Meta-labeling:** **RATIFIED (admin, 2026-11-13)** — in scope as an L1.5 precision layer gated as Layer-1, primary = **both** the swing side and the frozen fib entry rule, tested as **separate BH-FDR families** (see SCQA Q2).
- **The ~10%/trade figure:** **both** — a ranking aspiration now, a **hard pass/fail bar at L2**.
- **Owner field:** a **free-text role label**; the admin defines the roster downstream. Do not assume fixed role names.
- **EV rationale at L1 = a predictive proxy** (precision@k, top-decile calibration, and the payoff-ratio implied by the target construction) — **not** an economic claim. Economic EV is computed at L2 only.
- **Meta-labeling positive class (default):** the *primary's favourable outcome* (swing side wins / frozen fib rule profitable). Opus may propose the magnitude-event (≥X% move) as an alternative definition to test.
- **"Net-new" excludes WI-047 variants** — a variant of an already-listed WI-047 family is a WI-047 item, not net-new. Same for variants of the self-proposed ideas (meta-relation generalization, cross-feature interactions, the four prediction targets).

---

## RESOLUTIONS TO INTAKE FLAGS (so the planner does not re-raise them)

- **"Cross-family selection" vs one-family-per-run:** binary and continuous forms are each their **own BH-FDR family** and thus their own gated run; the form-vs-form head-to-head is **descriptive**, not a gate. No contradiction with the anti-cherry-picking rule.
- **"No effect-size floor" vs "minimize false positives":** different layers. The **L1 library** admits every FDR survivor under a *predictive* licence (no effect-size floor). **False-positive minimization is the product/L2 objective.** Both hold.
- **"Accepted into the L1 library" + "PROVISIONAL":** survivors are written to the library **pending admin ratification**; ratification is what makes them adopted. Both statements hold at different moments.
- **"Net-new":** defined in GOAL.
- **Owner names:** free-text role label (DECISIONS).
- **"b_hold is the only survivor" vs "vol_expand 24/24":** family-scoped statements, both true. Only `b_hold` survived within the WI-035/036 three-binary set; the WI-048 T2 families (`vol_expand`, `high_low`, `up`) are a *separate* set, all writing survivors to the same L1 library.
- **"EV rationale" vs "predictive-only":** the EV rationale is a *predictive proxy* at L1 (see DECISIONS); no economic claim crosses the gate.
- **Meta-labeling "predictive-only" vs "~200 trades/yr":** the layer is *gated* predictive-only; the ~200/yr is the eventual *product use* at L2. Licence ≠ use.
- **Statistical power vs rarity:** L1 is gated on the full event panel (~460k USD / ~252k CAD events), not on the ~200/yr deployment selection.
- **10% edge horizon:** per completed trade; **capped at 3 months (~63 trading days) max hold** — deployment horizons {5,8,13,21,34,55} daily bars (all ≤ 3 mo; the h89 cell is out of the deployment window).
- **Core-h cap:** per WI (not per batch).
- **Items that can't plausibly reach ~10%/trade:** do NOT drop them; rank by the EV-proxy and flag plausibility. The 10% is an L1 *aspiration* — only L2 enforces it.
- **Cost/slippage in the plan:** permitted only as **L2-forward observations** (what T3 must test), never as an L1 verdict.
- **Meta-labeling primary:** both (swing side, frozen fib rule), as separate BH-FDR families.
- **EV holding horizon:** capped at 3 months (~63 trading days) max hold.
- **WI-048 d/e/f locks:** NOT cleared as of 2026-11-13 (`.hermes/locks.json` still lists them; `docs/kanban/in_progress/` is empty) — a pre-dispatch human action outside the planner's scope.

---

## IDEAL RESULT

A markdown plan (per the batch-planner prompt contract) that delivers:

1. **Status confirmation / correction** — does the recorded L0/L1 state hold up? Name any misread, over-claim, or missing distinction (e.g. is "249 columns" the right unit? is `b_hold`-only a limitation or the finding that the edge is volatility-shaped, consistent with the EV objective?).
2. **≥6 net-new extension items**, each: name · tier · mechanism (why it should carry signal, from quant/TA/ML practice) · **EV-proxy rationale (predictive — how it moves precision@k / top-decile calibration / the payoff-ratio toward the ~10%/200-yr objective; not an economic claim)** · cost (core-h) · one-BH-FDR-family boundary · finish condition · dependency · owner (free-text). Ranked; features (L0) separate from targets/conditioning (L1).
3. **Three-mindset sweep** — a short section each for: **quant trader** (execution/microstructure, cost & slippage realism **as L2-forward observations — where costs will bite and what T3 must test; never an L1 claim**, regime switching, cross-asset/lead-lag, position sizing & tail risk), **technical analyst** (market structure, swing/trend classification, Wyckoff phase, classical patterns, cycle/seasonality, support/resistance dynamics, how to express a "10% move likely" setup), **ML-for-finance** (label engineering, meta-labeling / triple-barrier refinements, sample weighting, purged-CV refinements, feature-selection discipline, calibration).
4. **Conditioning-axis design** — for the user's axes (high/med/low vol; velocity of change; peak/bottom vs middle 50%/75%), say whether each is best as a *new target family*, a *stratification within an existing family*, or a *feature*, and the BH-FDR multiplicity consequence of each choice.
5. **Binary vs continuous target families** — the comparison protocol (both forms, each its own BH-FDR family, rank-IC + precision@k; descriptive head-to-head, L2 decides deployment) and which proposed targets most likely favour which form.
6. **Precision-first evaluation addendum** — how to report precision@k / top-decile calibration as *predictive* L1 diagnostics (not economic) so the screen's low-volume, high-conviction intent is measurable without crossing the D-023 gate.
7. **L1-layer options assessment (stacking deferred)** — survey and trade off the plausible L1 architectures: single per-cell model vs per-market pooling; multi-target / multi-task; the ratified L1.5 meta-labeling layer (primary = swing side / frozen fib rule); simple ensembles (seed/averaging); and stacking **as an option not to build now**. For each: expected lift, cost, finish condition, and where it could leak. If stacking is recommended against, say why; if ever revisited, require a leakage test under purged/embargoed CV. State the gate licence for any new layer.
8. **3 biggest risks** + cheapest mitigation each.
9. **Open questions** — where this pack is silent; never guess.

---

## CONSTRAINTS (the plan must respect these)

- **Compute pacing is the primary sizing constraint — WIs must pause and hand off to a human.**
  Host: Hostinger VPS, 2 vCPU / 8 GB / no swap (CPU-credit model: full balance ≈ 3 h @ 100% CPU).
  `n_jobs=2` everywhere (never −1); float32 immediately; symbol-sequential reads; no all-ticker
  uncompressed DataFrame. **The core limit sizes and times ML training — a pacing guardrail, not a
  wall.** Therefore every WI must:
  - declare its **projected core-hours**, capped at the default **2.5 core-h per WI** (raise only by explicit admin approval);
  - run **checkpointed and pausable**, with named pause points and a **resume command**;
  - **report pacing in its spec and its run footer: `START_UTC`, projected core-h, `END_UTC`, and `NEXT_ALLOWED_RUN_UTC`** — after any burst ≥1 core-h, next run ≥ +30 min idle to recover credits;
  - **pause and require human intervention** when the modeled credit balance < 25% (run the monitor with an explicit `--state` path);
  - reference point — this brief is authored **2026-11-13T17:38Z (Fri)**; a ≤2.5 core-h burst started now clears for a next run at **≥ 18:08Z** (nominal: notional clean-run clock from burst *start*; the real +30 min idle window starts when the burst *ends*).
  - monitor before dispatch: `python3 ~/.hermes/skills/devops/hostinger-vps-cpu-credits/scripts/credit_monitor.py --vcpus 2 --state <user-writable-path>`.
- **Correctness invariants (never budget knobs):** purged/embargoed walk-forward CV
  (`PurgedWalkForwardSplit(embargo=max(20,h))`), CALIB-only selection at L2, float32, symbol-sequential, `n_jobs` caps.
- **One BH-FDR family per grid run.** Every tested cell joins ONE family; conditioning axes fold
  into the same family — they are **not** free extra families. Loosened axes are variant grids,
  never merged configs. Binary and continuous forms of the same target are **different families**,
  each its own run; the form head-to-head is descriptive, not a gate. This is the anti-cherry-picking rule.
- **Gate discipline:** L1/T1 evidence is **predictive only** (OOF AUC/IC + BH-FDR + calibration,
  plus precision@k / top-decile calibration as predictive diagnostics). Do NOT present economic
  magnitude or cost analysis at L1; the **EV / 10%-per-trade / 200-trades-per-year bar is enforced
  at T3 / Layer 2.** The "no effect-size floor" rule applies to the *predictive* L1 library; the
  product's false-positive minimisation is a Layer-2 concern. Any FDR survivor is written to the
  L1 library; verdicts are **PROVISIONAL** until the admin ratifies in chat.
- **Dependencies:** grep `pyproject.toml` before proposing new deps — new deps need their own
  adoption decision. Already available: numpy, pandas, pyarrow, scikit-learn, statsmodels,
  xgboost-cpu, lightgbm, catboost, torch (CPU), matplotlib, pandas_market_calendars, ib_async, pyyaml, psutil.
- **No new data ingestion** in this scope (no options chain, no shares-outstanding, no fundamentals).
- **Workflow:** file-lock protocol (`.hermes/locks.json`, `write_files` manifest); surgical WIs in
  `docs/kanban/`; one role per session. No secrets in git.
- **Batch itself:** no tools, no web; `max_tokens ≥ 16000` (Opus adaptive-thinking bills into the
  same budget); batch price $2/$10 per MTok; US infrastructure, no ZDR — no confidential material.

---

## CONTEXT PACK (compact — verbatim facts for the planner)

- Repo: `/home/yycuser/projects/signals`; `uv sync` / `uv run pytest`.
- Data: dual-market USD + CAD, raw OHLCV parquet per symbol under `data/raw_ohlcv/market={USD,CAD}/`; `min_date` default `2016-01-01`.
- Swing events: `src/swing_bsh/events.py` (`detect_swings`, `label_symbol`, `BARRIERS`, `K_VALUES`); first-touch geometry with ±2-bar shoulder (`tol2`) vs detected bar (`exact`); barriers `k∈{0.8,1.0}` × ATR.
- Board (single source): `docs/workflow/BOARD.md` — D-025 sprint WI-046→045→047→048→049; WI-048 sub-batch a–f DONE, verdicts PROVISIONAL. **Loose end (human action, not plannable):** WI-048 d/e/f locks recorded on the BOARD but `.hermes/locks.json` not cleared (cron write-block) — next interactive session must verify/empty `active_locks` before dispatch.
- Tier design: `docs/workflow/designs/D-025-tiered-workflow.md`.
- Feature gap report: `reports/t1_feature_gap_report.md` (gaps G1–G6; shortlist §5).
- L1 evidence: `reports/wi040_calibration.md` (attribution + calibration), `reports/wi036_summary.md`, `reports/wi038_summary.md`, `reports/wi044_summary.md`.
- L1 (T2) evidence: `reports/t2_grid_{up,highlow,volexpand}_summary.md`, `reports/t2_targets_ext_summary.md`, `reports/t2_label_density_probe.md`.
- Tier inventory: `reports/tiered_workflow_status_2026-11-10.md`.
- Frozen baseline (T3 only, context): `frozen_fib_w28entry_w30exit_t15_s10_d39_close`, 25 bps.
- L2 status (context, CLOSED): all 7 overlay questions ratified — statistical signal (placebo z to +5.88) but EVAL edge ~0 vs 25 bps. L2 paused pending WI-045 edge-decay probe.

---

## OPEN QUESTIONS (SCQA — situation · complication · question · answer)

All resolved this session; recorded under "DECISIONS ALREADY MADE". The SCQA blocks stand as the
decision record for the planner.

### Q1 — May L0 carry conditioning/regime *features*, or must conditioning live only in the target/stratification axis?  *(RATIFIED 2026-11-13 — recommendation accepted)*

- **Situation:** The aligned signal is volatility/range-regime-shaped (`atr_pct_3`, entropy, Hurst, k). The panel currently holds no explicit regime *state* variable — only raw levels and their cross-sectional ranks.
- **Complication:** The same conditional information can enter two ways that spend BH-FDR budget differently and imply different gates: as **panel features** (L0 — tests "does the conditional info improve prediction") or as **target stratifications** (L1 — tests "does the signal differ across regimes"). Doing both encodes the same information twice, inflates multiplicity, and risks a false discovery.
- **Question:** Do we allow regime/conditioning **features** in the panel, or restrict conditioning to target stratification?
- **Answer (RATIFIED):** Allow a **small, named regime-feature block** in L0 — volatility state, and rolling ATR%/entropy/Hurst percentiles. It is the cheapest strengthening of the exact families that already carry signal, and D-025/WI-047 already frames regime percentiles as T1 features. Keep stratification separate: one BH-FDR family per run, never both forms of the same axis together. *Change-my-mind:* if the percentile columns merely duplicate the raw levels (collinearity absorbed by BH-FDR), drop them and keep only stratification.

### Q2 — Is a meta-labeling layer in scope for L1?  *(RATIFIED 2026-11-13 — recommendation accepted)*

- **Situation:** The surviving signal is `b_hold` (hold-vs-exit characterisation of the event), and directional `up` is ~chance. The swing detector already produces high-recall events. The product wants **low-volume, high-precision** recommendations.
- **Complication:** Meta-labeling (a secondary model predicting whether the primary bet wins) is the textbook precision tool and maps directly onto the "~200 high-conviction names/year" mandate — but it adds a layer, and it must be assigned a gate licence and a primary signal, or it blurs the two-layer ML gate.
- **Question:** Do we add a meta-labeling layer, and if so what is the primary it filters?
- **Answer (RATIFIED):** Yes, scoped as an **L1.5 predictor layer gated as Layer-1 (predictive only)**: secondary model predicting P(favourable outcome), where the *primary* is the swing side (and/or the frozen fib entry rule), using detection-bar features + the primary's side. Its job is to *filter to the top ~200/yr* — a precision instrument. The filter's economic effect is measured later at L2, not at L1.

### Q3 — Continuous vs binary targets *(answered)*

- **Situation:** L1 families today are binary; legacy quantile work (WI-025) is REJECT lineage, and the legacy `y_20d_up/down/stay` set is a coarser ordered decomposition. **Complication:** the 10%-move objective is inherently magnitude/continuous, but a "≥10% move" event is naturally binary, and the two spend FDR budget separately. **Answer (admin):** test both as **separate BH-FDR families**; re-test continuous **fresh** (WI-025 = prior only); head-to-head is descriptive, deployment deferred to L2 (see IDEAL RESULT §5).

### Q4 — Ensembling/stacking *(answered — revised)*

- **Situation:** 9,745 L1 fold pickles across 10 learners and many cells; today each cell is gated independently. **Complication:** a stack can lift precision but leaks catastrophically under naive CV, and its gate licence is unstated. **Answer (admin):** **do not stack for now**; instead **explore L1-layer options** and recommend which L1 architecture to pursue/benchmark next (IDEAL RESULT §7). Any future stacking requires a mandatory purged/embargoed leakage test.

---

## OUTPUT FORMAT

Return markdown with these headings, in order:

```
## 1. Status assessment (confirm / correct)
## 2. Ranked extension items  (table: rank | item | tier | mechanism | EV-proxy rationale (predictive) | cost core-h | BH-FDR family | finish condition | owner | depends)
## 3. Quant-trader mindset
## 4. Technical-analyst mindset
## 5. ML-for-finance mindset
## 6. Conditioning-axis design (vol regime / velocity / peak-bottom-vs-mid)
## 7. Binary vs continuous target families
## 8. Precision-first evaluation addendum (predictive-only)
## 9. L1-layer options assessment (stacking deferred)
## 10. Three biggest risks + cheapest mitigation
## 11. Open questions
```
