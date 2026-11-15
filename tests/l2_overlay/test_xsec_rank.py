"""WI-066 — xsec top-k screener tests (D-027 §5 (b)): the planted signal is recovered net of cost,
the placebo shows nothing, the CALIB card carries the fold distribution / turnover / stop flag, and
the fold report is mandatory. Synthetic only: no reads or writes under `data/`.
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
