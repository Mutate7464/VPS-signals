# 00\_MASTER\_HANDOVER\_AND\_WORKFLOW.md — Executive Summary, Split-Node Architecture & Step-by-Step Agent Handover

## 1\. General Project Summary & Strategic Intention

- **Mission Statement:** Build an institutional-grade, zero-leakage quantitative stock screening and portfolio defense pipeline covering **300 USD equities (`SMART/NASDAQ/NYSE`)**, **300 CAD equities (`SMART/TSE`)**, and **active portfolio holdings (`holdings.csv`)**.  
- **Core Analytical Edge:** Combine multi-timeframe classic technical indicators (`RSI`, `Bollinger Bands %B & Width`, `ATR-Normalized MACD`, `ADX`, `OBV`) with frontier quantitative regime features (`Hurst Exponent`, `Fractional Differentiation`, `Kalman Filter Spread`, `Shannon Entropy`, `KAMA Efficiency`, `Yang-Zhang Realized Volatility`). Filter raw features through a statistical metadata layer (ADF stationarity, cross-sectional percentile ranks, Mutual Information, and VIF \< 5.0 collinearity pruning) before feeding calibrated **XGBoost (`hist`)** classifiers.  
- **Capital Allocation Output (Dual-Mode PDF Tearsheets):**  
  1. **Defense Mode (`holdings.csv` Surveillance):** Ranks active portfolio holdings by `Exit_Urgency = max(P(Y_15d_High), P(Y_20d_Down))` to flag immediate local top exhaustion (`15d_High`) or sustained bearish trend breakdowns (`20d_Down`).  
  2. **Discovery Mode (`watchlist_300_usd.csv` & `watchlist_300_cad.csv` Screening):** Ranks the 300 USD and 300 CAD universes to extract the **Top 30 Bottom Inflections (`Y_15d_Low`)** and **Top 30 Upward Momentum Trends (`Y_20d_Up`)** per currency, rendered in a 4-panel chart layout (Candlesticks \+ BBands \+ Peak/Trough markers, Volume, RSI, and the \#1 SHAP-ranked model indicator).

---

## 2\. Split-Node Hardware Topology & Expected Daily Workflow

To eliminate the need to run a heavy GUI/Java X11 environment or expose IBKR two-factor authentication on the remote Linux VPS, the architecture strictly separates **Local Data Ingestion (M1 MacBook Air)** from **Remote Quantitative Compute (`opencode` on Hostinger KVM2 VPS)**:

| Node | Hardware Spec | Assigned Responsibilities |
| :---- | :---- | :---- |
| **Node A (Local Edge & Control Plane)** | **2021 M1 MacBook Air (macOS)** | 1\. Runs local **IB Gateway / TWS** (`127.0.0.1:4001` or `4002`). 2\. Executes `ibkr_ingest.py` locally to pull/update partitioned Parquet OHLCV files (`~/quant-screener-local/data/raw_ohlcv/`). 3\. Pushes incremental Parquet delta files to the VPS via `rsync` over passwordless `ed25519` SSH. 4\. Connects via **VS Code Remote-SSH** to direct `opencode` and view final PDF reports. |
| **Node B (Backend Compute Engine)** | **Hostinger KVM2 Linux VPS (`2 vCPU / 8 GB RAM`)** | 1\. Receives synced `data/raw_ohlcv/` and `config/*.csv` files in `/opt/quant-screener/`. 2\. Runs `opencode` agent to execute dry-run validation, multi-horizon feature engineering (`float32`), statistical metadata pruning, 5-fold Purged Walk-Forward XGBoost training (`n_jobs=2`), model QA diagnostics, and batched PDF tearsheet compilation. |

---

## 3\. End-to-End Human \+ Agent Operational Runbook (Step-by-Step)

### Phase A: Local IBKR Data Download on M1 MacBook Air (Human Execution)

1. **Launch IB Gateway / TWS on M1 Mac:** Log in to IB Gateway (Port `4001` Live or `4002` Paper) on macOS.  
2. **Update Watchlists & Holdings Locally:** Edit `~/quant-screener-local/config/holdings.csv`, `watchlist_300_usd.csv`, and `watchlist_300_cad.csv`.  
3. **Run Local IBKR Ingestion Script:**  
     
   cd \~/quant-screener-local  
     
   source .venv/bin/activate  
     
   python3 \-m src.ibkr\_ingest \--market HOLDINGS  
     
   python3 \-m src.ibkr\_ingest \--market USD  
     
   python3 \-m src.ibkr\_ingest \--market CAD  
     
   *Note: Cold 5-year backfill takes \~15 minutes total across 600 tickers (1.5s pacing); subsequent daily incremental delta runs take \<90 seconds.*

### Phase B: Sync Parquet Data & Configs from M1 Mac to Hostinger KVM2 VPS

4. **Execute One-Command `rsync` over SSH:**  
     
   rsync \-avz \--delete \~/quant-screener-local/config/ root@\<VPS\_IP\>:/opt/quant-screener/config/  
     
   rsync \-avz \~/quant-screener-local/data/ root@\<VPS\_IP\>:/opt/quant-screener/data/

### Phase C: Remote VPS Dry-Run, Feature Engineering, Modeling & PDF Generation (`opencode`)

5. **Connect via VS Code Remote-SSH:** Open `/opt/quant-screener` on the Hostinger KVM2 VPS from VS Code on your M1 Mac and launch `opencode` in the integrated terminal.  
6. **Execute the 5-Gate HITL Agent Workflow (Copy-Paste Prompts Below):**

#### Prompt 1 — Gate 1 (VPS Data Integrity & Dry-Run Audit)

> *"Read `AGENTS.md` and `docs/00_MASTER_HANDOVER_AND_WORKFLOW.md` through `05_MODEL_GOVERNANCE_AND_QA.md`. Remember that IBKR OHLCV Parquet files have already been downloaded on my M1 Mac and synced to `/opt/quant-screener/data/raw_ohlcv/`. Build and run a local Parquet dry-run verifier (`src/verify_synced_data.py`) that checks schema integrity, `float32` types, date continuity, and corporate action adjustments across `USD`, `CAD`, and `HOLDINGS`. Output `reports/sprint1_ingestion_audit.md` and STOP at Gate 1 for my review."*

#### Prompt 2 — Gate 2 (Multi-Horizon Indicators, Targets & Anti-Leakage Pytest)

> *"Gate 1 approved. Execute Sprint 2 (EP-02): implement `src/targets.py` and `src/feature_engine.py` following `02_SYSTEM_ARCHITECTURE.md` (classic \+ frontier indicators across \[5, 10, 20, 50, 100\] windows, strictly `float32`, `n_jobs=2`). Run `pytest tests/test_leakage.py` to prove zero look-ahead bias. Generate `reports/sprint2_feature_summary.md` showing class balance for `Y_15d_High`, `Y_15d_Low`, `Y_20d_Up`, and `Y_20d_Down` and STOP at Gate 2."*

#### Prompt 3 — Gate 3 (Statistical Metadata Profiling & Collinearity Pruning)

> *"Gate 2 approved. Execute Sprint 3 (EP-03): implement and run `src/stat_metadata.py` on the training split to compute ADF stationarity transforms, cross-sectional date-grouped percentile ranks, Mutual Information per target, and iterative VIF pruning (`VIF < 5.0`). Save `data/metadata_catalog_USD.json` and `data/metadata_catalog_CAD.json`, write `reports/sprint3_metadata_selection.md`, and STOP at Gate 3 so I can inspect the surviving indicator whitelist."*

#### Prompt 4 — Gate 4 (Purged Walk-Forward XGBoost Training & Model QA Suite)

> *"Gate 3 approved. Execute Sprint 4 (EP-04): implement `src/xgb_trainer.py` and `src/model_qa.py` using 5-fold `PurgedWalkForwardSplit(embargo_td=20)`, `tree_method='hist'`, `n_jobs=2`, and isotonic probability calibration. Run the Placebo Target Permutation Test, Precision@30 lift, Brier Skill Score, regime stability breakdown, and SHAP feature importance audit. Output `reports/sprint4_model_qa.md` and STOP at Gate 4."*

#### Prompt 5 — Gate 5 (Holdings Defense & Top 30 Buy-Side PDF Compilation)

> *"Gate 4 approved. Execute Sprint 5 (EP-05): implement and run `src/pdf_compiler.py` in memory-safe batches of 10 tickers (`plt.close('all')`, `gc.collect()`). Generate `reports/screener_USD_YYYYMMDD.pdf` and `reports/screener_CAD_YYYYMMDD.pdf` containing Section 1 (`holdings.csv` sorted by exit urgency `max(P_15d_High, P_20d_Down)`), Section 2 (Top 30 `Y_15d_Low` bottom picks), and Section 3 (Top 30 `Y_20d_Up` trend picks) with 4-panel annotated charts. Output the final summary table."*

### Phase D: Pull Final PDFs Back to M1 MacBook Air (Or View Directly in VS Code)

7. **Sync Reports to M1 Mac:**  
     
   rsync \-avz root@\<VPS\_IP\>:/opt/quant-screener/reports/\*.pdf \~/quant-screener-local/reports/  
     
   open \~/quant-screener-local/reports/