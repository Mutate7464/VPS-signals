"""WI-037 — P(hold) trade-suppression filter tests (D-022 phase 2).

Synthetic only: no reads under `data/`, `reports/` or `/tmp`. Verify:
`uv run pytest tests/test_swing_bsh_hold_filter.py -q`
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.swing_bsh import hold_filter_gate as hf


# --------------------------------------------------------------------------- #
# Spec constants
# --------------------------------------------------------------------------- #
def test_constants_match_the_wi_spec():
    assert hf.TAU_GRID == (0.5, 0.6, 0.7, 0.8)
    assert (hf.VARIANT, hf.BINARY, hf.HORIZON) == ("exact_full_k0.8", "b_hold", 13)
    assert hf.N_SPLITS == 5 and hf.N_PLACEBO_SEEDS == 5
    assert hf.MODEL_DIR.name == "wi036" and hf.CORE_HOUR_CAP == 0.5
    assert hf.ADOPT_DIR.parts[-3:] == ("data", "models", "wi037")  # ADOPT-only pickles
    assert hf.REPORT_NAME == "wi037_summary.md"
    assert hf.CALIB_END < hf.EVAL_START


# --------------------------------------------------------------------------- #
# Veto rule: keep an entry iff P(hold) < tau (VETO on P >= tau)
# --------------------------------------------------------------------------- #
def test_veto_keeps_only_rows_strictly_below_tau():
    p = np.array([0.0, 0.49, 0.5, 0.6, 0.8, 1.0])
    assert hf.keep_mask(p, 0.5).tolist() == [True, True, False, False, False, False]
    assert hf.keep_mask(p, 0.8).tolist() == [True, True, True, True, False, False]


def test_veto_is_the_intersection_with_finite_probabilities():
    p = np.array([0.1, 0.7, np.nan, 0.3])
    eligible = np.isfinite(p)
    kept = hf.keep_mask(p, 0.5)
    assert kept.tolist() == (eligible & (p < 0.5)).tolist()
    assert not kept[2]  # a NaN probability never survives the intersection


# --------------------------------------------------------------------------- #
# Fold-matched inference: each fold pickle scores only its own OOF rows
# --------------------------------------------------------------------------- #
class _Recorder:
    def __init__(self, value):
        self.value, self.seen = value, []

    def predict_proba(self, X):
        self.seen.append(np.asarray(X, dtype="float64").copy())
        return np.full(len(X), self.value)


def test_oof_hold_proba_maps_each_fold_model_to_its_own_rows():
    X = np.arange(12, dtype="float32").reshape(6, 2)
    fold_id = np.array([0, 0, 1, 1, -1, 2])
    models = {0: _Recorder(0.1), 1: _Recorder(0.7), 2: _Recorder(0.9)}
    p = hf.oof_hold_proba(X, fold_id, models)
    assert np.allclose(p[[0, 1]], 0.1) and np.allclose(p[[2, 3]], 0.7)
    assert np.allclose(p[5], 0.9) and np.isnan(p[4])  # unmapped (-1) rows stay NaN
    for k, model in models.items():
        rows = np.flatnonzero(fold_id == k)
        assert len(model.seen) == 1 and np.array_equal(model.seen[0], X[rows])


def test_oof_hold_proba_leaves_rows_of_absent_fold_models_unscored():
    X = np.arange(6, dtype="float32").reshape(3, 2)
    p = hf.oof_hold_proba(X, np.array([0, 1, 2]), {0: _Recorder(0.2)})
    assert p[0] == pytest.approx(0.2) and np.isnan(p[1:]).all()


# --------------------------------------------------------------------------- #
# tau tuning: CALIB rows only, frozen before EVAL
# --------------------------------------------------------------------------- #
def test_pick_tau_tunes_on_calib_rows_and_ignores_eval_returns():
    frame = pd.DataFrame({
        "date": pd.to_datetime(["2022-01-03"] * 3 + ["2022-08-01"] * 3),
        "p_hold": [0.55, 0.65, 0.75] + [0.55, 0.65, 0.75],
        "r_frozen": [0.04, 0.05, -0.09] + [-9.0, -9.0, -9.0],
    })
    got = hf.pick_tau(frame, min_keep=1)
    assert got["n_calib"] == 3 and got["tau"] == 0.7  # max CALIB edge
    poisoned = frame.copy()
    poisoned.loc[3:, "r_frozen"] = 99.0  # EVAL returns must not move tau
    assert hf.pick_tau(poisoned, min_keep=1)["tau"] == got["tau"]


def test_smoke_drops_the_one_shot_eval_window():
    frame = pd.DataFrame({"date": pd.to_datetime(["2022-06-30", "2022-07-01", "2022-08-01"])})
    out = hf.drop_eval(frame)
    assert out["date"].tolist() == [pd.Timestamp("2022-06-30")]
    assert list(out.index) == [0]


def test_frame_stats_marks_eval_unscored_in_a_dry_run():
    frame = pd.DataFrame({"date": pd.to_datetime(["2022-01-03", "2022-08-01"]),
                          "p_hold": [0.1, 0.2], "r_frozen": [0.01, 0.02],
                          "y_hold": [0.0, 1.0]})
    scored = hf.frame_stats(frame, 0.5, include_eval=True)
    assert scored["eval_scored"] and scored["n_eval"] == 1
    dry = hf.frame_stats(frame, 0.5, include_eval=False)
    assert not dry["eval_scored"] and dry["n_eval"] == 0 and np.isnan(dry["eval_edge"])


# --------------------------------------------------------------------------- #
# Tradeable frame: at-bottom + fold-scored + priced, joined to the baseline
# --------------------------------------------------------------------------- #
def test_tradeable_frame_keeps_at_bottom_scored_rows_with_a_baseline_return():
    panel = pd.DataFrame({
        "symbol": ["AAA", "AAA", "AAA", "BBB", "BBB"],
        "date": pd.to_datetime(["2021-01-04", "2021-01-05", "2021-01-06",
                                "2021-01-04", "2021-01-05"]),
        "state": ["at_bottom", "at_top", "at_bottom", "at_bottom", "at_bottom"],
    })
    baseline = pd.DataFrame({
        "symbol": ["AAA", "BBB", "BBB"],
        "date": pd.to_datetime(["2021-01-04", "2021-01-04", "2021-01-05"]),
        "r_frozen": [0.01, 0.02, 0.03],
    })
    out = hf.tradeable_frame(panel, np.array([0.1, 0.2, np.nan, 0.3, 0.4]),
                             np.array([0, 0, 0, 1, -1]), baseline)
    assert out["symbol"].tolist() == ["AAA", "BBB"]
    assert out["p_hold"].tolist() == [0.1, 0.3] and out["fold"].tolist() == [0, 1]
    assert out["pos"].tolist() == [0, 3]  # positions index the panel/sub arrays


# --------------------------------------------------------------------------- #
# Design matrix: float32, no label / forward-outcome leakage
# --------------------------------------------------------------------------- #
def _toy_panel():
    rng = np.random.default_rng(0)
    n = 24
    return pd.DataFrame({
        "symbol": ["AAA"] * n,
        "date": pd.date_range("2021-01-04", periods=n, freq="D"),
        "state": np.where(np.arange(n) % 2 == 0, "at_bottom", "at_top"),
        "volume_ratio": rng.normal(size=n).astype("float32"),
        "vwap_dist": rng.normal(size=n).astype("float32"),
        "dow": (np.arange(n) % 5).astype("float32"),
        "b_hold": (np.arange(n) % 7 == 0).astype("int8"),
        "r_frozen": rng.normal(size=n).astype("float32"),
    })


def test_design_matrix_is_float32_without_label_or_forward_columns():
    X, feats = hf.design_matrix(_toy_panel())
    assert X.dtype == np.float32 and X.shape[1] == len(feats)
    assert not any(f.startswith(("b_", "r_", "fwd")) for f in feats)
    assert {"state_is_bottom", "k", "horizon"} <= set(feats)


def test_design_matrix_raises_if_a_leak_column_survives_the_filter(monkeypatch):
    panel = _toy_panel()
    monkeypatch.setattr(hf.ext, "candidate_features", lambda _p: ["volume_ratio", "b_hold"])
    _X, feats = hf.design_matrix(panel)  # binary_labels.feature_names() drops b_hold
    assert "b_hold" not in feats
    monkeypatch.setattr(hf.binary_labels, "feature_names", lambda names: list(names))
    monkeypatch.setattr(hf.binary_labels, "kept_features", lambda *_a, **_k: (["b_hold"], {}))
    with pytest.raises(RuntimeError, match="leaked"):
        hf.design_matrix(panel)


# --------------------------------------------------------------------------- #
# Report: dry runs never advertise a scored EVAL window
# --------------------------------------------------------------------------- #
def _toy_result(smoke: bool) -> dict:
    fold = {"fold": 0, "n_events": 3, "n_selected": 2, "baseline_mean": 0.0,
            "model_mean": 0.01, "edge": 0.01, "ic": 0.1, "win": True}
    return {"market": "USD", "verdict": "REJECT", "smoke": smoke, "n_eval_pending": 4,
            "n_oof_folds": 5, "embargo_td": 20, "n_rows": 10, "runtime_sec": 1.0,
            "core_sec": 1.0, "pickle": None,
            "tau": {"tau": 0.5, "n_calib": 2,
                    "table": [{"tau": 0.5, "n_kept": 3, "n_vetoed": 0, "edge": 0.0}]},
            "gate": {"folds": [fold], "n_folds_pos": 0, "n_events": 3, "n_selected": 2,
                     "pooled_baseline": 0.0, "pooled_model": 0.01, "pooled_edge": 0.01},
            "placebo": {"observed_edge": 0.01, "null_mean": 0.0, "null_sd": 0.1,
                        "z": 0.1, "n_seeds": 5},
            "stats": {"n_eval": 0 if smoke else 4, "n_eval_kept": 0,
                      "eval_baseline": float("nan"), "eval_edge": float("nan"),
                      "eval_scored": not smoke, "precision": float("nan"),
                      "prevalence": 0.0, "n_vetoed": 0}}


def test_report_flags_a_smoke_run(tmp_path):
    full = hf.build_report([_toy_result(False)], tmp_path / "full.md")
    assert "NOT scored" not in full.read_text() and "Smoke run" not in full.read_text()
    dry = hf.build_report([_toy_result(True)], tmp_path / "dry.md")
    text = dry.read_text()
    assert "**Smoke run**" in text and "NOT scored" in text and "4 entries withheld" in text