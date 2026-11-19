"""WI-085: the UI process writes only under `state/viz/` and opens `data/` read-only."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from src.visualizer import STATE_DIR, state_path
from src.visualizer.loader import VisualizerLoader

REPO = Path(__file__).resolve().parents[2]
SKIP_DIR_NAMES = {".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache", "node_modules"}
SKIP_REL_PATHS = {"state/viz"}


def _snapshot(root: Path) -> dict[str, tuple[int, int]]:
    snapshot: dict[str, tuple[int, int]] = {}
    for dirpath, dirnames, filenames in os.walk(root):
        current = Path(dirpath)
        kept = []
        for name in dirnames:
            if name in SKIP_DIR_NAMES:
                continue
            if (current / name).relative_to(root).as_posix() in SKIP_REL_PATHS:
                continue
            kept.append(name)
        dirnames[:] = kept
        for name in filenames:
            path = current / name
            try:
                stat = path.stat()
            except OSError:  # pragma: no cover - races with other writers
                continue
            snapshot[path.relative_to(root).as_posix()] = (int(stat.st_size), int(stat.st_mtime_ns))
    return snapshot


def test_loader_session_writes_nothing_outside_its_state_dir(tmp_path) -> None:
    state_dir = tmp_path / "viz_state"
    before = _snapshot(REPO)
    loader = VisualizerLoader(state_dir=state_dir)
    loader.load_columns("CAD", ["rsi_5", "atr_pct_20"])
    loader.sample_ohlcv("CAD", "RY")
    _, counts = loader.join_l0_ext("CAD", "clv")
    loader.write_state("manifest.json", loader.manifest())
    loader.write_state("bench.json", {"filter_latency": loader.filter_latency("CAD", repeats=1)})
    after = _snapshot(REPO)

    assert counts["matched_rows"] == counts["panel_rows"]
    assert (state_dir / "bench.json").is_file() and (state_dir / "manifest.json").is_file()
    changed = sorted(set(after.items()) ^ set(before.items()))
    assert changed == [], f"writes/reads escaped the state dir: {changed[:5]}"


def test_default_state_dir_is_state_viz() -> None:
    assert STATE_DIR.name == "viz" and STATE_DIR.parent.name == "state"
    assert state_path("bench.json").as_posix().endswith("state/viz/bench.json")


@pytest.mark.parametrize("name", ["../escape.json", "sub/bench.json", "/tmp/bench.json", ""])
def test_write_state_rejects_paths_outside_the_state_dir(tmp_path, name: str) -> None:
    loader = VisualizerLoader(state_dir=tmp_path / "viz")
    with pytest.raises(ValueError):
        loader.write_state(name, {"x": 1})


def test_no_data_file_is_modified_by_a_load() -> None:
    target = REPO / "data" / "features" / "features_CAD.parquet"
    before = (target.stat().st_size, target.stat().st_mtime_ns)
    frame = VisualizerLoader().load_columns("CAD", ["rsi_14"])
    after = (target.stat().st_size, target.stat().st_mtime_ns)
    assert len(frame) > 0 and after == before


def test_app_and_serve_script_honour_the_operating_rules() -> None:
    app_source = (REPO / "src" / "visualizer" / "app.py").read_text(encoding="utf-8")
    assert "dcc.Interval(" not in app_source, "polling would burn idle CPU"
    assert "debug=False" in app_source
    serve = (REPO / "tools" / "visualizer" / "serve.sh").read_text(encoding="utf-8")
    assert "--workers 1" in serve and "--threads 2" in serve
    assert "127.0.0.1" in serve
    assert "uv run gunicorn" in serve


def test_gunicorn_target_boots_with_startup_schema_checks() -> None:
    from src.visualizer import app as app_module

    assert app_module.server is not None
    assert app_module.app.layout is not None
    assert "no verdicts" in app_module.WATERMARK
    assert app_module.build_loader().ledger.budget_bytes == 3 * 1024**3
