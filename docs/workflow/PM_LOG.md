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

## 2026-11-14 — Cycle 39 (WI-066 closed GREEN by watchdog; chain hands back to interactive session)

- **WI-066 closed GREEN by watchdog cron:** builder finished (footer filled: 3 test-command attempts / 2 defects fixed, Status DONE ≈0.05 core-h) but died at the session layer before the EXIT_66 marker — artifacts all predate the log's last write, so closed PM-verified without a relaunch (WI-064/065 precedent). Close gate: `uv run pytest tests/l2_overlay/test_xsec_rank.py -q --maxfail=1` exit 0 (9 passed, 2.07s) + `--smoke` exit 0 (6 fold JSONs + 6 md reports in `reports/l2_xsec_rank_smoke/`). Diff-only audit clean: card + manifest paths only; card moved `in_progress/`→`done/`, footer Commit field patched to `PENDING (HEAD e72434157d6e; no commit made)`.
- **Commit:** WI-066 `42c285f` (source `src/l2_overlay/constructions/xsec_rank.py`, tests `tests/l2_overlay/test_xsec_rank.py`, done card) + this board/PM_LOG doc commit. Locks released via python3 json rewrite — no write-protection this time; `active_locks` EMPTY.
- **Gate values RULING on record (admin "proceed with recommendations" 2026-11-14, D-027 §11):** materiality floor 10 bps net; fold ceiling 50% max-share + majority-positive; min names per date 20; long-only first pass; sector map assumed absent; INCONCLUSIVE closed as-run; FDR family separate.
- **Chain STOPS here per ruling:** WI-067/068 dispatch and PM CALIB runs + stop/continue decisions belong to the interactive session (watchdog cron `wi066-watchdog` removed at close-out).
- **Rotation:** cycle 37 rotated to `docs/workflow/archive/PM_LOG-2026-11-14_cycles33-36.md`; newest-2 = cycles 38–39.
- **Cursor:** next cycle ingests sessions from 2026-11-14T23:30Z forward.
