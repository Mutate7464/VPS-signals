# WI-015 — Enriched features and run-target alignment — execution log

Plan: `docs/plans/2026-10-28-WI-015-perfanalytics.md` (frozen).
Build appends step rows here, ≤50 words each; details → step report artifacts under
`reports/perfanalytics/`.

Concern (open): BOARD.md still shows WI-015 at DESIGN/PLAN "awaiting admin plan
review", not EXECUTING; admin ordered Build in-chat (addendum commit `c350a95`).
Build leaves BOARD.md untouched per instruction — flagging for PM/scribe to move
the row.

03:54 | step 1 | done | `src/perfanalytics/targets/labelers.py` + `targets/__init__` exports: T1–T4 (close-to-close best qualifying bottom→peak pair ≥2×ATR(t), velocity, longest up-close streak, run flag) + bottom/peak-offset/low-high diagnostics; forward [t+1,t+k], NaN on incomplete window, T1/T2/T4 NaN on ATR warm-up, float32. `uv run pytest tests/perfanalytics/test_targets.py -q` 10 passed (shift-1, no-leak beyond t+k, trailing threshold, no-run, streak). Real CAD RY: 4816 rows 0.018 s, 34 warm-up NaN rows.

03:56 | step 2 | done | `src/perfanalytics/targets/dataset.py`: symbol-sequential builder → one `symbol=<T>.parquet` per ticker under `data/perfanalytics/run_targets_{market}/` + sibling schema/coverage json; `--market` default BOTH resolving **CAD then USD** (plan order, deliberately not `market_cli.BOTH`); stale files cleared on rebuild. `uv run pytest tests/perfanalytics/test_target_dataset.py -q` 8 passed (streaming-write order locked, all-NaN symbol skipped, invalid market exits 2 pre-write). Real CAD: 338 symbols / 1,191,669 rows / 30 MB / 11.8 s. Concern: `python -m` emits a benign runpy double-import warning.

04:06 | step 3 | done | `src/perfanalytics/features/panel.py` + shared `src/perfanalytics/markets.py` (CAD-then-USD): 15 existing families × exact fib grid 3→233 = 150 float32 columns, helpers imported from `src.feature_engine` so the panel cannot drift (overlap columns byte-equal to the shipped 92-col pool); symbol-sequential per-symbol parquet + schema json + `reports/perfanalytics/features_summary_{market}.md`. `uv run pytest tests/perfanalytics/test_features.py -q` 11 passed. Real CAD: 338 symbols / 1,196,063 rows / 150 cols; history coverage 338 at ≤144, 337 at 233. Concerns: `hurst_<W<12>` all-NaN (R/S floor) and `adx_*`/`vwap_zscore_*` need ~2W bars — surfaced as "feature absent", heatmap blanks.

04:06 | step 4 | done | `src/perfanalytics/correlation/alignment.py`: 5 chronological held-out folds + 20-session embargo (E5 split shape, held-out rows only, nothing trained), per-date cross-sectional Spearman IC, best-E5-factor sign reference, seeded 20-date circular block bootstrap (1000 draws, seed 42) → `reports/perfanalytics/alignment_{market}.{csv,json,md}`. Fold-major assembly keeps only one fold's cross-section in memory. `uv run pytest tests/perfanalytics/test_correlation.py -q` 8 passed (reproducible, no in-sample-as-held-out).

04:06 | addendum | done | `src/perfanalytics/correlation/visualize.py`: `heatmap_{market}.png` (family-block × window signed held-out IC, diverging cmap, blanks for absent), `alignment_top_{market}.csv` (top-10 per target×horizon: family, window, IC, noise margin, sign-match vs E5 best, pass/fail), family-vs-timeframe summary appended to `alignment_{market}.md` — all derived from the single alignment CSV (no recompute drift; deterministic). `tests/perfanalytics/test_visualization.py` 5 passed (PNG magic, non-empty, determinism). `tests/perfanalytics/test_pipeline_e2e.py` 6 passed (market order, suffixed paths, schemas, no WI-014 coupling). Focused suite 48 passed.

04:36 | step 5 | done | Focused suite `uv run pytest tests/perfanalytics -q` → 48 passed; repository suite `uv run pytest -q` → **444 passed, EXIT:0** (detached `logs/wi015_full_suite.out`) = 396 pre-existing + 48 new, nothing broken. Market modes covered: CAD-only, USD-only and BOTH (CLI ordering tests) — BOTH runs CAD then USD per plan. Frozen check: `git status` shows **no modified tracked files** — WI-014 scripts/CSV/PDF and every pre-existing report untouched; only new `reports/perfanalytics/*` + ignored `data/perfanalytics/*`. Concern: resource — alignment peak RSS 1.88 GB (CAD) / 2.86 GB (USD) on the 8 GB host, no swap; comfortably inside budget but the largest WI-015 footprint, single-process and fold-major by design.

## DEVIATIONS

1. **`donchian_break_f<W>` is NaN during warm-up (step 3).** The shipped
   `_range_fib_features` emits `0.0` while the prior window does not yet exist
   (`hh.shift(1)` is NaN). WI-015 masks those rows to NaN instead, so the panel's
   "no partial windows / NaN until full history" acceptance holds for every
   family (it is a binary flag, so `False` there would be a partial-window
   artefact). Only the warm-up rows change; the flag value is unchanged wherever
   a prior window exists. Flagged for PM — say the word and it reverts to the
   shipped `0.0` behaviour.

2. **Open concern (not a plan deviation): BOARD.md still shows WI-015 at
   DESIGN/PLAN**, not EXECUTING. The admin ordered Build in-chat after the
   addendum commit; Build was told not to touch BOARD.md, so the row still needs
   moving by PM/scribe.

STATUS: DONE | evidence: `uv run pytest tests/perfanalytics -q` → 48 passed; `uv run pytest -q` → 444 passed EXIT:0 (`logs/wi015_full_suite.out`); real runs exit 0 — targets CAD 338 sym/1,191,669 rows, USD 533 sym/2,121,659 rows; features CAD 338 sym/1,196,063 rows/150 cols (233-window coverage 337/338), USD 533 sym/2,128,588 rows (533/533) + `reports/perfanalytics/features_summary_{CAD,USD}.md`; alignment `reports/perfanalytics/alignment_{CAD,USD}.{csv,json,md}` (1200 candidate rows each; 558 CAD / 487 USD pass the same-sign + noise-margin bar, best-per-target cell 8/8 both markets; CAD 3:01, USD 5:11, `logs/wi015_alignment*.out`); addendum `heatmap_{CAD,USD}.png` (290 KB, `%PNG`), `alignment_top_{CAD,USD}.csv` (top-10 per target×horizon), family-vs-timeframe summary appended to both `.md`. BOARD.md and all WI-014 artifacts untouched by Build (log-only + new files). Stop at PM verification / admin gate.