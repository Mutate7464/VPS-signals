"""Shared market selection for the WI-015 pipeline.

The plan fixes the implicit both-market order for performance analytics at
**CAD then USD** (`--market {CAD,USD,BOTH}`, BOTH processes CAD first). That is
deliberately the opposite of `src.market_cli.BOTH` (`USD, CAD`), which stays as
is for the WI-013/WI-014 screener path. Validation is delegated to
`market_cli.normalize_market` so an invalid code is rejected before any write.
"""

from __future__ import annotations

from src.market_cli import MarketSelectionError, normalize_market

BOTH_ORDER: tuple[str, ...] = ("CAD", "USD")
_BOTH_ALIASES = frozenset({"BOTH", "ALL", "ANY"})

__all__ = ["BOTH_ORDER", "MarketSelectionError", "resolve_markets"]


def resolve_markets(value: str | None = None) -> list[str]:
    """Resolve `--market` to the ordered run list: CAD first on an implicit both."""
    if value is None:
        return list(BOTH_ORDER)
    raw = str(value).strip()
    if not raw or raw.upper() in _BOTH_ALIASES:
        return list(BOTH_ORDER)
    return [normalize_market(raw)]
