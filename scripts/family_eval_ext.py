"""WI-098 — Track B family-eval delta driver for the 7 built l0_ext / l1_bif families.

Evaluates the seven built-but-unevaluated Track B families (`nr_flags`, `clv`,
`cusum_flag`, `stoch_rsi`, `connors_rsi`, `fail_count`, `swing_levels`) with one
delta-vs-baseline event-level grid per `--family`:

* baseline = the incumbent event panel WITHOUT any family's columns — ALL 7 are
  excluded, not just the current one (the delta trap); baseline cells are shared
  across families and reused from a checkpoint;
* arm = baseline + that family's per-bar features joined at each event's detection
  bar (`data/features/l0_ext/<family>_{MKT}.parquet`, exact (symbol, date) key, no
  backfill — D-029 confirmation-date semantics);
* delta = fold-paired OOF statistic: AUC for the binary target (`b_hold`) and
  rank-IC for the continuous cross-sectional target (`xsec_vol_rank_bin`, fitted
  through the regression path — continuous labels are never int8-cast).

Per-family BH-FDR (alpha 0.05) over m = targets x learners x markets; survivors are
positive-delta FDR-passing cells. Decision statistic = cross-market min delta.
PROVISIONAL until admin ratification. Predictive-only license (D-023 layer 1): no
trading or economic metric is computed anywhere here.

Learner = `xgboost` (the repo's primary learner and the only one `binary_train`
fits as a true regressor, which the continuous target needs); panel/label/stat
machinery mirrors `scripts/run_l0_r12.py` read-only.

CLI::

    uv run python scripts/family_eval_ext.py --family nr_flags --market USD --resume
    L0EVAL_SMOKE=2 uv run python scripts/family_eval_ext.py --family clv --out /tmp/WI-098_smoke
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.dataset as ds
from scipy import stats
from sklearn.metrics import roc_auc_score

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # repo root -> `src` importable

from src.swing_bsh import binary_features_ext as ext
from src.swing_bsh import binary_grid, binary_labels, binary_train, train
from src.swing_bsh import targets_ext as tg
from src.xgb_trainer import PurgedWalkForwardSplit

BASE_DIR = Path(__file__).resolve().parents[1]
FEATURES_DIR = BASE_DIR / "data" / "features" / "l0_ext"
REPORTS_DIR = BASE_DIR / "reports" / "l0ext_eval"
CKPT_DIR = BASE_DIR / "data" / "models" / "l0ext_eval"
CACHE_DIR = Path("/tmp/l0ext_eval")
SMOKE_OUT = Path("/tmp/WI-098_smoke")

FAMILIES: tuple[str, ...] = ("nr_flags", "clv", "cusum_flag", "stoch_rsi", "connors_rsi",
                             "fail_count", "swing_levels")
TARGETS: tuple[str, ...] = ("b_hold", "xsec_vol_rank_bin")
REGRESSION_TARGETS: tuple[str, ...] = ("xsec_vol_rank_bin",)
LEARNERS: tuple[str, ...] = ("xgboost",)
HORIZON = 21
KEYS = ("symbol", "date")
N_SPLITS = binary_grid.N_SPLITS
PRUNE_RHO = 0.3
FDR_ALPHA = binary_grid.FDR_ALPHA
CORE_HOUR_CAP = 2.5
START_UTC = ""


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text()) if path.exists() else {}


def _f(v) -> str:
    v = float(v)
    return "n/a" if not np.isfinite(v) else f"{v:.4f}"


def is_regression(target: str) -> bool:
    """True for the continuous cross-sectional target (regression read-out, no int8 cast)."""
    return target in REGRESSION_TARGETS


# --------------------------------------------------------------------------- #
# Family features: projected read + detection-bar join
# --------------------------------------------------------------------------- #
def family_columns(family: str, market: str) -> list[str]:
    """Feature columns of one family's per-bar parquet (probed from the file schema)."""
    path = FEATURES_DIR / f"{family}_{market}.parquet"
    return [n for n in ds.dataset(path, format="parquet").schema.names if n not in KEYS]


def load_family(family: str, market: str, symbols=None) -> pd.DataFrame:
    """Projected, symbol-filtered read of one family's per-bar features (float32)."""
    cols = family_columns(family, market)
    df = ds.dataset(FEATURES_DIR / f"{family}_{market}.parquet", format="parquet").to_table(
        columns=[*KEYS, *cols]).to_pandas()
    df["symbol"] = df["symbol"].astype(str)
    if symbols is not None:
        df = df[df["symbol"].isin(list(symbols))]
    for c in cols:
        df[c] = pd.to_numeric(df[c], errors="coerce").astype("float32")
    return df.reset_index(drop=True)


def join_family(panel: pd.DataFrame, fam: pd.DataFrame, cols) -> pd.DataFrame:
    """Left-join one family's features at (symbol, detection date); absent row -> NaN.

    The key is the panel's detection bar exactly (no backfill, D-029); a family
    value at a later bar can never reach an earlier event.
    """
    out = panel.copy()
    out["symbol"] = out["symbol"].astype(str)
    right = pd.DataFrame({"symbol": fam["symbol"].to_numpy(),
                          "date": pd.to_datetime(fam["date"]).to_numpy(),
                          **{c: fam[c].to_numpy() for c in cols}}
                         ).drop_duplicates(["symbol", "date"])
    left = pd.DataFrame({"_row": np.arange(len(out)), "symbol": out["symbol"].to_numpy(),
                         "date": pd.to_datetime(out["date"]).to_numpy()})
    merged = left.merge(right, on=["symbol", "date"], how="left").sort_values("_row")
    for c in cols:
        out[c] = merged[c].to_numpy()
    return out.reset_index(drop=True)


def joined_panel(panel: pd.DataFrame, market: str, families=FAMILIES) -> pd.DataFrame:
    """Event panel + every family's per-bar features (all 7 joined once, symbol-filtered)."""
    out = panel.copy()
    syms = pd.unique(out["symbol"].astype(str))
    for f in families:
        out = join_family(out, load_family(f, market, symbols=syms), family_columns(f, market))
    return out


# --------------------------------------------------------------------------- #
# Feature sets + the baseline-exclusion prune probe
# --------------------------------------------------------------------------- #
def feature_sets(panel: pd.DataFrame, market: str, family: str) -> tuple[list, list, set]:
    """`(base, arm, all_family_cols)`; base excludes ALL 7 families' columns (delta trap)."""
    cand = ext.candidate_features(panel)
    allcols = {c for f in FAMILIES for c in family_columns(f, market)}
    base = [c for c in cand if c not in allcols]
    arm = base + [c for c in family_columns(family, market) if c in panel.columns]
    return base, arm, allcols


def pruned(panel: pd.DataFrame, feats: list) -> list[str]:
    """ρ-pruned kept feature names (WI-034 inline uniqueness prune, order-preserving)."""
    kept, _dropped = binary_labels.kept_features(panel, threshold=PRUNE_RHO, features=feats)
    return binary_labels.feature_names(kept)


def prune_probe(panel: pd.DataFrame, market: str, families=FAMILIES) -> dict[str, list[str]]:
    """`{family: sorted(baseline kept-set Δ arm kept-set)}` — must hold only that family's cols."""
    base = set(pruned(panel, feature_sets(panel, market, families[0])[0]))
    out: dict[str, list[str]] = {}
    for f in families:
        out[f] = sorted(set(pruned(panel, feature_sets(panel, market, f)[1])) ^ base)
    return out


def design(panel: pd.DataFrame, kept: list[str]):
    """float32 design matrix over the pruned whitelist (mirrors run_l0_r12._design)."""
    p = train.engineer(panel)
    p["k"] = np.float32(1.0)
    p["horizon"] = np.float32(HORIZON)
    return train.feature_matrix(p, kept)


# --------------------------------------------------------------------------- #
# Panel + labels (single pinned variant, single horizon; mirrors run_l0_r12)
# --------------------------------------------------------------------------- #
def _variant(market: str) -> str:
    return ext.variant_name(tg.PINNED_EVENT[market], "full", 0.8)


def load_market(market: str, *, limit=None, allow_fixture=False):
    """`(panel, {target: label array})` for one market; cached only when `limit is None`."""
    variant = _variant(market)
    pp, lp = CACHE_DIR / f"panel_{market}.parquet", CACHE_DIR / f"labels_{market}.npz"
    if limit is None and pp.exists() and lp.exists():
        blob = np.load(lp)
        return (pd.read_parquet(pp),
                {"b_hold": blob["b_hold"], "xsec_vol_rank_bin": blob["xsec_cont"]})
    panel, blabels = ext.build_variant_panel(
        market, allow_fixture=allow_fixture, max_symbols=limit,
        variants=[(variant, tg.PINNED_EVENT[market], "full", 0.8)], horizons=(HORIZON,))
    if panel.empty:
        raise RuntimeError(f"no swing events for market={market}")
    xrows: list[tuple] = []
    n_rows = 0
    for symbol, g, idx, states, _atr in tg.iter_events(market, allow_fixture=allow_fixture,
                                                       max_symbols=limit):
        n_rows += int(idx.size)
        high, low = g["high"].to_numpy("float64"), g["low"].to_numpy("float64")
        xrows.append((symbol, g["close"].to_numpy("float64"),
                      ext._entry_bars(high, low, idx, states == "at_bottom"),
                      g["date"].to_numpy()))
    if n_rows != len(panel):
        raise RuntimeError(f"label/panel row mismatch for {market}: {n_rows} != {len(panel)}")
    event = tg.PINNED_EVENT[market]
    frame = pd.DataFrame({
        "symbol": np.concatenate([[s] * bars[event].size for s, _c, bars, _d in xrows]),
        "bar": np.concatenate([bars[event] for _s, _c, bars, _d in xrows]),
        "date": np.concatenate([d[bars[event]] for _s, _c, bars, d in xrows])})
    xsec = np.asarray(tg.xsec_vol_rank_cont_labels(frame, {r[0]: r[1] for r in xrows}, HORIZON),
                      dtype="float32")
    b_hold = np.asarray(blabels[(variant, HORIZON)]["b_hold"])
    if limit is None:
        pp.parent.mkdir(parents=True, exist_ok=True)
        panel.to_parquet(pp, index=False)
        np.savez_compressed(lp, b_hold=b_hold, xsec_cont=xsec)
    return panel, {"b_hold": b_hold, "xsec_vol_rank_bin": xsec}


# --------------------------------------------------------------------------- #
# Fold-paired statistic + BH-FDR
# --------------------------------------------------------------------------- #
def fold_scores(X, y, dates, learner, params, splitter, tag, regression) -> dict[int, float]:
    """Per-fold OOF scores: AUC (binary) or rank-IC (continuous, regression path)."""
    cv = binary_grid.cell_cv(X=X, y=y, dates=dates, learner=learner, params=params,
                             splitter=splitter, model_dir=None, tag=tag, regression=regression)
    oof = np.asarray(cv["oof"], dtype="float64")
    fid = np.asarray(cv["fold_id"])
    yv = np.asarray(y, dtype="float64")
    out: dict[int, float] = {}
    for f in np.unique(fid[fid >= 0]):
        sel = (fid == f) & np.isfinite(oof)
        if regression:
            sel = sel & np.isfinite(yv)
            if int(sel.sum()) > 5 and np.unique(yv[sel]).size > 1 and np.unique(oof[sel]).size > 1:
                out[int(f)] = float(stats.spearmanr(oof[sel], yv[sel])[0])
        elif np.unique(yv[sel]).size > 1:
            out[int(f)] = float(roc_auc_score(yv[sel], oof[sel]))
    return out


def paired_p(deltas) -> tuple[float, float]:
    """Two-sided paired t over fold deltas -> (mean delta, p) — mirrors run_l0_r12."""
    d = np.asarray(deltas, dtype="float64")
    d = d[np.isfinite(d)]
    if d.size < 2 or float(np.std(d, ddof=1)) == 0.0:
        return (float(d.mean()) if d.size else float("nan")), 1.0
    t = float(d.mean()) / (float(np.std(d, ddof=1)) / math.sqrt(d.size))
    return float(d.mean()), float(2.0 * stats.t.sf(abs(t), df=d.size - 1))


def bh(pvals, m_total: int | None = None, alpha: float = FDR_ALPHA) -> np.ndarray:
    """BH-FDR survivors over the family's full multiplicity m (never only the finite p's)."""
    return binary_grid.bh_fdr(pvals, alpha=alpha, m_total=m_total)[0]


# --------------------------------------------------------------------------- #
# Run + reports
# --------------------------------------------------------------------------- #
def _cell_table(rows: list[dict]) -> list[str]:
    lines = ["| market | target | learner | h | base | arm | delta | p | FDR | feats |",
             "| :--- | :--- | :--- | ---: | ---: | ---: | ---: | ---: | :--- | ---: |"]
    for c in sorted(rows, key=lambda c: -c["delta"]):
        lines.append(f"| {c['market']} | `{c['target']}` | {c['learner']} | {c['h']} | "
                     f"{_f(c['base_mean'])} | {_f(c['arm_mean'])} | {c['delta']:+.4f} | "
                     f"{c['p']:.3g} | {'YES' if c.get('fdr') else ''} | {c['n_features']} |")
    if not rows:
        lines.append("| — | no cell completed | | | | | | | | |")
    return lines


def write_reports(family: str, cells: list[dict], probes: dict, out_dir: Path,
                  markets: list[str], m_total: int, budget) -> list[Path]:
    """Per-market `<family>_<MKT>.md` + consolidated `<family>_summary.md`."""
    out_dir.mkdir(parents=True, exist_ok=True)
    nxt = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%MZ")
    footer = ["", "## Footer", "",
              f"- START_UTC: {START_UTC}", f"- END_UTC: {_now()}",
              f"- core: {budget.spent():.1f}s of {int(budget.cap)}s cap",
              f"- NEXT_ALLOWED_RUN_UTC: {nxt} "
              f"(burst {'>=' if budget.spent() >= 3600 else '<'} 1 core-h)",
              "- Verdict PROVISIONAL — advisory until admin ratification.",
              "- PREDICTIVE ONLY (D-023 layer 1) — no trading/economic claim.", ""]
    written: list[Path] = []
    for market in markets:
        path = out_dir / f"{family}_{market}.md"
        path.write_text("\n".join([
            f"# WI-098 — family eval `{family}` ({market}) [PROVISIONAL]", "",
            f"- Generated (UTC): {_now()}",
            f"- Family columns: {', '.join('`' + c + '`' for c in family_columns(family, market))}",
            "- Baseline: event panel WITHOUT all 7 families' columns (delta trap); "
            "arm: baseline + this family's columns.",
            f"- Statistic: fold-paired OOF delta — AUC (`b_hold`) / rank-IC "
            f"(`xsec_vol_rank_bin`, regression path); learner `{LEARNERS[0]}`, h{HORIZON}",
            f"- BH-FDR alpha={FDR_ALPHA}, m = targets x learners x markets = {m_total}",
            "", *_cell_table([c for c in cells if c["market"] == market]), *footer]) + "\n")
        written.append(path)
    lines = [f"# WI-098 — `{family}` consolidated summary [PROVISIONAL]", "",
             f"- Generated (UTC): {_now()}",
             f"- Markets: {', '.join(markets)}; BH family m = {m_total} "
             f"({len(TARGETS)} targets x {len(LEARNERS)} learner(s) x {len(markets)} markets)",
             "", "## Prune probe — baseline kept-set Δ arm kept-set (family columns only)", "",
             "| market | family | diff | family-only |", "| :--- | :--- | :--- | :--- |"]
    for market in markets:
        for f, diff in sorted(probes.get(market, {}).items()):
            ok = set(diff) <= set(family_columns(f, market))
            lines.append(f"| {market} | `{f}` | "
                         f"{', '.join('`' + d + '`' for d in diff) or '—'} | "
                         f"{'OK' if ok else 'VIOLATION'} |")
    lines += ["", "## Cells (all markets)", "", *_cell_table(cells), "",
              "## Decision statistic (PROVISIONAL) — cross-market min delta", "",
              "| target | learner | min delta | markets |", "| :--- | :--- | ---: | :--- |"]
    for tgt in TARGETS:
        for learner in LEARNERS:
            got = [c for c in cells if c["target"] == tgt and c["learner"] == learner]
            if got:
                lines.append(f"| `{tgt}` | {learner} | "
                             f"{min(c['delta'] for c in got):+.4f} | {', '.join(markets)} |")
    lines += footer
    sum_path = out_dir / f"{family}_summary.md"
    sum_path.write_text("\n".join(lines) + "\n")
    written.append(sum_path)
    return written


def run(markets: list[str], family: str, *, ckpt_dir: Path, out_dir: Path, limit=None,
        allow_fixture=False, resume: bool = False, core_hours: float = CORE_HOUR_CAP,
        learners=LEARNERS) -> tuple[list[dict], list[Path]]:
    """One family's delta grid across markets (checkpointed per cell, budget-gated)."""
    budget = binary_grid.CoreBudget(core_hours)
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    arm_path, base_path = ckpt_dir / f"{family}_cells.json", ckpt_dir / "_baseline_cells.json"
    arm_cells = _load_json(arm_path) if resume else {}
    base_cells = _load_json(base_path) if resume else {}
    params = binary_train.learner_params(train.load_settings())
    splitter = PurgedWalkForwardSplit(n_splits=N_SPLITS, embargo_td=train.embargo_for([HORIZON]))
    grid_share = budget.cap * 0.95  # fits-only guard (no placebo reserve in this grid)
    cells: list[dict] = []
    probes: dict[str, dict] = {}
    info: dict[str, tuple] = {}
    stopped = False
    for market in markets:
        panel, y_by = load_market(market, limit=limit, allow_fixture=allow_fixture)
        joined = joined_panel(panel, market)
        probes[market] = prune_probe(joined, market)
        base_feats, arm_feats, _all = feature_sets(joined, market, family)
        base_kept, arm_kept = pruned(joined, base_feats), pruned(joined, arm_feats)
        Xb, _fb = design(joined, base_kept)
        Xa, _fa = design(joined, arm_kept)
        dates = joined["date"].to_numpy()
        info[market] = (len(joined), len(base_kept), len(arm_kept))
        for tgt in TARGETS:
            y = np.asarray(y_by[tgt])
            fin = np.isfinite(np.asarray(y, dtype="float64"))
            Xbt, Xat, dt_, yt = Xb[fin], Xa[fin], dates[fin], y[fin]
            for learner in learners:
                bk = f"{market}|base|{tgt}|{learner}|h{HORIZON}"
                ak = f"{market}|arm|{tgt}|{learner}|h{HORIZON}"
                if bk in base_cells:
                    base = {int(k): v for k, v in base_cells[bk]["fold_scores"].items()}
                elif budget.spent() > grid_share:
                    stopped = True
                    continue
                else:
                    base = fold_scores(Xbt, yt, dt_, learner, params[learner], splitter,
                                       f"{market}_base_{tgt}_{learner}", is_regression(tgt))
                    base_cells[bk] = {"fold_scores": base, "n_features": len(base_kept)}
                    base_path.write_text(json.dumps(base_cells))
                if ak in arm_cells:
                    arm = {int(k): v for k, v in arm_cells[ak]["fold_scores"].items()}
                    n_feat = arm_cells[ak]["n_features"]
                elif budget.spent() > grid_share:
                    stopped = True
                    continue
                else:
                    arm = fold_scores(Xat, yt, dt_, learner, params[learner], splitter,
                                      f"{market}_{family}_{tgt}_{learner}", is_regression(tgt))
                    n_feat = len(arm_kept)
                    arm_cells[ak] = {"fold_scores": arm, "n_features": n_feat}
                    arm_path.write_text(json.dumps(arm_cells))
                common = sorted(set(base) & set(arm))
                delta, p = paired_p([arm[f] - base[f] for f in common])
                cells.append({"family": family, "market": market, "target": tgt,
                              "learner": learner, "h": HORIZON,
                              "base_mean": float(np.mean(list(base.values()))) if base else np.nan,
                              "arm_mean": float(np.mean(list(arm.values()))) if arm else np.nan,
                              "delta": delta, "p": p, "n_features": n_feat,
                              "n_folds": len(common)})
    m_total = len(TARGETS) * len(learners) * len(markets)
    surv = bh([c["p"] for c in cells], m_total=m_total) if cells else np.zeros(0, dtype=bool)
    for c, s in zip(cells, surv):
        c["fdr"] = bool(s)
    reports = write_reports(family, cells, probes, out_dir, markets, m_total, budget)
    ok = all(set(d) <= set(family_columns(f, m)) for m, pr in probes.items() for f, d in pr.items())
    print(f"[l0ext] family={family} " + " ".join(
        f"{m}:rows={r},base={b},arm={a}" for m, (r, b, a) in info.items()))
    print("[l0ext] prune-probe family-only=" + ("OK" if ok else "VIOLATION") + " " + " ".join(
        f"{f}:+{len(d)}" for m in probes for f, d in sorted(probes[m].items())))
    print(f"[l0ext] cells={len(cells)} survivors={int(surv.sum())}/{m_total} "
          f"core={budget.spent():.1f}s of {int(budget.cap)}s cap stopped={stopped}")
    print(f"[l0ext] reports -> {out_dir}")
    return cells, reports


def main(argv: list[str] | None = None) -> int:
    global START_UTC
    parser = argparse.ArgumentParser(description="WI-098 Track B family-eval delta driver")
    parser.add_argument("--family", required=True, choices=list(FAMILIES))
    parser.add_argument("--market", default="ALL")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--out", default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--allow-fixture", action="store_true")
    parser.add_argument("--core-hours", type=float, default=CORE_HOUR_CAP)
    args = parser.parse_args(argv)

    smoke = os.environ.get("L0EVAL_SMOKE", "").strip()
    if args.limit is None and smoke.isdigit():
        args.limit = int(smoke)
    out_dir = Path(args.out) if args.out else (SMOKE_OUT if smoke else REPORTS_DIR)
    ckpt_dir = (out_dir / "cells") if smoke else CKPT_DIR  # smoke touches /tmp only

    from src.market_cli import cli_markets
    markets = cli_markets(args.market, prog="l0ext.eval")
    if markets is None:
        return 2
    START_UTC, t0 = _now(), time.time()
    run(markets, args.family, ckpt_dir=ckpt_dir, out_dir=out_dir, limit=args.limit,
        allow_fixture=args.allow_fixture, resume=args.resume, core_hours=args.core_hours)
    print(f"[l0ext] EXIT:0 | wall={time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
