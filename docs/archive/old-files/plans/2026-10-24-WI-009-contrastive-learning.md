# PLAN — WI-009 / Contrastive Learning for Technical Trading (D-003 Option 2)

Board row: WI-009 · Goal: G-001 · Dataset: **CAD** (admin switch 2026-10-24)
Brief: `docs/tech_approach/2026-W44/briefs/contrastive-learning-brief.md`

## GOAL
Deliver a contrastive (within-date pairwise) ranking module over IBKR price/volume
data on CAD that orders any two assets by relative forward outperformance and yields
top-10 recommendations with confidence scores, whose skill is measured as score-based
within-date rank-IC and beaten against the five E5 factors as a mandatory baseline.

## CONSTRAINTS
- **Dataset = CAD** (350 tickers, `data/raw_ohlcv/market=CAD`). Step 0 rebuilds the
  stale 2026-10-21 CAD features/targets/catalog **before any training**; do not train
  on the existing CAD parquets (they are 1400 rows × 66 features, pre-fib-expansion).
- **Reuse the 89 features** in `src/feature_engine.py` (via feature-name/signature
  grep). Do NOT rebuild RSI/MACD/BB/ATR — the draft plan's Step 2 is dropped.
- **Framework = PyTorch CPU** `torch 2.14.1+cpu`, installed from the `pytorch-cpu` uv
  index (`explicit = true` + `[tool.uv.sources]`) so uv does not pull the CUDA wheel.
  Rationale: PM-verified on this VPS (50 epochs × 4096 pairs × 89-dim in 0.40 s, peak
  RSS 0.33 GB, 2 threads, ~810 MB disk); xgboost `rank:pairwise` on Δ(a,b) is the
  no-new-framework alternative but cannot express embeddings, which are the point of
  contrastive learning. **torch: `torch.set_num_threads(2)`, float32 tensors, embed
  dim ≤ 64, per-date streamed pair sampling — never materialize O(N²) pairs.**
- **Train AND evaluate in within-date relative (pairwise/rank) space with score-based
  rank-IC** — never class-label IC (the E5 ridge/logit "sign flip" was a
  target-definition artifact; cleanest statements are single-factor within-date ICs).
- **E5 five factors computed inside the new module on CAD** as the mandatory baseline.
  `scripts/diag_signal.py` is USD-locked (`only --market USD is implemented`) — do NOT
  route the CAD baseline through `--exp e5 --market CAD`.
- Host guardrails: 2 vCPU / 8 GB / no swap; `n_jobs≤2`; float32 immediately after
  calculation; no all-ticker uncompressed DataFrame (streamed symbol iteration);
  `matplotlib.pyplot.close('all')` + `gc.collect()` if charts are emitted.
- **No live trading, no order execution, no secrets.** Daily shortlist only.
- ELE (TSE) is missing entirely — proceed without it.

## STEPS

### [x] Step 0 — Rebuild CAD features + targets + catalog
(a) Change: run the streaming rebuild path (the same one that produced the USD
89-feature/1,240,275-row artifacts), then regenerate the CAD catalog from those fresh
features.
(b) Acceptance: `data/features/features_CAD.parquet` has **89 feature columns**,
float32, ~1.2M labelled rows, ≥300 symbols; `targets_CAD.parquet` has the 4 int8
targets with the same row count; `data/metadata_catalog_CAD.json` is newer than the
features file.
(c) Verification:
```
uv run python -m src.feature_engine --market CAD --min-date 2016-01-01
uv run python -m src.stat_metadata --market CAD --vif-threshold 10 --min-mi-percentile 15
uv run python -c "import pandas as pd; f=pd.read_parquet('data/features/features_CAD.parquet'); t=pd.read_parquet('data/features/targets_CAD.parquet'); fc=[c for c in f.columns if c not in ('date','symbol','market')]; print('features',f.shape,len(fc),'targets',t.shape); assert len(fc)==89, len(fc)"
```

### [x] Step 1 — E5 factor baseline on CAD (within-date rank-IC)
(a) Change: new `src/factors/e5_baseline.py` computing the five E5 factors from raw
OHLCV exactly as the E5 report defines them (`mom_12_1` = close.shift(21)/close.shift(252)-1,
`rev_1m` = close/close.shift(21)-1, `vol_20` = 20d std of returns, `amihud_20` = mean of
|ret|/dollar_vol, `log_dollar_vol_20`), target `fwd_atr_ret_h` = (close.shift(-h)-close)/wilder_atr,
and per-date Spearman rank-IC + t-stat across dates, for CAD. Runnable as a module.
(b) Acceptance: runs on CAD, writes `reports/wi009_e5_baseline_CAD.md`, reports ≥5
factors with mean IC/t and >100 evaluated dates; no NaN t-stats.
(c) Verification:
```
uv run python -m src.factors.e5_baseline --market CAD
uv run python -c "import re,pathlib; p=pathlib.Path('reports/wi009_e5_baseline_CAD.md'); s=p.read_text(); print(s[:400]); assert 'mom_12_1' in s and 'vol_20' in s"
```

### [x] Step 2 — Within-date streamed pair sampler (no O(N²) materialisation)
(a) Change: `src/models/pair_sampler.py` — for each date, sample k pairs of
(winner, loser) from that date's cross-section using forward-relative return ranks;
yield batches; never build a full pair matrix.
(b) Acceptance: on a synthetic panel of 200 names × 50 dates the sampler yields ≥1 pair
per date, total pairs ≪ N², and peak extra memory is bounded (no 200×200 matrix
instantiated anywhere in the code path).
(c) Verification:
```
uv run pytest tests/test_pair_sampler.py -q
```

### [x] Step 3 — Contrastive model + within-date pairwise training
(a) Change: replace the placeholder `src/models/contrastive_ranking.py` with a real
torch CPU Siamese tower (embed ≤64), float32, `set_num_threads(2)`, pairwise
margin/BCE loss on sampler output; training script `scripts/train_contrastive.py`
consuming the CAD panel and evaluating **score-based within-date rank-IC** each epoch
against the Step-1 E5 baseline.
(b) Acceptance: trains on a CAD slice end-to-end; epoch loss decreases; emits a
rank-IC series with t-stat; run is CPU-only, 2 threads, float32.
(c) Verification:
```
uv run python scripts/train_contrastive.py --market CAD --epochs 2 --max-dates 40
uv run python -c "import json;d=json.load(open('reports/wi009_train_run.json'));print(d['epochs'][-1]);assert d['epochs'][-1]['rank_ic_t'] is not None"
```

### [x] Step 4 — Top-10 recommendation extraction
(a) Change: `scripts/rank_assets.py` scores the CAD cross-section on the latest
complete date, ranks it, emits top-10 with confidence (score z / pairwise win-rate).
(b) Acceptance: `reports/wi009_top10_CAD.csv` with 10 rows, columns
symbol,score,confidence,rank; no NaNs; symbols are live CAD universe members.
(c) Verification:
```
uv run python scripts/rank_assets.py --market CAD --top-n 10
uv run python -c "import pandas as pd;d=pd.read_csv('reports/wi009_top10_CAD.csv');print(d);assert len(d)==10 and d['score'].notna().all()"
```

### [x] Step 5 — Synthetic-data validation before real-data claims
(a) Change: `tests/test_contrastive_synthetic.py` — synthetic cross-sections with a
planted relative-performance ordering; the contrastive ranker must recover it
(within-date rank-IC clearly > 0 and ≥ the E5 baseline on the same synthetic panel).
(b) Acceptance: test passes; recovered IC on planted signal > 0.3 on the synthetic
panel (sanity floor for a learnable synthetic ordering).
(c) Verification:
```
uv run pytest tests/test_contrastive_synthetic.py -q
```

### [x] Step 6 — QA: reviewer subagent ×2 + fold in the run_e5 fix
(a) Change: (1) retro review of WI-002 diagnostic commits `d957d43` + `d5c5441`
(`scripts/diag_signal.py` run_e3/run_e5 — never reviewer-passed); (2) pre-commit review
of the WI-009 diff (guardrails, leakage, lookahead, no-live-trading). Fold the one-line
`run_e5` fix in under Deviations: evaluate the logit with `predict_proba`.
(b) Acceptance: both reviews returned; blocking findings triaged (fixed or recorded);
the `predict_proba` one-liner applied to `scripts/diag_signal.py` run_e5.
(c) Verification:
```
grep -n "predict_proba" scripts/diag_signal.py
uv run python -m src.feature_engine --market CAD --validate-leakage
```

## OUT OF SCOPE (non-goals)
- Live trading / order execution; real-time processing (daily batch only)
- Fundamental or alternative data; full trading strategy beyond ranking
- Hyper-parameter tuning of the legacy USD models
- Rebuilding RSI/MACD/BB/ATR feature code (reused as-is)

## EXECUTION LOG
00:00 | step 0 | CAD features+targets rebuilt via streaming path: 315 symbols, 701,599 labeled rows, 89 float32 features, 2016-01-04→2026-09-22; peak RSS 831MB | concern: row count is well below the USD 1,240,275 — CAD universe is 350 files minus 35 quarantined, and CAD tickers start later; expected, not a truncation bug (R-08 fix present in cb1303d, index verified aligned)
00:13 | step 0 | catalog regenerated from fresh features: 89 raw → 42 surviving (VIF 10 / MI percentile 15), 3 flagged non-stationary, whitelist 35/target | none
00:13 | step 0 | acceptance verified: 89 feature cols, float32, targets row-aligned (701,599) | none
00:14 | step 1 | CAD E5 baseline computed (715,193 rows, 313 symbols, 2,866 dates): mom_12_1 +0.0243 t+6.47; rev_1m −0.0094 t−3.13; vol_20 −0.0454 t−11.18; amihud_20 −0.0143 t−5.52; log_dollar_vol_20 +0.0029 t+1.35. 4 of 5 factors breach |t|>2 on CAD | concern: CAD floor is BREACHED, so the model must beat a live factor baseline — the brief's USD numbers (mom +5.54 / vol −4.72) are NOT the CAD numbers, as warned
00:14 | step 1 | multivariate purged-WF: ridge −0.0031 t−0.77; logit_median_split +0.0201 t+4.24 (scored with predict_proba — WI-002 one-line fix applied here) | none
00:16 | step 2 | pair sampler + rank-IC tests: 7/7 pass (first run 6/7 — my test asserted a finite t for a zero-dispersion IC, which is undefined; test corrected, not the code) | concern: test expectation wrong, code behaviour was right; logged for transparency
00:16 | step 5 | synthetic validation: 3/3 pass, planted relative ordering recovered (val rank-IC > 0.3) | none
00:19 | step 3 | first CAD training run (40 train dates, 10 val dates, 2 epochs): loss 0.759→0.713, val rank-IC +0.0430 t+1.88 then +0.0416 t+2.63 | concern: two bugs fixed en route — (a) merge collision on `amihud_20` (exists in BOTH the 89-feature matrix and the E5 panel → silently suffixed _x/_y; fixed by namespacing E5 cols to e5_*), (b) numpy.datetime64 has no .date()
00:19 | step 3 | SKILL CONCERN (gate-relevant): on the SAME 10 val dates the model's |IC| 0.043 is well short of the best single E5 factor rev_1m |IC| 0.157 (t−4.26); log_dollar_vol_20 −0.063 t−3.50 also stronger. The model has real but modest skill (t+2.63) and does NOT beat the factor baseline on this slice | concern: recent CAD regime is strongly reversal-driven (rev_1m flipped from −0.0094 full-sample to −0.157 on the 10 recent val dates); the run is also small (40 train dates). Escalating to a gate brief rather than claiming success
00:22 | step 4 | top-10 extracted: reports/wi009_top10_CAD.csv, universe 314 (1 row dropped for undefined features), 10 rows, no NaNs, ranks 1..10, all symbols live and un-quarantined; explicitly REIT-heavy | concern: the shortlist date is capped at 2026-09-22 because the feature matrix only keeps rows with all 4 forward targets defined (~20 trading days of lag). Production use needs a target-free inference path; noted as a limitation, not fixed here
00:25 | all | full suite re-run: 52 passed (496s), no regressions from the WI-009 additions | none
00:28 | step 6 | QA reviewer #1 (retro d957d43 + d5c5441): 1 blocker — run_e5 scores the logit with predict() (class labels) not predict_proba(); E5 verdict unaffected (driven by single-factor ICs) but the published line is wrong; E3 ablation generator clean | concern: reviewer #1 explicitly CLEARED the np.isin(date_codes, tr_idx) split mask as "internally consistent" — that clearance was WRONG (see next line)
00:31 | step 6 | QA reviewer #2 (WI-009 diff): verdict FIX BEFORE COMMIT — 1 blocker (multivariate_ic masks splits via pd.factorize codes; the splitter returns date POSITIONS, so this leaks held-out rows into training), 2 warnings (PairBatch.n_dates undercount after a spliced flush; rank_assets.py read the whole all-ticker parquet) | concern: the two reviewers disagreed on the same construct, so it had to be adjudicated by experiment
00:34 | step 6 | adjudication experiment: pd.factorize codes != true date positions for 100% of real CAD rows (max gap 1839); a staggered fixture shows 40 held-out rows pulled into the train fold. Reviewer #2 correct, reviewer #1 wrong | concern: the leak was REAL and had contaminated the CAD multivariate numbers I had already published
00:36 | step 6 | fixes: (a) e5_baseline.py — new tested helper date_positions(); splitter fed sorted unique dates, mask on positions; (b) diag_signal.py run_e5 — sort dates, mask on positions, and score the logit with predict_proba; (c) pair_sampler.PairBatch.n_dates now counts the dates actually in the emitted slice; (d) rank_assets.py — Arrow scan (read only the date column, then filter one date) instead of the full-parquet read; (e) train_contrastive.py — local `val_dates` no longer shadows args.val_dates | none
00:36 | step 6 | new regression test tests/test_e5_split_no_leak.py locks the mask fix and documents the leak (asserts the code-based mask differs and drags at/after the val fold into train) | none
00:37 | step 6 | E5 CAD multivariate recomputed AFTER the leak fix: ridge −0.0031 t−0.77 → −0.0046 t−1.26; logit +0.0201 t+4.24 → +0.0226 t+4.44. Single-factor ICs unchanged (they never used the splitter) | concern: previously reported multivariate numbers were contaminated; now corrected in the report
00:37 | step 6 | USD E5 report regenerated (truth-in-reporting): logit −0.0080 (t −2.78) → −0.0055 (t −1.67), exactly reproducing the brief's probe; ridge lines unchanged | none
00:38 | step 6 | WHY USD ridge was unaffected while CAD changed: USD's first iterated symbol (`A`) starts 2006-10-27 against a 2006-10-26 global start, so its dates own the early codes and codes≈positions there. CAD's first symbol (AAPL) starts 2021 against a 2007 global start — so the leak bit the dataset this work item actually uses | none
00:38 | step 6 | re-ran training and rank_assets after the fixes: training reproduces identical metrics (deterministic seed); shortlist output identical | none
00:40 | step 6 | full suite after all fixes: 56 passed (460s) | none
00:42 | gate | gate brief written: docs/human/briefings/2026-10-25-gate-WI-009-contrastive-ranking.md | concern: the model does NOT beat the E5 baseline on the held-out slice (val rank-IC +0.043 t+2.63 vs rev_1m |IC| 0.157 t−4.26). The brief set no numeric skill bar, so this is a human gate decision, not an agent verdict.

STATUS: DONE | evidence: `uv run pytest -q` → 56 passed; `uv run python -m src.factors.e5_baseline --market CAD --multivariate` → report written (4/5 factors breach |t|>2); `uv run python scripts/train_contrastive.py --market CAD --epochs 2 --max-train-dates 40 --val-dates 10` → val rank-IC +0.043 t+2.63, loss 0.759→0.713; `uv run python scripts/rank_assets.py --market CAD --top-n 10` → 10-row shortlist, no NaNs; both reviewer passes returned, all blocker/major findings fixed and regression-tested; skill result escalated to the human gate brief above

## Deviations
- **Brief's literal command omits `--min-date`.** `uv run python -m src.feature_engine
  --market CAD` takes the legacy `load_market_frame` path (concatenates all 350 tickers
  into one uncompressed frame → AGENTS.md memory violation, and timed out at 120 s in
  the previous session). Step 0 uses `--min-date 2016-01-01` instead, which is the
  streaming path that produced the USD 89-feature rebuild (see `logs/e2_run.out`).
- **ELE (TSE) missing entirely** — CAD has 350 files, no ELE; baseline/model proceed
  on the universe present.
- **`run_e5` logit scored by `predict_proba`** (one-line fix): class-label IC
  overstated the reported sign flip (−0.0055, t −1.67 with proper scores vs −0.0080,
  t −2.78 reported).
- **Prior session correction:** the previous turn marked this plan DONE with fabricated
  results and clobbered `docs/workflow/BOARD.md`. Reverted: board restored from git,
  plan reset to unchecked, false status removed. Step 0 had not in fact run.