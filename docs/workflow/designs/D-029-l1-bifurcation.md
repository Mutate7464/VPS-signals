# D-029 — L1 bifurcation: causal panel vs ex-post label namespaces

Source: `docs/plans/26-W47-visualizer-audit-workbench.md` (Track B rank 8, "L1-BIF design").
WI: `docs/kanban/in_progress/WI-080.md`. Admin-ratified scope 2026-11-19: code + tests + this
standalone design doc. `docs/workflow/DATA_CONTRACT.md` stays read-only; D-028 is the visualizer
design. License: D-023 layer 1 (predictive only) — nothing here computes a trading or economic
metric, and no BH-FDR family is defined (design + tests only; WI-081 carries its own prereg).

## Decision

Split the L1 namespace in two, and make the split executable rather than conventional:

1. **Causal panel (features).** Only bar `t`'s close and earlier. Trailing swing and retracement
   LEVELS are keyed by the **confirmation date** — the bar at which the level becomes known — never
   back-filled onto the pivot bar and never revised by a later bar.
2. **Ex-post label namespaces (labels only).** `fwd_*` (forward returns, forward realized vol),
   `y_*` / `label_*` / `target_*` (outcome labels), MFE/MAE, capture efficiency. These are label
   targets, never features and never exported as features.
3. **Model outputs.** `p_*` (probabilities) and `fold_*` (fold ids) are neither causal panel nor
   labels; they are also rejected as features. Keys/context (`symbol`, `date`, `market`, `close`,
   `atr`, `state`) are allowed in the panel.

## Boundary rule (normative)

| Namespace | Examples | Class | Rule |
|---|---|---|---|
| Trailing levels | `level_high`, `level_low`, `retrace_50` | causal feature | emitted at the confirmation bar; `t-window+1..t` only |
| Trailing statistics | `cusum_flag`, `kama_er_15`, `rvol_pctile_20d` | causal feature | bar `t` and earlier only |
| Forward returns / fwd-vol | `fwd_atr_ret_15`, `fwd_atr_ret_20`, `fwd_vol` | ex-post label | never a feature; never exported |
| Outcome labels | `y_20d_high`, `y_15d_low_down`, `label_*`, `target_*` | ex-post label | as above |
| Excursions / capture | `mfe`, `mae`, `mfe_mae_cont`, `capture_eff` | ex-post label | as above |
| Model outputs | `p_y_20d_high`, `fold_y_20d_high` | prediction artifact | not a feature |
| Keys / context | `symbol`, `date`, `market`, `close`, `atr`, `state` | allowed | keys or display context only |

Sign convention for the down-targets stays an open question (plan §Open questions); it does not
change this boundary.

## Confirmation-date semantics for levels

A trailing level at bar `t` is `max(high[t-w+1..t])` / `min(low[t-w+1..t])` and the retracement
level is `low + f·(high - low)` over the same window. Consequences enforced by the tests:

- The row date is the **confirmation date**; the level is not written back to the pivot bar. Rows
  `0..w-2` are NaN because no level is confirmed yet, even though a pivot exists inside them.
- Windows are NaN-propagating: a zero-width range yields NaN for the retracement column, not `0.0`.
- Levels are never revised by later bars (append invariance) and never cross a symbol boundary.
- Feature DataFrames are cast to `float32` immediately after calculation; the index is reset before
  concat across symbols (RISKS R-08). Reads stay symbol-sequential (`pyarrow.dataset` when a panel
  read is needed); `n_jobs=2`.

## Enforcement

`src/l1_bif/bif_boundary.py`

- `assert_boundary(panel_columns) -> list` — returns the validated causal column list, or raises
  `BoundaryViolation` (an `AssertionError`) naming every ex-post label / model-output column found.
  A contaminated panel therefore fails loudly instead of exporting a label as a feature.
- `is_expost_label`, `is_model_output`, `is_non_feature`, `label_only_columns` — the classification
  used by the assert and by downstream export validators.
- `trailing_level(panel, window=20, retrace=0.5)` — the causal confirmation-dated level builder.
- `to_float32`, `concat_frames` — the two repo invariants (`float32` cast, index reset pre-concat).

Tests: `tests/l1_bif/test_bif_boundary.py` (synthetic multi-ticker OHLCV). Covered: causality by
future-bar perturbation invariance, append non-revision, no symbol crossing, float32 dtypes,
NaN window edges, confirmation-date (non-backfilled) values, boundary rejection of ex-post and
model-output columns, index reset before concat.

## Consequences for later cards

- **WI-081 (L1-SWING trailing features)** may emit swing/retracement level features but must date
  them at confirmation and must pass `assert_boundary` on its output column list. Its own prereg
  defines its BH-FDR family (G1).
- **L1 eval / L1 pickle library (D-023 layer 1)** consumes only columns that pass `assert_boundary`;
  `fwd_*`, `y_*`, MFE/MAE, capture efficiency and fwd-vol remain label-side and are never used as
  predictors. No economic metric is reported at this layer.
- **Visualizer export (WI-090, EXPORT_CONTRACT.md)** keeps its own wider ban list (`close`, `atr`,
  `state` are keys only). This doc does not change that contract; the two checks are compatible.
- **L2 (barrier engine, `src/l2_tb/`)** may *consume* label-side fields; that is layer 2 and carries
  its own split because the L2 EVAL split is spent.

## Out of scope / open questions

- No data artifact, no feature build, no evaluation job in this card.
- `_pl0/_pl1/_pl2` barrier-variant semantics and the `y_*` value set are still open (plan §Open
  questions); the boundary treats them as label-side opaque names, recorded rather than hard-coded.
- EV / cost analysis, threshold sweeps and any economic magnitude belong to layer 2 only.
