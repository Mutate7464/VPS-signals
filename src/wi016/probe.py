"""WI-016 Steps 4–5 — legacy-vs-triple-barrier comparison and the probe-first gate.

Step 4 (`legacy_comparison`) runs the legacy five-label generation and the new
triple-barrier labels **once on the same symbol/date rows and the same feature
panel**, so the label families are directly comparable, and writes a `wi016_`
report. The legacy label code stays in `src.targets` (rebuildable) but the new
primary pipeline does not invoke it after this comparison.

Step 5 (`probe_gate`) is the mandatory stop. For every triple-barrier outcome
``(k, h)`` it computes the within-date rank-IC of each unified feature and each E5
factor, applies Benjamini–Hochberg FDR across the whole target×feature grid, a
five-seed placebo, the WI-009b same-sign clause and a cost overlay with a
NO_TRADE default, then emits one unambiguous **clear / not-clear** decision per
market. No model is trained and no action is emitted here.

CLI::

    python -m src.wi016.probe --market USD
    python -m src.wi016.probe --market CAD --alpha 0.05
"""

from __future__ import annotations

import argparse
import datetime as dt
import gc
import math
import re
from pathlib import Path

import numpy as np
import pandas as pd

from src.factors.e5_baseline import E5_FACTORS, factor_frame
from src.feature_engine import compute_features_wi016, iter_market_symbols
from src.market_cli import add_market_argument, cli_markets, report_path
from src.targets import TARGET_COLUMNS, compute_targets
from src.wi016.triple_barrier import (
    K_VALUES,
    VERTICAL_HORIZONS,
    _k_tag,
    compute_triple_barrier,
)

BASE_DIR = Path(__file__).resolve().parents[2]
REPORTS_DIR = BASE_DIR / "reports"

DEFAULT_FDR_ALPHA = 0.05
N_PLACEBO_SEEDS = 5
DEFAULT_COST_BPS = 20.0
"""Round-trip trading-cost proxy (bps); the real number is WI-011's overlay."""

IC_TO_BPS = 1000.0
"""Documented proxy: gross edge bps per unit |IC| (screening-scale, not a P&L model)."""

PLACEBO_SEED0 = 1000

__all__ = [
    "DEFAULT_COST_BPS",
    "DEFAULT_FDR_ALPHA",
    "N_PLACEBO_SEEDS",
    "benjamini_hochberg",
    "cost_overlay",
    "decide_target",
    "legacy_comparison",
    "probe_gate",
    "within_date_ic",
]


# --------------------------------------------------------------------------- #
# Statistics
# --------------------------------------------------------------------------- #
def _pvalue(t: float, n_dates: int) -> float:
    """Two-sided normal-approximation p-value for a per-date-mean t-stat."""
    if not np.isfinite(t) or n_dates < 3:
        return float("nan")
    return float(math.erfc(abs(t) / math.sqrt(2.0)))


def _fast_ic_detail(feature, target, dates):
    """Vectorized within-date Spearman rank-IC; returns per-date IC series too.

    Fully vectorized over date groups so a 2.3M-row market panel is tractable on
    the 2 vCPU host. Returns `(mean_ic, t_stat, n_dates, ic_dates, ic_values)`.
    """
    df = pd.DataFrame(
        {"s": np.asarray(feature, dtype="float64"), "f": np.asarray(target, dtype="float64"),
         "d": np.asarray(dates)}
    ).replace([np.inf, -np.inf], np.nan).dropna()
    if df.empty:
        return float("nan"), float("nan"), 0, np.array([]), np.array([])
    grp = df["d"]
    if grp.nunique() < 2:
        return float("nan"), float("nan"), 0, np.array([]), np.array([])
    rs = df.groupby("d", sort=False)["s"].rank()
    rf = df.groupby("d", sort=False)["f"].rank()
    ds = rs - rs.groupby(grp).transform("mean")
    df_ = rf - rf.groupby(grp).transform("mean")
    num = (ds * df_).groupby(grp).sum()
    den = np.sqrt((ds * ds).groupby(grp).sum() * (df_ * df_).groupby(grp).sum())
    size = grp.groupby(grp).size()
    ic_date = (num / den.replace(0.0, np.nan))[(size >= 3)]
    ic_date = ic_date[ic_date.notna()]
    if ic_date.empty:
        return float("nan"), float("nan"), 0, np.array([]), np.array([])
    arr = ic_date.to_numpy(dtype="float64")
    mean_ic = float(arr.mean())
    if arr.size > 2 and arr.std(ddof=1) > 0.0:
        t = float(mean_ic / (arr.std(ddof=1) / np.sqrt(arr.size)))
    else:
        t = float("nan")
    return mean_ic, t, int(arr.size), ic_date.index.to_numpy(), arr


def _fast_within_date_rank_ic(feature, target, dates) -> tuple[float, float, int]:
    """`(mean_ic, t_stat, n_dates)` — see `_fast_ic_detail`."""
    ic, t, n, _d, _v = _fast_ic_detail(feature, target, dates)
    return ic, t, n


def _same_sign_from_series(ic_dates, ic_values, n_windows: int = 2) -> bool:
    """WI-009b clause from the per-date IC series (one pass, no recompute)."""
    if ic_values.size == 0:
        return False
    order = np.argsort(ic_dates, kind="mergesort")
    d = ic_dates[order]
    v = ic_values[order]
    uniq = np.unique(d)
    if uniq.size < n_windows:
        return False
    bounds = np.linspace(0, uniq.size, n_windows + 1).astype(int)
    ics = []
    for i in range(n_windows):
        lo, hi = uniq[bounds[i]], uniq[max(bounds[i + 1] - 1, bounds[i])]
        m = (d >= lo) & (d <= hi)
        ics.append(float(v[m].mean()) if m.any() else float("nan"))
    finite = [x for x in ics if np.isfinite(x)]
    return bool(len(finite) == n_windows and any(x != 0.0 for x in finite)
                and len({np.sign(x) for x in finite}) == 1)


def within_date_ic(feature, target, dates) -> dict:
    """Within-date rank-IC with t-stat, p-value and the WI-009b same-sign flag."""
    ic, t, n, ic_dates, ic_vals = _fast_ic_detail(feature, target, dates)
    return {
        "ic": float(ic),
        "t": float(t),
        "n_dates": int(n),
        "p": _pvalue(float(t), int(n)),
        "same_sign": bool(_same_sign_from_series(ic_dates, ic_vals)),
    }


def benjamini_hochberg(pvals, alpha: float = DEFAULT_FDR_ALPHA) -> tuple[np.ndarray, np.ndarray]:
    """Benjamini–Hochberg FDR control.

    Returns `(reject, qvalues)` aligned to `pvals`. NaN p-values never reject and
    get q = NaN. Implemented directly so the step can be unit-tested without a
    statsmodels dependency in the gate path.
    """
    p = np.asarray(pvals, dtype="float64")
    reject = np.zeros(p.shape, dtype=bool)
    q = np.full(p.shape, np.nan)
    finite = np.isfinite(p)
    m = int(finite.sum())
    if m == 0:
        return reject, q
    idx = np.where(finite)[0]
    order = idx[np.argsort(p[idx], kind="mergesort")]
    ranked = p[order]
    # q_i = min_{j>=i} (m / j) * p_(j)
    qvals = ranked * m / np.arange(1, m + 1)
    qvals = np.minimum.accumulate(qvals[::-1])[::-1]
    qvals = np.clip(qvals, 0.0, 1.0)
    q[order] = qvals
    reject[order] = qvals <= alpha
    return reject, q


def placebo_ic(feature, target, dates, seeds: int = N_PLACEBO_SEEDS, seed0: int = PLACEBO_SEED0) -> dict:
    """Five-seed label-permutation null for one feature's within-date IC."""
    f = np.asarray(feature, dtype="float64")
    t = np.asarray(target, dtype="float64")
    d = np.asarray(dates)
    observed, _, _ = _fast_within_date_rank_ic(f, t, d)
    null = []
    for s in range(seeds):
        rng = np.random.default_rng(seed0 + s)
        null.append(_fast_within_date_rank_ic(f, rng.permutation(t), d)[0])
    null_arr = np.asarray([x for x in null if np.isfinite(x)], dtype="float64")
    max_abs = float(np.max(np.abs(null_arr))) if null_arr.size else float("nan")
    return {
        "observed_ic": float(observed),
        "null_abs_max": max_abs,
        "null_seeds": [float(x) for x in null],
        "clear": bool(np.isfinite(observed) and np.isfinite(max_abs) and abs(observed) > max_abs),
    }


def cost_overlay(ic: float, cost_bps: float = DEFAULT_COST_BPS) -> dict:
    """Screening cost overlay with a NO_TRADE default.

    The gross edge for a screen with |IC| is proxied as ``|IC| * IC_TO_BPS`` bps
    (documented screening scale — the WI-011 overlay owns the real P&L model).
    A signal is tradeable only when the net edge after `cost_bps` is positive;
    otherwise the gate returns NO_TRADE.
    """
    gross = abs(ic) * IC_TO_BPS if np.isfinite(ic) else float("nan")
    net = gross - cost_bps if np.isfinite(gross) else float("nan")
    tradeable = bool(np.isfinite(net) and net > 0.0)
    return {"gross_bps": gross, "cost_bps": float(cost_bps), "net_bps": net,
            "decision": "TRADE" if tradeable else "NO_TRADE", "tradeable": tradeable}


# --------------------------------------------------------------------------- #
# Step 4 — legacy vs triple-barrier comparison (same rows, same features)
# --------------------------------------------------------------------------- #
def _best_and_mean_ic(panel: pd.DataFrame, features: list[str], target_col: str) -> dict:
    dates = panel["date"].to_numpy()
    tgt = panel[target_col].to_numpy(dtype="float64")
    best_feat, best_ic = None, float("nan")
    ics = []
    for f in features:
        ic, _t, _n = _fast_within_date_rank_ic(panel[f].to_numpy(dtype="float64"), tgt, dates)
        if np.isfinite(ic):
            ics.append(abs(ic))
            if not np.isfinite(best_ic) or abs(ic) > best_ic:
                best_ic, best_feat = abs(ic), f
    return {
        "target": target_col,
        "n_rows": int(len(panel)),
        "n_dates": int(panel["date"].nunique()),
        "best_feature": best_feat,
        "best_abs_ic": best_ic,
        "mean_abs_ic": float(np.mean(ics)) if ics else float("nan"),
        "n_features": len(ics),
    }


def legacy_comparison(
    panel: pd.DataFrame,
    feature_cols: list[str],
    market: str = "USD",
    legacy_cols: tuple[str, ...] = tuple(TARGET_COLUMNS),
    k_values=K_VALUES,
    horizons=VERTICAL_HORIZONS,
    out_dir: Path = REPORTS_DIR,
) -> dict:
    """Compare the legacy five labels and the triple-barrier labels on one panel.

    `panel` must carry the identical `[date, symbol]` rows and feature panel for
    both label families (legacy `y_*` columns computed by `src.targets`, triple
    barrier by `src.wi016.triple_barrier`). Writes a `wi016_` comparison report.
    """
    rows = [_best_and_mean_ic(panel, feature_cols, c) for c in legacy_cols if c in panel.columns]
    tb_rows = []
    for k in k_values:
        for h in horizons:
            col = f"tb_label_{_k_tag(k)}_h{h}"
            if col in panel.columns:
                r = _best_and_mean_ic(panel, feature_cols, col)
                r["k"] = k
                r["h"] = h
                tb_rows.append(r)

    legacy_mean = float(np.nanmean([r["mean_abs_ic"] for r in rows])) if rows else float("nan")
    tb_mean = float(np.nanmean([r["mean_abs_ic"] for r in tb_rows])) if tb_rows else float("nan")

    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = report_path(out_dir, "wi016_legacy_comparison", market)
    lines = [
        f"# WI-016 legacy vs triple-barrier label comparison — {market}",
        "",
        f"- Generated (UTC): {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        f"- Panel: {len(panel):,} rows · {panel['date'].nunique()} dates · {panel['symbol'].nunique()} symbols",
        f"- Identical rows/features for both label families; {len(feature_cols)} features.",
        "",
        "## Legacy five labels",
        "",
        "| label | rows | dates | best feature | best |IC| | mean |IC| |",
        "| :--- | ---: | ---: | :--- | ---: | ---: |",
    ]
    for r in rows:
        lines.append(f"| `{r['target']}` | {r['n_rows']} | {r['n_dates']} | `{r['best_feature']}` | "
                     f"{r['best_abs_ic']:.4f} | {r['mean_abs_ic']:.4f} |")
    lines += ["", "## Triple-barrier fib-ladder labels", "",
              "| label | rows | dates | best feature | best |IC| | mean |IC| |",
              "| :--- | ---: | ---: | :--- | ---: | ---: |"]
    for r in tb_rows:
        lines.append(f"| `{r['target']}` | {r['n_rows']} | {r['n_dates']} | `{r['best_feature']}` | "
                     f"{r['best_abs_ic']:.4f} | {r['mean_abs_ic']:.4f} |")
    lines += ["", f"- Legacy mean |IC| (all labels): {legacy_mean:.4f}",
              f"- Triple-barrier mean |IC| (all k,h): {tb_mean:.4f}",
              f"- Verdict: {'triple-barrier >= legacy' if tb_mean >= legacy_mean else 'legacy > triple-barrier'} "
              "(screening-scale, not a model claim)."]
    md_path.write_text("\n".join(lines) + "\n")

    return {
        "market": market,
        "n_rows": int(len(panel)),
        "n_dates": int(panel["date"].nunique()),
        "n_features": len(feature_cols),
        "legacy": rows,
        "triple_barrier": tb_rows,
        "legacy_mean_abs_ic": legacy_mean,
        "triple_barrier_mean_abs_ic": tb_mean,
        "report": str(md_path),
    }


# --------------------------------------------------------------------------- #
# Step 5 — probe-first gate
# --------------------------------------------------------------------------- #
def _all_tests(panel, features, target_cols) -> tuple[list[dict], np.ndarray]:
    dates = panel["date"].to_numpy()
    tests: list[dict] = []
    pvals: list[float] = []
    for tcol in target_cols:
        tgt = panel[tcol].to_numpy(dtype="float64")
        for f in features:
            res = within_date_ic(panel[f].to_numpy(dtype="float64"), tgt, dates)
            tests.append({"target": tcol, "feature": f, **res})
            pvals.append(res["p"])
    return tests, np.asarray(pvals, dtype="float64")


def decide_target(target: str, rows: list[dict], alpha: float = DEFAULT_FDR_ALPHA) -> dict:
    """One target's gate verdict: any (feature) clearing every clause.

    A test clears when it is FDR-significant, same-sign, placebo-clear and
    cost-tradeable. The cost overlay defaults to NO_TRADE, so a target with no
    cost-positive feature is *not* cleared.
    """
    passing = [
        r for r in rows
        if r.get("target") == target
        and np.isfinite(r.get("q", np.nan)) and r["q"] <= alpha
        and r.get("same_sign")
        and r.get("placebo_clear")
        and r.get("tradeable")
    ]
    best = None
    if passing:
        best = max(passing, key=lambda r: abs(r["ic"]))
    return {
        "target": target,
        "cleared": bool(passing),
        "n_passing_features": len(passing),
        "best_feature": best["feature"] if best else None,
        "best_ic": best["ic"] if best else None,
    }


def _horizon_from_target(target_col: str) -> int:
    """Label horizon from a `tb_label_<k>_h<h>` column name (default 20)."""
    m = re.search(r"_h(\d+)$", str(target_col))
    return int(m.group(1)) if m else 20


def _fold_counts(panel: pd.DataFrame, target_cols: list[str]) -> list[dict]:
    """Events per purged walk-forward fold for each target (`embargo=max(20,h)`)."""
    from src.wi011.stats import fold_blocks

    dates = np.sort(pd.unique(panel["date"].to_numpy()))
    d = panel["date"].to_numpy()
    out = []
    for t in target_cols:
        h = _horizon_from_target(t)
        folds = fold_blocks(dates, horizon=h)
        defined = np.isfinite(panel[t].to_numpy(dtype="float64"))
        counts = []
        for f in folds:
            lo, hi = np.datetime64(f["val_min"]), np.datetime64(f["val_max"])
            counts.append({"fold": f["fold"], "embargo_td": f["embargo_td"],
                           "events": int((defined & (d >= lo) & (d <= hi)).sum())})
        out.append({"target": t, "horizon": h, "folds": counts})
    return out


def probe_gate(
    panel: pd.DataFrame,
    feature_cols: list[str],
    market: str = "USD",
    k_values=K_VALUES,
    horizons=VERTICAL_HORIZONS,
    alpha: float = DEFAULT_FDR_ALPHA,
    cost_bps: float = DEFAULT_COST_BPS,
    placebo_seeds: int = N_PLACEBO_SEEDS,
    max_placebo_tests: int = 100,
    out_dir: Path = REPORTS_DIR,
) -> dict:
    """Full per-market probe gate. Returns the decision + evidence; writes a report.

    Targets are the triple-barrier outcomes (`tb_label_{k}_h`). Features are the
    unified grid plus E5, evaluated with the within-date rank-IC. The five-seed
    placebo is applied to the top `max_placebo_tests` FDR survivors by |IC|
    (bounded for the 2 vCPU host; documented in the report).
    """
    target_cols = [
        f"tb_label_{_k_tag(k)}_h{h}"
        for k in k_values for h in horizons
        if f"tb_label_{_k_tag(k)}_h{h}" in panel.columns
    ]
    tests, pvals = _all_tests(panel, feature_cols, target_cols)
    reject, qvals = benjamini_hochberg(pvals, alpha=alpha)
    for r, q in zip(tests, qvals):
        r["q"] = float(q) if np.isfinite(q) else float("nan")
        r["fdr_significant"] = bool(np.isfinite(q) and q <= alpha)

    # Placebo + cost only for FDR survivors (bounds runtime on real panels).
    dates = panel["date"].to_numpy()
    survivors = sorted(
        (r for r in tests if r["fdr_significant"]), key=lambda r: abs(r["ic"]), reverse=True
    )[:max_placebo_tests]
    placebo_keys = {(r["target"], r["feature"]) for r in survivors}
    for r in tests:
        if (r["target"], r["feature"]) in placebo_keys:
            pl = placebo_ic(
                panel[r["feature"]].to_numpy(dtype="float64"),
                panel[r["target"]].to_numpy(dtype="float64"), dates, seeds=placebo_seeds,
            )
            r["placebo_clear"] = pl["clear"]
            r["placebo_null_abs_max"] = pl["null_abs_max"]
        else:
            r["placebo_clear"] = False
            r["placebo_null_abs_max"] = float("nan")
        r["tradeable"] = cost_overlay(r["ic"], cost_bps)["tradeable"]

    decisions = [decide_target(t, tests, alpha=alpha) for t in target_cols]
    cleared = [d for d in decisions if d["cleared"]]
    outcome = "CLEAR" if cleared else "NOT_CLEAR"

    # Label class balance per target (density evidence).
    density = []
    for t in target_cols:
        v = panel[t].to_numpy(dtype="float64")
        finite = v[np.isfinite(v)]
        density.append({
            "target": t,
            "n_events": int(finite.size),
            "plus": int((finite == 1).sum()),
            "minus": int((finite == -1).sum()),
            "neutral": int((finite == 0).sum()),
        })

    out_dir.mkdir(parents=True, exist_ok=True)
    fold_counts = _fold_counts(panel, target_cols)
    md_path = report_path(out_dir, "wi016_probe", market)
    _write_probe_report(md_path, market, len(panel), feature_cols, target_cols,
                        tests, decisions, density, fold_counts, outcome, alpha, cost_bps)

    return {
        "market": market,
        "outcome": outcome,
        "alpha": alpha,
        "cost_bps": cost_bps,
        "n_tests": len(tests),
        "n_fdr_significant": int(sum(r["fdr_significant"] for r in tests)),
        "decisions": decisions,
        "cleared_targets": [d["target"] for d in cleared],
        "density": density,
        "fold_counts": fold_counts,
        "tests": tests,
        "report": str(md_path),
    }


def _write_probe_report(md_path, market, n_rows, features, targets, tests, decisions, density,
                        fold_counts, outcome, alpha, cost_bps):
    lines = [
        f"# WI-016 probe-first gate — {market}",
        "",
        f"- Generated (UTC): {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        f"- Panel rows: {n_rows:,} · features: {len(features)} · targets: {len(targets)}",
        f"- Tests: {len(tests)} · BH-FDR alpha {alpha} · cost overlay {cost_bps} bps (NO_TRADE default)",
        "",
        f"## DECISION: **{outcome}**",
        "",
        "A target clears only when it has a feature that is FDR-significant, same-sign,",
        "placebo-clear and cost-tradeable.",
        "",
        "| target | cleared | passing features | best feature | best IC |",
        "| :--- | :---: | ---: | :--- | ---: |",
    ]
    for d in decisions:
        lines.append(f"| `{d['target']}` | {'yes' if d['cleared'] else 'no'} | {d['n_passing_features']} | "
                     f"`{d['best_feature']}` | {d['best_ic']:+.4f} |" if d["best_feature"] else
                     f"| `{d['target']}` | no | 0 | - | - |")
    lines += ["", "## Label class balance / density", "",
              "| target | events | +1 | -1 | 0 |", "| :--- | ---: | ---: | ---: | ---: |"]
    for row in density:
        lines.append(f"| `{row['target']}` | {row['n_events']} | {row['plus']} | {row['minus']} | {row['neutral']} |")
    lines += ["", "## Events per purged fold (`embargo_td = max(20, horizon)`)", "",
              "| target | h | folds (events) |", "| :--- | ---: | :--- |"]
    for row in fold_counts:
        folds = ", ".join(f"f{f['fold']}={f['events']}" for f in row["folds"]) or "n/a"
        lines.append(f"| `{row['target']}` | {row['horizon']} | {folds} |")
    lines += ["", "## Top FDR-significant tests", "",
              "| target | feature | IC | t | q | same-sign | placebo-clear | tradeable |",
              "| :--- | :--- | ---: | ---: | ---: | :---: | :---: | :---: |"]
    sig = sorted([r for r in tests if r["fdr_significant"]], key=lambda r: abs(r["ic"]), reverse=True)[:25]
    for r in sig:
        lines.append(f"| `{r['target']}` | `{r['feature']}` | {r['ic']:+.4f} | {r['t']:+.2f} | {r['q']:.4f} | "
                     f"{'Y' if r['same_sign'] else 'N'} | {'Y' if r['placebo_clear'] else 'N'} | "
                     f"{'Y' if r['tradeable'] else 'N'} |")
    if not sig:
        lines.append("| — | — | — | — | — | — | — | — |")
    md_path.write_text("\n".join(lines) + "\n")


# --------------------------------------------------------------------------- #
# Real-data panel + driver
# --------------------------------------------------------------------------- #
def build_probe_panel(market: str, min_date: str = "2016-01-01", allow_fixture: bool = False) -> pd.DataFrame:
    """One market's panel: WI-016 features + E5 + legacy labels + triple-barrier labels.

    Streams symbols one at a time (8 GB / no-swap host) and retains only the
    unified grid, E5 factors, label columns and identifiers, cast to float32.
    """
    from src.feature_engine import wi016_feature_names

    features = wi016_feature_names()
    parts = []
    for i, (_sym, raw) in enumerate(iter_market_symbols(market, min_date=min_date, allow_fixture=allow_fixture)):
        g = raw.sort_values("date").reset_index(drop=True)
        feats = compute_features_wi016(g)
        e5 = factor_frame(g)
        legacy = compute_targets(g)
        tb = compute_triple_barrier(g)
        base = pd.DataFrame({"date": g["date"], "symbol": g["symbol"], "market": g["market"]})
        combined = pd.concat([base, feats[features], e5, legacy, tb], axis=1)
        combined = combined[combined["date"] >= pd.Timestamp(min_date)]
        parts.append(combined)
        del g, feats, e5, legacy, tb, combined
        if (i + 1) % 50 == 0:
            gc.collect()
    if not parts:
        raise RuntimeError(f"no panel rows for market={market}")
    panel = pd.concat(parts, ignore_index=True)
    for c in panel.columns:
        if c not in ("date", "symbol", "market"):
            panel[c] = panel[c].astype("float32")
    return panel


def run_market(market: str, alpha: float = DEFAULT_FDR_ALPHA, cost_bps: float = DEFAULT_COST_BPS,
               allow_fixture: bool = False) -> dict:
    from src.feature_engine import wi016_feature_names

    panel = build_probe_panel(market, allow_fixture=allow_fixture)
    features = wi016_feature_names() + E5_FACTORS
    legacy = legacy_comparison(panel, features, market=market)
    gate = probe_gate(panel, features, market=market, alpha=alpha, cost_bps=cost_bps)
    return {"legacy": legacy, "gate": gate}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="WI-016 legacy comparison + probe gate")
    add_market_argument(parser)
    parser.add_argument("--alpha", type=float, default=DEFAULT_FDR_ALPHA)
    parser.add_argument("--cost-bps", type=float, default=DEFAULT_COST_BPS)
    parser.add_argument("--allow-fixture", action="store_true")
    args = parser.parse_args(argv)

    markets = cli_markets(args.market, prog="wi016.probe")
    if markets is None:
        return 2
    for mkt in markets:
        res = run_market(mkt, alpha=args.alpha, cost_bps=args.cost_bps, allow_fixture=args.allow_fixture)
        print(f"[wi016.probe] {mkt}: legacy -> {res['legacy']['report']}")
        print(f"[wi016.probe] {mkt}: gate DECISION = {res['gate']['outcome']} -> {res['gate']['report']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
