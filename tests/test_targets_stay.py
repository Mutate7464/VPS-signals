"""WI-009c prep: y_20d_stay target — ±5% band, exclusive of Up/Down (admin 2026-10-25)."""

import numpy as np
import pandas as pd

from src.targets import STAY_RET_MAX, TARGET_COLUMNS, compute_targets


def _synthetic(close: list[float]) -> pd.DataFrame:
    n = len(close)
    rng = np.random.default_rng(0)
    base = 100.0
    hi = base + np.abs(rng.normal(0.5, 0.3, n))
    lo = base - np.abs(rng.normal(0.5, 0.3, n))
    return pd.DataFrame(
        {
            "date": pd.date_range("2020-01-01", periods=n, freq="D"),
            "open": base,
            "high": hi,
            "low": lo,
            "close": close,
            "volume": 1_000_000.0,
        }
    )


def test_stay_column_exists_and_in_target_columns():
    assert "y_20d_stay" in TARGET_COLUMNS


def test_stay_is_exclusive_of_up_down():
    # Flat close → small fwd moves → stay rows; verify no row is stay AND up/down.
    close = list(np.full(120, 100.0))
    t = compute_targets(_synthetic(close))
    stay = t["y_20d_stay"]
    overlap = (stay == 1) & ((t["y_20d_up"] == 1) | (t["y_20d_down"] == 1))
    assert not overlap.any()


def test_stay_band_respects_threshold():
    # Non-trending close (alternating) so y_20d_up/down do not fire, isolating
    # the band rule: final fwd 20d close +4% (inside ±STAY_RET_MAX) vs +8% (outside).
    def mk(final: float) -> list[float]:
        close = list(np.full(41, 100.0)) + [106.0, 98.0] * 9 + [final]
        return close

    t4 = compute_targets(_synthetic(mk(104.0)))
    t8 = compute_targets(_synthetic(mk(108.0)))
    # Row 39 is the first row with a complete 20d forward window.
    assert t4.loc[39, "y_20d_up"] == 0.0 and t4.loc[39, "y_20d_down"] == 0.0
    assert t4.loc[39, "y_20d_stay"] == 1.0
    assert t8.loc[39, "y_20d_stay"] == 0.0


def test_stay_nan_where_forward_window_incomplete():
    close = list(np.full(30, 100.0))
    t = compute_targets(_synthetic(close))
    # Trailing 20 rows have no complete forward window → NaN (same mask as up/down).
    assert t["y_20d_stay"].tail(20).isna().all()
    assert t["y_20d_up"].tail(20).isna().all()
    assert t["y_20d_stay"].notna().sum() == t["y_20d_up"].notna().sum()


def test_stay_ret_max_constant():
    assert STAY_RET_MAX == 0.05