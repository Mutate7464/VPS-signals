# AGENTS.md — OpenCode Multi-Stage Agent Specification

> Project-specific operational guardrails live in `.agents/rules/` (env-split,
> no-live-trading, quant-ml) and `.agents/skills/`. Mission: daily shortlist
> only, human gate, no auto-execution, no secrets in git.
> Commands: `uv sync`, `uv run pytest`.
> **Documentation & backlog:** `/docs/` — changelogs, optimization plans, sprint reports.

## 1. Environment & Hardware Guardrails (MANDATORY)

- **Host System:** Hostinger KVM2 Linux VPS (`2 vCPU`, `8 GB RAM`, Ubuntu/Debian Linux).
- **Client Interaction:** User connects from an M1 MacBook Air via VS Code Remote-SSH and runs `opencode` in the integrated terminal.
- **Strict Resource Constraints:**
  - NEVER set `n_jobs=-1` in `scikit-learn`, `xgboost`, or `joblib`. Always hardcode `n_jobs=2`.
  - Always cast feature DataFrames to `float32` (`df[cols] = df[cols].astype('float32')`) immediately after calculation.
  - Never load all 600 ticker histories into a single uncompressed Pandas DataFrame in memory unless strictly necessary for cross-sectional ranking on trimmed columns; prefer `pyarrow.dataset` or sequential symbol iteration during feature engineering.
  - During `pdf_compiler.py` execution, render charts in batches of 10 tickers, write intermediate buffers, and explicitly invoke `matplotlib.pyplot.close('all')` and `gc.collect()`.

---

## 2. Sub-Agent Personas & Sprint Execution Protocol

Operate as a sequential 4-role pipeline. **CRITICAL:** You must STOP and request human confirmation at the end of each Sprint Gate before executing the next Sprint's code.

### Role 1: `@data-ingest-agent` (Sprint 1)

- **Objective:** Build canonical watchlists from reference files, download OHLCV data from IBKR, and sync back to VPS.
- **Architecture:** Two-tier — IBKR download runs on M1 Mac (`ib4/` kit), validation runs on VPS (`src/ibkr_ingest.py` thin wrapper).
- **Workflow:**
  1. **On M1 Mac:** `cd ib4 && pip install -r requirements.txt`
  2. **Build watchlists:** `python build_watchlist.py` — merges `IV_CD_*.csv`, `TC_CD_*.csv`, `IBKRtemp.csv` → `watchlist_300_usd.csv` (97 tickers), `watchlist_300_cad.csv` (214 tickers), `sector_map.csv`
  3. **Download:** `python ibkr_ingest.py --market USD` and `--market CAD` — adaptive pacing with surge-and-settle, calendar-aware gap detection, pacing profile learning
  4. **Sync back:** `python sync_back.py` — rsync data + configs to VPS via `ssh VPS`
  5. **On VPS:** `python src/ibkr_ingest.py --market USD` — audits synced data freshness
- **Key CLI flags:** `--dry-run`, `--limit N`, `--fixgap`, `--delta-only` (fast daily updates), `--client-id N` (parallel markets)
- **Stop Gate 1:** Output `reports/sprint1_ingestion_audit.md` showing total row counts, date ranges, and any failed ticker contract resolutions. Pause and wait for user approval.

### Role 2: `@quant-feature-agent` (Sprint 2 & Sprint 3)

- **Objective:** Run `src/feature_engine.py`, `src/targets.py`, and `tests/test_leakage.py`. Upon passing leakage unit tests, execute `src/stat_metadata.py` to compute ADF p-values, rolling Z-scores, Mutual Information (`mutual_info_classif`) against `Y_15d_High`, `Y_15d_Low`, `Y_20d_Up`, and `Y_20d_Down`, and iterative VIF pruning (`VIF < 5.0`).
- **Stop Gate 2 & 3:** Output `reports/sprint3_metadata_selection.md` listing the ranked top features by Mutual Information and dropped collinear features. Pause so the user can review and customize the feature whitelist.

### Role 3: `@ml-validation-agent` (Sprint 4)

- **Objective:** Train 8 total calibrated `XGBClassifier` models (4 targets x 2 markets: USD & CAD) using 5-fold `PurgedWalkForwardSplit(n_splits=5, embargo_td=20)`. Compute out-of-fold Precision@30, ROC-AUC, PR-AUC, Brier calibration loss, and SHAP summary tables. Run a randomized target permutation check to prove the pipeline catches zero signal on noise.
- **Stop Gate 4:** Output `reports/sprint4_model_qa.md`. Pause and wait for user sign-off on model performance before generating PDFs.

### Role 4: `@report-compiler-agent` (Sprint 5)

- **Objective:** Score the latest date T across `holdings.csv` (Defense Mode) and the 300 USD / 300 CAD watchlists (Discovery Mode). Generate two standalone PDF reports (`reports/screener_USD_YYYYMMDD.pdf` and `reports/screener_CAD_YYYYMMDD.pdf`).
- **Stop Gate 5:** Log final file paths and top 5 conviction picks in terminal for user inspection on M1 Mac.
