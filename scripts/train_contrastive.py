#!/usr/bin/env python3
"""Train the WI-009 contrastive ranker on CAD and evaluate in rank space.

Pipeline
--------
1. Read the *rebuilt* CAD feature matrix with an Arrow dataset scan (never a
   full all-ticker uncompressed frame), restricted to a date window.
2. Build the E5 factor + forward-return panel from raw OHLCV
   (`src.factors.e5_baseline.build_e5_panel`) and merge on (date, symbol).
   The forward return is the pairwise label; the E5 factors are the baseline.
3. Split dates by time with a 20-trading-day purge between train and validation.
4. Train with within-date pair batches streamed by `src.models.pair_sampler`.
5. Evaluate **score-based within-date rank-IC** on validation dates and compare
   against each E5 factor on the same rows.

Usage:
    uv run python scripts/train_contrastive.py --market CAD --epochs 2 \
        --max-train-dates 40 --val-dates 10
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

from src.factors.e5_baseline import E5_FACTORS, build_e5_panel  # noqa: E402
from src.models.contrastive_ranking import (  # noqa: E402
    ContrastiveRanker,
    configure_torch,
    ranknet_loss,
    save_model,
)
from src.models.pair_sampler import iter_pair_batches, within_date_rank_ic  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FEATURES_DIR = ROOT / "data" / "features"
REPORTS = ROOT / "reports"
MODELS = ROOT / "models"
EMBARGO_TD = 20


def parse_args():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--market", default="CAD")
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--embed-dim", type=int, default=32)
    ap.add_argument("--batch-pairs", type=int, default=4096)
    ap.add_argument("--pairs-per-date", type=int, default=512)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--val-frac", type=float, default=0.2)
    ap.add_argument("--val-dates", type=int, default=0, help="Force an exact number of validation dates.")
    ap.add_argument("--max-train-dates", type=int, default=0, help="Cap train dates (most recent kept).")
    ap.add_argument("--start-date", default=None)
    ap.add_argument("--end-date", default=None)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--tag", default=None, help="Suffix for output filenames.")
    return ap.parse_args()


def load_features(market: str, start: str | None, end: str | None) -> pd.DataFrame:
    """Arrow-scan the feature matrix, selecting only the date window requested."""
    import pyarrow.dataset as ds

    path = FEATURES_DIR / f"features_{market}.parquet"
    if not path.exists():
        raise SystemExit(f"missing {path} — run Step 0 (feature_engine) first")

    dataset = ds.dataset(path, format="parquet")
    filt = None
    if start is not None:
        filt = ds.field("date") >= pd.Timestamp(start)
    if end is not None:
        end_f = ds.field("date") <= pd.Timestamp(end)
        filt = end_f if filt is None else (filt & end_f)
    tbl = dataset.to_table(filter=filt)
    df = tbl.to_pandas()
    df["date"] = pd.to_datetime(df["date"]).dt.normalize()
    return df


def split_dates(dates: np.ndarray, val_frac: float, val_dates: int) -> tuple[np.ndarray, np.ndarray]:
    """Chronological split with a purge gap so train never abuts validation."""
    uniq = np.sort(pd.unique(dates))
    if len(uniq) < 5:
        raise SystemExit(f"need >=5 dates, got {len(uniq)}")
    n_val = val_dates if val_dates > 0 else max(1, int(round(len(uniq) * val_frac)))
    n_val = min(n_val, len(uniq) - 2)
    val = uniq[-n_val:]
    train_cut = max(1, len(uniq) - n_val - EMBARGO_TD)
    train = uniq[:train_cut]
    return train, val


def main() -> int:
    args = parse_args()
    configure_torch()
    rng = np.random.default_rng(args.seed)
    torch.manual_seed(args.seed)

    tag = args.tag or args.market
    print(f"[train] loading features for {args.market} ...")
    feats = load_features(args.market, args.start_date, args.end_date)
    feature_cols = [c for c in feats.columns if c not in ("date", "symbol", "market")]
    print(f"[train] features: {feats.shape}, {len(feature_cols)} feature columns")
    if len(feature_cols) < 10:
        raise SystemExit(f"only {len(feature_cols)} feature columns — is the feature rebuild done?")

    print("[train] building E5 factor + forward-return panel from raw OHLCV ...")
    e5 = build_e5_panel(args.market)
    # Namespace the E5 factor columns: `amihud_20` also exists in the 89-feature
    # matrix, so a bare merge would silently suffix both to _x/_y.
    e5 = e5.rename(columns={f: f"e5_{f}" for f in E5_FACTORS})
    panel = feats.merge(e5, on=["date", "symbol"], how="inner")
    del feats, e5
    panel = panel.dropna(subset=feature_cols + ["fwd_atr_ret_15"])
    panel = panel.sort_values(["date", "symbol"], kind="stable").reset_index(drop=True)
    print(f"[train] merged panel: {len(panel):,} rows, {panel['date'].nunique()} dates, "
          f"{panel['symbol'].nunique()} symbols")

    train_sel, val_sel = split_dates(panel["date"].to_numpy(), args.val_frac, args.val_dates)
    if args.max_train_dates and len(train_sel) > args.max_train_dates:
        train_sel = train_sel[-args.max_train_dates:]
    print(f"[train] train dates: {len(train_sel)} "
          f"({pd.Timestamp(train_sel[0]).date()} → {pd.Timestamp(train_sel[-1]).date()}) "
          f"| val dates: {len(val_sel)} "
          f"({pd.Timestamp(val_sel[0]).date()} → {pd.Timestamp(val_sel[-1]).date()}) "
          f"| embargo {EMBARGO_TD}td")

    train_panel = panel[panel["date"].isin(set(train_sel))].reset_index(drop=True)
    val_panel = panel[panel["date"].isin(set(val_sel))].reset_index(drop=True)
    if train_panel.empty or val_panel.empty:
        raise SystemExit("empty train or val panel after date split")

    model = ContrastiveRanker(input_dim=len(feature_cols), embed_dim=args.embed_dim)
    n_params = sum(p.numel() for p in model.parameters())
    print(f"[train] model: {len(feature_cols)} -> embed {args.embed_dim}, {n_params:,} params, "
          f"threads={torch.get_num_threads()}")

    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)

    # E5 baseline on the *validation* rows only (same rows the model is scored on).
    baseline = {
        fac: within_date_rank_ic(
            val_panel[f"e5_{fac}"].to_numpy(),
            val_panel["fwd_atr_ret_15"].to_numpy(),
            val_panel["date"].to_numpy(),
        )
        for fac in E5_FACTORS
    }

    epochs_log = []
    best = {"rank_ic": -np.inf, "epoch": -1, "state": None}
    for epoch in range(1, args.epochs + 1):
        model.train()
        losses = []
        n_pairs = 0
        for batch in iter_pair_batches(
            train_panel,
            feature_cols,
            "fwd_atr_ret_15",
            n_pairs_per_date=args.pairs_per_date,
            batch_pairs=args.batch_pairs,
            rng=rng,
        ):
            x_win = torch.from_numpy(batch.x_win)
            x_los = torch.from_numpy(batch.x_los)
            margin = model.pairwise_margin(x_win, x_los)
            loss = ranknet_loss(margin)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            losses.append(float(loss.detach()))
            n_pairs += int(batch.x_win.shape[0])

        # Validation: score the whole cross-section, then within-date rank-IC.
        scores = model.score_numpy(val_panel[feature_cols].to_numpy(dtype=np.float32))
        ic, t, n_d = within_date_rank_ic(scores, val_panel["fwd_atr_ret_15"].to_numpy(), val_panel["date"].to_numpy())

        epochs_log.append(
            {
                "epoch": epoch,
                "loss": float(np.mean(losses)) if losses else None,
                "pairs": n_pairs,
                "rank_ic": None if not np.isfinite(ic) else float(ic),
                "rank_ic_t": None if not np.isfinite(t) else float(t),
                "n_dates": n_d,
            }
        )
        print(f"[train] epoch {epoch}/{args.epochs} loss={epochs_log[-1]['loss']:.4f} "
              f"pairs={n_pairs:,} val_rank_ic={ic:+.4f} t={t:+.2f} dates={n_d}")

        if np.isfinite(ic) and ic > best["rank_ic"]:
            best = {"rank_ic": float(ic), "epoch": epoch,
                    "state": {k: v.clone() for k, v in model.state_dict().items()}}

    if best["state"] is not None:
        model.load_state_dict(best["state"])

    best_fac = max(baseline.items(), key=lambda kv: abs(kv[1][0]) if np.isfinite(kv[1][0]) else -1)
    summary = {
        "market": args.market,
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "config": vars(args),
        "n_features": len(feature_cols),
        "n_rows": int(len(panel)),
        "train_dates": [str(pd.Timestamp(d).date()) for d in train_sel],
        "val_dates": [str(pd.Timestamp(d).date()) for d in val_sel],
        "embargo_td": EMBARGO_TD,
        "epochs": epochs_log,
        "best_epoch": best["epoch"],
        "val_rank_ic": best["rank_ic"] if np.isfinite(best["rank_ic"]) else None,
        "e5_baseline_val": {k: {"mean_ic": (None if not np.isfinite(v[0]) else float(v[0])),
                                "t": (None if not np.isfinite(v[1]) else float(v[1])),
                                "n_dates": v[2]} for k, v in baseline.items()},
        "e5_best_factor": best_fac[0],
        "e5_best_abs_ic": float(abs(best_fac[1][0])) if np.isfinite(best_fac[1][0]) else None,
    }

    REPORTS.mkdir(parents=True, exist_ok=True)
    out_json = REPORTS / f"wi009_train_{tag}.json"
    out_json.write_text(json.dumps(summary, indent=2, default=str) + "\n")

    model_path = save_model(model, MODELS / f"contrastive_ranker_{tag}.pt", feature_cols)
    print(f"[train] wrote {out_json}")
    print(f"[train] wrote {model_path}")
    print(f"[train] val rank-IC {summary['val_rank_ic']} vs best E5 factor "
          f"{summary['e5_best_factor']} |IC|={summary['e5_best_abs_ic']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())