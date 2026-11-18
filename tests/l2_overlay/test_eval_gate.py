"""WI-071 — one-shot EVAL gate tests (D-027 §5/§7/§11): hash + lock refusals, the one-shot ledger,
BH-FDR over the FULL pre-registered family, the always-present PROVISIONAL tag, and a smoke run that
cannot read any EVAL data (every filesystem/parquet reader is trapped and asserted clean).
Synthetic only: nothing here reads or writes under `data/`.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.l2_overlay import harness as H
from src.l2_overlay.constructions import eval_gate as eg

BASE_DIR = Path(__file__).resolve().parents[2]
FAMILY = [eg.entry_key("b_xsec_topk", m, "b_hold") for m in ("USD", "CAD")]


def _prereg(tmp_path, *, unlocked=True, family=None) -> Path:
    payload = H.preregistration_template()
    payload.update({"fdr_family": list(FAMILY if family is None else family),
                    "eval_lock_released": bool(unlocked), "constructions": ["b_xsec_topk"]})
    return H.write_preregistration(payload, tmp_path / "prereg.json")


# ------------------------------------------------------------------ hash / lock refusals
def test_prereg_hash_mismatch_refuses(tmp_path):
    path = _prereg(tmp_path)
    assert eg.verify_prereg_hash(path)["family_id"] == "l2_rebuild"
    body = json.loads(path.read_text())
    body["materiality_floor_bps"] = 1.0                       # tamper after the freeze
    path.write_text(json.dumps(body, indent=2, sort_keys=True))
    with pytest.raises(ValueError):                            # a mismatch is a hard failure
        eg.verify_prereg_hash(path)


def test_empty_or_duplicated_family_refuses(tmp_path):
    with pytest.raises(eg.FamilyDefect):
        eg.verify_prereg_hash(_prereg(tmp_path, family=[]))
    with pytest.raises(eg.FamilyDefect):
        eg.verify_prereg_hash(_prereg(tmp_path, family=[FAMILY[0], FAMILY[0]]))


def test_held_evallock_refuses_before_any_look(tmp_path):
    payload = eg.verify_prereg_hash(_prereg(tmp_path, unlocked=False))
    eg.reset_ledger()
    fx = H.synthetic_fixture("wi037")
    ret = fx["events"]["ret"].to_numpy("float64")
    with pytest.raises(H.EvalLockError):                       # harness owns the lock
        eg.score_eval_once("k", fx["probs"], ret, fx["eval_mask"], 0.3, prereg=payload)
    assert eg.scored_keys() == frozenset()                     # refused before the ledger moved
    with pytest.raises(H.EvalLockError):
        eg.gate_report(payload, {})


def test_double_scoring_attempt_raises(tmp_path):
    payload = eg.verify_prereg_hash(_prereg(tmp_path))
    eg.reset_ledger()
    fx = H.synthetic_fixture("wi037")
    ret = fx["events"]["ret"].to_numpy("float64")
    first = eg.score_eval_once("k", fx["probs"], ret, fx["eval_mask"], 0.3, prereg=payload)
    assert np.isfinite(first)
    with pytest.raises(eg.DoubleScoringError):
        eg.score_eval_once("k", fx["probs"], ret, fx["eval_mask"], 0.3, prereg=payload)
    assert eg.scored_keys() == frozenset({"k"})


# ------------------------------------------------------------------ BH-FDR over the full family
def test_fdr_is_computed_over_the_full_family_not_per_construction():
    family = [eg.entry_key(c, m, "b_hold") for c in ("b_xsec_topk", "a_time_exits")
              for m in ("USD", "CAD", "GBP")]
    p = {family[0]: 0.002, family[1]: 0.01, family[2]: 0.04}
    p.update({k: float("nan") for k in family[3:]})             # declared INERT members
    out = eg.bh_fdr_across_family(p, family)
    assert out["family_size"] == 6 and out["n_tested"] == 3 and out["n_untested"] == 3
    q = out["q_values"]
    assert q[family[0]] == pytest.approx(0.002 * 6 / 1, rel=1e-12)      # denominator = FULL family
    assert q[family[1]] == pytest.approx(0.01 * 6 / 2, rel=1e-12)       # BH step-up by rank
    assert q[family[2]] == pytest.approx(0.04 * 6 / 3, rel=1e-12)
    assert all(not np.isfinite(q[k]) for k in family[3:])               # untested → no q
    assert out["rejected"][family[0]] and not out["rejected"][family[2]]
    sub = eg.bh_fdr_across_family({k: p[k] for k in family[:3]}, family[:3])
    assert sub["q_values"][family[0]] < q[family[0]]                    # per-construction ≠ family


def test_incomplete_or_foreign_family_members_raise():
    with pytest.raises(eg.FamilyDefect):
        eg.bh_fdr_across_family({FAMILY[0]: 0.01}, FAMILY)      # a member was never declared
    with pytest.raises(eg.FamilyDefect):
        eg.bh_fdr_across_family({FAMILY[0]: 0.01, FAMILY[1]: 0.02, "other|USD|s": 0.03}, FAMILY)
    with pytest.raises(eg.FamilyDefect):
        eg.bh_fdr_across_family({FAMILY[0]: 0.01}, [FAMILY[0], FAMILY[0]])


# ------------------------------------------------------------------ labels / provisional tag
def test_labels_use_the_floor_and_the_mandatory_fold_report():
    ok = {"fold_ceiling_ok": True, "max_fold_share": 0.3}
    assert eg.label_for(12.0, ok, 0.001) == "ADOPT"
    assert eg.label_for(12.0, ok, 0.20) == "INCONCLUSIVE"                 # survives BH? no
    assert eg.label_for(4.0, ok, 0.001) == "REJECT"                       # < 10 bps floor
    assert eg.label_for(12.0, {"fold_ceiling_ok": False}, 0.001) == "REJECT"
    assert eg.label_for(float("nan"), ok, 0.001) == "REJECT"
    assert eg.label_for(12.0, None, 0.001) == "REJECT"                    # fold report is mandatory


def test_verdict_labels_always_carry_the_provisional_tag(tmp_path):
    fold = {"max_fold_share": 0.3, "fold_ceiling_ok": True, "n_folds": 5, "n_positive_folds": 4}
    records = [dict(key=FAMILY[0], construction="b_xsec_topk", market="USD", signal="b_hold",
                    net_edge_bps=14.0, q_value=0.004, fold_report=fold, label="ADOPT"),
               dict(key=FAMILY[1], construction="b_xsec_topk", market="CAD", signal="b_hold",
                    net_edge_bps=-3.0, q_value=0.7,
                    fold_report={"fold_ceiling_ok": False}, label="REJECT")]
    written = eg.emit_verdicts(records, tmp_path)
    payload = json.loads(written["json"].read_text())
    assert payload["provisional"] is True and payload["tag"] == eg.PROVISIONAL_TAG
    assert payload["verdict_counts"] == {"ADOPT": 1, "REJECT": 1}
    assert all(r["status"] == eg.PROVISIONAL_TAG and "PROVISIONAL" in r["label_tagged"]
               for r in payload["verdicts"])
    md = written["md"].read_text()
    assert "ADOPT (PROVISIONAL)" in md and "REJECT (PROVISIONAL)" in md
    assert "admin ratifies in chat" in md


def test_emit_verdicts_refuses_an_unknown_label(tmp_path):
    with pytest.raises(ValueError):
        eg.emit_verdicts([{"key": "k", "construction": "c", "market": "m", "signal": "s",
                           "net_edge_bps": 1.0, "label": "ADOPTED"}], tmp_path)


# ------------------------------------------------------------------ smoke: no EVAL read at all
def test_smoke_writes_to_tmp_reads_no_eval_data_and_prints_few_lines(tmp_path, monkeypatch, capsys):
    reads: list[str] = []
    data_root = str(BASE_DIR / "data") + "/"

    def guard(path):
        p = str(path)
        reads.append(p)
        assert not p.startswith(data_root), f"smoke touched data/: {p}"

    for attr in ("read_text", "read_bytes"):
        orig = getattr(Path, attr)
        monkeypatch.setattr(Path, attr,
                            lambda self, *a, _o=orig, **k: (guard(self), _o(self, *a, **k))[1])
    monkeypatch.setattr(pd, "read_parquet",
                        lambda *a, **k: (_ for _ in ()).throw(AssertionError("read_parquet called")))

    assert eg.main(["--smoke", "--out", str(tmp_path)]) == 0
    assert reads, "the reader trap never fired — the no-EVAL-read proof is not live"
    payload = json.loads((tmp_path / eg.VERDICTS_JSON).read_text())
    family = eg.smoke_family()
    assert payload["provisional"] is True and payload["family_size"] == len(family) == 8
    assert all(len(r["key"].split("|")) == 3 for r in payload["verdicts"])   # construction×market×signal
    assert all(r["status"] == eg.PROVISIONAL_TAG for r in payload["verdicts"])
    assert eg.scored_keys() == frozenset(r["key"] for r in payload["verdicts"])
    assert (tmp_path / H.PREREG_NAME).exists() and (tmp_path / eg.VERDICTS_MD).exists()
    assert len(capsys.readouterr().out.strip().splitlines()) <= 5
