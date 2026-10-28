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

STATUS: PLAN