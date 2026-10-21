"""Sprint 0 — Build canonical 300-ticker watchlists + sector map from reference CSV files.

Input convention (files placed in `ibkrdownload/`):
  IV_CD_*.csv   — Canadian IV screen (.TO suffix, Sector/Industry/Sub-group columns)
  IV_US_*.csv   — US IV screen (same format, US exchanges)
  TC_CD_*.csv   — Canadian TC Quantamental screen (Sector & Industry column)
  TC_US_*.csv   — US TC Quantamental screen (same format, US exchanges)
  opt.csv       — IBKR API watchlist export (DES,SYMBOL,STK,SMART/EXCHANGE format)

Outputs:
  config/watchlist_300_usd.csv   — symbol,sec_type,exchange,primary_exchange,currency
  config/watchlist_300_cad.csv   — same format
  config/sector_map.csv          — symbol,market,sector,industry,sub_group,company_name
"""

import argparse
import glob
import logging
import os
import re
import sys
from pathlib import Path
from typing import Optional

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("BuildWatchlist")

# ---------------------------------------------------------------------------
# Exchange normalization
# ---------------------------------------------------------------------------
EXCHANGE_MAP = {
    "TSE":   {"primary_exchange": "TSE",     "currency": "CAD"},
    "TSX":   {"primary_exchange": "TSE",     "currency": "CAD"},
    "TSXV":  {"primary_exchange": "VENTURE", "currency": "CAD"},
    "NEO":   {"primary_exchange": "AEQS",    "currency": "CAD"},
    "NASDAQ": {"primary_exchange": "NASDAQ",  "currency": "USD"},
    "NYSE":  {"primary_exchange": "NYSE",    "currency": "USD"},
    "ARCA":  {"primary_exchange": "ARCA",    "currency": "USD"},
    "AMEX":  {"primary_exchange": "AMEX",    "currency": "USD"},
    "NYSEAMERICAN": {"primary_exchange": "AMEX", "currency": "USD"},
}

# Exchanges to exclude (non-primary Canadian exchanges)
EXCLUDE_EXCHANGES = {"TSXV", "NEO", "VENTURE", "AEQS"}

# Known US primary exchanges for well-known symbols (opt.csv only stores SMART/AMEX)
KNOWN_US_EXCHANGES = {
    "A": "NYSE", "AAPL": "NASDAQ", "ABBV": "NYSE", "ACN": "NYSE", "ADBE": "NASDAQ",
    "ADI": "NASDAQ", "ADP": "NASDAQ", "ADSK": "NASDAQ", "AEP": "NASDAQ", "ALAB": "NASDAQ",
    "AMD": "NASDAQ", "AMGN": "NASDAQ", "AMT": "NYSE", "AMZN": "NASDAQ", "ANET": "NYSE",
    "APH": "NYSE", "APP": "NASDAQ", "ARM": "NASDAQ", "AVGO": "NASDAQ", "AXP": "NYSE",
    "BA": "NYSE", "BABA": "NYSE", "BAC": "NYSE", "BKNG": "NASDAQ", "BLK": "NYSE",
    "BMY": "NYSE", "BRK B": "NYSE", "BSX": "NYSE", "BURL": "NYSE", "C": "NYSE",
    "CAT": "NYSE", "CCJ": "NYSE", "CCL": "NYSE", "CDNS": "NASDAQ", "CEG": "NASDAQ",
    "CI": "NYSE", "CLX": "NYSE", "CMCSA": "NASDAQ", "CMG": "NYSE", "COIN": "NASDAQ",
    "COST": "NASDAQ", "CRM": "NYSE", "CRWD": "NASDAQ", "CRWV": "NASDAQ",
    "CSCO": "NASDAQ", "CVS": "NYSE", "CVX": "NYSE", "CYTK": "NASDAQ",
    "DE": "NYSE", "DELL": "NYSE", "DHR": "NYSE", "DIS": "NYSE", "DOCU": "NASDAQ",
    "F": "NYSE", "FANG": "NASDAQ", "FDX": "NYSE", "FSLR": "NASDAQ", "FTAI": "NASDAQ",
    "FTNT": "NASDAQ", "GD": "NYSE", "GE": "NYSE", "GILD": "NASDAQ", "GM": "NYSE",
    "GME": "NYSE", "GOOG": "NASDAQ", "GOOGL": "NASDAQ", "GS": "NYSE", "HD": "NYSE",
    "HIMS": "NYSE", "HON": "NASDAQ", "HOOD": "NASDAQ", "IBM": "NYSE", "INTC": "NASDAQ",
    "INTU": "NASDAQ", "ISRG": "NASDAQ", "JNJ": "NYSE", "JPM": "NYSE", "KHC": "NASDAQ",
    "KKR": "NYSE", "KLAC": "NASDAQ", "KO": "NYSE", "LIN": "NASDAQ",
    "LLY": "NYSE", "LMT": "NYSE", "LNG": "NYSE", "LOW": "NYSE", "LRCX": "NASDAQ",
    "LULU": "NASDAQ", "LVS": "NYSE", "MA": "NYSE", "MAR": "NASDAQ", "MCD": "NYSE",
    "MDLZ": "NASDAQ", "META": "NASDAQ", "MMM": "NYSE", "MO": "NYSE", "MPC": "NYSE",
    "MRK": "NYSE", "MRNA": "NASDAQ", "MRVL": "NASDAQ", "MS": "NYSE",
    "MSFT": "NASDAQ", "MSTR": "NASDAQ", "MU": "NASDAQ", "NBIS": "NASDAQ",
    "NEE": "NYSE", "NFLX": "NASDAQ", "NKE": "NYSE", "NOW": "NYSE", "NVDA": "NASDAQ",
    "ORCL": "NYSE", "PANW": "NASDAQ", "PCG": "NYSE", "PDD": "NASDAQ",
    "PEP": "NASDAQ", "PFE": "NYSE", "PG": "NYSE", "PLTR": "NYSE",
    "PM": "NYSE", "PR": "NYSE", "PYPL": "NASDAQ", "QCOM": "NASDAQ",
    "RBLX": "NYSE", "REGN": "NASDAQ", "RIVN": "NASDAQ", "RKLB": "NASDAQ",
    "RTX": "NYSE", "SBUX": "NASDAQ", "SCHW": "NYSE", "SHW": "NYSE",
    "SMCI": "NASDAQ", "SNAP": "NYSE", "SNOW": "NYSE", "SOFI": "NASDAQ",
    "SPGI": "NYSE", "SQ": "NYSE", "SYK": "NYSE", "T": "NYSE", "TEM": "NASDAQ",
    "TEVA": "NYSE", "TGT": "NYSE", "TJX": "NYSE", "TMO": "NYSE",
    "TMUS": "NASDAQ", "TSLA": "NASDAQ", "TSM": "NYSE", "TXN": "NASDAQ",
    "U": "NYSE", "UBER": "NYSE", "UNH": "NYSE", "UNP": "NYSE",
    "UPS": "NYSE", "V": "NYSE", "VRT": "NYSE", "VZ": "NYSE",
    "WBD": "NASDAQ", "WFC": "NYSE", "WMT": "NYSE",
    "XOM": "NYSE", "XYZ": "NASDAQ", "ZM": "NASDAQ", "ZS": "NASDAQ",
}

# Hardcoded benchmark tickers (always included)
BENCHMARK_USD = [
    {"symbol": "SPY", "sec_type": "STK", "exchange": "SMART", "primary_exchange": "ARCA", "currency": "USD"},
    {"symbol": "QQQ", "sec_type": "STK", "exchange": "SMART", "primary_exchange": "NASDAQ", "currency": "USD"},
]
BENCHMARK_CAD = [
    {"symbol": "XIU", "sec_type": "STK", "exchange": "SMART", "primary_exchange": "TSE", "currency": "CAD"},
    {"symbol": "XIC", "sec_type": "STK", "exchange": "SMART", "primary_exchange": "TSE", "currency": "CAD"},
    {"symbol": "XDIV", "sec_type": "STK", "exchange": "SMART", "primary_exchange": "TSE", "currency": "CAD"},
]


def _normalize_symbol(sym: str) -> Optional[str]:
    """Strip whitespace, remove .TO suffix, reject empties/nans."""
    if pd.isna(sym):
        return None
    s = str(sym).strip().strip('"')
    if s.lower() in ("nan", "none", ""):
        return None
    # Remove .TO suffix (case-insensitive)
    if s.upper().endswith(".TO"):
        s = s[:-3]
    return s


def _normalize_exchange(exch_raw: str) -> Optional[str]:
    """Normalize exchange string to a known key in EXCHANGE_MAP."""
    if pd.isna(exch_raw):
        return None
    e = str(exch_raw).strip().strip('"').upper()
    # Common variations
    if e in ("NYSE AMERICAN", "NYSEAMERICAN", "NYSE MKT"):
        e = "AMEX"
    if e == "TSX":
        e = "TSE"
    return e if e in EXCHANGE_MAP else None


def _parse_opt_csv(filepath: str) -> pd.DataFrame:
    """Parse IBKR watchlist export format (DES,SYMBOL,STK,SMART/EXCHANGE)."""
    rows = []
    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("CSVEXPORT") or line.startswith("COLUMN"):
                continue
            # Format: DES,SYMBOL,STK,SMART/EXCHANGE,,,,,
            parts = [p.strip() for p in line.split(",")]
            if len(parts) < 4 or parts[0] != "DES":
                continue
            symbol = parts[1]
            exchange_field = parts[3]  # e.g., "SMART/AMEX" or "SMART/TSE"
            # Extract the primary exchange from SMART/XXX
            if "/" in exchange_field:
                primary = exchange_field.split("/")[-1].strip().upper()
            else:
                primary = exchange_field.strip().upper()
            sym_clean = _normalize_symbol(symbol)
            if not sym_clean or primary == "VALUE":
                continue  # skip invalid entries
            rows.append({"symbol_raw": sym_clean, "exchange_raw": primary, "sector": None, "industry": None, "sub_group": None, "company_name": None, "source": "opt"})
    return pd.DataFrame(rows)


def _parse_iv_csv(filepath: str, market: str) -> pd.DataFrame:
    """Parse IV (Implied Volatility) CSV file.

    Expected columns: Symbol, Description, Exch, ..., Sector, Industry, Sub-group
    """
    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        logger.warning(f"Failed to parse {filepath}: {e}")
        return pd.DataFrame()

    sym_col = "Symbol" if "Symbol" in df.columns else ("Ticker" if "Ticker" in df.columns else None)
    if sym_col is None:
        logger.warning(f"No Symbol/Ticker column in {filepath}")
        return pd.DataFrame()

    df["symbol_raw"] = df[sym_col].apply(_normalize_symbol)
    df = df.dropna(subset=["symbol_raw"])

    exch_col = "Exch" if "Exch" in df.columns else ("Exchange" if "Exchange" in df.columns else None)
    if exch_col:
        df["exchange_raw"] = df[exch_col].apply(_normalize_exchange)
    else:
        df["exchange_raw"] = "TSE" if market == "CAD" else None

    # Extract sector info
    df["sector"] = df.get("Sector", pd.Series(dtype=str))
    df["industry"] = df.get("Industry", pd.Series(dtype=str))
    df["sub_group"] = df.get("Sub-group", pd.Series(dtype=str))
    df["company_name"] = df.get("Description", pd.Series(dtype=str))
    df["source"] = os.path.basename(filepath)

    return df[["symbol_raw", "exchange_raw", "sector", "industry", "sub_group", "company_name", "source"]]


def _parse_tc_csv(filepath: str, market: str) -> pd.DataFrame:
    """Parse TC (Quantamental) CSV file.

    Expected columns: Rank, Exchange, Symbol, Company Name, Sector & Industry, ...
    """
    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        logger.warning(f"Failed to parse {filepath}: {e}")
        return pd.DataFrame()

    sym_col = "Symbol" if "Symbol" in df.columns else ("Ticker" if "Ticker" in df.columns else None)
    if sym_col is None:
        logger.warning(f"No Symbol/Ticker column in {filepath}")
        return pd.DataFrame()

    df["symbol_raw"] = df[sym_col].apply(_normalize_symbol)
    df = df.dropna(subset=["symbol_raw"])

    exch_col = "Exchange" if "Exchange" in df.columns else ("Exch" if "Exch" in df.columns else None)
    if exch_col:
        df["exchange_raw"] = df[exch_col].apply(_normalize_exchange)
    else:
        df["exchange_raw"] = "TSE" if market == "CAD" else None

    # Sector & Industry is a combined field like "Metals & Mining"
    if "Sector & Industry" in df.columns:
        df["sector_industry"] = df["Sector & Industry"].astype(str).str.strip()
        # Try to split on common separators — but keep as sector, leave industry blank
        df["sector"] = df["sector_industry"].replace(["nan", "None", ""], None)
        df["industry"] = None
    else:
        df["sector"] = None
        df["industry"] = None

    df["sub_group"] = None
    df["company_name"] = df.get("Company Name", pd.Series(dtype=str))
    df["source"] = os.path.basename(filepath)

    return df[["symbol_raw", "exchange_raw", "sector", "industry", "sub_group", "company_name", "source"]]


def _resolve_exchange(row: pd.Series, market: str) -> tuple:
    """Given a row with exchange_raw, resolve to (primary_exchange, currency)."""
    exch = row.get("exchange_raw")
    if exch and exch in EXCHANGE_MAP:
        info = EXCHANGE_MAP[exch]
        return info["primary_exchange"], info["currency"]

    # Fallback based on market
    if market == "CAD":
        return "TSE", "CAD"
    else:
        return "SMART", "USD"


def _merge_and_deduplicate(df_all: pd.DataFrame) -> pd.DataFrame:
    """Merge multiple source rows per symbol, preferring TC sector data, keeping first exchange."""
    if df_all.empty:
        return df_all

    # Priority: TC sources over IV sources for sector data
    df_all["source_priority"] = df_all["source"].apply(
        lambda s: 0 if str(s).startswith("TC_") else 1
    )

    # Group by symbol
    results = []
    for symbol, group in df_all.groupby("symbol_raw"):
        group = group.sort_values("source_priority")

        # Take the first (highest priority) non-null values
        row = {
            "symbol": symbol,
            "exchange_raw": group["exchange_raw"].dropna().iloc[0] if not group["exchange_raw"].dropna().empty else None,
            "sector": _first_non_null(group["sector"]),
            "industry": _first_non_null(group["industry"]),
            "sub_group": _first_non_null(group["sub_group"]),
            "company_name": _first_non_null(group["company_name"]),
            "sources": ", ".join(sorted(set(group["source"].astype(str)))),
        }
        results.append(row)

    return pd.DataFrame(results)


def _first_non_null(series: pd.Series) -> Optional[str]:
    """Return the first non-null, non-nan, non-empty string value in a series."""
    for val in series:
        if pd.notna(val) and str(val).strip() not in ("", "nan", "None"):
            return str(val).strip()
    return None


def build_watchlist(market: str, base_dir: str, dry_run: bool = False) -> tuple:
    """Build the watchlist and sector map for a given market (USD or CAD).

    Returns (watchlist_df, sector_df).
    """
    ibkr_dir = Path(base_dir) / "ibkrdownload"
    market_lower = market.lower()

    all_rows = []

    # --- Parse IV files ---
    # Convention: IV_US_*.csv (US market) or IV_CD_*.csv (Canadian market)
    mkt_suffix_iv = "US" if market == "USD" else "CD"
    iv_pattern = f"IV_{mkt_suffix_iv}_*.csv"
    for fp in sorted(glob.glob(str(ibkr_dir / iv_pattern))):
        logger.info(f"  Parsing IV: {os.path.basename(fp)}")
        df = _parse_iv_csv(fp, market)
        if not df.empty:
            all_rows.append(df)

    # --- Parse TC files ---
    # Convention: TC_US_*.csv (US market) or TC_CD_*.csv (Canadian market)
    mkt_suffix_tc = "US" if market == "USD" else "CD"
    tc_pattern = f"TC_{mkt_suffix_tc}_*.csv"
    for fp in sorted(glob.glob(str(ibkr_dir / tc_pattern))):
        logger.info(f"  Parsing TC: {os.path.basename(fp)}")
        df = _parse_tc_csv(fp, market)
        if not df.empty:
            all_rows.append(df)

    # --- Parse opt.csv (shared across markets) ---
    opt_path = ibkr_dir / "opt.csv"
    if opt_path.exists():
        logger.info(f"  Parsing opt.csv")
        df_opt = _parse_opt_csv(str(opt_path))
        if not df_opt.empty:
            # Filter opt.csv rows by market based on exchange
            df_opt = df_opt.dropna(subset=["exchange_raw"])
            if market == "CAD":
                df_opt = df_opt[df_opt["exchange_raw"].isin(["TSE", "TSX", "TSXV", "NEO"])]
            else:
                df_opt = df_opt[~df_opt["exchange_raw"].isin(["TSE", "TSX", "TSXV", "NEO", "VENTURE", "AEQS"])]
            if not df_opt.empty:
                all_rows.append(df_opt)

    if not all_rows:
        logger.warning(f"No reference files found for market={market} in {ibkr_dir}")
        return pd.DataFrame(), pd.DataFrame()

    # --- Merge all sources ---
    df_all = pd.concat(all_rows, ignore_index=True)
    logger.info(f"  Raw rows before dedup: {len(df_all)}")

    # --- Normalize exchange, drop excluded exchanges ---
    df_all["exchange_normalized"] = df_all["exchange_raw"].apply(_normalize_exchange)
    exclude_mask = df_all["exchange_normalized"].isin(EXCLUDE_EXCHANGES)
    if exclude_mask.any():
        logger.info(f"  Excluding {exclude_mask.sum()} tickers from {EXCLUDE_EXCHANGES}")
        df_all = df_all[~exclude_mask]

    # --- Deduplicate ---
    df_merged = _merge_and_deduplicate(df_all)
    logger.info(f"  Unique symbols after dedup: {len(df_merged)}")

    # --- Resolve exchanges ---
    resolved = df_merged["exchange_raw"].apply(
        lambda e: EXCHANGE_MAP.get(e, {"primary_exchange": "TSE" if market == "CAD" else "SMART", "currency": "CAD" if market == "CAD" else "USD"})
    )
    df_merged["primary_exchange"] = resolved.apply(lambda r: r["primary_exchange"])
    df_merged["currency"] = resolved.apply(lambda r: r["currency"])

    # Fix US exchanges: opt.csv exports everything as SMART/AMEX regardless of real exchange.
    # Use KNOWN_US_EXCHANGES to correct primary_exchange for well-known symbols.
    if market == "USD":
        for idx, row in df_merged.iterrows():
            sym = row["symbol"]
            if sym in KNOWN_US_EXCHANGES:
                df_merged.at[idx, "primary_exchange"] = KNOWN_US_EXCHANGES[sym]
            elif row["primary_exchange"] == "AMEX" and row["sources"] == "opt":
                # Unknown US ticker from opt.csv only — default to NASDAQ
                df_merged.at[idx, "primary_exchange"] = "NASDAQ"

    # --- Add benchmark tickers ---
    benchmarks = BENCHMARK_USD if market == "USD" else BENCHMARK_CAD
    bench_symbols = {b["symbol"] for b in benchmarks}
    existing_symbols = set(df_merged["symbol"])
    for b in benchmarks:
        if b["symbol"] not in existing_symbols:
            logger.info(f"  Adding benchmark: {b['symbol']}")
            new_row = {
                "symbol": b["symbol"],
                "exchange_raw": b["primary_exchange"],
                "primary_exchange": b["primary_exchange"],
                "currency": b["currency"],
                "sector": "Benchmark",
                "industry": None,
                "sub_group": None,
                "company_name": b["symbol"],
                "sources": "benchmark",
            }
            df_merged = pd.concat([df_merged, pd.DataFrame([new_row])], ignore_index=True)

    # --- Build watchlist CSV ---
    watchlist = pd.DataFrame({
        "symbol": df_merged["symbol"],
        "sec_type": "STK",
        "exchange": "SMART",
        "primary_exchange": df_merged["primary_exchange"],
        "currency": df_merged["currency"],
    })

    # --- Build sector map ---
    sector_map = pd.DataFrame({
        "symbol": df_merged["symbol"],
        "market": market,
        "sector": df_merged["sector"].fillna(""),
        "industry": df_merged["industry"].fillna(""),
        "sub_group": df_merged["sub_group"].fillna(""),
        "company_name": df_merged["company_name"].fillna(""),
    })

    # --- Write outputs ---
    config_dir = Path(base_dir) / "config"
    watchlist_path = config_dir / f"watchlist_300_{market_lower}.csv"
    sector_path = config_dir / "sector_map.csv"

    if not dry_run:
        watchlist.to_csv(watchlist_path, index=False)
        logger.info(f"  Wrote {len(watchlist)} tickers → {watchlist_path}")

        # For sector_map, merge both markets into one file
        if sector_path.exists() and market == "CAD":
            # Append to existing USD sector map
            existing = pd.read_csv(sector_path)
            sector_map = pd.concat([existing, sector_map], ignore_index=True)
        sector_map.to_csv(sector_path, index=False)
        logger.info(f"  Wrote {len(sector_map)} sector rows → {sector_path}")
    else:
        logger.info(f"  [DRY RUN] Would write {len(watchlist)} tickers → {watchlist_path}")

    return watchlist, sector_map


def main():
    parser = argparse.ArgumentParser(description="Build canonical watchlists from reference CSV files")
    parser.add_argument("--market", choices=["USD", "CAD"], default=None,
                        help="Build only one market (default: both)")
    parser.add_argument("--base-dir", default=str(Path(__file__).resolve().parent.parent),
                        help="Project base directory")
    parser.add_argument("--dry-run", action="store_true",
                        help="Parse and validate without writing files")
    args = parser.parse_args()

    base_dir = args.base_dir
    logger.info(f"Base directory: {base_dir}")
    logger.info(f"Dry run: {args.dry_run}")

    markets = [args.market] if args.market else ["USD", "CAD"]

    for market in markets:
        logger.info(f"{'='*60}")
        logger.info(f"Building {market} watchlist...")
        logger.info(f"{'='*60}")
        wl, sm = build_watchlist(market, base_dir, dry_run=args.dry_run)

        if not wl.empty:
            # Print summary
            exchange_counts = wl["primary_exchange"].value_counts().to_dict()
            logger.info(f"  Summary ({market}): {len(wl)} tickers")
            for exch, count in sorted(exchange_counts.items()):
                logger.info(f"    {exch}: {count}")
            if not sm.empty:
                sectors_with_data = sm["sector"].replace("", pd.NA).dropna()
                logger.info(f"  Sectors populated: {len(sectors_with_data)}/{len(sm)}")
        else:
            logger.warning(f"  No tickers found for {market}")

    logger.info("Done.")


if __name__ == "__main__":
    main()