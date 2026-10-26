"""WI-014 step 2 — factor tearsheet renderer contract.

Covers the renderer's acceptance bullets: the summary page carries the scoring
date, eligible universe size, ranking rule, the top-N table and the published IC
numbers (never invented ones) plus the NO_TRADE/cost caveat; each ticker page has
the candles/BB/trend, volume, RSI-14 and five-factor-percentile panels; a smoke PDF
is non-empty with one page per rendered name; and rendering never touches the
frozen Sprint-5 compiler or any pre-existing file.

The PDFs are written into `tmp_path`, and the chart panels are exercised on a tiny
synthetic OHLCV fixture, so this file costs nothing and reads no real panel.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import src.pdf_compiler_factor as factor_pdf
from src.factors.e5_baseline import E5_FACTORS

ROOT = Path(__file__).resolve().parents[1]
FROZEN_COMPILER = ROOT / "src" / "pdf_compiler.py"
SCORING_DATE = pd.Timestamp("2026-09-23")
LEGACY_PDFS = ("screener_USD_20261021.pdf", "screener_CAD_20261021.pdf")

STUB_IC_MD = """# WI-009 — E5 factor baseline (USD)

## Single-factor within-date rank-IC

| Factor | mean IC | t | dates |
| :--- | ---: | ---: | ---: |
| `mom_12_1` | +0.0209 | +6.00 | 2869 |
| `rev_1m` | +0.0025 | +0.90 | 2869 |
| `vol_20` | -0.0158 | -5.11 | 2869 |
| `amihud_20` | -0.0085 | -3.88 | 2869 |
| `log_dollar_vol_20` | +0.0052 | +2.65 | 2869 |

## Multivariate (purged WF, 20d embargo)

| Model | mean IC | t | dates |
| :--- | ---: | ---: | ---: |
| `ridge` | +0.0055 | +1.86 | 1722 |
"""


def _bars(n: int, seed: int, end: pd.Timestamp) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    close = 40.0 * np.exp(np.cumsum(0.001 + 0.008 * rng.standard_normal(n)))
    spread = close * 0.012 + 0.01
    open_ = close * (1.0 + 0.002 * rng.standard_normal(n))
    return pd.DataFrame(
        {
            "date": pd.bdate_range(end=end, periods=n),
            "open": open_,
            "high": np.maximum.reduce([close + spread, open_, close]),
            "low": np.minimum.reduce([close - spread, open_, close]),
            "close": close,
            "volume": np.exp(12.0 + 0.3 * rng.standard_normal(n)),
        }
    )


@pytest.fixture(scope="module")
def fixture(tmp_path_factory):
    """Synthetic raw tree whose bars run past the scoring date, plus a stub IC report."""
    root = tmp_path_factory.mktemp("wi014_pdf")
    raw_dir = root / "raw_ohlcv"
    reports_dir = root / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    (reports_dir / "wi012_e5_baseline_USD_h15.md").write_text(STUB_IC_MD)
    symbols = ("AAA", "BBB", "CCC")
    for seed, symbol in enumerate(symbols):
        target = raw_dir / "market=USD"
        target.mkdir(parents=True, exist_ok=True)
        # 180 bars ending 2026-10-21: the window for 2026-09-23 must stop there.
        _bars(180, seed=seed, end=pd.Timestamp("2026-10-21")).to_parquet(
            target / f"symbol={symbol}.parquet", index=False
        )
    return {"root": root, "raw_dir": raw_dir, "reports_dir": reports_dir, "symbols": symbols}


def _cross_section(symbols) -> pd.DataFrame:
    """Explicit same-date cross-section: mom_12_1 descends, others are filler."""
    rows = []
    mom = {"AAA": 0.50, "BBB": 0.10, "CCC": -0.20, "ZZZ": 0.30}
    for symbol in symbols:
        rows.append(
            {
                "symbol": symbol,
                "mom_12_1": mom[symbol],
                "rev_1m": 0.02,
                "vol_20": 0.03,
                "amihud_20": 1e-10,
                "log_dollar_vol_20": 16.0,
            }
        )
    return pd.DataFrame(rows, columns=["symbol", *E5_FACTORS])


def _shortlist(symbols) -> pd.DataFrame:
    cross = _cross_section(symbols).sort_values("mom_12_1", ascending=False).reset_index(drop=True)
    cross.insert(0, "rank", np.arange(1, len(cross) + 1, dtype="int32"))
    cross["scoring_date"] = SCORING_DATE.strftime("%Y-%m-%d")
    return cross[["rank", "symbol", *E5_FACTORS, "scoring_date"]]


def _ic_rows(fixture):
    return factor_pdf.parse_e5_ic_table(fixture["reports_dir"] / "wi012_e5_baseline_USD_h15.md")


# --------------------------------------------------------------------------- #
# IC numbers are read from the published report, never invented
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    ("market", "expected_mom"),
    [("CAD", 0.0271), ("USD", 0.0209)],
)
def test_parse_ic_table_reads_the_published_numbers(market, expected_mom):
    rows = factor_pdf.parse_e5_ic_table(ROOT / "reports" / f"wi012_e5_baseline_{market}_h15.md")
    values = {name: (ic, t, dates) for name, ic, t, dates in rows}
    assert sorted(values) == sorted(E5_FACTORS)
    assert values["mom_12_1"][0] == pytest.approx(expected_mom, abs=1e-4)
    assert all(dates > 0 for _, _, dates in values.values())


def test_parse_ic_table_excludes_multivariate_rows(fixture):
    rows = _ic_rows(fixture)
    assert [name for name, *_ in rows] == E5_FACTORS  # ridge/logit rows are not IC context


def test_parse_ic_table_refuses_missing_report(tmp_path):
    with pytest.raises(FileNotFoundError):
        factor_pdf.parse_e5_ic_table(tmp_path / "wi012_e5_baseline_XYZ_h15.md")


def test_parse_ic_table_refuses_a_drifted_factor_set(tmp_path):
    drifted = tmp_path / "wi012_e5_baseline_USD_h15.md"
    drifted.write_text(
        "# baseline\n\n| Factor | mean IC | t | dates |\n| :--- | ---: | ---: | ---: |\n"
        "| `mom_12_1` | +0.0209 | +6.00 | 2869 |\n| `made_up_factor` | +9.9999 | +99.00 | 2869 |\n"
    )
    with pytest.raises(ValueError):
        factor_pdf.parse_e5_ic_table(drifted)

    empty = tmp_path / "empty.md"
    empty.write_text("# no table here\n")
    with pytest.raises(ValueError):
        factor_pdf.parse_e5_ic_table(empty)


# --------------------------------------------------------------------------- #
# Same-date cross-section percentiles + point-in-time windows
# --------------------------------------------------------------------------- #
def test_cross_section_percentiles_are_same_date_ranks():
    percentiles = factor_pdf.cross_section_percentiles(_cross_section(["AAA", "BBB", "CCC"]))
    by_symbol = percentiles.set_index("symbol")
    assert by_symbol.loc["AAA", "mom_12_1_pct"] == pytest.approx(100.0)
    assert by_symbol.loc["CCC", "mom_12_1_pct"] == pytest.approx(100.0 / 3.0)
    assert ((percentiles["mom_12_1_pct"] > 0) & (percentiles["mom_12_1_pct"] <= 100)).all()
    # every factor is ranked, not just the ranking factor
    for name in E5_FACTORS:
        assert f"{name}_pct" in percentiles.columns


def test_raw_window_stops_at_the_scoring_date(fixture):
    window = factor_pdf.load_raw_window("USD", "AAA", SCORING_DATE, raw_dir=fixture["raw_dir"])
    assert window is not None
    assert window["date"].max() == SCORING_DATE, "chart must not show bars after the scoring date"
    assert len(window) == factor_pdf.CHART_LOOKBACK
    assert factor_pdf.load_raw_window("USD", "ZZZ", SCORING_DATE, raw_dir=fixture["raw_dir"]) is None


# --------------------------------------------------------------------------- #
# Page content contract
# --------------------------------------------------------------------------- #
def test_summary_content_has_required_metadata_and_caveat(fixture):
    shortlist = _shortlist(fixture["symbols"])
    content = factor_pdf.summary_content(
        market="USD", scoring_date=SCORING_DATE, shortlist=shortlist, eligible_symbols=42,
        stale_symbols=3, skipped={"no_raw_file": 2, "short_history": 1}, top_n=10,
        ic_rows=_ic_rows(fixture),
    )
    text = "\n".join([content["title"], content["subtitle"], *content["metadata"],
                      content["shortlist_caption"], content["ic_caption"], content["caveat"]])
    assert "2026-09-23" in text, "the scoring date must be on the page"
    assert "Eligible universe: 42 symbols" in text
    assert "3 stale symbol(s) excluded" in text
    assert "mom_12_1 descending" in text, "the ranking rule must be stated"
    assert "no_raw_file=2" in text
    assert content["caveat"] == factor_pdf.NO_TRADE_CAVEAT
    assert "NO_TRADE" in content["caveat"] and "cost" in content["caveat"]
    assert content["caveat_title"] == "NO_TRADE / cost caveat"
    assert content["shortlist_columns"] == ["#", "Symbol", *E5_FACTORS]
    assert [row[1] for row in content["shortlist_rows"]] == ["AAA", "BBB", "CCC"]
    # the IC table is the parsed report, verbatim: no substitute numbers.
    parsed = [[name, f"{ic:+.4f}", f"{t:+.2f}", str(dates)] for name, ic, t, dates in _ic_rows(fixture)]
    assert content["ic_rows"] == parsed


def test_ticker_content_lists_all_five_factors_with_percentiles(fixture):
    shortlist = _shortlist(fixture["symbols"])
    row = shortlist.iloc[0]
    percentiles = factor_pdf.cross_section_percentiles(_cross_section(fixture["symbols"])).set_index("symbol")
    content = factor_pdf.ticker_content(rank=1, symbol="AAA", market="USD", scoring_date=SCORING_DATE,
                                       row=row, percentiles=percentiles.loc["AAA"])
    assert content["title"].startswith("#1 AAA")
    assert "2026-09-23" in content["title"]
    assert len(content["panels"]) == 4
    panel_text = " ".join(content["panels"])
    for needle in ("Bollinger", "volume", "RSI-14", "percentile"):
        assert needle.lower() in panel_text.lower()
    assert [factor["factor"] for factor in content["factors"]] == E5_FACTORS
    assert content["factors"][0]["percentile"] == pytest.approx(100.0)
    assert content["factors"][0]["value"] == pytest.approx(0.50)
    assert "not a trade instruction" in content["footer"]


# --------------------------------------------------------------------------- #
# Rendering: pages, file, frozen artifacts
# --------------------------------------------------------------------------- #
def test_render_tearsheet_writes_summary_plus_one_page_per_name(fixture, tmp_path):
    symbols = fixture["symbols"]
    out = tmp_path / "screener_factor_USD_20260923.pdf"
    result = factor_pdf.render_tearsheet(
        market="USD", scoring_date=SCORING_DATE, shortlist=_shortlist(symbols),
        cross_section=_cross_section(symbols), out_path=out, eligible_symbols=42,
        stale_symbols=3, skipped={}, top_n=10, raw_dir=fixture["raw_dir"],
        reports_dir=fixture["reports_dir"],
    )
    assert out.exists() and out.stat().st_size > 5_000, "smoke PDF must be non-empty"
    assert out.read_bytes()[:4] == b"%PDF"
    assert result.pages == 1 + len(symbols)
    assert result.rendered_tickers == list(symbols)
    assert result.skipped_tickers == {}
    assert result.eligible_symbols == 42


def test_render_tearsheet_skips_names_without_a_window(fixture, tmp_path):
    out = tmp_path / "screener_factor_USD_20260923.pdf"
    result = factor_pdf.render_tearsheet(
        market="USD", scoring_date=SCORING_DATE,
        shortlist=_shortlist(["AAA", "ZZZ"]), cross_section=_cross_section(["AAA", "ZZZ"]),
        out_path=out, ic_rows=_ic_rows(fixture), raw_dir=fixture["raw_dir"],
    )
    assert result.pages == 2, "summary + the one name that has a raw window"
    assert result.rendered_tickers == ["AAA"]
    assert set(result.skipped_tickers) == {"ZZZ"}


def test_rendering_leaves_the_frozen_compiler_and_existing_files_untouched(fixture, tmp_path):
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    sentinel = reports_dir / "screener_CAD_20261021.pdf"  # same name as a frozen artifact
    sentinel.write_bytes(b"frozen legacy demo")
    before_compiler = hashlib.sha256(FROZEN_COMPILER.read_bytes()).hexdigest()
    before_sentinel = hashlib.sha256(sentinel.read_bytes()).hexdigest()

    out = reports_dir / "screener_factor_USD_20260923.pdf"
    factor_pdf.render_tearsheet(
        market="USD", scoring_date=SCORING_DATE, shortlist=_shortlist(["AAA"]),
        cross_section=_cross_section(["AAA"]), out_path=out, ic_rows=_ic_rows(fixture),
        raw_dir=fixture["raw_dir"],
    )

    assert hashlib.sha256(FROZEN_COMPILER.read_bytes()).hexdigest() == before_compiler
    assert hashlib.sha256(sentinel.read_bytes()).hexdigest() == before_sentinel
    assert out.name not in LEGACY_PDFS
    assert sorted(p.name for p in reports_dir.iterdir()) == sorted(
        [sentinel.name, out.name]
    ), "rendering writes exactly one new file"


class _FigureRecorder:
    """A `PdfPages` stand-in: keeps the figure so tests can read what was drawn."""

    def __init__(self):
        self.figures = []

    def savefig(self, figure, **kwargs):
        self.figures.append(figure)


def _drawn_text(figure) -> str:
    lines = [text.get_text() for text in figure.texts]
    for axes in figure.axes:
        lines += [axes.get_title(loc=loc) for loc in ("left", "center", "right")]
        lines += [axes.get_xlabel(), axes.get_ylabel()]
        for table in axes.tables:
            lines += [cell.get_text().get_text() for cell in table.get_celld().values()]
    return "\n".join(lines)


def test_summary_page_actually_draws_the_metadata_caveat_and_ic_table(fixture, monkeypatch):
    """The drawn page — not just the content dict — carries the required summary facts."""
    shortlist = _shortlist(fixture["symbols"])
    content = factor_pdf.summary_content(
        market="USD", scoring_date=SCORING_DATE, shortlist=shortlist, eligible_symbols=42,
        stale_symbols=3, skipped={"no_raw_file": 2}, top_n=10, ic_rows=_ic_rows(fixture),
    )
    recorder = _FigureRecorder()
    monkeypatch.setattr(factor_pdf.plt, "close", lambda *args, **kwargs: None)
    factor_pdf.draw_summary_page(recorder, content)
    monkeypatch.undo()

    drawn = _drawn_text(recorder.figures[-1])
    for needle in ("Eligible universe: 42", "Ranking rule:", "mom_12_1 descending",
                   "2026-09-23", "NO_TRADE", "cost", "wi012_e5_baseline_USD_h15.md",
                   "+0.0209", "log_dollar_vol_20"):
        assert needle in drawn, f"summary page is missing {needle!r}"

    import matplotlib.pyplot as plt

    plt.close("all")


def test_ticker_page_actually_draws_all_panels_and_factor_context(fixture, monkeypatch):
    shortlist = _shortlist(fixture["symbols"])
    percentiles = factor_pdf.cross_section_percentiles(_cross_section(fixture["symbols"])).set_index("symbol")
    window = factor_pdf.load_raw_window("USD", "AAA", SCORING_DATE, raw_dir=fixture["raw_dir"])
    content = factor_pdf.ticker_content(rank=1, symbol="AAA", market="USD", scoring_date=SCORING_DATE,
                                       row=shortlist.iloc[0], percentiles=percentiles.loc["AAA"])
    recorder = _FigureRecorder()
    monkeypatch.setattr(factor_pdf.plt, "close", lambda *args, **kwargs: None)
    factor_pdf.draw_factor_ticker_page(recorder, content, window)
    monkeypatch.undo()

    figure = recorder.figures[-1]
    assert len(figure.axes) == 4, "candles/BB/trend, volume, RSI-14 and factor context"
    labels = " ".join(tick.get_text() for tick in figure.axes[3].get_yticklabels())
    for name in E5_FACTORS:
        assert name in labels, f"factor panel is missing {name}"
    assert "pct=" in labels
    assert "not a trade instruction" in _drawn_text(figure)

    import matplotlib.pyplot as plt

    plt.close("all")


def test_reclaim_memory_closes_figures():
    import matplotlib.pyplot as plt

    plt.figure()
    plt.figure()
    factor_pdf.reclaim_memory()
    assert plt.get_fignums() == []
