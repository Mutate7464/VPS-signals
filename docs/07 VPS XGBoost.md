Daily OHLCV equity training on a 2 vCPU / 8 GB KVM 2 requires Parquet storage with float32 downcasting, corporate-action ratio back-adjustment, and strict time-series cross-validation, while shutting down both Hermes Agent and OpenCode during training in favor of decoupled OS-level telemetry and structured crash logging yields an extra ~3.5 GB of clean RAM.

	•	OHLCV Storage & Memory Footprint Optimization
	◦	Columnar Format: Abandon CSV/SQLite for training ingestion; store data in Apache Parquet using zstd or snappy compression with Polars (scan_parquet) for lazy evaluation and predicate pushdown.
	◦	Precision Downcasting: Downcast all price/indicator columns from float64 to float32 and volume/categorical encodings to int32/uint16, cutting baseline memory consumption by 50% with zero impact on XGBoost split precision (since tree_method='hist' quantizes features into uint8 bins anyway).
	◦	Scale Expectation: Even 3,000 tickers × 20 years of daily data (~15M rows × 50 engineered indicators) occupies only ~3 GB in float32 RAM, meaning the dataset will fit in-memory if intermediate pandas copies are eliminated via xgb.QuantileDMatrix and gc.collect().
	•	Financial Data Engineering & Corporate Action Adjustment
	◦	Proportional Back-Adjustment: You cannot feed raw Close alongside Adjusted Close into technical indicators; compute the adjustment factor $R_t = \frac{\text{Adj Close}_t}{\text{Close}_t}$ and multiply $O_t, H_t, L_t$ by $R_t$, while dividing Volume by the cumulative split factor so historical candlestick proportions (e.g., ATR, Bollinger Band width) remain uncorrupted across stock splits and dividends.
	◦	Stationarity Enforcement: Tree models cannot extrapolate outside historical feature bounds; never pass raw price levels ($P_t$) as features. Normalize all features into stationary ratios—such as log returns $\ln(P_t/P_{t-n})$, percentage distance from moving averages, Z-scores, or ATR-normalized distances.
	◦	Leakage Prevention: Standard $k$-fold cross-validation causes severe look-ahead bias on financial time series; implement Purged and Embargoed Walk-Forward Validation with an embargo period matching your forward return target horizon (e.g., 5-day embargo for a 5-day forward return label).
	•	Decoupled Telemetry & Post-Mortem Troubleshooting (OpenCode Shutdown)
	◦	Service Teardown Wrapper: Wrap the training execution in a bash script that runs systemctl stop hermes opencode pre-run, freeing up 2.0–3.5 GB of RAM and eliminating vCPU contention, then restarts OpenCode upon completion or trap failure (trap 'systemctl start opencode' EXIT).
	◦	Kernel OOM & Resource Auditing: Because the Linux OOM killer sends SIGKILL (-9) instantly without letting Python throw a MemoryError, log kernel ring buffer events via dmesg -T | grep -i -E 'oom|killed' and run a lightweight background monitor (vmstat -t 5 >> /var/log/xgb_mem.log) during training.
	◦	Structured Python Crash Dumps: Configure Python's native faulthandler module (to capture C-level segfaults inside libxgboost.so) and sys.excepthook to write structured JSON/text tracebacks and memory watermarks (resource.getrusage) to a dedicated log file that OpenCode can immediately ingest and analyze once restarted.
Markdown





# System Architecture & Optimization Design: XGBoost Equity Pipeline on KVM 2

## 1. Hardware & Resource Allocation Envelope
* **Host Spec:** Hostinger KVM 2 (2 vCPU, 8 GB RAM, 100 GB NVMe SSD)
* **Target Mode:** Batch Training Isolation (Hermes Agent & OpenCode stopped during heavy training runs)

| System Component | Active Idle Mode (RAM) | Training Isolation Mode (RAM) | Mitigation / Control Mechanism |
| :--- | :--- | :--- | :--- |
| **Linux OS & Kernel** | 0.8 GB | 0.8 GB | Base system overhead |
| **Hermes Agent** | 1.0 – 1.5 GB | **0.0 GB (Stopped)** | `systemctl stop hermes` pre-job |
| **OpenCode Server** | 1.0 – 2.0 GB | **0.0 GB (Stopped)** | `systemctl stop opencode` pre-job; restart on `EXIT` trap |
| **Data Ingestion Buffer** | N/A | 1.5 – 2.0 GB | Polars lazy frames + `float32` Parquet |
| **XGBoost `QuantileDMatrix`** | N/A | 2.5 – 3.5 GB | `tree_method='hist'`, `max_bin=128`, `nthread=2` |
| **Safety Margin / Headroom** | ~4.0 GB | **1.2 – 2.2 GB** | Protected by 8 GB NVMe Swap file (`swappiness=10`) |

---

## 2. OHLCV Data Engineering & Pipeline Architecture

### 2.1 Corporate Action Back-Adjustment
Raw OHLC combined with Adjusted Close breaks intraday volatility metrics (e.g., ATR, True Range, candlestick wicks) on split/dividend dates. Apply proportional adjustment prior to feature engineering:
* `adj_factor = adj_close / close`
* `adj_open = open * adj_factor`
* `adj_high = high * adj_factor`
* `adj_low = low * adj_factor`
* `adj_volume = volume / split_factor` (or utilize Dollar Volume: `close * volume`)

### 2.2 Feature Stationarity Rules
Decision trees partition feature space via orthogonal splits and cannot extrapolate trends outside the training range.
* **Prohibited:** Raw `adj_close`, raw `SMA_50`, raw `Volume`, raw `ATR`.
* **Required (Stationary):**
  * Relative Moving Averages: `(adj_close / SMA_50) - 1.0`
  * Volatility-Normalized Returns: `(adj_close - adj_close.shift(n)) / ATR_14`
  * Volume Shocks: `volume / volume_rolling_mean_20`
  * Bounded Oscillators: RSI, Bollinger Band `%B`, Band Width `(Upper - Lower) / Mid`.

### 2.3 Memory-Safe Matrix Construction
Avoid keeping both the DataFrame and the `DMatrix` in RAM simultaneously:
1. Compute features per ticker or sector chunk using **Polars** and write directly to partitioned `.parquet` files on the NVMe disk with `Float32` types.
2. Construct `xgb.QuantileDMatrix` directly from a custom `xgb.DataIter` reading Parquet chunks, or load only the feature columns, instantiate `QuantileDMatrix`, and immediately execute `del df; gc.collect()`.

### 2.4 Validation Topology
* **Purged Walk-Forward Split:** Train on expanding or sliding historical windows `[t_0, t_1]`, purge overlapping forward return labels at boundary `t_1 + embargo_days`, and validate on `[t_1 + embargo_days, t_2]`.
* **Cross-Sectional Target Ranking:** Target cross-sectional excess return (e.g., 5-day or 20-day forward return minus equal-weighted universe mean, or `rank:pairwise` / `reg:squarederror` on cross-sectional Z-scored returns) to neutralize broad market beta.

---

## 3. Headless Execution & Telemetry Architecture (OpenCode Offline)

### 3.1 Execution Wrapper (`run_training.sh`)
Automates daemon shutdown, memory telemetry, OOM protection, and guaranteed OpenCode recovery for post-run debugging:

```bash
#!/usr/bin/env bash
set -uo pipefail

LOG_DIR="/var/log/xgb_pipeline"
mkdir -p "$LOG_DIR"
RUN_ID=$(date +"%Y%m%d_%H%M%S")
RUN_LOG="$LOG_DIR/train_${RUN_ID}.log"
MEM_LOG="$LOG_DIR/mem_${RUN_ID}.csv"

# Guarantee services restart even if script is killed or fails
cleanup() {
    kill "$VMSTAT_PID" 2>/dev/null || true
    dmesg -T | grep -i -E 'oom|killed|out of memory' | tail -n 20 >> "$RUN_LOG"
    sudo systemctl start opencode
}
trap cleanup EXIT

echo "[INFO] Stopping Hermes and OpenCode to free RAM..." | tee -a "$RUN_LOG"
sudo systemctl stop hermes opencode || true
sync && echo 3 | sudo tee /proc/sys/vm/drop_caches > /dev/null

# Start lightweight background RAM/Swap telemetry (1-second overhead is negligible)
vmstat -t -n 5 > "$MEM_LOG" &
VMSTAT_PID=$!

# Run training with OOM score adjustment (+500 ensures kernel kills Python, not sshd)
echo "[INFO] Launching XGBoost pipeline..." | tee -a "$RUN_LOG"
choom -n 500 -p $$ 2>/dev/null || true
nice -n 10 python3 -X faulthandler train_model.py >> "$RUN_LOG" 2>&1
EXIT_CODE=$?

echo "[INFO] Training finished with exit code: $EXIT_CODE" | tee -a "$RUN_LOG"
3.2 Python Telemetry & Crash Hook (train_model.py)
Captures peak RSS memory, XGBoost evaluation metrics, and C-level segmentation faults so OpenCode can parse a single summary file upon restart:

Python




import faulthandler
import gc
import json
import logging
import resource
import sys
import traceback

faulthandler.enable()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

def log_memory(stage: str):
    rss_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
    logging.info(f"[MEM_WATERMARK] Stage: {stage} | Peak RSS: {rss_mb:.2f} MB")

def handle_exception(exc_type, exc_value, exc_traceback):
    rss_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
    crash_report = {
        "status": "CRASH",
        "peak_rss_mb": round(rss_mb, 2),
        "error_type": exc_type.__name__,
        "error_message": str(exc_value),
        "traceback": traceback.format_tb(exc_traceback),
    }
    with open("/var/log/xgb_pipeline/latest_crash.json", "w") as f:
        json.dump(crash_report, f, indent=2)
    sys.__excepthook__(exc_type, exc_value, exc_traceback)

sys.excepthook = handle_exception
4. OpenCode Troubleshooting Workflow
	1	When run_training.sh finishes or crashes, trap cleanup EXIT automatically restarts the OpenCode daemon.
	2	Connect via VS Code / OpenCode and point the agent to /var/log/xgb_pipeline/latest_crash.json, train_<RUN_ID>.log, and mem_<RUN_ID>.csv.
	3	If EXIT_CODE=137 (SIGKILL), inspect the appended dmesg tail at the bottom of train_<RUN_ID>.log and reduce max_bin (e.g., from 128 to 64) or transition to chunked xgb.DataIter loading.

