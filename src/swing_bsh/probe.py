"""WI-032 step 2 — D-021 §5 probe: swing-state first-touch labels vs features.

For every ``(state, k, horizon)`` group the probe forms the implied-side outcome
(``BUY`` at ``at_bottom``, ``SELL`` at ``at_top``; ``HOLD`` → NaN) and computes the
within-date rank-IC of each feature against it, BH-FDR across the whole grid, a
five-seed label-permutation placebo on the FDR survivors, and a |Spearman ρ|>0.7
uniqueness prune (≥500 resolved events per group). No model is trained.

CLI::

    python -m src.swing_bsh.probe --market CAD --limit 20 --out /tmp/wi032_smoke
    python -m src.swing_bsh.probe --market ALL
"""

from __future__ import annotations

import argparse
import datetime as dt
import gc
from pathlib import Path

import numpy as np
import pandas as pd

from src.feature_engine import compute_features_wi016, iter_market_symbols, wi016_feature_names
from src.market_cli import add_market_argument, cli_markets
from src.swing_bsh.events import BARRIERS, BUY, K_VALUES, SELL, label_symbol
from src.wi016.probe import N_PLACEBO_SEEDS, benjamini_hochberg, placebo_ic, within_date_ic

BASE_DIR = Path(__file__).resolve().parents[2]
REPORTS_DIR = BASE_DIR / "reports"
DEFAULT_FDR_ALPHA = 0.05
MIN_EVENTS = 500
UNIQUENESS_RHO = 0.7
MAX_PLACEBO_TESTS = 100
STATES = ("at_bottom", "at_top")

__all__ = [
    "build_event_panel", "favorable_outcome", "probe_market", "prune_features",
    "run_market", "write_report",
]


def favorable_outcome(panel: pd.DataFrame) -> np.ndarray:
    """Binary implied-side outcome: 1 favourable, 0 adverse, NaN for HOLD/other."""
    y = panel["y"].to_numpy(dtype="float64")
    state = panel["state"].to_numpy()
    win = ((state == "at_bottom") & (y == BUY)) | ((state == "at_top") & (y == SELL))
    lose = ((state == "at_bottom") & (y == SELL)) | ((state == "at_top") & (y == BUY))
    out = np.full(y.shape, np.nan)
    out[win] = 1.0
    out[lose] = 0.0
    return out


def prune_features(panel: pd.DataFrame, features, threshold=UNIQUENESS_RHO, max_rows=50000):
    """Keep one representative per |Spearman ρ|>threshold cluster; return (kept, dropped)."""
    feats = [f for f in features if f in panel.columns]
    X = panel[feats]
    if len(X) > max_rows:
        X = X.sample(max_rows, random_state=0)
    rho = X.rank().corr().abs().to_numpy()
    kept_pos: list[int] = []
    dropped: dict[str, str] = {}
    for j, f in enumerate(feats):
        dup = next((p for p in kept_pos if rho[j, p] > threshold), None)
        if dup is None:
            kept_pos.append(j)
        else:
            dropped[f] = feats[dup]
    return [feats[p] for p in kept_pos], dropped


def build_event_panel(market, k_values=K_VALUES, barriers=BARRIERS, features=None,
                      min_date="2016-01-01", allow_fixture=False, max_symbols=None):
    """One market's event panel: labelled swing events joined to features (float32)."""
    feats = list(features) if features is not None else wi016_feature_names()
    parts: list[pd.DataFrame] = []
    for i, (symbol, raw) in enumerate(
        iter_market_symbols(market, min_date=min_date, allow_fixture=allow_fixture)
    ):
        if max_symbols is not None and i >= max_symbols:
            break
        g = raw.sort_values("date").reset_index(drop=True)
        feats_df = compute_features_wi016(g)
        keep = feats_df[[f for f in feats if f in feats_df.columns]].assign(date=g["date"].to_numpy())
        for k in k_values:
            lab = label_symbol(g, symbol, k, barriers=barriers)
            if lab.empty:
                continue
            m = lab.merge(keep, on="date", how="inner")
            m["k"] = float(k)
            parts.append(m)
        del g, feats_df, keep
        if (i + 1) % 50 == 0:
            gc.collect()
    if not parts:
        return pd.DataFrame()
    panel = pd.concat(parts, ignore_index=True)
    for c in panel.columns:
        if c not in ("date", "symbol", "state"):
            panel[c] = pd.to_numeric(panel[c], errors="coerce").astype("float32")
    return panel


def _subgroup(panel, state, k, h):
    mask = ((panel["state"].to_numpy() == state)
            & (panel["k"].to_numpy() == float(k))
            & (panel["horizon"].to_numpy() == float(h)))
    return panel.loc[mask]


def probe_market(panel, market, features, k_values=K_VALUES, barriers=BARRIERS,
                 alpha=DEFAULT_FDR_ALPHA, seeds=N_PLACEBO_SEEDS, min_events=MIN_EVENTS):
    """Full probe grid for one market's event panel (rank-IC, FDR, placebo)."""
    if panel.empty:
        return {"market": market, "outcome": "ABORT", "reason": "no events",
                "n_events": 0, "groups": [], "tests": [], "n_fdr": 0}
    groups, tests, pvals = [], [], []
    for state in STATES:
        for k in k_values:
            for h in barriers:
                sub = _subgroup(panel, state, k, h)
                tgt = favorable_outcome(sub)
                n_res = int(np.isfinite(tgt).sum())
                groups.append({"state": state, "k": float(k), "h": int(h),
                               "n_events": int(len(sub)), "n_resolved": n_res})
                if n_res < min_events:
                    continue
                dates = sub["date"].to_numpy()
                for f in features:
                    res = within_date_ic(sub[f].to_numpy(dtype="float64"), tgt, dates)
                    tests.append({"state": state, "k": float(k), "h": int(h), "feature": f, **res})
                    pvals.append(res["p"])
    reject, qvals = benjamini_hochberg(np.asarray(pvals, dtype="float64"), alpha=alpha)
    for r, q in zip(tests, qvals):
        r["q"] = float(q) if np.isfinite(q) else float("nan")
        r["fdr_significant"] = bool(np.isfinite(q) and q <= alpha)
    n_fdr = int(sum(r["fdr_significant"] for r in tests))
    survivors = sorted((r for r in tests if r["fdr_significant"]),
                       key=lambda r: abs(r["ic"]), reverse=True)[:MAX_PLACEBO_TESTS]
    keys = {(r["state"], r["k"], r["h"], r["feature"]) for r in survivors}
    for r in tests:
        if (r["state"], r["k"], r["h"], r["feature"]) in keys:
            sub = _subgroup(panel, r["state"], r["k"], r["h"])
            pl = placebo_ic(sub[r["feature"]].to_numpy(dtype="float64"),
                            favorable_outcome(sub), sub["date"].to_numpy(), seeds=seeds)
            r["placebo_clear"] = bool(pl["clear"])
        else:
            r["placebo_clear"] = False

    def _cleared(state, k, h):
        return any(r["fdr_significant"] and r["same_sign"] and r["placebo_clear"]
                   for r in tests if (r["state"], r["k"], r["h"]) == (state, float(k), int(h)))

    decisions = [{"state": g["state"], "k": g["k"], "h": g["h"], "cleared": _cleared(g["state"], g["k"], g["h"])}
                 for g in groups if g["n_resolved"] >= min_events]
    outcome = "CLEAR" if any(d["cleared"] for d in decisions) else ("NOT_CLEAR" if tests else "ABORT")
    return {"market": market, "outcome": outcome, "reason": "", "n_events": int(len(panel)),
            "groups": groups, "tests": tests, "n_fdr": n_fdr, "decisions": decisions}


def run_market(market, features=None, k_values=K_VALUES, barriers=BARRIERS,
               allow_fixture=False, max_symbols=None):
    """Build one market's event panel and run the probe."""
    feats = list(features) if features is not None else wi016_feature_names()
    panel = build_event_panel(market, k_values=k_values, barriers=barriers,
                              allow_fixture=allow_fixture, max_symbols=max_symbols)
    kept, dropped = prune_features(panel, feats) if not panel.empty else (feats, {})
    res = probe_market(panel, market, kept, k_values=k_values, barriers=barriers)
    res.update({"n_features": len(feats), "n_kept": len(kept), "n_dropped": len(dropped)})
    return res


def write_report(results, out_path: Path) -> tuple[Path, Path]:
    """Write the combined WI-032 probe markdown; return (md, csv)."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# WI-032 probe — swing-conditioned buy/sell/hold (D-021 §5)",
        "",
        f"- Generated (UTC): {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        f"- Universe: wi016 feature whitelist, |Spearman ρ|>{UNIQUENESS_RHO} prune, ≥{MIN_EVENTS} resolved events/group",
        f"- BH-FDR alpha {DEFAULT_FDR_ALPHA} · {N_PLACEBO_SEEDS}-seed label-permutation placebo · no model trained",
        "",
    ]
    rows = []
    for res in results:
        lines += [f"## {res['market']} — DECISION: **{res['outcome']}**", "",
                  f"- Events: {res['n_events']:,} · features {res.get('n_kept', 0)}/{res.get('n_features', 0)} kept "
                  f"· tests {len(res['tests'])} · FDR-significant {res['n_fdr']}"]
        if res["outcome"] == "ABORT":
            lines.append(f"- ABORT: {res['reason']}")
        lines += ["", "| state | k | h | events | resolved | cleared |", "| :--- | ---: | ---: | ---: | ---: | :---: |"]
        for g in res["groups"]:
            dec = next((d for d in res.get("decisions", [])
                        if (d["state"], d["k"], d["h"]) == (g["state"], g["k"], g["h"])), None)
            lines.append(f"| {g['state']} | {g['k']} | {g['h']} | {g['n_events']:,} | {g['n_resolved']:,} | "
                         f"{'yes' if dec and dec['cleared'] else 'no'} |")
        top = sorted([r for r in res["tests"] if r["fdr_significant"]], key=lambda r: abs(r["ic"]), reverse=True)[:15]
        lines += ["", "| state | k | h | feature | IC | q | same-sign | placebo |",
                  "| :--- | ---: | ---: | :--- | ---: | ---: | :---: | :---: |"]
        for r in top:
            lines.append(f"| {r['state']} | {r['k']} | {r['h']} | `{r['feature']}` | {r['ic']:+.4f} | "
                         f"{r['q']:.4f} | {'Y' if r['same_sign'] else 'N'} | {'Y' if r['placebo_clear'] else 'N'} |")
            rows.append({"market": res["market"], **{k: r[k] for k in
                        ("state", "k", "h", "feature", "ic", "t", "q", "fdr_significant", "same_sign", "placebo_clear")}})
        lines.append("")
    out_path.write_text("\n".join(lines) + "\n")
    csv_path = out_path.with_suffix(".csv")
    pd.DataFrame(rows).to_csv(csv_path, index=False)
    return out_path, csv_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="WI-032 swing-anchored buy/sell/hold probe")
    add_market_argument(parser)
    parser.add_argument("--limit", type=int, default=None, help="Max symbols per market (debug/smoke).")
    parser.add_argument("--out", default=None, help="Output directory (smoke runs use /tmp).")
    parser.add_argument("--alpha", type=float, default=DEFAULT_FDR_ALPHA)
    parser.add_argument("--allow-fixture", action="store_true")
    args = parser.parse_args(argv)

    markets = cli_markets(args.market, prog="swing_bsh.probe")
    if markets is None:
        return 2
    out_dir = Path(args.out) if args.out else REPORTS_DIR
    results = [run_market(m, allow_fixture=args.allow_fixture, max_symbols=args.limit) for m in markets]
    md, csv = write_report(results, out_dir / "wi032_probe.md")
    print(f"[wi032.probe] report -> {md}")
    for res in results:
        print(f"[wi032.probe] {res['market']}: {res['outcome']} · {res['n_events']} events · "
              f"{len(res['tests'])} tests · {res['n_fdr']} FDR-significant")
    print(f"[wi032.probe] csv -> {csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
