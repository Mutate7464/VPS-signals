# Visualizer / audit workbench (Track A, Phase 0 — WI-085)

Read-only Dash + Plotly workbench over the artifacts in `data/`. It displays evidence and
computes no verdicts. Every KPI carries the watermark
"evidence only - no verdicts; out-of-fold, but threshold-selection bias risk".

## Run

```bash
bash tools/visualizer/serve.sh          # gunicorn --workers 1 --threads 2 on 127.0.0.1:8050
# from your laptop:
ssh -N -L 8050:127.0.0.1:8050 <vps>
```

`VIZ_HOST` / `VIZ_PORT` override the bind address. `debug=False`; there is no
`dcc.Interval`, so an idle process sleeps instead of polling (measured <1% CPU over 10 min).

## Measured artifact contracts (2026-11-19 metadata probes)

| Artifact | Measured on disk |
|---|---|
| `data/features/features_{USD,CAD}.parquet` | 1,240,275 / 701,599 rows; **92 columns = 89 float32 + `date` (timestamp[ns]), `symbol`, `market`** |
| `data/features/targets_{MKT}.parquet` | same row counts; 8 columns (`market`, `y_20d_stay`, `y_15d_high/low`, `y_20d_up/down`) |
| `data/oof_{MKT}[_variant].parquet` | canonical **41 columns**; `oof_CAD.parquet` is an extended 57-column variant (`_pl3/_pl4` extras, 1,400 rows) |
| `data/features/l0_ext/{feature}_{MKT}.parquet` | 2,593,425 / 1,401,504 rows; keys (`symbol` string, `date` date32); full universe, so a superset of the panel |
| `data/raw_ohlcv/market={MKT}/symbol={T}.parquet` | `date` date32 + 7 columns; dates strictly monotonic |

Deviations from the plan/D-028, recorded as evidence:

1. **92 feature columns, not 249.** The plan assumed a 249-column panel; the real file has
   92 (89 float32 + 3 keys). The frozen contract asserts the measured set, and the tests
   assert the width is *not* 249.
2. **Panel `date` is `timestamp[ns]`, not `date32`.** `date32` holds for `raw_ohlcv` and
   `l0_ext`; the loader casts `l0_ext.date` to `timestamp[ns]` before the join.
3. **`oof_CAD.parquet` is not the canonical 41-column form.** Extras are accepted only when
   they match `^(y|p|fold)_.*_pl\d+$` and are recorded in the schema report, never dropped.
4. **l0_ext covers the full universe**, so the (symbol, date) join is left-biased onto the
   panel: 1,353,150 USD / 699,905 CAD l0_ext rows fall outside the panel and
   `unmatched_panel_rows == 0`. The join reports both counts as evidence.

`y_*` value sets, `p_*` ranges and fold dtypes are recorded from the artifact (they are not
hard-coded); the `_pl0/1/2` semantics remain an open question (D-028).

## Memory and I/O rules

- Every panel read is a projection: `pq.read_table(path, columns=[keys + requested])`.
  The full panel is never materialised by the UI process.
- A byte ledger costs each load as `rows × cols × 4` **before** it happens and refuses
  requests above the 3.0 GB resident budget (`DataBudgetError` -> UI message).
- LRU caches: 64 column sets (keyed by source/market/variant/projection) and 32 OHLCV
  symbols. Eviction releases the ledger bytes.
- Raw OHLCV is read one symbol file at a time; no dataset is opened over `raw_ohlcv/`.
- The process writes **only** under `state/viz/` (`bench.json`, `manifest.json`, later
  `join_{MKT}.parquet`, `exports/`). `data/` is opened read-only. `n_jobs=2` applies to
  precompute jobs, which are separate processes (Phase 2).

## Phase-0 benchmark

```bash
uv run python -m src.visualizer.loader --bench
```

Writes `state/viz/bench.json` (row counts, peak RSS, filter latency, ledger/cache stats,
schema summary) and `state/viz/manifest.json` ((path, size, mtime) fingerprints plus
metadata-only row/column counts for later cache invalidation).

### Idle-CPU evidence (measured 2026-11-19, 600 s)

`serve.sh` was started, one render was fetched (`/` -> 200; `/_dash-layout` contains the
watermark and no Interval component), then the gunicorn process tree was sampled with
psutil for 600 s: **0.210 cpu-s over 600 s = 0.035 % of one core** (0.018 % of the 2-vCPU
host) — under the 1 % idle budget. The result is recorded in `state/viz/bench.json` under
`idle_cpu` (duration, cpu-seconds, percentages, HTTP status, watermark/interval flags).

## Tests

```bash
uv run pytest tests/visualizer -q --tb=short --maxfail=1
```

`test_schema.py` asserts the measured contracts on the real artifacts and includes negative
drift tests; `test_loader_budget.py` covers ledger refusal, projection discipline and the LRU
caps; `test_readonly.py` proves a loader session touches nothing outside `state/viz/` and
locks the operating rules (`debug=False`, no `dcc.Interval`, 1 worker / 2 threads, 127.0.0.1).
