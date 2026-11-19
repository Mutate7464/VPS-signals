"""Global filter bar: slider whitelist, date range, target selector (WI-086).

One `dcc.Store` (`filter-spec`) holds the whole UI state and is serialised to the
URL query string, so every view is reproducible and shareable. Sliders only ever
touch whitelisted features; the spec is validated on the way in and on the way out.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlencode

import numpy as np
import pandas as pd
from dash import dcc

from src.visualizer import MARKETS, STATE_DIR, state_path
from src.visualizer import schema
from src.visualizer.kpi import EV_SIGN_MODES, SIGN_MODE_DEFAULT

STORE_ID = "filter-spec"
DATE_COLUMN = "date"
#: Signal-context features (plan 26-W47) that may carry a slider.
SLIDER_WHITELIST: tuple[str, ...] = ("atr_pct_20", "entropy_20", "hurst_50", "adx_20", "kama_er_20")
TARGET_LABEL_COLUMNS: tuple[str, ...] = schema.TARGET_COLUMNS[3:]
#: Legacy selector: targets file labels, oof labels (`y_y_*`) and oof probabilities (`p_y_*`).
TARGET_OPTIONS: tuple[str, ...] = TARGET_LABEL_COLUMNS + tuple(
    column for column in schema.OOF_CANONICAL_COLUMNS if column.startswith(("y_y_", "p_y_"))
)
BENCH_KEY = "filter_roundtrip"
FILTER_BUDGET_MS = 1000.0

if not set(SLIDER_WHITELIST) <= set(schema.FEATURE_FLOAT_COLUMNS):
    raise ValueError("slider whitelist contains a non-feature column")
if not set(TARGET_LABEL_COLUMNS) <= set(schema.TARGET_COLUMNS):
    raise ValueError("target label columns disagree with the frozen targets schema")


def default_spec(
    market: str = MARKETS[0],
    target: str = "y_20d_stay",
    date_range: tuple[str, str] | None = None,
    sliders: dict | None = None,
    sign_mode: str = SIGN_MODE_DEFAULT,
) -> dict:
    """A validated starting spec (raises on anything outside the whitelist)."""
    spec = {
        "market": str(market).upper(),
        "target": target,
        "date_range": list(date_range) if date_range else [],
        "sliders": {k: [float(v[0]), float(v[1])] for k, v in dict(sliders or {}).items()},
        "bin": None,
        "sign_mode": sign_mode,
    }
    return validate_spec(spec)


def validate_spec(spec: dict) -> dict:
    """Reject anything outside the whitelist; raise `ValueError` with every problem."""
    errors: list[str] = []
    if not isinstance(spec, dict):
        raise ValueError("filter spec must be a dict")
    market = str(spec.get("market", "")).upper()
    if market not in MARKETS:
        errors.append(f"market {spec.get('market')!r} not in {MARKETS}")
    if spec.get("target") not in TARGET_OPTIONS:
        errors.append(f"target {spec.get('target')!r} is not a selector option")
    if spec.get("sign_mode", SIGN_MODE_DEFAULT) not in EV_SIGN_MODES:
        errors.append(f"sign_mode {spec.get('sign_mode')!r} not in {EV_SIGN_MODES}")
    for feature, bounds in dict(spec.get("sliders") or {}).items():
        if feature not in SLIDER_WHITELIST:
            errors.append(f"slider {feature!r} is outside the whitelist {SLIDER_WHITELIST}")
            continue
        if len(list(bounds)) != 2 or float(bounds[0]) > float(bounds[1]):
            errors.append(f"slider {feature!r} needs an ordered [low, high] pair")
    date_range = list(spec.get("date_range") or [])
    if date_range:
        try:
            low, high = (pd.Timestamp(value) for value in date_range)
            if low > high:
                errors.append("date_range low > high")
        except (TypeError, ValueError):
            errors.append(f"date_range {date_range!r} is not two parseable dates")
    if spec.get("bin") is not None and int(spec["bin"]) < 0:
        errors.append(f"bin {spec['bin']!r} must be null or a non-negative index")
    if errors:
        raise ValueError("invalid filter spec: " + "; ".join(errors))
    return spec


def encode_spec(spec: dict) -> str:
    """Serialise the spec to a URL query string (one `dcc.Store` -> one string)."""
    validate_spec(spec)
    return urlencode({"spec": json.dumps(spec, sort_keys=True, separators=(",", ":"))})


def decode_spec(search: str) -> dict:
    """Parse a `dcc.Location.search` value back into a validated spec."""
    query = parse_qs(str(search).lstrip("?"))
    if "spec" not in query:
        raise ValueError("query string carries no 'spec' parameter")
    return validate_spec(json.loads(query["spec"][0]))


def build_filter_store(spec: dict) -> dcc.Store:
    return dcc.Store(id=STORE_ID, data=validate_spec(spec), storage_type="memory")


def slider_bounds(frame: pd.DataFrame, quantiles: tuple[float, float] = (0.05, 0.95)) -> dict:
    """Default slider ranges from the retained frame (p5/p95, NaN-safe)."""
    bounds = {}
    for feature in SLIDER_WHITELIST:
        if feature not in frame.columns:
            continue
        values = np.asarray(frame[feature], dtype="float64")
        low = float(np.nanpercentile(values, quantiles[0] * 100))
        high = float(np.nanpercentile(values, quantiles[1] * 100))
        bounds[feature] = [low, high]
    return bounds


def apply_spec(frame: pd.DataFrame, spec: dict) -> tuple[np.ndarray, pd.DataFrame]:
    """Boolean mask + retained rows for one filter spec (whitelisted features only)."""
    validate_spec(spec)
    mask = np.ones(len(frame), dtype=bool)
    for feature, (low, high) in dict(spec.get("sliders") or {}).items():
        values = np.asarray(frame[feature], dtype="float64")
        mask &= (values >= float(low)) & (values <= float(high))
    if spec.get("date_range"):
        low, high = (pd.Timestamp(value) for value in spec["date_range"])
        dates = pd.to_datetime(frame[DATE_COLUMN])
        mask &= (dates >= low).to_numpy() & (dates <= high).to_numpy()
    return mask, frame.loc[mask]


def measure_filter_roundtrip(frame: pd.DataFrame, spec: dict, repeats: int = 7) -> dict:
    """Measured filter round-trip; the tunnel adds SSH + browser render on top."""
    latencies: list[float] = []
    retained = 0
    for _ in range(max(2, int(repeats))):
        start = time.perf_counter()
        _, filtered = apply_spec(frame, spec)
        retained = int(len(filtered))
        latencies.append((time.perf_counter() - start) * 1000.0)
    p95 = float(np.percentile(latencies, 95))
    return {
        "repeats": len(latencies),
        "n_rows": int(len(frame)),
        "retained_rows": retained,
        "latency_ms_p50": round(float(np.median(latencies)), 2),
        "latency_ms_p95": round(p95, 2),
        "budget_ms": FILTER_BUDGET_MS,
        "within_budget": bool(p95 <= FILTER_BUDGET_MS),
        "scope": "in-process mask+bins on the join rows; tunnel latency not measured here",
    }


def record_filter_bench(report: dict, state_dir: Path | str = STATE_DIR) -> Path:
    """Merge the measured round-trip into `state/viz/bench.json` (evidence file)."""
    path = state_path("bench.json", state_dir)
    payload = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    payload[BENCH_KEY] = dict(report, recorded_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path
