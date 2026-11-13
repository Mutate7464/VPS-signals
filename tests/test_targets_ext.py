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
    assert tg.FAMILIES == ("up", "high_low", "vol_expand", "vol_expand_fwd")
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
    assert grid.FAMILY_REPORT["vol_expand_fwd"] == "t2_grid_volexpandfwd_summary.md"
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
# `vol_expand_fwd` — forward window [t0+1, t0+h] vs the trailing [t0-h+1, t0]
# --------------------------------------------------------------------------- #
def test_vol_expand_fwd_ratio_and_missing_forward_window():
    close = _closes(np.concatenate([_QUIET, _LOUD]))  # 21 bars, 10 h
    t0 = np.array([10], dtype=np.int64)
    assert tg.vol_expand_fwd_labels(close, t0, 10).tolist() == [1]  # loud forward, quiet trailing
    rev = _closes(np.concatenate([_LOUD, _QUIET]))
    assert tg.vol_expand_fwd_labels(rev, t0, 10).tolist() == [0]
    assert tg.vol_expand_fwd_labels(close, t0, 10, threshold=500.0).tolist() == [0]
    # the backward-looking family still answers its own (unchanged) question
    assert tg.vol_expand_labels(close, np.array([20]), 10).tolist() == [1]
    assert tg.vol_expand_labels(rev, np.array([20]), 10).tolist() == [0]


def test_vol_expand_fwd_tail_rows_have_no_forward_window():
    close = _closes(np.concatenate([_QUIET, _LOUD]))  # 21 bars
    t0 = np.array([11, 20, 25], dtype=np.int64)
    assert tg.vol_expand_fwd_labels(close, t0, 10).tolist() == [0, 0, 0]  # t0+h >= n
    assert tg.vol_expand_fwd_labels(close, np.array([10]), 11).tolist() == [0]  # 21 >= 21


def test_vol_expand_fwd_window_holds_only_indices_after_t0():
    h = 5
    t0 = np.array([10], dtype=np.int64)
    # `_closes` return r[j] lands on the log-return of bar j+1 (close[j+1]/close[j])
    spike = np.tile([0.0001, 0.0002], 10)
    spike[10] = 0.06  # the return of bar t0+1: the first bar after t0
    assert tg.vol_expand_fwd_labels(_closes(spike), t0, h).tolist() == [1]
    ref_only = spike.copy()
    ref_only[10] = 0.0001
    ref_only[9] = 0.06  # the return ending at the reference bar itself -> trailing only
    assert tg.vol_expand_fwd_labels(_closes(ref_only), t0, h).tolist() == [0]
    late = spike.copy()
    late[16:] = 0.2  # bars strictly beyond t0 + h
    assert tg.vol_expand_fwd_labels(_closes(late), t0, h).tolist() == [1]


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


# --------------------------------------------------------------------------- #
# WI-058 — forward cross-sectional vol rank (same-date ranks, two families)
# --------------------------------------------------------------------------- #
def _universe(vols, n: int = 40, bar0: int = 10, h: int = 5):
    """`{symbol: closes}` with `vols[symbol]` set on the forward bars `[bar0+1, bar0+h]`."""
    shape = np.array([1.0, -0.8, 1.2, -1.0, 0.9])[:h]
    out = {}
    for symbol, v in vols.items():
        r = np.full(n - 1, 0.0005)
        r[bar0:bar0 + h] = 0.0005 + v * shape
        out[symbol] = _closes(r)
    return out


def _xsec_panel(symbols, bars, dates):
    return pd.DataFrame({"symbol": symbols, "bar": bars, "date": pd.to_datetime(dates)})


def test_xsec_vol_rank_is_a_same_date_rank_over_the_crafted_universe():
    closes = _universe({"A": 0.0002, "B": 0.01, "C": 0.05})
    panel = _xsec_panel(["A", "B", "C"], [10, 10, 10], ["2020-01-06"] * 3)
    cont = tg.xsec_vol_rank_cont_labels(panel, closes, 5)
    assert cont.dtype == np.float32
    assert np.allclose(cont, [0.0, 0.5, 1.0])  # quiet -> loud
    assert tg.xsec_vol_rank_bin_labels(panel, closes, 5).tolist() == [0, 0, 1]
    # ranks are relative: one name per date has no cross-section at all
    solo = _xsec_panel(["C"], [10], ["2020-01-06"])
    assert np.isnan(tg.xsec_vol_rank_cont_labels(solo, closes, 5)[0])


def test_xsec_vol_rank_tail_rows_are_nan_and_bin_zero():
    closes = _universe({"A": 0.0002, "B": 0.05})
    panel = _xsec_panel(["A", "B", "B"], [10, 10, 38], ["2020-01-06", "2020-01-06", "2020-01-07"])
    cont = tg.xsec_vol_rank_cont_labels(panel, closes, 5)
    assert np.isclose(cont[0], 0.0) and np.isclose(cont[1], 1.0)
    assert np.isnan(cont[2])  # 38 + 5 >= 40 -> no forward window
    assert tg.xsec_vol_rank_bin_labels(panel, closes, 5).tolist() == [0, 1, 0]


def test_xsec_vol_rank_reads_only_the_forward_window():
    closes = _universe({"A": 0.0002, "B": 0.01, "C": 0.05})
    panel = _xsec_panel(["A", "B", "C"], [10, 10, 10], ["2020-01-06"] * 3)
    base = tg.xsec_vol_rank_cont_labels(panel, closes, 5)
    past = {s: c.copy() for s, c in closes.items()}
    for c in past.values():
        c[:10] *= 1.5  # bars strictly before t0: no log-return inside the window moves
    assert np.allclose(tg.xsec_vol_rank_cont_labels(panel, past, 5), base)
    late = {s: c.copy() for s, c in closes.items()}
    for c in late.values():
        c[16:] *= 3.0  # bars strictly beyond t0 + h
    assert np.allclose(tg.xsec_vol_rank_cont_labels(panel, late, 5), base)


def test_xsec_families_are_registered_as_their_own_fdr_grids():
    assert tg.XSEC_FAMILIES == ("xsec_vol_rank_bin", "xsec_vol_rank_cont")
    assert tg.FAMILIES == ("up", "high_low", "vol_expand", "vol_expand_fwd")
    assert tg.ALL_FAMILIES == tg.FAMILIES + tg.XSEC_FAMILIES
    assert 0.5 < tg.XSEC_TOP_FRAC < 1.0
    for family in tg.XSEC_FAMILIES:
        assert family in grid.FAMILY_REPORT
        assert len(tg.HORIZONS) * len(grid.LEARNERS) * 2 == 24  # one BH-FDR family each
    assert grid.FAMILY_REPORT["xsec_vol_rank_bin"] == "t2_grid_xsecvolrankbin_summary.md"
    assert grid.FAMILY_REPORT["xsec_vol_rank_cont"] == "t2_grid_xsecvolrankcont_summary.md"
    assert tg.label_key("xsec_vol_rank_bin", "exact", 5) == ("xsec_vol_rank_bin", "exact", 5)


def test_build_targets_panel_wires_the_xsec_families(monkeypatch):
    n, close = 40, _universe({"A": 0.01})
    frame = pd.DataFrame({"date": pd.date_range("2020-01-01", periods=n),
                          "open": close["A"], "high": close["A"] * 1.01,
                          "low": close["A"] * 0.99, "close": close["A"]})
    idx = np.array([10, 12], dtype=np.int64)
    monkeypatch.setattr(tg, "iter_events",
                        lambda *a, **k: iter([("A", frame, idx, np.array(["at_bottom", "at_top"]),
                                               None)]))
    monkeypatch.setattr(tg.ext, "build_variant_panel",
                        lambda *a, **k: (pd.DataFrame({"symbol": ["A"] * 2}), None))
    panel, labels = tg.build_targets_panel("USD", families=tg.XSEC_FAMILIES, horizons=(5,))
    assert len(panel) == 2
    assert set(labels) == {(f, e, 5) for f in tg.XSEC_FAMILIES for e in tg.EVENT_MODES}
    for key, arr in labels.items():
        assert arr.shape == (2,)
        assert arr.dtype == (np.float32 if key[0] == "xsec_vol_rank_cont" else np.int8)


# --------------------------------------------------------------------------- #
# WI-059 — payoff ratio: ATR-normalized MFE/MAE over [t0+1, t0+h]
# --------------------------------------------------------------------------- #
def _mfe_path(t0: int = 2, n: int = 12):
    """Flat path with a +3.0 favourable high and a 1.5 adverse low inside `[t0+1, t0+h]`."""
    close = np.full(n, 10.0)
    low = np.full(n, 9.9)
    high = np.full(n, 10.1)
    high[t0 + 3] = 13.0  # favourable (bottom event): 13.0 - 10.0 = 3.0
    low[t0 + 4] = 8.5    # adverse: 10.0 - 8.5 = 1.5
    return high, low, close, np.full(n, 0.5)


def test_mfe_mae_families_are_their_own_fdr_grids():
    assert tg.MFE_MAE_FAMILIES == ("mfe_mae_bin", "mfe_mae_cont")
    assert tg.MFE_MAE_RATIO_THRESHOLD == 1.0
    assert tg.FAMILIES == ("up", "high_low", "vol_expand", "vol_expand_fwd")
    assert tg.ALL_FAMILIES == tg.FAMILIES + tg.XSEC_FAMILIES
    for family in tg.MFE_MAE_FAMILIES:
        assert family not in tg.ALL_FAMILIES
        assert family in grid.FAMILY_REPORT
        assert len(tg.HORIZONS) * len(grid.LEARNERS) * 2 == 24  # one BH-FDR family each
    assert grid.FAMILY_REPORT["mfe_mae_bin"] == "t2_grid_mfemaebin_summary.md"
    assert grid.FAMILY_REPORT["mfe_mae_cont"] == "t2_grid_mfemaecont_summary.md"
    assert grid.CORE_HOUR_CAP == 2.0  # cap 2.0 core-h per family


def test_mfe_mae_ratio_is_known_on_a_crafted_path():
    high, low, close, atr = _mfe_path()
    t0, bottom = np.array([2], dtype=np.int64), np.array(["at_bottom"])
    cont = tg.mfe_mae_cont_labels(high, low, close, atr, bottom, t0, 5)
    assert cont.dtype == np.float32
    assert np.isclose(cont[0], np.log(2.0), atol=1e-6)  # 3.0/0.5 ATR vs 1.5/0.5 ATR
    assert tg.mfe_mae_bin_labels(high, low, close, atr, bottom, t0, 5).tolist() == [1]
    assert tg.mfe_mae_bin_labels(high, low, close, atr, bottom, t0, 5,
                                 threshold=3.0).tolist() == [0]
    mild = high.copy()
    mild[2 + 3] = 11.0  # 1.0 favourable -> 2 ATR against the 3 ATR adverse
    assert np.isclose(tg.mfe_mae_cont_labels(mild, low, close, atr, bottom, t0, 5)[0],
                      np.log(2.0 / 3.0), atol=1e-6)
    assert tg.mfe_mae_bin_labels(mild, low, close, atr, bottom, t0, 5).tolist() == [0]
    flat = high.copy()
    flat[2 + 3] = 11.5  # 3 ATR favourable == 3 ATR adverse: the ratio is exactly 1
    assert np.isclose(tg.mfe_mae_cont_labels(flat, low, close, atr, bottom, t0, 5)[0], 0.0,
                      atol=1e-6)
    assert tg.mfe_mae_bin_labels(flat, low, close, atr, bottom, t0, 5).tolist() == [0]


def test_mfe_mae_side_implied_direction():
    high, low, close, atr = _mfe_path()
    t0, top = np.array([2], dtype=np.int64), np.array(["at_top"])
    # down-side event: favourable = the lowest low (3 ATR), adverse = the highest high (6 ATR)
    cont = tg.mfe_mae_cont_labels(high, low, close, atr, top, t0, 5)
    assert np.isclose(cont[0], np.log(0.5), atol=1e-6)
    assert tg.mfe_mae_bin_labels(high, low, close, atr, top, t0, 5).tolist() == [0]


def test_mfe_mae_window_starts_at_t0_plus_one_and_stops_at_t0_plus_h():
    high, low, close, atr = _mfe_path()
    t0, bottom = np.array([2], dtype=np.int64), np.array(["at_bottom"])
    base = tg.mfe_mae_cont_labels(high, low, close, atr, bottom, t0, 5)
    ref = high.copy(), low.copy()
    ref[0][2], ref[1][2] = 40.0, 1.0  # the reference bar itself is outside the window
    assert np.allclose(tg.mfe_mae_cont_labels(ref[0], ref[1], close, atr, bottom, t0, 5), base)
    late = high.copy(), low.copy()
    late[0][8], late[1][8] = 40.0, 1.0  # t0 + h = 7: strictly past the window
    assert np.allclose(tg.mfe_mae_cont_labels(late[0], late[1], close, atr, bottom, t0, 5), base)
    first = high.copy(), low.copy()
    first[0][3] = 20.0  # the first bar after t0 does move the label
    assert not np.allclose(tg.mfe_mae_cont_labels(first[0], first[1], close, atr, bottom, t0, 5),
                           base)


def test_mfe_mae_tail_rows_are_nan_and_bin_zero():
    high, low, close, atr = _mfe_path()
    t0 = np.array([2, 7, 11], dtype=np.int64)  # t0 + h = 7 exists; 12 and 16 do not
    bottom = np.array(["at_bottom"] * 3)
    cont = tg.mfe_mae_cont_labels(high, low, close, atr, bottom, t0, 5)
    assert np.isfinite(cont[0]) and np.isnan(cont[1]) and np.isnan(cont[2])
    assert tg.mfe_mae_bin_labels(high, low, close, atr, bottom, t0, 5).tolist() == [1, 0, 0]
    bad = np.zeros(close.size)  # no usable ATR scale -> nothing is defined
    assert np.isnan(tg.mfe_mae_cont_labels(high, low, close, bad, bottom, t0, 5)[0])
    assert tg.mfe_mae_bin_labels(high, low, close, bad, bottom, t0, 5).tolist() == [0, 0, 0]
