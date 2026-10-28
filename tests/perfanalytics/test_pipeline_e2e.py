"""WI-015 step 5 — end-to-end integration coverage.

Market selection (CAD before USD for BOTH), market-suffixed paths, documented
schemas, deterministic alignment, and the guarantee that WI-015 never reaches
into the shipped WI-014 path.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.perfanalytics.correlation import alignment as align
from src.perfanalytics.correlation import visualize as viz
from src.perfanalytics.features import panel as panel_mod
from src.perfanalytics.targets import dataset as dataset_mod

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
PACKAGE = Path(__file__).resolve().parents[2] / "src" / "perfanalytics"


def _raw(n: int = 260, seed: int = 0) -> pd.DataFrame:
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


def _source(market="CAD"):
    return [(f"S{i}", _raw(seed=i), ) for i in range(5)]


class _Iter:
    """Fresh `(symbol, frame)` iterator, re-created per fold like the real loader."""

    def __init__(self, market="CAD"):
        self.market = market

    def __call__(self):
        return iter(_source(self.market))


def test_full_pipeline_writes_every_artifact(tmp_path):
    data_root = tmp_path / "data"
    reports = tmp_path / "reports" / "perfanalytics"
    src = _source()

    dataset_mod.build_run_targets("CAD", out_dir=data_root, symbol_iter=src)
    panel_mod.build_feature_panel("CAD", out_dir=data_root, symbol_iter=src, reports_dir=reports)
    table, meta = align.run_alignment(
        "CAD", data_root=data_root, reports_dir=reports, symbol_factory=_Iter()
    )
    viz.build_all("CAD", reports)

    expected = [
        reports / "alignment_CAD.csv",
        reports / "alignment_CAD.json",
        reports / "alignment_CAD.md",
        reports / "alignment_top_CAD.csv",
        reports / "heatmap_CAD.png",
        reports / "features_summary_CAD.md",
        data_root / "run_targets_CAD_schema.json",
        data_root / "features_CAD_schema.json",
    ]
    for path in expected:
        assert path.exists(), path
        if path.suffix in {".csv", ".md", ".json"}:
            assert path.stat().st_size > 0
    assert (reports / "heatmap_CAD.png").read_bytes().startswith(PNG_MAGIC)
    assert meta["targets"] == [f"t{s}_{k}" for k in (15, 20) for s in ("1_amp", "2_vel", "3_streak", "4_freq")]
    assert list((data_root / "run_targets_CAD").glob("symbol=*.parquet"))
    assert list((data_root / "features_CAD").glob("symbol=*.parquet"))


def test_market_suffixed_outputs_stay_in_their_market(tmp_path):
    data_root = tmp_path / "data"
    reports = tmp_path / "reports" / "perfanalytics"
    src = _source()
    dataset_mod.build_run_targets("USD", out_dir=data_root, symbol_iter=src)
    panel_mod.build_feature_panel("USD", out_dir=data_root, symbol_iter=src, reports_dir=reports)
    align.run_alignment("USD", data_root=data_root, reports_dir=reports, symbol_factory=_Iter())
    viz.build_all("USD", reports)

    for path in reports.iterdir():
        assert path.name.endswith("_USD" + path.suffix), path
    assert (data_root / "run_targets_USD").exists()
    assert not (data_root / "run_targets_CAD").exists()
    assert not (reports / "heatmap_CAD.png").exists()


def test_all_clis_process_cad_before_usd(tmp_path, monkeypatch):
    seen: list[str] = []

    monkeypatch.setattr(dataset_mod, "build_run_targets", lambda m, **k: seen.append(f"targets:{m}") or tmp_path)
    monkeypatch.setattr(panel_mod, "build_feature_panel", lambda m, **k: seen.append(f"features:{m}") or tmp_path)
    monkeypatch.setattr(
        align, "run_alignment",
        lambda m, **k: (seen.append(f"align:{m}") or pd.DataFrame({"pass": []}), {}),
    )
    monkeypatch.setattr(
        viz, "build_all",
        lambda m, root=None: seen.append(f"viz:{m}") or {"heatmap": tmp_path, "top": tmp_path, "md": tmp_path},
    )

    for main in (dataset_mod.main, panel_mod.main, align.main, viz.main):
        assert main([]) == 0

    order = list(dict.fromkeys(seen))
    assert order == ["targets:CAD", "targets:USD", "features:CAD", "features:USD",
                     "align:CAD", "align:USD", "viz:CAD", "viz:USD"]


def test_dataset_schemas_are_documented(tmp_path):
    data_root = tmp_path / "data"
    reports = tmp_path / "reports"
    src = _source()
    dataset_mod.build_run_targets("CAD", out_dir=data_root, symbol_iter=src)
    panel_mod.build_feature_panel("CAD", out_dir=data_root, symbol_iter=src, reports_dir=reports)

    target_schema = json.loads((data_root / "run_targets_CAD_schema.json").read_text())
    assert target_schema["horizons"] == [15, 20]
    assert set(target_schema["columns"]) >= {"date", "symbol", "t1_amp_15", "diag_lowhigh_20"}

    feature_schema = json.loads((data_root / "features_CAD_schema.json").read_text())
    assert feature_schema["fib_grid"] == [3, 5, 8, 13, 21, 34, 55, 89, 144, 233]
    assert "no partial windows" in feature_schema["notes"]["warmup"]
    assert set(feature_schema["dtypes"].values()) == {"float32"}
    assert feature_schema["window_coverage_symbols"]["233"] == 5


def test_package_never_reaches_into_wi014_artifacts():
    offenders = []
    for path in PACKAGE.rglob("*.py"):
        text = path.read_text()
        for needle in ("wi014", "pdf_compiler_factor", "wi014_screener"):
            if needle in text:
                offenders.append(f"{path.name}:{needle}")
    assert offenders == []


def test_alignment_reports_only_held_out_dates(tmp_path):
    data_root = tmp_path / "data"
    reports = tmp_path / "reports"
    src = _source()
    dataset_mod.build_run_targets("CAD", out_dir=data_root, symbol_iter=src)
    panel_mod.build_feature_panel("CAD", out_dir=data_root, symbol_iter=src, reports_dir=reports)
    table, meta = align.run_alignment(
        "CAD", data_root=data_root, reports_dir=reports, symbol_factory=_Iter()
    )
    csv = pd.read_csv(reports / "alignment_CAD.csv")
    pd.testing.assert_frame_equal(csv, table, check_dtype=False)
    dates = np.sort(
        np.unique(
            np.concatenate(
                [pd.read_parquet(p, columns=["date"])["date"].to_numpy()
                 for p in (data_root / "run_targets_CAD").glob("symbol=*.parquet")]
            )
        )
    )
    n_held_out = sum(len(v) for v in align.fold_val_positions(dates))
    assert (csv["n_dates"] <= n_held_out).all()
    assert csv["n_dates"].max() > 0
