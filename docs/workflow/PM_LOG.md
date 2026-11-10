# PM_LOG.md — cursor for the Hermes PM cycle

> One entry per PM cycle, newest first. The newest entry's cursor (`cursor:` line)
> defines which opencode sessions the next cycle ingests. Kam's trigger: tell Hermes
> "run PM cycle". Full procedure: `docs/human/PM-CYCLE.md`.

## 2026-11-10 — Cycle 30 (WI-038 full-run close-out PROVISIONAL PASS; WI-040 done PM-verified)

- **WI-038 (L1 long-horizon gap fill) full-universe run: EXIT:0** (attempt 3, detached Popen; watchdog cron fired the close-out). 552 cells scored, 408 truncated by the 2.0 core-h cap (h=233 dropped, then 144; core USD 0.62 h + CAD 1.24 h ≈ 1.86 total, within cap). Winner `tol2_full_k0.8` — best cell mlp_torch|b_hold|h34, min cross-market AUC 0.6962 (CAD 0.8399); 20 BH-FDR survivors, all b_hold, h∈{34,55,89}, both markets; zero starved folds. Expectation (b_hold family again, weaker at long h than WI-036 short-h 0.7207) confirmed. Report `reports/wi038_summary.md`, pickles `data/models/wi038/`. **Verdict PROVISIONAL PASS (Layer 1) — pending admin ratification in chat.** WI card archived to `docs/kanban/done/`, locks released; cycles 27–29 rotated to `archive/PM_LOG-2026-11-09-cycles-27-29.md`.
- **WI-040 (L1 library consolidation) DONE:** builder session was killed by the runtime (EXIT 130) AFTER all artifacts landed; PM independently verified every DoD item before closing (no re-dispatch): tests 7/7, manifest 9,745 rows == 96+6,838+2,811 with 100% path resolution, winner-cell calibration usable (USD Brier skill +0.327, ECE 0.0009), top-20 permutation attribution both markets, `--infer` smoke exit 0. Library now indexed: `data/models/wi040/manifest.parquet` + `reports/wi040_{library_manifest,calibration}.md`. Lesson: builder dispatches that run long (WI-040 took ~40 min) also die at the tool-session layer — same Popen/watchdog lesson as the PM full-run dispatches.
- **Next (admin-gated):** (1) ratify WI-038 in chat; (2) L2 method/layer rebuild — new design doc naming why all seven prior L2 attempts REJECTed and what structurally changes; approval matrix before any dispatch.
- cursor: wi038 watchdog cron (22ed59fa56b6, removed by its own close-out) + surgical-builder WI-040 session (killed, artifacts verified above); no pending sessions.

## 2026-11-09 — Cycle 29b (WI-040 approved; L2 rebuild queued as the following WI)

- **Admin approval in chat ("approve. proceed with current WI; next WI will include rebuilding L2 method and layer"):** WI-040 (L1 library consolidation — manifest across wi035/036/038 pickles, winner-cell calibration + Brier, permutation attribution, `--infer` entrypoint; cap 0.5 core-h) APPROVED — dispatch after WI-038 closes; lock manifest `src/swing_bsh/library_audit.py` + `tests/test_swing_bsh_library_audit.py`.
- **Admin direction for the WI after WI-040: rebuild the Layer-2 method/layer.** All seven prior L2 attempts (WI-011/012/018/028/030/033/037) REJECTed vs the frozen rules; a rebuild must therefore come as a NEW design doc naming why the prior mechanism failed and what structurally changes — present matrix for admin gate before drafting WIs. Sequence: WI-038 close-out → WI-040 → L2 rebuild design + matrix.
- **WI-038 run note:** full-universe attempt 1 died at the PM's own tool timeout (EXIT 143, no grid output; partial pickles written — overwritten by attempt 2, idempotent). Attempt 2 relaunched as a tracked background process with notify-on-complete.
- cursor: none.