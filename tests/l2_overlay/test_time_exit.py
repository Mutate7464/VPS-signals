"""WI-068 — time-exit tests (D-027 §5 (a)): the identical-entry invariant holds across every exit arm,
the hybrid exits at `min(t_event, t_h)`, net-edge arithmetic matches `costs` exactly, the placebo shows
nothing, the frozen long horizon stops, and the fold report is mandatory. Synthetic only: no reads or
writes under `data/`.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.l2_overlay import costs
from src.l2_overlay import fold_report as foldrep
from src.l2_overlay import harness as H
from src.l2_overlay.constructions import time_exit as tx


def _fixture(seed=68, n_entries=200):
    return tx.synthetic_fixture("USD", n_entries=n_entries, seed=seed)


def _hand_frame():
    """6 entries, 2 folds, hand-checkable event / h13 / h55 returns (all finite)."""
    return pd.DataFrame({
        "symbol": ["a", "b", "c", "a", "b", "c"],
        "date": pd.to_datetime(["2021-01-04", "2021-01-05", "2021-01-06"] * 2),
        "fold": np.array([0, 0, 0, 1, 1, 1], dtype="int64"),
        "t_event": np.full(6, tx.EVENT_HORIZON_FIB, dtype="int64"),
        "r_event": np.array([0.0, 0.01, -0.01, 0.0, 0.0, 0.0], dtype="float32"),
        "r_h13": np.array([0.02, 0.03, 0.01, 0.04, 0.05, 0.03], dtype="float32"),
        "r_h55": np.array([-0.01, 0.0, -0.02, 0.01, 0.0, -0.01], dtype="float32")})


def test_identical_entries_across_every_exit_arm():
    frame = _fixture()
    arms = tx.compare_arms(frame)
    assert [a["arm"] for a in arms] == ["event_exit", "fixed_h13", "hybrid_h13", "fixed_h55", "hybrid_h55"]
    key = tx.entries_key(frame)
    assert len({a["entry_key"] for a in arms}) == 1 and arms[0]["entry_key"] == key
    assert {a["n_entries"] for a in arms} == {len(frame)}          # same entry rows, no arm-specific drop
    assert [a["cost_bps"] for a in arms] == [costs.single_leg_cost()] * len(arms)


def test_hybrid_exits_at_the_minimum_of_event_and_horizon():
    frame = _fixture()
    r_ev, t_ev = tx.event_returns(frame)
    for h in tx.HORIZONS:
        r_hy, t_hy = tx.hybrid_exit(frame, h)
        assert np.array_equal(t_hy, np.minimum(t_ev, h))           # min(t_event, t_h), exactly
        first = t_ev <= h
        assert np.allclose(r_hy[first], r_ev[first])               # the earlier event exit prices it
        assert np.allclose(r_hy[~first], tx.horizon_returns(frame, h)[~first])
    hand = _hand_frame()
    hand.loc[0, "t_event"] = 8                                     # early stop: 8 < 13 -> event return wins
    r_hy, t_hy = tx.hybrid_exit(hand, 13)
    assert t_hy[0] == 8 and r_hy[0] == pytest.approx(hand.loc[0, "r_event"])
    assert t_hy[1] == 13 and r_hy[1] == pytest.approx(hand.loc[1, "r_h13"])   # 39 > 13 -> h13 return wins
    assert t_hy[3] == 13 and r_hy[3] == pytest.approx(hand.loc[3, "r_h13"])


def test_fixed_horizon_holds_exactly_h_dates_and_uses_that_column():
    frame = _hand_frame()
    for h in tx.HORIZONS:
        arm = tx.simulate_fixed_horizon(frame, h)
        assert arm["holding_dates"] == float(h)
        assert arm["n_entries"] == len(frame)
        expected = costs.edge_bps(np.asarray(frame[f"r_h{h}"], "float64").mean()
                                 - np.asarray(frame["r_event"], "float64").mean())
        assert arm["gross_edge_bps"] == pytest.approx(expected, rel=1e-12, abs=1e-9)


def test_net_edge_arithmetic_matches_costs_exactly():
    frame = _hand_frame()
    arm = tx.simulate_fixed_horizon(frame, 13)
    r, base = np.asarray(frame["r_h13"], "float64"), np.asarray(frame["r_event"], "float64")
    fold = frame["fold"].to_numpy()
    gross = costs.edge_bps(r.mean() - base.mean())
    assert arm["cost_bps"] == costs.SINGLE_LEG_BPS == costs.single_leg_cost() == 50.0
    assert arm["gross_edge_bps"] == pytest.approx(gross, rel=1e-12, abs=1e-9)
    assert arm["net_edge_bps"] == pytest.approx(costs.net_edge_bps(gross, costs.single_leg_cost()),
                                                rel=1e-12, abs=1e-9)
    assert arm["net_edge_bps"] == pytest.approx(arm["gross_edge_bps"] - costs.single_leg_cost())
    assert arm["abs_net_edge_bps"] == pytest.approx(costs.edge_bps(r.mean()) - costs.single_leg_cost())
    for f in (0, 1):
        m = fold == f
        want = costs.bps_to_frac(costs.edge_bps(r[m].mean() - base[m].mean()) - costs.single_leg_cost())
        assert arm["per_fold_net_edge"][f] == pytest.approx(want, rel=1e-12, abs=1e-12)


def test_event_rules_take_the_first_fired_rule_and_never_drop_one():
    frame = _hand_frame()
    frame["t_event_b_stop"], frame["r_event_b_stop"] = 8, -0.02
    frame["t_event_fib_exit"], frame["r_event_fib_exit"] = tx.EVENT_HORIZON_FIB, 0.03
    r_ev, t_ev = tx.event_returns(frame, ("fib_exit", "b_stop"))
    assert np.array_equal(t_ev, np.full(len(frame), 8)) and np.allclose(r_ev, -0.02)
    partial = frame.drop(columns=["t_event_fib_exit", "r_event_fib_exit"])   # b_stop present, fib_exit absent
    with pytest.raises(KeyError, match="fib_exit"):
        tx.event_returns(partial, ("fib_exit", "b_stop"))


def test_planted_time_edge_continues_while_the_frozen_long_horizon_stops():
    arms = {a["arm"]: a for a in tx.compare_arms(_fixture())}
    assert arms["fixed_h13"]["net_edge_bps"] > H.MATERIALITY_FLOOR_BPS
    assert arms["fixed_h13"]["abs_net_edge_bps"] > H.MATERIALITY_FLOOR_BPS
    assert not arms["fixed_h13"]["stop"]["stop"] and arms["fixed_h13"]["fold_report"]["fold_ceiling_ok"]
    assert arms["fixed_h55"]["stop"]["stop"]                       # the planted long horizon decays
    assert arms["hybrid_h13"]["net_edge_bps"] > 0.0                # bounded by both arms, still positive
    assert not arms["hybrid_h13"]["stop"]["stop"]
    ev = arms["event_exit"]
    assert arms["hybrid_h55"]["net_edge_bps"] == pytest.approx(ev["net_edge_bps"])   # 39 < 55 -> event exit
    assert arms["hybrid_h55"]["holding_dates"] == pytest.approx(ev["holding_dates"])
    for a in arms.values():                                        # t_h bounds the hybrid holding length
        assert a["holding_dates"] <= max(tx.HORIZONS) + 1.0


def test_placebo_shows_nothing():
    frame, planted = _fixture(), tx.simulate_hybrid(_fixture(), 13)["net_edge_bps"]
    placebo = tx.placebo_net_edge(frame, 13)
    assert placebo <= 0.0                                          # no coherent paired edge: the 50 bps bites
    assert placebo < planted


def test_fold_report_is_mandatory_fail_closed():
    empty = _hand_frame().iloc[:0]
    with pytest.raises(foldrep.FoldReportMissing):
        tx.simulate_fixed_horizon(empty, 13)


def test_calib_card_records_folds_stop_flag_and_the_entry_key(tmp_path):
    path = tx.write_calib_report(tmp_path / "calib_USD_smoke.md", "USD", tx.compare_arms(_fixture()),
                                 smoke=True)
    text = path.read_text()
    for token in ("| arm |", "max fold share", "net vs event", "Fold report", "Stop flag",
                  "identical rows", tx.entries_key(_fixture())):
        assert token in text
    assert "**STOP**" in text or "STOP |" in text
    assert "EVAL unread" in text


def test_load_entries_is_calib_only_and_attaches_horizons_symbol_sequentially(tmp_path):
    days = pd.date_range("2021-01-04", periods=20, freq="B")
    panel = pd.concat([pd.DataFrame({"symbol": s, "date": days, "close": np.arange(1.0, 21.0) + off})
                       for s, off in (("USD00", 0.0), ("USD02", 9.0))], ignore_index=True)
    cache = tmp_path / "cache"
    cache.mkdir()
    panel.to_parquet(cache / "wi036_panel_USD.parquet", index=False)
    entries = pd.DataFrame({"symbol": "USD00", "date": days[:15],
                            "fold": np.arange(15) % 5, "r_event": 0.01,
                            "t_event": 39, "r_h55": 0.02})
    entries.loc[len(entries)] = ["USD00", pd.Timestamp("2022-06-06"), 0, 0.5, 39, 0.5]   # EVAL row
    path = tmp_path / "entries.parquet"
    entries.to_parquet(path, index=False)
    frame = tx.load_entries("USD", path, panel_cache=cache)
    assert len(frame) == 7                                         # 20 - 13 shifted exits; EVAL row dropped
    assert (pd.to_datetime(frame["date"]) < H.CALIB_END).all()
    assert frame["r_h13"].dtype == np.float32 and frame["r_event"].dtype == np.float32
    assert np.allclose(frame["r_h13"], [13.0 / (i + 1) for i in range(7)], rtol=1e-5)
    with pytest.raises(RuntimeError, match="cache missing"):
        tx.load_entries("USD", path, panel_cache=tmp_path / "nope")


def test_a_sparse_price_panel_fails_closed_instead_of_mis_dating_the_horizon(tmp_path):
    sparse = pd.DataFrame({"symbol": "USD00", "date": pd.date_range("2021-01-04", periods=20, freq="14D"),
                           "close": np.arange(1.0, 21.0)})
    cache = tmp_path / "cache"
    cache.mkdir()
    sparse.to_parquet(cache / "wi036_panel_USD.parquet", index=False)
    entries = pd.DataFrame({"symbol": "USD00", "date": sparse["date"].to_numpy(),
                            "fold": 0, "r_event": 0.01, "t_event": 39, "r_h55": 0.02})
    path = tmp_path / "entries.parquet"
    entries.to_parquet(path, index=False)
    with pytest.raises(RuntimeError, match="daily bar series"):     # h observations != h dates here
        tx.load_entries("USD", path, panel_cache=cache)


def test_smoke_run_writes_calib_and_fold_artifacts(tmp_path):
    arms = tx.run_market("CAD", _fixture(seed=7, n_entries=120), report_root=tmp_path, smoke=True)
    assert (tmp_path / "calib_CAD_smoke.md").exists()
    assert (tmp_path / "fold_fixed_h13_CAD_smoke.json").exists()
    assert len({a["entry_key"] for a in arms}) == 1
