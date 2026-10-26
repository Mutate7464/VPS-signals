"""WI-014 — E5 factor screener: latest-date top-N shortlist (CSV) and tearsheet PDF.

One command produces, for USD then CAD by default (or one market via `--market`),
the validated E5-factor top-N daily shortlist and a research tearsheet:

    reports/wi014_shortlist_{market}_{topN}.csv
    reports/screener_factor_{market}_{YYYYMMDD}.pdf

What is ranked
--------------
Existing E5 factor columns only, exactly as `src/factors/e5_baseline.py` defines
them (`mom_12_1`, `rev_1m`, `vol_20`, `amihud_20`, `log_dollar_vol_20`), ordered
by `mom_12_1` descending — the best-validated single factor on both markets
(WI-012: CAD +0.0271 t+7.33, USD +0.0209 t+6.00). No composite, no model, no
target/skill-bar change, no trade instruction: the shortlist is descriptive
research context under the WI-011 NO_TRADE/cost caveat.

Where the data comes from (bounded memory)
------------------------------------------
`data/features/features_{market}.parquet` is the freshness spine: it is read
column-pruned and in bounded batches (`symbol`, `date` only) to find each
symbol's latest feature row, which fixes the per-market scoring date. The five
factor *values* are not in that panel; they are computed per symbol from
`data/raw_ohlcv/market={market}/symbol={SYM}.parquet` with the shared
`factor_frame` definition (see `docs/plans/logs/WI-014-factor-screener-pdf.md`,
DEVIATIONS). Symbols are streamed one at a time, so no all-ticker
full-history frame is ever materialised.

CLI:
    uv run python scripts/wi014_screener.py --dry-run
    uv run python scripts/wi014_screener.py --market CAD --top-n 5
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.compute as pc
import pyarrow.parquet as pq

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.factors.e5_baseline import E5_FACTORS, factor_frame  # noqa: E402
from src.market_cli import (  # noqa: E402
    add_market_argument,
    cli_markets,
    report_path,
    run_markets,
)

FEATURES_DIR = BASE_DIR / "data" / "features"
RAW_DIR = BASE_DIR / "data" / "raw_ohlcv"
REPORTS = BASE_DIR / "reports"

DEFAULT_TOP_N = 10
RANK_FACTOR = "mom_12_1"
RANKING_RULE = "rank by mom_12_1 descending (WI-012-validated E5 single factor)"
SHORTLIST_COLUMNS = ["rank", "symbol", *E5_FACTORS, "scoring_date"]
# 252d mom_12_1 lookback + 20d vol/amihud window: below this a symbol cannot have
# a complete factor row, so it is skipped rather than ranked on NaNs.
MIN_BARS_FOR_FACTORS = 273
FEATURE_BATCH_SIZE = 131_072


# --------------------------------------------------------------------------- #
# Output paths (always market-suffixed — never a frozen unsuffixed report)
# --------------------------------------------------------------------------- #
def shortlist_csv_path(market: str, top_n: int, *, reports_dir: Path | None = None) -> Path:
    """`reports/wi014_shortlist_{market}_{topN}.csv` for one market."""
    return report_path(reports_dir if reports_dir is not None else REPORTS,
                       "wi014_shortlist", market, f"_{int(top_n)}.csv")


def tearsheet_pdf_path(market: str, scoring_date, *, reports_dir: Path | None = None) -> Path:
    """`reports/screener_factor_{market}_{YYYYMMDD}.pdf` for one market + scoring date."""
    stamp = pd.Timestamp(scoring_date).strftime("%Y%m%d")
    return report_path(reports_dir if reports_dir is not None else REPORTS,
                       "screener_factor", market, f"_{stamp}.pdf")


def features_path(market: str, *, features_dir: Path | None = None) -> Path:
    root = features_dir if features_dir is not None else FEATURES_DIR
    return Path(root) / f"features_{market}.parquet"


# --------------------------------------------------------------------------- #
# Freshness spine: latest feature row per symbol (bounded, column-pruned)
# --------------------------------------------------------------------------- #
def latest_feature_date_per_symbol(features_file: Path | str) -> dict[str, pd.Timestamp]:
    """Each symbol's latest feature date, read in bounded batches of 2 columns.

    Never materialises the all-ticker panel: one batch (~131k rows) of
    `symbol`+`date` is reduced to a per-symbol max before the next batch is read,
    and only the resulting `{symbol: date}` mapping (a few hundred entries) is
    retained.
    """
    latest: dict[str, pd.Timestamp] = {}
    reader = pq.ParquetFile(features_file)
    for batch in reader.iter_batches(batch_size=FEATURE_BATCH_SIZE, columns=["symbol", "date"]):
        frame = batch.to_pandas()
        per_symbol = frame.groupby("symbol", sort=False)["date"].max()
        for symbol, value in per_symbol.items():
            stamp = pd.Timestamp(value)
            previous = latest.get(symbol)
            if previous is None or stamp > previous:
                latest[symbol] = stamp
        del frame
    return latest


def resolve_scoring_date(features_file: Path | str) -> pd.Timestamp:
    """Latest feature date in one market's panel (per-batch max, `date` column only)."""
    best: pd.Timestamp | None = None
    reader = pq.ParquetFile(features_file)
    for batch in reader.iter_batches(batch_size=FEATURE_BATCH_SIZE, columns=["date"]):
        value = pc.max(batch.column("date")).as_py()
        if value is None:
            continue
        stamp = pd.Timestamp(value)
        if best is None or stamp > best:
            best = stamp
    if best is None:
        raise ValueError(f"{features_file} has no feature dates")
    return best


# --------------------------------------------------------------------------- #
# Cross-section for one market
# --------------------------------------------------------------------------- #
@dataclass
class MarketCross:
    """The eligible cross-section of one market on one scoring date."""

    market: str
    scoring_date: pd.Timestamp
    eligible: list[str]
    stale: dict[str, pd.Timestamp] = field(default_factory=dict)


@dataclass
class CrossSection:
    """E5 factor values for every eligible symbol on the scoring date."""

    market: str
    scoring_date: pd.Timestamp
    eligible_symbols: int
    stale_symbols: int
    frame: pd.DataFrame
    skipped: dict[str, int] = field(default_factory=dict)


@dataclass
class ShortlistResult:
    """One market's ranked shortlist plus the metadata the PDF/report needs."""

    market: str
    scoring_date: pd.Timestamp
    shortlist: pd.DataFrame
    cross_section: CrossSection
    stale: dict[str, pd.Timestamp] = field(default_factory=dict)

    @property
    def eligible_symbols(self) -> int:
        return self.cross_section.eligible_symbols


def load_raw_symbol(market: str, symbol: str, *, raw_dir: Path | None = None,
                    as_of=None) -> pd.DataFrame | None:
    """One symbol's OHLCV up to (and including) `as_of`; `None` when no raw file exists."""
    root = raw_dir if raw_dir is not None else RAW_DIR
    path = Path(root) / f"market={market}" / f"symbol={symbol}.parquet"
    if not path.exists():
        return None
    df = pd.read_parquet(path, columns=["date", "open", "high", "low", "close", "volume"])
    df["date"] = pd.to_datetime(df["date"]).astype("datetime64[ns]")
    df = df.sort_values("date").reset_index(drop=True)
    if as_of is not None:
        df = df[df["date"] <= pd.Timestamp(as_of)].reset_index(drop=True)
    return df


def resolve_market_cross(market: str, *, features_dir: Path | None = None,
                         as_of=None) -> MarketCross:
    """Resolve the market's scoring date and its eligible symbols.

    Eligible = the symbol's *latest* feature row lands on the scoring date. A
    symbol whose latest feature row is older is stale (delisted / short history)
    and is not ranked against a fresher cross-section. The scoring date defaults
    to the latest feature date in the market's panel and can be pinned with
    `as_of` (`--date`).

    Raises:
        FileNotFoundError: the market's feature panel is missing.
        ValueError: no symbol has a feature row on the requested date.
    """
    panel = features_path(market, features_dir=features_dir)
    if not panel.exists():
        raise FileNotFoundError(f"missing feature panel {panel}")
    latest = latest_feature_date_per_symbol(panel)
    if not latest:
        raise ValueError(f"{panel} has no feature rows")

    scoring_date = max(latest.values()) if as_of is None else pd.Timestamp(as_of)
    eligible = sorted(symbol for symbol, date in latest.items() if date == scoring_date)
    if not eligible:
        raise ValueError(
            f"{panel}: no symbol has a latest feature row on {scoring_date.date()}"
        )
    stale = {symbol: date for symbol, date in latest.items() if date != scoring_date}
    return MarketCross(market=market, scoring_date=scoring_date, eligible=eligible, stale=stale)


def build_cross_section(cross: MarketCross, *, raw_dir: Path | None = None) -> CrossSection:
    """Compute the five E5 factors for the latest eligible bar of each symbol.

    Symbols are read one at a time and dropped from scope immediately, so peak
    memory is one symbol's history, not the universe. Rows that cannot produce a
    complete factor row (no raw file, stale bar, short history, NaN factor) are
    counted in `skipped`, never ranked.
    """
    rows: list[dict[str, float]] = []
    skipped = {"no_raw_file": 0, "stale_bar": 0, "short_history": 0, "nan_factor": 0}

    for symbol in cross.eligible:
        # Read only bars up to the scoring date: a `--date` run must be exactly as
        # point-in-time as the latest-date run, never a peek at later bars.
        raw = load_raw_symbol(cross.market, symbol, raw_dir=raw_dir, as_of=cross.scoring_date)
        if raw is None or raw.empty:
            skipped["no_raw_file"] += 1
            continue
        if pd.Timestamp(raw["date"].iloc[-1]) != cross.scoring_date:
            skipped["stale_bar"] += 1
            continue
        if len(raw) < MIN_BARS_FOR_FACTORS:
            skipped["short_history"] += 1
            continue
        last = factor_frame(raw).iloc[-1]
        if last.isna().any():
            skipped["nan_factor"] += 1
            continue
        record: dict[str, float] = {"symbol": symbol}
        record.update({name: float(last[name]) for name in E5_FACTORS})
        rows.append(record)

    frame = pd.DataFrame(rows, columns=["symbol", *E5_FACTORS])
    if not frame.empty:
        for name in E5_FACTORS:
            frame[name] = frame[name].astype("float32")

    return CrossSection(
        market=cross.market,
        scoring_date=cross.scoring_date,
        eligible_symbols=len(cross.eligible),
        stale_symbols=len(cross.stale),
        frame=frame,
        skipped=skipped,
    )


# --------------------------------------------------------------------------- #
# Ranking + release
# --------------------------------------------------------------------------- #
def rank_shortlist(cross_section: pd.DataFrame, top_n: int, scoring_date) -> pd.DataFrame:
    """Rank the eligible cross-section by `mom_12_1` descending and take the top N.

    Ties break on symbol for a deterministic, reproducible file. The scoring date
    is carried on every row so the shortlist is self-describing.
    """
    if cross_section.empty:
        return pd.DataFrame(columns=SHORTLIST_COLUMNS)
    ranked = cross_section.sort_values(
        [RANK_FACTOR, "symbol"], ascending=[False, True], kind="mergesort"
    ).reset_index(drop=True)
    ranked = ranked.head(int(top_n)).reset_index(drop=True)
    ranked.insert(0, "rank", np.arange(1, len(ranked) + 1, dtype="int32"))
    ranked["scoring_date"] = pd.Timestamp(scoring_date).strftime("%Y-%m-%d")
    return ranked[SHORTLIST_COLUMNS]


def generate_shortlist(market: str, *, top_n: int = DEFAULT_TOP_N, as_of=None,
                       features_dir: Path | None = None, raw_dir: Path | None = None) -> ShortlistResult:
    """Resolve the market/date cross-section and rank the top-N shortlist (no writes)."""
    cross = resolve_market_cross(market, features_dir=features_dir, as_of=as_of)
    section = build_cross_section(cross, raw_dir=raw_dir)
    shortlist = rank_shortlist(section.frame, top_n, cross.scoring_date)
    return ShortlistResult(
        market=market, scoring_date=cross.scoring_date,
        shortlist=shortlist, cross_section=section, stale=cross.stale,
    )


def write_shortlist_csv(shortlist: pd.DataFrame, path: Path | str) -> Path:
    """Write the shortlist CSV (exact schema, no row index, full float precision)."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    shortlist.to_csv(out, index=False)
    return out


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def _positive_int(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("--top-n must be >= 1")
    return number


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    add_market_argument(parser)
    parser.add_argument("--top-n", type=_positive_int, default=DEFAULT_TOP_N,
                        help=f"How many names per market (default {DEFAULT_TOP_N}).")
    parser.add_argument("--date", default=None, metavar="YYYY-MM-DD",
                        help="Scoring date; default is the latest available feature date per market.")
    return parser


def run_one_market(market: str, args: argparse.Namespace) -> int:
    """Generate + write one market's shortlist CSV. Returns a process exit code."""
    try:
        result = generate_shortlist(market, top_n=args.top_n, as_of=args.date)
    except (FileNotFoundError, ValueError) as exc:
        print(f"[wi014_screener] {market}: {exc}", file=sys.stderr)
        return 1

    csv_path = write_shortlist_csv(result.shortlist, shortlist_csv_path(market, args.top_n))
    print(f"[wi014_screener] {market}: scoring_date={result.scoring_date.date()} "
          f"eligible={result.eligible_symbols} stale={result.cross_section.stale_symbols} "
          f"skipped={result.cross_section.skipped} rows={len(result.shortlist)}")
    print(f"[wi014_screener] {market}: {csv_path} ({csv_path.stat().st_size:,} bytes)")
    return 0


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    markets = cli_markets(args.market, prog="wi014_screener")
    if markets is None:
        return 2
    print(f"[wi014_screener] PLAN: markets={', '.join(markets)} "
          f"({'default BOTH, USD then CAD' if args.market is None else 'explicit --market'}); "
          f"top_n={args.top_n}; {RANKING_RULE}")

    return run_markets(markets, lambda market: run_one_market(market, args))


if __name__ == "__main__":
    raise SystemExit(main())
