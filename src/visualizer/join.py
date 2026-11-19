"""Join index features ⋈ oof ⋈ targets on (symbol, date) per market (WI-086).

Read path (plan 26-W47): every key read is a column projection through
`VisualizerLoader`; the 92-column panel is never materialised.

Storage: alignment is one int32 position per source row, so the UI can `take()`
any projected column lazily. The index is cached at `state/viz/join_{MKT}.parquet`
and keyed by the (path, size, mtime) fingerprint of its source files inside
`state/viz/manifest.json`; a stale fingerprint triggers a rebuild.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from src.visualizer import STATE_DIR, oof_path, state_path
from src.visualizer.loader import VisualizerLoader, fingerprint

JOIN_SOURCES: tuple[str, ...] = ("features", "targets", "oof")
KEY_COLUMNS: tuple[str, ...] = ("symbol", "date")
MANIFEST_KEY = "joins"
POSITION_DTYPE = "int32"
POSITION_COLUMNS: tuple[str, ...] = ("features_pos", "targets_pos", "oof_pos")
CACHE_COLUMNS: tuple[str, ...] = KEY_COLUMNS + POSITION_COLUMNS


class JoinError(RuntimeError):
    """The three sources cannot be aligned (null/duplicate keys, market mismatch)."""


@dataclass(frozen=True)
class JoinIndex:
    """Features-anchored alignment onto oof and targets rows."""

    market: str
    frame: pd.DataFrame
    counts: dict
    fingerprints: dict
    cached: bool
    cache_path: Path

    def positions(self, source: str) -> np.ndarray:
        return self.frame[f"{source}_pos"].to_numpy()

    def align(self, values, source: str, fill: float = np.nan) -> pd.Series:
        """Take `values` (source row order) onto the join rows; -1 becomes `fill`."""
        positions = self.positions(source)
        array = np.asarray(values, dtype="float32")
        out = np.full(len(positions), fill, dtype="float32")
        matched = positions >= 0
        out[matched] = array[positions[matched]]
        return pd.Series(out, index=self.frame.index)

    def values(self, loader: VisualizerLoader, source: str, column: str) -> pd.Series:
        """One projected column of `source`, aligned onto the join rows."""
        frame = loader.load_columns(self.market, [column], source=source)
        return self.align(frame[column].to_numpy(), source)


def cache_path(market: str, state_dir: Path | str = STATE_DIR) -> Path:
    return state_path(f"join_{market.upper()}.parquet", state_dir)


def source_fingerprints(loader: VisualizerLoader, market: str, oof_variant: str | None = None) -> dict:
    """(path, size, mtime) fingerprint of every join source, plus oof variants."""
    market = market.upper()
    out = {source: fingerprint(loader.source_path(source, market, oof_variant)) for source in JOIN_SOURCES}
    for path in sorted(oof_path(market).parent.glob(f"oof_{market}_*.parquet")):
        out[f"oof_variant:{path.stem}"] = fingerprint(path)
    return out


def _as_keys(frame: pd.DataFrame, market: str, source: str) -> pd.MultiIndex:
    if frame["symbol"].isna().any() or frame["date"].isna().any():
        raise JoinError(f"{source}:{market} has null (symbol, date) keys")
    symbols = frame["symbol"].astype(str).to_numpy()
    dates = pd.to_datetime(frame["date"]).to_numpy().astype("datetime64[ns]")
    return pd.MultiIndex.from_arrays([symbols, dates], names=list(KEY_COLUMNS))


def _lookup(anchor: pd.MultiIndex, source_frame: pd.DataFrame, market: str, source: str):
    keys = _as_keys(source_frame, market, source)
    duplicates = int(keys.duplicated().sum())
    if duplicates:
        keys = keys[~keys.duplicated()]
    return keys.get_indexer(anchor).astype(POSITION_DTYPE), duplicates


def source_frames(loader: VisualizerLoader, market: str) -> dict:
    """Projected key frames per source (targets keeps `market` for the cross-check)."""
    frames: dict[str, pd.DataFrame] = {}
    for source in JOIN_SOURCES:
        columns = list(KEY_COLUMNS) + (["market"] if source == "targets" else [])
        frames[source] = loader.load_columns(market, columns, source=source)[columns].copy()
    return frames


def build_frame(loader: VisualizerLoader, market: str) -> tuple[pd.DataFrame, dict]:
    """Build the alignment frame; features are the anchor, unmatched rows keep -1."""
    market = market.upper()
    frames = source_frames(loader, market)
    mismatched = int((frames["targets"]["market"].astype(str) != market).sum())
    if mismatched:
        raise JoinError(f"targets_{market}: {mismatched} rows carry a different market label")
    anchor = _as_keys(frames["features"], market, "features")
    frame = pd.DataFrame(
        {
            "symbol": pd.Categorical(frames["features"]["symbol"].astype(str)),
            "date": pd.to_datetime(frames["features"]["date"]).to_numpy().astype("datetime64[ns]"),
        }
    )
    frame["features_pos"] = np.arange(len(frame), dtype=POSITION_DTYPE)
    frame["targets_pos"], targets_dups = _lookup(anchor, frames["targets"], market, "targets")
    frame["oof_pos"], oof_dups = _lookup(anchor, frames["oof"], market, "oof")
    counts = {
        "market": market,
        "rows": int(len(frame)),
        "features_rows": int(len(frames["features"])),
        "targets_rows": int(len(frames["targets"])),
        "oof_rows": int(len(frames["oof"])),
        "targets_matched": int((frame["targets_pos"] >= 0).sum()),
        "targets_unmatched": int((frame["targets_pos"] < 0).sum()),
        "oof_matched": int((frame["oof_pos"] >= 0).sum()),
        "oof_unmatched": int((frame["oof_pos"] < 0).sum()),
        "targets_rows_outside_panel": int(len(frames["targets"]) - (frame["targets_pos"] >= 0).sum()),
        "oof_rows_outside_panel": int(len(frames["oof"]) - (frame["oof_pos"] >= 0).sum()),
        "targets_duplicate_keys": targets_dups,
        "oof_duplicate_keys": oof_dups,
        "market_mismatch_rows": mismatched,
    }
    return frame, counts


def read_manifest(state_dir: Path | str = STATE_DIR) -> dict:
    path = state_path("manifest.json", state_dir)
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


def manifest_entry(market: str, state_dir: Path | str = STATE_DIR) -> dict:
    return (read_manifest(state_dir).get(MANIFEST_KEY) or {}).get(market.upper(), {})


def is_fresh(market: str, fingerprints: dict, state_dir: Path | str = STATE_DIR) -> bool:
    entry = manifest_entry(market, state_dir)
    return bool(entry) and entry.get("fingerprints") == fingerprints and cache_path(market, state_dir).is_file()


def update_manifest(market: str, entry: dict, state_dir: Path | str = STATE_DIR) -> Path:
    path = state_path("manifest.json", state_dir)
    manifest = read_manifest(state_dir)
    joins = manifest.setdefault(MANIFEST_KEY, {})
    joins[market.upper()] = entry
    manifest["n_join_indexes"] = len(joins)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _read_cache(path: Path) -> pd.DataFrame:
    frame = pq.read_table(path, columns=list(CACHE_COLUMNS)).to_pandas()
    frame["symbol"] = frame["symbol"].astype("category")
    frame["date"] = frame["date"].astype("datetime64[ns]")
    for column in POSITION_COLUMNS:
        frame[column] = frame[column].astype(POSITION_DTYPE)
    return frame


def _write_cache(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pandas(frame, preserve_index=False), path)


def load_or_build(
    loader: VisualizerLoader,
    market: str,
    state_dir: Path | str | None = None,
    force: bool = False,
    oof_variant: str | None = None,
) -> JoinIndex:
    """Cached join index; rebuilds when the cache is missing or the fingerprint moved."""
    market = market.upper()
    state_dir = Path(state_dir or loader.state_dir)
    fingerprints = source_fingerprints(loader, market, oof_variant)
    path = cache_path(market, state_dir)
    if not force and is_fresh(market, fingerprints, state_dir):
        entry = manifest_entry(market, state_dir)
        return JoinIndex(market, _read_cache(path), entry.get("counts", {}), fingerprints, True, path)
    frame, counts = build_frame(loader, market)
    _write_cache(frame, path)
    entry = {
        "cache": str(path),
        "rows": int(len(frame)),
        "counts": counts,
        "fingerprints": fingerprints,
        "oof_variant": oof_variant,
        "built_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    update_manifest(market, entry, state_dir)
    return JoinIndex(market, frame, counts, fingerprints, False, path)
