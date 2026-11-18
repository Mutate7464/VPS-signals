# L2 time exits — fixed h13/h55 + hybrid vs event exits on identical entries (CAD)

- Generated (UTC): 2026-11-15T16:38:18Z
- Scope: CALIB only (EVAL unread — WI-071); horizons pre-registered ex ante, no learned chooser
- Entries: 16,029 identical rows (key `35cdc203569ef507`) in every arm; 1 folds
- Baseline: the frozen event exit on those same rows; cost 50 bps single-leg round trip (materiality floor 10 bps)
- Best arm `fixed_h55`: net +472.96 bps vs the event exit, absolute +600.57 bps (event exit absolute +77.61 bps)
- Stop/continue: `event_exit` STOP; `fixed_h13` STOP; `hybrid_h13` STOP; `fixed_h55` STOP; `hybrid_h55` STOP

| arm | entries | hold (dates) | gross vs event (bps) | net vs event (bps) | absolute net (bps) | max fold share | folds + | ceiling | Stop flag |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `event_exit` | 16,029 | 39.0 | +0.0 | -50.0 | +77.6 | inf | 0/1 | FAIL | STOP |
| `fixed_h13` | 16,029 | 13.0 | -33.1 | -83.1 | +44.5 | inf | 0/1 | FAIL | STOP |
| `hybrid_h13` | 16,029 | 13.0 | -33.1 | -83.1 | +44.5 | inf | 0/1 | FAIL | STOP |
| `fixed_h55` | 16,029 | 55.0 | +523.0 | +473.0 | +600.6 | 1.000 | 1/1 | FAIL | STOP |
| `hybrid_h55` | 16,029 | 39.0 | +0.0 | -50.0 | +77.6 | inf | 0/1 | FAIL | STOP |

| `fixed_h55` fold | net edge (bps) |
| ---: | ---: |
| 0 | +473.0 |

- Fold report (mandatory, fails closed): `event_exit` CALIB net edge -50.0000 bps <= materiality floor 10.0; `event_exit` fold ceiling failed (share n/a, positive folds 0/1); `fixed_h13` CALIB net edge -83.0932 bps <= materiality floor 10.0; `fixed_h13` fold ceiling failed (share n/a, positive folds 0/1); `hybrid_h13` CALIB net edge -83.0932 bps <= materiality floor 10.0; `hybrid_h13` fold ceiling failed (share n/a, positive folds 0/1); `fixed_h55` fold ceiling failed (share 1.0000, positive folds 1/1); `hybrid_h55` CALIB net edge -50.0000 bps <= materiality floor 10.0; `hybrid_h55` fold ceiling failed (share n/a, positive folds 0/1)
- Layer separation: no learner refit, no AUC selection, one-shot EVAL in WI-071 after the freeze.

Record-only: no shortlist, no deployment, no live trading.
