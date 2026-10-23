"""Sprint 1 / Gate 1 verifier for the synced VPS environment.

Responsibilities:
  1. Validate schema + row counts of `config/*.csv`.
  2. Scan `data/raw_ohlcv/market={USD,CAD}/*.parquet`:
       - float32 dtype check on numeric OHLCV columns,
       - min/max date continuity,
       - CB-02: < 125 bars -> quarantine,
       - CB-01: single-day return > +100% or < -50% -> quarantine,
       - `data/sync_manifest.json` presence/consistency,
       - CB-03: median max_date lagging market by > 3 trading days -> HARD HALT
         (real synced data only; skipped in dry run).
  3. Pre-sync dry run: if `data/raw_ohlcv/` is empty, generate a deterministic
     300-bar synthetic OHLCV fixture (5 USD + 5 CAD) under `data/raw_ohlcv_test/`
     and audit that instead, so the pipeline mechanics are verifiable immediately.
  4. Run `pytest tests/test_leakage.py` (baseline anti-leakage harness).
  5. Write `reports/sprint1_ingestion_audit.md` and update `state/PIPELINE_STATE.json`.

Exit code 0 = Gate 1 verified; 1 = CB-03 hard halt (data stale).
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

from src.state_manager import init_dirs, log_telemetry, quarantine_ticker, update_state

BASE_DIR = Path(__file__).resolve().parents[1]
CONFIG_DIR = BASE_DIR / "config"
RAW_DIR = BASE_DIR / "data" / "raw_ohlcv"
FIXTURE_DIR = BASE_DIR / "data" / "raw_ohlcv_test"
MANIFEST_PATH = BASE_DIR / "data" / "sync_manifest.json"
REPORT_PATH = BASE_DIR / "reports" / "sprint1_ingestion_audit.md"

WATCHLIST_COLUMNS = ["symbol", "sec_type", "exchange", "primary_exchange", "currency"]
HOLDINGS_COLUMNS = [
    "symbol", "sec_type", "exchange", "primary_exchange", "currency",
    "shares", "avg_cost", "entry_date",
]
OHLCV_COLUMNS = ["date", "open", "high", "low", "close", "volume"]
FLOAT_COLUMNS = ["open", "high", "low", "close", "volume"]

USD_FIXTURE = ["AAPL", "MSFT", "NVDA", "AMZN", "JPM"]
CAD_FIXTURE = ["RY", "TD", "SHOP", "ENB", "CNQ"]
N_BARS = 300
CB02_MIN_BARS = 125
CB03_MAX_LAG_TRADING_DAYS = 3


# --------------------------------------------------------------------------- #
# CSV validation
# --------------------------------------------------------------------------- #
def validate_csv(path: Path, required_columns: list[str]) -> dict:
    if not path.exists():
        return {"rows": 0, "cols_ok": False, "dups": 0, "missing": True}
    df = pd.read_csv(path)
    cols_ok = all(c in df.columns for c in required_columns)
    dups = int(df["symbol"].duplicated().sum()) if "symbol" in df.columns else 0
    return {
        "rows": int(len(df)),
        "cols_ok": bool(cols_ok),
        "dups": dups,
        "missing": False,
    }


# --------------------------------------------------------------------------- #
# Synthetic fixture (deterministic per-symbol seed)
# --------------------------------------------------------------------------- #
def synthetic_ohlcv(symbol: str, n_bars: int = N_BARS, end: str | None = None) -> pd.DataFrame:
    end = end or dt.date.today().isoformat()
    seed = int(hashlib.sha256(symbol.encode()).hexdigest()[:8], 16) % (2**32)
    rng = np.random.default_rng(seed)

    dates = pd.bdate_range(end=pd.Timestamp(end), periods=n_bars)
    base = 20.0 + (seed % 500)  # varied price level per symbol
    rets = rng.normal(0.0005, 0.015, size=n_bars)
    close = base * np.exp(np.cumsum(rets))
    open_ = close * (1 + rng.normal(0.0, 0.003, size=n_bars))
    high = np.maximum(open_, close) * (1 + rng.uniform(0.001, 0.01, size=n_bars))
    low = np.minimum(open_, close) * (1 - rng.uniform(0.001, 0.01, size=n_bars))
    volume = rng.integers(100_000, 5_000_000, size=n_bars)

    return pd.DataFrame(
        {
            "date": dates,
            "open": open_.astype("float32"),
            "high": high.astype("float32"),
            "low": low.astype("float32"),
            "close": close.astype("float32"),
            "volume": volume.astype("float32"),
        }
    )


def generate_fixture() -> int:
    count = 0
    for market, tickers in (("USD", USD_FIXTURE), ("CAD", CAD_FIXTURE)):
        out_dir = FIXTURE_DIR / f"market={market}"
        out_dir.mkdir(parents=True, exist_ok=True)
        for sym in tickers:
            df = synthetic_ohlcv(sym)
            df.to_parquet(out_dir / f"symbol={sym}.parquet", index=False)
            count += 1
    return count


# --------------------------------------------------------------------------- #
# Parquet audit
# --------------------------------------------------------------------------- #
def audit_parquet_dir(root: Path) -> tuple[list[dict], list[pd.Timestamp]]:
    files = sorted(root.rglob("*.parquet"))
    rows: list[dict] = []
    max_dates: list[pd.Timestamp] = []

    for p in files:
        symbol = p.stem.split("=", 1)[-1]
        market = p.parent.name.split("=", 1)[-1]
        entry = {"symbol": symbol, "market": market, "path": str(p.relative_to(BASE_DIR))}

        try:
            df = pd.read_parquet(p)
        except Exception as exc:
            entry["status"] = "READ_ERROR"
            entry["reason"] = f"PARQUET_READ_ERROR: {exc}"
            quarantine_ticker(symbol, market, "EP-01", entry["reason"])
            rows.append(entry)
            continue

        entry["rows"] = int(len(df))
        if not df.empty:
            df = df.sort_values("date").reset_index(drop=True)
            entry["min_date"] = str(pd.to_datetime(df["date"]).min().date())
            entry["max_date"] = str(pd.to_datetime(df["date"]).max().date())
            max_dates.append(pd.to_datetime(df["date"]).max())

        # float32 dtype check on numeric OHLCV columns
        non_f32 = [c for c in FLOAT_COLUMNS if c in df.columns and df[c].dtype != np.float32]

        # CB-01: single-day return > +100% or < -50%
        spike = False
        if len(df) >= 2:
            ret = df["close"].astype("float64").pct_change()
            spike = bool(((ret > 1.0) | (ret < -0.5)).any())

        reasons: list[str] = []
        if len(df) < CB02_MIN_BARS:  # CB-02
            reasons.append("INSUFFICIENT_LOOKBACK_FOR_HURST100")
        if spike:  # CB-01
            reasons.append("UNVERIFIED_CORP_ACTION")
        if non_f32:
            reasons.append("NON_FLOAT32:" + ",".join(non_f32))

        if reasons:
            entry["status"] = "QUARANTINED"
            entry["reason"] = "; ".join(reasons)
            for r in reasons:
                quarantine_ticker(symbol, market, "EP-01", r)
        else:
            entry["status"] = "OK"

        rows.append(entry)

    return rows, max_dates


def check_manifest() -> dict:
    if not MANIFEST_PATH.exists():
        return {"present": False, "note": "data/sync_manifest.json not found (expected after M1 Mac rsync)."}
    try:
        m = json.loads(MANIFEST_PATH.read_text())
        return {
            "present": True,
            "synced_at_utc": m.get("synced_at_utc"),
            "total_parquet_files": m.get("total_parquet_files"),
        }
    except Exception as exc:
        return {"present": True, "error": f"unreadable manifest: {exc}"}


def cb03_check(max_dates: list[pd.Timestamp]) -> dict:
    """CB-03: hard halt if median max_date lags market close by > 3 trading days."""
    if not max_dates:
        return {"status": "SKIP", "note": "no parquet data to evaluate."}
    median_max = sorted(max_dates)[len(max_dates) // 2]
    today = pd.Timestamp(dt.date.today())
    lag = max(0, len(pd.bdate_range(median_max, today)) - 1)
    if lag > CB03_MAX_LAG_TRADING_DAYS:
        return {
            "status": "HALT",
            "median_max_date": str(median_max.date()),
            "lag_trading_days": lag,
            "note": f"median max_date lags market by {lag} trading days (> {CB03_MAX_LAG_TRADING_DAYS}). Re-run ibkr_ingest.py + sync on M1 Mac.",
        }
    return {"status": "OK", "median_max_date": str(median_max.date()), "lag_trading_days": lag}


def run_leakage_tests() -> dict:
    t0 = time.time()
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_leakage.py", "-q"],
        cwd=BASE_DIR,
        capture_output=True,
        text=True,
    )
    elapsed = time.time() - t0
    return {
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
        "duration_sec": round(elapsed, 2),
    }


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> int:
    t_start = time.time()
    init_dirs()

    lines: list[str] = []

    def emit(text: str = "") -> None:
        lines.append(text)

    emit("# Sprint 1 — Ingestion Audit (Gate 1)")
    emit()
    emit(f"- Generated (UTC): {dt.datetime.now(dt.timezone.utc).isoformat()}")
    emit(f"- Base directory: `{BASE_DIR}`")
    emit()

    # --- 1. CSV validation -------------------------------------------------- #
    emit("## 1. Config CSV validation")
    emit()
    emit("| File | Rows | Required columns | Duplicate symbols |")
    emit("| :--- | ---: | :---: | ---: |")
    csv_specs = [
        ("config/watchlist_300_usd.csv", WATCHLIST_COLUMNS),
        ("config/watchlist_300_cad.csv", WATCHLIST_COLUMNS),
        ("config/holdings.csv", HOLDINGS_COLUMNS),
    ]
    csv_summary = {}
    for rel, cols in csv_specs:
        res = validate_csv(CONFIG_DIR / Path(rel).name, cols)
        csv_summary[rel] = res
        flag = "YES" if res["cols_ok"] else "NO"
        emit(f"| `{rel}` | {res['rows']} | {flag} | {res['dups']} |")
    emit()

    # --- 2. Parquet scan ---------------------------------------------------- #
    emit("## 2. OHLCV Parquet audit")
    emit()
    usd_files = list((RAW_DIR / "market=USD").glob("*.parquet"))
    cad_files = list((RAW_DIR / "market=CAD").glob("*.parquet"))
    real_count = len(usd_files) + len(cad_files)

    dry_run = real_count == 0
    if dry_run:
        emit(
            f"`data/raw_ohlcv/` is empty (pre-sync dry run). Generated a deterministic "
            f"{N_BARS}-bar synthetic fixture ({len(USD_FIXTURE)} USD + {len(CAD_FIXTURE)} CAD) "
            f"under `data/raw_ohlcv_test/`."
        )
        emit()
        n = generate_fixture()
        emit(f"- Synthetic fixture written: **{n}** Parquet files.")
        emit()
        audit_root = FIXTURE_DIR
        emit("### 2.1 Dry-run fixture audit")
    else:
        audit_root = RAW_DIR
        emit(
            f"Real synced data detected: **{len(usd_files)}** USD + **{len(cad_files)}** CAD "
            f"Parquet files under `data/raw_ohlcv/`."
        )
        emit()
        emit("### 2.1 Synced data audit")

    emit()
    audit_rows, max_dates = audit_parquet_dir(audit_root)

    emit("| Symbol | Market | Rows | Min date | Max date | Status | Reason |")
    emit("| :--- | :---: | ---: | :---: | :---: | :---: | :--- |")
    for r in audit_rows:
        emit(
            f"| {r['symbol']} | {r['market']} | {r.get('rows', '-')} "
            f"| {r.get('min_date', '-')} | {r.get('max_date', '-')} "
            f"| {r['status']} | {r.get('reason', '')} |"
        )
    emit()

    df_audit = pd.DataFrame(audit_rows)
    if not df_audit.empty:
        ok = int((df_audit["status"] == "OK").sum())
        quarantined = int((df_audit["status"] == "QUARANTINED").sum())
        read_err = int((df_audit["status"] == "READ_ERROR").sum())
        cb01 = sum(1 for r in audit_rows if "UNVERIFIED_CORP_ACTION" in (r.get("reason") or ""))
        cb02 = sum(1 for r in audit_rows if "INSUFFICIENT_LOOKBACK_FOR_HURST100" in (r.get("reason") or ""))
    else:
        ok = quarantined = read_err = cb01 = cb02 = 0

    emit("### 2.2 Summary")
    emit()
    emit(f"- Total files audited: **{len(audit_rows)}**")
    emit(f"- OK: **{ok}** | Quarantined: **{quarantined}** | Read errors: **{read_err}**")
    emit(f"- CB-01 (corporate-action spike) quarantines: **{cb01}**")
    emit(f"- CB-02 (insufficient lookback) quarantines: **{cb02}**")
    emit()

    # --- 3. Manifest + CB-03 ------------------------------------------------ #
    emit("## 3. Sync manifest & freshness")
    emit()
    manifest = check_manifest()
    if manifest["present"]:
        emit(
            f"- `data/sync_manifest.json` present — synced_at: `{manifest.get('synced_at_utc')}`, "
            f"files: `{manifest.get('total_parquet_files')}`."
        )
    else:
        emit(f"- {manifest['note']}")
    emit()

    cb03 = None
    if not dry_run:
        cb03 = cb03_check(max_dates)
        emit("### 3.1 Circuit breaker CB-03 (staleness)")
        emit()
        if cb03["status"] == "OK":
            emit(
                f"- Median max_date: `{cb03['median_max_date']}` "
                f"(lag {cb03['lag_trading_days']} trading day(s)) — **PASS**."
            )
        elif cb03["status"] == "HALT":
            emit(f"- **HALT** — {cb03['note']}")
        else:
            emit(f"- {cb03['note']}")
        emit()

    # --- 4. Leakage harness -------------------------------------------------- #
    emit("## 4. Baseline anti-leakage harness (`pytest tests/test_leakage.py`)")
    emit()
    leakage = run_leakage_tests()
    leak_pass = leakage["returncode"] == 0
    emit(f"- Result: **{'PASS' if leak_pass else 'FAIL'}** (exit code {leakage['returncode']}, "
         f"{leakage['duration_sec']}s)")
    emit()
    emit("```")
    emit(leakage["stdout"] or "(no stdout)")
    if leakage["stderr"]:
        emit(leakage["stderr"])
    emit("```")
    emit()

    # --- write report -------------------------------------------------------- #
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines) + "\n")

    # --- state + telemetry --------------------------------------------------- #
    update_state("EP-01", "gate_1", {
        "dry_run": dry_run,
        "parquet_files_audited": len(audit_rows),
        "ok": ok,
        "quarantined": quarantined,
        "cb01": cb01,
        "cb02": cb02,
        "leakage_harness_passed": leak_pass,
    })
    state = json.loads((BASE_DIR / "state" / "PIPELINE_STATE.json").read_text())
    state["gates_approved"]["gate_1"] = leak_pass and (cb03 is None or cb03["status"] != "HALT")
    (BASE_DIR / "state" / "PIPELINE_STATE.json").write_text(json.dumps(state, indent=2))

    log_telemetry(
        "verify_synced_data",
        "SUCCESS" if (leak_pass and (cb03 is None or cb03["status"] != "HALT")) else "BLOCKED",
        round(time.time() - t_start, 2),
        {"dry_run": dry_run, "files": len(audit_rows)},
    )

    print(f"[verify_synced_data] report written -> {REPORT_PATH}")
    print(f"[verify_synced_data] files={len(audit_rows)} ok={ok} quarantined={quarantined} "
          f"cb01={cb01} cb02={cb02} leakage={'PASS' if leak_pass else 'FAIL'}")

    if cb03 is not None and cb03["status"] == "HALT":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
