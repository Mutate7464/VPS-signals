# L2 prepared CALIB panels (WI-prep) — generated 2026-11-15T03:47:12Z

Script: `scripts/build_l2_prepared.py`. CALIB only: rows with date < 2022-05-02 (EVAL 2022-07-01 never written).

## Sources

| source | size (bytes) |
| :--- | ---: |
| `data/models/wi048/manifest.parquet` | 31,337 |
| `reports/fib_swings/trade_labels_w39.parquet` | 4,671,863 |
| winner fold pickles (wi048, 3 cells x 2 markets x 5 folds) | 10,290,293 (30 files) |
| wi035 b_hold pickles (10; read for feature list only) | 5,690,096 |

## Winner cells (manifest-selected)

- `xsec_vol_rank_cont` -> xgboost h55 (confirmed by ic); `move_occur` -> xgboost h5 (confirmed by auc); `move_dir_up` -> xgboost h5 (confirmed by auc)
- Variant per market from manifest: USD `exact_full_k0.8`, CAD `tol2_full_k0.8`; 5 fold pickles per cell asserted.

## USD

- Panel source: rebuilt via targets_ext.build_targets_panel (cache /home/yycuser/.hermes/cache/scratch/l2_prep_cache); panel rows 117,025; features 47 (rho-pruned kept 44).
- screen_bottom trade-label keys 2,821; matched to panel 1,372; unmatched 1,449; universe rows without policy row 19.
- Output rows (date < CALIB_END): 837; fold counts {-1: 544, 0: 176, 1: 117}.
- Cells: xsec_vol_rank_cont: scored 73,310/114,305 finite-label; move_occur: scored 75,202/117,025 finite-label; move_dir_up: scored 75,202/117,025 finite-label.

| column | non-NaN | dtype |
| :--- | ---: | :--- |
| date | 837 | datetime64[ns] |
| symbol | 837 | str |
| fold | 837 | int64 |
| r | 837 | float32 |
| xsec_vol_rank_cont | 293 | float32 |
| move_occur | 291 | float32 |
| move_dir_up | 291 | float32 |
| p_b_hold | 0 | float32 |

r (gross): n=837 mean +0.0010 std 0.1498 q05 -0.1417 q25 -0.1000 q50 -0.0717 q75 +0.1500 q95 +0.1523

## CAD

- Panel source: rebuilt via targets_ext.build_targets_panel (cache /home/yycuser/.hermes/cache/scratch/l2_prep_cache); panel rows 64,166; features 47 (rho-pruned kept 44).
- screen_bottom trade-label keys 1,670; matched to panel 764; unmatched 906; universe rows without policy row 15.
- Output rows (date < CALIB_END): 508; fold counts {-1: 348, 0: 125, 1: 35}.
- Cells: xsec_vol_rank_cont: scored 40,201/62,612 finite-label; move_occur: scored 41,296/64,166 finite-label; move_dir_up: scored 41,296/64,166 finite-label.

| column | non-NaN | dtype |
| :--- | ---: | :--- |
| date | 508 | datetime64[ns] |
| symbol | 508 | str |
| fold | 508 | int64 |
| r | 508 | float32 |
| xsec_vol_rank_cont | 160 | float32 |
| move_occur | 157 | float32 |
| move_dir_up | 157 | float32 |
| p_b_hold | 0 | float32 |

r (gross): n=508 mean +0.0777 std 0.6550 q05 -0.1310 q25 -0.1000 q50 -0.0447 q75 +0.1500 q95 +0.1986

## Coverage gaps

- USD: p_b_hold ALL-NaN - 2/23 wi035 features not produced by the current pipeline (train.engineer + panel): ['k', 'horizon']. The grid's _design() sets k=1/horizon=21 as constants; substituting them would be a guessed score, so none was used. Fold definition for wi035 is also not reconstructed (no fold boundaries on disk).
- USD: 1449/2821 screen_bottom trade-label event keys have no at_bottom panel row: 810 predate the panel start (2015-05-26); 639 are in-range non-panel events (2 of all unmatched exist only as at_top rows). Not fabricated.
- CAD: p_b_hold ALL-NaN - 2/23 wi035 features not produced by the current pipeline (train.engineer + panel): ['k', 'horizon']. The grid's _design() sets k=1/horizon=21 as constants; substituting them would be a guessed score, so none was used. Fold definition for wi035 is also not reconstructed (no fold boundaries on disk).
- CAD: 906/1670 screen_bottom trade-label event keys have no at_bottom panel row: 523 predate the panel start (2015-05-26); 383 are in-range non-panel events (2 of all unmatched exist only as at_top rows). Not fabricated.

## Notes

- USD: wi048 cache lacks label keys [('move_dir_up', 'exact', 5), ('move_occur', 'exact', 5), ('xsec_vol_rank_cont', 'exact', 55)]; rebuilt panel+labels from source with the current targets_ext (cache -> /home/yycuser/.hermes/cache/scratch/l2_prep_cache).
- USD: wi035 b_hold feature list has 23 names (provenance; USD=23, CAD=24 per the on-disk pickles).
- USD: 535 universe rows dated >= CALIB_END were excluded from output.
- USD: xsec_vol_rank_cont is a raw regressor output (not bounded to [0,1]); r is NOT clipped (outliers kept as recorded, e.g. CAD max r ~7.0).
- USD: `fold` column = xsec_vol_rank_cont h55 fold assignment; move_occur / move_dir_up / xsec scores each come from their own cell's fold assignment (h5 vs h55 validation blocks can differ slightly), so a row's score may be from a different fold number than its `fold`.
- USD: 40995 finite-label panel rows carry fold=-1 for xsec h55 (outside all purged validation blocks, e.g. the first 40% of dates is train-only) - NaN by design, not backfilled.
- CAD: wi048 cache lacks label keys [('move_dir_up', 'tol2', 5), ('move_occur', 'tol2', 5), ('xsec_vol_rank_cont', 'tol2', 55)]; rebuilt panel+labels from source with the current targets_ext (cache -> /home/yycuser/.hermes/cache/scratch/l2_prep_cache).
- CAD: wi035 b_hold feature list has 24 names (provenance; USD=23, CAD=24 per the on-disk pickles).
- CAD: 256 universe rows dated >= CALIB_END were excluded from output.
- CAD: xsec_vol_rank_cont is a raw regressor output (not bounded to [0,1]); r is NOT clipped (outliers kept as recorded, e.g. CAD max r ~7.0).
- CAD: `fold` column = xsec_vol_rank_cont h55 fold assignment; move_occur / move_dir_up / xsec scores each come from their own cell's fold assignment (h5 vs h55 validation blocks can differ slightly), so a row's score may be from a different fold number than its `fold`.
- CAD: 22411 finite-label panel rows carry fold=-1 for xsec h55 (outside all purged validation blocks, e.g. the first 40% of dates is train-only) - NaN by design, not backfilled.
