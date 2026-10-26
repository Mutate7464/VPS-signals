# WI-014 step 4 — end-to-end run and regression checks (evidence)

Plan `docs/plans/2026-10-26-WI-014-factor-screener-pdf.md` step 4 · goal G-001 · 2026-10-26.

## Run

`uv run python scripts/wi014_screener.py` (no flags: default BOTH, USD then CAD, top-10),
detached to `logs/wi014_e2e_run.out`; wall clock **25.78 s**, peak RSS **342 MB**
(`/usr/bin/time -v`), exit **0** — inside the 2 vCPU / 8 GB / no-swap host limit.

```
[wi014_screener] PLAN: markets=USD, CAD (default BOTH, USD then CAD); top_n=10; rank by mom_12_1 descending (WI-012-validated E5 single factor)
[wi014_screener] USD: scoring_date=2026-09-23 eligible=508 stale=0 skipped={'no_raw_file': 0, 'stale_bar': 0, 'short_history': 1, 'nan_factor': 0} rows=10
[wi014_screener] USD: reports/wi014_shortlist_USD_10.csv (810 bytes)
[wi014_screener] USD: reports/screener_factor_USD_20260923.pdf (259,039 bytes, 11 pages, tickers=SNDK,MU,TWST,WDC,VSXY,ASX,INTC,VIAV,FORM,AMD)
[wi014_screener] CAD: scoring_date=2026-09-22 eligible=315 stale=0 skipped={'no_raw_file': 0, 'stale_bar': 0, 'short_history': 2, 'nan_factor': 0} rows=10
[wi014_screener] CAD: reports/wi014_shortlist_CAD_10.csv (816 bytes)
[wi014_screener] CAD: reports/screener_factor_CAD_20260922.pdf (255,914 bytes, 11 pages, tickers=MU,FDY,ARG,MAU,AMD,NUAG,AMAT,CG,BDT,TKO)
EXIT:0
```

## Artifacts produced (all new; nothing pre-existing touched)

| Artifact | Size | Content |
| :--- | ---: | :--- |
| `reports/wi014_shortlist_USD_10.csv` | 810 B | header + 10 rows, `rank,symbol,mom_12_1,rev_1m,vol_20,amihud_20,log_dollar_vol_20,scoring_date`; scoring date 2026-09-23; mom_12_1 strictly descending (13.5076 → 1.8584) |
| `reports/wi014_shortlist_CAD_10.csv` | 816 B | same schema; scoring date 2026-09-22; mom_12_1 strictly descending (4.7954 → 1.4449) |
| `reports/screener_factor_USD_20260923.pdf` | 259,039 B | 11 pages = summary + 10 ticker pages, `%PDF` |
| `reports/screener_factor_CAD_20260922.pdf` | 255,914 B | 11 pages = summary + 10 ticker pages, `%PDF` |

Scoring dates equal each market's latest feature date in
`data/features/features_{USD,CAD}.parquet` (2026-09-23 / 2026-09-22), as the freshness
contract requires; 1 USD and 2 CAD symbols were excluded as short-history (no complete
factor row), and every shortlisted name got a chart page.

## Frozen-artifact verification

- `logs/wi014_frozen_hashes_pre.txt` (sha256 of all 66 pre-existing `reports/` files +
  `src/pdf_compiler.py`, taken before any WI-014 step ran) vs the same hashes recomputed
  **after** the end-to-end run and **again after** the full suite:
  `comm -3` diff = **0 changed pre-existing files**; the only differences are the four new
  WI-014 outputs. `src/pdf_compiler.py` hash unchanged.
- `git diff --exit-code -- src/pdf_compiler.py reports/screener_CAD_20261021.pdf reports/screener_USD_20261021.pdf`
  → exit 0 (note: `reports/*.pdf` is in `.gitignore`, so for the two legacy PDFs this
  command is vacuous — the sha256 comparison above is the real check, and it shows both
  20261021 PDFs byte-identical).
- `git status --short reports/` after the run shows **only** the two new CSVs
  (`wi014_shortlist_{USD,CAD}_10.csv`); the new PDFs are ignored by the repo's
  `reports/*.pdf` rule, exactly like the frozen demo PDFs, so they stay regenerable and
  uncommitted.

## Full suite

`uv run pytest tests/ -q` run detached → `logs/wi014_full_suite.out`, polled for its marker:

```
START 2026-10-26T23:30:52Z
396 passed in 530.14s (0:08:50)
EXIT:0
END 2026-10-26T23:39:45Z
```

396 = 360 (WI-013 baseline) + the 36 new WI-014 tests (14 generator/CLI contract +
15 renderer + 7 end-to-end CLI). No failures, no errors, no skips introduced.

## Acceptance mapping (plan step 4)

- *`reports/wi014_shortlist_{USD,CAD}_10.csv`, non-empty date-stamped PDFs exist* — yes,
  table above (10 rows each; 11-page non-empty PDFs).
- *Frozen artifacts remain unchanged* — 0 hash differences; `src/pdf_compiler.py` diff
  clean; only new WI-014 files in `reports/`.
- *Full tests pass* — 396 passed, `EXIT:0`.

## Stop point

Build stops here: the outputs are the research shortlist + tearsheet under the
NO_TRADE/cost caveat, and **the sprint human gate remains open** — PM verification first,
then the admin decides. No publishing, distribution or auto-execution was performed, and
BOARD.md was not modified by Build (PM/scribe own the board row).
