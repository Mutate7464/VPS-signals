# WI-017 run 5 — grid prune recommendations (REC C, gate-accepted 2026-11-01)

Rule (admin 2026-10-31 amendment, applied mechanically): drop a column only when
BOTH |ρ| ≥ 0.90 vs a kept sibling AND less useful (max |pass IC| over targets,
run 4); never empty a family. Nothing is applied to any shipped panel — this is
the recommended list for the next WI's feature build.

**Result: 176 of 264 dropped, 88 kept.** Adjacent smooth-family windows are
near-clones (|ρ| 0.99+), so they collapse to 1–4 representatives per family;
fast families (kama_er 17/17, hurst 12/12, entropy 11/14, vwap 10/17) earn the
dense grid. Plus one dead column: `hurst_9` (all-NaN by constructor, w≥12
needed — the shipped WI-016 grid wart).

| family | keep | drop |
|---|---|---|
| adx | 4 | 13 |
| amihud | 9 | 8 |
| atr_pct | 1 | 16 |
| bb_pct_b | 4 | 13 |
| bb_width | 4 | 13 |
| di_spread | 3 | 14 |
| donchian_break | 3 | 14 |
| entropy | 11 | 3 |
| fib_dist | 1 | 16 |
| hurst | 12 | 0 |
| kama_er | 17 | 0 |
| obv_zscore | 3 | 14 |
| range_pos | 1 | 16 |
| range_width | 2 | 15 |
| vwap_zscore | 10 | 7 |
| yangzhang | 3 | 14 |

Full column lists: `reports/wi017/run5_prune_recs.json` (`drop_columns`,
`keep_columns`). Caveats for the next WI: (1) verify the single-representative
families (atr_pct, fib_dist, range_pos) against the target actually being
modeled — usefulness here was measured against the full 165-target set, and the
best representative for a w≈34 directional target may differ; (2) WI-016's
shipped grid is frozen and untouched.
