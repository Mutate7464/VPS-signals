"""WI-048a — T2 target-family label builders + grid wiring (D-025 tier 2).

Synthetic only: no reads under `data/` or `reports/`. Verify:
`uv run pytest tests/test_targets_ext.py -q`
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

from src.swing_bsh import grid_targets_ext as grid
from src.swing_bsh import targets_ext as tg


# --------------------------------------------------------------------------- #
# Spec: three families x ladder x 2 learners x 2 markets, pinned variants
# --------------------------------------------------------------------------- #
def test_spec_constants_match_the_wi():
    assert tg.FAMILIES == ("up", "high_low", "vol_expand")
    assert tg.HORIZONS == (5, 8, 13, 21, 34, 55)
    assert tg.EVENT_MODES == ("exact", "tol2")
    assert tg.PINNED_EVENT == {"USD": "exact", "CAD": "tol2"}
    assert tg.VOL_RATIO_THRESHOLD == 1.0
    assert grid.LEARNERS == ("xgboost", "lightgbm")
    assert grid.PINNED_VARIANTS == ("exact_full_k0.8", "tol2_full_k0.8")
    assert grid.PRUNE_RHO == 0.3 and grid.CORE_HOUR_CAP == 2.0
    assert grid.FDR_ALPHA == 0.05 and grid.PINNED_K == 0.8
    assert grid.MODEL_DIR.name == "wi048" and grid.SUMMARY_NAME == "t2_targets_ext_summary.md"
    assert grid.FAMILY_REPORT["high_low"] == "t2_grid_highlow_summary.md"
    assert grid.FAMILY_REPORT["vol_expand"] == "t2_grid_volexpand_summary.md"
    # one BH-FDR family per sub-grid: 6 horizons x 2 learners x 2 markets
    assert len(tg.HORIZONS) * len(grid.LEARNERS) * 2 == 24


# --------------------------------------------------------------------------- #
# `up` — close[t+h] > close[t], undefined forward bars are 0
# --------------------------------------------------------------------------- #
def test_up_labels_direction_and_missing_forward_bar():
    close = np.array([10.0, 10.5, 9.0, 11.0, 11.0], dtype="float64")
    t0 = np.array([0, 1, 2, 3], dtype=np.int64)
    lab = tg.up_labels(close, t0, 2)
    assert lab.dtype == np.int8
    assert lab.tolist() == [0, 1, 1, 0]  # 9<10, 11>10.5, 11>9, no bar at t=5
    assert tg.up_labels(close, t0, 4).tolist() == [1, 0, 0, 0]  # t=4 is the last bar


def test_up_labels_do_not_read_past_the_horizon():
    close = np.array([10.0, 10.2, 10.4, 10.6, 10.8, 20.0], dtype="float64")
    t0 = np.array([0], dtype=np.int64)
    assert tg.up_labels(close, t0, 3)[0] == 1
    loud = close.copy()
    loud[4:] = -5.0  # bars strictly beyond t0 + h
    assert tg.up_labels(loud, t0, 3)[0] == 1


# --------------------------------------------------------------------------- #
# `high_low` — side-implied event-window extreme re-touched inside [t0+1, t0+h]
# --------------------------------------------------------------------------- #
def test_high_low_uses_the_side_implied_extreme_at_the_reference_bar():
    high = np.array([11.0, 11.0, 11.0, 11.0, 11.0, 11.0], dtype="float64")
    low = np.array([9.0, 9.5, 8.8, 9.2, 9.4, 9.6], dtype="float64")
    t0 = np.array([2], dtype=np.int64)
    # bottom event: level = low[2] = 8.8 -> re-touched by the bar-2 low itself is excluded
    assert tg.high_low_labels(high, low, np.array(["at_bottom"]), t0, 3).tolist() == [0]
    touched = low.copy()
    touched[4] = 8.79
    assert tg.high_low_labels(high, touched, np.array(["at_bottom"]), t0, 3).tolist() == [1]
    # the same bar outside the window is ignored
    assert tg.high_low_labels(high, touched, np.array(["at_bottom"]), t0, 1).tolist() == [0]
    # top event: level = high[t0]
    assert tg.high_low_labels(high, low, np.array(["at_top"]), t0, 3).tolist() == [1]
    raised = high.copy()
    raised[2] = 16.0  # only the reference bar's extreme moves up -> no re-test
    assert tg.high_low_labels(raised, low, np.array(["at_top"]), t0, 3).tolist() == [0]


def test_high_low_window_boundary_is_inclusive():
    high = np.full(8, 10.0)
    low = np.full(8, 9.0)
    low[1] = 8.0   # the reference bar's low is the event-window extreme
    low[6] = 8.0   # exactly t0 + h
    assert tg.high_low_labels(high, low, np.array(["at_bottom"]), np.array([1]), 5).tolist() == [1]
    assert tg.high_low_labels(high, low, np.array(["at_bottom"]), np.array([1]), 4).tolist() == [0]


# --------------------------------------------------------------------------- #
# `vol_expand` — h log-returns at t0 vs the prior h (same length)
# --------------------------------------------------------------------------- #
def _closes(returns, start: float = 10.0):
    """Bar closes from `n-1` simple returns (`close[i] = close[i-1] * (1 + r[i-1])`)."""
    r = np.asarray(returns, dtype="float64")
    return start * np.concatenate([[1.0], np.cumprod(1.0 + r)])


_QUIET = np.tile([0.0001, 0.0002], 5)
_LOUD = np.tile([0.04, 0.06], 5)


def test_vol_expand_ratio_threshold():
    close = _closes(np.concatenate([_QUIET, _LOUD]))  # 21 bars, t0 = 20
    t0 = np.array([20], dtype=np.int64)
    assert tg.vol_expand_labels(close, t0, 10).tolist() == [1]  # loud now, quiet before
    rev = _closes(np.concatenate([_LOUD, _QUIET]))
    assert tg.vol_expand_labels(rev, t0, 10).tolist() == [0]
    assert tg.vol_expand_labels(np.full(21, 10.0), t0, 5).tolist() == [0]  # zero prior vol
    assert tg.vol_expand_labels(close, np.array([8]), 10).tolist() == [0]  # no prior window
    assert tg.vol_expand_labels(close, np.array([15]), 5).tolist() == [1]
    assert tg.vol_expand_labels(close, np.array([15]), 5, threshold=500.0).tolist() == [0]


def test_vol_expand_reads_only_up_to_the_reference_bar():
    close = _closes(np.concatenate([_QUIET, _LOUD]))
    t0 = np.array([15], dtype=np.int64)
    before = tg.vol_expand_labels(close, t0, 5)[0]
    assert before == 1
    after = close.copy()
    after[16:] *= 3.0  # forward bars only
    assert tg.vol_expand_labels(after, t0, 5)[0] == before


# --------------------------------------------------------------------------- #
# `target_labels` — all keys, int8, `tol2` = shoulder reference bar
# --------------------------------------------------------------------------- #
def test_target_labels_grid_is_complete_and_int8():
    close = 10.0 + 0.1 * np.arange(60)
    high, low = close + 0.2, close - 0.2
    idx = np.array([10, 30], dtype=np.int64)
    states = np.array(["at_bottom", "at_top"])
    lab = tg.target_labels(high, low, close, idx, states)
    assert len(lab) == len(tg.FAMILIES) * len(tg.EVENT_MODES) * len(tg.HORIZONS)
    for key, arr in lab.items():
        assert key[0] in tg.FAMILIES and key[1] in tg.EVENT_MODES and key[2] in tg.HORIZONS
        assert arr.dtype == np.int8 and arr.shape == (idx.size,)
    assert tg.label_key("up", "exact", 5) == ("up", "exact", 5)
    only_up = tg.target_labels(high, low, close, idx, states, families=("up",), horizons=(5,))
    assert set(only_up) == {("up", "exact", 5), ("up", "tol2", 5)}


def test_tol2_labels_follow_the_shoulder_reference_bar():
    # detected bottom at bar 3, shoulder low one bar later (bar 4) inside the +/-2 window
    close = np.array([10.0, 10.0, 10.0, 10.0, 10.0, 9.0, 9.0, 9.0], dtype="float64")
    high = np.full(8, 10.5)
    low = np.full(8, 9.5)
    low[4] = 8.5
    idx = np.array([3], dtype=np.int64)
    states = np.array(["at_bottom"])
    lab = tg.target_labels(high, low, close, idx, states, families=("up",), horizons=(5,))
    # exact reference bar t0 = 3 -> close[8] does not exist; tol2 t0 = 4 -> close[9] neither
    assert lab[("up", "exact", 5)].tolist() == [0]
    assert lab[("up", "tol2", 5)].tolist() == [0]
    up = tg.target_labels(high, low, np.concatenate([close, [9.9, 10.2]]), idx, states,
                          families=("up",), horizons=(5,))
    assert up[("up", "exact", 5)].tolist() == [0]  # close[8] = 9.9 < close[3] = 10.0
    assert up[("up", "tol2", 5)].tolist() == [1]   # close[9] = 10.2 > close[4] = 10.0


# --------------------------------------------------------------------------- #
# Grid wiring: ranking, FDR multiplicity, sidecar round-trip, empty consolidate
# --------------------------------------------------------------------------- #
def _cell(market, learner, h, auc, ic=0.02, p=0.001, fdr=True):
    return {"market": market, "family": "up", "variant": "exact_full_k0.8", "event": "exact",
            "window": "full", "k": 0.8, "h": h, "binary": "up", "learner": learner,
            "tag": f"{market}_{learner}_exact_full_k0.8_up_h{h}", "auc": auc, "ic": ic,
            "fold_auc": [auc], "n_oof": 100, "n_pos": 40, "z": 2.0, "p": p, "fdr": fdr}


def test_rank_cells_uses_the_cross_market_minimum():
    cells = [_cell("USD", "xgboost", 5, 0.60), _cell("CAD", "xgboost", 5, 0.55),
             _cell("USD", "xgboost", 8, 0.70), _cell("CAD", "xgboost", 8, 0.72),
             _cell("USD", "lightgbm", 5, 0.50)]  # unpaired cell is dropped
    pair = grid.rank_cells(cells)
    assert pair["h"].tolist() == [8, 5]
    assert pair["auc_min"].round(2).tolist() == [0.70, 0.55]


def test_fdr_multiplicity_and_survivor_pickles(tmp_path):
    cells = [_cell("USD", "xgboost", 5, 0.60, p=0.001), _cell("CAD", "xgboost", 5, 0.60, p=0.5)]
    for c in cells:
        c.pop("fdr")
    results = [{"market": c["market"], "cells": [c], "skipped": []} for c in cells]
    assert grid.apply_fdr(results, m_total=24) == 1
    assert [c["fdr"] for c in cells] == [True, False]
    assert grid.save_survivors(results, tmp_path) == 0  # no fitted models held in memory here
    assert grid.write_manifest(cells, tmp_path).exists()


def test_consolidate_winner_attribution_glue(tmp_path, monkeypatch):
    n = 120
    rng = np.random.default_rng(0)
    panel = pd.DataFrame({"state": ["at_bottom"] * n, "date": pd.date_range("2020-01-01", periods=n),
                          "symbol": ["X"] * n, "close": rng.normal(10, 0.1, n),
                          "atr_pct_3": rng.normal(size=n).astype("float32")})
    labels = {tg.label_key("up", "exact", 5): rng.integers(0, 2, n).astype("int8"),
              tg.label_key("up", "tol2", 5): rng.integers(0, 2, n).astype("int8")}
    monkeypatch.setattr(grid, "load_panel", lambda *a, **k: (panel, labels))
    pair = pd.DataFrame([{"family": "up", "learner": "xgboost", "h": 5, "auc_usd": 0.61,
                          "auc_cad": 0.58, "auc_min": 0.58, "ic_min": 0.03}])
    attrs = grid._winner_attribution(pair, model_dir=tmp_path, cache_dir=None, allow_fixture=False)
    assert attrs["cell_id"] == "CAD|xgboost|up|h5"
    assert attrs["treeshap"] and attrs["linear"]
    assert grid._winner_attribution(pd.DataFrame(), model_dir=tmp_path, cache_dir=None,
                                    allow_fixture=False) == {}


def test_sidecar_round_trip_and_empty_consolidate(tmp_path):
    cells = [_cell("USD", "xgboost", 5, 0.60)]
    results = [{"market": "USD", "cells": cells, "skipped": ["CAD_xgboost_up_h5"], "core_sec": 1.0}]
    path = grid.dump_cells("up", results, tmp_path)
    payload = json.loads(path.read_text())
    assert payload["skipped"] == ["CAD_xgboost_up_h5"]
    assert "models" not in payload["cells"][0]
    assert grid._load_cells(tmp_path) == payload["cells"]
    report = grid.build_family_report("up", results, tmp_path / "family.md")
    text = report.read_text()
    assert "min AUC" in text and "FDR survivors" in text and "0.6000" in text
    summary = grid.consolidate(model_dir=tmp_path / "empty", out_dir=tmp_path,
                               cache_dir=None)
    assert "no family cells on disk" in summary.read_text()
    assert (tmp_path / "empty" / "manifest.parquet").exists()
