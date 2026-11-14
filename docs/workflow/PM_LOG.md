# PM_LOG.md — cursor for the Hermes PM cycle

> One entry per PM cycle, newest first. The newest entry's cursor (`cursor:` line)
> defines which opencode sessions the next cycle ingests. Kam's trigger: tell Hermes
> "run PM cycle". Full procedure: `docs/human/PM-CYCLE.md`.
## 2026-11-14 — Cycle 34 (D-026 L0 R12 runs closed — bug found+fixed, RATIFIED)

- **L0 R12 grid runs DONE + RATIFIED (admin in chat 2026-11-14, Layer 1).** Consolidated evidence: `reports/l0_r12_v2/l0_r12_consolidated.md` (supersedes nothing on disk).
- **First run contaminated (implementation bug, not theory):** `scripts/run_l0_r12.py` `_features_for` defined base = candidates minus *this* block's cols, so each block's fit included the other five blocks' surviving columns → all six blocks byte-identical fold AUCs; delta measured the union, not the block. Run retained (0.59 core-h, `reports/l0_r12_summary.md`, ckpt `/tmp/l0_r12_ckpt/` 84 cells) and relabeled as the **union test** (3/12 survivors, ΔAUC +0.002–0.005 — the ceiling).
- **Fix + corrected run:** base excludes all six blocks' cols; per-block delta re-run on a copied ckpt (`/tmp/l0_r12_ckpt_v2/`, nothing deleted) — 0.25 core-h. **L0-5 survives 4/12** (`disp_entropy_39`, all `xsec_vol_rank_bin`, ΔAUC +0.002–0.004, cross-market consistent); L0-2/L0-4 fully absorbed by ρ-prune (Q1 rule, delta ≡0 by construction, absorption table in report); L0-1/L0-3/L0-6 0/12.
- **Not kept (admin-directed flags, report §6):** 21 of 27 block cols excluded from the L1/L2 candidate set — L0-1 (3 absorbed + 2 no-delta), L0-2 (8 absorbed), L0-3 (3 no-delta), L0-4 (4 absorbed), L0-5 `disp_atr_pct_21` (absorbed), L0-6 (4 no-delta). Only addition: `disp_entropy_39`.
- **Admin direction recorded (not dispatched):** larger variant run at a lower rho-prune threshold to maximize parameters for L1/L2 grids — a NEW pre-registered family/variant, never merged into the ρ=0.3 verdicts; the flagged not-kept cols are its re-admission population.
- **Open items:** WI-048d/e/f verdicts still PROVISIONAL (ratification pending); L1 grid runs WI-058…061 pending, `ALL_FAMILIES` lacks `mfe_mae_*`/`move_*` wiring (PM-owned); scripts/run_l0_r12.py + reports/l0_r12_v2/ uncommitted (this cycle's commit).
- **Cursor:** next cycle ingests sessions from 2026-11-13T17:00Z forward.

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
