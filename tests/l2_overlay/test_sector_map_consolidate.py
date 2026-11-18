"""WI-073 — sector-map consolidation tests (pure; no network, no real writes)."""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.l2_overlay import sector_map_consolidate as smc            # noqa: E402
from src.swing_bsh import binary_features_ext as bfe                # noqa: E402

BASE = Path(__file__).resolve().parents[2]
CONFIG_ROWS, IBKR_ROWS = 808, 857
PANEL = {"USD": ["AAPL", "LULU", "TSLA", "SMH"], "CAD": ["AAPL", "ABX", "XEG", "NA"]}


def _frame(rows) -> pd.DataFrame:
    return pd.DataFrame([dict(zip(smc.COLUMNS, r)) for r in rows], columns=list(smc.COLUMNS))


CONFIG = _frame([("AAPL", "USD", "Hardware", "Hardware", "", "Apple Inc", "52"),
                 ("LULU", "USD", "Consumer Cyclical", "", "", "Lululemon", "56"),
                 ("TSLA", "USD", "", "", "", "Tesla Inc", "0"),
                 ("AAPL", "CAD", "Technology", "", "", "Apple Inc", "52"),
                 ("ABX", "CAD", "Basic Materials", "", "", "Barrick", "40")])
IBKR = _frame([("AAPL", "USD", "Hardware", "", "", "Apple Inc", "52"),
               ("LULU", "USD", "Retail - Cyclical", "", "", "Lululemon", "56"),
               ("AAPL", "CAD", "Hardware", "", "", "Apple Inc", "52"),
               ("ABX", "CAD", "Metals & Mining", "", "", "Barrick", "40"),
               ("XEG", "CAD", "Energy", "", "", "iShares Energy", "0")])


def test_precedence_config_wins_and_blanks_never_overwrite():
    canonical, conflicts = smc.consolidate(CONFIG, IBKR, PANEL, {})
    row = canonical.set_index(["symbol", "market"]).loc[("LULU", "USD")]
    assert row["sector"] == "Consumer Cyclical"                     # config wins over IBKR
    assert canonical.set_index(["symbol", "market"]).loc[("XEG", "CAD")]["sector"] == "Energy"
    # config blank vs IBKR non-blank: IBKR fills the blank (blank never overwrites non-blank)
    assert canonical.set_index(["symbol", "market"]).loc[("AAPL", "CAD")]["sector"] == "Technology"
    got = {(r["symbol"], r["market"]): r for r in conflicts.to_dict("records")}
    assert set(got) == {("LULU", "USD"), ("AAPL", "CAD"), ("ABX", "CAD")}
    assert got[("LULU", "USD")] == {"symbol": "LULU", "market": "USD",
                                    "config_sector": "Consumer Cyclical",
                                    "ibkr_sector": "Retail - Cyclical", "source_won": "config"}


def test_pick_sector_never_lets_a_blank_overwrite():
    assert smc.pick_sector("", "Energy") == ("Energy", "ibkr")
    assert smc.pick_sector("Banks", "") == ("Banks", "config")
    assert smc.pick_sector("", "", "") == ("", "")
    assert smc.pick_sector("Hardware", "Banks", "Energy") == ("Hardware", "config")


def test_coverage_invariant_every_panel_symbol_present():
    canonical, _ = smc.consolidate(CONFIG, IBKR, PANEL, {("NA", "CAD"): "Drug Manufacturers"})
    got = set(map(tuple, canonical[["symbol", "market"]].to_numpy()))
    for market, syms in PANEL.items():
        for symbol in syms:
            assert (symbol, market) in got, f"{symbol}/{market} missing from canonical"
    stats = smc.coverage(canonical, PANEL)
    assert stats["USD"]["panel"] == 4 and stats["CAD"]["panel"] == 4
    assert stats["CAD"]["non_blank"] == 4                             # ABX cfg, XEG ibkr, NA network
    # SMH is a panel symbol absent from both maps: the row is kept with a blank sector. WI-073 §1
    # forbids inventing a sector (no ETF constituent replace), so the blank is the DoD residual.
    assert canonical.set_index(["symbol", "market"]).loc[("SMH", "USD")]["sector"] == ""
    blanks = smc.unresolved_blanks(canonical, PANEL)
    assert blanks == [{"symbol": "SMH", "market": "USD"}, {"symbol": "TSLA", "market": "USD"}]
    assert "PASS" not in smc.wi070_readiness(blanks)
    assert "TSLA.USD" in smc.wi070_readiness(blanks)


def test_network_fill_beats_nothing_and_never_beats_a_source():
    canonical, _ = smc.consolidate(CONFIG, IBKR, PANEL, {("TSLA", "USD"): "Vehicles & Parts",
                                                         ("LULU", "USD"): "Banks"})
    idx = canonical.set_index(["symbol", "market"])["sector"]
    assert idx.loc[("TSLA", "USD")] == "Vehicles & Parts"
    assert idx.loc[("LULU", "USD")] == "Consumer Cyclical"            # config still wins


def test_consumer_contract_columns_and_round_trip(tmp_path):
    canonical, conflicts = smc.consolidate(CONFIG, IBKR, PANEL, {})
    assert list(canonical.columns) == list(smc.COLUMNS)               # columns unchanged
    assert list(conflicts.columns) == list(smc.CONFLICT_COLUMNS)
    out = tmp_path / "sector_map.csv"
    canonical.to_csv(out, index=False)
    real = pd.read_csv(BASE / "config/sector_map.csv", dtype=str)
    assert list(real.columns) == list(canonical.columns)              # matches the shipped header
    assert smc.CONFIG_MAP_PATH.read_text().splitlines()[0] == ",".join(smc.COLUMNS)
    mapping = bfe.load_sector_map(out)                                # consumer reads it unchanged
    # the consumer keys by symbol alone (one market per symbol is its documented contract);
    # the file itself stays per-market, so the round trip must preserve every distinct symbol.
    # Named residual (DoD "residual named"): the literal ticker "NA" is written to the file, but the
    # read-only consumer's default `na_values` parses it as NaN — that one symbol cannot be keyed.
    keys = {str(k) for k in mapping}
    assert set(canonical["symbol"]) - {"NA"} <= keys                  # everything else round-trips
    assert keys - {"nan"} <= set(canonical["symbol"])
    assert "NA" in set(canonical["symbol"]) and "nan" in keys         # residual named, not silent
    assert mapping["AAPL"] in {"Hardware", "Technology"}              # AAPL/USD vs AAPL/CAD forms
    assert mapping["XEG"] == "Energy" and bfe.MAX_SECTORS == 12


def test_conflicts_file_completeness_and_report_lines(tmp_path):
    canonical, conflicts = smc.consolidate(CONFIG, IBKR, PANEL, {})
    assert (conflicts["source_won"] == "config").all()
    assert not conflicts["config_sector"].str.strip().eq("").any()
    assert not conflicts["ibkr_sector"].str.strip().eq("").any()
    report = smc.report_markdown(canonical, conflicts, PANEL,
                                 before_stats={"USD": {"panel": 4, "mapped": 2, "non_blank": 2}},
                                 network_fill={("TSLA", "USD"): "Vehicles & Parts"}, attempts=2)
    for token in ("Coverage per market", "appear", "Conflicts recorded", "WI-070 readiness",
                  "network gap-fill attempts: 2", "Unresolved blanks:"):
        assert token in report
    assert "| USD | 4 | 2 | 2 | 4 |" in report
    assert "| CAD | 4 | 0 | 0 |" in report


class _Coro:
    """Stand-in for the `reqContractDetailsAsync` coroutine (carries the symbol, closes quietly)."""

    def __init__(self, symbol):
        self.symbol = symbol

    def close(self):
        pass


class _FakeIB:
    """Minimal IB stub: `TSLA` has metadata, `AAPL` has none, `BOOM` errors."""

    def __init__(self, fail_connect: bool = False):
        self.connected, self.fail_connect = False, fail_connect

    def connect(self, *a, **k):
        if self.fail_connect:
            raise ConnectionRefusedError("no gateway")
        self.connected = True

    def disconnect(self):
        self.connected = False

    def reqContractDetailsAsync(self, contract):
        return _Coro(contract.symbol)

    def run(self, coro, timeout=None):
        try:
            if coro.symbol == "BOOM":
                raise TimeoutError("no metadata")
            if coro.symbol == "TSLA":
                return [type("D", (), {"contract": type("C", (), {"sector": "Vehicles & Parts"})})()]
            return []
        finally:
            coro.close()


@pytest.fixture()
def fake_ib(monkeypatch):
    import types
    module = types.ModuleType("ib_async")
    module.IB = lambda *a, **k: _FakeIB()
    module.Stock = lambda symbol, *a, **k: type("S", (), {"symbol": symbol})()
    monkeypatch.setitem(sys.modules, "ib_async", module)
    return module


def test_fetch_missing_ibkr_extracts_sector_and_survives_errors(fake_ib):
    fill = smc.fetch_missing_ibkr({"USD": ["TSLA", "AAPL", "BOOM"]}, ib=_FakeIB())
    assert fill == {("TSLA", "USD"): "Vehicles & Parts"}          # miss/error rows stay blank
    assert smc.fetch_missing_ibkr({}, ib=_FakeIB()) == {}          # nothing wanted → no request


def test_fetch_missing_ibkr_returns_empty_when_no_gateway(fake_ib, monkeypatch):
    # the module's own connect site: a gateway that refuses the connection yields blanks, not a raise
    fake_ib.IB = lambda *a, **k: _FakeIB(fail_connect=True)
    assert smc.fetch_missing_ibkr({"USD": ["TSLA"]}) == {}
    # no ib_async at all → the guarded import fails inside the block and is swallowed
    monkeypatch.setitem(sys.modules, "ib_async", None)
    assert smc.fetch_missing_ibkr({"USD": ["TSLA"]}, port=1, connect_timeout=0.01) == {}


def test_output_roots_are_named_constants_and_only_one_connect_site():
    src = (BASE / "src/l2_overlay/sector_map_consolidate.py").read_text()
    assert "data/sector_map_conflicts.csv" in src and "reports/sector_map_consolidation.md" in src
    tree = ast.parse(src)
    connects = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
                and isinstance(n.func, ast.Attribute) and n.func.attr == "connect"]
    assert len(connects) == 1                                     # the one declared network path
    assert not [n for n in ast.walk(tree) if isinstance(n, ast.Call)
                and isinstance(n.func, ast.Attribute) and n.func.attr == "read_parquet"]
