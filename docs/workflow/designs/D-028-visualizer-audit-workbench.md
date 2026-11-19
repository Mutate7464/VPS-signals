# D-028 — Visualizer / Audit Workbench (Track A of plan 26-W47)

Source: `docs/plans/26-W47-visualizer-audit-workbench.md` (Opus batch, collected 2026-11-19).
Brief: `docs/workflow/briefs/2026-11-19-visualizer-audit-workbench-raw.md`. Admin ruling 2026-11-19:
Track B (L0/L1/L2 research) BEFORE Track A; Track B cards = WI-074..084. This doc covers Track A only.

## Decision
Dash + Plotly app in `src/visualizer/`, one gunicorn worker (2 threads) on 127.0.0.1 behind SSH tunnel,
`debug=False`, no `dcc.Interval`. Column-projecting `loader.py` with byte ledger (3.0 GB resident budget),
LRU caches, schema assertions at startup, writes only to `state/viz/`. Family-OOF materialization is the
only writer outside `state/viz/` and is its own carded job.

## WI id mapping (plan placeholder → card)
| Plan | Card | Phase |
|---|---|---|
| WI-VIZ-00 | WI-085 scaffold/loader/schema/bench | 0 |
| WI-VIZ-01 | WI-086 join index + global bar + KPI strip | 1 |
| WI-VIZ-02 | WI-087 View 1 legacy OOF | 1 |
| WI-VIZ-03 | WI-088 View 3 OHLC drill-down | 1 |
| WI-VIZ-04 | WI-089 View 2 threshold sweep | 2 |
| WI-VIZ-05 | WI-090 export + whitelist validator | 2 |
| WI-VIZ-06 | WI-091 View 1 family (manifest stats) | 2 |
| WI-VIZ-07 | WI-092 job runner + family-OOF pilot | 2 |
| WI-VIZ-08..n | WI-093 family-OOF materialization batches | 2 |
| WI-VIZ-12 | WI-094 switch View 1/2 family to OOF | 2 |
| WI-VIZ-09 | WI-095 View 4 correlation/dendrogram | 3 |
| WI-VIZ-10 | WI-096 View 5 heatmaps | 3 |
| WI-VIZ-11 | WI-097 View 6 PSI + Rank IC | 3 |

## Open questions split
**Blocking (name the WI):**
- Panel row counts per market → confirms 3 GB budget + latency figures. Blocks WI-085 dispatch only as a
  Phase-0 measurement (the card measures them; nothing blocks the card itself).
- `_pl0/1/2` semantics and `y_*` value set → needed by WI-086/087 schema assertions; recorded, not hard-coded.
- EV sign convention for `y_15d_low`/`y_20d_down` → blocks WI-086 KPI definition.
- Do manifests record per-fold test date ranges + feature lists → blocks WI-092/093 scoring scope.

**Non-blocking context:** CPU-credit model source (existing credit_monitor script), other VPS tenants
(memory headroom), family-OOF filename convention (decide at WI-093 with DATA_CONTRACT §1).

## Gates
Track A is NOT blocked by G0 (BOARD L0/L1/L2 correction — that gates Track B only). Human sign-off gate
per batch of cards still applies. Phase 1 exit: admin runs one "why did X win/fail" session and signs off
in the card. All KPIs carry the watermark "out-of-fold, but threshold-selection bias risk"; recomputed
barrier overlays are display math, labeled "not label source", MISMATCH badge never reconciled.
