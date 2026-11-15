# PM_LOG.md — cursor for the Hermes PM cycle

> One entry per PM cycle, newest first. The newest entry's cursor (`cursor:` line)
> defines which opencode sessions the next cycle ingests. Kam's trigger: tell Hermes
> "run PM cycle". Full procedure: `docs/human/PM-CYCLE.md`.
## 2026-11-14 — Cycle 38 (Phase-1 chain WI-064/065 closed GREEN; WI-066 dispatched)

- **Phase-1 chain (PID 77422) closed GREEN by watchdog cron:** both builders finished (EXIT_64:0, EXIT_65:0, CHAIN_DONE), footers filled, no live builder. Diff-only audit clean — dirty files matched the two manifests exactly (plus pre-existing untracked `data/`/`reports/` noise). WI-064 test gate exit 0 (5 passed + smoke EXIT 0, 2.4s); WI-065 test gate exit 0 (28 passed + smoke EXIT 0, D-024 guard pinned: tau 0.7, calib 0.0314, eval 0.0357, z 38.90). Cards in `done/`, locks EMPTY (released via python3 rewrite — no write-protection this time).
- **Commits:** WI-064 `6126626`, WI-065 `7e60406`, board+PM_LOG doc commit (this one). WI-064 footer notes INDEX.md added within manifest spirit (DoD §3); WI-065 deviations: prereg template emitted to `reports/l2_harness_smoke/` (outside manifest by design), harness.py 389 lines (accepted deviation).
- **WI-066 dispatched (single-signal xsec top-k screener, code+smoke only):** detached opencode surgical-builder, log `logs/wi066.out`, watchdog cron `wi066-watchdog` every 20m closes it and STOPS before WI-067/068 — PM CALIB runs and stop/continue decisions stay with the interactive session.
- **Gate rulings on record (D-027 §11):** floor 10 bps net; fold ceiling 50% max-share + majority-positive; min names/date 20; long-only first pass; sector map assumed absent; INCONCLUSIVE closed as-run; FDR family separate.
- **Rotation:** cycles 33–36 rotated to `docs/workflow/archive/PM_LOG-2026-11-14_cycles33-36.md`.
- **Cursor:** next cycle ingests sessions from 2026-11-14T23:00Z forward.

## 2026-11-15 — Cycle 40 cont. (WI-068 closed GREEN in interactive session)

- **WI-068 (fixed vs event exits, code+smoke) closed GREEN, one attempt (no timeout):** foreground dispatch completed inside the window. Close gate re-run by PM: `pytest tests/l2_overlay/test_time_exit.py` exit 0 (**12 passed**, 1.57s) + `--smoke` EXIT 0. Smoke CALIB read-out on identical entries: USD best fixed_h13 +103 bps vs event −50; CAD same shape → CONTINUE both markets. Smoke artifacts `reports/l2_time_exit_smoke/`. Commit `a2da37f` touched only the two manifest files + card footer (diff-only audit clean); card moved to `done/`, close `0980a69`; locks EMPTY.
- **WI-065-FIX1 (defect found at the PM full run):** the full-universe xsec CALIB crashed in `harness._cell_keys` — both real manifests carry the key data as `binary`/`h` columns, not the `family`/`horizon` names WI-065 assumed (smoke passed only on synthetic frames); wi040 also has 96 NaN `variant` rows. Scoped fix commit `182875a` (harness.py + test_harness_union.py, 44 tests green); union now loads: 10,760 raw → 8,571 unique cells (2,189 cross-manifest dupes dropped, wi040 kept first). Lock released.
- **PM CALIB prep status (blocker):** the drivers expect a PM-built prepared panel `data/models/l2_prepared/<MKT>.parquet` (per-date/symbol OOF scores of the winning cells + `r` + fold) — it does not exist and no WI produces it. Raw material verified: wi048 holds the winning fold pickles (xsec_vol_rank_cont xgboost/h55, move_occur/move_dir_up xgboost/h5; per-fold models, 47-feature design reproducible via `grid_targets_ext._design` + cached `load_panel`); b_hold pickles are WI-035-era with a 23-feature list in provenance (needs its own feature build). OPEN design decision: the definition of the panel's `r` (trade return) is not pinned in D-027 or the WI cards — memo to admin before building.
- **Next:** WI-069/070 remain CONDITIONAL (admin go after CALIB survivor / sector map); WI-071 one-shot EVAL gate is PM-owned. The interactive session's next decision is PM CALIB runs or holding for admin direction.
- **Cursor:** superseded by the WI-068 close — sessions from 2026-11-15T02:00Z forward.

## 2026-11-15 — Cycle 40 (WI-067 closed GREEN in interactive session)

- **WI-067 (regularised stack ranker, code+smoke) closed GREEN, two attempts:** attempt 1 (foreground dispatch) killed at the harness 420s ceiling mid-run — all three manifest files landed but unverified. Attempt 2 (scoped resume, approved foreground): fixed the verdict/guard logic (smoke had stack beating best single but verdict STOP), test gate exit 0 (**10 passed**, 5.80s) + `--smoke` EXIT 0. Beats-best-single guard holds on CALIB in both markets: USD stack +318.5 vs best single `xsec_vol_rank_cont` +151.4 bps; CAD +324.7 vs +142.8 bps → CONTINUE. Smoke artifacts `reports/l2_stack_rank_smoke/`, `data/models/l2_stack_rank_smoke/`.
- **Commits:** WI-067 source+tests+card `6966a8c` (footer: Attempts 2/2, Status DONE; no edits outside manifest); dispatch bookkeeping `7b7d529`; close-out `731a68d`. Locks released via python3 json rewrite; `active_locks` EMPTY.
- **Lesson:** foreground builder dispatch was blocked once on detached-Popen approval timeout (stop sign honored), then admin approved foreground relaunch — landed inside the 420s window. Keep the detached-Popen+watchdog pattern for any run modeled >~5 min.
- **Next:** WI-068 (fixed vs event exits, card in `draft/`) is the next dispatchable WI; WI-069/070 remain conditional; PM CALIB runs stay with the interactive session.
- **Cursor:** next cycle ingests sessions from 2026-11-15T01:30Z forward.

## 2026-11-14 — Cycle 39 (WI-066 closed GREEN by watchdog; chain hands back to interactive session)

- **WI-066 closed GREEN by watchdog cron:** builder finished (footer filled: 3 test-command attempts / 2 defects fixed, Status DONE ≈0.05 core-h) but died at the session layer before the EXIT_66 marker — artifacts all predate the log's last write, so closed PM-verified without a relaunch (WI-064/065 precedent). Close gate: `uv run pytest tests/l2_overlay/test_xsec_rank.py -q --maxfail=1` exit 0 (9 passed, 2.07s) + `--smoke` exit 0 (6 fold JSONs + 6 md reports in `reports/l2_xsec_rank_smoke/`). Diff-only audit clean: card + manifest paths only; card moved `in_progress/`→`done/`, footer Commit field patched to `PENDING (HEAD e72434157d6e; no commit made)`.
- **Commit:** WI-066 `42c285f` (source `src/l2_overlay/constructions/xsec_rank.py`, tests `tests/l2_overlay/test_xsec_rank.py`, done card) + this board/PM_LOG doc commit. Locks released via python3 json rewrite — no write-protection this time; `active_locks` EMPTY.
- **Gate values RULING on record (admin "proceed with recommendations" 2026-11-14, D-027 §11):** materiality floor 10 bps net; fold ceiling 50% max-share + majority-positive; min names per date 20; long-only first pass; sector map assumed absent; INCONCLUSIVE closed as-run; FDR family separate.
- **Chain STOPS here per ruling:** WI-067/068 dispatch and PM CALIB runs + stop/continue decisions belong to the interactive session (watchdog cron `wi066-watchdog` removed at close-out).
- **Rotation:** cycle 37 rotated to `docs/workflow/archive/PM_LOG-2026-11-14_cycles33-36.md`; newest-2 = cycles 38–39.
- **Cursor:** next cycle ingests sessions from 2026-11-14T23:30Z forward.
