"""WI-050 Phase 0 — precision@k / top-decile diagnostic over existing OOF scores.

Pure-python (numpy only) diagnostic on the WI-040 join schema (``y:int8``,
``p:float32`` plus optional ``symbol,date,h,k``): no training, no new data, no
file writes. Answers "if I took the top-k ranked events, how many positives do I
get, and are the top scores calibrated?" — a ranking/calibration read only; no
threshold, no entry rule and no trading claim follows (L1 predictive).

Invariants: no cross-symbol concat (callers pass one market's OOF frame),
float32 inputs, nothing written to disk.
"""

from __future__ import annotations

import numpy as np

DEFAULT_KS: tuple[int, ...] = (10, 25, 50, 100)
"""Row counts ranked desc by ``p`` — k counts rows, not symbols or dates."""

__all__ = ["DEFAULT_KS", "lift_at_k", "precision_at_k", "top_decile_calibration"]


def _prep(y, p) -> tuple[np.ndarray, np.ndarray]:
    """1-D ``int8`` labels + finite ``float64`` scores (NaN scores dropped)."""
    y_arr = np.asarray(y)
    p_arr = np.asarray(p, dtype="float64")
    if y_arr.ndim != 1 or p_arr.ndim != 1:
        raise ValueError("y and p must be 1-D")
    if y_arr.shape[0] != p_arr.shape[0]:
        raise ValueError("y and p must have equal length")
    y_bin = (np.nan_to_num(y_arr.astype("float64"), nan=0.0) != 0).astype("int8")
    keep = np.isfinite(p_arr)
    return y_bin[keep], p_arr[keep]


def _ranked_cumsum(y_bin: np.ndarray, p_fin: np.ndarray) -> np.ndarray:
    """Cumulative positive count after ranking scores desc (stable on ties)."""
    order = np.argsort(-p_fin, kind="stable")
    return np.cumsum(y_bin[order], dtype="float64")


def precision_at_k(y, p, ks=DEFAULT_KS) -> dict[int, float]:
    """Fraction of positives inside the top-``k`` scores, for each ``k`` in ``ks``.

    Rows are ranked by ``p`` descending (ties broken by a stable sort, i.e. the
    input order), ``NaN`` scores are dropped first and ``k`` counts rows. ``k``
    larger than the row count uses every row; ``k <= 0`` is skipped. Empty (or
    all-NaN) input returns ``{}``.
    """
    y_bin, p_fin = _prep(y, p)
    n = int(y_bin.size)
    if n == 0:
        return {}
    csum = _ranked_cumsum(y_bin, p_fin)
    out: dict[int, float] = {}
    for k in ks:
        k = int(k)
        if k <= 0:
            continue
        take = min(k, n)
        out[k] = float(csum[take - 1] / take)
    return out


def top_decile_calibration(y, p, n_bins: int = 10) -> dict:
    """Equal-width probability-bin calibration of the top scores.

    Returns ``{"ece": float, "bins": [(lo, hi, mean_p, frac_pos, n), ...]}`` with
    one tuple per non-empty bin (last bin closed on the right). Scores are
    clipped to ``[0, 1]`` so every dropped-NaN row lands in a bin; ``ece`` is the
    count-weighted mean absolute gap ``|frac_pos - mean_p|``. Empty (or all-NaN)
    input returns ``{"ece": nan, "bins": []}``.
    """
    y_bin, p_fin = _prep(y, p)
    n = int(y_bin.size)
    if n == 0:
        return {"ece": float("nan"), "bins": []}
    p_fin = np.clip(p_fin, 0.0, 1.0)
    n_bins = max(1, int(n_bins))
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    bins: list[tuple[float, float, float, float, int]] = []
    ece = 0.0
    for i in range(n_bins):
        lo, hi = float(edges[i]), float(edges[i + 1])
        mask = ((p_fin >= lo) & (p_fin < hi) if i < n_bins - 1
                else (p_fin >= lo) & (p_fin <= hi))
        cnt = int(mask.sum())
        if cnt == 0:
            continue
        mean_p = float(p_fin[mask].mean())
        frac_pos = float(y_bin[mask].mean())
        bins.append((lo, hi, mean_p, frac_pos, cnt))
        ece += (cnt / n) * abs(frac_pos - mean_p)
    return {"ece": float(ece), "bins": bins}


def lift_at_k(y, p, k: int) -> float:
    """``precision_at_k / base_rate`` — ``nan`` when empty or no positives."""
    y_bin, p_fin = _prep(y, p)
    if y_bin.size == 0:
        return float("nan")
    base = float(y_bin.mean())
    prec = precision_at_k(y_bin, p_fin, ks=(k,)).get(int(k))
    if prec is None or base <= 0.0:
        return float("nan")
    return float(prec / base)
