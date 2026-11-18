# L2 time-exit 5-seed sign-flip placebo — USD (PM full-run, CALIB only; EVAL unread)

- Generated (UTC): 2026-11-16T20:32:24Z
- Entries: 28,220 CALIB rows (same frames as reports/l2_time_exit/calib_USD.md)
- Placebo: sign-flip on the paired arm-vs-event differences, seeds [6800, 6801, 6802, 6803, 6804]; cost 50 bps single-leg round trip

| arm | observed net vs event (bps) | placebo net (bps) seeds 1-5 | placebo mean | observed in placebo range? |
| --- | ---: | --- | ---: | --- |
| `fixed_h13` | -64.2 | -57.6, -44.1, -56.8, -49.6, -43.2 | -50.2 | no |
| `fixed_h55` | +231.8 | -68.5, -64.8, -55.1, -49.7, -81.5 | -63.9 | no |
| `hybrid_h13` | -64.2 | -57.6, -44.1, -56.8, -49.6, -43.2 | -50.2 | no |
| `hybrid_h55` | -50.0 | -50.0, -50.0, -50.0, -50.0, -50.0 | -50.0 | YES — no edge beyond placebo |

- Reading: an observed net edge inside the sign-flip placebo range is indistinguishable from sign noise.

Record-only: no shortlist, no deployment, no live trading.
