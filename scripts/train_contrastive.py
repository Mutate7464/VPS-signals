#!/usr/bin/env python3
"""Train the WI-009 contrastive ranker on CAD and evaluate in rank space.

Pipeline
--------
1. Read the *rebuilt* CAD feature matrix with a slimmed Arrow dataset scan
   (never a full all-ticker uncompressed frame), restricted to a date window.
   The keep list is built by `src.models.training_data.keep_columns`, which
   refuses to drop any derived feature family (the E3 slim-mask bug class).
2. Build the E5 factor + forward-return panel from raw OHLCV
   (`src.factors.e5_baseline.build_e5_panel`) and merge on (date, symbol).
   The forward return is the pairwise label; the E5 factors are the baseline.
3. Split dates by time with a 20-trading-day purge between train and validation
   (`src.models.skill_bar.purged_date_split`).
4. Train with within-date pair batches streamed by `src.models.pair_sampler`,
   early-stopping on **val within-date rank-IC** (not on loss).
5. Evaluate **score-based within-date rank-IC** on the validation dates and
   compare against each E5 factor on the same rows, then test the explicit
   WI-009b skill bar (clause a: beat the best factor; clause b: |t| > 2 with a
   stable sign across >= 2 disjoint sub-windows) and write both reports.

Usage (WI-009b — full history, widened window):
    uv run python scripts/train_contrastive.py --market CAD --val-dates 60 \
        --epochs 12 --early-stop-patience 3 --report-prefix wi009b --tag wi009b

Usage (WI-009 pilot reproduction):
    uv run python scripts/train_contrastive.py --market CAD --epochs 2 \
        --max-train-dates 40 --val-dates 10
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

from src.factors.e5_baseline import E5_FACTORS, build_e5_panel  # noqa: E402
from src.market_cli import (  # noqa: E402
    add_market_argument,
    cli_markets,
    report_path,
    run_markets,
)
from src.models.contrastive_ranking import (  # noqa: E402
    ContrastiveRanker,
    configure_torch,
    ranknet_loss,
    save_model,
)
from src.models.pair_sampler import iter_pair_batches, within_date_rank_ic  # noqa: E402
from src.models.skill_bar import (  # noqa: E402
    EMBARGO_TD,
    factor_ics_from_panel,
    purged_date_split,
    skill_bar_verdict,
    stats_for_rows,
    sub_window_split,
    write_comparison_report,
)
from src.models.training_data import load_feature_panel  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
MODELS = ROOT / "models"

MODEL_SCORE_COL = "model_score"


def paths(market: str, prefix: str = "wi009", tag: str | None = None) -> dict[str, Path]:
    """Every output path this script resolves for one market (WI-013).

    The report/JSON paths were already market-suffixed under WI-009b; WI-013 adds
    the explicit contract (and the model filename, which follows `tag`).
    """
    tag = tag or market
    return {
        "train_json": report_path(REPORTS, f"{prefix}_train", market, suffix=".json"),
        "comparison_md": report_path(REPORTS, f"{prefix}_e5_vs_model", market),
        "model": MODELS / f"contrastive_ranker_{tag}.pt",
    }


def build_parser() -> argparse.ArgumentParser:
    """The CLI parser for this entry point (one shared `--market` flag)."""
    ap = argparse.ArgumentParser(description=__doc__)
    add_market_argument(ap)
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--embed-dim", type=int, default=32)
    ap.add_argument("--batch-pairs", type=int, default=4096)
    ap.add_argument("--pairs-per-date", type=int, default=512)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--val-frac", type=float, default=0.2)
    ap.add_argument("--val-dates", type=int, default=0, help="Force an exact number of validation dates.")
    ap.add_argument("--max-train-dates", type=int, default=0, help="Cap train dates (most recent kept).")
    ap.add_argument("--early-stop-patience", type=int, default=0,
                    help="Stop after N epochs without a val rank-IC improvement (0 = off).")
    ap.add_argument("--grad-clip", type=float, default=0.0,
                    help="Clip the gradient norm (0 = off). Stability guard on unscaled inputs.")
    ap.add_argument("--standardize", action="store_true",
                    help="Fit the winsorise+standardise input transform on TRAIN rows only "
                         "(stored in the model; off = WI-009 raw-feature behaviour).")
    ap.add_argument("--sub-windows", type=int, default=2,
                    help="Disjoint contiguous blocks of the val window for the clause-(b) guard.")
    ap.add_argument("--start-date", default=None)
    ap.add_argument("--end-date", default=None)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--report-prefix", default="wi009", help="Report filename prefix.")
    ap.add_argument("--tag", default=None, help="Suffix for the saved model filename (default: market).")
    return ap


def parse_args(argv=None):
    return build_parser().parse_args(argv)


def split_dates_frac(dates: np.ndarray, val_frac: float, val_dates: int) -> tuple[np.ndarray, np.ndarray, int]:
    """Legacy fraction-based split (kept for WI-009 pilot reproduction)."""
    uniq = np.sort(pd.unique(dates))
    if len(uniq) < 5:
        raise SystemExit(f"need >=5 dates, got {len(uniq)}")
    n_val = val_dates if val_dates > 0 else max(1, int(round(len(uniq) * val_frac)))
    n_val = min(n_val, len(uniq) - 2)
    val = uniq[-n_val:]
    train_cut = max(1, len(uniq) - n_val - EMBARGO_TD)
    train = uniq[:train_cut]
    return train, val, EMBARGO_TD


def evaluate(model: ContrastiveRanker, panel: pd.DataFrame, feature_cols: list[str]) -> tuple[np.ndarray, float, float, int]:
    """Score a panel and return (scores, mean within-date rank-IC, t, n_dates)."""
    scores = model.score_numpy(panel[feature_cols].to_numpy(dtype=np.float32))
    ic, t, n_d = within_date_rank_ic(
        scores, panel["fwd_atr_ret_15"].to_numpy(), panel["date"].to_numpy()
    )
    return scores, ic, t, n_d


def main(argv=None) -> int:
    args = parse_args(argv)
    markets = cli_markets(args.market, prog="train_contrastive")
    if markets is None:
        return 2
    print(f"[train] PLAN: markets={', '.join(markets)}")
    return run_markets(markets, lambda m: run_market(m, args))


def run_market(market: str, args) -> int:
    configure_torch()
    rng = np.random.default_rng(args.seed)
    torch.manual_seed(args.seed)
    t_start = time.time()

    prefix = args.report_prefix
    tag = args.tag or market

    print(f"[train] STEP panel: START")
    print(f"[train] loading features for {market} (slim Arrow scan) ...")
    feats_df, feature_cols, census = load_feature_panel(market, args.start_date, args.end_date)
    print(f"[train] features: {feats_df.shape}, {len(feature_cols)} feature columns, "
          f"census={census}")
    if len(feature_cols) < 10:
        raise SystemExit(f"only {len(feature_cols)} feature columns — is the feature rebuild done?")

    print("[train] building E5 factor + forward-return panel from raw OHLCV ...")
    e5 = build_e5_panel(market)
    # Namespace the E5 factor columns: `amihud_20` also exists in the 89-feature
    # matrix, so a bare merge would silently suffix both to _x/_y.
    e5 = e5.rename(columns={f: f"e5_{f}" for f in E5_FACTORS})
    panel = feats_df.merge(e5, on=["date", "symbol"], how="inner")
    del feats_df, e5
    panel = panel.dropna(subset=feature_cols + ["fwd_atr_ret_15"])
    panel = panel.sort_values(["date", "symbol"], kind="stable").reset_index(drop=True)
    n_symbols = int(panel["symbol"].nunique())
    print(f"[train] merged panel: {len(panel):,} rows, {panel['date'].nunique()} dates, "
          f"{n_symbols} symbols, rss={_rss_mb():.0f}MB")
    print(f"[train] STEP panel: END")

    if args.val_dates > 0:
        train_sel, val_sel, purge_gap = purged_date_split(
            panel["date"].to_numpy(), args.val_dates, EMBARGO_TD
        )
    else:
        train_sel, val_sel, purge_gap = split_dates_frac(
            panel["date"].to_numpy(), args.val_frac, args.val_dates
        )
    if args.max_train_dates and len(train_sel) > args.max_train_dates:
        train_sel = train_sel[-args.max_train_dates:]
    print(f"[train] train dates: {len(train_sel)} "
          f"({pd.Timestamp(train_sel[0]).date()} → {pd.Timestamp(train_sel[-1]).date()}) "
          f"| val dates: {len(val_sel)} "
          f"({pd.Timestamp(val_sel[0]).date()} → {pd.Timestamp(val_sel[-1]).date()}) "
          f"| purge gap {purge_gap}td")

    train_panel = panel[panel["date"].isin(set(train_sel))].reset_index(drop=True)
    val_panel = panel[panel["date"].isin(set(val_sel))].reset_index(drop=True)
    if train_panel.empty or val_panel.empty:
        raise SystemExit("empty train or val panel after date split")

    model = ContrastiveRanker(input_dim=len(feature_cols), embed_dim=args.embed_dim)
    n_params = sum(p.numel() for p in model.parameters())
    print(f"[train] model: {len(feature_cols)} -> embed {args.embed_dim}, {n_params:,} params, "
          f"threads={torch.get_num_threads()}")

    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)

    # Input transform: fitted on TRAIN rows only (never val) — leak-free, and
    # stored in the model blob so inference stays consistent with training.
    transform = None
    if args.standardize:
        transform = model.fit_input_transform(
            train_panel[feature_cols].to_numpy(dtype=np.float32)
        )
        print(f"[train] input transform (train-fold only): winsorise q{transform['lo_q']:.2f}/"
              f"q{transform['hi_q']:.2f} + standardise; rows={transform['n_rows']:,}, "
              f"clipped values={transform['n_clipped_values']:,}")
    else:
        print("[train] input transform: none (raw features, WI-009 behaviour)")

    # E5 factor baseline on the *validation* rows only (same rows the model is
    # scored on) — this is the number the skill bar's clause (a) compares against.
    factor_stats = factor_ics_from_panel(val_panel)
    print("[train] E5 baseline on the val window: "
          + ", ".join(f"{k} {v[0]:+.4f} (t {v[1]:+.2f})" for k, v in factor_stats.items()))

    epochs_log = []
    # Skill-bar clause (a) evaluates |IC|, so early stopping must select on |IC|
    # too (WI-009b reviewer F1): raw-IC selection picks the epoch closest to zero
    # when the model is consistently anti-correlated. Init 0.0 = "any epoch with
    # nonzero signal beats nothing"; |IC|-compare handles both signs.
    best = {"rank_ic": 0.0, "epoch": -1, "t": float("nan"), "state": None}
    stale = 0
    early_stopped = False

    print(f"[train] STEP training: START (epochs={args.epochs}, patience={args.early_stop_patience})")
    for epoch in range(1, args.epochs + 1):
        t_ep = time.time()
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
            if args.grad_clip > 0:
                torch.nn.utils.clip_grad_norm_(model.parameters(), args.grad_clip)
            optimizer.step()
            losses.append(float(loss.detach()))
            n_pairs += int(batch.x_win.shape[0])

        # Validation: score the whole cross-section, then within-date rank-IC.
        _, ic, t, n_d = evaluate(model, val_panel, feature_cols)
        secs = time.time() - t_ep

        epochs_log.append(
            {
                "epoch": epoch,
                "loss": float(np.mean(losses)) if losses else None,
                "pairs": n_pairs,
                "rank_ic": None if not np.isfinite(ic) else float(ic),
                "rank_ic_t": None if not np.isfinite(t) else float(t),
                "n_dates": n_d,
                "secs": round(secs, 1),
            }
        )
        print(f"[train] epoch {epoch}/{args.epochs} loss={epochs_log[-1]['loss']:.4f} "
              f"pairs={n_pairs:,} val_rank_ic={ic:+.4f} t={t:+.2f} dates={n_d} "
              f"secs={secs:.0f} rss={_rss_mb():.0f}MB", flush=True)

        if np.isfinite(ic) and abs(ic) > abs(best["rank_ic"]):
            best = {"rank_ic": float(ic), "epoch": epoch, "t": float(t),
                    "state": {k: v.clone() for k, v in model.state_dict().items()}}
            stale = 0
        else:
            stale += 1
            if args.early_stop_patience and stale >= args.early_stop_patience:
                early_stopped = True
                print(f"[train] early stop: no val rank-IC improvement for {stale} epochs "
                      f"(best epoch {best['epoch']})", flush=True)
                break

    if best["state"] is not None:
        model.load_state_dict(best["state"])
    print(f"[train] STEP training: END (best epoch {best['epoch']}, early_stopped={early_stopped})")

    # ---- final evaluation of the selected model (post-restore) -------------- #
    print("[train] STEP eval: START")
    scores, model_ic, model_t, model_n = evaluate(model, val_panel, feature_cols)
    val_scored = val_panel.assign(**{MODEL_SCORE_COL: scores})
    if np.isfinite(model_ic) and abs(model_ic - best["rank_ic"]) > 1e-9:
        print(f"[train] WARN: restored-model IC {model_ic:+.4f} != best-epoch IC "
              f"{best['rank_ic']:+.4f} (unexpected)")

    blocks = sub_window_split(val_sel, n_windows=args.sub_windows) if args.sub_windows >= 2 else []
    sub_windows = []
    sub_window_best_factor = {}
    for i, block in enumerate(blocks, start=1):
        sub = val_scored[val_scored["date"].isin(set(block))]
        ic, t, n = stats_for_rows(sub, MODEL_SCORE_COL)
        fstats = factor_ics_from_panel(sub)
        fname = max(fstats.items(), key=lambda kv: abs(kv[1][0]))[0]
        sub_windows.append(
            {
                "window": i,
                "dates": [str(pd.Timestamp(d).date()) for d in block],
                "n_dates": n,
                "rank_ic": None if not np.isfinite(ic) else float(ic),
                "rank_ic_t": None if not np.isfinite(t) else float(t),
                "factors": {k: {"mean_ic": float(v[0]), "t": float(v[1]), "n_dates": int(v[2])}
                            for k, v in fstats.items()},
                "best_factor": fname,
                "best_factor_abs_ic": float(abs(fstats[fname][0])),
            }
        )
        sub_window_best_factor[i] = {"name": fname, "abs_ic": float(abs(fstats[fname][0]))}
        print(f"[train] sub-window {i}: {n} dates, model IC {ic:+.4f} t {t:+.2f} | "
              f"best factor {fname} |IC| {abs(fstats[fname][0]):.4f}")

    verdict = skill_bar_verdict(
        model_ic=model_ic,
        model_t=model_t,
        factor_stats=factor_stats,
        sub_stats=[(w["rank_ic"], w["rank_ic_t"], w["n_dates"]) for w in sub_windows],
    )
    print(f"[train] SKILL BAR: {'PASS' if verdict['passed'] else 'FAIL'} | "
          f"clause a {'PASS' if verdict['clause_a']['passed'] else 'FAIL'} "
          f"(model |IC| {abs(model_ic):.4f} vs {verdict['clause_a']['best_factor']} "
          f"|IC| {verdict['clause_a']['best_factor_abs_ic']:.4f}) | "
          f"clause b {'PASS' if verdict['clause_b']['passed'] else 'FAIL'} "
          f"(t {model_t:+.2f})")
    print("[train] STEP eval: END")

    train_minutes = (time.time() - t_start) / 60.0
    last_epoch = epochs_log[-1] if epochs_log else {}
    best_fac = verdict["clause_a"]["best_factor"]
    summary = {
        "market": market,
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "config": vars(args),
        "n_features": len(feature_cols),
        "feature_census": census,
        "input_transform": transform,
        "n_rows": int(len(panel)),
        "n_symbols": n_symbols,
        "train_dates": [str(pd.Timestamp(d).date()) for d in train_sel],
        "val_dates": [str(pd.Timestamp(d).date()) for d in val_sel],
        "embargo_td": EMBARGO_TD,
        "purge_gap_td": purge_gap,
        "epochs_run": len(epochs_log),
        "early_stopped": early_stopped,
        "patience": args.early_stop_patience,
        "train_seconds": round(train_minutes * 60.0, 1),
        "epochs": epochs_log,
        "best_epoch": best["epoch"],
        "val_rank_ic": None if not np.isfinite(model_ic) else float(model_ic),
        "val_rank_ic_t": None if not np.isfinite(model_t) else float(model_t),
        "final_epoch_ic": last_epoch.get("rank_ic"),
        "final_epoch_t": last_epoch.get("rank_ic_t"),
        "e5_baseline_val": {k: {"mean_ic": (None if not np.isfinite(v[0]) else float(v[0])),
                                "t": (None if not np.isfinite(v[1]) else float(v[1])),
                                "n_dates": v[2]} for k, v in factor_stats.items()},
        "e5_best_factor": best_fac,
        "e5_best_abs_ic": verdict["clause_a"]["best_factor_abs_ic"],
        "sub_windows": sub_windows,
        "skill_bar": verdict,
        "model_path": None,
        "report_path": None,
    }

    # ---- reports ----------------------------------------------------------- #
    print("[train] STEP report: START")
    REPORTS.mkdir(parents=True, exist_ok=True)
    market_paths = paths(market, prefix, tag)
    out_json = market_paths["train_json"]
    out_md = market_paths["comparison_md"]
    model_path = save_model(model, market_paths["model"], feature_cols)

    write_comparison_report(
        out_md,
        {
            "market": market,
            "generated_utc": summary["generated_utc"],
            "n_rows": len(panel),
            "n_features": len(feature_cols),
            "n_symbols": n_symbols,
            "val_dates": summary["val_dates"],
            "val_start": summary["val_dates"][0],
            "val_end": summary["val_dates"][-1],
            "embargo_td": EMBARGO_TD,
            "n_train_dates": len(train_sel),
            "train_start": summary["train_dates"][0],
            "train_end": summary["train_dates"][-1],
            "epochs_run": len(epochs_log),
            "patience": args.early_stop_patience,
            "early_stopped": early_stopped,
            "train_minutes": train_minutes,
            "best_epoch": best["epoch"],
            "model_ic": summary["val_rank_ic"],
            "model_t": summary["val_rank_ic_t"],
            "final_epoch_ic": summary["final_epoch_ic"],
            "final_epoch_t": summary["final_epoch_t"],
            "skill_bar": verdict,
            "sub_window_best_factor": sub_window_best_factor,
        },
    )
    summary["model_path"] = str(model_path)
    summary["report_path"] = str(out_md)
    out_json.write_text(json.dumps(summary, indent=2, default=str) + "\n")
    print(f"[train] wrote {out_json}")
    print(f"[train] wrote {out_md}")
    print(f"[train] wrote {model_path}")
    print(f"[train] STEP report: END")
    print(f"[train] val rank-IC {summary['val_rank_ic']} (t {summary['val_rank_ic_t']}) vs best E5 factor "
          f"{summary['e5_best_factor']} |IC|={summary['e5_best_abs_ic']} on {len(val_sel)} val dates")
    print(f"[train] elapsed {train_minutes:.1f} min")
    return 0


def _rss_mb() -> float:
    """Peak/current RSS read from /proc — cheap host-budget telemetry."""
    try:
        with open("/proc/self/status") as fh:
            for line in fh:
                if line.startswith("VmRSS:"):
                    return float(line.split()[1]) / 1024.0
    except OSError:
        pass
    return float("nan")


if __name__ == "__main__":
    raise SystemExit(main())