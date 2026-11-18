# L2 time exits — fixed h13/h55 + hybrid vs event exits on identical entries (CAD)

- Generated (UTC): 2026-11-15T03:20:21Z
- Scope: CALIB only (EVAL unread — WI-071); horizons pre-registered ex ante, no learned chooser  (smoke / synthetic)
- Entries: 200 identical rows (key `61a2831967f2f648`) in every arm; 5 folds
- Baseline: the frozen event exit on those same rows; cost 50 bps single-leg round trip (materiality floor 10 bps)
- Best arm `fixed_h13`: net +103.20 bps vs the event exit, absolute +68.68 bps (event exit absolute -84.52 bps)
- Stop/continue: `event_exit` STOP; `fixed_h13` CONTINUE; `hybrid_h13` CONTINUE; `fixed_h55` STOP; `hybrid_h55` STOP

| arm | entries | hold (dates) | gross vs event (bps) | net vs event (bps) | absolute net (bps) | max fold share | folds + | ceiling | Stop flag |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `event_exit` | 200 | 32.3 | +0.0 | -50.0 | -84.5 | inf | 0/5 | FAIL | STOP |
| `fixed_h13` | 200 | 13.0 | +153.2 | +103.2 | +68.7 | 0.279 | 5/5 | pass | CONTINUE |
| `hybrid_h13` | 200 | 11.9 | +83.3 | +33.3 | -1.2 | 0.439 | 5/5 | pass | CONTINUE |
| `fixed_h55` | 200 | 55.0 | +22.1 | -27.9 | -62.5 | inf | 1/5 | FAIL | STOP |
| `hybrid_h55` | 200 | 32.3 | +0.0 | -50.0 | -84.5 | inf | 0/5 | FAIL | STOP |

| `fixed_h13` fold | net edge (bps) |
| ---: | ---: |
| 0 | +114.3 |
| 1 | +85.0 |
| 2 | +61.5 |
| 3 | +111.3 |
| 4 | +143.8 |

- Fold report (mandatory, fails closed): `event_exit` CALIB net edge -50.0000 bps <= materiality floor 10.0; `event_exit` fold ceiling failed (share n/a, positive folds 0/5); `fixed_h55` CALIB net edge -27.9494 bps <= materiality floor 10.0; `fixed_h55` fold ceiling failed (share n/a, positive folds 1/5); `hybrid_h55` CALIB net edge -50.0000 bps <= materiality floor 10.0; `hybrid_h55` fold ceiling failed (share n/a, positive folds 0/5)
- Layer separation: no learner refit, no AUC selection, one-shot EVAL in WI-071 after the freeze.

Record-only: no shortlist, no deployment, no live trading.
