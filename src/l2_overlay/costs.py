"""WI-065 — L2 cost model (D-027 §2, binding for every L2 card). Every value is in bps.

Single-leg round trip = 2 sides; L/S pair cycle = 4 sides; a rebalance at turnover fraction f pays
100·f; a mid-trade resize pays 25·|Δsize|. Pure arithmetic only: no data, no state, no I/O.
"""
from __future__ import annotations

SIDE_BPS = 25.0                       # one side (entry or exit), the D-027 §2 unit
SINGLE_LEG_BPS = 2.0 * SIDE_BPS       # 50 bps round trip
PAIR_BPS = 4.0 * SIDE_BPS             # 100 bps per pair cycle
__all__ = ["SIDE_BPS", "SINGLE_LEG_BPS", "PAIR_BPS", "single_leg_cost", "pair_cost",
           "turnover_cost", "resize_cost", "bps_to_frac", "edge_bps", "net_edge_bps"]


def single_leg_cost(side_bps: float = SIDE_BPS) -> float:
    """One round trip on a single leg: 2 × 25 = 50 bps."""
    return 2.0 * float(side_bps)


def pair_cost(side_bps: float = SIDE_BPS) -> float:
    """One L/S pair cycle: 4 sides = 100 bps."""
    return 4.0 * float(side_bps)


def turnover_cost(fraction, pair_bps: float | None = None) -> float:
    """100 · f bps for a pair rebalance at turnover fraction f (|f|: a rebalance is a magnitude)."""
    base = pair_cost() if pair_bps is None else float(pair_bps)
    return base * abs(float(fraction))


def resize_cost(dsize, side_bps: float = SIDE_BPS) -> float:
    """25 bps × |Δsize| for a mid-trade resize of size fraction Δsize."""
    return float(side_bps) * abs(float(dsize))


def bps_to_frac(bps) -> float:
    """bps → decimal fraction (50 bps → 0.005)."""
    return float(bps) / 1e4


def edge_bps(edge_frac) -> float:
    """A return-fraction edge → bps (0.0005 → 5.0)."""
    return float(edge_frac) * 1e4


def net_edge_bps(gross_edge_bps, cost_bps: float = SINGLE_LEG_BPS) -> float:
    """Gross bps edge minus an explicit cost; the D-027 cost-floor comparison."""
    return float(gross_edge_bps) - float(cost_bps)
