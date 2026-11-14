# PM_LOG.md — cursor for the Hermes PM cycle

> One entry per PM cycle, newest first. The newest entry's cursor (`cursor:` line)
> defines which opencode sessions the next cycle ingests. Kam's trigger: tell Hermes
> "run PM cycle". Full procedure: `docs/human/PM-CYCLE.md`.
## 2026-11-14 — Cycle 37 (D-027 issued — L2 rebuild scoping approved; Phase-1 chain dispatched)

- **D-027 created + committed** (`docs/workflow/designs/D-027-l2-rebuild.md`, commit ec39c78): (b)-led stepwise screener chain, WI-064…071, ≈11–14 core-h total, decay attribution (fold-concentration 55% / cost-floor 44.8%) as design driver. Source: batch-planner fullpack `docs/plans/26-W47-L2-rebuild-scoping-fullpack.md`.
- **Phase 0 defaults ADOPTED + Approval Matrix APPROVED (admin in chat).** Phase-1 chain (WI-064 meta-label driver → WI-065 harness upgrade) dispatched as ONE detached chain (PID 77422, `logs/phase1_chain.sh`, EXIT_64/EXIT_65 markers); watchdog cron 5088aa7d559e every 20m delivers close-out to this chat and STOPS before WI-066.
- **Gate-value rulings RECORDED (admin "proceed with recommendations" 2026-11-14, D-027 §11):** materiality floor **10 bps net**; fold ceiling **50% max-fold share + majority-positive** (confirmed as proposed); **min 20 names/date** for the xsec INERT precheck; **long-only first pass** (L/S awaits borrow confirmation); sector map assumed absent (WI-070 conditional); INCONCLUSIVE closed as-run; FDR family separate from D-024. Watchdog prompt updated to chain WI-066 (code+smoke) dispatch after a green Phase-1 close; PM CALIB runs and stop/continue decisions remain interactive-session gates.
- **Cursor:** next cycle ingests sessions from 2026-11-14T22:00Z forward.

## 2026-11-14 — Cycle 38 (Phase-1 chain WI-064/065 closed GREEN; WI-066 dispatched)

- **Phase-1 chain (PID 77422) closed GREEN by watchdog cron:** both builders finished (EXIT_64:0, EXIT_65:0, CHAIN_DONE), footers filled, no live builder. Diff-only audit clean — dirty files matched the two manifests exactly (plus pre-existing untracked `data/`/`reports/` noise). WI-064 test gate exit 0 (5 passed + smoke EXIT 0, 2.4s); WI-065 test gate exit 0 (28 passed + smoke EXIT 0, D-024 guard pinned: tau 0.7, calib 0.0314, eval 0.0357, z 38.90). Cards in `done/`, locks EMPTY (released via python3 rewrite — no write-protection this time).
- **Commits:** WI-064 `6126626`, WI-065 `7e60406`, board+PM_LOG doc commit (this one). WI-064 footer notes INDEX.md added within manifest spirit (DoD §3); WI-065 deviations: prereg template emitted to `reports/l2_harness_smoke/` (outside manifest by design), harness.py 389 lines (accepted deviation).
- **WI-066 dispatched (single-signal xsec top-k screener, code+smoke only):** detached opencode surgical-builder, log `logs/wi066.out`, watchdog cron `wi066-watchdog` every 20m closes it and STOPS before WI-067/068 — PM CALIB runs and stop/continue decisions stay with the interactive session.
- **Gate rulings on record (D-027 §11):** floor 10 bps net; fold ceiling 50% max-share + majority-positive; min names/date 20; long-only first pass; sector map assumed absent; INCONCLUSIVE closed as-run; FDR family separate.
- **Rotation:** cycles 33–36 rotated to `docs/workflow/archive/PM_LOG-2026-11-14_cycles33-36.md`.
- **Cursor:** next cycle ingests sessions from 2026-11-14T23:00Z forward.
