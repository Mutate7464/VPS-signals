"""WI-040 — Layer-1 pickle-library consolidation of the winning ``b_hold`` family (D-023 L1).

One manifest row per fold pickle under `data/models/{wi035,wi036,wi038}` (cell ->
market/learner/variant/binary/h -> OOF AUC/IC -> path), OOF calibration (reliability +
Brier) of the WI-036 winner cell (`exact_full_k0.8` / `b_hold`, best cross-market h) in
both markets, and a top-20 OOF permutation attribution table. Layer 1 only: predictive
stats, no threshold, no entry filter, no trading claim (D-023); no explanation-library
dependency. CLI::

    python -m src.swing_bsh.library_audit --build
    WI040_SMOKE=5 python -m src.swing_bsh.library_audit --build --out /tmp/wi040_smoke
    python -m src.swing_bsh.library_audit --infer --cell wi036:CAD_xgboost_exact_full_k0.8_b_hold_h13_f4 --symbols ENB.TO --tail 5
"""
from __future__ import annotations
import argparse, datetime as dt, os, pickle, re
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from src.swing_bsh import binary_features_ext as ext
from src.swing_bsh import binary_grid, binary_labels, binary_train, train
from src.xgb_trainer import PurgedWalkForwardSplit

BASE_DIR = Path(__file__).resolve().parents[2]
LIBRARY_DIRS = (("wi035", BASE_DIR / "data/models/wi035"), ("wi036", BASE_DIR / "data/models/wi036"),
                ("wi038", BASE_DIR / "data/models/wi038"))
MANIFEST_DIR, MANIFEST_NAME = BASE_DIR / "data/models/wi040", "manifest.parquet"
REPORTS_DIR = BASE_DIR / "reports"
MANIFEST_REPORT_NAME, CALIB_REPORT_NAME = "wi040_library_manifest.md", "wi040_calibration.md"
WI036_REPORT, WI038_REPORT = REPORTS_DIR / "wi036_summary.md", REPORTS_DIR / "wi038_summary.md"
MARKETS, CELL_KEY = ("USD", "CAD"), ["market", "learner", "variant", "binary", "h"]
CELL_FIELDS = ("market", "learner", "variant", "event", "window", "k", "h", "binary", "fold")
WINNER_FALLBACK = {"variant": "exact_full_k0.8", "learner": "xgboost", "binary": "b_hold", "h": 13}
CORE_HOUR_CAP, N_CALIB_BINS, N_PERM_SEEDS, PERM_TOP, MIN_ROWS = 0.5, 10, 3, 20, 30
DEFAULT_CACHE_DIR, DEFAULT_SMOKE_DIR = "/tmp/wi036", "/tmp/wi040_smoke"
MANIFEST_COLS = ["manifest_id", "library", "pickle_path", *CELL_FIELDS, "cell_id", "auc", "ic"]
_STAT_RE = re.compile(
    r"^\|\s*(?P<market>USD|CAD)\s*\|\s*`(?P<variant>[^`]+)`\s*\|\s*(?P<learner>[a-z_0-9]+)\s*\|"
    r"\s*(?P<binary>b_[a-z]+)\s*\|\s*(?P<h>\d+)\s*\|\s*(?P<auc>\d\.\d+)\s*\|"
    r"\s*(?P<z>[-+]?\d+\.\d+)\s*\|\s*(?P<p>[\d.]+e[-+]\d+|\d\.\d+)\s*\|")
_RANK_RE = re.compile(r"^\|\s*1\s*\|\s*`(?P<variant>[^`]+)`\s*\|\s*(?P<learner>[a-z_0-9]+)/"
                      r"(?P<binary>b_[a-z]+)/h(?P<h>\d+)\s*\|")


def _now(): return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _fmt(x, spec="{:.4f}"): return "n/a" if not np.isfinite(float(x)) else spec.format(float(x))


def _path(row):
    p = Path(str(row["pickle_path"]))
    return p if p.is_absolute() else BASE_DIR / p


def _proba(model, X):
    """1-D positive-class probability for both pickle families (1-D or 2-column output)."""
    p = np.asarray(model.predict_proba(X), dtype="float64")
    return p[:, 1] if p.ndim == 2 else np.asarray(p).ravel()


def _md(head, rows):
    """Minimal markdown table (no tabulate dependency)."""
    return ["| " + " | ".join(head) + " |", "| " + " | ".join("---" for _ in head) + " |"] + \
           ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]


def _write(path, lines):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")
    return path


# ------------------------------------------------------------------- manifest scan
def parse_pickle_name(name):
    """`<stem>.pkl` -> cell fields; tolerant of the WI-035 (no variant/h) naming."""
    out, stem = dict.fromkeys(CELL_FIELDS), name[:-4]
    if not name.endswith(".pkl"):
        return out
    m = re.search(r"_f(\d+|final)$", stem)
    if not m:
        return out
    out["fold"] = -1 if m.group(1) == "final" else int(m.group(1))
    rest = stem[: m.start()]
    m = re.search(r"_h(\d+)$", rest)
    if m:
        out["h"], rest = int(m.group(1)), rest[: m.start()]
    for b in ext.BINARY_COLUMNS:
        if rest.endswith("_" + b):
            out["binary"], rest = b, rest[: -len(b) - 1]
            break
    for n_, ev, win, k in ext.variant_grid():
        if rest.endswith("_" + n_):
            out.update(variant=n_, event=ev, window=win, k=float(k))
            rest = rest[: -len(n_) - 1]
            break
    out["market"], _, rest = rest.partition("_")
    out["learner"] = next((l for l in sorted(binary_grid.LEARNERS, key=len, reverse=True)
                           if rest == l or rest.endswith("_" + l)), None)
    return out


def cell_id(frame):
    """`market|learner|variant|binary|h<h>` cell key (WI-036 `_cell_key` form + market)."""
    return (frame["market"].fillna("?") + "|" + frame["learner"].fillna("?") + "|"
            + frame["variant"].fillna("unspecified") + "|" + frame["binary"].fillna("?")
            + "|h" + frame["h"].fillna(-1).astype(int).astype(str))


def scan_library(dirs=None, root=BASE_DIR):
    """One manifest row per ``*.pkl`` under the library dirs (row count == pickle count)."""
    rows = [{"manifest_id": f"{lib}:{p.stem}", "library": lib,
             "pickle_path": str(p.relative_to(root)) if p.is_relative_to(root) else str(p),
             **parse_pickle_name(p.name)}
            for lib, d in (LIBRARY_DIRS if dirs is None else dirs)
            for p in sorted(Path(d).glob("*.pkl"))]
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    for col in ("h", "k", "fold"):
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    frame["cell_id"], frame["auc"], frame["ic"] = cell_id(frame), np.nan, np.nan
    return frame[MANIFEST_COLS]


# --------------------------------------------------------- frozen-report cross-checks
def parse_report_stats(path):
    """FDR-survivor rows (`market/variant/learner/binary/h/auc/z/p`) from a WI report."""
    rows = [{**m.groupdict(), "h": int(m.group("h")), "auc_report": float(m.group("auc")),
             "z": float(m.group("z")), "p": float(m.group("p"))}
            for m in (_STAT_RE.match(l.strip()) for l in Path(path).read_text().splitlines()) if m]
    return pd.DataFrame(rows)


def winner_cell():
    """The WI-036 winner cell read from the frozen report ranking (else the WI-040 fallback)."""
    if WI036_REPORT.exists():
        for line in WI036_REPORT.read_text().splitlines():
            m = _RANK_RE.match(line.strip())
            if m:
                return {**m.groupdict(), "h": int(m.group("h"))}
    return dict(WINNER_FALLBACK)


def attach_report_stats(manifest, stats):
    """Left-join printed survivor AUCs onto the manifest (row count preserved)."""
    out = manifest.copy()
    if stats.empty:
        out["auc_report"], out["z"], out["p"] = np.nan, np.nan, np.nan
    else:
        out = out.merge(stats.drop_duplicates(subset=CELL_KEY)[CELL_KEY + ["auc_report", "z", "p"]],
                        on=CELL_KEY, how="left", validate="many_to_one")
    src = pd.Series("none", index=out.index, dtype="object")
    src[out["auc_report"].notna()], src[out["auc"].notna()] = "report", "refit"
    out["stats_source"] = src
    return out


def spot_check(manifest, n=3):
    """Manifest `auc_report` values vs the AUC literally printed in the WI-036/-038 reports."""
    text = "\n".join(p.read_text() for p in (WI036_REPORT, WI038_REPORT) if p.exists()).splitlines()
    rows = []
    for _, r in manifest[manifest["auc_report"].notna()].head(n).iterrows():
        sig = f"{r['market']} | `{r['variant']}` | {r['learner']} | {r['binary']} | {int(r['h'])}"
        m = next((_STAT_RE.match(x.strip()) for x in text if sig in x), None)
        printed = float(m.group("auc")) if m else np.nan
        rows.append([f"`{r['manifest_id']}`", f"`{r['cell_id']}`", _fmt(r["auc_report"]),
                     "n/a" if not m else _fmt(printed),
                     "yes" if m and printed == float(r["auc_report"]) else "NO"])
    return rows


# ------------------------------------------------- winner-cell OOF refit / Layer-1 stats
def load_market_panel(market, cache_dir=None, limit=None, allow_fixture=False):
    """The WI-036 multi-variant panel + labels: cached artifacts else a fresh build."""
    if cache_dir is not None and limit is None:
        keys = [(n, h) for n, _, _, _ in ext.variant_grid() for h in ext.HORIZONS]
        panel, labels = ext.load_variant_panel(cache_dir, market, keys)
        if panel is not None and not panel.empty:
            return panel, labels
    return ext.build_variant_panel(market, allow_fixture=allow_fixture, max_symbols=limit)


def cell_matrix(panel):
    """Design matrix exactly as `binary_grid.run_market` builds it (prune -> engineer)."""
    kept, _ = binary_labels.kept_features(panel, threshold=binary_grid.PRUNE_RHO,
                                         features=ext.candidate_features(panel))
    panel = train.engineer(panel)
    panel["k"], panel["horizon"] = np.float32(1.0), np.float32(21.0)
    return train.feature_matrix(panel, binary_labels.feature_names(kept))


def winner_oof(panel, labels, cell, params):
    """Purged walk-forward OOF for one cell through `binary_grid.cell_cv` (no pickle write).

    `params` is the learner-specific sub-dict (`binary_train.learner_params(cfg)[learner]`),
    exactly as `binary_grid.run_market` passes it, so the refit reproduces the frozen config.
    """
    key = (cell["variant"], int(cell["h"]))
    if labels is None or key not in labels:
        return None
    X, feats = cell_matrix(panel)
    y = np.asarray(labels[key][cell["binary"]], dtype="int8")
    splitter = PurgedWalkForwardSplit(n_splits=binary_grid.N_SPLITS,
                                     embargo_td=train.embargo_for([int(cell["h"])]))
    cv = binary_grid.cell_cv(X, y, panel["date"].to_numpy(), cell["learner"], params, splitter)
    auc, ic, folds = binary_grid.auc_ic(y, cv["oof"], cv["fold_id"])
    return {"X": X, "feats": feats, "y": y, "auc": auc, "ic": ic, "folds": folds,
            "oof": cv["oof"], "fold_id": cv["fold_id"], "models": cv["models"]}


def calibration_frame(y, p, bins=N_CALIB_BINS):
    """OOF reliability table: per bin count, mean probability, observed rate."""
    df = pd.DataFrame({"y": np.asarray(y, "float64"), "p": np.asarray(p, "float64")})
    df = df[np.isfinite(df["p"])]
    if df.empty:
        return df
    df["bin"] = pd.qcut(df["p"], q=int(min(bins, max(2, df["p"].nunique()))), labels=False,
                        duplicates="drop")
    return df.groupby("bin").agg(n=("y", "size"), p_mean=("p", "mean"), obs=("y", "mean")).reset_index()


def brier(y, p):
    y, p = np.asarray(y, "float64"), np.asarray(p, "float64")
    m = np.isfinite(p) & np.isfinite(y)
    return float(np.mean((p[m] - y[m]) ** 2)) if m.any() else float("nan")


def ece(y, p, bins=N_CALIB_BINS):
    """Expected calibration error = count-weighted mean |mean p - observed rate|."""
    t = calibration_frame(y, p, bins)
    if t.empty:
        return float("nan")
    n = t["n"].to_numpy("float64")
    return float(np.sum(n / n.sum() * np.abs(t["p_mean"] - t["obs"])))


def permutation_importance(X, y, feats, models, fold_id, seeds=N_PERM_SEEDS, top=PERM_TOP,
                           budget=None):
    """OOF AUC drop from shuffling one feature inside each fold (mean over `seeds`)."""
    rng = np.random.default_rng(binary_train.SEED)
    sel_of = {f: s for f, s in ((int(f), np.flatnonzero(fold_id == int(f)))
                                for f in sorted(models))
              if len(s) >= MIN_ROWS and len(np.unique(y[s])) > 1}
    if not sel_of:
        return pd.DataFrame(columns=["feature", "auc_drop", "auc_drop_sd", "seeds_used"]), 0
    base = {f: float(roc_auc_score(y[s], _proba(models[f], X[s]))) for f, s in sel_of.items()}
    drops, done = np.full((len(feats), seeds), np.nan), 0
    for k in range(seeds):
        if budget is not None and budget.exhausted():
            break
        for f, sel in sel_of.items():
            Xs, ys = X[sel].copy(), y[sel]
            for j in range(len(feats)):
                col = Xs[:, j].copy()
                Xs[:, j] = col[rng.permutation(len(sel))]
                d = base[f] - float(roc_auc_score(ys, _proba(models[f], Xs)))
                drops[j, k] = d if np.isnan(drops[j, k]) else drops[j, k] + d
                Xs[:, j] = col
        drops[:, k] /= len(sel_of)
        done += 1
    used = drops[:, : max(done, 1)]
    out = pd.DataFrame({"feature": list(feats), "auc_drop": np.nanmean(used, axis=1),
                        "auc_drop_sd": np.nanstd(used, axis=1), "seeds_used": done})
    return out.sort_values("auc_drop", ascending=False).head(top).reset_index(drop=True), done


# ------------------------------------------------------------------------------ reports
def _verdict(c):
    """Honest one-liner; never upgrades a poorly calibrated cell into a claim."""
    b, s = float(c["brier"]), float(c["skill"])
    if not np.isfinite(b) or not np.isfinite(s):
        return "insufficient OOF rows to judge calibration."
    weak = ("calibration is poor" if s < 0.02 or c["ece"] > 0.05
            else "calibration is modest" if s < 0.10 else "calibration is usable")
    return (f"{weak}: Brier skill {_fmt(s, '{:+.3f}')}, ECE {_fmt(c['ece'])} — reported as-is; "
            "predictive only, no threshold or trading claim follows.")


def write_reports(manifest, win, calib, rdir):
    """`wi040_library_manifest.md` + `wi040_calibration.md` (both Layer-1 only)."""
    cov = []
    for lib, _ in LIBRARY_DIRS:
        g = manifest[manifest["library"] == lib]
        cov.append([f"`{lib}`", len(g), g["cell_id"].nunique(),
                    "/".join(sorted(set(g["market"].dropna()))),
                    "/".join(sorted(set(g["learner"].dropna()))),
                    ",".join(str(int(v)) for v in sorted(set(g["h"].dropna()))) or "—",
                    g["variant"].nunique()])
    counts = manifest["stats_source"].value_counts().to_dict()
    rows = []
    for market in MARKETS:
        g = manifest[(manifest["market"] == market) & (manifest["learner"] == win["learner"])
                     & (manifest["variant"] == win["variant"]) & (manifest["binary"] == win["binary"])
                     & (manifest["h"] == float(win["h"]))]
        folds = sorted(int(v) for v in g["fold"].dropna())
        rows.append([market, len(g), f"{folds[0]}–{folds[-1]}" if folds else "—",
                     ("yes" if _path(g.iloc[0]).exists() else "NO") if len(g) else "—",
                     _fmt(g["auc"].iloc[0]) if len(g) else "n/a",
                     _fmt(g["auc_report"].iloc[0]) if len(g) else "n/a"])
    lines = ["# WI-040 — Layer-1 pickle library manifest (D-023 L1)", "", f"- Generated (UTC): {_now()}",
             f"- Scanned {', '.join('`' + lib + '`' for lib, _ in LIBRARY_DIRS)} -> **{len(manifest)} fold pickles / {manifest['cell_id'].nunique()} cells** (one row per pickle)",
             "- Rows: `" + ", ".join(MANIFEST_COLS + ["auc_report", "z", "p", "stats_source"]) + "`",
             "- Layer 1 only: predictive stats, no threshold / entry filter / trading claim; attribution is permutation-based.",
             "", "## 1. Coverage per library", ""]
    lines += _md(["library", "pickles", "cells", "markets", "learners", "horizons", "variants"], cov)
    lines += ["", "## 2. Winner cell (frozen WI-036 ranking) and stats source", "",
              f"- `{win['variant']}` / `{win['binary']}` / {win['learner']} / h{win['h']}.",
              "- WI-035/-036/-038 persist fold models only (`data/models/*` holds `*.pkl`, no per-cell OOF store), so `auc`/`ic` are recomputed **for the winner cell alone** (`wi040_calibration.md`); `auc_report` is the value printed in the WI-036/-038 FDR table for that exact cell, hence survivors only.",
              f"- `stats_source`: {counts.get('refit', 0)} rows refit (winner cell, both markets), {counts.get('report', 0)} rows carry only the printed AUC, {counts.get('none', 0)} rows have neither (the frozen tables list FDR survivors plus the ranking, not every cell).", ""]
    lines += _md(["market", "winner rows", "fold range", "pickle resolves", "auc (refit)",
                  "auc_report"], rows)
    lines += ["", "## 3. Spot-check — manifest `auc_report` vs the printed report value", ""]
    lines += _md(["manifest_id", "cell_id", "manifest", "printed", "match"],
                 spot_check(manifest)) or ["_no printed survivor row to check._"]
    _write(rdir / MANIFEST_REPORT_NAME, lines)
    lines = ["# WI-040 — winner-cell OOF calibration + permutation attribution (D-023 L1)", "",
             f"- Generated (UTC): {_now()}",
             f"- Cell `{win['variant']}` / `{win['binary']}` / {win['learner']} / h{win['h']} (cross-market WI-036 winner); 5-fold `PurgedWalkForwardSplit`, embargo `max(20, h)`, OOF probabilities re-fit through `binary_grid.cell_cv`",
             "- Layer 1 predictive stats only: no threshold, no entry rule, no return claim.", ""]
    for market, c in calib.items():
        rel = [[int(r["bin"]), int(r["n"]), _fmt(r["p_mean"]), _fmt(r["obs"]),
                _fmt(float(r["p_mean"]) - float(r["obs"]), "{:+.4f}")]
               for _, r in c["reliability"].iterrows()]
        imp = [[i + 1, f"`{r['feature']}`", _fmt(r["auc_drop"]), _fmt(r["auc_drop_sd"])]
               for i, r in c["imp"].iterrows()]
        lines += [f"## {market} — calibration", "",
                  f"- OOF rows {c['n_oof']}; positive rate (no-skill probability) {_fmt(c['prevalence'])}; per-fold AUC " + (", ".join(_fmt(v) for v in c["folds"]) or "n/a"),
                  f"- Pooled OOF AUC **{_fmt(c['auc'])}** (rank-IC {_fmt(c['ic'], '{:+.4f}')}); WI-036 printed AUC for the same cell {_fmt(c['auc_report'])}",
                  f"- Brier **{_fmt(c['brier'])}** vs no-skill Brier {_fmt(c['brier_base'])} (skill {_fmt(c['skill'], '{:+.3f}')}); ECE {_fmt(c['ece'])}",
                  f"- Honest read: {_verdict(c)}", ""]
        lines += _md(["bin", "n", "mean predicted", "observed rate", "gap"], rel) or ["_no finite OOF probabilities._"]
        lines += ["", f"## {market} — top-20 OOF permutation importance ({c['seeds']} seed(s) × {len(c['folds'])} folds)", ""]
        lines += _md(["rank", "feature", "mean AUC drop", "sd"], imp) or ["_no fold model scored._"]
        lines.append("")
    return _write(rdir / CALIB_REPORT_NAME, lines)


# ---------------------------------------------------------------------------- inference
def load_model(path):
    """One fold model out of a `{model, provenance}` pickle."""
    with open(path, "rb") as fh:
        blob = pickle.load(fh)
    return blob["model"] if isinstance(blob, dict) and "model" in blob else blob


def infer(manifest_id, symbols=None, tail=5, cache_dir=None, limit=None, allow_fixture=False,
          manifest=None, panel=None):
    """Score the last `tail` event bars of the named symbols with one manifest row."""
    manifest = scan_library() if manifest is None else manifest
    hit = manifest[manifest["manifest_id"] == manifest_id]
    if hit.empty:
        raise KeyError(f"unknown manifest_id: {manifest_id} (see {MANIFEST_REPORT_NAME})")
    row, path = hit.iloc[0], _path(hit.iloc[0])
    if not path.exists():
        raise FileNotFoundError(f"pickle missing for {manifest_id}: {path}")
    model = load_model(path)
    if panel is None:
        panel, _ = load_market_panel(row["market"], Path(cache_dir) if cache_dir else None, limit,
                                     allow_fixture)
    X, _feats = cell_matrix(panel)
    n_in = getattr(getattr(model, "model", model), "n_features_in_", None)
    if n_in is not None and int(n_in) != X.shape[1]:
        raise ValueError(f"feature mismatch for {manifest_id}: pickle expects {n_in}, panel gives {X.shape[1]}")
    frame = panel[["symbol", "date"]].copy()
    frame["p"] = _proba(model, X)
    names = [s.strip() for s in (symbols or "").split(",") if s.strip()]
    if names:
        frame = frame[frame["symbol"].isin(names)]
    frame = frame.sort_values(["symbol", "date"]).groupby("symbol", group_keys=False).tail(int(tail))
    frame.insert(0, "manifest_id", str(row["manifest_id"]))
    return frame.reset_index(drop=True)[["manifest_id", "symbol", "date", "p"]]


# ---------------------------------------------------------------------------------- CLI
def _build_cli(args, out_dir=None):
    stats = pd.concat([parse_report_stats(WI036_REPORT), parse_report_stats(WI038_REPORT)],
                      ignore_index=True)
    manifest = attach_report_stats(scan_library(), stats)
    win = winner_cell()
    params = binary_train.learner_params(train.load_settings())
    params.setdefault("mlp_torch", {})  # mirrors `binary_grid.run_market`
    budget, calib = binary_grid.CoreBudget(args.core_hours), {}
    for market in MARKETS:
        panel, labels = load_market_panel(market, Path(args.cache_dir) if args.cache_dir else None,
                                          args.limit, args.allow_fixture)
        res = winner_oof(panel, labels, win, params[win["learner"]])
        if res is None:
            continue
        imp, seeds = permutation_importance(res["X"], res["y"], res["feats"], res["models"],
                                            res["fold_id"], args.perm_seeds, PERM_TOP, budget)
        sel = np.isfinite(res["oof"])
        y_sel, p_sel = res["y"][sel], res["oof"][sel]
        prev = float(np.mean(y_sel)) if len(y_sel) else float("nan")
        base = brier(y_sel, np.full(len(y_sel), prev)) if len(y_sel) else float("nan")
        b = brier(y_sel, p_sel)
        mask = ((manifest["market"] == market) & (manifest["learner"] == win["learner"])
                & (manifest["variant"] == win["variant"]) & (manifest["binary"] == win["binary"])
                & (manifest["h"] == float(win["h"])))
        rep = manifest.loc[mask, "auc_report"]
        calib[market] = {"auc": res["auc"], "ic": res["ic"], "folds": res["folds"], "imp": imp,
                         "seeds": seeds, "n_oof": int(sel.sum()), "prevalence": prev, "brier": b,
                         "brier_base": base, "ece": ece(y_sel, p_sel),
                         "reliability": calibration_frame(y_sel, p_sel),
                         "skill": 1.0 - b / base if np.isfinite(base) and base > 0 else float("nan"),
                         "auc_report": float(rep.iloc[0]) if len(rep) else float("nan")}
        manifest.loc[mask, "auc"], manifest.loc[mask, "ic"] = float(res["auc"]), float(res["ic"])
        manifest.loc[mask, "stats_source"] = "refit"
        del panel, res["X"]
    mpath, rdir = (out_dir / MANIFEST_NAME, out_dir) if out_dir else \
        (MANIFEST_DIR / MANIFEST_NAME, REPORTS_DIR)
    mpath.parent.mkdir(parents=True, exist_ok=True)
    manifest.to_parquet(mpath, index=False)
    write_reports(manifest, win, calib, rdir)
    print(f"[wi040.audit] manifest -> {mpath} ({len(manifest)} pickles, {manifest['cell_id'].nunique()} cells, stats {manifest['stats_source'].value_counts().to_dict()})")
    for market, c in calib.items():
        print(f"[wi040.audit] {market} {win['variant']}/{win['binary']} h{win['h']}: AUC {_fmt(c['auc'])} IC {_fmt(c['ic'], '{:+.4f}')} Brier {_fmt(c['brier'])} ECE {_fmt(c['ece'])} seeds {c['seeds']}")
    print(f"[wi040.audit] reports -> {rdir}/[wi040_library_manifest.md, wi040_calibration.md]")
    print(f"[wi040.audit] core {budget.spent():.0f}s / cap {args.core_hours * 3600:.0f}s | EXIT:0")
    return 0


def _infer_cli(args):
    if not args.cell:
        print("[wi040.infer] --cell <manifest_id> required")
        return 2
    try:
        frame = infer(args.cell, args.symbols, args.tail, args.cache_dir, args.limit,
                      args.allow_fixture)
    except (KeyError, FileNotFoundError, ValueError, OSError) as exc:
        print(f"[wi040.infer] FAILED: {exc}")
        return 1
    p, last = frame["p"].to_numpy("float64"), frame.iloc[-1]
    print(f"[wi040.infer] cell {args.cell} | {frame['symbol'].nunique()} symbols, {len(frame)} bars")
    print(f"[wi040.infer] p mean {np.nanmean(p):.4f} min {np.nanmin(p):.4f} max {np.nanmax(p):.4f}"
          f" | last {last['symbol']} {pd.Timestamp(last['date']):%Y-%m-%d} p={p[-1]:.4f}")
    print("[wi040.infer] EXIT:0")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="WI-040 Layer-1 pickle-library audit (D-023 L1)")
    parser.add_argument("--build", action="store_true", help="Scan + calibrate + attribute.")
    parser.add_argument("--infer", action="store_true", help="Score from one manifest row.")
    parser.add_argument("--cell", default=None, help="manifest_id for --infer.")
    parser.add_argument("--symbols", default=None, help="Comma-separated symbols for --infer.")
    parser.add_argument("--tail", type=int, default=5, help="Last N event bars per symbol.")
    parser.add_argument("--limit", type=int, default=None, help="Max symbols per market (smoke).")
    parser.add_argument("--out", default=None, help="Output dir (smoke only; never a frozen path).")
    parser.add_argument("--cache-dir", default=DEFAULT_CACHE_DIR, help="WI-036 panel cache.")
    parser.add_argument("--allow-fixture", action="store_true")
    parser.add_argument("--perm-seeds", type=int, default=N_PERM_SEEDS)
    parser.add_argument("--core-hours", type=float, default=CORE_HOUR_CAP)
    args = parser.parse_args(argv)
    smoke = os.environ.get("WI040_SMOKE", "").strip()
    if smoke.isdigit() and args.limit is None:
        args.limit = int(smoke)
    if args.out is None and smoke:
        args.out = DEFAULT_SMOKE_DIR
    return _infer_cli(args) if args.infer else _build_cli(args, Path(args.out) if args.out else None)


if __name__ == "__main__":
    raise SystemExit(main())
