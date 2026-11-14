"""WI-064 — L1.5 meta-label driver (D-027 Phase 1): wire the frozen fib entries + the
feature panel through the WI-062 `meta_oof` machinery and persist per-market purged-CV
OOF probabilities as an L2 input artifact.

Layer: **L1.5 input-prep** (D-027) — an input for the L2 rebuild, not an L1 refit and not
a trading claim. Research scope: code + synthetic tests + `--smoke`; the full-universe run
is a separate PM go/no-go and needs `--full` plus an explicit `--baseline` PM artifact.

    uv run python -m src.l2_overlay.drivers.meta_label_full --smoke
    uv run python -m src.l2_overlay.drivers.meta_label_full --full --infer --baseline <pm_artifact.parquet>

Output root is a named constant (`OOF_ROOT` / `SMOKE_ROOT`), never read from `--out`:
`<root>/<MARKET>_oof.parquet` (`date:symbol:p_oof:fold`, `p_oof` float32) plus
`<root>/manifest.json` (input hashes + CV fold bounds). Only purged-CV OOF rows strictly
before `EVAL_START` are written — EVAL is never read. `meta_label_ext.meta_oof` is reused
unchanged; this driver only wires inputs, runs it and persists outputs.

Invariants: n_jobs=2, float32 immediately, purged/embargoed CV, symbol-sequential panel
reads, primary OOF as an alignment input only (never a feature column).
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from src.l2_overlay import harness as H
from src.swing_bsh import meta_label_ext as ml
from src.swing_bsh import train
from src.swing_bsh.hold_filter_gate import baseline_returns
from src.swing_bsh.hold_regime_audit import design_matrix
from src.swing_bsh.library_audit import load_market_panel

BASE_DIR = Path(__file__).resolve().parents[3]
OOF_ROOT = BASE_DIR / "data/models/l2_meta_oof"
SMOKE_ROOT = BASE_DIR / "data/models/l2_meta_oof_smoke"
PANEL_CACHE, BASELINE_DIR = "/tmp/wi036", "/tmp/wi035"
MARKETS: tuple[str, ...] = ("USD", "CAD")
OOF_COLUMNS = ("date", "symbol", "p_oof", "fold")
FLOAT32_COLUMNS = ("p_oof",)
EVAL_START = H.EVAL_START
N_JOBS, N_SPLITS, SEED, SMOKE_LIMIT = 2, ml.N_SPLITS, ml.SEED, 5

__all__ = ["BASE_DIR", "EVAL_START", "MARKETS", "OOF_COLUMNS", "OOF_ROOT", "SMOKE_ROOT",
           "load_baseline", "load_panel", "main", "prepare_market", "run_oof", "write_outputs"]


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _fmt(x, spec: str = "{:.4f}") -> str:
    return "n/a" if not np.isfinite(float(x)) else spec.format(float(x))


def _sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# --------------------------------------------------------------------------- inputs
def load_panel(market: str, cache_dir=PANEL_CACHE, limit=None, allow_fixture=False) -> pd.DataFrame:
    """Existing feature-panel load path (the `--infer` path): cache first, symbol-sequential slice."""
    panel, _labels = load_market_panel(market, Path(cache_dir) if cache_dir else None, None, allow_fixture)
    if panel is None or panel.empty:
        raise RuntimeError(f"no swing events for market={market}")
    if limit is not None:
        keep = list(pd.unique(panel["symbol"].astype(str)))[: int(limit)]
        panel = panel[panel["symbol"].astype(str).isin(keep)].reset_index(drop=True)
    return panel


def load_baseline(market: str, baseline=None):
    """Frozen fib baseline entries: the PM `--baseline` artifact, else the WI-035 frozen cell.

    Returns ``(frame[symbol, date, r_frozen(, p)], resolved_path)``; one row per (symbol, date).
    """
    if baseline is None:
        path = Path(BASELINE_DIR) / f"wi035_panel_{market}.parquet"
        frame = baseline_returns(market, BASELINE_DIR)
        cols = [c for c in ("symbol", "date", "r_frozen", "p") if c in frame.columns]
    else:
        path = Path(baseline)
        if not path.exists():
            raise FileNotFoundError(f"baseline artifact missing: {path}")
        frame = pd.read_parquet(path)
        missing = {"symbol", "date", "r_frozen"} - set(frame.columns)
        if missing:
            raise KeyError(f"baseline artifact {path} lacks {sorted(missing)}")
        cols = ["symbol", "date", "r_frozen"] + (["p"] if "p" in frame.columns else [])
    out = frame.loc[:, cols].copy()
    out["symbol"], out["date"] = out["symbol"].astype(str), pd.to_datetime(out["date"])
    out["r_frozen"] = pd.to_numeric(out["r_frozen"], errors="coerce").astype("float64")
    return out.dropna(subset=["r_frozen"]).reset_index(drop=True), path


def prepare_market(market: str, *, baseline=None, cache_dir=PANEL_CACHE, limit=None,
                   allow_fixture=False) -> dict:
    """Frozen fib entries joined (symbol, date) to the feature panel and its design matrix."""
    panel = load_panel(market, cache_dir, limit, allow_fixture)
    X, feats = design_matrix(panel)                      # float32 design matrix
    base, base_path = load_baseline(market, baseline)
    keys = pd.DataFrame({"symbol": panel["symbol"].astype(str).to_numpy(),
                         "date": pd.to_datetime(panel["date"]).to_numpy(),
                         "pos": np.arange(len(panel))})
    joined = keys.merge(base, on=["symbol", "date"], how="inner", sort=False)
    joined = joined.sort_values(["date", "symbol"], kind="mergesort").reset_index(drop=True)
    pos = joined["pos"].to_numpy()
    frame = pd.DataFrame({"symbol": joined["symbol"].astype(str).to_numpy(),
                          "date": joined["date"].to_numpy(),
                          "state": panel["state"].astype(str).to_numpy()[pos],
                          "r_frozen": joined["r_frozen"].to_numpy(dtype="float64"),
                          "p": (joined["p"].to_numpy(dtype="float64") if "p" in joined
                                else np.full(len(joined), np.nan))})
    return {"market": market, "frame": frame, "X": np.asarray(X, dtype="float32")[pos],
            "feats": list(feats),
            "inputs": {"baseline": base_path,
                       "panel_cache": Path(cache_dir) / f"wi036_panel_{market}.parquet"}}


# --------------------------------------------------------------------------- OOF
def run_oof(frame: pd.DataFrame, X, *, eval_start=EVAL_START, n_splits: int = N_SPLITS,
            min_train_rows: int = ml.MIN_TRAIN_ROWS, embargo_td: int = train.EMBARGO_FLOOR,
            seed: int = SEED) -> dict:
    """Purged-CV OOF meta probabilities on CALIB rows only; EVAL rows are dropped before the fit."""
    Xf = np.asarray(X, dtype="float32")
    if Xf.shape[0] != len(frame):
        raise ValueError(f"X rows {Xf.shape[0]} != frame rows {len(frame)}")
    dates = pd.to_datetime(pd.Series(frame["date"].to_numpy())).to_numpy()
    calib = dates < np.datetime64(pd.Timestamp(eval_start))     # EVAL lock: never read
    f, Xc, dc = frame.loc[calib].reset_index(drop=True), Xf[calib], dates[calib]
    y_meta = ml.build_meta_labels(ml.primary_sides(f["state"]), f["r_frozen"])
    po = f["p"].to_numpy(dtype="float64") if "p" in f.columns else np.full(len(f), np.nan)
    finite_po = np.isfinite(po)
    po = np.where(finite_po, po, np.where(np.isfinite(f["r_frozen"].to_numpy(dtype="float64")),
                                         0.5, np.nan))
    res = ml.meta_oof(y_meta, po, Xc, dc, n_splits=int(n_splits), embargo_td=int(embargo_td),
                      min_train_rows=int(min_train_rows), seed=int(seed))
    oof = pd.DataFrame({"date": dc, "symbol": f["symbol"].astype(str).to_numpy(),
                        "p_oof": np.asarray(res["oof"], dtype="float32"),
                        "fold": np.asarray(res["fold_id"], dtype="int16")})
    oof = oof.loc[oof["fold"] >= 0, list(OOF_COLUMNS)].reset_index(drop=True)
    if len(oof) and pd.Timestamp(oof["date"].max()) >= pd.Timestamp(eval_start):
        raise AssertionError("EVAL row leaked into the OOF artifact")
    return {"oof": oof, "auc": float(res["auc"]), "folds": res["folds"],
            "n_scored": int(res["n_scored"]), "n_calib_rows": int(calib.sum()),
            "primary_oof_as_feature": bool(res["primary_oof_used_as_feature"]),
            "feature_guard": res["feature_guard"]}


def write_outputs(out_root, market: str, res: dict, extra: dict | None = None):
    """Persist `<MARKET>_oof.parquet` + `manifest.json` (input hashes, fold bounds) under the root."""
    root = Path(out_root)
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{market}_oof.parquet"
    frame = res["oof"].astype({"p_oof": "float32", "fold": "int16"})[list(OOF_COLUMNS)]
    frame.to_parquet(path, index=False)
    payload = {"generated_by": "WI-064 src.l2_overlay.drivers.meta_label_full", "market": market,
               "written_utc": _now(), "layer": "L1.5 input-prep (D-027)", "n_jobs": N_JOBS,
               "seed": SEED, "eval_start": str(EVAL_START), "eval_locked": True,
               "oof_parquet": path.name, "n_rows": int(len(frame)), "n_scored": res["n_scored"],
               "n_calib_rows": res["n_calib_rows"], "auc": res["auc"],
               "oof_sha256": _sha256(path), "folds": res["folds"], **(extra or {})}
    mpath = root / "manifest.json"
    mpath.write_text(json.dumps(payload, indent=2, default=str) + "\n")
    return path, mpath


# --------------------------------------------------------------------------- CLI
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="WI-064 meta-label OOF driver (L1.5 input-prep, D-027)")
    ap.add_argument("--market", default=None, choices=list(MARKETS), help="One market (default: both).")
    ap.add_argument("--baseline", default=None, help="PM frozen fib baseline artifact (full run).")
    ap.add_argument("--cache-dir", default=PANEL_CACHE, help="WI-036 feature-panel cache.")
    ap.add_argument("--infer", action="store_true", help="Score the panel via the existing infer path.")
    ap.add_argument("--limit", type=int, default=None, help="First N symbols (smoke).")
    ap.add_argument("--smoke", action="store_true", help="Dry run into the smoke root.")
    ap.add_argument("--full", action="store_true", help="PM go/no-go acknowledgement (full run).")
    ap.add_argument("--allow-fixture", action="store_true")
    ap.add_argument("--n-splits", type=int, default=N_SPLITS)
    ap.add_argument("--min-train-rows", type=int, default=ml.MIN_TRAIN_ROWS)
    ap.add_argument("--out", default=None, help="Smoke-only write root.")
    args = ap.parse_args(argv)
    if args.out and not args.smoke:
        raise SystemExit("--out is smoke-only; the frozen root is a named constant")
    if not args.smoke and not args.full:
        raise SystemExit("full-universe run is a PM gate: pass --full (go/no-go) or use --smoke")
    if not args.smoke and not args.infer:
        raise SystemExit("--infer required: score the feature panel via the existing infer path")
    root = OOF_ROOT if not args.smoke else SMOKE_ROOT
    if args.out:
        root = Path(args.out)
        if root.resolve() == OOF_ROOT.resolve():
            raise SystemExit("refusing to write the frozen root from --out")
    if args.smoke and args.limit is None:
        args.limit = SMOKE_LIMIT
    t0, markets = time.time(), (args.market,) if args.market else MARKETS
    for market in markets:
        prep = prepare_market(market, baseline=args.baseline, cache_dir=args.cache_dir,
                              limit=args.limit, allow_fixture=args.allow_fixture)
        res = run_oof(prep["frame"], prep["X"], n_splits=args.n_splits,
                      min_train_rows=args.min_train_rows)
        extra = {"smoke": bool(args.smoke), "n_features": len(prep["feats"]),
                 "infer": True, "inputs": {k: {"path": str(p), "sha256": _sha256(p)}
                                           for k, p in prep["inputs"].items() if Path(p).exists()}}
        path, _ = write_outputs(root, market, res, extra)
        shown = path.relative_to(BASE_DIR) if path.is_relative_to(BASE_DIR) else path
        print(f"[wi064.meta] {market} rows {len(res['oof'])}/{res['n_calib_rows']} "
              f"folds {sum(1 for f in res['folds'] if 'n_val' in f)} auc {_fmt(res['auc'])} -> {shown}")
    print(f"[wi064.meta] root {root} | smoke {bool(args.smoke)} | "
          f"{time.time() - t0:.1f}s | EXIT:0")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI only
    raise SystemExit(main())
