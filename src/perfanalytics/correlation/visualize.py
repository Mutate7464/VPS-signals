"""WI-015 addendum — result visualization from the alignment matrix.

Derives every output from the **already-computed** `alignment_{market}.csv`
(held-out ICs, noise margins, sign matches) — nothing is recomputed, so the
heatmap, ranked table and Markdown summary cannot drift from the matrix the
analysis wrote.

Outputs per market, under `reports/perfanalytics/`:
    heatmap_{market}.png          family × window heatmap of signed held-out IC.
                                  Rows = target×horizon, grouped one block per
                                  feature family; columns = fib window; cell =
                                  held-out mean IC (diverging colormap, blank
                                  where the feature is absent).
    alignment_top_{market}.csv    top-10 family×window per target×horizon by |IC|,
                                  with noise margin, sign-match vs the E5 best
                                  factor, and pass/fail.
    alignment_{market}.md         a summary section appended: which family and
                                  which window aligns best per target, with the
                                  family-vs-timeframe comparison the admin asked
                                  for.

Determinism: the CSV is the single source; re-running yields identical outputs.
matplotlib figures are batched (≤10) and closed with `plt.close('all')` +
`gc.collect()` after each batch (host rule).

CLI:
    python -m src.perfanalytics.correlation.visualize            # BOTH, CAD then USD
    python -m src.perfanalytics.correlation.visualize --market CAD
"""

from __future__ import annotations

import argparse
import gc
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless: no display on the build host

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from src.market_cli import MarketSelectionError, normalize_market  # noqa: E402
from src.perfanalytics.features.panel import FIB_GRID, FAMILIES  # noqa: E402
from src.perfanalytics.markets import resolve_markets  # noqa: E402

BASE_DIR = Path(__file__).resolve().parents[3]
REPORTS = BASE_DIR / "reports" / "perfanalytics"

TOP_N = 10
SUMMARY_MARKER = "<!-- WI-015 ADDENDUM SUMMARY (generated — do not edit above this line) -->"
TARGET_ORDER = [f"T{t}@{k}" for k in (15, 20) for t in (1, 2, 3, 4)]


def load_matrix(market: str, reports_dir: Path | None = None) -> pd.DataFrame:
    """The alignment CSV for one market (the single held-out source artifact)."""
    root = REPORTS if reports_dir is None else Path(reports_dir)
    path = root / f"alignment_{normalize_market(market)}.csv"
    if not path.exists():
        raise FileNotFoundError(f"alignment matrix not found: {path}")
    return pd.read_csv(path)


def ranked_table(table: pd.DataFrame, market: str, top_n: int = TOP_N) -> pd.DataFrame:
    """Top-N family×window per target×horizon by |held-out IC|."""
    rows = []
    for (target, horizon), g in table.groupby(["target", "horizon"], sort=True):
        g = g[np.isfinite(g["held_out_ic"])].copy()
        if g.empty:
            continue
        g["abs_ic"] = g["held_out_ic"].abs()
        g = g.sort_values(["abs_ic", "column"], ascending=[False, True]).head(top_n)
        for rank, (_, r) in enumerate(g.iterrows(), start=1):
            rows.append(
                {
                    "target": target,
                    "horizon": int(horizon),
                    "rank": rank,
                    "family": r["family"],
                    "window": int(r["window"]),
                    "held_out_ic": r["held_out_ic"],
                    "noise_margin": r["noise_margin"],
                    "sign_match_vs_e5": bool(r["sign_match"]),
                    "pass": bool(r["pass"]),
                }
            )
    return pd.DataFrame(rows)


def _heatmap_matrix(table: pd.DataFrame) -> tuple[np.ndarray, list[str]]:
    """(rows × windows) signed held-out IC matrix, one row-block per family."""
    lookup = {
        (r["family"], f"{r['target']}@{int(r['horizon'])}", int(r["window"])): r["held_out_ic"]
        for _, r in table.iterrows()
    }
    mat = np.full((len(FAMILIES) * len(TARGET_ORDER), len(FIB_GRID)), np.nan)
    labels: list[str] = []
    for i, fam in enumerate(FAMILIES):
        for j, target in enumerate(TARGET_ORDER):
            row = i * len(TARGET_ORDER) + j
            labels.append(f"{fam} · {target}")
            for c, window in enumerate(FIB_GRID):
                mat[row, c] = lookup.get((fam, target, window), np.nan)
    return mat, labels


def build_heatmap(table: pd.DataFrame, market: str, out_path: Path) -> Path:
    """Family-block × window heatmap of signed held-out IC (one figure)."""
    mat, labels = _heatmap_matrix(table)
    finite = mat[np.isfinite(mat)]
    vmax = float(np.percentile(np.abs(finite), 95)) if finite.size else 1.0
    vmax = vmax or 1.0

    fig, ax = plt.subplots(figsize=(7.5, 0.16 * len(labels) + 1.6))
    cmap = plt.get_cmap("RdBu_r").with_extremes(bad="#e8e8e8")
    im = ax.imshow(mat, aspect="auto", cmap=cmap, vmin=-vmax, vmax=vmax, interpolation="nearest")
    ax.set_xticks(range(len(FIB_GRID)), [str(w) for w in FIB_GRID], fontsize=8)
    ax.set_yticks(range(len(labels)), labels, fontsize=6)
    ax.set_xlabel("fib window (sessions)", fontsize=9)
    for i in range(1, len(FAMILIES)):
        ax.axhline(i * len(TARGET_ORDER) - 0.5, color="black", linewidth=0.6)
    ax.set_title(
        f"WI-015 {market}: held-out Spearman IC by feature family × fib window\n"
        f"(rows grouped by family; blank = feature absent/undefined)",
        fontsize=10,
    )
    cbar = fig.colorbar(im, ax=ax, fraction=0.02, pad=0.02)
    cbar.set_label("held-out mean IC (signed)", fontsize=8)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=130)
    plt.close("all")
    gc.collect()
    return out_path


def summary_section(table: pd.DataFrame, market: str) -> str:
    """Family-and-window-vs-timeframe reading of the matrix (Markdown)."""
    finite = table[np.isfinite(table["held_out_ic"])]
    lines = [
        "",
        SUMMARY_MARKER,
        "",
        f"## Summary — best family and best timeframe ({market})",
        "",
        "Best **family** × **window** per target × horizon (by |held-out IC|):",
        "",
        "| Target | Best family | Best window | Held-out IC | Noise margin | Pass |",
        "| :--- | :--- | ---: | ---: | ---: | :--- |",
    ]
    best_rows: list[dict] = []
    for (target, horizon), g in finite.groupby(["target", "horizon"], sort=True):
        best = g.loc[g["held_out_ic"].abs().idxmax()]
        best_rows.append(best.to_dict())
        lines.append(
            f"| {target}@{int(horizon)} | `{best['family']}` | {int(best['window'])} | "
            f"{best['held_out_ic']:+.4f} | {best['noise_margin']:.4f} | "
            f"{'PASS' if best['pass'] else 'fail'} |"
        )

    # family-vs-timeframe: which family wins most often, and which window scale
    if best_rows:
        fam_counts = pd.Series([r["family"] for r in best_rows]).value_counts()
        win_counts = pd.Series([int(r["window"]) for r in best_rows]).value_counts()
        top_fam = fam_counts.index[0]
        top_windows = ", ".join(str(w) for w in win_counts.index[:3])
        mean_abs_by_window = (
            finite.assign(abs_ic=finite["held_out_ic"].abs())
            .groupby("window")["abs_ic"]
            .mean()
            .sort_values(ascending=False)
        )
        strongest_window = int(mean_abs_by_window.index[0])
        lines += [
            "",
            "**Family vs timeframe.**",
            "",
            f"- Most frequent best family across the eight target×horizon cells: `{top_fam}` "
            f"({fam_counts.iloc[0]}/{len(best_rows)} cells).",
            f"- Most frequent best window: {top_windows}.",
            f"- Window with the highest mean |held-out IC| over all family×target cells: "
            f"**{strongest_window}** ({mean_abs_by_window.iloc[0]:.4f}).",
            f"- Pass rate: {int(finite['pass'].sum())} of {len(finite)} finite cells clear the "
            "same-sign + noise-margin bar.",
            "",
            "Window means (ranked — the timeframe comparison at a glance):",
            "",
            "| Window | Mean \\|IC\\| | Best \\|IC\\| in window |",
            "| ---: | ---: | ---: |",
        ]
        best_abs_by_window = (
            finite.assign(abs_ic=finite["held_out_ic"].abs()).groupby("window")["abs_ic"].max()
        )
        for window, mean_abs in mean_abs_by_window.items():
            lines.append(f"| {int(window)} | {mean_abs:.4f} | {best_abs_by_window[window]:.4f} |")
    lines.append("")
    return "\n".join(lines)


def append_summary(table: pd.DataFrame, market: str, md_path: Path) -> Path:
    """Append (idempotently) the summary section to `alignment_{market}.md`."""
    body = md_path.read_text() if md_path.exists() else f"# WI-015 alignment ({market})\n"
    if SUMMARY_MARKER in body:
        body = body[: body.index(SUMMARY_MARKER)].rstrip() + "\n"
    md_path.write_text(body.rstrip() + "\n" + summary_section(table, market))
    return md_path


def build_all(market: str, reports_dir: Path | None = None) -> dict[str, Path]:
    """Write heatmap + ranked table + summary section for one market."""
    root = REPORTS if reports_dir is None else Path(reports_dir)
    code = normalize_market(market)
    table = load_matrix(code, root)
    rank = ranked_table(table, code)
    top_path = root / f"alignment_top_{code}.csv"
    rank.to_csv(top_path, index=False)
    heat_path = build_heatmap(table, code, root / f"heatmap_{code}.png")
    md_path = append_summary(table, code, root / f"alignment_{code}.md")
    return {"heatmap": heat_path, "top": top_path, "md": md_path}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--market", default=None, metavar="CAD|USD", help="Omit for both (CAD then USD).")
    ap.add_argument("--reports-dir", default=None, help="Override the report root (default reports/perfanalytics).")
    args = ap.parse_args(argv)

    try:
        markets = resolve_markets(args.market)
    except MarketSelectionError as exc:
        print(f"[perfanalytics.visualize] {exc}", file=sys.stderr)
        return 2

    root = Path(args.reports_dir) if args.reports_dir else None
    for market in markets:
        paths = build_all(market, root)
        print(f"[perfanalytics.visualize] {market}: {paths['heatmap']}, {paths['top']}, summary appended")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
