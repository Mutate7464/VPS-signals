# Gate Brief — WI-009b: does the contrastive ranker now beat the E5 factor baseline?

**Verdict in one line:** on the widened 60-date validation window the model
**passes the skill bar exactly as it was written** (|IC| 0.1313 vs the best
factor's 0.1274) — but it passes **with the opposite sign** and by 3.1%, so the
honest reading is that it does **not** yet beat the factor in any sense you could
trade; the numbers below are the decision.

**Decision requested:** APPROVE (accept the bar as met and move the work item to
a shortlist/deployment question) | **HOLD** (bar was too weak — re-specify it as
same-sign skill, keep the branch open) | REJECT (drop the contrastive branch and
fold the winning factor in directly, as the original gate's REJECT branch)

Traceable to **G-001**. Plan: `docs/plans/2026-10-25-WI-009b-beat-e5-baseline.md`.

## What was supposed to happen

The WI-009 gate approved one follow-up: train the contrastive ranker on
**full history** (not 40 dates), widen validation to **≥60 held-out purged
dates**, and decide against an **explicit** skill bar — because WI-009's result
(+0.043 vs the factor's 0.157 on 10 dates) had no bar to approve against.

The bar, fixed in the plan before the run: **(a)** beat the best single E5
factor's |IC| on identical rows and dates, and **(b)** |t| > 2 with the same sign
in ≥2 disjoint sub-windows of the validation set.

## The numbers

| Metric | Threshold (why) | Actual | Pass? |
| :--- | :--- | :--- | :--- |
| Full-history training | all available train dates, no 40-date cap | **2,585 train dates** (2016-02-09 → 2026-05-28), 1.32M pairs/epoch | ✅ |
| Widened validation window | ≥60 held-out dates, purged split, same dates for model and factors | **60 dates** (2026-06-26 → 2026-09-22), 20-trading-day purge gap, every factor at `n_dates = 60` | ✅ |
| Converged run | early stopping on val rank-IC, not loss | 5 epochs, early-stopped (patience 4), 49 s, peak RSS 1.04 GB, `EXIT:0` | ✅ |
| Clause (a) — beat best factor | model \|IC\| > best factor \|IC\| | model \|IC\| **0.1313** (IC **−0.1313**), `vol_20` **0.1274** → margin **+0.0040 (3.1%)** | ⚠️ **passes on magnitude only** |
| Clause (b) — sign stability | \|t\| > 2, ≥2 disjoint sub-windows, same sign | t **−6.55**; sub-windows **−0.1951 (t −6.30)** and **−0.0675 (t −3.39)** | ✅ |
| **Skill bar overall** | (a) AND (b) | **PASS — with caveats** | ⚠️ |

Factor-by-factor on the **same 60 dates** (score-based within-date rank-IC,
identical rows for model and factors):

| Ranker | mean IC | \|IC\| | t |
| :--- | ---: | ---: | ---: |
| **contrastive ranker** | **−0.1313** | 0.1313 | −6.55 |
| `e5_vol_20` (best factor) | **+0.1274** | 0.1274 | +3.48 |
| `e5_mom_12_1` | +0.0677 | 0.0677 | +3.13 |
| `e5_rev_1m` | −0.0555 | 0.0555 | −1.82 |
| `e5_amihud_20` | +0.0546 | 0.0546 | +4.08 |
| `e5_log_dollar_vol_20` | −0.0242 | 0.0242 | −3.04 |

**Two things you must read before the verdict:**
1. **SIGN INVERTED.** The model is *anti-correlated* with forward returns on this
   window. It clears clause (a) only because clause (a) compares magnitudes. You
   could flip the model's score and get +0.1313 — but that flip is chosen on this
   same window, so it is not a claim anyone should bank.
2. **THIN MARGIN.** 3.1% relative on one 60-date window, one seed. Not robust.

## Why the sign flips (explained, not fixed)

`vol_20` scores **−0.045** on the full CAD sample but **+0.127** on these 60
dates — high-volatility names underperform historically and outperformed recently.
The model learned the full-history tilt; the recent window inverts it. This is
exactly the regime sensitivity the WI-009 gate brief flagged as a risk, now
hitting the model rather than only the baseline. It is also why the baseline
number is part of the deliverable: `rev_1m` reads −0.157 on WI-009's 10 dates but
−0.0555 here, and the best factor changes identity (`rev_1m` → `vol_20`).

## A finding that changes how WI-009 should be read

The full-history run initially **diverged** (mean epoch loss ~9×10⁴). Root cause:
the 89 raw CAD indicators span ~11 orders of magnitude (`amihud_5` reaches
1.75×10¹¹), so the untrained tower produced astronomic margins — at *every*
learning rate tested. Fix: winsorise + standardise as **train-fold-only** model
buffers (input preprocessing, not an architecture change; the inference path is
unchanged).

Consequence: the WI-009 pilot ran 5 batches per epoch and never moved off
initialisation (loss 0.759 ≈ ln 2 = 0.693), so **WI-009's "+0.043 rank-IC" was
near-random-init output, not learned skill.** The pilot's headline number should
not be quoted as evidence of anything.

## Check it yourself (5 minutes)

- `cat reports/wi009b_e5_vs_model_CAD.md` — the comparison table, per-clause
  verdict, caveat block, sub-window table.
- `cat reports/wi009b_train_CAD.json` — config, `epochs` (+secs), `val_rank_ic`
  and `val_rank_ic_t`, `sub_windows`, `skill_bar`, `e5_baseline_val`, and the
  `val_dates` list (60; every factor shares it).
- `grep -E "SKILL BAR|EXIT:" logs/wi009b_train.out` — the detached run's markers.
- `uv run pytest tests/test_wi009b_skill_bar.py tests/test_wi009b_slim_masks.py tests/test_wi009b_input_transform.py -q` — expect 37 passed.
- `uv run pytest -q` — expect 99 passed (62 baseline + 37 new).

## Risks & what could be wrong

- **The bar may simply be the wrong bar.** It was written as a magnitude |IC|
  comparison (following the WI-009 gate's language), which a sign-inverted model
  can satisfy. If the intent was "the model is a usable signal", the bar must
  require **same sign** as the factor and a margin threshold. That is a
  re-specification decision, which is why this is a gate and not an agent verdict.
- **One seed, one window.** No seed-stability or multi-window run — deliberately
  not chased (STOP condition). A 3.1% margin on a single window is well inside
  window-to-window variation.
- **Early-stopping selection** is on val rank-IC. The report discloses both the
  selected epoch (IC −0.1313) and the final epoch (IC −0.1478) so you can see the
  selection effect; it is optimistic, though no future data enters training.
- **The model has not been given a fair architecture test.** It trains, converges,
  and produces a stable *inverse* signal — that is a genuine negative result for
  this tower/loss/pair recipe on this window, not a proven dead end.
- **Unchanged and out of scope:** the ~20-trading-day shortlist lag (feature rows
  require all four forward targets). `scripts/rank_assets.py` still loads the
  WI-009 pilot blob (`contrastive_ranker_CAD.pt`); the WI-009b model is saved as
  `contrastive_ranker_wi009b.pt` and nothing was repointed.

## One thing worth learning

Two ways to state "this asset will do well" — *how much* (pooled magnitude) and
*relative to its peers* (within-date rank) — can disagree in sign without either
being wrong. This work item adds a third: a model can be **significantly wrong
in the same direction every day** (t = −6.55, stable across two disjoint
sub-windows) which a magnitude-only skill bar reads as a win. When a bar is
written, the *direction* of the signal has to be part of it, or "beat the
baseline" becomes satisfiable by being confidently inverted.

## How to respond

- **"gate approved"** → accept the bar as met as written; next work item is the
  shortlist/target-free-inference question, not more model tuning.
- **"hold — <question>"** → work stops; the question lands in the plan's
  Deviations. Suggested re-specification: clause (a) becomes "same-sign as the
  best factor **and** |IC| greater", which this run **fails**.
- **"reject"** → drop the contrastive branch and ship the E5 factor baseline
  (`vol_20` on the recent window, `mom_12_1` on full history) as the D-003
  Option 2 technical signal.

---

## Addendum (PM cycle 9, 2026-10-25 ~05:00 UTC) — numbers superseded by the F1 fix

Reviewer pass `ses_e8ecc8dc` (verdict FIX BEFORE COMMIT) found the early-stop
selected on **raw IC, not |IC|** — the skill bar's own clause (a) metric
(reviewer F1; PM confirmed in code, cycle 9). Fix landed in
`scripts/train_contrastive.py` (abs-compare + init 0.0); training re-run
deterministically (`EXIT:0`):

- Selected epoch moves 1 → **5**: model val IC **−0.1478 (t −6.03)** on the same
  60 dates (was −0.1313 / t −6.55).
- Clause (a) margin over `vol_20` |IC| 0.1274: **+0.0204 = 16.0% relative**
  (was 3.1%) — the "thin margin" caveat retires; everything else in this brief
  stands unchanged.
- **The sign question is unaffected and still the gate:** the model remains
  anti-correlated (every epoch negative, sub-windows −0.217 / −0.078 same sign).
  A same-sign reading of clause (a) still **fails**. The re-specification
  decision above is unchanged by the fix.