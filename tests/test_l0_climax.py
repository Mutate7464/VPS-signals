"""WI-057 — L0-6 effort-vs-result / climax block (D-026 sprint).

Synthetic only: no reads under `data/` or `reports/`. Verify:
`uv run pytest tests/test_l0_climax.py -q`
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.swing_bsh import binary_features_ext as bei

W = 21
RATIO, Z = f"effort_result_{W}", f"effort_result_z_{W}"
NEW_COLUMNS = tuple(f"{n}_{w}" for w in (21, 55) for n in ("effort_result", "effort_result_z"))


def _block(volume, high=None, low=None, atr=1.0):
    n = np.asarray(volume, dtype="float64").size
    high = np.full(n, 1.0) if high is None else high
    low = np.zeros(n) if low is None else low
    atr = np.full(n, atr, dtype="float64") if np.isscalar(atr) else atr
    return bei._climax(np.asarray(volume, dtype="float64"), high, low, atr, windows=(W,))


def _series(n=140, seed=3):
    """Steady volume (~1000) with tiny range jitter and a wide bar."""
    rng = np.random.default_rng(seed)
    vol = 1_000.0 + rng.normal(0, 20.0, n)
    high = 1.0 + np.abs(rng.normal(0, 0.01, n))
    low = np.zeros(n)
    return vol, high, low


# --------------------------------------------------------------------------- #
# Large range on small volume -> low effort per unit of range
# --------------------------------------------------------------------------- #
def test_large_range_small_volume_gives_low_effort_result():
    vol, high, low = _series()
    high[100] = 5.0                     # huge range ...
    vol[100] = 100.0                    # ... on one tenth of the usual volume
    out = _block(vol, high, low)
    assert out[RATIO].iloc[100] < out[RATIO].iloc[:100].median()
    assert out[Z].iloc[100] < -1.0      # a clear outlier against its own window


def test_small_range_large_volume_gives_high_effort_result():
    vol, high, low = _series(seed=5)
    high[110] = 0.001                   # near-zero range with double volume
    vol[110] = 2_000.0
    out = _block(vol, high, low)
    assert out[RATIO].iloc[110] > out[RATIO].iloc[:110].median()
    assert out[Z].iloc[110] > 1.0


def test_result_is_atr_normalized():
    vol, high, low = _series()
    a = _block(vol, high, low, atr=1.0)
    b = _block(vol, high, low, atr=4.0)   # same bars, 4x larger ATR denominator
    # result is (high - low) / atr, so a 4x ATR shrinks the denominator -> 4x the ratio
    pd.testing.assert_series_equal(a[RATIO].iloc[W:] * 4.0, b[RATIO].iloc[W:],
                                   check_exact=False, rtol=1e-5, check_names=False)


# --------------------------------------------------------------------------- #
# Causal warmup: ratio from bar w, z-score from bar 2w-1
# --------------------------------------------------------------------------- #
def test_nan_warmup_then_finite():
    vol, high, low = _series()
    out = _block(vol, high, low)
    assert out[RATIO].iloc[: W - 1].isna().all()    # needs w volume observations
    assert out[RATIO].iloc[W - 1:].notna().all()
    assert out[Z].iloc[: 2 * W - 2].isna().all()    # needs w ratio values (bar 2w-1)
    assert out[Z].iloc[2 * W - 2:].notna().all()


def test_nan_atr_yields_nan_row():
    vol, high, low = _series()
    atr = np.ones(vol.size)
    atr[70] = np.nan
    out = _block(vol, high, low, atr=atr)
    assert np.isnan(out[RATIO].iloc[70])


def test_future_bars_do_not_change_the_row():
    vol, high, low = _series()
    t = 90
    base = _block(vol, high, low).iloc[t]
    b_vol, b_high = vol.copy(), high.copy()
    b_vol[t + 1:] *= 3.0                # only strictly future bars move
    b_high[t + 1:] *= 20.0
    after = _block(b_vol, b_high, low).iloc[t]
    pd.testing.assert_series_equal(base, after, check_exact=False, rtol=1e-6)


# --------------------------------------------------------------------------- #
# Contract: float32, dimensionless, recognised prefix
# --------------------------------------------------------------------------- #
def test_contract_float32_dimensionless_prefix():
    vol, high, low = _series()
    out = _block(vol, high, low)
    assert tuple(out.columns) == (RATIO, Z)
    assert all(out[c].dtype == np.float32 for c in out.columns)
    panel = pd.DataFrame({c: out[c] for c in out.columns})
    assert set(NEW_COLUMNS[:2]) <= set(bei.candidate_features(panel))


# --------------------------------------------------------------------------- #
# Wiring: the block lands in the panel and in candidate_features
# --------------------------------------------------------------------------- #
def _ohlcv(n: int = 400, seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    close = 100.0 * np.exp(np.cumsum(rng.normal(0, 0.01, n)))
    return pd.DataFrame({
        "date": pd.date_range("2015-01-01", periods=n, freq="B"),
        "open": close * (1 + rng.normal(0, 0.002, n)),
        "high": close * (1 + np.abs(rng.normal(0, 0.005, n))),
        "low": close * (1 - np.abs(rng.normal(0, 0.005, n))),
        "close": close,
        "volume": rng.integers(1_000, 10_000, n).astype("float64"),
    })


def test_block_wired_into_panel_and_candidate_features(monkeypatch):
    g = _ohlcv()
    monkeypatch.setattr(bei, "iter_market_symbols", lambda *a, **k: iter([("SYN", g)]))
    panel, _labels = bei.build_variant_panel("USD", max_symbols=1, with_sector=False)
    assert not panel.empty
    for col in NEW_COLUMNS:
        assert col in panel.columns and panel[col].dtype == np.float32
    assert set(NEW_COLUMNS) <= set(bei.candidate_features(panel))