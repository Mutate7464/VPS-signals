"""View 2 - threshold sweep on OOF probabilities (WI-089).

Sweep the OOF probability threshold across its quantiles and report, per step, retained
rows, trades/yr, hit rate, lift, EV and profit factor (definitions from
``src.visualizer.kpi``). The ~200 trades/yr product aspiration is drawn as an ILLUSTRATIVE
reference line: a display line only, which gates nothing (north-star rule).

Read path: one column projection - ``date`` plus ``p_*``, ``y_y_*`` and ``fwd_atr_ret_h`` -
from ``data/oof_{MKT}.parquet`` through ``VisualizerLoader``: float32, no dataset scan, no
per-symbol reads. Nothing is persisted; the only writable location in the UI process
(``state/viz/``) belongs to the loader. The sweep is a prefix-sum walk over the probability
order, retaining exactly ``p >= quantile(values, level)`` - the multiset the pandas
reference in the tests checks.
"""
from __future__ import annotations

import json
import time

import numpy as np
import pandas as pd

from src.visualizer import controls, kpi, schema

VIEW_NAME = "v2_sweep"
DATE_COLUMN = "date"
DEFAULT_STEPS = 41
STEP_LIMIT = 100
REFERENCE_TRADES_PER_YEAR = 200.0
REFERENCE_LABEL = "ILLUSTRATIVE"
REFERENCE_NOTE = (
    "~200 trades/yr is the product aspiration (AGENTS.md), drawn as a display line only: "
    "it is ILLUSTRATIVE, not a target, and it gates nothing in this tool."
)
COMPUTE_BUDGET_MS = 400.0
SERIALIZE_BUDGET_MS = 100.0
PAYLOAD_LIMIT_BYTES = 200 * 1024


def columns_for(target: str) -> dict[str, str]:
    """OOF columns behind a selector: ``p_y_*`` probabilities and ``y_y_*`` labels."""
    canonical = kpi.canonical_target(target)
    if canonical not in schema.OOF_TARGETS:
        raise KeyError(f"no OOF probability for selector {target!r}; OOF targets are {schema.OOF_TARGETS}")
    columns = {"target": canonical, "prob_column": f"p_{canonical}",
               "label_column": f"y_{canonical}", "ev_column": kpi.ev_column_for(canonical)}
    missing = [name for key, name in columns.items()
               if key != "target" and name not in schema.OOF_CANONICAL_COLUMNS]
    if missing:
        raise KeyError(f"selector {target!r} maps outside the canonical OOF columns: {missing}")
    return columns


def load_prob_frame(loader, market: str, columns: dict, date_range=None) -> tuple[pd.DataFrame, dict]:
    """One projected OOF read; the spec date range is applied, NaN rows are dropped."""
    market = str(market).upper()
    requested = [columns["prob_column"], columns["label_column"], columns["ev_column"]]
    frame = loader.load_columns(market, requested, source="oof")[[DATE_COLUMN] + requested].copy()
    rows_read = int(len(frame))
    rows_in_range = rows_read
    if date_range:
        low, high = (pd.Timestamp(value) for value in date_range)
        dates = pd.to_datetime(frame[DATE_COLUMN])
        mask = ((dates >= low) & (dates <= high)).to_numpy()
        frame, rows_in_range = frame.loc[mask].reset_index(drop=True), int(mask.sum())
    keep = frame[requested[0]].notna() & frame[requested[1]].notna() & frame[requested[2]].notna()
    kept = frame.loc[keep].reset_index(drop=True)
    if kept.empty:
        raise ValueError(f"no {market} OOF rows carry non-null {requested}")
    counts = {
        "market": market, "prob_column": requested[0], "label_column": requested[1],
        "ev_column": requested[2], "rows_read": rows_read, "rows_in_range": rows_in_range,
        "dropped_nan_rows": int((~keep).sum()), "analysed_rows": int(len(kept)),
        "date_min": str(pd.Timestamp(kept[DATE_COLUMN].min()).date()),
        "date_max": str(pd.Timestamp(kept[DATE_COLUMN].max()).date()), "sliders_applied": False}
    return kept, counts


def quantile_levels(n_steps: int = DEFAULT_STEPS) -> np.ndarray:
    """Sweep levels from 0 (retain the whole panel) to 1 (retain the probability maximum)."""
    if not 2 <= int(n_steps) <= STEP_LIMIT:
        raise ValueError(f"step count must be in [2, {STEP_LIMIT}], got {n_steps!r}")
    return np.linspace(0.0, 1.0, int(n_steps))


def years_in_range(dates) -> float:
    """Span in years (365.25 d) - the ``kpi.years_in_range`` definition, vectorised.

    The kpi version builds ``list(dates)`` first, which costs ~1 s on the USD OOF panel;
    the tests pin the two definitions together.
    """
    values = pd.to_datetime(pd.Series(dates)).dropna()
    if values.empty:
        return 0.0
    span_days = (values.max() - values.min()).total_seconds() / 86400.0
    return float(span_days / 365.25)


def sweep_steps(values, labels, signed, levels, years: float, base_rate: float) -> list[dict]:
    """One row per quantile level: prefix sums over the probability order (exact counts)."""
    values = np.asarray(values, dtype="float64")
    labels = np.asarray(labels, dtype="float64")
    signed = np.asarray(signed, dtype="float64")
    total = int(values.size)
    if total == 0:
        raise ValueError("cannot sweep an empty frame")
    order = np.argsort(values, kind="stable")
    ascending = values[order]

    def prefix(column) -> np.ndarray:
        return np.concatenate(([0.0], np.cumsum(column[order])))

    hits, ev_sum = prefix(labels), prefix(signed)
    positive, negative = prefix(np.maximum(signed, 0.0)), prefix(np.minimum(signed, 0.0))
    ends = {"hits": hits[total], "ev": ev_sum[total],
            "positive": positive[total], "negative": negative[total]}
    steps: list[dict] = []
    for level, threshold in zip(np.asarray(levels, dtype="float64"), np.atleast_1d(np.quantile(values, levels))):
        retained = total - int(np.searchsorted(ascending, float(threshold), side="left"))
        cut = total - retained  # the excluded low-probability block
        hit_sum, ev_kept = ends["hits"] - hits[cut], ends["ev"] - ev_sum[cut]
        positive_kept = ends["positive"] - positive[cut]
        negative_kept = ends["negative"] - negative[cut]
        hit_rate = float(hit_sum / retained) if retained else float("nan")
        steps.append({
            "quantile": float(level), "threshold": float(threshold), "retained_rows": retained,
            "trades_per_year": float(retained / years) if years > 0 else float("nan"),
            "hit_rate": hit_rate,
            "lift": float(hit_rate / base_rate) if base_rate and base_rate > 0 else float("nan"),
            "ev": float(ev_kept / retained) if retained else float("nan"),
            "profit_factor": float(positive_kept / abs(negative_kept)) if negative_kept < 0 else float("nan"),
        })
    return steps


def compute_view(frame: pd.DataFrame, columns: dict, market: str | None = None,
                 n_steps: int = DEFAULT_STEPS, sign_mode: str = kpi.SIGN_MODE_DEFAULT,
                 base_rate: float | None = None, years: float | None = None) -> dict:
    """Aggregate sweep payload (no verdict field, watermark on every run)."""
    target = columns["target"]
    sign = kpi.sign_for(target, sign_mode)
    values = frame[columns["prob_column"]].to_numpy(dtype="float64")
    labels = frame[columns["label_column"]].to_numpy(dtype="float64")
    signed = frame[columns["ev_column"]].to_numpy(dtype="float64") * sign
    observed = float(labels.mean()) if labels.size else float("nan")
    base = float(base_rate) if base_rate is not None else observed
    span = float(years) if years is not None else years_in_range(frame[DATE_COLUMN])
    sweep = sweep_steps(values, labels, signed, quantile_levels(n_steps), span, base)
    reference = {"trades_per_year": REFERENCE_TRADES_PER_YEAR, "label": REFERENCE_LABEL,
                 "role": "display line only - the product aspiration, not a gate and not a target",
                 "note": REFERENCE_NOTE, "watermark": kpi.WATERMARK, "nearest_step": min(
                     sweep, key=lambda s: abs(s["trades_per_year"] - REFERENCE_TRADES_PER_YEAR), default=None)}
    return {
        "view": VIEW_NAME, "market": market.upper() if market else None, "target": target,
        "prob_column": columns["prob_column"], "label_column": columns["label_column"],
        "ev_column": columns["ev_column"], "sign": float(sign), "sign_mode": sign_mode,
        "analysed_rows": int(len(frame)), "years": span, "base_rate": base,
        "steps": int(n_steps), "step_limit": STEP_LIMIT, "sweep": sweep, "reference": reference,
        "limits": {"bin_limit": STEP_LIMIT, "payload_limit_bytes": PAYLOAD_LIMIT_BYTES,
                   "compute_limit_ms": COMPUTE_BUDGET_MS, "serialize_limit_ms": SERIALIZE_BUDGET_MS},
        "watermark": kpi.WATERMARK,
        "notes": [
            "Evidence only - no verdict, no adopt/reject field.",
            "Each step retains the OOF rows with p >= the quantile threshold; hit rate and "
            "lift use the unfiltered base rate of the same OOF panel and period.",
            f"Reference line at {REFERENCE_TRADES_PER_YEAR:g} trades/yr is {REFERENCE_LABEL}: {REFERENCE_NOTE}",
            "View 2 reads the OOF panel alone, so feature sliders are not applied here "
            "(counts['sliders_applied'] is False); only the market and date range carry over.",
            kpi.sign_mode_note(target, sign_mode),
        ],
    }


def _clean(value):
    """JSON-safe copy: numpy scalars out, non-finite floats -> None (strict JSON)."""
    if isinstance(value, dict):
        return {key: _clean(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_clean(item) for item in value]
    if isinstance(value, float):
        return float(value) if np.isfinite(value) else None
    if isinstance(value, np.generic):
        return _clean(value.item())
    return value


def serialize_payload(payload: dict) -> str:
    """Compact, strict JSON (no NaN literals) - the server-side serialize step."""
    return json.dumps(_clean(payload), separators=(",", ":"), sort_keys=True)


def measure_budget(frame: pd.DataFrame, columns: dict, **kwargs) -> dict:
    """Measure the server budget on the given frame; the loader/IO time is not counted."""
    start = time.perf_counter()
    payload = compute_view(frame, columns, **kwargs)
    compute_ms = (time.perf_counter() - start) * 1000.0
    start = time.perf_counter()
    serialize_payload(payload)
    serialize_ms = (time.perf_counter() - start) * 1000.0
    compute_within = bool(compute_ms <= COMPUTE_BUDGET_MS)
    serialize_within = bool(serialize_ms <= SERIALIZE_BUDGET_MS)
    payload["budget_ms"] = {
        "compute": round(compute_ms, 2), "serialize": round(serialize_ms, 2),
        "compute_limit": COMPUTE_BUDGET_MS, "serialize_limit": SERIALIZE_BUDGET_MS,
        "compute_within": compute_within, "serialize_within": serialize_within}
    payload["payload_bytes"], payload["within_limits"] = 0, False
    for _ in range(8):  # fixed point: the size and the flag live inside the payload measured
        size = len(serialize_payload(payload).encode("utf-8"))
        within = bool(compute_within and serialize_within and size <= PAYLOAD_LIMIT_BYTES)
        if size == payload["payload_bytes"] and within is payload["within_limits"]:
            break
        payload["payload_bytes"], payload["within_limits"] = size, within
    return payload


def build_view(loader, spec: dict, target: str | None = None, n_steps: int = DEFAULT_STEPS, **kwargs) -> dict:
    """Dash-callback entry point: projected OOF read + quantile sweep + measured payload."""
    controls.validate_spec(spec)
    market = str(spec.get("market", "")).upper()
    columns = columns_for(target if target is not None else spec.get("target"))
    frame, counts = load_prob_frame(loader, market, columns, spec.get("date_range"))
    payload = measure_budget(frame, columns, market=market, n_steps=n_steps,
                             sign_mode=spec.get("sign_mode", kpi.SIGN_MODE_DEFAULT), **kwargs)
    payload["counts"] = counts
    return payload


def figures(payload: dict) -> dict:
    """Plotly sweep: hit rate and EV against trades/yr plus the ILLUSTRATIVE reference line."""
    import plotly.graph_objects as go

    sweep = payload["sweep"]
    x = [float(step["trades_per_year"]) for step in sweep]
    hover = [f"p >= {s['threshold']:.4f} (q={s['quantile']:.2f}), n={s['retained_rows']}" for s in sweep]
    reference = payload["reference"]
    figure = go.Figure([
        go.Scatter(x=x, y=[s["hit_rate"] for s in sweep], mode="lines+markers",
                   name="hit rate", hovertext=hover),
        go.Scatter(x=x, y=[s["ev"] for s in sweep], mode="lines+markers", yaxis="y2",
                   name=f"EV ({payload['ev_column']}, ATR units)")])
    figure.add_vline(x=reference["trades_per_year"], line_dash="dash", line_color="grey",
                     annotation_text=f"{reference['trades_per_year']:g} trades/yr ({reference['label']})")
    figure.update_layout(
        title=f"threshold sweep - {payload['prob_column']} retained by {payload['label_column']}",
        xaxis_title="trades/yr (retained rows / years)", yaxis_title="hit rate",
        yaxis2={"title": "EV (ATR units)", "overlaying": "y", "side": "right", "showgrid": False})
    return {"sweep": figure}
