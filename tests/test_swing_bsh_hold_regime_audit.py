"""WI-039 — regime-conditional `b_hold` audit tests (D-022 phase 2).

Synthetic only: no reads under `data/` or `reports/`. Verify:
`uv run pytest tests/test_swing_bsh_hold_regime_audit.py -q`
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import roc_auc_score

from src.swing_bsh import hold_regime_audit as audit


def test_spec_constants_match_the_wi():
    assert audit.VARIANT == "exact_full_k0.8" and audit.LEARNER == "xgboost"
    assert audit.BINARY == "b_hold" and audit.HORIZONS == (5, 8, 13, 21)
    assert audit.N_SPLITS == 5 and audit.CORE_HOUR_CAP == 0.3
    assert audit.MODEL_DIR.name == "wi036" and audit.REPORT_NAME == "wi039_summary.md"
    assert audit.REGIME_DAILY.name == "regime_daily_extended.csv"
    assert audit.EVAL_START == "2022-07-01"


# --------------------------------------------------------------------------- #
# Join on (symbol, date)
# --------------------------------------------------------------------------- #
def test_join_regime_on_symbol_date_attaches_labels_and_drops_unmatched():
    preds = pd.DataFrame({"symbol": ["A", "A", "B", "C"],
                          "date": pd.to_datetime(["2020-01-01", "2020-01-02",
                                                  "2020-01-01", "2020-01-01"]),
                          "oof": [0.1, 0.9, 0.4, 0.7]})
    reg = pd.DataFrame({"symbol": ["A", "A", "B"],
                        "date": pd.to_datetime(["2020-01-01", "2020-01-02", "2020-01-02"]),
                        "regime": ["chop_normal", "up_high", "chop_normal"]})
    out = audit.join_regime(preds, reg, on=("symbol", "date"))
    assert len(out) == 2                                    # C (no label) and B@01-02 dropped
    got = dict(zip(out["symbol"] + "@" + out["date"].dt.strftime("%m-%d"), out["regime"]))
    assert got == {"A@01-01": "chop_normal", "A@01-02": "up_high"}
    assert out["regime"].notna().all()


def test_market_daily_labels_reduce_to_the_symbol_date_join():
    """Market-daily WI-027 labels: the (symbol, date) join == the own-market (market, date) join."""
    preds = pd.DataFrame({"symbol": ["A", "B", "A"], "market": ["USD"] * 3,
                          "date": pd.to_datetime(["2020-01-01", "2020-01-01", "2020-01-02"]),
                          "oof": [0.2, 0.3, 0.4]})
    daily = pd.DataFrame({"market": ["USD", "USD"], "date": pd.to_datetime(["2020-01-01",
                                                                          "2020-01-02"]),
                          "regime": ["down_high", "up_normal"]})
    by_market = audit.join_regime(preds, daily, on=("market", "date"))
    expanded = preds.merge(daily, on=["market", "date"], how="left")
    by_symbol = audit.join_regime(preds, expanded[["symbol", "date", "regime"]],
                                  on=("symbol", "date"))
    assert by_market["regime"].tolist() == by_symbol["regime"].tolist()
    assert by_market["regime"].tolist() == ["down_high", "down_high", "up_normal"]


# --------------------------------------------------------------------------- #
# Empty-regime rows are dropped, never NaN
# --------------------------------------------------------------------------- #
def test_regime_table_drops_empty_regimes_and_never_emits_nan_rows():
    rng = np.random.default_rng(0)
    n = 400
    frame = pd.DataFrame({"regime": ["chop_normal"] * 300 + ["up_high"] * 100,
                          "h": 13, "oof": rng.random(n),
                          "y_hold": np.r_[rng.integers(0, 2, 300), np.zeros(100, dtype=int)]})
    tbl = audit.regime_table(frame)
    assert set(tbl["regime"]) == {"chop_normal", "up_high"}    # down_high rows simply absent
    assert tbl["regime"].notna().all() and len(tbl) == 2
    assert np.isclose(tbl.loc[tbl["regime"] == "chop_normal", "auc"].iloc[0],
                      roc_auc_score(frame.loc[frame["regime"] == "chop_normal", "y_hold"],
                                    frame.loc[frame["regime"] == "chop_normal", "oof"]))
    assert np.isnan(tbl.loc[tbl["regime"] == "up_high", "auc"].iloc[0])   # single-class cell
    assert audit.regime_table(pd.DataFrame(columns=["regime", "h", "oof", "y_hold"])).empty


# --------------------------------------------------------------------------- #
# Per-regime AUC == the pooled-input formula
# --------------------------------------------------------------------------- #
def test_cell_stats_auc_matches_the_pooled_input_formula():
    rng = np.random.default_rng(1)
    y = rng.integers(0, 2, 500).astype(float)
    p = np.clip(0.5 + 0.25 * (y - 0.5) + rng.normal(0, 0.2, 500), 0.0, 1.0)
    s = audit.cell_stats(y, p)
    assert s["n"] == 500
    assert s["auc"] == pytest.approx(roc_auc_score(y, p))
    assert s["hold_rate"] == pytest.approx(y.mean())
    assert np.isnan(audit.cell_stats(y[:50], p[:50])["auc"])        # n < MIN_N guard
    assert np.isnan(audit.cell_stats(np.zeros(200), rng.random(200))["auc"])


# --------------------------------------------------------------------------- #
# Concentration verdict + fold-consistent OOF + smoke output guard
# --------------------------------------------------------------------------- #
def _cell(auc, n, regime="chop_normal", h=13):
    return {"regime": regime, "h": h, "n": n, "auc": auc, "ic": 0.0, "hold_rate": 0.01}


def test_market_verdict_flags_a_concentrated_regime_and_a_robust_one():
    conc = audit.market_verdict(pd.DataFrame([_cell(0.62, 1000), _cell(0.50, 1000, "up_high")]))
    assert conc["verdict"] == "concentrated" and conc["regime"] == "chop_normal"
    robust = audit.market_verdict(pd.DataFrame([_cell(0.56, 1000), _cell(0.55, 1000, "up_high")]))
    assert robust["verdict"] == "robust" and robust["regime"] is None
    thin = audit.market_verdict(pd.DataFrame([_cell(0.62, 20), _cell(0.50, 10, "up_high")]))
    assert thin["verdict"] == "inconclusive"


class _FakeModel:
    """Mimics `CalibratedBinary.predict_proba`: a 1-D calibrated P(hold) vector."""

    def __init__(self, value):
        self.value = value

    def predict_proba(self, X):
        return np.full(len(X), self.value, dtype="float64")


def test_oof_proba_scores_only_each_folds_own_block():
    fold_id = np.array([0, 0, 1, 1, -1], dtype="int16")
    p = audit.oof_proba(np.zeros((5, 2)), fold_id, {0: _FakeModel(0.2), 1: _FakeModel(0.8)})
    assert p[:2].tolist() == [0.2, 0.2] and p[2:4].tolist() == [0.8, 0.8]
    assert np.isnan(p[4])                                    # rows outside the OOF blocks


def test_resolve_out_dir_keeps_smoke_runs_off_the_real_report():
    assert audit.resolve_out_dir(None, limit=5) != audit.REPORTS_DIR
    assert audit.resolve_out_dir(None, limit=5) == audit.DEFAULT_SMOKE_DIR
    assert audit.resolve_out_dir(None, limit=None) == audit.REPORTS_DIR
    assert audit.resolve_out_dir("/tmp/wi039_smoke", limit=5) == audit.DEFAULT_SMOKE_DIR
    with pytest.raises(ValueError):
        audit.resolve_out_dir(audit.REPORTS_DIR, limit=5)


def test_load_regime_labels_reads_regime_column_and_rejects_label_less_csv(tmp_path):
    good = tmp_path / "regime_daily_extended.csv"
    good.write_text("market,date,r1,r2,regime\nUSD,2020-01-02,1.0,0.5,up_high\n"
                    "CAD,2020-01-02,1.0,0.5,\n")
    out = audit.load_regime_labels(good)
    assert out["regime"].tolist() == ["up_high"]              # empty label dropped
    assert str(out["date"].dtype).startswith("datetime64")
    bad = tmp_path / "regime_daily.csv"
    bad.write_text("market,date,r1,r1_s5,r2,n_tickers\nUSD,2020-01-02,1.0,,0.5,10\n")
    with pytest.raises(ValueError, match="regime"):
        audit.load_regime_labels(bad)
