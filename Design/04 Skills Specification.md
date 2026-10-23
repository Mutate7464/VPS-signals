# 04\_SKILLS\_SPECIFICATION.md — Deterministic Agent Skills & CLI Tool Contracts

Each skill corresponds to an idempotent Python CLI module invocable by `opencode` with standardized JSON/Markdown status outputs.

---

## Skill 1: `skill_ibkr_ohlcv_sync`

- **Entrypoint:** `python3 -m src.ibkr_ingest --market {USD|CAD|HOLDINGS} --lookback "5 Y"`  
- **Input Contract:**  
  - CSV files in `config/` with schema: `symbol,sec_type,exchange,primary_exchange,currency` (e.g., `AAPL,STK,SMART,NASDAQ,USD` or `RY,STK,SMART,TSE,CAD`).  
- **Processing Logic:**  
  1. Connect via `ib_async.IB()` with `clientId=101`.  
  2. Qualify contracts via `ib.qualifyContractsAsync()`.  
  3. Check existing `data/raw_ohlcv/market={MKT}/symbol={SYM}.parquet`. If present, fetch only missing delta days (`durationStr="{N} D"`); otherwise pull `"5 Y"` of `1 day` bars (`whatToShow="ADJUSTED_LAST"`, `useRTH=True`).  
  4. Enforce rate limiter: 1 request per 1.5 seconds; exponential backoff on IBKR Error `162`.  
- **Output Contract:** Partitioned Parquet files (`date, open, high, low, close, volume, average, barCount`) \+ `data/audit_ingestion_summary.csv`.

---

## Skill 2: `skill_feature_and_target_builder`

- **Entrypoint:** `python3 -m src.feature_engine --market {USD|CAD} --validate-leakage`  
- **Input Contract:** Raw OHLCV Parquet directory.  
- **Processing Logic:**  
  1. Compute all classic and frontier indicators over windows `[5, 10, 20, 50, 100]`.  
  2. Compute 1-day, 3-day, and 5-day first differences (velocity) and second differences (acceleration) of core indicators (`RSI_14`, `Hurst_20`, `BB_PctB_20`, `Kalman_Spread_ATR`).  
  3. Run `pytest tests/test_leakage.py` before writing output. Halt immediately with exit code `1` if any future data dependency is detected.  
- **Output Contract:** `data/features/features_{USD|CAD}.parquet` (strictly `float32`) and `data/features/targets_{USD|CAD}.parquet` (`int8`).

---

## Skill 3: `skill_statistical_metadata_profiler`

- **Entrypoint:** `python3 -m src.stat_metadata --market {USD|CAD} --vif-threshold 5.0 --min-mi-percentile 30`  
- **Input Contract:** `features_{USD|CAD}.parquet` and `targets_{USD|CAD}.parquet` (restricted exclusively to the initial training split to avoid feature-selection look-ahead bias).  
- **Processing Logic:**  
  1. **Stationarity Check:** Run Augmented Dickey-Fuller (`statsmodels.tsa.stattools.adfuller`) on a random sample of 50 tickers per feature; flag any feature where median \$p \> 0.05\$ for automatic rolling Z-score transformation: \$Z\_{i,t} \= (X\_{i,t} \- \\mu\_{i,t-60:t}) / \\sigma\_{i,t-60:t}\$.  
  2. **Cross-Sectional Ranking:** Append cross-sectional percentile ranks (`_cs_pct`) grouped strictly by `date` across the 300 tickers.  
  3. **Target Relevance & Redundancy Pruning:** Calculate Mutual Information (`MI`) per target \$Y\_1 \\dots Y\_4\$ and iteratively drop features with Variance Inflation Factor \$\\text{VIF} \> 5.0\$ (retaining the member of any correlated pair with higher average MI).  
- **Output Contract:** `data/metadata_catalog_{USD|CAD}.json` containing the surviving feature whitelist per target, stationarity transform parameters, and MI rankings.

---

## Skill 4: `skill_purged_xgb_trainer`

- **Entrypoint:** `python3 -m src.xgb_trainer --market {USD|CAD} --embargo 20 --n-splits 5`  
- **Input Contract:** Feature Parquet, Target Parquet, and `metadata_catalog_{USD|CAD}.json`.  
- **Processing Logic:**  
  1. Construct 5-fold Purged Walk-Forward splits: for each split \$(Train\_k, Val\_k)\$, drop the final 20 trading days of \$Train\_k\$ so no forward 15d/20d window in \$Train\_k\$ overlaps with the start of \$Val\_k\$.  
  2. Calculate dynamic `scale_pos_weight = count(Y == 0) / count(Y == 1)` inside each training fold to handle class imbalance (\~8–15% positive rate for regime inflections).  
  3. Fit `XGBClassifier(n_estimators=400, max_depth=4, learning_rate=0.03, subsample=0.8, colsample_bytree=0.7, min_child_weight=20, reg_alpha=1.0, reg_lambda=5.0, tree_method="hist", n_jobs=2, early_stopping_rounds=30)`.  
  4. Fit `CalibratedClassifierCV(method="isotonic")` on the purged validation fold so predicted probabilities reflect true empirical hit rates.  
  5. Compute `shap.TreeExplainer` values for the latest inference date \$T\$ to identify the \#1 local driving indicator for every ticker.  
- **Output Contract:** Saved model artifacts in `models/{usd|cad}/`, inference predictions `data/predictions_{USD|CAD}_latest.parquet`, and `reports/sprint4_model_qa.md`.

---

## Skill 5: `skill_pdf_tearsheet_compiler`

- **Entrypoint:** `python3 -m src.pdf_compiler --market {USD|CAD} --top-n 30`  
- **Input Contract:** Latest predictions Parquet, raw OHLCV Parquet (trailing 120 trading days for plotting), and `config/holdings.csv`.  
- **Processing Logic:**  
  1. **Section 1 — Portfolio Defense (`holdings.csv` sorted by `max(P_15d_High, P_20d_Down)` descending):** Displays exit urgency table \+ full annotated charts for all active holdings.  
  2. **Section 2 — Buy-Side Bottom Inflections (Top 30 tickers from 300-ticker watchlist sorted by `P_15d_Low` descending).**  
  3. **Section 3 — Buy-Side Momentum Trends (Top 30 tickers from 300-ticker watchlist sorted by `P_20d_Up` descending).**  
  4. **4-Panel Chart Specification per Ticker (Rendered via `mplfinance` \+ `ReportLab`):**  
     - **Panel 1 (Main, 55% height):** 120-day OHLC candlesticks \+ 20-day Bollinger Bands (`2.0 std` shaded band) \+ algorithmic peak/trough triangle markers (`scipy.signal.argrelextrema` strictly on trailing window) \+ 20-day OLS trend channel overlay.  
     - **Panel 2 (Volume, 15% height):** Volume bars colored by up/down close with 20-day SMA volume line.  
     - **Panel 3 (Classic Oscillator, 15% height):** 14-day RSI with 30/70 reference lines.  
     - **Panel 4 (Top Model Indicator, 15% height):** Dynamically plots the \#1 highest-SHAP technical indicator for that specific stock and prediction with its 60-day rolling mean and \$\\pm 2\\sigma\$ threshold bands, plus a text callout box listing all 4 model probabilities (`P_15d_Low`, `P_20d_Up`, `P_15d_High`, `P_20d_Down`) and top 3 SHAP feature contributions.  
- **Output Contract:** `reports/screener_USD_YYYYMMDD.pdf` and `reports/screener_CAD_YYYYMMDD.pdf`.