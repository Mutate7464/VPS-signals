# GATE DECISION — WI-015 Performance analytics (fib 3→233 feature panel + run-target alignment matrix)

**Date:** 2026-10-29 · **Admin decision:** ACCEPT → DONE

## What was decided

- WI-015 **accepted** and closed DONE. Build evidence stood as verified: full suite 444 passed EXIT:0 (396 pre-existing + 48 new), PM independently re-verified (targeted re-run, alignment CSVs 1200 candidate rows/market, PNGs valid, frozen artifacts clean, no WI-014 touch). Deviation 1 (donchian warm-up NaN) accepted.
- Headline result on record: first positive feature→target alignment after the WI-009 series — run amplitude/velocity align with long-window (21–233) range/vol features (CAD `bb_width@233`, `range_width_f@233`; USD `yangzhang@144`, `atr_pct@233`).

## What ships

- `src/perfanalytics/{targets,features,correlation}/` + 48 tests; run-target datasets and enriched fib 3→233 panels under `data/perfanalytics/`; alignment matrix, heatmaps, ranked tables under `reports/perfanalytics/`. All frozen artifacts untouched since the gate.

## What carries forward

- The validated long-window range/vol family (144/233) directly seeds WI-016's feature re-evaluation and window-grid unification (`docs/workflow/designs/D-016-triple-barrier-fib-labeling.md`).
- WI-015's enriched panel is analysis-grade (research datasets), not the shipped screener input; the shipped panel remains `data/features/`.
