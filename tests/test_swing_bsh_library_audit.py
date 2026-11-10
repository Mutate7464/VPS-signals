"""WI-040 — Layer-1 pickle-library audit tests (D-023 L1).

Synthetic only: fake wi035/wi036/wi038 libraries and a fake WI-036 report under
`tmp_path`; no reads under `data/` or `reports/`. Verify:
`uv run pytest tests/test_swing_bsh_library_audit.py -q`
"""
from __future__ import annotations
import inspect
import pickle
from pathlib import Path

import numpy as np
import pandas as pd

from src.swing_bsh import library_audit as la

WINNER = "exact_full_k0.8"


class _Stub:
    """Fixed-probability fold model with the 1-D `predict_proba` of `CalibratedBinary`."""

    def __init__(self, p=0.5):
        self.p = float(p)

    def predict_proba(self, X):
        return np.full(len(X), self.p)


def _report_text() -> str:
    """Frozen-report stub in the WI-036 format (ranking row 1 + three FDR survivors)."""
    return "\n".join([
        "# WI-036 — test report", "",
        "| rank | variant | best cell (learner/binary/h) | AUC USD | AUC CAD | min AUC | min IC | median min AUC | cells |",
        "| ---: | :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: |",
        f"| 1 | `{WINNER}` | xgboost/b_hold/h13 | 0.7836 | 0.7207 | **0.7207** | +0.0529 | 0.5179 | 33 |",
        "", "## 3. FDR survivors (BH alpha=0.05)", "",
        "| market | variant | learner | binary | h | AUC | z | p |",
        "| :--- | :--- | :--- | :--- | ---: | ---: | ---: | ---: |",
        f"| USD | `{WINNER}` | xgboost | b_hold | 13 | 0.7836 | +11.94 | 3.48e-33 |",
        f"| CAD | `{WINNER}` | xgboost | b_hold | 13 | 0.7207 | +11.68 | 8.36e-32 |",
        "| CAD | `tol2_full_k0.8` | mlp_torch | b_hold | 34 | 0.8399 | +15.35 | 1.87e-53 |",
        ""])


def _library(tmp_path, monkeypatch):
    """Fake wi035/wi036/wi038 dirs + a frozen-report stub (14 pickles)."""
    dirs = {}
    for lib in ("wi035", "wi036", "wi038"):
        dirs[lib] = tmp_path / lib
        dirs[lib].mkdir()
    names = {
        "wi035": ["CAD_xgboost_b_hold_f0.pkl", "USD_hist_gbm_b_profit_ffinal.pkl"],
        "wi036": [f"{m}_xgboost_{WINNER}_b_hold_h13_f{f}.pkl"
                  for m in ("CAD", "USD") for f in range(5)]
                 + ["USD_logistic_l2_exact_full_k0.8_b_hold_h8_f0.pkl"],
        "wi038": ["CAD_mlp_torch_tol2_full_k0.8_b_hold_h34_f0.pkl"],
    }
    for lib, files in names.items():
        for name in files:
            (dirs[lib] / name).write_bytes(b"")
    report = tmp_path / "wi036_summary.md"
    report.write_text(_report_text())
    monkeypatch.setattr(la, "LIBRARY_DIRS", tuple(sorted(dirs.items())))
    monkeypatch.setattr(la, "WI036_REPORT", report)
    monkeypatch.setattr(la, "WI038_REPORT", tmp_path / "wi038_summary.md")
    return dirs


def _toy_panel(n=40, symbols=("AAA", "BBB")):
    rows = []
    for sym in symbols:
        for i in range(n // len(symbols)):
            rows.append({"symbol": sym, "date": pd.Timestamp("2020-01-01") + pd.Timedelta(days=i),
                         "state": "at_bottom" if i % 2 else "at_top",
                         "adx_21": float(i % 7), "rsi_14": float(50 + i % 5)})
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- naming
def test_parse_pickle_name_covers_both_naming_schemes():
    a = la.parse_pickle_name("CAD_xgboost_exact_full_k0.8_b_hold_h13_f4.pkl")
    assert (a["market"], a["learner"], a["variant"], a["binary"], a["h"], a["fold"]) == \
        ("CAD", "xgboost", "exact_full_k0.8", "b_hold", 13, 4)
    assert (a["event"], a["window"], a["k"]) == ("exact", "full", 0.8)
    b = la.parse_pickle_name("USD_logistic_l2_b_hold_f2.pkl")  # WI-035 legacy naming
    assert (b["market"], b["learner"], b["binary"], b["fold"]) == ("USD", "logistic_l2", "b_hold", 2)
    assert b["variant"] is None and b["h"] is None
    c = la.parse_pickle_name("CAD_xgboost_b_hold_ffinal.pkl")
    assert (c["fold"], c["binary"], c["learner"]) == (-1, "b_hold", "xgboost")
    assert la.parse_pickle_name("nonsense.pkl") == dict.fromkeys(la.CELL_FIELDS)


# ------------------------------------------------------- manifest coverage / winner
def test_manifest_covers_every_pickle_and_winner_row_resolves(tmp_path, monkeypatch):
    dirs = _library(tmp_path, monkeypatch)
    n_files = sum(len(list(d.glob("*.pkl"))) for d in dirs.values())
    manifest = la.scan_library()
    assert len(manifest) == n_files == 14
    assert manifest["manifest_id"].is_unique
    assert all(Path(p).exists() for p in manifest["pickle_path"])
    assert manifest["auc"].isna().all() and manifest["ic"].isna().all()
    win = la.winner_cell()
    assert win == {"variant": WINNER, "learner": "xgboost", "binary": "b_hold", "h": 13}
    hit = manifest[(manifest["market"] == "USD") & (manifest["learner"] == win["learner"])
                   & (manifest["variant"] == win["variant"]) & (manifest["binary"] == win["binary"])
                   & (manifest["h"] == float(win["h"]))]
    assert len(hit) == 5
    assert all(la._path(r).exists() for _, r in hit.iterrows())
    assert set(hit["cell_id"]) == {"USD|xgboost|exact_full_k0.8|b_hold|h13"}


def test_report_stats_merge_spot_check_and_row_count(tmp_path, monkeypatch):
    _library(tmp_path, monkeypatch)
    manifest = la.scan_library()
    stats = la.parse_report_stats(la.WI036_REPORT)
    assert len(stats) == 3 and stats["auc_report"].tolist() == [0.7836, 0.7207, 0.8399]
    merged = la.attach_report_stats(manifest, stats)
    assert len(merged) == len(manifest)  # merge never duplicates the manifest
    usd = merged[(merged["market"] == "USD") & (merged["h"] == 13.0)]
    assert set(usd["auc_report"]) == {0.7836} and set(usd["stats_source"]) == {"report"}
    legacy = merged[merged["library"] == "wi035"]
    assert set(legacy["stats_source"]) == {"none"}
    checks = la.spot_check(merged)
    assert len(checks) == 3 and all(row[-1] == "yes" for row in checks)


# --------------------------------------------------- calibration / attribution math
def test_calibration_frame_brier_ece_and_permutation_importance():
    y = np.array([0, 0, 1, 1] * 40)
    p = y.astype("float64")  # perfectly calibrated (degenerate) probabilities
    assert la.calibration_frame(y, p)["n"].sum() == len(y)
    assert la.brier(y, p) == 0.0 and la.ece(y, p) == 0.0
    assert la.brier(y, np.full(len(y), 0.5)) == 0.25
    assert la.brier(y, np.where(y == 1, 0.9, 0.1)) < 0.02
    assert la.ece(y, np.where(y == 1, 0.9, 0.1)) > 0.0  # 0.1 miscalibration is reported

    X = np.random.default_rng(0).standard_normal((120, 3)).astype("float32")
    y2 = (X[:, 0] > 0).astype("int8")
    fold_id = np.repeat([0, 1], 60)
    imp, seeds = la.permutation_importance(X, y2, ["a", "b", "c"],
                                          {0: _Stub(0.5), 1: _Stub(0.5)}, fold_id, seeds=2, top=3)
    assert seeds == 2 and len(imp) == 3 and list(imp["feature"]) == ["a", "b", "c"]
    assert np.allclose(imp["auc_drop"], 0.0)  # constant model -> shuffling cannot help


def test_no_explanation_library_dependency():
    src = inspect.getsource(la).lower()
    assert "import shap" not in src and "treeshap" not in src
    assert "shap." not in src and "lime" not in src


# ------------------------------------------------------------- inference + reports
def test_infer_smoke_scores_tail_bars_and_exits_zero(tmp_path, monkeypatch, capsys):
    _library(tmp_path, monkeypatch)
    manifest_id = "wi036:USD_xgboost_exact_full_k0.8_b_hold_h13_f4"
    row = la.scan_library().set_index("manifest_id").loc[manifest_id]
    with open(la._path(row), "wb") as fh:
        pickle.dump({"model": _Stub(0.7), "provenance": {"tag": "test"}}, fh)
    panel = _toy_panel()
    monkeypatch.setattr(la, "load_market_panel", lambda *a, **k: (panel, {}))
    rc = la.main(["--infer", "--cell", manifest_id, "--symbols", "AAA,BBB", "--tail", "2"])
    out = capsys.readouterr().out
    assert rc == 0 and "EXIT:0" in out and len(out.strip().splitlines()) <= 5
    frame = la.infer(manifest_id, "AAA,BBB", 2, panel=panel)
    assert len(frame) == 4 and set(frame["symbol"]) == {"AAA", "BBB"}
    assert frame["manifest_id"].eq(manifest_id).all() and frame["p"].eq(0.7).all()
    assert la.main(["--infer", "--cell", "wi036:missing"]) == 1


def test_reports_are_written_into_the_given_dir(tmp_path, monkeypatch):
    _library(tmp_path, monkeypatch)
    manifest = la.attach_report_stats(la.scan_library(), la.parse_report_stats(la.WI036_REPORT))
    out = tmp_path / "out"
    la.write_reports(manifest, la.winner_cell(), {}, out)
    assert (out / la.MANIFEST_REPORT_NAME).exists() and (out / la.CALIB_REPORT_NAME).exists()
    text = (out / la.MANIFEST_REPORT_NAME).read_text()
    assert "14 fold pickles" in text and "Spot-check" in text and "match |" in text
