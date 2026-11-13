"""WI-055 — L0-4 bipower jump-variation / jump-count block (D-026 sprint).

Synthetic only: no reads under `data/` or `reports/`. Verify:
`uv run pytest tests/test_l0_jump_intensity.py -q`
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.swing_bsh import binary_features_ext as bei

W = 21
RATIO, COUNT = f"jump_var_ratio_{W}", f"jump_count_{W}"
NEW_COLUMNS = tuple(f"{n}_{w}" for w in (21, 55) for n in ("jump_var_ratio", "jump_count"))


def _block(close):
    return bei._jump_intensity(np.asarray(close, dtype="float64"), windows=(W,))


# --------------------------------------------------------------------------- #
# Smooth (jump-free) window -> no jump variance, no jump bars
# --------------------------------------------------------------------------- #
def test_smooth_series_has_zero_jump_variance_and_count():
    out = _block(100.0 * 1.01 ** np.arange(120))
    row = out.iloc[-1]
    assert row[RATIO] == 0.0            # rv - bv <= 0 on a constant-return window
    assert row[COUNT] == 0.0


def test_diffusive_noise_stays_well_below_full_jump_variance():
    rng = np.random.default_rng(11)
    close = 100.0 * np.exp(np.cumsum(rng.normal(0, 0.01, 400)))
    out = _block(close)
    assert out[RATIO].max() < 0.6       # no single bar dominates any window
    assert out[COUNT].max() <= 1.0


# --------------------------------------------------------------------------- #
# One large bar -> the window's variance is attributed to the jump
# --------------------------------------------------------------------------- #
def test_single_large_bar_gives_positive_jump_variance():
    close = np.full(120, 50.0)
    close[80:] = 62.0                   # one-step jump, then flat again
    out = _block(close)
    at_jump, later = out.iloc[80], out.iloc[100]
    assert at_jump[RATIO] > 0.5         # bipower var ~0 while rv is the jump bar
    assert later[RATIO] > 0.5           # still inside the trailing window
    assert at_jump[COUNT] == 1.0 and later[COUNT] == 1.0
    assert out.iloc[79][RATIO] == 0.0   # before the jump: nothing
    assert out.iloc[101][RATIO] == 0.0  # jump bar has left the window
    assert out.iloc[101][COUNT] == 0.0


# --------------------------------------------------------------------------- #
# Causal warmup: ratio from bar w+1, count only ever a full window (bar 2w)
# --------------------------------------------------------------------------- #
def test_nan_warmup_then_finite():
    out = _block(100.0 * 1.005 ** np.arange(120))
    assert out[RATIO].iloc[: W + 1].isna().all()    # needs w prior returns
    assert out[RATIO].iloc[W + 1:].notna().all()
    assert out[COUNT].iloc[: 2 * W].isna().all()    # needs w jump indicators
    assert out[COUNT].iloc[2 * W:].notna().all()


def test_future_bars_do_not_change_the_row():
    close = 100.0 * 1.003 ** np.arange(120)
    t = 60
    base = _block(close).iloc[t]
    bumped = close.copy()
    bumped[t + 1:] *= 1.5               # only strictly future bars move
    after = _block(bumped).iloc[t]
    pd.testing.assert_series_equal(base, after, check_exact=False, rtol=1e-6)


# --------------------------------------------------------------------------- #
# Contract: float32, dimensionless, recognised prefix
# --------------------------------------------------------------------------- #
def test_contract_float32_dimensionless_prefix():
    out = _block(100.0 * 1.004 ** np.arange(120))
    assert tuple(out.columns) == (RATIO, COUNT)
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
