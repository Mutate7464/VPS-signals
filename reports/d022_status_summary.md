# D-022 thread status — three-binary first-touch decomposition (grounded, 2026-11-09)

## Current artifacts (inventoried)
- Swing event sampler + first-touch labels: `src/swing_bsh/events.py` (SWING_WINDOW=21, CLUSTER_GAP=10, k∈{1.5,2.0}, h∈{21,55}; HOLD=0/BUY=1/SELL=2).
- Joint 3-class model (WI-033, **REJECT both markets 2026-11-09**): `src/swing_bsh/{train,evaluate,probe}.py` — `XGBClassifier(multi:softprob)`, per-fold OvR isotonic (CB-04), P(BUY)≥0.5 filter at at-bottom k=1.5/h=21. Pooled edge −0.15pp USD (z −19.7) / −0.07pp CAD (z −8.0). No pickle written.
- WI-032 probe CLEAR both markets: 41/111 features kept, 13/19 (USD) and 19 (CAD) FDR-sig, same-sign, placebo-clear.
- Frozen production artifact: rule-based fib system (WI-028 at-bottom entry + WI-030 exit `t15_s10_d39_close`).

## Gate verdicts bearing on a re-run
- ADOPT_LOOSE_4OF5 active (WI-031): ≥4/5 folds, pooled edge > 0, placebo z ≥ 2.0.
- Learned artifacts 0-for-4 historically: WI-009b, WI-009c, WI-030 chooser, WI-033. Any new draft must state a structural change (kanban-orchestrator rule).

## Admin direction (chat, 2026-11-09)
Replace the joint 3-class label model with **three separate binary true/false/probability models** (profit-first / stop-first / vertical-hold), each independently trained and calibrated, with entry decided by thresholds on the separate probabilities.
