"""WI-011 Step 1 — preflight inspection of the existing CAD feature/target parquets.

Read-only. This script never rebuilds data: it inspects `data/features/features_CAD.parquet`
and `data/features/targets_CAD.parquet` and reports row counts, columns, symbol/date
coverage, duplicate keys and key alignment to `reports/wi011_preflight.md`.

Marker lines the plan's verify command greps for:

    FEATURE_ROWS: <n>
    TARGET_ROWS: <n>
    KEY_ALIGNMENT: PASS|FAIL
    DUPLICATE_KEYS: <n>

Exit code is non-zero when the preflight FAILS (missing inputs, duplicate keys,
unaligned key sets, or an unexplained row-count mismatch), so Build must stop
before any analysis step runs.

Why only the key columns are read
---------------------------------
The feature panel is 284 MB compressed with a single row group, so reading all 89
columns would pull the whole all-ticker frame into memory. The preflight only
needs `date`, `symbol`, `market` (plus the target label columns' names) to prove
coverage and alignment — that is what keeps it inside the 2 vCPU / 8 GB host rule.
"""

from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

BASE_DIR = Path(__file__).resolve().parents[1]
FEATURES = BASE_DIR / "data" / "features" / "features_CAD.parquet"
TARGETS = BASE_DIR / "data" / "features" / "targets_CAD.parquet"
REPORT = BASE_DIR / "reports" / "wi011_preflight.md"

KEY_COLUMNS = ["date", "symbol", "market"]


def _read_keys(path: Path) -> tuple[list[str], np.ndarray, np.ndarray, np.ndarray, int]:
    """Return (all_columns, date, symbol, market, n_rows) for one parquet input."""
    schema = pq.ParquetFile(path).schema_arrow
    cols = list(schema.names)
    missing = [c for c in KEY_COLUMNS if c not in cols]
    if missing:
        raise KeyError(f"{path.name}: missing key column(s) {missing}")
    tbl = pq.read_table(path, columns=KEY_COLUMNS)
    return (
        cols,
        tbl.column("date").to_numpy(zero_copy_only=False),
        tbl.column("symbol").to_pandas().to_numpy(dtype=object),
        tbl.column("market").to_pandas().to_numpy(dtype=object),
        tbl.num_rows,
    )


def _duplicate_keys(dates, symbols, markets) -> int:
    """Count duplicated (date, symbol, market) triples via a composite byte key."""
    d = np.asarray(dates, dtype="datetime64[ns]").astype("int64")
    s = pd_factorize_bytes(symbols)
    m = pd_factorize_bytes(markets)
    key = np.stack([d, s, m], axis=1)
    _, counts = np.unique(key, axis=0, return_counts=True)
    return int((counts - 1).clip(min=0).sum())


def pd_factorize_bytes(values) -> np.ndarray:
    """Dense integer codes for a string array (small helper, no pandas dependency)."""
    uniq, inv = np.unique(np.asarray(values, dtype=object).astype(str), return_inverse=True)
    if uniq.size == 0:
        return np.zeros(0, dtype="int64")
    return inv.astype("int64")


def _same_key_sequence(a: tuple, b: tuple) -> bool:
    """Exact element-wise equality of (date, symbol, market) sequences."""
    if len(a[0]) != len(b[0]):
        return False
    if not np.array_equal(a[0], b[0]):
        return False
    if not np.array_equal(a[1], b[1]):
        return False
    return bool(np.array_equal(a[2], b[2]))


def _monthly_coverage(dates, symbols) -> list[str]:
    """Rows/symbols per calendar year — the coverage sanity table."""
    d = np.asarray(dates, dtype="datetime64[ns]")
    years = d.astype("datetime64[Y]").astype(int) + 1970
    sym = np.asarray(symbols, dtype=object)
    lines = []
    for y in np.unique(years):
        mask = years == y
        lines.append(f"| {int(y)} | {int(mask.sum()):,} | {len(np.unique(sym[mask]))} |")
    return lines


def main() -> int:
    report_lines: list[str] = [
        "# WI-011 Step 1 — preflight (CAD inputs, read-only)",
        "",
        f"- Generated (UTC): {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        f"- Feature input: `{FEATURES.relative_to(BASE_DIR)}`",
        f"- Target input: `{TARGETS.relative_to(BASE_DIR)}`",
        "- Method: inspect existing parquets only; no feature/target regeneration, no "
        "all-ticker uncompressed frame (key columns are read, not the 89-column panel).",
        "",
    ]

    failures: list[str] = []

    for label, path in (("FEATURE", FEATURES), ("TARGET", TARGETS)):
        if not path.exists():
            failures.append(f"{label} input missing: {path}")

    if failures:
        report_lines += ["## FAILURES", ""] + [f"- {f}" for f in failures]
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text("\n".join(report_lines) + "\n")
        print(f"[wi011_preflight] FAIL (missing inputs) — wrote {REPORT}")
        return 1

    f_cols, f_date, f_sym, f_mkt, f_rows = _read_keys(FEATURES)
    t_cols, t_date, t_sym, t_mkt, t_rows = _read_keys(TARGETS)

    f_dup = _duplicate_keys(f_date, f_sym, f_mkt)
    t_dup = _duplicate_keys(t_date, t_sym, t_mkt)

    f_key_set = set(map(tuple, zip(f_date.astype("int64").tolist(), f_sym.tolist(), f_mkt.tolist())))
    t_key_set = set(map(tuple, zip(t_date.astype("int64").tolist(), t_sym.tolist(), t_mkt.tolist())))
    set_aligned = f_key_set == t_key_set
    order_aligned = _same_key_sequence((f_date, f_sym, f_mkt), (t_date, t_sym, t_mkt))

    f_dates = np.unique(f_date.astype("datetime64[ns]"))
    t_dates = np.unique(t_date.astype("datetime64[ns]"))

    report_lines += [
        "## Observed inputs",
        "",
        "| Input | Rows | Columns | Symbols | Unique dates | Date range |",
        "| :--- | ---: | ---: | ---: | ---: | :--- |",
        f"| features_CAD.parquet | {f_rows:,} | {len(f_cols)} | {len(np.unique(f_sym))} | "
        f"{len(f_dates)} | {f_dates.min()} → {f_dates.max()} |",
        f"| targets_CAD.parquet | {t_rows:,} | {len(t_cols)} | {len(np.unique(t_sym))} | "
        f"{len(t_dates)} | {t_dates.min()} → {t_dates.max()} |",
        "",
        f"FEATURE_ROWS: {f_rows}",
        f"TARGET_ROWS: {t_rows}",
        f"FEATURE_COLUMNS: {len(f_cols)}",
        f"TARGET_COLUMNS: {len(t_cols)}",
        "",
        "Target label columns: " + ", ".join(f"`{c}`" for c in t_cols if c not in KEY_COLUMNS),
        "",
        "Feature panel is the 89-indicator set defined by WI-002 E3 (63 classical + 26 "
        "fib/range); key columns plus identifiers only are read here.",
        "",
        "## Key integrity",
        "",
        f"DUPLICATE_KEYS: {f_dup + t_dup}",
        f"- duplicated feature keys: {f_dup}",
        f"- duplicated target keys: {t_dup}",
        f"KEY_ALIGNMENT: {'PASS' if set_aligned else 'FAIL'}",
        f"- aligned `(date, symbol, market)` coverage: {'exact key-set match' if set_aligned else 'KEY SETS DIFFER'}",
        f"KEY_ORDER_ALIGNMENT: {'PASS' if order_aligned else 'FAIL'}",
        "- key-order equality matters because the analysis scripts read the feature panel "
        "in row order and align the condition-state table positionally (no join).",
        "",
    ]

    if not set_aligned:
        only_f = len(f_key_set - t_key_set)
        only_t = len(t_key_set - f_key_set)
        failures.append(f"key sets differ (feature-only={only_f}, target-only={only_t})")
        report_lines += [f"- feature-only keys: {only_f}", f"- target-only keys: {only_t}", ""]
    if not order_aligned:
        failures.append("key sequence order differs between the feature and target parquets")
    if f_dup or t_dup:
        failures.append(f"duplicate keys present (feature={f_dup}, target={t_dup})")
    if f_rows != t_rows and set_aligned:
        failures.append(f"row counts differ with identical key sets (feature={f_rows}, target={t_rows})")

    report_lines += [
        "## Per-year coverage (feature panel)",
        "",
        "| Year | Rows | Symbols |",
        "| ---: | ---: | ---: |",
    ]
    report_lines += _monthly_coverage(f_date, f_sym)

    report_lines += ["", "## Verdict", ""]
    if failures:
        report_lines += ["FAIL"] + [f"- {f}" for f in failures]
    else:
        report_lines += [
            "PASS — inputs present, no duplicate keys, feature/target key sets and key order align; "
            "Step 2 may proceed.",
            "- Row counts are reported as observed (not hard-coded) and match exactly.",
        ]

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(report_lines) + "\n")
    print(f"[wi011_preflight] wrote {REPORT} (failures={len(failures)})")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())