"""WI-016 Step 6 — decision-rule synthesis into the shortlist artifact.

The meta-labeler (`src.wi016.meta_labeler`) predicts, per cleared barrier target,
the calibrated probability that the long bet's **profit barrier** is touched
first. This module turns that probability plus the point-in-time barrier geometry
into the four decision components the design asks for:

* **entry** — the top-decile primary event (long side) on the scoring date;
* **exit** — the symmetric barrier ``close ± k·ATR_t`` and the vertical time stop
  at ``h`` bars;
* **size** — meta-probability sizing, ``max(0, 2p − 1)`` (a confidence proxy, not
  a capital allocation);
* **abstain** — ``NO_TRADE`` is the **default**: a row trades only when the
  calibrated probability clears the coin-flip floor *and* the expected edge
  exceeds the cost band (20 bps, the WI-011 assumption).

Expected edge is the symmetric-barrier payoff ``(2p − 1) · k·ATR_t / close_t``
expressed in bps. That is a screening-scale approximation: it prices the barrier
distance, not intra-horizon drift, and it charges one flat round-trip cost.

Output: ``reports/wi016_shortlist_{market}.parquet`` — a **new** WI-014-compatible
artifact (the WI-014 shortlist schema ``rank, symbol, <E5 factors>, scoring_date``
plus the meta columns). Frozen ``reports/wi014_*`` artifacts are never touched and
**no order execution exists** anywhere in this module.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.factors.e5_baseline import E5_FACTORS
from src.market_cli import report_path
from src.wi016.meta_labeler import PRIMARY_COLUMN, TOP_DECILE_Q, primary_pct_rank, target_grid
from src.wi016.triple_barrier import barrier_levels

BASE_DIR = Path(__file__).resolve().parents[2]
REPORTS_DIR = BASE_DIR / "reports"

COST_BPS = 20.0
"""Standing round-trip cost band (unconfirmed WI-011 assumption; admin-adjudicated)."""

META_MIN_PROB = 0.5
"""Abstain floor: below a calibrated coin flip there is no bet to size."""

BPS = 1e4

SHORTLIST_COLUMNS: tuple[str, ...] = (
    "rank", "symbol", *E5_FACTORS, "scoring_date",
    "market", "target", "k", "h",
    "primary", "primary_pct", "decile_flag",
    "p_meta", "meta_calibration",
    "entry_close", "atr", "barrier_upper", "barrier_lower", "time_stop_bars",
    "expected_gross_bps", "cost_bps", "net_bps", "size", "decision", "abstain_reason",
)
"""WI-014-compatible shortlist schema (its columns first) plus the meta columns."""

ABSTAIN_REASONS: tuple[str, ...] = ("ok", "p_below_min", "net_edge_nonpositive", "undefined")

__all__ = [
    "ABSTAIN_REASONS",
    "COST_BPS",
    "META_MIN_PROB",
    "SHORTLIST_COLUMNS",
    "build_shortlist",
    "decide_action",
    "expected_edge_bps",
    "shortlist_path",
    "size_from_meta",
    "write_shortlist_parquet",
]


# --------------------------------------------------------------------------- #
# Decision rule
# --------------------------------------------------------------------------- #
def expected_edge_bps(p_meta: float, close: float, atr: float, k: float,
                      cost_bps: float = COST_BPS) -> dict:
    """Symmetric-barrier expected edge in bps, net of the cost band.

    ``gross = (2p − 1) · k·ATR/close`` (payoff ``+k·ATR`` at probability ``p``,
    ``−k·ATR`` otherwise). NaN/invalid geometry yields a NaN edge (and therefore
    ``NO_TRADE``).
    """
    p = float(p_meta)
    c = float(close)
    a = float(atr)
    if not np.isfinite(p) or not np.isfinite(c) or not np.isfinite(a) or c <= 0.0 or a < 0.0:
        return {"gross_bps": float("nan"), "net_bps": float("nan"), "cost_bps": float(cost_bps)}
    gross = (2.0 * p - 1.0) * (float(k) * a / c) * BPS
    return {"gross_bps": gross, "net_bps": gross - float(cost_bps), "cost_bps": float(cost_bps)}


def size_from_meta(p_meta: float) -> float:
    """Meta-probability size in ``[0, 1]``: ``max(0, 2p − 1)``; NaN sizes to 0."""
    p = float(p_meta)
    if not np.isfinite(p):
        return 0.0
    return float(min(1.0, max(0.0, 2.0 * p - 1.0)))


def decide_action(p_meta: float, close: float, atr: float, k: float,
                  cost_bps: float = COST_BPS, min_prob: float = META_MIN_PROB) -> dict:
    """Entry/exit/size/abstain decision for one event. ``NO_TRADE`` is the default.

    Trades only when the calibrated probability clears `min_prob` *and* the
    expected edge is positive after `cost_bps`. Returns the barrier levels, the
    net edge, the size and the abstain reason so the shortlist row is auditable.
    """
    k = float(k)
    edge = expected_edge_bps(p_meta, close, atr, k, cost_bps=cost_bps)
    upper = lower = float("nan")
    if np.isfinite(float(close)) and np.isfinite(float(atr)):
        u, l = barrier_levels(np.asarray([float(close)]), np.asarray([float(atr)]), k)
        upper, lower = float(u[0]), float(l[0])

    p = float(p_meta)
    if not np.isfinite(p) or not np.isfinite(edge["net_bps"]):
        reason = "undefined"
    elif p < float(min_prob):
        reason = "p_below_min"
    elif edge["net_bps"] <= 0.0:
        reason = "net_edge_nonpositive"
    else:
        reason = "ok"
    trade = reason == "ok"
    return {
        "gross_bps": edge["gross_bps"],
        "net_bps": edge["net_bps"],
        "cost_bps": edge["cost_bps"],
        "barrier_upper": upper,
        "barrier_lower": lower,
        "size": size_from_meta(p) if trade else 0.0,
        "decision": "TRADE" if trade else "NO_TRADE",
        "abstain_reason": reason,
    }


# --------------------------------------------------------------------------- #
# Shortlist artifact
# --------------------------------------------------------------------------- #
def shortlist_path(market: str, out_dir: Path = REPORTS_DIR) -> Path:
    """`reports/wi016_shortlist_{market}.parquet` (new artifact, never `wi014_*`)."""
    path = report_path(out_dir, "wi016_shortlist", market, ".parquet")
    if "wi014" in path.name:
        raise ValueError(f"refusing to write a frozen WI-014 artifact: {path}")
    return path


def _empty_shortlist() -> pd.DataFrame:
    return pd.DataFrame({c: pd.Series(dtype="float64") for c in SHORTLIST_COLUMNS})


def build_shortlist(
    panel: pd.DataFrame,
    meta_result: dict,
    market: str,
    cost_bps: float = COST_BPS,
    scoring_date=None,
    q: float = TOP_DECILE_Q,
    min_prob: float = META_MIN_PROB,
) -> tuple[pd.DataFrame, dict]:
    """Assemble the shortlist from the meta models + the latest cross-section.

    Events are the **top-decile** long-side primary rows on the scoring date
    (default: the panel's latest date); one row per (symbol, cleared target).
    Decisions come from :func:`decide_action`, so the artifact carries entry,
    barrier/time-stop exit, size and abstain fields. No order execution.
    """
    targets = meta_result.get("targets", {})
    if panel is None or panel.empty or not targets:
        return _empty_shortlist(), {"market": market, "scoring_date": None, "n_rows": 0,
                                    "n_trade": 0, "n_no_trade": 0, "cost_bps": float(cost_bps),
                                    "columns": list(SHORTLIST_COLUMNS)}

    date = pd.Timestamp(scoring_date) if scoring_date is not None else pd.Timestamp(panel["date"].max())
    latest = panel[panel["date"] == date]
    if latest.empty:
        return _empty_shortlist(), {"market": market, "scoring_date": str(date.date()), "n_rows": 0,
                                    "n_trade": 0, "n_no_trade": 0, "cost_bps": float(cost_bps),
                                    "columns": list(SHORTLIST_COLUMNS)}

    pct = primary_pct_rank(latest[PRIMARY_COLUMN].to_numpy(), latest["date"].to_numpy())
    top = latest[np.isfinite(pct) & (pct >= q)].copy()
    if top.empty:
        return _empty_shortlist(), {"market": market, "scoring_date": str(date.date()), "n_rows": 0,
                                    "n_trade": 0, "n_no_trade": 0, "cost_bps": float(cost_bps),
                                    "columns": list(SHORTLIST_COLUMNS)}
    top["primary_pct"] = pct[np.isfinite(pct) & (pct >= q)]

    frames: list[pd.DataFrame] = []
    for target, res in targets.items():
        model = res.get("final_model")
        if model is None:
            continue
        k, h = target_grid(target)
        feats = [f for f in res["features"] if f in top.columns]
        p_meta = np.asarray(model.predict_proba(top[feats].to_numpy(dtype="float32")), dtype="float64")

        close = top["close"].to_numpy(dtype="float64") if "close" in top.columns else np.full(len(top), np.nan)
        atr = top["atr"].to_numpy(dtype="float64") if "atr" in top.columns else np.full(len(top), np.nan)
        decisions = [decide_action(p, c, a, k, cost_bps=cost_bps, min_prob=min_prob)
                     for p, c, a in zip(p_meta, close, atr)]

        rows = pd.DataFrame({
            "symbol": top["symbol"].to_numpy(),
            "scoring_date": str(date.date()),
            "market": market,
            "target": target,
            "k": np.float32(k),
            "h": np.int16(h),
            "primary": top[PRIMARY_COLUMN].to_numpy(dtype="float32"),
            "primary_pct": top["primary_pct"].to_numpy(dtype="float32"),
            "decile_flag": np.int8(1),
            "p_meta": p_meta.astype("float32"),
            "meta_calibration": res.get("final_calibration") or "n/a",
            "entry_close": close.astype("float32"),
            "atr": atr.astype("float32"),
            "barrier_upper": np.asarray([d["barrier_upper"] for d in decisions], dtype="float32"),
            "barrier_lower": np.asarray([d["barrier_lower"] for d in decisions], dtype="float32"),
            "time_stop_bars": np.int16(h),
            "expected_gross_bps": np.asarray([d["gross_bps"] for d in decisions], dtype="float32"),
            "cost_bps": np.float32(cost_bps),
            "net_bps": np.asarray([d["net_bps"] for d in decisions], dtype="float32"),
            "size": np.asarray([d["size"] for d in decisions], dtype="float32"),
            "decision": [d["decision"] for d in decisions],
            "abstain_reason": [d["abstain_reason"] for d in decisions],
        })
        for f in E5_FACTORS:
            rows[f] = top[f].to_numpy(dtype="float32") if f in top.columns else np.float32("nan")
        frames.append(rows)

    if not frames:
        return _empty_shortlist(), {"market": market, "scoring_date": str(date.date()), "n_rows": 0,
                                    "n_trade": 0, "n_no_trade": 0, "cost_bps": float(cost_bps),
                                    "columns": list(SHORTLIST_COLUMNS)}

    shortlist = pd.concat(frames, ignore_index=True)
    shortlist = shortlist.sort_values(
        ["target", "p_meta", "symbol"], ascending=[True, False, True], kind="mergesort"
    ).reset_index(drop=True)
    shortlist.insert(0, "rank", shortlist.groupby("target", sort=False).cumcount().add(1).astype("int32"))
    shortlist = shortlist[list(SHORTLIST_COLUMNS)]

    info = {
        "market": market,
        "scoring_date": str(date.date()),
        "n_rows": int(len(shortlist)),
        "n_trade": int((shortlist["decision"] == "TRADE").sum()),
        "n_no_trade": int((shortlist["decision"] == "NO_TRADE").sum()),
        "cost_bps": float(cost_bps),
        "columns": list(shortlist.columns),
    }
    return shortlist, info


def write_shortlist_parquet(shortlist: pd.DataFrame, market: str,
                            out_dir: Path = REPORTS_DIR) -> Path:
    """Write the shortlist parquet (exact schema, no row index) and return its path."""
    path = shortlist_path(market, out_dir=out_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    frame = shortlist[list(SHORTLIST_COLUMNS)] if len(shortlist) else _empty_shortlist()
    frame.to_parquet(path, index=False)
    return path
