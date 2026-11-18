# Gate decision — WI-014 factor screener → daily shortlist CSV + tearsheet PDF

**Date:** 2026-10-28 · **Decision by:** admin (in-chat: "accept wi-014") · **Domain:** clear · **Door:** two-way.

## What was decided

**ACCEPT — WI-014 closed DONE.**

- **What ships:** `scripts/wi014_screener.py` (+ `src/pdf_compiler_factor.py`): daily top-10 research shortlist CSV + 11-page tearsheet PDF per market (USD + CAD), NO_TRADE caveat on the summary page. Both markets run from one command; market-suffixed output paths.
- **What doesn't:** no trading automation, no new factors/composite/model — this is a research-shortlist renderer on the existing E5 factor baseline.
- **Evidence:** Build steps 1–4, full suite **396 passed EXIT:0**, PM independently re-verified dry-run order, invalid-market exit 2, targeted 36, 2 CSVs (10 rows) + 2 non-empty PDFs, frozen artifacts clean (66 reports + `src/pdf_compiler.py` sha-identical). Plan `docs/plans/2026-10-26-WI-014-factor-screener-pdf.md`; log `docs/plans/logs/WI-014-factor-screener-pdf.md` STATUS: DONE.
- **What carries forward:** none of the open gates — this closes the last open gate. Next work item is **WI-015** (performance-analytics pivot, admin-ordered 2026-10-28): run/momentum targets + fib-window feature alignment, now in DESIGN/RESEARCH.

## Assumptions & review rule

Assumes the shortlist CSV/PDF schema stays frozen as shipped. Re-opens if the daily shortlist needs a different ranking key — the WI-015 target×feature matrix may propose one.