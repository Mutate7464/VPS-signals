# L2 time-exit 5-seed sign-flip placebo — CAD (PM full-run, CALIB only; EVAL unread)

- Generated (UTC): 2026-11-16T20:32:24Z
- Entries: 16,029 CALIB rows (same frames as reports/l2_time_exit/calib_CAD.md)
- Placebo: sign-flip on the paired arm-vs-event differences, seeds [6800, 6801, 6802, 6803, 6804]; cost 50 bps single-leg round trip

| arm | observed net vs event (bps) | placebo net (bps) seeds 1-5 | placebo mean | observed in placebo range? |
| --- | ---: | --- | ---: | --- |
| `fixed_h13` | -83.1 | -67.9, -26.0, -13.1, -57.0, -27.6 | -38.3 | no |
| `fixed_h55` | +473.0 | -93.2, +98.9, +5.4, -94.5, +31.7 | -10.3 | no |
| `hybrid_h13` | -83.1 | -67.9, -26.0, -13.1, -57.0, -27.6 | -38.3 | no |
| `hybrid_h55` | -50.0 | -50.0, -50.0, -50.0, -50.0, -50.0 | -50.0 | YES — no edge beyond placebo |

- Reading: an observed net edge inside the sign-flip placebo range is indistinguishable from sign noise.

Record-only: no shortlist, no deployment, no live trading.
