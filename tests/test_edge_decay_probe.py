"""WI-045 — edge-decay probe tests (frozen WI-042 artifact diagnostic, Layer 1).

Synthetic only: no read under `reports/`, `data/` or `/tmp`. Fixtures are built through the WI-041
harness (`synthetic_record`), so the decomposition identities are checked on data whose CALIB edge
is known, and the `--smoke` path is exercised under `tmp_path`.

Verify: `uv run pytest tests/test_edge_decay_probe.py -q --tb=short --maxfail=1`
"""

from __future__ import annotations

import copy
import json

import numpy as np

from src.l2_overlay import edge_decay_probe as P

PER, NF = 200, 4


def _uniform_cell(name: str = "syn|uniform") -> dict:
    """Half of every fold clears tau -> a uniform kept fraction, so the fold identity is exact."""
    n = PER * NF
    fold = np.repeat(np.arange(NF), PER)
    hi = np.zeros(n, dtype=bool)
    hi[::2] = True                      # within each fold the even index scores high
    return P.synthetic_record(name, np.where(hi, 0.9, 0.1).astype("float32"),
                              np.where(hi, 0.02, -0.01).astype("float32"), fold)


def _payload(cells) -> dict:
    return {"costs_bps": P.COST_BPS, "markets": {"SYN": {"cells": list(cells)}}}


# ------------------------------------------------------------------------------- spec / contract
def test_constants_pin_the_frozen_input_the_cost_floor_and_the_three_mechanisms():
    assert P.INPUT_JSON.name == "rerun_modern.json" and P.INPUT_JSON.parent == P.REPORTS_DIR
    assert P.INPUT_JSON.parent.name == "l2" and P.OUT_STEM == "edge_decay_probe"
    assert P.COST_BPS == 25.0 and P.N_JOBS == 2
    assert P.MECHANISMS == ("tau-mass", "fold-concentration", "cost-floor")
    assert set(P.__all__) >= {"probe_cells", "decompose_cell", "family_ranking", "write_reports"}


def test_only_ratified_adopt_cells_enter_and_each_is_market_tagged():
    payload = {"markets": {
        "USD": {"cells": [{"cell": "q|raw|all", "verdict": "ADOPT"},
                          {"cell": "q|raw|all", "verdict": "INERT"},
                          {"cell": "q|raw|up", "verdict": "REJECT"}]},
        "CAD": {"cells": [{"cell": "q|raw|all", "verdict": "ADOPT"}]}}}
    rows = P.adopt_cells(payload)
    assert [(r["market"], r["cell"]) for r in rows] == [("CAD", "q|raw|all"), ("USD", "q|raw|all")]


def test_probing_a_payload_never_mutates_it():
    payload = _payload(P.synthetic_fixture()["markets"]["SYN"]["cells"])
    before = copy.deepcopy(payload)
    assert len(P.probe_cells(payload)) == 3
    assert payload == before


# ------------------------------------------------------------------------------- decomposition
def test_gross_minus_cost_equals_net_and_the_cost_floor_binds():
    row = P.decompose_cell(_uniform_cell())
    assert row["gross_edge_bps"] - row["cost_bps"] == row["net_edge_bps"]
    assert row["net_edge_bps"] > 0.0                  # the harness picked a positive CALIB edge
    assert row["gross_edge_bps"] == row["net_edge_bps"] + P.COST_BPS
    assert row["cost_floor_binds"] is (row["net_edge_bps"] < P.COST_BPS)
    assert row["cost_floor_binds"] is False           # this fixture clears the 25 bps floor
    cost_cell = {r["cell"]: r for r in P.probe_cells(P.synthetic_fixture())}["syn|raw|cost"]
    assert cost_cell["net_edge_bps"] < P.COST_BPS and cost_cell["cost_floor_binds"] is True
    assert row["weights"]["cost-floor"] == P.COST_BPS / row["gross_edge_bps"]


def test_fold_shares_sum_to_the_calib_edge_when_the_tau_keeps_a_uniform_fraction():
    row = P.decompose_cell(_uniform_cell())
    assert row["mass_retained"] == 0.5                # exactly half of every fold is kept
    assert all(abs(f["n_selected"] / f["n_events"] - 0.5) < 1e-12 for f in row["folds"])
    recon = sum(f["contrib_bps"] for f in row["folds"])
    assert abs(recon - row["net_edge_bps"]) < 1e-9    # identity: contributions reconstruct the edge
    assert abs(row["fold_recon_gap_bps"]) < 1e-9
    pos = sum(f["contrib_bps"] for f in row["folds"] if f["contrib_bps"] > 0.0)
    assert abs(pos - recon) < 1e-9                    # every fold contributes positively here
    assert row["folds"] and all(f["weight"] > 0.0 for f in row["folds"])


def test_fold_concentration_isolates_the_fold_that_carries_the_edge():
    rows = {r["cell"]: r for r in P.probe_cells(P.synthetic_fixture())}
    fold_cell = rows["syn|raw|fold"]
    assert fold_cell["top_fold"] == 2 and fold_cell["top_fold_share"] > 0.9
    assert fold_cell["weights"]["fold-concentration"] == fold_cell["top_fold_share"]
    assert fold_cell["driver"] == "fold-concentration"
    assert P.fold_concentration([{"fold": 0, "n_events": 1, "n_selected": 1, "weight": 1.0,
                                  "edge_bps": -1.0, "contrib_bps": -1.0}]) == (-1, 0.0)


def test_tau_mass_weight_is_the_untraded_calib_fraction():
    rows = {r["cell"]: r for r in P.probe_cells(P.synthetic_fixture())}
    mass_cell = rows["syn|raw|mass"]
    assert mass_cell["mass_retained"] == mass_cell["n_selected"] / mass_cell["n_calib"]
    assert mass_cell["mass_retained"] < 0.25
    assert mass_cell["weights"]["tau-mass"] == 1.0 - mass_cell["mass_retained"]
    assert mass_cell["driver"] == "tau-mass"


def test_shares_are_a_normalised_partition_and_the_driver_is_its_argmax():
    rows = P.probe_cells(P.synthetic_fixture())
    assert {r["driver"] for r in rows} == set(P.MECHANISMS)   # one archetype per mechanism
    for r in rows:
        assert set(r["shares"]) == set(P.MECHANISMS)
        assert abs(sum(r["shares"].values()) - 1.0) < 1e-12
        assert r["driver"] == max(P.MECHANISMS, key=lambda m: r["shares"][m])
        assert all(0.0 <= r["shares"][m] <= 1.0 for m in P.MECHANISMS)


def test_family_ranking_is_one_line_over_every_cell_and_sums_to_one():
    rows = P.probe_cells(P.synthetic_fixture())
    rk = P.family_ranking(rows)
    assert abs(sum(rk["shares"].values()) - 1.0) < 1e-12
    assert rk["order"] == sorted(P.MECHANISMS, key=lambda m: -rk["shares"][m])
    assert sum(rk["cell_wins"].values()) == len(rows) and rk["n_cells"] == len(rows)
    assert rk["decay_bps"] > 0.0
    line = rk["line"]
    assert all(f"{i}. " in line for i in (1, 2, 3))
    assert all(m in line for m in P.MECHANISMS) and len(line.splitlines()) == 1


# ------------------------------------------------------------------------------- smoke / reports
def test_smoke_fixture_is_calib_only_with_one_archetype_per_mechanism():
    payload = P.synthetic_fixture()
    assert payload["probe_input"] == "synthetic:CALIB-only" and payload["smoke"] is True
    rows = P.probe_cells(payload)
    assert [r["market"] for r in rows] == ["SYN"] * 3
    assert all(r["n_eval"] == 0 for r in rows)            # no EVAL rows exist in the fixture
    assert all(r["n_selected"] <= r["n_calib"] for r in rows)
    assert all({f["fold"] for f in r["folds"]} == set(range(NF)) for r in rows)


def test_write_reports_and_the_smoke_cli_land_in_the_out_dir(tmp_path):
    rows = P.probe_cells(P.synthetic_fixture())
    md, js = P.write_reports(rows, P.family_ranking(rows), out_dir=tmp_path,
                             input_path="synthetic:CALIB-only", smoke=True)
    text, data = md.read_text(), json.loads(js.read_text())
    assert data["probe"] == "wi045_edge_decay_probe" and data["smoke"] is True
    assert data["n_cells"] == 3 and data["cost_bps"] == P.COST_BPS
    assert data["ranking"]["line"] in text and "CALIB-only" in text and "Layer 1" in text
    assert "Fold contributions" in text and "no deployment" in text
    assert [c["cell"] for c in data["cells"]] == [r["cell"] for r in rows]
    assert md.name == f"{P.OUT_STEM}.md" and js.name == f"{P.OUT_STEM}.json"
    before = {p.name for p in tmp_path.iterdir()}
    assert P.main(["--smoke", "--out", str(tmp_path / "cli")]) == 0
    made = {p.name for p in (tmp_path / "cli").iterdir()}
    assert made == {f"{P.OUT_STEM}.md", f"{P.OUT_STEM}.json"}
    assert before == {f"{P.OUT_STEM}.md", f"{P.OUT_STEM}.json"}