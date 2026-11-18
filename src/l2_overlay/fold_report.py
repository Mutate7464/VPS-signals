"""WI-065 — the mandatory per-fold report (D-027 §7 fold ceiling). Emitted on every scored run.

`fold_report(oof_edges)` returns `{per_fold_net_edge, max_fold_share, ...}`. A run with no fold rows
must fail closed (a missing column is a defect, not a zero), so the builder raises
`FoldReportMissing` rather than returning an empty report.

Ceiling (D-027 §11.2): max single fold ≤ 50% of the CALIB net edge AND net edge positive in a
majority of folds; a ceiling failure is a CALIB failure (`fold_ceiling_ok == False`).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

FOLD_CEILING_SHARE = 0.5
__all__ = ["FoldReportMissing", "FOLD_CEILING_SHARE", "fold_report", "require_fold_report",
           "write_fold_report"]


class FoldReportMissing(ValueError):
    """Raised when a scored run carries no fold rows — the fold report is mandatory."""


def _pairs(oof_edges) -> list[tuple[int, float]]:
    """Accept `{fold: edge}` or the harness `fold_edges` row shape (`fold` + `edge`/`net_edge`)."""
    if oof_edges is None:
        return []
    if isinstance(oof_edges, dict):
        return [(int(f), float(e)) for f, e in oof_edges.items()]
    out: list[tuple[int, float]] = []
    for row in oof_edges:
        f, e = (row["fold"], row.get("net_edge", row.get("edge"))) if isinstance(row, dict) else row
        out.append((int(f), float(e)))
    return out


def require_fold_report(oof_edges) -> list[tuple[int, float]]:
    """Fail closed: a scored run without fold rows is a defect."""
    pairs = _pairs(oof_edges)
    if not pairs:
        raise FoldReportMissing("fold report missing: no per-fold net edge rows were supplied")
    return pairs


def fold_report(oof_edges) -> dict:
    """Per-fold net edge + the max-fold concentration share; raises if the rows are absent."""
    pairs = require_fold_report(oof_edges)
    per = {int(f): float(e) for f, e in pairs}
    vals = np.asarray(list(per.values()), dtype="float64")
    finite = vals[np.isfinite(vals)]
    total = float(finite.sum()) if finite.size else float("nan")
    # share of a *positive* total absorbed by the single largest fold; non-positive ⇒ no operating point
    share = float(finite.max() / total) if finite.size and total > 0.0 else float("inf")
    n, n_pos = int(finite.size), int((finite > 0.0).sum())
    return {"per_fold_net_edge": per, "max_fold_share": share, "total_net_edge": total,
            "n_folds": n, "n_positive_folds": n_pos,
            "fold_ceiling_ok": bool(share <= FOLD_CEILING_SHARE and 2 * n_pos > n)}


def write_fold_report(report: dict, path) -> Path:
    """Persist the report beside the run (JSON); the column is never silently dropped."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return path
