"""WI-054 — L0-3 regime age / run-length block (D-026 sprint).

Synthetic only: no reads under `data/` or `reports/`. Verify:
`uv run pytest tests/test_l0_regime_age.py -q`
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.swing_bsh import binary_features_ext as bei

WIN = bei.REGIME_WIN
NEW_COLUMNS = ("regime_age_vol", "regime_prev_dur_vol", "regime_age_hurst")


def _frame(atr_pct=None, hurst=None, **extra) -> pd.DataFrame:
    n = len(atr_pct if atr_pct is not None else hurst)
    cols: dict[str, np.ndarray] = dict(extra)
    cols["atr_pct_21"] = np.full(n, np.nan) if atr_pct is None else atr_pct
    cols["hurst_63"] = np.full(n, np.nan) if hurst is None else hurst
    return pd.DataFrame(cols)


def _block(idx, atr_pct, hurst=None, **extra):
    n = len(atr_pct)
    h = np.full(n, np.nan) if hurst is None else hurst
    return bei._regime_age(_frame(atr_pct=np.asarray(atr_pct, "float64"),
                                  hurst=np.asarray(h, "float64"), **extra),
                           np.asarray(idx, dtype=np.int64))


def _flip_series() -> np.ndarray:
    """Low 0..299 (0.02), high 300..349 (0.10), low 350..560 (0.02)."""
    return np.concatenate([np.full(300, 0.02), np.full(50, 0.10), np.full(211, 0.02)])


# --------------------------------------------------------------------------- #
# Known regime flips -> expected run lengths
# --------------------------------------------------------------------------- #
def test_known_flips_give_expected_run_lengths():
    out = _block([232, 233, 249, 305, 349, 350, 400], _flip_series())
    age = out["regime_age_vol"].to_numpy()
    prev = out["regime_prev_dur_vol"].to_numpy()
    assert age.tolist() == [0, 1, 17, 5, 49, 0, 50]      # 0 = flip bar itself
    assert np.isnan(prev[:3]).all()                      # no flip yet
    assert prev[3:].tolist() == [68.0, 68.0, 50.0, 50.0]  # run start = bar 232


def test_warmup_rows_are_nan_and_first_defined_bar_is_zero():
    out = _block([0, 100, WIN - 2, WIN - 1, WIN + 5], _flip_series())
    assert out.iloc[:3].isna().all().all()
    assert out.iloc[3]["regime_age_vol"] == 0.0          # first bar with a median
    assert out.iloc[4]["regime_age_vol"] == 6.0


# --------------------------------------------------------------------------- #
# Monotone series -> monotonically increasing age, state never flips
# --------------------------------------------------------------------------- #
def test_monotone_series_age_increases():
    out = _block([WIN - 1, 250, 399], np.linspace(0.01, 0.05, 400))
    age = out["regime_age_vol"].to_numpy()
    assert age.tolist() == [0.0, 18.0, 167.0]
    assert np.isnan(out["regime_prev_dur_vol"].to_numpy()).all()  # no flip yet


def test_hurst_age_uses_its_own_series():
    hurst = np.concatenate([np.full(300, 0.40), np.full(261, 0.60)])
    out = _block([299, 305, 399], _flip_series(), hurst=hurst)
    assert out["regime_age_hurst"].to_numpy().tolist() == [67.0, 5.0, 99.0]  # run start = 232
    assert "regime_prev_dur_hurst" not in out.columns


# --------------------------------------------------------------------------- #
# Causality: only bars <= t are read
# --------------------------------------------------------------------------- #
def test_future_bars_do_not_change_the_row():
    base = _flip_series()
    t = 320
    bumped = base.copy()
    bumped[t + 1:] *= 3.0                                # strictly future bars only
    before, after = _block([t], base).iloc[0], _block([t], bumped).iloc[0]
    pd.testing.assert_series_equal(before, after, check_exact=False, rtol=1e-6)


# --------------------------------------------------------------------------- #
# Soft dependency: an explicit WI-047 state column wins over atr_pct_21
# --------------------------------------------------------------------------- #
def test_explicit_state_column_is_used_verbatim():
    state = np.concatenate([np.zeros(240), np.ones(321)]).astype("float64")
    out = _block([5, 239, 240, 250], _flip_series(), regime_state_vol=state)
    age = out["regime_age_vol"].to_numpy()
    assert age.tolist() == [5.0, 239.0, 0.0, 10.0]
    prev = out["regime_prev_dur_vol"].to_numpy()
    assert np.isnan(prev[:2]).all() and prev[2:].tolist() == [240.0, 240.0]
    assert np.isnan(out["regime_age_hurst"].to_numpy()).all()   # no hurst source


# --------------------------------------------------------------------------- #
# Contract: float32, dimensionless, recognised prefix
# --------------------------------------------------------------------------- #
def test_contract_float32_dimensionless_prefix():
    out = _block([WIN - 1, 399], _flip_series(), hurst=np.linspace(0.4, 0.6, 561))
    assert tuple(out.columns) == NEW_COLUMNS
    assert all(out[c].dtype == np.float32 for c in out.columns)
    panel = pd.DataFrame({c: out[c] for c in out.columns})
    assert set(NEW_COLUMNS) <= set(bei.candidate_features(panel))
