"""L1 bifurcation boundary: causal feature panel vs ex-post label namespaces (WI-080).

Design doc: ``docs/workflow/designs/D-029-l1-bifurcation.md``. License: D-023
layer 1 (predictive only) — this module defines and enforces a namespace split,
it computes no trading or economic metric.

Boundary rule (normative)
-------------------------
* **Causal panel (features):** bar ``t``'s close and earlier only. Trailing
  swing and retracement LEVELS are emitted at the bar where they are *confirmed*
  (the confirmation date) — never back-filled onto the pivot bar, never revised
  by a later bar.
* **Ex-post label namespaces (labels, never features, never exported):** anything
  forward looking — ``fwd_*`` (forward returns and forward realized vol),
  ``y_*`` / ``label_*`` / ``target_*`` (outcome labels), and the excursion /
  capture statistics ``mfe``, ``mae``, ``capture_eff*``.
* **Model outputs (``p_*``, ``fold_*``):** predictions and fold ids are not panel
  features either; they are rejected by :func:`assert_boundary` alongside the
  label namespaces. Keys/context (``symbol``, ``date``, ``market``, ``close``,
  ``atr``, ``state``) are allowed.

Repo invariants honoured: symbol-sequential computation (never cross a symbol
boundary), float32 immediately after calculation, index reset before concat
(RISKS R-08), n_jobs=2 (this module is single-process, pure pandas/numpy).
"""
from __future__ import annotations

from collections.abc import Iterable, Sequence

import pandas as pd

WINDOW = 20  # trailing swing/retracement confirmation window (bars)
N_JOBS = 2  # declared, unused: symbol-sequential, I/O-free
EXPOST_PREFIXES: tuple[str, ...] = ("fwd_", "y_", "label_", "target_")
MODEL_OUTPUT_PREFIXES: tuple[str, ...] = ("p_", "fold_")
EXPOST_TOKENS = frozenset({"mfe", "mae", "capture"})
EXPOST_NAMES = frozenset({"mfe", "mae", "fwd_vol", "fwd_rvol", "capture_eff",
                          "capture_efficiency"})
KEY_COLUMNS = ("symbol", "date", "market")


class BoundaryViolation(AssertionError):
    """Raised when an ex-post label or a model output is passed as a feature."""


def is_expost_label(name: str) -> bool:
    """True for ex-post label-only columns (MFE/MAE, capture eff., fwd-vol, ``y_*``)."""
    s = str(name).strip().lower()
    if s in EXPOST_NAMES or s.startswith(EXPOST_PREFIXES):
        return True
    return bool(EXPOST_TOKENS & set(s.split("_")))


def is_model_output(name: str) -> bool:
    """True for prediction / fold-id columns (never features)."""
    return str(name).strip().lower().startswith(MODEL_OUTPUT_PREFIXES)


def is_non_feature(name: str) -> bool:
    """True for any column that must never be exported as a feature."""
    return is_expost_label(name) or is_model_output(name)


def label_only_columns(panel_columns: Iterable[str]) -> list[str]:
    """Return the non-feature columns found in ``panel_columns`` (order kept)."""
    return [str(c) for c in panel_columns if is_non_feature(c)]


def assert_boundary(panel_columns: Sequence[str]) -> list[str]:
    """Assert ``panel_columns`` is a causal feature panel; return it as a list.

    Returns the validated column names in input order. Raises
    :class:`BoundaryViolation` (an ``AssertionError``) naming every ex-post
    label / model-output column found, so contamination fails loudly instead of
    being exported as a feature.
    """
    offending = label_only_columns(panel_columns)
    if offending:
        raise BoundaryViolation(
            f"{len(offending)} non-feature column(s) inside the L1 boundary: {offending}"
        )
    return [str(c) for c in panel_columns]


def to_float32(df: pd.DataFrame, exclude: Sequence[str] = KEY_COLUMNS) -> pd.DataFrame:
    """Cast numeric/bool columns to float32 immediately after calculation."""
    out = df.copy(deep=False)
    for col in out.columns:
        if col in exclude:
            continue
        s = out[col]
        if (pd.api.types.is_float_dtype(s) or pd.api.types.is_integer_dtype(s)
                or pd.api.types.is_bool_dtype(s)):
            out[col] = s.astype("float32")
    return out


def concat_frames(frames: Iterable[pd.DataFrame]) -> pd.DataFrame:
    """Concat per-symbol frames with the index reset first (RISKS R-08)."""
    parts = [f.reset_index(drop=True) for f in frames]
    if not parts:
        raise ValueError("concat_frames: no frames")
    return pd.concat(parts, ignore_index=True).reset_index(drop=True)


def _levels_one(d: pd.DataFrame, window: int, retrace: float) -> pd.DataFrame:
    """Trailing levels for one symbol, confirmation-dated and index-reset."""
    d = d.sort_values("date").reset_index(drop=True)
    high = d["high"].astype("float64")
    low = d["low"].astype("float64")
    lh = high.rolling(window, min_periods=window).max()
    ll = low.rolling(window, min_periods=window).min()
    rng = lh - ll
    # zero-width range carries no retracement evidence -> NaN, never 0.0
    r = (ll + retrace * rng).where(rng > 0)
    return pd.DataFrame({
        "date": d["date"].to_numpy(),
        "level_high": lh.to_numpy(),
        "level_low": ll.to_numpy(),
        f"retrace_{int(round(retrace * 100))}": r.to_numpy(),
    })


def trailing_level(panel: pd.DataFrame, window: int = WINDOW,
                   retrace: float = 0.5) -> pd.DataFrame:
    """Causal trailing swing + retracement LEVELS, dated at their confirmation bar.

    Bar ``t`` uses bars ``t-window+1..t`` only, so a level is emitted at the bar
    that confirms it and is never back-filled onto its pivot bar. Windows are
    NaN-propagating: the first ``window-1`` bars per symbol are NaN, and a
    zero-width range gives NaN for the retracement column. Output is float32;
    the index is reset before concat across symbols (RISKS R-08).
    """
    if window < 2:
        raise ValueError("window must be >= 2")
    if not 0.0 < retrace < 1.0:
        raise ValueError("retrace must be in (0, 1)")
    rcol = f"retrace_{int(round(retrace * 100))}"
    if "symbol" in panel.columns:
        parts = [
            _levels_one(g, window, retrace).assign(symbol=g["symbol"].iloc[0])
            for _, g in panel.groupby("symbol", sort=False)
        ]
        out = concat_frames(parts)[["symbol", "date", "level_high", "level_low", rcol]]
    else:
        out = _levels_one(panel, window, retrace).reset_index(drop=True)
    return to_float32(out).reset_index(drop=True)
