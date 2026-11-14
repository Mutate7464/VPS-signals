"""WI-065 — harness upgrade tests (D-027 §4/§7/§8): union loader, pre-registration + EVAL lock,
CALIB stop flag, xsec precheck — plus the D-024 smoke regression guard (outputs reproduce unchanged).

Synthetic only: no reads under `data/`; manifests are written to `tmp_path`.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest

from src.l2_overlay import harness as h

COLS = ["pickle_path", "market", "learner", "variant", "binary", "h", "fold"]


def _manifest(rows) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=COLS)


def _write(tmp_path, name: str, rows) -> "object":
    path = tmp_path / name / "manifest.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    _manifest(rows).to_parquet(path)
    return path


# ------------------------------------------------------------------ union loader (D-027 §4/§8)
def test_union_dedups_overlapping_cell_keys_to_the_expected_count(tmp_path):
    wi040 = _write(tmp_path, "wi040", [
        ["a", "USD", "xgboost", "v1", "b_hold", 5, 0],
        ["b", "USD", "xgboost", "v1", "b_hold", 5, 1],
        ["c", "CAD", "xgboost", "v1", "up", 13, 0]])
    wi048 = _write(tmp_path, "wi048", [
        ["b2", "USD", "xgboost", "v1", "b_hold", 5, 1],     # duplicate cell key
        ["d", "USD", "xgboost", "v1", "up", 13, 0]])
    union = h.load_union((wi040, wi048))
    assert len(union) == 4                                   # 5 raw rows, 1 duplicate dropped
    assert union["cell_key"].is_unique
    rep = union.attrs["union_report"]
    assert rep["n_raw"] == 5 and rep["n_union"] == 4 and rep["n_dropped"] == 1
    assert rep["per_source"] == [{"source": "wi040", "rows": 3}, {"source": "wi048", "rows": 2}]


def test_assert_no_duplicate_cells_flags_a_repeated_key():
    dup = _manifest([["a", "USD", "xgboost", "v1", "b_hold", 5, 0]] * 2)
    with pytest.raises(ValueError, match="entered twice"):
        h.assert_no_duplicate_cells(dup)


def test_assert_no_duplicate_cells_needs_the_cell_key_columns():
    with pytest.raises(KeyError, match="cell-key columns"):
        h.assert_no_duplicate_cells(pd.DataFrame({"market": ["USD"]}))


# --------------------------------------------------- pre-registration (sha256) + EVAL lock
def test_preregistration_hash_round_trips_and_detects_tampering(tmp_path):
    path = h.write_preregistration(h.preregistration_template(), tmp_path / "prereg.json")
    payload = h.load_preregistration(path)                    # verifies the sha256
    assert payload["hash"] == h.prereg_hash(payload)
    assert payload["materiality_floor_bps"] == h.MATERIALITY_FLOOR_BPS == 10.0
    assert payload["params"]["min_names_per_date"] == 20 and payload["eval_lock_released"] is False
    body = json.loads(path.read_text())
    body["materiality_floor_bps"] = 0.0                       # tamper after the hash was frozen
    path.write_text(json.dumps(body))
    with pytest.raises(ValueError, match="hash mismatch"):
        h.load_preregistration(path)


def test_prereg_hash_ignores_its_own_field():
    base = h.preregistration_template()
    assert h.prereg_hash(dict(base, hash="deadbeef")) == h.prereg_hash(base)


def test_eval_read_is_blocked_until_the_lock_is_released():
    locked = h.preregistration_template()                     # eval_lock_released False
    called: list[int] = []

    def loader(*a, **k):
        called.append(1)
        return "EVAL"

    with pytest.raises(h.EvalLockError):
        h.assert_eval_unlocked(locked)
    with pytest.raises(h.EvalLockError):
        h.eval_read(loader, locked)
    assert called == []                                       # EVAL never touched while locked
    released = dict(locked, eval_lock_released=True)
    h.assert_eval_unlocked(released)
    assert h.eval_read(loader, released) == "EVAL" and called == [1]


# ------------------------------------------------------------ CALIB stop flag (D-027 §7/§11)
def test_calib_stop_below_the_materiality_floor():
    ok = {"fold_ceiling_ok": True, "max_fold_share": 0.2, "n_positive_folds": 5, "n_folds": 5}
    assert h.calib_stop(25.0, ok)["stop"] is False
    assert h.calib_stop(10.0, ok)["stop"] is True             # boundary: floor is exclusive
    assert "materiality floor" in h.calib_stop(float("nan"), ok)["reasons"][0]


def test_calib_stop_on_a_fold_ceiling_failure():
    bad = {"fold_ceiling_ok": False, "max_fold_share": 0.75, "n_positive_folds": 1, "n_folds": 3}
    stop = h.calib_stop(50.0, bad)
    assert stop["stop"] is True and "fold ceiling" in stop["reasons"][0]


# ------------------------------------------------------------------ xsec precheck (D-027 §7)
def test_xsec_precheck_enforces_names_per_date_and_the_calib_floor():
    rng = np.random.default_rng(3)
    probs = rng.random(240)
    ok, _ = h.xsec_inert_precheck(probs, np.full(20, 30.0))
    assert ok
    thin, reason = h.xsec_inert_precheck(probs, np.array([30.0] * 19 + [5.0]))
    assert not thin and "below the 20-name floor" in reason
    too_few, _ = h.xsec_inert_precheck(rng.random(150), np.full(20, 30.0))
    assert not too_few


# ------------------------------------------------- D-024 smoke regression guard (frozen outputs)
def test_d024_smoke_outputs_reproduce_unchanged():
    """WI-041 behaviour is pinned: the harness upgrade must not move any scored number."""
    fx = h.synthetic_fixture("wi037")
    res = h.run_overlay("wi037", "frozen_fib_wi035", fx["probs"], fx["events"], fx["tau_grid"],
                        fx["calib_mask"], fx["eval_mask"], smoke=True)
    assert res.verdict == "ADOPT" and res.tau == 0.7
    assert res.calib_edge == pytest.approx(0.031415030387414916, rel=1e-12)
    assert res.eval_edge == pytest.approx(0.03570867421472247, rel=1e-12)
    assert res.placebo_z == pytest.approx(38.89829147461478, rel=1e-12)
    assert res.fold_report["max_fold_share"] == pytest.approx(0.218342627657552, rel=1e-12)
    assert [f["fold"] for f in res.folds] == [0, 1, 2, 3, 4]
