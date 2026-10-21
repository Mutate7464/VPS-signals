"""Sprint 1 — Async-paced IBKR OHLCV ingestion engine (runs on Node A / M1 Mac).

Downloads ADJUSTED_LAST daily bars into partitioned Parquet files under
`data/raw_ohlcv/market={USD|CAD}/symbol={SYM}.parquet`. Incremental delta
fetches are computed from the last stored bar date. Rate-limited at 1 request /
`request_delay_sec` with a `Semaphore(1)`.

NOTE: this module is executed on the M1 MacBook Air (local IB Gateway on
`127.0.0.1:4001/4002`), NOT on the Linux VPS. It is synced here for completeness.
"""

import argparse
import asyncio
import datetime as dt
from pathlib import Path

import pandas as pd
import yaml
from ib_async import IB, Stock, util


def load_config(config_path: str = "config/settings.yaml") -> dict:
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def compute_duration_str(parquet_path: Path, default_lookback: str = "5 Y") -> str:
    """If Parquet file exists, compute delta days since last bar; otherwise return full cold lookback."""
    if not parquet_path.exists():
        return default_lookback
    df_existing = pd.read_parquet(parquet_path, columns=["date"])
    if df_existing.empty:
        return default_lookback
    last_date = pd.to_datetime(df_existing["date"]).max().date()
    delta_days = (dt.date.today() - last_date).days
    if delta_days <= 0:
        return "0 D"
    # Pad by 5 days to overwrite any recent corporate action adjustments
    return f"{min(delta_days + 5, 365)} D"


async def fetch_ticker_ohlcv(ib: IB, row: pd.Series, market_label: str, cfg: dict, sem: asyncio.Semaphore) -> dict:
    symbol = str(row["symbol"]).strip()
    currency = str(row["currency"]).strip()
    exchange = str(row.get("exchange", "SMART")).strip()
    primary_exch = str(row.get("primary_exchange", "")).strip()

    out_dir = Path(cfg["project"]["base_dir"]) / "data" / "raw_ohlcv" / f"market={market_label}"
    out_dir.mkdir(parents=True, exist_ok=True)
    parquet_path = out_dir / f"symbol={symbol}.parquet"

    duration_str = compute_duration_str(parquet_path, cfg["ibkr"]["lookback_cold"])

    if duration_str == "0 D":
        df_old = pd.read_parquet(parquet_path)
        return {
            "symbol": symbol,
            "market": market_label,
            "status": "UP_TO_DATE",
            "rows": len(df_old),
            "min_date": str(df_old["date"].min()),
            "max_date": str(df_old["date"].max()),
        }

    contract = Stock(symbol, exchange, currency, primaryExchange=primary_exch)

    async with sem:
        try:
            qualified = await ib.qualifyContractsAsync(contract)
            if not qualified:
                return {"symbol": symbol, "market": market_label, "status": "UNQUALIFIED", "rows": 0}

            bars = await ib.reqHistoricalDataAsync(
                contract,
                endDateTime="",
                durationStr=duration_str,
                barSizeSetting=cfg["ibkr"]["bar_size"],
                whatToShow=cfg["ibkr"]["what_to_show"],
                useRTH=cfg["ibkr"]["use_rth"],
                formatDate=1,
                timeout=cfg["ibkr"]["timeout_sec"],
            )
            await asyncio.sleep(cfg["ibkr"]["request_delay_sec"])

            if not bars:
                return {"symbol": symbol, "market": market_label, "status": "EMPTY_BARS", "rows": 0}

            df_new = util.df(bars)
            df_new["date"] = pd.to_datetime(df_new["date"]).dt.date
            num_cols = ["open", "high", "low", "close", "volume", "average"]
            for c in num_cols:
                if c in df_new.columns:
                    df_new[c] = df_new[c].astype("float32")

            if parquet_path.exists():
                df_old = pd.read_parquet(parquet_path)
                df_combined = (
                    pd.concat([df_old, df_new], ignore_index=True)
                    .drop_duplicates(subset=["date"], keep="last")
                    .sort_values("date")
                    .reset_index(drop=True)
                )
            else:
                df_combined = df_new.sort_values("date").reset_index(drop=True)

            df_combined.to_parquet(parquet_path, index=False, engine="pyarrow")

            return {
                "symbol": symbol,
                "market": market_label,
                "status": "SUCCESS",
                "rows": len(df_combined),
                "min_date": str(df_combined["date"].min()),
                "max_date": str(df_combined["date"].max()),
            }

        except Exception as exc:
            await asyncio.sleep(5.0)
            return {"symbol": symbol, "market": market_label, "status": f"ERROR: {exc}", "rows": 0}


async def main_async(market: str, dry_run: bool = False):
    cfg = load_config()
    path_map = {
        "USD": cfg["watchlists"]["usd_path"],
        "CAD": cfg["watchlists"]["cad_path"],
        "HOLDINGS": cfg["watchlists"]["holdings_path"],
    }
    csv_path = Path(cfg["project"]["base_dir"]) / path_map[market]
    df_watch = pd.read_csv(csv_path)

    if dry_run:
        print(f"[DRY RUN] Validated {len(df_watch)} rows in {csv_path}")
        return

    ib = IB()
    await ib.connectAsync(
        cfg["ibkr"]["host"], cfg["ibkr"]["port"], clientId=cfg["ibkr"]["client_id"]
    )

    sem = asyncio.Semaphore(1)
    audit_rows = []
    for _, row in df_watch.iterrows():
        mkt_label = str(row["currency"]).strip().upper()
        res = await fetch_ticker_ohlcv(ib, row, mkt_label, cfg, sem)
        audit_rows.append(res)
        print(f"[{res['market']}] {res['symbol']}: {res['status']} ({res['rows']} rows)")

    ib.disconnect()

    df_audit = pd.DataFrame(audit_rows)
    audit_out = Path(cfg["project"]["base_dir"]) / "data" / f"audit_ingestion_{market}.csv"
    df_audit.to_csv(audit_out, index=False)
    print(f"Saved Gate 1 audit summary to {audit_out}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--market", choices=["USD", "CAD", "HOLDINGS"], required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    asyncio.run(main_async(args.market, args.dry_run))
