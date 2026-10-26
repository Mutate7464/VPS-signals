#!/usr/bin/env python3
"""WI-013 F-4 — rebuild both metadata feature panels without their label columns.

What is wrong today
-------------------
`data/features/features_{USD,CAD}_metadata.parquet` are the *metadata* feature
panels (surviving features + per-date cross-sectional percentiles). Both embed
four target/label columns — `y_15d_high`, `y_15d_low`, `y_20d_up`, `y_20d_down` —
that `src/stat_metadata.py` appended by concatenating the target frame. The
trainer selects explicit catalog columns, so there is no live leak; but any
all-columns consumer of these panels would train on the labels. WI-013 removes
them.

How the rebuild stays honest
----------------------------
The recipe mirrors `src/stat_metadata.py` exactly — it does **not** use the
legacy full-history `load_market_frame` path:

1. `data/metadata_catalog_{market}.json` supplies the surviving feature list and
   the ADF stationarity flags (the same catalog that produced the panel);
2. the *raw* values come from `features_{market}.parquet`, not from the panel
   being replaced;
3. flagged survivors get the identical trailing transform —
   `(s - s.rolling(60, min_periods=20).mean()) / (s.rolling(60, min_periods=20).std(ddof=1) + 1e-12)`
   per symbol — and **every** surviving feature gets
   `groupby("date").rank(pct=True).astype("float32")`;
4. the four label columns are never written, so "remove" is structural rather
   than a post-hoc drop.

Bounded memory (host rule: 2 vCPU / 8 GB, no all-ticker uncompressed frame)
--------------------------------------------------------------------------
Symbols are streamed from `pyarrow.dataset` in batches and reduced one symbol at
a time (a symbol's rows are contiguous in the source file), each symbol's
transformed slice is appended to a staging Parquet, the date-group percentiles are
computed one feature column at a time from that staging file, and the final panel
is written batch by batch. The only per-market resident arrays are the computed
percentile columns (~120-160 MB); no 89-column all-ticker frame is materialised.

Verification gate (no swap on mismatch)
---------------------------------------
Before anything is replaced, every column of the rebuilt panel is compared against
the pre-swap panel with
`pandas.testing.assert_frame_equal(check_dtype=True, check_exact=True)`, one column
at a time (same assertion, bounded memory), together with the row count and the
column order. If either market fails, **neither** panel is swapped: the mismatches
are reported and the script exits non-zero for escalation.

CLI::

    uv run python scripts/rebuild_wi013_metadata.py --markets USD CAD
    uv run python scripts/rebuild_wi013_metadata.py --markets CAD --no-swap
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.dataset as ds
import pyarrow.parquet as pq

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from src.market_cli import MARKET_CHOICES, normalize_market  # noqa: E402

try:  # host hygiene: hand freed buffers straight back to the OS (8 GB, no swap)
    pa.set_memory_pool(pa.system_memory_pool())
except Exception:  # pragma: no cover - pool selection is best-effort
    pass

FEATURES_DIR = BASE_DIR / "data" / "features"
REPORTS_DIR = BASE_DIR / "reports"
CATALOG_STEM = "metadata_catalog"
VERIFICATION_REPORT = REPORTS_DIR / "wi013_rebuild_verification.md"

MARKETS_DEFAULT = ("USD", "CAD")

ROLLING_Z_WINDOW = 60
MIN_PERIODS = 20
"""Mirror `src/stat_metadata.py`: 60-row rolling Z-score, min 20 observations."""

LABEL_COLUMNS = ("y_15d_high", "y_15d_low", "y_20d_up", "y_20d_down")
"""The four label columns this work item removes from both metadata panels."""

KEY_COLUMNS = ("date", "symbol", "market")
BATCH_ROWS = 50_000


# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #
def features_path(market: str) -> Path:
    return FEATURES_DIR / f"features_{market}.parquet"


def panel_path(market: str) -> Path:
    return FEATURES_DIR / f"features_{market}_metadata.parquet"


def catalog_path(market: str) -> Path:
    return BASE_DIR / "data" / f"{CATALOG_STEM}_{market}.json"


def backup_path(market: str) -> Path:
    """Pre-swap backup left on disk next to the panel it protects."""
    return FEATURES_DIR / f"features_{market}_metadata_pre_wi013.parquet"


def _rel(path: Path | str) -> str:
    """Repo-relative path when possible, absolute otherwise (tests use tmp paths)."""
    try:
        return str(Path(path).relative_to(BASE_DIR))
    except ValueError:
        return str(path)


# --------------------------------------------------------------------------- #
# Catalog + reconstruction
# --------------------------------------------------------------------------- #
def load_catalog(market: str) -> dict:
    """Read the metadata catalog that produced this market's panel."""
    path = catalog_path(market)
    if not path.exists():
        raise FileNotFoundError(f"metadata catalog missing: {path}")
    catalog = json.loads(path.read_text())
    surviving = list(catalog["surviving_features"])
    if not surviving:
        raise ValueError(f"{path}: surviving_features is empty")
    return catalog


def flagged_survivors(catalog: dict) -> list[str]:
    """Survivors flagged non-stationary by ADF — the ones the panel Z-scores."""
    stationarity = catalog["stationarity"]
    return [f for f in catalog["surviving_features"] if stationarity.get(f, {}).get("flagged")]


def expected_columns(catalog: dict) -> list[str]:
    """The rebuilt panel's column order: keys, survivors, then their percentiles."""
    surviving = list(catalog["surviving_features"])
    return list(KEY_COLUMNS) + surviving + [f"{c}_cs_pct" for c in surviving]


def _transform_piece(piece: pd.DataFrame, flagged: list[str]) -> pd.DataFrame:
    """Apply the `src/stat_metadata.py` trailing Z-score to one symbol's rows.

    The exact pandas expression `apply_stationarity_transform` uses, so the
    rebuilt values are bit-identical rather than merely close.
    """
    if not flagged:
        return piece
    out = piece.copy()
    out[flagged] = piece.groupby("symbol")[flagged].transform(
        lambda s: (s - s.rolling(ROLLING_Z_WINDOW, min_periods=MIN_PERIODS).mean())
        / (s.rolling(ROLLING_Z_WINDOW, min_periods=MIN_PERIODS).std(ddof=1) + 1e-12)
    )
    return out


def reconstruct_from_features(
    features: Path,
    catalog: dict,
    out_path: Path,
    batch_rows: int = BATCH_ROWS,
) -> int:
    """Stream `features` through the metadata transform into `out_path`.

    One symbol is held at a time (symbols are contiguous in the source file), so
    no all-ticker frame is materialised. Returns the number of rows written.
    """
    surviving = list(catalog["surviving_features"])
    flagged = flagged_survivors(catalog)
    columns = list(KEY_COLUMNS) + surviving

    dataset = ds.dataset(str(features), format="parquet")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    writer: pq.ParquetWriter | None = None
    pending = pd.DataFrame()
    rows_written = 0

    def _flush(piece: pd.DataFrame) -> None:
        nonlocal writer, rows_written
        table = pa.Table.from_pandas(piece[columns], preserve_index=False)
        if writer is None:
            writer = pq.ParquetWriter(str(out_path), table.schema)
        writer.write_table(table)
        rows_written += len(piece)

    try:
        for batch in dataset.to_batches(columns=columns, batch_size=batch_rows):
            frame = batch.to_pandas()
            if not pending.empty:
                frame = pd.concat([pending, frame], ignore_index=True)
            symbols = frame["symbol"].to_numpy()
            # Rewind to the start of the trailing symbol run: that run may be
            # truncated by the batch boundary, every earlier symbol is complete.
            cut = len(symbols) - 1
            while cut > 0 and symbols[cut - 1] == symbols[-1]:
                cut -= 1
            if cut == 0:
                pending = frame
                continue
            complete = frame.iloc[:cut].reset_index(drop=True)
            pending = frame.iloc[cut:].reset_index(drop=True)
            _flush(_transform_piece(complete, flagged))
        if not pending.empty:
            _flush(_transform_piece(pending.reset_index(drop=True), flagged))
    finally:
        if writer is not None:
            writer.close()
    return rows_written


def _staged_schema(staged_path: Path, surviving: list[str]) -> pa.Schema:
    """The rebuilt panel's schema: the staged key dtypes + survivors + percentiles.

    Key dtypes are taken from the staged file (which took them from
    `features_{market}.parquet`) rather than hardcoded, so a date unit could never
    be silently converted on the way out.
    """
    names = {f.name: f.type for f in pq.ParquetFile(str(staged_path)).schema_arrow}
    fields = [pa.field(c, names[c]) for c in KEY_COLUMNS]
    fields += [pa.field(c, names[c]) for c in surviving]
    fields += [pa.field(f"{c}_cs_pct", pa.float32()) for c in surviving]
    return pa.schema(fields)


def compute_cs_percentiles(staged_path: Path, surviving: list[str]) -> dict[str, np.ndarray]:
    """`groupby("date").rank(pct=True).astype("float32")` per feature, one column at a time.

    Same pandas call `src/stat_metadata.add_cs_percentile` makes, so the values are
    identical; reading one feature column at a time keeps the pass bounded.
    """
    dates = pq.read_table(str(staged_path), columns=["date"]).to_pandas()["date"]
    out: dict[str, np.ndarray] = {}
    for column in surviving:
        values = pq.read_table(str(staged_path), columns=[column]).to_pandas()[column]
        ranked = pd.DataFrame({"date": dates, "v": values}).groupby("date")["v"].rank(pct=True)
        out[column] = ranked.astype("float32").to_numpy()
    return out


def write_panel(
    staged_path: Path,
    percentiles: dict[str, np.ndarray],
    surviving: list[str],
    out_path: Path,
    batch_rows: int = BATCH_ROWS,
) -> int:
    """Write the final label-free panel, batch by batch, in the staged row order."""
    schema = _staged_schema(staged_path, surviving)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    offset = 0
    written = 0
    scanner = ds.dataset(str(staged_path), format="parquet").scanner(batch_size=batch_rows)
    with pq.ParquetWriter(str(out_path), schema) as writer:
        for batch in scanner.to_batches():
            frame = batch.to_pandas()
            n = len(frame)
            for column in surviving:
                frame[f"{column}_cs_pct"] = percentiles[column][offset : offset + n]
            writer.write_table(
                pa.Table.from_pandas(frame[list(schema.names)], schema=schema, preserve_index=False)
            )
            offset += n
            written += n
    return written


# --------------------------------------------------------------------------- #
# Verification (no swap unless old == new on every surviving column)
# --------------------------------------------------------------------------- #
def compare_columns(old_path: Path, new_path: Path, columns: list[str]) -> list[dict]:
    """Compare `new_path` against `old_path` column by column, exactly.

    Every column is check:dtype AND value-exact via
    `pandas.testing.assert_frame_equal(check_dtype=True, check_exact=True)` — the
    same assertion the plan names, applied one column at a time so the comparison
    never materialises an all-ticker frame.
    """
    rows = []
    for column in columns:
        new = pq.read_table(str(new_path), columns=[column]).to_pandas()
        old = pq.read_table(str(old_path), columns=[column]).to_pandas()
        record = {
            "column": column,
            "old_rows": int(len(old)),
            "new_rows": int(len(new)),
            "old_dtype": str(old[column].dtype),
            "new_dtype": str(new[column].dtype),
            "equal": False,
            "mismatches": 0,
        }
        if len(old) != len(new):
            rows.append(record)
            continue
        try:
            pd.testing.assert_frame_equal(new, old, check_dtype=True, check_exact=True)
            record["equal"] = True
        except AssertionError as exc:
            record["mismatches"] = _count_mismatches(new[column].to_numpy(), old[column].to_numpy())
            record["detail"] = str(exc).strip().splitlines()[0][:200]
        rows.append(record)
    return rows


def _count_mismatches(new: np.ndarray, old: np.ndarray) -> int:
    try:
        return int(np.count_nonzero(~((new == old) | (pd.isna(new) & pd.isna(old)))))
    except (TypeError, ValueError):  # pragma: no cover - object columns
        return -1


def verify_market(market: str, old_path: Path, new_path: Path) -> dict:
    """Full pre-swap verification for one market."""
    catalog = load_catalog(market)
    columns = expected_columns(catalog)
    new_schema = list(pq.ParquetFile(str(new_path)).schema_arrow.names)
    old_schema = list(pq.ParquetFile(str(old_path)).schema_arrow.names)
    old_labels = sorted(c for c in old_schema if c.startswith("y_"))
    new_labels = sorted(c for c in new_schema if c.startswith("y_"))
    new_rows = int(pq.ParquetFile(str(new_path)).metadata.num_rows)
    old_rows = int(pq.ParquetFile(str(old_path)).metadata.num_rows)

    column_rows = compare_columns(old_path, new_path, columns)
    return {
        "market": market,
        "old_rows": old_rows,
        "new_rows": new_rows,
        "rows_equal": old_rows == new_rows,
        "old_columns": len(old_schema),
        "new_columns": len(new_schema),
        "dropped_labels": old_labels,
        "labels_present_after": new_labels,
        "column_order_ok": new_schema == columns,
        "expected_columns_ok": new_schema == [c for c in old_schema if c not in LABEL_COLUMNS],
        "columns_compared": len(column_rows),
        "columns_unequal": [r["column"] for r in column_rows if not r["equal"]],
        "column_rows": column_rows,
        "pass": bool(
            old_rows == new_rows
            and not new_labels
            and new_schema == columns
            and all(r["equal"] for r in column_rows)
        ),
    }


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def rebuild_market(market: str, staging_dir: Path, batch_rows: int = BATCH_ROWS) -> dict:
    """Reconstruct, verify, and (only on a pass) atomically replace one panel."""
    market = normalize_market(market)
    catalog = load_catalog(market)
    surviving = list(catalog["surviving_features"])
    transformed = staging_dir / f"features_{market}_metadata_transformed.parquet"
    rebuilt = staging_dir / f"features_{market}_metadata_rebuilt.parquet"

    rows = reconstruct_from_features(features_path(market), catalog, transformed, batch_rows=batch_rows)
    percentiles = compute_cs_percentiles(transformed, surviving)
    written = write_panel(transformed, percentiles, surviving, rebuilt, batch_rows)
    if written != rows:
        raise RuntimeError(f"{market}: rebuilt row count drifted ({written} != {rows})")
    del percentiles

    return {
        "market": market,
        "staged": rebuilt,
        "transformed": transformed,
        "staged_rows": rows,
        "catalog_surviving": len(surviving),
        "flagged": flagged_survivors(catalog),
    }


def render_report(results: list[dict], swap: bool, staging_dir: Path) -> Path:
    """Write `reports/wi013_rebuild_verification.md` — the per-market old/new table."""
    all_pass = all(r["verification"]["pass"] for r in results) and len(results) > 0
    lines = [
        "# WI-013 — metadata panel rebuild verification (F-4)",
        "",
        f"- Generated (UTC): {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        "- Rebuild recipe: `data/metadata_catalog_{market}.json` (surviving features + ADF "
        "stationarity flags) applied to `features_{market}.parquet` — the same 60-row "
        "per-symbol Z-score and per-date `rank(pct=True)` construction as "
        "`src/stat_metadata.py`, not the legacy `load_market_frame` path.",
        "- Comparison: every surviving column checked with "
        "`pandas.testing.assert_frame_equal(check_dtype=True, check_exact=True)`, one column "
        "at a time (same assertion, bounded memory), plus row count and column order.",
        f"- Swap performed: **{'YES' if all_pass and swap else 'NO'}**"
        + ("" if all_pass else " — at least one market failed verification, so no panel was replaced."),
        f"- Staging directory: `{staging_dir}`",
    ]
    if all_pass and all(not v["dropped_labels"] for v in (r["verification"] for r in results)):
        lines.append(
            "- NOTE: the reference panel already carried no label columns, so this run compared "
            "two label-free panels (no pre-WI-013 backup was found on disk)."
        )
    lines += [
        "",
        "## Per-market result",
        "",
        "| Market | Old rows | New rows | Rows equal | Cols old → new | Labels dropped | Labels left | "
        "Column order | Columns compared | Columns unequal | Verdict |",
        "| :--- | ---: | ---: | :--- | :--- | :--- | :--- | :--- | ---: | :--- | :--- |",
    ]
    for r in results:
        v = r["verification"]
        lines.append(
            f"| {v['market']} | {v['old_rows']:,} | {v['new_rows']:,} | "
            f"{'yes' if v['rows_equal'] else '**NO**'} | {v['old_columns']} → {v['new_columns']} | "
            f"{', '.join(f'`{c}`' for c in v['dropped_labels']) or '(none)'} | "
            f"{', '.join(f'`{c}`' for c in v['labels_present_after']) or '(none)'} | "
            f"{'ok' if v['column_order_ok'] else '**MISMATCH**'} | {v['columns_compared']} | "
            f"{', '.join(f'`{c}`' for c in v['columns_unequal']) or 'none'} | "
            f"**{'PASS' if v['pass'] else 'FAIL'}** |"
        )

    for r in results:
        v = r["verification"]
        lines += [
            "",
            f"## {v['market']} — per-column equality (old vs new, exact)",
            "",
            f"- Comparison reference: `{v.get('reference', '(unspecified)')}`",
            f"- Old panel columns: {v['old_columns']} · new: {v['new_columns']} · "
            f"labels removed: {', '.join(f'`{c}`' for c in v['dropped_labels']) or '(none)'}",
            f"- Surviving-column order equals the catalog order: "
            f"**{'yes' if v['column_order_ok'] else 'NO'}**; equals the old order minus labels: "
            f"**{'yes' if v['expected_columns_ok'] else 'NO'}**",
            f"- Backups: `{r['backup']}`" if r.get("backup") else "- Backups: not written (no swap)",
            "",
            "| Column | Rows old | Rows new | dtype old | dtype new | exact equal |",
            "| :--- | ---: | ---: | :--- | :--- | :--- |",
        ]
        for c in v["column_rows"]:
            verdict = "yes" if c["equal"] else f"**NO** ({c['mismatches']} rows)"
            lines.append(
                f"| `{c['column']}` | {c['old_rows']:,} | {c['new_rows']:,} | {c['old_dtype']} | "
                f"{c['new_dtype']} | {verdict} |"
            )

    if not all_pass:
        lines += [
            "",
            "## Escalation",
            "",
            "- At least one market failed the old==new check. Per the plan, no swap was "
            "performed; the staging file is retained for diagnosis and this needs escalation.",
        ]

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    VERIFICATION_REPORT.write_text("\n".join(lines) + "\n")
    return VERIFICATION_REPORT


def build_parser() -> argparse.ArgumentParser:
    """The CLI parser for this entry point."""
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument(
        "--markets",
        nargs="+",
        default=list(MARKETS_DEFAULT),
        help=f"Markets to rebuild, in order (default: {' '.join(MARKETS_DEFAULT)}).",
    )
    ap.add_argument("--no-swap", action="store_true", help="Verify only; never replace a panel.")
    ap.add_argument("--staging-dir", default=None, help="Where staged panels are written (default: a temp dir).")
    ap.add_argument("--batch-rows", type=int, default=BATCH_ROWS)
    return ap


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    try:
        markets = [normalize_market(m) for m in args.markets]
    except ValueError as exc:
        print(f"[rebuild-wi013] {exc}", file=sys.stderr)
        return 2

    staging_dir = Path(args.staging_dir) if args.staging_dir else Path(tempfile.mkdtemp(prefix="wi013_rebuild_"))
    staging_dir.mkdir(parents=True, exist_ok=True)
    print(f"[rebuild-wi013] PLAN: markets={', '.join(markets)} staging={staging_dir} swap={not args.no_swap}")

    results: list[dict] = []
    for market in markets:
        print(f"[rebuild-wi013] {market}: streaming features_{market}.parquet → staged panel ...")
        staged = rebuild_market(market, staging_dir, batch_rows=args.batch_rows)["staged"]
        # The comparison reference is the *pre-swap* panel: the retained backup when
        # one exists (a re-run), else the panel that is about to be replaced.
        backup = backup_path(market)
        reference = backup if backup.exists() else panel_path(market)
        verification = verify_market(market, reference, staged)
        verification["reference"] = (
            f"{_rel(backup)} (pre-swap backup)"
            if backup.exists()
            else f"{_rel(panel_path(market))} (pre-swap panel)"
        )
        results.append(
            {
                "market": market,
                "staged": staged,
                "staged_rows": pq.ParquetFile(str(staged)).metadata.num_rows,
                "verification": verification,
            }
        )
        print(
            f"[rebuild-wi013] {market}: rows {verification['old_rows']:,} → {verification['new_rows']:,} · "
            f"columns compared {verification['columns_compared']} · unequal "
            f"{verification['columns_unequal'] or 'none'} · labels after "
            f"{verification['labels_present_after'] or '(none)'} · "
            f"{'PASS' if verification['pass'] else 'FAIL'}"
        )

    all_pass = all(r["verification"]["pass"] for r in results) and bool(results)
    if all_pass and not args.no_swap:
        for r in results:
            market = r["market"]
            target = panel_path(market)
            backup = backup_path(market)
            if not backup.exists():
                shutil.copy2(target, backup)
            os.replace(r["staged"], target)
            r["backup"] = _rel(backup)
            print(f"[rebuild-wi013] {market}: backup {backup.name} · atomically replaced {target.name}")
    elif all_pass:
        print("[rebuild-wi013] --no-swap: both markets verified, panels left in place")

    report = render_report(results, swap=not args.no_swap, staging_dir=staging_dir)
    print(f"[rebuild-wi013] wrote {report}")
    if not all_pass:
        print("[rebuild-wi013] VERIFICATION FAILED — no swap performed (escalate)", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
