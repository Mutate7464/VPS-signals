"""WI-044 — L1 learner extension tests (D-024 §2).

Synthetic only: no reads under `data/` or `reports/`.
`uv run pytest tests/test_swing_bsh_learner_ext.py -q`
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from pathlib import Path

from src.swing_bsh import binary_features_ext as ext
from src.swing_bsh import binary_grid, binary_train, learner_ext as le, train

NEW6 = ("lightgbm", "catboost", "random_forest", "extra_trees", "xgboost_isotonic",
        "elasticnet_logistic")


def _block(n: int = 300, seed: int = 0):
    """Small synthetic design block with a learnable signal and ~30% positives."""
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(n, 6)).astype("float32")
    X[::17, 3] = np.nan
    y = (rng.random(n) < 1.0 / (1.0 + np.exp(-2.0 * X[:, 0]))).astype("int8")
    return X[: n // 2], y[: n // 2], X[n // 2:], y[n // 2:]


def _small_params(learner: str) -> dict:
    """Tiny overrides so each fit stays sub-second inside the test session."""
    params = le.new_learner_params()[learner]
    for key, value in (("n_estimators", 25), ("iterations", 25), ("max_iter", 60)):
        if key in params:
            params[key] = value
    return params


# --------------------------------------------------------------------------- #
# §2 learner registry = exactly the six new learners
# --------------------------------------------------------------------------- #
def test_registry_is_exactly_the_six_new_learners():
    assert le.NEW_LEARNERS == NEW6
    assert len(set(le.NEW_LEARNERS)) == 6
    assert not set(le.NEW_LEARNERS) & set(binary_grid.LEARNERS)  # no double-scored learner
    assert set(le.new_learner_params()) == set(NEW6)
    assert set(le.DEP_MODULES) == set(NEW6)


def test_cpu_limits_are_forced_on_lightgbm_and_catboost():
    assert le.new_learner_params()["lightgbm"]["n_jobs"] == 2
    assert le.new_learner_params()["catboost"]["thread_count"] == 2
    # re-imposed even when the caller smuggles other values in
    assert le.learner_kwargs("lightgbm", {"n_jobs": 8})["n_jobs"] == 2
    assert le.learner_kwargs("catboost", {"thread_count": 64})["thread_count"] == 2
    assert le.learner_kwargs("random_forest")["n_jobs"] == 2
    assert le.learner_kwargs("xgboost_isotonic")["n_jobs"] == 2
    assert le.learner_kwargs("elasticnet_logistic")["l1_ratios"] == le.EL_L1_RATIOS
    assert "n_jobs" not in le.learner_kwargs("elasticnet_logistic")  # sklearn >=1.8: saga is serial
    with pytest.raises(ValueError):
        le.learner_kwargs("xgboost")  # the WI-036 learners are not re-plumbed here


def test_xgb_isotonic_inherits_the_wi036_winner_hyperparams():
    cfg = {"modeling": {"xgb_params": {"max_depth": 3, "n_estimators": 40}}}
    params = le.new_learner_params(cfg)["xgboost_isotonic"]
    assert params["max_depth"] == 3 and params["n_estimators"] == 40
    assert le.learner_kwargs("xgboost_isotonic", params)["objective"] == "binary:logistic"


# --------------------------------------------------------------------------- #
# §2 grid constants + embargo = max(20, h)
# --------------------------------------------------------------------------- #
def test_grid_constants_match_the_spec():
    assert le.VARIANTS == ("exact_full_k0.8", "tol2_full_k0.8")
    assert set(le.VARIANTS) <= {v[0] for v in ext.variant_grid()}   # top-2 WI-036 families
    assert le.HORIZONS == (13, 21, 34, 55)
    assert set(le.HORIZONS) < set(ext.HORIZONS)
    assert le.BINARY == "b_hold" and le.BINARY in ext.BINARY_COLUMNS
    assert le.MARKETS == ("USD", "CAD")
    assert le.N_SPLITS == binary_grid.N_SPLITS == 5
    assert le.FDR_ALPHA == binary_grid.FDR_ALPHA == 0.05
    assert le.CORE_HOUR_CAP == 2.0
    assert le.MODEL_DIR.name == "wi044" and "models" in le.MODEL_DIR.parts
    assert le.REPORT_NAME == "wi044_summary.md"
    assert le.fdr_m_total() == 2 * 4 * 1 * 6 * 2 == 96


def test_embargo_is_max_20_h():
    for h in le.HORIZONS:
        assert le.embargo_for(h) == max(20, h)
    assert le.horizon_splitter(13).embargo_td == 20
    assert le.horizon_splitter(55).embargo_td == 55
    # reuse, not re-derivation: the 20-day floor is the shared WI-033 helper
    assert le.embargo_for(21) == train.embargo_for([21])


# --------------------------------------------------------------------------- #
# §2 import guard: all six learners import on a clean env
# --------------------------------------------------------------------------- #
def test_import_guard_loads_all_six_learners():
    modules = le.import_learner_deps()
    assert set(modules) == set(NEW6)
    assert all(mod is not None for mod in modules.values())
    assert modules["lightgbm"].__name__ == "lightgbm"
    assert modules["catboost"].__name__ == "catboost"
    with pytest.raises(ValueError):
        le.import_learner_deps(["nope"])


# --------------------------------------------------------------------------- #
# Registry dispatch: every learner fits + calibrates through the WI-035 hook
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("learner", NEW6)
def test_each_learner_fits_and_calibrates_under_the_mode(learner):
    Xf, yf, Xc, yc = _block()
    with le.learner_extension_mode():
        assert getattr(binary_train._fit_learner, "_wi044_wrapped", False)
        assert getattr(binary_train.learner_params, "_wi044_wrapped", False)
        model = binary_train.fit_calibrated_binary(learner, Xf, yf, Xc, yc,
                                                   _small_params(learner))
    assert model is not None
    assert model.learner == learner
    p = np.asarray(model.predict_proba(Xc), dtype="float64")
    assert p.shape == (len(yc),)
    assert np.isfinite(p).all() and ((0.0 <= p) & (p <= 1.0)).all()
    if learner == "elasticnet_logistic":  # l1_ratio chosen on the calibration block
        assert model.model.l1_ratio in le.EL_L1_RATIOS


def test_xgboost_isotonic_degrades_gracefully_on_a_thin_fold():
    """A fold with a single minority example cannot be split — the base fit is used instead."""
    rng = np.random.default_rng(3)
    X = rng.normal(size=(40, 5)).astype("float32")
    y = np.concatenate([np.zeros(1, dtype="int8"), np.ones(39, dtype="int8")])
    with le.learner_extension_mode():
        model = binary_train.fit_calibrated_binary("xgboost_isotonic", X, y, X, y,
                                                   _small_params("xgboost_isotonic"))
    assert model is not None and np.isfinite(model.predict_proba(X)).all()


def test_registry_matches_fold_params_from_settings_style_cfg():
    cfg = {"modeling": {"xgb_params": {"n_estimators": 30}}}
    with le.learner_extension_mode():
        params = binary_train.learner_params(cfg)
    assert set(NEW6) <= set(params)
    assert params["xgboost_isotonic"]["n_estimators"] == 30      # winner params inherited
    assert params["lightgbm"]["n_jobs"] == 2 and params["catboost"]["thread_count"] == 2
    assert "xgboost" in params and len(params) == 3 + 6


# --------------------------------------------------------------------------- #
# In-place override is restored (grid, binary set, registry, learner hooks)
# --------------------------------------------------------------------------- #
def test_mode_patches_and_restores_everything():
    before = (ext.HORIZONS, ext.BINARY_COLUMNS, ext.variant_grid, binary_grid.LEARNERS,
              binary_train._fit_learner, binary_train.learner_params, binary_grid.cell_cv)
    full_learners = binary_grid.LEARNERS
    with pytest.raises(RuntimeError):
        with le.learner_extension_mode():
            assert ext.HORIZONS == le.HORIZONS
            assert ext.BINARY_COLUMNS == (le.BINARY,)
            assert tuple(v[0] for v in ext.variant_grid()) == le.VARIANTS
            assert binary_grid.LEARNERS == full_learners + NEW6
            assert getattr(binary_grid.cell_cv, "_wi044_wrapped", False)
            le.CALIB_STATS["USD_lightgbm_x_f0"] = {"n": 1}
            raise RuntimeError("boom")
    after = (ext.HORIZONS, ext.BINARY_COLUMNS, ext.variant_grid, binary_grid.LEARNERS,
             binary_train._fit_learner, binary_train.learner_params, binary_grid.cell_cv)
    assert after == before
    assert le.CALIB_STATS == {}                                   # diagnostics never leak out


# --------------------------------------------------------------------------- #
# Calibration diagnostics + report
# --------------------------------------------------------------------------- #
def test_calibration_stats_and_learner_table():
    rng = np.random.default_rng(1)
    y = (rng.random(400) < 0.1).astype("int8")
    oof = np.clip(0.1 * y + rng.normal(0.05, 0.02, 400), 0.0, 1.0)
    stats = le.calibration_stats(y, oof)
    assert stats["n"] == 400 and stats["prevalence"] == pytest.approx(y.mean())
    assert 0.0 <= stats["brier"] <= 1.0 and stats["max_p"] >= stats["mean_p"]
    assert le.calibration_stats(y, np.full(400, np.nan)) == {}    # no OOF predictions

    cells = {f"USD_{ln}_exact_full_k0.8_b_hold_h13": {**stats, "learner": ln, "tag": "t",
                                                      "brier": 0.02 + 0.01 * i}
             for i, ln in enumerate(("lightgbm", "catboost"))}
    table = le.learner_calibration(cells)
    assert set(table["learner"]) == {"lightgbm", "catboost"}
    assert table["cells"].sum() == 2 and table["events"].sum() == 800
    assert list(table["brier"]) == sorted(table["brier"])       # ascending Brier
    assert le.learner_calibration({}).empty


def test_report_renders_ranking_fdr_and_calibration(tmp_path):
    cell = {"market": "USD", "h": 13, "tag": "USD_lightgbm_exact_full_k0.8_b_hold_h13",
            "variant": "exact_full_k0.8", "event": "exact", "window": "full", "k": 0.8,
            "binary": "b_hold", "learner": "lightgbm", "auc": 0.66, "ic": 0.04, "z": 2.9,
            "p": 1e-3, "fold_auc": [], "n_oof": 0, "fdr": True}
    out = {"results": [{"market": "USD", "cells": [cell], "core_sec": 1.0,
                        "skipped": ["CAD_catboost_tol2_full_k0.8_b_hold_h55"]}],
           "cells": [cell], "ranking": binary_grid.rank_variants([cell]),
           "survivors": pd.DataFrame([cell]), "n_placebo": 1, "m_total": le.fdr_m_total(),
           "dry_run": True, "learners": NEW6, "core_hours": 2.0, "core_sec": 1.0,
           "calibration": {"USD_lightgbm_exact_full_k0.8_b_hold_h13": {
               "n": 200, "prevalence": 0.03, "mean_p": 0.04, "max_p": 0.31, "brier": 0.03,
               "learner": "lightgbm", "tag": "USD_lightgbm_exact_full_k0.8_b_hold_h13"}}}
    text = le.build_report(out, tmp_path / le.REPORT_NAME).read_text()
    assert "WI-044" in text and "max p̂" in text and "lightgbm" in text
    assert "no cell survived BH-FDR" not in text                  # the survivor row is rendered
    assert "Smoke/dry run" in text and str(le.fdr_m_total()) in text


def test_resolve_out_dir_never_writes_the_real_report_in_a_dry_run(tmp_path):
    assert le.resolve_out_dir(None, dry_run=True) == Path(le.DEFAULT_SMOKE_DIR)
    assert le.resolve_out_dir(None, dry_run=False) == le.REPORTS_DIR
    with pytest.raises(ValueError):
        le.resolve_out_dir(le.REPORTS_DIR, dry_run=True)
    assert le.resolve_out_dir(tmp_path, dry_run=True) == tmp_path


# --------------------------------------------------------------------------- #
# main(): dry run writes the report under --out only, no wi044 pickles
# --------------------------------------------------------------------------- #
def test_main_dry_run_writes_only_the_smoke_report(monkeypatch, tmp_path):
    seen: dict = {}

    def fake_run_extension(cfg, markets, **kw):
        seen["markets"] = list(markets)
        seen["model_dir"] = kw.get("model_dir")
        seen["dry_run"] = kw.get("dry_run")
        seen["grid"] = (ext.HORIZONS, tuple(v[0] for v in ext.variant_grid()),
                        ext.BINARY_COLUMNS)
        seen["registry"] = binary_grid.LEARNERS
        return {"results": [{"market": m, "cells": [], "skipped": [], "core_sec": 0.0}
                            for m in markets],
                "cells": [], "ranking": pd.DataFrame(), "survivors": pd.DataFrame(),
                "n_placebo": 0, "m_total": le.fdr_m_total(), "dry_run": True,
                "learners": le.NEW_LEARNERS, "core_hours": 2.0, "core_sec": 0.0,
                "calibration": {}}

    monkeypatch.setattr(le, "run_extension", fake_run_extension)
    monkeypatch.setattr("src.market_cli.cli_markets", lambda *a, **k: ["USD", "CAD"])
    monkeypatch.setattr(le.train, "load_settings", lambda: {})
    monkeypatch.setenv("WI044_SMOKE", "5")

    assert le.main(["--out", str(tmp_path / "smoke")]) == 0
    assert seen["markets"] == ["USD", "CAD"] and seen["dry_run"] is True
    assert seen["model_dir"] is None                              # dry run: no wi044 pickles
    assert seen["grid"] == (le.HORIZONS, le.VARIANTS, (le.BINARY,))
    assert seen["registry"] == binary_grid.LEARNERS + NEW6
    assert (tmp_path / "smoke" / le.REPORT_NAME).exists()
    assert not list(tmp_path.rglob("*.pkl"))                      # nothing pickled
    # the full WI-036 grid is restored after main returns
    assert tuple(v[0] for v in ext.variant_grid()) == tuple(v[0] for v in le._CANONICAL_VARIANTS)
    assert ext.HORIZONS == tuple(h for h in (5, 8, 13, 21, 34, 55, 89, 144, 233))
