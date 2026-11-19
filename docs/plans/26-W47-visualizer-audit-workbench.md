## Recommendation
Build a **Dash + Plotly** app in `src/visualizer/`. Run it as one process bound to 127.0.0.1 and reach it through an SSH tunnel. It reads artifacts in place through a column-projecting loader with a byte budget, and it writes only to `state/viz/`.

Ship in four Track A phases. Phase 1 is View 3 plus View 1 on legacy OOF targets. Family-OOF materialization is a separate checkpointed batch WI that follows Phase 1. Track B (L0 features, L1 bifurcation, L2 barrier engine) is a ranked set of separate WIs. No Track B card is dispatched until a human corrects BOARD.md, and each card also needs its own prereg.

## Goal
Plan a read-only, human-in-the-loop visual audit workbench. The success test is that the admin can answer "why did model X win or fail" in minutes. The workbench displays evidence and computes no verdicts.

Track B research WIs are planned alongside it but gated separately. Every WI carries an owner, a core-h estimate, its files touched, and a finish condition.

## Current conditions
- **Governance:** D-027 closed and ratified 2026-11-16, with no open sprint. D-026 and D-027 are already planned and WI-047 is integrated; none is re-proposed here.
- **Freeze conflict:** BOARD.md says L1 is FROZEN, but the 2026-11-19 admin ruling says L0/L1/L2 are UNFROZEN. Correcting BOARD.md is a pending human action.
- **Features:** `data/features/features_{USD,CAD}.parquet` holds 249 causal float32 columns plus symbol, date, state, close and atr.
- **Targets:** `targets_{USD,CAD}.parquet` adds market and `y_20d_stay`.
- **OOF:** `data/oof_{MKT}[_variant].parquet` has 41 columns. There are 4 legacy targets, each with `y_/p_/fold_` columns, plus `_pl0/1/2` barrier pairs and `fwd_atr_ret_15/20`.
- **Raw OHLCV:** 1,068 per-symbol files (USD 674, CAD 394).
- **Model manifests:** wi040 has 9,745 fold rows and wi048 has 295 rows. Pickles are xgboost/lightgbm across 9 families and h5–h55.
- **Audit today:** static reports only.
- **Hardware:** VPS with 2 vCPU, 8 GB, no swap and CPU credits. Python 3.14, uv only.
- **L2 EVAL split is SPENT.**
- **Signal context:** the surviving signal is vol-regime shaped (atr_pct_3, entropy_*, hurst_*, adx_*, kama_er_15).

## Ideal result
The admin opens a browser tunnel and can do the following:
- filter on whitelisted features;
- pick any legacy target, prediction or `y_20d_stay` slice;
- see KPIs with the watermark "out-of-fold, but threshold-selection bias risk";
- click a decile bin or row to get an OHLC window (−40/+15 bars) with feature subplots and labeled barrier overlays;
- export a schema-validated whitelist file for a future gate WI.

Across all of this:
- Filter round-trips take ≤1 s and the idle server uses near-zero CPU.
- No file outside `state/viz/` is written, except by the separately carded family-OOF batch job.
- Track B is costed and ranked, with each WI waiting on its gates.

## Plan

### Stack choice: Dash + Plotly (runner-up: Marimo)

| Criterion | Dash + Plotly | Marimo | Streamlit |
|---|---|---|---|
| Headless over SSH | `gunicorn -w 1` on 127.0.0.1 | `marimo run --headless` | yes |
| Git-friendly | plain `.py` callbacks | plain `.py` cells | plain `.py` |
| 1 s budget | only the affected callback runs | reactive DAG; recompute scope depends on cell graph | whole script reruns per interaction; caching required |
| Click-to-drill (View 3) | `clickData` is native and mature | possible via `mo.ui.plotly`, less direct | possible via component events |
| Idle CPU | Flask sleeps; no polling if `dcc.Interval` is avoided | low | low |
| Memory | one worker holds one copy of the panel | one kernel per session | one copy per session unless cached globally |

Why Dash: explicit callbacks give per-control recompute and make the latency budget testable per callback. View 3's drill-down is a click-driven pattern that Dash handles natively. A single gunicorn worker guarantees one in-memory panel copy, which matters with no swap.

Operating rules:
- `debug=False` (no reloader).
- No `dcc.Interval`.
- 1 worker with 2 threads.
- `n_jobs=2` in precompute only.

### Data-access loader spec (`src/visualizer/loader.py`)

**Read path**
- Use `pyarrow.dataset.dataset(path, format="parquet")` per market file.
- Always pass a column projection: `to_table(columns=[keys + requested])`. Never load the full 249-column panel.
- Raw OHLCV is read per symbol only, with `pq.read_table("data/raw_ohlcv/market=M/symbol=T.parquet")`.
- No dataset object is ever opened over the whole `raw_ohlcv/` tree in the UI process.

**Schema assertions** (run at startup; any failure stops the server)
1. Features:
   - Column set = 249 classified columns from `src/swing_bsh/feature_inventory.py` ∪ {symbol, date, state, close, atr}.
   - All 249 are float32.
   - `date` is date32.
   - (symbol, date) is unique.
2. OOF:
   - Exactly the 41 listed columns.
   - `p_*` is in [0, 1] or NaN.
   - `fold_*` is integer.
   - `y_*` value sets are recorded, not hard-coded. The `_pl*` semantics are an open question.
3. Targets: `market` and `y_20d_stay` present; (symbol, date) unique.
4. Raw OHLCV per file: date32, float open/high/low/close/volume/average, and int64 barCount. Dates are monotonic.

**Joins**
- Join features ⋈ oof ⋈ targets on (symbol, date) within one market.
- Market comes from the filename for features and OOF, and is cross-checked against `targets.market`.
- A row-alignment index (int32 positions per source) is built once. It is cached at `state/viz/join_{MKT}.parquet` and keyed by a (path, size, mtime) fingerprint in `state/viz/manifest.json`. A stale fingerprint triggers a rebuild.
- Unmatched-row counts are displayed as evidence.

**Memory caps**
- A loader-level byte ledger estimates cost as `rows × cols × 4` before any load.
- Default UI budget is 3.0 GB for resident columns. Requests above it are refused with a UI message.
- Columns are held in an LRU keyed by (market, column).
- OHLCV uses an LRU of 32 symbols.
- Precompute jobs run as separate processes and must not start while UI RSS plus job estimate exceeds 6 GB.

**Dtypes**
- float32 throughout; no upcasting except for in-kernel reductions.
- symbol is dictionary-encoded.

**Latency example.** Row counts are not in the pack and Phase 0 measures them; the figures below assume an illustrative N = 2.5M rows per market.
- A 5-slider filter touches 5 float32 columns (~50 MB) as boolean masks: roughly 10–30 ms.
- Decile binning on the masked subset: roughly 100 ms.
- Bootstrap CIs run on a pre-aggregated (date, bin) → (n, hits) table, resampling dates (a date-cluster bootstrap), with B=200. This stays well under 200 ms because the date count is far below N.
- The target-shuffled null shuffles within date. It is computed by hypergeometric sampling on the same aggregate.
- The payload is server-side binned aggregates only (≤100 bins per histogram, target <200 KB JSON).
- Server budget is 400 ms compute plus 100 ms serialize, leaving ~500 ms for SSH and browser render.
- A Phase 0 benchmark replaces these estimates with measured numbers.

### View-to-phase split and UI state

| View | Phase | Source | Notes |
|---|---|---|---|
| Global bar + KPI strip | 1 (export in 2) | features ⋈ oof/targets | Sliders on whitelisted features only. Target selector covers legacy `y_*`, `p_*` and `y_20d_stay` (hit-rate only). |
| View 1, legacy OOF targets | 1 | same join | True/false histograms, decile hit rate, n, CIs, shuffled null |
| View 3, OHLC drill-down | 1 | raw_ohlcv + events + features | Overlay boundary defined in the next table |
| View 2, threshold sweep | 2 | OOF `p_*` + `fwd_*` | Reference line at 200 trades/yr, labeled illustrative |
| View 1, family namespace | 2 (stats), post-OOF (full) | manifests, then family OOF | Shows manifest AUC/IC until family OOF exists |
| View 4, Spearman/MI/dendrogram | 3 | precompute → `state/viz/` | |
| View 5, 2D hit-rate heatmaps | 3 | features × regime/year | SHAP/ICE loader hook is a stub (none exist) |
| View 6, PSI + Rank IC/ICIR | 3 | features vs fold ids | PSI bands <0.10 / 0.10–0.25 / ≥0.25 shown as labels, not verdicts |

**KPI definitions** (shown with the watermark)

| KPI | Definition |
|---|---|
| trades/yr | retained rows ÷ years in range (overlapping events counted) |
| hit rate | mean(y) over retained rows |
| lift | hit rate ÷ unfiltered base rate for the same target and period |
| EV | mean `fwd_atr_ret_h` for the horizon matching the target (15 for `y_15d_*`, 20 for `y_20d_*`) |
| profit factor | Σ positive fwd ÷ \|Σ negative fwd\| |

Sign handling for the low/down targets is an open question.

**UI state**
- A single `dcc.Store` filter spec holds market, target column, slider ranges, date range and the selected bin.
- It is serialized to the URL query string so views are reproducible and shareable.
- The server holds arrays; the client holds only the spec and aggregates.

**View 3 overlay boundary (artifact vs display math)**

| Element | Source | Class |
|---|---|---|
| Candles | raw OHLCV slice | artifact, read-only |
| Entry marker | OOF/targets row date | artifact |
| Exit marker at +h bars | bar counting | display math |
| Feature subplots | features parquet values | artifact (not recomputed) |
| Barrier lines | geometry from `wi048/*_cells.json` and reports × atr at entry | **recomputed display math**, labeled "not label source" |
| First-touch marker | recomputed from barrier lines | **recomputed display math**. Compared with the stored `y_*`; any disagreement shows a MISMATCH badge and is never reconciled |

If a cell's geometry does not fully determine the levels, the overlay is omitted and labeled "not reproducible".

### Phase 0: scaffold and contracts (owner: viz-dev agent / 0.5 core-h / done when below)
**WI-VIZ-00, Scaffold, loader, schema contracts, benchmark**
- write_files:
  - `pyproject.toml`, `uv.lock`
  - `src/visualizer/{__init__,loader,schema,cache,app}.py`
  - `tools/visualizer/serve.sh`
  - `tests/visualizer/{test_schema,test_loader_budget,test_readonly}.py`
  - `docs/visualizer/README.md`
  - `docs/kanban/draft/WI-VIZ-00.md`
- Read path: projected reads of features, OOF and targets for both markets; 10 sampled OHLCV files.
- Done when:
  - `uv lock` resolves on Python 3.14.
  - Schema tests pass on the real artifacts.
  - `test_readonly` passes: all writes are under `state/viz/` and data files are opened read-only.
  - `state/viz/bench.json` records row counts, peak RSS and filter latency.
  - The server idles at <1% CPU over 10 minutes.

### Phase 1: View 3 plus View 1 on legacy targets (owner: viz-dev agent; acceptance by admin)
**WI-VIZ-01, Join index, global bar, KPI strip** (0.5 core-h)
- write_files:
  - `src/visualizer/{join,kpi,controls}.py`
  - `tests/visualizer/test_join.py`
  - `docs/kanban/draft/WI-VIZ-01.md`
- Done when:
  - The join index is cached with its fingerprint.
  - KPIs match a hand-computed pandas reference on one market and target to 1e-6.
  - The watermark renders.
  - The p95 filter round-trip is ≤1 s over the tunnel.

**WI-VIZ-02, View 1 legacy** (0.3 core-h)
- write_files:
  - `src/visualizer/views/v1_feature_target.py`
  - `src/visualizer/stats/{bootstrap,null}.py`
  - `tests/visualizer/test_v1_stats.py`
  - `docs/kanban/draft/WI-VIZ-02.md`
- Done when:
  - Decile n sums to the retained count.
  - Date-cluster CIs are reproducible with a fixed seed.
  - The shuffled null mean ≈ base rate within MC error.

**WI-VIZ-03, View 3 drill-down** (0.3 core-h)
- write_files:
  - `src/visualizer/views/v3_ohlc.py`
  - `src/visualizer/overlay/barriers.py`
  - `tests/visualizer/test_overlay.py`
  - `docs/kanban/draft/WI-VIZ-03.md`
- Done when:
  - Clicking a bin or row opens a −40/+15 window in ≤1 s.
  - Every overlay element carries its boundary label.
  - The mismatch rate between recomputed first-touch and stored `y_*` is reported on 100 sampled events, shown as evidence only.

**Phase 1 exit:** the admin runs one "why did X win/fail" session and signs off in the WI card.

### Phase 2: sweep, export, family namespace, job runner (owner: viz-dev agent)
**WI-VIZ-04, View 2 threshold sweep** (0.3 core-h)
- write_files: `src/visualizer/views/v2_sweep.py`, test, card.
- Done when the quantile sweep matches a reference implementation and the 200/yr reference line is labeled illustrative.

**WI-VIZ-05, Export plus whitelist validator (sync/export contract)** (0.2 core-h)
- write_files:
  - `src/visualizer/export.py`
  - `docs/visualizer/EXPORT_CONTRACT.md`
  - `tests/visualizer/test_whitelist.py`
  - card
- Validator rules:
  - Reject any `fwd_*`, `y_*` or target-derived column, plus close, atr and state.
  - date, symbol and market are allowed as keys only.
  - Enforce float32 types and finite ranges.
  - Output goes to `state/viz/exports/`.
- Done when a negative test with each banned column fails and the output contains no verdict field.

**WI-VIZ-06, View 1 family namespace (manifest stats)** (0.2 core-h)
- write_files: `src/visualizer/views/v1_family.py`, test, card.
- Done when the selector lists 9 families × learner × horizon from both manifests and shows the AUC/IC stats.

**WI-VIZ-07, Job runner plus family-OOF pilot** (owner: viz-dev agent; ops human confirms each interval / 1.0 core-h)
- write_files:
  - `src/visualizer/jobs/{runner,credit_model}.py`
  - `tools/visualizer/score_family_oof.py`
  - `tests/visualizer/test_runner_checkpoint.py`
  - card
- The runner checkpoints per (market, family, fold) chunk. It stops after 2.5 core-h pending human confirmation, and pauses when the modeled credit balance is below 25%.
- The pilot scores 50 pickles.
- Done when per-pickle score time and RSS are measured, a resume after kill reproduces identical output, and the full-run job count is computed.

**WI-VIZ-08..n, Family-OOF materialization batches** (owner: viz-dev agent plus ops human / ≤2.5 core-h each; count from the pilot)
- Writes `data/oof_*` alongside existing files. This is the only non-`state/viz/` writer and is carded explicitly. Symbol comes from the filename per DATA_CONTRACT §1.
- Done when all manifest rows are scored or listed as failed, and the schema test passes.

**WI-VIZ-12, Switch View 1/2 family namespace to OOF** (0.2 core-h; after VIZ-08..n)

### Phase 3: Views 4, 5, 6 (owner: viz-dev agent)
**WI-VIZ-09, View 4** (1.5 core-h precompute)
- Spearman 249×249 per market, MI on a date-stratified subsample, and a dendrogram, all cached to `state/viz/v4/`.
- Done when the cache is fingerprinted and the view renders in ≤1 s from cache.

**WI-VIZ-10, View 5** (0.5 core-h)
- Feature-decile × vol-regime-decile/year heatmaps, plus a SHAP/ICE loader stub that raises "no artifact".
- Done when heatmap cell n is shown and cells with low n are greyed.

**WI-VIZ-11, View 6** (2.0 core-h, one checkpointed job)
- Rolling PSI per era and cross-sectional Rank IC/ICIR, cached.
- Done when PSI on two identical eras ≈ 0 and the bands are displayed as labels.

### Track B: separately gated research WIs
Gates:
- **G0:** BOARD.md corrected to show L0/L1/L2 UNFROZEN (owner: admin, human; 0 core-h).
- **G1:** per-WI prereg defining its own BH-FDR family.
- **G2 (L2 only):** new prereg plus a new split, because the L2 EVAL split is spent.

All Track B verdicts are PROVISIONAL. Outputs follow EXPORT_CONTRACT.md. New modules go under `src/l0_ext/`, `src/l1_bif/` or `src/l2_tb/`, with outputs in `data/features/l0_ext/`. The existing features parquet is not modified.

The ranking uses the WI-040 prior that vol-regime features carry nearly all the signal.

| Rank | WI | Net-new? | Build core-h (est.) | L1 eval | Finish condition |
|---|---|---|---|---|---|
| 1 | L0-NR (NR4–NR7) | net-new; vol-compression | 0.3 | prereg-sized, ≤2.5/job | causality test (no t+1 data); predictive-only result at L1 per D-023 |
| 2 | L0-CUSUM break flag | net-new; regime | 0.4 | same | same, plus a test that flags are not revised |
| 3 | L0-CLV | net-new | 0.2 | same | same |
| 4 | L0-KAMA variant | variant of kama_er_15 | 0.2 | same, only if View 4 shows \|ρ\|<0.9 to kama_er_15 | redundancy report first |
| 5 | L0-StochRSI | net-new | 0.2 | same | same |
| 6 | L0-ConnorsRSI | net-new | 0.3 | same | same |
| 7 | L0-FailCount | net-new; highest leakage risk | 0.5 | same | failure counted only after outcome resolves (lag ≥ h); leakage test |
| 8 | L1-BIF design | boundary formalization; MFE/MAE labels already exist as families | 0.2 | none | doc plus tests: swing levels use the confirmation date, not the pivot date; MFE/MAE, capture efficiency and fwd-vol are confined to label namespaces |
| 9 | L1-SWING trailing features | net-new features | 0.5 | prereg | causal tests pass |
| 10 | EVT-AUDIT swing detector | audit | 0.2 | none | states whether all overlapping triggers are captured, with counts |
| 11 | L2-TB gap-aware engine | **variant:** k·σ barriers, first-touch, target grids, fixed_h55. **Net-new pending code audit:** gap fill at bar open, parallel 1.0/1.5/2.0σ columns, T1 milestone (+5%/1.5σ), trailing ATR R-stop, SPY/XIU excess, forced TIMEOUT=0 | 1.5 | **G2 required** | unit tests on synthetic gap bars; reproduces fixed_h55 when the new features are disabled |

Shared Track B write_files pattern: `src/<module>/<feature>.py`, `tests/<module>/test_<feature>.py`, `data/features/l0_ext/<feature>_{MKT}.parquet` (or `reports/` for evaluations), and `docs/kanban/draft/WI-<id>.md`.

Owners:
- research agent (build);
- admin (prereg approval and ratification);
- ops human (job confirmation).

## Risks and mitigations
1. **OOM on the no-swap 8 GB VPS.** Causes: eager panel loads, a dataset scan across 674/1,068 OHLCV files, or a precompute job running alongside the UI.
   - *Cheapest mitigation:* the loader's byte ledger refuses over-budget loads, and `test_loader_budget` enforces it. OHLCV is per-file with an LRU of 32. Jobs check UI RSS before starting.
2. **CPU-credit drain from family-OOF scoring** (9,745 + 295 pickles) and Phase 3 precompute.
   - *Cheapest mitigation:* the pilot in WI-VIZ-07 measures cost before any full run. The runner enforces the 2.5 core-h confirmation interval, pauses below 25% modeled credit, and resumes from checkpoints.
3. **Evidence read as verdict.** This covers threshold-selection bias on the sweeps and KPIs, and recomputed barrier overlays disagreeing with the stored labels.
   - *Cheapest mitigation:* a mandatory watermark on every KPI and sweep, a MISMATCH badge rather than silent reconciliation, overlay boundary labels, and a test asserting that no verdict or adopt/reject strings appear in UI or export output.

## Open questions
- Has BOARD.md been corrected to show L0/L1/L2 UNFROZEN? This blocks all Track B dispatch; Track A is not blocked.
- What are the panel row counts per market? They are needed to confirm the 3 GB budget and the latency estimates.
- What do `_pl0/_pl1/_pl2` encode, and what is the value set of `y_*`?
- What is the EV sign convention for `y_15d_low` and `y_20d_down`?
- Do the manifests record per-fold test date ranges and feature lists? These are needed for family-OOF scoring.
- What filename convention should family OOF use under `data/` (variant suffix or new pattern)?
- How is the CPU-credit balance modeled on the Hostinger KVM2, and from what source?
- What else runs on the VPS? This determines the real memory headroom.
- Is SPY/XIU present in `raw_ohlcv`, which L2-TB benchmark excess needs?
- Do the wi048 cells json files fully determine barrier levels, including what `k0.8` and `tol2` mean?
- Do the existing first-touch fills already handle gaps? This sets the net-new vs variant split for L2-TB.
- Does the existing swing detector emit overlapping triggers? EVT-AUDIT answers this.
- Do Dash, pyarrow, xgboost and lightgbm all lock on Python 3.14 under uv?
- Is a per-WI L1 evaluation cost available from wi040 manifest timings, so L0 eval jobs can be sized?

## What would change this plan
- **Dash fails to lock on Python 3.14,** or the admin wants ad-hoc notebook-style exploration: switch to Marimo. The loader, cache and job runner carry over unchanged.
- **Phase 0 shows panel rows small enough** that all 249 columns fit under 2 GB: drop the column LRU and load the panel eagerly at startup.
- **The pilot shows full family-OOF scoring above ~10 jobs:** defer VIZ-08..n behind Phase 3 and keep the family namespace on manifest stats only.
- **BOARD.md remains uncorrected:** Track B stays parked and Track A proceeds unchanged.