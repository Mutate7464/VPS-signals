# BOARD.md — flat queue (single source for "what now / what next")

> Rules: `WORKFLOW.md` §2. **Rows are pointer-only:** one line per row — title, gate, verdict tag, evidence path. Verdict narratives, test counts and ratification quotes live in the WI card and the cited report; `PM_LOG.md` is the canonical decision record.
> Kanban dirs: `docs/kanban/{ready,in_progress,blocked,done}/` (cards hold detail); archived cards: `docs/archive/wi/` (indexed in `docs/execution/WI_AND_RUN_LEDGER.md`).
> Full pre-lean board (2026-11-14, all per-WI narratives preserved): `docs/workflow/archive/BOARD-2026-11-14-pre-lean.md`; older: `docs/workflow/archive/BOARD-2026-11-07-pre-flat.md`.

**Last updated:** 2026-11-19 (Track A visualizer chain running: WI-085..088 DONE, WI-089 dispatched; Track B batch WI-074..079 built+closed; housekeeping trim 2026-11-18 — board was over its 5 KB cap; the full ratified
D-027/D-026 closure narrative is preserved verbatim in `docs/workflow/archive/BOARD-2026-11-16-D027-active-detail.md`).
D-027 sprint CLOSED + RATIFIED: WI-071-EVAL **ADOPT** (fixed_h55 unsized = L2 overlay exit rule; net +452.1 USD / +445.7 CAD, both folds positive, BH q≈0; EVAL split SPENT; shortlist-only, no live trading). (b) KILLED, (c) vol-target REJECT, (d) descoped (new prereg + new split required for any future EVAL). D-026 sprint DONE + RATIFIED (L1 extension: 5 families integrated). ~~L1 library FROZEN~~ — **UNFROZEN (admin 2026-11-19): L0/L1/L2 all open for new research WIs.**

## ACTIVE
- [DONE] WI-085 | Scaffold visualizer: loader, schema contracts, latency benchmark | gate 0 (machinery) | no verdict numbers — machinery accepted | `docs/kanban/done/WI-085.md` | commits b93935f 2606baf
- [DONE] WI-086 | Join index, global filter bar, KPI strip | gate 0 (machinery) | no verdict numbers — machinery accepted | `docs/kanban/done/WI-086.md` | commit 5ca9578
- [DONE] WI-087 | View 1 legacy-target histograms, decile hit rate, CIs, null | gate 0 (machinery) | no verdict numbers — machinery accepted | `docs/kanban/done/WI-087.md` | commit 202cd12
- [DONE] WI-088 | View 3 OHLC drill-down, barrier overlays, mismatch badge | gate 0 (machinery) | no verdict numbers — machinery accepted | `docs/kanban/done/WI-088.md` | commit 9cc2997
- [DONE] WI-074..079 | L0 feature batch (NR4/NR7, CUSUM, CLV, StochRSI, Connors RSI, fail_count) — all code+tests+smoke PASS, gates green | RATIFIED-eligible machinery (no gate numbers — eval jobs are separate BH-FDR family gates) | cards `docs/kanban/done/` | commits 5bcd41b 9ef7a4c 4300c9e 72e4191 c034805 68a966a
No WIP, no open sprint brief. Admin 2026-11-19: next = **Track B (L0/L1/L2 research) BEFORE Track A (visualizer)**; plan `docs/plans/26-W47-visualizer-audit-workbench.md`, brief `docs/workflow/briefs/2026-11-19-visualizer-audit-workbench-raw.md`.
Any future (d)/vol-target EVAL needs a NEW prereg + NEW split. Full narrative: `docs/workflow/archive/BOARD-2026-11-16-D027-active-detail.md`.


### D-027 SPRINT — CLOSED + RATIFIED 2026-11-16 (design `designs/D-027-l2-rebuild.md`, outcome §13; full detail `archive/BOARD-2026-11-16-D027-active-detail.md`)
- [DONE] WI-064/065/066/067/071/072/073 | infra, harness, screeners, EVAL machinery, sector map — all code+smoke PASS | cards `docs/archive/wi/` (compacted 2026-11-18; ledger `docs/execution/WI_AND_RUN_LEDGER.md`) | commits 6126626 7e60406 6966a8c 4e3e125 cdf02a9
- [DONE] WI-068 | fixed time exits h13/h55 vs event on identical entries | ACCEPTED — fixed_h55 carried to EVAL | card `docs/archive/wi/WI-068-time-exits.md` | commit a2da37f
- [DONE] WI-069 | (c) vol-target sizing | full CALIB: sizing REDUCES net edge both markets → (c) REJECT RATIFIED | `reports/l2_vol_target/`
- [DONE] WI-071-EVAL | one-shot EVAL, fixed_h55 unsized, split SPENT | computed REJECT (ceiling knife-edge 0.533/0.597, 2 folds positive) → **RATIFIED ADOPT (admin in chat, Layer 2)** | `reports/l2_eval/` | commit 846ce5d
- [DESCOPED] WI-070 | (d) sector pairs — any future (d) EVAL needs a NEW prereg + NEW split | card `draft/`


### D-026 SPRINT — DONE + RATIFIED 2026-11-14 (design `designs/D-026-l0l1-extension.md`; full detail `archive/BOARD-2026-11-16-D027-active-detail.md`)
- Ruling: `vol_expand` label backward-looking — quarantined; forward use only via `vol_expand_fwd` (WI-051)
- [DONE] WI-059b | L1-1/1-2 continuous families, regression read-out | 24/24 survivors, best min rank-IC +0.6475 (xgboost/h55) RATIFIED L1 | `reports/l1_ext_cont/`
- [DONE] WI-060 | `move_occur` + `move_dir_up` grids | 24/24 survivors each, min AUC 0.6033 / 0.6407 RATIFIED L1 | `reports/t2_grid_move{occur,dirup}_summary.md`
- [DONE] WI-061 | L1-4 average-uniqueness weighting (code+tests, `sample_weight=` opt-in) | RATIFIED | card `docs/archive/wi/`
- [DONE] WI-050/051/052 | Phase 0 harness + fwd label + L0-1 block | cards `docs/archive/wi/`
- [DONE] WI-053…057 | L0-2…L0-6 blocks — only L0-5 survives (`disp_entropy_39`); 21/27 cols not-kept | `reports/l0_r12_v2/l0_r12_consolidated.md`
- [DONE] WI-058/059a | L1-1 xsec vol-rank bin + `mfe_mae_bin` grids | RATIFIED L1 (min AUC 0.8226 / 0.5515) | `reports/t2_grid_*_summary.md`, `reports/l1_ext/`
- [DONE] WI-062 | L1.5 meta-label machinery + permuted-label leakage test | RATIFIED (full-universe run = separate future gate) | card `docs/archive/wi/`

### D-025 SPRINT — complete (design `designs/D-025-tiered-workflow.md`)
- [FOLDED] WI-049 | mechanism survey → folded into the L2 rebuild brief; card `draft/` retained as source material
- **L1 FREEZE (admin 2026-11-14)** stands: larger-variant lower-ρ family PARKED post-rebuild
- [DONE] WI-045…048f | tier map · edge-decay probe · feature-gap inventory · label builders + grids up/high_low/vol_expand | survivors RATIFIED into L1 library | `reports/t2_grid_*.md`, `reports/t2_targets_ext_summary.md`

### CLOSED
- D-024 batch (WI-032…044) — all DONE + RATIFIED 2026-11-09/10: L2 reruns closed per D-024 pre-committed closure (REJECT/INERT permanent; 20 ADOPTs statistically real, economically nil — NO deployment); L1 library consolidated (WI-040 manifest 9,745 rows) | `reports/l2/rerun_modern.md`, `reports/l2/rerun_legacy.md`, `reports/wi040_library_manifest.md`; cards `docs/archive/wi/`
- D-023 and earlier (WI-001…031) — closed; cards `docs/archive/wi/`, briefs `docs/archive/old-files/human-briefings/`, per-WI one-liners in this file's git history
- [DONE] WI-034 | binary-decompose probe | DEFERRED by admin 2026-11-09 (superseded by WI-035/036; question re-answered by WI-060's move decomposition) — card archived 2026-11-14 to `docs/archive/wi/`
- [BLOCKED] none (`docs/kanban/blocked/` empty)

## BACKLOG
- [BACKLOG] WI-005 | Post-MVP: EP-06 index scraper, EP-07 Telegram digest, EP-08 regime tuning | superseded by `docs/governance/PHASE2_HANDOVER_RUNBOOK.md`

## Column policies
- `[TODO]` = in `ready/`, meets DoR, admin-ordered. `[WIP]` = in `in_progress/`, locks registered, WIP limit 1.
- `[BLOCKED]` = in `blocked/`, two-strike tripped, owner and 1-line reason on the row.
- `[DONE]` = QA verdict and gate recorded. Rows are pointer-only (WORKFLOW §2): narrative lives in the card + cited report; PM_LOG is canonical.
- Risks: `RISKS.md`. Data facts: `DATA_CONTRACT.md`. Decisions: `designs/`. Gate and cycle record: `PM_LOG.md` (newest 2 cycles).
