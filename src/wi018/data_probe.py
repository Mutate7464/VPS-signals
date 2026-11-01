"""WI-018 step 1 — preflight of the frozen WI-017 USD inputs.

Why this module exists
----------------------
Every later WI-018 stage streams `reports/wi017/derived/<SYM>.parquet` and
`reports/wi017/features/<SYM>.parquet`. Before a single rate is measured, the
inputs must be proven to be what the plan says they are: 593 USD symbols present
in **both** directories, nonempty frames, per-symbol target/feature row *and*
date alignment, the primary target `first_touch_34` plus the two secondary
robustness targets, all 88 `keep_columns` of the run-5 prune list present, and a
264-column feature grid. The target inventory is *reported*, never assumed: the
observed value domain is recorded as-is and any value outside the documented
`{+1, 0, -1}` encoding is flagged informationally (not silently coerced).

Nothing downstream may write a study artifact before this probe passes:
`require_preflight()` is the gate every later stage calls first, and
`reports/wi018/preflight_USD.json` is the record it reads.

Bounded memory: symbols are visited sequentially, one symbol frame at a time.

CLI::

    python -m src.wi018.data_probe --market USD --assert-inputs
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from src.wi018 import (
    DATE_COLUMN,
    DERIVED_DIR,
    EXPECTED_FEATURE_COLUMNS,
    EXPECTED_USD_SYMBOLS,
    FEATURES_DIR,
    MARKET,
    PREFLIGHT_JSON,
    PRIMARY_TARGET,
    PRUNE_RECS,
    REPORTS_DIR,
    SECONDARY_TARGETS,
    TARGET_VALUES,
)

__all__ = [
    "PreflightError",
    "load_keep_columns",
    "main",
    "probe_symbol",
    "require_preflight",
    "run_preflight",
    "symbol_paths",
    "write_report",
]

TARGET_COLUMNS = (PRIMARY_TARGET, *SECONDARY_TARGETS)


class PreflightError(ValueError):
    """An on-disk input violates a WI-018 preflight contract."""


# --------------------------------------------------------------------------- #
# Input discovery
# --------------------------------------------------------------------------- #
def symbol_paths(directory: Path) -> dict[str, Path]:
    """`{symbol: path}` for every `*.parquet` in `directory` (sorted, deterministic)."""
    directory = Path(directory)
    if not directory.is_dir():
        raise PreflightError(f"input directory missing: {directory}")
    out = {p.stem: p for p in sorted(directory.glob("*.parquet"))}
    if not out:
        raise PreflightError(f"no *.parquet inputs under {directory}")
    return out


def load_keep_columns(path: Path = PRUNE_RECS) -> list[str]:
    """The 88 run-5 `keep_columns`, validated for shape before any use."""
    path = Path(path)
    if not path.is_file():
        raise PreflightError(f"prune list missing: {path}")
    try:
        payload = json.loads(path.read_text())
    except (OSError, ValueError) as exc:  # malformed JSON / unreadable
        raise PreflightError(f"prune list unreadable: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise PreflightError(f"prune list must be a JSON object, got {type(payload).__name__}")
    keep = payload.get("keep_columns")
    if not isinstance(keep, list) or not keep:
        raise PreflightError("prune list needs a nonempty 'keep_columns' list")
    if not all(isinstance(c, str) and c for c in keep):
        raise PreflightError("'keep_columns' must contain nonempty strings")
    if len(set(keep)) != len(keep):
        raise PreflightError("'keep_columns' contains duplicates")
    n_keep = payload.get("n_keep")
    if n_keep is not None and int(n_keep) != len(keep):
        raise PreflightError(f"n_keep={n_keep} disagrees with {len(keep)} keep_columns")
    return list(keep)


def _as_dates(values) -> np.ndarray:
    """Parquet restores `date` as `date32` (python `date` objects); force ns."""
    return pd.to_datetime(pd.Series(values).to_numpy()).to_numpy().astype("datetime64[ns]")


def _value_inventory(values: pd.Series) -> dict:
    """Observed value -> count, stringified keys, NaN folded to `null` (no assumptions)."""
    counts = pd.Series(values).value_counts(dropna=False)
    out: dict[str, int] = {}
    for value, n in counts.items():
        if value is None or (isinstance(value, float) and np.isnan(value)):
            key = "null"
        else:
            key = repr(float(value))
        out[key] = int(n)
    return dict(sorted(out.items()))


# --------------------------------------------------------------------------- #
# Per-symbol probe
# --------------------------------------------------------------------------- #
def probe_symbol(
    symbol: str,
    derived_path: Path,
    features_path: Path,
    keep_columns: list[str],
    expected_feature_columns: int = EXPECTED_FEATURE_COLUMNS,
) -> dict:
    """Validate one symbol's derived/feature pair; raise `PreflightError` on a breach.

    Checks, in order: both files readable and nonempty; `date` present in both;
    primary + secondary targets present; the feature grid has exactly
    `expected_feature_columns` columns (excluding `date`) and contains every
    `keep_columns` entry; equal row counts; elementwise-identical dates; unique
    dates. Returns the observed row counts, date bounds, null/finite counts and
    the target value inventory.
    """
    feature_schema = pq.ParquetFile(features_path).schema_arrow.names
    derived_schema = pq.ParquetFile(derived_path).schema_arrow.names
    for label, names in ((symbol + " features", feature_schema), (symbol + " derived", derived_schema)):
        if DATE_COLUMN not in names:
            raise PreflightError(f"{label}: missing '{DATE_COLUMN}' column")
    missing_targets = [c for c in TARGET_COLUMNS if c not in derived_schema]
    if missing_targets:
        raise PreflightError(f"{symbol} derived: missing target columns {missing_targets}")
    feature_columns = [c for c in feature_schema if c != DATE_COLUMN]
    if len(feature_columns) != expected_feature_columns:
        raise PreflightError(
            f"{symbol} features: {len(feature_columns)} feature columns, "
            f"expected {expected_feature_columns}"
        )
    missing_keep = [c for c in keep_columns if c not in feature_schema]
    if missing_keep:
        raise PreflightError(f"{symbol} features: {len(missing_keep)} keep_columns absent, e.g. {missing_keep[:3]}")

    derived = pq.read_table(derived_path, columns=[DATE_COLUMN, *TARGET_COLUMNS]).to_pandas()
    features = pq.read_table(features_path, columns=[DATE_COLUMN, *keep_columns]).to_pandas()
    if len(derived) == 0 or len(features) == 0:
        raise PreflightError(f"{symbol}: empty input (derived={len(derived)}, features={len(features)})")
    if len(derived) != len(features):
        raise PreflightError(f"{symbol}: row mismatch derived={len(derived)} features={len(features)}")

    d_dates = _as_dates(derived[DATE_COLUMN])
    f_dates = _as_dates(features[DATE_COLUMN])
    if d_dates.size != f_dates.size or not np.array_equal(d_dates, f_dates):
        raise PreflightError(f"{symbol}: feature/target dates are not aligned")
    if np.unique(d_dates).size != d_dates.size:
        raise PreflightError(f"{symbol}: duplicate dates in the input frames")

    target_stats: dict[str, dict] = {}
    for col in TARGET_COLUMNS:
        values = derived[col].astype("float64")
        finite = np.isfinite(values.to_numpy())
        target_stats[col] = {
            "finite": int(finite.sum()),
            "null": int((~finite).sum()),
            "finite_fraction": float(finite.mean()),
            "value_counts": _value_inventory(derived[col]),
        }

    # Only the 88 keep columns are read (bounded memory) — coverage is reported
    # for those columns, not for the whole 264-column grid.
    keep_values = features.drop(columns=[DATE_COLUMN]).to_numpy(dtype="float64")
    keep_finite = np.isfinite(keep_values)
    return {
        "symbol": symbol,
        "rows": int(len(derived)),
        "date_min": str(pd.Timestamp(d_dates.min()).date()),
        "date_max": str(pd.Timestamp(d_dates.max()).date()),
        "targets": target_stats,
        "keep_cells": int(keep_finite.size),
        "keep_cells_finite": int(keep_finite.sum()),
        "feature_columns": len(feature_columns),
        "keep_columns": len(keep_columns),
    }


# --------------------------------------------------------------------------- #
# Whole-market preflight
# --------------------------------------------------------------------------- #
def _merge_value_counts(per_symbol: list[dict], column: str) -> dict[str, int]:
    total: dict[str, int] = {}
    for sym in per_symbol:
        for key, n in sym["targets"][column]["value_counts"].items():
            total[key] = total.get(key, 0) + int(n)
    return dict(sorted(total.items()))


def run_preflight(
    market: str = MARKET,
    derived_dir: Path = DERIVED_DIR,
    features_dir: Path = FEATURES_DIR,
    prune_path: Path = PRUNE_RECS,
    expected_symbols: int = EXPECTED_USD_SYMBOLS,
) -> dict:
    """Full USD preflight: returns the report payload (never writes)."""
    market = market.upper()
    if market != MARKET:
        raise PreflightError(f"WI-018 is USD-only (got market={market!r}; CAD is skipped per D-018 Q2)")
    keep_columns = load_keep_columns(prune_path)
    derived = symbol_paths(derived_dir)
    features = symbol_paths(features_dir)

    derived_only = sorted(set(derived) - set(features))
    features_only = sorted(set(features) - set(derived))
    checks = {
        "symbol_sets_match": not derived_only and not features_only,
        "expected_symbol_count": len(derived) == expected_symbols and len(features) == expected_symbols,
        "all_symbols_probed": False,
    }
    if not checks["symbol_sets_match"]:
        raise PreflightError(
            f"symbol sets differ: derived-only={derived_only[:5]} features-only={features_only[:5]}"
        )
    if not checks["expected_symbol_count"]:
        raise PreflightError(
            f"expected {expected_symbols} USD symbols, got derived={len(derived)} features={len(features)}"
        )

    per_symbol = [
        probe_symbol(sym, derived[sym], features[sym], keep_columns)
        for sym in sorted(derived)
    ]
    checks["all_symbols_probed"] = len(per_symbol) == len(derived)

    total_rows = int(sum(s["rows"] for s in per_symbol))
    targets: dict[str, dict] = {}
    for col in TARGET_COLUMNS:
        finite = int(sum(s["targets"][col]["finite"] for s in per_symbol))
        null = int(sum(s["targets"][col]["null"] for s in per_symbol))
        counts = _merge_value_counts(per_symbol, col)
        observed = sorted(float(k) for k in counts if k != "null")
        targets[col] = {
            "finite": finite,
            "null": null,
            "finite_fraction": float(finite / total_rows) if total_rows else float("nan"),
            "value_counts": counts,
            "observed_values": observed,
            "unexpected_values": sorted(v for v in observed if v not in TARGET_VALUES),
        }

    keep_cells = int(sum(s["keep_cells"] for s in per_symbol))
    keep_cells_finite = int(sum(s["keep_cells_finite"] for s in per_symbol))
    date_min = min(s["date_min"] for s in per_symbol)
    date_max = max(s["date_max"] for s in per_symbol)
    checks["nonempty_inputs"] = total_rows > 0
    checks["feature_schema_264_columns"] = all(
        s["feature_columns"] == EXPECTED_FEATURE_COLUMNS for s in per_symbol
    )
    checks["keep_columns_88_present"] = all(s["keep_columns"] == len(keep_columns) for s in per_symbol)
    checks["targets_present"] = all(
        s["targets"][PRIMARY_TARGET]["finite"] > 0 and s["targets"][PRIMARY_TARGET]["null"] >= 0
        for s in per_symbol
    )
    verdict = "PASS" if all(checks.values()) else "FAIL"
    return {
        "step": "WI-018 step 1 preflight",
        "market": MARKET,
        "scope": "USD only — CAD skipped (D-018 Q2)",
        "generated_utc": dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "config": {
            "derived_dir": str(derived_dir),
            "features_dir": str(features_dir),
            "prune_recs": str(prune_path),
            "expected_symbols": int(expected_symbols),
            "expected_feature_columns": int(EXPECTED_FEATURE_COLUMNS),
            "primary_target": PRIMARY_TARGET,
            "secondary_targets": list(SECONDARY_TARGETS),
            "keep_columns": len(keep_columns),
        },
        "checks": checks,
        "summary": {
            "symbols": len(per_symbol),
            "total_rows": total_rows,
            "date_min": date_min,
            "date_max": date_max,
            "keep_cells": keep_cells,
            "keep_cells_finite": keep_cells_finite,
            "keep_finite_fraction": float(keep_cells_finite / keep_cells) if keep_cells else float("nan"),
        },
        "targets": targets,
        "per_symbol": per_symbol,
        "verdict": verdict,
    }


# --------------------------------------------------------------------------- #
# Report / gate
# --------------------------------------------------------------------------- #
def write_report(report: dict, path: Path = PREFLIGHT_JSON) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=1, sort_keys=False))
    return path


def require_preflight(path: Path = PREFLIGHT_JSON, market: str = MARKET) -> dict:
    """Gate for later stages: the preflight must exist and say PASS.

    Every WI-018 stage calls this before writing anything, so "no study outputs
    before the preflight passes" is enforced by code, not by convention.
    """
    path = Path(path)
    if not path.is_file():
        raise PreflightError(f"preflight report missing ({path}) — run step 1 first")
    report = json.loads(path.read_text())
    if report.get("verdict") != "PASS":
        raise PreflightError(f"preflight verdict is {report.get('verdict')!r} ({path}) — inputs not verified")
    if report.get("market") != market.upper():
        raise PreflightError(f"preflight report is for {report.get('market')!r}, not {market!r}")
    return report


def summarize(report: dict) -> str:
    s = report["summary"]
    t = report["targets"][PRIMARY_TARGET]
    lines = [
        f"WI-018 preflight [{report['market']}] verdict={report['verdict']}",
        f"  symbols={s['symbols']} rows={s['total_rows']} dates {s['date_min']}..{s['date_max']}",
        f"  keep-column cells finite={s['keep_cells_finite']}/{s['keep_cells']} "
        f"({s['keep_finite_fraction']:.4f})",
        f"  {PRIMARY_TARGET}: finite={t['finite']} null={t['null']} values={t['value_counts']}",
        f"  checks={report['checks']}",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="WI-018 step 1: preflight the WI-017 USD inputs")
    ap.add_argument("--market", default=MARKET, help="USD only (CAD skipped, D-018 Q2)")
    ap.add_argument("--assert-inputs", action="store_true", help="nonzero exit unless the probe passes")
    ap.add_argument("--out", default=str(PREFLIGHT_JSON), help="preflight report path")
    ap.add_argument("--derived-dir", default=str(DERIVED_DIR))
    ap.add_argument("--features-dir", default=str(FEATURES_DIR))
    ap.add_argument("--prune-recs", default=str(PRUNE_RECS))
    ap.add_argument("--expected-symbols", type=int, default=EXPECTED_USD_SYMBOLS,
                    help="expected USD symbol count (test fixtures override the 593 contract)")
    args = ap.parse_args(argv)

    try:
        report = run_preflight(
            args.market,
            derived_dir=Path(args.derived_dir),
            features_dir=Path(args.features_dir),
            prune_path=Path(args.prune_recs),
            expected_symbols=args.expected_symbols,
        )
    except PreflightError as exc:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        report = {
            "step": "WI-018 step 1 preflight",
            "market": args.market.upper(),
            "generated_utc": dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "checks": {"preflight_error": False},
            "verdict": "FAIL",
            "error": str(exc),
        }
        write_report(report, Path(args.out))
        print(f"PREFLIGHT FAIL: {exc}")
        return 1

    write_report(report, Path(args.out))
    print(summarize(report))
    if args.assert_inputs and report["verdict"] != "PASS":
        print(f"PREFLIGHT FAIL: checks={report['checks']}")
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
