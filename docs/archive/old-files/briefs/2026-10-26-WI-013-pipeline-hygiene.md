# Brief — WI-013: Pipeline hygiene + two-market parametrization

> Admin order 2026-10-26 (option A accepted): pay down findings F-2..F-5 from
> `reports/wi012_iteration_notes.md` so both markets run natively. F-3 amended
> by admin: **default is BOTH USD and CAD** unless a market is explicitly
> specified. No research content: no models, no targets, no skill bars.

## Context (verified during WI-012, this cycle)

- F-1 is DONE (e5 horizon-20 NaN fix + regression `tests/test_e5_baseline_horizon_nans.py`); it is NOT in scope here.
- F-2: `src/factors/e5_baseline.py` `write_report` hardcodes "Compiled on CAD" even for USD output (~line 189/192 report body text).
- F-3: `src/wi011/__init__.py` `MARKET = "CAD"` constant; `scripts/wi011_preflight.py` hardcodes `features_CAD.parquet` / `targets_CAD.parquet` paths; the other five WI-011 scripts take their market only from that constant. WI-012's USD run required temporary sed patches + reverts.
- F-4: BOTH `data/features/features_{USD,CAD}_metadata.parquet` embed 4 label columns (`y_15d_high`, `y_15d_low`, `y_20d_up`, `y_20d_down`). No live leak (trainer selects explicit catalog columns), but any all-columns consumer would train on labels.
- F-5: every stage script writes its report to a hardcoded path (`reports/wi009_e5_baseline_{market}.md` excepted) — WI-012 overwrote frozen gate reports 3× (`wi009c_regression.md`, `wi009c_summary.md`, `wi011_*.md`), each needing `git checkout` restore.

## Goal

Every report-writing stage script in the current route runs BOTH markets natively
(default) or one by flag, writes market-suffixed report paths so frozen gate
artifacts can never be overwritten, and the metadata feature panels contain no
label columns, with the rebuild verified old==new on all surviving columns.

## Required changes

1. **F-3 + F-5 (report writers):** add `--market` to the six `scripts/wi011_*.py`
   scripts (choices USD/CAD; default = run BOTH sequentially, USD then CAD) and
   thread it through `src/wi011` (replace the module constant with a parameter;
   `src/wi011/panel.py` functions already take `market` args). Same treatment for
   `scripts/probe_wi009c.py`, `scripts/train_wi009c.py`, `scripts/evaluate_wi009c.py`,
   `scripts/wi009b_launch.py`, `scripts/rank_assets.py`, `scripts/train_contrastive.py`,
   `scripts/check_wi009c_inputs.py`: default = both markets sequentially.
   All report/output paths MUST become market-suffixed (e.g.
   `reports/wi011_preflight_{market}.md`, `reports/wi009c_regression_{market}.md`,
   `reports/wi009c_summary_{market}.md`); a run must never write an unsuffixed path.
   NOTE: existing unsuffixed CAD files are frozen gate records — do NOT rename,
   delete, or rewrite them; the first suffixed run for CAD may (and should)
   produce a NEW file alongside.
2. **F-2:** fix the hardcoded "Compiled on CAD" report string in
   `src/factors/e5_baseline.py` to name the actual market.
3. **F-4 (rebuild, both markets):** strip the 4 label columns from
   `data/features/features_{USD,CAD}_metadata.parquet`. Rebuild must follow the
   skill's rebuild recipe: mirror the original construction (do NOT use the
   legacy full-history `load_market_frame` path), write to a staging file,
   **assert old==new on row count and every surviving column (byte/dtype-safe
   comparison) before swap**, and leave a backup of the pre-swap file on disk.
   Add a regression test asserting NO `y_*` label columns exist in either
   metadata panel loader path.
4. Backfill the canonical WI-009c regression/summary/shortlist reports for CAD
   under the new suffixed names (regeneration is cheap: ridge train 19.4s USD /
   similar CAD; use existing scripts with the new flags) so future runs compare
   like-for-like without touching frozen files.

## Constraints

- Read-only wrt frozen gate artifacts: no `git rm`/rename/rewrite of any existing
  `reports/wi009*`, `reports/wi011_*` unsuffixed file, `reports/diag_*`, or
  sprint reports. Do not commit regenerated copies of frozen reports.
- Host limits: n_jobs=2, float32 immediately, no all-ticker uncompressed frames.
- No change to factor math, target definitions, skill-bar logic, or split logic.
- No secrets/credentials. `git add` by explicit path only.

## Acceptance / deterministic verifies (plan must carry these or equivalents)

- `uv run pytest tests/ -q` full suite passes with the new tests.
- New test files: (a) metadata panels contain no `y_*` label columns;
  (b) every `--market`-capable script defaults to both markets and rejects
  invalid market strings; (c) report path helper yields market-suffixed paths
  for every writer listed above (no unsuffixed writer reachable).
- F-4 swap verification: printed old==new table (rows + per-column equality)
  for USD and CAD, committed as `reports/wi013_rebuild_verification.md`;
  pre-swap backups exist on disk (gitignored path is fine).
- Spot-run: `uv run python scripts/wi011_preflight.py` alone prints a plan
  line naming BOTH markets and writes `wi011_preflight_USD.md` + `..._CAD.md`.
- Frozen-artifact guard: `git status --short reports/` shows NO modification to
  any pre-existing unsuffixed report after a full both-market run.

## Out of scope

- F-1 (done), P-1 verifier dedupe wart, P-2 gitignore audit, P-3 doc rotation,
  WI-004/WI-005 backlog, any new model/target/feature research, USD screener
  wiring (that is a separate gated decision resting on WI-012's result).

## Stop point

Plan ends at the human gate: Build executes steps, PM verifies, admin decides.
No auto-merge of the F-4 swap if the old==new assert fails — escalate.