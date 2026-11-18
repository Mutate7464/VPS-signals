"""WI-072 — b_hold OOF rebuild tests (D-027 §6): the 23-name provenance schema, the derivation of the
grid constants / engineered column the prepared panel does not carry, loud failures instead of a
fabricated score, and a smoke run that writes finite float32 `1 − P(hold)` scores. Synthetic only:
no `data/` panel reads (the one provenance test reads the frozen WI-035 pickle, and skips without it).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.l2_overlay import harness as H
from src.l2_overlay.constructions import b_hold_scores as bs

# The WI-035 USD provenance list, pinned literally: a silent schema edit would invalidate every score.
PROVENANCE_23 = ("adx_3", "adx_21", "adx_144", "di_spread_3", "di_spread_144", "atr_pct_3", "amihud_3",
                 "donchian_break_144", "kama_er_3", "kama_er_15", "hurst_9", "hurst_15", "hurst_24",
                 "hurst_39", "hurst_63", "entropy_9", "entropy_24", "entropy_102",
                 "range_compression_8_55", "range_compression_21_144", "state_is_bottom", "k", "horizon")


def _fixture(n_dates=40, n_names=12, seed=3, market="USD"):
    return bs.synthetic_fixture(market, n_dates=n_dates, n_names=n_names, seed=seed)


def test_smoke_feature_schema_is_the_23_provenance_names():
    assert bs.SMOKE_FEATURES == PROVENANCE_23 and len(bs.SMOKE_FEATURES) == 23
    fx = _fixture(n_dates=3, n_names=4)
    assert set(bs.SMOKE_FEATURES) <= set(fx.columns)              # the fixture carries the full schema
    assert {"date", "symbol", "state", "fold"} <= set(fx.columns)  # plus the prepared-panel keys


def test_design_matrix_derives_the_grid_constants_and_the_engineered_column():
    """The prepared panel has no `k`/`horizon`/`state_is_bottom`: that gap is what this rebuild closes."""
    fx = _fixture(n_dates=4, n_names=5)
    panel = fx.drop(columns=["k", "horizon", "state_is_bottom"])
    X = bs.design_matrix(panel, bs.SMOKE_FEATURES)
    assert X.dtype == np.float32 and X.shape == (len(panel), 23)
    assert np.all(X[:, bs.SMOKE_FEATURES.index("k")] == np.float32(1.0))
    assert np.all(X[:, bs.SMOKE_FEATURES.index("horizon")] == np.float32(21.0))
    assert np.array_equal(X[:, bs.SMOKE_FEATURES.index("state_is_bottom")],
                          (panel["state"].to_numpy() == "at_bottom").astype("float32"))
    assert np.array_equal(X[:, 0], panel["adx_3"].to_numpy("float32"))   # provenance order, not panel order


def test_missing_feature_is_a_defect_not_a_fabricated_score():
    panel = _fixture(n_dates=3, n_names=4).drop(columns=["hurst_39"])
    with pytest.raises(KeyError, match="not produced by the panel/pipeline"):
        bs.design_matrix(panel, bs.SMOKE_FEATURES)


def test_prepared_row_without_a_panel_row_is_a_defect():
    fx = _fixture(n_dates=3, n_names=4)
    panel = fx.iloc[1:].reset_index(drop=True)                    # one prepared key loses its panel row
    with pytest.raises(KeyError, match="have no feature-panel row"):
        bs.align_rows(panel, fx)
    assert np.array_equal(bs.align_rows(fx, fx), np.arange(len(fx)))
    with pytest.raises(FileNotFoundError, match="full run is a PM gate"):
        bs.read_prepared("USD", prepared_root="/tmp/wi072_no_such_prepared_root")


def test_score_oof_requires_a_pickle_for_every_fold_with_rows():
    X = _fixture(n_dates=2, n_names=3)
    X = bs.design_matrix(X, bs.SMOKE_FEATURES)
    model = bs.smoke_models()[0]
    with pytest.raises(ValueError, match="no b_hold OOF score"):
        bs.score_oof(X, np.array([0, 1, 0, 1, 0, 1]), {0: model})   # fold 1 has rows but no pickle
    out = bs.score_oof(X, np.array([0, -1, 0, -1, 0, -1]), {0: model})
    assert np.isfinite(out[[0, 2, 4]]).all() and np.isnan(out[[1, 3, 5]]).all()   # fold -1 = NaNs


def test_eval_rows_never_reach_the_calib_only_structure():
    fx = _fixture(n_dates=4, n_names=4)
    assert bs.assert_calib_only(fx["date"]) == len(fx)
    ev = fx.copy()
    ev.loc[ev.index[-1], "date"] = pd.Timestamp(H.EVAL_START)
    with pytest.raises(bs.EvalLeak, match="reached a CALIB-only structure"):
        bs.assert_calib_only(ev["date"])
    with pytest.raises(bs.EvalLeak):
        bs.build_scores("USD", ev, ev, bs.smoke_models(), bs.SMOKE_FEATURES)


def test_smoke_run_writes_finite_float32_scores(tmp_path):
    fx = _fixture()
    res = bs.run_market("USD", fx, fx, score_root=tmp_path / "scores",
                        report_root=tmp_path / "reports", smoke=True)
    frame = pd.read_parquet(res["artifact"])
    assert res["artifact"].exists() and res["manifest"].exists() and res["report"].exists()
    assert list(frame.columns) == list(bs.OUT_COLUMNS) and len(frame) == len(fx)
    for col in ("p_b_hold", "b_hold"):
        assert frame[col].dtype == np.float32 and np.isfinite(frame[col].to_numpy()).all()
    p = frame["p_b_hold"].to_numpy("float64")
    assert ((p >= 0.0) & (p <= 1.0)).all()
    assert np.allclose(frame["b_hold"], 1.0 - frame["p_b_hold"], atol=1e-6)
    assert frame["b_hold"].nunique() > 5                          # scores vary with the features
    assert float(np.corrcoef(frame["b_hold"], fx["adx_3"])[0, 1]) > 0.4   # planted, not constant
    assert set(frame["fold"].unique()) == set(range(bs.N_SPLITS))
    assert res["stats"]["n_scored"] == res["stats"]["n_rows"] == len(fx)
    text = res["report"].read_text()
    for token in ("WI-035", "CALIB only", "Fold counts", "Record-only"):
        assert token in text


@pytest.mark.skipif(not (bs.WI035_DIR / "USD_hist_gbm_b_hold_f0.pkl").exists(),
                    reason="frozen WI-035 b_hold pickles not on this host")
def test_provenance_reproduces_the_smoke_schema():
    """Ground truth for PROVENANCE_23: the pickles' own feature list (read-only, frozen artifact)."""
    assert set(bs.feature_list("USD")) == set(bs.SMOKE_FEATURES)
    assert sorted(bs.pickle_paths("USD")) == list(range(bs.N_SPLITS))
