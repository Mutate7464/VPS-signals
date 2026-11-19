"""WI-098 — synthetic-fixture tests for the family-eval delta driver.

Covers: detection-bar join correctness (value at the bar, NaN tail, float32 cast of
int8/int16 sources), the baseline-exclusion prune probe (delta trap), the regression
path (continuous labels are never int8-cast), no-lookahead (future-bar perturbation
invariance), BH-FDR math, and checkpoint reuse. No real data artifact is touched.
"""

from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd
import pytest

from scripts import family_eval_ext as fe

FAM_COLS: dict[str, tuple[str, ...]] = {
    "nr_flags": ("nr4", "nr7"),
    "clv": ("clv", "clv_ma14"),
    "cusum_flag": ("cusum_flag", "cusum_stat"),
    "stoch_rsi": ("stochrsi_14_14",),
    "connors_rsi": ("connors_rsi",),
    "fail_count": ("fail_count_20",),
    "swing_levels": ("dist_to_swing_hi_atr", "dist_to_swing_lo_atr",
                     "dist_ret50_atr", "dist_ret75_atr"),
}
BASE_COLS = ("rsi_14", "atr_pct_21", "adx_21")


def _dates(n: int, start=dt.date(2020, 1, 1)) -> list:
    return [start + dt.timedelta(days=i) for i in range(n)]


def _write_families(root, dates, symbols=("S1", "S2"), market="USD") -> None:
    """Seven tiny per-bar family parquets; nr4 == nr7 (a duplicate the prune must catch)."""
    for fam, cols in FAM_COLS.items():
        rows = []
        for s in symbols:
            for i, d in enumerate(dates):
                if fam == "nr_flags":
                    vals = (i + 0.5, i + 0.5)  # rank-identical pair
                elif fam == "cusum_flag":
                    vals = (i % 2, i + 0.5)
                elif fam == "fail_count":
                    vals = (i,)
                elif fam == "swing_levels":
                    vals = tuple(i + 0.1 * (k + 1) for k in range(len(cols)))
                else:
                    vals = tuple(i + 0.5 + 0.25 * k for k in range(len(cols)))
                rows.append((s, d, *vals))
        df = pd.DataFrame(rows, columns=["symbol", "date", *cols])
        for c in cols:
            if c == "cusum_flag":
                df[c] = df[c].astype("int8")
            elif c == "fail_count_20":
                df[c] = df[c].astype("int16")
            else:
                df[c] = df[c].astype("float32")
        df.to_parquet(root / f"{fam}_{market}.parquet", index=False)


def _panel(dates, symbols=("S1", "S2"), informative: bool = False) -> pd.DataFrame:
    """Event panel; constant base candidates by default (no rank relation to family columns)."""
    rows = []
    for s in symbols:
        for i, d in enumerate(dates):
            if informative:  # periodic (val-range covered by train) so trees can score OOF
                vals = {"rsi_14": float(i % 7), "atr_pct_21": float((3 * i) % 5),
                        "adx_21": float(i % 3)}
            else:
                vals = {c: 1.0 for c in BASE_COLS}
            rows.append({"symbol": s, "date": d, "state": "at_bottom", "close": 10.0,
                         "atr": 1.0, **vals})
    return pd.DataFrame(rows)


def _fixture(tmp_path, monkeypatch, n_dates=6, symbols=("S1", "S2"), informative=False):
    feat = tmp_path / "feat"
    feat.mkdir()
    monkeypatch.setattr(fe, "FEATURES_DIR", feat)
    dates = _dates(n_dates)
    _write_families(feat, dates, symbols=symbols)
    return dates, _panel(dates, symbols=symbols, informative=informative)


def _synth_market(tmp_path, monkeypatch, n_dates=40, symbols=("S1", "S2"), informative=False):
    """Patch `load_market` so `run` executes end-to-end on the synthetic fixture."""
    dates, panel = _fixture(tmp_path, monkeypatch, n_dates=n_dates, symbols=symbols,
                            informative=informative)
    n = len(panel)
    if informative:
        x = panel["rsi_14"].to_numpy("float64")
        labels = {"b_hold": (x > 3.0).astype("int8"),
                  "xsec_vol_rank_bin": (x / 6.0).astype("float32")}
    else:
        labels = {"b_hold": (np.arange(n) % 2).astype("int8"),
                  "xsec_vol_rank_bin": ((np.arange(n) % 7) / 6.0).astype("float32")}
    monkeypatch.setattr(fe, "load_market", lambda *a, **k: (panel.copy(), labels))
    return panel, labels


# --------------------------------------------------------------------------- #
# Join correctness
# --------------------------------------------------------------------------- #
def test_load_family_casts_to_float32(tmp_path, monkeypatch):
    _fixture(tmp_path, monkeypatch)
    for fam, cols in FAM_COLS.items():
        df = fe.load_family(fam, "USD")
        assert list(df.columns) == ["symbol", "date", *cols]
        assert all(str(df[c].dtype) == "float32" for c in cols)


def test_join_takes_the_detection_bar_value_and_nan_tail(tmp_path, monkeypatch):
    dates, _p = _fixture(tmp_path, monkeypatch)
    panel = pd.DataFrame({"symbol": ["S1", "S1", "S2"],
                          "date": [dates[1], dates[4], dates[-1] + dt.timedelta(days=3)]})
    fam = fe.load_family("nr_flags", "USD")
    out = fe.join_family(panel, fam, ["nr4", "nr7"])
    assert out["nr4"].dtype == np.float32
    assert out.loc[0, "nr4"] == np.float32(1.5)  # date index 1 -> i + 0.5
    assert out.loc[1, "nr4"] == np.float32(4.5)
    assert np.isnan(out.loc[2, "nr4"])           # tail date absent from the family frame
    assert len(out) == len(panel)                # never row-dropping or row-multiplying


def test_join_is_lookahead_free(tmp_path, monkeypatch):
    dates, _p = _fixture(tmp_path, monkeypatch)
    panel = pd.DataFrame({"symbol": ["S1", "S1"], "date": [dates[1], dates[3]]})
    fam = fe.load_family("nr_flags", "USD")
    before = fe.join_family(panel, fam, ["nr4"])["nr4"].to_numpy()
    perturbed = fam.copy()
    perturbed.loc[perturbed["date"] > dates[1], "nr4"] *= 100.0
    after = fe.join_family(panel, perturbed, ["nr4"])["nr4"].to_numpy()
    assert after[0] == before[0]      # a later bar never reaches an earlier event
    assert after[1] != before[1]      # sanity: the perturbation is real at a later bar


# --------------------------------------------------------------------------- #
# Baseline exclusion (delta trap) + prune probe
# --------------------------------------------------------------------------- #
def test_prune_probe_diff_is_family_only(tmp_path, monkeypatch):
    dates, panel = _fixture(tmp_path, monkeypatch)
    joined = fe.joined_panel(panel, "USD")
    probe = fe.prune_probe(joined, "USD")
    assert set(probe) == set(FAM_COLS)
    for fam, diff in probe.items():
        assert set(diff) <= set(FAM_COLS[fam])   # no base and no other family's column
    assert probe["nr_flags"] == ["nr4"]          # the rank-identical nr7 is pruned away
    base = set(fe.pruned(joined, fe.feature_sets(joined, "USD", "nr_flags")[0]))
    all_family = {c for cols in FAM_COLS.values() for c in cols}
    assert not (base & all_family)               # baseline excludes ALL 7 families
    for fam in FAM_COLS:                         # and is the same for every family
        assert fe.feature_sets(joined, "USD", fam)[0] == \
            fe.feature_sets(joined, "USD", "nr_flags")[0]


def test_feature_sets_arm_is_base_plus_family(tmp_path, monkeypatch):
    dates, panel = _fixture(tmp_path, monkeypatch)
    joined = fe.joined_panel(panel, "USD")
    base, arm, allcols = fe.feature_sets(joined, "USD", "clv")
    assert arm[:len(base)] == base
    assert set(arm) - set(base) == set(FAM_COLS["clv"])
    assert allcols == {c for cols in FAM_COLS.values() for c in cols}


# --------------------------------------------------------------------------- #
# Statistic paths
# --------------------------------------------------------------------------- #
def test_regression_path_keeps_continuous_labels(monkeypatch):
    seen: dict = {}

    def fake_cell_cv(**kw):
        seen.update(kw)
        n = len(kw["y"])
        return {"oof": np.linspace(0.0, 1.0, n), "fold_id": np.zeros(n, dtype="int16"),
                "models": {}}

    monkeypatch.setattr(fe.binary_grid, "cell_cv", fake_cell_cv)
    X = np.zeros((40, 3), dtype="float32")
    y = np.linspace(0.0, 1.0, 40).astype("float32")
    dates = _dates(40)
    assert fe.is_regression("xsec_vol_rank_bin") and not fe.is_regression("b_hold")
    out = fe.fold_scores(X, y, dates, "xgboost", {}, None, "t", True)
    assert seen["regression"] is True
    assert seen["y"].dtype == np.float32
    assert np.unique(seen["y"]).size > 2            # continuous, never binarised
    assert out[0] == pytest.approx(1.0)             # rank-IC of a monotone pair
    fe.fold_scores(X, (np.arange(40) % 2).astype("int8"), dates, "xgboost", {}, None, "t", False)
    assert seen["regression"] is False


def test_paired_p_and_bh_fdr_math():
    assert list(fe.bh([0.01, 0.02, 0.03, 0.04], m_total=4)) == [True] * 4
    assert not any(fe.bh([0.01, 0.02, 0.03, 0.04], m_total=100))
    assert list(fe.bh([0.01, 0.04, 0.03, 0.5], m_total=4)) == [True, False, False, False]
    assert list(fe.bh([float("nan"), 0.001], m_total=2)) == [False, True]
    delta, p = fe.paired_p([0.05, 0.05, 0.05, 0.05, 0.05])
    assert delta == pytest.approx(0.05) and p == 1.0        # zero variance -> no evidence
    assert np.isnan(fe.paired_p([])[0])


# --------------------------------------------------------------------------- #
# Driver: checkpoint reuse + end-to-end
# --------------------------------------------------------------------------- #
def test_run_checkpoints_and_reuses(tmp_path, monkeypatch):
    _synth_market(tmp_path, monkeypatch, n_dates=12)
    calls: list[tuple] = []

    def stub(X, y, dates, learner, params, splitter, tag, regression):
        calls.append((tag, str(np.asarray(y).dtype), regression))
        return {0: 0.6, 1: 0.55}

    monkeypatch.setattr(fe, "fold_scores", stub)
    ckpt, out = tmp_path / "ckpt", tmp_path / "out"
    cells, _r = fe.run(["USD"], "nr_flags", ckpt_dir=ckpt, out_dir=out, resume=False)
    assert len(calls) == 4                        # 2 targets x (baseline + arm)
    by_tag = {t: d for t, d, _ in calls}
    assert by_tag["USD_base_b_hold_xgboost"] == "int8"
    assert by_tag["USD_nr_flags_xsec_vol_rank_bin_xgboost"] == "float32"
    assert (ckpt / "nr_flags_cells.json").exists()
    assert (ckpt / "_baseline_cells.json").exists()
    assert (out / "nr_flags_summary.md").exists() and (out / "nr_flags_USD.md").exists()
    calls.clear()
    cells2, _r2 = fe.run(["USD"], "nr_flags", ckpt_dir=ckpt, out_dir=out, resume=True)
    assert calls == []                            # --resume fits only missing cells
    assert [c["delta"] for c in cells] == [c["delta"] for c in cells2]
    assert len(cells) == 2


def test_run_end_to_end_synthetic_cv(tmp_path, monkeypatch):
    _synth_market(tmp_path, monkeypatch, n_dates=120, symbols=("S1", "S2", "S3"),
                  informative=True)
    cells, reports = fe.run(["USD"], "swing_levels", ckpt_dir=tmp_path / "ckpt",
                            out_dir=tmp_path / "out")
    assert len(cells) == 2                        # 2 targets x 1 learner x 1 market
    assert all(np.isfinite(c["p"]) for c in cells)
    assert all(c["n_folds"] >= 1 for c in cells)  # the real purged-CV path produced scores
    text = (tmp_path / "out" / "swing_levels_summary.md").read_text()
    assert "PROVISIONAL" in text and "VIOLATION" not in text
    assert len(reports) == 2                      # one market report + the summary
