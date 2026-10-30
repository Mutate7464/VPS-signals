"""WI-016 Step 2 — triple-barrier fib-ladder labels (D-016 accepted spec).

Definition (AFML ch. 3, D-016 §1/§3/§4)
---------------------------------------
For every event ``(ticker, t)`` the trade is a *first-touch* outcome, not a
fixed-horizon one:

* profit barrier  ``close_t + k·ATR_t``   → class ``+1``
* stop barrier    ``close_t − k·ATR_t``   → class ``−1``
* vertical barrier ``t + h`` (fib ladder) → class ``sign(realized return)``

Symmetric ``k ∈ {1.5, 2.0}`` (the side is unknown at label time) and the curated
vertical ladder ``h ∈ {8, 21, 55, 144, 233}`` (D-016 Q1: 1:1 with the feature
window grid minus the 3-bar runt). The legacy "stay" target is no longer a
separate label: it is the vertical/neutral outcome.

Causality contract (enforced by ``tests/test_triple_barrier.py``)
----------------------------------------------------------------
* ``ATR_t`` is `src.targets.wilder_atr` — trailing, `<= t` only — so the barrier
  levels never observe the path they are meant to predict.
* Every computed column is `float32` (labels) / `int8` (touch type), NaN where
  the trailing ATR warm-up or the forward ``[t+1 .. t+h]`` window is incomplete.
  The last ``h`` rows of every series are therefore NaN ("horizon tail mask").

CLI::

    python -m src.wi016.triple_barrier --market USD
    python -m src.wi016.triple_barrier --market CAD --allow-fixture --dry-run
"""

from __future__ import annotations

import argparse
import csv
import gc
import json
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view

from src.feature_engine import iter_market_symbols
from src.market_cli import add_market_argument, cli_markets, report_path
from src.targets import ATR_WINDOW, wilder_atr
from src.wi011.stats import fold_blocks

BASE_DIR = Path(__file__).resolve().parents[2]
REPORTS_DIR = BASE_DIR / "reports"

K_VALUES: tuple[float, ...] = (1.5, 2.0)
"""Symmetric barrier ATR multiples (D-016 Q4 — both probed, one ships)."""

VERTICAL_HORIZONS: tuple[int, ...] = (8, 21, 55, 144, 233)
"""Curated fib vertical ladder (D-016 Q1)."""

TOUCH_PROFIT = 1
TOUCH_STOP = -1
TOUCH_VERTICAL = 0
TOUCH_INVALID = -9
"""Sentinel for an undefined event (incomplete ATR warm-up / forward window)."""

__all__ = [
    "ATR_WINDOW",
    "K_VALUES",
    "VERTICAL_HORIZONS",
    "TOUCH_PROFIT",
    "TOUCH_STOP",
    "TOUCH_VERTICAL",
    "TOUCH_INVALID",
    "TripleBarrierAccumulator",
    "barrier_levels",
    "compute_triple_barrier",
    "label_columns",
    "run_market",
]


def _k_tag(k: float) -> str:
    """`1.5` → `k15`, `2.0` → `k20` (stable, dot-free column tags)."""
    return f"k{int(round(k * 10))}"


def label_columns(k_values=K_VALUES, horizons=VERTICAL_HORIZONS) -> list[str]:
    """The label/touch column names produced for a (k, h) grid."""
    cols: list[str] = []
    for k in k_values:
        for h in horizons:
            tag = _k_tag(k)
            cols += [f"tb_label_{tag}_h{h}", f"tb_touch_{tag}_h{h}"]
    for h in horizons:
        cols.append(f"tb_fret_h{h}")
    return cols


def barrier_levels(close: np.ndarray, atr: np.ndarray, k: float) -> tuple[np.ndarray, np.ndarray]:
    """Symmetric barrier levels ``(upper, lower)`` at ``close ± k·ATR``.

    `close`/`atr` are trailing quantities; the returned levels at ``t`` depend
    on data at or before ``t`` only.
    """
    c = np.asarray(close, dtype="float64")
    a = np.asarray(atr, dtype="float64")
    return c + k * a, c - k * a


def _first_touch(hit: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """First ``True`` offset per row of a `(m, h)` boolean hit matrix.

    Returns ``(any_hit, first_offset)`` where `first_offset` is 0-based into the
    forward window (``h + 1`` when nothing registered).
    """
    any_hit = hit.any(axis=1)
    first = np.where(any_hit, hit.argmax(axis=1), hit.shape[1] + 1)
    return any_hit, first


def compute_triple_barrier(
    df: pd.DataFrame,
    k_values=K_VALUES,
    horizons=VERTICAL_HORIZONS,
    atr_window: int = ATR_WINDOW,
) -> pd.DataFrame:
    """Triple-barrier labels for **one symbol** (`df` sorted by date, 0..n-1 index).

    Returns a DataFrame aligned to `df.index` with, per ``(k, h)``:
    ``tb_label_<k>_h<h>`` (float32, ∈ {-1.0, 0.0, +1.0}), ``tb_touch_<k>_h<h>``
    (int8; +1 profit, −1 stop, 0 vertical) and ``tb_fret_h<h>`` (float32 realized
    return over ``[t, t+h]`` used for the vertical sign).
    """
    close = df["close"].astype("float64").to_numpy()
    high = df["high"].astype("float64").to_numpy()
    low = df["low"].astype("float64").to_numpy()
    n = len(close)
    atr = wilder_atr(df, atr_window).astype("float64").to_numpy()

    out: dict[str, np.ndarray] = {}
    # Realized return per horizon is k-independent.
    fret_by_h: dict[int, np.ndarray] = {}
    for h in horizons:
        fret = np.full(n, np.nan)
        if n > h:
            sw_close = sliding_window_view(close, h + 1)[:, 1:]
            fret[: n - h] = (sw_close[:, -1] - close[: n - h]) / (close[: n - h] + 1e-12)
        fret_by_h[h] = fret
        out[f"tb_fret_h{h}"] = fret.astype("float32")

    valid_atr = np.isfinite(atr)

    for k in k_values:
        tag = _k_tag(k)
        upper, lower = barrier_levels(close, atr, k)
        for h in horizons:
            m = max(n - h, 0)
            label = np.full(n, np.nan)
            touch = np.full(n, TOUCH_INVALID, dtype="float64")
            if m > 0:
                fwd_high = sliding_window_view(high, h + 1)[:, 1:]
                fwd_low = sliding_window_view(low, h + 1)[:, 1:]
                up_hit = fwd_high >= upper[:m, None]
                dn_hit = fwd_low <= lower[:m, None]
                prof_any, prof_first = _first_touch(up_hit)
                stop_any, stop_first = _first_touch(dn_hit)

                # Profit only if it strictly precedes the stop; a same-bar tie is
                # resolved pessimistically (stop first).
                profit_first = prof_any & (prof_first < stop_first)
                stop_first_mask = stop_any & ~profit_first
                vert = ~prof_any & ~stop_any

                touch_arr = np.zeros(m, dtype="float64")
                touch_arr[profit_first] = TOUCH_PROFIT
                touch_arr[stop_first_mask] = TOUCH_STOP

                lab = np.where(profit_first, 1.0, np.where(stop_first_mask, -1.0, np.nan))
                fret_m = fret_by_h[h][:m]
                lab = np.where(vert, np.sign(fret_m), lab)

                ok = valid_atr[:m] & np.isfinite(close[:m])
                label[:m] = np.where(ok, lab, np.nan)
                touch[:m] = np.where(ok, touch_arr, TOUCH_INVALID)
            out[f"tb_label_{tag}_h{h}"] = label.astype("float32")
            out[f"tb_touch_{tag}_h{h}"] = touch.astype("int8")

    res = pd.DataFrame(out, index=df.index)
    return res


# --------------------------------------------------------------------------- #
# Diagnostics accumulator / report
# --------------------------------------------------------------------------- #
@dataclass
class TripleBarrierAccumulator:
    """Streaming per-(k,h) density / class-balance / event-by-date counters.

    Holds only counters — never a full panel — so a market can be processed
    symbol-by-symbol on the 8 GB / no-swap host.
    """

    k_values: tuple[float, ...] = K_VALUES
    horizons: tuple[int, ...] = VERTICAL_HORIZONS
    n_symbols: int = 0
    n_rows: int = 0
    touch_counts: dict[tuple[float, int], dict[str, int]] = field(default_factory=dict)
    label_counts: dict[tuple[float, int], dict[int, int]] = field(default_factory=dict)
    events_by_date: dict[int, Counter] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in self.k_values:
            for h in self.horizons:
                self.touch_counts[(k, h)] = {"profit": 0, "stop": 0, "vertical": 0}
                self.label_counts[(k, h)] = {1: 0, -1: 0, 0: 0}
                self.events_by_date[h] = Counter()

    def add_symbol(self, labels: pd.DataFrame, dates: pd.Series) -> None:
        """Accumulate one symbol's label frame (`dates` aligns to `labels`)."""
        self.n_symbols += 1
        self.n_rows += int(len(labels))
        d = pd.to_datetime(pd.Series(dates)).to_numpy()
        for k in self.k_values:
            tag = _k_tag(k)
            for h in self.horizons:
                lab = labels[f"tb_label_{tag}_h{h}"].to_numpy(dtype="float64")
                touch = labels[f"tb_touch_{tag}_h{h}"].to_numpy(dtype="float64")
                defined = np.isfinite(lab)
                self.events_by_date[h].update(d[defined])
                tc = self.touch_counts[(k, h)]
                for name, val in (("profit", TOUCH_PROFIT), ("stop", TOUCH_STOP), ("vertical", TOUCH_VERTICAL)):
                    tc[name] += int((touch[defined] == val).sum())
                lc = self.label_counts[(k, h)]
                for val in (1, -1, 0):
                    lc[val] += int((lab[defined] == val).sum())

    def summary(self) -> dict:
        """Density, class balance and events-per-fold per (k, h)."""
        all_dates = sorted({d for per_h in self.events_by_date.values() for d in per_h})
        uniq = np.array(all_dates, dtype="datetime64[ns]") if all_dates else np.array([], dtype="datetime64[ns]")
        rows: list[dict] = []
        for k in self.k_values:
            for h in self.horizons:
                tc = self.touch_counts[(k, h)]
                lc = self.label_counts[(k, h)]
                n_ev = sum(tc.values())
                folds = fold_blocks(uniq, horizon=h) if uniq.size else []
                per_fold = []
                for f in folds:
                    lo = np.datetime64(f["val_min"])
                    hi = np.datetime64(f["val_max"])
                    cnt = sum(v for date, v in self.events_by_date[h].items() if lo <= np.datetime64(date) <= hi)
                    per_fold.append({"fold": f["fold"], "embargo_td": f["embargo_td"], "events": int(cnt)})
                rows.append(
                    {
                        "k": k,
                        "h": h,
                        "n_events": n_ev,
                        "profit": tc["profit"],
                        "stop": tc["stop"],
                        "vertical": tc["vertical"],
                        "profit_density": tc["profit"] / n_ev if n_ev else float("nan"),
                        "stop_density": tc["stop"] / n_ev if n_ev else float("nan"),
                        "vertical_density": tc["vertical"] / n_ev if n_ev else float("nan"),
                        "class_plus": lc[1],
                        "class_minus": lc[-1],
                        "class_neutral": lc[0],
                        "folds": per_fold,
                    }
                )
        return {"n_symbols": self.n_symbols, "n_rows": self.n_rows, "grid": rows}


def _write_report(summary: dict, market: str, out_dir: Path = REPORTS_DIR) -> tuple[Path, Path]:
    """Write `reports/wi016_label_density_{market}.{md,csv}`; return both paths."""
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = report_path(out_dir, "wi016_label_density", market)
    csv_path = md_path.with_suffix(".csv")

    with open(csv_path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["k", "h", "n_events", "profit", "stop", "vertical",
                    "profit_density", "stop_density", "vertical_density",
                    "class_plus", "class_minus", "class_neutral", "folds"])
        for r in summary["grid"]:
            w.writerow([
                r["k"], r["h"], r["n_events"], r["profit"], r["stop"], r["vertical"],
                f"{r['profit_density']:.4f}", f"{r['stop_density']:.4f}", f"{r['vertical_density']:.4f}",
                r["class_plus"], r["class_minus"], r["class_neutral"],
                json.dumps(r["folds"]),
            ])

    lines = [
        f"# WI-016 triple-barrier label density — {market}",
        "",
        f"- Symbols processed: {summary['n_symbols']}",
        f"- Rows seen: {summary['n_rows']}",
        f"- k values: {list(K_VALUES)} · vertical ladder: {list(VERTICAL_HORIZONS)}",
        "- Touch density is the share of defined events whose *first touch* was that barrier.",
        "",
        "| k | h | events | profit | stop | vertical | profit_density | stop_density | vertical_density | +1 | -1 | 0 |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in summary["grid"]:
        lines.append(
            f"| {r['k']} | {r['h']} | {r['n_events']} | {r['profit']} | {r['stop']} | {r['vertical']} | "
            f"{r['profit_density']:.3f} | {r['stop_density']:.3f} | {r['vertical_density']:.3f} | "
            f"{r['class_plus']} | {r['class_minus']} | {r['class_neutral']} |"
        )
    lines += ["", "## Events per purged fold (`embargo_td = max(20, horizon)`)", ""]
    for r in summary["grid"]:
        folds = ", ".join(f"f{f['fold']}={f['events']}" for f in r["folds"]) or "n/a"
        lines.append(f"- k={r['k']}, h={r['h']}: {folds}")
    md_path.write_text("\n".join(lines) + "\n")
    return md_path, csv_path


def run_market(
    market: str,
    k_values=K_VALUES,
    horizons=VERTICAL_HORIZONS,
    allow_fixture: bool = False,
    min_date: str | None = None,
    dry_run: bool = False,
) -> dict:
    """Stream one market's symbols through the labeler and write the density report."""
    acc = TripleBarrierAccumulator(k_values=tuple(k_values), horizons=tuple(horizons))
    for i, (_symbol, raw) in enumerate(iter_market_symbols(market, min_date=min_date, allow_fixture=allow_fixture)):
        g = raw.sort_values("date").reset_index(drop=True)
        labels = compute_triple_barrier(g, k_values=k_values, horizons=horizons)
        acc.add_symbol(labels, g["date"])
        del g, labels
        if (i + 1) % 50 == 0:
            gc.collect()
    summary = acc.summary()
    summary["market"] = market
    if not dry_run:
        md_path, csv_path = _write_report(summary, market)
        summary["report_md"] = str(md_path)
        summary["report_csv"] = str(csv_path)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="WI-016 triple-barrier fib-ladder labels")
    add_market_argument(parser)
    parser.add_argument("--allow-fixture", action="store_true")
    parser.add_argument("--min-date", default=None, help="Earliest date (YYYY-MM-DD)")
    parser.add_argument("--dry-run", action="store_true", help="Compute but write no report")
    args = parser.parse_args(argv)

    markets = cli_markets(args.market, prog="wi016.triple_barrier")
    if markets is None:
        return 2
    for mkt in markets:
        summary = run_market(
            mkt, allow_fixture=args.allow_fixture, min_date=args.min_date, dry_run=args.dry_run
        )
        print(f"[wi016.triple_barrier] {mkt}: {summary['n_symbols']} symbols, {summary['n_rows']} rows")
        if "report_md" in summary:
            print(f"[wi016.triple_barrier] {mkt}: report -> {summary['report_md']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
