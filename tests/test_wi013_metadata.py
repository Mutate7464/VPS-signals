"""WI-013 F-4 — the metadata panels carry no label columns, and the rebuild is exact.

Two things are pinned here:

1. **No labels.** Neither `features_{USD,CAD}_metadata.parquet` schema may contain a
   `y_*` target column: the panels are a feature feed, and the four label columns
   `src/stat_metadata.py` used to concatenate on made any all-columns consumer a
   label-leak footgun.
2. **The rebuild is the same construction, exactly.** `scripts/rebuild_wi013_metadata.py`
   reconstructs the panel from `features_{market}.parquet` + the metadata catalog
   with the same 60-row per-symbol Z-score and per-date `rank(pct=True)` pandas
   calls `src/stat_metadata.py` uses, and refuses to swap unless every surviving
   column is `assert_frame_equal(..., check_dtype=True, check_exact=True)`-equal.

The synthetic tests run the real reconstruction code path on a small multi-symbol
frame (with a batch size that forces symbol boundaries to fall inside batches); the
artifact tests read only parquet schemas / row counts, never a full panel.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
FEATURES_DIR = ROOT / "data" / "features"
sys.path.insert(0, str(ROOT))

MARKETS = ("USD", "CAD")
LABELS = ("y_15d_high", "y_15d_low", "y_20d_up", "y_20d_down")


def load_rebuild_module():
    """Import `scripts/rebuild_wi013_metadata.py` without running its CLI."""
    path = SCRIPTS_DIR / "rebuild_wi013_metadata.py"
    spec = importlib.util.spec_from_file_location("wi013_rebuild_metadata", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


mod = load_rebuild_module()


def panel_path(market: str) -> Path:
    return FEATURES_DIR / f"features_{market}_metadata.parquet"


# --------------------------------------------------------------------------- #
# The panels themselves
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("market", MARKETS)
def test_metadata_panels_have_no_label_columns(market):
    path = panel_path(market)
    if not path.exists():
        pytest.skip(f"{path.name} not present")
    names = list(pq.ParquetFile(str(path)).schema_arrow.names)
    assert [c for c in names if c.startswith("y_")] == [], f"{path.name} still carries label columns"
    assert not set(LABELS) & set(names)


@pytest.mark.parametrize("market", MARKETS)
def test_metadata_panel_columns_are_keys_survivors_and_percentiles(market):
    path = panel_path(market)
    if not path.exists():
        pytest.skip(f"{path.name} not present")
    if not mod.catalog_path(market).exists():
        pytest.skip("metadata catalog not present")
    catalog = mod.load_catalog(market)
    names = list(pq.ParquetFile(str(path)).schema_arrow.names)
    assert names == mod.expected_columns(catalog)
    assert len(names) == 3 + 2 * len(catalog["surviving_features"])


@pytest.mark.parametrize("market", MARKETS)
def test_metadata_panel_still_covers_every_feature_row(market):
    """The label strip must not have changed the panel's row count."""
    panel, features = panel_path(market), FEATURES_DIR / f"features_{market}.parquet"
    if not (panel.exists() and features.exists()):
        pytest.skip("artifacts not present")
    assert pq.ParquetFile(str(panel)).metadata.num_rows == pq.ParquetFile(str(features)).metadata.num_rows


def test_expected_columns_drops_exactly_the_labels():
    catalog = mod.load_catalog("CAD") if mod.catalog_path("CAD").exists() else None
    if catalog is None:
        pytest.skip("metadata catalog not present")
    columns = mod.expected_columns(catalog)
    assert not [c for c in columns if c.startswith("y_")]
    assert mod.LABEL_COLUMNS == LABELS


@pytest.mark.parametrize("market", MARKETS)
def test_pre_swap_backup_exists(market):
    """A pre-swap backup is retained on disk after the swap."""
    backup = mod.backup_path(market)
    if not panel_path(market).exists():
        pytest.skip("panel not present")
    if not backup.exists():
        pytest.skip("no pre-swap backup on disk (panel never swapped in this tree)")
    assert pq.ParquetFile(str(backup)).metadata.num_rows == pq.ParquetFile(
        str(panel_path(market))
    ).metadata.num_rows
    backup_names = list(pq.ParquetFile(str(backup)).schema_arrow.names)
    assert set(LABELS) <= set(backup_names), "the backup should be the pre-WI-013 panel"


# --------------------------------------------------------------------------- #
# The reconstruction itself (synthetic, cheap)
# --------------------------------------------------------------------------- #
SYNTH_SURVIVING = ("feat_a", "feat_flagged_1", "feat_b", "feat_flagged_2")


def synth_catalog() -> dict:
    return {
        "market": "USD",
        "surviving_features": list(SYNTH_SURVIVING),
        "stationarity": {
            f: {"flagged": f.startswith("feat_flagged")} for f in SYNTH_SURVIVING
        },
    }


def synth_features(tmp_path: Path, symbols=("AAA", "BBB", "CCC")) -> pd.DataFrame:
    """Symbol-major raw features with per-symbol row counts and overlapping dates."""
    rng = np.random.default_rng(11)
    dates = pd.bdate_range("2020-01-01", periods=70)
    parts = []
    for i, symbol in enumerate(symbols):
        n = len(dates) - 5 * i
        parts.append(
            pd.DataFrame(
                {
                    "date": dates[:n],
                    "symbol": symbol,
                    "market": "USD",
                    **{
                        c: rng.standard_normal(n).astype("float32") * 10.0
                        for c in SYNTH_SURVIVING
                    },
                }
            )
        )
    frame = pd.concat(parts, ignore_index=True)
    return frame


def write_synth_features(tmp_path: Path, frame: pd.DataFrame) -> Path:
    path = tmp_path / "features_SYNTH.parquet"
    frame.to_parquet(path, index=False)
    return path


def reference_panel(frame: pd.DataFrame, catalog: dict) -> pd.DataFrame:
    """The `src/stat_metadata.py` construction, written the obvious (not streaming) way."""
    surviving = list(catalog["surviving_features"])
    flagged = [f for f in surviving if catalog["stationarity"][f]["flagged"]]
    out = frame.copy()
    if flagged:
        out[flagged] = frame.groupby("symbol")[flagged].transform(
            lambda s: (s - s.rolling(60, min_periods=20).mean())
            / (s.rolling(60, min_periods=20).std(ddof=1) + 1e-12)
        )
    cs = out.groupby("date")[surviving].rank(pct=True).astype("float32")
    cs.columns = [f"{c}_cs_pct" for c in surviving]
    return pd.concat([out[["date", "symbol", "market"] + surviving], cs], axis=1)


@pytest.mark.parametrize("batch_rows", [7, 500])
def test_reconstruction_reproduces_the_stat_metadata_construction(tmp_path, batch_rows):
    frame = synth_features(tmp_path)
    features = write_synth_features(tmp_path, frame)
    catalog = synth_catalog()
    staged = tmp_path / "staged.parquet"
    rebuilt = tmp_path / "rebuilt.parquet"

    rows = mod.reconstruct_from_features(features, catalog, staged, batch_rows=batch_rows)
    assert rows == len(frame)
    percentiles = mod.compute_cs_percentiles(staged, catalog["surviving_features"])
    assert mod.write_panel(staged, percentiles, catalog["surviving_features"], rebuilt) == len(frame)

    got = pq.read_table(str(rebuilt)).to_pandas()
    expected = reference_panel(frame, catalog)
    assert list(got.columns) == mod.expected_columns(catalog)
    pd.testing.assert_frame_equal(got, expected, check_dtype=True, check_exact=True)


def test_reconstruction_applies_the_zscore_only_to_flagged_survivors(tmp_path):
    frame = synth_features(tmp_path, symbols=("AAA",))
    features = write_synth_features(tmp_path, frame)
    catalog = synth_catalog()
    staged = tmp_path / "staged.parquet"
    mod.reconstruct_from_features(features, catalog, staged, batch_rows=500)
    staged_df = pq.read_table(str(staged)).to_pandas()
    for column in ("feat_a", "feat_b"):
        np.testing.assert_array_equal(staged_df[column].to_numpy(), frame[column].to_numpy())
    # The Z-scored columns are centred and unit-scaled where the window is full.
    tail = staged_df["feat_flagged_1"].to_numpy()[40:]
    assert abs(float(np.nanmean(tail))) < 1.0
    assert pd.api.types.is_float_dtype(staged_df["feat_flagged_1"])


# --------------------------------------------------------------------------- #
# Verification + swap guard
# --------------------------------------------------------------------------- #
def test_compare_columns_detects_value_and_dtype_mismatches(tmp_path):
    old = pd.DataFrame({"a": np.array([1.0, 2.0, 3.0]), "b": np.array([1.0, 2.0, 3.0])})
    new = old.copy()
    new.loc[1, "b"] = 2.0 + 1e-7  # one value, tiny difference
    old_p, new_p = tmp_path / "old.parquet", tmp_path / "new.parquet"
    old.to_parquet(old_p, index=False)
    new.to_parquet(new_p, index=False)

    rows = {r["column"]: r for r in mod.compare_columns(old_p, new_p, ["a", "b"])}
    assert rows["a"]["equal"] is True
    assert rows["b"]["equal"] is False and rows["b"]["mismatches"] == 1

    dtype_p = tmp_path / "dtype.parquet"
    old.assign(a=old["a"].astype("float32")).to_parquet(dtype_p, index=False)
    rows = {r["column"]: r for r in mod.compare_columns(old_p, dtype_p, ["a"])}
    assert rows["a"]["equal"] is False, "a dtype-only change must fail the exact comparison"


def test_a_mismatch_prevents_every_swap(tmp_path, monkeypatch):
    """One failing market means no panel is replaced — the plan's escalation rule."""
    panels = {}
    for market in MARKETS:
        path = tmp_path / f"features_{market}_metadata.parquet"
        pd.DataFrame({"a": np.array([1.0, 2.0])}).to_parquet(path, index=False)
        panels[market] = path
    staged = tmp_path / "staged.parquet"
    pd.DataFrame({"a": np.array([1.0, 2.0])}).to_parquet(staged, index=False)
    before = {m: p.read_bytes() for m, p in panels.items()}

    def fake_verification(market, old_path, new_path):
        return {
            "market": market,
            "old_rows": 2,
            "new_rows": 2,
            "rows_equal": True,
            "old_columns": 1,
            "new_columns": 1,
            "dropped_labels": [] if market == "USD" else list(LABELS),
            "labels_present_after": [],
            "column_order_ok": market != "USD",
            "expected_columns_ok": market != "USD",
            "columns_compared": 1,
            "columns_unequal": [] if market != "USD" else ["a"],
            "column_rows": [],
            "pass": market != "USD",
        }

    monkeypatch.setattr(mod, "panel_path", lambda m: panels[m])
    monkeypatch.setattr(mod, "backup_path", lambda m: tmp_path / f"backup_{m}.parquet")
    monkeypatch.setattr(mod, "REPORTS_DIR", tmp_path)
    monkeypatch.setattr(mod, "VERIFICATION_REPORT", tmp_path / "verif.md")
    monkeypatch.setattr(mod, "rebuild_market", lambda m, staging, batch_rows=0: {"market": m, "staged": staged})
    monkeypatch.setattr(mod, "verify_market", fake_verification)

    rc = mod.main(["--markets", "USD", "CAD", "--staging-dir", str(tmp_path)])
    assert rc == 1, "a failing market must return non-zero"
    for market, path in panels.items():
        assert path.read_bytes() == before[market], f"{market} was swapped despite a failure"
        assert not (tmp_path / f"backup_{market}.parquet").exists()
    assert "FAIL" in (tmp_path / "verif.md").read_text()


def test_rebuild_cli_defaults_to_both_markets_and_rejects_invalid():
    parser = mod.build_parser()
    assert parser.parse_args([]).markets == ["USD", "CAD"]
    assert parser.parse_args(["--markets", "CAD"]).markets == ["CAD"]
    assert mod.main(["--markets", "EUR"]) == 2


def test_rebuild_never_swaps_without_verification_flag(tmp_path, monkeypatch):
    """`--no-swap` verifies and reports but leaves the panels untouched."""
    panel = tmp_path / "features_CAD_metadata.parquet"
    pd.DataFrame({"a": np.array([1.0])}).to_parquet(panel, index=False)
    before = panel.read_bytes()
    staged = tmp_path / "staged.parquet"
    pd.DataFrame({"a": np.array([1.0])}).to_parquet(staged, index=False)
    monkeypatch.setattr(mod, "panel_path", lambda m: panel)
    monkeypatch.setattr(mod, "REPORTS_DIR", tmp_path)
    monkeypatch.setattr(mod, "VERIFICATION_REPORT", tmp_path / "verif.md")
    monkeypatch.setattr(mod, "rebuild_market", lambda m, staging, batch_rows=0: {"market": m, "staged": staged})
    monkeypatch.setattr(
        mod,
        "verify_market",
        lambda m, old, new: {
            "market": m, "old_rows": 1, "new_rows": 1, "rows_equal": True, "old_columns": 1,
            "new_columns": 1, "dropped_labels": [], "labels_present_after": [],
            "column_order_ok": True, "expected_columns_ok": True, "columns_compared": 1,
            "columns_unequal": [], "column_rows": [], "pass": True,
        },
    )
    assert mod.main(["--markets", "CAD", "--no-swap", "--staging-dir", str(tmp_path)]) == 0
    assert panel.read_bytes() == before
