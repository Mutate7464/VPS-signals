"""WI-017 targets: brute-force base + derived target grid (USD).

Confirmed definitions (admin clarify 2026-10-31):
- Run 1 (base): per window w in WI017_WINDOWS, lookforward over the next w
  trading days — peak/bottom (swing extremes), +10% up-barrier touch,
  -10% down-barrier touch, ±5% stay band. Triple-barrier family per window.
- Run 2 (adds): velocity (%/day from bottom to peak within the window) and
  technical pivot / triple point (three trendlines/barriers intersecting) —
  defined after run-1 output review.

Per-target base rates reported before any modeling; targets with <1% event
share are flagged dead-on-arrival, not modeled.
"""
