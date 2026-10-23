"""Sprint 5 — PDF tearsheet compiler (4-panel annotated charts).

Builds `reports/screener_{USD|CAD}_YYYYMMDD.pdf` with three sections:

  Section 1 — Portfolio Defense: `config/holdings.csv` ranked by
              `Exit_Urgency = max(P_15d_High, P_20d_Down)` descending.
  Section 2 — Buy-Side Bottom Inflections: top-N by `P_15d_Low`.
  Section 3 — Buy-Side Upward Momentum:     top-N by `P_20d_Up`.

Per ticker, a 4-panel page:
  Panel 1 (main): 120-day OHLC candlesticks + 20d Bollinger Bands + peak/trough
                  triangle markers + 20d OLS trend channel.
  Panel 2: volume bars (colored by close direction) + 20d SMA volume.
  Panel 3: 14-day RSI with 30/70 levels.
  Panel 4: #1 SHAP driver indicator + 60d mean / +-2std bands + callout box of
           all 4 probabilities and top-3 SHAP contributions.

Memory guardrail (CB-06): figures are rendered and closed immediately, with
`gc.collect()` every `BATCH_GC_SIZE` pages, keeping VPS RSS well under 4.2 GB.

CLI:
    python -m src.pdf_compiler --market USD --top-n 2    # smoke test
    python -m src.pdf_compiler --market ALL --top-n 30
"""

from __future__ import annotations

import argparse
import datetime as dt
import gc
import sys
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless vector backend — no display needed

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages
from scipy.signal import argrelextrema

from src.feature_engine import (
    _adx,
    _amihud,
    _efficiency_ratio,
    _frac_diff_fixed,
    _hurst_rs,
    _kalman_filter,
    _rsi,
    _shannon_entropy,
    _vwap_zscore,
    _yang_zhang_vol,
    wilder_atr,
)
from src.state_manager import init_dirs, log_telemetry, update_state

BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw_ohlcv"
FIXTURE_DIR = BASE_DIR / "data" / "raw_ohlcv_test"
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"
CONFIG_DIR = BASE_DIR / "config"
PDF_BLOCK_FLAG = BASE_DIR / "state" / "PDF_BLOCKED"

CHART_LOOKBACK = 120
BATCH_GC_SIZE = 10
UP_COLOR = "#26a69a"
DOWN_COLOR = "#ef5350"

PROB = {
    "p_15d_high": "P_15d_High",
    "p_15d_low": "P_15d_Low",
    "p_20d_up": "P_20d_Up",
    "p_20d_down": "P_20d_Down",
}


# --------------------------------------------------------------------------- #
# Data loading
# --------------------------------------------------------------------------- #
def load_raw(market: str, symbol: str) -> pd.DataFrame | None:
    for root in (RAW_DIR, FIXTURE_DIR):
        p = root / f"market={market}" / f"symbol={symbol}.parquet"
        if p.exists():
            df = pd.read_parquet(p).sort_values("date").tail(CHART_LOOKBACK).reset_index(drop=True)
            for c in ("open", "high", "low", "close", "volume"):
                df[c] = df[c].astype("float64")
            return df
    return None


def load_predictions(market: str) -> pd.DataFrame:
    return pd.read_parquet(DATA_DIR / f"predictions_{market}_latest.parquet")


def load_holdings() -> pd.DataFrame:
    p = CONFIG_DIR / "holdings.csv"
    if not p.exists():
        return pd.DataFrame()
    return pd.read_csv(p)


# --------------------------------------------------------------------------- #
# Feature recomputation for Panel 4 (top SHAP driver)
# --------------------------------------------------------------------------- #
def _bb_pct_b(df: pd.DataFrame, w: int) -> pd.Series:
    c = df["close"].astype("float64")
    sma = c.rolling(w, min_periods=w).mean()
    std = c.rolling(w, min_periods=w).std(ddof=1)
    return (c - (sma - 2 * std)) / (4 * std + 1e-12)


def _bb_width(df: pd.DataFrame, w: int) -> pd.Series:
    c = df["close"].astype("float64")
    sma = c.rolling(w, min_periods=w).mean()
    std = c.rolling(w, min_periods=w).std(ddof=1)
    return (4 * std) / (sma + 1e-12)


def _obv_zscore(df: pd.DataFrame, w: int) -> pd.Series:
    c = df["close"].astype("float64")
    obv = (np.sign(c.diff()).fillna(0.0) * df["volume"]).cumsum()
    slope = obv.diff()
    m = slope.rolling(w, min_periods=w).mean()
    s = slope.rolling(w, min_periods=w).std(ddof=1)
    return (slope - m) / (s + 1e-12)


def compute_feature_series(df: pd.DataFrame, name: str) -> pd.Series | None:
    """Recompute a (raw) feature series from OHLCV for the top SHAP driver panel."""
    base = name[:-7] if name.endswith("_cs_pct") else name  # strip cross-sectional suffix
    close = df["close"].astype("float64")
    atr20 = wilder_atr(df).astype("float64")

    if base.startswith("rsi_") and base.endswith("_slope_5"):
        return None
    if base.startswith("rsi_"):
        return _rsi(close, int(base.split("_")[1]))
    if base.startswith("bb_pct_b_"):
        return _bb_pct_b(df, int(base.split("_")[-1]))
    if base.startswith("bb_width_"):
        return _bb_width(df, int(base.split("_")[-1]))
    if base.startswith("adx_"):
        adx, _ = _adx(df, int(base.split("_")[1]))
        return adx
    if base.startswith("di_spread_"):
        _, di = _adx(df, int(base.split("_")[-1]))
        return di
    if base.startswith("atr_pct_"):
        return wilder_atr(df, int(base.split("_")[-1])) / (close + 1e-12)
    if base.startswith("obv_zscore_"):
        return _obv_zscore(df, int(base.split("_")[-1]))
    if base.startswith("hurst_"):
        return close.rolling(int(base.split("_")[1]), min_periods=int(base.split("_")[1])).apply(_hurst_rs, raw=True)
    if base.startswith("entropy_"):
        return close.rolling(int(base.split("_")[1]), min_periods=int(base.split("_")[1])).apply(_shannon_entropy, raw=True)
    if base.startswith("kama_er_"):
        return _efficiency_ratio(close, int(base.split("_")[-1]))
    if base.startswith("vwap_zscore_"):
        return _vwap_zscore(df, int(base.split("_")[-1]))
    if base.startswith("amihud_"):
        return _amihud(df, int(base.split("_")[1]))
    if base.startswith("yangzhang_"):
        return _yang_zhang_vol(df, int(base.split("_")[-1]))
    if base in ("macd_norm_line", "macd_norm_hist"):
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        line = ema12 - ema26
        hist = line - line.ewm(span=9, adjust=False).mean()
        s = hist if base.endswith("hist") else line
        return s / (atr20 + 1e-12)
    if base == "kalman_spread_atr":
        kf = _kalman_filter(close.to_numpy())
        return (close - kf) / (atr20 + 1e-12)
    if base == "frac_diff_close":
        return _frac_diff_fixed(np.log(close), 0.40, 100)
    return None


# --------------------------------------------------------------------------- #
# Plotting
# --------------------------------------------------------------------------- #
def _style_x(ax, dates, n_ticks: int = 6) -> None:
    n = len(dates)
    if n == 0:
        return
    idx = np.unique(np.linspace(0, n - 1, min(n_ticks, n)).astype(int))
    ax.set_xticks(idx)
    ax.set_xticklabels([pd.Timestamp(dates[i]).strftime("%y-%m-%d") for i in idx], fontsize=6)
    ax.tick_params(axis="x", labelsize=6)
    ax.grid(alpha=0.25)


def _candles(ax, df) -> None:
    for i in range(len(df)):
        o, h, l, c = df["open"].iloc[i], df["high"].iloc[i], df["low"].iloc[i], df["close"].iloc[i]
        color = UP_COLOR if c >= o else DOWN_COLOR
        ax.plot([i, i], [l, h], color=color, lw=0.7, zorder=2)
        ax.add_patch(plt.Rectangle((i - 0.3, min(o, c)), 0.6, max(abs(c - o), 1e-9), color=color, zorder=3))


def _trend_channel(ax, close: pd.Series, window: int = 20) -> None:
    logc = np.log(close)
    x = np.arange(len(close))
    xw = x[-window:]
    yw = logc.iloc[-window:].to_numpy()
    if len(yw) < 2:
        return
    b, a = np.polyfit(xw, yw, 1)
    ax.plot(xw, np.exp(a + b * xw), color="#ff9800", lw=1.2, ls="--", label=f"{window}d trend")


def draw_ticker_page(pdf: PdfPages, df: pd.DataFrame, title: str, probs: dict, top3: str, top_driver: str) -> None:
    dates = df["date"].to_list()
    close = df["close"].astype("float64")
    x = np.arange(len(df))

    fig = plt.figure(figsize=(8.5, 11))
    gs = fig.add_gridspec(4, 1, height_ratios=[11, 3, 3, 3], hspace=0.45, left=0.08, right=0.95, top=0.94, bottom=0.05)

    # Panel 1 — candlesticks + Bollinger + peaks/troughs + trend channel.
    ax1 = fig.add_subplot(gs[0])
    _candles(ax1, df)
    sma20 = close.rolling(20, min_periods=20).mean()
    std20 = close.rolling(20, min_periods=20).std(ddof=1)
    ax1.plot(x, sma20, color="#1e88e5", lw=1.0, label="SMA20")
    ax1.fill_between(x, sma20 - 2 * std20, sma20 + 2 * std20, color="#1e88e5", alpha=0.10)
    ax1.plot(x, sma20 + 2 * std20, color="#1e88e5", lw=0.6, alpha=0.6)
    ax1.plot(x, sma20 - 2 * std20, color="#1e88e5", lw=0.6, alpha=0.6)
    _trend_channel(ax1, close, 20)
    if len(close) > 10:
        peaks = argrelextrema(close.to_numpy(), np.greater, order=5)[0]
        troughs = argrelextrema(close.to_numpy(), np.less, order=5)[0]
        ax1.scatter(peaks, close.iloc[peaks], marker="v", s=40, color=DOWN_COLOR, zorder=5)
        ax1.scatter(troughs, close.iloc[troughs], marker="^", s=40, color=UP_COLOR, zorder=5)
    ax1.set_title(title, fontsize=10, loc="left")
    ax1.legend(loc="upper right", fontsize=6, ncol=3)
    _style_x(ax1, dates)

    # Panel 2 — volume.
    ax2 = fig.add_subplot(gs[1])
    colors = [UP_COLOR if df["close"].iloc[i] >= df["open"].iloc[i] else DOWN_COLOR for i in range(len(df))]
    ax2.bar(x, df["volume"], color=colors, width=0.8)
    ax2.plot(x, df["volume"].rolling(20, min_periods=20).mean(), color="#1e88e5", lw=1.0, label="Vol SMA20")
    ax2.set_ylabel("Vol", fontsize=7)
    ax2.legend(loc="upper right", fontsize=6)
    _style_x(ax2, dates)

    # Panel 3 — RSI 14.
    ax3 = fig.add_subplot(gs[2])
    rsi = _rsi(close, 14)
    ax3.plot(x, rsi, color="#7e57c2", lw=1.0)
    ax3.axhline(70, color=DOWN_COLOR, lw=0.7, ls="--")
    ax3.axhline(30, color=UP_COLOR, lw=0.7, ls="--")
    ax3.set_ylim(0, 100)
    ax3.set_ylabel("RSI14", fontsize=7)
    _style_x(ax3, dates)

    # Panel 4 — top SHAP driver + 60d bands + callout.
    ax4 = fig.add_subplot(gs[3])
    series = compute_feature_series(df, top_driver)
    label = top_driver
    if series is None:
        series = _rsi(close, 14)
        label = "rsi_14 (fallback)"
    series = series.astype("float64")
    ax4.plot(x, series, color="#8e24aa", lw=1.0, label=label)
    m = series.rolling(60, min_periods=30).mean()
    s = series.rolling(60, min_periods=30).std(ddof=1)
    ax4.plot(x, m, color="#333333", lw=0.8, ls="--")
    ax4.fill_between(x, m - 2 * s, m + 2 * s, color="#8e24aa", alpha=0.08)
    ax4.set_ylabel(label, fontsize=6)
    ax4.legend(loc="upper right", fontsize=6)
    _style_x(ax4, dates)

    # Callout box: all 4 probabilities + top-3 SHAP contributions.
    txt = "\n".join(
        [f"{PROB[k]}: {v:.3f}" for k, v in probs.items() if np.isfinite(v)]
        + [f"Top3: {top3}" if top3 else ""]
    )
    fig.text(0.08, 0.015, txt, fontsize=7, family="monospace",
             bbox=dict(boxstyle="round,pad=0.4", fc="#f5f5f5", ec="#cccccc", alpha=0.9))

    pdf.savefig(fig)
    plt.close(fig)


def summary_page(pdf: PdfPages, market: str, section: str, columns: list[str], data: list[list]) -> None:
    fig, ax = plt.subplots(figsize=(8.5, 11))
    ax.axis("off")
    ax.set_title(f"{market} — {section}", fontsize=12, loc="left")
    if data:
        table = ax.table(cellText=data, colLabels=columns, loc="center", cellLoc="left")
        table.auto_set_font_size(False)
        table.set_fontsize(8)
        table.scale(1, 1.6)
    else:
        ax.text(0.5, 0.5, "(no data)", ha="center", va="center")
    pdf.savefig(fig)
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Section builders
# --------------------------------------------------------------------------- #
def render_section(pdf, market, title, tickers, score_col, driver_target, n_batch_meta) -> None:
    preds = load_predictions(market)
    summary_page(pdf, market, title,
                 ["Rank", "Symbol", score_col, "P_15d_Low", "P_20d_Up", "P_15d_High", "P_20d_Down"],
                 [[str(i + 1), s, f"{p:.3f}", f"{r['p_15d_low']:.3f}", f"{r['p_20d_up']:.3f}",
                   f"{r['p_15d_high']:.3f}", f"{r['p_20d_down']:.3f}"]
                  for i, (s, p, r) in enumerate(tickers)])

    for rank, (symbol, score, r) in enumerate(tickers, 1):
        df = load_raw(market, symbol)
        if df is None:
            continue
        probs = {k: float(r[k]) for k in PROB}
        top3 = r.get(f"top3_{driver_target}", "")
        top_driver = r.get(f"top_driver_{driver_target}", "")
        draw_ticker_page(
            pdf, df, f"#{rank} {symbol} — {title} ({score_col}={score:.3f})",
            probs, top3, top_driver,
        )
        n_batch_meta[0] += 1
        if n_batch_meta[0] % BATCH_GC_SIZE == 0:
            gc.collect()


def render_market(market: str, top_n: int) -> Path:
    preds = load_predictions(market)
    out = REPORTS_DIR / f"screener_{market}_{dt.date.today().strftime('%Y%m%d')}.pdf"
    n_batch = [0]

    with PdfPages(out) as pdf:
        # Section 1 — Portfolio Defense (holdings in this market).
        holdings = load_holdings()
        if not holdings.empty and "currency" in holdings.columns:
            h = holdings[holdings["currency"].str.upper() == market]
            h_rows = []
            for _, row in h.iterrows():
                sym = str(row["symbol"])
                p = preds[preds["symbol"] == sym]
                if p.empty:
                    continue
                p = p.iloc[0]
                urgency = max(float(p["p_15d_high"]), float(p["p_20d_down"]))
                h_rows.append((sym, urgency, p))
            h_rows.sort(key=lambda t: t[1], reverse=True)
            render_section(pdf, market, "Section 1 — Portfolio Defense (Exit Urgency)", h_rows,
                           "Exit_Urgency", "y_15d_high", n_batch)

        # Section 2 — Bottom inflections (Y_15d_Low).
        s2 = list(preds.nlargest(top_n, "p_15d_low").iterrows())
        s2 = [(r["symbol"], float(r["p_15d_low"]), r) for _, r in s2]
        render_section(pdf, market, "Section 2 — Buy-Side Bottom Inflections (P_15d_Low)", s2,
                       "p_15d_low", "y_15d_low", n_batch)

        # Section 3 — Upward momentum (Y_20d_Up).
        s3 = list(preds.nlargest(top_n, "p_20d_up").iterrows())
        s3 = [(r["symbol"], float(r["p_20d_up"]), r) for _, r in s3]
        render_section(pdf, market, "Section 3 — Buy-Side Upward Momentum (P_20d_Up)", s3,
                       "p_20d_up", "y_20d_up", n_batch)

    return out


def main() -> int:
    init_dirs()
    if PDF_BLOCK_FLAG.exists():
        print(f"[pdf_compiler] BLOCKED: {PDF_BLOCK_FLAG.read_text().strip()}", file=sys.stderr)
        return 1

    parser = argparse.ArgumentParser()
    parser.add_argument("--market", choices=["USD", "CAD", "ALL"], default="ALL")
    parser.add_argument("--top-n", type=int, default=30)
    args = parser.parse_args()

    markets = ["USD", "CAD"] if args.market == "ALL" else [args.market]
    t0 = time.time()
    for mkt in markets:
        out = render_market(mkt, args.top_n)
        print(f"[pdf_compiler] {mkt}: {out} ({out.stat().st_size:,} bytes)")
    elapsed = time.time() - t0
    log_telemetry("pdf_compiler", "SUCCESS", elapsed, {"markets": markets, "top_n": args.top_n})
    update_state("EP-05", "gate_5", {"markets": markets, "top_n": args.top_n})
    return 0


if __name__ == "__main__":
    sys.exit(main())
