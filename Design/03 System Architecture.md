# 02\_SYSTEM\_ARCHITECTURE.md — Data Schemas, Mathematical Definitions & System Design

## 1\. Directory Structure (`/opt/quant-screener/`)

/opt/quant-screener/

├── AGENTS.md                        \# Primary opencode agent orchestration & guardrails

├── config/

│   ├── settings.yaml                \# Hyperparameters, lookbacks, IBKR port (4001/4002), paths

│   ├── watchlist\_300\_usd.csv        \# Columns: symbol,sec\_type,exchange,primary\_exchange,currency

│   ├── watchlist\_300\_cad.csv        \# Columns: symbol,sec\_type,exchange,primary\_exchange,currency

│   └── holdings.csv                 \# Columns: symbol,currency,exchange,shares,avg\_cost,entry\_date

├── data/

│   ├── raw\_ohlcv/                   \# Partitioned Parquet: market={USD|CAD}/symbol={SYM}.parquet

│   ├── features/                    \# Point-in-time feature matrices (float32 Parquet)

│   └── metadata\_catalog.json        \# Statistical analysis output: MI scores, VIF, stationarity flags

├── models/

│   ├── usd/                         \# Calibrated XGBoost models \+ SHAP explainers (Y1..Y4)

│   └── cad/                         \# Calibrated XGBoost models \+ SHAP explainers (Y1..Y4)

├── src/

│   ├── ibkr\_ingest.py

│   ├── feature\_engine.py

│   ├── targets.py

│   ├── stat\_metadata.py

│   ├── xgb\_trainer.py

│   ├── model\_qa.py

│   └── pdf\_compiler.py

├── tests/

│   └── test\_leakage.py              \# Mandatory pytest gate checking t vs t+1 invariance

└── reports/                         \# Output Markdown diagnostics and daily PDF tearsheets

---

## 2\. Mathematical Target Formulations (`src/targets.py`)

Let \$C\_t, H\_t, L\_t\$ denote Adjusted Close, High, and Low at day \$t\$, and let \$\\text{ATR}\_{20,t}\$ be the 20-day Wilder Average True Range known at the close of day \$t\$. All targets evaluate purely over the forward horizon \$\[t+1, t+k\]\$ and are stored in a separate table (`targets.parquet`) joined **only** during purged training folds:

1. **`Y_15d_High` (15-Day Peak / Exhaustion Inflection — Sell/Trim Signal):**  
   - Binary \$1\$ if the stock rallies to a significant local peak within the next 15 trading days and subsequently stalls/reverses, OR if \$C\_t\$ is already at an extreme local top that fails to advance:  
   - Specifically: \$\\max\_{i \\in \[1, 15\]} H\_{t+i} \\ge C\_t \+ 2.0 \\times \\text{ATR}*{20,t}\$ AND \$C*{t+15} \\le \\max\_{i \\in \[1, 15\]} H\_{t+i} \- 1.25 \\times \\text{ATR}*{20,t}\$, OR \$\\max*{i \\in \[1, 15\]} H\_{t+i} \\le C\_t \+ 0.35 \\times \\text{ATR}*{20,t}\$ while \$C*{t+15} \\le C\_t \- 1.5 \\times \\text{ATR}\_{20,t}\$ (immediate top rejection).  
2. **`Y_15d_Low` (15-Day Bottom / Capitulation Inflection — Buy Signal):**  
   - Binary \$1\$ if \$C\_t\$ represents a durable 15-day floor or flushes into a sharp V-bottom reversal over \$\[t+1, t+15\]\$:  
   - Specifically: \$\\min\_{i \\in \[1, 15\]} L\_{t+i} \\ge C\_t \- 0.5 \\times \\text{ATR}*{20,t}\$ AND \$\\max*{i \\in \[1, 15\]} C\_{t+i} \\ge C\_t \+ 2.0 \\times \\text{ATR}*{20,t}\$ (immediate floor bounce), OR \$\\min*{i \\in \[1, 10\]} L\_{t+i} \\le C\_t \- 1.5 \\times \\text{ATR}*{20,t}\$ followed by \$C*{t+15} \\ge \\min\_{i \\in \[1, 10\]} L\_{t+i} \+ 2.0 \\times \\text{ATR}\_{20,t}\$ (spring reversal).  
3. **`Y_20d_Up` (20-Day Sustained Upward Trend — Buy Signal):**  
   - Fit ordinary least squares (OLS) linear regression on log prices \$\\ln(C\_{t+1 \\dots t+20})\$ over \$i \\in \[1, 20\]\$.  
   - Binary \$1\$ if forward 20-day cumulative return \$(C\_{t+20} \- C\_t) \\ge \+2.0 \\times \\text{ATR}\_{20,t}\$ AND OLS slope \$\\beta\_1 \> 0\$ with coefficient of determination \$R^2 \\ge 0.60\$.  
4. **`Y_20d_Down` (20-Day Sustained Downward Trend — Exit/Short Signal):**  
   - Binary \$1\$ if forward 20-day cumulative return \$(C\_{t+20} \- C\_t) \\le \-2.0 \\times \\text{ATR}\_{20,t}\$ AND OLS slope \$\\beta\_1 \< 0\$ with \$R^2 \\ge 0.60\$.

---

## 3\. Multi-Horizon Technical Indicator Matrix (`src/feature_engine.py`)

Computed strictly on trailing windows \$W \\in {5, 10, 20, 50, 100}\$ using data \$\\le t\$:

- **Classic Indicators (Normalized for Price-Level Stationarity):**  
  - `RSI_W`: Wilder's Relative Strength Index (\$W \\in {5, 14, 21}\$) \+ 5-day RSI slope.  
  - `BB_PctB_W` & `BB_Width_W`: Bollinger Band \$%B \= (C\_t \- \\text{Lower}) / (\\text{Upper} \- \\text{Lower})\$ and Bandwidth normalized by \$\\text{SMA}\_W\$.  
  - `MACD_Norm`: \$(12, 26, 9)\$ MACD line and histogram divided by \$\\text{ATR}\_{20,t}\$.  
  - `ADX_W` & `DI_Spread_W`: Trend strength and \$(\\text{+DI}\_W \- \\text{-DI}\_W)\$.  
  - `ATR_Pct_W`: \$\\text{ATR}\_{W,t} / C\_t\$ volatility regime ratio.  
  - `OBV_ZScore_W`: Rolling Z-score of On-Balance Volume slope over window \$W\$.  
- **Frontier Quantitative Indicators:**  
  - `Hurst_W` (\$W \\in {20, 50, 100}\$): Rescaled Range (\$R/S\$) Hurst Exponent (\$H \< 0.45\$ flags mean-reverting regime; \$H \> 0.55\$ flags persistent trending regime).  
  - `FracDiff_Close` (\$d \= 0.40\$): Fixed-window fractionally differentiated log close price.  
  - `Shannon_Entropy_W` (\$W \\in {10, 20}\$): Shannon information entropy of discretized daily return bins.  
  - `Kalman_Spread_ATR`: Distance between \$C\_t\$ and a 1D Kalman Filter state estimate, normalized by \$\\text{ATR}\_{20,t}\$.  
  - `KAMA_Efficiency_W`: Kaufman Adaptive Moving Average Efficiency Ratio.  
  - `VWAP_ZScore_W` & `Amihud_Illiquidity_W`: Volume-weighted price anchor deviation and institutional absorption proxy.  
  - `YangZhang_Vol_W`: Open-High-Low-Close overnight-adjusted realized volatility estimator.

---

## 4\. Point-in-Time Anti-Leakage Architecture

1. **Strict Causal Windowing:** Every feature transformation at row \$t\$ is tested by `tests/test_leakage.py`: the test mutates \$O, H, L, C, V\$ at \$t+1 \\dots t+20\$ with random noise and asserts `np.allclose(X_original.loc[:t], X_mutated.loc[:t], equal_nan=True)`.  
2. **Cross-Sectional Standardization Only Within Date \$t\$:** When `stat_metadata.py` computes cross-sectional percentile ranks (`cs_rank_pct`) across the 300 USD or 300 CAD universe, it groups exclusively by `date == t` (never across the full time-series index).