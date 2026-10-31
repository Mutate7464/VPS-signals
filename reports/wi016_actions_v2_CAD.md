# WI-016 step-6 fix — decision rule v2 — CAD

- Generated (UTC): 2026-10-31T05:32:42Z
- Artifact: `reports/wi016_shortlist_CAD.parquet` (re-emitted under rule v2)
- Baseline band: commission 20 bps + slippage 5 bps (total 25 bps); scoring date 2026-10-28
- Model unchanged from step 6 (`p_meta` identical; no model spec retrained); frozen `reports/wi014_*` / `reports/perfanalytics/` untouched; USD remains descriptive (NOT_CLEAR at the addendum gate).

## Rule v2 (expected edge and cost on consistent terms)

- `gross edge (bps) = (2·p − 1) · k·ATR/close · 10000`
- `breakeven p* = 0.5 + (cost_bps + slippage_bps) / (2 · k·ATR/close · 10000)` per event
- `net edge (bps) = gross edge − (cost_bps + slippage_bps)`
- **TRADE** iff `p_meta ≥ p*` (equivalently net edge > 0) **and** `p_meta ≥ floor`; otherwise **NO_TRADE** carrying the binding reason (`p_below_floor` / `net_edge_nonpositive` / `undefined`).
- `p*` is derived per event from the barrier geometry, so a modest cost band now binds on low-volatility names instead of being dwarfed by the barrier-distance payoff.

## Out-of-fold calibrated probability floor

- Selection: maximise OOF precision on barrier-resolved **top-decile** events subject to OOF recall ≥ 0.50 and the floor ≥ 0.50 (guards exclude the degenerate all-abstain and sub-coin-flip/vacuous-floor corners). Pooled across the cleared targets.
- Chosen floor: **0.5303**  (source: oof_calibrated)
- OOF precision 0.5677, OOF recall 0.5069, OOF predicted-positive share 48.7% (n = 168,923, OOF pos rate 0.545)

| OOF threshold | precision | recall | predicted share |
| ---: | ---: | ---: | ---: |
| 1.0000 | 1.0000 | 0.0000 | 0.0% |
| 0.6072 | 0.6035 | 0.1006 | 9.1% |
| 0.5695 | 0.5816 | 0.1939 | 18.2% |
| 0.5523 | 0.5685 | 0.2842 | 27.3% |
| 0.5355 | 0.5703 | 0.3802 | 36.4% |
| 0.5325 | 0.5661 | 0.4717 | 45.5% |
| 0.5229 | 0.5619 | 0.5619 | 54.5% |
| 0.5097 | 0.5568 | 0.6496 | 63.6% |
| 0.4937 | 0.5554 | 0.7405 | 72.7% |
| 0.4867 | 0.5559 | 0.8337 | 81.8% |
| 0.4711 | 0.5530 | 0.9216 | 90.9% |
| 0.0000 | 0.5455 | 1.0000 | 100.0% |

## Baseline shortlist (20 + 5 bps)

- Rows: 148 (133 TRADE / 15 NO_TRADE; trade share 89.9%)
- Abstain reasons: ok: 133; p_below_floor: 15
- Tradeable net edge (bps): min 12.4744, p25 83.2363, median 122.0714, p75 181.5151, max 643.5731, mean 148.3384

## Sensitivity — trade share and net-edge across cost × slippage

| commission (bps) | slippage (bps) | TRADE | trade share | median net (bps) | mean net (bps) |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 10 | 0 | 133 | 89.9% | 137.0714 | 163.3384 |
| 10 | 5 | 133 | 89.9% | 132.0714 | 158.3384 |
| 10 | 10 | 133 | 89.9% | 127.0714 | 153.3384 |
| 20 | 0 | 133 | 89.9% | 127.0714 | 153.3384 |
| 20 | 5 | 133 | 89.9% | 122.0714 | 148.3384 |
| 20 | 10 | 133 | 89.9% | 117.0714 | 143.3384 |
| 30 | 0 | 133 | 89.9% | 117.0714 | 143.3384 |
| 30 | 5 | 133 | 89.9% | 112.0714 | 138.3384 |
| 30 | 10 | 132 | 89.2% | 107.9747 | 134.3676 |

## Caveats

- The floor is calibrated in-sample-CV (OOF) and applied to the same panel's scoring date; it is a research decision threshold, not a validated trading edge.
- Pooling OOF across targets lets the higher-event h8 targets dominate the pooled precision curve; per-target sensitivities are not separately floored.
- The meta-label is a first-touch binary; intra-horizon drift beyond the flat cost + slippage band is not modelled. No paper-tracked performance exists yet.
- **No order execution exists** anywhere in this pipeline; this artifact is research context behind the human gate.
