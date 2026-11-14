# PHASE2_HANDOVER_RUNBOOK.md — Phase 2 handover (from MVP closeout 2026-11-02)

> **Admin direction 2026-11-06 (in-chat):** P-5 retargeted — 10%/trade goal, low-volume low-risk trades (paper-track must measure realized per-trade P&L, not just bps assumptions; see P-5 note). P-4 scope confirmed — long XGBoost runs stay, probe gates entry to them; **+ low-base-rate eligibility rule added** (few-success datasets assumed; `INELIGIBLE_LOW_N` routing at G1). P-3 **reversed** — markets assumed different, per-market paths kept separate, no `--market` unification sweep. P-1 first sprint unchanged.

## 1. Operational readiness & environment setup

- **Host:** Linux VPS, 2 vCPU / 8 GB, no swap. Hard limits: `n_jobs=2` everywhere (never -1), float32 feature frames, symbol-sequential iteration or `pyarrow.dataset` (no all-ticker uncompressed DataFrame), PDF batches of 10 with `plt.close('all')` + `gc.collect()`.
- **Setup:** `uv sync` (Python ≥3.11; pyproject = `quant-screener`; torch from CPU index). Verify: `uv run python -c "import pandas, pyarrow, xgboost; print('ok')"`.
- **Env vars:** copy `.env.example` → `.env` (gitignored): `OPENROUTER_API_KEY`, `DISCORD_TOKEN`, `IBKR_HOST`, `DISCORD_WEBHOOK_URL` (notify_gate.sh). Confirm `git status` never shows `.env`.
- **Commands:** lint `bash -n <script>` (shell) · single-file tests `uv run pytest tests/test_<wi>_*.py -q` · full suite `uv run pytest` (~7–8 min; run detached, poll `EXIT:N`) · daily shortlist `uv run python scripts/wi014_screener.py --market <CAD|USD>` · data verify `uv run python src/verify_synced_data.py`.
- **Health check:** green suite baseline = **662 passed** (WI-018 close). State: `state/PIPELINE_STATE.json` (`gate_1` live; gates 2–5 legacy). Data: `data/raw_ohlcv/market=<MKT>/symbol=<T>.parquet` (546 USD + 350 CAD).
- **Agent routing:** read root `AGENT.md` → per-dir `INDEX.md` → `docs/architecture/DECISIONS_AND_NEGATIVE_KNOWLEDGE.md` before proposing changes. Board: `docs/workflow/BOARD.md`.

## 2. Prioritized Phase 2 backlog (sprint-ready; acceptance criteria stated)

| # | Item | Entry point | Acceptance criteria |
|---|---|---|---|
| P-1 | **Module splits per debt register D-1** (34 files >250 lines) | `scripts/train_wi009c.py`, `src/feature_engine.py`, `src/xgb_trainer.py` first | per-module single responsibility ≤250 lines; targeted tests per module; suite ≥662 green; no behavior change (regression-locked) |
| P-2 | pytest-cov instrumentation (D-3) | `pyproject.toml` | coverage report on suite run; baseline recorded; CI/agent docs updated |
| P-3 | ~~`--market` parametrization sweep (D-2)~~ **REVERSED 2026-11-06 (admin):** markets assumed different — keep per-market code paths separate; D-2 hardcoded constants stay as-is, treated as per-market configuration | `src/wi016/__init__.py`, `src/wi018/*`, `scripts/wi011_*` | dropped — no unification; document per-market paths instead |
| P-4 | G-gate recalibration build-out (D-019 R1–R4, R6, R7) **+ admin 2026-11-06: low-base-rate eligibility** — datasets/conditions with few successes, high failure assumed; G1 must emit trigger counts + base-rate CIs, conditions below min-event threshold or with any zero-positive fold get `INELIGIBLE_LOW_N` (data question) and never enter G2's testing budget; "untested-lack-of-data" ≠ "tested-and-refuted" in backlog routing. Long XGBoost runs stay — probe gates *entry* to them, does not replace them | `docs/workflow/designs/D-019-g-gate-recalibration.md` | effect-size floor + tiered G2 verdicts + low-N eligibility rule implemented in probe tooling; permutation-null calibration run first; fail-closed rule in WORKFLOW.md |
| P-5 | Paper-track validation of cost assumptions (D-6) | cost overlays WI-011/016/018 | realized round-trip fills recorded ≥1 month; bps assumptions re-derived |
| P-6 | Post-MVP research (WI-05 backlog: EP-06 index scraper, EP-07 Telegram digest, EP-08 regime-conditional tuning) | `docs/workflow/BOARD.md` BACKLOG | decomposed into WI plans; D-019 bars apply; probe-first |
| P-7 | Grid rebuild with `hurst_9` fix (w≥12) + verifier dedupe (D-8, D-9) | `src/wi016/` grid, verifier audit path | no all-NaN columns in smoke; verifier idempotent on re-run |

## 3. Rollback & incident protocol

1. Stable baseline = `main` at commit `561f299` (2026-11-01, post-WI-018-gate). Tag on demand: `git tag mvp-baseline 561f299 && git push origin mvp-baseline`.
2. Failed Phase 2 deploy: `git revert <bad-commits>` (no history rewrite — `main` is PR-protected); re-run `uv run pytest`; confirm ≥662 passed; restore any frozen report artifacts with `git checkout -- <path>` after confirming diff is metadata-only.
3. Frozen gate artifacts (suffixed `_CAD`/`_USD` reports, hash baselines) always win over regeneration — never commit regenerated variants of a gate-frozen report.
4. Data incidents (bad sync): quarantine via dead-letter CSV, verifier re-run, `data/adjudicated_tickers.csv` skip-list governs reinstatement. No auto-reinstatement.
5. Escalation: admin gate on every sprint gate; nothing self-approves; Discord webhook pings via `scripts/notify_gate.sh` for long-run completion.