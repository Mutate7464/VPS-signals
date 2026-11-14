"""WI-016 addendum — honest-edge probe tests.

Verify: `uv run pytest tests/test_wi016_addendum.py`
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.wi016.addendum import (
    band_verdicts,
    duration_report,
    event_uniqueness,
    primary_bakeoff,
    restricted_gate,
    step5_verdict,
    top_decile_mask,
    touch_restricted_mask,
    uniqueness_weighted_stats,
)
from src.wi016.triple_barrier import (
    VERTICAL_HORIZONS,
    compute_triple_barrier,
    label_columns,
)


def _panel(n_dates: int = 60, per_date: int = 30, signal: bool = True, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = np.repeat(pd.date_range("2020-01-01", periods=n_dates, freq="B"), per_date)
    n = n_dates * per_date
    f_signal = rng.normal(0, 1, n)
    f_noise = rng.normal(0, 1, n)
    symbols = np.tile([f"S{i:02d}" for i in range(per_date)], n_dates)

    if signal:
        p = 1.0 / (1.0 + np.exp(-2.0 * f_signal))
    else:
        p = np.full(n, 0.5)
    profit = rng.random(n) < p
    touch = np.where(profit, 1.0, -1.0)
    vertical = rng.random(n) < 0.2
    touch = np.where(vertical, 0.0, touch)
    drift = np.sign(f_signal + rng.normal(0, 1, n))
    label = np.where(vertical, drift, touch)

    return pd.DataFrame({
        "date": dates,
        "symbol": symbols,
        "f_signal": f_signal.astype("float32"),
        "f_noise": f_noise.astype("float32"),
        "tb_label_k15_h8": label.astype("float32"),
        "tb_touch_k15_h8": touch.astype("int8"),
        "tb_fret_h8": ((0.02 * f_signal if signal else 0.0) + rng.normal(0, 0.01, n)).astype("float32"),
    })


# --------------------------------------------------------------------------- #
# Deliverable 1 — touch restriction + gate
# --------------------------------------------------------------------------- #
def test_touch_restricted_mask_excludes_vertical_and_invalid():
    t = np.array([1.0, -1.0, 0.0, -9.0, np.nan])
    assert touch_restricted_mask(t).tolist() == [True, True, False, False, False]


def test_restricted_gate_clears_real_signal_and_counts_classes(tmp_path):
    panel = _panel(signal=True)
    res = restricted_gate(panel, ["f_signal", "f_noise"], market="USD",
                          k_values=(1.5,), horizons=(8,), out_dir=tmp_path)
    assert res["outcome"] == "CLEAR"
    # class counts exclude vertical rows from the restricted sample.
    cc = res["class_counts"][0]
    assert cc["n_restricted"] == cc["profit"] + cc["stop"]
    assert cc["n_restricted"] < cc["n_defined"]
    assert (tmp_path / "wi016_addendum_probe_USD.md").exists()
    # the realized-return target is present too.
    assert any(d["target"] == "tb_fret_h8" for d in res["decisions"])


def test_restricted_gate_reports_verdict_change_vs_step5(tmp_path):
    (tmp_path / "wi016_probe_USD.md").write_text(
        "| `tb_label_k15_h8` | no | 0 | - | - |\n")
    panel = _panel(signal=True)
    res = restricted_gate(panel, ["f_signal", "f_noise"], market="USD",
                          k_values=(1.5,), horizons=(8,), out_dir=tmp_path)
    assert res["step5"] == {"tb_label_k15_h8": False}
    body = (tmp_path / "wi016_addendum_probe_USD.md").read_text()
    assert "Verdict change vs step 5" in body
    assert "YES" in body  # step5 said no, addendum clears -> flipped


def test_restricted_gate_not_clear_without_signal(tmp_path):
    panel = _panel(signal=False)
    res = restricted_gate(panel, ["f_signal", "f_noise"], market="CAD",
                          k_values=(1.5,), horizons=(8,), out_dir=tmp_path)
    assert res["outcome"] == "NOT_CLEAR"


def test_band_verdicts_flip_with_cost():
    tests = [{"target": "t", "feature": "f", "ic": 0.03, "fdr_significant": True,
              "same_sign": True, "placebo_clear": True, "kind": "touch_restricted"}]
    bands = band_verdicts(tests, ["t"], cost_bands=(10.0, 20.0, 30.0))
    assert bands[10.0]["clear"] is True   # 30 bps gross > 10
    assert bands[20.0]["clear"] is True   # 30 > 20
    assert bands[30.0]["clear"] is False  # 30 not > 30


def test_band_verdicts_split_barrier_from_realized_return():
    tests = [
        {"target": "lab", "feature": "f", "ic": 0.015, "fdr_significant": True,
         "same_sign": True, "placebo_clear": True, "kind": "touch_restricted"},
        {"target": "fret", "feature": "f", "ic": 0.05, "fdr_significant": True,
         "same_sign": True, "placebo_clear": True, "kind": "realized_return"},
    ]
    bands = band_verdicts(tests, ["lab", "fret"], cost_bands=(20.0,))
    assert bands[20.0]["by_kind"] == {"touch_restricted": False, "realized_return": True}


# --------------------------------------------------------------------------- #
# Deliverable 2 — overlap-aware weights
# --------------------------------------------------------------------------- #
def test_event_uniqueness_is_per_symbol_and_shrinks_with_overlap():
    dates = pd.date_range("2020-01-01", periods=40, freq="B")  # one symbol
    u8 = event_uniqueness(dates, horizon=8)
    u1 = event_uniqueness(dates, horizon=1)
    fin = np.isfinite(u8)
    assert 0.1 < np.nanmean(u8) < 0.4          # interior ≈ 1/8, not ~5e-5
    assert np.nanmean(u8) < np.nanmean(u1)
    assert np.all((u8[fin] > 0) & (u8[fin] <= 1.0))
    # Two symbols on disjoint dates are independent -> same per-symbol uniqueness.
    two = np.concatenate([dates, dates + pd.Timedelta(days=365)])
    syms = np.array(["A"] * 40 + ["B"] * 40)
    u2 = event_uniqueness(two, horizon=8, symbols=syms)
    assert np.nanmean(u2) == pytest.approx(np.nanmean(u8), rel=0.05)


def test_uniqueness_weighted_stats_shrinks_t_under_overlap():
    rng = np.random.default_rng(3)
    v = rng.normal(0.3, 1.0, 200)
    u = np.full(200, 1.0 / 8.0)
    s = uniqueness_weighted_stats(np.arange(200), v, u)
    assert abs(s["weighted_t"]) < abs(s["unweighted_t"])
    assert s["effective_n"] == pytest.approx(200 / 8)
    # Equal weights reproduce the unweighted t exactly (no spurious inflation).
    s1 = uniqueness_weighted_stats(np.arange(200), v, np.ones(200))
    assert s1["weighted_t"] == pytest.approx(s1["unweighted_t"])


def test_uniqueness_weighted_stats_downweights_pseudo_replication():
    v = np.array([0.5, 0.5, 0.5, 0.5, 0.5, 0.01])
    w = np.array([1.0, 1.0, 1.0, 1.0, 0.1, 0.1])  # last two nearly unique-free
    s = uniqueness_weighted_stats(np.arange(6), v, w)
    assert s["unweighted_ic"] == pytest.approx(float(v.mean()))
    assert s["weighted_ic"] != s["unweighted_ic"]
    assert s["n_dates"] == 6


# --------------------------------------------------------------------------- #
# Deliverable 3 — primary bake-off
# --------------------------------------------------------------------------- #
def test_top_decile_mask_is_per_date_and_long_side():
    rng = np.random.default_rng(0)
    dates = np.repeat(pd.date_range("2020-01-01", periods=10, freq="B"), 100)
    v = rng.normal(0, 1, 1000)
    m = top_decile_mask(v, dates)
    per_date = pd.Series(m).groupby(pd.Series(dates)).sum()
    assert per_date.between(8, 12).all()
    # selected values are above each date's median
    assert (v[m] > np.median(v)).mean() > 0.9


def test_primary_bakeoff_picks_signal_primary(tmp_path):
    panel = _panel(signal=True)
    res = primary_bakeoff(panel, market="USD", k_values=(1.5,), horizons=(8,),
                          candidates=("f_signal", "f_noise"), out_dir=tmp_path)
    assert res["winner"] == "f_signal"
    row = next(r for r in res["rows"] if r["candidate"] == "f_signal")
    assert row["mean_gated_abs_ic"] >= row["mean_ungated_abs_ic"] - 1e-9
    assert (tmp_path / "wi016_addendum_bakeoff_USD.md").exists()
    assert res["skipped"] == []


# --------------------------------------------------------------------------- #
# Deliverable 5 — duration columns
# --------------------------------------------------------------------------- #
def _walk(n: int = 400, seed: int = 1) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    close = 100.0 + np.cumsum(rng.normal(0, 1.0, n))
    return pd.DataFrame({
        "date": pd.date_range("2015-01-01", periods=n, freq="B"),
        "open": close, "high": close + 1.0, "low": close - 1.0, "close": close,
        "volume": 1000.0,
    })


def test_label_columns_include_duration():
    cols = label_columns()
    for k_tag in ("k15", "k20"):
        for h in VERTICAL_HORIZONS:
            assert f"tb_duration_{k_tag}_h{h}" in cols


def test_compute_triple_barrier_emits_duration_in_bars():
    lab = compute_triple_barrier(_walk(), k_values=(1.5,), horizons=(8,))
    dur = lab["tb_duration_k15_h8"].to_numpy()
    label = lab["tb_label_k15_h8"].to_numpy()
    fin = np.isfinite(dur)
    assert fin.any()
    assert dur[fin].min() >= 1.0 and dur[fin].max() <= 8.0
    # NaN exactly matches the label NaN mask (tail + ATR warm-up).
    assert np.array_equal(fin, np.isfinite(label))


def test_duration_report_writes_market_report(tmp_path):
    panel = _panel()
    panel["tb_duration_k15_h8"] = 4.0
    res = duration_report(panel, market="CAD", k_values=(1.5,), horizons=(8,), out_dir=tmp_path)
    assert res["report"].endswith("wi016_addendum_duration_CAD.md")
    assert (tmp_path / "wi016_addendum_duration_CAD.md").exists()


# --------------------------------------------------------------------------- #
# Step-5 comparison parser
# --------------------------------------------------------------------------- #
def test_step5_verdict_parses_report(tmp_path):
    (tmp_path / "wi016_probe_USD.md").write_text(
        "| target | cleared |\n| `tb_label_k15_h8` | yes |\n| `tb_label_k20_h8` | no |\n"
    )
    v = step5_verdict("USD", out_dir=tmp_path)
    assert v == {"tb_label_k15_h8": True, "tb_label_k20_h8": False}
