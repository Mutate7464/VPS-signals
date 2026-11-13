"""WI-053 — L0-2 realized asymmetry / semivariance / skew block (D-026 sprint).

Synthetic only: no reads under `data/` or `reports/`. Verify:
`uv run pytest tests/test_l0_asymmetry.py -q`
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.swing_bsh import binary_features_ext as bei

W = 5
NEW_COLUMNS = (f"semivar_up_{W}", f"semivar_dn_{W}", f"semivar_ratio_{W}", f"rv_skew_{W}")


def _block(close):
    return bei._realized_asymmetry(np.asarray(close, dtype="float64"), windows=(W,))


# --------------------------------------------------------------------------- #
# Payoff shape: monotone up -> positive skew, upside semivariance dominates
# --------------------------------------------------------------------------- #
def test_monotone_up_has_positive_skew_and_up_semivar():
    out = _block(100.0 * 1.01 ** np.arange(40))
    row = out.iloc[-1]
    assert row["rv_skew_5"] > 0
    assert row["semivar_up_5"] > 0
    assert row["semivar_dn_5"] == 0.0          # every log return is positive
    assert row["semivar_ratio_5"] > 1.0


def test_monotone_down_has_negative_skew_and_down_semivar():
    out = _block(100.0 * 0.99 ** np.arange(40))
    row = out.iloc[-1]
    assert row["rv_skew_5"] < 0
    assert row["semivar_dn_5"] > 0
    assert row["semivar_up_5"] == 0.0
    assert 0.0 < row["semivar_ratio_5"] < 1.0  # eps-guarded, stays strictly positive


# --------------------------------------------------------------------------- #
# Flat window -> zero semivariance on both sides, neutral ratio
# --------------------------------------------------------------------------- #
def test_flat_series_gives_ratio_one_and_zero_semivariance():
    out = _block(np.full(30, 50.0))
    row = out.iloc[-1]
    assert row["semivar_up_5"] == 0.0
    assert row["semivar_dn_5"] == 0.0
    assert row["semivar_ratio_5"] == 1.0
    assert row["rv_skew_5"] == 0.0


# --------------------------------------------------------------------------- #
# Causal warmup: NaN until `w` prior returns exist, never a fabricated value
# --------------------------------------------------------------------------- #
def test_nan_warmup_then_finite():
    close = 100.0 * 1.005 ** np.arange(30)
    out = _block(close)
    assert out.iloc[:W].isna().all().all()     # rows 0..w-1: fewer than w returns
    assert out.iloc[W:].notna().all().all()    # bar w onwards: w prior returns


def test_future_bars_do_not_change_the_row():
    close = 100.0 * 1.003 ** np.arange(30)
    t = 20
    base = _block(close).iloc[t]
    bumped = close.copy()
    bumped[t + 1:] *= 1.5                      # only strictly future bars move
    after = _block(bumped).iloc[t]
    pd.testing.assert_series_equal(base, after, check_exact=False, rtol=1e-6)


# --------------------------------------------------------------------------- #
# Contract: float32, dimensionless, recognised prefix
# --------------------------------------------------------------------------- #
def test_contract_float32_dimensionless_prefix():
    out = _block(100.0 * 1.004 ** np.arange(40))
    assert tuple(out.columns) == NEW_COLUMNS
    assert all(out[c].dtype == np.float32 for c in out.columns)
    panel = pd.DataFrame({c: out[c] for c in out.columns})
    picked = bei.candidate_features(panel)
    assert set(NEW_COLUMNS) <= set(picked)


# --------------------------------------------------------------------------- #
# Ratio is the eps-guarded semivariance ratio on both tails
# --------------------------------------------------------------------------- #
def test_ratio_is_the_semivariance_ratio():
    up = _block(100.0 * 1.01 ** np.arange(40)).iloc[-1]
    down = _block(100.0 * 0.99 ** np.arange(40)).iloc[-1]
    for row in (up, down):
        exp = (float(row["semivar_up_5"]) + 1e-12) / (float(row["semivar_dn_5"]) + 1e-12)
        assert np.isclose(float(row["semivar_ratio_5"]), exp, rtol=1e-5)