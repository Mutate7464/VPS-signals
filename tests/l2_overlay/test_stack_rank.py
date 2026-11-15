"""WI-067 — stack-ranker tests (D-027 §6): correlated cells cluster as expected, the pruning log is
complete, the EVAL lock holds (no EVAL row ever reaches a fit), the beats-best-single guard stops the
card when it should, the memory guard extrapolates the smoke scale against the 8 GB ceiling, and the
end-to-end smoke run writes the CALIB card plus the stack-score artifact. Synthetic only: no reads or
writes under `data/`.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.l2_overlay import harness as H
from src.l2_overlay import prune
from src.l2_overlay.constructions import stack_rank as sr


def _fixture(**kw):
    return sr.synthetic_fixture("USD", **kw)


def _block_matrix(n_rows=400, n_per_block=4, seed=5):
    """Two correlated blocks (ρ≈0.95 inside, ≈0 across): the clustering must recover both."""
    rng = np.random.default_rng(seed)
    a, b = rng.normal(size=n_rows), rng.normal(size=n_rows)
    cols = {}
    for i in range(n_per_block):
        cols[f"a{i}"] = (a + rng.normal(0.0, 0.3, n_rows)).astype("float32")
        cols[f"b{i}"] = (b + rng.normal(0.0, 0.3, n_rows)).astype("float32")
    return pd.DataFrame(cols)


def _folds(net_edge_bps, worst_bps=None, ceiling_ok=True):
    """Fold report row: every fold at `net_edge_bps` unless a worse `worst_bps` is supplied."""
    per = {i: float(worst_bps if worst_bps is not None else net_edge_bps) / 1e4 for i in range(5)}
    return {"per_fold_net_edge": per, "max_fold_share": 0.3, "fold_ceiling_ok": ceiling_ok,
            "n_positive_folds": 4, "n_folds": 5}


def _stack_row(net_edge, worst=None, ceiling_ok=True, trades=2.0):
    return {"net_edge_bps": net_edge, "k": 4, "band": 2.0, "horizon": 13, "trades_per_week": trades,
            "fold_report": _folds(net_edge, worst, ceiling_ok), "signal": "stack", "n_trials": 24}


def _single_row(net_edge, worst=None, ceiling_ok=True):
    return {"signal": "xsec_vol_rank_cont", "net_edge_bps": net_edge, "trades_per_week": 2.0,
            "fold_report": _folds(net_edge, worst, ceiling_ok)}


def test_correlated_cells_cluster_by_block():
    matrix = _block_matrix()
    cl = prune.cluster_by_correlation(matrix, threshold=0.7)
    assert len(cl.cluster_rep) == 2
    assert len({cl.cell_cluster[f"a{i}"] for i in range(4)}) == 1
    assert len({cl.cell_cluster[f"b{i}"] for i in range(4)}) == 1
    assert cl.cell_cluster["a0"] != cl.cell_cluster["b0"]
    scores = prune.cluster_scores(matrix, cl)
    assert scores.shape == (400, 2) and scores.to_numpy().dtype == np.float32


def test_pruning_log_lists_every_input_cell_once():
    matrix = _block_matrix(seed=9)
    cl = prune.cluster_by_correlation(matrix, threshold=0.7)
    log = prune.log_frame(cl)
    assert sorted(log["cell"]) == sorted(matrix.columns)
    assert log["cell"].is_unique and len(cl.log) == matrix.shape[1]
    assert set(log["cluster"]) == set(cl.cluster_rep)
    for row in cl.log:                                   # every rep is a member of its own cluster
        assert cl.cell_cluster[row["representative"]] == row["cluster"]
    assert int(log["kept"].sum()) == len(cl.cluster_rep)  # exactly one representative per cluster


def test_uncorrelated_cells_are_never_merged():
    rng = np.random.default_rng(3)
    matrix = pd.DataFrame({f"c{i}": rng.normal(size=200).astype("float32") for i in range(6)})
    cl = prune.cluster_by_correlation(matrix, threshold=0.7)
    assert len(cl.cluster_rep) == 6
    assert all(row["kept"] for row in cl.log)


def test_eval_rows_never_reach_the_fit():
    assert sr.assert_calib_only(list(pd.date_range("2021-01-04", periods=40, freq="B"))) == 40
    with pytest.raises(sr.EvalLeak):
        sr.assert_calib_only([pd.Timestamp("2021-06-01"), pd.Timestamp(H.EVAL_START)])
    fx = _fixture(n_dates=40, n_names=8, n_cells=4)
    panel = fx["panel"]
    X, y = panel[fx["cells"]].to_numpy("float32"), sr.stack_labels(panel["r"])
    assert sr.fit_stack(X, y, dates=panel["date"]).n_folds >= 1     # CALIB dates fit normally
    leaked = panel["date"].to_numpy().copy()
    leaked[-1] = np.datetime64(H.EVAL_START)                        # one EVAL row is enough
    with pytest.raises(sr.EvalLeak):
        sr.fit_stack(X, y, dates=leaked)


def test_purged_folds_embargo_train_from_val_and_only_oof_rows_are_scorable():
    fx = _fixture()
    panel = fx["panel"]
    X = panel[fx["cells"]].to_numpy("float32")
    model = sr.fit_stack(X, sr.stack_labels(panel["r"]), dates=panel["date"])
    assert model.n_folds == sr.N_SPLITS and model.oof.dtype == np.float32
    scored = np.isfinite(model.oof)
    assert 0.5 < scored.mean() < 1.0 and (model.fold_id[scored] >= 0).all()   # no in-sample fill
    assert model.oof[~scored].size and np.isnan(model.oof[~scored]).all()
    for tr, va in sr.purged_splits(panel["date"].to_numpy()):
        gap = np.unique(panel["date"].to_numpy()[va]).min() - np.unique(panel["date"].to_numpy()[tr]).max()
        assert gap >= np.timedelta64(sr.EMBARGO_TD, "D")   # purge: the embargo always separates train/val


def test_guard_stops_when_the_stack_does_not_beat_the_best_single():
    single = _single_row(40.0)
    losing = sr.stack_guard(_stack_row(25.0), single)
    assert losing["stop"] is True and losing["beats_best_single"] is False
    assert any("does not beat the best single" in r for r in losing["reasons"])
    winning = sr.stack_guard(_stack_row(80.0), single)
    assert winning["stop"] is False and winning["beats_best_single"] is True
    concentrated = sr.stack_guard(_stack_row(180.0, ceiling_ok=False), single)
    assert concentrated["stop"] is True
    assert any("fold ceiling" in r for r in concentrated["reasons"])
    # a bigger edge still loses the fold-report half of the guard if one fold lags the single's worst fold
    thinner = sr.stack_guard(_stack_row(60.0, worst=2.0), _single_row(10.0, worst=8.0))
    assert thinner["stop"] is True
    assert any("worst fold" in r for r in thinner["reasons"])
    floored = sr.stack_guard(_stack_row(8.0), _single_row(5.0))
    assert floored["stop"] is True and any("materiality floor" in r for r in floored["reasons"])


def test_memory_guard_extrapolates_the_smoke_scale_and_pauses_above_the_ceiling():
    assert sr.projected_peak_gb(1_000, 10) < sr.projected_peak_gb(*sr.FULL_SCALE)
    assert sr.assert_memory_budget(*sr.FULL_SCALE)["projected_peak_gb"] < sr.MEMORY_CEILING_GB
    with pytest.raises(MemoryError):                     # over the ceiling the card pauses for admin
        sr.assert_memory_budget(5_000_000, 400)


def test_smoke_run_writes_the_card_and_beats_the_best_single(tmp_path):
    fx = _fixture(n_dates=90, n_names=24, n_cells=8)
    res = sr.run_market("USD", fx["panel"], fx["meta"], cells=fx["cells"], regime=fx["regime"],
                        score_root=tmp_path / "scores", report_root=tmp_path / "reports", smoke=True)
    assert res["verdict"] == "CONTINUE" and res["guard"]["beats_best_single"] is True
    assert res["stack"]["net_edge_bps"] > res["single"]["net_edge_bps"]
    assert res["clustering"].cell_cluster.keys() == set(fx["cells"])   # every input cell logged
    assert res["artifact"].exists() and res["report"].exists()
    scores = pd.read_parquet(res["artifact"])
    assert scores["stack_score"].dtype == np.float32 and len(scores) == len(fx["panel"])
    assert 0 < int(np.isfinite(scores["stack_score"]).sum()) < len(scores)   # OOF window only
    text = res["report"].read_text()
    for token in ("| cell | cluster | representative | kept | reason |", "Guard beats-best-single: **YES**",
                  "Stop flag: **CONTINUE**", "purged folds", "regime metafeatures", "Ranker window"):
        assert token in text


def test_guard_compares_stack_and_best_single_on_the_same_oof_window(tmp_path):
    """The reported STOP-on-a-beating-edge symptom: both sides must be tuned on the OOF window only.

    `run_market` tunes the stack **and** `best_single` on the rows carrying a purged-CV OOF score, so the
    fold half of the guard is like for like. Mixing windows (single on the full CALIB panel) would make a
    beating stack fail on the worst-fold clause; this pins the basis to the artifact's scored rows.
    """
    fx = _fixture(n_dates=90, n_names=24, n_cells=8)
    res = sr.run_market("USD", fx["panel"], fx["meta"], cells=fx["cells"], regime=fx["regime"],
                        score_root=tmp_path / "scores", report_root=tmp_path / "reports", smoke=True)
    assert res["verdict"] == "CONTINUE" and res["n_oof_rows"] < res["n_rows"]
    scored = pd.read_parquet(res["artifact"])
    window = scored[np.isfinite(scored["stack_score"].to_numpy("float32"))]
    assert len(window) == res["n_oof_rows"]
    folds = set(window["fold"].tolist())
    assert set(res["stack"]["fold_report"]["per_fold_net_edge"]) == folds
    assert set(res["single"]["fold_report"]["per_fold_net_edge"]) == folds


def test_stopped_stack_emits_no_artifact(tmp_path):
    fx = _fixture(n_dates=90, n_names=24, n_cells=8)
    rng = np.random.default_rng(2)
    dead = fx["panel"].copy()
    for col in [*fx["cells"], *fx["regime"]]:            # the stack's inputs carry nothing to learn
        dead[col] = rng.normal(size=len(dead)).astype("float32")
    meta = fx["meta"].assign(p_oof=rng.random(len(fx["meta"])).astype("float32"))
    res = sr.run_market("USD", dead, meta, cells=fx["cells"], regime=fx["regime"],
                        score_root=tmp_path / "scores", report_root=tmp_path / "reports", smoke=True)
    assert res["guard"]["beats_best_single"] is False and res["guard"]["stop"] is True
    assert res["artifact"] is None and not (tmp_path / "scores").exists()
    assert "**STOP**" in res["report"].read_text()
