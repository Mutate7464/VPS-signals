"""WI-043 — legacy-L2 rerun tests (D-024 §2 harness wiring).

Synthetic only: no reads under `data/`, `reports/`, the WI-040 manifest or `/tmp`. Two synthetic
markets and a stub manifest are injected through `run_markets`'s seams, so the cell loop, the
cross-market port, the cost rule, the WI-011 cadence gate and the single BH-FDR family are all
exercised without touching the frozen library.

Verify: `uv run pytest tests/test_l2_rerun_legacy.py -q --tb=short --maxfail=1`
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

from src.l2_overlay import harness as H
from src.l2_overlay import rerun_legacy as R
from src.l2_overlay import rerun_modern as M

CALIB_N, EVAL_N, REGIMES, HZ = 800, 300, ("up_high", "down_high"), (5, 13, 34)


def _stub_manifest() -> pd.DataFrame:
    """Minimal manifest frame — the loader is synthetic, so no path is ever opened."""
    return pd.DataFrame({"pickle_path": ["/nonexistent/p.pkl"], "market": ["USD"],
                         "learner": [M.LEARNER], "variant": [M.VARIANT], "binary": [M.BINARY],
                         "h": [float(HZ[0])], "fold": [0]})


def _market(market: str = "USD", *, n_calib: int = CALIB_N, n_eval: int = EVAL_N, seed: int = 3,
            per_day: int = 1, flat: bool = False, inert: bool = False) -> dict:
    """Synthetic prepared market: `b_hold` mass spreads the tau grid, CALIB ends before the freeze."""
    rng = np.random.default_rng(seed)
    calib = np.repeat(np.datetime64("2020-01-06") + np.arange(n_calib // per_day + 1), per_day)[:n_calib]
    ev = np.repeat(np.datetime64("2022-08-01") + np.arange(n_eval // per_day + 1), per_day)[:n_eval]
    dates, n = np.concatenate([calib, ev]), int(n_calib) + int(n_eval)
    probs, labels = {}, {}
    for h in HZ:
        p = (rng.random(n) * (0.001 if inert else 0.9)).astype("float32")
        probs[h] = p
        labels[h] = ((p + rng.normal(0.0, 0.05, n)) >= 0.45).astype("int8")   # not separable
    ret = (np.zeros(n) if flat
           else np.where(labels[5] == 1, 0.05, -0.01) + rng.normal(0.0, 0.02, n))
    return {"market": market, "dates": dates, "ret": ret.astype("float64"), "fold": np.arange(n) % 5,
            "probs": probs, "labels": labels,
            "regime": np.array([REGIMES[i % len(REGIMES)] for i in range(n)], dtype=object),
            "notes": {"n_events": n, "n_features": 40, "horizons": sorted(probs),
                      "partial_horizons": [], "n_no_regime": 0}}


def _run(tmp_path, *, smoke: bool = False, usd: dict | None = None, cad: dict | None = None):
    """Full or smoke run on two synthetic markets, reports written under `tmp_path`."""
    mk = {"USD": usd if usd is not None else _market("USD"),
          "CAD": cad if cad is not None else _market("CAD", seed=5)}
    s = R.run_markets(("USD", "CAD"), smoke=smoke, manifest=_stub_manifest(),
                      loader=lambda market, **_kw: mk[market])
    return s, R.write_report(s, tmp_path / R.REPORT_NAME), R.write_json(s, tmp_path / R.JSON_NAME)


# ------------------------------------------------------------------------------- question spec
def test_the_three_legacy_questions_each_map_to_a_frozen_baseline():
    assert [q["name"] for q in R.QUESTIONS] == ["wi012", "wi018", "wi011"]
    assert {q["name"]: q["ref_h"] for q in R.QUESTIONS} == {"wi012": 5, "wi018": 34, "wi011": 13}
    assert len(set(R.BASELINES.values())) == 3
    assert all(b.endswith(R.FROZEN) for b in R.BASELINES.values())
    assert set(R.BASELINES) == {q["name"] for q in R.QUESTIONS}
    assert {q["name"]: q["judge_markets"] for q in R.QUESTIONS} == {
        "wi012": ("CAD",), "wi018": ("USD",), "wi011": ("USD", "CAD")}   # D-018 Q2: USD only


def test_score_form_and_the_family_id_are_pinned():
    assert R.SCORE_FORM == "keep=1-p"          # the harness takes an event iff score >= tau
    assert R.FAMILY_ID.startswith("wi043") and "wi042" not in R.FAMILY_ID
    assert R.FAMILY_ID != M.FAMILY_ID


# ------------------------------------------------------------------------------- FDR family
def test_the_fdr_family_is_exactly_the_three_legacy_questions(tmp_path):
    assert R.FAMILY == ("wi012", "wi018", "wi011") and len(R.FAMILY) == 3
    s, _rep, _js = _run(tmp_path)
    tested = [c for c in s["cells"] if np.isfinite(c["placebo_z"])]
    assert s["family_questions"] == 3 and s["family"] == R.FAMILY_ID
    assert s["family_size"] == len(tested) > 0
    assert {c["question"] for c in s["cells"]} == set(R.FAMILY)
    assert {c["question"] for c in tested} <= set(R.FAMILY)
    assert all(np.isfinite(c["p_value"]) and np.isfinite(c["q_value"]) for c in tested)
    assert all(np.isnan(c["p_value"]) and np.isnan(c["q_value"])
               for c in s["cells"] if c not in tested)
    assert not any(c["verdict"] == "ADOPT" and c["q_value"] >= s["fdr_alpha"] for c in s["cells"])
    assert all(c["verdict"] in {"INERT", "REJECT", "INCONCLUSIVE", "ADOPT"} for c in s["cells"])


def test_regime_conditioning_cells_join_the_same_family(tmp_path):
    s, _rep, _js = _run(tmp_path)
    assert {c["conditioning"] for c in s["cells"]} >= {"all", *REGIMES}
    assert len({c["cell"] for c in s["cells"] if c["market"] == "USD"}) == len(
        [c for c in s["cells"] if c["market"] == "USD"])


# ------------------------------------------------------------------------------- cross-market
def test_wi012_is_tuned_on_usd_and_judged_on_cad_edges_only(tmp_path):
    s, _rep, _js = _run(tmp_path, cad=_market("CAD", seed=5, flat=True))
    w12 = [c for c in s["cells"] if c["question"] == "wi012"]
    assert w12 and all(c["market"] == "CAD" for c in w12)
    assert all(c["tuned_on"] == "USD" for c in w12)
    judged = [c for c in w12 if np.isfinite(c["calib_edge"])]
    assert judged and all(c["calib_edge"] == 0.0 and c["eval_edge"] == 0.0 for c in judged)
    assert all(c["verdict"] == "REJECT" for c in judged)     # a zero CAD edge cannot ADOPT
    usd = [c for c in s["cells"] if c["question"] == "wi018" and np.isfinite(c["eval_edge"])]
    assert usd and all(c["eval_edge"] != 0.0 for c in usd)   # USD events are not the judge here


# ------------------------------------------------------------------------------- cost overlay
def test_cost_rule_charges_one_round_trip_and_leaves_the_tau_argmax_alone():
    assert np.isclose(R.net_edge(0.0010), 0.0010 - 0.0025)
    assert np.isnan(R.net_edge(float("nan")))
    rng = np.random.default_rng(0)
    p, ret = rng.random(400), rng.normal(0.0, 0.02, 400)
    best, table = H.pick_tau_by_calib_edge(p, ret, np.ones(400, dtype=bool))
    net = [dict(t, calib_edge=R.net_edge(t["calib_edge"])) for t in table]
    picked = min([t for t in net if np.isfinite(t["calib_edge"])],
                 key=lambda d: (-d["calib_edge"], -d["n_selected"], d["tau"]))
    assert picked["tau"] == best["tau"]


def test_wi018_cells_are_net_of_the_extra_round_trip(tmp_path):
    s, _rep, _js = _run(tmp_path)
    assert s["costs_bps"] == R.COST_BPS == 25.0
    w18 = [c for c in s["cells"] if c["question"] == "wi018" and np.isfinite(c["eval_edge"])]
    assert w18 and all(np.isclose(c["eval_edge"], c["gross_eval_edge"] - 0.0025) for c in w18)
    assert all(c["market"] == "USD" for c in w18)


# ------------------------------------------------------------------------------- wi011 cadence
def test_cadence_envelope_separates_a_trigger_from_a_state():
    day = np.datetime64("2021-06-01") + np.arange(300)
    state = np.repeat(day, 3)                                # three names per day -> a state
    ok, why = R.cadence_ok(state, np.ones(state.size, bool), np.ones(state.size, bool))
    assert not ok and "not a trigger" in why
    trigger = day[::2]                                       # one name every other day
    ok_t, why_t = R.cadence_ok(trigger, np.ones(trigger.size, bool), np.ones(trigger.size, bool))
    assert ok_t and why_t == ""


def test_wi011_states_are_inert_without_burning_eval(tmp_path):
    s, _rep, _js = _run(tmp_path, usd=_market("USD", per_day=5))
    gated = [c for c in s["cells"] if c["question"] == "wi011" and "cadence" in c["reason"]]
    assert gated and all(c["verdict"] == "INERT" and np.isnan(c["placebo_z"]) for c in gated)


# ------------------------------------------------------------------------------- smoke / INERT
def test_smoke_stops_at_the_precheck_and_never_scores_eval(tmp_path):
    s, rep, js = _run(tmp_path, smoke=True)
    assert s["smoke"] is True and s["family_size"] == 0
    assert all(not np.isfinite(c["eval_edge"]) and not np.isfinite(c["placebo_z"]) for c in s["cells"])
    assert all(c["reason"].startswith(("INERT", "precheck ok")) for c in s["cells"])
    text, payload = rep.read_text(), json.loads(js.read_text())
    assert "Smoke run" in text and "EVAL withheld (smoke)" in text
    assert payload["smoke"] is True and payload["family"] == R.FAMILY_ID


def test_thin_calib_mass_is_inert_not_a_verdict(tmp_path):
    s, _rep, _js = _run(tmp_path, usd=_market("USD", inert=True), cad=_market("CAD", inert=True))
    assert all(c["verdict"] == "INERT" for c in s["cells"])
    assert any("tau range" in c["reason"] for c in s["cells"])


# ------------------------------------------------------------------------------- report / CLI
def test_report_shape_matches_the_modern_rerun(tmp_path):
    _s, rep, js = _run(tmp_path)
    text, payload = rep.read_text(), json.loads(js.read_text())
    assert all(f"### {q['name']}" in text for q in R.QUESTIONS)
    assert "BH-FDR family (every tested cell)" in text and "PROVISIONAL" in text
    for key in ("family", "family_size", "cells", "markets", "baselines", "closure", "questions"):
        assert key in payload
    assert payload["baselines"] == R.BASELINES and payload["family"] == R.FAMILY_ID
    assert set(payload["closure"]) == set(R.FAMILY)


def test_cli_rejects_an_unknown_market():
    assert R.main(["--market", "XXX"]) == 2
