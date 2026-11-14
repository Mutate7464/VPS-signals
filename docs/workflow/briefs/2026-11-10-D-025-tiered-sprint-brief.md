# D-025 Tiered-Sprint Brief — WI-046 → 045 → 047 → 048 → 049

> For: the next series of builder/PM runs | 2026-11-10 | Everything a cold-start session needs, token-optimized.
> Full specs: `docs/kanban/draft/WI-04X-*.md` (approval-gated; this brief does not replace the gate).

## STATE (verified 2026-11-10, commit 3b7b6db)

- **L1 library (RATIFIED):** `data/models/wi040/manifest.parquet`, 9,745 rows = WI-036(96) + WI-038(6,838) + WI-044(2,811) fold pickles. Only `b_hold`, h∈{5..89}, 10 learners. Best: xgb/b_hold/h13 AUC .7836 USD/.7207 CAD (Brier skill +.327 USD); rf/b_hold/h21 min AUC .7341.
- **L2 CLOSED (all 7 questions, RATIFIED):** 4 modern (WI-042) + 3 legacy (WI-043). Pattern: placebo z up to +5.88 but EVAL edge ~0 vs 25 bps. Cross-market transfer REJECT (wi012, CAD edge −0.46 bps). L2 pause: no overlay dispatch until WI-045 names the decay mechanism.
- **Aligned features (~8–10 of 100+):** `atr_pct_3` (top both markets), `cs_entropy_102`, `entropy_24/39`, `hurst_15/39`, `adx_21/144`, `di_spread_3/233`, `kama_er_15`, `range_compression_8_55`, `swing_depth_atr`, `bars_since_opp`. Sector one-hots/calendar ≈ 0.
- **Frozen baseline:** `frozen_fib_w28entry_w30exit_t15_s10_d39_close`, 25 bps. Panel caches: `/tmp/wi036`, `/tmp/wi035` (must exist before any L2 rerun).

## SERIES (WIP 1, order 046→045→047→048→049)

| WI | One-liner | Cap core-h | Notes |
|---|---|---|---|
| 046 | Docs → tier map (T1 features / T2 predictions / T3 action) | 0 | doc-only; table verbatim from D-025 §1 |
| 045 | Edge-decay probe: rank tau-mass vs fold vs cost floor on WI-042's 20 ADOPT cells (`reports/l2/rerun_modern.json`) | 0.3 | no refit; unblocks 049 |
| 047 | Feature gap inventory + research shortlist (realized-vol, volume/liquidity, seasonality, cross-asset); strengthens entropy/Hurst/ATR% | 0.2 | no new deps/ingestion |
| 048 | Target families `up` / `high_low` / `vol_expand` × h ladder × library learners, ONE BH-FDR family, probe-first dry-run on denser market | 2.0 | builder = code+tests+smoke; **PM owns full grid** |
| 049 | Mechanism survey doc (time-exits, relative-value, vol-target sizing, L/S pairs), each tied to a WI-045 mechanism, cost math on frozen baseline | 0.1 | depends 045; scoping only |

## MECHANICS (per skills kanban-orchestrator + signals-workflow-execution; those win on conflict)

- Approvals: matrix presented 2026-11-10, **PAUSED — dispatch only after admin approves in chat**. Verdicts PROVISIONAL until admin ratifies; D-024 pre-committed closures stand.
- Locks: register `write_files` in `.hermes/locks.json` before moving card to `in_progress/`. **Before dispatching: `pgrep -af 'opencode run'` + `cronjob_manage list` — a chain watchdog may have already advanced the queue (near-miss 2026-11-10).**
- Dispatch: `/home/yycuser/.opencode/bin/opencode run --agent surgical-builder --auto --format json "<prompt>"` detached via Popen + watchdog cron (never `terminal(background=true)` for >10 min runs); prompt appends: "Run long commands in the FOREGROUND and wait for them; fill telemetry only after the full run completes."
- Audit: diff-only, never read full source; re-run `test_command` yourself; builder full-run claims are self-reports — PM re-verifies and owns verdict numbers.
- Budget = caps + grids; correctness invariants (purged/embargoed CV, CALIB-only selection, float32, symbol-sequential, n_jobs=2) are NEVER loosened.
- VPS: 2 vCPU; `uv sync` breaks lightgbm unless `sitecustomize.py` preloads torch's libgomp (re-create after any venv rebuild).

## KEY PATHS

- Board (single source): `docs/workflow/BOARD.md` · Design: `docs/workflow/designs/D-025-tiered-workflow.md` · Inventory: `reports/tiered_workflow_status_2026-11-10.md`
- L2 reports: `reports/l2/{rerun_modern,rerun_legacy}.{md,json}` · L1: `reports/wi040_calibration.md`, `reports/wi044_summary.md`
- Harness: `src/l2_overlay/harness.py` · Grid: `src/swing_bsh/binary_grid.py` · Manifest schema: `src/swing_bsh/library_audit.py`
