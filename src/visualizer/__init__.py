"""Visualizer / audit workbench package (WI-085, Phase 0 scaffold).

Read-only over `data/`; the only writable location is `state/viz/`.
This module is deliberately dependency-free (stdlib only) so that `schema.py`
and `loader.py` can both import the path contract without a cycle.

Measured artifacts (2026-11-19 metadata probes):
- `data/features/features_{MKT}.parquet`     92 cols (89 float32 + date/symbol/market)
- `data/features/targets_{MKT}.parquet`      8 cols
- `data/oof_{MKT}[_variant].parquet`         41 canonical cols
- `data/features/l0_ext/{feature}_{MKT}.parquet`  keys (symbol, date date32)
- `data/raw_ohlcv/market={MKT}/symbol={T}.parquet`  date32 + 7 cols
"""
from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
RAW_OHLCV_DIR = DATA_DIR / "raw_ohlcv"
FEATURES_DIR = DATA_DIR / "features"
L0_EXT_DIR = FEATURES_DIR / "l0_ext"

MARKETS: tuple[str, ...] = ("USD", "CAD")

#: The ONLY writable location for the UI process (override in tests via VIZ_STATE_DIR).
STATE_DIR = Path(os.environ.get("VIZ_STATE_DIR", str(REPO_ROOT / "state" / "viz")))

#: Resident-column budget for the UI process (plan 26-W47: 3.0 GB).
DEFAULT_BUDGET_BYTES = 3 * 1024**3
#: LRU sizes (plan 26-W47 memory caps).
COLUMN_LRU_SIZE = 64
OHLCV_LRU_SIZE = 32
#: Repo law: never -1.
N_JOBS = 2

L0_EXT_FEATURES: tuple[str, ...] = (
    "nr_flags",
    "cusum_flag",
    "clv",
    "stoch_rsi",
    "connors_rsi",
    "fail_count",
)


def feature_path(market: str) -> Path:
    return FEATURES_DIR / f"features_{market.upper()}.parquet"


def targets_path(market: str) -> Path:
    return FEATURES_DIR / f"targets_{market.upper()}.parquet"


def oof_path(market: str, variant: str | None = None) -> Path:
    suffix = f"_{variant}" if variant else ""
    return DATA_DIR / f"oof_{market.upper()}{suffix}.parquet"


def l0_ext_path(feature: str, market: str) -> Path:
    return L0_EXT_DIR / f"{feature}_{market.upper()}.parquet"


def raw_ohlcv_path(market: str, symbol: str) -> Path:
    return RAW_OHLCV_DIR / f"market={market.upper()}" / f"symbol={symbol}.parquet"


def state_path(name: str, base: Path | str | None = None) -> Path:
    """Resolve a state file name under `state/viz/` (flat names only)."""
    if not name or "/" in name or "\\" in name or name in {".", ".."}:
        raise ValueError(f"state file name must be a flat file name: {name!r}")
    return Path(base) / name if base is not None else STATE_DIR / name
