"""Dash app skeleton for the visualizer / audit workbench (WI-085, Phase 0).

Operating rules (plan 26-W47 / D-028):
- `debug=False`; no `dcc.Interval` (no polling -> the idle process sleeps);
- one gunicorn worker with 2 threads (`tools/visualizer/serve.sh`), bound to 127.0.0.1
  and reached through an SSH tunnel;
- schema contracts run at startup and stop the server on drift;
- the process writes ONLY under `state/viz/`; `data/` is opened read-only.

Phase 1 (WI-086/087/088) adds the join index, KPI strip and views. This card ships the
scaffold, the loader, the contracts and the Phase-0 benchmark.
"""
from __future__ import annotations

import os

from dash import Dash, Input, Output, dcc, html

from src.visualizer import DEFAULT_BUDGET_BYTES, MARKETS, STATE_DIR, state_path
from src.visualizer.loader import VisualizerLoader
from src.visualizer.schema import assert_all_artifacts

WATERMARK = "evidence only - no verdicts; out-of-fold, but threshold-selection bias risk"


def build_loader(budget_bytes: int = DEFAULT_BUDGET_BYTES) -> VisualizerLoader:
    """One loader per worker: one in-memory panel copy, costed by the byte ledger."""
    return VisualizerLoader(budget_bytes=budget_bytes)


def create_app(loader: VisualizerLoader | None = None, check_schema: bool = True) -> Dash:
    """Build the Dash app; schema drift raises `SchemaError` before the server starts."""
    schema_report = assert_all_artifacts() if check_schema else {"markets": {}, "l0_ext": {}, "raw_ohlcv": []}
    loader = loader or build_loader()

    app = Dash(__name__, title="Signals audit workbench")
    app.server.config["JSON_SORT_KEYS"] = False
    status_rows = [
        html.Tr([html.Td(market), html.Td(f"{len(schema_report['markets'].get(market, {}))} artifacts")])
        for market in MARKETS
    ]
    app.layout = html.Div(
        [
            html.H2("Signals audit workbench - scaffold (WI-085)"),
            html.Div(WATERMARK, id="watermark", style={"color": "#8a6d3b", "fontWeight": "bold"}),
            html.Div(
                [
                    html.Label("Market"),
                    dcc.Dropdown(
                        id="market",
                        options=[{"label": m, "value": m} for m in MARKETS],
                        value=MARKETS[0],
                        clearable=False,
                        style={"width": "160px"},
                    ),
                ]
            ),
            html.Button("Refresh status", id="refresh", n_clicks=0),
            html.Div(id="status"),
            html.Table(
                [html.Thead(html.Tr([html.Th("Market"), html.Th("Artifacts checked")]))] + status_rows,
                style={"marginTop": "12px"},
            ),
            html.Pre(
                f"loader budget {loader.ledger.budget_bytes / 2**30:.1f} GB | state dir {STATE_DIR}",
                style={"color": "#555"},
            ),
        ]
    )

    @app.callback(Output("status", "children"), Input("refresh", "n_clicks"), Input("market", "value"))
    def _status(_clicks: int, market: str) -> list:
        """Per-control recompute: reads the loader's ledger only, never the panel."""
        snapshot = loader.ledger.snapshot()
        return [
            html.Div(f"market: {market}"),
            html.Div(f"resident columns: {snapshot['used_bytes'] / 2**20:.1f} MB / {snapshot['budget_bytes'] / 2**30:.1f} GB"),
            html.Div(f"cached column sets: {len(loader.columns)} | cached symbols: {len(loader.ohlcv)}"),
            html.Div(f"bench: {state_path('bench.json')}"),
        ]

    return app


app = create_app()
server = app.server  # gunicorn target: src.visualizer.app:server


if __name__ == "__main__":  # pragma: no cover - local single-process run
    app.run(
        debug=False,
        host=os.environ.get("VIZ_HOST", "127.0.0.1"),
        port=int(os.environ.get("VIZ_PORT", "8050")),
    )
