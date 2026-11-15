"""WI-069 — vol-target entry-only sizing tests (D-027 §5 (c)): the entry-only invariant (no mid-trade
resize, no forward input in a weight), sized-vs-unsized arithmetic through `costs`, the mandatory fold
report (fails closed), a placebo that shows nothing, and the CALIB card + fold artifact of a smoke run.
Synthetic only: no reads or writes under `data/`.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.l2_overlay import costs
from src.l2_overlay import fold_report as foldrep
from src.l2_overlay.constructions import vol_target as vt


def _fixture(n=250, seed=69, sized_edge=True):
    return vt.synthetic_fixture("USD", n_entries=n, seed=seed, sized_edge=sized_edge)


def _hand_frame():
    """4 entries, 2 folds, hand-checkable vol/exit pairs (low-vol winner, high-vol loser)."""
    dates = pd.to_datetime(["2021-01-04", "2021-01-05", "2021-01-06", "2021-01-07"])
    entries = pd.DataFrame({"symbol": ["a", "b", "c", "d"], "date": dates,
                            "fold": np.array([0, 0, 1, 1], dtype="int64"),
                            "r_event": np.zeros(4, dtype="float32"),
                            "r_h13": np.array([0.10, 0.05, -0.04, 0.02], dtype="float32"),
                            "r_h55": np.array([0.10, 0.05, -0.04, 0.02], dtype="float32")})
    panel = pd.DataFrame({"symbol": ["a", "b", "c", "d"], "date": dates,
                          "atr_pct_21": np.array([0.005, 0.02, 0.04, 0.01], dtype="float32"),
                          "entropy_39": np.array([1.0, 1.5, 0.5, 1.2], dtype="float32")})
    return entries, panel


def test_weights_are_entry_only_and_forward_blind():
    _, panel = _hand_frame()
    w = vt.target_weights(panel)
    assert w.shape == (panel.shape[0],) and w.dtype == np.float32
    assert float(w.min()) >= vt.W_MIN and float(w.max()) <= vt.W_MAX
    # monotone decreasing in the causal entry vol (sized at entry, never at the exit)
    assert w[0] > w[3] > w[1] > w[2]
    # the forward WI-058 label and any other forward column can never move a weight
    polluted = panel.assign(xsec_vol_rank_cont=np.array([0.9, 0.1, 0.5, 0.2], dtype="float32"),
                            entropy_39=np.array([9.0, 1.0, 3.0, 7.0], dtype="float32"))
    assert np.array_equal(w, vt.target_weights(polluted))
    # fail closed: no causal column, no weights
    with pytest.raises(KeyError):
        vt.target_weights(panel.drop(columns=["atr_pct_21"]))
    with pytest.raises(ValueError):
        vt.target_weights(panel, ann_vol_target=0.0)


def test_unusable_entry_vol_sizes_down_and_is_counted():
    entries, panel = _hand_frame()
    broken = panel.assign(atr_pct_21=np.array([np.nan, 0.0, 0.04, 0.01], dtype="float32"))
    w = vt.target_weights(broken)
    assert w[0] == pytest.approx(vt.W_MIN) and w[1] == pytest.approx(vt.W_MIN)
    assert vt.vol_imputed(broken) == 2 and vt.vol_imputed(panel) == 0
    res = vt.compare_sized_vs_unsized(entries, broken)
    assert res["n_vol_imputed"] == 2 and res["vol_nan_policy"] == vt.VOL_NAN_POLICY


def test_entry_only_cost_has_no_resize_term():
    entries, panel = _hand_frame()
    w = vt.target_weights(panel).astype("float64")
    net = vt.sized_net_frac(entries["r_h55"], w)
    round_trip = costs.bps_to_frac(costs.SINGLE_LEG_BPS)
    assert np.allclose(net, w * (np.asarray(entries["r_h55"], "float64") - round_trip))
    assert w.shape[0] == len(entries)                                  # exactly one weight per event
    assert [n for n in dir(vt) if "resize" in n or "rebalance" in n] == []   # no mid-trade path exists
    assert costs.resize_cost(0.0) == 0.0                               # frozen size ⇒ Δ == 0


def test_sized_vs_unsized_edge_arithmetic_matches_costs():
    entries, panel = _hand_frame()
    res = vt.compare_sized_vs_unsized(entries, panel)
    r = np.asarray(entries["r_h55"], "float64")
    w = np.asarray(vt.target_weights(panel), "float64")
    cost = costs.SINGLE_LEG_BPS
    assert res["unsized_bps"] == pytest.approx(costs.edge_bps(r.mean()) - cost)
    assert res["sized_bps"] == pytest.approx(costs.edge_bps(float((w * r).sum() / w.sum())) - cost)
    assert res["edge_delta_bps"] == pytest.approx(res["sized_bps"] - res["unsized_bps"])
    assert res["edge_delta_bps"] > 0.0                     # down-sizing the high-vol loser must pay
    flat = entries.assign(r_h55=np.full(4, 0.03, dtype="float32"))
    assert vt.compare_sized_vs_unsized(flat, panel)["edge_delta_bps"] == pytest.approx(0.0, abs=1e-9)


def test_risk_adjusted_read_out_is_sized_vs_unsized():
    entries, panel = _fixture(seed=11)
    res = vt.compare_sized_vs_unsized(entries, panel)
    assert np.isfinite(res["ra_sized"]) and np.isfinite(res["ra_unsized"])
    assert res["ra_sized"] == pytest.approx(vt.risk_adjusted(vt.sized_net_frac(entries["r_h55"], vt.target_weights(panel))))
    assert np.isnan(vt.risk_adjusted(np.array([0.01, 0.01])))         # zero dispersion ⇒ no ratio


def test_fold_report_is_mandatory_and_records_ceiling():
    entries, panel = _hand_frame()
    with pytest.raises(foldrep.FoldReportMissing):                    # fails closed, never an empty report
        vt.compare_sized_vs_unsized(entries.iloc[0:0], panel.iloc[0:0])
    res = vt.compare_sized_vs_unsized(entries, panel)
    assert res["fold_report"]["n_folds"] == 2 and isinstance(res["stop"]["stop"], bool)
    single = entries.assign(fold=np.zeros(len(entries), dtype="int64"))  # the survivor reality: one fold
    res1 = vt.compare_sized_vs_unsized(single, panel)
    assert res1["fold_report"]["n_folds"] == 1 and res1["fold_report"]["fold_ceiling_ok"] is False
    assert res1["stop"]["stop"] is True                               # ceiling failure = CALIB failure


def test_placebo_shows_nothing_when_sizing_carries_no_edge():
    entries, panel = _fixture(seed=5, sized_edge=False)
    assert np.isfinite(vt.compare_sized_vs_unsized(entries, panel)["edge_delta_bps"])
    pl = vt.placebo_sized_edge(entries, panel)
    assert abs(float(pl["observed_bps"])) < 60.0                      # no vol link ⇒ no improvement
    assert abs(float(pl["z"])) < 2.0                                  # and the null is indistinguishable


def test_regime_attribution_axes_are_present_only_when_available():
    entries, panel = _fixture(seed=3)
    res = vt.compare_sized_vs_unsized(entries, panel)
    axes = {row["axis"] for row in res["regimes"]}
    assert f"vol_regime:{vt.VOL_COLUMN}" in axes and "disp_entropy_39" in axes
    assert "xsec_vol_rank_cont" in axes                               # post-hoc attribution axis only
    widx = [row for row in res["regimes"] if row["axis"] == f"vol_regime:{vt.VOL_COLUMN}"]
    assert sum(row["n"] for row in widx) == len(entries)
    assert all(float(row["mean_weight"]) > 0.0 for row in widx)
    bare = vt.compare_sized_vs_unsized(entries, panel.drop(columns=["entropy_39", "xsec_vol_rank_cont"]))
    assert {row["axis"] for row in bare["regimes"]} == {f"vol_regime:{vt.VOL_COLUMN}"}


def test_smoke_run_writes_calib_card_and_mandatory_fold_report(tmp_path):
    entries, panel = _fixture(seed=2)
    res = vt.run_market("USD", entries, panel, report_root=tmp_path, smoke=True)
    card, folds = tmp_path / "calib_USD_smoke.md", tmp_path / "fold_USD_smoke.json"
    assert card.exists() and folds.exists() and res["stop"]["stop"] in (True, False)
    text = card.read_text()
    for needle in ("Entry-only sizing", "Fold report", "Stop/continue", "no mid-trade resize"):
        assert needle in text
    assert "xsec_vol_rank_cont" in text and "atr_pct_21" in text
