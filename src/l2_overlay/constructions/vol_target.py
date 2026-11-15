"""WI-069 — (c) vol-target entry-only sizing on the WI-068 CALIB survivor (D-027 §5 (c), Layer 2).

CONDITIONAL CARD, DISPATCHED (D-027 §6): a CALIB survivor exists — WI-068 construction (a), fixed h55
time exits on the frozen fib fallback entries (`data/models/l2_time_exit/<MARKET>_fib.parquet`; rows
`symbol, date, fold, r_event, t_event, r_h13, r_h55`). Its read-out is +231.8 bps (USD) / +473.0 bps
(CAD) net vs the event exit on identical rows with the fold ceiling FAILING on one fold id, so this
card sizes the same rows and attributes the outcome across VOL REGIMES rather than folds.

Sizing is ENTRY-ONLY: one weight per event, computed at entry and never revised, so a mid-trade resize
(25 bps × |Δsize|, D-027 §2) cannot occur; the cost per event is the single-leg round trip scaled by the
deployed size. CAUSALITY: the sizer reads `atr_pct_21` (ATR% of price at the entry bar) from the WI-036
causal panel. `xsec_vol_rank_cont` is the WI-058 FORWARD realized-vol label — admissible as a post-hoc
attribution axis only, never as a weight input.

    uv run python -m src.l2_overlay.constructions.vol_target --smoke   # synthetic, *_smoke roots
"""
from __future__ import annotations
import argparse, datetime as dt, hashlib
from pathlib import Path
import numpy as np
import pandas as pd
from src.l2_overlay import costs
from src.l2_overlay import fold_report as foldrep
from src.l2_overlay import harness as H

BASE_DIR = Path(__file__).resolve().parents[3]        # named input/output roots (never CLI args)
ENTRIES_ROOT = BASE_DIR / "data" / "models" / "l2_time_exit"    # WI-068 construction (a) survivor
ENTRY_NAME, PANEL_NAME = "{market}_fib.parquet", "wi036_panel_{market}.parquet"
PANEL_CACHE = Path("/tmp/wi036")                      # causal WI-036 panel (atr_pct_*, entropy_39)
REPORTS_ROOT, REPORTS_SMOKE_ROOT = (BASE_DIR / "reports" / "l2_vol_target",
                                    BASE_DIR / "reports" / "l2_vol_target_smoke")
MARKETS: tuple[str, ...] = ("USD", "CAD")
EXIT_ARM, BASELINE_ARM = "r_h55", "r_event"           # survivor arm vs the frozen event exit
VOL_COLUMN = "atr_pct_21"                             # causal entry-bar vol proxy (sizing axis)
REGIME_COLUMNS: tuple[str, ...] = ("xsec_vol_rank_cont", "disp_entropy_39")   # attribution only
DISP_OUT, DISP_FROM = "disp_entropy_39", "entropy_39"  # `_universe_dispersion` output ← source
ANN_VOL_TARGET, ANN_DAYS, W_MIN, W_MAX = 0.20, 252.0, 0.25, 2.0
VOL_NAN_POLICY = "min_weight"                         # an unusable entry vol sizes DOWN, never up
REGIME_QUANTILES, MIN_VOL_COVERAGE = 5, 0.99
SMOKE_ENTRIES, SMOKE_SEED, PLACEBO_SEED0, N_PLACEBO_SEEDS = 240, 69, 6900, 5
N_JOBS = 2                                            # repo law; nothing here fans out
PANEL_COLUMNS: tuple[str, ...] = ("symbol", "date", VOL_COLUMN, DISP_FROM)
CALIB_END = H.CALIB_END
__all__ = ["BASE_DIR", "ENTRIES_ROOT", "REPORTS_ROOT", "REPORTS_SMOKE_ROOT", "MARKETS", "EXIT_ARM",
           "BASELINE_ARM", "VOL_COLUMN", "REGIME_COLUMNS", "ANN_VOL_TARGET", "W_MIN", "W_MAX",
           "VOL_NAN_POLICY", "causal_vol", "vol_imputed", "target_weights", "regime_bucket",
           "regime_axes", "sized_net_frac", "per_unit_edge_bps", "risk_adjusted", "entries_key",
           "compare_sized_vs_unsized", "placebo_sized_edge", "attach_features", "load_entries",
           "load_panel", "synthetic_fixture", "write_calib_report", "run_market", "main"]


def _fmt(x, spec: str = "{:+.2f}") -> str:
    return "n/a" if not np.isfinite(float(x)) else spec.format(float(x))


def causal_vol(panel, *, vol_column: str = VOL_COLUMN) -> np.ndarray:
    """Entry-bar causal vol proxy (float32); a missing column fails closed (bad values are counted)."""
    if vol_column not in getattr(panel, "columns", []):
        raise KeyError(f"panel lacks the causal sizing column {vol_column!r}")
    return np.asarray(panel[vol_column], dtype="float32")


def vol_imputed(panel, *, vol_column: str = VOL_COLUMN) -> int:
    """Rows whose entry vol is unusable and are therefore sized down by policy (`VOL_NAN_POLICY`)."""
    v = np.asarray(causal_vol(panel, vol_column=vol_column), dtype="float64")
    return int((~np.isfinite(v) | (v <= 0.0)).sum())


def target_weights(panel, ann_vol_target: float = ANN_VOL_TARGET, *, vol_column: str = VOL_COLUMN,
                   w_min: float = W_MIN, w_max: float = W_MAX) -> np.ndarray:
    """ENTRY-ONLY weights: w = ann_vol_target / (atr%_t0 · √252) per event, clipped; never revised.

    Unusable entry vol (non-finite or non-positive) takes `w_min` — an explicit conservative policy,
    never a silent mean imputation (`vol_imputed` counts those rows).
    """
    if not np.isfinite(float(ann_vol_target)) or float(ann_vol_target) <= 0.0:
        raise ValueError("ann_vol_target must be finite and positive")
    vol = (causal_vol(panel, vol_column=vol_column) * np.sqrt(float(ANN_DAYS))).astype("float64")
    ok = np.isfinite(vol) & (vol > 0.0)
    w = np.full(vol.size, float(w_min), dtype="float64")
    w[ok] = np.clip(float(ann_vol_target) / vol[ok], float(w_min), float(w_max))
    return w.astype("float32")


def regime_bucket(values, n: int = REGIME_QUANTILES) -> np.ndarray:
    """Per-event quantile bucket of one attribution axis (int64, -1 where the axis is missing)."""
    v = np.asarray(values, dtype="float64")
    out, ok = np.full(v.size, -1, dtype="int64"), np.isfinite(v)
    if ok.any():
        rank = pd.Series(v[ok]).rank(pct=True).to_numpy("float64")
        out[ok] = np.clip((rank * int(n) - 1e-9).astype("int64"), 0, int(n) - 1)
    return out


def regime_axes(panel, *, columns=REGIME_COLUMNS) -> dict:
    """Attribution axes actually present (never silently substituted): causal vol + named regimes."""
    axes: dict[str, np.ndarray] = {}
    has = getattr(panel, "columns", [])
    if VOL_COLUMN in has:
        axes[f"vol_regime:{VOL_COLUMN}"] = np.asarray(panel[VOL_COLUMN], dtype="float64")
    dates = pd.to_datetime(pd.Series(np.asarray(panel["date"]))) if "date" in has else None
    for col in tuple(columns):
        if col in has:
            axes[col] = np.asarray(panel[col], dtype="float64")
        elif col == DISP_OUT and DISP_FROM in has and dates is not None:
            axes[col] = panel.groupby(dates)[DISP_FROM].transform("std", ddof=0).to_numpy("float64")
    return axes


def sized_net_frac(r, weights, *, cost_bps: float = costs.SINGLE_LEG_BPS) -> np.ndarray:
    """Per-event net contribution of a sized trade: w·r − w·cost (the round trip scales with size)."""
    w, rr = np.asarray(weights, "float64"), np.asarray(r, "float64")
    return w * rr - w * costs.bps_to_frac(cost_bps)


def per_unit_edge_bps(r, weights, *, cost_bps: float = costs.SINGLE_LEG_BPS) -> float:
    """Net bps per unit of deployed size: 1e4·Σ(w·r)/Σw − cost; unit weights ⇒ absolute arm edge."""
    w, rr = np.asarray(weights, "float64"), np.asarray(r, "float64")
    ok = np.isfinite(w) & np.isfinite(rr) & (w > 0.0)
    rr, w = rr[ok], w[ok]
    if not rr.size or float(w.sum()) <= 0.0:
        return float("nan")
    return costs.edge_bps(float((w * rr).sum() / w.sum())) - float(cost_bps)


def risk_adjusted(returns) -> float:
    """Mean/std (ddof=1) of a per-event net contribution series — the risk-adjusted read-out."""
    x = np.asarray(returns, "float64")
    x = x[np.isfinite(x)]
    sd = float(x.std(ddof=1)) if x.size > 1 else float("nan")
    return float(x.mean() / sd) if np.isfinite(sd) and sd > 0.0 else float("nan")


def entries_key(entries) -> str:
    """Stable digest of the sized rows (provenance: every arm sizes the same entry set)."""
    keys = sorted(f"{s}|{d}" for s, d in zip(entries["symbol"].astype(str),
                                             pd.to_datetime(pd.Series(entries["date"].to_numpy()))))
    return hashlib.sha1("\n".join(keys).encode()).hexdigest()[:16]


def _regime_table(r, weights, axes, fold) -> list[dict]:
    """Per-regime sizing delta — the concentration read-out when folds are degenerate (one fold id)."""
    rows = []
    for axis, values in axes.items():
        bucket = regime_bucket(values)
        for b in sorted({int(v) for v in bucket.tolist() if int(v) >= 0}):
            m = bucket == b
            unsized = per_unit_edge_bps(r[m], np.ones(int(m.sum())))
            sized = per_unit_edge_bps(r[m], weights[m])
            rows.append({"axis": axis, "bucket": b, "n": int(m.sum()), "folds":
                         sorted({int(v) for v in fold[m].tolist()}), "unsized_bps": unsized,
                         "mean_weight": float(np.asarray(weights, "float64")[m].mean()),
                         "sized_bps": sized, "delta_bps": sized - unsized})
    return rows


def compare_sized_vs_unsized(entries, panel, *, ann_vol_target: float = ANN_VOL_TARGET,
                             arm: str = EXIT_ARM, cost_bps: float = costs.SINGLE_LEG_BPS) -> dict:
    """Sized vs unsized on the SAME rows and exit arm; mandatory fold report + regime attribution.

    `panel` must be row-aligned to `entries` — a real run passes the merged frame (`attach_features`),
    because the full causal panel is not in entry-row order.
    """
    if arm not in entries.columns:
        raise KeyError(f"entries lack the survivor arm column {arm!r}")
    if "fold" not in entries.columns:
        raise KeyError("entries lack 'fold' — the fold report is mandatory (D-027 §7)")
    r, fold = np.asarray(entries[arm], dtype="float64"), np.asarray(entries["fold"], dtype="int64")
    weights = target_weights(panel, ann_vol_target)
    if weights.shape[0] != r.shape[0]:
        raise ValueError(f"weights ({weights.shape[0]}) are not aligned to the {r.shape[0]} events")
    allm = np.ones(r.size, bool)

    def edge(mask, w):
        """Per-unit-size net bps on one row subset (unit weights ⇒ the unsized arm)."""
        return per_unit_edge_bps(r[mask], np.asarray(w, "float64")[mask], cost_bps=cost_bps)

    unsized_bps, sized_bps = edge(allm, np.ones(r.size)), edge(allm, weights)
    per_fold = {int(f): costs.bps_to_frac(edge(fold == f, weights) - edge(fold == f, np.ones(r.size)))
                for f in sorted({int(v) for v in fold.tolist()})}
    rep = foldrep.fold_report(per_fold)                 # mandatory: fails closed when the rows are absent
    return {"market": entries.attrs.get("market", ""), "arm": arm, "n_entries": int(r.size),
            "entry_key": entries_key(entries), "ann_vol_target": float(ann_vol_target),
            "cost_bps": float(cost_bps), "mean_weight": float(np.asarray(weights, "float64").mean()),
            "n_vol_imputed": vol_imputed(panel), "vol_nan_policy": VOL_NAN_POLICY,
            "unsized_bps": float(unsized_bps), "sized_bps": float(sized_bps),
            "edge_delta_bps": float(sized_bps - unsized_bps),
            "ra_sized": risk_adjusted(sized_net_frac(r, weights, cost_bps=cost_bps)),
            "ra_unsized": risk_adjusted(sized_net_frac(r, np.ones(r.size), cost_bps=cost_bps)),
            "per_fold_net_edge": per_fold, "fold_report": rep,
            "regimes": _regime_table(r, weights, regime_axes(panel), fold),
            "stop": H.calib_stop(sized_bps, rep)}


def placebo_sized_edge(entries, panel, *, arm: str = EXIT_ARM, ann_vol_target: float = ANN_VOL_TARGET,
                       seed0: int = PLACEBO_SEED0, n_seeds: int = N_PLACEBO_SEEDS) -> dict:
    """Weight-permutation placebo: destroy the vol→size link, keep the row set and the frozen exit."""
    r = np.asarray(entries[arm], dtype="float64")
    one = np.ones(r.size)
    w = target_weights(panel, ann_vol_target).astype("float64")
    observed = per_unit_edge_bps(r, w) - per_unit_edge_bps(r, one)
    null = np.asarray([per_unit_edge_bps(r, np.random.default_rng(int(seed0) + s).permutation(w))
                       - per_unit_edge_bps(r, one) for s in range(int(n_seeds))], dtype="float64")
    null = null[np.isfinite(null)]
    mean = float(null.mean()) if null.size else float("nan")
    sd = float(null.std(ddof=1)) if null.size > 1 else float("nan")
    z = float((observed - mean) / sd) if np.isfinite(sd) and sd > 0.0 else float("nan")
    return {"observed_bps": float(observed), "null_mean_bps": mean, "null_sd_bps": sd, "z": z}


def attach_features(entries, panel, *, coverage: float = MIN_VOL_COVERAGE) -> pd.DataFrame:
    """Join the causal panel columns onto the entry rows on (symbol, date); float32, fail closed."""
    left, right = entries.copy(), panel.copy()
    for frame in (left, right):
        frame["symbol"], frame["date"] = frame["symbol"].astype(str), pd.to_datetime(frame["date"])
    keep = [c for c in PANEL_COLUMNS if c in right.columns]
    out = left.merge(right[keep].drop_duplicates(["symbol", "date"]), on=["symbol", "date"], how="left")
    for c in keep:
        if c not in ("symbol", "date"):
            out[c] = out[c].astype("float32")
    got = float(np.isfinite(out[VOL_COLUMN].to_numpy("float32")).mean()) if VOL_COLUMN in out else 0.0
    if got < float(coverage):
        raise RuntimeError(f"causal panel coverage {got:.3f} < {float(coverage):.2f} at the entry rows "
                           f"({PANEL_CACHE / PANEL_NAME.format(market='<MARKET>')})")
    return out


def load_entries(market: str, *, root=ENTRIES_ROOT, entry_name: str = ENTRY_NAME) -> pd.DataFrame:
    """Survivor entry rows (CALIB only — EVAL rows are dropped before any arithmetic), float32."""
    path = Path(root) / str(entry_name).format(market=market)
    if not path.exists():
        raise FileNotFoundError(f"survivor entry artifact missing: {path}")
    raw = pd.read_parquet(path)
    missing = {"symbol", "date", EXIT_ARM, "fold"} - set(raw.columns)
    if missing:
        raise KeyError(f"entry artifact {path} lacks {sorted(missing)}")
    frame = raw[pd.to_datetime(raw["date"]) < CALIB_END].copy()
    frame["symbol"], frame["date"] = frame["symbol"].astype(str), pd.to_datetime(frame["date"])
    for c in (BASELINE_ARM, EXIT_ARM):
        if c in frame.columns:
            frame[c] = frame[c].astype("float32")
    frame["fold"], frame.attrs["market"] = frame["fold"].to_numpy("int64"), market
    return frame


def load_panel(market: str, *, cache=PANEL_CACHE, panel_name: str = PANEL_NAME) -> pd.DataFrame:
    """The causal WI-036 feature panel, only the columns this card reads."""
    path = Path(cache) / str(panel_name).format(market=market)
    if not path.exists():
        raise RuntimeError(f"causal feature panel missing: {path}")
    panel = pd.read_parquet(path, columns=list(PANEL_COLUMNS))
    panel["symbol"], panel["date"] = panel["symbol"].astype(str), pd.to_datetime(panel["date"])
    return panel


def synthetic_fixture(market: str = "USD", n_entries: int = SMOKE_ENTRIES, seed: int = SMOKE_SEED,
                      *, sized_edge: bool = True) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Synthetic survivor rows + panel: vol regimes carry the edge only when `sized_edge` is asked."""
    rng = np.random.default_rng(int(seed) + (0 if market == "USD" else 1))
    n = int(n_entries)
    dates = pd.to_datetime("2021-01-04") + pd.to_timedelta(np.arange(n) // 25, unit="D")  # 25-name xsec
    symbols, vol = np.asarray([f"S{i % 25:02d}" for i in range(n)]), rng.uniform(0.005, 0.06, n)
    tilt = (0.02 * (vol <= np.median(vol)) - 0.01 * (vol > np.median(vol))) if sized_edge else np.zeros(n)
    r_h55 = (0.03 + tilt + rng.normal(0.0, 0.004, n)).astype("float32")
    entries = pd.DataFrame({"symbol": symbols, "date": dates, "fold": np.zeros(n, dtype="int64"),
                            "r_event": (r_h55 - 0.02).astype("float32"),
                            "t_event": np.full(n, 39, "int64"), "r_h13": (r_h55 - 0.01).astype("float32"),
                            "r_h55": r_h55})
    panel = pd.DataFrame({"symbol": symbols, "date": dates, "atr_pct_21": vol.astype("float32"),
                          "entropy_39": rng.normal(1.0, 0.2, n).astype("float32"),
                          "xsec_vol_rank_cont": rng.random(n).astype("float32")})  # forward label
    entries.attrs["market"], panel.attrs["market"] = market, market
    return entries, panel


def write_calib_report(path, market: str, result: dict, placebo: dict, *, smoke: bool = False) -> Path:
    """`reports/l2_vol_target/calib_<market>[_smoke].md` — sized vs unsized, regimes, fold report."""
    rep = result["fold_report"]
    tag = "  (smoke / synthetic fixture)" if smoke else ""
    reg = result["regimes"]
    lines = [f"# L2 vol-target entry-only sizing — WI-068 survivor (a), {market}{tag}", "",
             f"- Generated (UTC): {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
             f"- Survivor arm `{result['arm']}` on {result['n_entries']:,} identical rows "
             f"(key `{result['entry_key']}`); EVAL unread (WI-071)",
             f"- Entry-only sizing: ann_vol_target {result['ann_vol_target']:.0%}, mean weight "
             f"{_fmt(result['mean_weight'])} clipped to [{W_MIN}, {W_MAX}], no mid-trade resize; "
             f"entry-vol policy `{result['vol_nan_policy']}` on {result['n_vol_imputed']} row(s)",
             f"- Per-unit-size net edge: unsized {_fmt(result['unsized_bps'])} bps → sized "
             f"{_fmt(result['sized_bps'])} bps (delta {_fmt(result['edge_delta_bps'])} bps); cost "
             f"{result['cost_bps']:.0f} bps round trip",
             f"- Risk-adjusted (mean/std): unsized {_fmt(result['ra_unsized'], '{:+.3f}')} → sized "
             f"{_fmt(result['ra_sized'], '{:+.3f}')}; placebo z {_fmt(placebo['z'], '{:+.2f}')} "
             f"(observed {_fmt(placebo['observed_bps'])} bps)",
             f"- Fold report (mandatory, fails closed): max-fold share {_fmt(rep['max_fold_share'])} "
             f"(ceiling {foldrep.FOLD_CEILING_SHARE:.0%}, {'pass' if rep['fold_ceiling_ok'] else 'FAIL'}); "
             f"positive folds {rep['n_positive_folds']}/{rep['n_folds']}",
             f"- Stop/continue: **{'STOP' if result['stop']['stop'] else 'CONTINUE'}**"
             + (f" — {'; '.join(result['stop']['reasons'])}" if result["stop"]["reasons"] else "")]
    lines += ["", "| fold | net sizing delta (bps) |", "| ---: | ---: |",
              *[f"| {f} | {_fmt(costs.edge_bps(v))} |"
                for f, v in sorted(result["per_fold_net_edge"].items())],
              "", "| regime axis | bucket | n | mean weight | unsized bps | sized bps | delta bps |",
              "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
              *[f"| {x['axis']} | {x['bucket']} | {x['n']:,} | {x['mean_weight']:.3f} | "
                f"{_fmt(x['unsized_bps'])} | {_fmt(x['sized_bps'])} | {_fmt(x['delta_bps'])} |" for x in reg],
              "", f"- Attribution axes present: {sorted({x['axis'] for x in reg}) or 'none'} (absent axes "
                  f"are recorded, never substituted; `xsec_vol_rank_cont` is the forward WI-058 label — "
                  f"post-hoc attribution only)",
              "- Layer separation: no learner refit, no AUC selection, no EVAL read.",
              "", "Record-only: no shortlist, no deployment, no live trading."]
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")
    return path


def run_market(market: str, entries: pd.DataFrame, panel: pd.DataFrame, *, report_root=REPORTS_ROOT,
               smoke: bool = False) -> dict:
    """One market: size the survivor rows, write the CALIB card + fold report, print one line."""
    entries = attach_features(entries, panel)
    result, placebo = compare_sized_vs_unsized(entries, entries), placebo_sized_edge(entries, entries)
    suffix = "_smoke" if smoke else ""
    path = write_calib_report(Path(report_root) / f"calib_{market}{suffix}.md", market, result,
                              placebo, smoke=smoke)
    foldrep.write_fold_report(result["fold_report"], Path(report_root) / f"fold_{market}{suffix}.json")
    print(f"[l2.voltarget] {market}: n={result['n_entries']} unsized={_fmt(result['unsized_bps'], '{:+.0f}')}"
          f" sized={_fmt(result['sized_bps'], '{:+.0f}')}bps delta={_fmt(result['edge_delta_bps'], '{:+.0f}')}"
          f"bps z={_fmt(placebo['z'], '{:+.2f}')} "
          f"{'STOP' if result['stop']['stop'] else 'CONTINUE'} -> {path.name}")
    return result


def main(argv=None) -> int:
    """CLI: `--smoke` (synthetic, `*_smoke` roots) or the full CALIB run on the survivor artifacts."""
    ap = argparse.ArgumentParser(description="WI-069 vol-target entry-only sizing on the WI-068 survivor")
    ap.add_argument("--smoke", action="store_true", help="synthetic run into the *_smoke roots")
    ap.add_argument("--market", default=None, help="limit to one market (default: both)")
    args = ap.parse_args(argv)
    for mk in (args.market,) if args.market else MARKETS:
        if args.smoke:
            run_market(mk, *synthetic_fixture(mk), report_root=REPORTS_SMOKE_ROOT, smoke=True)
        else:
            run_market(mk, load_entries(mk), load_panel(mk), report_root=REPORTS_ROOT)
    print(f"[l2.voltarget] {'smoke' if args.smoke else 'calib'} reports -> "
          f"{REPORTS_SMOKE_ROOT if args.smoke else REPORTS_ROOT} | EXIT:0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
