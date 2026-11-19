"""Barrier overlays for View 3 (WI-088): recomputed display math, never a label source.

Levels are ``close_entry +/- k*ATR_entry``, where ``k`` (barrier multiplier) and ``h``
(vertical barrier) are read from ``data/models/wi048/<family>_cells.json`` and the ATR is
the Wilder ATR at the entry bar (trailing, causal). First touch is recomputed from the
raw high/low path over bars ``[t+1, t+h]`` and compared with the stored ``y_*`` value;
disagreement is a MISMATCH badge and is NEVER reconciled (D-028).

``_pl0/1/2`` semantics are an OPEN QUESTION (D-028), so the stored label is decoded with
one documented convention (``POSITIVE_TOUCH`` = "up") and the mismatch rate is evidence,
not an error. When a cell's geometry underdetermines the levels the overlay is omitted
and labelled "not reproducible".
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

from src.visualizer import REPO_ROOT

MODEL_DIR = REPO_ROOT / "data" / "models" / "wi048"
CELL_SUFFIX = "_cells.json"
DEFAULT_FAMILY = "high_low"
DEFAULT_HORIZON = 5

ARTIFACT_CLASS = "artifact, read-only"
OVERLAY_CLASS = "recomputed display math"
OVERLAY_LABEL = "not label source"
REPRODUCIBLE, NOT_REPRODUCIBLE = "reproducible", "not reproducible"
MATCH, MISMATCH, UNRESOLVED = "match", "MISMATCH", "unresolved"
TOUCH_UP, TOUCH_DOWN, TOUCH_NONE = "up", "down", "none"
#: Same-bar tie -> stop side wins (mirrors `src.swing_bsh.events._first_touch`, D-016).
TIE_WINS = TOUCH_DOWN
#: Documented decode of the stored binary label; `_pl*` semantics are unresolved (D-028).
POSITIVE_TOUCH = TOUCH_UP
SAMPLE_EVENTS = 100
MISMATCH_NOTE = (
    "stored label decoded by convention (1 == up barrier first); _pl0/1/2 semantics are "
    "unresolved (D-028) - a nonzero mismatch rate is evidence, never reconciled"
)


@dataclass(frozen=True)
class BarrierGeometry:
    """Recomputed barrier levels for one event, or an omitted (not reproducible) overlay."""

    market: str
    family: str
    h: int | None
    k: float | None
    reproducible: bool
    entry_close: float | None
    atr_entry: float | None
    upper: float | None
    lower: float | None
    reason: str | None
    boundary_class: str = OVERLAY_CLASS
    boundary_label: str = OVERLAY_LABEL

    def as_dict(self) -> dict:
        return asdict(self)


def cells_path(family: str, model_dir: Path | str = MODEL_DIR) -> Path:
    return Path(model_dir) / f"{family}{CELL_SUFFIX}"


def available_families(model_dir: Path | str = MODEL_DIR) -> list[str]:
    return sorted(p.name[: -len(CELL_SUFFIX)] for p in Path(model_dir).glob(f"*{CELL_SUFFIX}"))


def load_cells(family: str = DEFAULT_FAMILY, model_dir: Path | str = MODEL_DIR) -> list[dict]:
    """Read one wi048 family sidecar (read-only JSON); the `cells` list is returned as-is."""
    payload = json.loads(cells_path(family, model_dir).read_text(encoding="utf-8"))
    return list(payload.get("cells") or [])


def select_cell(cells, market=None, h=None, learner=None, variant=None) -> dict | None:
    """First cell matching the filters; `None` when the grid does not carry one."""
    for cell in cells:
        if market is not None and str(cell.get("market", "")).upper() != str(market).upper():
            continue
        if h is not None and int(cell.get("h", -1)) != int(h):
            continue
        if learner is not None and cell.get("learner") != learner:
            continue
        if variant is not None and cell.get("variant") != variant:
            continue
        return cell
    return None


def _finite(value) -> bool:
    try:
        return bool(np.isfinite(float(value)))
    except (TypeError, ValueError):
        return False


def geometry_from_cell(cell, entry_close, atr_entry) -> BarrierGeometry:
    """Levels from cell `k`/`h` x ATR at entry; omitted + labelled when underdetermined."""
    cell = cell or {}
    family = str(cell.get("family", DEFAULT_FAMILY))
    market = str(cell.get("market", "")).upper()
    h, k = cell.get("h"), cell.get("k")

    def omitted(reason: str) -> BarrierGeometry:
        return BarrierGeometry(
            market, family, h, k, False, entry_close, atr_entry, None, None, reason,
            OVERLAY_CLASS, NOT_REPRODUCIBLE,
        )

    if not cell:
        return omitted("no wi048 cell selected for this family/horizon")
    if not _finite(k):
        return omitted("cell geometry lacks a finite k (barrier multiplier)")
    if h is None:
        return omitted("cell geometry lacks h (vertical barrier)")
    if not _finite(entry_close):
        return omitted("entry close is not finite")
    if not _finite(atr_entry) or float(atr_entry) <= 0.0:
        return omitted("ATR at entry is not finite/positive")
    return BarrierGeometry(
        market, family, int(h), float(k), True, float(entry_close), float(atr_entry),
        float(entry_close) + float(k) * float(atr_entry),
        float(entry_close) - float(k) * float(atr_entry), None, OVERLAY_CLASS, OVERLAY_LABEL,
    )


def first_touch(high, low, entry_close, atr_entry, k, h, tie: str = TIE_WINS) -> dict:
    """Recomputed first touch over forward bars [t+1, t+h] (pessimistic same-bar tie)."""
    bars = max(0, int(h))
    high = np.asarray(high, dtype="float64")[:bars]
    low = np.asarray(low, dtype="float64")[:bars]
    upper = float(entry_close) + float(k) * float(atr_entry)
    lower = float(entry_close) - float(k) * float(atr_entry)
    up = np.flatnonzero(high >= upper)
    dn = np.flatnonzero(low <= lower)
    ou = int(up[0]) + 1 if up.size else None
    ol = int(dn[0]) + 1 if dn.size else None
    if ou is None and ol is None:
        touch = TOUCH_NONE
    elif ou is not None and ol is not None and ou == ol:
        touch = tie
    elif ol is None or (ou is not None and ou < ol):
        touch = TOUCH_UP
    else:
        touch = TOUCH_DOWN
    return {
        "touch": touch, "up_offset": ou, "down_offset": ol, "bars_scanned": int(high.size),
        "upper": upper, "lower": lower, "tie_wins": tie,
        "boundary_class": OVERLAY_CLASS, "boundary_label": OVERLAY_LABEL,
    }


def mismatch(recomputed_touch, stored_value, positive_touch: str = POSITIVE_TOUCH) -> dict:
    """MISMATCH badge from the recomputed up-touch vs the stored `y_*` binary label."""
    base = {
        "recomputed_touch": recomputed_touch, "positive_touch": positive_touch,
        "reconciled": False, "boundary_class": OVERLAY_CLASS,
        "boundary_label": OVERLAY_LABEL, "note": MISMATCH_NOTE,
    }
    if stored_value is None or not _finite(stored_value):
        return dict(base, badge=UNRESOLVED, agrees=None, stored_value=None,
                    recomputed_positive=None, stored_positive=None)
    recomputed_positive = bool(recomputed_touch == positive_touch)
    stored_positive = bool(float(stored_value) > 0)
    agrees = recomputed_positive == stored_positive
    return dict(
        base, badge=MATCH if agrees else MISMATCH, agrees=bool(agrees),
        stored_value=float(stored_value), recomputed_positive=recomputed_positive,
        stored_positive=stored_positive,
    )


def mismatch_rate(records, sampled: int = SAMPLE_EVENTS) -> dict:
    """Mismatch rate over sampled events - reported as evidence, never reconciled."""
    scored = [r for r in records if r.get("agrees") is not None]
    bad = sum(1 for r in scored if not r["agrees"])
    return {
        "n_sampled": len(records), "n_scored": len(scored), "mismatches": int(bad),
        "rate": (float(bad) / len(scored)) if scored else None,
        "sampled_target": int(sampled),
        "badge_rule": "recomputed up-touch vs stored label > 0",
        "reconciled": False, "boundary_class": OVERLAY_CLASS, "boundary_label": OVERLAY_LABEL,
        "note": MISMATCH_NOTE,
    }
