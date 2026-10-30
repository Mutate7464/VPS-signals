"""WI-016 steps 4–5 — legacy comparison + probe-gate tests.

Verify: `uv run pytest tests/test_wi016_probe.py`
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.wi016.probe import (
    benjamini_hochberg,
    cost_overlay,
    decide_target,
    legacy_comparison,
    probe_gate,
    within_date_ic,
)


def _panel(n_dates: int = 40, per_date: int = 20, signal: bool = True, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = np.repeat(pd.date_range("2020-01-01", periods=n_dates, freq="B"), per_date)
    n = n_dates * per_date
    f_signal = rng.normal(0, 1, n)
    f_noise = rng.normal(0, 1, n)
    symbols = np.tile([f"S{i:02d}" for i in range(per_date)], n_dates)

    if signal:
        tb = (0.8 * f_signal + rng.normal(0, 0.6, n) > 0).astype(float)
    else:
        tb = rng.integers(-1, 2, n).astype(float)

    panel = pd.DataFrame(
        {
            "date": dates,
            "symbol": symbols,
            "f_signal": f_signal.astype("float32"),
            "f_noise": f_noise.astype("float32"),
            # synthetic triple-barrier label + legacy labels
            "tb_label_k15_h8": tb.astype("float32"),
            "y_15d_high": (rng.random(n) > 0.5).astype("float32"),
            "y_20d_up": (rng.random(n) > 0.5).astype("float32"),
        }
    )
    return panel


# --------------------------------------------------------------------------- #
# FDR
# --------------------------------------------------------------------------- #
def test_benjamini_hochberg_rejects_small_pvalues():
    reject, q = benjamini_hochberg([0.001, 0.04, 0.5], alpha=0.05)
    assert reject.tolist() == [True, False, False]
    assert q[0] == pytest.approx(0.003)
    # q-values dominate p-values and are clipped to [0, 1].
    assert np.all(q >= np.array([0.001, 0.04, 0.5]))
    assert np.all(q <= 1.0)


def test_benjamini_hochberg_handles_nan_and_is_less_strict_than_bonferroni():
    reject, q = benjamini_hochberg([0.001, 0.02, 0.03, np.nan], alpha=0.05)
    assert not reject[3]  # NaN never rejects
    assert np.isnan(q[3])
    # BH (4 tests) rejects more than a Bonferroni alpha/m cutoff would.
    bonferroni = 0.05 / 3
    assert sum(reject) >= sum(1 for p in [0.001, 0.02, 0.03] if p <= bonferroni)


def test_benjamini_hochberg_is_monotone_in_rank():
    p = np.array([0.001, 0.01, 0.02, 0.2, 0.9])
    _, q = benjamini_hochberg(p)
    fin = q[np.isfinite(q)]
    assert np.all(np.diff(fin) >= -1e-12)


# --------------------------------------------------------------------------- #
# Cost overlay
# --------------------------------------------------------------------------- #
def test_cost_overlay_defaults_to_no_trade():
    assert cost_overlay(0.001)["decision"] == "NO_TRADE"
    assert cost_overlay(0.001)["tradeable"] is False
    strong = cost_overlay(0.5)
    assert strong["decision"] == "TRADE" and strong["net_bps"] > 0
    assert cost_overlay(float("nan"))["decision"] == "NO_TRADE"


# --------------------------------------------------------------------------- #
# Decision logic
# --------------------------------------------------------------------------- #
def _row(**kw):
    base = {"target": "t", "feature": "f", "ic": 0.2, "q": 0.01, "same_sign": True,
            "placebo_clear": True, "tradeable": True}
    base.update(kw)
    return base


def test_decide_target_requires_every_clause():
    assert decide_target("t", [_row()])["cleared"] is True
    assert decide_target("t", [_row(q=0.2)])["cleared"] is False
    assert decide_target("t", [_row(same_sign=False)])["cleared"] is False
    assert decide_target("t", [_row(placebo_clear=False)])["cleared"] is False
    assert decide_target("t", [_row(tradeable=False)])["cleared"] is False
    assert decide_target("t", [])["cleared"] is False


def test_within_date_ic_flags_predictive_feature():
    panel = _panel(signal=True)
    res = within_date_ic(panel["f_signal"].to_numpy(), panel["tb_label_k15_h8"].to_numpy(), panel["date"].to_numpy())
    assert res["ic"] > 0
    assert res["same_sign"] is True
    assert res["p"] < 0.05


# --------------------------------------------------------------------------- #
# Step 4 — legacy comparison on identical rows
# --------------------------------------------------------------------------- #
def test_legacy_comparison_uses_identical_rows_and_writes_report(tmp_path):
    panel = _panel()
    features = ["f_signal", "f_noise"]
    res = legacy_comparison(panel, features, market="USD", out_dir=tmp_path)
    assert res["n_rows"] == len(panel)
    assert all(r["n_rows"] == len(panel) for r in res["legacy"])
    assert all(r["n_rows"] == len(panel) for r in res["triple_barrier"])
    assert all(r["n_features"] == len(features) for r in res["legacy"] + res["triple_barrier"])
    assert res["report"].endswith("wi016_legacy_comparison_USD.md")
    assert (tmp_path / "wi016_legacy_comparison_USD.md").exists()


# --------------------------------------------------------------------------- #
# Step 5 — probe gate outcome
# --------------------------------------------------------------------------- #
def test_probe_gate_clears_a_real_signal(tmp_path):
    panel = _panel(signal=True)
    res = probe_gate(panel, ["f_signal", "f_noise"], market="USD", k_values=(1.5,), horizons=(8,),
                     out_dir=tmp_path)
    assert res["outcome"] == "CLEAR"
    assert res["cleared_targets"] == ["tb_label_k15_h8"]
    d = res["decisions"][0]
    assert d["best_feature"] == "f_signal"
    assert (tmp_path / "wi016_probe_USD.md").exists()


def test_probe_gate_not_clear_without_signal(tmp_path):
    panel = _panel(signal=False)
    # A target that is constant carries no IC at all -> deterministic NO_CLEAR.
    panel["tb_label_k15_h8"] = 0.0
    res = probe_gate(panel, ["f_signal", "f_noise"], market="USD", k_values=(1.5,), horizons=(8,),
                     out_dir=tmp_path)
    assert res["outcome"] == "NOT_CLEAR"
    assert res["cleared_targets"] == []
