"""WI-063 — L1.5 meta-label driver tests (Layer 1 predictive only; synthetic only).

No reads under `data/` or `reports/`; the smoke CLI writes only under /tmp.
Run: `uv run pytest tests/test_run_meta_label.py -q --tb=short --maxfail=1`
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from scripts import run_meta_label as drv
from src.swing_bsh import meta_label_ext as ml

N, SEED, N_SPLITS = 900, 11, 3
SMOKE_OUT = Path("/tmp/wi063_meta_label_smoke_test")


@pytest.fixture(scope="module")
def separated() -> dict:
    """Real-signal fixture: one feature drives the meta label."""
    panel = drv.synthetic_panel(n=N, seed=SEED)
    return drv.meta_label_payload(panel, "USD", n_splits=N_SPLITS)


@pytest.fixture(scope="module")
def permuted() -> dict:
    """Null fixture: labels shuffled against the features (no-leakage control)."""
    panel = drv.synthetic_panel(n=N, seed=SEED, permute=True)
    return drv.meta_label_payload(panel, "USD", n_splits=N_SPLITS)


# --------------------------------------------------------------------------- #
# Contract — Layer-1 payload only
# --------------------------------------------------------------------------- #
def test_payload_is_layer1_and_carries_the_cost_note(separated):
    p = separated
    assert p["layer"] == 1 and p["wi"] == "WI-063"
    assert p["cost"] == ml.DEFAULT_COST == 0.0
    assert "r_frozen" in p["cost_note"]          # cost already inside the outcome
    for key in ("pooled_oof_auc", "folds", "n_rows", "n_labeled", "n_scored",
                "meta_positive_rate", "primary_side_prevalence", "feature_guard"):
        assert key in p
    assert p["n_rows"] == N
    assert p["n_labeled"] > 300                  # half the fixture rows are at_top
    assert p["n_purged"] == p["n_rows"] - p["n_labeled"]
    assert p["n_scored"] >= 100
    assert 0.0 < p["meta_positive_rate"] < 1.0
    assert 0.0 < p["primary_side_prevalence"] < 1.0
    assert all("auc" in f for f in p["folds"])
    # Layer 1 only: no trading artefacts in the payload
    assert not any(k in p for k in ("threshold", "entry_rule", "ev", "positions"))


def test_primary_oof_is_never_a_feature(separated):
    p = separated
    assert p["primary_oof_used_as_feature"] is False
    assert p["feature_guard_ok"] is True
    assert p["feature_guard"] == ml.PRIMARY_PRED_RE
    for name in p["features"]:
        assert not ml.is_primary_prediction_name(name)
    for name in ("r_frozen", "y", "state", "symbol", "date"):
        assert name not in p["features"]
    assert "r_frozen" in p["excluded_feature_columns"]
    assert "state_is_bottom" in p["features"]    # engineered side flag is geometry


def test_feature_guard_rejects_label_and_primary_prediction_columns(separated):
    names = ["geom_score", "atr_pct", "p_buy", "primary_oof", "b_hold", "fwd_ret",
             "y", "r_frozen", "pred", "oof_meta"]
    assert ml.feature_names(names) == ["geom_score", "atr_pct"]
    assert separated["primary_oof_used_as_feature"] is False


# --------------------------------------------------------------------------- #
# Predictive separation + no-leakage null
# --------------------------------------------------------------------------- #
def test_synthetic_separation_gives_meta_auc_above_one_half(separated):
    auc = separated["pooled_oof_auc"]
    assert np.isfinite(auc) and auc > 0.60, auc
    scored = [f for f in separated["folds"] if f.get("n_val", 0) > 0]
    assert len(scored) >= 2
    assert all(f.get("max_train_idx", -1) < f.get("min_val_idx", -1) for f in scored)


def test_permuted_labels_give_meta_auc_near_one_half(permuted):
    auc = permuted["pooled_oof_auc"]
    assert np.isfinite(auc)
    assert abs(auc - 0.5) < 0.10, auc            # null: no fold reads its own OOF
    assert permuted["n_scored"] >= 100


# --------------------------------------------------------------------------- #
# Output paths + smoke CLI
# --------------------------------------------------------------------------- #
def test_smoke_payload_cannot_be_written_to_a_real_path(separated):
    smoke = {**separated, "mode": "smoke"}
    with pytest.raises(ValueError):
        drv.write_outputs(smoke, Path("reports/l15_meta_label"))


def test_smoke_cli_runs_end_to_end_and_writes_only_tmp():
    reports = Path(drv.OUT_DIR)
    before = sorted(reports.glob("meta_label_*.json")) if reports.exists() else []

    SMOKE_OUT.mkdir(parents=True, exist_ok=True)
    for stale in SMOKE_OUT.glob("meta_label_USD.*"):
        stale.unlink()

    assert drv.main(["--market", "USD", "--smoke", "--out", str(SMOKE_OUT)]) == 0
    json_path = SMOKE_OUT / "meta_label_USD.json"
    md_path = SMOKE_OUT / "meta_label_USD.md"
    assert json_path.exists() and md_path.exists()
    payload = json.loads(json_path.read_text())
    assert payload["mode"] == "smoke" and payload["synthetic_fixture"] is True
    assert payload["primary_oof_used_as_feature"] is False
    assert payload["feature_guard_ok"] is True
    assert payload["pooled_oof_auc"] is not None
    assert "pooled OOF AUC" in md_path.read_text()

    after = sorted(reports.glob("meta_label_*.json")) if reports.exists() else []
    assert after == before                       # smoke never touched the real path