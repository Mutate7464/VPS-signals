"""WI-066 / WI-072 — xsec top-k screener tests (D-027 §5 (b)): the planted signal is recovered net of
cost, the placebo shows nothing, the CALIB card carries the fold distribution / turnover / stop flag,
and the fold report is mandatory. WI-072 adds the generic union-library column, the widened grids, the
symmetric long/short pass (planted + placebo) and the turnover effect of the wider band. Synthetic only:
no reads or writes under `data/`.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.l2_overlay import costs
from src.l2_overlay import fold_report as foldrep
from src.l2_overlay.constructions import xsec_rank as xr


def _fixture(seed=11, n_dates=120, n_names=25):
    return xr.synthetic_fixture("USD", n_dates=n_dates, n_names=n_names, seed=seed)


def _sim(panel, signal, k=4, band=2.0, horizon=13):
    return xr.simulate(xr.build_entries(panel, signal, k, band, horizon))


def test_rank_scores_are_per_date_percentile_float32():
    panel = _fixture(n_dates=3, n_names=4)
    r = xr.rank_scores(panel, "xsec_vol_rank_cont")
    assert r.dtype == np.float32 and r.shape[0] == len(panel)
    assert np.all((r >= 0.0) & (r <= 1.0))
    assert len(np.unique(r[:4])) == 4                 # one distinct rank per name inside a date


def test_all_three_named_signals_build_a_score_vector():
    panel = _fixture(n_dates=4, n_names=6)
    for signal in xr.SIGNALS:
        v = xr.signal_values(panel, signal)
        assert v.dtype == np.float32 and v.shape[0] == len(panel)
    with pytest.raises(KeyError, match="unknown signal"):
        xr.signal_values(panel, "nope")


def test_unscored_rows_are_never_candidates():
    """PM full-run regression (cycle 41): a date whose scores are all NaN must contribute no
    held rows — argsort over NaN would otherwise select arbitrary unscored names."""
    panel = _fixture(n_dates=6, n_names=5)
    panel.loc[panel["date"] == panel["date"].unique()[0], "xsec_vol_rank_cont"] = np.nan
    entries = xr.build_entries(panel, "xsec_vol_rank_cont", k=2, band=2.0, horizon=13)
    scored_dates = panel.loc[np.isfinite(panel["xsec_vol_rank_cont"]), "date"].unique()
    assert set(entries["date"].unique()) <= set(scored_dates)   # no unscored-date rows at all
    sel = entries.loc[entries["selected"], "date"].unique()
    assert set(sel) <= set(scored_dates)
    with pytest.raises(ValueError, match="no finite scores"):
        nan_panel = panel.copy()
        nan_panel["xsec_vol_rank_cont"] = np.nan
        xr.build_entries(nan_panel, "xsec_vol_rank_cont", k=2, band=2.0, horizon=13)


def test_planted_signal_is_recovered_net_of_cost():
    panel = _fixture()
    for signal in xr.SIGNALS:
        sim = _sim(panel, signal)
        assert sim["gross_edge_bps"] > costs.SINGLE_LEG_BPS   # clears the round trip before cost
        assert sim["net_edge_bps"] > 0.0
        assert sim["fold_report"]["n_folds"] == 5


def test_placebo_shows_nothing():
    panel = _fixture()
    planted = _sim(panel, "xsec_vol_rank_cont")["net_edge_bps"]
    shuffled = panel.copy()
    rng = np.random.default_rng(7)
    shuffled["xsec_vol_rank_cont"] = rng.permutation(shuffled["xsec_vol_rank_cont"].to_numpy())
    placebo = _sim(shuffled, "xsec_vol_rank_cont")["net_edge_bps"]
    assert placebo < 0.0                              # gross ≈ 0, so the 50 bps round trip bites
    assert placebo < planted


def test_topk_hysteresis_enters_topk_and_exits_below_the_band():
    scores = np.array([0.9, 0.8, 0.1, 0.2, 0.9, 0.8, 0.05, 0.1, 0.99])
    dates = np.array([1, 1, 1, 2, 2, 2, 3, 3, 3])
    syms = np.array(["a", "b", "c", "a", "b", "c", "a", "b", "c"])
    held = xr.topk_with_hysteresis(scores, 1, 2.0, dates=dates, symbols=syms)
    # d1: enter a. d2: a drops to rank 2 = exit rank -> exit; b enters. d3: c enters, b held.
    assert held.tolist() == [True, False, False, False, True, False, False, True, True]


def test_horizon_forces_an_exit_after_the_holding_cap():
    scores = np.array([0.9, 0.9, 0.9, 0.9])
    dates = np.array([1, 2, 3, 4])
    syms = np.array(["a", "a", "a", "a"])
    assert xr.topk_with_hysteresis(scores, 1, 2.0, dates=dates, symbols=syms).all()
    # horizon=2 flattens the name on the third date; it may re-enter only from the next date on.
    capped = xr.topk_with_hysteresis(scores, 1, 2.0, dates=dates, symbols=syms, horizon=2)
    assert capped.tolist() == [True, True, False, True]


def test_turnover_fraction_counts_new_entries_only():
    panel = _fixture(n_dates=20, n_names=10)
    ent = xr.build_entries(panel, "xsec_vol_rank_cont", 3, 2.0, 5)
    f = xr.turnover_fraction(ent)
    assert 0.0 < f <= 1.0
    assert int(ent["entry"].sum()) <= int(ent["selected"].sum())


def test_calib_card_records_folds_turnover_and_stop_flag(tmp_path):
    panel = _fixture()
    best = xr.tune_signal(panel, "xsec_vol_rank_cont")
    assert {"k", "band", "horizon", "trades_per_week", "net_edge_bps", "fold_report", "stop"} <= set(best)
    assert best["fold_report"]["n_folds"] > 1
    assert best["n_trials"] == len(xr.K_GRID) * len(xr.BAND_GRID) * len(xr.HORIZON_GRID)
    path = xr.write_calib_report(tmp_path / "calib_xsec_vol_rank_cont_USD.md", "USD",
                                 "xsec_vol_rank_cont", best)
    text = path.read_text()
    for token in ("| fold |", "turnover f", "net edge", "Fold report", "Stop flag"):
        assert token in text
    assert "**STOP**" in text or "**CONTINUE**" in text


def test_fold_report_is_mandatory_fail_closed():
    empty = pd.DataFrame({"date": pd.to_datetime([]), "symbol": [], "fold": [], "r": [],
                          "score": [], "selected": [], "entry": []})
    with pytest.raises(foldrep.FoldReportMissing):
        xr.simulate(empty)


# --------------------------------------------------------------------------- WI-072 re-open
def test_generic_union_library_column_is_scored_by_name():
    """(a) any union-library cell that is a panel column is scoreable; the named signals stay."""
    panel = _fixture(n_dates=4, n_names=6)
    panel["move_occur_raw"] = np.linspace(0.0, 1.0, len(panel)).astype("float32")
    v = xr.signal_values(panel, "move_occur_raw")
    assert v.dtype == np.float32
    assert np.allclose(v, panel["move_occur_raw"].to_numpy("float32"))
    assert xr.signal_names(panel)[: len(xr.SIGNALS)] == xr.SIGNALS      # named signals first
    assert "p_b_hold" in xr.signal_names(panel)                        # widened library set
    with pytest.raises(KeyError, match="unknown signal"):
        xr.signal_values(panel, "not_a_library_cell")


def test_widened_grids_add_the_new_band_and_horizon_values():
    """(b) the retry grid adds the wider bands (lower turnover) and the longer horizons."""
    assert {2.0, 3.0} <= set(xr.BAND_GRID) and 1.5 in xr.BAND_GRID
    assert {10, 21, 34} <= set(xr.HORIZON_GRID)
    assert list(xr.BAND_GRID) == sorted(xr.BAND_GRID)
    assert list(xr.HORIZON_GRID) == sorted(xr.HORIZON_GRID) and list(xr.K_GRID) == sorted(xr.K_GRID)
    assert xr.DIRECTIONS == ("long", "long_short")                      # D-027 §5 first, then second pass


def test_long_short_pass_recovers_the_planted_cross_section():
    """(c) the L/S pass harvests both tails: a pair cycle (100 bps) is cleared before cost."""
    panel = _fixture()
    entries = xr.build_entries(panel, "xsec_vol_rank_cont", 4, 2.0, 13, "long_short")
    sim = xr.simulate(entries, direction="long_short")
    assert sim["direction"] == "long_short" and sim["n_pairs"] > 0
    assert set(entries.loc[entries["selected"], "side"].tolist()) == {1, -1}
    assert sim["gross_edge_bps"] > costs.PAIR_BPS
    assert sim["cost_bps"] >= costs.PAIR_BPS                            # pair cycle + turnover amortization
    assert sim["net_edge_bps"] > 0.0
    long_only = _sim(panel, "xsec_vol_rank_cont")
    assert long_only["n_pairs"] == 0 and long_only["direction"] == "long"


def test_long_short_placebo_shows_nothing():
    """A shuffled score has no tail information: gross ≈ 0, so the pair cycle bites."""
    panel = _fixture()
    shuffled = panel.copy()
    rng = np.random.default_rng(3)
    shuffled["xsec_vol_rank_cont"] = rng.permutation(shuffled["xsec_vol_rank_cont"].to_numpy())
    planted = xr.simulate(xr.build_entries(panel, "xsec_vol_rank_cont", 4, 2.0, 13, "long_short"),
                          direction="long_short")["net_edge_bps"]
    placebo = xr.simulate(xr.build_entries(shuffled, "xsec_vol_rank_cont", 4, 2.0, 13, "long_short"),
                          direction="long_short")["net_edge_bps"]
    assert placebo < 0.0 and placebo < planted


def test_wider_band_lowers_turnover_on_a_high_churn_fixture():
    """(b) rationale: the wider band holds a name past the top-k, so the held set churns less."""
    panel = _fixture(seed=5, n_dates=150, n_names=30)
    rng = np.random.default_rng(99)
    panel["xsec_vol_rank_cont"] = (panel["xsec_vol_rank_cont"].to_numpy("float32")
                                   + rng.normal(0.0, 3.0, len(panel)).astype("float32"))  # ranks churn
    narrow = xr.turnover_fraction(xr.build_entries(panel, "xsec_vol_rank_cont", 4, 1.5, 13))
    wide = xr.turnover_fraction(xr.build_entries(panel, "xsec_vol_rank_cont", 4, 3.0, 13))
    assert wide < narrow
    assert 0.0 < wide < 1.0


def test_long_short_positions_hold_both_extremes_with_symmetric_hysteresis():
    """k=1, band=2.0, 4 names: hold the best long / the worst short, exiting only past the band."""
    scores = np.array([0.9, 0.6, 0.4, 0.1,      # d1: a best (long), d worst (short)
                       0.6, 0.9, 0.1, 0.4,      # d2: a keeps its long (rank 2 of 4 < band edge); c joins short
                       0.1, 0.95, 0.3, 0.5])    # d3: a falls to worst -> long out, short in; d rises -> short out
    dates = np.array([1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3])
    syms = np.array(["a", "b", "c", "d"] * 3)
    held, side = xr.topk_positions(scores, 1, 2.0, dates=dates, symbols=syms, direction="long_short")
    assert side.tolist() == [1, 0, 0, -1, 1, 1, -1, -1, -1, 1, -1, 0]
    assert held.tolist() == [True, False, False, True, True, True, True, True, True, True, True, False]
    long_only = xr.topk_with_hysteresis(scores, 1, 2.0, dates=dates, symbols=syms)
    assert long_only.tolist() == [True, False, False, False, True, True, False, False, False, True,
                                 False, False]
    with pytest.raises(ValueError, match="unknown direction"):
        xr.topk_positions(scores, 1, 2.0, dates=dates, symbols=syms, direction="both")
