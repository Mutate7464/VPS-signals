# Visualizer / Audit-Workbench Plan — batch-planner input (Opus review)

> **Provenance:** facts gathered from repo artifacts on 2026-11-19 (file listings, DATA_CONTRACT.md,
> BOARD.md, reports/ index, L0L1 batch brief 2026-11-13). The batch model has no tools; every
> number below was verified on disk this session.
> **Operator:** `batch_brief.py --input <this file> --id 26-W47-visualizer-audit-workbench --model anthropic/claude-haiku-5.5`, then `batch_plan.py` after intake returns ready.

---

## PRODUCT OBJECTIVE

A **human-in-the-loop visual audit workbench** serving the manual screener: the analyst inspects
features, targets, OOF predictions, and models interactively to (a) prune features, (b) sanity-check
labels for leakage/sanity before gates, (c) inspect individual events/candles before and after gate
verdicts. It is **tooling, not research** — no BH-FDR family, no gate verdicts, read-only on
`data/`. Success = the admin can answer "why did model X win / fail" in minutes, visually.

## GOAL

Produce a build plan for a visualizer tool inside the `signals` repo that reuses existing artifacts
in place (no data copying), scoped in phases so Phase 1 is a small, low-core-hour deliverable.
Falsifiable finish line: one markdown plan with a phased WI decomposition (each item: owner,
core-hour estimate, files touched, finish condition), a chosen UI/framework stack with rationale,
a data-access layer design against the ACTUAL schemas below, and 3 biggest risks.

## DECISIONS ALREADY MADE (do NOT relitigate)

1. **Location: inside the signals repo** (`tools/visualizer/` or `src/visualizer/`), not a
   standalone repo. Reads repo artifacts in place. Extract to a standalone package later only if
   it proves reusable elsewhere.
2. **Read-only on `data/` and `raw_ohlcv/`** for the VISUALIZER itself — no re-derivation of
   features/targets/models inside the tool. HOWEVER (admin, 2026-11-19): the L0/L1/L2 research
   layers are **UNFROZEN**, and the attached design prompt's engineering content IS in scope as
   a second track (see L0/L1/L2 TRACK below).
3. **Runs on the VPS** (Hostinger KVM2, 2 vCPU/8 GB), served over SSH tunnel / browser; the
   attached prompt's "local M1 Marimo + rsync mart" split-compute architecture is DESCOPED for v1 —
   if the plan concludes local-offload is essential it must justify it against the actual artifact
   sizes (event panel fits, see below).
4. **CPU discipline applies:** `n_jobs=2`, `pyarrow.dataset`/symbol-sequential reads, no
   all-ticker uncompressed DataFrame, float32, any precompute job ≤ 2.5 core-h with the credit
   monitor checked before dispatch.
5. **Read-only UI cannot cross gates:** verdicts remain PROVISIONAL until admin ratification;
   the visualizer displays evidence, never computes verdicts.
6. **UI stack chosen by the plan** but must run headless over SSH and be git-friendly (Marimo or
   Streamlit/Plotly/Dash equivalent — the plan picks one and justifies it).

## CURRENT CONDITIONS (verified on disk, 2026-11-19)

- **Board state:** D-027 sprint CLOSED + RATIFIED 2026-11-16. No WIP, no open sprint brief; next
  sprint is admin-ordered. L1 library FROZEN for the L2 rebuild. D-026 ratified: 5 L1 families
  integrated (`vol_expand_fwd`, `move_occur`, `move_dir_up`, `xsec_vol_rank_bin`, `mfe_mae_bin`,
  continuous families in `reports/l1_ext_cont/`). L2 EVAL (fixed_h55 unsized) RATIFIED ADOPT.
- **Repo layout:** `src/` (feature_engine.py, targets.py, swing_bsh/, l2_overlay/, models/,
  labels/, reporting/, perfanalytics/), `data/`, `reports/`, `docs/`, `tools/` (empty-ish),
  `config/`, `tests/`. `pyproject.toml` + `uv.lock` (Python 3.14).
- **Feature panel** (`data/features/features_{USD,CAD}.parquet`): 249 classified causal columns +
  keys (`symbol`, `date`, `state`, `close`, `atr`), dimensionless, float32. Metadata parquets
  alongside (`features_*_metadata.parquet`). Builder: `src/feature_engine.py`
  (`compute_features_wi016()`) + `src/swing_bsh/feature_inventory.py` (column classification).
- **Targets:** `data/features/targets_{USD,CAD}.parquet`; OOF predictions
  `data/oof_{MKT}[_variant].parquet` (41 cols: `date`, `symbol`, `close`, `fwd_atr_ret_15/20`,
  `y_<target>`, `p_<target>`, `fold_<target>`, barrier variants `_pl0/_pl1/_pl2`). Variants:
  `fib_only`, `cs_pct_only`, `no_static`, `legacy19`.
- **Raw OHLCV:** `data/raw_ohlcv/market={USD|CAD}/symbol=<TICKER>.parquet`
  (`date date32`, `open/high/low/close float`, `volume float`, `average float`, `barCount int64`);
  USD 674 files, CAD 394 (~1,068 universe).
- **Model pickles:** `data/models/wi040/manifest.parquet` (9,745 fold rows) +
  `data/models/wi048/manifest.parquet` (295 rows) and per-cell pickle files named
  `<MKT>_<learner>_<geometry>_<family>_h<h>_f<fold>.pkl` (families: `up`, `high_low`, `vol_expand`,
  `move_occur`, `move_dir_up`, `mfe_mae_bin`, `mfe_mae_cont`, `xsec_vol_rank_bin`,
  `xsec_vol_rank_cont`; learners xgboost/lightgbm; geometry `exact_full_k0.8` USD /
  `tol2_full_k0.8` CAD; horizons 5–55).
- **L2 artifacts:** `data/models/l2_prepared`, `l2_xsec_rank/` (parquet outputs),
  `data/predictions_{MKT}_latest.parquet`, `reports/l2/`, `reports/l2_eval/` (WI-071 EVAL),
  `reports/l2_time_exit/`, screener PDFs in `reports/`.
- **What signal won (context for the views):** surviving signal is volatility-regime shaped —
  `atr_pct_3`, `entropy_*`, `hurst_*`, `adx_*`, `kama_er_15` carry ~all signal (WI-040
  permutation attribution); `b_hold` short-horizon best h13 AUC 0.7836 USD / 0.7207 CAD;
  `vol_expand` 24/24 FDR survivors.
- **Existing per-WI reports** in `reports/` are the current "audit layer" — static markdown/PDFs.
  There is NO interactive tool today.

## MAPPING PROMPT-VIEWS → EXISTING ARTIFACTS (the plan must confirm/refine)

| Attached-prompt view | Replaces-with-reality |
|---|---|
| Global control bar, threshold rule builder, KPI strip | filters over `features_*.parquet` joined to `oof_*.parquet` / targets on (symbol, date) |
| View 1 histograms + decile lift | same join; feature column × target column |
| View 2 throughput vs expectancy curve | OOF `p_<target>` + `fwd_*` returns |
| View 3 candlestick click-to-inspect | `raw_ohlcv/.../symbol=<T>.parquet` slices + event windows from OOF/targets; overlay barrier levels where reproducible from saved artifacts |
| View 4 correlation/dendrogram pruner | feature panel columns via `feature_inventory.py` classification |
| View 5 regime attribution heatmap | `atr_pct_*`/regime columns × target hit rates |
| View 6 PSI / rolling IC drift | feature panel vs. OOF fold ids |
| Manifest/leakage verification | `docs/workflow/DATA_CONTRACT.md` §2 schema checks |

## CONSTRAINTS

- VPS: 2 vCPU / 8 GB / no swap, CPU-credit model; `n_jobs=2` everywhere; visualizer server must
  idle near-zero CPU (no continuous polling/recompute).
- No secrets in git; no live trading; daily shortlist + human gate only.
- Dependencies via `uv` only (`uv sync`); the tool must not pin new heavy deps without reason.
- Repo workflow: changes go through WI cards in `docs/kanban/draft/` with `write_files` manifests
  (lock-governed); visualizer WIs follow the same protocol.
- Batch = text-in/text-out: the plan may not assume tool access; any external citation is a
  recollection to verify.

## VIEW SPECS (verbatim intent from the admin's source design prompt)

- **Global Control Bar:** target selector (any target/prediction column) + threshold-rule builder
  (min/max range sliders on active feature columns); KPI strip: retained trades/yr, conditional hit
  rate, lift vs base, EV, profit factor; export of a validated feature whitelist/pruned list
  (strictly excluding any `fwd_*`/`y_*`/target column from feature lists).
- **View 1 — Target-conditioned histograms & decile lift:** overlaid true/false histograms per
  feature with threshold markers; decile conditional hit-rate with bin counts, bootstrap CIs,
  target-shuffled null baseline.
- **View 2 — Throughput vs expectancy curve:** sweep threshold across quantiles plotting hit
  rate/lift/EV against retained trade frequency, reference line at 200 trades/yr.
- **View 3 — Click-to-inspect candlestick viewer:** any histogram bin/table row opens a Plotly
  OHLC window (entry −40 to exit +15 bars) for that symbol with indicator subplots and barrier
  overlays where reproducible from saved artifacts.
- **View 4 — Redundancy & collinearity pruner:** Spearman heatmap + mutual-information matrix
  across active features; hierarchical-clustering dendrogram grouping collinear features.
- **View 5 — Regime attribution & interactions:** 2D conditional hit-rate heatmaps (feature
  decile × volatility-regime decile or calendar year); loader hook for optional pre-computed
  SHAP/ICE parquet outputs (none exist yet — deferred).
- **View 6 — Temporal stability & drift:** rolling Population Stability Index across
  chronological eras (<0.10 stable / 0.10–0.25 shift / ≥0.25 drift); rolling cross-sectional
  Rank IC and ICIR with stability summary.

## RESOLVED (admin, 2026-11-19 — previously intake questions)

- **Six-view specs:** supplied in VIEW SPECS above; the planner must design against them.
- **Core-hour cap:** repo default 2.5 core-h per WI — the cap is the *expected interval between
  human confirmations*, not a wall; a read-only visualizer should use far less. Precompute jobs
  (if any) remain checkpointed and pausable.
- **Cache write path:** the visualizer may write caches ONLY to a non-data path
  (`state/viz/` preferred; `tools/visualizer/cache/` acceptable). `data/` and `raw_ohlcv/` stay
  strictly read-only.
- **Filter-latency budget: 1 s** end-to-end (server render over SSH) — the UI is for eyeballing,
  not trading. The 100 ms local-slider target from the source prompt is DESCOPED with the
  split-compute architecture.
- **Export consumer (admin, 2026-11-19):** the exported pruned-feature whitelist / rule set IS
  consumed downstream — as INPUT to a future L0/L1 gate WI. It is advisory until that gate WI
  runs; the export itself computes no verdict and crosses no gate.
- **Core-hour cap vs "not a wall":** the 2.5 core-h default is the per-WI *sizing* (the expected
  interval between human confirmations). Same rule as AGENTS.md applies: jobs run checkpointed,
  and pause/hand back when the credit model says so. No contradiction.
- **Full OOF schema (probed 2026-11-19, `data/oof_USD_fib_only.parquet`, 41 cols):** keys
  `date, symbol, close`; forward returns `fwd_atr_ret_15, fwd_atr_ret_20` (labels, never
  features); legacy 5-target block `{y_y_15d_high, y_y_15d_low, y_y_20d_up, y_y_20d_down}` each
  with `{y_*, p_*, fold_*}` plus barrier-variant pairs `{y_*_pl0/pl1/pl2, p_*_pl0/pl1/pl2}`.
  Targets parquet adds `market` + `y_20d_stay`.
- **Barrier levels in View 3:** NOT stored as levels anywhere — only as label variants
  (`_pl0/_pl1/_pl2`). Overlays must therefore either (a) recompute the barrier rectangle from
  raw OHLCV + the geometry parameters in reports (pure display math, allowed — not
  re-derivation of features/targets), or (b) ship in a later phase. The plan must pick one.
- **Owners:** free-text role label per WI (admin defines roster downstream). No fixed names.
- **"Validated" whitelist:** validation = schema check that no `fwd_*`/`y_*`/target-derived
  column enters the exported feature list, plus a type/range check per feature — nothing more
  (no gate semantics). Keys `close` (absolute price) and `atr` are EXCLUDED from eligibility —
  the panel is dimensionless by design; `date/symbol/market` are join keys only.
- **Target namespaces (admin, 2026-11-19):** View 1 selector exposes BOTH — OOF legacy targets
  (`y_15d_high`, `y_15d_low`, `y_20d_up`, `y_20d_down` from `oof_*.parquet`) AND model pickle
  families (`up`, `high_low`, `vol_expand`, `move_occur`, `move_dir_up`, `mfe_mae_bin`,
  `mfe_mae_cont`, `xsec_vol_rank_bin`, `xsec_vol_rank_cont`). NOTE for the plan: pickle-family
  OOF probability columns live per fold in the manifest/pickle dirs — the data-access layer must
  read whichever form is materialized on disk (probe before designing; if family OOF is not
  materialized as parquet, the plan must name the materialization WI or scope View 1 to legacy
  OOF + family hit-rate columns from the targets grid).
- **KPI statistics (admin, 2026-11-19):** KPIs (EV, profit factor, hit rate) are computed on OOF
  predictions TOO, but the UI WATERMARKS them "in-sample, selection-bias risk" — display-only
  diagnostic. No verdict framing; gates are computed elsewhere by WIs.
- **Geometry parameters for barrier overlays:** per-cell geometry (`exact_full_k0.8`,
  `tol2_full_k0.8`, horizons, families) is recorded in `data/models/wi048/*_cells.json` and the
  summary reports — read those; no re-derivation.
- **Phase-1 scope recommendation (non-binding):** admin leans to shipping View 3 (candlestick
  inspector) + View 1 (histograms) first — they answer the recent gate questions fastest. The
  plan proposes the final phase split.
- **Family-OOF materialization (admin, 2026-11-19):** MATERIALIZE pickle-family OOF
  probabilities to parquet in v1 — its own WI (batch scoring job over the fold pickles,
  checkpointed, core-h sized per the 2.5-h default). Until that artifact exists the family
  selector shows family AUC/IC stats from `data/models/wi048/manifest.parquet` only.
- **`state` column (admin, 2026-11-19):** EXCLUDED from the whitelist — key/slicing axis only,
  like `close`/`atr`.
- **KPI watermark wording (factual fix):** OOF predictions are out-of-fold by construction; the
  KPI watermark reads "out-of-fold, but threshold-selection bias risk" — the selection bias
  comes from interactively picking thresholds on the same OOF stream, not from sampling.
- **Planning model:** the PLAN is produced by Opus 5.5 via the OpenRouter Batch API
  (`batch_plan.py`, no --model override). The `--model anthropic/claude-haiku-5.5` flag above is
  the INTAKE EDITOR only (non-reasoning cheap gate), not the planner.
- **Family-OOF parquet destination:** the read-only rule covers the VISUALIZER process only.
  Model/pipeline artifacts (including the materialized family-OOF parquet) go to their canonical
  `data/` home (alongside `data/oof_*.parquet`), produced by a dedicated WI — the same exception
  every existing builder enjoys. The visualizer itself still writes only to `state/viz/`.
  Keys must align with the panel's `symbol/date` convention (`symbol` from filename, never the
  full stem — DATA_CONTRACT §1).
- **Phase 1 composition (admin rulings consolidated):** Phase 1 = View 3 (candlestick inspector)
  + View 1 legacy-OOF targets; the family-OOF materialization WI is its own scheduled WI (v1
  track) that may run as MULTIPLE checkpointed jobs — the 2.5 core-h figure sizes each human-
  confirmation interval, and AGENTS.md pacing policy governs the total (check credit balance
  before each job, pause when modeled balance < 25%). Once materialized, the family selector
  lights up; it shows manifest stats only until then.
- **`y_20d_stay` in View 1:** yes — selectable. It is a member of the legacy 3-class
  decomposition. SCHEMA FACT (probed): `y_20d_stay` exists ONLY in `data/features/targets_*.parquet`
  — `oof_*.parquet` contains NO fifth target block (4 blocks: y_15d_high, y_15d_low, y_20d_up,
  y_20d_down; no stay probabilities/folds materialized). View 1 therefore exposes `y_20d_stay`
  as a hit-rate slice from the targets parquet, not an OOF-probability selector.
- **Sequencing (admin 2026-11-19, supersedes earlier ordering): TRACK B BEFORE TRACK A.** The
  L0/L1/L2 research WIs are decomposed and dispatched first; visualizer WIs follow. The batch
  plan in flight (`26-W47-visualizer-audit-workbench`) covers both tracks; when it lands, WI
  cards are created Track-B-first regardless of the plan's own ranking.
- **Cache path (fixed):** `state/viz/` is the default. `tools/visualizer/cache/` is not used.
- **Barrier overlay ruling:** recompute-from-geometry is PERMITTED display math (read per-cell
  geometry from `data/models/wi048/*_cells.json` + reports; slice raw OHLCV; draw). No feature or
  target is re-derived. The plan must still state the boundary explicitly per overlay element.

## L0/L1/L2 TRACK (admin, 2026-11-19: layers UNFROZEN — integrate into this plan)

The layers are NOT frozen; the attached source prompt's engineering content is a candidate
research track. The plan must include, as separate WIs from the visualizer WIs, costed and
ranked:

- **L0 net-new orthogonal pure-price features** from the prompt not yet in the 249-col panel:
  KAMA variant / Connors RSI / StochRSI / CLV / NR4-NR7 / CUSUM structural-break flag / rolling
  failure count of prior primary signals — each its own BH-FDR family, judged predictive-only at
  L1 (D-023). FracDiff (d=0.4) and Hurst ALREADY EXIST (`feature_engine.py`) — do not re-propose.
- **L1 causal vs ex-post bifurcation:** trailing (causal) swing/retracement levels vs ex-post
  audit targets (MFE/MAE, capture efficiency, fwd-vol) — the ex-post ones are LABELS ONLY, never
  features; the plan must design the leakage boundary for any new columns.
- **L2 gap-aware triple-barrier engine:** profit barrier +10% or k_tp·σ_pre, stop k_sl·σ_pre
  (parallel 1.0/1.5/2.0σ profiles computed as columns), gap-aware stop fills (GAP_SL at bar
  open), T1 milestone (+5%/1.5σ), trailing ATR stop R-multiple, benchmark excess (SPY/XIU),
  forced TIMEOUT=0. Existing first-touch/target grids and the ratified fixed_h55 overlay are
  prior art, not the same object — the plan states what is genuinely net-new vs variant.
- **Event sampling rule:** unfiltered overlapping events (capture ALL historical triggers,
  ignore concurrent open positions to avoid path-dependent bias) — the plan must state whether
  the existing swing detector already satisfies this and what changes if not.
- **Sync/export contract:** schema-validated export (audit config) consumed by the future gate
  WI (per DECISIONS on the whitelist).

These research WIs follow every repo invariant: n_jobs=2, float32, pyarrow.dataset /
symbol-sequential, checkpointed ≤ 2.5 core-h per human-confirmation interval, credit monitor
before dispatch, no secrets, PROVISIONAL verdicts until admin ratification.

## INTAKE FINAL ANSWERS (2026-11-19)

1. **One plan, two WI tracks:** the L0/L1/L2 research track is part of THIS deliverable — the
   plan carries both the visualizer WIs (Track A) and the research WIs (Track B) as separate,
   independently-gated WIs in the same decomposition.
2. **200 trades/yr is an ILLUSTRATIVE DISPLAY LINE ONLY** — the product aspiration per AGENTS.md
   ("never block/fail a current step for not reaching the aspiration"). It gates nothing in the
   visualizer; each research WI is judged only by its own tier gate (L1 predictive-only).
3. **Board frozen-state:** the admin's ruling above (L0/L1/L2 UNFROZEN, 2026-11-19) supersedes
   the BOARD's "L1 library FROZEN" line; correcting BOARD.md is a pre-dispatch human action
   outside the planner's scope. The planner reads the UNFROZEN state from this brief.

## ALREADY PLANNED — do NOT re-propose

- L0/L1 extension sprint D-026 (done, ratified). L2 rebuild D-027 (done, ratified; EVAL split
  SPENT — any new L2 EVAL needs a new prereg + new split). Mechanism survey folded. Feature
  shortlist WI-047 integrated. **The visualizer is new tooling, not a sprint research item.**

## IDEAL RESULT

A markdown plan per the batch prompt contract:
1. **Stack recommendation** with rationale (VPS headless, git-friendly, dep footprint).
2. **Phased WI decomposition** — each WI: title, files-touched (`write_files` manifest preview),
   core-hour estimate, data read-path spec against the verified schemas above, finish condition.
3. **Data-access layer design** — one loader module spec: schema assertions, join keys
   (symbol/date), memory caps, pyarrow.dataset usage, float32, example filter latency budget.
4. **View specs** — which of the 6 mapped views ship in which phase, with what UI state.
5. **3 biggest risks** + cheapest mitigation each (e.g. VPS memory on 674-file OHLCV lazy reads).
6. **Open questions** the pack left unresolved — never guessed.
