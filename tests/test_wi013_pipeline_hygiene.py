"""WI-013 — two-market parametrization: market selection + market-suffixed paths.

Two contracts are tested here:

1. **Which markets a run touches** (`src/market_cli.resolve_markets`): an omitted
   `--market` means *both*, US D then CAD; an explicit `--market USD|CAD` means
   exactly that one; anything else is rejected before any work runs.
2. **Where a run may write**: every output path a stage script resolves is
   market-suffixed, so a run can never overwrite a frozen unsuffixed gate report
   (WI-012 finding F-5), and an explicit `--out`-style override cannot smuggle an
   unsuffixed or cross-market path past the guard.

The tests are static and cheap: they import the stage scripts and call their path
helpers / parsers, so they never read the multi-hundred-MB feature parquets.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
REPORTS_DIR = ROOT / "reports"
sys.path.insert(0, str(ROOT))

from src.market_cli import (  # noqa: E402
    BOTH,
    MARKET_CHOICES,
    MarketSelectionError,
    add_market_argument,
    cli_markets,
    is_market_suffixed,
    market_suffix,
    report_path,
    resolve_markets,
    resolve_output,
    run_markets,
    suffix_path,
)

WI011_SCRIPTS = (
    "wi011_preflight",
    "wi011_conditions",
    "wi011_indicator_association",
    "wi011_condition_expectancy",
    "wi011_ts_momentum",
    "wi011_tradeable_conditions",
)


def load_stage_script(name: str):
    """Import `scripts/<name>.py` under a private module name (no side effects)."""
    path = SCRIPTS_DIR / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"wi013_{name}", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def market_agnostic_paths(module) -> list[Path]:
    """Every module-level `Path`-valued constant in a stage script."""
    return [
        value
        for value in vars(module).values()
        if isinstance(value, Path)
    ]


# --------------------------------------------------------------------------- #
# market_cli — default BOTH (USD then CAD), explicit single, invalid rejected
# --------------------------------------------------------------------------- #
def test_market_cli_default_selection_is_usd_then_cad():
    assert resolve_markets(None) == ["USD", "CAD"]
    assert resolve_markets("") == ["USD", "CAD"]
    assert resolve_markets("both") == ["USD", "CAD"]
    assert tuple(resolve_markets(None)) == BOTH


def test_market_cli_explicit_single_market_selects_only_itself():
    assert resolve_markets("USD") == ["USD"]
    assert resolve_markets("CAD") == ["CAD"]
    assert resolve_markets(" cad ") == ["CAD"]
    for market in MARKET_CHOICES:
        assert resolve_markets(market) != list(BOTH)


@pytest.mark.parametrize("bad", ["EUR", "US", "cadd", "USDCAD", "1", "CAD;USD"])
def test_market_cli_rejects_invalid_market_values(bad):
    with pytest.raises(MarketSelectionError):
        resolve_markets(bad)


def test_market_cli_cli_wrapper_fails_closed_before_any_work(capsys):
    assert cli_markets("EUR", prog="demo") is None
    assert "invalid market" in capsys.readouterr().err
    assert cli_markets(None) == ["USD", "CAD"]


def test_market_cli_flag_defaults_to_both_via_the_shared_argument():
    ap = argparse.ArgumentParser()
    add_market_argument(ap)
    args = ap.parse_args([])
    assert args.market is None and resolve_markets(args.market) == ["USD", "CAD"]
    assert resolve_markets(ap.parse_args(["--market", "CAD"]).market) == ["CAD"]


def test_market_cli_run_markets_keeps_usd_first_and_reports_the_first_failure():
    seen: list[str] = []
    assert run_markets(["USD", "CAD"], lambda m: seen.append(m) or 0) == 0
    assert seen == ["USD", "CAD"]
    seen.clear()
    assert run_markets(["USD", "CAD"], lambda m: seen.append(m) or (3 if m == "USD" else 0)) == 3
    assert seen == ["USD", "CAD"]  # a failing market never skips the other


# --------------------------------------------------------------------------- #
# market_cli — output routing
# --------------------------------------------------------------------------- #
def test_market_cli_suffix_path_inserts_the_market_and_is_idempotent():
    assert suffix_path("reports/wi009c_probe.md", "CAD") == Path("reports/wi009c_probe_CAD.md")
    assert suffix_path("reports/wi009c_probe_CAD.md", "CAD") == Path("reports/wi009c_probe_CAD.md")
    assert suffix_path("logs/wi009b_train.out", "USD") == Path("logs/wi009b_train_USD.out")
    assert suffix_path("data/wi009c_oof.parquet", "cad") == Path("data/wi009c_oof_CAD.parquet")


def test_market_cli_rejects_a_cross_market_output_override():
    with pytest.raises(MarketSelectionError):
        suffix_path("reports/wi009c_probe_CAD.md", "USD")
    with pytest.raises(MarketSelectionError):
        resolve_output("reports/wi009c_probe_USD.md", "CAD", what="--out")


def test_market_cli_resolve_output_suffixes_unsuffixed_overrides():
    assert resolve_output("tmp/note.md", "CAD") == Path("tmp/note_CAD.md")
    assert resolve_output("tmp/note_USD.md", "USD") == Path("tmp/note_USD.md")


def test_market_cli_report_path_is_suffixed_and_refuses_a_suffixed_stem():
    for market in MARKET_CHOICES:
        p = report_path(REPORTS_DIR, "wi011_preflight", market)
        assert p.name == f"wi011_preflight_{market}.md"
        assert is_market_suffixed(p, market)
        assert not is_market_suffixed(p, "CAD" if market == "USD" else "USD")
    with pytest.raises(MarketSelectionError):
        report_path(REPORTS_DIR, "wi011_preflight_CAD", "CAD")


def test_market_cli_market_suffix_normalizes_case():
    assert market_suffix("cad") == "_CAD"
    assert market_suffix("Usd") == "_USD"
    with pytest.raises(MarketSelectionError):
        market_suffix("eur")


# --------------------------------------------------------------------------- #
# WI-011 writers — every output is market-suffixed (F-3 + F-5)
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("script_name", WI011_SCRIPTS)
@pytest.mark.parametrize("market", MARKET_CHOICES)
def test_wi011_report_paths_are_market_suffixed_for_every_writer(script_name, market):
    module = load_stage_script(script_name)
    outputs = module.paths(market)
    assert outputs, f"{script_name} declares no output paths"
    for kind, path in outputs.items():
        assert is_market_suffixed(path, market), f"{script_name}.{kind} → {path} is not {market}-suffixed"


@pytest.mark.parametrize("script_name", WI011_SCRIPTS)
def test_wi011_report_paths_differ_between_markets(script_name):
    module = load_stage_script(script_name)
    usd, cad = module.paths("USD"), module.paths("CAD")
    assert set(usd) == set(cad)
    for kind in usd:
        assert usd[kind] != cad[kind]


def test_wi011_report_paths_never_resolve_to_an_unsuffixed_target(tmp_path):
    """An implicit both-market run writes two distinct suffixed files per writer."""
    module = load_stage_script("wi011_tradeable_conditions")
    written = []
    for market in resolve_markets(None):
        written += list(module.paths(market).values())
    assert len(written) == len(set(written)) == 4
    assert all(p.stem.upper().endswith(("_USD", "_CAD")) for p in written)
    assert not any(p.name == "wi011_tradeable_conditions.md" for p in written)
    assert not any(p.name == "wi011_decision_rules.md" for p in written)


@pytest.mark.parametrize("script_name", WI011_SCRIPTS)
def test_wi011_report_paths_leave_no_unsuffixed_module_constant(script_name):
    """No stage script may keep a module-level path constant into reports/."""
    module = load_stage_script(script_name)
    offenders = [
        p
        for p in market_agnostic_paths(module)
        if p.suffix and REPORTS_DIR in p.parents and not _any_market_suffix(p)
    ]
    assert not offenders, f"{script_name} keeps unsuffixed report constants: {offenders}"


@pytest.mark.parametrize("script_name", WI011_SCRIPTS)
def test_wi011_cli_defaults_to_both_markets(script_name):
    module = load_stage_script(script_name)
    args = module.build_parser().parse_args([])
    assert resolve_markets(args.market) == ["USD", "CAD"]
    assert resolve_markets(module.build_parser().parse_args(["--market", "USD"]).market) == ["USD"]
    with pytest.raises(MarketSelectionError):
        resolve_markets(module.build_parser().parse_args(["--market", "EUR"]).market)


def test_wi011_module_constant_market_is_gone():
    """F-3: `src/wi011.MARKET` must not come back as an implicit default."""
    import src.wi011 as wi011

    assert not hasattr(wi011, "MARKET")


def test_wi011_selection_path_is_market_specific():
    from src.wi011.conditions import load_selected_indicators, selection_path

    assert selection_path("USD").name == "wi011_selected_indicators_USD.json"
    assert selection_path("CAD").name == "wi011_selected_indicators_CAD.json"
    assert load_selected_indicators("USD") == [] or isinstance(load_selected_indicators("USD"), list)
    with pytest.raises(ValueError):
        load_selected_indicators()


def _any_market_suffix(path: Path) -> bool:
    return any(is_market_suffixed(path, market) for market in MARKET_CHOICES)


# --------------------------------------------------------------------------- #
# Steps 1–2 writers — every stage script routes output per market (F-5)
# --------------------------------------------------------------------------- #
STEP2_SCRIPTS = (
    "probe_wi009c",
    "train_wi009c",
    "evaluate_wi009c",
    "wi009b_launch",
    "rank_assets",
    "train_contrastive",
    "check_wi009c_inputs",
)
ALL_WRITER_SCRIPTS = WI011_SCRIPTS + STEP2_SCRIPTS


def script_parser(module):
    """The script's parser, whatever helper name it exposes."""
    builder = getattr(module, "build_parser", None)
    if builder is not None:
        return builder()
    raise AssertionError("stage script exposes no build_parser()")


@pytest.mark.parametrize("script_name", ALL_WRITER_SCRIPTS)
@pytest.mark.parametrize("market", MARKET_CHOICES)
def test_report_paths_are_market_suffixed_for_every_step1_step2_writer(script_name, market):
    module = load_stage_script(script_name)
    outputs = module.paths(market)
    assert outputs, f"{script_name} declares no paths"
    for kind, path in outputs.items():
        assert is_market_suffixed(path, market), f"{script_name}.{kind} → {path} is not {market}-suffixed"


@pytest.mark.parametrize("script_name", ALL_WRITER_SCRIPTS)
def test_report_paths_default_to_both_markets_and_reject_invalid(script_name):
    module = load_stage_script(script_name)
    parser = script_parser(module)
    assert resolve_markets(parser.parse_args([]).market) == ["USD", "CAD"]
    assert resolve_markets(parser.parse_args(["--market", "CAD"]).market) == ["CAD"]
    with pytest.raises(MarketSelectionError):
        resolve_markets(parser.parse_args(["--market", "EUR"]).market)


@pytest.mark.parametrize("script_name", ALL_WRITER_SCRIPTS)
def test_report_paths_no_unsuffixed_output_is_reachable(script_name):
    """A both-market run resolves two distinct suffixed files for every writer."""
    module = load_stage_script(script_name)
    written = []
    for market in resolve_markets(None):
        written += [p for p in module.paths(market).values()]
    assert len(written) == len(set(written)), f"{script_name} resolves a colliding pair of paths"
    assert all(_any_market_suffix(p) for p in written)
    if script_name == "train_wi009c":
        # F-5: the regression report used to be the unsuffixed frozen gate file.
        assert not any(p.name.startswith("wi009c_regression.md") for p in written)
        assert not any(p.name == "wi009c_regression_smoke.md" for p in written)
        assert {p.name for p in written if p.name.startswith("wi009c_regression")} == {
            "wi009c_regression_USD.json", "wi009c_regression_CAD.json",
            "wi009c_regression_USD.md", "wi009c_regression_CAD.md",
        }
    if script_name == "evaluate_wi009c":
        assert not any(p.name == "wi009c_summary.md" for p in written)
        assert {p.name for p in written if p.name.startswith("wi009c_summary")} == {
            "wi009c_summary_USD.json", "wi009c_summary_CAD.json",
            "wi009c_summary_USD.md", "wi009c_summary_CAD.md",
        }


@pytest.mark.parametrize("script_name", STEP2_SCRIPTS)
def test_report_paths_leave_no_unsuffixed_module_constant(script_name):
    module = load_stage_script(script_name)
    offenders = [
        p
        for p in market_agnostic_paths(module)
        if p.suffix and (REPORTS_DIR in p.parents or "logs" in p.parts) and not _any_market_suffix(p)
    ]
    assert not offenders, f"{script_name} keeps unsuffixed path constants: {offenders}"


def test_report_paths_check_wi009c_inputs_override_is_suffixed(tmp_path, capsys):
    """An explicit `--out` is routed through the suffix guard, not written as given."""
    module = load_stage_script("check_wi009c_inputs")
    features = ROOT / "data" / "features" / "features_CAD.parquet"
    if not features.exists():
        pytest.skip("CAD features artifact not present")
    override = tmp_path / "check.txt"
    rc = module.run_market("CAD", str(override))
    capsys.readouterr()
    assert rc == 0
    assert not override.exists(), "the unsuffixed override must not be the write target"
    assert (tmp_path / "check_CAD.txt").is_file()
    with pytest.raises(MarketSelectionError):
        module.run_market("USD", str(tmp_path / "check_CAD.txt"))


# --------------------------------------------------------------------------- #
# F-2 — the E5 baseline report names its market
# --------------------------------------------------------------------------- #
def test_e5_report_market_names_the_market_in_path_and_body(tmp_path, monkeypatch):
    import pandas as pd

    from src.factors import e5_baseline

    monkeypatch.setattr(e5_baseline, "REPORTS", tmp_path)
    panel = pd.DataFrame(
        {
            "date": pd.bdate_range("2024-01-02", periods=30),
            "symbol": ["X"] * 30,
            "fwd_atr_ret_15": np.linspace(-0.1, 0.1, 30),
        }
    )
    single = {"mom_12_1": (0.05, 3.0, 20), "rev_1m": (-0.01, -1.0, 20)}

    usd = e5_baseline.write_report("USD", panel, 15, single, None)
    cad = e5_baseline.write_report("CAD", panel, 15, single, None)

    assert usd.name == "wi009_e5_baseline_USD.md"
    assert cad.name == "wi009_e5_baseline_CAD.md"
    assert "Compiled on USD" in usd.read_text()
    assert "Compiled on CAD" not in usd.read_text()
    assert "Compiled on CAD" in cad.read_text()
    assert "# WI-009 — E5 factor baseline (USD)" in usd.read_text()
