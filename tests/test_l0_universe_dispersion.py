"""WI-056 — L0-5 universe vol-regime dispersion (D-026 sprint).

Synthetic only: no reads under `data/` or `reports/`. The WI-056 §1 net-new
precondition vs WI-047 #3 (market-residual context) is asserted, not assumed —
see `test_net_new_vs_wi047_3_market_residual_context`.

Verify: `uv run pytest tests/test_l0_universe_dispersion.py -q`
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.swing_bsh import binary_features_ext as bei

NEW_COLUMNS = ("disp_atr_pct_21", "disp_entropy_39")


def _panel(dates, atr, entropy) -> pd.DataFrame:
    n = len(dates)
    return pd.DataFrame({
        "date": pd.to_datetime(dates),
        "symbol": [f"S{i}" for i in range(n)],
        "atr_pct_21": np.asarray(atr, "float64"),
        "entropy_39": np.asarray(entropy, "float64"),
    })


def _disp(dates, atr, entropy) -> pd.DataFrame:
    return bei._universe_dispersion(_panel(dates, atr, entropy)).set_index("date")


# --------------------------------------------------------------------------- #
# Crafted multi-symbol dates -> known IQR / std
# --------------------------------------------------------------------------- #
def test_two_symbol_dates_give_known_iqr_and_std():
    d1, d2 = "2020-01-01", "2020-01-02"
    out = _disp([d1, d1, d1, d2, d2],
                [0.10, 0.20, 0.40, 0.30, 0.30],
                [0.10, 0.50, 0.90, 0.20, 0.60])
    # date 1: IQR([.1,.2,.4]) = .30 - .15 = .15 ; std([.1,.5,.9]) = sqrt(.1066..) = .3266
    assert out.loc[d1, "disp_atr_pct_21"] == pytest.approx(0.15, rel=1e-6)
    assert out.loc[d1, "disp_entropy_39"] == pytest.approx(0.3265986, rel=1e-6)
    # date 2: flat atr -> IQR 0 ; std([.2,.6]) = .20
    assert out.loc[d2, "disp_atr_pct_21"] == pytest.approx(0.0, abs=1e-7)
    assert out.loc[d2, "disp_entropy_39"] == pytest.approx(0.20, rel=1e-6)


def test_single_symbol_date_is_zero():
    out = _disp(["2020-01-01", "2020-01-01", "2020-01-02"],
                [0.10, 0.40, 0.77], [0.10, 0.90, 0.42])
    assert out.loc["2020-01-02", "disp_atr_pct_21"] == 0.0
    assert out.loc["2020-01-02", "disp_entropy_39"] == 0.0


def test_nan_dates_and_partial_rows():
    out = _disp(["2020-01-01", "2020-01-01", "2020-01-02", "2020-01-02"],
                [np.nan, np.nan, 0.20, np.nan], [np.nan, 0.50, np.nan, np.nan])
    assert np.isnan(out.loc["2020-01-01", "disp_atr_pct_21"])      # no finite value
    assert out.loc["2020-01-01", "disp_entropy_39"] == 0.0         # one finite value
    assert np.isnan(out.loc["2020-01-02", "disp_entropy_39"])


# --------------------------------------------------------------------------- #
# Same-date only: other dates' rows cannot move a date's spread
# --------------------------------------------------------------------------- #
def test_spread_reads_only_same_date_rows():
    base = _disp(["2020-01-01", "2020-01-01", "2020-01-02"],
                 [0.10, 0.20, 0.30], [0.10, 0.30, 0.50])
    shocked = _disp(["2020-01-01", "2020-01-01", "2020-01-02", "2020-01-02"],
                    [0.10, 0.20, 0.30, 99.0], [0.10, 0.30, 0.50, 99.0])
    assert shocked.loc["2020-01-01", "disp_atr_pct_21"] == base.loc["2020-01-01", "disp_atr_pct_21"]
    assert shocked.loc["2020-01-01", "disp_entropy_39"] == base.loc["2020-01-01", "disp_entropy_39"]
    assert len(base) == 2 and len(shocked) == 2                   # one row per date


# --------------------------------------------------------------------------- #
# Contract: date-keyed float32, broadcast onto every same-date row
# --------------------------------------------------------------------------- #
def test_output_is_date_keyed_float32_and_broadcasts():
    panel = _panel(["2020-01-01", "2020-01-01", "2020-01-02", "2020-01-02"],
                   [0.10, 0.40, 0.20, 0.20], [0.10, 0.90, 0.30, 0.30])
    out = bei._universe_dispersion(panel)
    assert list(out.columns) == ["date", *NEW_COLUMNS]
    assert out["disp_atr_pct_21"].dtype == np.float32
    assert out["disp_entropy_39"].dtype == np.float32
    merged = panel.merge(out, on="date", how="left")
    assert len(merged) == len(panel)                              # row-aligned broadcast
    assert merged.groupby("date")["disp_atr_pct_21"].nunique().max() == 1


def test_candidate_features_picks_up_the_disp_prefix():
    panel = _panel(["2020-01-01", "2020-01-02"], [0.10, 0.40], [0.10, 0.90])
    panel = panel.merge(bei._universe_dispersion(panel), on="date", how="left")
    feats = bei.candidate_features(panel)
    assert set(NEW_COLUMNS) <= set(feats)


# --------------------------------------------------------------------------- #
# Precondition: net-new vs WI-047 #3 (market-residual context)
# --------------------------------------------------------------------------- #
def test_net_new_vs_wi047_3_market_residual_context():
    """WI-047 shortlist #3 = per-name market-residual context (`mkt_resid_mom_{w}`,
    `beta_mkt_{w}`, `corr_mkt_{w}`, `breadth_divergence_21`): *first-moment,
    per-symbol* statistics against a same-date cross-sectional mean-return proxy.
    L0-5 emits *date-level second-moment* spread columns only — no per-symbol beta,
    correlation, residual or breadth divergence — so the blocks are disjoint by
    construction. Asserted here so the precondition is evidence, not recollection.
    """
    out = bei._universe_dispersion(_panel(["2020-01-01", "2020-01-01"],
                                          [0.10, 0.40], [0.10, 0.90]))
    assert list(out.columns) == ["date", *NEW_COLUMNS]
    assert not any(c.startswith(("mkt_resid", "beta_mkt", "corr_mkt", "breadth_"))
                   for c in out.columns)
    assert len(out) == out["date"].nunique()                      # date-level, not per-name
    assert {n: how for n, _, how in bei.DISP_SOURCES} == {        # contract's "IQR / std"
        "disp_atr_pct_21": "iqr", "disp_entropy_39": "std"}
