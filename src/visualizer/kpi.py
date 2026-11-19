"""KPI strip for the audit workbench (WI-086) - evidence only, never a verdict.

Every KPI is returned with the mandatory watermark so no number can be read
without its caveat. Definitions follow plan 26-W47:

- trades/yr    retained rows / years in the selected date range (overlaps counted)
- hit rate     mean(label) over the retained rows
- lift         hit rate / unfiltered base rate for the same target and period
- EV           mean forward ATR return for the horizon matching the target
               (15 for `y_15d_*`, 20 for `y_20d_*`)
- profit factor sum(positive) / |sum(negative)| of the same signed returns

The sign convention for the low/down targets is an OPEN QUESTION (D-028). It is a
config flag (`sign_mode`), reported in the payload and flagged in the UI; the raw
reading is never silently flipped.
"""
from __future__ import annotations

import re
from typing import Iterable

import pandas as pd

WATERMARK = "evidence only - no verdicts; out-of-fold, but threshold-selection bias risk"
HORIZON_RE = re.compile(r"^y_(\d+)d_")
EV_SIGN_MODES: tuple[str, ...] = ("raw", "negate_low_down")
SIGN_MODE_DEFAULT = "raw"
LOW_DOWN_TARGETS: tuple[str, ...] = ("y_15d_low", "y_20d_down")
KPI_ORDER: tuple[str, ...] = ("trades_per_year", "hit_rate", "lift", "ev", "profit_factor")
KPI_UNITS: dict[str, str] = {
    "trades_per_year": "trades/yr",
    "hit_rate": "fraction",
    "lift": "x base rate",
    "ev": "ATR units",
    "profit_factor": "x",
}
DATE_COLUMN = "date"


def canonical_target(target: str) -> str:
    """Normalise an oof label/probability name onto the targets-file label (`y_y_15d_high` -> `y_15d_high`)."""
    text = str(target)
    for prefix in ("y_y_", "p_y_"):
        if text.startswith(prefix):
            return "y_" + text[len(prefix) :]
    return text


def horizon_for(target: str) -> int:
    match = HORIZON_RE.match(canonical_target(target))
    if not match:
        raise ValueError(f"no EV horizon in target name: {target!r}")
    return int(match.group(1))


def ev_column_for(target: str) -> str:
    return f"fwd_atr_ret_{horizon_for(target)}"


def sign_for(target: str, sign_mode: str = SIGN_MODE_DEFAULT) -> float:
    if sign_mode not in EV_SIGN_MODES:
        raise ValueError(f"sign_mode must be one of {EV_SIGN_MODES}, got {sign_mode!r}")
    flipped = sign_mode == "negate_low_down" and canonical_target(target) in LOW_DOWN_TARGETS
    return -1.0 if flipped else 1.0


def sign_mode_note(target: str, sign_mode: str = SIGN_MODE_DEFAULT) -> str:
    """The UI flag for the unresolved sign convention (never hidden)."""
    if canonical_target(target) in LOW_DOWN_TARGETS:
        return (
            f"Open question: sign convention for {canonical_target(target)} is unresolved; "
            f"sign_mode={sign_mode} (EV and profit factor read as-is unless flipped by config)."
        )
    return f"sign_mode={sign_mode}; no down-side sign question for {canonical_target(target)}."


def years_in_range(dates: Iterable) -> float:
    values = pd.to_datetime(pd.Series(list(dates))).dropna()
    if values.empty:
        return 0.0
    span_days = (values.max() - values.min()).total_seconds() / 86400.0
    return float(span_days / 365.25)


def base_rate_for(frame: pd.DataFrame, target: str, label_column: str | None = None) -> float:
    column = label_column or target
    if column not in frame.columns:
        raise KeyError(f"base frame has no label column {column!r}")
    return float(pd.Series(frame[column], dtype="float64").mean())


def compute_kpis(
    retained: pd.DataFrame,
    target: str,
    base_rate: float | None = None,
    years: float | None = None,
    sign_mode: str = SIGN_MODE_DEFAULT,
    label_column: str | None = None,
    ev_column: str | None = None,
) -> dict:
    """Raw KPI values over the retained rows (float64 arithmetic, 1e-6 reproducible)."""
    label_column = label_column or target
    if label_column not in retained.columns:
        raise KeyError(f"retained frame has no label column {label_column!r}")
    ev_column = ev_column or ev_column_for(target)
    if ev_column not in retained.columns:
        raise KeyError(f"retained frame has no forward-return column {ev_column!r}")
    sign = sign_for(target, sign_mode)
    labels = pd.Series(retained[label_column], dtype="float64")
    signed = pd.Series(retained[ev_column], dtype="float64") * sign
    if years is None:
        years = years_in_range(retained[DATE_COLUMN]) if DATE_COLUMN in retained.columns else 0.0
    negative = signed[signed < 0].sum()
    positive = signed[signed > 0].sum()
    base = float(base_rate) if base_rate is not None else float("nan")
    return {
        "n_rows": int(labels.size),
        "n_return_rows": int(signed.notna().sum()),
        "years": float(years),
        "trades_per_year": float(labels.size / years) if years and years > 0 else float("nan"),
        "hit_rate": float(labels.mean()),
        "base_rate": base,
        "lift": float(labels.mean() / base) if base and base > 0 else float("nan"),
        "ev": float(signed.mean()),
        "profit_factor": float(positive / abs(negative)) if abs(negative) > 0 else float("nan"),
        "ev_column": ev_column,
        "ev_horizon": horizon_for(target),
        "sign": sign,
        "sign_mode": sign_mode,
    }


def kpi_strip(
    retained: pd.DataFrame,
    target: str,
    base_frame: pd.DataFrame | None = None,
    market: str | None = None,
    years: float | None = None,
    sign_mode: str = SIGN_MODE_DEFAULT,
    label_column: str | None = None,
    ev_column: str | None = None,
) -> dict:
    """Watermarked KPI payload: every KPI carries the caveat in its own entry."""
    base_rate = base_rate_for(base_frame, target, label_column) if base_frame is not None else None
    values = compute_kpis(
        retained,
        target,
        base_rate=base_rate,
        years=years,
        sign_mode=sign_mode,
        label_column=label_column,
        ev_column=ev_column,
    )
    kpis = {
        name: {"value": values[name], "units": KPI_UNITS[name], "watermark": WATERMARK}
        for name in KPI_ORDER
    }
    for name, units in (("base_rate", "fraction"), ("n_rows", "rows")):
        kpis[name] = {"value": values[name], "units": units, "watermark": WATERMARK}
    return {
        "market": market.upper() if market else None,
        "target": target,
        "ev_column": values["ev_column"],
        "ev_horizon": values["ev_horizon"],
        "sign_mode": values["sign_mode"],
        "sign": values["sign"],
        "years": values["years"],
        "watermark": WATERMARK,
        "kpis": kpis,
        "notes": [sign_mode_note(target, sign_mode)],
    }


def render_strip(payload: dict) -> list[dict]:
    """Flat label/value rows for the KPI strip - each row repeats the watermark."""
    rows = []
    for name in KPI_ORDER + ("base_rate", "n_rows"):
        entry = payload["kpis"][name]
        rows.append(
            {
                "label": name.replace("_", " "),
                "value": entry["value"],
                "units": entry["units"],
                "watermark": entry["watermark"],
            }
        )
    return rows
