"""WI-017 features: ALL existing fib-windowed families recomputed at the full
3-233 grid (admin confirmed full-grid scope 2026-10-31).

Families: range_pos, range_width, fib_dist, donchian_break, adx, di_spread,
atr_pct, bb_pct_b, bb_width, obv_zscore, amihud, yangzhang, kama_er, hurst,
entropy, vwap_zscore (+ WI-015 perfanalytics families: bb_width/range_width@
233 alignment positives are re-confirmed at full grid).

Redundancy is measured and reported (dense grids produced near-clones before —
feature_engine.py:63); prune sets recommended, never silently applied.
"""
