"""WI-013 — shared market selection and market-suffixed output routing.

Why this module exists
---------------------
Before WI-013 every stage script hard-coded a single market (`MARKET = "CAD"`
in `src/wi011`, `--market` defaults of `"CAD"`) *and* a market-less report path
(`reports/wi011_preflight.md`, `reports/wi009c_summary.md`, ...). Two problems
followed: a USD run needed temporary source patches, and a CAD run silently
overwrote the frozen gate reports (WI-012 finding F-5).

This module is the one place that decides:

1. **Which markets run.** Omitting `--market` means *both*, in the fixed order
   USD then CAD (admin amendment 2026-10-26). An explicit `--market USD|CAD`
   selects exactly that one. Anything else is rejected *before* any work runs —
   these scripts must never write on invalid input.
2. **Where output goes.** Every output path is market-suffixed
   (`reports/wi011_preflight_CAD.md`, `logs/wi009b_train_USD.pid`, ...). Existing
   unsuffixed files are frozen gate records and are never a writable target.

The suffix helpers are idempotent (suffixing an already-suffixed path is a
no-op) and refuse a path that names a *different* market than the run
(`wi009c_probe_CAD.md` during a USD run is an error, not a rename), so a
`--out`/`--report` override can never smuggle an unsuffixed or cross-market
write past the guard.

Usage in a stage script::

    ap.add_argument("--market", default=None)
    ...
    markets = resolve_markets(args.market)          # ["USD", "CAD"] by default
    rc = run_markets(markets, lambda m: run_one(m, args))

    out = resolve_output(args.out, market, what="--out") if args.out else report_path(REPORTS, "wi009c_probe", market)
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable, Iterable
from pathlib import Path

__all__ = [
    "BOTH",
    "MARKET_CHOICES",
    "MarketSelectionError",
    "add_market_argument",
    "cli_markets",
    "is_market_suffixed",
    "market_suffix",
    "normalize_market",
    "report_path",
    "resolve_markets",
    "resolve_output",
    "run_markets",
    "suffix_path",
]

MARKET_CHOICES: tuple[str, ...] = ("USD", "CAD")
"""The only accepted explicit market codes."""

BOTH: tuple[str, ...] = ("USD", "CAD")
"""Default market selection order for an implicit "both" run: USD, then CAD."""

_BOTH_ALIASES: frozenset[str] = frozenset({"BOTH", "ALL", "ANY"})


class MarketSelectionError(ValueError):
    """Raised for an unknown market or a cross-market output override."""


def normalize_market(value: str) -> str:
    """Return the canonical upper-case market code, or raise `MarketSelectionError`."""
    if not isinstance(value, str):
        raise MarketSelectionError(f"market must be a string, got {type(value).__name__}")
    code = value.strip().upper()
    if code in MARKET_CHOICES:
        return code
    raise MarketSelectionError(
        f"invalid market {value!r}: choose {'/'.join(MARKET_CHOICES)}, or omit --market to run both "
        f"({' then '.join(BOTH)})"
    )


def resolve_markets(value: str | None = None) -> list[str]:
    """Resolve `--market` into the ordered list of markets to run.

    Args:
        value: the raw `--market` value; `None`/empty/`BOTH`/`ALL` mean both.

    Returns:
        `["USD", "CAD"]` for an implicit both-market run, else the single market.

    Raises:
        MarketSelectionError: on any value that is neither empty, a both-alias,
            nor a valid market code.
    """
    if value is None:
        return list(BOTH)
    raw = str(value).strip()
    if not raw or raw.upper() in _BOTH_ALIASES:
        return list(BOTH)
    return [normalize_market(raw)]


def add_market_argument(parser: argparse.ArgumentParser) -> None:
    """Add the standard `--market` flag (no `choices=`, so both-market default works)."""
    parser.add_argument(
        "--market",
        default=None,
        metavar="USD|CAD",
        help="Run one market only. Omit to run both, USD then CAD (default).",
    )


def cli_markets(value: str | None, *, prog: str = "script") -> list[str] | None:
    """`resolve_markets` for `main()`: print the error and return `None` on bad input.

    Returning `None` (rather than raising) lets every stage script fail *before*
    writing anything, with a non-zero exit code.
    """
    try:
        return resolve_markets(value)
    except MarketSelectionError as exc:
        print(f"[{prog}] {exc}", file=sys.stderr)
        return None


def market_suffix(market: str) -> str:
    """`"_CAD"` for `"cad"` — the canonical, validated market suffix."""
    return f"_{normalize_market(market)}"


def _stem_market(path: Path) -> str | None:
    """The market code a path's stem already ends with, or `None`."""
    tail = path.stem.upper().rsplit("_", 1)[-1]
    return tail if tail in MARKET_CHOICES else None


def is_market_suffixed(path: Path | str, market: str) -> bool:
    """True when `path`'s stem already carries this market's suffix."""
    return _stem_market(Path(path)) == normalize_market(market)


def suffix_path(path: Path | str, market: str) -> Path:
    """Insert the market suffix before the file suffix (idempotent).

    Raises:
        MarketSelectionError: when the path already names a *different* market.
    """
    p = Path(path)
    code = normalize_market(market)
    found = _stem_market(p)
    if found is not None:
        if found != code:
            raise MarketSelectionError(
                f"{p} is suffixed for {found}, but this run is {code} — refusing a cross-market write"
            )
        return p
    return p.with_name(f"{p.stem}_{code}{p.suffix}")


def resolve_output(path: Path | str, market: str, *, what: str = "output path") -> Path:
    """Route an explicit output override to a market-suffixed path.

    An override that is already suffixed for this market is kept as given; an
    unsuffixed override gets the suffix; an override naming another market is
    rejected before anything is written.
    """
    try:
        return suffix_path(path, market)
    except MarketSelectionError as exc:
        raise MarketSelectionError(f"{what}: {exc}") from None


def report_path(reports_dir: Path | str, stem: str, market: str, suffix: str = ".md") -> Path:
    """The canonical market-suffixed report path for a run.

    `report_path("reports", "wi011_preflight", "CAD")` →
    `reports/wi011_preflight_CAD.md`. A stem that already carries a market code
    is rejected rather than double-suffixed.
    """
    code = normalize_market(market)
    if _stem_market(Path(f"{stem}{suffix}")) is not None:
        raise MarketSelectionError(f"report stem {stem!r} already carries a market suffix")
    return Path(reports_dir) / f"{stem}_{code}{suffix}"


def run_markets(markets: Iterable[str], run_one: Callable[[str], int]) -> int:
    """Run `run_one(market)` for each market in order; return the first non-zero code.

    Every market in the selection is attempted (the markets are independent), and
    the selection order is preserved — USD before CAD for an implicit both run.
    """
    rc = 0
    for market in markets:
        result = int(run_one(market))
        if result and not rc:
            rc = result
    return rc
