"""Training-panel loading for the WI-009b contrastive run.

Two jobs:

1. **Slim read.** The trainer only needs identifiers + feature columns, so the
   Arrow scan is handed an explicit column list instead of materialising every
   column of the parquet. The keep list is *inclusive*: anything that is not an
   identifier, a label, or a namespaced E5 column is a model feature.
2. **Mask guard (E3 bug class).** `tests/test_feature_masks.py` regression-locks
   the 2026-10-23 bug where the trainer's memory-slim `keep_cols` silently
   dropped every `_cs_pct` column, so five feature-set masks resolved to zero
   features ("no valid features" on every target). Here the same failure mode is
   prevented by census: every derived cluster present in the source schema must
   survive the keep list, and the feature count must be unchanged, or the load
   raises before any training happens.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.feature_engine import FIB_FEATURE_NAMES

__all__ = [
    "ID_COLUMNS",
    "LABEL_COLUMNS",
    "E5_PREFIX",
    "keep_columns",
    "feature_columns",
    "feature_census",
    "load_feature_panel",
    "schema_column_names",
]

ID_COLUMNS = ("date", "symbol", "market")
LABEL_COLUMNS = ("fwd_atr_ret_15", "fwd_atr_ret_20")
E5_PREFIX = "e5_"

BASE_DIR = Path(__file__).resolve().parents[2]
FEATURES_DIR = BASE_DIR / "data" / "features"

_FIB_SET = frozenset(FIB_FEATURE_NAMES)


def schema_column_names(path: str | Path) -> list[str]:
    """Read only the parquet schema (no data) and return the column names."""
    import pyarrow.parquet as pq

    pf = pq.ParquetFile(str(path))
    return [f.name for f in pf.schema_arrow]


def feature_columns(schema_names) -> list[str]:
    """Everything that is not an identifier, a label, or an E5 factor column."""
    return [
        str(c)
        for c in schema_names
        if c not in ID_COLUMNS
        and c not in LABEL_COLUMNS
        and not str(c).startswith(E5_PREFIX)
    ]


def feature_census(names) -> dict[str, int]:
    """Count features per family present in the given column list.

    Counted **directly from the list**, deliberately *not* through
    `feature_columns`: if the census reused the keep rule, a selective keep rule
    would hide the very family it dropped and the `keep_columns` guard below
    could never fire (a tautology — caught in review of this work item).

    `range_fib` = the range/Donchian/fibonacci expansion, `cs_pct` = the
    date-grouped cross-sectional percentile ranks (the family the E3 slim mask
    dropped), `classic` = the remaining indicator columns.
    """
    counts = {"classic": 0, "range_fib": 0, "cs_pct": 0}
    for c in names:
        c = str(c)
        if c in ID_COLUMNS or c in LABEL_COLUMNS or c.startswith(E5_PREFIX):
            continue
        if c in _FIB_SET:
            counts["range_fib"] += 1
        elif c.endswith("_cs_pct"):
            counts["cs_pct"] += 1
        else:
            counts["classic"] += 1
    return counts


def keep_columns(schema_names) -> list[str]:
    """Slim keep list = identifiers + all feature columns, with census guards.

    Raises:
        ValueError: if no features are found, or a feature family that exists in
            the source schema would be dropped by the keep list (the E3 slim-mask
            bug class), or the kept feature count differs from the source's.
    """
    names = [str(c) for c in schema_names]
    ids = [c for c in names if c in ID_COLUMNS]
    feats = feature_columns(names)
    if not feats:
        raise ValueError(f"no feature columns found in schema ({len(names)} columns)")
    if not {"date", "symbol"} <= set(ids):
        raise ValueError(f"schema is missing date/symbol identifiers: {ids}")

    keep = ids + feats
    # Compare the feature census of the SOURCE schema against the census of the
    # keep list. This is the real guard for the E3 bug class: if any future edit
    # makes `feature_columns` selective (a whitelist that forgets `_cs_pct` or
    # the range/fib expansion), the two censuses diverge and the load refuses.
    src_census = feature_census(names)
    keep_census = feature_census(keep)
    if keep_census != src_census:
        raise ValueError(
            f"keep list changes the feature census: source={src_census} keep={keep_census} "
            "— a derived column family would be silently dropped (E3 bug class)"
        )
    return keep


def load_feature_panel(
    market: str,
    start: str | None = None,
    end: str | None = None,
    path: str | Path | None = None,
) -> tuple[pd.DataFrame, list[str], dict[str, int]]:
    """Arrow-scan the feature panel over a date window, reading only keep columns.

    Returns:
        (panel, feature_columns, census). `date` is normalised to day precision.
    """
    import pyarrow.dataset as ds

    path = Path(path) if path is not None else FEATURES_DIR / f"features_{market}.parquet"
    if not path.exists():
        raise SystemExit(f"missing {path} — run the feature_engine rebuild first")

    keep = keep_columns(schema_column_names(path))
    feats = feature_columns(keep)
    census = feature_census(keep)

    dataset = ds.dataset(str(path), format="parquet")
    filt = None
    if start is not None:
        filt = ds.field("date") >= pd.Timestamp(start)
    if end is not None:
        end_f = ds.field("date") <= pd.Timestamp(end)
        filt = end_f if filt is None else (filt & end_f)

    tbl = dataset.to_table(columns=keep, filter=filt)
    df = tbl.to_pandas()
    df["date"] = pd.to_datetime(df["date"]).dt.normalize()
    for c in feats:
        if df[c].dtype != np.float32:
            df[c] = df[c].astype("float32")
    return df, feats, census