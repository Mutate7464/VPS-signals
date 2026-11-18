# Gate Brief — WI-009 contrastive pairwise ranking (WI-009, traceable to G-001)

**Verdict in one line:** the WI-009 deliverable is built, reviewed and passes every
stated acceptance criterion, **but on the held-out CAD slice it ranks worse than a
single E5 factor already in production** — so the open question is whether to keep
investing in the embedding approach or fold the winning factor in directly.

**Decision requested:** APPROVE to continue (WI-009b: make it beat the baseline) |
**HOLD** (if you want the shortlist-lag and threshold questions answered first) |
REJECT (drop the contrastive branch; ship the factor baseline instead)

## What was supposed to happen
Implement a contrastive / pairwise ranking model over IBKR price–volume data on the
**CAD** dataset (admin switch 2026-10-24): rank any two assets by relative forward
outperformance, extract a top-10 shortlist with confidence, and evaluate it in
within-date rank space against the five E5 factors as a mandatory baseline.

## What actually happened
Step 0 rebuilt the stale CAD dataset first (the old files were 1,400 rows × 66
features, pre-dating both the fib/range expansion and the index-truncation fix).
The rebuilt panel is **701,599 rows × 89 float32 features, 315 symbols**. The E5
baseline was then computed on CAD inside the new module (`scripts/diag_signal.py`
is USD-locked). The model trains and produces a clean top-10. The number that
matters: on the **same 10 held-out dates** the model scores rank-IC **+0.043
(t +2.63)** while the single factor `rev_1m` scores **|IC| 0.157 (t −4.26)** —
i.e. real but modest skill, and *below* the baseline it was measured against.

## The numbers that decide this
| Metric | Threshold (why) | Actual | Pass? |
| :--- | :--- | :--- | :--- |
| CAD dataset rebuilt before training | 89 float32 features, not the stale 66-col 2026-10-21 file | 701,599 rows × **89** float32, 315 symbols, catalog 89→42 surviving | ✅ |
| Framework guardrails | torch CPU, 2 threads, float32, embed ≤64, no O(N²) pairs | 2 threads, float32, embed 32, streamed pairs (~20.4k/epoch, not 199k² ) | ✅ |
| Ranking consistency (crit. 1) | any two assets orderable, consistent across universe | scalar score tower ⇒ transitive order; unit-tested | ✅ |
| Top-10 + confidence (crit. 2) | extractable with confidence scores | `reports/wi009_top10_CAD.csv`, 10 rows, ranks 1–10, no NaNs | ✅ |
| Synthetic validation first (crit. 3) | planted ordering recovered before real data | recovered, val rank-IC > 0.3 | ✅ |
| E5 baseline mandatory (crit. 5) | five factors on CAD, score-based within-date rank-IC | computed; **4 of 5 breach \|t\|>2** (vol_20 −0.045 t −11.18) | ✅ |
| **Model vs baseline skill** | **no numeric bar was set in the brief** | model +0.043 t +2.63 vs `rev_1m` 0.157 t −4.26 | ⚠️ **not approved — no threshold to approve against** |

Note on the last row: the brief required that the model *be evaluated against* the
E5 factors, and it was — apples-to-apples, same rows and same metric. It did **not**
state a numeric pass bar for "beats the baseline". I am therefore not calling this
a pass or a fail; it is the decision in front of you.

## Check it yourself (5 minutes)
- `cat reports/wi009_train_CAD.json` — look at `val_rank_ic`, `e5_baseline_val`, and
  `epochs`; confirm the model and the factors share the same 10 `val_dates`.
- `cat reports/wi009_e5_baseline_CAD.md` — the CAD factor table (USD numbers in the
  brief, e.g. mom +5.54, are **not** the CAD numbers).
- `cat reports/wi009_top10_CAD.csv` — the shortlist (notably REIT-heavy).
- `uv run pytest tests/test_pair_sampler.py tests/test_contrastive_synthetic.py tests/test_e5_split_no_leak.py -q` — expect 14 passed.
- `uv run python scripts/rank_assets.py --market CAD --top-n 10` — regenerate it yourself.

## Risks & what could be wrong
- **The skill result is from a deliberately small run** (40 training dates, 10
  validation dates, 2 epochs) to fit the host budget. Whether the model closes the
  gap with full-history training is **not yet established** — this is the single
  biggest unknown, and it is cheap to test before any verdict on the approach.
- **The shortlist lags ~20 trading days.** The feature matrix only retains rows with
  all four forward targets defined, so the "latest" rankable date is 2026-09-22, not
  the newest data. Production use needs a target-free inference path. Not fixed here.
- **Two real defects were found and fixed during QA**, both worth knowing about
  because one is pre-existing in WI-002 code:
  1. the purged-split mask mapped index sets through `pd.factorize` codes instead of
     date positions — a genuine **train/val leak** (they disagree for 100% of CAD
     rows). Fixed in both the new E5 module and `scripts/diag_signal.py run_e5`.
  2. `run_e5` scored its logistic model with `predict` (class labels) rather than
     `predict_proba`, inflating the reported t-stat.
  The USD E5 report is being regenerated so its published numbers stop carrying
  defect 2 and the leak.
- **Regime sensitivity:** `rev_1m` went from −0.0094 over the full CAD sample to
  −0.157 on the 10 recent validation dates, so the baseline the model must beat
  moves a lot with the window. A single 10-date comparison deserves a wider re-run.

## One thing worth learning
In cross-sectional equity ranking there are two ways to state "this asset will do
well": *how much* (a continuous, pooled magnitude) and *relative to its peers*
(a within-date rank). The E5 probe showed the two can disagree in sign without
either being wrong — a "sign flip" between ridge and logit was a target-definition
artefact, not a contradiction. WI-009 therefore trains and scores only in the
relative/rank space. That is also why the model is compared factor-by-factor: a
rank model that cannot beat a plain 12-1 momentum or 1-month reversal factor is not
yet earning its complexity.

## How to respond
- "gate approved" → WI-009b: full-history training run + explicit skill bar, then re-gate.
- "hold — <question>" → work stops; the question lands in the plan's Deviations.
- "reject" → drop the contrastive branch and ship the E5 factor baseline as the
  technical signal for D-003 Option 2.