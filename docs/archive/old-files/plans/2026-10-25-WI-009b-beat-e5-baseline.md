# PLAN — WI-009b / make the contrastive ranker beat the E5 factor baseline

Board row: WI-009b · Goal: **G-001** · Dataset: **CAD**
Seed: gate brief `docs/human/briefings/2026-10-25-gate-WI-009-contrastive-ranking.md`
(APPROVE branch, admin 2026-10-25: "full-history training run + explicit skill bar, then re-gate")
Parent: `docs/plans/2026-10-24-WI-009-contrastive-learning.md` (Steps 0–6 DONE, commit `19795ac`)

## GOAL

On a widened purged validation window (≥60 held-out CAD dates, identical dates for model and
factors), the WI-009 contrastive ranker's within-date val rank-IC must satisfy **both** clauses
of an explicit skill bar: **(a)** it beats the best single E5 factor's |IC| on the same rows/dates,
and **(b)** |t| > 2 with the same sign in ≥2 disjoint sub-windows of the val set. Verdict is
reported per clause, factor-by-factor, from the existing apples-to-apples harness.

## CONSTRAINTS

- Dataset **CAD** (`data/features/features_CAD.parquet`, 701,599 rows × 89 float32 features,
  315 symbols). Do not rebuild features; Step 0 of WI-009 is done and leak-locked.
- **Skill bar is explicit and fixed in this plan** (it is the deliverable's pass condition):
  - clause (a): `abs(model_val_rank_ic) > max_f abs(factor_f_val_rank_ic)` on the same val rows.
  - clause (b): model `|t| > 2` **and** in each of ≥2 disjoint contiguous sub-windows of the
    val window the model's mean IC has `|t| > 2` with the **same sign** as the full-window
    model IC. (Sub-window factor comparison is reported as information, not a pass clause.)
  - Metric is `within_date_rank_ic` from `src/models/pair_sampler.py` — never class-label IC,
    never a pooled magnitude IC.
- Purged chronological split: val = the last N unique merged-panel dates; train = everything
  before, minus a 20-trading-day purge gap so 15td forward labels cannot straddle the boundary.
  Same dates for model and for all five factors.
- **torch CPU** (`configure_torch()`, 2 threads), float32, embed ≤64, streamed per-date pairs,
  never an O(N²) pair matrix, `n_jobs ≤ 2`, <2 GB training panel in memory.
- Long job ⇒ **detached runner only**: `subprocess.Popen(..., start_new_session=True)` writing
  `logs/wi009b_train.out` with `START` / `END` / `EXIT:<code>` markers per stage. Never trust a
  killed foreground run; poll the log.
- Slim the training read to the columns the model needs, keeping **all** derived feature
  columns (fib/range/`_cs_pct` clusters) in the keep set, with a regression test in the
  `tests/test_feature_masks.py` style proving every mask resolves non-empty (the E3 bug class).
- No live trading, no order execution, no secrets. Commit step-scoped explicit paths only —
  never `git add -A`.
- **OUT OF SCOPE (do not fix here):** the target-free inference path / ~20-trading-day
  shortlist lag; REIT concentration of the shortlist; architecture changes of any kind
  (a different model is a new work item needing admin approval).
- **Selection-effect note (honest reporting):** early stopping picks the best epoch on the val
  window. That is not a leak (no future data enters training) but it is optimistic selection;
  the reports must therefore also carry the **final-epoch** metrics next to the selected-best
  metrics so the reader can see the selection effect.

## STOP conditions (report, do not tune past them)

1. Full-history training still loses clause (a) on the widened window → **STOP**, write the
   re-gate brief (the REJECT branch of the original gate), and do not chase it with
   architecture changes.
2. Any train/val leak suspicion → stop, lock it with a regression test first
   (`tests/test_e5_split_no_leak.py` pattern).
3. Two-strike build failure → human-gated escalation; write the pre-escalation handover,
   never switch models mid-run.

## STEPS

### [x] Step 0 — Plan file + board row
(a) Change: this file; move the WI-009b board row READY → **EXECUTING** naming this plan.
(b) Acceptance: board EXECUTING cell contains the exact plan path.
(c) Verification: `grep -n "WI-009b" docs/workflow/BOARD.md | grep -c "2026-10-25-WI-009b-beat-e5-baseline.md"`

### [x] Step 1 — Skill-bar module (widened purged split + sub-windows + verdict + report)
(a) Change: new `src/models/skill_bar.py`:
   - `purged_date_split(dates, val_dates, embargo_td=20)` — returns `(train_dates, val_dates, purge_gap)`
     with the val window being the last `val_dates` unique dates; asserts the gap ≥ embargo.
   - `sub_window_split(val_dates, n_windows=2)` — n disjoint contiguous equal blocks.
   - `factor_ics(panel, target, factors)` — wraps the shared `within_date_rank_ic`.
   - `skill_bar_verdict(model_ic, model_t, factor_ics, sub_stats)` — structured dict with
     `clause_a`, `clause_b`, `passed`, and the reasons.
   - `write_comparison_report(...)` — the `reports/wi009b_e5_vs_model_CAD.md` writer
     (model vs 5 factors table, sub-window table, verdict per clause, config/time/epochs).
(b) Acceptance: module imports with no torch dependency; split returns disjoint ordered
   train/val with a purge gap of exactly `embargo_td` dates; a deliberately crafted IC set
   that fails clause (a) and one that fails clause (b) both return `passed=False`.
(c) Verification: `uv run pytest tests/test_wi009b_skill_bar.py -q`

### [x] Step 2 — Slim training read + mask regression test
(a) Change: in `scripts/train_contrastive.py`, `slim_feature_columns(schema_names)` (or module
   helper) builds the Arrow `columns=` keep list = ids + every non-identifier feature column,
   with a hard guard that the resulting feature count is unchanged and that every present
   derived cluster (fib/range/`_cs_pct`) survived. New
   `tests/test_wi009b_slim_masks.py` mirrors `tests/test_feature_masks.py`: against the real
   CAD schema, the keep set retains **all 89** features, resolves non-empty, and contains
   every derived cluster present in the source.
(b) Acceptance: test passes; training run log reports the same 89 feature columns as WI-009.
(c) Verification:
```
uv run pytest tests/test_wi009b_slim_masks.py -q
uv run python -c "import pyarrow.parquet as pq; from scripts.train_contrastive import slim_feature_columns as s; n=[f.name for f in pq.ParquetFile('data/features/features_CAD.parquet').schema_arrow]; k=s(n); print(len(k)); assert len([c for c in k if c not in ('date','symbol','market')])==89"
```

### [x] Step 3 — Early stopping + widened-window plumbing in the trainer
(a) Change: `scripts/train_contrastive.py` gains `--report-prefix` (default `wi009`),
   `--early-stop-patience` (0 = off), per-epoch wall-clock `secs`, final-epoch metrics, the
   sub-window stats and the skill-bar verdict in the JSON, and calls the report writer.
   Outputs for this work item become `reports/wi009b_train_CAD.json` and
   `reports/wi009b_e5_vs_model_CAD.md`. `--val-dates 60` must be honoured (≥60 held-out dates).
(b) Acceptance: a short probe run writes `reports/wi009b_train_CAD.json` containing
   `config`, `epochs[].secs`, `val_rank_ic`, `val_rank_ic_t`, `sub_windows`, `skill_bar`,
   `e5_baseline_val` (5 factors, same `n_dates` as the model), and `report` path; and the md
   verdict table. Existing WI-009 outputs must not be overwritten by the probe.
(c) Verification:
```
uv run python scripts/train_contrastive.py --market CAD --epochs 1 --max-train-dates 200 \
  --val-dates 60 --report-prefix wi009b_probe --tag wi009b_probe
uv run python -c "import json;d=json.load(open('reports/wi009b_probe_train_CAD.json'));print(d['val_dates'][0],len(d['val_dates']),d['skill_bar']);assert len(d['val_dates'])>=60 and 'skill_bar' in d"
```

### [x] Step 4 — Timing calibration before committing the host
(a) Change: none (measurement only) — from the Step-3 probe, extrapolate seconds/epoch to the
   full-history date count and pick the epoch budget so the detached job finishes inside the
   host budget (2 vCPU / 8 GB / no swap) with memory headroom; record the arithmetic in the
   EXECUTION LOG.
(b) Acceptance: a seconds/epoch and peak-RSS estimate for the full run, and a chosen
   `--epochs` + `--early-stop-patience` pair, both logged.
(c) Verification: `grep -n "step 4" docs/plans/2026-10-25-WI-009b-beat-e5-baseline.md`

### [x] Step 5 — Detached full-history training run
(a) Change: new `scripts/wi009b_launch.py` — starts the training command with
   `subprocess.Popen(..., start_new_session=True, cwd=repo)`, stdout/stderr →
   `logs/wi009b_train.out`, writes `START`/`END`/`EXIT:<code>` markers around the run, prints
   the pid, exits immediately. Launch: all available CAD train dates (no `--max-train-dates`),
   `--val-dates 60`, chosen epochs/patience, `--report-prefix wi009b --tag CAD`.
(b) Acceptance: process survives the session (detached), log shows panel build, per-epoch
   lines with loss + val rank-IC/t + secs, early-stop reason if any, and `EXIT:0`.
(c) Verification:
```
uv run python scripts/wi009b_launch.py --epochs <E> --early-stop-patience <P> --val-dates 60
sleep 60; tail -20 logs/wi009b_train.out     # poll until the EXIT marker appears
grep -c "^EXIT:0" logs/wi009b_train.out
```

### [x] Step 6 — Emit and verify the deliverables
(a) Change: the run itself emits `reports/wi009b_train_CAD.json` and
   `reports/wi009b_e5_vs_model_CAD.md`; nothing hand-written.
(b) Acceptance: JSON has train config, epochs (+secs), val rank-IC and t, the five-factor
   comparison on the identical val dates, sub-window stats and the skill-bar verdict; MD has
   the model-vs-5-factors table, the sub-window stability table, and a verdict line per clause.
   The JSON `val_dates` list length ≥60 and equals the `n_dates` of every factor.
(c) Verification:
```
uv run python -c "import json;d=json.load(open('reports/wi009b_train_CAD.json'));n=len(d['val_dates']);print(n,d['skill_bar']);assert n>=60;assert all(v['n_dates']==n for v in d['e5_baseline_val'].values());assert all(len(w['dates'])==n//2 for w in d['sub_windows']))"
head -40 reports/wi009b_e5_vs_model_CAD.md
```

### [x] Step 7 — Regression suite + commit + board
(a) Change: run the full suite (62-test baseline must stay green plus the new tests); commit
   step-scoped explicit paths (plan, `src/models/skill_bar.py`, `scripts/train_contrastive.py`,
   `scripts/wi009b_launch.py`, `tests/test_wi009b_*.py`, the two reports, BOARD row).
(b) Acceptance: suite green; commit(s) contain no stray files; board row updated with the
   verdict and the commit hash.
(c) Verification:
```
uv run pytest tests/test_wi009b_skill_bar.py tests/test_wi009b_slim_masks.py -q
uv run pytest -q            # full suite, expect >=62 + new
git status --short
```

### [x] Step 8 — Re-gate brief (branch decided by the verdict)
(a) Change: if the skill bar **passes** → write the gate brief for the human with the numbers
   and the residual risks (shortlist lag, REIT concentration, selection effect) and stop for
   the gate. If clause (a) **fails** → write the re-gate brief recommending the REJECT branch
   (fold the winning factor in directly) per the STOP condition. Either way: human gate, no
   self-approval.
(b) Acceptance: brief exists at `docs/human/briefings/2026-10-25-gate-WI-009b-skill-bar.md`
   with the final table, the sub-window stability, epochs/time, and one explicit decision.
(c) Verification: `test -f docs/human/briefings/2026-10-25-gate-WI-009b-skill-bar.md && head -30 docs/human/briefings/2026-10-25-gate-WI-009b-skill-bar.md`

## EXECUTION LOG

All times are session wall clock (host clock, UTC).

03:33 | step 0 | plan written (`docs/plans/2026-10-25-WI-009b-beat-e5-baseline.md`, GOAL/CONSTRAINTS/8 steps with verify commands); board WI-009b row READY → **EXECUTING**, naming this plan | none
03:36 | step 1 | `src/models/skill_bar.py` + `tests/test_wi009b_skill_bar.py`: widened purged split (val = last N unique dates, purge gap exactly 20td, purge rows in NEITHER fold), disjoint contiguous sub-windows, clause-(a)/(b) verdict, markdown comparison writer. First run 8/21 failed — both were **my own test expectations**, not code: (a) `abs()` applied to a dict key instead of its value, (b) a perfectly-planted factor has zero IC dispersion so its t is undefined (nan) — the same lesson as WI-009 step 2. Tests corrected, code unchanged | concern: test-authoring errors, logged for transparency
03:38 | step 2 | `src/models/training_data.py` + `tests/test_wi009b_slim_masks.py`: slim Arrow-scan keep list (ids + every non-identifier column) with a census guard; real CAD schema → 92 columns → **89 features** kept, census classic 63 / range_fib 26 / cs_pct 0; fixture test proves `e5_*`/`fwd_atr_ret_*` columns are not read and features return float32 | none
03:40 | step 3 | trainer extended: `--report-prefix`, `--early-stop-patience`, `--grad-clip`, `--sub-windows`, per-epoch `secs`, final-epoch metrics, sub-window stats, skill-bar verdict, JSON + MD emit. FIRST probe run: mean epoch loss **36,831** (WI-009 pilot: 0.759) | concern: loss explosion — diagnosed rather than assumed
03:42 | step 3 | diagnosis: the panel has **0 non-finite values** after dropna (353,074 NaN cells removed) but raw indicator scales span ~11 orders of magnitude (`amihud_5` max 1.75e11) → astronomic initial margins → mean loss ~9e4 at lr 1e-3, 1e-4 AND 3e-5, with and without grad clipping. The WI-009 pilot never saw this because it ran 5 batches/epoch and barely moved off init (loss 0.759 ≈ ln 2 = 0.693) | concern: **this reframes WI-009's result** — the pilot's "+0.043 rank-IC" was near-random-init output, not learned skill
03:42 | step 3 | FIX (input preprocessing, NOT architecture): winsorise q1/q99 + standardise as **model buffers**, fitted on **train-fold rows only**, applied inside `embed`; initialised to identity so untrained models and the WI-009 path are numerically unchanged; buffers travel in the state dict, so `load_model` / `score_numpy` / `scripts/rank_assets.py` need no change and inference stays consistent with training. New `tests/test_wi009b_input_transform.py` (6 tests, incl. save/load round trip and a train-stats-only proof). After the fix: loss 0.6950 → 0.6874 (chance 0.6931) | concern: a stability fix inside "enough epochs to converge"; logged as a Deviation because the plan did not name it
03:43 | step 4 | timing calibration from the probe: 200 train dates (102k pairs) = 1 s/epoch, peak RSS 1.06 GB; full history 2,585 dates (1.32M pairs) = 8-9 s/epoch ⇒ an ~3-minute 20-epoch budget, safely inside the host budget (2 vCPU / 8 GB / no swap). Chose `--epochs 20 --early-stop-patience 4` | none
03:43 | step 5 | `scripts/wi009b_launch.py`: detached `Popen(start_new_session=True)` wrapping the trainer in `sh -c` so the **child** writes its own `END`/`EXIT:<code>` markers; per-stage `STEP …: START/END` markers come from the trainer; `--status` polls pid + markers | none
03:44 | step 5 | detached full-history run #1: **EXIT:0**, 47 s training, 5 epochs (early stop, patience 4), 1,317,953 pairs/epoch, peak RSS 1.04 GB | none
03:47 | step 5 | run #2 after adding the caveat machinery: **bit-identical** metrics (deterministic seed 7) → EXIT:0 | none
03:59 | step 6 | run #3 after the review fix to the census guard: EXIT:0, identical metrics again | none
04:00 | step 6 | artifacts verified: `reports/wi009b_train_CAD.json` (60 val dates; **every** factor `n_dates == 60`; 2 sub-windows of 30 dates; `purge_gap_td` 20; `epochs_run` 5; `train_seconds` 49.4; input transform + feature census recorded) and `reports/wi009b_e5_vs_model_CAD.md` (model-vs-5-factors table, per-clause verdict, caveat block, sub-window table) | none
04:00 | step 6 | **SKILL RESULT** (widened window, 60 dates 2026-06-26 → 2026-09-22, 2,585 train dates 2016-02-09 → 2026-05-28): model val rank-IC **−0.1313 (t −6.55)** vs best factor `vol_20` **|IC| 0.1274 (t +3.48)**. Clause (a) PASS by 0.0040 (3.1% relative); clause (b) PASS (sub-windows −0.1951 t −6.30 and −0.0675 t −3.39, same sign, both |t|>2). Mechanically the bar **passes** | concern: the PASS is **magnitude-only, sign-inverted and 3.1%-thin** — the model is anti-correlated with forward returns on this window, so it is NOT an economic win. Reported as PASS *with caveats* and escalated to the human gate, not declared success
04:00 | step 6 | why the sign inverts (explanation, not a fix): the model trains on 2016-2026, where `vol_20` IC is −0.045 (high vol underperforms), but on the widened val window `vol_20` flips to **+0.127** (high vol outperforms) — the exact regime sensitivity the WI-009 gate brief flagged. The model learned the full-history tilt and the recent window inverted it | concern: single seed, single window; a sign flip fitted on this same window is not claimable
04:00 | step 6 | the baseline moves with the window, as the brief warned: on these 60 dates `rev_1m` is −0.0555 (t −1.82) vs −0.157 on the 10 dates WI-009 used, and the best factor switches from `rev_1m` to `vol_20` | none
04:05 | step 7 | reviewer pass on the diff (read-only subagent): 2 major, 2 warn, 2 nit. **FIXED**: the `keep_columns` census guard was tautological (the census reused `feature_columns`, so a selective keep rule hid the family it dropped — the E3 bug class could still have slipped through). `feature_census` now counts families **directly from the column list** and `keep_columns` compares source vs keep censuses; the new E3-simulation test proves the guard can fire. **REJECTED WITH REASON**: switching early stopping to `|IC|` — that selects the most extreme IC regardless of direction (here the *most negative* epoch, |IC| 0.1478, a 16% "margin") and would reward sign inversion; raw-IC selection is the honest objective for a ranker meant to put winners high, and the final-epoch IC is already reported beside the selected epoch. **NOTED, NO CHANGE**: global `dropna` on the label is required because *both* folds need the label (train pairs and the val metric); `strict=True` on the state restore is correct for a fixed architecture | none
04:05 | step 7 | full suite after all fixes: **99 passed** (62-test baseline + 37 new), 453 s | none
04:12 | step 7 | committed step-scoped paths only (plan, `src/models/{skill_bar,training_data,contrastive_ranking}.py`, `scripts/{train_contrastive,wi009b_launch}.py`, `tests/test_wi009b_{skill_bar,slim_masks,input_transform}.py`, `reports/wi009b_{train_CAD.json,e5_vs_model_CAD.md}`, BOARD row); probe artifacts deleted, no stray files | concern: untracked WI-010 quarantine scripts and `debug_test*.py` are pre-existing and deliberately left alone
04:15 | step 8 | re-gate brief written: `docs/human/briefings/2026-10-25-gate-WI-009b-skill-bar.md` — verdict table, the caveat in plain language, and the decision requested. **Human gate: no self-approval** | concern: the bar as specified (|IC|) passes while the economically meaningful statement (same-sign skill) fails, so this is an admin judgment call, not an agent verdict

STATUS: DONE | evidence: `uv run python scripts/wi009b_launch.py --epochs 20 --early-stop-patience 4 --val-dates 60 --standardize --lr 1e-3 --grad-clip 1.0` → `logs/wi009b_train.out` shows 5 epochs (early stop), `STEP …: START/END` per stage, `SKILL BAR: PASS` and `EXIT:0`; `reports/wi009b_train_CAD.json` verified by the Step-6 command (60 val dates, all 5 factors `n_dates==60`, 2×30-date sub-windows, purge gap 20td); `reports/wi009b_e5_vs_model_CAD.md` written; `uv run pytest -q` → 99 passed (62 baseline + 37 new); skill result (PASS with the sign-inverted / thin-margin caveats) escalated to the human gate brief above

## Deviations

- **Input transform added to the model (winsorise q1/q99 + standardise, train-fold
  statistics only).** Not in the plan. Without it the full-history run diverges
  (mean epoch loss ~9e4 at every lr tested) because 89 raw indicators span ~11
  orders of magnitude — i.e. the plan's "enough epochs to converge" was not
  reachable. It is input preprocessing, not an architecture change: same tower,
  same loss, same streamed pairs. The statistics are fitted on **train-fold rows
  only** (leak-free) and stored as buffers in the state dict, so the existing
  inference path is unchanged and consistent. Reviewer-confirmed leak-free.
- **Early stopping kept on raw (signed) val rank-IC**, not `|IC|`, against the
  reviewer's major finding. Rationale in the log line at 04:05. The selection
  effect is disclosed in the report (selected epoch vs final epoch).
- **Probe artifact naming.** The plan's Step-3 verify command was corrected before
  the run so the probe file is `reports/wi009b_probe_train_CAD.json` (`--report-prefix`
  names the reports, `--tag` names the model file). Probe artifacts were deleted
  after use; no stray files.
- **`keep_columns` census guard strengthened after review.** The first version's
  count check was tautological; it now compares a source census computed
  independently of the keep rule against the keep-list census, with an
  E3-simulation test proving it fires. (Reviewer finding, fixed.)
- **The forced `--standardize` run is the deliverable; WI-009 comparability.** The
  raw-feature path (`--standardize` off) is preserved and reproducible, but it
  cannot converge on the full history — see the first Deviation. This is the
  single biggest interpretive caveat on the comparison with WI-009's pilot number.
- **`models/` and `logs/` are gitignored**, so the trained blob
  (`contrastive_ranker_wi009b.pt`) and the run log are regenerable artifacts, not
  committed files; the run log lines are quoted in this plan.
- **Shortlist / target-free inference path untouched** (explicitly out of scope).
  Consequence: `scripts/rank_assets.py` still loads the WI-009 pilot blob
  (`models/contrastive_ranker_CAD.pt`); the WI-009b model is saved separately as
  `contrastive_ranker_wi009b.pt`. Repointing the shortlist path is **not** part of
  this work item.
- **Single seed (7), single window.** No seed-stability or multi-window
  robustness run was performed — that would be chasing the result, which the STOP
  conditions forbid. Flagged as an open question for the gate.