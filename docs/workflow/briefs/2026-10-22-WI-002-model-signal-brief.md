# WI-002 Context Brief — Model Signal Diagnosis (E2 Faithful Re-Run)

> Generated: 2026-10-22 | For: Planning models working on WI-002 · G-001
> Source evidence: `reports/sprint4_model_qa.md`, `src/targets.py`, `src/feature_engine.py`, `src/stat_metadata.py`, `src/xgb_trainer.py`, `config/settings.yaml`, `data/` on disk, `D-002-model-signal-diagnostics.md`, `board.md`

## WHAT (2 lines)
WI-002 diagnoses **why Gate 4 failed on all 4 USD targets** (all metrics ≈ random; ROC-AUC 0.426–0.512, BSS negative, P@K lift 0.79–1.08 vs ≥1.5 threshold). The root cause is already identified (H1, very-high prior): the Gate 4 run was performed on the **5-ticker test fixture, not the 546-ticker real USD universe** — the plan re-runs faithfully on real data.

## STATE

### The artifact on disk is a 5-ticker fixture run
- `data/oof_USD.parquet`: **1,400 rows, 5 symbols** (`AAPL, AMZN, JPM, MSFT, NVDA`), date range 2025-08-28 → 2026-09-23 (line-confirmed via `uv run python` read). P@K effectively K=1.
- `data/train_meta_USD.json`: fold `best_iteration` values: `y_15d_high`: `[-1, -1, 3, 8, 16]`; `y_15d_low`: `[-1, -1, -1, -1, 5]`; `y_20d_up`: `[-1, -1, 67, 68, 161]`; `y_20d_down`: `[37, 78, 39, 130, 388]`. Many folds stopped at round 0 (no learning).
- `data/features/features_USD.parquet`: **84 KB** — same 5-ticker artifact.
- `data/metadata_catalog_USD.json`: **63 raw → 10 surviving (VIF < 5.0) → 7 whitelisted per target** (30th-percentile MI). Surviving features are all from the Amihud/KAMA/entropy/ADX/BB-width families — RSI, MACD, ATR%, VWAP, OBV, Yang-Zhang, Kalman, Hurst(50,100), frac-diff all pruned. MI values were inflated by ticker-identity signal (`amihud_50` ticker-mean R²=0.49).

### Real data is present but never used by the pipeline
- `data/raw_ohlcv/market=USD/`: **546 parquet files**, 2,181,907 total rows, 2006-10-26 → 2026-10-21. `load_market_frame()` falls back to `data/raw_ohlcv_test/` (5-ticker fixture) when `data/raw_ohlcv/` has no parquet — but **546 files exist NOW** (synced by WI-003 after the Gate 4 run).
- `data/dead_letter_tickers.csv`: **72 quarantined tickers** (73 lines incl. header): 37 USD, 35 CAD. 70 tagged `CB-01` (extreme returns), 2 tagged `CB-02` (short history). `load_market_frame()` **does not read or apply this list** (`src/feature_engine.py:288-303` — no quarantine logic exists).

### What the pipeline does (Sprints 2→4)
- **Targets** (`src/targets.py:103-147`): 4 binary labels on forward windows — `y_15d_high` (exhaustion), `y_15d_low` (V-bottom), `y_20d_up`/`y_20d_down` (OLS slope+R² ≥ 0.60 + ATR-adjusted return). Constants: `ATR_WINDOW=20`, `TREND_ATR_MULT=2.0`, `TREND_MIN_R2=0.60`.
- **Features** (`src/feature_engine.py:195-282`): 63 columns across RSI(5,14,21), BB(5,10,20,50,100), MACD, ADX(5,10,20,50,100), ATR%(5,10,20,50,100), OBV(5,10,20,50,100), Hurst(20,50,100), frac-diff(d=0.40), entropy(10,20), Kalman, KAMA(5,10,20,50,100), VWAP(5,10,20,50,100), Amihud(5,10,20,50,100), Yang-Zhang(5,10,20,50,100). All causal, all float32.
- **Metadata** (`src/stat_metadata.py`): ADF on 50 tickers → flag if median p>0.05 → rolling Z-score transform; MI (`mutual_info_classif`) on 80% train split; iterative VIF < 5.0 pruning (drop lowest mean-MI of each collinear pair); cross-sectional percentile ranks (`_cs_pct`); whitelist = features with MI ≥ 30th percentile within surviving set.
- **Trainer** (`src/xgb_trainer.py`): `PurgedWalkForwardSplit(n_splits=5, embargo_td=20)`, 40% initial train, 20% calib holdout. `XGBClassifier(tree_method="hist", n_jobs=2)` + isotonic calibration (fallback to sigmoid/Platt if < 25 calib positives — CB-04). 5 placebo permutation seeds. Parameters from `config/settings.yaml` (line 51-62): `max_depth=4, learning_rate=0.03, n_estimators=400, subsample=0.8, colsample_bytree=0.7, min_child_weight=20, reg_alpha=1.0, reg_lambda=5.0`. Outputs: `data/oof_{MKT}.parquet`, `data/train_meta_{MKT}.json`, `data/predictions_{MKT}_latest.parquet`, `models/{mkt}/{target}.pkl`.

### Gate 4 thresholds (what "PASS" means)
> From `G-001-dual-market-screener.md`: P@K lift ≥1.5×, BSS >0.05, PR-AUC lift >1.35×, deflated IC ρ>0.04 (t>2.5), placebo CB-05 clean. Current: **all 4 USD targets FAIL every threshold** (`sprint4_model_qa.md:17-20`).

### The E2 plan — what Build will execute (Steps 1–7)
1. `scripts/e2_preflight.py` — audit dataset size, quarantine impact, projected RAM, fit verdict.
2. `src/run_logging.py` — structured JSONL logging, RSS tracking, XGBoost TrainingCallback, memory guard.
3. Loader fix in `src/feature_engine.py` — quarantine filter, `datetime64[ns]` normalization, streaming per-symbol iterator, `train_start: "2016-01-01"` config, fixture refusal.
4. Feature regeneration for USD on real 546-ticker data (streaming, memory-safe).
5. Metadata efficiency (MI subsampled to 300K rows, VIF corr-once on 500K rows, seeded ADF tickers).
6. Trainer hardening (slim panel, per-target checkpoint, XGBoost logging, `--resume`, `--placebo-seeds`).
7. QA header (universe size in report) + `scripts/run_e2.sh` launcher (stop/restart `hermes-gateway`, cgroup memory cap 5.5 GB, `OMP_NUM_THREADS=2`).

## FILES (≤8, with why and line ranges)
1. **`reports/sprint4_model_qa.md`** — The failed Gate 4 output you're diagnosing. Read all 118 lines. Key: lines 17-20 (USD governance table with all FAIL), lines 22-29 (placebo — clean), lines 31-38 (generalization gap), lines 40-55 (regime stability), lines 57-64 (SHAP dominance).
2. **`docs/workflow/designs/D-002-model-signal-diagnostics.md`** — Hypothesis ranking and experiment decision matrix. Read lines 1-66. Key: lines 12-23 (artifact findings — the 5-ticker discovery), lines 27-33 (H1–H4 ranked), lines 47-56 (E0–E5 experiments), lines 57-59 (decision matrix).
3. **`docs/plans/2026-10-22-WI-002-e2-full-universe-rerun.md`** — The 9-step executable E2 plan. Read lines 1-145. Key: lines 11-26 (findings table — data vs pipeline alignment, all measured), lines 38-128 (Steps 1–9 with acceptance criteria and verify commands), lines 130-138 (estimated cost, out of scope).
4. **`src/feature_engine.py:288-303`** — `load_market_frame()` — the fallback bug. Reads `RAW_DIR` first, if no parquet found falls back to `FIXTURE_DIR` (the 5-ticker test data). No quarantine filter exists.
5. **`src/stat_metadata.py:99-107,113-144`** — MI computation and VIF pruning. `compute_mi` (line 99) uses all training rows; `compute_vif_pruning` (line 113) recomputes `corr()` in a while-loop on the full float64 frame. Both will be O(N²) on 1.3M real rows.
6. **`src/xgb_trainer.py:190-215,265-358`** — `build_panel()` drops only NaN-target rows (`dropna(subset=TARGET_COLUMNS)` at line 273) — the raw panel from `build_panel` is kept in memory alongside the dropped version. `train_market()` (line 265) writes all outputs only at end — no per-target checkpointing.
7. **`src/targets.py:120-147`** — The 4 target definitions. Read lines 120-147. Key: `cond1/cond2` logic for `y_15d_high`/`y_15d_low` (lines 121-128), trend slope+R² logic for `y_20d_up`/`y_20d_down` (lines 131-134). Forward-window alignment uses `_forward_roll` (line 48) and `_ols_forward_slope_r2` (line 69) — both only read [t+1, t+h].
8. **`config/settings.yaml:47-62`** — Modeling parameters. E2 does NOT change these. `n_splits: 5`, `embargo_td: 20`, `vif_threshold: 5.0`, XGBoost: 400 trees, depth 4, lr 0.03, min_child_weight 20.

## LANDMINES
- **5-ticker fixture artifact:** every file in `data/` (oof, features, meta, catalog) is from a 5-symbol universe. Any planning that inspects these files must treat them as invalid for the real-universe re-run. The 546 real files in `data/raw_ohlcv/market=USD/` are untouched by the pipeline.
- **Quarantine not applied:** 37 USD tickers in `dead_letter_tickers.csv` will be included unless E2 Step 3 loader is implemented. Must read `src/feature_engine.py:288-303` — no quarantine import or filtering exists today.
- **Memory constraint is real:** Host has 7.9 GB total, 0 swap. Current panel build keeps 2 copies of a ~63-column DataFrame. At 2.18M rows × 63 cols × 4 bytes = ~550 MB per copy × 2 (raw + panel) + targets + concat overhead → 2–3 GB peak for fixture, but 4+ GB for real data. Plan caps peak RSS at 4.5 GB with guard.
- **No hyper-parameter changes allowed** in E2. `config/settings.yaml` stays as-is. This is a faithful re-run to confirm H1, not a tuning pass.
- **Step 8 is human-launched**, not agent-executed. Build only prepares Steps 1–7. The training run (1–2.5 h) happens as a detached background process with Hermes and opencode stopped.

## OPEN QUESTIONS
- **Admin approval status:** The plan is written (board shows EXECUTING with plan file named), but the board row also says "Step 8 human-launched; Step 9 analysis." Has the admin explicitly approved Steps 1–7 execution? The plan resolves this as "awaiting admin go (board must show EXECUTING naming this file before Build starts)" — line 4.
- **`--min-date` default:** Plan defaults to `2016-01-01` (line 40). Admin may override. The preflight (Step 1) will project row counts for both 2016-01-01 and 2006-01-01. If the admin wants full history, the plan says "raise `--min-date` to 2019-01-01 if RSS > 3.5 GB" (line 133).
- **CAD deferred:** The plan explicitly defers CAD until after USD E2 review (line 145). Anyone planning CAD work should wait.