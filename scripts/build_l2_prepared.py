#!/usr/bin/env python
"""PM-owned prep: CALIB-only prepared L2 panels `data/models/l2_prepared/<MKT>.parquet`.

Row universe = fib `screen_bottom` swing events: trade-label keys (market, symbol, date) with
screen_bottom==True, joined to the WI-048 feature panel on (symbol, date). Columns:

    date, symbol, fold (int; -1 = not out-of-fold), r (gross trade return, float32),
    xsec_vol_rank_cont, move_occur, move_dir_up, p_b_hold   (float32; NaN = coverage gap)

Scores are OUT-OF-FOLD predictions of the WI-048 winning-cell fold pickles. Validation blocks are
reproduced with the grid's own `PurgedWalkForwardSplit(n_splits=5, embargo_td=max(20,h))` on the
finite-label rows of each cell. Nothing is fitted here. Only rows with date < CALIB_END are written.

    uv run python scripts/build_l2_prepared.py

Invariants: n_jobs=2 (predict only), float32 immediately, no row >= CALIB_END is written.
"""
from __future__ import annotations

import datetime as dt
import os
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

from src.l2_overlay import harness as H  # noqa: E402
from src.swing_bsh import binary_features_ext as ext  # noqa: E402
from src.swing_bsh import grid_targets_ext as gt  # noqa: E402
from src.swing_bsh import targets_ext as tg  # noqa: E402
from src.swing_bsh import train  # noqa: E402
from src.xgb_trainer import PurgedWalkForwardSplit  # noqa: E402

MARKETS = ("USD", "CAD")
WI048_MANIFEST = BASE / "data" / "models" / "wi048" / "manifest.parquet"
WI035_DIR = BASE / "data" / "models" / "wi035"
TRADE_LABELS = BASE / "reports" / "fib_swings" / "trade_labels_w39.parquet"
OUT_DIR = BASE / "data" / "models" / "l2_prepared"
REPORT = BASE / "reports" / "l2_prepared" / "prep_report.md"
CACHE_FALLBACK = Path(os.path.expanduser("~/.hermes/cache/scratch/l2_prep_cache"))
# Admin ruling 2026-11-15: r = ASPIRATIONAL trade label (10% target / 5% stop, 39d, close exit) —
# replaces the frozen fib t15_s10_d39_close convention for the L2 panel (PM_LOG cycle 40 blocker).
POLICY = "t10_s5_d39_close"
COST_ADD = 0.0025  # trade labels store net of 25 bps round trip; store GROSS
N_SPLITS = 5
N_FEATURES_EXPECTED = 47
# Board-ruled winning cells: column -> (learner, horizon, metric used to confirm the ruling)
WINNERS = {
    "xsec_vol_rank_cont": ("xgboost", 55, "ic"),
    "move_occur": ("xgboost", 5, "auc"),
    "move_dir_up": ("xgboost", 5, "auc"),
}
SCORE_COLS = ("xsec_vol_rank_cont", "move_occur", "move_dir_up", "p_b_hold")


def _b_hold_paths(market: str) -> list[Path]:
    return [WI035_DIR / f"{market}_hist_gbm_b_hold_f{k}.pkl" for k in range(N_SPLITS)]

GAPS: list[str] = []
NOTES: list[str] = []
STATS: dict[str, dict] = {}


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _rel(p: Path) -> str:
    return str(Path(p).relative_to(BASE))


def winner_pickles(market: str, manifest: pd.DataFrame) -> dict[str, dict[int, Path]]:
    """Select winner rows from the manifest (never assume the variant); assert 5 folds each."""
    expected_variant = ext.variant_name(tg.PINNED_EVENT[market], "full", 0.8)
    out: dict[str, dict[int, Path]] = {}
    for fam, (learner, h, metric) in WINNERS.items():
        # the ruled (learner, h) must be the metric winner for this market's pinned variant
        mv = manifest[(manifest["market"] == market) & (manifest["binary"] == fam)
                      & (manifest["variant"] == expected_variant)]
        assert not mv.empty, f"no manifest rows for {market} {fam} {expected_variant}"
        best = mv[mv["learner"] == learner].groupby("h")[metric].mean()
        assert int(best.idxmax()) == h, f"{market} {fam}: ruled h{h} is not the {metric} max"
        other = mv[(mv["learner"] != learner) & (mv["h"] == h)][metric].mean()
        assert best.loc[h] > other, f"{market} {fam} h{h}: {learner} is not the {metric} winner"
        sel = mv[(mv["learner"] == learner) & (mv["h"] == h)]
        assert set(sel["variant"]) == {expected_variant}, f"variant mismatch for {market} {fam}"
        assert sorted(sel["fold"].tolist()) == list(range(N_SPLITS)), f"{market} {fam} h{h}: folds"
        paths = {}
        for _, r in sel.iterrows():
            p = BASE / r["pickle_path"]
            assert p.exists(), f"missing pickle {p}"
            paths[int(r["fold"])] = p
        out[fam] = paths
    return out


def load_panel_labels(market: str):
    """WI-048 cache first; rebuild (cache to a scratch dir) when it lacks the needed label keys."""
    needed = {tg.label_key(fam, tg.PINNED_EVENT[market], h)
              for fam, (_, h, _m) in WINNERS.items()}
    panel, labels = gt.load_panel(market, cache_dir=gt.DEFAULT_CACHE_DIR)
    src = "wi048 cache (/tmp/wi048)"
    if not needed.issubset(labels.keys()):
        missing = sorted(needed - set(labels.keys()))
        NOTES.append(f"{market}: wi048 cache lacks label keys {missing}; rebuilt panel+labels "
                     f"from source with the current targets_ext (cache -> {CACHE_FALLBACK}).")
        panel, labels = gt.load_panel(market, cache_dir=CACHE_FALLBACK)
        src = f"rebuilt via targets_ext.build_targets_panel (cache {CACHE_FALLBACK})"
    assert needed.issubset(labels.keys()), f"{market}: still missing label keys after rebuild"
    panel = panel.reset_index(drop=True)
    panel["date"] = pd.to_datetime(panel["date"])
    return panel, labels, src


def fold_positions(dates: np.ndarray, y_raw: np.ndarray, h: int) -> np.ndarray:
    """Panel-position fold id per row, reproducing `binary_grid.cell_cv` exactly."""
    finite = np.isfinite(y_raw)
    pos = np.where(finite)[0]
    dh = dates[finite]
    splitter = PurgedWalkForwardSplit(n_splits=N_SPLITS, embargo_td=train.embargo_for([h]))
    fold = np.full(len(dates), -1, dtype=np.int64)
    for k, (_tr, va) in enumerate(splitter.split(dh)):
        fold[pos[va]] = k
    return fold


def score_cell(X: np.ndarray, fold: np.ndarray, pickles: dict[int, Path], regression: bool,
               cell: str) -> np.ndarray:
    out = np.full(len(fold), np.nan, dtype=np.float32)
    for k, path in sorted(pickles.items()):
        with open(path, "rb") as fh:
            model = pickle.load(fh)["model"]
        idx = np.where(fold == k)[0]
        if idx.size == 0:
            continue
        n_in = getattr(getattr(model, "model", model), "n_features_in_", None)
        assert n_in in (None, X.shape[1]), f"{cell} f{k}: model expects {n_in}, X has {X.shape[1]}"
        if regression:
            pred = np.asarray(model.predict(X[idx]), dtype="float64")
        else:
            pred = np.asarray(model.predict_proba(X[idx]), dtype="float64")
            assert pred.ndim == 1, f"{cell} f{k}: predict_proba not 1-d"
        out[idx] = pred.astype("float32")
    folds_with_rows = {int(k) for k in np.unique(fold) if k >= 0}
    missing = folds_with_rows - set(pickles)
    assert not missing, f"{cell}: fold rows without pickle {sorted(missing)}"
    return out


def legacy_b_hold(panel: pd.DataFrame, market: str) -> np.ndarray:
    """p_b_hold from the WI-035 hist_gbm b_hold models; NaN unless all 23 features are produced."""
    n = len(panel)
    nan = np.full(n, np.nan, dtype=np.float32)
    feats35 = None
    for path in _b_hold_paths(market):
        with open(path, "rb") as fh:
            prov = pickle.load(fh)["provenance"]
        f = list(prov["features"])
        assert feats35 is None or f == feats35, "wi035 fold feature lists differ"
        feats35 = f
    NOTES.append(f"{market}: wi035 b_hold feature list has {len(feats35)} names (provenance; "
                 f"USD=23, CAD=24 per the on-disk pickles).")
    p2 = train.engineer(panel)
    produced = [c for c in feats35 if c in p2.columns]
    missing = [c for c in feats35 if c not in p2.columns]
    if missing:
        GAPS.append(f"{market}: p_b_hold ALL-NaN - {len(missing)}/23 wi035 features not produced by "
                    f"the current pipeline (train.engineer + panel): {missing}. The grid's "
                    f"_design() sets k=1/horizon=21 as constants; substituting them would be a "
                    f"guessed score, so none was used. Fold definition for wi035 is also not "
                    f"reconstructed (no fold boundaries on disk).")
        return nan
    raise NotImplementedError(f"all 23 wi035 features present for {market}: fold reconstruction "
                              f"for wi035 is not wired; refusing to score silently")


def trade_tables(market: str):
    tl = pd.read_parquet(TRADE_LABELS, columns=["symbol", "market", "date", "screen_bottom",
                                                 "policy", "ret", "reason"])
    tl = tl[tl["market"].astype(str) == market].copy()
    tl["date"] = pd.to_datetime(tl["date"])
    tl["screen_bottom"] = tl["screen_bottom"].astype(bool)
    sb = tl[tl["screen_bottom"]]
    sb_keys = sb[["symbol", "date"]].drop_duplicates()
    pol = sb[sb["policy"].astype(str) == POLICY]
    assert not pol.duplicated(["symbol", "date"]).any(), "duplicate policy rows per event"
    pol = pol[["symbol", "date", "ret", "reason"]].copy()
    return sb_keys, pol


def fib_sim_gross(o, h, l, c, i):
    """t10_s5_d39_close first-touch sim (scripts/fib_trade_labels.py `simulate`, entry_mode='close';
    admin ruling 2026-11-15: aspirational 10% target / 5% stop),
    GROSS: the stored trade-label ret subtracts COST=0.0025, this does not."""
    entry = c[i]
    T, S = entry * 1.10, entry * 0.95
    if i + 39 >= len(c):
        return np.nan
    for j in range(i + 1, i + 40):
        if o[j] <= S:
            return o[j] / entry - 1.0
        if o[j] >= T:
            return o[j] / entry - 1.0
        if l[j] <= S and h[j] >= T:
            return S / entry - 1.0
        if l[j] <= S:
            return S / entry - 1.0
        if h[j] >= T:
            return T / entry - 1.0
    return c[i + 39] / entry - 1.0


def fib_r_for_panel(panel: pd.DataFrame, market: str) -> np.ndarray:
    """Gross t15_s10_d39_close return for every panel row via the OHLC panels."""
    root = BASE / "data" / "raw_ohlcv" / f"market={market}"
    files = sorted(root.rglob("*.parquet"))
    assert files, f"no OHLC files under {root}"
    r = np.full(len(panel), np.nan, dtype=np.float64)
    pos_of = {}
    for pos, (sym, dt) in enumerate(zip(panel["symbol"].astype(str).to_numpy(),
                                         pd.to_datetime(panel["date"]))):
        pos_of.setdefault(sym, []).append((pos, dt))
    n_bars = n_miss = 0
    for f in files:
        sym = (f.stem.replace("symbol=", "") if f.name.startswith("symbol=")
               else f.parent.name.replace("symbol=", ""))
        rows = pos_of.get(sym)
        if not rows:
            continue
        g = pd.read_parquet(f, columns=["date", "open", "high", "low", "close"])
        g["date"] = pd.to_datetime(g["date"])
        dmap = {d: i for i, d in enumerate(g["date"])}
        o = g["open"].to_numpy("float64"); h_ = g["high"].to_numpy("float64")
        l_ = g["low"].to_numpy("float64"); c = g["close"].to_numpy("float64")
        n_bars += len(g)
        for pos, dt in rows:
            i = dmap.get(dt)
            if i is None:
                n_miss += 1
                continue
            r[pos] = fib_sim_gross(o, h_, l_, c, i)
    NOTES.append(f"{market}: fib sim over {len(files)} OHLC symbols ({n_bars:,} bars); "
                 f"{n_miss} event dates not found in OHLC -> r NaN.")
    return r.astype(np.float32)


def build_market(market: str, manifest: pd.DataFrame) -> pd.DataFrame:
    panel, labels, src = load_panel_labels(market)
    STATS[market] = {"panel_source": src, "panel_rows": int(len(panel)),
                     "panel_dupe_symbol_date": int(panel.duplicated(["symbol", "date"]).sum()),
                     "panel_dupe_symbol_date_bottom": int(panel[panel["state"] == "at_bottom"].duplicated(["symbol", "date"]).sum())}
    X, feats, kept, dropped = gt._design(panel)
    X = np.asarray(X, dtype=np.float32)
    STATS[market].update({"n_features": int(X.shape[1]), "n_pruned_kept": len(kept)})
    assert X.shape[1] == N_FEATURES_EXPECTED, f"{market}: {X.shape[1]} features (expected 47)"
    dates = panel["date"].to_numpy()
    event = tg.PINNED_EVENT[market]

    pickles = winner_pickles(market, manifest)
    scores: dict[str, np.ndarray] = {}
    fold_xsec: np.ndarray | None = None
    for fam, (learner, h, _m) in WINNERS.items():
        y_raw = np.asarray(labels[tg.label_key(fam, event, h)])
        cont = fam == "xsec_vol_rank_cont"
        fold = fold_positions(dates, y_raw, h)
        sc = score_cell(X, fold, pickles[fam], regression=cont, cell=f"{market}/{fam}/h{h}")
        scores[fam] = sc
        STATS[market][f"cell_{fam}"] = {"learner": learner, "h": h, "n_scored": int(np.isfinite(sc).sum()),
                                        "n_fold_rows": int((fold >= 0).sum()),
                                        "n_finite_label": int(np.isfinite(y_raw).sum())}
        if cont:
            fold_xsec = fold
    assert fold_xsec is not None
    scores["p_b_hold"] = legacy_b_hold(panel, market)

    # row universe (admin amendment 2026-11-15, PM_LOG cycle 41): ALL swing events (both
    # states) on per-date quorum dates (>= MIN_NAMES_PER_DATE candidates). The at_bottom-only
    # universe cannot fill a >=20-name cross-section (median 10 USD / 7 CAD names per date);
    # the quorum filter replaces the harness precheck's global kill switch for this panel.
    sb_keys, pol = trade_tables(market)
    pos = pd.DataFrame({"symbol": panel["symbol"].astype(str).to_numpy(), "date": panel["date"],
                        "state": panel["state"].astype(str).to_numpy(), "pos": np.arange(len(panel))})
    bottom = pos[pos["state"] == "at_bottom"]
    assert not bottom.duplicated(["symbol", "date"]).any(), "duplicate universe event keys"
    n_sb = len(sb_keys)
    um = sb_keys.assign(symbol=sb_keys["symbol"].astype(str)).merge(
        bottom[["symbol", "date"]].drop_duplicates(), on=["symbol", "date"], how="left", indicator=True)
    um = um[um["_merge"] == "left_only"]
    unmatched, matched = int(len(um)), n_sb - int(len(um))
    top_only = um.merge(pos[pos["state"] == "at_top"][["symbol", "date"]].drop_duplicates(),
                        on=["symbol", "date"], how="inner")
    n_top_only = int(len(top_only))
    uni_all = pos[pd.to_datetime(pos["date"]) < pd.Timestamp(H.CALIB_END)].copy()
    n_all = int(len(uni_all))
    dup = int(uni_all.duplicated(["symbol", "date"]).sum())
    if dup:
        NOTES.append(f"{market}: {dup} (symbol, date) rows carry both states; first kept, rest dropped.")
        uni_all = uni_all.drop_duplicates(["symbol", "date"], keep="first")
    qcnt = uni_all.groupby(uni_all["date"].astype("object"))["symbol"].transform("size")
    uni = uni_all[qcnt >= H.MIN_NAMES_PER_DATE].copy()
    n_quorum_dates = int(uni["date"].nunique())
    n_thin_dropped = int(uni_all["date"].nunique()) - n_quorum_dates
    assert not uni.duplicated(["symbol", "date"]).any(), "duplicate universe event keys after dedupe"
    NOTES.append(f"{market}: universe amendment — all swing events on quorum dates "
                 f"(>={H.MIN_NAMES_PER_DATE} candidates): {len(uni):,}/{n_all:,} CALIB rows kept, "
                 f"{n_thin_dropped} thin dates dropped, {n_quorum_dates} quorum dates.")
    r_all = fib_r_for_panel(panel, market)
    uni["r"] = r_all[uni["pos"].to_numpy()]
    # cross-validation: sim replication vs the precomputed fib trade-label rets
    chk = uni.merge(pol.assign(symbol=pol["symbol"].astype(str)), on=["symbol", "date"], how="inner")
    chk = chk[chk["ret"].notna() & chk["r"].notna()]
    if len(chk):
        diff = (chk["r"].astype("float64") - (chk["ret"].astype("float64") + COST_ADD)).abs()
        STATS[market]["sim_vs_trade_labels_n"] = int(len(chk))
        STATS[market]["sim_vs_trade_labels_max_abs_diff"] = float(diff.max())
        assert diff.quantile(0.99) < 1e-6, f"sim replication mismatch: q99 {diff.quantile(0.99):.2e}"
    no_policy = int(pd.isna(uni["r"]).sum())
    p = uni["pos"].to_numpy()
    out = pd.DataFrame({
        "date": panel["date"].to_numpy()[p],
        "symbol": panel["symbol"].astype(str).to_numpy()[p],
        "fold": fold_xsec[p].astype("int64"),
        "r": uni["r"].to_numpy(dtype="float32"),
    })
    for col in SCORE_COLS:
        out[col] = scores[col][p].astype("float32")
    cal = pd.to_datetime(out["date"]) < pd.Timestamp(H.CALIB_END)
    n_post = int((~cal).sum())
    out = out.loc[cal].reset_index(drop=True)
    assert (pd.to_datetime(out["date"]) < pd.Timestamp(H.CALIB_END)).all()
    assert not out.duplicated(["date", "symbol"]).any()
    out = out.astype({"r": "float32", **{c: "float32" for c in SCORE_COLS}, "fold": "int64"})
    STATS[market].update({
        "screen_bottom_event_keys": int(n_sb), "universe_matched_to_panel": int(matched),
        "trade_keys_without_panel_row": int(unmatched), "trade_keys_only_at_top_row": n_top_only,
        "universe_no_policy_row": no_policy,
        "rows_out_calib": int(len(out)), "rows_dropped_ge_calib_end": n_post,
        "fold_counts": {int(k): int(v) for k, v in out["fold"].value_counts().sort_index().items()},
        "finite_label_rows_without_fold_xsec_h55": int(((fold_xsec < 0) & np.isfinite(
            np.asarray(labels[tg.label_key("xsec_vol_rank_cont", event, 55)], dtype="float64"))).sum()),
    })
    um_pre = um["date"] < panel["date"].min()
    pre = int(um_pre.sum())
    STATS[market]["unmatched_before_panel_start"] = pre
    STATS[market]["panel_min_date"] = str(panel["date"].min().date())
    if unmatched:
        GAPS.append(f"{market}: {unmatched}/{n_sb} screen_bottom trade-label event keys have no "
                    f"at_bottom panel row: {pre} predate the panel start "
                    f"({panel['date'].min().date()}); {unmatched - pre} are in-range non-panel events "
                    f"({n_top_only} of all unmatched exist only as at_top rows). Not fabricated.")
    if n_post:
        NOTES.append(f"{market}: {n_post} universe rows dated >= CALIB_END were excluded from output.")
    gap_fold = STATS[market]["finite_label_rows_without_fold_xsec_h55"]
    NOTES.append(f"{market}: xsec_vol_rank_cont is a raw regressor output (not bounded to [0,1]); "
                 "r is NOT clipped (outliers kept as recorded, e.g. CAD max r ~7.0).")
    NOTES.append(f"{market}: `fold` column = xsec_vol_rank_cont h55 fold assignment; move_occur / "
                 f"move_dir_up / xsec scores each come from their own cell's fold assignment (h5 vs h55 "
                 f"validation blocks can differ slightly), so a row's score may be from a different fold "
                 f"number than its `fold`.")
    NOTES.append(f"{market}: {gap_fold} finite-label panel rows carry fold=-1 for xsec h55 (outside "
                 f"all purged validation blocks, e.g. the first 40% of dates is train-only) - "
                 f"NaN by design, not backfilled.")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / f"{market}.parquet"
    out.to_parquet(path, index=False)
    STATS[market]["output"] = _rel(path)
    STATS[market]["output_bytes"] = path.stat().st_size
    return out


def write_report(frames: dict[str, pd.DataFrame]) -> None:
    lines = [f"# L2 prepared CALIB panels (WI-prep) — generated {_now()}", "",
             "Script: `scripts/build_l2_prepared.py`. CALIB only: rows with date < "
             f"{H.CALIB_END} (EVAL {H.EVAL_START} never written).", "",
             "## Sources", "",
             "| source | size (bytes) |", "| :--- | ---: |"]
    for p in (WI048_MANIFEST, TRADE_LABELS):
        lines.append(f"| `{_rel(p)}` | {p.stat().st_size:,} |")
    win_paths = [p for m in MARKETS for fam in WINNERS for p in
                 winner_pickles(m, pd.read_parquet(WI048_MANIFEST))[fam].values()]
    lines.append(f"| winner fold pickles (wi048, 3 cells x 2 markets x 5 folds) | "
                 f"{sum(p.stat().st_size for p in win_paths):,} ({len(win_paths)} files) |")
    b_paths = [p for m in MARKETS for p in _b_hold_paths(m)]
    lines.append(f"| wi035 b_hold pickles (10; read for feature list only) | "
                 f"{sum(p.stat().st_size for p in b_paths):,} |")
    lines += ["", "## Winner cells (manifest-selected)", "",
              "- " + "; ".join(f"`{f}` -> {ln} h{h} (confirmed by {m})"
                               for f, (ln, h, m) in WINNERS.items()),
              f"- Variant per market from manifest: USD `{ext.variant_name('exact', 'full', 0.8)}`, "
              f"CAD `{ext.variant_name('tol2', 'full', 0.8)}`; 5 fold pickles per cell asserted."]
    for m in MARKETS:
        if m not in STATS:
            continue
        s = STATS[m]
        lines += ["", f"## {m}", "",
                  f"- Panel source: {s['panel_source']}; panel rows {s['panel_rows']:,}; "
                  f"features {s['n_features']} (rho-pruned kept {s['n_pruned_kept']}).",
                  f"- screen_bottom trade-label keys {s['screen_bottom_event_keys']:,}; matched to panel "
                  f"{s['universe_matched_to_panel']:,}; unmatched {s['trade_keys_without_panel_row']:,}; "
                  f"universe rows without policy row {s['universe_no_policy_row']:,}.",
                  f"- Output rows (date < CALIB_END): {s['rows_out_calib']:,}; fold counts {s['fold_counts']}.",
                  f"- Cells: " + "; ".join(f"{f}: scored {s['cell_' + f]['n_scored']:,}/"
                                          f"{s['cell_' + f]['n_finite_label']:,} finite-label"
                                          for f in WINNERS) + "."]
        df = frames[m]
        lines += ["", "| column | non-NaN | dtype |", "| :--- | ---: | :--- |"]
        for c in df.columns:
            lines.append(f"| {c} | {int(df[c].notna().sum()):,} | {df[c].dtype} |")
        rs = df["r"].dropna().astype("float64")
        if len(rs):
            q = rs.quantile([0.05, 0.25, 0.5, 0.75, 0.95])
            lines += ["", f"r (gross): n={len(rs):,} mean {rs.mean():+.4f} std {rs.std():.4f} "
                          f"q05 {q.iloc[0]:+.4f} q25 {q.iloc[1]:+.4f} q50 {q.iloc[2]:+.4f} "
                          f"q75 {q.iloc[3]:+.4f} q95 {q.iloc[4]:+.4f}"]
    lines += ["", "## Coverage gaps", ""] + [f"- {g}" for g in GAPS] if GAPS else ["", "## Coverage gaps", "", "- none"]
    lines += ["", "## Notes", ""] + [f"- {n}" for n in NOTES]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n")


def main() -> None:
    manifest = pd.read_parquet(WI048_MANIFEST)
    frames = {}
    for m in MARKETS:
        frames[m] = build_market(m, manifest)
    write_report(frames)
    for m in MARKETS:
        s = STATS[m]
        print(f"{m}: rows={s['rows_out_calib']} folds={s['fold_counts']} -> {s['output']}")
    print(f"report: {_rel(REPORT)}; gaps: {len(GAPS)}")


if __name__ == "__main__":
    main()
