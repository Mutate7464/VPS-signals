"""WI-041 — L2 overlay harness tests (D-024 §2 protocol).

Synthetic only: no reads under `data/`, `reports/` or `/tmp`.
Verify: `uv run pytest tests/test_l2_overlay_harness.py -q --tb=short --maxfail=1`
"""

from __future__ import annotations

import numpy as np

from src.l2_overlay import harness as h


def _fx(**kw) -> dict:
    return h.synthetic_fixture("wi037", **kw)


def _run(**kw) -> h.OverlayResult:
    fx = _fx(**kw)
    return h.run_overlay("wi037", "frozen_fib_wi035", fx["probs"], fx["events"], fx["tau_grid"],
                         fx["calib_mask"], fx["eval_mask"], smoke=True)


# --------------------------------------------------------------------------- spec constants
def test_protocol_constants():
    assert h.MIN_CALIB_EVENTS == 200 and h.N_PLACEBO_SEEDS == 5
    assert h.PLACEBO_Z_MIN == 2.0 and h.N_JOBS == 2
    assert h.CALIB_END < h.EVAL_START
    assert h.REPORTS_DIR.parts[-2:] == ("reports", "l2")


# ------------------------------------------------------------------------ decision rule
def test_selection_rule_is_ge_tau_and_finite():
    p = np.array([0.0, 0.29, 0.3, 0.7, np.nan])
    assert h.selected_mask(p, 0.3).tolist() == [False, False, True, True, False]


# ------------------------------------------------------------------------ INERT precheck
def test_inert_when_probability_mass_sits_below_the_tau_range():
    res = _run(inert=True)
    assert res.verdict == "INERT" and "no operating point" in res.inert_reason
    assert not np.isfinite(res.calib_edge) and not np.isfinite(res.eval_edge)
    assert not np.isfinite(res.placebo_z) and res.tau_table == []


def test_inert_when_calib_events_below_the_floor():
    fx = _fx(n_calib=150, n_eval=60)
    res = h.run_overlay("wi037", "b", fx["probs"], fx["events"], fx["tau_grid"],
                        fx["calib_mask"], fx["eval_mask"])
    assert res.verdict == "INERT" and "floor" in res.inert_reason


def test_feasible_requires_the_tau_range_to_span_the_mass():
    rng = np.random.default_rng(0)
    assert h.feasible(rng.random(300), (0.1, 0.7))[0]
    assert not h.feasible(np.full(300, 0.001), (0.1, 0.7))[0]
    assert not h.feasible(np.full(300, 0.99), (0.1, 0.7))[0]


# ---------------------------------------------------------- tau tuned on CALIB edge only
def test_pick_tau_maximises_calib_edge():
    best, table = h.pick_tau_by_calib_edge(np.array([0.2, 0.4, 0.6, 0.8]),
                                           np.array([0.0, 0.0, 0.0, 0.10]),
                                           np.ones(4, bool), (0.3, 0.5, 0.7))
    assert best["tau"] == 0.7 and best["calib_edge"] > 0
    assert [row["tau"] for row in table] == [0.3, 0.5, 0.7]


def test_tau_ignores_whatever_eval_scoring_returns(monkeypatch):
    base = _run()
    monkeypatch.setattr(h, "score_eval", lambda probs, ret, mask, tau: 99.0)
    poisoned = _run()
    assert poisoned.tau == base.tau and poisoned.calib_edge == base.calib_edge
    assert poisoned.eval_edge == 99.0  # EVAL feeds nothing back into the frozen tau


def test_tau_and_calib_edge_are_identical_when_eval_returns_are_poisoned():
    fx = _fx()
    events = fx["events"].copy()
    events.loc[~fx["calib_mask"], "ret"] = 1234.0
    a = h.run_overlay("wi037", "b", fx["probs"], fx["events"], fx["tau_grid"],
                      fx["calib_mask"], fx["eval_mask"])
    b = h.run_overlay("wi037", "b", fx["probs"], events, fx["tau_grid"],
                      fx["calib_mask"], fx["eval_mask"])
    assert a.tau == b.tau and a.calib_edge == b.calib_edge


# ------------------------------------------------------------------------ placebo / verdict
def test_placebo_runs_and_is_deterministic():
    res = _run()
    assert np.isfinite(res.placebo_z) and res.placebo_z >= h.PLACEBO_Z_MIN
    fx = _fx()
    a = h.placebo_z(fx["probs"], fx["events"]["ret"], res.tau)
    b = h.placebo_z(fx["probs"], fx["events"]["ret"], res.tau)
    assert a == b and np.isfinite(a)


def test_verdict_mapping_requires_calib_eval_and_placebo():
    cases = [(0.01, 0.02, 2.5, "ADOPT"), (0.01, 0.02, 2.0, "ADOPT"),
             (0.00, 0.02, 2.5, "REJECT"), (0.01, -0.001, 2.5, "REJECT"),
             (0.01, 0.02, 1.99, "INCONCLUSIVE"), (float("nan"), 0.02, 2.5, "REJECT"),
             (0.01, float("nan"), 2.5, "REJECT")]
    assert [h.classify(*c[:3]) for c in cases] == [c[3] for c in cases]


# ------------------------------------------------------------------------ report / CLI
def test_full_protocol_reports_per_fold_edges():
    res = _run()
    assert res.verdict in {"ADOPT", "REJECT", "INCONCLUSIVE"}
    assert res.tau in set(h.TAU_GRID)
    assert np.isfinite(res.calib_edge) and np.isfinite(res.eval_edge)
    assert {f["fold"] for f in res.folds} == set(range(5))
    assert all({"fold", "n_events", "n_selected", "edge"} <= set(f) for f in res.folds)


def test_explicit_baseline_array_overrides_the_event_column():
    fx = _fx()
    ret = np.asarray(fx["events"]["ret"], dtype="float64")
    res = h.run_overlay("wi037", ret, fx["probs"], fx["events"], fx["tau_grid"],
                        fx["calib_mask"], fx["eval_mask"])
    assert res.baseline == "explicit" and np.isfinite(res.calib_edge)


def test_report_records_the_inert_reason(tmp_path):
    report = h.write_report(_run(inert=True), tmp_path / "wi037.md")
    text = report.read_text()
    assert "**INERT**" in text and "no operating point" in text


def test_cli_smoke_writes_a_synthetic_report(tmp_path):
    assert h.main(["--question", "wi037", "--out", str(tmp_path)]) == 0
    text = (tmp_path / "wi037.md").read_text()
    assert "D-024" in text and "smoke / synthetic fixture" in text
