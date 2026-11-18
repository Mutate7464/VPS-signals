# 01\_PROJECT\_PLAN.md — PMP Project Charter & Agile Sprint Plan

## 1\. Project Charter & Executive Summary

- **Project Name:** Dual-Market Quantitative Stock Screener & Portfolio Exit Monitor (MVP v1.0)  
- **Execution Topology:** M1 MacBook Air (VS Code Remote-SSH Control Plane) \-\> Hostinger KVM2 Linux VPS (`2 vCPU`, `8 GB RAM`, `opencode` CLI Agent Backend)  
- **Business Objective:** Construct an end-to-end, leak-free machine learning pipeline that ingests daily OHLCV bars for 300 USD (`SMART/NASDAQ/NYSE`) and 300 CAD (`SMART/TSE`) equities plus active portfolio holdings via IBKR API, engineers classic and frontier technical indicators, filters features via statistical metadata, trains 4 point-in-time XGBoost regime classifiers, and compiles an annotated multi-panel PDF report.  
- **Target Regimes & Allocation Split:**  
  1. **Discovery (Buy-Side Screening on 300 USD & 300 CAD Watchlists):**  
     - `Y_15d_Low` (Bottom Inflection): Top 30 USD \+ Top 30 CAD tickers.  
     - `Y_20d_Up` (Upward Trend): Top 30 USD \+ Top 30 CAD tickers.  
  2. **Defense (Sell-Side Surveillance on Active `holdings.csv`):**  
     - Ranked descending by `Exit_Urgency = max(P(Y_15d_High), P(Y_20d_Down))` to flag immediate top exhaustion or downward trend breakdowns.

---

## 2\. Work Breakdown Structure (WBS) & Agile Epics (5 Sprints)

| Epic ID | Sprint | Module Name | Core Deliverables | HITL Verification Gate (Definition of Done) |
| :---- | :---- | :---- | :---- | :---- |
| **EP-01** | Sprint 1 | IBKR Ingestion & Parquet Store | `ibkr_ingest.py`, schema validation, incremental delta fetcher for `watchlist_300_usd.csv`, `watchlist_300_cad.csv`, and `holdings.csv`. | **Gate 1:** Human inspects `data/audit_ingestion_summary.csv` verifying 600+ tickers, corporate action adjustments (`ADJUSTED_LAST`), zero missing trading days, and IBKR pacing compliance. |
| **EP-02** | Sprint 2 | Multi-Horizon Feature Engineering | `feature_engine.py` computing classic & frontier indicators across `[5, 10, 20, 50, 100]` windows \+ forward target labeler (`targets.py`). | **Gate 2:** Human reviews `reports/feature_distributions.md` and verifies strict `t` vs `t+k` boundary alignment (zero `shift(-k)` leakage in `X` matrix). |
| **EP-03** | Sprint 3 | Statistical Metadata & Pruning | `stat_metadata.py` executing ADF stationarity checks, rolling cross-sectional Z-scores/percentiles, Mutual Information (MI), and VIF pruning (`VIF < 5.0`). | **Gate 3:** Human reviews `data/metadata_catalog.json` and approves the surviving feature whitelist (\~25–35 orthogonal features) before model training. |
| **EP-04** | Sprint 4 | Purged XGBoost Training & QA | `xgb_trainer.py` & `model_qa.py` implementing Purged Walk-Forward CV (`embargo=20d`), isotonic probability calibration, and SHAP extraction. | **Gate 4:** Human inspects `reports/model_diagnostics.md` (Precision@30, Brier Score, PR-AUC, placebo permutation test, top SHAP drivers) to sign off on model validity. |
| **EP-05** | Sprint 5 | Ranking & Annotated PDF Compiler | `pdf_compiler.py` rendering Holdings Exit Alerts \+ Top 30 `15d_Low` & Top 30 `20d_Up` tearsheets (USD & CAD) with OHLCV, BBands, RSI, and \#1 SHAP feature panel. | **Gate 5:** Human opens generated PDFs on M1 Mac via VS Code (`reports/screener_USD_YYYYMMDD.pdf` & `screener_CAD_YYYYMMDD.pdf`) to validate peak/trough markers. |

---

## 3\. Product Backlog (Deferred Post-MVP Items)

- **EP-06 (Backlog \- Post-MVP):** Dynamic Index Constituent Scraper — Automate retrieval of top 300 S\&P 500 / NASDAQ and top 300 S\&P/TSX Composite tickers by 60-day median dollar volume to replace manual CSV watchlists.  
- **EP-07 (Backlog \- Post-MVP):** Telegram Automated Digest Integration — Push daily PDF summary and urgent `holdings.csv` sell alerts (`P > 0.75`) via Telegram bot webhook on VPS cron completion.  
- **EP-08 (Backlog \- Post-MVP):** Regime-Conditional Hyperparameter Tuning — Optuna Bayesian optimization stratified by VIX / TSX volatility regimes.

---

## 4\. Risk Register & Mitigation Matrix (PMBOK Aligned)

1. **Risk R-01 (Look-Ahead Bias / Serial Correlation Leakage):** Overlapping 15d/20d forward labels cause adjacent training rows to share future returns.  
   - *Mitigation:* Enforce strict 20-trading-day embargo purge between train and validation folds (`PurgedWalkForwardSplit`) and hard-drop the trailing 20 rows of every training fold.  
2. **Risk R-02 (Hostinger KVM2 OOM Crash):** 8 GB RAM exhausted by concurrent IB Gateway \+ Pandas copies \+ Matplotlib figure buffers.  
   - *Mitigation:* Enforce `float32` schemas, constrain `XGBClassifier(n_jobs=2, tree_method='hist')`, process indicators per-ticker via generator streams, and invoke `plt.close(fig)` \+ `gc.collect()` every 10 charts.  
3. **Risk R-03 (IBKR API Pacing Violation \- Error 162):** Requesting 600+ historical series simultaneously triggers a 10-minute socket lock.  
   - *Mitigation:* Implement `asyncio.Semaphore(1)` with a 1.5-second delay between historical requests (\~15 minutes for cold 5-year backfill; \<90 seconds for daily 5-day incremental delta updates).