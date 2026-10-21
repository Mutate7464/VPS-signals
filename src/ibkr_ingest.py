"""Sprint 1 — VPS-side data validation wrapper.

This is the thin VPS copy of ibkr_ingest.py. It validates that synced OHLCV data
exists and is fresh. The actual IBKR download engine lives in ibkrdownload/ibkr_ingest.py
and runs on the M1 MacBook Air (where IB Gateway is locally accessible).

Usage (VPS):
  python src/ibkr_ingest.py --market USD --dry-run     # validate watchlist CSV
  python src/ibkr_ingest.py --market USD                # audit synced data freshness
"""

import argparse
import datetime as dt
import logging
from pathlib import Path

import pandas as pd
import yaml

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("IBKRIngestVPS")


M1_INSTRUCTIONS = """
╔══════════════════════════════════════════════════════════════════════════════╗
║  IBKR data download runs on the M1 MacBook Air (IB Gateway is there).       ║
║                                                                            ║
║  On the M1 Mac:                                                            ║
║    cd ibkrdownload                                                         ║
║    pip install -r requirements.txt                                         ║
║    python build_watchlist.py              # rebuild watchlists if needed    ║
║    python ibkr_ingest.py --market USD     # download USD data               ║
║    python ibkr_ingest.py --market CAD     # download CAD data               ║
║    python sync_back.py                    # push data back to VPS           ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""


def load_config(config_path: str = "config/settings.yaml") -> dict:
    cfg_path = Path(__file__).resolve().parent.parent / config_path
    with open(cfg_path, "r") as f:
        return yaml.safe_load(f)


def audit_synced_data(base_dir: Path, market: str) -> dict:
    """Check data/raw_ohlcv/market={USD|CAD}/ for Parquet files and freshness."""
    ohlcv_dir = base_dir / "data" / "raw_ohlcv" / f"market={market}"
    stats = {
        "market": market,
        "dir_exists": ohlcv_dir.exists(),
        "file_count": 0,
        "total_rows": 0,
        "oldest_date": None,
        "newest_date": None,
        "stale_tickers": [],
        "missing_benchmarks": [],
    }

    if not ohlcv_dir.exists():
        return stats

    parquet_files = list(ohlcv_dir.glob("symbol=*.parquet"))
    stats["file_count"] = len(parquet_files)

    if not parquet_files:
        return stats

    dates_all = []
    benchmark_tickers = {"USD": ["SPY", "QQQ"], "CAD": ["XIU", "XIC", "XDIV"]}
    benchmark_set = set(benchmark_tickers.get(market, []))

    for pq in parquet_files:
        try:
            sym = pq.stem.replace("symbol=", "")
            df = pd.read_parquet(pq, columns=["date"])
            if df.empty:
                continue
            df["date"] = pd.to_datetime(df["date"])
            stats["total_rows"] += len(df)
            dates_all.append(df["date"].min())
            dates_all.append(df["date"].max())

            # Check freshness (< 5 trading days behind is OK)
            newest = df["date"].max().date()
            age_days = (dt.date.today() - newest).days
            if age_days > 7:
                stats["stale_tickers"].append(f"{sym} ({age_days}d old)")

            # Track benchmarks
            benchmark_set.discard(sym)
        except Exception:
            pass

    stats["missing_benchmarks"] = list(benchmark_set)

    if dates_all:
        stats["oldest_date"] = str(min(dates_all).date())
        stats["newest_date"] = str(max(dates_all).date())

    return stats


def main():
    parser = argparse.ArgumentParser(
        description="VPS-side data validation wrapper (M1 Mac handles actual IBKR download)"
    )
    parser.add_argument("--market", choices=["USD", "CAD", "HOLDINGS"], default=None,
                        help="Which market to audit (default: all)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Validate watchlist CSV without auditing data")
    args = parser.parse_args()

    cfg = load_config()
    base_dir = Path(cfg["project"]["base_dir"])

    # Dry-run: just validate the CSV
    if args.dry_run:
        markets = [args.market] if args.market else ["USD", "CAD"]
        for mkt in markets:
            mkt_lower = mkt.lower()
            if mkt == "HOLDINGS":
                csv_path = base_dir / cfg["watchlists"]["holdings_path"]
            else:
                key = "usd_path" if mkt == "USD" else "cad_path"
                csv_path = base_dir / cfg["watchlists"][key]
            if csv_path.exists():
                df = pd.read_csv(csv_path)
                logger.info("[%s] Watchlist: %d tickers in %s", mkt, len(df), csv_path)
            else:
                logger.warning("[%s] Watchlist not found: %s", mkt, csv_path)
        return

    # Full audit
    print(M1_INSTRUCTIONS)

    markets = [args.market] if args.market else ["USD", "CAD"]
    all_empty = True

    for mkt in markets:
        stats = audit_synced_data(base_dir, mkt)
        print(f"\n── {mkt} ──")
        print(f"  Directory:  {'✅ exists' if stats['dir_exists'] else '❌ MISSING — run ingest on M1 Mac'}")
        print(f"  Files:      {stats['file_count']} Parquet files")
        print(f"  Total rows: {stats['total_rows']:,}")
        print(f"  Date range: {stats['oldest_date'] or 'N/A'} → {stats['newest_date'] or 'N/A'}")

        if stats["file_count"] > 0:
            all_empty = False

        if stats["stale_tickers"]:
            print(f"  ⚠️  Stale (>7d): {', '.join(stats['stale_tickers'][:10])}")
            if len(stats["stale_tickers"]) > 10:
                print(f"       ... and {len(stats['stale_tickers']) - 10} more")

        if stats["missing_benchmarks"]:
            print(f"  ⚠️  Missing benchmarks: {', '.join(stats['missing_benchmarks'])}")

    if all_empty:
        print("\n⚠️  No synced data found. Run ingest on the M1 Mac, then sync_back.py.")


if __name__ == "__main__":
    main()