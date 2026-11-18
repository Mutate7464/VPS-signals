"""WI-067 — the pruning stage of the L2 stack (D-027 §6/§10.3): cells → clusters → logged representatives.

The union carries thousands of overlapping cells; a regularised fit over near-duplicate columns is
unstable and memory-hungry. So before any fit the CALIB OOF **cell matrix** is read (chunked, float32,
symbol-sequential) and collapsed to one score per correlation cluster. Nothing is dropped silently: the
returned log lists every input cell with its cluster, its representative and a reason.

    from src.l2_overlay import prune
    cl = prune.cluster_by_correlation(oof_matrix, threshold=0.7)
    scores = prune.cluster_scores(oof_matrix, cl)      # float32, one column per cluster

Invariants: CALIB-only input (EVAL is never read), float32 immediately, chunked reads, deterministic
(input order breaks every tie), n_jobs=2 (nothing here fans out, kept explicit).
"""
from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

import numpy as np
import pandas as pd

from src.l2_overlay import harness as H

BASE_DIR = Path(__file__).resolve().parents[2]
UNION_OOF_ROOT = BASE_DIR / "data" / "models" / "l2_union_oof"    # per-cell CALIB OOF score artifacts
PRUNE_THRESHOLD, MIN_PERIODS = 0.7, 50
CELL_BATCH_ROWS, N_JOBS = 250_000, 2                              # chunked reads; repo law
MEMORY_CEILING_GB, FULL_SCALE = 8.0, (500_000, 120)               # §10.3: events x design columns
__all__ = ["Clustering", "PRUNE_THRESHOLD", "MIN_PERIODS", "UNION_OOF_ROOT", "FULL_SCALE",
           "MEMORY_CEILING_GB", "load_cell_matrix", "projected_peak_gb", "assert_memory_budget",
           "correlation_matrix", "cluster_by_correlation", "cluster_scores", "log_frame"]


class Clustering(NamedTuple):
    """`cell -> cluster` for **every** input cell, `cluster -> representative cell`, and the log."""
    cell_cluster: dict    # str -> int
    cluster_rep: dict     # int -> str
    log: list             # one row per input cell: cell/cluster/representative/kept/reason


def correlation_matrix(oof_matrix, *, min_periods: int = MIN_PERIODS) -> pd.DataFrame:
    """Absolute pairwise Spearman ρ across cells (NaN-safe pairwise); diagonal forced to 0."""
    frame = pd.DataFrame(oof_matrix).astype("float32")
    if frame.shape[1] == 0:
        raise ValueError("pruning needs at least one cell column")
    rho = frame.corr(method="spearman", min_periods=int(min_periods)).abs().fillna(0.0)
    arr = np.array(rho.to_numpy(dtype="float64"), copy=True)
    np.fill_diagonal(arr, 0.0)
    return pd.DataFrame(arr, index=rho.index.astype(str), columns=rho.columns.astype(str))


def _hub(rho: pd.DataFrame, members: list[str]) -> str:
    """Cluster member with the highest total |ρ| to the others (ties resolve by input order)."""
    if len(members) == 1:
        return members[0]
    sums = [float(rho.loc[m, [o for o in members if o != m]].sum()) for m in members]
    return members[int(np.argmax(sums))]


def cluster_by_correlation(oof_matrix, threshold: float = PRUNE_THRESHOLD, *,
                           min_periods: int = MIN_PERIODS) -> Clustering:
    """Greedy single-link clustering on |ρ| > `threshold`; log every input cell, keep every rep."""
    rho = correlation_matrix(oof_matrix, min_periods=min_periods)
    cells = [str(c) for c in rho.columns]
    cell_cluster: dict[str, int] = {}
    members: dict[int, list[str]] = {}
    for cell in cells:
        hit = next((c for c in sorted(members) if rho.at[cell, members[c][0]] > float(threshold)), None)
        if hit is None:
            hit = len(members)
            members[hit] = [cell]
        else:
            members[hit].append(cell)
        cell_cluster[cell] = hit
    cluster_rep = {c: _hub(rho, mem) for c, mem in members.items()}
    log = [{"cell": c, "cluster": int(cell_cluster[c]), "representative": cluster_rep[cell_cluster[c]],
            "kept": c == cluster_rep[cell_cluster[c]],
            "reason": ("cluster representative" if c == cluster_rep[cell_cluster[c]]
                       else f"|rho|>{float(threshold):g} with {cluster_rep[cell_cluster[c]]}")} for c in cells]
    return Clustering(cell_cluster, cluster_rep, log)


def cluster_scores(oof_matrix, clustering: Clustering) -> pd.DataFrame:
    """One float32 score per cluster: row-wise mean of the cluster's z-scored members."""
    frame = pd.DataFrame(oof_matrix).astype("float32")
    frame.columns = [str(c) for c in frame.columns]
    z = ((frame - frame.mean()) / frame.std(ddof=0).replace(0.0, np.nan)).astype("float32")
    out: dict[str, np.ndarray] = {}
    for cluster, rep in sorted(clustering.cluster_rep.items()):
        members = [c for c, k in clustering.cell_cluster.items() if int(k) == int(cluster) and c in z.columns]
        out[f"cl{int(cluster):02d}_{rep}"] = np.nanmean(z[members].to_numpy("float32"), axis=1).astype("float32")
    return pd.DataFrame(out, index=frame.index, dtype="float32")


def log_frame(clustering: Clustering) -> pd.DataFrame:
    """The pruning log as a frame (report table / completeness assertions)."""
    return pd.DataFrame(clustering.log, columns=["cell", "cluster", "representative", "kept", "reason"])


def load_cell_matrix(market: str, *, root=None, batch_rows: int = CELL_BATCH_ROWS):
    """CALIB OOF cell matrix keyed (date, symbol) + a load log (a missing artifact is logged, not dropped).

    Cells come from the WI-065 union loader (cell-key dedup, no cell twice). Each cell artifact is read in
    float32 batches (`pyarrow.dataset`), never as one all-ticker frame.
    """
    import pyarrow.dataset as ds

    base = Path(root) if root is not None else UNION_OOF_ROOT
    sub = H.load_union()
    sub = sub.loc[sub["market"].astype(str) == market]
    frame, log = None, []
    for _, row in sub.iterrows():
        cell, lib = str(row["cell_key"]), str(row["library"])
        path = base / lib / f"{cell.replace('|', '__')}.parquet"
        if not path.exists():
            log.append({"cell": cell, "status": "missing", "rows": 0})
            continue
        scanner = ds.dataset(path, format="parquet").scanner(columns=["date", "symbol", "score"],
                                                             batch_size=int(batch_rows))
        part = pd.concat([b.to_pandas() for b in scanner.to_batches()], ignore_index=True)
        part = part.rename(columns={"score": cell}).astype({cell: "float32"})   # float32 immediately
        part["date"], part["symbol"] = pd.to_datetime(part["date"]), part["symbol"].astype(str)
        frame = part if frame is None else frame.merge(part, on=["date", "symbol"], how="outer", sort=True)
        log.append({"cell": cell, "status": "loaded", "rows": int(len(part))})
    if frame is None:
        raise FileNotFoundError(f"no union OOF score artifacts under {base} for market={market}")
    return frame.reset_index(drop=True), log


def projected_peak_gb(n_events: int, n_cols: int, *, overhead: float = 3.0) -> float:
    """Smoke-scaled extrapolation: float32 matrix + float64 correlation/fit workspace."""
    return float(overhead * (4.0 * n_events * n_cols + 8.0 * n_cols ** 2 + 8.0 * n_events * (n_cols + 9)) / 1e9)


def assert_memory_budget(n_events: int, n_cols: int, *, ceiling_gb: float = MEMORY_CEILING_GB) -> dict:
    """Extrapolate the smoke scale to the full run; over the ceiling the card pauses for admin."""
    gb = projected_peak_gb(n_events, n_cols)
    if gb >= float(ceiling_gb):
        raise MemoryError(f"projected peak {gb:.2f} GB >= ceiling {ceiling_gb:.1f} GB — pause for admin")
    return {"projected_peak_gb": gb, "ceiling_gb": float(ceiling_gb), "n_events": int(n_events),
            "n_cols": int(n_cols)}
