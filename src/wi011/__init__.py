"""WI-011 — condition-first meta-analysis support package.

Modules:
    conditions : trailing, point-in-time per-symbol primitives and the declared
                 condition vocabulary (Step 2), incl. the Step 3-selected
                 indicator subset hook.
    panel      : sequential per-symbol panel builder (conditions + forward
                 returns + cost proxies) that never materialises an all-ticker
                 uncompressed frame.
    stats      : purged walk-forward evaluation helpers, conditional expectancy
                 statistics and the two-disjoint-sub-window sign test.
"""

from __future__ import annotations

HORIZONS: tuple[int, ...] = (1, 2, 5, 10, 15, 20, 60, 120)
"""The eight fixed horizons (trading days) named by the WI-011 plan, Step 2(a).

Forward return over horizon h is measured on close prices as
`close.shift(-h)/close - 1`; the window is the *forward* path [t+1 .. t+h], so a
label observed at t needs h future bars. Horizons are fixed by the plan and are
never re-selected after looking at results.
"""

MARKET = "CAD"
"""WI-011 is CAD-universe only (plan CONSTRAINTS)."""