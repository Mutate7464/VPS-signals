"""Fibonacci-window enriched feature panel (WI-015, plan step 3).

Re-builds the **existing normalized feature families** at the admin-confirmed
Fibonacci window grid ``3, 5, 8, 13, 21, 34, 55, 89, 144, 233`` and writes a
market-suffixed Parquet dataset ``data/perfanalytics/features_{market}/``, one
``symbol=<TICKER>.parquet`` per symbol, one symbol at a time.

Families and column names (``<W>`` = fib window; range/Donchian keep the
existing ``f<W>`` naming, `docs/tech_approach/perfanalytics/features-research.md`)
--------------------------------------------------------------------------
    rsi_<W>            Wilder RSI                       (src.feature_engine._rsi)
    bb_pct_b_<W>       position in the 2σ Bollinger band
    bb_width_<W>       band width / SMA
    adx_<W>            Wilder ADX                        (_adx)
    di_spread_<W>      +DI − −DI                          (_adx)
    atr_pct_<W>        Wilder ATR / close                 (src.targets.wilder_atr)
    obv_zscore_<W>     z-score of the OBV slope
    hurst_<W>          rescaled-range Hurst exponent      (_hurst_rs_vec)
    kama_er_<W>        Kaufman efficiency ratio            (_efficiency_ratio)
    vwap_zscore_<W>    close vs rolling VWAP z-score       (_vwap_zscore)
    amihud_<W>         mean |ret| / dollar volume          (_amihud)
    yangzhang_<W>      Yang-Zhang volatility (annualized)  (_yang_zhang_vol)
    range_pos_f<W>     (close − low)/range, 0..1
    range_width_f<W>   range / close
    donchian_break_f<W> 1.0 if close > prior window's high

The indicator bodies come from `src.feature_engine`'s existing helpers wherever
one exists, so this panel cannot drift from the shipped 92-column pool. Only the
window list changes (fib grid instead of the shipped 5/10/20/50/100).

Warm-up policy
    Every value is NaN until the full window is available (the helpers' causal
    ``min_periods=window``); no partial windows are ever emitted. ``hurst_<W>``
    is additionally undefined for ``W < 12`` (the R/S estimator needs >= 2 lags
    at ``window // 4``), so ``hurst_3`` / ``hurst_5`` / ``hurst_8`` are all-NaN
    columns by construction — the "feature absent" case the heatmap blanks.
    Per-symbol
    history is checked before the 144/233 windows: a symbol shorter than the
    window simply gets an all-NaN column, and the coverage counts land in
    ``features_{market}_schema.json`` + ``reports/perfanalytics/features_summary_{market}.md``.

Outputs are float32 immediately after calculation (host rule), symbol-sequential
(never an all-ticker uncompressed frame).

CLI:
    python -m src.perfanalytics.features.panel                    # BOTH, CAD then USD
    python -m src.perfanalytics.features.panel --market USD
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from collections.abc import Iterable, Iterator
from pathlib import Path

import numpy as np
import pandas as pd

from src.feature_engine import (
    _adx,
    _amihud,
    _efficiency_ratio,
    _hurst_rs_vec,
    _rsi,
    _vwap_zscore,
    _yang_zhang_vol,
    iter_market_symbols,
)
from src.market_cli import MarketSelectionError, normalize_market
from src.perfanalytics.markets import BOTH_ORDER, resolve_markets
from src.targets import wilder_atr

BASE_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = BASE_DIR / "data" / "perfanalytics"
REPORTS = BASE_DIR / "reports" / "perfanalytics"

FIB_GRID: tuple[int, ...] = (3, 5, 8, 13, 21, 34, 55, 89, 144, 233)
# `_hurst_rs_vec` needs >= 2 R/S lags, which requires window // 4 >= 3 -> W >= 12.
MIN_HURST_WINDOW = 12

# Family -> builder key. Order fixes column order in the panel and the report.
FAMILIES: tuple[str, ...] = (
    "rsi",
    "bb_pct_b",
    "bb_width",
    "adx",
    "di_spread",
    "atr_pct",
    "obv_zscore",
    "hurst",
    "kama_er",
    "vwap_zscore",
    "amihud",
    "yangzhang",
    "range_pos_f",
    "range_width_f",
    "donchian_break_f",
)

# Families whose column name carries the `f<W>` fib-window convention.
F_PREFIXED = frozenset({"range_pos_f", "range_width_f", "donchian_break_f"})


def feature_columns(windows: tuple[int, ...] = FIB_GRID) -> list[str]:
    """Family-major, window-minor column list for the panel."""
    return [f"{fam}{w}" if fam in F_PREFIXED else f"{fam}_{w}" for fam in FAMILIES for w in windows]


def family_of(column: str) -> str:
    """The family a panel column belongs to (inverse of :func:`feature_columns`)."""
    for fam in FAMILIES:
        if column.startswith(fam + ("_" if fam not in F_PREFIXED else "")):
            return fam
    raise KeyError(column)


def window_of(column: str) -> int:
    """The fib window a panel column was built at."""
    return int(column.rsplit("_", 1)[-1].replace("f", ""))


def compute_fib_features(
    df: pd.DataFrame,
    windows: tuple[int, ...] = FIB_GRID,
    coverage: dict[int, int] | None = None,
) -> pd.DataFrame:
    """The fib-grid feature panel for one symbol's date-sorted OHLCV frame.

    ``coverage`` is updated in place with ``{window: n_symbols_with_enough_history}``
    so the caller can report how many symbols support 144/233.
    """
    close = df["close"].astype("float64")
    high = df["high"].astype("float64")
    low = df["low"].astype("float64")
    n = len(df)

    data: dict[str, np.ndarray] = {}
    obv = (np.sign(close.diff()).fillna(0.0) * df["volume"]).cumsum()
    obv_slope = obv.diff()
    close_arr = close.to_numpy(dtype="float64")

    for w in windows:
        if coverage is not None:
            coverage[w] = coverage.get(w, 0) + int(n >= w)
        # One window at a time, collected into a dict and assembled once: a
        # per-column `df[col] = ...` loop fragments the frame and warns.
        sma = close.rolling(w, min_periods=w).mean()
        std = close.rolling(w, min_periods=w).std(ddof=1)
        upper = sma + 2.0 * std
        lower = sma - 2.0 * std
        adx, di_spread = _adx(df, w)
        m = obv_slope.rolling(w, min_periods=w).mean()
        s = obv_slope.rolling(w, min_periods=w).std(ddof=1)
        hh = high.rolling(w, min_periods=w).max()
        ll = low.rolling(w, min_periods=w).min()
        rng = hh - ll

        data[f"rsi_{w}"] = _rsi(close, w).to_numpy("float32")
        data[f"bb_pct_b_{w}"] = ((close - lower) / (upper - lower + 1e-12)).to_numpy("float32")
        data[f"bb_width_{w}"] = ((upper - lower) / (sma + 1e-12)).to_numpy("float32")
        data[f"adx_{w}"] = adx.to_numpy("float32")
        data[f"di_spread_{w}"] = di_spread.to_numpy("float32")
        data[f"atr_pct_{w}"] = (wilder_atr(df, w) / (close + 1e-12)).to_numpy("float32")
        data[f"obv_zscore_{w}"] = ((obv_slope - m) / (s + 1e-12)).to_numpy("float32")
        data[f"hurst_{w}"] = (
            np.full(n, np.nan, dtype="float32")
            if w < MIN_HURST_WINDOW
            else _hurst_rs_vec(close_arr, w).astype("float32")
        )
        data[f"kama_er_{w}"] = _efficiency_ratio(close, w).to_numpy("float32")
        data[f"vwap_zscore_{w}"] = _vwap_zscore(df, w).to_numpy("float32")
        data[f"amihud_{w}"] = _amihud(df, w).to_numpy("float32")
        data[f"yangzhang_{w}"] = _yang_zhang_vol(df, w).to_numpy("float32")
        data[f"range_pos_f{w}"] = ((close - ll) / (rng + 1e-12)).clip(0.0, 1.0).to_numpy("float32")
        data[f"range_width_f{w}"] = (rng / (close + 1e-12)).to_numpy("float32")
        # Breakout vs the PRIOR window's high: NaN until a prior window exists
        # (no partial-window False flags at the start of the series).
        prior_high = hh.shift(1)
        data[f"donchian_break_f{w}"] = (
            (close > prior_high).astype("float64").where(prior_high.notna()).to_numpy("float32")
        )

    return pd.DataFrame(data, index=df.index)[feature_columns(windows)]


def _default_symbol_iter(market: str, min_date: str | None) -> Iterator[tuple[str, pd.DataFrame]]:
    return iter_market_symbols(market, min_date=min_date, allow_fixture=False)


def dataset_dir(market: str, base: Path | None = None) -> Path:
    """`data/perfanalytics/features_<MARKET>/` (market-suffixed dataset)."""
    root = DATA_DIR if base is None else Path(base)
    return root / f"features_{normalize_market(market)}"


def build_feature_panel(
    market: str,
    out_dir: Path | None = None,
    min_date: str | None = None,
    symbol_iter: Iterable[tuple[str, pd.DataFrame]] | None = None,
    windows: tuple[int, ...] = FIB_GRID,
    reports_dir: Path | None = None,
) -> Path:
    """Write the fib-grid feature dataset for one market; return its directory."""
    code = normalize_market(market)
    out = dataset_dir(code, out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for stale in out.glob("symbol=*.parquet"):
        stale.unlink()

    cols = feature_columns(windows)
    all_cols = ["date", "symbol"] + cols
    src = symbol_iter if symbol_iter is not None else _default_symbol_iter(code, min_date)

    coverage: dict[int, int] = {}
    symbols = 0
    rows = 0
    date_min: pd.Timestamp | None = None
    date_max: pd.Timestamp | None = None
    for symbol, df in src:
        g = df.sort_values("date").reset_index(drop=True)
        if len(g) < min(windows):
            continue
        feats = compute_fib_features(g, windows=windows, coverage=coverage)
        keep = feats.notna().any(axis=1).to_numpy()
        if not keep.any():
            continue
        frame = feats.loc[keep].copy()
        frame.insert(0, "symbol", symbol)
        frame.insert(0, "date", pd.to_datetime(g.loc[keep, "date"]).to_numpy())
        frame = frame[all_cols]
        frame.to_parquet(out / f"symbol={symbol}.parquet", index=False)
        symbols += 1
        rows += len(frame)
        dmin, dmax = frame["date"].min(), frame["date"].max()
        date_min = dmin if date_min is None else min(date_min, dmin)
        date_max = dmax if date_max is None else max(date_max, dmax)

    _write_schema(code, out, windows, symbols, rows, coverage, date_min, date_max)
    _write_summary(code, windows, symbols, rows, coverage, reports_dir)
    return out


def _write_schema(
    market: str,
    out: Path,
    windows: tuple[int, ...],
    symbols: int,
    rows: int,
    coverage: dict[int, int],
    date_min: pd.Timestamp | None,
    date_max: pd.Timestamp | None,
) -> Path:
    cols = feature_columns(windows)
    hunan = {f"hurst_{w}": "undefined for w < 8" for w in windows if w < MIN_HURST_WINDOW}
    schema = {
        "market": market,
        "dataset": _relative_to_base(out),
        "generated_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "fib_grid": list(windows),
        "families": list(FAMILIES),
        "columns": cols,
        "dtypes": {c: "float32" for c in cols},
        "notes": {
            "warmup": "NaN until the full window is available; no partial windows",
            "absent": hunan,
            "range_naming": "range/Donchian columns keep the existing f<W> suffix",
        },
        "rows": rows,
        "symbols": symbols,
        "window_coverage_symbols": {str(w): coverage.get(w, 0) for w in windows},
        "date_min": None if date_min is None else str(date_min.date()),
        "date_max": None if date_max is None else str(date_max.date()),
    }
    path = out.parent / f"{out.name}_schema.json"
    path.write_text(json.dumps(schema, indent=2) + "\n")
    return path


def _write_summary(
    market: str,
    windows: tuple[int, ...],
    symbols: int,
    rows: int,
    coverage: dict[int, int],
    reports_dir: Path | None,
) -> Path:
    """Human-readable panel documentation (schema + warm-up coverage)."""
    root = REPORTS if reports_dir is None else Path(reports_dir)
    root.mkdir(parents=True, exist_ok=True)
    out = root / f"features_summary_{market}.md"
    lines = [
        f"# WI-015 — enriched feature panel ({market})",
        "",
        f"- Generated (UTC): {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        f"- Dataset: `data/perfanalytics/features_{market}/` · {symbols} symbols · {rows:,} rows",
        f"- Fib grid: {', '.join(str(w) for w in windows)} · {len(FAMILIES)} families · "
        f"{len(feature_columns(windows))} columns (all float32)",
        "- Warm-up: NaN until the full window is available; no partial windows.",
        f"- `hurst_<W>` is all-NaN for W < {MIN_HURST_WINDOW} (R/S estimator floor).",
        "",
        "## Family × window columns",
        "",
        "| Family | Columns |",
        "| :--- | :--- |",
    ]
    for fam in FAMILIES:
        cols = [c for c in feature_columns(windows) if family_of(c) == fam]
        lines.append(f"| `{fam}` | {', '.join(f'`{c}`' for c in cols)} |")
    lines += [
        "",
        "## Per-symbol history coverage (symbols with >= W bars)",
        "",
        "| Window | Symbols with full window |",
        "| ---: | ---: |",
    ]
    for w in windows:
        lines.append(f"| {w} | {coverage.get(w, 0)} |")
    out.write_text("\n".join(lines) + "\n")
    return out


def _relative_to_base(path: Path) -> str:
    try:
        return str(path.relative_to(BASE_DIR))
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--market", default=None, metavar="CAD|USD", help="Omit for both (CAD then USD).")
    ap.add_argument("--min-date", default=None, help="Drop bars before this date (YYYY-MM-DD).")
    ap.add_argument("--out-dir", default=None, help="Override the dataset root (default data/perfanalytics).")
    ap.add_argument("--reports-dir", default=None, help="Override the report root (default reports/perfanalytics).")
    args = ap.parse_args(argv)

    try:
        markets = resolve_markets(args.market)
    except MarketSelectionError as exc:
        print(f"[perfanalytics.features] {exc}", file=sys.stderr)
        return 2

    base = Path(args.out_dir) if args.out_dir else None
    reports = Path(args.reports_dir) if args.reports_dir else None
    for market in markets:
        out = build_feature_panel(market, out_dir=base, min_date=args.min_date, reports_dir=reports)
        print(f"[perfanalytics.features] {market}: wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
