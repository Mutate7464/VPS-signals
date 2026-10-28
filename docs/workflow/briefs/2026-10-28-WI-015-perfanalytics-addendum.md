# Addendum — WI-015: result visualization (admin order 2026-10-28, plan approval + scope add)

Approved with "proceed. visualize results -> confirm best performing features
(comparing with family - feature & timeframe)". Extends plan step 4 outputs;
does not change steps 1–3 or the frozen plan file.

## Required outputs (per market, under `reports/perfanalytics/`)

1. **Family×window heatmap** `heatmap_{market}.png`: signed held-out Spearman IC.
   Rows = target×horizon (T1..T4 × k∈{15,20}); columns = window (fib grid
   3,5,8,13,21,34,55,89,144,233); one row-group per feature family. Cell =
   held-out mean IC (signed, diverging colormap), NaN where feature absent.
   matplotlib: batch ≤10 figures, `plt.close('all')` + `gc.collect()` per batch.
2. **Ranked table** `alignment_top_{market}.csv`: per target×horizon, top-10
   family×window by |IC| with columns: family, window, held-out IC, noise
   margin, sign-match vs E5 best factor, pass/fail.
3. **Summary section** appended to `alignment_{market}.md`: which family and
   which window aligns best per target, explicitly calling out the
   family-vs-timeframe comparison the admin asked for.

Determinism: same seed-42 bootstrap inputs as step 4; heatmap and table derive
from the same held-in artifact — no recomputation drift. Tests: rendering
smoke (files exist, non-empty, PNG header) in `tests/perfanalytics/test_visualization.py`.