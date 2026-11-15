"""WI-066 / WI-072 — cross-sectional top-k screener (D-027 §5, construction (b)).

Layer 2 (overlay/trading, D-027 §7): k / band / holding horizon are tuned on CALIB net edge only,
against the frozen fib baseline and the 50 bps single-leg round trip. EVAL is never read here (the
hashed pre-registration + one-shot EVAL belong to WI-071). First pass is LONG-ONLY (D-027 §11.5):
enter inside the top-k, hold until the name falls below top-(k·band). Second pass (D-027 §5) is the
symmetric **long/short** pass (`direction="long_short"`): long the top-k, short the bottom-k, exit
long below top-(k·band) and short above bottom-(k·band), 100 bps pair cycle.

WI-072 re-open (admin 2026-11-15): (a) `signal_values` scores **any union-library cell named as a
panel column** (the three named signals stay); (b) grids widened — `HORIZON_GRID` += 10/21/34,
`BAND_GRID` += 2.0/3.0 (a wider band lowers turnover; the USD card died on f≈0.51 cost); (c) the L/S
pass above. `load_candidates` folds in the rebuilt b_hold OOF coverage
(`data/models/l2_b_hold_scores/<MKT>.parquet`, WI-072) when that artifact exists.

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
B_HOLD_SCORES_ROOT = UNION_ROOT / "l2_b_hold_scores"     # WI-072 rebuilt b_hold OOF coverage
MARKETS: tuple[str, ...] = ("USD", "CAD")
SIGNALS: tuple[str, ...] = ("xsec_vol_rank_cont", "move_occur_x_dir_up", "b_hold")
EXTRA_SIGNALS: tuple[str, ...] = ("p_b_hold", "move_occur", "move_dir_up")   # raw union-library cells
DIRECTIONS: tuple[str, ...] = ("long", "long_short")     # D-027 §5 first / second pass
K_GRID: tuple[int, ...] = (4, 6, 8, 12)
BAND_GRID: tuple[float, ...] = (1.5, 2.0, 3.0)
HORIZON_GRID: tuple[int, ...] = (5, 10, 13, 21, 34)
TRADES_PER_WEEK_MAX = 4.0            # operator capacity (~200 trades/yr, D-027 §1)
SMOKE_DATES, SMOKE_NAMES, SMOKE_SEED, N_JOBS = 180, 30, 11, 2
__all__ = ["BASE_DIR", "B_HOLD_SCORES_ROOT", "REPORTS_ROOT", "REPORTS_SMOKE_ROOT", "POSITIONS_ROOT",
           "POSITIONS_SMOKE_ROOT", "SIGNALS", "EXTRA_SIGNALS", "DIRECTIONS", "MARKETS", "K_GRID",
           "BAND_GRID", "HORIZON_GRID", "signal_values", "signal_names", "rank_scores",
           "topk_positions", "topk_with_hysteresis", "turnover_fraction", "simulate", "build_entries",
           "tune_signal", "synthetic_fixture", "load_candidates", "write_calib_report", "main"]

def signal_values(panel, signal) -> np.ndarray:
    """Raw per-candidate score for a named signal (higher = more attractive; long-biased).

    WI-072: any union-library cell that exists as a panel column is scoreable by name."""
    if signal == "xsec_vol_rank_cont":
        return np.asarray(panel["xsec_vol_rank_cont"], dtype="float32")
    if signal == "move_occur_x_dir_up":     # move present × up direction (D-027 §5 lead caveat)
        return (np.asarray(panel["move_occur"], "float32")
                * np.asarray(panel["move_dir_up"], "float32")).astype("float32")
    if signal == "b_hold":                  # keep-score form 1 - P(hold) (repo convention)
        col = "p_b_hold" if "p_b_hold" in panel.columns else "b_hold"
        v = np.asarray(panel[col], dtype="float32")
        return (1.0 - v).astype("float32") if col == "p_b_hold" else v
    if signal in panel.columns:             # generic cell: the raw column is the score, as stored
        return np.asarray(panel[signal], dtype="float32")
    raise KeyError(f"unknown signal {signal!r}; expected {SIGNALS} or a union-library score column "
                   f"of the panel")

def signal_names(panel) -> tuple[str, ...]:
    """The named signals plus the widened union-library columns actually present in the panel."""
    extras = tuple(c for c in EXTRA_SIGNALS if c in panel.columns and c not in SIGNALS)
    return SIGNALS + extras

def rank_scores(panel, signal) -> np.ndarray:
    """Per-date cross-sectional percentile rank of `signal` (NaN-safe), float32 in [0, 1]."""
    frame = pd.DataFrame({"date": pd.to_datetime(pd.Series(np.asarray(panel["date"]))),
                          "v": signal_values(panel, signal)})
    return frame.groupby("date")["v"].rank(pct=True).to_numpy("float32")

def topk_positions(scores, k, band, *, dates=None, symbols=None, horizon=None, direction="long"):
    """`(held, side)` per row — long top-k with hysteresis; `long_short` adds the symmetric short leg.

    Long: enter inside the top-k, exit below top-(k·band), `side = +1`. L/S pass: also enter inside the
    bottom-k and exit above bottom-(k·band), `side = -1` (a name may flip legs on the same date).
    `horizon` caps the hold length; a forced exit may re-enter at the earliest on the next date.
    """
    if direction not in DIRECTIONS:
        raise ValueError(f"unknown direction {direction!r}; expected {DIRECTIONS}")
    v = np.asarray(scores["score"] if hasattr(scores, "columns") else scores, dtype="float64")
    if hasattr(scores, "columns"):
        dates = scores["date"].to_numpy() if "date" in scores.columns else dates
        symbols = scores["symbol"].to_numpy() if "symbol" in scores.columns else symbols
    n = v.size
    d = (np.zeros(n, "int64") if dates is None
         else pd.to_datetime(pd.Series(dates)).to_numpy().astype("int64"))
    ident = np.arange(n) if symbols is None else np.asarray(symbols).astype(str)
    exit_span = max(int(k), int(round(float(k) * float(band))))    # widened top/bottom band
    held, side = np.zeros(n, dtype=bool), np.zeros(n, dtype="int8")
    longs, shorts = {}, {}                      # symbol -> entry date index
    for t, stamp in enumerate(sorted(set(d.tolist()))):
        idx = np.flatnonzero(d == stamp)
        n_today = idx.size
        order = idx[np.argsort(-v[idx], kind="stable")]        # descending score, order[0] = best
        pos = {ident[i]: r for r, i in enumerate(order)}       # 0 = best score, n_today-1 = worst
        blocked = set()            # a name force-closed today may re-enter at the earliest tomorrow
        for book in (longs, shorts):
            for key in list(book):
                if horizon is not None and t - book[key] >= int(horizon):
                    del book[key]
                    blocked.add(key)
        for key in list(longs):
            r = pos.get(key)
            if r is not None and r >= exit_span:              # fell out of the widened top band
                del longs[key]
        for key in list(shorts):
            r = pos.get(key)
            if r is not None and r < n_today - exit_span:     # rose out of the widened bottom band
                del shorts[key]
        for i in order[: int(k)]:
            if ident[i] not in blocked:
                longs.setdefault(ident[i], t)
        if direction == "long_short":
            for i in order[-int(k):]:
                if ident[i] not in blocked:
                    shorts.setdefault(ident[i], t)
        for i in idx:
            if ident[i] in longs:
                held[i], side[i] = True, 1
            elif ident[i] in shorts:
                held[i], side[i] = True, -1
    return held, side

def topk_with_hysteresis(scores, k, band, *, dates=None, symbols=None, horizon=None) -> np.ndarray:
    """Long-only held mask (WI-066 first pass): enter inside top-k, exit below top-(k·band)."""
    return topk_positions(scores, k, band, dates=dates, symbols=symbols, horizon=horizon,
                          direction="long")[0]

def turnover_fraction(entries) -> float:
    """Mean per-date fraction of the held set that is newly entered (portfolio replacement, f)."""
    d = pd.to_datetime(pd.Series(np.asarray(entries["date"]))).to_numpy().astype("int64")
    sel, ent = entries["selected"].to_numpy(bool), entries["entry"].to_numpy(bool)
    fracs = [int(((d == s) & ent).sum()) / int(((d == s) & sel).sum())
             for s in sorted(set(d.tolist())) if ((d == s) & sel).any()]
    return float(np.mean(fracs)) if fracs else 0.0

def simulate(entries, costs=costs, direction="long") -> dict:
    """Per-trade net edge of the held set + the mandatory fold report.

    Long pass: mean(r|held) − mean(r|all) − 50 bps round trip − 50·f amortization. L/S pass (D-027 §5):
    the held set carries its own side, so the edge is mean(side·r|held) − 100 bps pair cycle − 100·f
    amortization (dollar-neutral, no baseline subtraction).
    """
    sel = entries["selected"].to_numpy(bool)
    r = entries["r"].to_numpy("float64")
    side = (entries["side"].to_numpy("float64") if "side" in entries.columns
            else np.where(sel, 1.0, 0.0))
    pos = side * r
    long_short = direction == "long_short"
    base = 0.0 if long_short else (float(np.nanmean(r)) if r.size else float("nan"))
    kept = float(np.nanmean(pos[sel])) if sel.any() else float("nan")
    turn = turnover_fraction(entries)
    cost_bps = (costs.pair_cost() + costs.turnover_cost(turn, pair_bps=costs.PAIR_BPS) if long_short
                else costs.single_leg_cost() + costs.turnover_cost(turn, pair_bps=costs.SINGLE_LEG_BPS))
    gross = costs.edge_bps(kept - base) if np.isfinite(kept) and np.isfinite(base) else float("nan")
    net = costs.net_edge_bps(gross, cost_bps) if np.isfinite(gross) else float("nan")
    folds, per_fold = entries["fold"].to_numpy(), {}
    for fo in sorted({int(x) for x in folds.tolist()}):
        m = folds == fo
        edge = (np.nanmean(pos[m & sel]) - (0.0 if long_short else np.nanmean(r[m]))
                if (m & sel).any() else float("nan"))
        per_fold[fo] = (costs.bps_to_frac(costs.edge_bps(edge) - cost_bps)
                        if np.isfinite(edge) else float("nan"))
    rep = foldrep.fold_report(per_fold)                     # mandatory; raises if the rows are absent
    return {"net_edge_bps": float(net), "gross_edge_bps": float(gross), "cost_bps": float(cost_bps),
            "turnover_f": float(turn), "direction": direction, "n_pairs": int((side[sel] == -1).sum()),
            "n_selected": int(sel.sum()),
            "n_entries": int(entries["entry"].sum()) if "entry" in entries.columns else int(sel.sum()),
            "per_fold_net_edge": per_fold, "fold_report": rep}

def build_entries(panel, signal, k, band, horizon, direction="long") -> pd.DataFrame:
    """Candidates for one (signal, k, band, horizon, direction): rank, held mask, side, entry flag.

    Rows without a finite OOF score for this signal are NOT candidates (no score ⇒ no decision;
    PM full-run defect fix, cycle 41 — an all-NaN-score date would otherwise let argsort select
    arbitrary unscored names)."""
    frame = panel.reset_index(drop=True)
    v = signal_values(frame, signal)
    frame = frame.loc[np.isfinite(np.asarray(v, dtype="float64"))].reset_index(drop=True)
    if frame.empty:
        raise ValueError(f"no finite scores for signal {signal!r}; nothing to rank")
    scores = rank_scores(frame, signal)
    held, side = topk_positions(scores, k, band, dates=frame["date"].to_numpy(),
                                symbols=frame["symbol"].to_numpy(), horizon=horizon,
                                direction=direction)
    out = pd.DataFrame({"date": pd.to_datetime(pd.Series(frame["date"].to_numpy())),
                        "symbol": frame["symbol"].astype(str).to_numpy(),
                        "fold": np.asarray(frame["fold"], "int64"),
                        "r": np.asarray(frame["r"], "float32"),
                        "score": scores.astype("float32"), "selected": held, "side": side.astype("int8")})
    out = out.sort_values(["symbol", "date"], kind="mergesort")
    prev = out.groupby("symbol")["selected"].shift(1, fill_value=False).to_numpy(bool)
    out["entry"] = out["selected"].to_numpy(bool) & ~prev    # first date a name is held
    return out.sort_values(["date", "symbol"], kind="mergesort").reset_index(drop=True)

def tune_signal(panel, signal, k_grid=K_GRID, band_grid=BAND_GRID, h_grid=HORIZON_GRID,
                direction="long") -> dict:
    """Pick (k, band, horizon) by max CALIB net edge, inside the ~4 trades/week capacity where possible."""
    weeks = max(len(pd.unique(pd.to_datetime(panel["date"]))) / 5.0, 1e-9)
    trials = []
    for k in k_grid:
        for band in band_grid:
            for h in h_grid:
                sim = simulate(build_entries(panel, signal, k, band, h, direction), direction=direction)
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
    """CALIB-only panel: union scores (WI-065) + the causal price panel + the WI-072 b_hold rebuild.

    Rows >= CALIB_END never load."""
    union = H.load_union()
    if not (union["market"].astype(str) == market).any():
        raise RuntimeError(f"no union cells for market={market}")
    path = Path(prepared_root) / f"{market}.parquet"
    if not path.exists():
        raise FileNotFoundError(f"prepared CALIB panel missing: {path} (full run is a PM gate)")
    frame = _merge_b_hold_scores(pd.read_parquet(path), market)
    return frame[pd.to_datetime(frame["date"]) < H.CALIB_END].reset_index(drop=True)

def _merge_b_hold_scores(frame, market, *, root=B_HOLD_SCORES_ROOT):
    """WI-072: the rebuilt b_hold OOF coverage replaces the prepared panel's all-NaN `p_b_hold`."""
    path = Path(root) / f"{market}.parquet"
    if not path.exists():
        return frame
    scores = pd.read_parquet(path, columns=["date", "symbol", "p_b_hold"])
    out = frame.merge(scores.rename(columns={"p_b_hold": "p_b_hold_oof"}), on=["date", "symbol"],
                      how="left")
    rebuilt = out["p_b_hold_oof"].to_numpy("float32")
    out["p_b_hold"] = (np.where(np.isfinite(rebuilt), rebuilt, out.get("p_b_hold", np.nan))
                       .astype("float32"))
    return out.drop(columns=["p_b_hold_oof"])

def write_calib_report(path, market, signal, best, *, smoke=False) -> Path:
    """CALIB card: fold distribution, turnover f, net edge and the stop/continue flag."""
    rep = best["fold_report"]
    share = "n/a" if not np.isfinite(float(rep["max_fold_share"])) else f"{rep['max_fold_share']:.4f}"
    lines = [f"# L2 xsec top-k screener — {signal} / {market} (D-027 §5 construction (b))", "",
             f"- Generated (UTC): {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
             f"- Scope: CALIB only (params tuned on CALIB net edge; EVAL unread — WI-071)"
             f"{'  (smoke / synthetic)' if smoke else ''}",
             f"- Pass: {best['direction']} (D-027 §5 {'first pass' if best['direction'] == 'long' else 'second pass, symmetric bottom-k leg'})",
             f"- Baseline: frozen fib rule; cost {costs.single_leg_cost():.0f} bps single-leg round trip, "
             f"{costs.pair_cost():.0f} bps L/S pair cycle",
             f"- Params: k={int(best['k'])}, band={float(best['band']):g}, "
             f"horizon={int(best['horizon'])} dates ({int(best['n_trials'])} CALIB trials)",
             f"- Capacity: {best['trades_per_week']:.2f} trades/week (cap {TRADES_PER_WEEK_MAX:g}), "
             f"{int(best['n_selected']):,} held rows ({int(best['n_pairs']):,} short rows); turnover f "
             f"{best['turnover_f']:.4f} -> cost {best['cost_bps']:.1f} bps",
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

def _run_screener(markets, panel_for, report_root, positions_root, *, smoke,
                  directions=DIRECTIONS) -> int:
    """Shared runner: INERT precheck → CALIB-only tuning per direction → card + fold report + positions."""
    for mk in markets:
        panel = panel_for(mk)
        names = panel.groupby("date")["symbol"].size().to_numpy()
        parts = []
        for signal in signal_names(panel):
            ok, reason = H.xsec_inert_precheck(rank_scores(panel, signal), names)
            if not ok:
                parts.append(f"{signal}:INERT")
                continue
            cells = []
            for direction in directions:
                best = tune_signal(panel, signal, direction=direction)
                tag = f"{signal}_{mk}_{direction}"
                write_calib_report(report_root / f"calib_{tag}.md", mk, signal, best, smoke=smoke)
                foldrep.write_fold_report(best["fold_report"], report_root / f"fold_{tag}.json")
                pos = positions_root / f"{tag}.parquet"
                pos.parent.mkdir(parents=True, exist_ok=True)
                build_entries(panel, signal, best["k"], best["band"], best["horizon"],
                              direction).to_parquet(pos, index=False)
                cells.append(f"{'L' if direction == 'long' else 'S'}:{best['net_edge_bps']:+.0f}"
                             f"{'stop' if best['stop']['stop'] else 'go'}")
            parts.append(f"{signal}[{'/'.join(cells)}]")
        print(f"[l2.xsec] {'smoke' if smoke else 'calib'} {mk}: " + " ".join(parts))
    return 0

def main(argv=None) -> int:
    """CLI: `--smoke` (synthetic, `*_smoke` roots) or the full CALIB run (PM gate)."""
    ap = argparse.ArgumentParser(description="WI-066/072 xsec top-k screener (D-027 §5 (b))")
    ap.add_argument("--smoke", action="store_true", help="synthetic run into the *_smoke roots")
    ap.add_argument("--market", default=None, help="limit to one market (default: both)")
    ap.add_argument("--direction", default=None, choices=list(DIRECTIONS),
                    help="limit to one pass (default: long then long_short)")
    args = ap.parse_args(argv)
    markets = (args.market,) if args.market else MARKETS
    directions = (args.direction,) if args.direction else DIRECTIONS
    if not args.smoke:
        return _run_screener(markets, load_candidates, REPORTS_ROOT, POSITIONS_ROOT, smoke=False,
                             directions=directions)
    rc = _run_screener(markets, synthetic_fixture, REPORTS_SMOKE_ROOT, POSITIONS_SMOKE_ROOT, smoke=True,
                       directions=directions)
    print(f"[l2.xsec] smoke artifacts -> {REPORTS_SMOKE_ROOT}, {POSITIONS_SMOKE_ROOT} | EXIT:0")
    return rc

if __name__ == "__main__":
    raise SystemExit(main())
