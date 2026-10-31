"""WI-016 addendum — honest-edge probe (both markets), PM finding 2026-10-30.

The step-5 probe labels conflate barrier first-touch with vertical drift sign, so
its ±1 targets are not profit/stop counts and its ``|IC|*1000bps`` edge proxy
overstates the tradeable edge. This module re-tests the step-5 edge under the PM
finding's corrections, reusing the existing WI-016 machinery
(`src.wi016.triple_barrier`, `src.wi016.probe`, the unified feature grid, E5):

1. **Touch-restricted probe** — within-date rank-IC of the unified features and
   E5 against (a) barrier-resolved labels (``tb_touch_*`` ∈ {+1,−1}) and (b) the
   realized-return regression target ``tb_fret_h*``; per-target class counts and
   the verdict change vs step 5.
2. **Overlap-aware statistics** — average-uniqueness weights (AFML ch. 4) on the
   per-date IC t-stat for overlapping windows, weighted vs unweighted.
3. **Primary bake-off (de-anchor E5)** — candidate primaries (E5 composite rank,
   ``mom_12_1``, ``vol_20``, ``yangzhang_21``, ``tc_rating``) each gating events
   (top-decile per date, long side); event-gated vs ungated IC.
4. **Cost sensitivity** — net-edge bands at 10 / 20 / 30 bps, each ending in an
   explicit per-market CLEAR / NOT_CLEAR line.
5. Duration columns live in `src.wi016.triple_barrier`; summarised here.

Analysis + reports + tests only: no model training, no shortlist, no frozen
artifact writes. All artifacts are ``wi016_addendum_``-prefixed.

CLI::

    python -m src.wi016.addendum --market USD
    python -m src.wi016.addendum --market CAD --allow-fixture
"""

from __future__ import annotations

import argparse
import datetime as dt
import gc
import re
from pathlib import Path

import numpy as np
import pandas as pd

from src.factors.e5_baseline import E5_FACTORS, factor_frame
from src.feature_engine import compute_features_wi016, iter_market_symbols
from src.market_cli import add_market_argument, cli_markets, report_path
from src.wi016.probe import (
    DEFAULT_COST_BPS,
    DEFAULT_FDR_ALPHA,
    IC_TO_BPS,
    N_PLACEBO_SEEDS,
    _fast_ic_detail,
    benjamini_hochberg,
    cost_overlay,
    decide_target,
    placebo_ic,
    within_date_ic,
)
from src.wi016.triple_barrier import (
    K_VALUES,
    VERTICAL_HORIZONS,
    _k_tag,
    compute_triple_barrier,
)

BASE_DIR = Path(__file__).resolve().parents[2]
REPORTS_DIR = BASE_DIR / "reports"
CONFIG_DIR = BASE_DIR / "config"

COST_BANDS: tuple[float, ...] = (10.0, 20.0, 30.0)
"""Unconfirmed WI-011 cost assumption — bands for the admin's flip point."""

PRIMARY_CANDIDATES: tuple[str, ...] = (
    "e5_composite",
    "mom_12_1",
    "vol_20",
    "yangzhang_21",
    "tc_rating",
)
"""Bake-off primaries; E5 is *not* assumed to win (de-anchoring)."""

TOP_DECILE_Q = 0.9
"""Top-decile share for event gating (long side, per date)."""

MIN_DATE = "2016-01-01"

__all__ = [
    "COST_BANDS",
    "PRIMARY_CANDIDATES",
    "band_verdicts",
    "build_addendum_panel",
    "duration_report",
    "e5_composite_rank",
    "event_uniqueness",
    "primary_bakeoff",
    "restricted_gate",
    "run_market",
    "step5_verdict",
    "top_decile_mask",
    "touch_restricted_mask",
    "uniqueness_weighted_stats",
]


# --------------------------------------------------------------------------- #
# Target masking helpers
# --------------------------------------------------------------------------- #
def touch_restricted_mask(touch) -> np.ndarray:
    """Rows whose first touch was a real barrier (``+1`` profit or ``−1`` stop).

    Vertical exits (``0``) and undefined events (``−9``) are excluded, so the
    target measures barrier capture rather than vertical drift sign.
    """
    t = np.asarray(touch, dtype="float64")
    return (t == 1.0) | (t == -1.0)


def _restricted_targets(panel: pd.DataFrame, k_values, horizons) -> tuple[list, list]:
    """Build ``(targets, class_counts)`` for the addendum.

    ``targets`` is a list of ``(name, values, mask, kind)``; ``kind`` is
    ``"touch_restricted"`` (barrier-resolved labels) or ``"realized_return"``
    (the ``tb_fret_h*`` regression target). ``class_counts`` records the touch
    mix per barrier label so the addendum report shows *why* the sample shrinks.
    """
    targets: list = []
    class_counts: list = []
    for k in k_values:
        tag = _k_tag(k)
        for h in horizons:
            lab_col = f"tb_label_{tag}_h{h}"
            touch_col = f"tb_touch_{tag}_h{h}"
            if lab_col not in panel.columns or touch_col not in panel.columns:
                continue
            lab = panel[lab_col].to_numpy(dtype="float64")
            touch = panel[touch_col].to_numpy(dtype="float64")
            finite = np.isfinite(lab)
            targets.append((lab_col, lab, finite & touch_restricted_mask(touch), "touch_restricted"))
            class_counts.append({
                "target": lab_col,
                "k": k,
                "h": h,
                "n_defined": int(finite.sum()),
                "n_restricted": int((finite & touch_restricted_mask(touch)).sum()),
                "profit": int((finite & (touch == 1.0)).sum()),
                "stop": int((finite & (touch == -1.0)).sum()),
                "vertical": int((finite & (touch == 0.0)).sum()),
            })
    for h in horizons:
        fret_col = f"tb_fret_h{h}"
        if fret_col not in panel.columns:
            continue
        fret = panel[fret_col].to_numpy(dtype="float64")
        targets.append((fret_col, fret, np.isfinite(fret), "realized_return"))
    return targets, class_counts


# --------------------------------------------------------------------------- #
# Deliverable 1 — touch-restricted probe (same gate clauses as step 5)
# --------------------------------------------------------------------------- #
def restricted_gate(
    panel: pd.DataFrame,
    feature_cols: list[str],
    market: str = "USD",
    k_values=K_VALUES,
    horizons=VERTICAL_HORIZONS,
    alpha: float = DEFAULT_FDR_ALPHA,
    cost_bps: float = DEFAULT_COST_BPS,
    placebo_seeds: int = N_PLACEBO_SEEDS,
    max_placebo_tests: int = 100,
    cost_bands=COST_BANDS,
    out_dir: Path = REPORTS_DIR,
) -> dict:
    """Re-run the step-5 gate on touch-restricted labels + realized returns.

    Same clauses (BH-FDR, WI-009b same-sign, five-seed placebo, cost overlay),
    but each target is evaluated only on its tradeable rows. Returns the
    decisions, the per-band verdicts and the class-count evidence; writes a
    ``wi016_addendum_probe_<market>.md`` report.
    """
    dates = panel["date"].to_numpy()
    targets, class_counts = _restricted_targets(panel, k_values, horizons)
    target_map = {name: (vals, mask) for name, vals, mask, _kind in targets}
    target_kind = {name: kind for name, _v, _m, kind in targets}
    target_names = [name for name, _v, _m, _k in targets]

    tests: list[dict] = []
    pvals: list[float] = []
    for name in target_names:
        vals, mask = target_map[name]
        v = vals[mask]
        d = dates[mask]
        for f in feature_cols:
            res = within_date_ic(panel[f].to_numpy(dtype="float64")[mask], v, d)
            tests.append({"target": name, "feature": f, "kind": target_kind[name], **res})
            pvals.append(res["p"])

    reject, qvals = benjamini_hochberg(np.asarray(pvals, dtype="float64"), alpha=alpha)
    for r, q in zip(tests, qvals):
        r["q"] = float(q) if np.isfinite(q) else float("nan")
        r["fdr_significant"] = bool(np.isfinite(q) and q <= alpha)

    survivors = sorted(
        (r for r in tests if r["fdr_significant"]), key=lambda r: abs(r["ic"]), reverse=True
    )[:max_placebo_tests]
    placebo_keys = {(r["target"], r["feature"]) for r in survivors}
    for r in tests:
        if (r["target"], r["feature"]) in placebo_keys:
            vals, mask = target_map[r["target"]]
            pl = placebo_ic(
                panel[r["feature"]].to_numpy(dtype="float64")[mask], vals[mask], dates[mask],
                seeds=placebo_seeds,
            )
            r["placebo_clear"] = pl["clear"]
            r["placebo_null_abs_max"] = pl["null_abs_max"]
        else:
            r["placebo_clear"] = False
            r["placebo_null_abs_max"] = float("nan")
        r["tradeable"] = cost_overlay(r["ic"], cost_bps)["tradeable"]

    decisions = [decide_target(t, tests, alpha=alpha) for t in target_names]
    # The honest, apples-to-apples re-test of step 5 is the barrier-resolved
    # label verdict; the realized-return targets are a separate diagnostic.
    outcome = _class_outcome(decisions, target_kind, "touch_restricted")
    fret_outcome = _class_outcome(decisions, target_kind, "realized_return")
    bands = band_verdicts(tests, target_names, alpha=alpha, cost_bands=cost_bands)
    s5 = step5_verdict(market, out_dir)

    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = report_path(out_dir, "wi016_addendum_probe", market)
    _write_probe_report(md_path, panel, market, feature_cols, target_names, tests,
                        decisions, class_counts, bands, outcome, fret_outcome, alpha, s5)
    return {
        "market": market,
        "outcome": outcome,
        "fret_outcome": fret_outcome,
        "step5": s5,
        "alpha": alpha,
        "cost_bps": cost_bps,
        "decisions": decisions,
        "class_counts": class_counts,
        "bands": bands,
        "tests": tests,
        "report": str(md_path),
    }


def _class_outcome(decisions: list[dict], kind_of: dict, kind: str) -> str:
    """CLEAR when any target of `kind` passes every clause."""
    return "CLEAR" if any(d["cleared"] and kind_of.get(d["target"]) == kind for d in decisions) else "NOT_CLEAR"


def band_verdicts(tests: list[dict], target_names: list[str], alpha: float = DEFAULT_FDR_ALPHA,
                  cost_bands=COST_BANDS) -> dict:
    """Per-cost-band clear/not-clear verdict (net edge = ``|IC|*1000 − band``).

    Verdicts are split by target class (``touch_restricted`` barrier labels vs
    ``realized_return`` regression targets) so the barrier-resolved verdict is
    never conflated with the long-horizon regression diagnostic.
    """
    kind_of = {r["target"]: r.get("kind") for r in tests}
    kinds = sorted({k for k in kind_of.values() if k})
    out: dict = {}
    for band in cost_bands:
        passing = [
            r for r in tests
            if r.get("fdr_significant") and r.get("same_sign") and r.get("placebo_clear")
            and np.isfinite(r.get("ic", np.nan)) and abs(r["ic"]) * IC_TO_BPS - band > 0.0
        ]
        per_target = {t: bool(any(r["target"] == t for r in passing)) for t in target_names}
        by_kind = {kind: bool(any(kind_of.get(r["target"]) == kind for r in passing))
                   for kind in kinds}
        out[float(band)] = {
            "cost_bps": float(band),
            "clear": bool(passing),
            "by_kind": by_kind,
            "n_tradeable": len(passing),
            "per_target": per_target,
            "best_ic": max((abs(r["ic"]) for r in passing), default=float("nan")),
        }
    return out


def _write_probe_report(md_path, panel, market, features, target_names, tests, decisions,
                        class_counts, bands, outcome, fret_outcome, alpha, step5=None):
    step5 = step5 or {}
    lines = [
        f"# WI-016 addendum honest-edge probe — {market}",
        "",
        f"- Generated (UTC): {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        f"- Panel rows: {len(panel):,} · features: {len(features)} · targets: {len(target_names)}",
        f"- BH-FDR alpha {alpha}; cost bands {list(COST_BANDS)} bps (unconfirmed WI-011 assumption)",
        "- Touch-restricted labels = barrier-resolved rows only (`tb_touch_*` ∈ {+1,−1});",
        "  realized-return targets are `tb_fret_h*`.",
        "",
        f"## DECISION @ {DEFAULT_COST_BPS:.0f} bps — barrier-resolved labels: **{outcome}**",
        "",
        f"## Diagnostic @ {DEFAULT_COST_BPS:.0f} bps — realized-return targets: **{fret_outcome}**",
        "",
        "The barrier-resolved verdict is the apples-to-apples re-test of step 5; the",
        "realized-return targets are a separate long-horizon regression diagnostic and",
        "must not be read as barrier capture.",
        "",
        "| target | kind | cleared | passing | best feature | best IC |",
        "| :--- | :--- | :---: | ---: | :--- | ---: |",
    ]
    kind = {r["target"]: r["kind"] for r in tests}
    for d in decisions:
        if d["best_feature"]:
            lines.append(f"| `{d['target']}` | {kind.get(d['target'], '-')} | "
                         f"{'yes' if d['cleared'] else 'no'} | {d['n_passing_features']} | "
                         f"`{d['best_feature']}` | {d['best_ic']:+.4f} |")
        else:
            lines.append(f"| `{d['target']}` | {kind.get(d['target'], '-')} | no | 0 | - | - |")

    lines += ["", "## Touch class counts (why the sample shrinks)", "",
              "| target | defined | profit | stop | vertical | touch-restricted |",
              "| :--- | ---: | ---: | ---: | ---: | ---: |"]
    for r in class_counts:
        lines.append(f"| `{r['target']}` | {r['n_defined']:,} | {r['profit']:,} | {r['stop']:,} | "
                     f"{r['vertical']:,} | {r['n_restricted']:,} |")

    dec_map = {d["target"]: d["cleared"] for d in decisions}
    changed = [t for t in dec_map if t in step5 and step5[t] != dec_map[t]]
    if step5:
        lines += ["", "## Verdict change vs step 5 (touch-restricted labels)", "",
                  "Step-5 verdicts parsed from the frozen `wi016_probe_<market>.md`; "
                  "addendum uses barrier-resolved samples.",
                  "",
                  "| target | step 5 | addendum | changed |",
                  "| :--- | :---: | :---: | :---: |"]
        for t in target_names:
            if t not in step5:
                continue
            lines.append(f"| `{t}` | {'CLEAR' if step5[t] else 'NOT_CLEAR'} | "
                         f"{'CLEAR' if dec_map.get(t) else 'NOT_CLEAR'} | "
                         f"{'YES' if t in changed else 'no'} |")
        lines += ["", f"- {len(changed)} target(s) flipped between step 5 and the addendum."]

    lines += ["", "## Cost sensitivity (net edge = |IC|·1000 − band)", "",
              "| band (bps) | barrier-resolved | realized-return | tradeable tests | best |IC| |",
              "| :--- | :---: | :---: | ---: | ---: |"]
    for band in COST_BANDS:
        b = bands[float(band)]
        bk = b["by_kind"]
        lines.append(f"| {band:.0f} | "
                     f"{'CLEAR' if bk.get('touch_restricted') else 'NOT_CLEAR'} | "
                     f"{'CLEAR' if bk.get('realized_return') else 'NOT_CLEAR'} | "
                     f"{b['n_tradeable']} | {b['best_ic']:.4f} |")
    lines += ["", "### Per-band per-market verdict lines", ""]
    for band in COST_BANDS:
        b = bands[float(band)]
        bk = b["by_kind"]
        lines.append(f"- **{market} @ {band:.0f} bps — barrier-resolved: "
                     f"{'CLEAR' if bk.get('touch_restricted') else 'NOT_CLEAR'}**")
        lines.append(f"- **{market} @ {band:.0f} bps — realized-return: "
                     f"{'CLEAR' if bk.get('realized_return') else 'NOT_CLEAR'}**")

    lines += ["", "## Top FDR-significant tests (restricted sample)", "",
              "| target | feature | IC | t | q | same-sign | placebo | tradeable@20 |",
              "| :--- | :--- | ---: | ---: | ---: | :---: | :---: | :---: |"]
    sig = sorted([r for r in tests if r["fdr_significant"]], key=lambda r: abs(r["ic"]), reverse=True)[:25]
    for r in sig:
        lines.append(f"| `{r['target']}` | `{r['feature']}` | {r['ic']:+.4f} | {r['t']:+.2f} | "
                     f"{r['q']:.4f} | {'Y' if r['same_sign'] else 'N'} | "
                     f"{'Y' if r['placebo_clear'] else 'N'} | {'Y' if r['tradeable'] else 'N'} |")
    if not sig:
        lines.append("| — | — | — | — | — | — | — | — |")
    md_path.write_text("\n".join(lines) + "\n")


# --------------------------------------------------------------------------- #
# Deliverable 2 — overlap-aware (average-uniqueness) statistics
# --------------------------------------------------------------------------- #
def event_uniqueness(dates, horizon: int, symbols=None) -> np.ndarray:
    """AFML ch. 4 average uniqueness per event for a forward ``[t+1, t+h]`` span.

    Concurrency is computed **per symbol** (a daily event series overlaps itself
    h-fold: h=8 daily events ⇒ mean uniqueness ≈ 1/8 in the interior). Passing
    `symbols` groups the rows by symbol; without it all rows are treated as one
    series. Each event's uniqueness is the mean of ``1/concurrency`` over its
    span; events whose window runs past the series end get NaN (tail mask), which
    matches the label NaN contract.
    """
    d = np.asarray(pd.to_datetime(pd.Series(dates)).to_numpy())
    if symbols is None:
        groups = [np.arange(d.size)]
    else:
        sym = np.asarray(symbols)
        groups = [np.where(sym == s)[0] for s in pd.unique(sym)]
    out = np.full(d.size, np.nan, dtype="float64")
    for idx in groups:
        if idx.size == 0:
            continue
        order = idx[np.argsort(d[idx], kind="mergesort")]
        dd = d[order]
        uniq = np.sort(pd.unique(dd))
        npos = uniq.size
        pos = np.searchsorted(uniq, dd)
        diff = np.zeros(npos + 1, dtype="float64")
        start = pos + 1
        end = pos + horizon
        valid = start <= (npos - 1)
        s = start[valid]
        e = np.minimum(end[valid], npos - 1)
        np.add.at(diff, s, 1.0)
        np.add.at(diff, e + 1, -1.0)
        conc = np.maximum(np.cumsum(diff[:npos]), 1.0)
        pref = np.concatenate([[0.0], np.cumsum(1.0 / conc)])
        span = e - s + 1
        u = np.full(pos.size, np.nan, dtype="float64")
        u[valid] = (pref[e + 1] - pref[s]) / span
        out[order] = u
    return out


def uniqueness_weighted_stats(ic_dates, ic_values, uniqueness, n_windows: int = 1) -> dict:
    """Weighted vs unweighted mean/t for a per-date IC series.

    Each date's weight is the mean average-uniqueness of its events, so
    overlapping windows (h=8 daily events ⇒ up to 8×) down-weight the
    pseudo-replication that inflates the unweighted t-stat.
    """
    ic_dates = np.asarray(ic_dates)
    v = np.asarray(ic_values, dtype="float64")
    u = np.asarray(uniqueness, dtype="float64")
    if v.size == 0 or v.size != u.size:
        return {"unweighted_ic": float("nan"), "unweighted_t": float("nan"),
                "weighted_ic": float("nan"), "weighted_t": float("nan"), "n_dates": 0,
                "effective_n": float("nan"), "mean_uniqueness": float("nan")}
    mean_ic = float(v.mean())
    unweighted_t = _t_stat(mean_ic, v)
    sw = float(np.nansum(u))
    sw2 = float(np.nansum(u ** 2))
    if sw > 0.0 and np.isfinite(sw) and (sw - sw2 / sw) > 0.0:
        mu = float(np.nansum(u * v) / sw)
        # Weighted unbiased variance + Kish effective sample size: with equal
        # weights this reproduces the unweighted t-stat exactly; overlapping
        # windows reduce n_eff and shrink |t| (the inflation becomes visible).
        var = float(np.nansum(u * (v - mu) ** 2) / (sw - sw2 / sw))
        # Effective (uniqueness-weighted) sample size: sum of uniqueness. With
        # no overlap (u=1) it equals n_dates and the t-stat matches exactly;
        # h-fold overlap gives sw ≈ n/h and shrinks |t| accordingly.
        n_eff = sw
        weighted_t = float(mu / np.sqrt(var / n_eff)) if var > 0.0 else float("nan")
    else:
        mu, weighted_t, n_eff = float("nan"), float("nan"), float("nan")
    return {"unweighted_ic": mean_ic, "unweighted_t": unweighted_t,
            "weighted_ic": mu, "weighted_t": weighted_t, "n_dates": int(v.size),
            "effective_n": float(n_eff), "mean_uniqueness": float(np.nanmean(u))}


def _t_stat(mean: float, values: np.ndarray) -> float:
    if values.size > 2 and values.std(ddof=1) > 0.0:
        return float(mean / (values.std(ddof=1) / np.sqrt(values.size)))
    return float("nan")


def _horizon_of(target_col: str, default: int = 20) -> int:
    m = re.search(r"_h(\d+)$", str(target_col))
    return int(m.group(1)) if m else default


def overlap_stats(panel: pd.DataFrame, tests: list[dict], per_target: int = 1) -> list[dict]:
    """Weighted vs unweighted IC/t for the best ``per_target`` tests per target."""
    dates = panel["date"].to_numpy()
    by_target: dict[str, list[dict]] = {}
    for r in tests:
        if np.isfinite(r["ic"]):
            by_target.setdefault(r["target"], []).append(r)
    cache: dict[int, np.ndarray] = {}
    out: list[dict] = []
    symbols = panel["symbol"].to_numpy() if "symbol" in panel.columns else None
    for tname, rows in by_target.items():
        h = _horizon_of(tname)
        best = sorted(rows, key=lambda r: abs(r["ic"]), reverse=True)[:per_target]
        mask = _target_mask(panel, tname, h)
        if h not in cache:
            cache[h] = event_uniqueness(dates, h, symbols=symbols)
        u = cache[h][mask]
        for r in best:
            _ic, _t, n, ic_dates, ic_vals = _fast_ic_detail(
                panel[r["feature"]].to_numpy(dtype="float64")[mask],
                panel[tname].to_numpy(dtype="float64")[mask], dates[mask],
            )
            # align uniqueness to the per-date IC series
            date_u = pd.Series(u).groupby(pd.Series(dates[mask])).mean()
            w = date_u.reindex(pd.Index(ic_dates)).to_numpy(dtype="float64")
            stats = uniqueness_weighted_stats(ic_dates, ic_vals, w)
            out.append({"target": tname, "feature": r["feature"], "horizon": h, **stats})
    return out


def _target_mask(panel: pd.DataFrame, target_col: str, horizon: int) -> np.ndarray:
    if target_col.startswith("tb_fret_h"):
        return np.isfinite(panel[target_col].to_numpy(dtype="float64"))
    tag = target_col.split("_h")[0].replace("tb_label_", "")
    touch_col = f"tb_touch_{tag}_h{horizon}"
    lab = panel[target_col].to_numpy(dtype="float64")
    if touch_col in panel.columns:
        return np.isfinite(lab) & touch_restricted_mask(panel[touch_col].to_numpy(dtype="float64"))
    return np.isfinite(lab)


# --------------------------------------------------------------------------- #
# Deliverable 3 — primary bake-off (de-anchor E5)
# --------------------------------------------------------------------------- #
def e5_composite_rank(panel: pd.DataFrame, factors=E5_FACTORS) -> np.ndarray:
    """Per-date mean rank of the E5 factors (composite primary signal)."""
    frames = []
    for f in factors:
        if f not in panel.columns:
            continue
        s = pd.to_numeric(panel[f], errors="coerce")
        frames.append(s.groupby(panel["date"]).rank(pct=True))
    if not frames:
        return np.full(len(panel), np.nan)
    return pd.concat(frames, axis=1).mean(axis=1).to_numpy(dtype="float64")


def top_decile_mask(values, dates, q: float = TOP_DECILE_Q) -> np.ndarray:
    """Top-decile (long side) rows per date; NaN values never selected."""
    v = np.asarray(values, dtype="float64")
    s = pd.Series(np.where(np.isfinite(v), v, np.nan))
    pct = s.groupby(pd.Series(np.asarray(dates))).rank(pct=True).to_numpy()
    return np.isfinite(pct) & (pct >= q)


def primary_bakeoff(
    panel: pd.DataFrame,
    market: str = "USD",
    k_values=K_VALUES,
    horizons=VERTICAL_HORIZONS,
    candidates=PRIMARY_CANDIDATES,
    q: float = TOP_DECILE_Q,
    out_dir: Path = REPORTS_DIR,
) -> dict:
    """Gate events by each candidate primary; compare gated vs ungated IC.

    For every touch-restricted label the candidate primary's own within-date
    rank-IC is measured on the full restricted sample (ungated) and on its
    per-date top decile (gated). The primary that maximises the mean |gated IC|
    wins on data — E5 is not assumed.
    """
    dates = panel["date"].to_numpy()
    if "e5_composite" in candidates:
        panel = panel.copy()
        panel["e5_composite"] = e5_composite_rank(panel).astype("float32")

    available, skipped = [], []
    for c in candidates:
        if c in panel.columns and np.isfinite(panel[c].to_numpy(dtype="float64")).any():
            available.append(c)
        else:
            skipped.append(c)

    targets, _cc = _restricted_targets(panel, k_values, horizons)
    targets = [(n, v, m, kind) for n, v, m, kind in targets if kind == "touch_restricted"]

    rows: list[dict] = []
    for c in available:
        pv = panel[c].to_numpy(dtype="float64")
        ungated, gated, gated_n = [], [], []
        for name, vals, mask, _kind in targets:
            ug = within_date_ic(pv[mask], vals[mask], dates[mask])
            gmask = mask & top_decile_mask(pv, dates, q=q)
            gt = within_date_ic(pv[gmask], vals[gmask], dates[gmask])
            ungated.append(ug["ic"])
            gated.append(gt["ic"])
            gated_n.append(int(gmask.sum()))
        mean_u = float(np.nanmean([abs(x) for x in ungated])) if ungated else float("nan")
        mean_g = float(np.nanmean([abs(x) for x in gated])) if gated else float("nan")
        rows.append({"candidate": c, "mean_ungated_abs_ic": mean_u,
                     "mean_gated_abs_ic": mean_g, "n_targets": len(targets),
                     "mean_gated_events": float(np.mean(gated_n)) if gated_n else float("nan")})

    winner = None
    if rows:
        winner = max(rows, key=lambda r: (r["mean_gated_abs_ic"] if np.isfinite(r["mean_gated_abs_ic"]) else -1.0))

    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = report_path(out_dir, "wi016_addendum_bakeoff", market)
    lines = [
        f"# WI-016 addendum primary bake-off (E5 de-anchored) — {market}",
        "",
        f"- Generated (UTC): {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        f"- Target: touch-restricted barrier labels; gate = per-date top decile (q={q}), long side",
        f"- Candidates tested: {', '.join(f'`{c}`' for c in available) or 'none'}",
        f"- Skipped (absent in panel): {', '.join(f'`{c}`' for c in skipped) or 'none'}",
        "",
        "| primary | mean |ungated IC| | mean |gated IC| | gated events (mean) | n targets |",
        "| :--- | ---: | ---: | ---: | ---: |",
    ]
    for r in rows:
        lines.append(f"| `{r['candidate']}` | {r['mean_ungated_abs_ic']:.4f} | "
                     f"{r['mean_gated_abs_ic']:.4f} | {r['mean_gated_events']:.0f} | {r['n_targets']} |")
    if winner:
        lines += ["", f"**Winner (data-chosen): `{winner['candidate']}`** "
                       f"(mean |gated IC| {winner['mean_gated_abs_ic']:.4f}; "
                       f"E5 composite {'wins' if winner['candidate'] == 'e5_composite' else 'does NOT win'} the bake-off)."]
    lines += ["", f"- **{market} bake-off: best primary = "
                  f"{'`' + winner['candidate'] + '`' if winner else 'none available'}**"]
    md_path.write_text("\n".join(lines) + "\n")
    return {"market": market, "rows": rows, "available": available, "skipped": skipped,
            "winner": winner["candidate"] if winner else None, "report": str(md_path)}


# --------------------------------------------------------------------------- #
# Deliverable 5 — duration columns summary
# --------------------------------------------------------------------------- #
def duration_report(panel: pd.DataFrame, market: str = "USD", k_values=K_VALUES,
                    horizons=VERTICAL_HORIZONS, out_dir: Path = REPORTS_DIR) -> dict:
    """Per-(k,h) first-touch duration stats for barrier vs vertical outcomes."""
    rows: list[dict] = []
    for k in k_values:
        tag = _k_tag(k)
        for h in horizons:
            dur_col = f"tb_duration_{tag}_h{h}"
            touch_col = f"tb_touch_{tag}_h{h}"
            if dur_col not in panel.columns:
                continue
            dur = panel[dur_col].to_numpy(dtype="float64")
            touch = panel[touch_col].to_numpy(dtype="float64")
            fin = np.isfinite(dur)
            bars = dur[fin]
            rows.append({
                "target": dur_col, "k": k, "h": h, "n": int(fin.sum()),
                "mean_bars": float(bars.mean()) if bars.size else float("nan"),
                "median_bars": float(np.median(bars)) if bars.size else float("nan"),
                "barrier_mean_bars": float(dur[fin & ((touch == 1.0) | (touch == -1.0))].mean())
                if (fin & ((touch == 1.0) | (touch == -1.0))).any() else float("nan"),
                "vertical_mean_bars": float(dur[fin & (touch == 0.0)].mean())
                if (fin & (touch == 0.0)).any() else float("nan"),
            })
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = report_path(out_dir, "wi016_addendum_duration", market)
    lines = [
        f"# WI-016 addendum first-touch duration — {market}",
        "",
        f"- Generated (UTC): {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        "- `tb_duration_{k}_h{h}` is 1-based bars to first touch (barrier) or h (vertical).",
        "",
        "| duration column | events | mean bars | median bars | barrier mean | vertical mean |",
        "| :--- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for r in rows:
        lines.append(f"| `{r['target']}` | {r['n']:,} | {r['mean_bars']:.2f} | {r['median_bars']:.1f} | "
                     f"{r['barrier_mean_bars']:.2f} | {r['vertical_mean_bars']:.2f} |")
    lines += ["", f"- **{market} duration columns recorded for all (k, h).**"]
    md_path.write_text("\n".join(lines) + "\n")
    return {"market": market, "rows": rows, "report": str(md_path)}


# --------------------------------------------------------------------------- #
# Step-5 comparison
# --------------------------------------------------------------------------- #
def step5_verdict(market: str, out_dir: Path = REPORTS_DIR) -> dict:
    """Parse the frozen step-5 probe report's per-target clear/not-clear column."""
    p = report_path(out_dir, "wi016_probe", market)
    out: dict[str, bool] = {}
    if not p.exists():
        return out
    for line in p.read_text().splitlines():
        m = re.match(r"\|\s*`([^`]+)`\s*\|\s*(yes|no)\s*\|", line)
        if m:
            out[m.group(1)] = m.group(2) == "yes"
    return out


# --------------------------------------------------------------------------- #
# Panel + driver
# --------------------------------------------------------------------------- #
def _join_tc_rating(panel: pd.DataFrame, market: str) -> pd.DataFrame:
    """Attach the static per-symbol broker `tc_rating` (watchlist config)."""
    path = CONFIG_DIR / f"watchlist_300_{market.lower()}.csv"
    if not path.exists():
        panel["tc_rating"] = np.float32("nan")
        return panel
    cfg = pd.read_csv(path)
    if "tc_rating" not in cfg.columns:
        panel["tc_rating"] = np.float32("nan")
        return panel
    mapping = cfg.set_index("symbol")["tc_rating"]
    panel["tc_rating"] = panel["symbol"].map(mapping).astype("float32")
    return panel


def build_addendum_panel(market: str, min_date: str = MIN_DATE, allow_fixture: bool = False,
                         max_symbols: int | None = None) -> pd.DataFrame:
    """One market's addendum panel: WI-016 features + E5 + triple-barrier + tc_rating.

    Streams symbols one at a time (8 GB / no-swap host); legacy `y_*` targets are
    intentionally not computed (not needed by the addendum). Every calculated
    column is cast to float32 immediately; only the unified grid, E5, labels and
    identifiers are retained.
    """
    from src.feature_engine import wi016_feature_names

    features = wi016_feature_names()
    parts: list[pd.DataFrame] = []
    for i, (_sym, raw) in enumerate(iter_market_symbols(market, min_date=min_date, allow_fixture=allow_fixture)):
        if max_symbols is not None and i >= max_symbols:
            break
        g = raw.sort_values("date").reset_index(drop=True)
        feats = compute_features_wi016(g)
        e5 = factor_frame(g)
        tb = compute_triple_barrier(g)
        base = pd.DataFrame({"date": g["date"], "symbol": g["symbol"], "market": g["market"]})
        combined = pd.concat([base, feats[features], e5, tb], axis=1)
        combined = combined[combined["date"] >= pd.Timestamp(min_date)]
        parts.append(combined)
        del g, feats, e5, tb, combined
        if (i + 1) % 50 == 0:
            gc.collect()
    if not parts:
        raise RuntimeError(f"no addendum panel rows for market={market}")
    panel = pd.concat(parts, ignore_index=True)
    for c in panel.columns:
        if c not in ("date", "symbol", "market"):
            panel[c] = panel[c].astype("float32")
    return _join_tc_rating(panel, market)


def run_market(market: str, alpha: float = DEFAULT_FDR_ALPHA, allow_fixture: bool = False,
               max_symbols: int | None = None) -> dict:
    from src.feature_engine import wi016_feature_names

    panel = build_addendum_panel(market, allow_fixture=allow_fixture, max_symbols=max_symbols)
    features = wi016_feature_names() + E5_FACTORS
    gate = restricted_gate(panel, features, market=market, alpha=alpha)
    overlap = overlap_stats(panel, gate["tests"])
    bakeoff = primary_bakeoff(panel, market=market)
    duration = duration_report(panel, market=market)
    _append_overlap_section(gate["report"], market, overlap)
    return {"market": market, "gate": gate, "overlap": overlap,
            "bakeoff": bakeoff, "duration": duration}


def _append_overlap_section(report_path_str: str, market: str, overlap: list[dict]) -> None:
    """Append the overlap-aware (uniqueness-weighted) table to the probe report."""
    path = Path(report_path_str)
    lines = [
        "", "## Overlap-aware statistics (average-uniqueness weights, AFML ch. 4)", "",
        "Weighted vs unweighted per-date IC t-stat for the best restricted test per target;",
        "weight = mean average-uniqueness of that date's events.",
        "",
        "| target | feature | horizon | unweighted IC | unweighted t | weighted IC | weighted t | effective n | mean uniqueness |",
        "| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for r in overlap:
        lines.append(f"| `{r['target']}` | `{r['feature']}` | {r['horizon']} | "
                     f"{r['unweighted_ic']:+.4f} | {r['unweighted_t']:+.2f} | "
                     f"{r['weighted_ic']:+.4f} | {r['weighted_t']:+.2f} | "
                     f"{r['effective_n']:.1f} | {r['mean_uniqueness']:.3f} |")
    if not overlap:
        lines.append("| — | — | — | — | — | — | — | — | — |")
    lines += ["", f"- **{market} overlap check: weighted t-stats above; compare with the unweighted column.**"]
    with open(path, "a") as fh:
        fh.write("\n".join(lines) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="WI-016 addendum honest-edge probe")
    add_market_argument(parser)
    parser.add_argument("--alpha", type=float, default=DEFAULT_FDR_ALPHA)
    parser.add_argument("--allow-fixture", action="store_true")
    parser.add_argument("--max-symbols", type=int, default=None,
                        help="Debug bound on symbols per market (default: all).")
    args = parser.parse_args(argv)

    markets = cli_markets(args.market, prog="wi016.addendum")
    if markets is None:
        return 2
    for mkt in markets:
        res = run_market(mkt, alpha=args.alpha, allow_fixture=args.allow_fixture,
                         max_symbols=args.max_symbols)
        print(f"[wi016.addendum] {mkt}: probe -> {res['gate']['report']}")
        print(f"[wi016.addendum] {mkt}: bakeoff -> {res['bakeoff']['report']}")
        print(f"[wi016.addendum] {mkt}: duration -> {res['duration']['report']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
