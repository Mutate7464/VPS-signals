**Architecting this dual-market 600-ticker quantitative screening pipeline requires decomposing the system into five decoupled, Agile-gated epics: Data Ingestion, Multi-Timeframe Feature Engineering, Statistical Metadata Filtering, Leak-Free XGBoost Modeling, and Automated PDF Reporting. Structuring the Markdown design suite around strict human-in-the-loop (HITL) verification gates ensures complete elimination of look-ahead bias while establishing modular agent skills that execute deterministically.**

* **Inference 1: Decoupling the pipeline into PMP/Agile-aligned Markdown specifications (`PLAN.md`, `AGENT.md`, `SKILLS.md`, `EVALUATION.md`) prevents context drift and enables deterministic agent execution with human auditability.**
* **Scope & Wants (Functional Requirements):** Ingest daily OHLCV data for the top 300 USD and top 300 CAD equities via the Interactive Brokers (IBKR) API; compute classic and frontier technical indicators across multiple lookback horizons; execute statistical analysis to construct a distilled metadata feed; train strict point-in-time XGBoost models to predict four regimes (15-day high, 15-day low, 20-day upward trend, 20-day downward trend); and generate an automated tearsheet PDF showcasing the top 50 USD and top 50 CAD selections with annotated candlestick charts, Bollinger Bands, RSI, and the top-performing model indicator.
* **Non-Functional & Learning Needs:** Enforce zero future data leakage (strictly lagged features and walk-forward validation), build an evaluation harness for model diagnostics (SHAP feature importance, precision-at-$K$, out-of-sample calibration), and pause execution at defined Sprint Review gates so you can inspect intermediate artifacts and validate the quantitative logic before advancing.
* **Proposed Markdown Deliverable Blueprint (To be generated after your confirmation):**
* `01_PROJECT_PLAN.md`: PMP Project Charter, Work Breakdown Structure (WBS), 5 Agile Epics, Sprint Backlog, and Human-in-the-Loop (HITL) Definition of Done (DoD) gates.
* `02_SYSTEM_ARCHITECTURE.md`: Data schemas (Parquet/SQLite), IBKR API pacing engine (`ib_async`), feature matrix design, and strict point-in-time anti-leakage boundary rules.
* `03_AGENT_ORCHESTRATION.md`: System prompts, sub-agent personas (Data Engineer, Quant Researcher, ML Engineer, Reporting Analyst), and state handoff protocols.
* `04_SKILLS_SPECIFICATION.md`: Modular, callable Python tool definitions (`ibkr_ohlcv_fetcher`, `indicator_engine`, `stat_metadata_profiler`, `xgb_purged_trainer`, `pdf_chart_compiler`) with strict input/output contracts.
* `05_MODEL_GOVERNANCE_AND_QA.md`: Purged walk-forward cross-validation design, Brier score / Precision@50 metrics, and automated leak-detection unit tests.




* **Inference 2: Ingesting 600 equities via the IBKR API requires asynchronous pacing management and standardized exchange routing to prevent socket disconnects and survivorship distortion.**
* **Contract Routing & Pacing:** Pulling 3 to 5 years of daily adjusted OHLCV (`TRADES` or `ADJUSTED_LAST`) for 600 tickers via `ib_async` against TWS or IB Gateway must respect IBKR's historical data throttling rules (maximum 60 requests per 10-minute window for identical bar types, or ~10–15 seconds per batch with async backoff).
* **Dual-Market Partitioning:** The 300 USD universe routes via `SMART/USD` (mapping to S&P 500 / liquid NASDAQ constituents) and the 300 CAD universe routes via `SMART/CAD` on `TSE` (mapping to S&P/TSX Composite plus liquid mid-caps). Data is persisted locally in partitioned Apache Parquet files to decouple daily incremental updates from heavy historical backfills.


* **Inference 3: Combining classic and frontier technical indicators with a statistical metadata layer resolves multicollinearity and non-stationarity before tree-based gradient boosting.**
* **Classic & Frontier Feature Matrix:** Classic indicators (RSI, Bollinger Bands `%B` and Bandwidth, ATR-normalized MACD, OBV, ADX) will be paired with frontier quantitative indicators (Hurst Exponent for mean-reversion vs. momentum regime detection, Shannon Entropy for price noise, Volume-Weighted Average Price [VWAP] Z-scores, Fractional Differentiation for stationarity preservation, and KAMA/Kalman Filter slopes) computed across 5, 10, 20, 50, and 100-day windows.
* **Statistical Metadata Feed:** Raw price levels violate stationarity across a 600-stock cross-section. The statistical analysis layer transforms indicators into cross-sectional percentile ranks, rolling Z-scores, Mutual Information (MI) target scores, and Variance Inflation Factor (VIF) collinearity flags—feeding the XGBoost model a clean, stationary metadata feature set alongside raw normalized indicators.


* **Inference 4: Defining the four prediction targets requires explicit mathematical formulations and Purged Walk-Forward Cross-Validation to eliminate overlapping label leakage.**
* **Target Formulation ($Y_1 \dots Y_4$):** Because a 15-day or 20-day forward window creates serial correlation between consecutive daily rows ($t$ and $t+1$ share 14 to 19 days of future price action), standard $k$-fold splitting leaks future regime state into the training set. The pipeline must enforce an **embargo period of 20 trading days** between train and validation folds.
* **Ranking the Top 50 per Market:** Four distinct `XGBClassifier` models (or a unified `MultiOutputClassifier` predicting calibrated probabilities via Platt/Isotonic scaling) will output $P(\text{15d High})$, $P(\text{15d Low})$, $P(\text{20d Up Trend})$, and $P(\text{20d Down Trend})$. A composite conviction score ranks the 300 USD and 300 CAD tickers independently to isolate the top 50 per currency.


* **Inference 5: Automated PDF generation of 100 multi-panel financial charts requires vector-optimized rendering and dynamic SHAP-driven subplot injection.**
* **Dynamic Indicator Selection:** For each selected ticker, the reporting engine extracts the global or local (SHAP) #1 highest-contributing feature from the winning XGBoost prediction and plots it in a dedicated panel alongside the OHLCV candlesticks, 20-day Bollinger Bands, and 14-day RSI—automatically annotating algorithmic swing peaks, troughs, and 20-day trend channels using `mplfinance` and `ReportLab` / `WeasyPrint`.


* **Strategic Clarifications & Sensitivities (Please confirm or adjust before we generate the Markdown files):**
* **1. Mathematical Target Definitions:** How would you like to strictly define the four forward labels at day $t$?
* *Proposed Default:* **15d High/Low:** Binary classification where $1$ indicates that the current close $C_t$ is within $X\%$ of the forward 15-day maximum/minimum (i.e., identifying an immediate local bottom/top inflection), *OR* that price breaks above/below the trailing 20-day high/low within the next 15 days. **20d Up/Down Trend:** Forward 20-day log return exceeds $+1.5 \times \text{ATR}_{20}$ (Up) or falls below $-1.5 \times \text{ATR}_{20}$ (Down) with a positive/negative linear regression slope $R^2 > 0.60$. Which formulation matches your trading thesis?


* **2. Top 300 Ticker Universe Source:** Should the ingestion module dynamically scrape/pull index constituents (e.g., S&P 500 top 300 by market cap/dollar volume for USD; S&P/TSX Composite + TSX SmallCap top 300 by dollar volume for CAD), or will you supply a static master CSV watchlist formatted for IBKR (`Symbol, SecType, Exchange, Currency`)?
* **3. Top 50 Ranking Mix:** Should the final 50 USD and 50 CAD selections in the PDF be split evenly across the four signals (e.g., top 12–13 tickers per category: Long Inflection, Short Inflection, Bull Trend, Bear Trend), or ranked purely by highest aggregate model probability regardless of direction?
* **4. Execution Environment & Agent Tooling:** Are you deploying these Markdown specs into a specific agent framework (e.g., local Claude Code / Cursor / Antigravity IDE / Hermes Agent workflows) on your workstation or Linux VPS, so I can format the `AGENT.md` and `SKILLS.md` frontmatter and directory paths to match your exact runtime?



*Assumptions: Local TWS or headless IB Gateway is active with US and Canadian (TSX) market data subscriptions (or delayed/EOD historical permissions); pipeline executes in Python 3.11+ utilizing `ib_async`, `pandas-ta` / `ta-lib`, `xgboost`, `scikit-learn`, `shap`, and `mplfinance`; models are trained on EOD daily bars with a 5-year trailing lookback.*