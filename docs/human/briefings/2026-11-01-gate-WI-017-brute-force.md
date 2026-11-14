# Gate brief — WI-017: Brute-force target/feature confirmation (USD), runs 1–4

Date: 2026-11-01 · Admin direction 2026-10-31 (chat + Discord) · PM: Hermes
Domain: complicated · Door: two-way (research artifacts only; nothing shipped)

## What happened

Full brute-force sweep, USD, 593 symbols, nothing window-pruned, in isolated
subfolders (`src/wi017/`, `reports/wi017/`, charter
`docs/tech_approach/wi017-brute-force-usd/README.md`):

- **Run 1** base targets — peak/bottom, +10%/−10% barrier touch, ±5% stay band,
  all 17 fib windows 3–233 (`reports/wi017/run1_base_rates.md`).
- **Run 2** derived family — first-touch triple-barrier verdict, days-to-touch,
  rung, velocity (`reports/wi017/run2_summary.md`).
- **Run 3** full feature grid — 16 families × 17 windows = 264 columns, plus
  redundancy report under the relaxed prune rule (`reports/wi017/run3_redundancy.md`).
- **Run 4** alignment matrix — 165 targets × 264 features, 5 chronological folds,
  20-session embargo, block-bootstrap noise margin, same-sign bar vs best E5
  factor (`reports/wi017/run4_alignment.{md,csv,json}`).

Every run recompute-verified against independent implementations; 12 regression
tests; run 3 shown byte-equal to the WI-016 engine on all 99 shared columns.
Two real bugs caught before contaminating anything (run-1 forward-window
orientation; run-3 all-NaN hurst below w=12). Commits `170e1e4`, `8c7b7e3`,
`68f48dd`, `a55dfa0`.

## Why it matters — the actual finding

**The sweep separates mechanical alignment from tradeable signal:**

1. **Amplitude targets are strongly aligned — mechanically.** Best cells are
   trailing-vol → forward-amplitude (atr_pct_34 → rung_63 IC +0.71;
   touch_up10/dn10 via vol features IC +0.12–0.34). High vol predicts large
   forward range and touching *either* barrier. Strong confirmation the
   features measure what they claim; not an edge by itself.
2. **Direction is thin — WI-016's verdict is confirmed, not refuted.** The
   genuinely directional target (`first_touch_*`, which side hits first) tops
   out at **|IC| ≈ 0.03–0.06** (best: first_touch_13 atr_pct_63 +0.053);
   `first_touch_63`: zero cells pass; `first_touch_55`: 17 of 264. The most
   balanced 3-way target (w≈34) reaches only +0.034. This is the same
   statistically-thin zone WI-016 hit on USD.
3. **WI-015 positives survive on USD**: bb_width_233 +0.567, range_width_233
   +0.644, yangzhang_144 +0.705, atr_pct_233 +0.649 — but against amplitude
   targets (rung/stay5), consistent with #1.
4. **Redundancy**: 558 high-ρ pairs / 34,716 (1.6%), all adjacent-window
   smooth-family clones; fast families (kama_er, hurst, entropy, vwap) earn
   their dense grid. Prune deferred per admin rule — verdicts now available in
   run 4 data.
5. **DOA screen**: stay5 < 1% base rate at w ≥ 63 (down to 0.02%) — descriptive
   only there. Usable 3-way balance at w ≈ 34 (38/30/33).
6. **Wart for next WI**: shipped WI-016 grid's `hurst_9` column is all-NaN by
   constructor (needs w ≥ 12) — dead column in past panels, not wrong values.

## What we can do about it

| # | Option | Why | Expected outcome | Risk / cost |
|---|---|---|---|---|
| A | **Close WI-017 as confirmation; open next WI on condition-first directional study at w≈34 (first_touch targets, vol + fib-structure features, WI-011 cost overlay)** | Direction is where any real edge would live; w≈34 is the only balanced 3-way region; conditions (not levels) were WI-011's productive frame | Either a tradeable condition set with cost survival, or a clean negative that retires the directional route on USD | ~1 WI of effort; WI-011 precedent says "none survive costs" is a live possibility |
| B | Close WI-017 with no successor | Triple-confirmed across WI-002/009*/016 that direction is thin on this universe; stop spending there | Pipeline stays factor-screener-only; no new bets | Zero cost; risks missing the one region (w≈34 3-way) the sweep newly identified |
| C | Prune the grid and rebuild the WI-016 feature panel (drop 558-ρ clones + dead hurst_9, keep fast families dense) | Cheap hygiene, makes every future panel smaller and cleaner | Leaner panels, no information loss measured | Small; prune list already computable from run 3/4 data |
| D | Extend brute force (CAD market, more barrier levels, meta-labeling) | Completeness | More confirmation of what is likely the same structure | High compute for low marginal information; direction would remain thin |

## REC

**A + C together** (C is a ~half-day hygiene fold into the next WI; A is the
substantive bet). Reasoning: the sweep's only genuinely new, actionable finding
is that w≈34 is a uniquely balanced 3-way region never tested with
condition-first methods; WI-011's machinery already exists and its negative was
about conditions on *levels*, not on this target family. The |IC|≈0.05 ceiling
means any A-route success will be thin too — set the expectation now: it clears
only if a condition set survives the 20+5 bps cost overlay, else it closes as a
documented negative and B's world (factor screener stands) is where we land.

Assumptions that must hold: run-4 folds are leakage-clean (embargo verified in
its own build; spot re-verified here); commission assumptions unchanged
(WI-011's 20+5 bps). Review rule: any first_touch-condition cell clearing
|IC| ≥ 0.05 AND surviving costs re-opens the route; nothing weaker does.

## Decision requested

1. Close WI-017 as **confirmation delivered** (verdict: assumptions confirmed —
   WI-015 positives real, WI-016 thin-direction verdict stands)?
2. Open the A-route WI (condition-first on first_touch @ w≈34, with C folded in)?
3. Or B / D.

## GATE DECISION

**2026-11-01, admin (chat): "confirm. proceed with rec" → REC A+C ACCEPTED.**

- WI-017 **closed as confirmation delivered**: assumptions confirmed — WI-015
  positives real on USD (against amplitude targets); WI-016's thin-direction
  verdict stands (first_touch best |IC| ≈ 0.03–0.06, first_touch_63 zero passes).
- **A-route opened as WI-018**: condition-first study on first_touch targets at
  w≈34 (the sweep's uniquely balanced 3-way region), vol + fib-structure
  features, WI-011 cost overlay (20+5 bps). Expectation set at gate: it ships
  only if a condition set survives costs; otherwise it closes as a documented
  negative and the E5 factor screener stands as the MVP signal.
- **C folded into WI-018**: prune recommendations computed (176 drop / 88 keep,
  `reports/wi017/run5_prune_recs.{md,json}`); next WI verifies single-representative
  families against its actual target before applying. Shipped WI-016 grid frozen
  and untouched. `hurst_9` dead-column fix rides along.
- Nothing auto-executed: the ADR is at `docs/workflow/designs/D-018-*.md`
  (status: proposed) with open questions at the definition gate.
