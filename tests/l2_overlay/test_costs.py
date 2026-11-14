"""WI-065 — L2 cost model tests (D-027 §2). Exact 50 / 100 / 100·f / 25·|Δsize| bps arithmetic."""
from __future__ import annotations

import pytest

from src.l2_overlay import costs as c

BPS = 1e-4


def test_constants_match_the_d027_table():
    assert c.SIDE_BPS == 25.0 and c.SINGLE_LEG_BPS == 50.0 and c.PAIR_BPS == 100.0


def test_single_leg_round_trip_is_fifty_bps():
    assert c.single_leg_cost() == 50.0
    assert c.single_leg_cost() == c.bps_to_frac(50.0) / BPS


def test_pair_cycle_is_one_hundred_bps():
    assert c.pair_cost() == 100.0
    assert c.pair_cost(side_bps=10.0) == 40.0


def test_turnover_is_100_times_f():
    for f in (0.0, 0.25, 0.5, 1.0, 2.0):
        assert c.turnover_cost(f) == pytest.approx(100.0 * f, rel=1e-12)
    assert c.turnover_cost(0.5) == 50.0
    assert c.turnover_cost(-0.5) == 50.0          # a rebalance is a magnitude
    assert c.turnover_cost(0.5, pair_bps=40.0) == 20.0


def test_resize_is_25_times_abs_dsize():
    assert c.resize_cost(0.4) == pytest.approx(10.0, rel=1e-12)   # 25 × 0.4
    assert c.resize_cost(-1.0) == 25.0
    assert c.resize_cost(0.0) == 0.0
    assert c.resize_cost(2.0, side_bps=10.0) == 20.0


def test_edge_conversions_round_trip():
    assert c.bps_to_frac(50.0) == pytest.approx(0.005, rel=1e-12)
    assert c.edge_bps(0.005) == pytest.approx(50.0, rel=1e-12)
    assert c.net_edge_bps(60.0) == 10.0            # gross minus the 50 bps single-leg default
    assert c.net_edge_bps(10.0, cost_bps=100.0) == -90.0
