"""WI-072 — b_hold OOF score rebuild for the amended universe (D-027 §6, WI-066 signal `b_hold`).

The WI-066 (b) retry named a rebuilt b_hold OOF coverage as a new input: the prepared panel's
`p_b_hold` column was all-NaN because `scripts/build_l2_prepared.py` could not produce three of the
WI-035 provenance features (`k`, `horizon` — grid `_design()` constants — and the engineered
`state_is_bottom`). This driver scores the prepared-panel rows with the frozen WI-035
`hist_gbm` b_hold fold pickles: feature names come from **pickle provenance** (23 names for USD,
24 for CAD), the fold of a row is the **prepared panel's `fold` column**, and the output is
`1 − P(hold)` per row — the repo's b_hold score convention.

    uv run python -m src.l2_overlay.constructions.b_hold_scores --smoke   # synthetic, *_smoke roots
    uv run python -m src.l2_overlay.constructions.b_hold_scores --full    # full CALIB run = PM gate

Layer: **L1.5 input-prep** (D-027) — an input for the L2 ranker, not a trading claim and not an L1
refit. Output roots are named constants: `<root>/<MARKET>.parquet` (`date:symbol:market:fold:p_b_hold:
b_hold`, float32) + `manifest.json`, beside a card under `reports/l2_b_hold_scores[_smoke]/`.

Invariants: n_jobs=2, float32 immediately, CALIB only (no EVAL read), no fabricated score — a missing
feature, a prepared row without a panel row, or a fold without a pickle fails loudly.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import pickle
import time
from pathlib import Path

import numpy as np
import pandas as pd

from src.l2_overlay import harness as H

BASE_DIR = Path(__file__).resolve().parents[3]        # named input/output roots (never CLI args)
WI035_DIR = BASE_DIR / "data/models/wi035"
PREPARED_ROOT = BASE_DIR / "data/models/l2_prepared"
SCORE_ROOT, SCORE_SMOKE_ROOT = (BASE_DIR / "data/models/l2_b_hold_scores",
                                BASE_DIR / "data/models/l2_b_hold_scores_smoke")
REPORTS_ROOT, REPORTS_SMOKE_ROOT = (BASE_DIR / "reports/l2_b_hold_scores",
                                    BASE_DIR / "reports/l2_b_hold_scores_smoke")
PANEL_CACHE = "/tmp/wi048"                            # `build_l2_prepared` cache, then its rebuild
CACHE_FALLBACK = Path("~/.hermes/cache/scratch/l2_prep_cache").expanduser()
MARKETS: tuple[str, ...] = ("USD", "CAD")
N_SPLITS, N_JOBS = 5, 2
GRID_CONSTANTS = {"k": 1.0, "horizon": 21.0}          # binary_grid `_design()` constants (not in the panel)
OUT_COLUMNS = ("date", "symbol", "market", "fold", "p_b_hold", "b_hold")
# The WI-035 USD provenance list (23 names); `feature_list()` is the authority when pickles are on disk.
SMOKE_FEATURES: tuple[str, ...] = (
    "adx_3", "adx_21", "adx_144", "di_spread_3", "di_spread_144", "atr_pct_3", "amihud_3",
    "donchian_break_144", "kama_er_3", "kama_er_15", "hurst_9", "hurst_15", "hurst_24", "hurst_39",
    "hurst_63", "entropy_9", "entropy_24", "entropy_102", "range_compression_8_55",
    "range_compression_21_144", "state_is_bottom", "k", "horizon")
SMOKE_DATES, SMOKE_NAMES, SMOKE_SEED = 90, 25, 72
__all__ = ["BASE_DIR", "MARKETS", "OUT_COLUMNS", "PREPARED_ROOT", "REPORTS_ROOT", "REPORTS_SMOKE_ROOT",
           "SCORE_ROOT", "SCORE_SMOKE_ROOT", "SMOKE_FEATURES", "EvalLeak", "SmokeModel", "align_rows",
           "assert_calib_only", "build_scores", "design_matrix", "feature_list", "load_models",
           "load_panel", "main", "pickle_paths", "read_prepared", "run_market", "score_oof",
           "smoke_models", "synthetic_fixture", "write_card", "write_outputs"]


class EvalLeak(RuntimeError):
    """Raised when a row at/after `EVAL_START` reaches this CALIB-only structure."""


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# --------------------------------------------------------------------------- frozen model inputs
def pickle_paths(market: str, *, pickle_dir=WI035_DIR) -> dict[int, Path]:
    """The five WI-035 fold pickles for `market`; a missing pickle is a defect, not a gap."""
    paths = {k: Path(pickle_dir) / f"{market}_hist_gbm_b_hold_f{k}.pkl" for k in range(N_SPLITS)}
    missing = [str(p) for p in paths.values() if not p.exists()]
    if missing:
        raise FileNotFoundError(f"WI-035 b_hold fold pickles missing: {missing}")
    return paths


def _load_pickle(path):
    with open(path, "rb") as fh:
        return pickle.load(fh)


def feature_list(market: str, *, pickle_dir=WI035_DIR) -> tuple[str, ...]:
    """Feature names (ORDER = model input order) from the WI-035 provenance; folds must agree."""
    feats: tuple[str, ...] | None = None
    for path in pickle_paths(market, pickle_dir=pickle_dir).values():
        f = tuple(str(c) for c in _load_pickle(path)["provenance"]["features"])
        if feats is not None and f != feats:
            raise ValueError(f"{market}: WI-035 fold feature lists differ ({path.name})")
        feats = f
    return feats


def load_models(market: str, *, pickle_dir=WI035_DIR) -> dict[int, object]:
    """`{fold: CalibratedBinary}` — frozen b_hold models, no refit anywhere in this module."""
    return {k: _load_pickle(p)["model"] for k, p in pickle_paths(market, pickle_dir=pickle_dir).items()}


class SmokeModel:
    """Deterministic stand-in for a WI-035 pickle: same `predict_proba` / `n_features_in_` surface.

    P(hold) falls with the first provenance feature (`adx_3` = the synthetic fixture's latent),
    so `1 − P(hold)` is a planted score in a smoke run.
    """

    def __init__(self, n_features: int, fold: int):
        self.n_features_in_, self.fold = int(n_features), int(fold)

    def predict_proba(self, X) -> np.ndarray:
        x = np.asarray(X, dtype="float64")
        return 1.0 / (1.0 + np.exp(0.5 * x[:, 0]))


def smoke_models(n_features: int = len(SMOKE_FEATURES)) -> dict[int, SmokeModel]:
    """Five fold stand-ins for the smoke roots (no pickle read, no fit)."""
    return {k: SmokeModel(n_features, k) for k in range(N_SPLITS)}


# --------------------------------------------------------------------------- panel / universe wiring
def load_panel(market: str, *, caches=(CACHE_FALLBACK, PANEL_CACHE)) -> pd.DataFrame:
    """Feature panel (CALIB rows only) from the caches `build_l2_prepared.py` uses, rebuilt one first."""
    from src.swing_bsh import grid_targets_ext as gt     # heavy import kept local

    panel, src = None, None
    for cache in caches:
        candidate, _labels = gt.load_panel(market, cache_dir=cache)
        if candidate is not None and not candidate.empty:
            panel, src = candidate, str(cache)
            break
    if panel is None:
        raise FileNotFoundError(f"no feature panel for {market} in caches {list(map(str, caches))}")
    panel = panel.reset_index(drop=True)
    panel["date"] = pd.to_datetime(panel["date"])
    calib = panel["date"] < pd.Timestamp(H.CALIB_END)
    assert_calib_only(panel.loc[calib, "date"])
    out = panel.loc[calib].reset_index(drop=True)
    out.attrs["panel_source"] = src
    return out


def read_prepared(market: str, *, prepared_root=PREPARED_ROOT) -> pd.DataFrame:
    """The amended-universe panel (WI-072 cycle 41): one row per quorum-date swing event."""
    path = Path(prepared_root) / f"{market}.parquet"
    if not path.exists():
        raise FileNotFoundError(f"prepared CALIB panel missing: {path} (full run is a PM gate)")
    frame = pd.read_parquet(path, columns=["date", "symbol", "fold"]).reset_index(drop=True)
    frame["date"], frame["symbol"] = pd.to_datetime(frame["date"]), frame["symbol"].astype(str)
    assert_calib_only(frame["date"])
    return frame


def assert_calib_only(dates, *, eval_start: str = H.EVAL_START) -> int:
    """EVAL lock: an EVAL/undated row reaching this CALIB-only structure is a defect, not a warning."""
    d = pd.to_datetime(pd.Series(np.asarray(dates)))
    bad = int(((d >= pd.Timestamp(eval_start)) | d.isna()).sum())
    if bad:
        raise EvalLeak(f"{bad} EVAL/undated rows reached a CALIB-only structure (eval_start {eval_start})")
    return int(len(d))


def _keys(frame: pd.DataFrame) -> np.ndarray:
    day = pd.to_datetime(frame["date"]).dt.strftime("%Y-%m-%d")
    return (frame["symbol"].astype(str) + "|" + day).to_numpy()


def align_rows(panel: pd.DataFrame, prepared: pd.DataFrame) -> np.ndarray:
    """Panel position per prepared row via `(symbol, date)`; an unmatched key is a defect (no drop)."""
    pos = pd.Series(np.arange(len(panel)), index=_keys(panel))
    hit = pd.Series(_keys(prepared)).map(pos[~pos.index.duplicated(keep="first")])
    miss = int(hit.isna().sum())
    if miss:
        raise KeyError(f"{miss}/{len(prepared)} prepared rows have no feature-panel row")
    return hit.to_numpy("int64")


def design_matrix(panel: pd.DataFrame, features) -> np.ndarray:
    """float32 design matrix in provenance order: panel columns + `state_is_bottom` + grid constants."""
    cols, missing = {}, []
    for name in features:
        if name in panel.columns:
            cols[name] = panel[name]
        elif name == "state_is_bottom" and "state" in panel.columns:
            cols[name] = (panel["state"].astype(str).to_numpy() == "at_bottom").astype("float32")
        elif name in GRID_CONSTANTS:
            cols[name] = np.full(len(panel), GRID_CONSTANTS[name], dtype="float32")
        else:
            missing.append(name)
    if missing:
        raise KeyError(f"b_hold features not produced by the panel/pipeline: {missing}")
    return pd.DataFrame({n: np.asarray(cols[n], dtype="float32") for n in features}).to_numpy("float32")


def score_oof(X, fold, models: dict) -> np.ndarray:
    """Per-row `(symbol, date)`-aligned: score a row only with the fold pickle its fold names."""
    fold = np.asarray(fold, dtype="int64")
    out = np.full(len(fold), np.nan, dtype="float32")
    for k, model in sorted(models.items()):
        idx = np.flatnonzero(fold == int(k))
        if idx.size == 0:
            continue
        n_in = getattr(model, "n_features_in_", None)
        if n_in not in (None, np.asarray(X).shape[1]):
            raise ValueError(f"fold {k}: model expects {n_in} features, X has {np.asarray(X).shape[1]}")
        pred = np.asarray(model.predict_proba(np.asarray(X)[idx]), dtype="float64")
        if pred.ndim != 1:
            raise ValueError(f"fold {k}: b_hold predict_proba is not 1-d")
        out[idx] = pred.astype("float32")
    scored = fold >= 0                                            # fold -1 = not out-of-fold (NaN by design)
    left = int((~np.isfinite(out[scored])).sum())
    if left:
        raise ValueError(f"{left} rows carry a fold id but no b_hold OOF score (missing fold pickle)")
    return out


def build_scores(market: str, panel: pd.DataFrame, prepared: pd.DataFrame, models: dict,
                 features) -> tuple[pd.DataFrame, dict]:
    """One `1 − P(hold)` OOF score per prepared row, aligned to the prepared panel's own fold column."""
    pos = align_rows(panel, prepared)
    X = design_matrix(panel, features)[pos]
    fold = pd.to_numeric(prepared["fold"]).to_numpy("int64")
    p = score_oof(X, fold, models)
    out = pd.DataFrame({"date": pd.to_datetime(prepared["date"]), "symbol": prepared["symbol"].astype(str),
                        "market": market, "fold": fold, "p_b_hold": p})
    out["b_hold"] = (1.0 - out["p_b_hold"]).astype("float32")
    assert_calib_only(out["date"])
    assert not out.duplicated(["date", "symbol"]).any(), "duplicate (symbol, date) event keys"
    counts = {int(k): int(v) for k, v in out["fold"].value_counts().sort_index().items()}
    stats = {"market": market, "n_rows": int(len(out)), "n_scored": int((fold >= 0).sum()),
             "n_not_oof": int((fold < 0).sum()), "fold_counts": counts, "n_features": int(len(features)),
             "features": [str(f) for f in features], "panel_source": panel.attrs.get("panel_source", "")}
    return out.astype({c: "float32" for c in ("p_b_hold", "b_hold")})[list(OUT_COLUMNS)], stats


def synthetic_fixture(market="USD", n_dates=SMOKE_DATES, n_names=SMOKE_NAMES, seed=SMOKE_SEED):
    """Deterministic panel with the full 23-feature provenance schema (no `data/` read).

    The frame doubles as the prepared panel (it carries `date`/`symbol`/`fold`), so a smoke run
    exercises the whole alignment path without touching disk inputs.
    """
    rng = np.random.default_rng(seed)
    n = int(n_dates) * int(n_names)
    latent = rng.normal(0.0, 1.0, n).astype("float32")
    frame = pd.DataFrame({
        "date": np.repeat(pd.date_range("2021-01-04", periods=int(n_dates), freq="B").to_numpy(), int(n_names)),
        "symbol": np.tile(np.array([f"{market}{i:02d}" for i in range(int(n_names))]), int(n_dates)),
        "state": np.tile(np.array(["at_bottom", "at_top"] * (int(n_names) // 2 + 1))[: int(n_names)],
                         int(n_dates)),
        "fold": np.repeat(np.arange(int(n_dates)) % N_SPLITS, int(n_names)).astype("int64"),
    })
    for i, name in enumerate(SMOKE_FEATURES):
        if name == "state_is_bottom":
            continue
        frame[name] = (latent if i == 0 else rng.normal(0.0, 1.0, n)).astype("float32")
    frame["k"], frame["horizon"] = np.float32(1.0), np.float32(21.0)
    frame["state_is_bottom"] = (frame["state"].to_numpy() == "at_bottom").astype("float32")
    return frame.sort_values(["date", "symbol"], kind="mergesort").reset_index(drop=True)


# --------------------------------------------------------------------------- artifacts
def write_outputs(score_root, market: str, frame: pd.DataFrame, stats: dict, *, smoke: bool):
    """`<root>/<MARKET>.parquet` (float32) + `manifest.json` (fold counts, feature list, sha256)."""
    root = Path(score_root)
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{market}.parquet"
    frame.astype({c: "float32" for c in ("p_b_hold", "b_hold")})[list(OUT_COLUMNS)].to_parquet(
        path, index=False)
    payload = {"generated_by": "WI-072 src.l2_overlay.constructions.b_hold_scores", "market": market,
               "written_utc": _now(), "layer": "L1.5 input-prep (D-027 §6)", "n_jobs": N_JOBS,
               "eval_start": str(H.EVAL_START), "eval_locked": True, "smoke": bool(smoke),
               "score_parquet": path.name, "score_sha256": _sha256(path), **stats}
    mpath = root / "manifest.json"
    mpath.write_text(json.dumps(payload, indent=2, default=str) + "\n")
    return path, mpath


def write_card(report_root, market: str, stats: dict, *, smoke: bool) -> Path:
    """CALIB card: coverage, schema and fold distribution of the rebuilt scores (record-only)."""
    folds = ", ".join(f"{k}:{v:,}" for k, v in stats["fold_counts"].items())
    lines = [f"# b_hold OOF scores — {market} (WI-072, D-027 §6)", "",
             f"- Generated (UTC): {_now()}{'  (smoke / synthetic)' if smoke else ''}",
             "- Source: WI-035 `hist_gbm` b_hold fold pickles; feature names from provenance; "
             "no refit, CALIB only (EVAL unread)",
             f"- Rows: {stats['n_rows']:,} written, {stats['n_scored']:,} out-of-fold scored, "
             f"{stats['n_not_oof']:,} fold = -1 (NaN by design)",
             f"- Fold counts (prepared panel's `fold`): {folds}",
             f"- Schema: {stats['n_features']} provenance features: " + ", ".join(stats["features"]),
             f"- Panel source: `{stats.get('panel_source', '')}`", "",
             "Record-only: no shortlist, no deployment, no live trading."]
    path = Path(report_root) / f"b_hold_scores_{market}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")
    return path


def run_market(market: str, panel: pd.DataFrame, prepared: pd.DataFrame, *, models=None, features=None,
               score_root=SCORE_ROOT, report_root=REPORTS_ROOT, smoke: bool = False) -> dict:
    """Build → persist → card for one market; `models`/`features` are injectable for tests."""
    feats = tuple(features) if features is not None else (SMOKE_FEATURES if smoke else feature_list(market))
    mdl = models if models is not None else (smoke_models(len(feats)) if smoke else load_models(market))
    frame, stats = build_scores(market, panel, prepared, mdl, feats)
    artifact, manifest = write_outputs(score_root, market, frame, stats, smoke=smoke)
    report = write_card(report_root, market, stats, smoke=smoke)
    return {"artifact": artifact, "manifest": manifest, "report": report, "stats": stats, "frame": frame}


# --------------------------------------------------------------------------- CLI
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="WI-072 b_hold OOF score rebuild (D-027 §6)")
    ap.add_argument("--market", default=None, choices=list(MARKETS), help="One market (default: both).")
    ap.add_argument("--smoke", action="store_true", help="Synthetic run into the *_smoke roots.")
    ap.add_argument("--full", action="store_true", help="PM go/no-go acknowledgement (full CALIB run).")
    args = ap.parse_args(argv)
    if not args.smoke and not args.full:
        raise SystemExit("full CALIB run is a PM gate: pass --full (go/no-go) or use --smoke")
    markets = (args.market,) if args.market else MARKETS
    score_root = SCORE_SMOKE_ROOT if args.smoke else SCORE_ROOT
    report_root = REPORTS_SMOKE_ROOT if args.smoke else REPORTS_ROOT
    t0 = time.time()
    for market in markets:
        panel = synthetic_fixture(market) if args.smoke else load_panel(market)
        prepared = panel if args.smoke else read_prepared(market)
        res = run_market(market, panel, prepared, score_root=score_root, report_root=report_root,
                         smoke=args.smoke)
        s = res["stats"]
        print(f"[wi072.b_hold] {'smoke' if args.smoke else 'calib'} {market}: rows {s['n_rows']:,} "
              f"scored {s['n_scored']:,} folds {s['fold_counts']} -> "
              f"{res['artifact'].relative_to(BASE_DIR)}")
    print(f"[wi072.b_hold] roots {score_root.relative_to(BASE_DIR)}, "
          f"{report_root.relative_to(BASE_DIR)} | {time.time() - t0:.1f}s | EXIT:0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
