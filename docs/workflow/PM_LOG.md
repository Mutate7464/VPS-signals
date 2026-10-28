# PM_LOG.md — cursor for the Hermes PM cycle

> One entry per PM cycle, newest first. The newest entry's cursor (`cursor:` line)
> defines which opencode sessions the next cycle ingests. Kam's trigger: tell Hermes
> "run PM cycle". Full procedure: `docs/human/PM-CYCLE.md`.

## 2026-10-28 — Cycle 17 (WI-014 gate ACCEPT → DONE; WI-015 pivot setup + feature-window spec confirmed)

- **GATE DECISION (admin, in-chat 2026-10-28): WI-014 ACCEPT.** Canonical record = this entry; human stream `docs/human/briefings/2026-10-28-gate-WI-014-factor-screener-pdf.md`; board row → DONE (collapsed). Shortlist CSV + tearsheet PDF ships as built (suite 396 EXIT:0, PM-verified); no execution beyond the record.
- **WI-015 (admin order, same message): pivot to performance analytics.** Setup done commit `9076c29`: `src/perfanalytics/{targets,features,correlation}/` stubs + `docs/tech_approach/perfanalytics/` (README, targets-research, features-research); board row added at DESIGN/RESEARCH. Target drafts T1 amplitude / T2 velocity / T3 duration / T4 frequency + 8 brainstormed.
- **Feature-window spec CONFIRMED (admin):** iterate the current normalized feature families at Fibonacci-scaled windows **3→200** (grid 3, 5, 8, 13, 21, 34, 55, 89, 144, cap 200), then per-target alignment (which family×window correlates with each run target). Written into `features-research.md`; replaces the earlier "fib retracement band" reading.
- Open decisions still with admin: run-trigger (ATR vs fixed %), k grid, close-vs-wick amplitude — parked in targets-research open questions.
- cursor: `ses_e85a141e0ffec` unchanged (no new opencode sessions; work executed by PM directly).

## 2026-10-26 — Cycle 16 (WI-014: plan approved in-chat -> Build -> PM verify -> gate open)
- Admin APPROVED the WI-014 plan in-chat ("approve"). Board row -> EXECUTING (commit `8f75c97`), Build dispatched detached headless (`logs/wi014_build.out`).
- **Delivered (Build commits `2c33cc3`..`878db57`, steps 1-4):** `scripts/wi014_screener.py` (+`src/pdf_compiler_factor.py`), tests `test_wi014_screener.py`/`test_pdf_compiler_factor.py`; e2e run 25.8 s / peak RSS 342 MB -> `wi014_shortlist_{USD,CAD}_10.csv` + `screener_factor_{USD,CAD}_*.pdf` (11 pages each). Frozen baseline: 66 pre-existing reports + `src/pdf_compiler.py` sha-identical; full suite **396 passed EXIT:0** (`logs/wi014_full_suite.out`).
- **PM re-verified independently:** dry-run prints USD then CAD, suffixed paths only; `--market XYZ` exit 2 before writes; targeted 36 passed; CSVs 10 rows + header, schema rank/symbol/5 factors/date; PDFs ~256 KB, `%PDF` header; `git status reports/ src/` clean of modifications.
- **Open for admin gate:** WI-014 verdict (research-shortlist tearsheets, NO_TRADE caveat on summary page). No unresolved deviations; Build left BOARD.md untouched per plan.
- cursor: `ses_e85a141e0ffec` unchanged (Build sessions ingested via artifacts + logs, not full transcripts).
