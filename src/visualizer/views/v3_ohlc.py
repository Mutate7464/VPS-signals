"""View 3 - OHLC drill-down with labeled barrier overlays (WI-088).

Click a decile bin/row -> a -40/+15 bar window for that symbol. Candles, the entry
marker and the feature subplot are artifacts (read-only); the exit marker at +h bars,
the barrier lines and the first-touch marker are recomputed DISPLAY MATH and carry the
boundary label "not label source". The recomputed first touch is compared with the
stored `y_*`; disagreement is a MISMATCH badge and is never reconciled (D-028).

Reads are per-symbol OHLCV (`VisualizerLoader.sample_ohlcv`, never a dataset over the
tree) plus one projected feature column and one projected OOF label column; float32
throughout. Nothing is persisted (writes only ever go to `state/viz/` from the loader).
"""
from __future__ import annotations

import json
import time

import numpy as np
import pandas as pd

from src.targets import wilder_atr
from src.visualizer import controls, kpi, schema
from src.visualizer.overlay import barriers

VIEW_NAME = "v3_ohlc"
DATE_COLUMN = "date"
WINDOW_BEFORE = 40
WINDOW_AFTER = 15
DEFAULT_FEATURE = "atr_pct_20"
LATENCY_BUDGET_MS = 1000.0
MIN_HISTORY = 21  # Wilder ATR(20) needs 20 prior bars
#: wi048 family -> OOF label column for the MISMATCH comparison (explicit; D-028 open).
STORED_LABEL_COLUMNS = {"high_low": "y_y_15d_high"}


def window_bounds(n, entry_index, before=WINDOW_BEFORE, after=WINDOW_AFTER) -> tuple[int, int, int]:
    """Clipped `(start, stop, entry_offset)` for the -before/+after bar window."""
    start = max(0, int(entry_index) - int(before))
    stop = min(int(n), int(entry_index) + int(after) + 1)
    return start, stop, int(entry_index) - start


def entry_position(ohlcv: pd.DataFrame, entry_date) -> int:
    """Row index of the entry bar in the (date-sorted) per-symbol OHLCV frame."""
    days = pd.to_datetime(ohlcv[DATE_COLUMN]).dt.normalize().to_numpy()
    hits = np.flatnonzero(days == np.datetime64(pd.Timestamp(entry_date).normalize()))
    if not hits.size:
        raise KeyError(f"entry date {entry_date} is not in the raw OHLCV file")
    return int(hits[0])


def atr_at_entry(ohlcv: pd.DataFrame, entry_index: int) -> float:
    """Trailing Wilder ATR at the entry bar (`NaN` when history is too short)."""
    atr = wilder_atr(ohlcv).to_numpy(dtype="float64")
    value = atr[int(entry_index)] if 0 <= int(entry_index) < atr.size else np.nan
    return float(value) if np.isfinite(value) else float("nan")


def slice_window(ohlcv: pd.DataFrame, entry_index: int, before=WINDOW_BEFORE,
                 after=WINDOW_AFTER) -> tuple[pd.DataFrame, int]:
    """The -before/+after bar slice with a `rel` bar offset column (0 = entry)."""
    start, stop, offset = window_bounds(len(ohlcv), entry_index, before, after)
    window = ohlcv.iloc[start:stop].reset_index(drop=True).copy()
    window["rel"] = np.arange(start, stop, dtype="int32") - int(entry_index)
    return window, offset


def _row_value(loader, index, source, column, symbol, entry_date):
    """One projected `source` column taken onto the (symbol, entry_date) join row."""
    aligned = index.values(loader, source, column).to_numpy()
    frame = index.frame
    mask = (frame["symbol"].astype(str).to_numpy() == str(symbol)) & (
        pd.to_datetime(frame[DATE_COLUMN]).dt.normalize().to_numpy()
        == np.datetime64(pd.Timestamp(entry_date).normalize())
    )
    if not mask.any():
        return None
    value = aligned[mask][0]
    return None if not np.isfinite(value) else float(value)


def feature_window(loader, index, symbol, feature, dates) -> list:
    """Artifact feature values aligned to the window dates (None where the panel lacks a row)."""
    aligned = index.values(loader, "features", feature).to_numpy()
    frame = index.frame
    keep = frame["symbol"].astype(str).to_numpy() == str(symbol)
    days = pd.to_datetime(frame[DATE_COLUMN]).dt.normalize().to_numpy()[keep]
    wanted = pd.to_datetime(pd.Series(list(dates))).dt.normalize().to_numpy()
    # Keys stay np.datetime64 so they match the np.datetime64 window days.
    lookup = {np.datetime64(day): value for day, value in zip(days, aligned[keep])}
    out = []
    for day in wanted:
        value = lookup.get(np.datetime64(day), np.nan)
        out.append(float(value) if np.isfinite(value) else None)
    return out


def _candles(window: pd.DataFrame) -> list[dict]:
    return [
        {
            "rel": int(row.rel), "date": str(pd.Timestamp(row.date).date()),
            "open": float(row.open), "high": float(row.high), "low": float(row.low),
            "close": float(row.close), "volume": float(row.volume),
        }
        for row in window.itertuples(index=False)
    ]


def _overlay_elements(geometry, feature: str) -> list[dict]:
    """Every overlay element with its boundary class and label (artifacts vs display math)."""
    elements = [
        {"element": "candles", "boundary_class": barriers.ARTIFACT_CLASS,
         "boundary_label": "raw OHLCV slice (read-only)"},
        {"element": "entry_marker", "boundary_class": "artifact",
         "boundary_label": "entry date from the OOF/targets row"},
        {"element": "exit_marker", "boundary_class": barriers.OVERLAY_CLASS,
         "boundary_label": barriers.OVERLAY_LABEL},
        {"element": "feature_subplot", "boundary_class": "artifact (not recomputed)",
         "boundary_label": f"features parquet {feature}"},
    ]
    if geometry.reproducible:
        elements.append({"element": "barrier_lines", "boundary_class": barriers.OVERLAY_CLASS,
                         "boundary_label": barriers.OVERLAY_LABEL})
        elements.append({"element": "first_touch_marker", "boundary_class": barriers.OVERLAY_CLASS,
                         "boundary_label": barriers.OVERLAY_LABEL})
    else:
        elements.append({"element": "barrier_lines", "boundary_class": "omitted",
                         "boundary_label": barriers.NOT_REPRODUCIBLE})
    return elements


def build_view(loader, index, spec, symbol, entry_date, feature=DEFAULT_FEATURE,
               family=barriers.DEFAULT_FAMILY, h=barriers.DEFAULT_HORIZON, stored_column=None,
               cells=None, before=WINDOW_BEFORE, after=WINDOW_AFTER) -> dict:
    """Dash-callback entry point: per-symbol window + labeled overlays + MISMATCH badge."""
    controls.validate_spec(spec)
    market = index.market
    if str(spec.get("market", "")).upper() != market:
        raise ValueError(f"spec market {spec.get('market')!r} != join market {market!r}")
    if feature not in schema.FEATURE_FLOAT_COLUMNS:
        raise ValueError(f"{feature!r} is not a float32 feature column")
    h = int(h)
    ohlcv = loader.sample_ohlcv(market, symbol).sort_values(DATE_COLUMN).reset_index(drop=True)
    entry_index = entry_position(ohlcv, entry_date)
    start, stop, entry_offset = window_bounds(len(ohlcv), entry_index, before, after)
    window, entry_offset = slice_window(ohlcv, entry_index, before, after)
    atr_entry = atr_at_entry(ohlcv, entry_index)
    entry_close = float(window["close"].to_numpy()[entry_offset])

    cells = barriers.load_cells(family) if cells is None else cells
    cell = barriers.select_cell(cells, market=market, h=h)
    geometry = barriers.geometry_from_cell(cell, entry_close, atr_entry)
    stored_column = stored_column if stored_column is not None else STORED_LABEL_COLUMNS.get(family)
    stored_value = (
        _row_value(loader, index, "oof", stored_column, symbol, entry_date)
        if stored_column else None
    )

    forward = ohlcv.iloc[entry_index + 1: entry_index + 1 + h]
    recomputed = None
    if geometry.reproducible and len(forward) >= h and h > 0:
        recomputed = barriers.first_touch(
            forward["high"].to_numpy(), forward["low"].to_numpy(),
            entry_close, atr_entry, geometry.k, h,
        )
    badge = barriers.mismatch(recomputed["touch"] if recomputed else None, stored_value)

    dates = window[DATE_COLUMN].tolist()
    exit_offset = entry_offset + h
    exit_row = window.iloc[exit_offset] if 0 <= exit_offset < len(window) else None
    entry_row = window.iloc[entry_offset]
    return {
        "view": VIEW_NAME, "market": market, "symbol": str(symbol),
        "entry_date": str(pd.Timestamp(entry_date).normalize().date()),
        "family": family, "h": h, "feature": feature, "stored_column": stored_column,
        "window": {
            "before": int(before), "after": int(after), "start": int(start), "stop": int(stop),
            "entry_offset": int(entry_offset), "bars": int(len(window)),
        },
        "candles": _candles(window),
        "entry_marker": {
            "rel": 0, "date": str(pd.Timestamp(entry_row.date).date()),
            "close": entry_close, "boundary_class": "artifact",
            "boundary_label": "entry date from the OOF/targets row",
        },
        "exit_marker": None if exit_row is None else {
            "rel": h, "date": str(pd.Timestamp(exit_row.date).date()),
            "close": float(exit_row.close), "boundary_class": barriers.OVERLAY_CLASS,
            "boundary_label": barriers.OVERLAY_LABEL,
        },
        "feature_subplot": {
            "column": feature, "values": feature_window(loader, index, symbol, feature, dates),
            "boundary_class": "artifact (not recomputed)",
            "boundary_label": f"features parquet {feature}",
        },
        "barriers": geometry.as_dict(),
        "first_touch": recomputed,
        "mismatch": badge,
        "stored_value": stored_value,
        "overlay_elements": _overlay_elements(geometry, feature),
        "watermark": kpi.WATERMARK,
        "notes": [
            "Evidence only - no verdict, no adopt/reject field.",
            "Candles/entry marker/feature subplot are artifacts; exit marker, barrier lines "
            "and first-touch marker are recomputed display math, labeled 'not label source'.",
            "Barrier levels are display math from the wi048 cell k x ATR at entry, not the "
            "label source; any disagreement with the stored y_* is a MISMATCH badge, never reconciled.",
        ],
    }


def sample_events(index, n: int = barriers.SAMPLE_EVENTS, max_symbols: int = 12, seed: int = 0) -> list:
    """Deterministic sample of `n` (symbol, date) events that carry a stored OOF row.

    Drawn from at most `max_symbols` symbols so the per-symbol OHLCV LRU bounds the IO.
    """
    frame = index.frame
    matched = frame[frame["oof_pos"] >= 0]
    if matched.empty:
        return []
    symbols = sorted(matched["symbol"].astype(str).unique())[: int(max_symbols)]
    sub = matched[matched["symbol"].astype(str).isin(symbols)]
    rng = np.random.default_rng(int(seed))
    take = min(int(n), len(sub))
    picks = np.sort(rng.choice(len(sub), size=take, replace=False))
    rows = sub.iloc[picks]
    return [(str(row["symbol"]), pd.Timestamp(row[DATE_COLUMN])) for _, row in rows.iterrows()]


def mismatch_evidence(loader, index, spec, feature=DEFAULT_FEATURE, family=barriers.DEFAULT_FAMILY,
                      h=barriers.DEFAULT_HORIZON, n: int = barriers.SAMPLE_EVENTS, seed: int = 0,
                      max_symbols: int = 12) -> dict:
    """MISMATCH rate over `n` sampled events - evidence only, never reconciled (D-028)."""
    records, skipped = [], 0
    for symbol, entry_date in sample_events(index, n=n, max_symbols=max_symbols, seed=seed):
        try:
            payload = build_view(loader, index, spec, symbol, entry_date,
                                 feature=feature, family=family, h=h)
        except (KeyError, ValueError):
            skipped += 1
            continue
        records.append(payload["mismatch"])
    report = barriers.mismatch_rate(records, sampled=n)
    report.update({"family": family, "h": int(h), "seed": int(seed), "skipped": int(skipped),
                   "watermark": kpi.WATERMARK})
    return report


def measure_latency(loader, index, spec, symbol, entry_date, repeats: int = 3, **kwargs) -> dict:
    """Measured click-to-window latency (per-symbol read + projected columns); tunnel excluded."""
    latencies, payload = [], None
    for _ in range(max(1, int(repeats))):
        start = time.perf_counter()
        payload = build_view(loader, index, spec, symbol, entry_date, **kwargs)
        latencies.append((time.perf_counter() - start) * 1000.0)
    payload["latency_ms"] = round(float(np.median(latencies)), 2)
    payload["latency_ms_max"] = round(float(max(latencies)), 2)
    payload["latency_budget_ms"] = LATENCY_BUDGET_MS
    payload["within_budget"] = bool(max(latencies) <= LATENCY_BUDGET_MS)
    payload["latency_scope"] = (
        "in-process window build (per-symbol OHLCV read + one projected feature/label column); "
        "tunnel latency not measured here"
    )
    return payload


def _clean(value):
    """JSON-safe copy: numpy scalars/arrays out, non-finite floats -> None."""
    if isinstance(value, dict):
        return {key: _clean(item) for key, item in value.items()}
    if isinstance(value, (np.ndarray, list, tuple)):
        items = value.tolist() if isinstance(value, np.ndarray) else value
        return [_clean(item) for item in items]
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return float(value) if np.isfinite(value) else None
    return value


def serialize_payload(payload: dict) -> str:
    """Compact, strict JSON (no NaN literals) - the server-side serialize step."""
    return json.dumps(_clean(payload), separators=(",", ":"), sort_keys=True)


def figures(payload: dict) -> dict:
    """Plotly figures: OHLC with labeled overlays, plus the artifact feature subplot."""
    import plotly.graph_objects as go

    candles = payload["candles"]
    x = [candle["date"] for candle in candles]
    ohlc = go.Figure(
        go.Candlestick(
            x=x, open=[c["open"] for c in candles], high=[c["high"] for c in candles],
            low=[c["low"] for c in candles], close=[c["close"] for c in candles],
            name="OHLC (artifact)",
        )
    )
    geometry = payload["barriers"]
    if geometry["reproducible"]:
        for name, level in (("upper", geometry["upper"]), ("lower", geometry["lower"])):
            ohlc.add_hline(y=level, line_dash="dash",
                           annotation_text=f"{name} {geometry['k']}*ATR ({barriers.OVERLAY_LABEL})")
    entry = payload["entry_marker"]
    ohlc.add_trace(go.Scatter(x=[entry["date"]], y=[entry["close"]], mode="markers",
                              marker_symbol="triangle-up", name="entry (artifact)"))
    if payload["exit_marker"]:
        exit_marker = payload["exit_marker"]
        ohlc.add_trace(go.Scatter(x=[exit_marker["date"]], y=[exit_marker["close"]], mode="markers",
                                  marker_symbol="triangle-down",
                                  name=f"exit +{payload['h']}b ({barriers.OVERLAY_LABEL})"))
    first_touch = payload["first_touch"]
    if first_touch and first_touch["touch"] != barriers.TOUCH_NONE:
        up = first_touch["touch"] == barriers.TOUCH_UP
        offset = first_touch["up_offset"] if up else first_touch["down_offset"]
        index = int(payload["window"]["entry_offset"]) + int(offset)
        if 0 <= index < len(candles):
            level = geometry["upper"] if up else geometry["lower"]
            ohlc.add_trace(go.Scatter(x=[candles[index]["date"]], y=[level], mode="markers",
                                      marker_symbol="x",
                                      name=f"first touch ({barriers.OVERLAY_LABEL})"))
    ohlc.update_layout(
        title=f"{payload['symbol']} {payload['entry_date']} - barrier overlay "
              f"({barriers.OVERLAY_LABEL}); badge {payload['mismatch']['badge']}",
        xaxis_rangeslider_visible=False,
    )
    feature = go.Figure(
        go.Scatter(x=x, y=payload["feature_subplot"]["values"], mode="lines",
                   name=f"{payload['feature']} (artifact)")
    )
    feature.update_layout(title=f"{payload['feature']} (artifact, not recomputed)")
    return {"ohlc": ohlc, "feature": feature}
