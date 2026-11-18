"""WI-063 — L1.5 meta-label full-universe driver (Layer 1 predictive only).

Runs the ratified WI-062 machinery per market: ``train.build_event_panel`` ->
``meta_label_ext.primary_sides`` -> ``build_meta_labels`` -> ``feature_names`` ->
``meta_oof``.

**Cost note:** ``build_meta_labels`` is called with ``cost=0.0`` — the 25 bps
per-side floor is already priced inside ``r_frozen`` (the frozen fib-rule forward
return); charging it again would double-count the round trip.

Layer 1 only (D-023): pooled OOF AUC, per-fold AUCs, n rows/scored, positive rate,
primary-side prevalence and the feature-guard status. No threshold, no entry rule,
no EV. ``primary_oof`` is an alignment placeholder and is never a feature (the
WI-062 guard rejects every ``p_/prob/pred/oof`` column).

``--smoke`` runs a synthetic fixture and writes only under a ``/tmp`` prefix; it
never touches ``reports/l15_meta_label``. Purge sentinels (``-1``) are excluded
from fits and scores. Invariants: float32 X, ``n_jobs=2``, stdout <= 5 lines.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))  # repo root -> `src` importable

from src.swing_bsh import meta_label_ext as mlx  # noqa: E402
from src.swing_bsh import train  # noqa: E402

N_JOBS = 2
OUT_DIR = BASE_DIR / "reports" / "l15_meta_label"
SMOKE_DIR = Path("/tmp/wi063_meta_label_smoke")
SMOKE_SPLITS, SMOKE_ROWS = 3, 600

__all__ = ["OUT_DIR", "SMOKE_DIR", "main", "meta_label_payload", "prepare_panel",
           "run_market", "run_smoke", "summary_markdown", "synthetic_panel",
           "write_outputs"]


# --------------------------------------------------------------------------- #
# Panel -> labels / features / OOF
# --------------------------------------------------------------------------- #
def prepare_panel(panel, *, k: float = train.GATE_K,
                  horizon: int = train.GATE_H) -> pd.DataFrame:
    """Keep the canonical gate geometry, order by time, add engineered columns."""
    if panel is None or panel.empty:
        raise RuntimeError("empty event panel")
    out = panel
    if "k" in out.columns:
        out = out[np.isclose(out["k"].to_numpy(dtype="float64"), float(k))]
    if "horizon" in out.columns:
        out = out[np.isclose(out["horizon"].to_numpy(dtype="float64"), float(horizon))]
    if out.empty:
        raise RuntimeError(f"no events at k={k}, horizon={horizon}")
    out = out.sort_values(["date", "symbol"], kind="stable").reset_index(drop=True)
    return train.engineer(out)


def meta_label_payload(panel, market: str, *, n_splits: int = mlx.N_SPLITS,
                       params: dict | None = None) -> dict:
    """Layer-1 payload for one market (never writes; see `write_outputs`)."""
    p = prepare_panel(panel)
    side = mlx.primary_sides(p["state"])
    y_meta = mlx.build_meta_labels(side, p["r_frozen"], cost=0.0)
    feats = mlx.feature_names(p.columns)
    X = (p[feats].to_numpy(dtype="float32") if feats
         else np.empty((len(p), 0), dtype="float32"))
    embargo = (train.embargo_for(p["horizon"].to_numpy())
               if "horizon" in p.columns else train.EMBARGO_FLOOR)
    res = mlx.meta_oof(y_meta, side, X, p["date"].to_numpy(), n_splits=int(n_splits),
                       embargo_td=embargo, params=params)
    if res["primary_oof_used_as_feature"] is not False:   # structural guard
        raise AssertionError("primary_oof leaked into the meta feature matrix")
    folds = [{**f, "auc": mlx.meta_auc(
        y_meta, np.where(res["fold_id"] == f["fold"], res["oof"], np.nan))}
        for f in res["folds"]]
    valid = y_meta >= 0
    finite_side = np.isfinite(side.astype("float64"))
    return {
        "wi": "WI-063", "market": str(market), "layer": 1,
        "primary": "swing_side(at_bottom=long, at_top=short)",
        "label": "y_meta = 1 iff side * r_frozen > cost", "cost": mlx.DEFAULT_COST,
        "cost_note": "25 bps per-side floor already inside r_frozen",
        "n_rows": int(len(y_meta)), "n_labeled": int(valid.sum()),
        "n_purged": int(len(y_meta) - valid.sum()), "n_scored": int(res["n_scored"]),
        "meta_positive_rate": float(y_meta[valid].mean()) if valid.any() else None,
        "primary_side_prevalence": (float(np.mean(side[finite_side] > 0))
                                    if finite_side.any() else None),
        "pooled_oof_auc": float(res["auc"]), "folds": folds,
        "embargo_td": int(embargo), "n_features": len(feats), "features": feats,
        "excluded_feature_columns": [str(c) for c in p.columns
                                     if mlx.is_primary_prediction_name(c)],
        "feature_guard": str(res["feature_guard"]),
        "feature_guard_ok": bool(all(not mlx.is_primary_prediction_name(f) for f in feats)),
        "primary_oof_used_as_feature": bool(res["primary_oof_used_as_feature"]),
    }


# --------------------------------------------------------------------------- #
# Output (JSON + markdown summary)
# --------------------------------------------------------------------------- #
def _clean(obj):
    """json-safe copy: non-finite floats -> null."""
    if isinstance(obj, dict):
        return {str(k): _clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_clean(v) for v in obj]
    if isinstance(obj, float):
        return obj if math.isfinite(obj) else None
    if isinstance(obj, (np.floating, np.integer)):
        return _clean(obj.item())
    return bool(obj) if isinstance(obj, np.bool_) else obj


def _fmt(x) -> str:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return "n/a"
    return f"{v:.4f}" if math.isfinite(v) else "n/a"


def summary_markdown(p: dict) -> str:
    """One-page Layer-1 read-out (pooled AUC, fold table, guards)."""
    lines = [
        f"# L1.5 meta-label — {p['market']}", "",
        "Layer 1 predictive only (D-023): no threshold, no entry rule, no EV.",
        "Primary = swing side; label = primary wins vs `r_frozen` with **cost=0.0**",
        "(the 25 bps per-side floor is already inside `r_frozen`).", "",
        "| metric | value |", "|---|---|",
        f"| rows | {p['n_rows']} |", f"| labeled | {p['n_labeled']} |",
        f"| purge sentinels (-1) | {p['n_purged']} |", f"| OOF scored | {p['n_scored']} |",
        f"| meta positive rate | {_fmt(p['meta_positive_rate'])} |",
        f"| primary long share | {_fmt(p['primary_side_prevalence'])} |",
        f"| pooled OOF AUC | {_fmt(p['pooled_oof_auc'])} |",
        f"| embargo (td) | {p['embargo_td']} |",
        f"| features | {p['n_features']} |",
        f"| feature guard | `{p['feature_guard']}` |",
        f"| feature_guard_ok | {p['feature_guard_ok']} |",
        f"| primary_oof_used_as_feature | {p['primary_oof_used_as_feature']} |",
        f"| mode | {p.get('mode', 'full')} |", "",
        "## Fold table", "",
        "| fold | n_train | n_calib | n_val | pos_train | pos_val | fold AUC | calibration |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for f in p["folds"]:
        lines.append(
            f"| {f.get('fold')} | {f.get('n_train', '-')} | {f.get('n_calib', '-')} | "
            f"{f.get('n_val', '-')} | {f.get('pos_train', '-')} | {f.get('pos_val', '-')} | "
            f"{_fmt(f.get('auc'))} | {f.get('calibration', f.get('skipped', '-'))} |")
    return "\n".join(lines) + "\n"


def write_outputs(payload: dict, out_dir) -> tuple[Path, Path]:
    """Write `meta_label_<MKT>.json` + `.md`; smoke payloads may only go to /tmp."""
    out = Path(out_dir)
    resolved = out.resolve()
    if payload.get("mode") == "smoke" and not (
            resolved == Path("/tmp") or Path("/tmp") in resolved.parents):
        raise ValueError(f"smoke output must stay under /tmp, got {out}")
    out.mkdir(parents=True, exist_ok=True)
    stem = f"meta_label_{payload['market']}"
    json_path, md_path = out / f"{stem}.json", out / f"{stem}.md"
    json_path.write_text(json.dumps(_clean(payload), indent=2))
    md_path.write_text(summary_markdown(payload))
    return json_path, md_path


# --------------------------------------------------------------------------- #
# Drivers
# --------------------------------------------------------------------------- #
def run_market(market: str, *, out_dir=OUT_DIR, max_symbols: int | None = None,
               n_splits: int = mlx.N_SPLITS, allow_fixture: bool = False) -> dict:
    """Full-universe run (PM-owned): build the panel, score OOF, write JSON/MD."""
    panel = train.build_event_panel(market, allow_fixture=allow_fixture,
                                    max_symbols=max_symbols)
    payload = meta_label_payload(panel, market, n_splits=n_splits)
    write_outputs(payload, out_dir)
    return payload


def synthetic_panel(n: int = SMOKE_ROWS, seed: int = 7,
                    *, permute: bool = False) -> pd.DataFrame:
    """Tiny deterministic fixture: half at_top (purge sentinels), signal in one feature."""
    rng = np.random.default_rng(seed)
    bottom = (np.arange(n) % 2 == 0)
    state = np.where(bottom, "at_bottom", "at_top")
    latent = rng.normal(size=n).astype("float32")
    ret = np.full(n, np.nan, dtype="float32")
    ret[bottom] = 0.01 * latent[bottom]
    if permute:
        rows = np.flatnonzero(bottom)
        ret[rows] = rng.permutation(ret[rows])
    return pd.DataFrame({
        "symbol": np.full(n, "MOCK", dtype=object),
        "date": pd.bdate_range("2020-01-02", periods=n), "state": state,
        "y": np.zeros(n, dtype="int8"),
        "k": np.full(n, train.GATE_K, dtype="float32"),
        "horizon": np.full(n, train.GATE_H, dtype="float32"),
        "close": (10.0 + latent).astype("float32"),
        "atr": np.full(n, 0.2, dtype="float32"), "r_frozen": ret,
        "geom_score": latent,
        "atr_pct": np.abs(rng.normal(0.01, 0.004, n)).astype("float32"),
    })


def run_smoke(market: str = "USD", *, out_dir=SMOKE_DIR) -> dict:
    """End-to-end synthetic smoke; output is forced under /tmp by `write_outputs`."""
    payload = meta_label_payload(synthetic_panel(), market, n_splits=SMOKE_SPLITS)
    payload["mode"] = "smoke"
    payload["synthetic_fixture"] = True
    write_outputs(payload, out_dir)
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="WI-063 L1.5 meta-label driver (Layer 1 only)")
    parser.add_argument("--market", default="CAD", choices=["USD", "CAD"])
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--allow-fixture", action="store_true")
    parser.add_argument("--out", default=None)
    args = parser.parse_args(argv)
    if args.smoke:
        out = Path(args.out) if args.out else SMOKE_DIR
        payload = run_smoke(args.market, out_dir=out)
    else:
        out = Path(args.out) if args.out else OUT_DIR
        payload = run_market(args.market, out_dir=out, max_symbols=args.limit,
                             allow_fixture=args.allow_fixture)
    mode = "smoke" if args.smoke else "full"
    print(f"[wi063.meta] {payload['market']} {mode}: {payload['n_rows']} rows, "
          f"{payload['n_labeled']} labeled, {payload['n_features']} features")
    print(f"[wi063.meta] pooled OOF AUC {_fmt(payload['pooled_oof_auc'])} | scored "
          f"{payload['n_scored']} | primary_oof_used_as_feature="
          f"{payload['primary_oof_used_as_feature']}")
    print(f"[wi063.meta] out -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())