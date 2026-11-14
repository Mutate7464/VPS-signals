# DECISIONS_AND_NEGATIVE_KNOWLEDGE.md — ADR + failed-attempt register

> Read BEFORE proposing architectural or model changes. Every entry below was verified by experiment or suite run, not opinion. Positive ADRs live in `docs/workflow/designs/D-##`; this file indexes them and carries the negative register.

## Standing decisions (ADR index)

| ADR | Decision | Doc |
|---|---|---|
| D-003 | Hybrid technical-factor route (contrastive ranking), IBKR data only | `docs/workflow/designs/D-003-technical-trading-approach.md` |
| D-010 | Continuous-first probabilities + quarantine consolidation | `docs/workflow/designs/D-010-*.md` |
| D-013 | Two-market parametrization (`--market`, suffixed reports) | `docs/workflow/designs/D-013-pipeline-hygiene-market-routing.md` |
| D-016 | Triple-barrier fib-ladder labeling + meta-labeling | `docs/workflow/designs/D-016-triple-barrier-fib-labeling.md` |
| D-018 | Condition-first first-touch directional study (Q4=BH-FDR 5%) | `docs/workflow/designs/D-018-condition-first-first-touch.md` |
| D-019 | G-gate recalibration: effect-size floor, tiered G2 verdicts, fail-closed plan rule | `docs/workflow/designs/D-019-g-gate-recalibration.md` (ACCEPTED) |

## Negative knowledge (DO NOT repeat — use the stated alternative)

1. **Binary targets on this universe are blind to the real signal.**
   Context: WI-002 Gate 4 (all 4 USD binary targets ≈ random) → WI-009c step 1 (0/5 targets clear bar).
   Root cause: signal lives in continuous fwd-ATR-return space; binary labels discard it.
   Directive: DO NOT re-train classifiers on binary up/down/stay labels here. Use continuous targets or E5 factor ranks; any new model work starts from a new target/data spec, probe-first.

2. **89-feature pool adds nothing over the E5 factors at current label definitions.**
   Context: triple-confirmed WI-002 / WI-009b / WI-009c; WI-017 brute-force confirmed on USD.
   Directive: DO NOT scale feature spend before a new label spec proves headroom. E5 factor screener (WI-014) is the MVP signal.

3. **Ranking models can learn a sign-inverted regime tilt and still "pass" naive bars.**
   Context: WI-009b contrastive ranker IC −0.1478 while best factor vol_20 +0.1274.
   Root cause: model learned full-history vol tilt; recent window inverted the regime.
   Directive: every skill bar must require **same sign as best factor AND |IC| ≥ margin** (adopted 2026-10-25). Never ship a ranker on an anti-correlated eval; negation chosen on eval window = curve-fit.

4. **Lookforward label windows: `shift(-1)` + `rolling(w)` corrupts every label.**
   Context: grid-sweep label code (WI-016/017 era).
   Root cause: rolling looks backward; only post-shift re-anchors forward.
   Directive: for forward window `[t+1..t+w]` use `series.rolling(w, min_periods=w).max().shift(-w)`. Regression-locked in tests; verify panels by independent recompute at ~30 sampled points (float32 → compare with tolerance).

5. **Significance bars have zero gate power on large panels.**
   Context: WI-018 G2 — 3,658 hypotheses, BH-FDR 5% → 2,506 survivors (density 0.685) = a wall.
   Root cause: CI half-width shrinks ~1/√N; at ~5,000 dates any nonzero difference clears.
   Directive: DO NOT gate on p-values/FDR alone. Binding filter = effect-size floor (≥2× round-trip bps) + fold-wise sign stability; calibrate thresholds with a permutation null first (D-019). A survivor wall = fail-closed: never cost it out or ship it.

6. **Tradeable condition rules do not survive costs at this universe size.**
   Context: WI-011 (CAD) + WI-012 (USD) — 0 survivors.
   Directive: conditions are descriptive context (attribution), never entry rules. Default NO_TRADE.

7. **XGBoost E5 split leaks future rows into train folds.**
   Context: WI-009, found by reviewer #2.
   Directive: use purged walk-forward splits; regression test `tests/test_e5_split_no_leak.py` is the durable lock. Adjudicate reviewer disagreements by experiment, never by authority.

8. **`tc_rating` as backtest primary violates point-in-time causality.**
   Context: WI-016 addendum bake-off — static watchlist snapshot, no history.
   Directive: EXCLUDE from backtest primaries. Clean primary: `yangzhang_21` (CAD) / `mom_12_1` (USD). Any live use needs point-in-time history first.

9. **Windowed estimators carry silent minimum-window constraints.**
   Context: shipped `hurst_9` all-NaN (needs w≥12); fixed ±10% barrier at w=233 ≈ always touched (target degenerates to base rate).
   Directive: smoke-test every family×window on 1–2 symbols for all-NaN columns BEFORE any sweep; report base rates before modeling; flag <1% event shares DOA.

10. **Fixed-column reads of heterogeneous per-symbol parquet KeyError mid-run.**
    Context: grid sweeps — short-history symbols carry fewer windows.
    Directive: read schema first (`pq.read_schema`), intersect wanted columns, pad missing as NaN; normalize dates to `datetime64[ns]` on both merge sides.

11. **Overwriting frozen gate reports in place.**
    Context: report scripts hardcode paths (`reports/wi011_*`).
    Directive: any rerun must copy fresh output to a validation prefix and `git checkout --` the frozen path. The frozen gate record wins over regeneration.

12. **Verbose polling / full-transcript ingestion burns ~30–50k tokens per cycle.**
    Context: PM cycles with opencode JSON logs.
    Directive: poll lean (`grep -c step_start`, `STATUS:` line, artifact `ls`); never `tail` JSON transcripts into context; prefer docs/INDEX routing over full source reads.

## Architecture topology (current)

- **Data:** `data/raw_ohlcv/market=<MKT>/symbol=<T>.parquet` ( synced from M1 Mac via IBKR kit) → feature panel (`src/feature_engine.py`) → E5 stat metadata (`src/stat_metadata.py`, `src/factors/e5_baseline.py`) → screener shortlist (`scripts/wi014_screener.py`) → PDF tearsheet (`src/pdf_compiler_factor.py`).
- **Research WI packages:** `src/wi011..wi018/` — self-contained, market-parametrized where patched (WI-013); `src/perfanalytics/` is the standing feature/target/alignment library.
- **Models:** `models/` (gitignored, regenerable) — y_15d_high/low, y_20d_up/down per market + contrastive rankers (research-only).
- **State:** `state/PIPELINE_STATE.json` (only `gate_1` is written by `verify_synced_data.py`; gates 2–5 legacy).
- **Constraints:** 2 vCPU / 8 GB host — `n_jobs=2`, float32 features, symbol-sequential iteration, `pyarrow.dataset`; no all-ticker uncompressed frames.