# L2 time exits — fixed h13/h55 + hybrid vs event exits on identical entries (USD)

- Generated (UTC): 2026-11-15T16:38:17Z
- Scope: CALIB only (EVAL unread — WI-071); horizons pre-registered ex ante, no learned chooser
- Entries: 28,220 identical rows (key `02076ff55dc55cef`) in every arm; 1 folds
- Baseline: the frozen event exit on those same rows; cost 50 bps single-leg round trip (materiality floor 10 bps)
- Best arm `fixed_h55`: net +231.77 bps vs the event exit, absolute +329.41 bps (event exit absolute +47.64 bps)
- Stop/continue: `event_exit` STOP; `fixed_h13` STOP; `hybrid_h13` STOP; `fixed_h55` STOP; `hybrid_h55` STOP

| arm | entries | hold (dates) | gross vs event (bps) | net vs event (bps) | absolute net (bps) | max fold share | folds + | ceiling | Stop flag |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `event_exit` | 28,220 | 39.0 | +0.0 | -50.0 | +47.6 | inf | 0/1 | FAIL | STOP |
| `fixed_h13` | 28,220 | 13.0 | -14.2 | -64.2 | +33.5 | inf | 0/1 | FAIL | STOP |
| `hybrid_h13` | 28,220 | 13.0 | -14.2 | -64.2 | +33.5 | inf | 0/1 | FAIL | STOP |
| `fixed_h55` | 28,220 | 55.0 | +281.8 | +231.8 | +329.4 | 1.000 | 1/1 | FAIL | STOP |
| `hybrid_h55` | 28,220 | 39.0 | +0.0 | -50.0 | +47.6 | inf | 0/1 | FAIL | STOP |

| `fixed_h55` fold | net edge (bps) |
| ---: | ---: |
| 0 | +231.8 |

- Fold report (mandatory, fails closed): `event_exit` CALIB net edge -50.0000 bps <= materiality floor 10.0; `event_exit` fold ceiling failed (share n/a, positive folds 0/1); `fixed_h13` CALIB net edge -64.1838 bps <= materiality floor 10.0; `fixed_h13` fold ceiling failed (share n/a, positive folds 0/1); `hybrid_h13` CALIB net edge -64.1838 bps <= materiality floor 10.0; `hybrid_h13` fold ceiling failed (share n/a, positive folds 0/1); `fixed_h55` fold ceiling failed (share 1.0000, positive folds 1/1); `hybrid_h55` CALIB net edge -50.0000 bps <= materiality floor 10.0; `hybrid_h55` fold ceiling failed (share n/a, positive folds 0/1)
- Layer separation: no learner refit, no AUC selection, one-shot EVAL in WI-071 after the freeze.

Record-only: no shortlist, no deployment, no live trading.
