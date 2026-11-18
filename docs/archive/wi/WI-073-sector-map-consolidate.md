---
wi_id: WI-073
title: Sector map consolidation (canonical config/sector_map.csv; unblocks WI-070)
status: draft
agent: surgical-builder
depends_on: []
gate_layer: "infra (metadata; no gate — this is a data product, not a trading claim)"
board_row: "D-027 Phase 4 enabler for WI-070"
write_files:
  - src/l2_overlay/sector_map_consolidate.py
  - tests/l2_overlay/test_sector_map_consolidate.py
  - config/sector_map.csv
  - reports/sector_map_consolidation.md
  - data/sector_map_conflicts.csv
read_only_files:
  - IBKRDownload/sector_map.csv
  - IBKRDownload/ibkr_ingest.py
  - src/swing_bsh/binary_features_ext.py
  - src/build_watchlist.py
  - docs/workflow/designs/D-027-l2-rebuild.md
  - docs/kanban/draft/WI-070-sector-pairs.md
test_command: uv run pytest tests/l2_overlay/test_sector_map_consolidate.py -q --tb=short --maxfail=1 && uv run python -m src.l2_overlay.sector_map_consolidate --smoke
---

## 1. Objective and invariant
- Build ONE canonical sector map at `config/sector_map.csv` covering **every symbol in the
  price panels** (measured 2026-11-16: USD 674, CAD 394 parquet files). Measured state:
  config map covers USD 606/674 (68 missing, 1 blank-sector) but CAD only 199/394 (195
  missing); IBKRDownload copy covers CAD 347/394; on the 162-symbol CAD overlap the two
  copies disagree on sector for ~41%. This WI consolidates and gap-fills; it does NOT
  invent sectors.
- Precedence rule (declared, deterministic): for a symbol in both sources, `config/`
  wins; every overridden value recorded in `data/sector_map_conflicts.csv`
  (symbol, market, config_sector, ibkr_sector, source_won). Blanks never overwrite a
  non-blank.
- Gap-fill source: IBKR contract metadata via the existing `ib_async` path
  (`ibkr_ingest.py` pattern) for symbols missing from both maps. Fill `sector`;
  `industry`/`sub_group`/`tc_rating` may stay blank. Network runs happen only in the
  smoke/full run step, foreground, with per-symbol timeout + try/except — a metadata
  miss leaves the row blank, never aborts the run.
- Invariants: n_jobs=2, float32 n/a (no features), no EVAL reads, no edits outside
  `write_files`. Consumer contract preserved: `load_sector_map` in
  `src/swing_bsh/binary_features_ext.py` must read the output unchanged (columns,
  MAX_SECTORS=12 tail-collapse semantics) — verify with an import-level test, do not
  edit the consumer (read-only).

## 2. I/O contract and blueprint (literal)
- Inputs: `config/sector_map.csv` (current, precedence winner), `IBKRDownload/sector_map.csv`,
  panel symbol inventory via `pyarrow.dataset`/glob over `data/raw_ohlcv/market=*/symbol=*.parquet`.
- Output: `config/sector_map.csv` (full universe, columns unchanged:
  symbol,market,sector,industry,sub_group,company_name,tc_rating),
  `data/sector_map_conflicts.csv`, report `reports/sector_map_consolidation.md`.
- `sector_map_consolidate.py`: `load_sources() -> (config_df, ibkr_df, panel_symbols)` |
  `consolidate(config_df, ibkr_df, panel_symbols, fill_rows) -> canonical_df` (pure, tested
  without network) | `fetch_missing_ibkr(symbols) -> fill_rows` (network, smoke only) |
  `main()` writes outputs + report (counts: per-market coverage before/after, conflicts
  count, remaining blanks).
- Report must state: coverage per market before/after, unresolved blanks count, and a
  WI-070 readiness line (all mapped symbols have a non-blank sector, or the residual
  named).
- Tests: precedence rule incl. blank-never-overwrites; coverage invariant (every panel
  symbol present in output); consumer-contract test (columns + dtype round-trip);
  conflicts file completeness. No network in pytest.

## 3. Definition of Done (binary)
- [ ] No edits outside `write_files`.
- [ ] `test_command` exits 0.
- [ ] `config/sector_map.csv` covers 100% of panel symbols with non-blank sector, or the
  residual list is named in the report.
- [ ] Report + conflicts CSV written; stdout ≤5 lines.

## 4. Telemetry footer (executor fills, ≤3 lines)
- **Attempts:** 3 verification runs, 2 fix rounds (distinct defects, one fix each — no repeated error) | **Commit:** PENDING (HEAD 97cd0e0; no commit made) | **Status:** DONE
- **Notes / error tail:** Module was wrong twice: (a) `pd.read_csv(dtype=str)` + default `na_values` coerced the *real* ticker `NA` (National Bank of Canada, CAD) to NaN, minting a phantom `nan,CAD,Banks` row and leaving `NA.CAD` blank → fixed by `na_filter=False` in a new `_read_map` (plus a `NAN`-symbol guard in `_clean`); (b) `CONSTITUENT_SOURCES` invented ETF sectors (WI-073 §1 "it does NOT invent sectors") and masked the planner's expected residual → removed, `__all__` updated. Tests were wrong three times: the consumer round-trip (read-only `load_sector_map` parses the literal ticker `NA` as NaN — impossible to key, so the residual is now named rather than asserted away), the `SMH` constituent expectation, and a no-gateway assertion that injected a stub instead of exercising the module's own connect site; also `network-fill attempts` → actual report wording `network gap-fill attempts`. `report_markdown` now takes `before_stats` (incumbent config measured before overwrite) instead of `root=`, so the before/after table is a real before. Known deviations: module is 346 lines (guardrail 250) — inherited at 337 from the killed run and unattainable without gutting the report builder/contract; `src/l2_overlay/INDEX.md` not updated because it is outside `write_files`.
- **Result:** `config/sector_map.csv` = 1072 rows, columns unchanged, **100 % panel coverage** (USD 674/674, CAD 394/394 mapped); non-blank after USD 631/674 (before 605) / CAD 378/394 (before 192); `data/sector_map_conflicts.csv` = 67 rows (config won; CAD 65 / USD 2); residual **59 blanks named** = USD 43 / CAD 16 (planner expected ~60 = USD 43 / CAD 17; USD exact, CAD one better because `NA.CAD` now reads `Banks` from IBKR). WI-070 readiness: **CONDITIONAL**. Offline gap-fill: gateway refused `127.0.0.1:4001`, 50 probes / 0 sectors, run not aborted (2 stderr warnings), `main --smoke` stdout 4 lines, re-run byte-identical (md5 `7eab0d4d…`), wall-clock ~5 s ≪ 0.01 core-h. `test_command` exit 0 (9 passed).
