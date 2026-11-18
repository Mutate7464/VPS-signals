"""WI-064 — synthetic tests for the L1.5 meta-label OOF driver (D-027 Phase 1).

No market data: a synthetic panel proves (a) the OOF is purged-CV only (each fold's fit
block ends before its validation block starts; fold ids are monotone in date), (b) no
EVAL-period row is ever read or written, and (c) the output schema/dtypes and the
manifest contract are exact.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest

from src.l2_overlay.drivers import meta_label_full as driver

N_DATES, N_SYMBOLS, N_EVAL_DATES, N_FEATURES = 260, 4, 40, 7
EVAL_SYMBOL = "ZM_EVAL_ONLY"


def _synthetic() -> tuple[pd.DataFrame, np.ndarray]:
    """CALIB rows (all symbols) + EVAL-only rows carrying a sentinel symbol."""
    rng = np.random.default_rng(7)
    calib = pd.bdate_range(end="2022-06-28", periods=N_DATES)
    eval_dates = pd.bdate_range(start="2022-07-05", periods=N_EVAL_DATES)
    rows, feats = [], []
    for i, date in enumerate(calib):
        for s in range(N_SYMBOLS):
            state = "at_bottom" if (i + s) % 2 == 0 else "at_top"
            ret = float(rng.normal(0.003, 0.02))
            rows.append({"symbol": f"SYM{s}", "date": date, "state": state, "r_frozen": ret})
            feats.append(rng.normal(size=N_FEATURES))
    for date in eval_dates:                      # must never reach the artifact
        rows.append({"symbol": EVAL_SYMBOL, "date": date, "state": "at_bottom", "r_frozen": 0.9})
        feats.append(np.zeros(N_FEATURES))
    frame = pd.DataFrame(rows).sort_values(["date", "symbol"], kind="mergesort").reset_index(drop=True)
    return frame, np.asarray(feats, dtype="float32")


def _oof(n_splits: int = 4) -> dict:
    frame, X = _synthetic()
    return driver.run_oof(frame, X, n_splits=n_splits)


def test_oof_is_purged_cv_only():
    res = _oof()
    oof = res["oof"]
    assert not oof.empty and res["n_scored"] == len(oof)
    assert res["primary_oof_as_feature"] is False
    assert set(oof["fold"]).issubset(set(range(4)))
    by_date = oof.groupby("date")["fold"].nunique()
    assert int(by_date.max()) == 1                       # one fold per date, no re-shuffle
    ordered = oof.sort_values("date")
    assert ordered["fold"].is_monotonic_increasing        # walk-forward, earlier folds first
    scored = [f for f in res["folds"] if "n_train" in f]
    assert scored and all(f["max_train_idx"] < f["min_val_idx"] for f in scored)
    assert all("skipped" in f or f["n_train"] >= 30 for f in res["folds"])


def test_no_eval_row_is_read_or_written():
    res = _oof()
    oof = res["oof"]
    assert pd.Timestamp(oof["date"].max()) < pd.Timestamp(driver.EVAL_START)
    assert EVAL_SYMBOL not in set(oof["symbol"])
    assert res["n_calib_rows"] == N_DATES * N_SYMBOLS
    assert res["n_calib_rows"] < len(_synthetic()[0])


def test_output_schema_and_manifest_are_exact(tmp_path):
    res = _oof()
    path, mpath = driver.write_outputs(tmp_path, "CAD", res, {"inputs": {"baseline": {"path": "x"}}})
    assert path.name == "CAD_oof.parquet" and path.exists()
    df = pd.read_parquet(path)
    assert list(df.columns) == list(driver.OOF_COLUMNS) == ["date", "symbol", "p_oof", "fold"]
    assert str(df["p_oof"].dtype) == "float32"
    assert str(df["date"].dtype).startswith("datetime64")
    assert str(df["fold"].dtype) == "int16"
    assert str(df["symbol"].dtype) in ("object", "str")   # pandas 3 reads arrow strings as `str`
    assert all(isinstance(s, str) for s in df["symbol"])
    assert int(df["fold"].min()) >= 0
    assert bool(df["p_oof"].between(0.0, 1.0).all()) and df["p_oof"].notna().all()
    man = json.loads(mpath.read_text())
    assert man["oof_parquet"] == "CAD_oof.parquet" and man["market"] == "CAD"
    assert man["n_rows"] == len(df) and man["eval_locked"] is True
    assert man["folds"] and man["inputs"]["baseline"]["path"] == "x"
    assert len(man["oof_sha256"]) == 64


def test_roots_are_named_constants_and_never_the_same_shape(tmp_path):
    assert driver.SMOKE_ROOT != driver.OOF_ROOT
    assert driver.OOF_ROOT.name == "l2_meta_oof" and driver.SMOKE_ROOT.name == "l2_meta_oof_smoke"
    assert driver.OOF_ROOT.parent.name == "models"


def test_load_baseline_normalises_and_validates(tmp_path):
    src = tmp_path / "pm_baseline.parquet"
    pd.DataFrame({"symbol": ["AAA", "BBB", "CCC"], "date": pd.to_datetime(["2020-01-02"] * 3),
                  "r_frozen": [0.01, np.nan, -0.02], "extra": 1}).to_parquet(src, index=False)
    frame, path = driver.load_baseline("CAD", src)
    assert path == src and len(frame) == 2 and frame["symbol"].tolist() == ["AAA", "CCC"]
    assert str(frame["r_frozen"].dtype) == "float64"
    pd.DataFrame({"symbol": ["AAA"], "date": pd.to_datetime(["2020-01-02"])}).to_parquet(
        tmp_path / "bad.parquet", index=False)
    with pytest.raises(KeyError):
        driver.load_baseline("CAD", tmp_path / "bad.parquet")
    with pytest.raises(FileNotFoundError):
        driver.load_baseline("CAD", tmp_path / "missing.parquet")
