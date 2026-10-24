# D-002 — Combined E2–E5 verdict (USD, 508 tickers, 2016-01 → 2026-09)

> Generated 2026-10-24 · one line per hypothesis, each traced to its report file.
> Gate decision (continue / redesign / stop) belongs to the admin — this file is the evidence pack.

| Hypothesis | Verdict | One-line basis | Report |
| :--- | :--- | :--- | :--- |
| **H1** — E2's null was a fixture artifact; a clean run has signal | **NOT CONFIRMED** | 0/4 targets pass ≥3/5 governance gates on the real universe (ROC-AUC 0.48–0.54) | `reports/diag_D002_e2.md` |
| **H2** — feature set/selection is the binding constraint (richer features fix it) | **NOT SUPPORTED** (partially observed) | Deflated IC t > 2.5 is reached on the 15d targets by the E2-faithful baselines too (`full` +3.54 on y_15d_low, `legacy19` +4.11/+3.78), so the new fib/range block and every ablation set do NOT isolate a feature-set fix; signal presence tracks the target (15d yes, 20d no), not the feature set | `reports/diag_D002_e3.md` |
| **H3** — labels/metric are misaligned with what the model learns | **SUPPORTED** | Continuous Spearman IC of model prob vs fwd ATR return is significant on 15d targets (t +4.31/+3.27) while ALL binary gates fail → ranking signal exists that the absolute ATR-breakout labels + within-date K-gates cannot express; additionally ticker-prior AUC beats the model on all 4 targets → strong identity-signal component | `reports/diag_D002_e4.md` |
| **H4** — little signal in OHLCV at 15–20d (unpredictability floor) | **NOT SUPPORTED (floor BREACHED)** | Classic factors DO predict the continuous fwd ATR return: mom_12_1 t +5.54, vol_20 t −4.72, amihud_20 t −3.37, ridge oof IC t +2.25/+2.05 → a trivial-factor explanation for the model's IC cannot be excluded, and factor structure is clearly present | `reports/diag_D002_e5.md` |

## Synthesis (what the three diagnostics jointly say)

1. **Signal exists in the continuous forward-ATR-return space** — E4 (model IC t +4.31) and E5 (factor IC t up to +5.54) agree independently.
2. **The pipeline's expression of it is the broken part** — absolute binary ATR-breakout labels + within-date top-K gates are blind to that signal (E4), and the model's AUC is partly a per-ticker identity signal (ticker-prior ≥ model on all targets).
3. **Features were never the binding constraint** — the E2-era 19-feature set and every ablation of the new 89-feature set land in the same place per target (E3).
4. **Consequence for any redesign** (admin decision, per ADR D-002): target/metric redesign (cross-sectional / relative labels) is the indicated fix (H3 fires), and any new target must be tested against the 5 classic factors as a baseline control (E5's floor result), since factor structure is present and would contaminate an uncontrolled comparison.

## Cost/scale notes

- E3 chain: 5 sets × 4 targets × (1 real + 3 placebo) × 5 folds + final on 1,240,275 rows; E2-frozen hyper-parameters; `wl + wl_cs_pct` (64-col) masks verified by `tests/test_feature_masks.py`.
- E5: purged 5-fold WF, 20d embargo, same splitter as the trainer; factors computed raw per symbol (float32).
