#!/usr/bin/env python3
"""Score one market's cross-section and emit a top-N daily shortlist (WI-009/WI-013).

Ordering is consistent across the universe by construction: the model emits one
scalar score per asset, so "A out-ranks B" is just `score(A) > score(B)` and the
order is transitive. Confidence is the pairwise win rate — the fraction of
same-date peers the asset out-scores (computed from ranks; no O(N^2) matrix).

Usage (WI-013: omitted `--market` ranks BOTH, USD then CAD)::

    uv run python scripts/rank_assets.py                    # both markets
    uv run python scripts/rank_assets.py --market CAD --top-n 10
    uv run python scripts/rank_assets.py --market CAD --date 2026-09-22
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

from src.market_cli import add_market_argument, cli_markets, run_markets  # noqa: E402
from src.models.contrastive_ranking import load_model  # noqa: E402
from src.models.pair_sampler import pairwise_win_rate  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FEATURES_DIR = ROOT / "data" / "features"
REPORTS = ROOT / "reports"
MODELS = ROOT / "models"


def paths(market: str, top_n: int = 10) -> dict[str, Path]:
    """Every input/output path this script resolves for one market (WI-013)."""
    return {
        "model": MODELS / f"contrastive_ranker_{market}.pt",
        "features": FEATURES_DIR / f"features_{market}.parquet",
        "shortlist": REPORTS / f"wi009_top{top_n}_{market}.csv",
    }


def build_parser() -> argparse.ArgumentParser:
    """The CLI parser for this entry point (one shared `--market` flag)."""
    ap = argparse.ArgumentParser(description=__doc__)
    add_market_argument(ap)
    ap.add_argument("--top-n", type=int, default=10)
    ap.add_argument("--date", default=None, help="Score this date (default: latest available).")
    ap.add_argument("--model", default=None, help="Model path (default: models/contrastive_ranker_<market>.pt)")
    return ap


def parse_args(argv=None):
    return build_parser().parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    markets = cli_markets(args.market, prog="rank_assets")
    if markets is None:
        return 2
    print(f"[rank] PLAN: markets={', '.join(markets)}")
    return run_markets(markets, lambda m: run_market(m, args))


def run_market(market: str, args) -> int:
    market_paths = paths(market, args.top_n)
    model_path = Path(args.model) if args.model else market_paths["model"]
    if not model_path.exists():
        raise SystemExit(f"missing model {model_path} — train first")

    import pyarrow.dataset as ds

    model, feature_cols = load_model(model_path)
    # Arrow scan, never a full all-ticker read: only the date column is touched to
    # find the latest date, then only that date's rows are materialised.
    dataset = ds.dataset(market_paths["features"], format="parquet")
    if args.date:
        target_date = pd.Timestamp(args.date).normalize()
    else:
        max_date = pd.to_datetime(dataset.to_table(columns=["date"]).column("date").to_pandas()).max()
        target_date = pd.Timestamp(max_date).normalize()

    day = dataset.to_table(filter=ds.field("date") == target_date).to_pandas()
    day["date"] = pd.to_datetime(day["date"]).dt.normalize()
    if day.empty:
        raise SystemExit(f"no rows for {target_date.date()}")

    # Rows with undefined features cannot be scored — drop, and say how many.
    before = len(day)
    day = day.dropna(subset=feature_cols)
    dropped = before - len(day)

    scores = model.score_numpy(day[feature_cols].to_numpy(dtype=np.float32))
    day["score"] = scores
    day["confidence"] = pairwise_win_rate(scores, day["date"].to_numpy())
    day = day.sort_values("score", ascending=False).reset_index(drop=True)
    day["rank"] = np.arange(1, len(day) + 1)

    top = day.head(args.top_n)[["symbol", "score", "confidence", "rank"]]
    REPORTS.mkdir(parents=True, exist_ok=True)
    out = market_paths["shortlist"]
    top.to_csv(out, index=False)

    print(f"[rank] market={market} date={target_date.date()} universe={len(day)} "
          f"(dropped {dropped} rows with undefined features)")
    print(f"[rank] wrote {out}")
    print(top.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())