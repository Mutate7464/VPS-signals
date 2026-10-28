# Performance Analytics (WI-015) — pivot from regime labels to run/momentum analytics

> Status: SETUP / RESEARCH (brainstorm stage). Admin direction 2026-10-28 (in chat).
> Code home: `src/perfanalytics/` · research docs: this folder · outputs → `reports/perfanalytics/` · data stays in `data/` (no copies).

## Why the pivot

WI-002/009b/009c/011 quadruple-confirmed: on this universe, binary/three-class
regime labels are the bottleneck — the 89-feature pool adds nothing at those
target definitions. The admin's new direction inverts the question: instead of
asking "will it be up/down/stay?", measure **how big / fast / long** the
upward run is when it happens (frequency × intensity), then ask which
**features align with which run target**.

## File map

| Path | Contents |
|---|---|
| `docs/tech_approach/perfanalytics/README.md` | This charter + file map |
| `docs/tech_approach/perfanalytics/targets-research.md` | Target taxonomy, definitions, brainstorm, open questions |
| `docs/tech_approach/perfanalytics/features-research.md` | Fib-spacing features + alignment analysis plan (target×feature matrix) |
| `src/perfanalytics/targets/` | Run-target labelers (continuous, forward window, trailing thresholds) |
| `src/perfanalytics/features/` | Feature builders (fib spacing + derived) |
| `src/perfanalytics/correlation/` | Alignment diagnostics (per-target association, same-sign bar) |
| `reports/perfanalytics/` | Generated analysis outputs |

## Ground rules carried over

- Point-in-time discipline: evaluation strictly over [t+1, t+k]; any threshold
  (ATR, run size) uses trailing (≤ t) data only — `src/targets.py` pattern.
- Same-sign skill bar (WI-009b re-spec): any shipped association must match the
  sign of the best univariate factor AND clear a noise margin, held-out.
- 2 vCPU / 8 GB: `n_jobs=2`, float32 immediately after calc, symbol-sequential
  iteration (never all-ticker uncompressed frames).
- CAD + USD both parametrized (`--market`), market-suffixed report paths (F-2..F-5).