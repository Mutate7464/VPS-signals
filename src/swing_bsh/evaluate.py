"""WI-033 step 2 — ADOPT_LOOSE_4OF5 gate for the swing-conditioned 3-class model.

The gate compares the **model-filtered** at-bottom swing events against the
**frozen fib-rule baseline** (WI-028 entry + WI-030 exit ``t15_s10_d39_close``)
fold by fold: the frozen exit prices every event, so the model can only earn its
keep by *selecting* the events the frozen rule would take anyway. A fold is a
"win" when the model-selected events' mean return beats the all-events baseline;
the verdict is **ADOPT** when the model wins >= 4/5 folds, the pooled edge is
positive and the CB-05 label-permutation placebo clears z >= 2 (else REJECT /
INCONCLUSIVE). The canonical gate geometry is ``k=1.5, h=21`` at-bottom rows.

A model pickle and a WI-014-compatible shortlist are written **only** on ADOPT
(no auto-execution; the shortlist sits behind the human gate).

CLI::

    python -m src.swing_bsh.evaluate --market CAD --limit 20 --out /tmp/wi033_smoke
    python -m src.swing_bsh.evaluate --market ALL
"""

from __future__ import annotations

import argparse
import datetime as dt
import time
from pathlib import Path

import numpy as np
import pandas as pd

from src.swing_bsh import train
from src.swing_bsh.events import BUY

BASE_DIR = Path(__file__).resolve().parents[2]
REPORTS_DIR = BASE_DIR / "reports"

N_PLACEBO_SEEDS = 5
PLACEBO_SEED0 = 1000
PLACEBO_Z_MIN = 2.0
FOLD_THRESHOLD = 4
COST_BPS = 25.0
SELECT_PROB = 0.5
"""The model takes an at-bottom event when its calibrated P(BUY) clears this floor."""

SHORTLIST_COLUMNS = (
    "rank", "symbol", "market", "scoring_date", "state", "k", "horizon",
    "p_buy", "p_hold", "p_sell", "entry_close", "atr", "barrier_upper",
    "barrier_lower", "time_stop_bars", "frozen_exit", "decision", "size",
)

__all__ = [
    "FOLD_THRESHOLD", "N_PLACEBO_SEEDS", "SHORTLIST_COLUMNS", "build_shortlist",
    "fold_gate", "gate_frame", "placebo_z", "selection_edge", "verdict",
    "write_summary",
]


# --------------------------------------------------------------------------- #
# Gate statistics
# --------------------------------------------------------------------------- #
def gate_frame(oof: pd.DataFrame, k: float = train.GATE_K, h: int = train.GATE_H) -> pd.DataFrame:
    """Canonical at-bottom gate rows (k, h) with the model's OOF selection."""
    mask = (
        (oof["state"].to_numpy() == "at_bottom")
        & (oof["k"].to_numpy(dtype="float64") == float(k))
        & (oof["horizon"].to_numpy(dtype="float64") == float(h))
        & (oof["fold"].to_numpy() >= 0)
        & np.isfinite(oof["r_frozen"].to_numpy(dtype="float64"))
    )
    return pd.DataFrame({
        "pos": np.flatnonzero(mask),
        "symbol": oof["symbol"].to_numpy()[mask],
        "date": oof["date"].to_numpy()[mask],
        "fold": oof["fold"].to_numpy()[mask].astype(int),
        "p_buy": oof["p_buy"].to_numpy(dtype="float64")[mask],
        "r_frozen": oof["r_frozen"].to_numpy(dtype="float64")[mask],
        "selected": ((oof["pred"].to_numpy()[mask] == BUY)
                     & (oof["p_buy"].to_numpy(dtype="float64")[mask] >= SELECT_PROB)),
    })


def selection_edge(selected, ret) -> float:
    """Mean return of the selected events minus the all-events baseline."""
    selected = np.asarray(selected, dtype=bool)
    ret = np.asarray(ret, dtype="float64")
    if ret.size == 0 or not selected.any():
        return float("nan")
    return float(ret[selected].mean() - ret.mean())


def _spearman(a, b) -> float:
    """Within-group Spearman rank-IC of two arrays (NaN-safe)."""
    a = np.asarray(a, dtype="float64")
    b = np.asarray(b, dtype="float64")
    ok = np.isfinite(a) & np.isfinite(b)
    if ok.sum() < 3:
        return float("nan")
    ra = pd.Series(a[ok]).rank().to_numpy()
    rb = pd.Series(b[ok]).rank().to_numpy()
    if ra.std() == 0.0 or rb.std() == 0.0:
        return float("nan")
    return float(np.corrcoef(ra, rb)[0, 1])


def fold_gate(g: pd.DataFrame) -> dict:
    """Per-fold model-vs-baseline expectancy table + pooled edge and rank-IC."""
    rows: list[dict] = []
    for fold, grp in g.groupby("fold", sort=True):
        base = grp["r_frozen"].to_numpy(dtype="float64")
        sel = grp.loc[grp["selected"], "r_frozen"].to_numpy(dtype="float64")
        b = float(base.mean()) if base.size else float("nan")
        m = float(sel.mean()) if sel.size else float("nan")
        edge = m - b if np.isfinite(m) and np.isfinite(b) else float("nan")
        rows.append({"fold": int(fold), "n_events": int(base.size), "n_selected": int(sel.size),
                     "baseline_mean": b, "model_mean": m, "edge": edge,
                     "ic": _spearman(grp["p_buy"], grp["r_frozen"]),
                     "win": bool(np.isfinite(edge) and edge > 0.0)})
    ret = g["r_frozen"].to_numpy(dtype="float64")
    selected = g["selected"].to_numpy(dtype=bool)
    pooled_model = float(ret[selected].mean()) if selected.any() else float("nan")
    pooled_base = float(ret.mean()) if ret.size else float("nan")
    edge = (pooled_model - pooled_base
            if np.isfinite(pooled_model) and np.isfinite(pooled_base) else float("nan"))
    return {
        "folds": rows, "n_folds_pos": int(sum(r["win"] for r in rows)),
        "n_events": int(ret.size), "n_selected": int(selected.sum()),
        "pooled_baseline": pooled_base, "pooled_model": pooled_model, "pooled_edge": edge,
        "pooled_ic": _spearman(g["p_buy"], g["r_frozen"]),
    }


def verdict(n_folds_pos: int, pooled_edge: float, placebo_z: float,
            threshold: int = FOLD_THRESHOLD, z_min: float = PLACEBO_Z_MIN) -> str:
    """ADOPT / REJECT / INCONCLUSIVE from the fold wins, pooled edge and placebo z."""
    if n_folds_pos < threshold or not np.isfinite(pooled_edge) or pooled_edge <= 0.0:
        return "REJECT"
    if not np.isfinite(placebo_z) or placebo_z < z_min:
        return "INCONCLUSIVE"
    return "ADOPT"


def placebo_z(X, y, dates, params, splitter, g: pd.DataFrame,
              n_seeds: int = N_PLACEBO_SEEDS, seed0: int = PLACEBO_SEED0) -> dict:
    """CB-05-style label-permutation placebo: null distribution of the selection edge."""
    ret = g["r_frozen"].to_numpy(dtype="float64")
    pos = g["pos"].to_numpy()
    observed = selection_edge(g["selected"].to_numpy(), ret)
    null: list[float] = []
    for s in range(n_seeds):
        y_perm = np.random.default_rng(seed0 + s).permutation(y)
        oof_p, _fid, _stats = train.run_cv(X, y_perm, dates, params, splitter)
        finite = np.isfinite(oof_p).all(axis=1)
        pred = np.where(finite, np.nanargmax(np.where(finite[:, None], oof_p, -np.inf), axis=1), -1)
        null.append(selection_edge((pred[pos] == BUY) & (oof_p[pos, 1] >= SELECT_PROB), ret))
    arr = np.asarray([v for v in null if np.isfinite(v)], dtype="float64")
    mean = float(arr.mean()) if arr.size else float("nan")
    sd = float(arr.std(ddof=1)) if arr.size > 1 else float("nan")
    z = float((observed - mean) / sd) if np.isfinite(sd) and sd > 0.0 else float("nan")
    return {"observed_edge": observed, "null_mean": mean, "null_sd": sd,
            "null_edges": [float(v) for v in null], "z": z, "n_seeds": int(arr.size)}


# --------------------------------------------------------------------------- #
# Shortlist (WI-014-compatible head; written only on ADOPT)
# --------------------------------------------------------------------------- #
def build_shortlist(oof: pd.DataFrame, market: str, frozen_exit: str = train.FROZEN_EXIT[0]) -> pd.DataFrame:
    """Latest-date at-bottom BUY rows in a WI-014-compatible shortlist schema."""
    rows = oof[(oof["state"] == "at_bottom") & (oof["pred"] == BUY)
               & (oof["p_buy"] >= SELECT_PROB)].copy()
    if rows.empty:
        return pd.DataFrame(columns=SHORTLIST_COLUMNS)
    date = rows["date"].max()
    rows = rows[rows["date"] == date].sort_values(["p_buy", "symbol"], ascending=[False, True])
    k = train.GATE_K
    entry = rows["close"].to_numpy(dtype="float64")
    atr = rows["atr"].to_numpy(dtype="float64")
    out = pd.DataFrame({
        "symbol": rows["symbol"].to_numpy(), "market": market,
        "scoring_date": str(pd.Timestamp(date).date()), "state": rows["state"].to_numpy(),
        "k": rows["k"].to_numpy(dtype="float32"), "horizon": rows["horizon"].to_numpy(dtype="int16"),
        "p_buy": rows["p_buy"].to_numpy(dtype="float32"),
        "p_hold": rows["p_hold"].to_numpy(dtype="float32"),
        "p_sell": rows["p_sell"].to_numpy(dtype="float32"),
        "entry_close": entry.astype("float32"), "atr": atr.astype("float32"),
        "barrier_upper": (entry + k * atr).astype("float32"),
        "barrier_lower": (entry - k * atr).astype("float32"),
        "time_stop_bars": np.int16(train.FROZEN_EXIT[3]), "frozen_exit": frozen_exit,
        "decision": "TRADE",
        "size": np.clip(2.0 * rows["p_buy"].to_numpy(dtype="float64") - 1.0, 0.0, 1.0).astype("float32"),
    })
    out.insert(0, "rank", np.arange(1, len(out) + 1, dtype="int32"))
    return out[list(SHORTLIST_COLUMNS)]


# --------------------------------------------------------------------------- #
# Report
# --------------------------------------------------------------------------- #
def _fmt(x, spec="{:.4f}") -> str:
    v = float(x)
    return "n/a" if not np.isfinite(v) else spec.format(v)


def write_summary(results: list[dict], path: Path) -> Path:
    """Write `reports/wi033_summary.md` — gate verdict + per-fold table per market."""
    lines = [
        "# WI-033 — swing-conditioned 3-class buy/sell/hold gate (ADOPT_LOOSE_4OF5)",
        "",
        f"- Generated (UTC): {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        f"- Model: `XGBClassifier(objective=\"multi:softprob\", tree_method=\"hist\", n_jobs=2)`; "
        f"per-fold OvR isotonic calibration, sigmoid fallback < {train.CB04_MIN_POSITIVES} positives (CB-04)",
        f"- CV: 5-fold `PurgedWalkForwardSplit(embargo_td=max(20, horizon))`; gate geometry "
        f"k={train.GATE_K}, h={train.GATE_H} (at-bottom rows)",
        f"- Baseline: frozen fib rules — WI-028 at-bottom entry + WI-030 exit `{train.FROZEN_EXIT[0]}` "
        f"({COST_BPS:.0f} bps cost); placebo: CB-05 {N_PLACEBO_SEEDS}-seed label permutation",
        f"- Model filter: take an at-bottom event when calibrated P(BUY) >= {SELECT_PROB}",
        f"- Gate: ADOPT iff model beats baseline in >= {FOLD_THRESHOLD}/5 folds AND pooled edge > 0 "
        f"AND placebo z >= {PLACEBO_Z_MIN}",
        "",
        "| market | events | selected | folds won | pooled baseline | pooled model | pooled edge | placebo z | verdict |",
        "| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :---: |",
    ]
    for r in results:
        gate, pl = r["gate"], r["placebo"]
        lines.append(
            f"| {r['market']} | {gate['n_events']:,} | {gate['n_selected']:,} | "
            f"{gate['n_folds_pos']}/5 | {_fmt(gate['pooled_baseline'])} | {_fmt(gate['pooled_model'])} | "
            f"{_fmt(gate['pooled_edge'])} | {_fmt(pl['z'], '{:+.2f}')} | **{r['verdict']}** |"
        )
    for r in results:
        lines += ["", f"## {r['market']} — VERDICT: **{r['verdict']}**", "",
                  f"- Events: {r['n_rows']:,} swing-event rows · {r['n_symbols']} symbols · "
                  f"{len(r['features'])} features ({r['n_features_pruned']}/{r['n_features_input']} kept)",
                  f"- Embargo: {r['embargo_td']} td · runtime {r['runtime_sec']}s · "
                  f"final calibration: {r.get('final_meta', {}) and r['final_meta']['calibration']}",
                  f"- Placebo: observed edge {_fmt(r['placebo']['observed_edge'])}, "
                  f"null mean {_fmt(r['placebo']['null_mean'])}, sd {_fmt(r['placebo']['null_sd'])}, "
                  f"z {_fmt(r['placebo']['z'], '{:+.2f}')} ({r['placebo']['n_seeds']} seeds)",
                  f"- Pooled rank-IC (P(BUY) vs frozen return): {_fmt(r['gate'].get('pooled_ic'))}",
                  "", "| fold | events | selected | baseline mean | model mean | edge | IC | win |",
                  "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | :---: |"]
        for f in r["gate"]["folds"]:
            lines.append(
                f"| {f['fold']} | {f['n_events']:,} | {f['n_selected']:,} | "
                f"{_fmt(f['baseline_mean'])} | {_fmt(f['model_mean'])} | {_fmt(f['edge'])} | "
                f"{_fmt(f.get('ic'))} | {'yes' if f['win'] else 'no'} |"
            )
        if r.get("shap_importance"):
            top = list(r["shap_importance"].items())[:8]
            lines += ["", "Top TreeSHAP drivers (mean |contrib| share, 20k-row sample): "
                      + ", ".join(f"`{k}` {v:.3f}" for k, v in top)]
        if r["verdict"] == "ADOPT":
            lines += ["", f"- Model pickle: `models/swing_bsh/{r['market']}.pkl` · "
                      f"shortlist: `reports/wi033_shortlist_{r['market']}.parquet` (human gate)"]
        else:
            lines += ["", "- No model pickle written (gate not ADOPT; DoD §3)."]
    lines += ["", "## Notes / deviations", "",
              "- Gate geometry restricted to the primary at-bottom k=1.5/h=21 rows "
              "(one row per event); the model itself is trained on all states/k/horizons.",
              "- The placebo is the CB-05 label-permutation form: 5 seeds retrain the full CV on "
              "permuted labels and re-select; z compares the observed selection edge to that null.",
              ""]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")
    return path


# --------------------------------------------------------------------------- #
# Driver
# --------------------------------------------------------------------------- #
def run_market(market: str, cfg: dict, *, out_dir: Path = REPORTS_DIR, limit: int | None = None,
               allow_fixture: bool = False, placebo_seeds: int = N_PLACEBO_SEEDS,
               checkpoint_dir: Path | None = None) -> dict:
    """Train, gate and (only on ADOPT) emit the model + shortlist for one market."""
    res = train.train_market(market, cfg, allow_fixture=allow_fixture, max_symbols=limit,
                             checkpoint_dir=checkpoint_dir or out_dir)
    g = gate_frame(res["oof"])
    gate = fold_gate(g)
    pl = (placebo_z(res["X"], res["y"], res["dates"], res["params"], res["splitter"], g,
                    n_seeds=placebo_seeds)
          if placebo_seeds > 0 else
          {"observed_edge": gate["pooled_edge"], "null_mean": float("nan"),
           "null_sd": float("nan"), "null_edges": [], "z": float("nan"), "n_seeds": 0})
    v = verdict(gate["n_folds_pos"], gate["pooled_edge"], pl["z"])
    result = {**res, "gate": gate, "placebo": pl, "verdict": v, "out_dir": str(out_dir)}
    if v == "ADOPT":
        result["model_path"] = str(train.save_model(res))
        shortlist = build_shortlist(res["oof"], market)
        sl_path = Path(out_dir) / f"wi033_shortlist_{market}.parquet"
        shortlist.to_parquet(sl_path, index=False)
        result["shortlist_path"] = str(sl_path)
        result["shortlist_rows"] = int(len(shortlist))
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="WI-033 swing-conditioned 3-class gate (ADOPT_LOOSE_4OF5)")
    parser.add_argument("--market", default="ALL", help="USD | CAD | ALL (default ALL)")
    parser.add_argument("--limit", type=int, default=None, help="Max symbols per market (smoke).")
    parser.add_argument("--out", default=None, help="Output dir (smoke runs use /tmp).")
    parser.add_argument("--allow-fixture", action="store_true")
    parser.add_argument("--placebo-seeds", type=int, default=N_PLACEBO_SEEDS)
    args = parser.parse_args(argv)

    from src.market_cli import cli_markets
    markets = cli_markets(args.market, prog="wi033.evaluate")
    if markets is None:
        return 2
    out_dir = Path(args.out) if args.out else REPORTS_DIR
    cfg = train.load_settings()
    t0 = time.time()
    results = [run_market(m, cfg, out_dir=out_dir, limit=args.limit,
                          allow_fixture=args.allow_fixture,
                          placebo_seeds=args.placebo_seeds) for m in markets]
    report = write_summary(results, out_dir / "wi033_summary.md")
    for r in results:
        print(f"[wi033.evaluate] {r['market']}: verdict={r['verdict']} "
              f"folds={r['gate']['n_folds_pos']}/5 edge={_fmt(r['gate']['pooled_edge'])} "
              f"z={_fmt(r['placebo']['z'], '{:+.2f}')} runtime={r['runtime_sec']}s")
    print(f"[wi033.evaluate] report -> {report} | total {round(time.time() - t0, 1)}s")
    print("[wi033.evaluate] EXIT:0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
