"""WI-042 — modern-L2 rerun tests (D-024 §2 harness wiring).

Synthetic only: no reads under `data/`, `reports/`, the WI-040 manifest or `/tmp`. A synthetic
market and a stub manifest are injected through `run_markets`'s seams, so the cell loop, the
BH-FDR family and the smoke precheck are exercised without touching the frozen library.

Verify: `uv run pytest tests/test_l2_rerun_modern.py -q --tb=short --maxfail=1`
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

from src.l2_overlay import rerun_modern as R

CALIB_N, EVAL_N, REGIMES, HZ = 900, 400, ("up_high", "down_high"), (5, 13, 21)


def _stub_manifest() -> pd.DataFrame:
    """Minimal manifest frame — the loader is synthetic, so no path is ever opened."""
    return pd.DataFrame({"pickle_path": ["/nonexistent/p.pkl"], "market": ["USD"],
                         "learner": [R.LEARNER], "variant": [R.VARIANT], "binary": [R.BINARY],
                         "h": [float(HZ[0])], "fold": [0]})


def _market(market: str = "USD", *, n_calib: int = CALIB_N, n_eval: int = EVAL_N, seed: int = 3) -> dict:
    """Synthetic prepared market: `b_hold` mass spreads for h5/h21, sits under the grid for h13."""
    rng = np.random.default_rng(seed)
    n = int(n_calib) + int(n_eval)
    dates = np.concatenate([np.datetime64("2021-06-01") + np.arange(n_calib),
                            np.datetime64("2022-08-01") + np.arange(n_eval)])
    probs, labels = {}, {}
    for h in HZ:
        p = (rng.random(n) * (0.002 if h == 13 else 0.9)).astype("float32")
        probs[h] = p
        labels[h] = ((p + rng.normal(0.0, 0.05, n)) >= 0.45).astype("int8")   # not separable
    ret = np.where(labels[5] == 1, 0.05, -0.01) + rng.normal(0.0, 0.02, n)
    return {"market": market, "dates": dates, "ret": ret.astype("float64"), "fold": np.arange(n) % 5,
            "probs": probs, "labels": labels,
            "regime": np.array([REGIMES[i % len(REGIMES)] for i in range(n)], dtype=object),
            "notes": {"n_events": n, "n_features": 40, "horizons": sorted(probs),
                      "partial_horizons": [], "n_no_regime": 0}}


def _run(tmp_path, *, smoke: bool = False, market: dict | None = None):
    """Full or smoke run on a synthetic market, reports written under `tmp_path`."""
    mk = market if market is not None else _market()
    s = R.run_markets(("USD",), smoke=smoke, manifest=_stub_manifest(),
                      loader=lambda *_a, **_k: mk)
    return s, R.write_report(s, tmp_path / R.REPORT_NAME), R.write_json(s, tmp_path / R.JSON_NAME)


# ------------------------------------------------------------------------------- question spec
def test_the_four_questions_each_map_to_a_frozen_baseline():
    assert [q["name"] for q in R.QUESTIONS] == ["wi037", "wi033", "wi030", "wi028"]
    assert {q["name"]: q["ref_h"] for q in R.QUESTIONS} == {"wi037": 13, "wi033": 21, "wi030": 34,
                                                            "wi028": 5}
    assert len(set(R.BASELINES.values())) == 4
    assert all("t15_s10_d39_close" in b for b in R.BASELINES.values())
    assert set(R.BASELINES) == {q["name"] for q in R.QUESTIONS}


def test_keep_score_form_and_the_wi042_family_are_pinned():
    assert R.SCORE_FORM == "keep=1-p"          # the harness takes an event iff score >= tau
    assert R.FAMILY_ID.startswith("wi042") and "wi043" not in R.FAMILY_ID


# ------------------------------------------------------------------------------- FDR family
def test_bh_fdr_is_a_monotone_step_up():
    q, rejected = R.bh_fdr([0.001, 0.01, 0.02, 0.5], alpha=0.05)
    assert q.tolist() == sorted(q.tolist()) and rejected.tolist() == [True, True, True, False]
    assert R.bh_fdr([])[0].size == 0


def test_family_is_every_tested_cell_and_excludes_inert_ones(tmp_path):
    s, _rep, _js = _run(tmp_path)
    tested = [c for c in s["cells"] if np.isfinite(c["placebo_z"])]
    untested = [c for c in s["cells"] if not np.isfinite(c["placebo_z"])]
    assert s["family_size"] == len(tested) > 0
    assert all(np.isfinite(c["p_value"]) and np.isfinite(c["q_value"]) for c in tested)
    assert all(np.isnan(c["p_value"]) and np.isnan(c["q_value"]) for c in untested)
    assert {c["question"] for c in s["cells"]} == {q["name"] for q in R.QUESTIONS}
    assert any(c["verdict"] == "INERT" for c in s["cells"])       # thin-mass / missing-cell paths


def test_adopt_requires_family_survival(tmp_path):
    s, _rep, _js = _run(tmp_path)
    assert not any(c["verdict"] == "ADOPT" and c["q_value"] >= s["fdr_alpha"] for c in s["cells"])
    assert all(c["verdict"] in {"INERT", "REJECT", "INCONCLUSIVE", "ADOPT"} for c in s["cells"])


def test_regime_conditioning_cells_join_the_same_family(tmp_path):
    s, _rep, _js = _run(tmp_path)
    assert {c["conditioning"] for c in s["cells"]} >= {"all", *REGIMES}
    assert len({c["cell"] for c in s["cells"]}) == len(s["cells"])   # every cell is distinct


# ------------------------------------------------------------------------------- smoke / EVAL
def test_smoke_stops_at_the_precheck_and_never_scores_eval(tmp_path):
    s, rep, js = _run(tmp_path, smoke=True)
    assert s["smoke"] is True and s["family_size"] == 0
    assert all(not np.isfinite(c["eval_edge"]) and not np.isfinite(c["placebo_z"]) for c in s["cells"])
    assert all(c["reason"].startswith(("INERT", "precheck ok")) for c in s["cells"])
    text, payload = rep.read_text(), json.loads(js.read_text())
    assert "Smoke run" in text and "EVAL withheld (smoke)" in text
    assert payload["smoke"] is True and payload["family"] == R.FAMILY_ID


def test_thin_calib_mass_is_inert_not_a_verdict(tmp_path):
    s, _rep, _js = _run(tmp_path, market=_market(n_calib=150, n_eval=60))
    assert all(c["verdict"] == "INERT" for c in s["cells"])
    assert any("floor" in c["reason"] for c in s["cells"])


# ------------------------------------------------------------------------------- stack source
def test_stack_ignores_the_eval_window_when_it_is_frozen():
    pr = _market()
    calib = pr["dates"] < np.datetime64(R.CALIB_END)
    base = R.stack_scores(pr, 5, calib)
    poisoned = {**pr, "labels": {h: y.copy() for h, y in pr["labels"].items()},
                "ret": pr["ret"].copy()}
    for h in poisoned["labels"]:
        poisoned["labels"][h][~calib] = 1 - poisoned["labels"][h][~calib]   # EVAL labels only
    other = R.stack_scores(poisoned, 5, calib)
    assert np.allclose(base, other) and not np.allclose(base, 0.5)          # a real fit, not a stub


def test_stack_is_absent_without_a_label_or_calib_rows():
    pr = _market()
    calib = pr["dates"] < np.datetime64(R.CALIB_END)
    assert R.stack_scores(pr, 34, calib) is None                            # no h34 label here
    assert R.stack_scores(pr, 5, np.zeros(len(calib), dtype=bool)) is None   # no CALIB rows


# ------------------------------------------------------------------------------- report / CLI
def test_report_lists_each_question_and_the_fdr_table(tmp_path):
    _s, rep, js = _run(tmp_path)
    text, payload = rep.read_text(), json.loads(js.read_text())
    assert all(f"### {q['name']}" in text for q in R.QUESTIONS)
    assert "BH-FDR family (every tested cell)" in text and "PROVISIONAL" in text
    assert payload["baselines"] == R.BASELINES and payload["family"] == R.FAMILY_ID
    assert set(payload["closure"]) == {q["name"] for q in R.QUESTIONS}
    assert payload["cells"] and payload["family_size"] == len(
        [c for c in payload["cells"] if np.isfinite(c["placebo_z"])])


def test_cli_rejects_an_unknown_market():
    assert R.main(["--market", "XXX"]) == 2
