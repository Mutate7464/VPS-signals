"""WI-018 step 1 regression tests — preflight contracts for the WI-017 USD inputs.

Locks: the 593-symbol/264-column/88-keep-column contract, per-symbol row and
date alignment (across `date32` and `timestamp` on-disk representations), the
target inventory reporting observed values without assuming an encoding, and
the malformed-input failures that must stop the study before any output exists.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from src.wi018.data_probe import (
    PreflightError,
    load_keep_columns,
    main,
    probe_symbol,
    require_preflight,
    run_preflight,
    symbol_paths,
    write_report,
)

PRIMARY = "first_touch_34"
SECONDARY = ("first_touch_24", "first_touch_39")
N_FEATURE_COLUMNS = 264


def _keep_columns(n: int = 88) -> list[str]:
    return [f"feat_{i:03d}" for i in range(n)]


def _dates(n_rows: int = 50) -> np.ndarray:
    return pd.bdate_range("2020-01-01", periods=n_rows).to_numpy().astype("datetime64[ns]")


def _derived_table(n_rows: int = 50, *, target_values=None, date32: bool = True) -> pa.Table:
    dates = _dates(n_rows)
    rng = np.random.default_rng(7)
    columns = {
        "date": dates,
        PRIMARY: np.asarray(target_values if target_values is not None else rng.integers(-1, 2, n_rows), dtype="float32"),
    }
    for col in SECONDARY:
        columns[col] = rng.integers(-1, 2, n_rows).astype("float32")
    table = pa.table(columns)
    if date32:
        table = table.set_column(0, "date", table.column("date").cast(pa.date32()))
    return table


def _features_table(n_rows: int = 50, n_columns: int = N_FEATURE_COLUMNS, keep=(), date32: bool = False) -> pa.Table:
    dates = _dates(n_rows)
    rng = np.random.default_rng(11)
    columns = {"date": dates}
    for i in range(n_columns):
        name = f"feat_{i:03d}"
        values = rng.normal(size=n_rows).astype("float32")
        if i == 0:  # a little deliberate missingness on the first column
            values[:3] = np.nan
        columns[name] = values
    table = pa.table(columns)
    if date32:
        table = table.set_column(0, "date", table.column("date").cast(pa.date32()))
    return table


def _write_market(
    tmp_path: Path,
    n_symbols: int = 3,
    n_rows: int = 50,
    keep=(),
    n_columns: int = N_FEATURE_COLUMNS,
    symbols: list[str] | None = None,
    feature_symbols: list[str] | None = None,
    prune_symbols=None,
    n_keep_declared: int | None = None,
) -> dict:
    """Synthetic USD market: `reports/wi017/{derived,features}` + prune list."""
    derived_dir = tmp_path / "derived"
    features_dir = tmp_path / "features"
    derived_dir.mkdir(parents=True, exist_ok=True)
    features_dir.mkdir(parents=True, exist_ok=True)
    symbols = symbols or [f"SYM{i}" for i in range(n_symbols)]
    feature_symbols = feature_symbols if feature_symbols is not None else list(symbols)
    for sym in symbols:
        pq.write_table(_derived_table(n_rows), derived_dir / f"{sym}.parquet")
    for sym in feature_symbols:
        pq.write_table(_features_table(n_rows, n_columns), features_dir / f"{sym}.parquet")
    keep = list(keep)
    prune = tmp_path / "run5_prune_recs.json"
    prune.write_text(json.dumps({
        "n_features": n_columns,
        "n_keep": len(keep) if n_keep_declared is None else n_keep_declared,
        "keep_columns": keep,
    }))
    return {"derived": derived_dir, "features": features_dir, "prune": prune, "symbols": symbols}


def _market_with_all_symbols(tmp_path: Path, feature_symbols) -> dict:
    """Market where the declared symbol list drives the prune list size."""
    return _write_market(tmp_path, keep=_keep_columns(), feature_symbols=feature_symbols)


# --------------------------------------------------------------------------- #
# per-symbol probe
# --------------------------------------------------------------------------- #
def test_probe_symbol_reports_counts_bounds_and_inventory(tmp_path):
    paths = _write_market(tmp_path, keep=_keep_columns())
    res = probe_symbol("SYM0", paths["derived"] / "SYM0.parquet", paths["features"] / "SYM0.parquet", _keep_columns())
    assert res["rows"] == 50
    assert res["date_min"] == "2020-01-01"
    assert res["date_max"] == str(pd.Timestamp(_dates(50)[-1]).date())
    assert res["feature_columns"] == N_FEATURE_COLUMNS
    assert res["keep_columns"] == 88
    # 3 NaNs in the first keep column (feat_000) out of 88 cols x 50 rows
    assert res["keep_cells"] == 88 * 50
    assert res["keep_cells_finite"] == 88 * 50 - 3
    assert res["targets"][PRIMARY]["finite"] + res["targets"][PRIMARY]["null"] == 50
    assert set(res["targets"][PRIMARY]["value_counts"]) <= {"-1.0", "0.0", "1.0"}


def test_probe_symbol_tolerates_mixed_date_representations(tmp_path):
    """derived on disk is date32, features is timestamp — alignment must still hold."""
    paths = _write_market(tmp_path, keep=_keep_columns())
    res = probe_symbol("SYM0", paths["derived"] / "SYM0.parquet", paths["features"] / "SYM0.parquet", _keep_columns())
    assert res["rows"] == 50


def test_probe_symbol_missing_keep_column_raises(tmp_path):
    paths = _write_market(tmp_path, keep=_keep_columns())
    with pytest.raises(PreflightError, match="keep_columns absent"):
        probe_symbol("SYM0", paths["derived"] / "SYM0.parquet", paths["features"] / "SYM0.parquet",
                     [*_keep_columns(), "not_a_column"])


def test_probe_symbol_wrong_feature_schema_raises(tmp_path):
    paths = _write_market(tmp_path, keep=_keep_columns(), n_columns=263)
    with pytest.raises(PreflightError, match="263 feature columns"):
        probe_symbol("SYM0", paths["derived"] / "SYM0.parquet", paths["features"] / "SYM0.parquet", _keep_columns())


def test_probe_symbol_row_mismatch_raises(tmp_path):
    paths = _write_market(tmp_path, keep=_keep_columns())
    pq.write_table(_features_table(49), paths["features"] / "SYM0.parquet")
    with pytest.raises(PreflightError, match="row mismatch"):
        probe_symbol("SYM0", paths["derived"] / "SYM0.parquet", paths["features"] / "SYM0.parquet", _keep_columns())


def test_probe_symbol_date_misalignment_raises(tmp_path):
    paths = _write_market(tmp_path, keep=_keep_columns())
    table = _features_table(50)
    table = table.set_column(0, "date", pa.array(pd.bdate_range("2020-02-01", periods=50).to_numpy()))
    pq.write_table(table, paths["features"] / "SYM0.parquet")
    with pytest.raises(PreflightError, match="not aligned"):
        probe_symbol("SYM0", paths["derived"] / "SYM0.parquet", paths["features"] / "SYM0.parquet", _keep_columns())


def test_probe_symbol_duplicate_dates_raise(tmp_path):
    paths = _write_market(tmp_path, keep=_keep_columns())
    dates = np.repeat(_dates(25), 2)
    for name in ("derived", "features"):
        target = paths[name] / "SYM0.parquet"
        table = pq.read_table(target).set_column(0, "date", pa.array(dates))
        pq.write_table(table, target)
    with pytest.raises(PreflightError, match="duplicate dates"):
        probe_symbol("SYM0", paths["derived"] / "SYM0.parquet", paths["features"] / "SYM0.parquet", _keep_columns())


def test_probe_symbol_empty_input_raises(tmp_path):
    paths = _write_market(tmp_path, keep=_keep_columns())
    pq.write_table(_derived_table(0), paths["derived"] / "SYM0.parquet")
    pq.write_table(_features_table(0), paths["features"] / "SYM0.parquet")
    with pytest.raises(PreflightError, match="empty input"):
        probe_symbol("SYM0", paths["derived"] / "SYM0.parquet", paths["features"] / "SYM0.parquet", _keep_columns())


def test_probe_symbol_missing_target_raises(tmp_path):
    paths = _write_market(tmp_path, keep=_keep_columns())
    table = _derived_table(50).drop_columns(["first_touch_34"])
    pq.write_table(table, paths["derived"] / "SYM0.parquet")
    with pytest.raises(PreflightError, match="missing target columns"):
        probe_symbol("SYM0", paths["derived"] / "SYM0.parquet", paths["features"] / "SYM0.parquet", _keep_columns())


def test_probe_symbol_missing_date_column_raises(tmp_path):
    paths = _write_market(tmp_path, keep=_keep_columns())
    pq.write_table(_features_table(50).drop_columns(["date"]), paths["features"] / "SYM0.parquet")
    with pytest.raises(PreflightError, match="missing 'date' column"):
        probe_symbol("SYM0", paths["derived"] / "SYM0.parquet", paths["features"] / "SYM0.parquet", _keep_columns())


# --------------------------------------------------------------------------- #
# prune list + discovery contracts
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "payload, match",
    [
        ({"keep_columns": []}, "nonempty 'keep_columns'"),
        ({"keep_columns": ["a", "a"]}, "duplicates"),
        ({"keep_columns": ["a", 3]}, "nonempty strings"),
        ({"n_keep": 5, "keep_columns": ["a", "b"]}, "disagrees"),
        (["a", "b"], "must be a JSON object"),
        ({}, "nonempty 'keep_columns'"),
    ],
)
def test_load_keep_columns_rejects_malformed(tmp_path, payload, match):
    path = tmp_path / "prune.json"
    path.write_text(json.dumps(payload))
    with pytest.raises(PreflightError, match=match):
        load_keep_columns(path)


def test_load_keep_columns_rejects_bad_json_and_missing_file(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not json")
    with pytest.raises(PreflightError, match="unreadable"):
        load_keep_columns(bad)
    with pytest.raises(PreflightError, match="missing"):
        load_keep_columns(tmp_path / "nope.json")


def test_load_keep_columns_accepts_valid(tmp_path):
    path = tmp_path / "prune.json"
    path.write_text(json.dumps({"n_keep": 2, "keep_columns": ["adx_3", "atr_pct_34"]}))
    assert load_keep_columns(path) == ["adx_3", "atr_pct_34"]


def test_symbol_paths_requires_parquet_directory(tmp_path):
    with pytest.raises(PreflightError, match="input directory missing"):
        symbol_paths(tmp_path / "absent")
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(PreflightError, match=r"no \*\.parquet inputs"):
        symbol_paths(empty)


# --------------------------------------------------------------------------- #
# whole-market preflight
# --------------------------------------------------------------------------- #
def test_run_preflight_aggregates_and_passes(tmp_path):
    keep = _keep_columns()
    paths = _write_market(tmp_path, n_symbols=3, keep=keep)
    report = run_preflight("USD", paths["derived"], paths["features"], paths["prune"], expected_symbols=3)
    assert report["verdict"] == "PASS"
    assert report["checks"]["symbol_sets_match"] and report["checks"]["feature_schema_264_columns"]
    assert report["summary"]["symbols"] == 3
    assert report["summary"]["total_rows"] == 150
    assert report["summary"]["keep_cells"] == 3 * 88 * 50
    assert report["summary"]["keep_cells_finite"] == 3 * 88 * 50 - 9
    assert report["targets"][PRIMARY]["finite"] + report["targets"][PRIMARY]["null"] == 150
    assert len(report["per_symbol"]) == 3
    # rate/sum sanity: observed shares must be inside [0, 1]
    assert 0.0 <= report["targets"][PRIMARY]["finite_fraction"] <= 1.0


def test_run_preflight_reports_unexpected_target_values_without_coercing(tmp_path):
    keep = _keep_columns()
    paths = _write_market(tmp_path, n_symbols=1, keep=keep)
    values = np.zeros(50, dtype="float32")
    values[0] = 2.0
    pq.write_table(_derived_table(50, target_values=values), paths["derived"] / "SYM0.parquet")
    report = run_preflight("USD", paths["derived"], paths["features"], paths["prune"], expected_symbols=1)
    assert report["targets"][PRIMARY]["unexpected_values"] == [2.0]
    assert report["targets"][PRIMARY]["value_counts"]["2.0"] == 1
    assert report["verdict"] == "PASS"  # documented as information, not a hard failure


def test_run_preflight_flags_null_targets(tmp_path):
    keep = _keep_columns()
    paths = _write_market(tmp_path, n_symbols=1, keep=keep)
    values = np.full(50, np.nan, dtype="float32")
    pq.write_table(_derived_table(50, target_values=values), paths["derived"] / "SYM0.parquet")
    report = run_preflight("USD", paths["derived"], paths["features"], paths["prune"], expected_symbols=1)
    assert report["targets"][PRIMARY]["null"] == 50
    assert report["targets"][PRIMARY]["finite"] == 0


def test_run_preflight_rejects_symbol_set_mismatch(tmp_path):
    keep = _keep_columns()
    paths = _write_market(tmp_path, n_symbols=2, keep=keep, feature_symbols=["SYM0", "SYM9"])
    with pytest.raises(PreflightError, match="symbol sets differ"):
        run_preflight("USD", paths["derived"], paths["features"], paths["prune"], expected_symbols=2)


def test_run_preflight_rejects_wrong_symbol_count(tmp_path):
    keep = _keep_columns()
    paths = _write_market(tmp_path, n_symbols=2, keep=keep)
    with pytest.raises(PreflightError, match="expected 3 USD symbols"):
        run_preflight("USD", paths["derived"], paths["features"], paths["prune"], expected_symbols=3)


def test_run_preflight_rejects_non_usd_market(tmp_path):
    keep = _keep_columns()
    paths = _write_market(tmp_path, n_symbols=1, keep=keep)
    with pytest.raises(PreflightError, match="USD-only"):
        run_preflight("CAD", paths["derived"], paths["features"], paths["prune"], expected_symbols=1)


# --------------------------------------------------------------------------- #
# report + gate
# --------------------------------------------------------------------------- #
def test_write_and_require_preflight_roundtrip(tmp_path):
    report = {"market": "USD", "verdict": "PASS", "checks": {}}
    out = write_report(report, tmp_path / "preflight_USD.json")
    assert require_preflight(out, "USD")["verdict"] == "PASS"
    with pytest.raises(PreflightError, match="preflight report missing"):
        require_preflight(tmp_path / "absent.json", "USD")
    write_report({"market": "USD", "verdict": "FAIL"}, tmp_path / "preflight_USD.json")
    with pytest.raises(PreflightError, match="not verified"):
        require_preflight(tmp_path / "preflight_USD.json", "USD")
    write_report({"market": "CAD", "verdict": "PASS"}, tmp_path / "preflight_USD.json")
    with pytest.raises(PreflightError, match="not 'USD'"):
        require_preflight(tmp_path / "preflight_USD.json", "USD")


def test_main_writes_report_and_asserts_inputs(tmp_path, capsys):
    keep = _keep_columns()
    paths = _write_market(tmp_path, n_symbols=1, keep=keep)
    out = tmp_path / "preflight_USD.json"
    rc = main(["--market", "USD", "--assert-inputs", "--out", str(out), "--expected-symbols", "1",
               "--derived-dir", str(paths["derived"]), "--features-dir", str(paths["features"]),
               "--prune-recs", str(paths["prune"])])
    assert rc == 0
    assert json.loads(out.read_text())["verdict"] == "PASS"


def test_main_fails_on_malformed_market(tmp_path, capsys):
    paths = _write_market(tmp_path, n_symbols=1, keep=_keep_columns(), feature_symbols=[])
    out = tmp_path / "preflight_USD.json"
    rc = main(["--market", "USD", "--assert-inputs", "--out", str(out), "--expected-symbols", "1",
               "--derived-dir", str(paths["derived"]), "--features-dir", str(paths["features"]),
               "--prune-recs", str(paths["prune"])])
    assert rc == 1
    assert json.loads(out.read_text())["verdict"] == "FAIL"


# --------------------------------------------------------------------------- #
# on-disk integration (skipped when the WI-017 inputs / report are absent)
# --------------------------------------------------------------------------- #
DISK_REPORT = Path("reports/wi018/preflight_USD.json")


@pytest.mark.skipif(not DISK_REPORT.is_file(), reason="WI-018 preflight report not generated yet")
def test_disk_preflight_report_is_pass_and_complete():
    report = json.loads(DISK_REPORT.read_text())
    assert report["market"] == "USD"
    assert report["verdict"] == "PASS"
    assert all(report["checks"].values())
    assert report["summary"]["symbols"] == 593
    assert report["summary"]["total_rows"] > 2_000_000
    assert report["config"]["keep_columns"] == 88
    assert report["targets"]["first_touch_34"]["finite"] > 2_000_000
    assert report["targets"]["first_touch_34"]["unexpected_values"] == []
