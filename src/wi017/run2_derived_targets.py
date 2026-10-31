"""WI-017 run 2: derived targets on top of run-1 base outputs (USD).

Per window w in WI017_WINDOWS, per entry date t (reference close_t):

  first_touch_{w}   +1.0 if +10% high-barrier is touched before -10% low-barrier
                    within [t+1..t+w]; -1.0 if -10% first; 0.0 if neither
                    touched in the window (WI-016-style triple-barrier verdict).
  days_to_up_{w}    trading days from t to the FIRST +10% touch (NaN if never)
  days_to_dn_{w}    trading days from t to the FIRST -10% touch (NaN if never)
  rung_{w}          peak_ret - bottom_ret over the window (bottom-to-peak amplitude)
  velocity_{w}      rung / |bars between peak day and bottom day| (%/day, >=1 day
                    denominator; NaN when window incomplete). Sign carried by
                    peak position vs bottom position: positive when peak comes
                    after the bottom (bottom-to-peak velocity per admin spec),
                    negative when the peak precedes the bottom.

Implementation: numpy sliding_window_view (strided views, no copies) per
symbol, sequential; float32 on output. Outputs:
  reports/wi017/derived/<SYM>.parquet
  reports/wi017/run2_summary.json / .md
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
OUT_DIR = "reports/wi017/derived"
SUMMARY_JSON = "reports/wi017/run2_summary.json"
SUMMARY_MD = "reports/wi017/run2_summary.md"


def quarantined_symbols() -> set[str]:
    try:
        df = pd.read_csv(QUARANTINE_CSV)
        return set(df["symbol"].astype(str)) if "symbol" in df.columns else set()
    except OSError:
        return set()


def derived_for_symbol(high: np.ndarray, low: np.ndarray, close: np.ndarray) -> pd.DataFrame:
    """Vectorized first-touch / velocity columns for one symbol."""
    from numpy.lib.stride_tricks import sliding_window_view

    n = len(close)
    out: dict[str, np.ndarray] = {}
    for w in WI017_WINDOWS:
        if n <= w:
            continue  # no complete forward window for any t
        # sliding row j covers high[j..j+w-1]; we need window [t+1..t+w] for
        # entry t = j-1, so drop row 0 -> rows j=1..n-w, entries t=0..n-w-1
        wh = sliding_window_view(high, w)[1:]  # shape (n-w, w)
        wl = sliding_window_view(low, w)[1:]
        c = close[: n - w]  # close_t for entry t = j-1

        up_hit = wh >= 1.10 * c[:, None]
        dn_hit = wl <= 0.90 * c[:, None]
        # first True index (k+1 = days from t), 0 if never -> masked later
        def _first(hits: np.ndarray) -> np.ndarray:
            any_hit = hits.any(axis=1)
            idx = np.where(any_hit, hits.argmax(axis=1) + 1, 0)
            return np.where(any_hit, idx, np.nan)

        d_up = _first(up_hit)
        d_dn = _first(dn_hit)
        first_touch = np.zeros(len(c), dtype="float32")
        both_up = ~np.isnan(d_up) & (np.isnan(d_dn) | (d_up < d_dn))
        both_dn = ~np.isnan(d_dn) & (np.isnan(d_up) | (d_dn < d_up))
        first_touch[both_up] = 1.0
        first_touch[both_dn] = -1.0

        pos_pk = wh.argmax(axis=1) + 1  # day of forward peak (1-based within window)
        pos_bt = wl.argmin(axis=1) + 1
        peak = wh.max(axis=1)
        bot = wl.min(axis=1)
        rung = (peak - bot) / c  # amplitude in return units
        delta = np.abs(pos_pk - pos_bt).astype("float64")
        sign = np.where(pos_pk > pos_bt, 1.0, -1.0)  # + : bottom precedes peak
        velocity = sign * rung / np.maximum(delta, 1.0)

        m = n - len(c)  # tail rows have no window
        def _pad(arr: np.ndarray) -> np.ndarray:
            return np.concatenate([arr.astype("float32"), np.full(m, np.nan, "float32")])

        out[f"first_touch_{w}"] = _pad(first_touch)
        out[f"days_to_up_{w}"] = _pad(d_up.astype("float32"))
        out[f"days_to_dn_{w}"] = _pad(d_dn.astype("float32"))
        out[f"rung_{w}"] = _pad(rung.astype("float32"))
        out[f"velocity_{w}"] = _pad(velocity.astype("float32"))
    return pd.DataFrame(out)


def main() -> int:
    t0 = time.time()
    os.makedirs(OUT_DIR, exist_ok=True)
    quar = quarantined_symbols()
    files = sorted(glob.glob(RAW_GLOB))
    acc: dict[int, dict[str, float]] = {}
    n_symbols = 0
    for f in files:
        sym = os.path.basename(f).replace("symbol=", "").replace(".parquet", "")
        if sym in quar:
            continue
        df = pq.read_table(f).to_pandas().sort_values("date").reset_index(drop=True)
        df = df[df["close"] > 0]
        if len(df) < 5:
            continue
        high = df["high"].to_numpy("float64")
        low = df["low"].to_numpy("float64")
        close = df["close"].to_numpy("float64")
        res = derived_for_symbol(high, low, close)
        res.insert(0, "date", df["date"].values)
        res.insert(1, "close", close.astype("float32"))
        pq.write_table(pa.Table.from_pandas(res, preserve_index=False), os.path.join(OUT_DIR, f"{sym}.parquet"))
        n_symbols += 1
        for w in WI017_WINDOWS:
            if f"first_touch_{w}" not in res.columns:
                continue
            a = acc.setdefault(w, {"n": 0.0, "up": 0.0, "dn": 0.0, "neither": 0.0,
                                   "rung": 0.0, "vel": 0.0, "vel_abs": 0.0})
            ft = res[f"first_touch_{w}"]
            m = ft.notna()
            a["n"] += float(m.sum())
            a["up"] += float((ft[m] == 1.0).sum())
            a["dn"] += float((ft[m] == -1.0).sum())
            a["neither"] += float((ft[m] == 0.0).sum())
            rk = res[f"rung_{w}"][m]
            vl = res[f"velocity_{w}"][m]
            a["rung"] += float(rk.sum())
            a["vel"] += float(vl.sum())
            a["vel_abs"] += float(vl.abs().sum())
    summary = {
        "market": MARKET,
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "symbols_written": n_symbols,
        "definitions": {
            "first_touch": "+1 up10 touched before dn10 in [t+1..t+w]; -1 dn first; 0 neither",
            "days_to_up/dn": "trading days from t to FIRST barrier touch (NaN never)",
            "rung": "(fwd peak - fwd bottom)/close_t",
            "velocity": "signed rung / |bars between peak day and bottom day| (min 1); + when bottom precedes peak (bottom-to-peak per admin spec)",
        },
        "per_window": {
            str(w): {
                "n_rows": int(v["n"]),
                "share_up_first": round(v["up"] / v["n"], 6) if v["n"] else None,
                "share_dn_first": round(v["dn"] / v["n"], 6) if v["n"] else None,
                "share_neither": round(v["neither"] / v["n"], 6) if v["n"] else None,
                "mean_rung": round(v["rung"] / v["n"], 6) if v["n"] else None,
                "mean_velocity": round(v["vel"] / v["n"], 6) if v["n"] else None,
                "mean_abs_velocity": round(v["vel_abs"] / v["n"], 6) if v["n"] else None,
            }
            for w, v in acc.items()
        },
    }
    with open(SUMMARY_JSON, "w") as fh:
        json.dump(summary, fh, indent=2)
    lines = [
        "# WI-017 run 2 — derived targets (first-touch triple-barrier, velocity), USD",
        "",
        f"Generated (UTC): {summary['generated_utc']} · symbols: {summary['symbols_written']}",
        "",
        "| window | rows | up-first | dn-first | neither | mean rung | mean vel | mean |vel| |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for w in list(WI017_WINDOWS):
        v = summary["per_window"].get(str(w))
        if v:
            lines.append(
                f"| {w} | {v['n_rows']} | {v['share_up_first']} | {v['share_dn_first']} "
                f"| {v['share_neither']} | {v['mean_rung']} | {v['mean_velocity']} | {v['mean_abs_velocity']} |"
            )
    lines += [
        "",
        "Definitions: " + "; ".join(f"`{k}` = {v}" for k, v in summary["definitions"].items()),
        "",
        "DOA screen (<1% share): flagged per admin rule, kept descriptive.",
    ]
    with open(SUMMARY_MD, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"DONE symbols={n_symbols} elapsed={time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
