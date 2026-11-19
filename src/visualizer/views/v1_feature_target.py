"""View 1 - legacy OOF targets (WI-087): histograms, decile hit rate, CIs, null.

Aggregates only, carrying the WI-086 watermark, persisted nowhere; every feature
read is one column projection through the WI-086 join index (float32).

The CIs and the null read a pre-aggregated ``(date, bin) -> (n, hits)`` table,
which keeps ``B=200``/``sims=200`` inside the DoD budgets (<=100 bins per
histogram, <200 KB JSON, compute <=400 ms, serialize <=100 ms server-side).
"""
from __future__ import annotations

import json
import time

import numpy as np
import pandas as pd

from src.visualizer import controls, kpi, schema
from src.visualizer.stats.bootstrap import (
    B_DEFAULT,
    CONFIDENCE,
    SEED_DEFAULT,
    bin_intervals,
    preaggregate,
)
from src.visualizer.stats.null import SIM_DEFAULT, target_shifted_null

VIEW_NAME = "v1_legacy_target"
DECILE_BINS = 10
HIST_BINS = 50
BIN_LIMIT = 100
COMPUTE_BUDGET_MS = 400.0
SERIALIZE_BUDGET_MS = 100.0
PAYLOAD_LIMIT_BYTES = 200 * 1024
DATE_COLUMN = "date"


def label_for(target: str) -> tuple[str, str]:
    """``(source, column)`` of the observed label behind a selector option."""
    canonical = kpi.canonical_target(target)
    if canonical in schema.TARGET_COLUMNS:
        return "targets", canonical
    if target in schema.OOF_CANONICAL_COLUMNS and str(target).startswith("y_"):
        return "oof", str(target)
    raise KeyError(f"no observed label column for selector {target!r}")


def retained_frame(loader, index, spec, feature, target) -> tuple[pd.DataFrame, dict]:
    """Join-aligned rows for one spec: spec mask, then non-null feature and label."""
    controls.validate_spec(spec)
    if str(spec.get("market", "")).upper() != index.market:
        raise ValueError(f"spec market {spec.get('market')!r} != join market {index.market!r}")
    if feature not in schema.FEATURE_FLOAT_COLUMNS:
        raise ValueError(f"{feature!r} is not a float32 feature column")
    source, label_column = label_for(target)
    columns = sorted({feature, *(spec.get("sliders") or {})})
    features = loader.load_columns(index.market, columns, source="features")
    labels = loader.load_columns(index.market, [label_column], source=source)
    frame = pd.DataFrame({DATE_COLUMN: index.frame[DATE_COLUMN].to_numpy()})
    frame[label_column] = index.align(labels[label_column].to_numpy(), source).to_numpy()
    for column in columns:
        frame[column] = index.align(features[column].to_numpy(), "features").to_numpy()
    mask, _ = controls.apply_spec(frame, spec)
    filtered = frame.loc[mask]
    keep = filtered[feature].notna() & filtered[label_column].notna() & filtered[DATE_COLUMN].notna()
    rows = filtered.loc[keep].reset_index(drop=True)
    counts = {
        "market": index.market, "feature": feature, "target": target,
        "label_source": source, "label_column": label_column,
        "rows_after_spec": int(mask.sum()), "dropped_nan_rows": int((~keep).sum()),
        "retained_rows": int(len(rows)),
    }
    return rows, counts


def decile_edges(values, n_bins: int = DECILE_BINS) -> np.ndarray:
    """Quantile edges over the retained values (ties collapse bins, n still sums)."""
    return np.quantile(np.asarray(values, dtype="float64"), np.linspace(0.0, 1.0, int(n_bins) + 1))


def assign_bins(values, edges) -> np.ndarray:
    """Every value lands in exactly one bin: interior edges, clipped to the last."""
    interior = np.asarray(edges, dtype="float64")[1:-1]
    bins = np.searchsorted(interior, np.asarray(values, dtype="float64"), side="left")
    return np.clip(bins, 0, int(len(edges)) - 2).astype("int16")


def histogram_split(values, positive, bins: int = HIST_BINS) -> dict:
    """True/false histograms on shared edges; the two counts sum to the retained n."""
    values = np.asarray(values, dtype="float64")
    mask = np.asarray(positive, dtype=bool)
    low, high = float(values.min()), float(values.max())
    edges = np.linspace(low, high, int(bins) + 1) if high > low else np.array([low - 0.5, low + 0.5])
    if not np.isfinite(low + high):
        edges = np.array([0.0, 1.0])
    return {
        "bins": int(len(edges) - 1),
        "edges": [float(edge) for edge in edges],
        "true": np.histogram(values[mask], bins=edges)[0].astype("int64").tolist(),
        "false": np.histogram(values[~mask], bins=edges)[0].astype("int64").tolist(),
        "n_true": int(mask.sum()), "n_false": int((~mask).sum()),
    }


def compute_view(
    rows: pd.DataFrame, feature: str, target: str, market: str | None = None, n_bins: int = DECILE_BINS,
    hist_bins: int = HIST_BINS, b: int = B_DEFAULT, sims: int = SIM_DEFAULT, seed: int = SEED_DEFAULT,
    confidence: float = CONFIDENCE, base_rate: float | None = None,
) -> dict:
    """Aggregate payload for View 1 (no verdict field, watermark on every run)."""
    if int(n_bins) > BIN_LIMIT or int(hist_bins) > BIN_LIMIT:
        raise ValueError(f"bin counts must stay <= {BIN_LIMIT} (payload budget)")
    source, label_column = label_for(target)
    values = rows[feature].to_numpy(dtype="float32")
    labels = rows[label_column].to_numpy(dtype="float64")
    positive = labels > 0
    edges = decile_edges(values, n_bins)
    agg = preaggregate(rows[DATE_COLUMN].to_numpy(), assign_bins(values, edges), labels)
    intervals, bootstrap_meta = bin_intervals(agg, n_bins, b=b, seed=seed, confidence=confidence)
    null = target_shifted_null(agg, n_bins, sims=sims, seed=seed, confidence=confidence)
    hit_rate = float(labels.mean()) if labels.size else float("nan")
    reference = float(base_rate) if base_rate is not None else hit_rate
    deciles = []
    for entry in intervals:
        bin_index = entry["bin"]
        deciles.append(
            dict(
                entry,
                low=float(edges[bin_index]),
                high=float(edges[bin_index + 1]),
                null_rate=float(null["bin_rate"][bin_index]),
                null_low=float(null["bin_low"][bin_index]),
                null_high=float(null["bin_high"][bin_index]),
            )
        )
    return {
        "view": VIEW_NAME, "market": market.upper() if market else None, "target": target,
        "feature": feature, "label_source": source, "label_column": label_column,
        "retained_rows": int(len(rows)), "n_true": int(positive.sum()), "n_false": int((~positive).sum()),
        "hit_rate": hit_rate, "base_rate": reference,
        "lift": float(hit_rate / reference) if reference and reference > 0 else float("nan"),
        "decile_bins": int(n_bins), "hist_bins": int(hist_bins),
        "edge_duplicates": int((np.diff(edges) == 0).sum()),
        "deciles": deciles, "decile_n_total": int(sum(entry["n"] for entry in deciles)),
        "histograms": histogram_split(values, positive, hist_bins),
        "bootstrap": bootstrap_meta,
        "null": {key: value for key, value in null.items() if not key.startswith("bin_") and key != "totals_n"},
        "limits": {
            "bin_limit": BIN_LIMIT, "payload_limit_bytes": PAYLOAD_LIMIT_BYTES,
            "compute_limit_ms": COMPUTE_BUDGET_MS, "serialize_limit_ms": SERIALIZE_BUDGET_MS,
        },
        "watermark": kpi.WATERMARK,
        "notes": [
            "Evidence only - no verdict, no adopt/reject field.",
            "CIs resample dates (clusters), not rows; the null shuffles labels within a date.",
            f"hit rate is the mean of the observed {label_column}, not a model probability.",
        ],
    }


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


def measure_budget(rows: pd.DataFrame, feature: str, target: str, **kwargs) -> dict:
    """Measure the DoD budget on the given rows; the loader/IO time is not counted."""
    start = time.perf_counter()
    payload = compute_view(rows, feature, target, **kwargs)
    compute_ms = (time.perf_counter() - start) * 1000.0
    start = time.perf_counter()
    serialize_payload(payload)
    serialize_ms = (time.perf_counter() - start) * 1000.0
    compute_within = bool(compute_ms <= COMPUTE_BUDGET_MS)
    serialize_within = bool(serialize_ms <= SERIALIZE_BUDGET_MS)
    payload["budget_ms"] = {
        "compute": round(compute_ms, 2), "serialize": round(serialize_ms, 2),
        "compute_limit": COMPUTE_BUDGET_MS, "serialize_limit": SERIALIZE_BUDGET_MS,
        "compute_within": compute_within, "serialize_within": serialize_within,
    }
    # Fixed point: the byte counter and the byte-budget flag live inside the payload
    # they measure, so settle both fields and the serialized text together.
    payload["payload_bytes"] = 0
    payload["within_limits"] = False
    for _ in range(8):
        size = len(serialize_payload(payload).encode("utf-8"))
        within = bool(compute_within and serialize_within and size <= PAYLOAD_LIMIT_BYTES)
        if size == payload["payload_bytes"] and within is payload["within_limits"]:
            break
        payload["payload_bytes"], payload["within_limits"] = size, within
    return payload


def build_view(loader, index, spec, feature: str, target: str, **kwargs) -> dict:
    """Dash-callback entry point: projected read + spec mask + measured payload."""
    rows, counts = retained_frame(loader, index, spec, feature, target)
    payload = measure_budget(rows, feature, target, market=index.market, **kwargs)
    payload["counts"] = counts
    return payload


def figures(payload: dict) -> dict:
    """Plotly figures for the view: true/false histograms and the decile evidence."""
    import plotly.graph_objects as go

    def series(key: str) -> list[float]:
        return [float("nan") if entry[key] is None else float(entry[key]) for entry in payload["deciles"]]

    hist = payload["histograms"]
    centers = [(hist["edges"][i] + hist["edges"][i + 1]) / 2.0 for i in range(hist["bins"])]
    label = payload["label_column"]
    hist_fig = go.Figure(
        [
            go.Bar(x=centers, y=hist["true"], name=f"{label} = 1"),
            go.Bar(x=centers, y=[-value for value in hist["false"]], name=f"{label} = 0"),
        ]
    )
    hist_fig.update_layout(barmode="relative", title=f"true/false histograms - {payload['feature']}")
    axis = [entry["bin"] for entry in payload["deciles"]]
    decile_fig = go.Figure(
        [
            go.Scatter(
                x=axis, y=series("hit_rate"), mode="lines+markers", name="decile hit rate",
                hovertext=[f"n={entry['n']} hits={entry['hits']}" for entry in payload["deciles"]],
            ),
            go.Scatter(x=axis, y=series("ci_low"), mode="lines", name="CI low"),
            go.Scatter(x=axis, y=series("ci_high"), mode="lines", name="CI high"),
            go.Scatter(x=axis, y=series("null_rate"), mode="lines", name="within-date null"),
        ]
    )
    decile_fig.update_layout(title=f"{payload['target']} hit rate by decile of {payload['feature']}")
    return {"histogram": hist_fig, "decile": decile_fig}
