"""WI-039 — regime-conditional audit of the winning `b_hold` signal (D-022 phase 2).

Inference/join only (no training, no refit): the WI-036 winning cells (`exact_full_k0.8`
xgboost `b_hold`, h in {5, 8, 13, 21}, both markets) are re-scored from their fold pickles
(`data/models/wi036/`) — each fold pickle scores **only its own OOF time block** — then
joined to the WI-027 3x2 regime labels on (symbol, date). The label artifact is
`reports/fib_swings/regime_daily_extended.csv` (= `regime_daily.csv` + atrp63/vol21/trend/
vol_cat/regime, written by `scripts/fib_regime_labels.py`); labels are market-daily, so the join
resolves inside each row's own market.

    WI039_SMOKE=5 python -m src.swing_bsh.hold_regime_audit --out /tmp/wi039_smoke
"""

from __future__ import annotations

import argparse, datetime as dt, os, pickle, time
from pathlib import Path

import numpy as np, pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import roc_auc_score

from src.swing_bsh import binary_features_ext as ext
from src.swing_bsh import binary_grid, binary_labels, train
from src.xgb_trainer import PurgedWalkForwardSplit

BASE_DIR = Path(__file__).resolve().parents[2]
REPORTS_DIR, MODEL_DIR = BASE_DIR / "reports", BASE_DIR / "data" / "models" / "wi036"
REGIME_DAILY = REPORTS_DIR / "fib_swings" / "regime_daily_extended.csv"
REGIME_DAILY_WI027 = REPORTS_DIR / "fib_swings" / "regime_daily.csv"
DEFAULT_SMOKE_DIR, REPORT_NAME = Path("/tmp/wi039_smoke"), "wi039_summary.md"
LEARNER, VARIANT, BINARY = "xgboost", ext.variant_name("exact", "full", 0.8), "b_hold"
HORIZONS: tuple[int, ...] = (5, 8, 13, 21)
N_SPLITS, MIN_N, CORE_HOUR_CAP = 5, 100, 0.3
CONC_SHARE, CONC_AUC, ROBUST_AUC = 0.60, 0.55, 0.52
EVAL_START = "2022-07-01"  # one-shot EVAL window (WI-022/037): dry runs never score it

def design_matrix(panel: pd.DataFrame):
    """Re-derive the WI-036 design matrix (rho>0.3 prune -> engineer -> float32)."""
    kept, _ = binary_labels.kept_features(panel, threshold=binary_grid.PRUNE_RHO,
                                          features=ext.candidate_features(panel))
    eng = train.engineer(panel)
    eng["k"], eng["horizon"] = np.float32(1.0), np.float32(21.0)      # WI-036 cell constants
    X, feats = train.feature_matrix(eng, binary_labels.feature_names(kept))
    assert not any(binary_labels.is_leakage_column(f) for f in feats), "label column leaked"
    return X, feats

def loaded_models(market: str, h: int, model_dir: Path = MODEL_DIR) -> dict:
    """Available fold pickles of one WI-036 winning cell, keyed by fold index."""
    tag, out = f"{market}_{LEARNER}_{VARIANT}_{BINARY}_h{h}", {}
    for k in range(N_SPLITS):
        path = Path(model_dir) / f"{tag}_f{k}.pkl"
        if path.exists():
            with open(path, "rb") as fh:
                out[k] = pickle.load(fh)["model"]
    return out

def oof_proba(X, fold_id, models) -> np.ndarray:
    """Fold-consistent OOF: each fold pickle scores only its own validation block."""
    p = np.full(len(fold_id), np.nan, dtype="float64")
    for k, model in models.items():
        rows = np.asarray(fold_id) == k
        if rows.any():
            p[rows] = np.asarray(model.predict_proba(X[rows]), dtype="float64").ravel()
    return p

def audit_frame(panel, y, p, fold_id, market, h, sub) -> pd.DataFrame:
    """Scored OOF rows (symbol, date, market, h, oof, y_hold) restricted to `sub`."""
    y, p, fold_id = (np.asarray(a) for a in (y, p, fold_id))
    keep = (fold_id[sub] >= 0) & np.isfinite(p[sub])
    idx = np.asarray(sub)[keep]
    return pd.DataFrame({"symbol": panel["symbol"].astype(str).to_numpy()[idx],
                         "date": panel["date"].to_numpy()[idx], "market": market, "h": int(h),
                         "fold": fold_id[sub][keep].astype(int), "oof": p[idx], "y_hold": y[idx]})

def load_regime_labels(path=REGIME_DAILY) -> pd.DataFrame:
    """WI-027 `(market, date, regime)` labels; rows with an empty `regime` are dropped."""
    p = Path(path)
    if not p.exists() and Path(REGIME_DAILY_WI027).exists():
        p = Path(REGIME_DAILY_WI027)
    df = pd.read_csv(p)
    if "regime" not in df.columns:
        raise ValueError(f"{p} carries no `regime` column — the WI-027 labels live in "
                         f"{Path(REGIME_DAILY).name}, not {Path(REGIME_DAILY_WI027).name}")
    df = df[["market", "date", "regime"]].copy()
    df["date"] = pd.to_datetime(df["date"])
    df["regime"] = df["regime"].astype(str).str.strip().replace({"": np.nan, "nan": np.nan})
    return df.dropna(subset=["regime"]).reset_index(drop=True)

def join_regime(preds: pd.DataFrame, regimes: pd.DataFrame, on=("symbol", "date")) -> pd.DataFrame:
    """Left-join `regime` onto prediction rows on `on`; unmatched rows are dropped."""
    keys = list(on)
    reg = regimes[keys + ["regime"]].dropna(subset=["regime"]).drop_duplicates(keys)
    return preds.merge(reg, on=keys, how="left").dropna(subset=["regime"]).reset_index(drop=True)

def cell_stats(y, p, min_n: int = MIN_N) -> dict:
    """Pooled AUC + rank-IC + hold prevalence on one cell's fold-consistent OOF inputs."""
    y, p = np.asarray(y, dtype="float64"), np.asarray(p, dtype="float64")
    ok = len(y) >= int(min_n) and np.unique(y).size > 1 and np.isfinite(p).all()
    return {"n": int(len(y)), "auc": float(roc_auc_score(y, p)) if ok else float("nan"),
            "ic": float(spearmanr(p, y)[0]) if ok else float("nan"),
            "hold_rate": float(y.mean()) if len(y) else float("nan")}

def regime_table(frame: pd.DataFrame, min_n: int = MIN_N) -> pd.DataFrame:
    """Per (regime x h) stats; regimes/horizons with no rows are absent, never NaN rows."""
    cols = ["regime", "h", "n", "auc", "ic", "hold_rate"]
    if not len(frame):
        return pd.DataFrame(columns=cols)
    return pd.DataFrame([dict(regime=r, h=int(h), **cell_stats(g["y_hold"], g["oof"], min_n))
                         for (r, h), g in frame.groupby(["regime", "h"], sort=True)], columns=cols)

def market_verdict(table: pd.DataFrame, min_n: int = MIN_N) -> dict:
    """Robust vs concentrated: the share of signal mass (excess AUC x n) in the top regime.

    CONCENTRATED iff the top regime holds >= `CONC_SHARE` of the market's excess AUC, its
    n-weighted AUC >= `CONC_AUC` and another populated regime scores below `ROBUST_AUC`.
    """
    miss = {"verdict": "inconclusive", "regime": None, "share": np.nan, "auc": np.nan, "n": 0}
    ok = table[np.isfinite(table["auc"].to_numpy(float)) & (table["n"].to_numpy(float) >= min_n)]
    if not len(ok):
        return miss
    a, w = ok["auc"].to_numpy(float), ok["n"].to_numpy(float)
    g = ok.assign(mass=np.clip(a - 0.5, 0.0, None) * w, aw=a * w).groupby("regime", sort=False)
    per = pd.DataFrame({"mass": g["mass"].sum(), "n": g["n"].sum(), "aw": g["aw"].sum()})
    per["auc"] = per["aw"] / per["n"]
    total, top = float(per["mass"].sum()), per["mass"].idxmax()
    share = float(per.loc[top, "mass"] / total) if total > 0 else np.nan
    weak = per[(per.index != top) & (per["auc"] < ROBUST_AUC) & (per["n"] >= min_n)]
    conc = total > 0 and share >= CONC_SHARE and float(per.loc[top, "auc"]) >= CONC_AUC and len(weak)
    return {"verdict": "concentrated" if conc else "robust", "regime": str(top) if conc else None,
            "share": share, "auc": float(per.loc[top, "auc"]), "n": int(per.loc[top, "n"])}

def run_market(market: str, *, model_dir=MODEL_DIR, cache_dir=None, regime_path=REGIME_DAILY,
               limit=None, smoke=False, budget=None) -> dict:
    """Audit one market's winning-cell OOF `b_hold` by WI-027 regime (join only, no refit)."""
    t0, budget = time.time(), budget or binary_grid.CoreBudget(CORE_HOUR_CAP)
    panel, labels = ((None, None) if cache_dir is None else
                     ext.load_variant_panel(cache_dir, market, [(VARIANT, h) for h in HORIZONS]))
    if panel is None or not labels:
        panel, labels = ext.build_variant_panel(market, variants=[(VARIANT, "exact", "full", 0.8)],
                                                horizons=HORIZONS, max_symbols=limit)
    if panel.empty:
        raise RuntimeError(f"no swing events for market={market}")
    X, feats = design_matrix(panel)
    dates, sym = panel["date"].to_numpy(), panel["symbol"].astype(str).to_numpy()
    sub = np.arange(len(panel)) if limit is None else np.flatnonzero(
        pd.Series(sym).isin(set(pd.unique(sym)[: int(limit)])))
    frames, coverage, missing = [], {}, []
    for h in HORIZONS:
        models = loaded_models(market, h, model_dir) if not budget.exhausted() else {}
        if not models:
            missing.append((int(h), "core budget spent" if budget.exhausted() else "no fold pickles"))
            continue
        if any(int(getattr(getattr(m, "model", None), "n_features_in_", len(feats))) != len(feats)
               for m in models.values()):
            raise RuntimeError(f"pickle/matrix width mismatch ({market} h{h}): {len(feats)}")
        splitter = PurgedWalkForwardSplit(n_splits=N_SPLITS, embargo_td=train.embargo_for([h]))
        fid = np.full(len(dates), -1, dtype="int16")
        for k, (_tr, va) in enumerate(splitter.split(dates)):
            fid[va] = k
        p = oof_proba(X, fid, models)
        coverage[int(h)] = int(np.unique(fid[np.isfinite(p)]).size)
        frames.append(audit_frame(panel, labels[(VARIANT, h)][BINARY], p, fid, market, h, sub))
    frame = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(
        columns=["symbol", "date", "market", "h", "fold", "oof", "y_hold"])
    n_joined = len(frame)
    frame = join_regime(frame, load_regime_labels(regime_path).query("market == @market"),
                        on=("market", "date"))
    n_eval = int((frame["date"].to_numpy() >= np.datetime64(EVAL_START)).sum())
    if smoke:  # dry run: the one-shot EVAL window stays untouched
        frame = frame[frame["date"].to_numpy() < np.datetime64(EVAL_START)].reset_index(drop=True)
    table = regime_table(frame)
    return {"market": market, "n_rows": len(panel), "n_symbols": int(frame["symbol"].nunique()),
            "n_oof": len(frame), "n_dropped_label": n_joined - len(frame), "n_eval_pending": n_eval,
            "n_features": len(feats), "coverage": coverage, "missing": missing, "table": table,
            "verdict": market_verdict(table), "smoke": bool(smoke),
            "core_sec": round(budget.spent(), 1), "runtime_sec": round(time.time() - t0, 1)}

def fmt(x, spec: str = "{:.4f}") -> str:
    """`n/a` for a non-finite value, else the formatted float."""
    return "n/a" if not np.isfinite(float(x)) else spec.format(float(x))

def resolve_out_dir(out, *, limit, reports_dir=REPORTS_DIR, smoke_dir=DEFAULT_SMOKE_DIR) -> Path:
    """Limited (smoke) runs never write the real report under `reports/`."""
    if out is None:
        return Path(smoke_dir) if limit is not None else Path(reports_dir)
    out = Path(out)
    if limit is not None and out.resolve() == Path(reports_dir).resolve():
        raise ValueError(f"a limited run may not write the real report ({out})")
    return out

def build_report(results: list[dict], path: Path) -> Path:
    """`wi039_summary.md` — per market x regime x h AUC/IC/n/hold-rate plus a verdict line each."""
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out = ["# WI-039 — regime-conditional audit of the `b_hold` signal (D-022 phase 2)\n",
           f"- Generated (UTC): {now} · inference/join only: WI-036 `{VARIANT}`|{LEARNER}|`{BINARY}`|h in {HORIZONS} fold pickles (`{MODEL_DIR.name}/`) re-score only their own OOF block (no training, no refit)",
           f"- WI-027 3x2 regime labels from `{Path(REGIME_DAILY).name}` joined on (symbol, date) — market-daily, so the join resolves inside each row's own market; unmatched rows dropped, never NaN-filled",
           f"- Per market x regime x h: pooled OOF AUC + rank-IC, n, `{BINARY}` hold prevalence (cells with n < {MIN_N} reported, not scored); `n_jobs=2`, float32, symbol-sequential"]
    if any(r.get("smoke") for r in results):
        out.append(f"- **Smoke run**: the one-shot EVAL window (date >= {EVAL_START}) is excluded.")
    for r in results:
        v = r["verdict"]
        cov = ", ".join(f"h{h}:{c}/{N_SPLITS}" for h, c in sorted(r["coverage"].items()))
        mass = (f"share {fmt(v['share'], '{:.2f}')}, AUC {fmt(v['auc'])}, n={v['n']:,}; "
                f"others below {ROBUST_AUC}")
        verdict = {"concentrated": f"**concentrated in `{v['regime']}`** ({mass})",
                   "robust": f"**robust across regimes** (no regime above the {CONC_SHARE} "
                             f"excess-AUC share; {mass})",
                   "inconclusive": f"**inconclusive** (no regime x h cell clears n>={MIN_N})"}[
                       v["verdict"]]
        miss = ", ".join(f"h{h} ({w})" for h, w in r["missing"]) or "none"
        ev = (f"NOT scored (smoke; {r['n_eval_pending']:,} rows withheld)" if r["smoke"]
              else "included (full-universe run)")
        out += ["", f"## {r['market']}\n",
                f"- {r['n_oof']:,} joined OOF rows from {r['n_symbols']} symbols ({r['n_features']} features, {r['n_rows']:,} panel rows); {r['n_dropped_label']:,} dropped (no regime label); folds {cov or 'none'}; not scored: {miss}",
                f"- EVAL window: {ev}\n", "| h | regime | n | AUC | rank-IC | hold rate |",
                "| ---: | :--- | ---: | ---: | ---: | ---: |"]
        out += ([f"| {int(x['h'])} | `{x['regime']}` | {int(x['n']):,} | {fmt(x['auc'])} | "
                 f"{fmt(x['ic'], '{:+.4f}')} | {fmt(x['hold_rate'], '{:.4f}')} |"
                 for _, x in r["table"].iterrows()] or ["| — | no joined rows with a label | | | | |"])
        out += ["", f"VERDICT {r['market']}: {verdict}",
                f"- runtime {r['runtime_sec']}s core {r['core_sec']}s", ""]
    out += ["## Notes / deviations\n",
            f"- Regime source: the WI names `regime_daily.csv` (r1/r1_s5/r2 only) — the WI-027 `regime` column is written by `scripts/fib_regime_labels.py` to `{Path(REGIME_DAILY).name}` (= `regime_daily.csv` + atrp63/vol21/trend/vol_cat/regime), so that superset is read (override with `--regime-daily`).",
            "- Inference/join only: WI-036 pickles score their own OOF blocks, nothing is fitted or tuned; concentration feeds WI-037 (a one-regime signal implies a regime-gated veto).",
            f"- `{BINARY}` prevalence is a few tenths of a percent (WI-036), so hold rate is small by construction and a per-cell AUC needs both classes in the cell."]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(out) + "\n")
    return path

def main(argv: list[str] | None = None) -> int:
    """CLI: `--market ALL --limit N --out DIR --cache-dir DIR --regime-daily PATH`."""
    p = argparse.ArgumentParser(description="WI-039 regime audit of the b_hold signal")
    p.add_argument("--market", default="ALL", help="USD | CAD | ALL (default ALL)")
    p.add_argument("--limit", type=int, default=None, help="Max symbols per market (smoke).")
    p.add_argument("--out", default=None, help="Output dir (smoke runs use /tmp).")
    p.add_argument("--cache-dir", default="/tmp/wi036", help="WI-036 panel cache dir.")
    p.add_argument("--regime-daily", default=str(REGIME_DAILY), help="WI-027 label CSV.")
    a = p.parse_args(argv)
    smoke = os.environ.get("WI039_SMOKE", "").strip()
    if a.limit is None and smoke.isdigit():
        a.limit = int(smoke)
    from src.market_cli import cli_markets
    markets = cli_markets(a.market, prog="wi039.hold_regime_audit")
    if markets is None:
        return 2
    try:
        out_dir = resolve_out_dir(a.out, limit=a.limit)
    except ValueError as exc:
        print(f"[wi039.regime] {exc}", flush=True)
        return 2
    t0, budget = time.time(), binary_grid.CoreBudget(CORE_HOUR_CAP)
    results = [run_market(m, cache_dir=Path(a.cache_dir), regime_path=Path(a.regime_daily),
                          limit=a.limit, smoke=a.limit is not None, budget=budget) for m in markets]
    report = build_report(results, out_dir / REPORT_NAME)
    for r in results:
        v = r["verdict"]
        print(f"[wi039.regime] {r['market']}: joined={r['n_oof']:,} verdict={v['verdict']}"
              + (f"({v['regime']})" if v["regime"] else "") + f" core={r['core_sec']}s")
    print(f"[wi039.regime] report -> {report} | total {round(time.time() - t0, 1)}s")
    print("[wi039.regime] EXIT:0")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
