# PM_LOG.md — cursor for the Hermes PM cycle

> One entry per PM cycle, newest first. The newest entry's cursor (`cursor:` line)
> defines which opencode sessions the next cycle ingests. Kam's trigger: tell Hermes
> "run PM cycle". Full procedure: `docs/human/PM-CYCLE.md`.
## 2026-11-13 — Cycle 33 (WI-048 d→e→f chain closed — PM-verified; verdicts PROVISIONAL)

- **Chain complete:** detached PM-run chain (PID 3971052, log `logs/wi-048def_run.out`) finished 05:30–05:59 UTC; watchdog FINISHED, all three stage markers EXIT:0 (`EXIT_D/E/F:`). Chain PID confirmed dead via `kill -0` before close-out.
- **WI-048d (PROVISIONAL, Layer 1 predictive-only):** `high_low` grid — 24 cells scored, 0 truncated; BH-FDR (α=0.05, m=24) survivors 24 (12 USD + 12 CAD, all horizons, both learners; min cross-market AUC 0.5768 lightgbm/h13 — weakly predictive CAD-side). Report `reports/t2_grid_highlow_summary.md`, 121 pickles. All 24 survivors ACCEPTED into the L1 library (no effect-size floor).
- **WI-048e (PROVISIONAL, Layer 1 predictive-only):** `vol_expand` grid — 24 cells, 0 truncated; 24 FDR survivors (12 USD + 12 CAD, all horizons); strongest family: best min-AUC 0.7068 (lightgbm/h13), min rank-IC +0.3581. Report `reports/t2_grid_volexpand_summary.md`, 121 pickles. All 24 ACCEPTED into the L1 library.
- **WI-048f (PROVISIONAL):** cross-family consolidation — 72 cells joined; ranking by cross-market min AUC: vol_expand 0.7068 > high_low 0.6089 > up 0.5038 (WI-048c's `up` remains the weakest family — min-AUC ≈ 0.50, nil); winner-cell attribution for USD|lightgbm|vol_expand|h13 (TreeSHAP: `bars_since_opp` 0.192, `atr_pct_3` 0.152; linear: `atr_pct_3` +0.533). Report `reports/t2_targets_ext_summary.md`.
- **Artifact verification:** `data/models/wi048/manifest.parquet` 295 rows == 295 pickles on disk (set-identical); per family 24 survivor cells × 5 folds = 120 + 1 winner refit. `git status` showed only pre-existing untracked `data/`/`reports/` dirs — no unauthorized tracked edits.
- **Commits:** WI-048d 0b44f35 (+ a385c38 stale-copy fixup), WI-048e 8e48a68, WI-048f 94d88c5; doc close-out commit follows. Cards in `done/`, BOARD rows DONE, umbrella WI-048 closed.
- **Locks:** cron-mode write protection blocked the `.hermes/locks.json` rewrite — d/e/f lock release RECORDED on the BOARD umbrella row per protocol; next interactive session must verify and empty `active_locks` before dispatching anything.
- **Watchdog teardown:** monitor cron (wi048-def-chain-watchdog) removed; `~/.hermes/scripts/wi048_watch.sh` deleted.
- **Open:** admin ratification of d/e/f verdicts in chat (PROVISIONAL until then); EVAL split still virgin; WI-049 (T3 mechanism survey) is next queued.
- cursor: no opencode sessions — all three stages were PM-run (uv run python -m src.swing_bsh.grid_targets_ext), no builder dispatched.
- **Rotation:** Cycle 31 (2026-11-10) rotated to `docs/workflow/archive/PM_LOG-2026-11-10_cycle31.md`.

## 2026-11-13 — Cycle 32 (L1 predictive-only rule; WI-048c ratified; WI-048d dispatched)

- **Admin direction (2026-11-13): T1/T2 gate evidence is PREDICTIVE-ONLY.** Gate evidence at Tier 1 and Tier 2 (Layer 1) = OOF AUC/IC + BH-FDR + calibration. No economic-magnitude or cost analysis is presented at T1/T2 — cost/edge analysis belongs to T3/Layer 2 only. Any FDR-surviving predictor is ACCEPTED and integrated into the L1 pickle library: no effect-size floor, no economic bar at L1. Landed doc-only in `AGENTS.md` (hard constraints) + `WORKFLOW.md` §7 (tier map) in one commit.
- **WI-048c RATIFIED (admin in chat 2026-11-13, Layer 1):** 24 cells, 0 truncated, 11 BH-FDR survivors (8 CAD `up` h5–h21 both learners + 3 USD h5/h8). All 11 accepted into the L1 library (55 fold pickles + `data/models/wi048/manifest.parquet`, WI-040 schema). Predictive license only — no trading claim; EVAL split unburned. Card frontmatter set `verdict: RATIFIED`; PROVISIONAL prefix stripped from the BOARD row.
- **Kanban bookkeeping (commit f40a92a):** WI-048a/b/c cards closed (`status: done` + `verdict:` lines; stale telemetry-footer SHAs corrected 048a→bd80bd5, 048b→3e4fb18, 048c 5880906→f94d5e3); WI-048d/e/f drafts staged into git (were untracked); duplicate WI-045/046/047 cards in `draft/` removed (identical cards already in `done/`, so HEAD carried both copies); BOARD header + D-025 rows refreshed.
- **Dispatched (admin: "ratify and dispatch"):** WI-048d grid `high_low` — PM full-universe run, detached Popen + monitor watchdog cron; close-out chain d → e → f. Credit check before launch: balance 100%, burst_left 3.00 h @100% (each sub-grid ≈ 0.53 core-h, under the 1 core-h pause threshold).
- cursor: opencode session cursor unchanged; pending = WI-048d watchdog cron.
