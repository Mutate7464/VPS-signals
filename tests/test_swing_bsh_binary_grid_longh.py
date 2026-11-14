"""WI-038 — long-horizon gap fill tests (D-022 phase 2).

Synthetic only: no reads under `data/` or `reports/`.
`uv run pytest tests/test_swing_bsh_binary_grid_longh.py -q`
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.swing_bsh import binary_features_ext as ext
from src.swing_bsh import binary_grid, binary_grid_longh as longh
from src.swing_bsh.binary_labels import BINARY_COLUMNS

WIDE_HORIZONS = (5, 8, 13, 21, 34, 55, 89, 144, 233)  # the WI-036 ladder (untouched)


# --------------------------------------------------------------------------- #
# §2 constants: horizon override + embargo = max(20, h)
# --------------------------------------------------------------------------- #
def test_long_horizon_constants_match_the_spec():
    assert longh.LONG_HORIZONS == (34, 55, 89, 144, 233)
    assert set(longh.LONG_HORIZONS) < set(WIDE_HORIZONS)  # the WI-036 tail, not the full ladder
    assert longh.CORE_HOUR_CAP == 2.0
    assert longh.MODEL_DIR.name == "wi038" and "models" in longh.MODEL_DIR.parts
    assert longh.REPORT_NAME == "wi038_summary.md"


def test_embargo_is_max_20_h():
    for h in longh.LONG_HORIZONS:
        assert longh.embargo_for(h) == max(20, h)
    assert longh.horizon_splitter(34).embargo_td == 34
    assert longh.horizon_splitter(144).embargo_td == 144
    assert longh.horizon_splitter(233).embargo_td == 233
    # reuse, not re-derivation: the 20-day floor is the shared WI-033 helper
    assert longh.embargo_for(144) == longh.train.embargo_for([144])


# --------------------------------------------------------------------------- #
# §2 the driver imports the WI-036 machinery (monkeypatched), it does not re-implement
# --------------------------------------------------------------------------- #
def test_driver_imports_machinery_and_overrides_horizons(monkeypatch, tmp_path):
    assert longh.binary_grid is binary_grid
    for name in ("cell_cv", "fit_learner", "run_market", "run_placebo", "bh_fdr", "rank_variants"):
        assert not hasattr(longh, name)  # never re-implemented in the driver
    seen: dict = {}

    def fake_run_market(market, cfg, **kw):
        seen["horizons"] = ext.HORIZONS
        seen["model_dir"] = kw.get("model_dir")
        seen["guarded"] = bool(getattr(binary_grid._panel_and_labels, "_wi038_guarded", False))
        return {"market": market, "cells": [], "skipped": [], "core_sec": 0.0, "X": None,
                "labels": {}, "params": {}, "dates": None, "splitters": {}}

    monkeypatch.setattr(binary_grid, "run_market", fake_run_market)
    monkeypatch.setattr(binary_grid, "run_placebo", lambda results, budget, seeds=5: 0)
    monkeypatch.setattr("src.market_cli.cli_markets", lambda *a, **k: ["USD"])
    monkeypatch.setattr(longh.train, "load_settings", lambda: {})
    monkeypatch.setenv("WI038_SMOKE", "5")

    assert longh.main(["--out", str(tmp_path / "smoke")]) == 0
    assert seen["horizons"] == longh.LONG_HORIZONS          # overridden in place during the run
    assert seen["model_dir"] is None                        # dry run: no wi038 pickles
    assert seen["guarded"] is True                          # one-shot EVAL guard installed
    assert ext.HORIZONS == WIDE_HORIZONS                    # restored afterwards
    assert not getattr(binary_grid.cell_cv, "_wi038_wrapped", False)
    assert not getattr(binary_grid._panel_and_labels, "_wi038_guarded", False)
    assert (tmp_path / "smoke" / longh.REPORT_NAME).exists()  # reported under --out only


def test_dry_run_never_writes_the_real_report(tmp_path):
    assert longh.resolve_out_dir(None, dry_run=True) == Path(longh.DEFAULT_SMOKE_DIR)
    assert longh.resolve_out_dir(None, dry_run=False) == longh.REPORTS_DIR
    with pytest.raises(ValueError):
        longh.resolve_out_dir(longh.REPORTS_DIR, dry_run=True)
    assert longh.resolve_out_dir(tmp_path, dry_run=True) == tmp_path


def test_high_horizon_mode_installs_and_restores():
    with pytest.raises(RuntimeError):
        with longh.high_horizon_mode(longh.LONG_HORIZONS, dry_run=True):
            assert ext.HORIZONS == longh.LONG_HORIZONS
            assert getattr(binary_grid.cell_cv, "_wi038_wrapped", False)
            assert getattr(binary_grid._panel_and_labels, "_wi038_guarded", False)
            raise RuntimeError("boom")
    assert ext.HORIZONS == WIDE_HORIZONS
    assert not getattr(binary_grid.cell_cv, "_wi038_wrapped", False)
    assert not getattr(binary_grid._panel_and_labels, "_wi038_guarded", False)


# --------------------------------------------------------------------------- #
# Report: starved folds are flagged, dropped horizons recorded
# --------------------------------------------------------------------------- #
def test_report_flags_starved_folds_and_records_drops(tmp_path):
    cell = {"market": "USD", "h": 233, "tag": "USD_xgboost_exact_full_k1.0_b_hold_h233",
            "variant": "exact_full_k1.0", "event": "exact", "window": "full", "k": 1.0,
            "binary": "b_hold", "learner": "xgboost", "auc": 0.58, "ic": 0.01, "z": np.nan,
            "p": np.nan, "fold_auc": [], "n_oof": 0, "fdr": False}
    longh.FOLD_COUNTS[cell["tag"]] = {0: 100, 1: 60, 2: 25, 3: 5, 4: 0}
    out = {"results": [{"market": "USD", "cells": [cell], "core_sec": 1.0,
                        "skipped": ["CAD_xgboost_exact_full_k1.0_b_hold_h233"]}],
           "ranking": binary_grid.rank_variants([cell]), "survivors": pd.DataFrame(),
           "n_placebo": 0, "m_total": 960, "dry_run": True, "horizons": longh.LONG_HORIZONS,
           "core_hours": 2.0, "learners": ("xgboost",), "cells": [cell]}
    text = longh.build_report(out, tmp_path / "wi038_summary.md").read_text()
    longh.FOLD_COUNTS.clear()
    assert "FLAGGED" in text and "f3(5)" in text and "f4(0)" in text  # starved folds flagged
    assert "f0(100)" not in text                                      # healthy folds not flagged
    assert "h=233 dropped first" in text                              # dropped horizon recorded
    assert "one-shot EVAL window" in text                             # dry run is honest


# --------------------------------------------------------------------------- #
# Live path: only long horizons are scored, folds are counted (stub learner)
# --------------------------------------------------------------------------- #
class _StubModel:
    method = "isotonic"

    def predict_proba(self, X):
        return np.full(len(X), 0.5)


def test_run_high_h_scores_only_long_horizons_and_counts_folds(tmp_path, monkeypatch):
    n = 900
    rng = np.random.default_rng(0)
    panel = pd.DataFrame({
        "symbol": ["AAA"] * n, "date": pd.date_range("2016-01-04", periods=n, freq="B"),
        "state": ["at_bottom"] * n, "close": rng.uniform(9, 11, n).astype("float32"),
        "atr": np.full(n, 0.5, dtype="float32"), "adx_21": rng.uniform(0, 50, n).astype("float32"),
        "rsi_14": rng.uniform(0, 100, n).astype("float32")})
    keys = [(name, h) for name, _, _, _ in ext.variant_grid() for h in longh.LONG_HORIZONS]
    labels = {k: {b: (rng.random(n) > 0.5).astype("int8") for b in BINARY_COLUMNS} for k in keys}
    monkeypatch.setattr(ext, "build_variant_panel", lambda *a, **k: (panel, labels))
    monkeypatch.setattr(binary_grid, "fit_learner", lambda *a, **k: _StubModel())
    monkeypatch.setattr(binary_grid, "run_placebo", lambda results, budget, seeds=5: 0)
    cfg = {"modeling": {"xgb_params": {"n_estimators": 5}}}
    with longh.high_horizon_mode(longh.LONG_HORIZONS, dry_run=True):
        out = longh.run_high_h(cfg, ["USD"], learners=("xgboost",), horizons=longh.LONG_HORIZONS,
                               out_dir=tmp_path, model_dir=None, limit=None, allow_fixture=False,
                               cache_dir=None, core_hours=10.0, placebo_seeds=0, dry_run=True)
        counts = {k: dict(v) for k, v in longh.FOLD_COUNTS.items()}
    assert {c["h"] for c in out["cells"]} == set(longh.LONG_HORIZONS)
    assert len(out["cells"]) == 8 * 5 * 3 * 1
    assert any(counts.values())                     # folds were actually counted
    assert not list(tmp_path.glob("*.pkl"))         # dry run: no pickles written
