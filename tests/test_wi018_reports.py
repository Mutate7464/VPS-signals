"""WI-018 step 5 — cross-artifact integrity and regression assertions.

Steps 1-4 each ship their own acceptance self-check. This module is the *cross*
check: the five artifacts must agree with each other and with the frozen
configuration constants, the allowed-write rule must hold (`reports/wi018/` only,
JSON/markdown only, no CSV), and the memo must repeat the verdicts the machine
readables carry. Nothing here re-derives a study result — it only asserts the
artifacts are consistent, which is what makes the WI's evidence auditable.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.wi018 import (
    ATLAS_JSON,
    BOOTSTRAP_BLOCK_DATES,
    BOOTSTRAP_DRAWS,
    BOOTSTRAP_SEED,
    COST_BPS_TOTAL,
    EXPECTED_FEATURE_COLUMNS,
    EXPECTED_USD_SYMBOLS,
    FDR_ALPHA,
    FEATURES_DIR,
    G3_JSON,
    HORIZON,
    MARKET,
    PREFLIGHT_JSON,
    PRIMARY_TARGET,
    PROBE_JSON,
    PRUNE_RECS,
    REPORTS_DIR,
    SECONDARY_TARGETS,
    SUMMARY_MD,
    BINNINGS,
)

ARTIFACTS = (PREFLIGHT_JSON, ATLAS_JSON, PROBE_JSON, G3_JSON)
READABLE = (*ARTIFACTS, SUMMARY_MD)

pytestmark = pytest.mark.skipif(
    not all(Path(path).is_file() for path in READABLE),
    reason="WI-018 artifacts not fully generated yet (steps 1-4)",
)


def _load(path: Path) -> dict:
    return json.loads(Path(path).read_text())


def _check_ok(value) -> bool:
    """Accept both check shapes in this WI: a bool, or `{"ok": bool, ...}`."""
    if isinstance(value, dict):
        return bool(value.get("ok"))
    return bool(value)


def _all_checks_ok(payload: dict) -> bool:
    checks = payload.get("checks") or {}
    assert checks, f"{payload.get('step')}: no self-checks recorded"
    return all(_check_ok(value) for value in checks.values())


# --------------------------------------------------------------------------- #
# presence, scope, provenance
# --------------------------------------------------------------------------- #
def test_every_artifact_is_present_and_writes_stayed_in_the_allowed_place():
    for path in READABLE:
        assert Path(path).is_file(), f"missing artifact {path}"
    for path in Path(REPORTS_DIR).iterdir():
        assert path.suffix in {".json", ".md"}, f"unexpected artifact type {path}"
        assert path.suffix != ".csv", "no shortlist/CSV is shipped by WI-018"
    for step in ("data_probe", "atlas", "probe", "cost_overlay"):
        assert (REPORTS_DIR.parents[1] / "src" / "wi018" / f"{step}.py").is_file()


def test_every_artifact_records_usd_only_scope_and_the_target():
    for path in ARTIFACTS:
        payload = _load(path)
        assert payload["market"] == MARKET
        assert "USD" in payload["scope"] and "CAD" in payload["scope"], path
        assert payload.get("generated_utc")
        assert payload.get("config")
    for path in (ATLAS_JSON, PROBE_JSON, G3_JSON):
        assert _load(path)["target"] == PRIMARY_TARGET


def test_provenance_points_at_the_frozen_wi017_inputs_read_only():
    probe = _load(PROBE_JSON)
    preflight = _load(PREFLIGHT_JSON)
    provenance = probe["input_provenance"]
    assert provenance["preflight_report"].endswith("preflight_USD.json")
    assert provenance["symbols"] == preflight["summary"]["symbols"]
    assert provenance["derived_dir"] == str(FEATURES_DIR.parent / "derived")
    assert provenance["features_dir"] == str(FEATURES_DIR)
    assert provenance["prune_recs"] == str(PRUNE_RECS)
    g3 = _load(G3_JSON)
    assert g3["input_provenance"]["probe_verdict"] == probe["verdict"]
    assert g3["input_provenance"]["symbols"] == preflight["summary"]["symbols"]


# --------------------------------------------------------------------------- #
# counts and gates agree
# --------------------------------------------------------------------------- #
def within_atlas_targets(atlas: dict) -> set[str]:
    return set(atlas["unconditional"])


def test_feature_and_cell_counts_agree_across_atlas_and_probe():
    atlas = _load(ATLAS_JSON)
    probe = _load(PROBE_JSON)
    prune = _load(PRUNE_RECS)
    n_features = atlas["config"]["n_features"]
    assert prune["n_features"] == EXPECTED_FEATURE_COLUMNS
    assert prune["n_keep"] == n_features and prune["n_drop"] + n_features == EXPECTED_FEATURE_COLUMNS
    assert probe["config"]["n_features"] == n_features
    assert len(probe["config"]["features"]) == n_features
    assert sorted(probe["config"]["features"]) == sorted(atlas["config"]["features"]) == sorted(prune["keep_columns"])
    n_states = sum(BINNINGS.values())
    assert atlas["coverage"]["cells_total"] == n_features * n_states
    assert probe["hypotheses"]["n_univariate"] == n_features * n_states * 2
    assert atlas["summary"]["symbols"] == EXPECTED_USD_SYMBOLS == probe["input_provenance"]["symbols"]


def test_probe_family_and_flags_are_internally_consistent():
    probe = _load(PROBE_JSON)
    hyp = probe["hypotheses"]
    assert hyp["n_total"] == hyp["n_univariate"] + hyp["n_conjunction"]
    assert hyp["n_conjunction"] == 2 * hyp["n_conjunction_pairs"]
    if hyp["n_conjunction"]:
        assert hyp["univariate_selection_pass"]["n_rejected"] > 0
        assert hyp["n_survivor_states"] >= 2
    assert probe["g2_pass"] == (hyp["n_survivors"] > 0)
    assert probe["g3_eligible"] == (probe["g2_pass"] and not probe["red_flag"])
    assert probe["g3_skipped"] == (not probe["g3_eligible"])
    assert len(probe["survivors"]) == hyp["n_survivors"]
    density = hyp["survivor_density"]
    assert probe["red_flag"] == bool(density > probe["config"]["survivor_density_red_flag"])
    assert abs(density - hyp["n_survivors"] / hyp["n_total"]) < 1e-12


def test_g3_gate_follows_the_g2_verdict_and_the_memo_follows_both():
    probe = _load(PROBE_JSON)
    g3 = _load(G3_JSON)
    memo = Path(SUMMARY_MD).read_text()
    assert g3["g2_verdict"] == probe["verdict"]
    if probe["g3_eligible"]:
        assert g3["g3_skipped"] is False and g3["g3_decision"] in {"TRADE", "NO_TRADE"}
        assert g3["n_conditions"] == len(probe["survivors"])
        assert g3["n_tradeable"] == sum(1 for c in g3["conditions"] if c["decision"] == "TRADE")
        assert g3["g3_decision"] == ("TRADE" if g3["n_tradeable"] else "NO_TRADE")
    else:
        assert g3["g3_skipped"] is True and g3["g3_decision"] == "SKIPPED"
        assert g3["conditions"] == [] and g3["skip_reason"]
        assert g3["g2_survivors_available"] == len(probe["survivors"])
        if probe["red_flag"]:
            assert "red flag" in g3["skip_reason"]
            assert "NO_TRADE" in memo and "wall" in memo
    assert probe["verdict"] in memo
    assert (g3["g3_decision"] in memo) or (g3["g3_skipped"] and "SKIPPED" in memo)


def test_every_artifact_self_check_passed():
    for path in ARTIFACTS:
        assert _all_checks_ok(_load(path)), f"{path} self-check failed"


# --------------------------------------------------------------------------- #
# frozen configuration
# --------------------------------------------------------------------------- #
def test_reports_record_the_deterministic_configuration():
    probe = _load(PROBE_JSON)
    g3 = _load(G3_JSON)
    atlas = _load(ATLAS_JSON)
    expected_bootstrap = (
        f"circular {BOOTSTRAP_BLOCK_DATES}-date blocks, {BOOTSTRAP_DRAWS} draws, seed {BOOTSTRAP_SEED}"
    )
    for payload in (probe, g3, atlas):
        assert expected_bootstrap in payload["config"]["bootstrap"], payload["step"]
    assert probe["config"]["fdr_alpha"] == FDR_ALPHA
    assert probe["config"]["embargo_td"] == max(20, HORIZON)
    assert probe["config"]["fold_helper"] == "src.wi011.stats.fold_blocks"
    assert g3["config"]["overlay_helper"] == "src.wi016.probe.cost_overlay"
    assert g3["config"]["cost_bps_total"] == COST_BPS_TOTAL == 25.0
    assert g3["config"]["embargo_td"] == probe["config"]["embargo_td"]
    assert g3["config"]["ic_dates"].startswith("held-out folds only")
    assert g3["config"]["executable_output"] is False


def test_secondary_targets_are_robustness_reads_never_selection_targets():
    atlas = _load(ATLAS_JSON)
    probe = _load(PROBE_JSON)
    assert probe["target"] == PRIMARY_TARGET
    assert tuple(probe["config"]["secondary_targets"]) == SECONDARY_TARGETS
    assert probe["config"]["secondary_role"].startswith("robustness reads only")
    # G1 reports the decision target's unconditional split; nothing selects on the
    # secondary targets anywhere in the shipped artifacts.
    assert within_atlas_targets(atlas) == {PRIMARY_TARGET}
    assert within_atlas_targets(atlas) <= {PRIMARY_TARGET, *SECONDARY_TARGETS}


# --------------------------------------------------------------------------- #
# memo
# --------------------------------------------------------------------------- #
def test_memo_is_generated_from_the_artifacts_and_declares_ship_shape():
    memo = Path(SUMMARY_MD).read_text()
    for token in ("G1", "G2", "G3", "NO_TRADE", "assumption", "memo", "Limitations", "Follow-up"):
        assert token in memo, f"memo is missing {token!r}"
    lowered = memo.lower()
    assert "no shortlist csv" in lowered
    assert "no trading integration" in lowered
    assert "no executable rules" in lowered
    for path in (PREFLIGHT_JSON, ATLAS_JSON, PROBE_JSON, G3_JSON):
        assert Path(path).stem in memo, f"memo does not cite {Path(path).name}"


def test_memo_survives_a_missing_optional_artifact():
    # The memo is generated in the same run as G3; it must still render when only
    # the G2 payload is available (the G2-only negative path).
    from src.wi018.cost_overlay import build_summary_markdown

    memo = build_summary_markdown(g3={"g3_skipped": True, "g3_decision": "SKIPPED",
                                      "skip_reason": "G2 verdict G2_FAIL with 0 survivor(s)"},
                                  probe=_load(PROBE_JSON))
    assert "G3" in memo and "SKIPPED" in memo and "NO_TRADE" in memo
    assert "Limitations" in memo and "Follow-up" in memo
