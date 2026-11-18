# QUANT_SCREENER_MASTER_SUMMARY.md — Complete Executive Blueprint, Architecture, Runbook & Model Routing

## 1. Executive Summary & Strategic Intention
- **Objective:** End-to-end, leak-free quantitative stock screener and portfolio exit monitor across **300 USD equities (`SMART/NASDAQ/NYSE`)**, **300 CAD equities (`SMART/TSE`)**, and **active portfolio positions (`holdings.csv`)**[cite: 6, 7].
- **Output Deliverables (`reports/screener_{USD|CAD}_YYYYMMDD.pdf`):**
  1. **Section 1 — Portfolio Defense (`holdings.csv`):** Ranked descending by `Exit_Urgency = max(P(Y_15d_High), P(Y_20d_Down))` to flag immediate top exhaustion or trend breakdown exits[cite: 2, 6, 7].
  2. **Section 2 — Buy-Side Bottom Inflections (`watchlist_300`):** Top 30 USD and Top 30 CAD equities ranked by calibrated `P(Y_15d_Low)`[cite: 2, 6, 7].
  3. **Section 3 — Buy-Side Upward Momentum (`watchlist_300`):** Top 30 USD and Top 30 CAD equities ranked by calibrated `P(Y_20d_Up)`[cite: 2, 6, 7].
  4. **4-Panel Visual Tearsheet per Selected Ticker:**
     - **Panel 1 (55%):** 120-day OHLC Candlesticks + 20d Bollinger Bands (`2.0 std`) + algorithmic peak/trough markers + 20d OLS trend channel[cite: 2, 3].
     - **Panel 2 (15%):** Volume bars colored by close direction + 20d SMA volume[cite: 2].
     - **Panel 3 (15%):** 14-day Wilder RSI with 30/70 levels[cite: 2].
     - **Panel 4 (15%):** #1 highest-SHAP model indicator for that ticker with 60d mean / `±2 std` bands + callout box of all 4 probabilities[cite: 2].

---

## 2. Split-Node Hardware Topology & Guardrails
- **Node A — 2021 M1 MacBook Air (Local Ingestion & Control Plane):**
  - Runs IB Gateway / TWS (`127.0.0.1:4001` or `4002`) locally on macOS[cite: 1, 3, 7].
  - Executes `python3 -m src.ibkr_ingest --market {HOLDINGS|USD|CAD}` with 1.5s async pacing (`ADJUSTED_LAST`, 5-year cold lookback, incremental delta updates)[cite: 2, 3, 7].
  - Runs `sync_to_vps.sh` to generate `data/sync_manifest.json` (SHA-256 hashes + row counts) and atomically `rsync --delay-updates` Parquet files to the VPS.
- **Node B — Hostinger KVM2 Linux VPS (`2 vCPU / 8 GB RAM` Compute Backend):**
  - Accessed via VS Code Remote-SSH from M1 Mac; all `opencode` sessions run inside `tmux new-session -A -s quant`[cite: 1, 7].
  - **Hard Resource Limits:** 4 GB `/swapfile` (`swappiness=10`), VS Code Pylance indexing disabled on `data/` and `.venv/`, `n_jobs=2` hardcoded across `xgboost` and `scikit-learn`, all features cast to `float32`, and `plt.close('all')` + `gc.collect()` executed every 10 charts[cite: 1, 3, 6].

---

## 3. Mathematical Targets & Multi-Horizon Feature Matrix
- **Point-in-Time Targets (`src/targets.py`, evaluated strictly over `[t+1, t+k]`):**
  - `Y_15d_High`: `max(H_{t+1..t+15}) >= C_t + 2.0 * ATR_20` followed by `>= 1.25 * ATR_20` pullback by `t+15`, OR immediate rejection (`max(H) <= C_t + 0.35 * ATR_20` and `C_{t+15} <= C_t - 1.5 * ATR_20`)[cite: 5].
  - `Y_15d_Low`: Durable floor (`min(L_{t+1..t+15}) >= C_t - 0.5 * ATR_20` and `max(C) >= C_t + 2.0 * ATR_20`) OR V-bottom spring reversal (`min(L_{t+1..t+10}) <= C_t - 1.5 * ATR_20` and `C_{t+15} >= min(L) + 2.0 * ATR_20`)[cite: 5].
  - `Y_20d_Up`: `(C_{t+20} - C_t) >= +2.0 * ATR_20` AND 20-day log-price OLS regression slope `> 0` with `R^2 >= 0.60`[cite: 3, 5].
  - `Y_20d_Down`: `(C_{t+20} - C_t) <= -2.0 * ATR_20` AND 20-day log-price OLS regression slope `< 0` with `R^2 >= 0.60`[cite: 3, 5].
- **Indicators (`src/feature_engine.py`, windows `[5, 10, 20, 50, 100]`, strictly `<= t`):**
  - *Classic:* `RSI` (`5, 14, 21`) + 5d slope, `BB_PctB` & `BB_Width`, `ATR_20`-normalized `MACD`, `ADX` & `DI_Spread`, `ATR_Pct`, `OBV_ZScore`[cite: 3, 5].
  - *Frontier:* `Hurst_W` (`20, 50, 100`), `FracDiff_Close` (`d=0.40`), `Shannon_Entropy_W` (`10, 20`), `Kalman_Spread_ATR`, `KAMA_Efficiency_W`, `VWAP_ZScore_W`, `Amihud_Illiquidity_W`, `YangZhang_Vol_W`[cite: 3, 5].
- **Statistical Metadata Layer (`src/stat_metadata.py`):**
  - Augmented Dickey-Fuller (`ADF`) test (`p > 0.05` triggers 60d rolling Z-score transform), date-grouped cross-sectional percentile ranks (`_cs_pct`), Mutual Information (`MI`) scoring per target, and iterative collinearity pruning (`VIF < 5.0`)[cite: 1, 2, 6, 7].

---

## 4. 5-Sprint Agile Execution Plan, Circuit Breakers & Model Routing

| Sprint / Epic | Core Script(s) | HITL Stop Gate & Verification Artifact | Recommended `opencode` Model | Circuit Breakers & Guardrails |
| :--- | :--- | :--- | :--- | :--- |
| **Sprint 1 (`EP-01`)** | `ibkr_ingest.py` (Mac)<br>`verify_synced_data.py` (VPS) | **Gate 1:** Inspect `reports/sprint1_ingestion_audit.md` & `sync_manifest.json`[cite: 1, 7]. | `deepseek/deepseek-v4-pro` *or* `google/gemini-3.8-flash` | **CB-01:** Quarantine daily jumps `> +100%` or `< -50%` to `dead_letter_tickers.csv`.<br>**CB-03:** Halt if median `max_date` lags market by `> 3` days. |
| **Sprint 2 (`EP-02`)** | `targets.py`<br>`feature_engine.py`<br>`tests/test_leakage.py` | **Gate 2:** Pass `pytest tests/test_leakage.py` (+500% future spike invariance) & review `sprint2_feature_summary.md`[cite: 2, 3, 4, 7]. | `deepseek/deepseek-v4-pro` (Escalate to `openai/gpt-6.1-sol` after 2 fails) | **CB-02:** Quarantine tickers with `< 125` bars.<br>**RAM Check:** Ensure `rss_memory_mb < 2,500 MB` via `float32` enforcement. |
| **Sprint 3 (`EP-03`)** | `stat_metadata.py` | **Gate 3:** Approve ~25–35 surviving features in `data/metadata_catalog_{USD|CAD}.json`[cite: 2, 6, 7]. | `x-ai/grok-4.6` *or* `deepseek/deepseek-v4-pro` | Enforce `groupby('date')` on cross-sectional ranks; compute `MI` and `VIF < 5.0` strictly on training split[cite: 2, 5, 7]. |
| **Sprint 4 (`EP-04`)** | `xgb_trainer.py`<br>`model_qa.py` | **Gate 4:** Inspect `reports/sprint4_model_qa.md` (`Precision@30 >= 1.5x lift`, `Brier > 0.05`, `IC > 0.04`)[cite: 1, 2, 4, 7]. | **`openai/gpt-6.1-sol`** (or `gpt-5.6-sol` / `claude-opus-5.5`) | **20-Day Embargo** between train/val folds[cite: 1, 2, 3, 4, 6].<br>**CB-04:** Fallback `isotonic -> sigmoid` if val positives `< 25`.<br>**CB-05:** Hard halt if Placebo Shuffled `ROC-AUC > 0.52`[cite: 4]. |
| **Sprint 5 (`EP-05`)** | `pdf_compiler.py` | **Gate 5:** Smoke-test `--top-n 2` first, then run `--top-n 30` and pull PDFs to M1 Mac[cite: 1, 2, 7]. | `deepseek/deepseek-v4-pro` *or* `google/gemini-3.8-flash` | **CB-06:** Batch 10 charts at a time with `plt.close('all')` + `gc.collect()` to cap VPS RAM `< 4.2 GB`[cite: 1, 3, 6, 7]. |

---

## 5. Daily Operational Checklist (M1 Mac -> KVM2 VPS -> PDF Tearsheet)
1. **M1 Mac (Ingest):** Start IB Gateway -> Run `python3 -m src.ibkr_ingest --market {HOLDINGS|USD|CAD}`[cite: 2, 3, 7].
2. **M1 Mac (Sync):** Run `./sync_to_vps.sh` (verifies SHA-256 manifest and runs atomic `rsync --delay-updates`).
3. **VPS via VS Code Remote-SSH (`tmux attach -t quant`):**
   - Launch `opencode` -> Run Gate 1 through Gate 5 prompts from `00_MASTER_HANDOVER_AND_WORKFLOW.md`[cite: 7].
   - Confirm `docs/SESSION_HANDOVER.md` and `state/PIPELINE_STATE.json` update at each gate.
4. **M1 Mac (Review):** Run `rsync -avz root@<VPS_IP>:/opt/quant-screener/reports/*.pdf ~/quant-screener-local/reports/ && open ~/quant-screener-local/reports/`[cite: 7].

# 07_OPERATIONAL_RUNBOOK_AND_RECOVERY.md — VS Code Remote-SSH Hardening, Atomic Sync, State Checkpointing & Circuit Breakers

## 1. Hostinger KVM2 VPS & VS Code Remote-SSH Hardening (`2 vCPU / 8 GB RAM`)

### 1.1 One-Time Linux 4 GB Swap File Provisioning (OOM Circuit Breaker)
Run once on the Hostinger KVM2 VPS to prevent Linux Kernel `SIGKILL (Exit 137)` when `vscode-server`, `opencode`, and `XGBClassifier(tree_method='hist', n_jobs=2)` run concurrently:
```bash
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
sudo sysctl vm.swappiness=10
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf

# 1.2 VS Code Remote-SSH Memory Throttle (/opt/quant-screener/.vscode/settings.json)

## Prevents Pylance and file watchers from indexing 600+ Parquet files and exhausting VPS RAM:

JSON
{
  "files.watcherExclude": {
    "**/.git/objects/**": true,
    "**/.venv/**": true,
    "**/data/**": true,
    "**/models/**": true,
    "**/reports/**": true,
    "**/logs/**": true
  },
  "search.exclude": {
    "**/.venv": true,
    "**/data": true,
    "**/models": true,
    "**/reports": true
  },
  "python.analysis.indexing": false,
  "python.analysis.autoSearchPaths": false,
  "python.analysis.diagnosticMode": "openFilesOnly"
}

2. Atomic M1 Mac-to-VPS Sync Script (~/quant-screener-local/sync_to_vps.sh)
Run on your M1 MacBook Air after IB Gateway ingestion completes. Generates a SHA-256 manifest and uses --delay-updates so the VPS never reads half-transferred Parquet files:

Bash
#!/usr/bin/env bash
set -euo pipefail

LOCAL_DIR="$HOME/quant-screener-local"
VPS_HOST="root@<YOUR_VPS_IP>"
REMOTE_DIR="/opt/quant-screener"

echo "[1/4] Generating SHA-256 sync manifest on M1 Mac..."
python3 - << 'EOF'
import hashlib, json, datetime as dt
from pathlib import Path
import pandas as pd

base = Path.home() / "quant-screener-local"
raw_dir = base / "data" / "raw_ohlcv"
parquets = list(raw_dir.rglob("*.parquet"))

max_dates = []
for p in parquets[:50]:  # Sample check for speed
    df = pd.read_parquet(p, columns=["date"])
    if not df.empty:
        max_dates.append(str(df["date"].max()))

manifest = {
    "synced_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    "total_parquet_files": len(parquets),
    "sample_median_max_date": sorted(max_dates)[len(max_dates)//2] if max_dates else None,
    "config_hashes": {}
}
for cfg_file in ["watchlist_300_usd.csv", "watchlist_300_cad.csv", "holdings.csv", "settings.yaml"]:
    p = base / "config" / cfg_file
    if p.exists():
        manifest["config_hashes"][cfg_file] = hashlib.sha256(p.read_bytes()).hexdigest()

(base / "data" / "sync_manifest.json").write_text(json.dumps(manifest, indent=2))
print(f"Manifest written: {len(parquets)} Parquet files ready.")
EOF

echo "[2/4] Syncing config/*.csv and settings.yaml to VPS..."
rsync -avz --delay-updates "$LOCAL_DIR/config/" "$VPS_HOST:$REMOTE_DIR/config/"

echo "[3/4] Atomic syncing data/raw_ohlcv/ and sync_manifest.json to VPS..."
rsync -avz --delay-updates --exclude='*.tmp' "$LOCAL_DIR/data/" "$VPS_HOST:$REMOTE_DIR/data/"

echo "[4/4] Sync complete. Ready for Gate 1 verification on VPS."

3. Idempotent State Ledger, Telemetry & Quarantine (src/state_manager.py)
Used by all skills (EP-01 through EP-05) to log RAM usage, checkpoint completed tickers, and quarantine broken tickers into data/dead_letter_tickers.csv without crashing the batch:

Python
import csv
import datetime as dt
import json
import os
import time
from pathlib import Path
import psutil

BASE_DIR = Path("/opt/quant-screener")
STATE_FILE = BASE_DIR / "state" / "PIPELINE_STATE.json"
DEAD_LETTER_FILE = BASE_DIR / "data" / "dead_letter_tickers.csv"
LOG_DIR = BASE_DIR / "logs"


def init_dirs():
    (BASE_DIR / "state").mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    if not STATE_FILE.exists():
        default_state = {
            "current_sprint": "EP-01",
            "gates_approved": {"gate_1": False, "gate_2": False, "gate_3": False, "gate_4": False, "gate_5": False},
            "checkpoints": {},
            "last_updated_utc": None,
            "last_error": None,
        }
        STATE_FILE.write_text(json.dumps(default_state, indent=2))


def update_state(sprint: str, key: str, value) -> None:
    init_dirs()
    state = json.loads(STATE_FILE.read_text())
    state["current_sprint"] = sprint
    state["checkpoints"][key] = value
    state["last_updated_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
    STATE_FILE.write_text(json.dumps(state, indent=2))


def log_telemetry(step_name: str, status: str, duration_sec: float, extra: dict = None) -> None:
    init_dirs()
    proc = psutil.Process(os.getpid())
    rss_mb = round(proc.memory_info().rss / (1024 * 1024), 2)
    payload = {
        "timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "step": step_name,
        "status": status,
        "duration_sec": round(duration_sec, 2),
        "rss_memory_mb": rss_mb,
        "extra": extra or {},
    }
    log_file = LOG_DIR / f"pipeline_run_{dt.date.today().strftime('%Y%m%d')}.jsonl"
    with open(log_file, "a") as f:
        f.write(json.dumps(payload) + "\n")


def quarantine_ticker(symbol: str, market: str, sprint: str, reason: str) -> None:
    """Logs broken/insufficient-history tickers to dead_letter_tickers.csv and continues batch."""
    DEAD_LETTER_FILE.parent.mkdir(parents=True, exist_ok=True)
    file_exists = DEAD_LETTER_FILE.exists()
    with open(DEAD_LETTER_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp_utc", "symbol", "market", "sprint", "reason"])
        writer.writerow([dt.datetime.now(dt.timezone.utc).isoformat(), symbol, market, sprint, reason])

4. Quantitative Circuit Breakers (Mandatory Halt vs. Auto-Fallback Conditions)CodeCondition TriggerAction TypeAutomated Resolution / GuardrailCB-01Single-day bar return R_t > +100% or < -50% (Unadjusted Split/Spike)Quarantine TickerLog symbol to data/dead_letter_tickers.csv (UNVERIFIED_CORP_ACTION) and exclude from cross-sectional percentile ranking so it does not distort ATR/Z-scores.CB-02Ticker history < 125 trading daysQuarantine TickerLog symbol to data/dead_letter_tickers.csv (INSUFFICIENT_LOOKBACK_FOR_HURST100) and skip cleanly.CB-03Synced Parquet median max_date lags expected market close by > 3 trading daysHard Halt (Gate 1)Abort verify_synced_data.py with exit code 1; prompt human to re-run ibkr_ingest.py and sync_to_vps.sh on M1 Mac.CB-04Validation fold positive target count < 25 rows (Positive Rate < 2%)Auto-Fallback (Sprint 4)Switch CalibratedClassifierCV from method="isotonic" to parametric method="sigmoid" (Platt scaling) to prevent step-function overfitting.CB-05Placebo Shuffled-Target Permutation Test ROC-AUC > 0.52Hard Halt (Gate 4)Delete model artifacts in models/, log CRITICAL_LEAKAGE_DETECTED, and block pdf_compiler.py execution.CB-06VPS RSS Memory > 6,800 MB during feature or PDF batchAuto-ThrottleForce immediate plt.close('all') + gc.collect() and reduce batch chunk size from 10 to 5.5. Rolling Agent Handover Template (docs/SESSION_HANDOVER.md)Instruct opencode to overwrite/update this file at the end of every Sprint Gate or before closing a session so any new agent session resumes with zero context loss:Markdown# SESSION_HANDOVER.md — OpenCode Live Context Ledger
- **Last Updated (UTC):** YYYY-MM-DD HH:MM:SS
- **Active Sprint & Gate Status:** [e.g., EP-03 Completed / Waiting for Human Sign-Off on Gate 3]
- **Latest Synced Market Date:** USD = YYYY-MM-DD (298 active, 2 quarantined) | CAD = YYYY-MM-DD (299 active, 1 quarantined)
- **Peak VPS Memory Observed:** [e.g., 3,420 MB RSS during EP-02]
- **Key Artifacts Generated This Session:**
  - `data/features/features_USD.parquet` (Passed `pytest tests/test_leakage.py`)
  - `data/metadata_catalog_USD.json` (31 features retained after `VIF < 5.0` pruning)
- **Active Anomalies / Quarantined Tickers:**
  - See `data/dead_letter_tickers.csv`
- **Exact Next Command / Prompt for Next Session:**
  - Run Sprint 4 (`python3 -m src.xgb_trainer --market USD --embargo 20 --n-splits 5`) after human approves `reports/sprint3_metadata_selection.md`.

* **Summary of Your Complete 8-Document Architecture Suite (`00` through `07`):**
  * **`00_MASTER_HANDOVER_AND_WORKFLOW.md`** — Executive summary, M1 Mac $\rightarrow$ KVM2 VPS split-node topology, and copy-paste prompts for all 5 Gates[cite: 7].
  * **`01_PROJECT_PLAN.md`** — PMP Charter, WBS, 5 Agile Sprints, Product Backlog (`EP-06` to `EP-08`), and Risk Register[cite: 6].
  * **`02_SYSTEM_ARCHITECTURE.md`** — Directory layout, exact mathematical definitions for `Y_15d_High`, `Y_15d_Low`, `Y_20d_Up`, `Y_20d_Down`, and classic/frontier indicators[cite: 5].
  * **`03_AGENTS.md` (`AGENTS.md`)** — `opencode` hardware guardrails (`n_jobs=2`, `float32`, batched GC) and 4 sub-agent role protocols[cite: 1].
  * **`04_SKILLS_SPECIFICATION.md`** — CLI contracts for all 5 Python modules[cite: 2].
  * **`05_MODEL_GOVERNANCE_AND_QA.md`** — Anti-leakage unit tests, Precision@30, Brier Skill Score, Placebo Permutation Test, and SHAP audits[cite: 4].
  * **`06_SPRINT1_AND_2_STARTER_CODE.md`** — Ready-to-run `settings.yaml`, CSV templates, `ibkr_ingest.py`, and `test_leakage.py`[cite: 3].
  * **`07_OPERATIONAL_RUNBOOK_AND_RECOVERY.md`** — VS Code Remote-SSH RAM throttling, 4 GB swap setup, atomic `sync_to_vps.sh`, `state_manager.py`, circuit breakers (`CB-01` to `CB-06`), and `SESSION_HANDOVER.md`.

Tier / Role in Your WorkflowModel NameAPI Pricing (Input / Output per 1M)Key Coding & Terminal BenchmarksBest Sprint Fit in Your Quant PipelineTier 1: Ultra-Value Workhorse (Default in opencode)DeepSeek V4-Pro / V4.1 Flash (via OpenRouter / DeepSeek API)$0.66 / $1.98 (Off-peak down to $0.60 output)74.5%–90.6% Terminal-Bench 2.1; strong NumPy/PyArrow/XGBoost fluencySprints 1, 2 & 5: Writing ibkr_ingest.py, verify_synced_data.py, standard feature_engine.py indicators, and mplfinance PDF boilerplate.   Tier 1B: Fast High-Context WorkhorseGemini 3.8 Flash$0.75 / $3.75 (1M context window)89.4% Terminal-Bench 2.1; 76.3 Coding Index; 57% SciCodeSprint 1 & 5: Reading all 8 architecture docs (00–07) in a single prompt without context truncation; debugging long traceback logs.Tier 2: Best Value Mid-Tier All-RounderGrok 4.6 or Claude Sonnet 5 / 5.5$2.00 / $6.00 (Grok) | $2.00 / $10.00 (Sonnet)69.9% CursorBench 3.2 (Grok); 82.25 BenchAlign (Sonnet 5.5)Sprint 2 & 3: Implementing frontier math (FracDiff_Close, Hurst_W, Kalman_Spread_ATR) and iterative VIF < 5.0 statistical pruning.   Tier 3: Precision Escalation ("Heavy Lifter")GPT-6.1 Sol / GPT-5.6 Sol or Claude Opus 5.5$4.00 / $20.00 ($0.20 cache read on Opus 5.5)89.9% SWE-bench Pro (Opus 5.5); 66.0% Terminal-Bench Hard (GPT Sol)

# QUANT_SCREENER_MASTER_SUMMARY.md — Complete Executive Blueprint, Architecture, Runbook & Model Routing

## 1. Executive Summary & Strategic Intention
- **Objective:** End-to-end, leak-free quantitative stock screener and portfolio exit monitor across **300 USD equities (`SMART/NASDAQ/NYSE`)**, **300 CAD equities (`SMART/TSE`)**, and **active portfolio positions (`holdings.csv`)**[cite: 6, 7].
- **Output Deliverables (`reports/screener_{USD|CAD}_YYYYMMDD.pdf`):**
  1. **Section 1 — Portfolio Defense (`holdings.csv`):** Ranked descending by `Exit_Urgency = max(P(Y_15d_High), P(Y_20d_Down))` to flag immediate top exhaustion or trend breakdown exits[cite: 2, 6, 7].
  2. **Section 2 — Buy-Side Bottom Inflections (`watchlist_300`):** Top 30 USD and Top 30 CAD equities ranked by calibrated `P(Y_15d_Low)`[cite: 2, 6, 7].
  3. **Section 3 — Buy-Side Upward Momentum (`watchlist_300`):** Top 30 USD and Top 30 CAD equities ranked by calibrated `P(Y_20d_Up)`[cite: 2, 6, 7].
  4. **4-Panel Visual Tearsheet per Selected Ticker:**
     - **Panel 1 (55%):** 120-day OHLC Candlesticks + 20d Bollinger Bands (`2.0 std`) + algorithmic peak/trough markers + 20d OLS trend channel[cite: 2, 3].
     - **Panel 2 (15%):** Volume bars colored by close direction + 20d SMA volume[cite: 2].
     - **Panel 3 (15%):** 14-day Wilder RSI with 30/70 levels[cite: 2].
     - **Panel 4 (15%):** #1 highest-SHAP model indicator for that ticker with 60d mean / `±2 std` bands + callout box of all 4 probabilities[cite: 2].

---

## 2. Split-Node Hardware Topology & Guardrails
- **Node A — 2021 M1 MacBook Air (Local Ingestion & Control Plane):**
  - Runs IB Gateway / TWS (`127.0.0.1:4001` or `4002`) locally on macOS[cite: 1, 3, 7].
  - Executes `python3 -m src.ibkr_ingest --market {HOLDINGS|USD|CAD}` with 1.5s async pacing (`ADJUSTED_LAST`, 5-year cold lookback, incremental delta updates)[cite: 2, 3, 7].
  - Runs `sync_to_vps.sh` to generate `data/sync_manifest.json` (SHA-256 hashes + row counts) and atomically `rsync --delay-updates` Parquet files to the VPS.
- **Node B — Hostinger KVM2 Linux VPS (`2 vCPU / 8 GB RAM` Compute Backend):**
  - Accessed via VS Code Remote-SSH from M1 Mac; all `opencode` sessions run inside `tmux new-session -A -s quant`[cite: 1, 7].
  - **Hard Resource Limits:** 4 GB `/swapfile` (`swappiness=10`), VS Code Pylance indexing disabled on `data/` and `.venv/`, `n_jobs=2` hardcoded across `xgboost` and `scikit-learn`, all features cast to `float32`, and `plt.close('all')` + `gc.collect()` executed every 10 charts[cite: 1, 3, 6].

---

## 3. Mathematical Targets & Multi-Horizon Feature Matrix
- **Point-in-Time Targets (`src/targets.py`, evaluated strictly over `[t+1, t+k]`):**
  - `Y_15d_High`: `max(H_{t+1..t+15}) >= C_t + 2.0 * ATR_20` followed by `>= 1.25 * ATR_20` pullback by `t+15`, OR immediate rejection (`max(H) <= C_t + 0.35 * ATR_20` and `C_{t+15} <= C_t - 1.5 * ATR_20`)[cite: 5].
  - `Y_15d_Low`: Durable floor (`min(L_{t+1..t+15}) >= C_t - 0.5 * ATR_20` and `max(C) >= C_t + 2.0 * ATR_20`) OR V-bottom spring reversal (`min(L_{t+1..t+10}) <= C_t - 1.5 * ATR_20` and `C_{t+15} >= min(L) + 2.0 * ATR_20`)[cite: 5].
  - `Y_20d_Up`: `(C_{t+20} - C_t) >= +2.0 * ATR_20` AND 20-day log-price OLS regression slope `> 0` with `R^2 >= 0.60`[cite: 3, 5].
  - `Y_20d_Down`: `(C_{t+20} - C_t) <= -2.0 * ATR_20` AND 20-day log-price OLS regression slope `< 0` with `R^2 >= 0.60`[cite: 3, 5].
- **Indicators (`src/feature_engine.py`, windows `[5, 10, 20, 50, 100]`, strictly `<= t`):**
  - *Classic:* `RSI` (`5, 14, 21`) + 5d slope, `BB_PctB` & `BB_Width`, `ATR_20`-normalized `MACD`, `ADX` & `DI_Spread`, `ATR_Pct`, `OBV_ZScore`[cite: 3, 5].
  - *Frontier:* `Hurst_W` (`20, 50, 100`), `FracDiff_Close` (`d=0.40`), `Shannon_Entropy_W` (`10, 20`), `Kalman_Spread_ATR`, `KAMA_Efficiency_W`, `VWAP_ZScore_W`, `Amihud_Illiquidity_W`, `YangZhang_Vol_W`[cite: 3, 5].
- **Statistical Metadata Layer (`src/stat_metadata.py`):**
  - Augmented Dickey-Fuller (`ADF`) test (`p > 0.05` triggers 60d rolling Z-score transform), date-grouped cross-sectional percentile ranks (`_cs_pct`), Mutual Information (`MI`) scoring per target, and iterative collinearity pruning (`VIF < 5.0`)[cite: 1, 2, 6, 7].

---

## 4. 5-Sprint Agile Execution Plan, Circuit Breakers & Model Routing

| Sprint / Epic | Core Script(s) | HITL Stop Gate & Verification Artifact | Recommended `opencode` Model | Circuit Breakers & Guardrails |
| :--- | :--- | :--- | :--- | :--- |
| **Sprint 1 (`EP-01`)** | `ibkr_ingest.py` (Mac)<br>`verify_synced_data.py` (VPS) | **Gate 1:** Inspect `reports/sprint1_ingestion_audit.md` & `sync_manifest.json`[cite: 1, 7]. | `deepseek/deepseek-v4-pro` *or* `google/gemini-3.8-flash` | **CB-01:** Quarantine daily jumps `> +100%` or `< -50%` to `dead_letter_tickers.csv`.<br>**CB-03:** Halt if median `max_date` lags market by `> 3` days. |
| **Sprint 2 (`EP-02`)** | `targets.py`<br>`feature_engine.py`<br>`tests/test_leakage.py` | **Gate 2:** Pass `pytest tests/test_leakage.py` (+500% future spike invariance) & review `sprint2_feature_summary.md`[cite: 2, 3, 4, 7]. | `deepseek/deepseek-v4-pro` (Escalate to `openai/gpt-6.1-sol` after 2 fails) | **CB-02:** Quarantine tickers with `< 125` bars.<br>**RAM Check:** Ensure `rss_memory_mb < 2,500 MB` via `float32` enforcement. |
| **Sprint 3 (`EP-03`)** | `stat_metadata.py` | **Gate 3:** Approve ~25–35 surviving features in `data/metadata_catalog_{USD|CAD}.json`[cite: 2, 6, 7]. | `x-ai/grok-4.6` *or* `deepseek/deepseek-v4-pro` | Enforce `groupby('date')` on cross-sectional ranks; compute `MI` and `VIF < 5.0` strictly on training split[cite: 2, 5, 7]. |
| **Sprint 4 (`EP-04`)** | `xgb_trainer.py`<br>`model_qa.py` | **Gate 4:** Inspect `reports/sprint4_model_qa.md` (`Precision@30 >= 1.5x lift`, `Brier > 0.05`, `IC > 0.04`)[cite: 1, 2, 4, 7]. | **`openai/gpt-6.1-sol`** (or `gpt-5.6-sol` / `claude-opus-5.5`) | **20-Day Embargo** between train/val folds[cite: 1, 2, 3, 4, 6].<br>**CB-04:** Fallback `isotonic -> sigmoid` if val positives `< 25`.<br>**CB-05:** Hard halt if Placebo Shuffled `ROC-AUC > 0.52`[cite: 4]. |
| **Sprint 5 (`EP-05`)** | `pdf_compiler.py` | **Gate 5:** Smoke-test `--top-n 2` first, then run `--top-n 30` and pull PDFs to M1 Mac[cite: 1, 2, 7]. | `deepseek/deepseek-v4-pro` *or* `google/gemini-3.8-flash` | **CB-06:** Batch 10 charts at a time with `plt.close('all')` + `gc.collect()` to cap VPS RAM `< 4.2 GB`[cite: 1, 3, 6, 7]. |

---

## 5. Daily Operational Checklist (M1 Mac -> KVM2 VPS -> PDF Tearsheet)
1. **M1 Mac (Ingest):** Start IB Gateway -> Run `python3 -m src.ibkr_ingest --market {HOLDINGS|USD|CAD}`[cite: 2, 3, 7].
2. **M1 Mac (Sync):** Run `./sync_to_vps.sh` (verifies SHA-256 manifest and runs atomic `rsync --delay-updates`).
3. **VPS via VS Code Remote-SSH (`tmux attach -t quant`):**
   - Launch `opencode` -> Run Gate 1 through Gate 5 prompts from `00_MASTER_HANDOVER_AND_WORKFLOW.md`[cite: 7].
   - Confirm `docs/SESSION_HANDOVER.md` and `state/PIPELINE_STATE.json` update at each gate.
4. **M1 Mac (Review):** Run `rsync -avz root@<VPS_IP>:/opt/quant-screener/reports/*.pdf ~/quant-screener-local/reports/ && open ~/quant-screener-local/reports/`[cite: 7].