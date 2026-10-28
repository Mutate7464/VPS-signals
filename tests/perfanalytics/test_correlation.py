"""WI-015 step 4 — held-out alignment matrix tests."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.perfanalytics.correlation import alignment as align
from src.perfanalytics.features.panel import build_feature_panel, feature_columns
from src.perfanalytics.targets import build_run_targets
from src.xgb_trainer import PurgedWalkForwardSplit


def _raw(n: int = 400, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    close = 100.0 * np.cumprod(1.0 + rng.normal(0.0005, 0.02, n))
    high = close * (1.0 + np.abs(rng.normal(0.005, 0.003, n)))
    low = close * (1.0 - np.abs(rng.normal(0.005, 0.003, n)))
    return pd.DataFrame(
        {
            "date": pd.date_range("2020-01-01", periods=n, freq="B"),
            "open": close,
            "high": np.maximum(high, close),
            "low": np.minimum(low, close),
            "close": close,
            "volume": rng.uniform(5e5, 5e6, n),
        }
    )


N_SYMBOLS = 8


def _source():
    return [(f"S{i}", _raw(seed=i)) for i in range(N_SYMBOLS)]


@pytest.fixture()
def built(tmp_path):
    build_run_targets("CAD", out_dir=tmp_path, symbol_iter=_source())
    build_feature_panel("CAD", out_dir=tmp_path, symbol_iter=_source(), reports_dir=tmp_path / "rep")
    return tmp_path


def _run(built):
    return align.run_alignment(
        "CAD", data_root=built, reports_dir=built / "rep", symbol_factory=_source
    )


def test_fold_val_blocks_match_e5_split_and_are_disjoint():
    dates = np.sort(pd.date_range("2020-01-01", periods=400, freq="B").to_numpy())
    folds = align.fold_val_positions(dates)
    assert len(folds) == align.N_SPLITS
    flat = np.concatenate(folds)
    assert len(flat) == len(np.unique(flat))  # disjoint held-out blocks
    assert flat.max() == len(dates) - 1  # ends on the last date
    # the embargo invariant the split promises: no train date within embargo
    for train_idx, val_idx in PurgedWalkForwardSplit(
        n_splits=align.N_SPLITS, embargo_td=align.EMBARGO_TD
    ).split(dates):
        assert train_idx.max() + align.EMBARGO_TD < val_idx.min()


def test_block_bootstrap_margin_is_deterministic_and_zero_for_constant():
    ic = np.linspace(-0.05, 0.05, 200)
    a = align.block_bootstrap_margin(ic)
    b = align.block_bootstrap_margin(ic)
    assert a == b and np.isfinite(a) and a > 0
    assert align.block_bootstrap_margin(np.full(200, 0.03)) == 0.0
    assert np.isnan(align.block_bootstrap_margin(np.array([0.1])))


def test_alignment_matrix_schema_and_coverage(built):
    table, meta = _run(built)
    assert set(table.columns) == {
        "target", "horizon", "family", "window", "column", "held_out_ic", "n_dates",
        "noise_margin", "baseline_factor", "baseline_ic", "sign_match", "pass",
    }
    cells = set(zip(table["target"], table["horizon"]))
    assert cells == {(f"T{t}@{k}", k) for t in (1, 2, 3, 4) for k in (15, 20)}
    assert len(table) == 8 * len(feature_columns())
    # Features that are all-NaN for this universe (estimator/pipeline floors at the
    # longest windows) score no held-out dates; every computable one must.
    sample = pd.read_parquet(built / "features_CAD" / "symbol=S0.parquet")
    absent_cols = {c for c in feature_columns() if sample[c].isna().all()}
    assert {"hurst_3", "hurst_5", "hurst_8"} <= absent_cols
    absent = table[table["column"].isin(absent_cols)]
    assert len(absent) == len(absent_cols) * 8
    assert (absent["n_dates"] == 0).all() and absent["held_out_ic"].isna().all()
    present = table[~table["column"].isin(absent_cols)]
    assert (present["n_dates"] > 0).all()
    assert np.isfinite(present["noise_margin"]).all()
    # E5 factors are the baseline, never candidates
    assert not table["column"].str.startswith("e5_").any()
    assert table["baseline_factor"].notna().all()


def test_no_in_sample_result_is_reported_as_held_out(built):
    table, meta = _run(built)
    dates = np.sort(
        np.unique(
            np.concatenate(
                [pd.read_parquet(p, columns=["date"])["date"].to_numpy()
                 for p in (built / "run_targets_CAD").glob("symbol=*.parquet")]
            )
        )
    )
    folds = align.fold_val_positions(dates)
    n_held_out = sum(len(f) for f in folds)
    assert (table["n_dates"] <= n_held_out).all()
    # reported blocks name exactly the held-out validation ranges
    assert meta["fold_date_blocks"][-1][1] == str(pd.Timestamp(dates[-1]).date())
    assert meta["n_splits"] == 5 and meta["embargo_td"] == 20


def test_pass_requires_sign_match(built):
    table, _ = _run(built)
    assert not table.loc[~table["sign_match"], "pass"].any()
    # the bar must be a real one: a sign-matched cell only passes above its margin
    matched = table[table["sign_match"]]
    assert (matched.loc[matched["pass"], "held_out_ic"].abs()
            > matched.loc[matched["pass"], "noise_margin"]).all()


def test_alignment_is_reproducible(built):
    t1, m1 = _run(built)
    t2, m2 = _run(built)
    pd.testing.assert_frame_equal(t1, t2)
    assert m1["fold_date_blocks"] == m2["fold_date_blocks"]


def test_reports_written(built):
    _run(built)
    csv = built / "rep" / "alignment_CAD.csv"
    md = built / "rep" / "alignment_CAD.md"
    js = built / "rep" / "alignment_CAD.json"
    assert csv.exists() and md.exists() and js.exists()
    assert "Best family×window per target × horizon" in md.read_text()
    assert len(pd.read_csv(csv)) == 8 * len(feature_columns())


def test_cli_rejects_invalid_market(capsys):
    assert align.main(["--market", "XYZ"]) == 2
    assert "invalid market" in capsys.readouterr().err
