"""WI-018 shared streaming machinery: date blocks, cross-sectional state codes.

Both G1 (atlas) and G2 (probe) must bin features into states *identically*, or
the probe would test states the atlas never described. This module is the single
implementation of that binning:

* the USD universe's unique dates are read once (dates only) and split into
  contiguous blocks of `DATES_PER_BLOCK` dates — symbols are then visited
  sequentially per block, so no all-ticker uncompressed frame is ever held;
* per feature, per date, state edges are the **within-date USD cross-sectional
  quantiles** (nearest-rank on that date's finite values, no interpolation), so
  a state means "in the top quintile of this feature *relative to its peers that
  day*" — the frame WI-011/WI-016 used;
* a date with fewer names than the binning has bins produces no state at all for
  that feature/date (recorded as undefined, never imputed);
* ties go to the **upper** bin (`code = #{edges < value}`), deterministically;
* undefined (NaN/inf) feature values are excluded from every state.

State codes are packed into one `int8` code space: quintiles occupy 0..4 and
terciles 5..7, with -1 meaning undefined (see `N_STATES`).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from src.wi018 import BINNINGS, DATES_PER_BLOCK, DATE_COLUMN

__all__ = [
    "CLASSES",
    "N_STATES",
    "QUANTILES",
    "STATE_OFFSET",
    "classify_target",
    "date_blocks",
    "edges_from_sorted",
    "feature_columns",
    "feature_families",
    "global_dates",
    "group_sorted",
    "quantile_edges",
    "read_block_pairs",
    "schema_columns",
    "state_codes",
    "state_layout",
    "symbol_column",
]

CLASSES = ("up", "dn", "neither")
"""Target classes in accumulator order (+1 up-first, -1 down-first, 0 neither)."""

QUANTILES = {"quintile": (0.2, 0.4, 0.6, 0.8), "tercile": (1.0 / 3.0, 2.0 / 3.0)}
BINNING_ORDER = tuple(BINNINGS)
"""Fixed binning order for accumulator axes: `("quintile", "tercile")`."""


def binning_index(binning: str) -> int:
    """Position of `binning` in the accumulator axis order."""
    return BINNING_ORDER.index(binning)

STATE_OFFSET = {"quintile": 0, "tercile": 5}
N_STATES = 8
"""8 packed state codes: 0..4 quintile bins, 5..7 tercile bins, -1 undefined."""

SYMBOL_COLUMN = "_sym"


def symbol_column() -> str:
    """Name of the injected symbol-code column (int32, sorted-symbol index)."""
    return SYMBOL_COLUMN


# --------------------------------------------------------------------------- #
# Universe dates and blocks
# --------------------------------------------------------------------------- #
def global_dates(derived_dir: Path) -> np.ndarray:
    """Sorted union of every symbol's dates (`datetime64[ns]`), dates only."""
    dates: list[np.ndarray] = []
    for path in sorted(Path(derived_dir).glob("*.parquet")):
        col = pq.read_table(path, columns=[DATE_COLUMN])[DATE_COLUMN]
        dates.append(pd.to_datetime(col.to_pandas().to_numpy()).to_numpy().astype("datetime64[ns]"))
    if not dates:
        raise FileNotFoundError(f"no symbols under {derived_dir}")
    return np.unique(np.concatenate(dates))


def date_blocks(dates: np.ndarray, size: int = DATES_PER_BLOCK) -> list[dict]:
    """Contiguous blocks of the sorted date array: `{first, last, lo, hi, positions}`."""
    dates = np.asarray(dates)
    if dates.size == 0:
        raise ValueError("no dates to block")
    out = []
    for start in range(0, dates.size, size):
        stop = min(start + size, dates.size)
        out.append(
            {
                "first": start,
                "last": stop - 1,
                "lo": dates[start],
                "hi": dates[stop - 1],
                "positions": np.arange(start, stop),
            }
        )
    return out


def _read_one(path: Path, columns: list[str], lo, hi) -> pd.DataFrame:
    """One symbol's rows inside `[lo, hi]` (predicate pushdown, dates as ns)."""
    table = pq.read_table(
        path,
        columns=columns,
        filters=[(DATE_COLUMN, ">=", pd.Timestamp(lo).date()), (DATE_COLUMN, "<=", pd.Timestamp(hi).date())],
    )
    frame = table.to_pandas()
    if frame.empty:
        return frame
    frame[DATE_COLUMN] = pd.to_datetime(frame[DATE_COLUMN].to_numpy()).to_numpy().astype("datetime64[ns]")
    return frame


def read_block_pairs(
    derived_paths: dict[str, Path],
    feature_paths: dict[str, Path],
    feature_columns: list[str],
    target_columns: list[str],
    lo,
    hi,
) -> tuple[pd.DataFrame, pd.DataFrame] | None:
    """Aligned `(features, targets)` frames for one date block, symbols concatenated.

    Symbols are visited sequentially; feature and target frames come from the
    *same* per-symbol read, so row alignment can never depend on a join. The
    features frame carries an injected `_sym` code column (index into the sorted
    symbol list) for breadth diagnostics. Returns `None` when the block is empty.
    """
    features_parts: list[pd.DataFrame] = []
    target_parts: list[pd.DataFrame] = []
    for code, sym in enumerate(sorted(derived_paths)):
        feats = _read_one(feature_paths[sym], [DATE_COLUMN, *feature_columns], lo, hi)
        tgts = _read_one(derived_paths[sym], [DATE_COLUMN, *target_columns], lo, hi)
        if len(feats) != len(tgts):
            raise ValueError(
                f"{sym}: block row mismatch features={len(feats)} targets={len(tgts)} "
                "(preflight should have caught this)"
            )
        if feats.empty:
            continue
        feats = feats.copy()
        feats[SYMBOL_COLUMN] = np.int32(code)
        features_parts.append(feats)
        target_parts.append(tgts.reset_index(drop=True))
    if not features_parts:
        return None
    return (
        pd.concat(features_parts, ignore_index=True),
        pd.concat(target_parts, ignore_index=True),
    )


# --------------------------------------------------------------------------- #
# Feature schema helpers
# --------------------------------------------------------------------------- #
def schema_columns(path: Path) -> list[str]:
    """Feature columns (excluding `date`) from one parquet file's schema."""
    names = pq.ParquetFile(path).schema_arrow.names
    return [c for c in names if c != DATE_COLUMN]


def feature_columns(features_dir: Path) -> list[str]:
    """Feature columns (excluding `date`) from the first symbol's parquet schema."""
    for path in sorted(Path(features_dir).glob("*.parquet")):
        return schema_columns(path)
    raise FileNotFoundError(f"no symbols under {features_dir}")


def feature_families(columns) -> dict[str, list[str]]:
    """`{family: [columns]}` by stripping the trailing window suffix.

    WI-017 run-3 column names are `{family}_{window}`; the pruned grid keeps a
    handful of windows per family (sometimes exactly one, which is exactly why
    the atlas carries a target-representativeness check per flagged family).
    """
    out: dict[str, list[str]] = {}
    for col in columns:
        out.setdefault(col.rsplit("_", 1)[0], []).append(col)
    return {k: sorted(v) for k, v in sorted(out.items())}


def state_layout() -> list[tuple[str, int, int]]:
    """`(binning, bin_index_zero_based, code)` for every packed state, in order."""
    return [(binning, b, STATE_OFFSET[binning] + b) for binning, n in BINNINGS.items() for b in range(n)]


# --------------------------------------------------------------------------- #
# Cross-sectional state coding
# --------------------------------------------------------------------------- #
def group_sorted(values, date_pos, n_dates: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Finite values sorted within each date: `(xs, starts, sizes)`.

    `xs` is the concatenation of each date's finite values in ascending order,
    `starts[i]`/`sizes[i]` delimit date `i` inside `xs`. One sort serves every
    quantile set, so quintile and tercile edges share the same ordering.
    """
    v = np.asarray(values, dtype="float64")
    d = np.asarray(date_pos, dtype="int64")
    ok = np.isfinite(v) & (d >= 0)
    if not ok.any():
        return np.array([]), np.zeros(int(n_dates), dtype="int64"), np.zeros(int(n_dates), dtype="int64")
    x, g = v[ok], d[ok]
    order = np.lexsort((x, g))
    x, g = x[order], g[order]
    starts = np.searchsorted(g, np.arange(int(n_dates)), side="left")
    ends = np.searchsorted(g, np.arange(int(n_dates)), side="right")
    return x, starts, ends - starts


def edges_from_sorted(xs, starts, sizes, quantiles, min_names: int) -> np.ndarray:
    """Per-date nearest-rank edges from the sorted groups: `(n_dates, len(quantiles))`.

    Nearest rank (no interpolation) keeps an edge on a real observation, which is
    what makes tie handling deterministic. Dates with fewer than `min_names`
    finite values get NaN edges, so no state exists for them.
    """
    n_dates = int(np.asarray(sizes).size)
    edges = np.full((n_dates, len(quantiles)), np.nan)
    sizes = np.asarray(sizes)
    enough = sizes >= max(int(min_names), len(quantiles) + 1)
    if not enough.any():
        return edges
    for j, q in enumerate(quantiles):
        pos = np.asarray(starts) + np.maximum(np.ceil(q * sizes).astype("int64") - 1, 0)
        edges[enough, j] = np.asarray(xs)[pos[enough]]
    return edges


def quantile_edges(values, date_pos, n_dates: int, quantiles, min_names: int | None = None) -> np.ndarray:
    """Convenience wrapper: `edges_from_sorted(group_sorted(...))`."""
    xs, starts, sizes = group_sorted(values, date_pos, n_dates)
    return edges_from_sorted(xs, starts, sizes, quantiles, min_names or (len(quantiles) + 1))


def state_codes(values, edges: np.ndarray, date_pos, offset: int = 0) -> np.ndarray:
    """Packed `int8` state code per row (`-1` undefined).

    `code = offset + #{edges[date] < value}` — ties go to the upper bin — and a
    row is undefined when its value is non-finite or its date has no edges.
    """
    v = np.asarray(values, dtype="float64")
    pos = np.asarray(date_pos, dtype="int64")
    row_edges = np.full((v.size, edges.shape[1]), np.nan)
    mapped = pos >= 0
    row_edges[mapped] = edges[pos[mapped]]
    codes = (np.sum(v[:, None] > row_edges, axis=1) + int(offset)).astype("int8")
    undefined = ~np.isfinite(v) | np.isnan(row_edges).any(axis=1)
    codes[undefined] = -1
    return codes


def classify_target(target: np.ndarray) -> np.ndarray:
    """`int8` class per row: 0 up (+1), 1 down (-1), 2 neither (0), -1 unusable.

    Unusable means non-finite *or* a value outside the documented encoding — an
    unexpected value is never silently folded into "neither".
    """
    t = np.asarray(target, dtype="float64")
    out = np.full(t.shape, -1, dtype="int8")
    finite = np.isfinite(t)
    out[finite & (t == 1.0)] = 0
    out[finite & (t == -1.0)] = 1
    out[finite & (t == 0.0)] = 2
    return out
