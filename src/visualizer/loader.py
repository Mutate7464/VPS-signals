"""Column-projecting, budget-guarded loader for the visualizer (WI-085).

Read path (plan 26-W47):
- every panel read is a projection: `pq.read_table(path, columns=[keys + requested])`;
  the full 92-column features panel is never materialised by the UI;
- raw OHLCV is read per symbol file only, never via a dataset over `raw_ohlcv/`;
- `l0_ext` joins the panel on (symbol, date); unmatched counts are returned as evidence;
- all writes go to `state/viz/` (the UI process is read-only over `data/`).
"""
from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

from src.visualizer import (
    COLUMN_LRU_SIZE,
    DEFAULT_BUDGET_BYTES,
    L0_EXT_FEATURES,
    MARKETS,
    N_JOBS,
    OHLCV_LRU_SIZE,
    STATE_DIR,
    feature_path,
    l0_ext_path,
    oof_path,
    raw_ohlcv_path,
    state_path,
    targets_path,
)
from src.visualizer import schema as schema_module
from src.visualizer.cache import ByteLedger, make_caches, process_rss_bytes
from src.visualizer.schema import (
    FEATURE_FLOAT_COLUMNS,
    L0_EXT_FLOAT_COLUMNS,
    SAMPLE_OHLCV_PER_MARKET,
    sampled_ohlcv_paths,
)

#: Key columns injected into every projection, per source.
SOURCE_KEYS: dict[str, tuple[str, ...]] = {
    "features": ("date", "symbol", "market"),
    "targets": ("date", "symbol", "market"),
    "oof": ("date", "symbol", "close"),
    "l0_ext": ("symbol", "date"),
}
#: Filter-latency probe columns (whitelisted features only).
FILTER_PROBE_COLUMNS: tuple[str, ...] = ("rsi_14", "atr_pct_20", "entropy_20", "hurst_50", "adx_20")


def _to_pandas(table: pa.Table) -> pd.DataFrame:
    """Dictionary-encode string keys and keep float32 (no upcasting)."""
    table = table.combine_chunks()
    for index, field in enumerate(table.schema):
        if pa.types.is_string(field.type) or pa.types.is_large_string(field.type):
            table = table.set_column(index, field.name, pc.dictionary_encode(table.column(index)))
    frame = table.to_pandas()
    for name in frame.columns:
        if frame[name].dtype == np.float64:
            frame[name] = frame[name].astype(np.float32)
    return frame


def _cast_dates(table: pa.Table, target: pa.DataType = pa.timestamp("ns")) -> pa.Table:
    index = table.schema.get_field_index("date")
    if index >= 0 and table.schema.field("date").type != target:
        table = table.set_column(index, "date", pc.cast(table.column(index), target))
    return table


def fingerprint(path: Path) -> dict:
    """(path, size, mtime) fingerprint plus metadata-only row/column counts."""
    stat = path.stat()
    meta = pq.ParquetFile(path).metadata
    return {
        "path": str(path),
        "size_bytes": int(stat.st_size),
        "mtime_ns": int(stat.st_mtime_ns),
        "rows": int(meta.num_rows),
        "columns": int(meta.num_columns),
    }


class VisualizerLoader:
    """One in-memory panel copy per worker, costed before every load."""

    def __init__(
        self,
        budget_bytes: int = DEFAULT_BUDGET_BYTES,
        state_dir: Path | str = STATE_DIR,
        markets: tuple[str, ...] = MARKETS,
    ) -> None:
        self.ledger = ByteLedger(budget_bytes)
        self.columns, self.ohlcv = make_caches()
        self.state_dir = Path(state_dir)
        self.markets = tuple(m.upper() for m in markets)

    # ── paths / metadata ────────────────────────────────────────────────
    def source_path(self, source: str, market: str, variant: str | None = None) -> Path:
        if source == "features":
            return feature_path(market)
        if source == "targets":
            return targets_path(market)
        if source == "oof":
            return oof_path(market, variant)
        raise ValueError(f"unknown source {source!r}")

    @staticmethod
    def parquet_rows(path: Path) -> int:
        return int(pq.ParquetFile(path).metadata.num_rows)

    @staticmethod
    def read_projected(path: Path, columns: list[str]) -> pa.Table:
        """The only panel read primitive: always a column projection."""
        return pq.read_table(path, columns=list(columns))

    # ── projected loads ────────────────────────────────────────────────
    def load_columns(
        self,
        market: str,
        columns: list[str] | tuple[str, ...],
        source: str = "features",
        variant: str | None = None,
    ) -> pd.DataFrame:
        market = market.upper()
        requested = list(dict.fromkeys(columns))
        projection = [k for k in SOURCE_KEYS[source] if k not in requested] + requested
        key = (source, market, variant, tuple(projection))
        cached = self.columns.get(key)
        if cached is not None:
            return cached
        path = self.source_path(source, market, variant)
        rows = self.parquet_rows(path)
        self.ledger.reserve(key, ByteLedger.estimate(rows, len(projection)), label=f"{source}:{market}")
        try:
            frame = _to_pandas(self.read_projected(path, projection))
        except Exception:
            self.ledger.release(key)
            raise
        for evicted in self.columns.put(key, frame):
            self.ledger.release(evicted)
        return frame

    def sample_ohlcv(self, market: str, symbol: str) -> pd.DataFrame:
        """Single-symbol OHLCV read (LRU of 32 symbols); never a dataset scan."""
        market, symbol = market.upper(), symbol.upper()
        key = (market, symbol)
        cached = self.ohlcv.get(key)
        if cached is not None:
            return cached
        path = raw_ohlcv_path(market, symbol)
        frame = _to_pandas(pq.read_table(path))
        self.ohlcv.put(key, frame)
        return frame

    def sample_ohlcv_files(self, per_market: int = SAMPLE_OHLCV_PER_MARKET) -> dict[str, list[dict]]:
        """The 10 sampled OHLCV files (5 per market) with their measured row counts."""
        out: dict[str, list[dict]] = {}
        for market, symbol, path in sampled_ohlcv_paths(per_market):
            frame = self.sample_ohlcv(market, symbol)
            out.setdefault(market, []).append({"symbol": symbol, "rows": int(len(frame))})
        return out

    def join_l0_ext(
        self,
        market: str,
        feature: str,
        value_columns: list[str] | tuple[str, ...] | None = None,
    ) -> tuple[pd.DataFrame, dict]:
        """Join one l0_ext feature onto the panel on (symbol, date); report unmatched counts."""
        market = market.upper()
        values = list(value_columns or L0_EXT_FLOAT_COLUMNS[feature])
        panel = _to_pandas(self.read_projected(feature_path(market), ["symbol", "date"]))
        ext_table = _cast_dates(self.read_projected(l0_ext_path(feature, market), ["symbol", "date"] + values))
        ext = _to_pandas(ext_table)
        merged = panel.merge(ext, on=["symbol", "date"], how="outer", indicator=True, sort=False)
        flag = merged.pop("_merge")
        counts = {
            "market": market,
            "feature": feature,
            "panel_rows": int(len(panel)),
            "ext_rows": int(len(ext)),
            "matched_rows": int((flag == "both").sum()),
            "unmatched_panel_rows": int((flag == "left_only").sum()),
            "ext_rows_outside_panel": int((flag == "right_only").sum()),
        }
        return merged, counts

    def filter_latency(self, market: str = "USD", repeats: int = 3) -> dict:
        """Measured round-trip for a 5-slider boolean filter plus decile binning."""
        frame = self.load_columns(market, list(FILTER_PROBE_COLUMNS))
        values = [frame[c].to_numpy() for c in FILTER_PROBE_COLUMNS]
        bounds = [(float(np.nanpercentile(v, 25)), float(np.nanpercentile(v, 75))) for v in values]
        latencies, retained = [], 0
        for _ in range(max(1, repeats)):
            start = time.perf_counter()
            mask = np.ones(len(frame), dtype=bool)
            for column_values, (low, high) in zip(values, bounds):
                mask &= (column_values >= low) & (column_values <= high)
            retained = int(mask.sum())
            np.nanpercentile(values[0][mask], np.arange(0, 101, 10))
            latencies.append((time.perf_counter() - start) * 1000.0)
        return {
            "market": market.upper(),
            "columns": list(FILTER_PROBE_COLUMNS),
            "retained_rows": retained,
            "latency_ms_median": round(float(np.median(latencies)), 2),
            "latency_ms_max": round(float(max(latencies)), 2),
            "repeats": repeats,
        }

    # ── evidence writes (state/viz only) ──────────────────────────────
    def write_state(self, name: str, payload: dict) -> Path:
        path = state_path(name, self.state_dir).resolve()
        if not path.is_relative_to(self.state_dir.resolve()):
            raise ValueError(f"refusing to write outside {self.state_dir}: {path}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        return path

    def row_counts(self) -> dict:
        counts: dict[str, dict] = {"features": {}, "targets": {}, "oof": {}, "oof_variants": {}, "l0_ext": {}}
        for market in self.markets:
            counts["features"][market] = self.parquet_rows(feature_path(market))
            counts["targets"][market] = self.parquet_rows(targets_path(market))
            oof_file = oof_path(market)
            counts["oof"][market] = self.parquet_rows(oof_file)
            counts["oof_variants"][market] = {
                p.stem: self.parquet_rows(p)
                for p in sorted(oof_file.parent.glob(f"oof_{market}_*.parquet"))
            }
            for feature in L0_EXT_FEATURES:
                counts["l0_ext"][f"{feature}_{market}"] = self.parquet_rows(l0_ext_path(feature, market))
        return counts

    def manifest(self) -> dict:
        entries = [fingerprint(feature_path(m)) for m in self.markets]
        entries += [fingerprint(targets_path(m)) for m in self.markets]
        for market in self.markets:
            entries.append(fingerprint(oof_path(market)))
            entries += [fingerprint(p) for p in sorted(oof_path(market).parent.glob(f"oof_{market}_*.parquet"))]
            entries += [fingerprint(l0_ext_path(f, market)) for f in L0_EXT_FEATURES]
        entries += [fingerprint(p) for _, _, p in sampled_ohlcv_paths()]
        return {"artifacts": entries, "n_artifacts": len(entries), "sample_ohlcv_files": len(sampled_ohlcv_paths())}

    def run_benchmark(self) -> dict:
        """Phase-0 measurement: row counts, peak RSS, filter latency -> state/viz/bench.json."""
        import resource

        schema_report = schema_module.assert_all_artifacts(self.markets)
        latency = self.filter_latency(self.markets[0])
        report = {
            "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "row_counts": self.row_counts(),
            "sample_ohlcv": self.sample_ohlcv_files(),
            "filter_latency": latency,
            "rss_mb": round(process_rss_bytes() / 2**20, 1),
            "peak_rss_mb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0, 1),
            "ledger": self.ledger.snapshot(),
            "caches": [self.columns.stats(), self.ohlcv.stats()],
            "limits": {
                "budget_bytes": self.ledger.budget_bytes,
                "column_lru_size": COLUMN_LRU_SIZE,
                "ohlcv_lru_size": OHLCV_LRU_SIZE,
                "n_jobs": N_JOBS,
            },
            "schema": {
                "ok": True,
                "markets": list(self.markets),
                "feature_columns": len(FEATURE_FLOAT_COLUMNS) + 3,
                "feature_float32_columns": len(FEATURE_FLOAT_COLUMNS),
                "oof_canonical_columns": len(schema_module.OOF_CANONICAL_COLUMNS),
                "l0_ext_files": len(schema_report["l0_ext"]),
                "raw_ohlcv_sampled": len(schema_report["raw_ohlcv"]),
            },
        }
        self.write_state("bench.json", report)
        self.write_state("manifest.json", self.manifest())
        return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Visualizer loader / Phase-0 benchmark (WI-085)")
    parser.add_argument("--bench", action="store_true", help="write state/viz/bench.json + manifest.json")
    parser.add_argument("--budget-gb", type=float, default=DEFAULT_BUDGET_BYTES / 2**30)
    args = parser.parse_args(argv)
    loader = VisualizerLoader(budget_bytes=int(args.budget_gb * 2**30))
    if not args.bench:
        parser.print_help()
        return 0
    report = loader.run_benchmark()
    print(f"bench: features USD={report['row_counts']['features']['USD']} CAD={report['row_counts']['features']['CAD']}")
    print(
        f"bench: peak_rss={report['peak_rss_mb']} MB filter_median={report['filter_latency']['latency_ms_median']} ms "
        f"-> {state_path('bench.json')}"
    )
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
