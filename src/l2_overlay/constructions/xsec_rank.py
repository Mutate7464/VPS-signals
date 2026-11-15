"""WI-066 — single-signal cross-sectional top-k screener (D-027 §5, construction (b)).

Layer 2 (overlay/trading, D-027 §7): k / band / holding horizon are tuned on CALIB net edge only,
against the frozen fib baseline and the 50 bps single-leg round trip. EVAL is never read here (the
hashed pre-registration + one-shot EVAL belong to WI-071). First pass is LONG-ONLY (D-027 §11.5):
enter inside the top-k, hold until the name falls below top-(k·band).

    uv run python -m src.l2_overlay.constructions.xsec_rank --smoke   # synthetic, *_smoke paths
    uv run python -m src.l2_overlay.constructions.xsec_rank           # full CALIB run = PM gate

Invariants: n_jobs=2, float32 immediately, symbol-sequential reads, no EVAL read.
"""
from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

import numpy as np
import pandas as pd

from src.l2_overlay import costs
from src.l2_overlay import fold_report as foldrep
from src.l2_overlay import harness as H

BASE_DIR = Path(__file__).resolve().parents[3]        # named input/output roots (never CLI args)
UNION_ROOT = BASE_DIR / "data" / "models"
PREPARED_ROOT = UNION_ROOT / "l2_prepared"
POSITIONS_ROOT, POSITIONS_SMOKE_ROOT = UNION_ROOT / "l2_xsec_rank", UNION_ROOT / "l2_xsec_rank_smoke"
REPORTS_ROOT, REPORTS_SMOKE_ROOT = (BASE_DIR / "reports" / "l2_xsec_rank",
                                    BASE_DIR / "reports" / "l2_xsec_rank_smoke")
MARKETS: tuple[str, ...] = ("USD", "CAD")
SIGNALS: tuple[str, ...] = ("xsec_vol_rank_cont", "move_occur_x_dir_up", "b_hold")
K_GRID: tuple[int, ...] = (4, 6, 8, 12)
BAND_GRID: tuple[float, ...] = (1.5, 2.0)
HORIZON_GRID: tuple[int, ...] = (5, 13, 21)
TRADES_PER_WEEK_MAX = 4.0            # operator capacity (~200 trades/yr, D-027 §1)
SMOKE_DATES, SMOKE_NAMES, SMOKE_SEED, N_JOBS = 180, 30, 11, 2
__all__ = ["BASE_DIR", "REPORTS_ROOT", "REPORTS_SMOKE_ROOT", "POSITIONS_ROOT", "POSITIONS_SMOKE_ROOT",
           "SIGNALS", "MARKETS", "K_GRID", "BAND_GRID", "HORIZON_GRID", "signal_values", "rank_scores",
           "topk_with_hysteresis", "turnover_fraction", "simulate", "build_entries", "tune_signal",
           "synthetic_fixture", "load_candidates", "write_calib_report", "main"]

def signal_values(panel, signal) -> np.ndarray:
    """Raw per-candidate score for a named signal (higher = more attractive; long-biased)."""
    if signal == "xsec_vol_rank_cont":
        return np.asarray(panel["xsec_vol_rank_cont"], dtype="float32")
    if signal == "move_occur_x_dir_up":     # move present × up direction (D-027 §5 lead caveat)
        return (np.asarray(panel["move_occur"], "float32")
                * np.asarray(panel["move_dir_up"], "float32")).astype("float32")
    if signal == "b_hold":                  # keep-score form 1 - P(hold) (repo convention)
        col = "p_b_hold" if "p_b_hold" in panel.columns else "b_hold"
        v = np.asarray(panel[col], dtype="float32")
        return (1.0 - v).astype("float32") if col == "p_b_hold" else v
    raise KeyError(f"unknown signal {signal!r}; expected one of {SIGNALS}")

def rank_scores(panel, signal) -> np.ndarray:
    """Per-date cross-sectional percentile rank of `signal` (NaN-safe), float32 in [0, 1]."""
    frame = pd.DataFrame({"date": pd.to_datetime(pd.Series(np.asarray(panel["date"]))),
                          "v": signal_values(panel, signal)})
    return frame.groupby("date")["v"].rank(pct=True).to_numpy("float32")

def topk_with_hysteresis(scores, k, band, *, dates=None, symbols=None, horizon=None) -> np.ndarray:
    """Long-only top-k hold: enter inside top-k, exit below top-(k·band); `horizon` caps the hold length."""
    v = np.asarray(scores["score"] if hasattr(scores, "columns") else scores, dtype="float64")
    if hasattr(scores, "columns"):
        dates = scores["date"].to_numpy() if "date" in scores.columns else dates
        symbols = scores["symbol"].to_numpy() if "symbol" in scores.columns else symbols
    n = v.size
    d = (np.zeros(n, "int64") if dates is None
         else pd.to_datetime(pd.Series(dates)).to_numpy().astype("int64"))
    ident = np.arange(n) if symbols is None else np.asarray(symbols).astype(str)
    exit_rank = max(int(k), int(round(float(k) * float(band))))
    out, held = np.zeros(n, dtype=bool), {}
    for t, stamp in enumerate(sorted(set(d.tolist()))):
        idx = np.flatnonzero(d == stamp)
        order = idx[np.argsort(-v[idx], kind="stable")]
        rank_of = {ident[i]: r for r, i in enumerate(order)}
        blocked = set()            # a name force-closed today may re-enter at the earliest tomorrow
        for key in list(held):
            if horizon is not None and t - held[key] >= int(horizon):
                del held[key]
                blocked.add(key)
            elif key in rank_of and rank_of[key] >= exit_rank:
                del held[key]
        for i in order[: int(k)]:
            if ident[i] not in blocked:
                held.setdefault(ident[i], t)
        for i in idx:
            if ident[i] in held:
                out[i] = True
    return out

def turnover_fraction(entries) -> float:
    """Mean per-date fraction of the held set that is newly entered (portfolio replacement, f)."""
    d = pd.to_datetime(pd.Series(np.asarray(entries["date"]))).to_numpy().astype("int64")
    sel, ent = entries["selected"].to_numpy(bool), entries["entry"].to_numpy(bool)
    fracs = [int(((d == s) & ent).sum()) / int(((d == s) & sel).sum())
             for s in sorted(set(d.tolist())) if ((d == s) & sel).any()]
    return float(np.mean(fracs)) if fracs else 0.0

def simulate(entries, costs=costs) -> dict:
    """Per-trade net edge of the held set: edge - 50 bps round trip - 50·f amortization; emits the fold report."""
    sel = entries["selected"].to_numpy(bool)
    r = entries["r"].to_numpy("float64")
    base = float(np.nanmean(r)) if r.size else float("nan")
    kept = float(np.nanmean(r[sel])) if sel.any() else float("nan")
    turn = turnover_fraction(entries)
    cost_bps = costs.single_leg_cost() + costs.turnover_cost(turn, pair_bps=costs.SINGLE_LEG_BPS)
    gross = costs.edge_bps(kept - base) if np.isfinite(kept) and np.isfinite(base) else float("nan")
    net = costs.net_edge_bps(gross, cost_bps) if np.isfinite(gross) else float("nan")
    folds, per_fold = entries["fold"].to_numpy(), {}
    for fo in sorted({int(x) for x in folds.tolist()}):
        m = folds == fo
        edge = np.nanmean(r[m & sel]) - np.nanmean(r[m]) if (m & sel).any() else float("nan")
        per_fold[fo] = (costs.bps_to_frac(costs.edge_bps(edge) - cost_bps)
                        if np.isfinite(edge) else float("nan"))
    rep = foldrep.fold_report(per_fold)                     # mandatory; raises if the rows are absent
    return {"net_edge_bps": float(net), "gross_edge_bps": float(gross), "cost_bps": float(cost_bps),
            "turnover_f": float(turn), "n_selected": int(sel.sum()),
            "n_entries": int(entries["entry"].sum()) if "entry" in entries.columns else int(sel.sum()),
            "per_fold_net_edge": per_fold, "fold_report": rep}

def build_entries(panel, signal, k, band, horizon) -> pd.DataFrame:
    """Candidates for one (signal, k, band, horizon): rank, held mask, entry flag — float32.

    Rows without a finite OOF score for this signal are NOT candidates (no score ⇒ no decision;
    PM full-run defect fix, cycle 41 — an all-NaN-score date would otherwise let argsort select
    arbitrary unscored names)."""
    frame = panel.reset_index(drop=True)
    v = signal_values(frame, signal)
    frame = frame.loc[np.isfinite(np.asarray(v, dtype="float64"))].reset_index(drop=True)
    if frame.empty:
        raise ValueError(f"no finite scores for signal {signal!r}; nothing to rank")
    scores = rank_scores(frame, signal)
    held = topk_with_hysteresis(scores, k, band, dates=frame["date"].to_numpy(),
                                symbols=frame["symbol"].to_numpy(), horizon=horizon)
    out = pd.DataFrame({"date": pd.to_datetime(pd.Series(frame["date"].to_numpy())),
                        "symbol": frame["symbol"].astype(str).to_numpy(),
                        "fold": np.asarray(frame["fold"], "int64"),
                        "r": np.asarray(frame["r"], "float32"),
                        "score": scores.astype("float32"), "selected": held})
    out = out.sort_values(["symbol", "date"], kind="mergesort")
    prev = out.groupby("symbol")["selected"].shift(1, fill_value=False).to_numpy(bool)
    out["entry"] = out["selected"].to_numpy(bool) & ~prev    # first date a name is held
    return out.sort_values(["date", "symbol"], kind="mergesort").reset_index(drop=True)

def tune_signal(panel, signal, k_grid=K_GRID, band_grid=BAND_GRID, h_grid=HORIZON_GRID) -> dict:
    """Pick (k, band, horizon) by max CALIB net edge, inside the ~4 trades/week capacity where possible."""
    weeks = max(len(pd.unique(pd.to_datetime(panel["date"]))) / 5.0, 1e-9)
    trials = []
    for k in k_grid:
        for band in band_grid:
            for h in h_grid:
                sim = simulate(build_entries(panel, signal, k, band, h))
                trials.append({"k": int(k), "band": float(band), "horizon": int(h),
                               "trades_per_week": sim["n_entries"] / weeks, **sim})
    inside = [t for t in trials if np.isfinite(t["net_edge_bps"])
              and t["trades_per_week"] <= TRADES_PER_WEEK_MAX]
    best = max(inside or trials, key=lambda t: (t["net_edge_bps"], -t["trades_per_week"]))
    best["stop"] = H.calib_stop(best["net_edge_bps"], best["fold_report"])
    best["n_trials"] = len(trials)
    return best

def synthetic_fixture(market="USD", n_dates=SMOKE_DATES, n_names=SMOKE_NAMES, seed=SMOKE_SEED):
    """Deterministic planted cross-section (no `data/` read): each signal tracks the latent that sets r."""
    rng = np.random.default_rng(seed)
    n = int(n_dates) * int(n_names)
    latent = rng.normal(0.0, 1.0, n).astype("float32")
    return pd.DataFrame({
        "date": np.repeat(pd.date_range("2021-01-04", periods=int(n_dates), freq="B").to_numpy(), int(n_names)),
        "symbol": np.tile(np.array([f"{market}{i:02d}" for i in range(int(n_names))]), int(n_dates)),
        "fold": np.repeat(np.arange(int(n_dates)) % 5, int(n_names)).astype("int64"),
        "r": (0.02 * latent + rng.normal(0.0, 0.008, n)).astype("float32"),
        "xsec_vol_rank_cont": (latent + rng.normal(0.0, 0.5, n)).astype("float32"),
        "move_occur": rng.random(n).astype("float32"),
        "move_dir_up": (latent + rng.normal(0.0, 0.5, n)).astype("float32"),
        "p_b_hold": (1.0 / (1.0 + np.exp(latent.astype("float64")))).astype("float32"),
    }).sort_values(["date", "symbol"], kind="mergesort").reset_index(drop=True)

def load_candidates(market: str, *, prepared_root=PREPARED_ROOT) -> pd.DataFrame:
    """CALIB-only panel: union scores (WI-065) + the causal price panel; rows >= CALIB_END never load."""
    union = H.load_union()
    if not (union["market"].astype(str) == market).any():
        raise RuntimeError(f"no union cells for market={market}")
    path = Path(prepared_root) / f"{market}.parquet"
    if not path.exists():
        raise FileNotFoundError(f"prepared CALIB panel missing: {path} (full run is a PM gate)")
    frame = pd.read_parquet(path)
    return frame[pd.to_datetime(frame["date"]) < H.CALIB_END].reset_index(drop=True)

def write_calib_report(path, market, signal, best, *, smoke=False) -> Path:
    """CALIB card: fold distribution, turnover f, net edge and the stop/continue flag."""
    rep = best["fold_report"]
    share = "n/a" if not np.isfinite(float(rep["max_fold_share"])) else f"{rep['max_fold_share']:.4f}"
    lines = [f"# L2 xsec top-k screener — {signal} / {market} (D-027 §5 construction (b))", "",
             f"- Generated (UTC): {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
             f"- Scope: CALIB only (params tuned on CALIB net edge; EVAL unread — WI-071)"
             f"{'  (smoke / synthetic)' if smoke else ''}",
             f"- Baseline: frozen fib rule; cost {costs.single_leg_cost():.0f} bps single-leg round trip",
             f"- Params: k={int(best['k'])}, band={float(best['band']):g}, "
             f"horizon={int(best['horizon'])} dates ({int(best['n_trials'])} CALIB trials)",
             f"- Capacity: {best['trades_per_week']:.2f} trades/week (cap {TRADES_PER_WEEK_MAX:g}), "
             f"{int(best['n_selected']):,} held rows; turnover f {best['turnover_f']:.4f} "
             f"-> cost {best['cost_bps']:.1f} bps",
             f"- Gross edge {best['gross_edge_bps']:+.1f} bps; net edge {best['net_edge_bps']:+.1f} bps "
             f"(materiality floor {H.MATERIALITY_FLOOR_BPS:.1f})",
             f"- Fold report: max-fold share {share} (ceiling {foldrep.FOLD_CEILING_SHARE:.0%}, "
             f"{'pass' if rep['fold_ceiling_ok'] else 'FAIL'}); "
             f"positive folds {rep['n_positive_folds']}/{rep['n_folds']}",
             f"- Stop flag: **{'STOP' if best['stop']['stop'] else 'CONTINUE'}**"
             + (" — " + "; ".join(best["stop"]["reasons"]) if best["stop"]["reasons"] else ""),
             "", "| fold | net edge (bps) |", "| ---: | ---: |"]
    lines += [f"| {f} | {1e4 * float(v):+.1f} |" for f, v in sorted(best["per_fold_net_edge"].items())]
    lines += ["", "Record-only: no shortlist, no deployment, no live trading."]
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")
    return path

def _run_screener(markets, panel_for, report_root, positions_root, *, smoke) -> int:
    """Shared runner: INERT precheck -> CALIB-only tuning -> card + fold report + positions."""
    for mk in markets:
        panel, parts = panel_for(mk), []
        names = panel.groupby("date")["symbol"].size().to_numpy()
        for signal in SIGNALS:
            ok, reason = H.xsec_inert_precheck(rank_scores(panel, signal), names)
            if not ok:
                print(f"[l2.xsec] {signal}/{mk}: INERT — {reason}")
                continue
            best = tune_signal(panel, signal)
            write_calib_report(report_root / f"calib_{signal}_{mk}.md", mk, signal, best, smoke=smoke)
            foldrep.write_fold_report(best["fold_report"], report_root / f"fold_{signal}_{mk}.json")
            pos = positions_root / f"{mk}_{signal}.parquet"
            pos.parent.mkdir(parents=True, exist_ok=True)
            build_entries(panel, signal, best["k"], best["band"],
                          best["horizon"]).to_parquet(pos, index=False)
            parts.append(f"{signal}:{best['net_edge_bps']:+.0f}bps/"
                         f"{'stop' if best['stop']['stop'] else 'go'}")
        print(f"[l2.xsec] {'smoke' if smoke else 'calib'} {mk}: " + " ".join(parts))
    return 0

def main(argv=None) -> int:
    """CLI: `--smoke` (synthetic, `*_smoke` roots) or the full CALIB run (PM gate)."""
    ap = argparse.ArgumentParser(description="WI-066 xsec top-k screener (D-027 §5 (b))")
    ap.add_argument("--smoke", action="store_true", help="synthetic run into the *_smoke roots")
    ap.add_argument("--market", default=None, help="limit to one market (default: both)")
    args = ap.parse_args(argv)
    markets = (args.market,) if args.market else MARKETS
    if not args.smoke:
        return _run_screener(markets, load_candidates, REPORTS_ROOT, POSITIONS_ROOT, smoke=False)
    rc = _run_screener(markets, synthetic_fixture, REPORTS_SMOKE_ROOT, POSITIONS_SMOKE_ROOT, smoke=True)
    print(f"[l2.xsec] smoke artifacts -> {REPORTS_SMOKE_ROOT}, {POSITIONS_SMOKE_ROOT} | EXIT:0")
    return rc

if __name__ == "__main__":
    raise SystemExit(main())
