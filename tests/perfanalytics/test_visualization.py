"""WI-015 addendum — result visualization smoke + determinism tests."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.perfanalytics.correlation import alignment as align
from src.perfanalytics.correlation import visualize as viz
from src.perfanalytics.features.panel import build_feature_panel, feature_columns
from src.perfanalytics.targets import build_run_targets

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def _raw(n: int = 300, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    close = 100.0 * np.cumprod(1.0 + rng.normal(0.0005, 0.02, n))
    return pd.DataFrame(
        {
            "date": pd.date_range("2020-01-01", periods=n, freq="B"),
            "open": close,
            "high": close * 1.01,
            "low": close * 0.99,
            "close": close,
            "volume": 1_000_000.0,
        }
    )


def _source():
    return [(f"S{i}", _raw(seed=i)) for i in range(6)]


@pytest.fixture()
def reports(tmp_path):
    build_run_targets("CAD", out_dir=tmp_path, symbol_iter=_source())
    build_feature_panel("CAD", out_dir=tmp_path, symbol_iter=_source(), reports_dir=tmp_path / "rep")
    align.run_alignment(
        "CAD", data_root=tmp_path, reports_dir=tmp_path / "rep", symbol_factory=_source
    )
    return tmp_path / "rep"


def test_renders_heatmap_top_table_and_summary(reports):
    paths = viz.build_all("CAD", reports)
    png = paths["heatmap"].read_bytes()
    assert len(png) > 1000, "heatmap PNG is suspiciously small"
    assert png.startswith(PNG_MAGIC)

    top = pd.read_csv(paths["top"])
    assert set(top.columns) == {
        "target", "horizon", "rank", "family", "window",
        "held_out_ic", "noise_margin", "sign_match_vs_e5", "pass",
    }
    assert set(zip(top["target"], top["horizon"])) == {
        (f"T{t}", k) for t in (1, 2, 3, 4) for k in (15, 20)
    }
    for _, g in top.groupby(["target", "horizon"]):
        assert len(g) <= viz.TOP_N
        assert (g["held_out_ic"].abs().diff().dropna() <= 1e-12).all()  # descending |IC|

    md = paths["md"].read_text()
    assert viz.SUMMARY_MARKER in md
    assert "Family vs timeframe" in md
    assert "Most frequent best family" in md
    assert "| T1@15 |" in md  # target×horizon label rendered once, not doubled
    assert "@15@15" not in md
    # the summary must not duplicate itself when re-applied
    viz.append_summary(viz.load_matrix("CAD", reports), "CAD", paths["md"])
    assert paths["md"].read_text().count(viz.SUMMARY_MARKER) == 1


def test_outputs_are_deterministic(reports):
    first = viz.build_all("CAD", reports)
    heat1 = first["heatmap"].read_bytes()
    top1 = first["top"].read_bytes()
    md1 = first["md"].read_text()
    second = viz.build_all("CAD", reports)
    assert second["heatmap"].read_bytes() == heat1
    assert second["top"].read_bytes() == top1
    assert second["md"].read_text() == md1


def test_ranked_table_uses_only_the_matrix(reports):
    table = viz.load_matrix("CAD", reports)
    rank = viz.ranked_table(table, "CAD")
    keys = set(zip(table["target"], table["horizon"], table["family"], table["window"]))
    for _, r in rank.iterrows():
        assert (r["target"], r["horizon"], r["family"], r["window"]) in keys


def test_heatmap_matrix_shape_and_family_blocks(reports):
    table = viz.load_matrix("CAD", reports)
    mat, labels = viz._heatmap_matrix(table)
    assert mat.shape == (len(viz.FAMILIES) * len(viz.TARGET_ORDER), len(viz.FIB_GRID))
    assert labels[: len(viz.TARGET_ORDER)] == [f"{viz.FAMILIES[0]} · {t}" for t in viz.TARGET_ORDER]
    # absent hurst short windows must be blank, not zero
    hurst_row = viz.FAMILIES.index("hurst") * len(viz.TARGET_ORDER)
    assert np.isnan(mat[hurst_row, 0])  # window 3 absent


def test_cli_rejects_invalid_market(capsys):
    assert viz.main(["--market", "XYZ"]) == 2
    assert "invalid market" in capsys.readouterr().err
