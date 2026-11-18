# L2 prepared CALIB panels (WI-prep) — generated 2026-11-15T16:57:01Z

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
- screen_bottom trade-label keys 2,821; matched to panel 1,372; unmatched 1,449; universe rows without policy row 0.
- Output rows (date < CALIB_END): 62,782; fold counts {-1: 38697, 0: 12484, 1: 11601}.
- Cells: xsec_vol_rank_cont: scored 73,310/114,305 finite-label; move_occur: scored 75,202/117,025 finite-label; move_dir_up: scored 75,202/117,025 finite-label.

| column | non-NaN | dtype |
| :--- | ---: | :--- |
| date | 62,782 | datetime64[ns] |
| symbol | 62,782 | str |
| fold | 62,782 | int64 |
| r | 62,782 | float32 |
| xsec_vol_rank_cont | 24,085 | float32 |
| move_occur | 23,274 | float32 |
| move_dir_up | 23,274 | float32 |
| p_b_hold | 0 | float32 |

r (gross): n=62,782 mean +0.0062 std 0.0773 q05 -0.0591 q25 -0.0500 q50 -0.0500 q75 +0.1000 q95 +0.1010

## CAD

- Panel source: rebuilt via targets_ext.build_targets_panel (cache /home/yycuser/.hermes/cache/scratch/l2_prep_cache); panel rows 64,166; features 47 (rho-pruned kept 44).
- screen_bottom trade-label keys 1,670; matched to panel 764; unmatched 906; universe rows without policy row 0.
- Output rows (date < CALIB_END): 22,289; fold counts {-1: 13685, 0: 4456, 1: 4148}.
- Cells: xsec_vol_rank_cont: scored 40,201/62,612 finite-label; move_occur: scored 41,296/64,166 finite-label; move_dir_up: scored 41,296/64,166 finite-label.

| column | non-NaN | dtype |
| :--- | ---: | :--- |
| date | 22,289 | datetime64[ns] |
| symbol | 22,289 | str |
| fold | 22,289 | int64 |
| r | 22,289 | float32 |
| xsec_vol_rank_cont | 8,604 | float32 |
| move_occur | 8,309 | float32 |
| move_dir_up | 8,309 | float32 |
| p_b_hold | 0 | float32 |

r (gross): n=22,289 mean +0.0083 std 0.1732 q05 -0.0570 q25 -0.0500 q50 -0.0500 q75 +0.1000 q95 +0.1000

## Coverage gaps

- USD: p_b_hold ALL-NaN - 2/23 wi035 features not produced by the current pipeline (train.engineer + panel): ['k', 'horizon']. The grid's _design() sets k=1/horizon=21 as constants; substituting them would be a guessed score, so none was used. Fold definition for wi035 is also not reconstructed (no fold boundaries on disk).
- USD: 1449/2821 screen_bottom trade-label event keys have no at_bottom panel row: 810 predate the panel start (2015-05-26); 639 are in-range non-panel events (2 of all unmatched exist only as at_top rows). Not fabricated.
- CAD: p_b_hold ALL-NaN - 2/23 wi035 features not produced by the current pipeline (train.engineer + panel): ['k', 'horizon']. The grid's _design() sets k=1/horizon=21 as constants; substituting them would be a guessed score, so none was used. Fold definition for wi035 is also not reconstructed (no fold boundaries on disk).
- CAD: 906/1670 screen_bottom trade-label event keys have no at_bottom panel row: 523 predate the panel start (2015-05-26); 383 are in-range non-panel events (2 of all unmatched exist only as at_top rows). Not fabricated.

## Notes

- USD: wi048 cache lacks label keys [('move_dir_up', 'exact', 5), ('move_occur', 'exact', 5), ('xsec_vol_rank_cont', 'exact', 55)]; rebuilt panel+labels from source with the current targets_ext (cache -> /home/yycuser/.hermes/cache/scratch/l2_prep_cache).
- USD: wi035 b_hold feature list has 23 names (provenance; USD=23, CAD=24 per the on-disk pickles).
- USD: 42 (symbol, date) rows carry both states; first kept, rest dropped.
- USD: universe amendment — all swing events on quorum dates (>=20 candidates): 62,782/66,054 CALIB rows kept, 239 thin dates dropped, 1508 quorum dates.
- USD: fib sim over 674 OHLC symbols (2,539,401 bars); 0 event dates not found in OHLC -> r NaN.
- USD: xsec_vol_rank_cont is a raw regressor output (not bounded to [0,1]); r is NOT clipped (outliers kept as recorded, e.g. CAD max r ~7.0).
- USD: `fold` column = xsec_vol_rank_cont h55 fold assignment; move_occur / move_dir_up / xsec scores each come from their own cell's fold assignment (h5 vs h55 validation blocks can differ slightly), so a row's score may be from a different fold number than its `fold`.
- USD: 40995 finite-label panel rows carry fold=-1 for xsec h55 (outside all purged validation blocks, e.g. the first 40% of dates is train-only) - NaN by design, not backfilled.
- CAD: wi048 cache lacks label keys [('move_dir_up', 'tol2', 5), ('move_occur', 'tol2', 5), ('xsec_vol_rank_cont', 'tol2', 55)]; rebuilt panel+labels from source with the current targets_ext (cache -> /home/yycuser/.hermes/cache/scratch/l2_prep_cache).
- CAD: wi035 b_hold feature list has 24 names (provenance; USD=23, CAD=24 per the on-disk pickles).
- CAD: 59 (symbol, date) rows carry both states; first kept, rest dropped.
- CAD: universe amendment — all swing events on quorum dates (>=20 candidates): 22,289/35,453 CALIB rows kept, 937 thin dates dropped, 803 quorum dates.
- CAD: fib sim over 394 OHLC symbols (1,362,968 bars); 0 event dates not found in OHLC -> r NaN.
- CAD: xsec_vol_rank_cont is a raw regressor output (not bounded to [0,1]); r is NOT clipped (outliers kept as recorded, e.g. CAD max r ~7.0).
- CAD: `fold` column = xsec_vol_rank_cont h55 fold assignment; move_occur / move_dir_up / xsec scores each come from their own cell's fold assignment (h5 vs h55 validation blocks can differ slightly), so a row's score may be from a different fold number than its `fold`.
- CAD: 22411 finite-label panel rows carry fold=-1 for xsec h55 (outside all purged validation blocks, e.g. the first 40% of dates is train-only) - NaN by design, not backfilled.
