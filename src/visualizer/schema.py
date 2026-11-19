"""Frozen schema contracts for the visualizer (WI-085).

RECORDED from metadata probes of the real artifacts on 2026-11-19 (no full scans);
they are not the plan's assumed 249-column panel:

- `features_{MKT}.parquet`: 92 columns = 89 float32 features + `date` (timestamp[ns]),
  `symbol`, `market`; USD 1,240,275 / CAD 701,599 rows, identical column set per market.
- `targets_{MKT}.parquet`: 8 columns, same row counts.
- `oof_{MKT}[_variant].parquet`: the canonical 41 columns. `oof_CAD.parquet` is an extended
  variant (41 + 16 `_pl3`/`_pl4` columns = 57); extras are recorded, never dropped.
- `l0_ext/{feature}_{MKT}.parquet`: USD 2,593,425 / CAD 1,401,504 rows, keys (`symbol`
  string, `date` date32); full universe, so it is a superset of the panel.
- `raw_ohlcv/...`: `date` date32 + 7 columns; dates monotonic.

`y_*` value sets, `p_*` ranges and fold dtypes are RECORDED from the artifact, not
hard-coded (D-028 open question: `_pl0/1/2` semantics, `y_*` value set).
"""
from __future__ import annotations

import re
from pathlib import Path

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

from src.visualizer import (
    MARKETS,
    feature_path,
    l0_ext_path,
    oof_path,
    raw_ohlcv_path,
    targets_path,
)

FEATURE_COLUMNS: tuple[str, ...] = tuple(
    "date symbol market rsi_5 rsi_14 rsi_21 rsi_14_slope_5 bb_pct_b_5 bb_width_5 bb_pct_b_10"
    " bb_width_10 bb_pct_b_20 bb_width_20 bb_pct_b_50 bb_width_50 bb_pct_b_100 bb_width_100"
    " macd_norm_line macd_norm_hist adx_5 di_spread_5 adx_10 di_spread_10 adx_20 di_spread_20"
    " adx_50 di_spread_50 adx_100 di_spread_100 atr_pct_5 atr_pct_10 atr_pct_20 atr_pct_50"
    " atr_pct_100 obv_zscore_5 obv_zscore_10 obv_zscore_20 obv_zscore_50 obv_zscore_100 hurst_20"
    " hurst_50 hurst_100 frac_diff_close entropy_10 entropy_20 kalman_spread_atr kama_er_5"
    " kama_er_10 kama_er_20 kama_er_50 kama_er_100 vwap_zscore_5 vwap_zscore_10 vwap_zscore_20"
    " vwap_zscore_50 vwap_zscore_100 amihud_5 amihud_10 amihud_20 amihud_50 amihud_100"
    " yangzhang_5 yangzhang_10 yangzhang_20 yangzhang_50 yangzhang_100 range_pos_f3"
    " range_width_f3 range_pos_f6 range_width_f6 donchian_break_f6 range_pos_f9 range_width_f9"
    " range_pos_f15 range_width_f15 donchian_break_f15 range_pos_f24 range_width_f24 range_pos_f39"
    " range_width_f39 range_pos_f63 range_width_f63 range_pos_f102 range_width_f102"
    " range_compression_f6_39 range_compression_f15_102 pct_from_high_f102 pct_from_low_f102"
    " fib_dist_f15 fib_dist_f39 fib_dist_f102 gap_z".split()
)
FEATURE_KEYS: tuple[str, ...] = FEATURE_COLUMNS[:3]
FEATURE_FLOAT_COLUMNS: tuple[str, ...] = FEATURE_COLUMNS[3:]
N_FEATURE_COLUMNS = 92
N_FEATURE_FLOAT32 = 89
PANEL_ROWS_MEASURED = {"USD": 1_240_275, "CAD": 701_599}

TARGET_COLUMNS: tuple[str, ...] = tuple(
    "date symbol market y_15d_high y_15d_low y_20d_up y_20d_down y_20d_stay".split()
)
TARGET_REQUIRED_COLUMNS: tuple[str, ...] = ("market", "y_20d_stay")
TARGET_ROWS_MEASURED = PANEL_ROWS_MEASURED

OOF_CANONICAL_COLUMNS: tuple[str, ...] = tuple(
    "date symbol close fwd_atr_ret_15 fwd_atr_ret_20 y_y_15d_high p_y_15d_high fold_y_15d_high"
    " y_y_15d_high_pl0 p_y_15d_high_pl0 y_y_15d_high_pl1 p_y_15d_high_pl1 y_y_15d_high_pl2"
    " p_y_15d_high_pl2 y_y_15d_low p_y_15d_low fold_y_15d_low y_y_15d_low_pl0 p_y_15d_low_pl0"
    " y_y_15d_low_pl1 p_y_15d_low_pl1 y_y_15d_low_pl2 p_y_15d_low_pl2 y_y_20d_up p_y_20d_up"
    " fold_y_20d_up y_y_20d_up_pl0 p_y_20d_up_pl0 y_y_20d_up_pl1 p_y_20d_up_pl1 y_y_20d_up_pl2"
    " p_y_20d_up_pl2 y_y_20d_down p_y_20d_down fold_y_20d_down y_y_20d_down_pl0 p_y_20d_down_pl0"
    " y_y_20d_down_pl1 p_y_20d_down_pl1 y_y_20d_down_pl2 p_y_20d_down_pl2".split()
)
OOF_CANONICAL_N = 41
OOF_KEY_COLUMNS: tuple[str, ...] = ("date", "symbol", "close")
OOF_FWD_COLUMNS: tuple[str, ...] = ("fwd_atr_ret_15", "fwd_atr_ret_20")
OOF_TARGETS: tuple[str, ...] = ("y_15d_high", "y_15d_low", "y_20d_up", "y_20d_down")
#: Extra columns are only legal as additional barrier variants of y_/p_/fold_.
OOF_VARIANT_RE = re.compile(r"^(?:y|p|fold)_.*_pl\d+$")
OOF_ROWS_MEASURED = {"USD": 1_240_275, "CAD": 1_400}

L0_EXT_COLUMNS: dict[str, tuple[str, ...]] = {
    "nr_flags": ("symbol", "date", "nr4", "nr7"),
    "cusum_flag": ("symbol", "date", "cusum_flag", "cusum_stat"),
    "clv": ("symbol", "date", "clv", "clv_ma14"),
    "stoch_rsi": ("symbol", "date", "stochrsi_14_14"),
    "connors_rsi": ("symbol", "date", "connors_rsi"),
    "fail_count": ("symbol", "date", "fail_count_20"),
}
L0_EXT_FLOAT_COLUMNS: dict[str, tuple[str, ...]] = {
    "nr_flags": ("nr4", "nr7"),
    "cusum_flag": ("cusum_stat",),
    "clv": ("clv", "clv_ma14"),
    "stoch_rsi": ("stochrsi_14_14",),
    "connors_rsi": ("connors_rsi",),
    "fail_count": (),
}
L0_EXT_ROWS_MEASURED = {"USD": 2_593_425, "CAD": 1_401_504}
L0_EXT_KEY_UNIQUE_CHECK = "nr_flags"

RAW_OHLCV_COLUMNS: tuple[str, ...] = (
    "date", "open", "high", "low", "close", "volume", "average", "barCount",
)
RAW_OHLCV_FLOAT_COLUMNS: tuple[str, ...] = RAW_OHLCV_COLUMNS[1:-1]
SAMPLE_OHLCV_PER_MARKET = 5  # 5 USD + 5 CAD = the 10 sampled OHLCV files


class SchemaError(AssertionError):
    """A real artifact deviates from the frozen WI-085 schema contract."""


# Guard against typos in the frozen literal counts (measured 2026-11-19).
if len(FEATURE_COLUMNS) != N_FEATURE_COLUMNS or len(FEATURE_FLOAT_COLUMNS) != N_FEATURE_FLOAT32:
    raise SchemaError("feature contract literals disagree with the frozen column tuple")
if len(OOF_CANONICAL_COLUMNS) != OOF_CANONICAL_N:
    raise SchemaError("OOF contract literals disagree with the frozen column tuple")


def _schema(path: Path) -> pa.Schema:
    return pq.ParquetFile(path).schema_arrow


def _rows(path: Path) -> int:
    return pq.ParquetFile(path).metadata.num_rows


def _duplicate_key_rows(path: Path, keys: tuple[str, ...] = ("symbol", "date")) -> int:
    """Count duplicate (symbol, date) rows using a projected, dictionary-encoded read."""
    table = pq.read_table(path, columns=list(keys)).combine_chunks()
    cols = []
    for name in keys:
        col = table.column(name)
        if pa.types.is_string(col.type) or pa.types.is_large_string(col.type):
            col = pc.dictionary_encode(col)
        cols.append(col)
    frame = pa.table(dict(zip(keys, cols))).to_pandas()
    return int(frame.duplicated(subset=list(keys)).sum())


def sampled_ohlcv_paths(per_market: int = SAMPLE_OHLCV_PER_MARKET) -> list[tuple[str, str, Path]]:
    """Deterministic 10-file OHLCV sample: first `per_market` sorted symbols per market."""
    out: list[tuple[str, str, Path]] = []
    for market in MARKETS:
        market_dir = raw_ohlcv_path(market, "X").parent
        symbols = sorted(p.stem.replace("symbol=", "") for p in market_dir.glob("symbol=*.parquet"))
        out.extend((market, symbol, raw_ohlcv_path(market, symbol)) for symbol in symbols[:per_market])
    return out


def assert_features_schema(path: Path | str, market: str | None = None) -> dict:
    path = Path(path)
    sch = _schema(path)
    columns = tuple(sch.names)
    if columns != FEATURE_COLUMNS:
        missing = [c for c in FEATURE_COLUMNS if c not in columns]
        extra = [c for c in columns if c not in FEATURE_COLUMNS]
        raise SchemaError(
            f"{path.name}: feature column set != measured {N_FEATURE_COLUMNS}-column contract "
            f"(missing={missing[:5]}, unexpected={extra[:5]}, got {len(columns)} cols)"
        )
    floats = [name for name, typ in zip(columns, sch.types) if typ == pa.float32()]
    if len(floats) != N_FEATURE_FLOAT32:
        raise SchemaError(f"{path.name}: expected {N_FEATURE_FLOAT32} float32 features, got {len(floats)}")
    date_type = sch.field("date").type
    if not pa.types.is_timestamp(date_type):
        raise SchemaError(f"{path.name}: date is {date_type}, expected a timestamp (panel key)")
    duplicates = _duplicate_key_rows(path)
    if duplicates:
        raise SchemaError(f"{path.name}: (symbol, date) not unique ({duplicates} duplicate rows)")
    rows = _rows(path)
    return {
        "path": str(path),
        "market": market or path.stem.rsplit("_", 1)[-1],
        "rows": rows,
        "columns": len(columns),
        "float32_columns": len(floats),
        "keys": list(FEATURE_KEYS),
        "date_type": str(date_type),
        "key_duplicate_rows": duplicates,
        "rows_measured_2026_11_19": PANEL_ROWS_MEASURED.get((market or "").upper()),
    }


def assert_targets_schema(path: Path | str, market: str | None = None) -> dict:
    path = Path(path)
    sch = _schema(path)
    columns = tuple(sch.names)
    if columns != TARGET_COLUMNS:
        raise SchemaError(f"{path.name}: target columns {columns} != {TARGET_COLUMNS}")
    missing = [c for c in TARGET_REQUIRED_COLUMNS if c not in columns]
    if missing:
        raise SchemaError(f"{path.name}: missing required target columns {missing}")
    duplicates = _duplicate_key_rows(path)
    if duplicates:
        raise SchemaError(f"{path.name}: (symbol, date) not unique ({duplicates} duplicate rows)")
    return {
        "path": str(path),
        "market": market or path.stem.rsplit("_", 1)[-1],
        "rows": _rows(path),
        "columns": len(columns),
        "required_present": list(TARGET_REQUIRED_COLUMNS),
        "key_duplicate_rows": duplicates,
    }


def assert_oof_schema(path: Path | str, market: str | None = None) -> dict:
    path = Path(path)
    sch = _schema(path)
    columns = tuple(sch.names)
    missing = [c for c in OOF_CANONICAL_COLUMNS if c not in columns]
    if missing:
        raise SchemaError(f"{path.name}: missing canonical OOF columns {missing[:5]}")
    extras = [c for c in columns if c not in OOF_CANONICAL_COLUMNS]
    illegal = [c for c in extras if not OOF_VARIANT_RE.match(c)]
    if illegal:
        raise SchemaError(f"{path.name}: unexpected non-variant OOF columns {illegal[:5]}")

    p_cols = [c for c in columns if c.startswith("p_")]
    y_cols = [c for c in columns if c.startswith("y_")]
    fold_cols = [c for c in columns if c.startswith("fold_")]
    table = pq.read_table(path, columns=p_cols + y_cols + fold_cols).combine_chunks()

    p_ranges: dict[str, list[float | None]] = {}
    for name in p_cols:
        col = pc.drop_null(table.column(name))
        if len(col) == 0:
            p_ranges[name] = [None, None]
            continue
        mm = pc.min_max(col).as_py()
        lo, hi = float(mm["min"]), float(mm["max"])
        if lo < 0.0 or hi > 1.0:
            raise SchemaError(f"{path.name}: {name} outside [0, 1] ({lo} .. {hi})")
        p_ranges[name] = [lo, hi]

    fold_types: dict[str, str] = {}
    for name in fold_cols:
        typ = table.schema.field(name).type
        if not pa.types.is_integer(typ):
            raise SchemaError(f"{path.name}: {name} is {typ}, expected an integer fold id")
        fold_types[name] = str(typ)

    y_value_sets = {name: sorted(pc.unique(table.column(name)).to_pylist()) for name in y_cols}
    return {
        "path": str(path),
        "market": market or path.stem.rsplit("_", 1)[-1],
        "rows": _rows(path),
        "columns": len(columns),
        "canonical_columns": len(OOF_CANONICAL_COLUMNS),
        "variant_extra_columns": extras,
        "p_ranges": p_ranges,
        "fold_types": fold_types,
        "y_value_sets": y_value_sets,
        "rows_measured_2026_11_19": OOF_ROWS_MEASURED.get((market or "").upper()),
    }


def assert_l0_ext_schema(path: Path | str, feature: str, market: str, check_keys: bool = False) -> dict:
    path = Path(path)
    expected = L0_EXT_COLUMNS[feature]
    sch = _schema(path)
    columns = tuple(sch.names)
    if columns != expected:
        raise SchemaError(f"{path.name}: columns {columns} != measured {expected}")
    if not pa.types.is_date32(sch.field("date").type):
        raise SchemaError(f"{path.name}: date is {sch.field('date').type}, expected date32[day]")
    for name in L0_EXT_FLOAT_COLUMNS[feature]:
        if sch.field(name).type != pa.float32():
            raise SchemaError(f"{path.name}: {name} is {sch.field(name).type}, expected float32")
    rows = _rows(path)
    expected_rows = L0_EXT_ROWS_MEASURED[market.upper()]
    if rows != expected_rows:
        raise SchemaError(
            f"{path.name}: {rows} rows != measured {expected_rows} (2026-11-19); "
            "re-record L0_EXT_ROWS_MEASURED if the artifact was regenerated"
        )
    duplicates = _duplicate_key_rows(path) if check_keys else None
    if duplicates:
        raise SchemaError(f"{path.name}: (symbol, date) not unique ({duplicates} duplicate rows)")
    return {
        "path": str(path),
        "feature": feature,
        "market": market.upper(),
        "rows": rows,
        "columns": list(columns),
        "date_type": str(sch.field("date").type),
        "key_duplicate_rows": duplicates,
    }


def assert_raw_ohlcv_schema(path: Path | str) -> dict:
    path = Path(path)
    sch = _schema(path)
    columns = tuple(sch.names)
    if columns != RAW_OHLCV_COLUMNS:
        raise SchemaError(f"{path.name}: columns {columns} != {RAW_OHLCV_COLUMNS}")
    if not pa.types.is_date32(sch.field("date").type):
        raise SchemaError(f"{path.name}: date is {sch.field('date').type}, expected date32[day]")
    for name in RAW_OHLCV_FLOAT_COLUMNS:
        if sch.field(name).type != pa.float32():
            raise SchemaError(f"{path.name}: {name} is {sch.field(name).type}, expected float32")
    if not pa.types.is_int64(sch.field("barCount").type):
        raise SchemaError(f"{path.name}: barCount is {sch.field('barCount').type}, expected int64")
    dates = pq.read_table(path, columns=["date"]).column("date").combine_chunks()
    days = pc.cast(dates, pa.int32()).to_numpy()
    if len(days) > 1 and not bool((days[1:] > days[:-1]).all()):
        raise SchemaError(f"{path.name}: dates are not strictly monotonic")
    return {
        "path": str(path),
        "rows": _rows(path),
        "columns": list(columns),
        "date_type": str(sch.field("date").type),
        "dates_monotonic": True,
    }


def assert_all_artifacts(markets: tuple[str, ...] = MARKETS, ohlcv_sample: int = SAMPLE_OHLCV_PER_MARKET) -> dict:
    """Run every startup contract on the real artifacts. Raises `SchemaError` on drift."""
    report: dict = {"markets": {}, "l0_ext": {}, "raw_ohlcv": []}
    for market in markets:
        market_key = market.upper()
        report["markets"][market_key] = {
            "features": assert_features_schema(feature_path(market), market_key),
            "targets": assert_targets_schema(targets_path(market), market_key),
            "oof": assert_oof_schema(oof_path(market), market_key),
        }
        for feature in L0_EXT_COLUMNS:
            key = f"{feature}_{market_key}"
            report["l0_ext"][key] = assert_l0_ext_schema(
                l0_ext_path(feature, market), feature, market_key,
                check_keys=(feature == L0_EXT_KEY_UNIQUE_CHECK),
            )
    for market, symbol, path in sampled_ohlcv_paths(ohlcv_sample):
        entry = assert_raw_ohlcv_schema(path)
        entry.update({"market": market, "symbol": symbol})
        report["raw_ohlcv"].append(entry)
    return report
