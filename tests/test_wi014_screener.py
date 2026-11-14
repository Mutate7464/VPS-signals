"""WI-014 — E5 factor screener: shortlist generation contract + CLI behaviour.

Everything here runs on a tiny synthetic fixture (features spine + raw OHLCV
written into `tmp_path`), so the suite never reads the real multi-hundred-MB
feature panels and never writes into `reports/`. The fixture deliberately mixes
four cases the contract has to separate:

    AAA, BBB, DDD  fresh feature row on the market scoring date
    CCC            feature spine stops 5 bars earlier  → stale, not ranked
    EEE            fresh feature row, no raw file      → skipped (no_raw_file)
    GGG (USD)      fresh feature row, 50 raw bars       → skipped (short_history)

Step 1 covers the generator contract (scoring date, eligibility, ranking, schema,
suffixed paths, invalid market writing nothing). Step 3 adds the end-to-end CLI
runs (dry-run, both-market order, CSV+PDF smoke).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
sys.path.insert(0, str(ROOT))

import src.pdf_compiler_factor as factor_pdf  # noqa: E402
from src.factors.e5_baseline import E5_FACTORS, factor_frame  # noqa: E402
from src.market_cli import BOTH, resolve_markets  # noqa: E402

IC_STUB = """# WI-009 — E5 factor baseline ({market})

## Single-factor within-date rank-IC

| Factor | mean IC | t | dates |
| :--- | ---: | ---: | ---: |
| `mom_12_1` | {mom} | +6.00 | 2869 |
| `rev_1m` | +0.0025 | +0.90 | 2869 |
| `vol_20` | -0.0158 | -5.11 | 2869 |
| `amihud_20` | -0.0085 | -3.88 | 2869 |
| `log_dollar_vol_20` | +0.0052 | +2.65 | 2869 |

## Multivariate (purged WF, 20d embargo)

| Model | mean IC | t | dates |
| :--- | ---: | ---: | ---: |
| `ridge` | +0.0055 | +1.86 | 1722 |
"""

USD_END = pd.Timestamp("2026-09-23")
CAD_END = pd.Timestamp("2026-09-22")
N_BARS = 320
FRESH_USD = ("AAA", "BBB", "DDD")
STALE_USD = "CCC"
NO_RAW_USD = "EEE"
SHORT_USD = "GGG"


def load_stage_script(name: str):
    """Import `scripts/<name>.py` under a private module name (no side effects)."""
    path = SCRIPTS_DIR / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"wi014_{name}", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def screener():
    return load_stage_script("wi014_screener")


def _bars(n: int, seed: int, drift: float, end: pd.Timestamp) -> pd.DataFrame:
    """Deterministic OHLCV ending on `end`; `drift` separates the momentum ranks."""
    rng = np.random.default_rng(seed)
    ret = drift + 0.008 * rng.standard_normal(n)
    close = 40.0 * np.exp(np.cumsum(ret))
    spread = close * 0.012 + 0.01
    open_ = close * (1.0 + 0.002 * rng.standard_normal(n))
    high = np.maximum.reduce([close + spread, open_, close])
    low = np.minimum.reduce([close - spread, open_, close])
    return pd.DataFrame(
        {
            "date": pd.bdate_range(end=end, periods=n),
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": np.exp(12.0 + 0.3 * rng.standard_normal(n)),
        }
    )


@pytest.fixture(scope="module")
def fixture(tmp_path_factory):
    """A synthetic two-market project tree: features spine, raw bars, reports dir."""
    root = tmp_path_factory.mktemp("wi014_fixture")
    features_dir = root / "features"
    raw_dir = root / "raw_ohlcv"
    reports_dir = root / "reports"
    for directory in (features_dir, raw_dir, reports_dir):
        directory.mkdir(parents=True, exist_ok=True)

    bars: dict[tuple[str, str], pd.DataFrame] = {}
    spans: dict[str, dict[str, pd.DataFrame]] = {"USD": {}, "CAD": {}}

    plan = [
        ("USD", "AAA", 1, 0.0025, USD_END, N_BARS),
        ("USD", "BBB", 2, 0.0010, USD_END, N_BARS),
        ("USD", "DDD", 3, 0.0002, USD_END, N_BARS),
        ("USD", STALE_USD, 4, 0.0032, USD_END, N_BARS),
        ("USD", SHORT_USD, 6, 0.0004, USD_END, 50),
        ("CAD", "FFF", 7, 0.0018, CAD_END, N_BARS),
        ("CAD", "HHH", 8, 0.0006, CAD_END, N_BARS),
    ]
    for market, symbol, seed, drift, end, n in plan:
        frame = _bars(n, seed=seed, drift=drift, end=end)
        bars[(market, symbol)] = frame
        spans[market][symbol] = frame[["date"]]

    # CCC: raw data reaches the market date, the *feature spine* stops 5 bars earlier.
    stale_dates = bars[("USD", STALE_USD)]["date"].iloc[:-5]
    spans["USD"][STALE_USD] = pd.DataFrame({"date": stale_dates.to_numpy()})
    # EEE: features are fresh, but no raw file exists at all.
    spans["USD"][NO_RAW_USD] = bars[("USD", "AAA")][["date"]].copy()

    ic_md = {}
    for market, mom_ic in (("USD", "+0.0209"), ("CAD", "+0.0271")):
        text = IC_STUB.format(market=market, mom=mom_ic)
        ic_md[market] = text
        (reports_dir / f"wi012_e5_baseline_{market}_h15.md").write_text(text)

    for market, per_symbol in spans.items():
        rows = [
            {"date": date, "symbol": symbol, "market": market}
            for symbol, frame in per_symbol.items()
            for date in frame["date"]
        ]
        panel = pd.DataFrame(rows).sort_values(["date", "symbol"]).reset_index(drop=True)
        panel.to_parquet(features_dir / f"features_{market}.parquet", index=False)

    for (market, symbol), frame in bars.items():
        target = raw_dir / f"market={market}"
        target.mkdir(parents=True, exist_ok=True)
        frame.to_parquet(target / f"symbol={symbol}.parquet", index=False)

    return {
        "root": root,
        "features_dir": features_dir,
        "raw_dir": raw_dir,
        "reports_dir": reports_dir,
        "bars": bars,
        "ic_md": ic_md,
    }


@pytest.fixture
def patched(screener, fixture, monkeypatch, tmp_path):
    """Point the stage script at the synthetic tree, with a per-test `reports/`."""
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    # The per-test reports dir starts with only the published IC reports (the
    # frozen read-only inputs); every other file in it is the run's own output.
    for market, text in fixture["ic_md"].items():
        (reports_dir / f"wi012_e5_baseline_{market}_h15.md").write_text(text)
    monkeypatch.setattr(screener, "FEATURES_DIR", fixture["features_dir"])
    monkeypatch.setattr(screener, "RAW_DIR", fixture["raw_dir"])
    monkeypatch.setattr(screener, "REPORTS", reports_dir)
    return {**fixture, "reports_dir": reports_dir}


def _written(reports_dir: Path) -> set[str]:
    """Files a run produced (the copies of the frozen IC reports are excluded)."""
    return {p.name for p in reports_dir.iterdir() if not p.name.startswith("wi012_e5_baseline_")}


def _expected_mom(screener, fixture, market: str, symbol: str) -> float:
    """The E5 `mom_12_1` the shared definition yields for the symbol's latest bar."""
    raw = screener.load_raw_symbol(market, symbol, raw_dir=fixture["raw_dir"])
    return float(factor_frame(raw).iloc[-1]["mom_12_1"])


# --------------------------------------------------------------------------- #
# Market selection (default BOTH, explicit single, invalid rejected)
# --------------------------------------------------------------------------- #
def test_default_selection_is_usd_then_cad(screener):
    args = screener.build_parser().parse_args([])
    assert args.market is None, "omitting --market must mean both markets"
    assert resolve_markets(args.market) == ["USD", "CAD"]
    assert BOTH == ("USD", "CAD")
    assert screener.DEFAULT_TOP_N == 10


def test_explicit_market_selects_one(screener, patched, capsys):
    rc = screener.main(["--market", "CAD", "--top-n", "1"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "markets=CAD" in out
    assert "CAD" in (patched["reports_dir"] / "wi014_shortlist_CAD_1.csv").name
    assert not (patched["reports_dir"] / "wi014_shortlist_USD_1.csv").exists()


def test_invalid_market_writes_nothing(screener, patched, capsys):
    rc = screener.main(["--market", "XYZ"])
    err = capsys.readouterr().err
    assert rc != 0
    assert "invalid market" in err
    assert _written(patched["reports_dir"]) == set()


def test_missing_scoring_date_writes_nothing(screener, patched):
    """A --date no symbol's latest feature row lands on is an error before any write."""
    with pytest.raises(ValueError):
        screener.generate_shortlist("USD", as_of="2026-09-22", features_dir=patched["features_dir"],
                                   raw_dir=patched["raw_dir"])
    assert screener.main(["--market", "USD", "--date", "2026-09-22"]) != 0
    assert _written(patched["reports_dir"]) == set()


# --------------------------------------------------------------------------- #
# Freshness spine + eligibility
# --------------------------------------------------------------------------- #
def test_scoring_date_is_latest_feature_date(screener, patched):
    cross = screener.resolve_market_cross("USD", features_dir=patched["features_dir"])
    assert cross.scoring_date == USD_END
    assert screener.resolve_scoring_date(patched["features_dir"] / "features_USD.parquet") == USD_END
    cad = screener.resolve_market_cross("CAD", features_dir=patched["features_dir"])
    assert cad.scoring_date == CAD_END


def test_stale_and_missing_symbols_are_excluded_not_ranked(screener, patched):
    result = screener.generate_shortlist("USD", top_n=10, features_dir=patched["features_dir"],
                                        raw_dir=patched["raw_dir"])
    symbols = set(result.shortlist["symbol"])
    assert STALE_USD not in symbols, "a symbol whose feature spine is stale must not be ranked"
    assert NO_RAW_USD not in symbols
    assert SHORT_USD not in symbols
    assert symbols == set(FRESH_USD)
    assert set(result.stale) == {STALE_USD}
    assert result.cross_section.skipped["no_raw_file"] == 1
    assert result.cross_section.skipped["short_history"] == 1
    assert result.eligible_symbols == 5  # AAA, BBB, DDD, EEE, GGG all have a row on the date


def test_date_flag_pins_the_scoring_date(screener, patched):
    """`--date` pins the cross-section to an older session: only that session's rows rank."""
    spine = pd.read_parquet(patched["features_dir"] / "features_USD.parquet")
    stale_date = pd.Timestamp(spine.loc[spine["symbol"] == STALE_USD, "date"].max())
    pinned = stale_date.strftime("%Y-%m-%d")
    cross = screener.resolve_market_cross("USD", features_dir=patched["features_dir"], as_of=pinned)
    assert cross.scoring_date == stale_date
    assert cross.eligible == [STALE_USD], "only symbols with a row on the pinned date are eligible"

    result = screener.generate_shortlist("USD", top_n=10, as_of=pinned,
                                        features_dir=patched["features_dir"], raw_dir=patched["raw_dir"])
    assert result.shortlist["symbol"].tolist() == [STALE_USD]


# --------------------------------------------------------------------------- #
# Ranking + schema
# --------------------------------------------------------------------------- #
def test_ranking_is_mom_12_1_descending(screener, patched):
    result = screener.generate_shortlist("USD", top_n=10, features_dir=patched["features_dir"],
                                        raw_dir=patched["raw_dir"])
    shortlist = result.shortlist
    assert list(shortlist["rank"]) == [1, 2, 3]
    assert shortlist["mom_12_1"].is_monotonic_decreasing
    expected = sorted(FRESH_USD, key=lambda s: _expected_mom(screener, patched, "USD", s), reverse=True)
    assert list(shortlist["symbol"]) == expected
    assert set(shortlist.columns) == set(screener.SHORTLIST_COLUMNS)
    assert list(shortlist.columns) == ["rank", "symbol", *E5_FACTORS, "scoring_date"]


def test_factor_values_come_from_the_shared_e5_definitions(screener, patched):
    result = screener.generate_shortlist("USD", top_n=10, features_dir=patched["features_dir"],
                                        raw_dir=patched["raw_dir"])
    raw = screener.load_raw_symbol("USD", "AAA", raw_dir=patched["raw_dir"])
    latest = factor_frame(raw).iloc[-1]
    row = result.shortlist[result.shortlist["symbol"] == "AAA"].iloc[0]
    for name in E5_FACTORS:
        assert row[name] == pytest.approx(float(latest[name]), rel=1e-6)


def test_top_n_caps_rows_and_scores_the_market_date(screener, patched):
    result = screener.generate_shortlist("USD", top_n=2, features_dir=patched["features_dir"],
                                        raw_dir=patched["raw_dir"])
    assert len(result.shortlist) == 2
    assert set(result.shortlist["scoring_date"]) == {USD_END.strftime("%Y-%m-%d")}


# --------------------------------------------------------------------------- #
# Output paths + CSV release
# --------------------------------------------------------------------------- #
def test_output_paths_are_market_suffixed(screener):
    csv_path = screener.shortlist_csv_path("CAD", 10)
    pdf_path = screener.tearsheet_pdf_path("USD", pd.Timestamp("2026-09-23"))
    assert csv_path.name == "wi014_shortlist_CAD_10.csv"
    assert pdf_path.name == "screener_factor_USD_20260923.pdf"
    assert csv_path.parent.name == "reports"
    for market in BOTH:
        assert f"_{market}_" in screener.shortlist_csv_path(market, 10).name
        assert f"_{market}_" in screener.tearsheet_pdf_path(market, USD_END).name


def test_no_module_path_constant_is_a_writable_report_file(screener):
    """Only directories are module-level paths: every report target is built suffixed."""
    paths = [value for value in vars(screener).values() if isinstance(value, Path)]
    assert paths, "expected module-level path constants"
    for path in paths:
        assert path.suffix == "", f"{path} looks like a file; report targets must go through the suffix helpers"


def test_write_shortlist_csv_round_trips_schema(screener, patched):
    result = screener.generate_shortlist("USD", top_n=2, features_dir=patched["features_dir"],
                                        raw_dir=patched["raw_dir"])
    path = screener.write_shortlist_csv(result.shortlist, patched["reports_dir"] / "wi014_shortlist_USD_2.csv")
    back = pd.read_csv(path)
    assert list(back.columns) == screener.SHORTLIST_COLUMNS
    assert len(back) == 2
    assert back["rank"].tolist() == [1, 2]
    assert (back["scoring_date"] == USD_END.strftime("%Y-%m-%d")).all()
    assert back["symbol"].is_unique


def test_generated_csv_matches_ranking_contract(screener, patched, capsys):
    rc = screener.main(["--market", "USD", "--top-n", "3"])
    assert rc == 0
    csv_path = patched["reports_dir"] / "wi014_shortlist_USD_3.csv"
    assert csv_path.exists()
    back = pd.read_csv(csv_path)
    assert list(back.columns) == screener.SHORTLIST_COLUMNS
    assert back["mom_12_1"].is_monotonic_decreasing
    assert "scoring_date=2026-09-23" in capsys.readouterr().out
    # top-n=3 with 3 fresh symbols: every eligible name is present, in rank order.
    assert back["symbol"].tolist() == sorted(
        FRESH_USD, key=lambda s: _expected_mom(screener, patched, "USD", s), reverse=True
    )


# --------------------------------------------------------------------------- #
# Step 3 — end-to-end CLI: dry run, both markets, CSV + PDF per market
# --------------------------------------------------------------------------- #
def test_dry_run_prints_both_markets_in_order_and_writes_nothing(screener, patched, capsys):
    rc = screener.main(["--dry-run"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "markets=USD, CAD" in out
    assert "dry-run 1/2 market=USD" in out and "dry-run 2/2 market=CAD" in out
    assert out.index("market=USD") < out.index("market=CAD")
    assert _written(patched["reports_dir"]) == set(), "--dry-run must not write"

    usd_line = next(line for line in out.splitlines() if "market=USD" in line)
    cad_line = next(line for line in out.splitlines() if "market=CAD" in line)
    assert "wi014_shortlist_USD_10.csv" in usd_line and "screener_factor_USD_20260923.pdf" in usd_line
    assert "wi014_shortlist_CAD_10.csv" in cad_line and "screener_factor_CAD_20260922.pdf" in cad_line
    assert "nothing written" in usd_line
    # only market-suffixed paths: no unsuffixed report name anywhere in the plan
    for line in out.splitlines():
        for token in ("wi014_shortlist_", "screener_factor_"):
            assert token not in line or "_USD" in line or "_CAD" in line


def test_dry_run_single_market_reports_one_line(screener, patched, capsys):
    rc = screener.main(["--market", "CAD", "--top-n", "3", "--dry-run"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "1/1 market=CAD" in out
    assert "wi014_shortlist_CAD_3.csv" in out
    assert "market=USD" not in out
    assert _written(patched["reports_dir"]) == set()


def test_invalid_market_dry_run_writes_nothing(screener, patched, capsys):
    rc = screener.main(["--market", "XYZ", "--dry-run"])
    assert rc != 0
    assert "invalid market" in capsys.readouterr().err
    assert _written(patched["reports_dir"]) == set()


def test_default_run_writes_csv_and_pdf_for_both_markets(screener, patched, capsys):
    rc = screener.main([])
    out = capsys.readouterr().out
    assert rc == 0
    assert _written(patched["reports_dir"]) == {
        "wi014_shortlist_USD_10.csv",
        "wi014_shortlist_CAD_10.csv",
        "screener_factor_USD_20260923.pdf",
        "screener_factor_CAD_20260922.pdf",
    }
    for name in ("wi014_shortlist_USD_10.csv", "wi014_shortlist_CAD_10.csv"):
        csv_path = patched["reports_dir"] / name
        assert csv_path.stat().st_size > 0
        assert list(pd.read_csv(csv_path).columns) == screener.SHORTLIST_COLUMNS
    for name, expected_pages in (("screener_factor_USD_20260923.pdf", 4),
                                 ("screener_factor_CAD_20260922.pdf", 3)):
        pdf_path = patched["reports_dir"] / name
        assert pdf_path.read_bytes()[:4] == b"%PDF"
        assert pdf_path.stat().st_size > 5_000, "PDF must be non-empty"
        assert f"{expected_pages} pages" in out
    assert "tickers=" in out


def test_small_top_n_writes_both_output_types(screener, patched):
    rc = screener.main(["--market", "USD", "--top-n", "2"])
    assert rc == 0
    written = _written(patched["reports_dir"])
    assert written == {"wi014_shortlist_USD_2.csv", "screener_factor_USD_20260923.pdf"}
    back = pd.read_csv(patched["reports_dir"] / "wi014_shortlist_USD_2.csv")
    assert back["rank"].tolist() == [1, 2]
    assert (patched["reports_dir"] / "screener_factor_USD_20260923.pdf").stat().st_size > 5_000


def test_run_fails_before_writing_when_the_ic_report_is_missing(screener, patched, capsys):
    """No published IC table → no CSV either: the summary may not quote invented numbers."""
    (patched["reports_dir"] / "wi012_e5_baseline_USD_h15.md").unlink()
    rc = screener.main(["--market", "USD"])
    assert rc != 0
    assert "missing E5 baseline report" in capsys.readouterr().err
    assert _written(patched["reports_dir"]) == set()


def test_ranking_rule_comes_from_the_renderer(screener):
    """The CSV run and the tearsheet print the same rule from one definition."""
    assert screener.RANK_FACTOR == factor_pdf.RANK_FACTOR == "mom_12_1"
    assert screener.RANKING_RULE == factor_pdf.RANKING_RULE
    assert "descending" in screener.RANKING_RULE
