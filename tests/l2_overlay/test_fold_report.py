"""WI-065 — mandatory fold-report tests (D-027 §7/§11.2): the column is never optional.

A scored run with no fold rows must fail closed (raise), and the concentration share / fold
ceiling must be exact on synthetic edges.
"""
from __future__ import annotations

import json

import pytest

from src.l2_overlay import fold_report as fr


def test_missing_rows_fail_closed():
    for bad in (None, {}, []):
        with pytest.raises(fr.FoldReportMissing):
            fr.fold_report(bad)


def test_require_fold_report_rejects_the_empty_shape_explicitly():
    with pytest.raises(fr.FoldReportMissing):
        fr.require_fold_report([])


def test_per_fold_edges_and_share_are_exact():
    rep = fr.fold_report({0: 0.02, 1: 0.01, 2: 0.01})
    assert rep["per_fold_net_edge"] == {0: 0.02, 1: 0.01, 2: 0.01}
    assert rep["total_net_edge"] == pytest.approx(0.04, rel=1e-12)
    assert rep["max_fold_share"] == pytest.approx(0.5, rel=1e-12)     # 0.02 / 0.04
    assert rep["n_folds"] == 3 and rep["n_positive_folds"] == 3
    assert rep["fold_ceiling_ok"] is True                             # ≤50% AND majority positive


def test_accepts_the_harness_fold_edges_row_shape():
    rows = [{"fold": 0, "edge": 0.03, "n_events": 5}, {"fold": 1, "edge": 0.01, "n_events": 5}]
    rep = fr.fold_report(rows)
    assert rep["per_fold_net_edge"] == {0: 0.03, 1: 0.01}
    assert rep["max_fold_share"] == pytest.approx(0.75, rel=1e-12)
    assert rep["fold_ceiling_ok"] is False                            # 0.03 / 0.04 > 50%


def test_net_edge_must_be_positive_in_a_majority_of_folds():
    rep = fr.fold_report({0: 0.05, 1: -0.01, 2: -0.01})
    assert rep["n_positive_folds"] == 1 and rep["fold_ceiling_ok"] is False


def test_non_positive_total_has_no_operating_point():
    rep = fr.fold_report({0: -0.01, 1: -0.02})
    assert rep["max_fold_share"] == float("inf") and rep["fold_ceiling_ok"] is False


def test_write_fold_report_persists_json(tmp_path):
    path = fr.write_fold_report(fr.fold_report({0: 0.02, 1: 0.02}), tmp_path / "fold_report.json")
    assert json.loads(path.read_text())["max_fold_share"] == pytest.approx(0.5, rel=1e-12)
