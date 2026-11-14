"""WI-016 Step 6 (fix) — decision-rule synthesis into the shortlist artifact.

The meta-labeler (`src.wi016.meta_labeler`) predicts, per cleared barrier target,
the calibrated probability that the long bet's **profit barrier** is touched
first. This module turns that probability plus the point-in-time barrier geometry
into the four decision components the design asks for:

* **entry** — the top-decile primary event (long side) on the scoring date;
* **exit** — the symmetric barrier ``close ± k·ATR_t`` and the vertical time stop
  at ``h`` bars;
* **size** — meta-probability sizing, ``max(0, 2p − 1)`` (a confidence proxy, not
  a capital allocation);
* **abstain** — ``NO_TRADE`` is the **default**.

Rule v2 (admin gate decision 2026-10-30, Option B — HOLD + fix)
--------------------------------------------------------------
The step-6 rule compared a policy-scale number (expected edge in bps) with a
barrier-distance payoff and let the cost band almost never bind (99.3% TRADE).
Rule v2 puts expected edge and cost on the **same terms** and derives the
breakeven probability from the cost + slippage band:

    gross edge (bps) = (2p − 1) · k·ATR/close · 10000
    breakeven p*      = 0.5 + (cost_bps + slippage_bps) / (2 · k·ATR/close · 10000)
    net edge (bps)    = gross edge − (cost_bps + slippage_bps)

``p*`` is exactly the probability at which the net expected edge is zero, so
``p ≥ p*`` and ``net > 0`` are the same condition. A row is **TRADE** only when
``p_meta ≥ p*`` **and** ``p_meta ≥ floor``, where the probability ``floor`` is
**calibrated out-of-fold** (see :func:`calibrate_prob_floor`) rather than
hand-picked; otherwise it is ``NO_TRADE`` carrying the binding reason.

Output: ``reports/wi016_shortlist_{market}.parquet`` — a **new** WI-014-compatible
artifact (the WI-014 shortlist schema ``rank, symbol, <E5 factors>, scoring_date``
plus the meta columns) and ``reports/wi016_actions_v2_{market}.md``. Frozen
``reports/wi014_*`` artifacts are never touched and **no order execution exists**
anywhere in this module.
"""

from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

import numpy as np
import pandas as pd

from src.factors.e5_baseline import E5_FACTORS
from src.market_cli import add_market_argument, cli_markets, report_path
from src.wi016.meta_labeler import PRIMARY_COLUMN, TOP_DECILE_Q, primary_pct_rank, target_grid
from src.wi016.triple_barrier import barrier_levels

BASE_DIR = Path(__file__).resolve().parents[2]
REPORTS_DIR = BASE_DIR / "reports"

COST_BPS = 20.0
"""Standing round-trip commission band (unconfirmed WI-011 assumption; admin-adjudicated)."""

SLIPPAGE_BPS = 5.0
"""Standing round-trip slippage band added to the commission band in rule v2."""

META_MIN_PROB = 0.5
"""Fallback probability floor when no out-of-fold predictions are available."""

MIN_RECALL_FOR_FLOOR = 0.5
"""Minimum OOF recall the calibrated floor must keep (guards the all-abstain corner).

Maximising OOF precision alone is degenerate (threshold → 1 ⇒ precision → 1,
recall → 0). The floor is therefore the highest threshold whose OOF recall is at
least this value — i.e. the point on the precision/recall curve that maximises
precision subject to a stated minimum recall.
"""

BPS = 1e4

SENSITIVITY_COSTS: tuple[float, ...] = (10.0, 20.0, 30.0)
"""Commission bands re-tested in the sensitivity table."""

SENSITIVITY_SLIPPAGE: tuple[float, ...] = (0.0, 5.0, 10.0)
"""Slippage bands re-tested in the sensitivity table."""

SHORTLIST_COLUMNS: tuple[str, ...] = (
    "rank", "symbol", *E5_FACTORS, "scoring_date",
    "market", "target", "k", "h",
    "primary", "primary_pct", "decile_flag",
    "p_meta", "meta_calibration", "p_star", "p_floor",
    "entry_close", "atr", "barrier_upper", "barrier_lower", "time_stop_bars",
    "expected_gross_bps", "cost_bps", "slippage_bps", "net_bps",
    "size", "decision", "abstain_reason",
)
"""WI-014-compatible shortlist schema (its columns first) plus the meta columns."""

ABSTAIN_REASONS: tuple[str, ...] = ("ok", "p_below_floor", "net_edge_nonpositive", "undefined")

__all__ = [
    "ABSTAIN_REASONS",
    "COST_BPS",
    "META_MIN_PROB",
    "MIN_RECALL_FOR_FLOOR",
    "SENSITIVITY_COSTS",
    "SENSITIVITY_SLIPPAGE",
    "SHORTLIST_COLUMNS",
    "SLIPPAGE_BPS",
    "band_sensitivity",
    "breakeven_prob",
    "build_shortlist",
    "calibrate_prob_floor",
    "decide_action",
    "expected_edge_bps",
    "shortlist_path",
    "size_from_meta",
    "write_actions_v2_report",
    "write_shortlist_parquet",
]


# --------------------------------------------------------------------------- #
# Decision rule v2 (units reconciled; breakeven probability from cost+slippage)
# --------------------------------------------------------------------------- #
def _valid_geometry(close: float, atr: float, k: float) -> bool:
    return (
        np.isfinite(close) and np.isfinite(atr) and np.isfinite(k)
        and close > 0.0 and atr >= 0.0 and k > 0.0
    )


def breakeven_prob(cost_bps: float, slippage_bps: float, k: float, atr: float,
                   close: float) -> float:
    """Per-event breakeven probability ``p*`` for the symmetric barrier bet.

    ``p* = 0.5 + (cost_bps + slippage_bps) / (2 · k·ATR/close · 10000)`` — the
    probability at which the gross expected edge equals the total cost band. An
    invalid geometry (``ATR = 0`` included) yields ``inf``/``NaN`` so no bet clears.
    """
    if not _valid_geometry(float(close), float(atr), float(k)):
        return float("nan")
    if float(atr) == 0.0:
        return float("inf")
    denom = 2.0 * float(k) * (float(atr) / float(close)) * BPS
    return 0.5 + (float(cost_bps) + float(slippage_bps)) / denom


def expected_edge_bps(p_meta: float, close: float, atr: float, k: float,
                      cost_bps: float = COST_BPS, slippage_bps: float = SLIPPAGE_BPS) -> dict:
    """Symmetric-barrier net expected edge in bps, with the breakeven probability.

    ``gross = (2p − 1) · k·ATR/close`` in bps (payoff ``+k·ATR`` at probability
    ``p``, ``−k·ATR`` otherwise) and ``net = gross − (cost_bps + slippage_bps)``.
    Edge and cost are therefore on the same terms (bps of price). NaN/invalid
    geometry yields a NaN edge (and therefore ``NO_TRADE``).
    """
    p = float(p_meta)
    c = float(close)
    a = float(atr)
    kk = float(k)
    cost = float(cost_bps)
    slip = float(slippage_bps)
    total = cost + slip
    base = {
        "gross_bps": float("nan"),
        "net_bps": float("nan"),
        "cost_bps": cost,
        "slippage_bps": slip,
        "total_cost_bps": total,
        "p_star": float("nan"),
    }
    if not np.isfinite(p) or not _valid_geometry(c, a, kk):
        return base
    p_star = breakeven_prob(cost, slip, kk, a, c)
    gross = (2.0 * p - 1.0) * (kk * a / c) * BPS
    base.update({"gross_bps": gross, "net_bps": gross - total, "p_star": p_star})
    return base


def size_from_meta(p_meta: float) -> float:
    """Meta-probability size in ``[0, 1]``: ``max(0, 2p − 1)``; NaN sizes to 0."""
    p = float(p_meta)
    if not np.isfinite(p):
        return 0.0
    return float(min(1.0, max(0.0, 2.0 * p - 1.0)))


def decide_action(p_meta: float, close: float, atr: float, k: float,
                  cost_bps: float = COST_BPS, slippage_bps: float = SLIPPAGE_BPS,
                  min_prob: float = META_MIN_PROB) -> dict:
    """Entry/exit/size/abstain decision for one event. ``NO_TRADE`` is the default.

    Trades only when ``p_meta`` clears **both** the per-event breakeven ``p*``
    (equivalently, net edge > 0 under the ``cost_bps + slippage_bps`` band) **and**
    the calibrated probability ``min_prob`` floor. The returned ``abstain_reason``
    names whichever threshold is binding. Barrier levels, net edge, ``p*`` and the
    size make each row auditable; no order execution exists.
    """
    k = float(k)
    edge = expected_edge_bps(p_meta, close, atr, k, cost_bps=cost_bps, slippage_bps=slippage_bps)
    floor = float(min_prob)
    p_star = float(edge["p_star"])
    upper = lower = float("nan")
    if np.isfinite(float(close)) and np.isfinite(float(atr)):
        u, l = barrier_levels(np.asarray([float(close)]), np.asarray([float(atr)]), k)
        upper, lower = float(u[0]), float(l[0])

    p = float(p_meta)
    if not np.isfinite(p) or not np.isfinite(edge["net_bps"]):
        reason = "undefined"
    elif p < floor and (not np.isfinite(p_star) or floor >= p_star):
        reason = "p_below_floor"
    elif p < p_star:
        reason = "net_edge_nonpositive"
    elif p < floor:
        reason = "p_below_floor"
    else:
        reason = "ok"
    trade = reason == "ok"
    return {
        "gross_bps": edge["gross_bps"],
        "net_bps": edge["net_bps"],
        "cost_bps": edge["cost_bps"],
        "slippage_bps": edge["slippage_bps"],
        "p_star": p_star,
        "p_floor": floor,
        "barrier_upper": upper,
        "barrier_lower": lower,
        "size": size_from_meta(p) if trade else 0.0,
        "decision": "TRADE" if trade else "NO_TRADE",
        "abstain_reason": reason,
    }


# --------------------------------------------------------------------------- #
# Out-of-fold calibrated probability floor
# --------------------------------------------------------------------------- #
def _precision_recall_curve(oof: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Threshold, precision, recall and predicted-share arrays from sorted OOF scores."""
    order = np.argsort(oof, kind="mergesort")[::-1]
    scores = oof[order]
    labels = y[order]
    cum_tp = np.cumsum(labels)
    n_pred = np.arange(1, labels.size + 1, dtype="float64")
    precision = cum_tp / n_pred
    positives = float(labels.sum())
    recall = cum_tp / positives if positives > 0 else np.zeros_like(n_pred)
    share = n_pred / float(labels.size)
    return scores, precision, recall, share, n_pred


def calibrate_prob_floor(
    meta_result: dict,
    min_recall: float = MIN_RECALL_FOR_FLOOR,
    floor_lower_bound: float = META_MIN_PROB,
    n_sweep: int = 11,
) -> dict:
    """Choose the OOF-calibrated probability floor (not hand-picked).

    Pools the out-of-fold predictions of every cleared target and restricts to
    **top-decile** barrier-resolved events — the stratum the shipped decisions
    trade. Selects the threshold that maximises OOF precision subject to OOF
    recall ≥ ``min_recall`` (excluding the degenerate all-abstain corner) and
    ≥ ``floor_lower_bound`` (a floor below a coin flip would be a vacuous
    filter, so the near-inert corner is also excluded). Reports precision, recall,
    predicted-positive (trade) share and a compact precision/recall sweep. Falls
    back to :data:`META_MIN_PROB` when no OOF predictions carrying labels are
    available (e.g. unit-test fixtures).
    """
    oofs: list[np.ndarray] = []
    labels: list[np.ndarray] = []
    deciles: list[np.ndarray] = []
    for res in meta_result.get("targets", {}).values():
        oof, y, flag = res.get("oof"), res.get("oof_label"), res.get("oof_decile")
        if oof is None or y is None or flag is None:
            continue
        oofs.append(np.asarray(oof, dtype="float64"))
        labels.append(np.asarray(y, dtype="float64"))
        deciles.append(np.asarray(flag))
    if not oofs:
        return {"floor": META_MIN_PROB, "precision": float("nan"), "recall": float("nan"),
                "trade_share": float("nan"), "n_events": 0, "n_pred": 0,
                "pos_rate": float("nan"), "min_recall": float(min_recall),
                "floor_lower_bound": float(floor_lower_bound),
                "source": "fallback_default", "sweep": []}

    oof = np.concatenate(oofs)
    y = np.concatenate(labels)
    flag = np.concatenate(deciles)
    keep = np.isfinite(oof) & (flag == 1)
    oof, y = oof[keep], y[keep]
    if oof.size == 0 or y.sum() == 0:
        return {"floor": META_MIN_PROB, "precision": float("nan"), "recall": float("nan"),
                "trade_share": float("nan"), "n_events": int(oof.size), "n_pred": 0,
                "pos_rate": float(y.mean()) if y.size else float("nan"),
                "min_recall": float(min_recall), "floor_lower_bound": float(floor_lower_bound),
                "source": "fallback_default", "sweep": []}

    scores, precision, recall, share, _n_pred = _precision_recall_curve(oof, y)
    recall_ok = recall >= (float(min_recall) - 1e-12)
    bounded = scores >= float(floor_lower_bound)
    feasible = recall_ok & bounded
    if feasible.any():
        idx = np.where(feasible)[0]
        best = int(idx[int(np.argmax(precision[idx]))])
        source = "oof_calibrated"
    elif recall_ok.any():  # no threshold at/above the lower bound keeps recall — use the best below it
        idx = np.where(recall_ok)[0]
        best = int(idx[int(np.argmax(precision[idx]))])
        source = "oof_calibrated_below_lower_bound"
    else:  # pragma: no cover - a degenerate but finite recall floor this low is unreachable here
        best = int(np.argmax(precision))
        source = "oof_calibrated_no_recall_floor"
    floor = float(scores[best])

    step = max(1, scores.size // max(1, n_sweep))
    sweep: list[dict] = []
    for i in range(0, scores.size, step):
        row = {"threshold": float(scores[i]), "precision": float(precision[i]),
               "recall": float(recall[i]), "trade_share": float(share[i])}
        if sweep and round(sweep[-1]["threshold"], 6) == round(row["threshold"], 6):
            continue
        sweep.append(row)
    return {
        "floor": floor,
        "precision": float(precision[best]),
        "recall": float(recall[best]),
        "trade_share": float(share[best]),
        "n_events": int(oof.size),
        "n_pred": int(_n_pred[best]),
        "pos_rate": float(y.mean()),
        "min_recall": float(min_recall),
        "floor_lower_bound": float(floor_lower_bound),
        "source": source,
        "sweep": sweep,
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


def actions_v2_report_path(market: str, out_dir: Path = REPORTS_DIR) -> Path:
    """`reports/wi016_actions_v2_{market}.md` — the corrected-rule report."""
    return report_path(out_dir, "wi016_actions_v2", market, ".md")


def _empty_shortlist() -> pd.DataFrame:
    return pd.DataFrame({c: pd.Series(dtype="float64") for c in SHORTLIST_COLUMNS})


def build_shortlist(
    panel: pd.DataFrame,
    meta_result: dict,
    market: str,
    cost_bps: float = COST_BPS,
    slippage_bps: float = SLIPPAGE_BPS,
    scoring_date=None,
    q: float = TOP_DECILE_Q,
    min_prob: float | None = None,
) -> tuple[pd.DataFrame, dict]:
    """Assemble the shortlist from the meta models + the latest cross-section.

    Events are the **top-decile** long-side primary rows on the scoring date
    (default: the panel's latest date); one row per (symbol, cleared target).
    Decisions come from :func:`decide_action` under rule v2; the probability floor
    is calibrated out-of-fold from ``meta_result`` unless ``min_prob`` is given.
    The artifact carries entry, barrier/time-stop exit, ``p*``/floor, size and
    abstain fields. No order execution.
    """
    targets = meta_result.get("targets", {})
    floor_info = (calibrate_prob_floor(meta_result) if min_prob is None
                  else {"floor": float(min_prob), "source": "explicit", "precision": float("nan"),
                        "recall": float("nan"), "trade_share": float("nan"), "n_events": 0,
                        "n_pred": 0, "pos_rate": float("nan"),
                        "min_recall": float(MIN_RECALL_FOR_FLOOR),
                        "floor_lower_bound": float("nan"), "sweep": []})
    floor = float(floor_info["floor"])
    meta_common = {"market": market, "scoring_date": None, "n_rows": 0, "n_trade": 0,
                   "n_no_trade": 0, "cost_bps": float(cost_bps), "slippage_bps": float(slippage_bps),
                   "p_floor": floor, "floor_info": floor_info, "columns": list(SHORTLIST_COLUMNS)}
    if panel is None or panel.empty or not targets:
        return _empty_shortlist(), dict(meta_common)

    date = pd.Timestamp(scoring_date) if scoring_date is not None else pd.Timestamp(panel["date"].max())
    latest = panel[panel["date"] == date]
    if latest.empty:
        info = dict(meta_common)
        info["scoring_date"] = str(date.date())
        return _empty_shortlist(), info

    pct = primary_pct_rank(latest[PRIMARY_COLUMN].to_numpy(), latest["date"].to_numpy())
    top = latest[np.isfinite(pct) & (pct >= q)].copy()
    if top.empty:
        info = dict(meta_common)
        info["scoring_date"] = str(date.date())
        return _empty_shortlist(), info
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
        decisions = [decide_action(p, c, a, k, cost_bps=cost_bps, slippage_bps=slippage_bps, min_prob=floor)
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
            "p_star": np.asarray([d["p_star"] for d in decisions], dtype="float32"),
            "p_floor": np.float32(floor),
            "entry_close": close.astype("float32"),
            "atr": atr.astype("float32"),
            "barrier_upper": np.asarray([d["barrier_upper"] for d in decisions], dtype="float32"),
            "barrier_lower": np.asarray([d["barrier_lower"] for d in decisions], dtype="float32"),
            "time_stop_bars": np.int16(h),
            "expected_gross_bps": np.asarray([d["gross_bps"] for d in decisions], dtype="float32"),
            "cost_bps": np.float32(cost_bps),
            "slippage_bps": np.float32(slippage_bps),
            "net_bps": np.asarray([d["net_bps"] for d in decisions], dtype="float32"),
            "size": np.asarray([d["size"] for d in decisions], dtype="float32"),
            "decision": [d["decision"] for d in decisions],
            "abstain_reason": [d["abstain_reason"] for d in decisions],
        })
        for f in E5_FACTORS:
            rows[f] = top[f].to_numpy(dtype="float32") if f in top.columns else np.float32("nan")
        frames.append(rows)

    if not frames:
        info = dict(meta_common)
        info["scoring_date"] = str(date.date())
        return _empty_shortlist(), info

    shortlist = pd.concat(frames, ignore_index=True)
    shortlist = shortlist.sort_values(
        ["target", "p_meta", "symbol"], ascending=[True, False, True], kind="mergesort"
    ).reset_index(drop=True)
    shortlist.insert(0, "rank", shortlist.groupby("target", sort=False).cumcount().add(1).astype("int32"))
    shortlist = shortlist[list(SHORTLIST_COLUMNS)]

    info = dict(meta_common)
    info.update({
        "scoring_date": str(date.date()),
        "n_rows": int(len(shortlist)),
        "n_trade": int((shortlist["decision"] == "TRADE").sum()),
        "n_no_trade": int((shortlist["decision"] == "NO_TRADE").sum()),
        "columns": list(shortlist.columns),
    })
    return shortlist, info


def write_shortlist_parquet(shortlist: pd.DataFrame, market: str,
                            out_dir: Path = REPORTS_DIR) -> Path:
    """Write the shortlist parquet (exact schema, no row index) and return its path."""
    path = shortlist_path(market, out_dir=out_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    frame = shortlist[list(SHORTLIST_COLUMNS)] if len(shortlist) else _empty_shortlist()
    frame.to_parquet(path, index=False)
    return path


# --------------------------------------------------------------------------- #
# Band sensitivity (cost × slippage) — pure recompute, no retraining
# --------------------------------------------------------------------------- #
def band_sensitivity(
    shortlist: pd.DataFrame,
    costs: tuple[float, ...] = SENSITIVITY_COSTS,
    slippages: tuple[float, ...] = SENSITIVITY_SLIPPAGE,
    min_prob: float | None = None,
) -> list[dict]:
    """Trade share and net-edge distribution across the cost × slippage grid.

    Re-decides each shortlist row under every band from its stored ``p_meta`` and
    barrier geometry (no model is refit). ``min_prob`` defaults to the row's
    ``p_floor`` (the calibrated floor), so the floor is held fixed across bands.
    """
    cells: list[dict] = []
    if shortlist is None or shortlist.empty:
        for cost in costs:
            for slip in slippages:
                cells.append({"cost_bps": float(cost), "slippage_bps": float(slip),
                              "n_rows": 0, "n_trade": 0, "trade_share": float("nan"),
                              "net_bps_median": float("nan"), "net_bps_mean": float("nan")})
        return cells
    p = shortlist["p_meta"].to_numpy(dtype="float64")
    c = shortlist["entry_close"].to_numpy(dtype="float64")
    a = shortlist["atr"].to_numpy(dtype="float64")
    k = shortlist["k"].to_numpy(dtype="float64")
    floor = float(min_prob) if min_prob is not None else float(shortlist["p_floor"].iloc[0])
    n = len(shortlist)
    for cost in costs:
        for slip in slippages:
            decisions = [decide_action(pp, cc, aa, kk, cost_bps=cost, slippage_bps=slip, min_prob=floor)
                         for pp, cc, aa, kk in zip(p, c, a, k)]
            traded = [d["net_bps"] for d in decisions if d["decision"] == "TRADE"]
            n_trade = len(traded)
            cells.append({
                "cost_bps": float(cost), "slippage_bps": float(slip),
                "n_rows": int(n), "n_trade": int(n_trade),
                "trade_share": float(n_trade / n) if n else float("nan"),
                "net_bps_median": float(np.median(traded)) if traded else float("nan"),
                "net_bps_mean": float(np.mean(traded)) if traded else float("nan"),
            })
    return cells


# --------------------------------------------------------------------------- #
# Report
# --------------------------------------------------------------------------- #
def _fmt(value, spec: str = "{:.4f}", empty: str = "n/a") -> str:
    v = float(value)
    return empty if not np.isfinite(v) else spec.format(v)


def write_actions_v2_report(
    market: str,
    shortlist: pd.DataFrame,
    info: dict,
    sensitivity: list[dict] | None = None,
    out_dir: Path = REPORTS_DIR,
) -> Path:
    """Write `reports/wi016_actions_v2_{market}.md` and return its path."""
    out_dir.mkdir(parents=True, exist_ok=True)
    path = actions_v2_report_path(market, out_dir=out_dir)
    floor_info = info.get("floor_info", {}) or {}
    n = int(info.get("n_rows", 0))
    n_trade = int(info.get("n_trade", 0))
    trade_share = (n_trade / n) if n else float("nan")
    cost = float(info.get("cost_bps", COST_BPS))
    slip = float(info.get("slippage_bps", SLIPPAGE_BPS))

    lines = [
        f"# WI-016 step-6 fix — decision rule v2 — {market}",
        "",
        f"- Generated (UTC): {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        f"- Artifact: `reports/wi016_shortlist_{market}.parquet` (re-emitted under rule v2)",
        f"- Baseline band: commission {cost:.0f} bps + slippage {slip:.0f} bps "
        f"(total {cost + slip:.0f} bps); scoring date {info.get('scoring_date')}",
        "- Model unchanged from step 6 (`p_meta` identical; no model spec retrained); "
        "frozen `reports/wi014_*` / `reports/perfanalytics/` untouched; USD remains descriptive "
        "(NOT_CLEAR at the addendum gate).",
        "",
        "## Rule v2 (expected edge and cost on consistent terms)",
        "",
        "- `gross edge (bps) = (2·p − 1) · k·ATR/close · 10000`",
        "- `breakeven p* = 0.5 + (cost_bps + slippage_bps) / (2 · k·ATR/close · 10000)` per event",
        "- `net edge (bps) = gross edge − (cost_bps + slippage_bps)`",
        "- **TRADE** iff `p_meta ≥ p*` (equivalently net edge > 0) **and** `p_meta ≥ floor`; "
        "otherwise **NO_TRADE** carrying the binding reason (`p_below_floor` / "
        "`net_edge_nonpositive` / `undefined`).",
        "- `p*` is derived per event from the barrier geometry, so a modest cost band now binds "
        "on low-volatility names instead of being dwarfed by the barrier-distance payoff.",
        "",
        "## Out-of-fold calibrated probability floor",
        "",
        f"- Selection: maximise OOF precision on barrier-resolved **top-decile** events subject "
        f"to OOF recall ≥ {_fmt(floor_info.get('min_recall'), '{:.2f}')} and the floor ≥ "
        f"{_fmt(floor_info.get('floor_lower_bound'), '{:.2f}')} (guards exclude the degenerate "
        "all-abstain and sub-coin-flip/vacuous-floor corners). Pooled across the cleared targets.",
        f"- Chosen floor: **{_fmt(floor_info.get('floor'))}**  "
        f"(source: {floor_info.get('source', 'n/a')})",
        f"- OOF precision {_fmt(floor_info.get('precision'))}, OOF recall "
        f"{_fmt(floor_info.get('recall'))}, OOF predicted-positive share "
        f"{_fmt(floor_info.get('trade_share'), '{:.1%}')} "
        f"(n = {int(floor_info.get('n_events', 0)):,}, OOF pos rate "
        f"{_fmt(floor_info.get('pos_rate'), '{:.3f}')})",
        "",
        "| OOF threshold | precision | recall | predicted share |",
        "| ---: | ---: | ---: | ---: |",
    ]
    for row in floor_info.get("sweep", []):
        lines.append(f"| {_fmt(row['threshold'])} | {_fmt(row['precision'])} | "
                     f"{_fmt(row['recall'])} | {_fmt(row['trade_share'], '{:.1%}')} |")

    lines += [
        "",
        f"## Baseline shortlist ({cost:.0f} + {slip:.0f} bps)",
        "",
        f"- Rows: {n} ({n_trade} TRADE / {int(info.get('n_no_trade', 0))} NO_TRADE; "
        f"trade share {_fmt(trade_share, '{:.1%}')})",
    ]
    if n and "abstain_reason" in shortlist:
        counts = shortlist["abstain_reason"].value_counts()
        reasons = "; ".join(f"{r}: {int(counts[r])}" for r in ABSTAIN_REASONS if r in counts)
        lines.append(f"- Abstain reasons: {reasons}")
        traded = shortlist.loc[shortlist["decision"] == "TRADE", "net_bps"].to_numpy(dtype="float64")
        lines.append(
            "- Tradeable net edge (bps): "
            + (f"min {_fmt(traded.min())}, p25 {_fmt(np.percentile(traded, 25))}, "
               f"median {_fmt(np.median(traded))}, p75 {_fmt(np.percentile(traded, 75))}, "
               f"max {_fmt(traded.max())}, mean {_fmt(traded.mean())}"
               if traded.size else "no tradeable rows")
        )

    if sensitivity:
        lines += [
            "",
            "## Sensitivity — trade share and net-edge across cost × slippage",
            "",
            "| commission (bps) | slippage (bps) | TRADE | trade share | median net (bps) | mean net (bps) |",
            "| ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
        for cell in sensitivity:
            lines.append(
                f"| {cell['cost_bps']:.0f} | {cell['slippage_bps']:.0f} | {cell['n_trade']} | "
                f"{_fmt(cell['trade_share'], '{:.1%}')} | {_fmt(cell['net_bps_median'])} | "
                f"{_fmt(cell['net_bps_mean'])} |"
            )

    lines += [
        "",
        "## Caveats",
        "",
        "- The floor is calibrated in-sample-CV (OOF) and applied to the same panel's scoring date; "
        "it is a research decision threshold, not a validated trading edge.",
        "- Pooling OOF across targets lets the higher-event h8 targets dominate the pooled "
        "precision curve; per-target sensitivities are not separately floored.",
        "- The meta-label is a first-touch binary; intra-horizon drift beyond the flat cost + "
        "slippage band is not modelled. No paper-tracked performance exists yet.",
        "- **No order execution exists** anywhere in this pipeline; this artifact is research "
        "context behind the human gate.",
    ]
    path.write_text("\n".join(lines) + "\n")
    return path


# --------------------------------------------------------------------------- #
# Driver (CAD only under the addendum gate; no order execution)
# --------------------------------------------------------------------------- #
def run_actions_v2(
    market: str = "CAD",
    *,
    allow_fixture: bool = False,
    max_symbols: int | None = None,
    n_splits: int = 5,
    placebo_seeds: int | None = None,
    cost_bps: float = COST_BPS,
    slippage_bps: float = SLIPPAGE_BPS,
    out_dir: Path = REPORTS_DIR,
) -> dict:
    """Re-run the unchanged meta-labeler and re-emit the shortlist under rule v2.

    The models are not re-specified (`p_meta` reproduces the step-6 artifact); only
    the decision rule, the calibrated floor and the report change.
    """
    from src.wi016 import meta_labeler as ml

    kwargs = {} if placebo_seeds is None else {"placebo_seeds": placebo_seeds}
    panel = ml.build_meta_panel(market, allow_fixture=allow_fixture, max_symbols=max_symbols)
    result = ml.meta_labeler(panel, market, n_splits=n_splits, **kwargs)
    shortlist, info = build_shortlist(panel, result, market, cost_bps=cost_bps,
                                      slippage_bps=slippage_bps)
    parquet = write_shortlist_parquet(shortlist, market, out_dir=out_dir)
    info["path"] = str(parquet)
    sensitivity = band_sensitivity(shortlist)
    report = write_actions_v2_report(market, shortlist, info, sensitivity, out_dir=out_dir)
    return {"market": market, "shortlist": shortlist, "shortlist_meta": info,
            "sensitivity": sensitivity, "report": str(report)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="WI-016 step-6 decision rule v2 (re-emit shortlist)")
    add_market_argument(parser)
    parser.add_argument("--allow-fixture", action="store_true")
    parser.add_argument("--max-symbols", type=int, default=None,
                        help="Debug bound on symbols per market (default: all).")
    parser.add_argument("--n-splits", type=int, default=5)
    parser.add_argument("--placebo-seeds", type=int, default=None)
    parser.add_argument("--cost-bps", type=float, default=COST_BPS)
    parser.add_argument("--slippage-bps", type=float, default=SLIPPAGE_BPS)
    args = parser.parse_args(argv)

    markets = cli_markets(args.market, prog="wi016.actions")
    if markets is None:
        return 2
    for mkt in markets:
        res = run_actions_v2(mkt, allow_fixture=args.allow_fixture, max_symbols=args.max_symbols,
                             n_splits=args.n_splits, placebo_seeds=args.placebo_seeds,
                             cost_bps=args.cost_bps, slippage_bps=args.slippage_bps)
        print(f"[wi016.actions] {mkt}: shortlist -> {res['shortlist_meta']['path']} "
              f"({res['shortlist_meta']['n_rows']} rows, {res['shortlist_meta']['n_trade']} TRADE, "
              f"floor {res['shortlist_meta']['p_floor']:.4f})")
        print(f"[wi016.actions] {mkt}: report -> {res['report']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
