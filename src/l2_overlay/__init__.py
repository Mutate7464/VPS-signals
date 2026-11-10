"""Layer-2 overlay protocol package (D-024 §2) — one harness, not per-WI scripts.

Re-exports are lazy (PEP 562) so `python -m src.l2_overlay.harness` stays warning-free.
"""
from __future__ import annotations

_NAMES = ("MIN_CALIB_EVENTS", "N_PLACEBO_SEEDS", "PLACEBO_Z_MIN", "TAU_GRID", "OverlayResult",
          "classify", "feasible", "fold_edges", "pick_tau_by_calib_edge", "placebo_z",
          "run_overlay", "score_eval", "selected_mask", "synthetic_fixture", "write_report")

__all__ = list(_NAMES)


def __getattr__(name):
    if name in _NAMES:
        from src.l2_overlay import harness
        return getattr(harness, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
