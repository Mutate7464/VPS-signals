    
    A -.- A1["1.1 AdjustableSemaphore"]
    A -.- A2["1.2 HMDS burst debounce"]
    A -.- A3["1.3 Fix _reset_pacing target"]
    A -.- A4["1.4 sys.exit on failure"]
    A -.- A5["1.5 Profile EMA guard"]
    A -.- A6["1.6 Delete corrupted profile"]
```
### Expected Throughput Impact
| Phase | Current | Expected | Improvement |
|---|---|---|---|
| **Baseline** (current code, ramp_start=3) | ~2 req/min | — | — |
| **Phase 1** (bug fixes) | — | ~5-8 req/min | 3-4× |
| **Phase 2** (warm-start) | — | ~8-12 req/min | 1.5× over Phase 1 |
| **Phase 3** (pipeline) | — | ~12-15 req/min | 1.2× over Phase 2 |
| **Phase 4** (predictive) | — | ~15-20 req/min | 1.3× over Phase 3 |
| **Phase 5** (parallel markets) | — | ~25-30 req/min total | 2× with dual client IDs |
> **Note:** These are estimates based on IBKR's documented 50 msg/sec gateway limit and the pacing event log analysis. Real-world throughput depends on HMDS farm load, time of day, and account tier.
---
## Appendix: Pacing Event Log Replay
Full timeline of the most recent run's pacing behavior (from `data/pacing_events.jsonl`):
```
20:59:02 [USD] ── Discovery phase, concurrency=5 ──
   HMDS cancels burst (6 cancels in <1s) → throttle 5→3→2→1
   
21:00:17 [USD] ── Recovery ──
   6 more HMDS cancels at concurrency=1 (drain from earlier burst)
   
21:00:33 [USD] restore 1→2 (success streak)
21:00:45 [USD] restore 2→3
21:01:17 [USD] GLOBAL_PAUSE (consecutive_hits >= 4)
21:01:50 [USD] restore 1→2 (post-pause recovery)
21:14:48 [USD] ── Ramp phase ──
   Gradual restore 1→2→3 over 1 minute
   
21:32:32 [CAD] ── Ramp phase, starting fresh ──
   restore 1→2→3 over 10 seconds
21:46:24 [CAD] ── HMDS burst at concurrency=15 ──
   15 cancels in <1 second
   Ceiling cascaded: 15→14→13→12→11→10→9→8→7→6→5→4
   (Each cancel dropped ceiling by 1 — BUG #5)
   
23:21:37 [CAD] ── Confirm phase ──
   restore 1→2→3 after long recovery
```
**Root cause pattern:** Burst cancels → cascading ceiling erosion → slow recovery → repeat. Fix #1.2 (burst debounce) eliminates this cycle entirely.