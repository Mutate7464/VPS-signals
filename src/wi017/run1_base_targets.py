"""WI-017 run 1: base targets over the full fib grid (USD), symbol-sequential.

Per window w in WI017_WINDOWS, per entry date t (close_t reference):
  peak_ret_w    = max(high[t+1..t+w]) / close_t - 1        (lookforward peak)
  bottom_ret_w   = min(low[t+1..t+w]) / close_t - 1        (lookforward bottom)
  touch_up10_w   = 1.0 if peak_ret_w >= +0.10 else 0.0
  touch_dn10_w   = 1.0 if bottom_ret_w <= -0.10 else 0.0
  stay5_w        = 1.0 if peak_ret_w <= +0.05 AND bottom_ret_w >= -0.05 else 0.0

Outputs (isolation — nothing outside reports/wi017/):
  reports/wi017/targets/<SYM>.parquet   per-date target columns (float32)
  reports/wi017/run1_base_rates.json    per-window base rates
  reports/wi017/run1_base_rates.md      human summary

Constraints honored: n_jobs irrelevant (sequential), float32 immediately,
one symbol in memory at a time, quarantined symbols skipped, no data copies.
Bad-data guard: non-positive close rows are dropped per existing repo wart
(HMMC/ICL non-positive closes, WI-010 finding).
"""
from __future__ import annotations

import glob
import json
import os
import sys
import time

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _REPO_ROOT)
from src.wi017 import MARKET, WI017_WINDOWS  # noqa: E402

RAW_GLOB = "data/raw_ohlcv/market=USD/*.parquet"
QUARANTINE_CSV = "data/dead_letter_tickers.csv"
OUT_DIR = "reports/wi017/targets"
SUMMARY_JSON = "reports/wi017/run1_base_rates.json"
SUMMARY_MD = "reports/wi017/run1_base_rates.md"


def quarantined_symbols() -> set[str]:
    q: set[str] = set()
    try:
        df = pd.read_csv(QUARANTINE_CSV)
        if "symbol" in df.columns:
            q = set(df["symbol"].astype(str))
    except OSError:
        pass
    return q


def targets_for_symbol(df: pd.DataFrame) -> pd.DataFrame:
    """Compute base-target columns for one symbol (float32 out)."""
    df = df.sort_values("date").reset_index(drop=True)
    close = df["close"].astype("float64")
    high = df["high"].astype("float64")
    low = df["low"].astype("float64")
    out = pd.DataFrame({"date": df["date"].values, "close": close.astype("float32").values})
    # forward window [t+1..t+w]: backward rolling over [t-w+1..t], then shift(-w)
    # so the value lands at t (standard forward-rolling idiom).
    for w in WI017_WINDOWS:
        hi = high.rolling(w, min_periods=w).max().shift(-w)
        lo = low.rolling(w, min_periods=w).min().shift(-w)
        peak = (hi / close - 1.0).astype("float32")
        bot = (lo / close - 1.0).astype("float32")
        out[f"peak_ret_{w}"] = peak.values
        out[f"bottom_ret_{w}"] = bot.values
        out[f"touch_up10_{w}"] = (peak >= 0.10).astype("float32").values
        out[f"touch_dn10_{w}"] = (bot <= -0.10).astype("float32").values
        out[f"stay5_{w}"] = ((peak <= 0.05) & (bot >= -0.05)).astype("float32").values
    return out


def main() -> int:
    t0 = time.time()
    os.makedirs(OUT_DIR, exist_ok=True)
    quar = quarantined_symbols()
    files = sorted(glob.glob(RAW_GLOB))
    per_window: dict[int, dict[str, float]] = {}
    n_symbols = 0
    skipped_quarantine = 0
    short_symbols: list[tuple[str, int]] = []
    bad_rows_total = 0
    for f in files:
        sym = os.path.basename(f).replace("symbol=", "").replace(".parquet", "")
        if sym in quar:
            skipped_quarantine += 1
            continue
        df = pq.read_table(f).to_pandas()
        df = df[df["close"] > 0]
        if len(df) < 5:
            continue
        if len(df) < max(WI017_WINDOWS):
            short_symbols.append((sym, len(df)))
        tgt = targets_for_symbol(df)
        pq.write_table(
            pa.Table.from_pandas(tgt, preserve_index=False),
            os.path.join(OUT_DIR, f"{sym}.parquet"),
        )
        n_symbols += 1
        # accumulate base rates: mean over non-NaN rows only
        for w in WI017_WINDOWS:
            acc = per_window.setdefault(
                w, {"n": 0.0, "up": 0.0, "dn": 0.0, "stay": 0.0, "peak_sum": 0.0, "bot_sum": 0.0}
            )
            m = tgt[f"touch_up10_{w}"].notna()
            acc["n"] += float(m.sum())
            acc["up"] += float(tgt.loc[m, f"touch_up10_{w}"].sum())
            acc["dn"] += float(tgt.loc[m, f"touch_dn10_{w}"].sum())
            acc["stay"] += float(tgt.loc[m, f"stay5_{w}"].sum())
            pm = tgt[f"peak_ret_{w}"].notna()
            acc["peak_sum"] += float(tgt.loc[pm, f"peak_ret_{w}"].sum())
            acc["bot_sum"] += float(tgt.loc[pm, f"bottom_ret_{w}"].sum())
    summary = {
        "market": MARKET,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "windows": list(WI017_WINDOWS),
        "symbols_written": n_symbols,
        "skipped_quarantined": skipped_quarantine,
        "short_history_symbols_lt_233": short_symbols,
        "barrier_defs": {
            "touch_up10": "max(high[t+1..t+w]) >= 1.10 * close_t",
            "touch_dn10": "min(low[t+1..t+w]) <= 0.90 * close_t",
            "stay5": "max(high) <= 1.05*close_t AND min(low) >= 0.95*close_t over [t+1..t+w]",
            "peak_ret/bottom_ret": "extreme forward return vs close_t (descriptive)",
        },
        "per_window": {
            str(w): {
                "n_rows": int(v["n"]),
                "base_rate_up10": round(v["up"] / v["n"], 6) if v["n"] else None,
                "base_rate_dn10": round(v["dn"] / v["n"], 6) if v["n"] else None,
                "base_rate_stay5": round(v["stay"] / v["n"], 6) if v["n"] else None,
                "mean_peak_ret": round(v["peak_sum"] / v["n"], 6) if v["n"] else None,
                "mean_bottom_ret": round(v["bot_sum"] / v["n"], 6) if v["n"] else None,
            }
            for w, v in per_window.items()
        },
    }
    with open(SUMMARY_JSON, "w") as fh:
        json.dump(summary, fh, indent=2)
    write_md(summary)
    print(f"DONE symbols={n_symbols} quarantined_skipped={skipped_quarantine} "
          f"elapsed={time.time() - t0:.0f}s")
    return 0


def write_md(s: dict) -> None:
    lines = [
        "# WI-017 run 1 — base targets, USD, full fib grid 3–233",
        "",
        f"Generated (UTC): {s['generated_utc']} · symbols written: {s['symbols_written']}"
        f" · quarantined skipped: {s['skipped_quarantined']}",
        "",
        "Definitions: " + "; ".join(f"`{k}` = {v}" for k, v in s["barrier_defs"].items()),
        "",
        "| window | rows | up10 base | dn10 base | stay5 base | mean peak ret | mean bottom ret |",
        "|---|---|---|---|---|---|---|",
    ]
    for w in s["windows"]:
        v = s["per_window"][str(w)]
        lines.append(
            f"| {w} | {v['n_rows']} | {v['base_rate_up10']} | {v['base_rate_dn10']} "
            f"| {v['base_rate_stay5']} | {v['mean_peak_ret']} | {v['mean_bottom_ret']} |"
        )
    short = s.get("short_history_symbols_lt_233") or []
    lines += [
        "",
        f"Symbols with < 233 rows (window-233 columns NaN for them): "
        f"{len(short)} — {', '.join(f'{sym}({n})' for sym, n in short[:10])}"
        + (" …" if len(short) > 10 else ""),
        "",
        "DOA screen: any window × barrier with base rate < 1% is flagged dead-on-arrival for",
        "modeling (kept descriptive). Edge-case targets queue last per admin amendment.",
    ]
    with open(SUMMARY_MD, "w") as fh:
        fh.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
