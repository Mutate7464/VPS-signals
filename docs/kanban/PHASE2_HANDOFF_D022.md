# PHASE-2 HANDOFF — D-022 thread, WIs 037–039 (for a fresh Hermes session)

> Read order for a cold start: BOARD.md ACTIVE/TODO rows → this file → the three WI
> cards in `docs/kanban/draft/`. Everything needed to run is referenced by path here.
> Written 2026-11-09 by the PM session that closed WI-035/036 (commits `feb155a`,
> `93cdc48`, `ca385bc`).

## 1. Where the thread stands (gated verdicts, all committed)

- **Frozen production artifact**: rule-based fib system (WI-028 at-bottom entry +
  WI-030 exit `t15_s10_d39_close`, 25 bps). NOTHING has beaten it; learned artifacts
  are 0-for-5 vs gates (WI-009b/c, 030, 033, 035) — WI-035's CAD "ADOPT" is a
  documented fat-tail artifact (39 events), not an edge.
- **The one real ML signal (WI-036, target-variant ablation)**: `b_hold`
  (price stays inside ±k·ATR band, no barrier touch) at SHORT horizons —
  57/57 BH-FDR survivors, all b_hold, h∈{5,8,13,21}. Winner: `exact_full_k0.8`,
  xgboost, h=13, AUC USD 0.7836 / CAD 0.7207, rank-IC ~+0.05. Attribution:
  volatility-persistence features (`atr_pct_3`, `hurst_39`, `adx_144`, entropy,
  `kama_er`). NOT predictable: b_profit/b_stop (entry/exit direction/timing),
  any variant, any learner, both markets. Report: `reports/wi036_summary.md`.
- **Artifacts for reuse**: pickles `data/models/wi035/` (96) and
  `data/models/wi036/` (6,838, ~500 MB, untracked) — naming
  `<MKT>_<learner>_<variant>_<binary>_h<h>_f<fold>.pkl`. Pickles are FOLD-FITTED:
  apply fold-f's model only to fold-f's time block. mlp_torch pickles reload
  (module alias fixed in WI-036); binary_labels/train/evaluate (WI-035) and
  binary_features_ext/binary_grid (WI-036) are the reusable modules, tests green.
- **Known caveats to carry into any downstream claim**: (a) b_hold class
  prevalence is likely majority at short h — report precision at the operating
  threshold, never AUC alone; (b) WI-036 FDR used m=60 tested cells (not full
  1,728; survivors robust, p<=1.4e-4); (c) h>=34 cells were NEVER TESTED
  (budget truncation) — WI-038 fills the gap; (d) downstream stacking rule:
  never feed b_profit/b_stop outputs together with b_hold into one learner
  (double-counting the complement) — use P(hold) alone or hold + (profit−stop).

## 2. The staged batch (approval ALREADY given by admin in chat 2026-11-09:
"stage WI (will run in new session)"; the matrix rows below were presented and
directed. Re-confirm locks are free before dispatch, then run the standard
kanban-orchestrator Stage 2: register locks, move card to in_progress/, dispatch
OpenCode surgical-builder, diff-only audit, two-strike on failure.)

| Order | Card (docs/kanban/draft/) | What | Cap |
| :--- | :--- | :--- | ---: |
| 1 | WI-037-hold-filter-tradeable-gate.md | P(hold) veto on frozen fib entries; ADOPT_LOOSE_4OF5 + placebo vs frozen baseline — the tradeable-decision test | 0.5 core-h |
| 2 | WI-039-regime-audit-hold.md | Per-regime AUC of the b_hold signal (WI-027 labels) — rider; if signal is regime-concentrated, WI-037's veto should be regime-gated | 0.3 core-h |
| 3 | WI-038-long-horizon-gap-fill.md | h∈{34..233} cells (untested, not negative); drop h=233 first if tight | 2.0 core-h |

WIP limit 1: run sequentially. WI-037 + WI-039 together are < 1 core-h; WI-038
after a >=30 min idle pause (VPS pacing policy, AGENTS.md).

## 3. VPS / dispatch conditions (updated in AGENTS.md 2026-11-09 — obey)

- Default per-WI cap **2.5 core-h** (WI-037/039/038 carry their own smaller caps).
- Balance check BEFORE each dispatch:
  `python3 ~/.hermes/skills/devops/hostinger-vps-cpu-credits/scripts/credit_monitor.py --vcpus 2 --state $HOME/.hermes/cache/scratch/cm_state.json`
  (default /var/lib state needs root — always pass --state; balance was ~100%
  after WI-036's 2.55 core-h burst).
- Bursts under cap: full speed, then >= 30 min idle. Jobs modeled > 3 core-h:
  throttle to ~1.0–1.1 cores instead of pausing. Pause >= 30 min if balance < 25%.
- Dispatch mechanics (unchanged): `/home/yycuser/.opencode/bin/opencode run
  --agent surgical-builder --auto --format json "Execute <WI path> strictly within
  its locked file manifest. Run long commands in the FOREGROUND and wait ..."`
  as a terminal(background=true) job, log to `logs/<wi>.out`, heartbeat 300.
- Two-strike discipline is live: WI-036 needed a strike-1 resume (step ceiling);
  budget the same possibility. Long jobs MUST be foreground in the builder or the
  telemetry ends PENDING with an unwritten artifact.

## 4. Decision tree after the batch

- WI-037 ADOPT: b_hold filter joins the frozen system behind the human gate —
  then a shortlist-integration WI (daily report only, NO auto-execution).
- WI-037 REJECT: the b_hold signal is real but not tradeable as a veto — close
  the thread; frozen rules stand; b_hold remains documented regime knowledge.
- WI-039 concentration in one regime: re-gate WI-037 restricted to that regime
  before any adopt claim.
- WI-038 long-h survivors: extend, else record negative and stop spending.

## 5. Open admin questions (from chat, unresolved)

- "More ML models?" — PM recommendation on record: no (learner is not the
  constraint; logistic matched XGB). Revisit only if WI-038 finds new long-h signal.
- "More data?" — longer history would help h>=89 cells (years consumed by
  embargo); more tickers low value. Not staged; awaiting admin.
