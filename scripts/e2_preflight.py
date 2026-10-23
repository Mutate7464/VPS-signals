"""E2 pre-flight: dataset provenance + memory projection (read-only)."""
from __future__ import annotations
import argparse, csv, datetime as dt, glob, sys
from pathlib import Path
import numpy as np, psutil, pyarrow.parquet as pq

BASE = Path(__file__).resolve().parents[1]
DL = BASE / "data" / "dead_letter_tickers.csv"
RAW = BASE / "data" / "raw_ohlcv"

def load_quarantine(market: str) -> set[str]:
    if not DL.exists():
        return set()
    with open(DL) as f:
        r = csv.DictReader(f)
        return {row["symbol"] for row in r if row.get("market") == market}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--market", default="USD")
    parser.add_argument("--min-date", default="2016-01-01")
    args = parser.parse_args()
    market = args.market.upper()
    import pandas as pd
    mindate = pd.Timestamp(args.min_date)

    quar = load_quarantine(market)
    files = sorted(glob.glob(str(RAW / f"market={market}" / "*.parquet")))
    if not files:
        print(f"ERROR: no parquet files in {RAW}/market={market}", file=sys.stderr)
        sys.exit(1)

    rows = []; mins = []; maxs = []; syms = []; qcount = 0; short = 0; short500 = 0
    for f in files:
        sym = Path(f).stem.split("=",1)[-1]
        if sym in quar:
            qcount += 1
            continue
        t = pq.read_table(f)
        d = pd.to_datetime(t.column("date").to_pandas())
        r = t.num_rows
        rows.append(r); mins.append(d.min()); maxs.append(d.max()); syms.append(sym)
        if r < 125: short += 1
        elif r < 500: short500 += 1

    rarr = np.array(rows)
    total = rarr.sum()
    print(f"=== Dataset provenance ({market}) ===")
    print(f"source:        {RAW}/market={market}")
    print(f"tickers:       {len(syms)} (quarantined excluded: {qcount})")
    print(f"total rows:    {total}")
    print(f"rows median:   {np.median(rarr):.0f}  min: {rarr.min()}  max: {rarr.max()}")
    print(f"  < 125 bars:  {short}")
    print(f"  < 500 bars:  {short500}")
    print(f"date min:      {min(mins).date()}  max: {max(maxs).date()}")

    # projected labeled rows with the window cut
    warmup = pd.Timedelta(days=250)
    win_start = mindate - warmup
    projected = 0
    n_after_win = 0
    for f in files:
        sym = Path(f).stem.split("=",1)[-1]
        if sym in quar: continue
        t = pq.read_table(f)
        d = pd.to_datetime(t.column("date").to_pandas())
        # rows >= win_start
        n = (d >= win_start).sum()
        # after feature/target computation we drop ~20 trailing rows + any nan from windows
        labeled = max(0, n - 20)
        projected += labeled
        if labeled > 0:
            n_after_win += 1

    print(f"window start:  {win_start.date()} (min_date={mindate.date()}, read from min_date-250d)")
    print(f"tickers with labeled rows after window: {n_after_win}")
    print(f"projected labeled rows (after window, ≈rows-20 per ticker): {projected}")

    # memory projection
    n_cols = 63   # raw features
    projected_ram_mb = projected * n_cols * 4 / (1024*1024)
    full_ram_mb = projected * (n_cols * 2 + 10) * 4 / (1024*1024)  # cs_pct doubles, plus targets etc
    mem = psutil.virtual_memory()
    print(f"projected feature-only float32 RAM: {projected_ram_mb:.0f} MB ({projected} rows × {n_cols} cols)")
    print(f"projected full panel RAM (w/ targets, cs_pct, etc): {full_ram_mb:.0f} MB")
    print(f"MemAvailable:   {mem.available/(1024*1024):.0f} MB  (total {mem.total/(1024*1024):.0f} MB)")
    print(f"fit vs 4.5 GB budget: {'OK' if full_ram_mb < 4500 else 'TIGHT — consider --min-date 2019-01-01'}")

    # Write report
    report = BASE / "reports" / "diag_D002_e2_preflight.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    with open(report, "w") as rp:
        rp.write(f"# E2 Pre-flight Audit ({market})\n\nGenerated: {dt.datetime.now(dt.timezone.utc).isoformat()}\n\n")
        rp.write(f"- source: `{RAW}/market={market}`\n")
        rp.write(f"- tickers: {len(syms)} (quarantined excluded: {qcount})\n")
        rp.write(f"- total rows: {total}  median: {np.median(rarr):.0f}  min: {rarr.min()}  max: {rarr.max()}\n")
        rp.write(f"- < 125 bars: {short}  < 500 bars: {short500}\n")
        rp.write(f"- date range: {min(mins).date()} → {max(maxs).date()}\n")
        rp.write(f"- window: read from {win_start.date()} (min_date={mindate.date()} - 250d warmup)\n")
        rp.write(f"- tickers with labeled rows after window: {n_after_win}\n")
        rp.write(f"- projected labeled rows: {projected}\n")
        rp.write(f"- projected feature-only RAM: {projected_ram_mb:.0f} MB\n")
        rp.write(f"- projected full panel RAM: {full_ram_mb:.0f} MB\n")
        rp.write(f"- MemAvailable: {mem.available/(1024*1024):.0f} MB / {mem.total/(1024*1024):.0f} MB\n")
        rp.write(f"- budget 4.5 GB: {'OK' if full_ram_mb < 4500 else 'TIGHT'}\n")
        rp.write(f"\n## Quarantine list ({market})\n\n{qcount} tickers excluded from `data/dead_letter_tickers.csv`.\n")
    print(f"\nReport written to {report}")

if __name__ == "__main__":
    main()
