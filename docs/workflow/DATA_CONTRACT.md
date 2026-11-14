# DATA_CONTRACT.md — disk reference (read on demand, never per task)

> Maximum ~250 tokens of facts per section. Schemas below come from metadata-only probes on 2026-11-07 (`pyarrow.parquet.read_schema`). Re-probe before relying on any row marked *not probed*.

## 1. Raw OHLCV (input)
- **Path:** `data/raw_ohlcv/market=<USD|CAD>/symbol=<TICKER>.parquet`
- **Key:** `symbol` comes from the filename (strip the `symbol=` prefix). Never use the full stem as a join key.
- **Schema (probed USD, `symbol=A.parquet`):** `date date32[day]`, `open float`, `high float`, `low float`, `close float`, `volume float`, `average float`, `barCount int64` (8 columns).
- **Counts:** USD 674 files. CAD count *not probed*.

## 2. OOF predictions (model output)
- **Path pattern:** `data/oof_<MKT>[_variant].parquet` (USD variants present: `fib_only`, `cs_pct_only`, `no_static`, `legacy19`).
- **Probed (`data/oof_USD_fib_only.parquet`):** 41 columns.
  - `date timestamp[ns]`, `symbol dictionary<string>`, `close float`
  - Forward returns (targets, never features): `fwd_atr_ret_15`, `fwd_atr_ret_20` (float)
  - Touch labels: `y_<target>` int8, e.g. `y_y_15d_high`
  - Probabilities: `p_<target>` float; fold id: `fold_<target>` int16
  - Barrier variants: `_pl0`, `_pl1`, `_pl2` suffixes on the same pattern

## 3. Invariants (every WI)
- Cast feature DataFrames to `float32` right after calculation.
- `n_jobs=2` (never -1). Symbol-sequential or `pyarrow.dataset` reads. No all-ticker uncompressed frame.
- No lookahead: `fwd_*` and `y_*` are labels, never features. Purged walk-forward, embargo 20d (RISKS R-01).
- Index alignment: reset the index after filtering before concat (RISKS R-08).
- Stdout ≤5 lines for executor runs. Suppress progress bars.

## 4. Dry-run subset
- Every WI names one of: a ≤10-symbol file list, or an env filter (for example `FIB_SMOKE=<tickers>`) with a `--out /tmp/<wi>_smoke` prefix.
- Smoke output must never overwrite frozen report names.

## 5. Output destinations
- Reports: `reports/<topic>/` (frozen once gated). Re-runs go to a validation prefix first.
- Models: `data/models/`. Predictions: `data/predictions_<MKT>_*_latest.parquet`.
