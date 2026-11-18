# Brief — WI-014: E5 factor screener → daily shortlist → tearsheet PDF (both markets)

> Admin goal 2026-10-26: finish the workflow — produce a PDF of recommendations for
> BOTH CAD and USD from the validated route, before next week's analytics pivot
> (learn/combine technical indicators, add metrics). This is the "USD screener
> wiring" that WI-013 deliberately left out of scope.

## Context (verified this session)

- The only PDFs today, `reports/screener_{CAD,USD}_20261021.pdf` (WI-001, Sprint 5),
  are built by `src/pdf_compiler.py` from `data/**/predictions_{market}_latest.parquet`
  — the Gate-4-FAILED xgb models (WI-002: all targets ≈ random). Structural demo only.
- The classifier-route shortlists (`wi009c_shortlist_CAD.csv`, `wi012_shortlist_USD.csv`)
  rest on the WI-009c NEGATIVE verdict ("composite rests on noise — NOT usable").
  They are NOT recommendations and must not feed the PDF.
- The validated MVP signal is the **E5 factor baseline** (WI-009c gate; WI-012
  cross-market): single-factor within-date rank-IC vs `fwd_atr_ret_15` —
  `mom_12_1` +0.0271 t+7.33 (CAD), generalizes on USD (+0.0209 t+6.00, WI-012);
  `vol_20`, `amihud_20`, `rev_1m` negative; `log_dollar_vol_20` weak.
  No script ranks the latest cross-section into a top-N shortlist, and no PDF
  renders it. WI-013's `src/market_cli.py` (default BOTH = USD→CAD) is available.
- WI-011 verdict: NO_TRADE survives costs at this universe size → the PDF is a
  **research shortlist** with the cost/NO_TRADE caveat stated on the summary page,
  not trade instructions (human gate, per project rules).

## Admin defaults (flag to admin in the plan review; overrides change this brief)

- Ranking: **`mom_12_1` descending** (best-validated single factor, both markets).
  All five E5 factor values shown per ticker as context columns, no composite invented.
- Top-N: **10** per market.
- Freshness: latest available feature date per market; the date is printed on the page.

## Goal

Running one command produces, for USD then CAD by default (or one via `--market`),
a top-N daily shortlist CSV and a tearsheet PDF per market:
`reports/wi014_shortlist_{market}_{topN}.csv` and
`reports/screener_factor_{market}_{YYYYMMDD}.pdf` (new name — the legacy
`screener_{market}_*` files are frozen demo artifacts and must stay untouched).

## Required changes

1. **Shortlist generator** `scripts/wi014_screener.py` using `src/market_cli.py`
   (default BOTH, USD then CAD; explicit single; invalid rejected before writes).
   For each market: load `features_{market}.parquet` (bounded memory — select
   latest date per symbol, never an all-ticker full-history frame), read the five
   E5 factor columns, rank by `mom_12_1` descending, write the suffixed CSV with
   rank, symbol, factor values, and the scoring date.
2. **Tearsheet renderer** `src/pdf_compiler_factor.py` (new module; do NOT modify
   or delete `src/pdf_compiler.py` — it is the frozen Sprint-5 record). Per market,
   in dependency order: summary page (date, universe size, ranking rule, top-N
   table, E5 single-factor IC table from `reports/wi012_e5_baseline_{market}_h15.md`
   numbers, NO_TRADE/cost caveat footer) then one page per shortlisted ticker:
   candles/BB/trend channel, volume, RSI-14 (reuse `src/pdf_compiler.py` drawing
   logic via import where possible; copy, don't edit, if import is entangled with
   the predictions loader), and a factor-context panel (the five E5 factor values
   vs their cross-section percentile). PDF rules: batch 10 pages,
   `matplotlib.pyplot.close('all')` + `gc.collect()` per batch, Agg backend.
3. **CLI wiring**: `scripts/wi014_screener.py` generates CSV + PDF in one
   invocation; `--top-n` (default 10), `--market`, `--date` (default latest).
   A `--dry-run` prints the plan line and resolved paths without writing.
4. Tests: default BOTH order, invalid market rejection, no unsuffixed writer path
   reachable, CSV schema (rank/symbol/factors/date), PDF file created non-empty
   for a small top-n smoke run, legacy `screener_*_20261021.pdf` and
   `src/pdf_compiler.py` untouched.

## Constraints

- No new modeling, no composite score invention, no target/skill-bar changes —
  ranking uses an existing factor column as-is. This is presentation + plumbing,
  not research (research is next week's pivot).
- Frozen artifacts read-only: `reports/screener_*_20261021.pdf`, `src/pdf_compiler.py`,
  all `reports/wi009*`, `wi011_*`, `wi012_*`, `diag_*`, sprint reports. New outputs
  use the new prefixes above. `git status --short reports/` after a full run must
  show no modification to any pre-existing file.
- Host limits: n_jobs=2, feature frames to float32 immediately, no all-ticker
  uncompressed frames, PDF batch-10 + gc.
- No secrets. `git add` by explicit path only.

## Acceptance / deterministic verifies (plan must carry these or equivalents)

- `uv run python scripts/wi014_screener.py --dry-run` prints both markets in
  USD→CAD order and resolves only suffixed paths; `--market XYZ` exits non-zero
  writing nothing.
- `uv run python scripts/wi014_screener.py` writes 2 CSVs + 2 non-empty PDFs
  (`screener_factor_USD_*.pdf`, `screener_factor_CAD_*.pdf`) and both
  `wi014_shortlist_{USD,CAD}_10.csv`; `git status --short reports/` clean of
  pre-existing modifications.
- `uv run pytest tests/ -q` full suite passes including new tests.
- Summary page states: ranking rule, date, universe size, NO_TRADE/cost caveat.

## Out of scope

- Next week's analytics pivot (indicator learning/combination, new metrics,
  feature research) — anything beyond rendering existing factors.
- WI-004/WI-005 backlog, portfolio construction, position sizing, backtests,
  cost modeling, any model training, auto-execution of anything.

## Stop point

Plan ends at the human gate: Build executes steps, PM verifies PDFs/CSVs, admin
decides. No auto-publish or distribution of the PDFs beyond the repo.
