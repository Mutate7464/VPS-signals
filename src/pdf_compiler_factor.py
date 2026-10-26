"""WI-014 step 2 — E5 factor tearsheet renderer (summary page + one page per name).

This is the *factor* tearsheet, separate from `src/pdf_compiler.py`, which is the
frozen Sprint-5 predictions-route record and is left byte-identical. Only drawing
logic that is decoupled from the legacy predictions loader is imported from it
(`_candles`, `_trend_channel`, `_style_x`, the up/down colours, the 120-bar chart
lookback and the batch-10 GC size); nothing in that module is modified or copied
into a competing definitions file.

Page layout:

  1. Summary — scoring date, eligible universe size, ranking rule, the top-N table,
     the E5 single-factor IC table read from the published WI-012 baseline report
     (`reports/wi012_e5_baseline_{market}_h15.md`), and the NO_TRADE/cost caveat.
  2..N. One page per shortlist member — candles + 20d Bollinger Bands + 20d trend
     channel, volume, RSI-14, and all five E5 factor values with their same-date
     cross-section percentiles.

Memory lifecycle (CB-06 guardrail): Agg backend; each figure is saved and closed
immediately; `matplotlib.pyplot.close('all')` + `gc.collect()` run after every
batch of `BATCH_GC_SIZE` (10) pages.

Presentation contract: descriptive context only. No composite score, no trade
instruction, no claim of profitability — the summary carries the WI-011
NO_TRADE/cost caveat, and IC numbers are only ever read from the validated report.
"""

from __future__ import annotations

import gc
import re
import textwrap
from dataclasses import dataclass, field
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless vector backend — no display needed

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages  # noqa: E402

from src.factors.e5_baseline import E5_FACTORS  # noqa: E402
from src.feature_engine import _rsi  # noqa: E402
from src.pdf_compiler import (  # noqa: E402
    BATCH_GC_SIZE,
    CHART_LOOKBACK,
    DOWN_COLOR,
    UP_COLOR,
    _candles,
    _style_x,
    _trend_channel,
)

BASE_DIR = Path(__file__).resolve().parents[1]
REPORTS = BASE_DIR / "reports"
RAW_DIR = BASE_DIR / "data" / "raw_ohlcv"

RANK_FACTOR = "mom_12_1"
RANKING_RULE = f"rank by {RANK_FACTOR} descending (WI-012-validated E5 single factor)"
IC_HORIZON = 15
MIN_CHART_BARS = 30  # below this a ticker page would be empty noise; skip it

NO_TRADE_CAVEAT = (
    "Research context only — this is not a trade instruction and not a recommendation. "
    "WI-011 found that no condition or decision rule survived round-trip costs at this "
    "universe size, so the project default remains NO_TRADE. The shortlist ranks an "
    "existing, validated factor; it carries no forecast, no composite score and no "
    "position sizing. No order is ever placed or published automatically — every "
    "distribution stays behind the sprint human gate."
)

_IC_ROW = re.compile(
    r"^\|\s*`([A-Za-z0-9_]+)`\s*\|\s*([+-]?\d+\.\d+)\s*\|\s*([+-]?\d+\.\d+)\s*\|\s*(\d+)\s*\|\s*$"
)


@dataclass
class TearsheetResult:
    """What one market's tearsheet render produced."""

    market: str
    scoring_date: pd.Timestamp
    path: Path
    pages: int
    shortlist_size: int
    rendered_tickers: list[str] = field(default_factory=list)
    skipped_tickers: dict[str, str] = field(default_factory=dict)
    eligible_symbols: int = 0


# --------------------------------------------------------------------------- #
# Validated IC numbers (read, never invented)
# --------------------------------------------------------------------------- #
def ic_report_path(market: str, *, reports_dir: Path | None = None) -> Path:
    """The published WI-012 E5 baseline report that supplies the IC table."""
    root = reports_dir if reports_dir is not None else REPORTS
    return Path(root) / f"wi012_e5_baseline_{market}_h{IC_HORIZON}.md"


def parse_e5_ic_table(report_file: Path | str) -> list[tuple[str, float, float, int]]:
    """Single-factor within-date rank-IC rows of a WI-012 E5 baseline report.

    The tearsheet must not print an invented number, so the table is parsed from
    the published report and the parsed factor set has to be exactly the five E5
    factors — a missing report or a drifted table is an error, not a blank cell.

    Returns:
        `[(factor, mean_ic, t_stat, n_dates), ...]` in report order.

    Raises:
        FileNotFoundError: the report does not exist.
        ValueError: the single-factor table is absent or names a different factor set.
    """
    path = Path(report_file)
    if not path.exists():
        raise FileNotFoundError(f"missing E5 baseline report {path}")

    single_section = path.read_text().split("## Multivariate", 1)[0]
    rows: list[tuple[str, float, float, int]] = []
    for line in single_section.splitlines():
        match = _IC_ROW.match(line.strip())
        if match:
            rows.append((match.group(1), float(match.group(2)), float(match.group(3)), int(match.group(4))))

    names = [name for name, *_ in rows]
    if sorted(names) != sorted(E5_FACTORS):
        raise ValueError(
            f"{path}: single-factor IC table must list exactly the five E5 factors "
            f"(got {names or 'nothing'})"
        )
    return rows


# --------------------------------------------------------------------------- #
# Context: same-date cross-section percentiles + point-in-time price window
# --------------------------------------------------------------------------- #
def cross_section_percentiles(cross_section: pd.DataFrame) -> pd.DataFrame:
    """Per-factor percentile (0-100) within the scoring date's eligible cross-section.

    `rank(pct=True)` on one date, so a value is always read against the universe it
    was ranked in — descriptive context, not a score.
    """
    frame = cross_section[["symbol", *E5_FACTORS]].copy()
    for name in E5_FACTORS:
        frame[f"{name}_pct"] = frame[name].rank(pct=True, method="average") * 100.0
    return frame


def load_raw_window(market: str, symbol: str, scoring_date, *, raw_dir: Path | None = None,
                    lookback: int = CHART_LOOKBACK) -> pd.DataFrame | None:
    """Trailing `lookback` bars up to and including the scoring date.

    Point-in-time by construction: bars after the scoring date are never charted,
    so a tearsheet for an older date cannot show later prices.
    """
    root = raw_dir if raw_dir is not None else RAW_DIR
    path = Path(root) / f"market={market}" / f"symbol={symbol}.parquet"
    if not path.exists():
        return None
    df = pd.read_parquet(path, columns=["date", "open", "high", "low", "close", "volume"])
    df["date"] = pd.to_datetime(df["date"]).astype("datetime64[ns]")
    df = df[df["date"] <= pd.Timestamp(scoring_date)].sort_values("date").tail(lookback).reset_index(drop=True)
    for column in ("open", "high", "low", "close", "volume"):
        df[column] = df[column].astype("float64")
    return df if len(df) else None


def reclaim_memory() -> None:
    """Batch cleanup: drop every open figure, then collect (CB-06 memory guardrail)."""
    plt.close("all")
    gc.collect()


# --------------------------------------------------------------------------- #
# Page content (pure — the renderer draws exactly this, tests read it directly)
# --------------------------------------------------------------------------- #
def _fmt(value: float) -> str:
    """Compact formatting that survives both ~1e-10 (amihud) and ~1e2 (log dollar vol)."""
    if value is None or not np.isfinite(value):
        return "n/a"
    return f"{value:.4g}"


def summary_content(*, market: str, scoring_date, shortlist: pd.DataFrame, eligible_symbols: int,
                    stale_symbols: int = 0, skipped: dict[str, int] | None = None, top_n: int | None = None,
                    ic_rows: list[tuple[str, float, float, int]], ranking_rule: str = RANKING_RULE,
                    rank_factor: str = RANK_FACTOR) -> dict:
    """The summary page's exact text and tables."""
    date_str = pd.Timestamp(scoring_date).strftime("%Y-%m-%d")
    skipped = skipped or {}
    skipped_line = ", ".join(f"{reason}={count}" for reason, count in sorted(skipped.items()) if count) or "none"

    shortlist_rows = [
        [str(int(row["rank"])), str(row["symbol"])] + [_fmt(float(row[name])) for name in E5_FACTORS]
        for _, row in shortlist.iterrows()
    ]

    return {
        "title": f"E5 factor screener — {market}",
        "subtitle": (
            f"Scoring date {date_str} · research shortlist (descriptive context, not advice)"
        ),
        "metadata": [
            f"Eligible universe: {eligible_symbols} symbols with a feature row on {date_str} "
            f"({stale_symbols} stale symbol(s) excluded)",
            f"Universe after factor guard: {len(shortlist)} ranked · skipped: {skipped_line}",
            f"Ranking rule: {ranking_rule}",
            f"Shortlist: {len(shortlist)} name(s) requested top-N={top_n if top_n is not None else len(shortlist)}",
            "Factors: existing E5 definitions (mom_12_1, rev_1m, vol_20, amihud_20, log_dollar_vol_20) "
            "— no composite, no model, no target change",
        ],
        "shortlist_caption": f"Top {len(shortlist)} by {rank_factor} descending",
        "shortlist_columns": ["#", "Symbol", *E5_FACTORS],
        "shortlist_rows": shortlist_rows,
        "ic_caption": (
            "E5 single-factor within-date rank-IC vs fwd_atr_ret_15 — values read from "
            f"reports/wi012_e5_baseline_{market}_h{IC_HORIZON}.md"
        ),
        "ic_columns": ["Factor", "mean IC", "t", "dates"],
        "ic_rows": [[f"{name}", f"{ic:+.4f}", f"{t:+.2f}", str(dates)] for name, ic, t, dates in ic_rows],
        "caveat_title": "NO_TRADE / cost caveat",
        "caveat": NO_TRADE_CAVEAT,
    }


def ticker_content(*, rank: int, symbol: str, market: str, scoring_date, row: pd.Series,
                   percentiles: pd.Series | None, panel_titles: tuple[str, ...] | None = None) -> dict:
    """One ticker page's title, panel titles and five-factor context rows."""
    date_str = pd.Timestamp(scoring_date).strftime("%Y-%m-%d")
    percentiles = percentiles if percentiles is not None else pd.Series(dtype="float64")
    factors = []
    for name in E5_FACTORS:
        value = float(row[name])
        pct = percentiles.get(f"{name}_pct", float("nan"))
        factors.append(
            {
                "factor": name,
                "value": value,
                "value_text": _fmt(value),
                "percentile": float(pct) if np.isfinite(pct) else float("nan"),
            }
        )
    return {
        "title": f"#{rank} {symbol} — E5 factor shortlist ({market}, scoring date {date_str})",
        "panels": panel_titles or (
            "candles + 20d Bollinger Bands + 20d trend channel",
            "volume + 20d volume SMA",
            "RSI-14 (30/70)",
            f"E5 factors vs the {date_str} cross-section (percentile 0-100)",
        ),
        "factors": factors,
        "footer": "Research context only · NO_TRADE default (WI-011 cost verdict) · not a trade instruction",
    }


# --------------------------------------------------------------------------- #
# Drawing (imported legacy primitives where decoupled from the predictions path)
# --------------------------------------------------------------------------- #
def draw_summary_page(pdf: PdfPages, content: dict) -> None:
    """Render the summary page: metadata, top-N table, IC table, NO_TRADE caveat."""
    fig = plt.figure(figsize=(8.5, 11))
    fig.text(0.07, 0.955, content["title"], fontsize=15, weight="bold")
    fig.text(0.07, 0.930, content["subtitle"], fontsize=9, color="#444444")
    fig.text(0.07, 0.900, "\n".join(content["metadata"]), fontsize=8.5, va="top", linespacing=1.6)

    ax_short = fig.add_axes([0.07, 0.50, 0.86, 0.30])
    ax_short.axis("off")
    ax_short.set_title(content["shortlist_caption"], fontsize=10, loc="left")
    if content["shortlist_rows"]:
        table = ax_short.table(cellText=content["shortlist_rows"], colLabels=content["shortlist_columns"],
                               loc="upper center", cellLoc="right")
        table.auto_set_font_size(False)
        table.set_fontsize(8)
        table.scale(1, 1.35)
    else:
        ax_short.text(0.5, 0.5, "(no eligible names)", ha="center", va="center", fontsize=9)

    ax_ic = fig.add_axes([0.07, 0.27, 0.86, 0.16])
    ax_ic.axis("off")
    ax_ic.set_title(content["ic_caption"], fontsize=8, loc="left", wrap=True)
    ic_table = ax_ic.table(cellText=content["ic_rows"], colLabels=content["ic_columns"],
                           loc="upper center", cellLoc="right")
    ic_table.auto_set_font_size(False)
    ic_table.set_fontsize(8)
    ic_table.scale(1, 1.25)

    fig.text(0.07, 0.20, content["caveat_title"], fontsize=10, weight="bold", color="#b71c1c")
    fig.text(0.07, 0.165, textwrap.fill(content["caveat"], 96), fontsize=8, va="top", linespacing=1.5,
             bbox=dict(boxstyle="round,pad=0.5", fc="#fff5f5", ec="#e0b4b4"))

    pdf.savefig(fig)
    plt.close(fig)


def _factor_label(factor: dict) -> str:
    """`mom_12_1  value=0.1234  pct=93` — the value and its cross-section percentile."""
    percentile = factor["percentile"]
    percentile_text = f"{percentile:.0f}" if np.isfinite(percentile) else "n/a"
    return f"{factor['factor']}  value={factor['value_text']}  pct={percentile_text}"


def draw_factor_ticker_page(pdf: PdfPages, content: dict, window: pd.DataFrame) -> None:
    """One ticker page: candles/BB/trend, volume, RSI-14, factor percentiles."""
    dates = window["date"].to_list()
    close = window["close"].astype("float64")
    x = np.arange(len(window))

    fig = plt.figure(figsize=(8.5, 11))
    gs = fig.add_gridspec(4, 1, height_ratios=[11, 3, 3, 4.5], hspace=0.55,
                          left=0.08, right=0.95, top=0.93, bottom=0.07)

    # Panel 1 — candlesticks + 20d Bollinger Bands + 20d OLS trend channel (legacy drawing logic).
    ax1 = fig.add_subplot(gs[0])
    _candles(ax1, window)
    sma20 = close.rolling(20, min_periods=20).mean()
    std20 = close.rolling(20, min_periods=20).std(ddof=1)
    ax1.plot(x, sma20, color="#1e88e5", lw=1.0, label="SMA20")
    ax1.fill_between(x, sma20 - 2 * std20, sma20 + 2 * std20, color="#1e88e5", alpha=0.10)
    ax1.plot(x, sma20 + 2 * std20, color="#1e88e5", lw=0.6, alpha=0.6)
    ax1.plot(x, sma20 - 2 * std20, color="#1e88e5", lw=0.6, alpha=0.6)
    _trend_channel(ax1, close, 20)
    ax1.set_title(content["title"], fontsize=10, loc="left")
    ax1.set_ylabel(content["panels"][0], fontsize=7)
    ax1.legend(loc="upper right", fontsize=6, ncol=3)
    _style_x(ax1, dates)

    # Panel 2 — volume, coloured by close direction.
    ax2 = fig.add_subplot(gs[1])
    colors = [UP_COLOR if window["close"].iloc[i] >= window["open"].iloc[i] else DOWN_COLOR
              for i in range(len(window))]
    ax2.bar(x, window["volume"], color=colors, width=0.8)
    ax2.plot(x, window["volume"].rolling(20, min_periods=20).mean(), color="#1e88e5", lw=1.0, label="Vol SMA20")
    ax2.set_ylabel(content["panels"][1], fontsize=7)
    ax2.legend(loc="upper right", fontsize=6)
    _style_x(ax2, dates)

    # Panel 3 — RSI-14.
    ax3 = fig.add_subplot(gs[2])
    ax3.plot(x, _rsi(close, 14), color="#7e57c2", lw=1.0)
    ax3.axhline(70, color=DOWN_COLOR, lw=0.7, ls="--")
    ax3.axhline(30, color=UP_COLOR, lw=0.7, ls="--")
    ax3.set_ylim(0, 100)
    ax3.set_ylabel(content["panels"][2], fontsize=7)
    _style_x(ax3, dates)

    # Panel 4 — the five E5 factors with their same-date cross-section percentiles.
    ax4 = fig.add_subplot(gs[3])
    names = [factor["factor"] for factor in content["factors"]]
    pcts = [factor["percentile"] if np.isfinite(factor["percentile"]) else 0.0 for factor in content["factors"]]
    positions = np.arange(len(names))[::-1]
    ax4.barh(positions, pcts, color="#8e24aa", height=0.55, alpha=0.85)
    ax4.axvline(50, color="#999999", lw=0.8, ls=":")
    ax4.set_xlim(0, 100)
    ax4.set_yticks(positions)
    ax4.set_yticklabels([_factor_label(factor) for factor in content["factors"]], fontsize=7)
    ax4.set_xlabel(content["panels"][3], fontsize=7)
    ax4.grid(axis="x", alpha=0.25)

    fig.text(0.08, 0.02, content["footer"], fontsize=7, color="#555555")

    pdf.savefig(fig)
    plt.close(fig)


# --------------------------------------------------------------------------- #
# Market tearsheet
# --------------------------------------------------------------------------- #
def render_tearsheet(*, market: str, scoring_date, shortlist: pd.DataFrame, cross_section: pd.DataFrame,
                     out_path: Path | str, eligible_symbols: int = 0, stale_symbols: int = 0,
                     skipped: dict[str, int] | None = None, top_n: int | None = None,
                     raw_dir: Path | None = None, reports_dir: Path | None = None,
                     ic_rows: list[tuple[str, float, float, int]] | None = None,
                     ranking_rule: str = RANKING_RULE, rank_factor: str = RANK_FACTOR,
                     batch_size: int = BATCH_GC_SIZE) -> TearsheetResult:
    """Write one market's E5 tearsheet PDF: summary page then one page per name.

    Pages are rendered in batches: every figure is saved and closed immediately and
    `close('all')` + `gc.collect()` run after each batch of `batch_size` (10) pages.
    """
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    rows = ic_rows if ic_rows is not None else parse_e5_ic_table(ic_report_path(market, reports_dir=reports_dir))
    percentiles = cross_section_percentiles(cross_section).set_index("symbol")

    pages = 0
    rendered: list[str] = []
    skipped_tickers: dict[str, str] = {}

    with PdfPages(out) as pdf:
        draw_summary_page(pdf, summary_content(
            market=market, scoring_date=scoring_date, shortlist=shortlist,
            eligible_symbols=eligible_symbols, stale_symbols=stale_symbols, skipped=skipped,
            top_n=top_n, ic_rows=rows, ranking_rule=ranking_rule, rank_factor=rank_factor,
        ))
        pages += 1
        if pages % batch_size == 0:
            reclaim_memory()

        for _, row in shortlist.iterrows():
            symbol = str(row["symbol"])
            window = load_raw_window(market, symbol, scoring_date, raw_dir=raw_dir)
            if window is None or len(window) < MIN_CHART_BARS:
                skipped_tickers[symbol] = "no raw window for the scoring date"
                continue
            pct_row = percentiles.loc[symbol] if symbol in percentiles.index else None
            draw_factor_ticker_page(pdf, ticker_content(
                rank=int(row["rank"]), symbol=symbol, market=market, scoring_date=scoring_date,
                row=row, percentiles=pct_row,
            ), window)
            rendered.append(symbol)
            pages += 1
            if pages % batch_size == 0:
                reclaim_memory()

        reclaim_memory()

    return TearsheetResult(
        market=market, scoring_date=pd.Timestamp(scoring_date), path=out, pages=pages,
        shortlist_size=len(shortlist), rendered_tickers=rendered, skipped_tickers=skipped_tickers,
        eligible_symbols=eligible_symbols,
    )
