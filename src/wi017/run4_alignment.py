#!/usr/bin/env python
"""WI-017 run 4: target x feature alignment matrix (USD, full fib grid 3-233).

Method (reuses the WI-015 alignment machinery by import — no re-derivation):
- Five chronological held-out folds, 20-session embargo
  (`src.perfanalytics.correlation.alignment.fold_val_positions`); held-out rows
  only are scored.
- Per-date cross-sectional Spearman rank IC (>=3 names/date, pairwise
  complete), mean over held-out dates — same estimator as WI-015.
- Baseline: the five E5 factors (`src.factors.e5_baseline.factor_frame`),
  scored the same way; the best |IC| E5 factor per target supplies the sign
  reference (same-sign skill bar, WI-009b cycle).
- Noise margin: 1000-draw circular block bootstrap, 20-date blocks, seed 42.
- Degenerate-target screen (admin rule: base rates first, edge cases last):
  binary touch/stay targets with pooled base rate <1% or >99% are SKIPPED, not
  scored (rates from run1_base_rates.json).

Targets: run-1 base stems (peak_ret, bottom_ret, touch_up10, touch_dn10, stay5)
and run-2 derived stems (first_touch, days_to_up, days_to_dn, rung, velocity)
x 17 windows. Features: the run-3 264-column grid (run3 COLUMN_ORDER).

Outputs: reports/wi017/run4_alignment.{csv,json,md}.
Memory: one fold frame at a time (float32, ~1 GB), scored in <=150-date blocks.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from src.factors.e5_baseline import E5_FACTORS, factor_frame
from src.perfanalytics.correlation.alignment import (
    block_bootstrap_margin,
    daily_spearman_ic,
    fold_val_positions,
)
from src.wi017 import WI017_WINDOWS
from src.wi017.run1_base_targets import quarantined_symbols
from src.wi017.run3_feature_grid import COLUMN_ORDER

BASE = Path(__file__).resolve().parents[2]
T_DIR = BASE / "reports/wi017/targets"
D_DIR = BASE / "reports/wi017/derived"
F_DIR = BASE / "reports/wi017/features"
E5_DIR = BASE / "reports/wi017/e5"
RAW_GLOB = "data/raw_ohlcv/market=USD/*.parquet"
OUT_DIR = BASE / "reports/wi017"

BASE_STEMS = ("peak_ret", "bottom_ret", "touch_up10", "touch_dn10", "stay5")
DERIVED_STEMS = ("first_touch", "days_to_up", "days_to_dn", "rung", "velocity")
# run1_base_rates.json key for each binary stem
RATE_KEY = {"touch_up10": "base_rate_up10", "touch_dn10": "base_rate_dn10",
            "stay5": "base_rate_stay5"}
DEGENERATE_LO, DEGENERATE_HI = 0.01, 0.99

E5_COLS = [f"e5_{f}" for f in E5_FACTORS]
DATE_BLOCK = 150  # dates per scoring block (memory bound)


def _ns(values) -> np.ndarray:
    return pd.to_datetime(values).to_numpy().astype("datetime64[ns]")


def build_e5_cache() -> int:
    """Compute the five E5 factors per symbol once, cache to reports/wi017/e5/."""
    import glob
    import os

    import pyarrow as pa
    import pyarrow.parquet as pq

    E5_DIR.mkdir(parents=True, exist_ok=True)
    quar = quarantined_symbols()
    n = 0
    for f in sorted(glob.glob(RAW_GLOB)):
        sym = os.path.basename(f).replace("symbol=", "").replace(".parquet", "")
        if sym in quar or not (F_DIR / f"{sym}.parquet").exists():
            continue
        out = E5_DIR / f"{sym}.parquet"
        if out.exists():
            n += 1
            continue
        df = pq.read_table(f).to_pandas()
        df = df[df["close"] > 0].sort_values("date").reset_index(drop=True)
        fac = factor_frame(df)
        fac.insert(0, "date", _ns(df["date"]))
        pq.write_table(
            pa.Table.from_pandas(fac, preserve_index=False),
            out,
        )
        n += 1
        if n % 100 == 0:
            print(f"  e5 cache: {n} symbols", flush=True)
    return n


def target_columns() -> tuple[list[str], list[dict]]:
    """Scored target columns + the degenerate-screen skips (with reasons)."""
    rates = json.loads((OUT_DIR / "run1_base_rates.json").read_text())["per_window"]
    cols: list[str] = []
    skipped: list[dict] = []
    for w in WI017_WINDOWS:
        a = rates[str(w)]
        for stem in BASE_STEMS:
            col = f"{stem}_{w}"
            key = RATE_KEY.get(stem)
            if key is not None:
                r = a[key]
                if r < DEGENERATE_LO or r > DEGENERATE_HI:
                    skipped.append({"column": col, "base_rate": r,
                                    "reason": "degenerate (<1% or >99%)"})
                    continue
            cols.append(col)
        for stem in DERIVED_STEMS:
            cols.append(f"{stem}_{w}")
    return cols, skipped


def _read(path: Path, cols: list[str]) -> pd.DataFrame:
    """Read `cols`; short-history symbols carry only feasible windows, so a
    fixed-column read KeyErrors — filter to the file's schema, then the
    caller pads what is missing with NaN."""
    import pyarrow.parquet as _pq
    avail = set(_pq.read_schema(path).names)
    use = [c for c in cols if c in avail]
    df = pd.read_parquet(path, columns=["date"] + use)
    df["date"] = _ns(df["date"])
    return df


def main() -> int:
    t0 = time.time()
    t_cols, skipped = target_columns()
    f_cols = list(COLUMN_ORDER)
    symbols = sorted(p.stem for p in F_DIR.glob("*.parquet"))
    import os
    smoke = os.environ.get("WI017_RUN4_SMOKE")
    if smoke:
        symbols = [s for s in symbols if s in smoke.split(",")]
    print(f"targets={len(t_cols)} skipped_degenerate={len(skipped)} "
          f"features={len(f_cols)} symbols={len(symbols)}", flush=True)

    n_e5 = build_e5_cache()
    print(f"e5 cache ready: {n_e5} symbols ({time.time() - t0:.0f}s)", flush=True)

    # all dates from the feature grid (same universe/rows as targets)
    sym_dates = {s: _ns(pd.read_parquet(F_DIR / f"{s}.parquet",
                                        columns=["date"])["date"]) for s in symbols}
    all_dates = np.unique(np.concatenate(list(sym_dates.values())))
    date_pos = {s: np.searchsorted(all_dates, d) for s, d in sym_dates.items()}
    folds = fold_val_positions(all_dates)
    print(f"dates={len(all_dates)} folds={len(folds)} "
          f"({time.time() - t0:.0f}s)", flush=True)

    series: dict[str, dict[str, list[np.ndarray]]] = {
        t: {f: [] for f in f_cols + E5_COLS} for t in t_cols
    }

    for k, val_pos in enumerate(folds):
        fold_dates = all_dates[val_pos]
        # per-symbol fold frames (held-out rows only, float32) — one fold in RAM
        parts: list[pd.DataFrame] = []
        for sym in symbols:
            dpos = date_pos[sym]
            in_fold = np.isin(dpos, val_pos)
            if not in_fold.any():
                continue
            tf = pd.read_parquet(F_DIR / f"{sym}.parquet")
            tf = tf.loc[in_fold]
            tf["date"] = _ns(tf["date"])
            td = _read(D_DIR / f"{sym}.parquet",
                       [c for c in t_cols if "_".join(c.split("_")[:-1]) in DERIVED_STEMS])
            tb = _read(T_DIR / f"{sym}.parquet",
                       [c for c in t_cols if "_".join(c.split("_")[:-1]) in BASE_STEMS])
            e5 = _read(E5_DIR / f"{sym}.parquet", E5_FACTORS)
            m = (tf.merge(tb, on="date", how="inner")
                    .merge(td, on="date", how="inner")
                    .merge(e5, on="date", how="inner"))
            m = m.rename(columns={f: f"e5_{f}" for f in E5_FACTORS})
            for c in t_cols:
                if c not in m:
                    m[c] = np.nan
            parts.append(m)
            del tf, td, tb, e5
        fold_df = pd.concat(parts, ignore_index=True)
        del parts
        print(f"fold {k + 1}/{len(folds)}: {len(fold_df):,} rows "
              f"({time.time() - t0:.0f}s)", flush=True)
        # score in <=DATE_BLOCK-date blocks (rank/IC memory bound)
        codes = pd.factorize(fold_df["date"].to_numpy(), sort=True)[0]
        uniq = pd.unique(fold_df["date"].to_numpy())
        uniq.sort()
        for b0 in range(0, len(uniq), DATE_BLOCK):
            block = set(pd.DatetimeIndex(uniq[b0: b0 + DATE_BLOCK]))
            mask = fold_df["date"].isin(block).to_numpy()
            sub = fold_df.loc[mask]
            ics = daily_spearman_ic(sub, t_cols, f_cols + E5_COLS)
            for t_col, mat in ics.items():
                for j, f_col in enumerate(f_cols + E5_COLS):
                    col = mat[:, j]
                    good = np.isfinite(col)
                    if good.any():
                        series[t_col][f_col].append(col[good])
            del sub, ics, mask
            print(f"  block {b0 // DATE_BLOCK + 1}: scored "
                  f"({time.time() - t0:.0f}s)", flush=True)
        del fold_df

    # ---- verdict table ----
    rows = []
    for t_col in t_cols:
        base_series = {f: np.concatenate(series[t_col][f])
                       for f in E5_COLS if series[t_col][f]}
        base_best = (max(base_series, key=lambda f: abs(base_series[f].mean()))
                     if base_series else None)
        base_ic = float(base_series[base_best].mean()) if base_best else float("nan")
        for f_col in f_cols:
            parts = series[t_col][f_col]
            ic = np.concatenate(parts) if parts else np.array([])
            observed = float(ic.mean()) if ic.size else float("nan")
            margin = block_bootstrap_margin(ic) if ic.size else float("nan")
            sign_match = bool(np.isfinite(observed) and np.isfinite(base_ic)
                              and np.sign(observed) == np.sign(base_ic))
            passed = bool(sign_match and np.isfinite(margin)
                          and abs(observed) > margin)
            rows.append({
                "target": t_col, "family": f_col.rsplit("_", 1)[0],
                "window": int(f_col.rsplit("_", 1)[-1]), "column": f_col,
                "held_out_ic": observed, "n_dates": int(ic.size),
                "noise_margin": margin, "baseline_factor": base_best,
                "baseline_ic": base_ic, "sign_match": sign_match, "pass": passed,
            })
    table = pd.DataFrame(rows)
    pfx = "run4_smoke" if smoke else "run4_alignment"
    table.to_csv(OUT_DIR / f"{pfx}.csv", index=False)

    meta = {
        "market": "USD",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "method": "WI-015 shape: 5 chronological folds, 20-session embargo, "
                  "per-date cross-sectional Spearman IC (>=3 names), mean over "
                  "held-out dates; 1000-draw circular block bootstrap "
                  "(20-date blocks, seed 42); same-sign vs best E5 factor.",
        "targets": t_cols, "n_targets": len(t_cols),
        "skipped_degenerate": skipped,
        "n_features": len(f_cols), "symbols": len(symbols),
        "elapsed_s": round(time.time() - t0, 1),
    }
    (OUT_DIR / (pfx + ".json")).write_text(json.dumps(meta, indent=2) + "\n")

    # markdown summary: best per target + verdicts vs standing assumptions
    n_pass = int(table["pass"].sum())
    best_rows = []
    for t_col, g in table.groupby("target", sort=True):
        g = g[np.isfinite(g["held_out_ic"])]
        if g.empty:
            continue
        if not np.isfinite(g["held_out_ic"].abs()).any():
            continue
        best = g.loc[g["held_out_ic"].abs().idxmax()]
        best_rows.append(best)
    best = pd.DataFrame(best_rows)
    md = ["# WI-017 run 4 — target x feature alignment matrix (USD, full grid)",
          "",
          f"Generated (UTC): {meta['generated_utc']} · targets: {len(t_cols)} "
          f"(+{len(skipped)} skipped degenerate) · features: {len(f_cols)} · "
          f"symbols: {len(symbols)}",
          "",
          "Method: " + meta["method"],
          "",
          f"**Passes: {n_pass} of {len(table)} candidate cells clear the "
          "same-sign + noise-margin bar.**",
          "",
          "## Best feature per target (top 30 by |IC|)",
          "",
          "| Target | Best feature | Held-out IC | Margin | Baseline | Pass |",
          "|---|---|---:|---:|---|---|",
          ]
    if best.empty:
        md.append("| (no finite IC — smoke/degenerate run) | | | | | |")
    for _, r in (best.assign(a=best["held_out_ic"].abs()).nlargest(30, "a").iterrows()
                 if not best.empty else []):
        md.append(f"| {r['target']} | {r['column']} | {r['held_out_ic']:+.4f} | "
                  f"{r['noise_margin']:.4f} | {r['baseline_factor']} | "
                  f"{'PASS' if r['pass'] else 'fail'} |")
    # standing-assumption checks
    sa = ["", "## Standing-assumption checks", ""]
    for fam, w in (("bb_width", 233), ("range_width", 233),
                   ("yangzhang", 144), ("atr_pct", 233)):
        col = f"{fam}_{w}"
        sub = table[table["column"] == col]
        if sub.empty:
            sa.append(f"- WI-015 positive `{col}`: not in grid (unexpected).")
            continue
        sfin = sub[np.isfinite(sub["held_out_ic"])]
        top = (sfin.loc[sfin["held_out_ic"].abs().idxmax()]
               if np.isfinite(sfin["held_out_ic"].abs()).any() else sub.iloc[0])
        n_pass_col = int(sub["pass"].sum())
        sa.append(f"- WI-015 positive `{col}`: best target "
                  f"`{top['target']}` IC {top['held_out_ic']:+.4f} "
                  f"(margin {top['noise_margin']:.4f}), clears bar on "
                  f"{n_pass_col}/{len(sub)} targets.")
    e5_beats = table.merge(
        table.groupby("target", as_index=False)["baseline_ic"].first().rename(
            columns={"target": "target", "baseline_ic": "b"}),
        on="target")
    e5_beats = e5_beats[np.isfinite(e5_beats["held_out_ic"]) &
                       np.isfinite(e5_beats["baseline_ic"])]
    n_beat = int((e5_beats["held_out_ic"].abs() >
                  e5_beats["baseline_ic"].abs()).sum())
    sa.append(f"- 'E5 factors are the signal' (WI-009 triple-confirmation): "
              f"fib-grid features beat the best E5 |IC| on {n_beat} of "
              f"{len(e5_beats)} scored target cells.")
    sa.append(f"- WI-016 USD NOT_CLEAR (barrier-resolved): this matrix is "
              f"descriptive; total PASS cells above quantify what clears "
              f"the WI-015-style bar on USD.")
    md += sa
    (OUT_DIR / (pfx + ".md")).write_text("\n".join(md) + "\n")

    print(f"DONE targets={len(t_cols)} features={len(f_cols)} pass={n_pass} "
          f"elapsed={time.time() - t0:.0f}s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
