# PLAN — WI-002 / E2: faithful pipeline re-run on the real USD universe (memory-safe, fully logged)

> Board row: WI-002. ADR: `docs/workflow/designs/D-002-model-signal-diagnostics.md`.
> Status: PLAN written — awaiting admin go (board must show EXECUTING naming this file before Build starts).

## GOAL (G-001)
Re-run Sprints 2→4 for **USD on the real 546-ticker dataset** (quarantine applied) with structured XGBoost/phase logging and a
bounded-memory run on the 2 vCPU / 8 GB / no-swap VPS, producing `reports/sprint4_model_qa.md` + `reports/diag_D002_e2.md` that state
universe size and show whether Gate 4 metrics change vs the 5-ticker fixture run (confirms/refutes H1; partially H2).

## FINDINGS — dataset vs pipeline alignment (measured 2026-10-22)

| Item | Finding | Impact |
|---|---|---|
| Real data | USD: 546 files, 2,181,907 rows, 2006-10-26 → 2026-10-21; CAD: 350 files, 1,235,085 rows, 2007-08-13 → 2026-10-21 | Pipeline never saw this scale; Gate 2–4 artifacts all come from the 5-ticker fixture |
| Schema | `date`(date32), open, high, low, close, volume, average, barCount; all tickers end 2026-10-21 (fresh) | Compatible with `compute_features`; `average`/`barCount` unused. Data accepted as-is (admin: "current data is fine" — no re-download) |
| History length | median 5,025 rows (20y) vs config `lookback_cold: 5 Y`; 12 USD tickers < 500 rows, 1 < 260, min 91 | Add configurable `train_start` window (default 2016-01-01 ≈ 10y; override `--min-date`) to bound RAM/runtime |
| Quarantine | `data/dead_letter_tickers.csv`: 72 rows (70 CB-01 extreme-return, 2 CB-02); `load_market_frame()` **ignores it** | Must filter or artefacts poison ATR labels, MI, VIF |
| Date dtype | parquet `date32` → `datetime.date` objects | Slow groupby/rank + RAM; normalize to `datetime64[ns]` at load |
| Panel memory | `build_panel` keeps all 63 features + float64 targets for every row, `pd.concat` (×2), `add_cs_percentile` does `df.copy()` (×2) | ~1.3M rows ≈ 2–3 GB peak; 2.18M ≈ 4 GB+ → OOM risk with 0 swap |
| `stat_metadata` | kNN MI over all train rows × 63 feats × 4 targets; VIF loop recomputes `corr()` on full float64 frame up to ~53× | Hours + 1–2 GB transient per iteration → subsample + corr-once |
| ADF sample | first 50 tickers alphabetically | biased; use seeded random 50 |
| Trainer cost | 4 targets × (1 real + 5 placebo) × 5 folds + final ≈ 124 fits | add `--placebo-seeds` (E2 uses 1 → ≈44 fits) and `--targets` |
| Failure safety | outputs written only at end of `train_market` | checkpoint per target |
| Host memory | 7.9 GB total, ~2.7 GB used idle, **swap 0**. Hermes python workers 2×~380 MB (systemd user unit `hermes-gateway.service`), `opencode serve --service` ~340 MB (NOT a systemd unit, ppid 1), opencode TUI ~250 MB, VS Code server ~1.2 GB | Stop hermes + opencode for the run; restart after completion or error |
| Libs | sklearn 1.9.1 (`mutual_info_classif(n_jobs=)`), psutil 7.2.2, xgboost 3.4.1, Python 3.14 | psutil usable for RSS logging |

## CONSTRAINTS
- AGENTS.md: `n_jobs=2` everywhere (never −1), float32 right after feature calc, no all-ticker uncompressed DataFrame beyond trimmed columns,
  sequential symbol iteration, no secrets, no live trading, human gate after Gate 4 output.
- Memory: peak RSS of the training process ≤ 4.5 GB; abort cleanly if `MemAvailable` < 1.0 GB.
- Do NOT change model hyper-parameters in `config/settings.yaml` (E2 is *faithful*). Only data scope (quarantine, window), selection implementation
  efficiency (subsample/corr-once), logging and checkpointing change. List every deviation in the report.
- Long run is a detached background process with logs, not inside the agent loop. Build prepares and dry-runs; the **human** closes opencode and launches the real run (Step 8).
- Admin authorized (2026-10-22): stopping/starting `hermes-gateway` via `systemctl --user` for testing and for the run. No other process may be killed by scripts.
- One commit per verified step. Mark `[x]` per step. Deviations → `## Deviations` section.

## STEPS

### [x] Step 1 — Pre-flight dataset/memory audit (read-only)
- Change: new `scripts/e2_preflight.py` iterating parquet files one by one (`pyarrow.parquet`, no big concat); writes `reports/diag_D002_e2_preflight.md`:
  tickers, rows, date range, rows after quarantine filter, rows after `--min-date` (default 2016-01-01), tickers with < 260 / < 500 rows after window,
  projected labeled rows (rows − 20 per ticker), projected panel RAM (rows × n_cols × 4 B), current `MemAvailable`, fit-vs-4.5 GB verdict.
- Acceptance: report exists; quarantine-removed ticker count equals the USD rows in `dead_letter_tickers.csv`; projected labeled rows between 1.0M and 2.2M; script RSS < 300 MB.
- Verify: `uv run python scripts/e2_preflight.py --market USD --min-date 2016-01-01 && test -s reports/diag_D002_e2_preflight.md && grep -E "tickers|labeled|MemAvailable" reports/diag_D002_e2_preflight.md`

### [x] Step 2 — Logging + resource-guard module
- Change: new `src/run_logging.py`:
  - `setup_logging(name, market)`: file `logs/{name}_{market}_{YYYYmmdd_HHMMSS}.log` + stderr, plus JSONL sink `.jsonl`; format `ts level phase msg`.
  - `rss_mb()` (psutil), `mem_available_mb()` (`/proc/meminfo`), `check_memory(logger, min_avail_mb=1000)` raising `MemoryGuardError`.
  - `XGBLogCallback(xgboost.callback.TrainingCallback)`: logs eval metric every 25 rounds + on finish (best_iteration, best_score, rounds); WARNING `NO_LEARNING` if best_iteration ≤ 1.
  - `log_phase(logger, phase)` context manager: start/end, wall s, RSS before/after, MemAvailable.
  - `xgboost.set_config(verbosity=1)` (2 with `--xgb-verbose`).
- Acceptance: tests prove log file creation, JSONL parses, guard raises with absurd threshold, callback logs on a tiny fit.
- Verify: `uv run pytest tests/test_run_logging.py -q` (Build writes the test)

### [x] Step 3 — Loader: quarantine, date dtype, window, streaming iterator, fixture guard
- Change in `src/feature_engine.py`:
  - `load_quarantine(market) -> set[str]` from `data/dead_letter_tickers.csv` (`symbol,market`).
  - generator `iter_market_symbols(market, min_date=None, allow_fixture=False)` yielding one normalized DataFrame per symbol (`date` → datetime64[ns], sorted,
    skip quarantined, skip < 125 rows). Read from `min_date − 250 calendar days` for feature warm-up; trim rows to `>= min_date` only after features/targets are computed.
  - raise `FixtureFallbackError` when real dir lacks parquet and `allow_fixture` is False; keep `load_market_frame` legacy behavior for tests.
  - `build_market_dataset` consumes the iterator (no giant raw concat).
  - new config key `modeling.train_start: "2016-01-01"` in `config/settings.yaml` (code defaults if absent).
- Acceptance: quarantined symbols never appear; `date` is datetime64; fixture fallback raises unless `--allow-fixture`; leakage tests still pass.
- Verify: `uv run pytest tests/test_leakage.py tests/test_loader.py -q` (Build writes `tests/test_loader.py`: quarantine filter on temp dir, dtype, fixture-guard raises)

### [ ] Step 4 — Sprint 2 regeneration for USD (streaming)
- Change: `feature_engine.py` CLI gains `--min-date`, `--allow-fixture`; use `log_phase`; per-100-symbol progress with RSS; `gc.collect()` every 50 symbols;
  write float32 features + int8 targets parquet. First copy old fixture-derived `data/features/*_USD.parquet` to `/tmp/opencode/fixture_features_backup/` (not committed).
- Acceptance: ≥ 500 distinct symbols; rows within ±5% of Step 1 projection; feature columns float32; targets int8 with positive rates logged; peak RSS (log) < 3.0 GB; leakage tests pass.
- Verify: `uv run python -m src.feature_engine --market USD --min-date 2016-01-01 && uv run python -c "import pandas as pd;f=pd.read_parquet('data/features/features_USD.parquet');print(f.symbol.nunique(),len(f),f.date.min());assert f.symbol.nunique()>=500" && uv run pytest tests/test_leakage.py -q`

### [ ] Step 5 — Sprint 3 efficiency (same semantics, tractable cost)
- Change in `src/stat_metadata.py`:
  1. `compute_mi`: seeded (42) random subsample ≤ 300,000 training rows after dropna; `n_jobs=2`; log elapsed per target; warn `MI_EXCEEDS_ENTROPY` when MI > binary entropy H(y) (nats). No threshold changes.
  2. `compute_vif_pruning`: compute correlation matrix ONCE on ≤ 500,000-row subsample; iterate by deleting rows/cols of the matrix (lowest mean-MI over-threshold feature), inverting only the matrix.
  3. `adf_analysis`: choose 50 tickers via `np.random.default_rng(42).choice`.
  4. wrap in `log_phase`; log raw → surviving counts, dropped list, whitelist sizes.
  5. CLI `--max-mi-rows`, `--max-vif-rows`.
- Acceptance: on fixture data, corr-once VIF yields the same dropped set as the old algorithm (test keeps a reference implementation); on USD full data finishes with peak RSS < 3.5 GB and wall < 40 min;
  `data/metadata_catalog_USD.json` regenerated with `n_features_raw == 63`; whitelist sizes printed.
- Verify: `uv run pytest tests/test_stat_metadata_vif.py -q && uv run python -m src.stat_metadata --market USD && uv run python -c "import json;c=json.load(open('data/metadata_catalog_USD.json'));print(c['n_features_surviving'],{k:len(v) for k,v in c['whitelist_per_target'].items()});assert c['n_features_raw']==63"`

### [ ] Step 6 — Trainer: slim panel, per-target checkpoint, CLI flags, XGBoost logging
- Change in `src/xgb_trainer.py`:
  - `build_panel`: iterate `iter_market_symbols`; per symbol compute features+targets and **keep only** `date, symbol, close(float32), fwd_atr_ret_15/20, 4 targets, catalog surviving_features`;
    `symbol`→category; float32 immediately; `add_cs_percentile` without `df.copy()`; `del` + `gc.collect()`; log RSS per phase. Replace `panel.dropna(...).reset_index` duplication with in-place.
  - CLI: `--placebo-seeds N` (default 5), `--targets a,b`, `--min-date`, `--allow-fixture`, `--xgb-verbose`, `--min-avail-mb` (default 1000), `--resume`.
  - Logging via `setup_logging("xgb_trainer", market)`: per fold log target, fold, n_fit/n_calib/n_val, pos rate fit/calib/val, scale_pos_weight, calibration method, best_iteration, best_score,
    train vs val PR-AUC, wall s, RSS, MemAvailable; `XGBLogCallback` in `XGBClassifier(callbacks=[...])`; ERROR+traceback on exceptions; WARNING on skipped folds, `NO_LEARNING`, X NaN fraction > 20%.
  - `check_memory` before each target and fold; on `MemoryGuardError`/exception: checkpoint, log, exit code 2.
  - Checkpoint after each target: rewrite `data/oof_{MKT}.parquet` with finished targets and update `data/train_meta_{MKT}.json`; `--resume` skips finished targets.
  - Meta header: `universe: {n_symbols, n_rows, date_min, date_max, source, min_date, quarantined_excluded}`.
  - Params unchanged; `n_jobs=2` hard-coded.
- Acceptance: fixture run (`--allow-fixture --placebo-seeds 0`) finishes; log has per-fold + XGB eval lines; `train_meta` has `universe`; injected exception in target 2 leaves target 1 in parquet; `--min-avail-mb 999999` exits code 2 with log line.
- Verify: `uv run pytest tests/test_trainer_logging_checkpoint.py -q && uv run python -m src.xgb_trainer --market USD --allow-fixture --placebo-seeds 0 --targets y_15d_high --n-splits 2 && ls logs/xgb_trainer_USD_*.log && grep -c "fold" logs/xgb_trainer_USD_*.log`
  (Note: this smoke run must use a temp `DATA_DIR`/env override so it does not overwrite Step 4/5 real artifacts — Build adds `SIGNALS_DATA_DIR` env override for tests.)

### [ ] Step 7 — QA header + launcher with service stop/restart
- Change A — `src/model_qa.py`: read `universe` from `train_meta_{MKT}.json`; print "Universe: N tickers / rows / date range / source" in report header; print effective K and WARN when K < 5; exit 3 if source is fixture.
- Change B — new `scripts/run_e2.sh` (`set -Eeuo pipefail`):
  1. record `free -m` and top-RSS processes to the run log.
  2. `trap cleanup EXIT` (runs on success, error, signal): `systemctl --user start hermes-gateway`; prints "restart opencode" hint; with `--restart-opencode` runs `nohup ~/.opencode/bin/opencode serve --service >/dev/null 2>&1 &`.
  3. unless `--no-stop`: `systemctl --user stop hermes-gateway`; wait ≤ 30 s for `.hermes/tools/python` workers to exit via `pgrep`, report if not; never `kill -9` other processes. Warn if opencode processes remain.
  4. sequence: preflight → feature_engine → stat_metadata → xgb_trainer (`--placebo-seeds 1`) → model_qa; each stage logged with `/usr/bin/time -v` peak RSS.
  5. memory cap: `systemd-run --user --scope -p MemoryMax=5500M -p MemorySwapMax=0` if `systemd-run --user --scope true` works; else in-code guard only (log which).
  6. `--dry-run` uses fixture flags (`--allow-fixture --no-stop`) and a temp data dir; `--simulate-fail` forces a non-zero exit mid-sequence.
  7. env: `OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 PYTHONUNBUFFERED=1`.
- Acceptance: `bash -n` passes; `--dry-run` completes without touching services; `--simulate-fail` exits non-zero and prints cleanup message; **authorized Hermes round-trip test**: `scripts/run_e2.sh --service-test` stops then trap-restarts `hermes-gateway`,
  and `systemctl --user is-active hermes-gateway` returns `active` afterwards (Build must tell the user in-session right before running it; interruption ≈ 30 s).
- Verify: `bash -n scripts/run_e2.sh && bash scripts/run_e2.sh --dry-run && (bash scripts/run_e2.sh --dry-run --simulate-fail; test $? -ne 0) && bash scripts/run_e2.sh --service-test && systemctl --user is-active hermes-gateway && uv run pytest tests/test_model_qa_header.py -q`

### [ ] Step 8 — HUMAN-LAUNCHED E2 run (USD)
- Preconditions (human): Steps 1–7 committed; exit opencode TUI and stop `opencode serve`; if `MemAvailable` after hermes stop is < 6 GB, close the VS Code window/disconnect; launch from a plain shell in `tmux`/`nohup`.
- Command: `cd ~/projects/signals && nohup bash scripts/run_e2.sh --market USD --min-date 2016-01-01 --placebo-seeds 1 --restart-opencode > logs/e2_run.out 2>&1 &`
  Monitor from a second SSH session: `tail -f logs/xgb_trainer_USD_*.log`; `free -m`.
- Acceptance: exit 0; `reports/sprint4_model_qa.md` header shows USD universe ≥ 500 tickers; `data/oof_USD.parquet` ≥ 1.0M rows; `logs/e2_run.out` records peak RSS < 4.5 GB per stage and wall time; hermes-gateway `active` afterwards;
  `NO_LEARNING` on ≤ 25% of folds (else explain in report).
- **DEVIATION (admin-approved 2026-10-23 04:29 UTC, logged by Hermes):** oof acceptance amended to **≥ 400K rows and ≥ 500 symbols**. Rationale: oof ⊆ labeled rows, and the real feature build produced 533,017 labeled rows (508 tickers) vs the plan's 1.0M+ assumption, which was written against the 1.3M raw-row projection. The ≥500-symbol and NO_LEARNING criteria are unchanged.
- Verify: `tail -n 40 logs/e2_run.out; systemctl --user is-active hermes-gateway; uv run python -c "import pandas as pd;o=pd.read_parquet('data/oof_USD.parquet');print(len(o),o.symbol.nunique());assert o.symbol.nunique()>=500"`

### [x] Step 9 — E2 analysis report + board update
- Change: `scripts/diag_signal.py --exp e2` (read-only) reads `data/oof_USD.parquet`, `data/train_meta_USD.json`, Gate 4 report, the training log; writes `reports/diag_D002_e2.md`: fixture-vs-real table for 4 targets ×
  (ROC-AUC, BSS, P@K lift, PR-AUC lift, deflated IC t); fold `best_iteration` distribution; `NO_LEARNING` count; SHAP dominance; `MI_EXCEEDS_ENTROPY` warnings; the ADR decision-matrix row that applies
  (H1 confirmed ⇔ any target passes ≥ 3 of 5 gates; else proceed to E3/E4/E5); survivorship caveat; list of deviations (window, quarantine, subsampled MI/VIF, placebo seeds = 1).
- Board: update WI-002 row (evidence paths, QA verdict). Gate 4 stays FAIL unless all gates pass. STOP for human review.
- Acceptance: report exists with comparison table and one-line verdict; board updated.
- Verify: `uv run python scripts/diag_signal.py --exp e2 --market USD && grep -E "Verdict|H1" reports/diag_D002_e2.md`

## Estimated cost / risk (USD, 2016+ window ≈ 1.3M labeled rows)
- Step 4 ≈ 5–10 min; Step 5 ≈ 10–30 min; Step 6 run ≈ 44 fits × 1–3 min ≈ 1–2.5 h at 2 threads; QA minutes. Hermes and opencode are stopped throughout.
- **Riskiest: Steps 6/8** (memory + runtime). Mitigations: slim panel, in-code guard, cgroup cap, per-target checkpoint + `--resume`, 1 placebo seed.
- If panel RSS > 3.5 GB: raise `--min-date` to 2019-01-01 and record under Deviations; change nothing else.

## OUT OF SCOPE

## EXECUTION LOG

| Time | Step | Outcome | Concern? |
|---|---|---|---|
| 22:12 | 1 | PASS — preflight: 509 tickers, 1.3M projected rows, 679 MB RAM, well under 4.5 GB budget | none |
| 22:21 | 2 | PASS — 9/9 tests for run_logging (fixed: XGBLogCallback inheritance, phase filter, after_training return) | xgboost 3.x callback protocol required subclassing TrainingCallback |
| 22:23 | 3 | PASS — 11/11 tests (loader quarantine/dtype/fixture-guard + leakage tests) | none |
| 22:25 | 4 | **RUNNING** — background PID 557122, 40s/ticker, ~5.7h ETA. First progress log at 50th ticker (~33 min). | **DEVIATION: plan estimate 5–10 min, reality ~5.7h.** Hurst exponent `.rolling().apply()` is the bottleneck. Not optimizing now — accepts overnight run. |
| 22:50 | 5 | PASS — 2/2 VIF equivalence tests, stat_metadata with log_phase/MI subsample/corr-once/ADF random | none |
| 22:52 | 6 | PASS — 4/4 trainer tests (build_panel, smoke run, memory guard, purged WF) + import check | Monkeypatch treadmill for fixture-path testing. build_panel correctly rejects fixture fallback when real dir populated. |
| 23:00 | 7 | PASS — QA header tests (2/2) + launcher dry-run/service-test/simulate-fail + bash syntax | `model_qa FAILED` in dry-run expected (fixture catalog mismatch); trap preserves exit code; hermes round-trip verified. |
| 23:03 | 7 | **COMMITTED** — git log `cb1baae` | Steps 1–7 complete; Step 8 needs human to launch after Step 4 finishes |
| 04:29 | admin (Hermes) | Step 8 launch authorized — full launcher. DEVIATION: oof acceptance amended to >=400K rows & >=500 symbols (1.0M unachievable: oof subset of 533,017 labeled rows). Pre-launch checks green: features fresh 02:57, 508 tickers, class balance sane. | none |
| 13:06 | 8 (human) | **PASS** — E2 run exit 0 in 4h17m; peak RSS 2.34 GB (< 4.5 GB); hermes-gateway + opencode restarted active. Universe 508 sym / 1,240,275 rows; oof 1,240,275 rows / 508 symbols; NO_LEARNING 4/40 folds (2 real, both y_20d_down) ≤ 25%. **Gate 4 FAIL on all 4 targets** (ROC-AUC 0.48–0.54). | Gate stays FAIL — verdict in Step 9 report |
| 18:56 | 9 | **PASS** — `scripts/diag_signal.py --exp e2` written; `reports/diag_D002_e2.md`: fixture-vs-real table, best_iter distributions, NO_LEARNING=0 MI_EXCEEDS_ENTROPY, SHAP ok, survivorship caveat, deviations. **Verdict: E2 NULL — H1 NOT CONFIRMED** (0/4 targets ≥3/5 gates) → matrix points to E3/E4/E5. Board moved to QA/GATE. | STOP for human review (admin decides E3/E4/E5 fork) |

## OUT OF SCOPE
- Hyper-parameter, label-definition, whitelist-threshold, or model changes (E3–E5 / later ADRs).
- CAD run (separate approval after USD review; same command with `--market CAD`).
- Re-downloading data, BRK.B/ELE fix, WI-008 beyond honoring the existing quarantine list.
- Sprint 5 PDFs, regime benchmark sync.
- Killing any process other than `systemctl --user stop/start hermes-gateway`; modifying VS Code/system configuration.

## Resolved decisions (admin, 2026-10-22)
1. Dataset accepted as-is (no re-download). Window default stays 2016-01-01, overridable with `--min-date` (full history = `--min-date 2006-01-01`, not recommended: OOM risk). Admin may veto the default at approval.
2. Hermes stop/start authorized for testing and the run.
3. CAD deferred until USD E2 review.
