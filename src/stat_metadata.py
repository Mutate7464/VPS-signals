"""Sprint 3 — Statistical metadata profiler (stationarity, cross-sectional ranks, MI, VIF).

Transforms the raw feature matrix into a clean, stationary, decorrelated
metadata feed for XGBoost:

  1. Stationarity (Augmented Dickey-Fuller): per feature, run ADF on up to
     `ADF_SAMPLE_TICKERS` tickers; flag any feature whose median p > 0.05 for a
     60-day rolling Z-score transform.
  2. Cross-sectional percentile ranks (`_cs_pct`) grouped strictly by `date`
     (point-in-time safe — each date's rank uses only that date's cross-section).
  3. Target relevance (Mutual Information) per target.
  4. Iterative Variance Inflation Factor pruning (`VIF < 5.0`), retaining the
     higher-MI member of any collinear pair.

All MI/VIF/ADF statistics are computed strictly on the *training* split (the
first `TRAIN_SPLIT_FRACTION` of dates) to avoid feature-selection look-ahead.

CLI:
    python -m src.stat_metadata --market USD --vif-threshold 5.0 --min-mi-percentile 30
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_selection import mutual_info_classif
from statsmodels.tsa.stattools import adfuller

from src.state_manager import init_dirs, update_state
from src.targets import TARGET_COLUMNS

BASE_DIR = Path(__file__).resolve().parents[1]
FEATURES_DIR = BASE_DIR / "data" / "features"
CATALOG_PATH = BASE_DIR / "data" / "metadata_catalog_{market}.json"
REPORT_PATH = BASE_DIR / "reports" / "sprint3_metadata_selection.md"

VIF_THRESHOLD = 5.0
MIN_MI_PERCENTILE = 30
ADF_SAMPLE_TICKERS = 50
ADF_P_THRESHOLD = 0.05
ADF_MIN_OBS = 30
TRAIN_SPLIT_FRACTION = 0.80
ROLLING_Z_WINDOW = 60


# --------------------------------------------------------------------------- #
# Loading + splitting
# --------------------------------------------------------------------------- #
def load_dataset(market: str) -> pd.DataFrame:
    feats = pd.read_parquet(FEATURES_DIR / f"features_{market}.parquet")
    targs = pd.read_parquet(FEATURES_DIR / f"targets_{market}.parquet")
    targs = targs[["date", "symbol", "market"] + TARGET_COLUMNS]
    return feats.merge(targs, on=["date", "symbol", "market"], how="inner")


def train_split(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Timestamp]:
    dates = np.sort(df["date"].unique())
    cutoff = pd.Timestamp(dates[int(len(dates) * TRAIN_SPLIT_FRACTION)])
    return df[df["date"] < cutoff].reset_index(drop=True), cutoff


# --------------------------------------------------------------------------- #
# Stationarity (ADF)
# --------------------------------------------------------------------------- #
def adf_analysis(train: pd.DataFrame, feature_cols: list[str]) -> dict:
    results = {}
    for feat in feature_cols:
        ps = []
        tickers = list(train["symbol"].unique())[:ADF_SAMPLE_TICKERS]
        for sym in tickers:
            series = train.loc[train["symbol"] == sym, feat].replace([np.inf, -np.inf], np.nan).dropna()
            series = series.reset_index(drop=True)
            if len(series) < ADF_MIN_OBS or series.std() == 0.0:
                continue
            try:
                p = float(adfuller(series, autolag="AIC", result_object=True).pvalue)
                if not np.isnan(p):
                    ps.append(p)
            except Exception:
                continue
        median_p = float(np.median(ps)) if ps else np.nan
        results[feat] = {
            "adf_p_median": median_p,
            "flagged": bool(not np.isnan(median_p) and median_p > ADF_P_THRESHOLD),
            "n_tickers_tested": len(ps),
        }
    return results


# --------------------------------------------------------------------------- #
# Mutual information
# --------------------------------------------------------------------------- #
def compute_mi(train: pd.DataFrame, feature_cols: list[str]) -> dict:
    sub = train[feature_cols + TARGET_COLUMNS].replace([np.inf, -np.inf], np.nan).dropna()
    X = sub[feature_cols].astype("float64").to_numpy()
    mi = {}
    for t in TARGET_COLUMNS:
        y = sub[t].astype("int").to_numpy()
        vals = mutual_info_classif(X, y, random_state=42)
        mi[t] = {f: float(v) for f, v in zip(feature_cols, vals)}
    return mi


# --------------------------------------------------------------------------- #
# VIF pruning (retaining higher-MI member of each collinear pair)
# --------------------------------------------------------------------------- #
def compute_vif_pruning(train: pd.DataFrame, feature_cols: list[str], mean_mi: dict) -> tuple[list[str], list[dict]]:
    remaining = list(feature_cols)
    dropped: list[dict] = []

    # Drop constant (zero-variance) features first — no signal, undefined VIF.
    for f in list(remaining):
        s = train[f].replace([np.inf, -np.inf], np.nan).dropna()
        if s.std() == 0.0:
            dropped.append({"feature": f, "reason": "CONSTANT"})
            remaining.remove(f)

    guard = 0
    while len(remaining) > 1 and guard < len(feature_cols) + 5:
        guard += 1
        sub = train[remaining].replace([np.inf, -np.inf], np.nan).dropna().astype("float64")
        corr = sub.corr().to_numpy()
        if corr.shape[0] < 2:
            break
        try:
            inv = np.linalg.inv(corr)
        except np.linalg.LinAlgError:
            inv = np.linalg.pinv(corr)
        vif = np.diag(inv).astype("float64")
        over = [i for i in range(len(remaining)) if np.isfinite(vif[i]) and vif[i] > VIF_THRESHOLD]
        if not over:
            break
        # Among over-threshold features, drop the lowest mean-MI (retain higher MI).
        worst = min(over, key=lambda i: mean_mi.get(remaining[i], 0.0))
        dropped.append({"feature": remaining[worst], "reason": "VIF", "vif": float(vif[worst])})
        remaining.pop(worst)

    return remaining, dropped


# --------------------------------------------------------------------------- #
# Cross-sectional ranks + stationarity transform
# --------------------------------------------------------------------------- #
def add_cs_percentile(df: pd.DataFrame, feature_cols: list[str]) -> pd.DataFrame:
    out = df.copy()
    for feat in feature_cols:
        out[f"{feat}_cs_pct"] = out.groupby("date")[feat].rank(pct=True).astype("float32")
    return out


def apply_stationarity_transform(df: pd.DataFrame, flagged: list[str]) -> pd.DataFrame:
    out = df.copy()
    for feat in flagged:
        out[feat] = df.groupby("symbol")[feat].transform(
            lambda s: (s - s.rolling(ROLLING_Z_WINDOW, min_periods=20).mean())
            / (s.rolling(ROLLING_Z_WINDOW, min_periods=20).std(ddof=1) + 1e-12)
        )
    return out


# --------------------------------------------------------------------------- #
# Report + catalog
# --------------------------------------------------------------------------- #
def whitelist_per_target(surviving: list[str], mi: dict, min_pct: float) -> dict:
    wl = {}
    for t in TARGET_COLUMNS:
        vals = {f: mi[t].get(f, 0.0) for f in surviving}
        if not vals:
            wl[t] = []
            continue
        threshold = float(np.percentile(list(vals.values()), min_pct))
        wl[t] = [f for f in surviving if vals[f] >= threshold]
    return wl


def run_market(market: str, vif_threshold: float, min_mi_percentile: float) -> dict:
    df = load_dataset(market)
    train, cutoff = train_split(df)
    feature_cols = [c for c in df.columns if c not in TARGET_COLUMNS + ["date", "symbol", "market"]]

    adf = adf_analysis(train, feature_cols)
    mi = compute_mi(train, feature_cols)
    mean_mi = {f: float(np.mean([mi[t][f] for t in TARGET_COLUMNS])) for f in feature_cols}
    surviving, dropped = compute_vif_pruning(train, feature_cols, mean_mi)
    flagged = [f for f in feature_cols if adf[f]["flagged"]]
    wl = whitelist_per_target(surviving, mi, min_mi_percentile)

    # Build the metadata-transformed matrix (surviving features + cs_pct + targets).
    transformed = apply_stationarity_transform(df, [f for f in surviving if f in flagged])
    transformed = add_cs_percentile(transformed, surviving)
    keep_cols = (
        ["date", "symbol", "market"]
        + surviving
        + [f"{f}_cs_pct" for f in surviving]
        + TARGET_COLUMNS
    )
    out_path = FEATURES_DIR / f"features_{market}_metadata.parquet"
    transformed[keep_cols].to_parquet(out_path, index=False)

    catalog = {
        "market": market,
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "train_cutoff_date": str(cutoff.date()),
        "n_features_raw": len(feature_cols),
        "n_features_surviving": len(surviving),
        "vif_threshold": vif_threshold,
        "min_mi_percentile": min_mi_percentile,
        "stationarity": adf,
        "dropped_features": dropped,
        "surviving_features": surviving,
        "mi_rankings": mi,
        "whitelist_per_target": wl,
    }
    CATALOG_PATH.with_name(CATALOG_PATH.name.format(market=market)).write_text(
        json.dumps(catalog, indent=2)
    )

    return {
        "catalog": catalog,
        "top_mi": {t: sorted(mi[t].items(), key=lambda kv: kv[1], reverse=True)[:10] for t in TARGET_COLUMNS},
        "out_path": out_path,
    }


def write_report(results: dict) -> None:
    lines = [
        "# Sprint 3 — Statistical Metadata Selection (Gate 3)",
        "",
        f"- Generated (UTC): {dt.datetime.now(dt.timezone.utc).isoformat()}",
        "",
    ]
    for market, r in results.items():
        c = r["catalog"]
        lines += [
            f"## {market}",
            "",
            f"- Raw features: **{c['n_features_raw']}** | Surviving after VIF pruning: **{c['n_features_surviving']}**",
            f"- Train cutoff (feature selection split): `{c['train_cutoff_date']}`",
            "",
            "### Stationarity (ADF) — features flagged for rolling Z-score",
            "",
        ]
        flagged = [f for f, v in c["stationarity"].items() if v["flagged"]]
        lines.append(f"- **{len(flagged)}** non-stationary features flagged (median p > 0.05):")
        lines.append("")
        lines.append(", ".join(f"`{f}`" for f in flagged) if flagged else "(none)")
        lines += ["", "### Collinearity pruning (VIF) — dropped features", ""]
        if c["dropped_features"]:
            lines.append("| Feature | Reason | VIF |")
            lines.append("| :--- | :--- | ---: |")
            for d in c["dropped_features"]:
                lines.append(f"| `{d['feature']}` | {d['reason']} | {d.get('vif', '-')} |")
        else:
            lines.append("(none dropped)")
        lines += ["", "### Top features by Mutual Information (per target)", ""]
        for t in TARGET_COLUMNS:
            lines.append(f"**{t}**")
            lines.append("")
            for feat, val in r["top_mi"][t]:
                lines.append(f"- `{feat}` — MI {val:.4f}")
            lines.append("")
        lines += ["", "### Surviving whitelist (per target)", ""]
        for t in TARGET_COLUMNS:
            wl = c["whitelist_per_target"][t]
            lines.append(f"- **{t}** ({len(wl)} features): " + (", ".join(f"`{f}`" for f in wl) if wl else "(none)"))
            lines.append("")
        lines.append(f"- Transformed feature matrix saved to `data/features/features_{market}_metadata.parquet`")
        lines.append("")
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines) + "\n")


def main() -> int:
    init_dirs()
    parser = argparse.ArgumentParser()
    parser.add_argument("--market", choices=["USD", "CAD", "ALL"], default="ALL")
    parser.add_argument("--vif-threshold", type=float, default=VIF_THRESHOLD)
    parser.add_argument("--min-mi-percentile", type=float, default=MIN_MI_PERCENTILE)
    args = parser.parse_args()

    markets = ["USD", "CAD"] if args.market == "ALL" else [args.market]
    results = {}
    for mkt in markets:
        r = run_market(mkt, args.vif_threshold, args.min_mi_percentile)
        results[mkt] = r
        print(
            f"[stat_metadata] {mkt}: {r['catalog']['n_features_raw']} raw -> "
            f"{r['catalog']['n_features_surviving']} surviving features"
        )

    write_report(results)
    update_state("EP-03", "gate_3", {
        "markets": {m: results[m]["catalog"]["n_features_surviving"] for m in results},
    })
    print(f"[stat_metadata] summary -> {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
