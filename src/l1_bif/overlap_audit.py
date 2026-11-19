"""WI-082 — audit the swing detector for unfiltered overlapping triggers.

Plan ``26-W47-visualizer-audit-workbench`` rank 10 (EVT-AUDIT). Audit-only: no
feature is computed, no parquet is written, no gate verdict is emitted. The
question answered is whether ``src.swing_bsh.events.detect_swings`` (imported
read-only, never re-implemented) emits **all** historical triggers — it applies a
same-side ``gap`` spacing only, with no concurrent-position filter — reported as
counts.

Report terms (``hold_bars`` = the shortest vertical barrier, ``min(BARRIERS)``):
  * ``total_triggers``  raw detector output, both sides;
  * ``overlapping_pairs``  pairs ``i < j`` with ``bar_j - bar_i < hold_bars`` (a
    position opened at ``i`` is still open at ``j``);
  * ``clusters``  maximal chained runs (consecutive distance ``< hold_bars``);
  * ``suppressed_by_no_concurrent``  triggers dropped by a sequential
    keep-first-while-open rule — the only filter consistent with the detector's
    own ``gap`` collapse.

Causality: a trigger at bar ``t`` reads bars ``t-window+1..t`` only (trailing
rolling extrema), so no future bar can create, move or delete it at or before its
own bar. A NaN inside a trailing window yields no trigger (NaN-propagating, never
``fillna``). License: D-023 layer 1 predictive-only — counting only, no trading
or economic metric is produced here.

Repo invariants: symbol-sequential reads with column projection, float32 cast in
:func:`prepare_frame`, index reset before concat (RISKS R-08), no all-ticker
frame, report writes confined to ``/tmp``.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from src.swing_bsh.events import BARRIERS, CLUSTER_GAP, SWING_WINDOW, detect_swings

HOLD_BARS = int(min(BARRIERS))  # shortest vertical barrier = reference holding window
RAW_ROOT = Path("data/raw_ohlcv")
SMOKE_DIR = Path("/tmp/WI-082_smoke")
FLOAT_COLS = ("open", "high", "low", "close")
COUNT_KEYS = (
    "total_triggers",
    "at_bottom",
    "at_top",
    "overlapping_pairs",
    "clusters",
    "suppressed_by_no_concurrent",
)

__all__ = [
    "COUNT_KEYS", "HOLD_BARS", "SMOKE_DIR", "audit_market", "audit_overlap",
    "audit_symbol", "load_symbol_frame", "prepare_frame", "swing_events",
]


def _check(window: int, gap: int, hold_bars: int) -> None:
    if window < 2:
        raise ValueError("window must be >= 2")
    if gap < 1:
        raise ValueError("gap must be >= 1")
    if hold_bars < 1:
        raise ValueError("hold_bars must be >= 1")


def prepare_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Date-sorted, index-reset copy with OHLC cast to float32 (NaN preserved)."""
    out = df.sort_values("date").reset_index(drop=True)
    for col in FLOAT_COLS:
        if col in out.columns:
            out[col] = out[col].astype("float32")
    return out


def swing_events(df: pd.DataFrame, *, window: int = SWING_WINDOW,
                 gap: int = CLUSTER_GAP) -> list[tuple[int, str]]:
    """Trailing ``(bar_index, state)`` triggers for ONE symbol (detector under audit)."""
    return detect_swings(prepare_frame(df), window=window, gap=gap)


def _counts(events: list[tuple[int, str]], hold_bars: int) -> dict:
    """Counts for one symbol's trigger list (no label, no verdict)."""
    bars = np.array([t for t, _ in events], dtype="int64")
    n = int(bars.size)
    if n == 0:
        return dict.fromkeys(COUNT_KEYS, 0) | {"first_bar": None, "last_bar": None}
    # pairs i < j whose bar distance is strictly below the holding window
    upper = np.searchsorted(bars, bars + hold_bars, side="left")
    pairs = int((upper - np.arange(n) - 1).sum())
    clusters = int(1 + np.count_nonzero(np.diff(bars) >= hold_bars))
    kept, last = 0, -(10**9)
    for t in bars:  # sequential keep-first-while-open
        if int(t) - last >= hold_bars:
            kept += 1
            last = int(t)
    n_bottom = int(sum(1 for _, s in events if s == "at_bottom"))
    return {
        "total_triggers": n,
        "overlapping_pairs": pairs,
        "clusters": clusters,
        "suppressed_by_no_concurrent": n - kept,
        "at_bottom": n_bottom,
        "at_top": n - n_bottom,
        "first_bar": int(bars[0]),
        "last_bar": int(bars[-1]),
    }


def audit_symbol(df: pd.DataFrame, symbol: str = "<frame>", *,
                 window: int = SWING_WINDOW, gap: int = CLUSTER_GAP,
                 hold_bars: int = HOLD_BARS) -> dict:
    """Counts report for one symbol's OHLCV frame (index-stable, causal)."""
    _check(window, gap, hold_bars)
    g = prepare_frame(df)
    return {"symbol": str(symbol), "bars": int(len(g)),
            **_counts(swing_events(g, window=window, gap=gap), hold_bars)}


def _aggregate(per_symbol: list[dict]) -> dict:
    return {k: int(sum(p[k] for p in per_symbol)) for k in COUNT_KEYS}


def audit_overlap(df: pd.DataFrame, *, window: int = SWING_WINDOW,
                  gap: int = CLUSTER_GAP, hold_bars: int = HOLD_BARS) -> dict:
    """Counts report over a single- or multi-symbol OHLCV frame; writes nothing."""
    _check(window, gap, hold_bars)
    if "symbol" in df.columns:
        parts = [
            audit_symbol(g, str(sym), window=window, gap=gap, hold_bars=hold_bars)
            for sym, g in df.groupby("symbol", sort=False)
        ]
        label = "<frame>"
    else:
        parts = [audit_symbol(df, "<frame>", window=window, gap=gap, hold_bars=hold_bars)]
        label = "<frame>"
    return {
        "label": label,
        "n_symbols": len(parts),
        "window": int(window),
        "gap": int(gap),
        "hold_bars": int(hold_bars),
        "totals": _aggregate(parts),
        "per_symbol": parts,
    }


def load_symbol_frame(path: Path, columns: tuple[str, ...] = ("date", "high", "low", "close")):
    """Column-projected single-symbol read (never a dataset scan over raw_ohlcv)."""
    return pq.read_table(Path(path), columns=list(columns)).to_pandas()


def audit_market(market: str, *, limit: int | None = None, root: Path = RAW_ROOT,
                 window: int = SWING_WINDOW, gap: int = CLUSTER_GAP,
                 hold_bars: int = HOLD_BARS) -> dict:
    """Symbol-sequential audit of ``market=<MKT>``; ``limit`` = first N symbols."""
    _check(window, gap, hold_bars)
    files = sorted((Path(root) / f"market={market}").glob("symbol=*.parquet"))
    if limit is not None:
        files = files[:limit]
    if not files:
        raise FileNotFoundError(f"no raw_ohlcv files for market={market} under {root}")
    per_symbol = [
        audit_symbol(
            load_symbol_frame(f), f.name[len("symbol=") : -len(".parquet")],
            window=window, gap=gap, hold_bars=hold_bars,
        )
        for f in files
    ]
    return {
        "market": market,
        "n_symbols": len(per_symbol),
        "limit": limit,
        "window": int(window),
        "gap": int(gap),
        "hold_bars": int(hold_bars),
        "totals": _aggregate(per_symbol),
        "per_symbol": per_symbol,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="WI-082 swing-overlap audit (read-only)")
    ap.add_argument("--market", default="ALL", choices=["USD", "CAD", "ALL"])
    ap.add_argument("--limit", type=int, default=10, help="first N symbols (dry-run)")
    ap.add_argument("--out", default=str(SMOKE_DIR))
    ap.add_argument("--window", type=int, default=SWING_WINDOW)
    ap.add_argument("--gap", type=int, default=CLUSTER_GAP)
    ap.add_argument("--hold-bars", type=int, default=HOLD_BARS)
    args = ap.parse_args(argv)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    markets = ["USD", "CAD"] if args.market == "ALL" else [args.market]
    stamp = "all" if args.limit is None else f"first{args.limit}"
    for mkt in markets:
        rep = audit_market(mkt, limit=args.limit, window=args.window, gap=args.gap,
                           hold_bars=args.hold_bars)
        path = out / f"overlap_audit_{mkt}_dryrun_{stamp}.json"
        path.write_text(json.dumps(rep, indent=2))
        t = rep["totals"]
        print(
            f"WI-082 overlap_audit {mkt}: symbols={rep['n_symbols']} "
            f"triggers={t['total_triggers']} pairs={t['overlapping_pairs']} "
            f"clusters={t['clusters']} suppressed={t['suppressed_by_no_concurrent']} -> {path}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
