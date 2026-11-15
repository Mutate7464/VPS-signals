"""WI-068 — fixed time exits (h13/h55) + hybrid vs event exits on **identical entries** (D-027 §5 (a), Layer 2).

Horizons are fixed ex ante and pre-registered (`HORIZONS`): no learned chooser exists here. Every arm
scores the same entry rows and folds against the frozen event exit on those rows, paying the 50 bps
single-leg round trip; the mandatory fold report and the CALIB stop flag are emitted on every run.

RE-ENTRY JUSTIFICATION (D-027 §7; the card is defective without it). The adjacent closed question is
WI-030 (learned exit chooser), closed REJECT on *selection on predictive stats judged on edge*. Two
things changed: (1) structural — no learned chooser at all, h13/h55 are pre-registered, so that failure
mode cannot recur and the only comparison is between pre-committed exit rules on one entry set; (2) new
input — the WI-059b regression read-outs and the post-WI-058 families (xsec_rank / mfe_mae / move_*)
carry exit-timing information that did not exist when WI-030 ran. The D-024 closure binds to the
original inputs and to the learned-chooser mechanism; only the fixed-horizon question is re-opened.

    uv run python -m src.l2_overlay.constructions.time_exit --smoke    # synthetic, *_smoke paths

Entry-set contract (one row per event — the SAME rows feed every arm): `symbol`, `date`, `fold`,
`r_event`, `t_event`, `r_h13`, `r_h55`. A WI-066/067 screener artifact may instead carry
`entry`/`selected` flags plus `r`/`r_frozen`; missing `r_h<h>` columns are attached from the causal
price cache (symbol-sequential, business-daily — a sparse panel fails closed rather than mis-dating the
horizon). Either the per-rule event
columns (`r_event_<rule>`, `t_event_<rule>`) or the aggregate pair are required: the event exit fires on
the first fired rule (min offset) and a named rule is never silently dropped. Invariants: n_jobs=2,
float32 immediately, symbol-sequential reads, no EVAL read (rows >= CALIB_END dropped before arithmetic).
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

from src.l2_overlay import costs
from src.l2_overlay import fold_report as foldrep
from src.l2_overlay import harness as H

BASE_DIR = Path(__file__).resolve().parents[3]        # named input/output roots (never CLI args)
MODELS_ROOT = BASE_DIR / "data" / "models"
ENTRIES_ROOT = MODELS_ROOT / "l2_xsec_rank"
BASELINE_DIR, PANEL_CACHE = Path("/tmp/wi035"), Path("/tmp/wi036")
REPORTS_ROOT = BASE_DIR / "reports" / "l2_time_exit"
REPORTS_SMOKE_ROOT = BASE_DIR / "reports" / "l2_time_exit_smoke"
MARKETS: tuple[str, ...] = ("USD", "CAD")
HORIZONS: tuple[int, ...] = (13, 55)                    # pre-registered, fixed ex ante (never tuned)
EVENT_RULES: tuple[str, ...] = ("fib_exit", "b_stop")   # frozen event exits, OR semantics
EVENT_HORIZON_FIB = 39                                  # WI-030 frozen exit horizon (t15_s10_d39_close)
SMOKE_MARKET, SMOKE_ENTRIES, SMOKE_SEED, PLACEBO_SEED, N_JOBS = "USD", 200, 68, 6800, 2
MAX_PANEL_GAP_DAYS = 5.0            # a causal cache must be business-daily, else `h` dates is not `h` dates
__all__ = ["BASE_DIR", "REPORTS_ROOT", "REPORTS_SMOKE_ROOT", "ENTRIES_ROOT", "MARKETS", "HORIZONS",
           "EVENT_RULES", "EVENT_HORIZON_FIB", "event_returns", "hybrid_exit", "horizon_returns",
           "simulate_fixed_horizon", "simulate_event_exit", "simulate_hybrid", "placebo_net_edge",
           "entries_key", "compare_arms", "horizon_returns_from_cache", "attach_horizons", "load_entries",
           "synthetic_fixture", "write_calib_report", "run_market", "main"]

def _fmt(x, spec: str = "{:+.2f}") -> str:
    return "n/a" if not np.isfinite(float(x)) else spec.format(float(x))

def entries_key(entries) -> str:
    """Stable digest of the entry rows; every arm must report the same key (identical-entry invariant)."""
    keys = sorted(f"{s}|{d}" for s, d in zip(entries["symbol"].astype(str),
                                             pd.to_datetime(pd.Series(entries["date"].to_numpy()))))
    return hashlib.sha1("\n".join(keys).encode()).hexdigest()[:16]

def event_returns(entries, event_rules=EVENT_RULES):
    """Event-exit `(r_event, t_event)`: the FIRST fired rule wins (min holding offset), none is dropped."""
    per_rule = [r for r in event_rules if f"t_event_{r}" in entries.columns and f"r_event_{r}" in entries.columns]
    if per_rule and len(per_rule) != len(tuple(event_rules)):
        raise KeyError(f"entries lack per-rule event columns for {sorted(set(event_rules) - set(per_rule))}")
    if not per_rule:
        for col in ("t_event", "r_event"):
            if col not in entries.columns:
                raise KeyError(f"entries need {col!r} (or per-rule columns for {tuple(event_rules)})")
        return (entries["r_event"].to_numpy("float32"), entries["t_event"].to_numpy("int64"))
    big = np.iinfo("int64").max
    t, r = np.full(len(entries), big, dtype="int64"), np.full(len(entries), np.nan, dtype="float64")
    for rule in per_rule:
        tt, rr = entries[f"t_event_{rule}"].to_numpy("int64"), entries[f"r_event_{rule}"].to_numpy("float64")
        take = np.isfinite(rr) & (tt >= 0) & (tt < t)
        t[take], r[take] = tt[take], rr[take]
    bad = ~np.isfinite(r) | (t == big)
    if bad.any():
        raise ValueError(f"{int(bad.sum())}/{len(entries)} entries have no finite event exit")
    return r.astype("float32"), t

def horizon_returns(entries, h) -> np.ndarray:
    """Forward return at the pre-registered horizon `h`; a missing `r_h<h>` column fails closed."""
    col = f"r_h{int(h)}"
    if col not in entries.columns:
        raise KeyError(f"entries lack the pre-registered horizon column {col!r}")
    return np.asarray(entries[col], dtype="float32")

def hybrid_exit(entries, h, event_rules=EVENT_RULES):
    """Whichever comes first: exit at `min(t_event, t_h)` and take the return of the arm that fired."""
    r_event, t_event = event_returns(entries, event_rules)
    first_event = t_event <= int(h)
    return (np.where(first_event, r_event, horizon_returns(entries, h)).astype("float32"),
            np.where(first_event, t_event, int(h)).astype("int64"))

def _score(entries, r_exit, t_held, *, arm, horizon, baseline_r) -> dict:
    """One arm vs the event exit on the same rows: net edge, mandatory fold report, stop/continue flag."""
    fold = entries["fold"].to_numpy("int64")
    r, base = np.asarray(r_exit, "float64"), np.asarray(baseline_r, "float64")
    ok = np.isfinite(r) & np.isfinite(base)
    r, base, fold, held = r[ok], base[ok], fold[ok], np.asarray(t_held, "int64")[ok]
    cost = costs.single_leg_cost()
    gross = costs.edge_bps(float(r.mean()) - float(base.mean())) if r.size else float("nan")
    per_fold = {} if not r.size else {
        int(f): costs.bps_to_frac(costs.edge_bps(float(r[fold == f].mean()) - float(base[fold == f].mean())) - cost)
        for f in sorted({int(v) for v in fold.tolist()})}
    rep = foldrep.fold_report(per_fold)                 # mandatory: raises if the fold rows are absent
    net = costs.net_edge_bps(gross, cost) if np.isfinite(gross) else float("nan")
    return {"arm": arm, "horizon": horizon, "n_entries": int(ok.sum()), "cost_bps": float(cost),
            "holding_dates": float(held.mean()) if held.size else float("nan"),
            "gross_edge_bps": float(gross), "net_edge_bps": float(net),
            "abs_net_edge_bps": float(costs.edge_bps(float(r.mean())) - cost) if r.size else float("nan"),
            "per_fold_net_edge": per_fold, "fold_report": rep, "entry_key": entries_key(entries),
            "stop": H.calib_stop(net, rep)}

def simulate_fixed_horizon(entries, h, event_rules=EVENT_RULES) -> dict:
    """Fixed pre-registered horizon: hold exactly `h` dates, exit at the h-th forward return."""
    return _score(entries, horizon_returns(entries, h), np.full(len(entries), int(h), "int64"),
                  arm=f"fixed_h{int(h)}", horizon=int(h), baseline_r=event_returns(entries, event_rules)[0])

def simulate_event_exit(entries, event_rules=EVENT_RULES) -> dict:
    """Event exit alone = the frozen baseline arm (0 gross by construction, i.e. the 50 bps round trip)."""
    r_event, t_event = event_returns(entries, event_rules)
    return _score(entries, r_event, t_event, arm="event_exit", horizon=None, baseline_r=r_event)

def simulate_hybrid(entries, h, event_rules=EVENT_RULES) -> dict:
    """Time/event hybrid: exit at `min(t_event, t_h)`, whichever comes first."""
    r_hy, t_hy = hybrid_exit(entries, h, event_rules)
    return _score(entries, r_hy, t_hy, arm=f"hybrid_h{int(h)}", horizon=int(h),
                  baseline_r=event_returns(entries, event_rules)[0])

def placebo_net_edge(entries, h, event_rules=EVENT_RULES, *, seed=PLACEBO_SEED) -> float:
    """Sign-flip placebo on the paired arm differences: no coherent paired edge survives the 50 bps."""
    r, base = hybrid_exit(entries, h, event_rules)[0], event_returns(entries, event_rules)[0]
    d = np.asarray(r, "float64") - np.asarray(base, "float64")
    d = d[np.isfinite(d)]
    signs = np.random.default_rng(int(seed)).choice([-1.0, 1.0], size=d.size)
    return (costs.net_edge_bps(costs.edge_bps(float((signs * d).mean())), costs.single_leg_cost())
            if d.size else float("nan"))

def compare_arms(entries, *, horizons=HORIZONS, event_rules=EVENT_RULES) -> list[dict]:
    """Event exit + fixed h + hybrid h for every pre-registered horizon — all on the same entry rows."""
    out = [simulate_event_exit(entries, event_rules)]
    for h in horizons:
        out += [simulate_fixed_horizon(entries, h, event_rules), simulate_hybrid(entries, h, event_rules)]
    return out

def horizon_returns_from_cache(frame, market, h, *, panel_cache=PANEL_CACHE) -> np.ndarray:
    """Causal symbol-sequential forward return at `h` **calendar-daily** dates of that symbol (float32).

    A cache that is not a business-daily bar series (e.g. a sparse swing-event panel) fails closed:
    there `h` observations is not `h` dates, and the derived edge would be wrong by construction.
    """
    path = Path(panel_cache) / f"wi036_panel_{market}.parquet"
    if not path.exists():
        raise RuntimeError(f"causal price cache missing: {path} (pass --entries carrying an r_h{int(h)} column)")
    panel = (pd.read_parquet(path, columns=["symbol", "date", "close"])
             .drop_duplicates(["symbol", "date"]).sort_values(["symbol", "date"], kind="mergesort"))
    gaps = panel.groupby("symbol")["date"].diff().dt.days.dropna()
    if gaps.empty or float(gaps.median()) > MAX_PANEL_GAP_DAYS:
        raise RuntimeError(f"price cache {path} is not a daily bar series (median gap "
                           f"{float(gaps.median()) if gaps.size else float('nan'):.1f}d) — pass --entries "
                           f"carrying an r_h{int(h)} column")
    sym, date = frame["symbol"].astype(str).to_numpy(), pd.to_datetime(frame["date"]).to_numpy()
    got = np.full(len(frame), np.nan)
    for name, grp in panel.groupby("symbol", sort=True):           # symbol-sequential (repo law)
        rows = np.flatnonzero(sym == name)
        close = np.asarray(grp["close"], "float64")
        pos = {s: i for i, s in enumerate(pd.to_datetime(grp["date"]).to_numpy())}
        for r in rows:
            i = pos.get(date[r])
            if i is not None and i + int(h) < close.size:
                got[r] = close[i + int(h)] / close[i] - 1.0
    return got.astype("float32")

def attach_horizons(frame, market, *, panel_cache=PANEL_CACHE, horizons=HORIZONS) -> pd.DataFrame:
    """Add only the missing `r_h<h>` columns from the causal price cache; never overwrite a given one."""
    out = frame.copy()
    for h in horizons:
        if f"r_h{int(h)}" not in out.columns:
            out[f"r_h{int(h)}"] = horizon_returns_from_cache(out, market, h, panel_cache=panel_cache)
    return out

def _entry_path(market, entries):
    """`--entries` (file or dir) > the WI-066/067 screener artifact if alive > the frozen fib baseline."""
    if entries is not None:
        path = Path(entries)
        if not path.is_dir():
            if not path.exists():
                raise FileNotFoundError(f"entry artifact missing: {path}")
            return path
        found = sorted(path.glob(f"{market}_*.parquet"))
        if not found:
            raise FileNotFoundError(f"no entry artifact for market={market} under {path}")
        return found[0]
    for root in (ENTRIES_ROOT,):                       # real runs never consume a *_smoke artifact
        if sorted(root.glob(f"{market}_*.parquet")):
            return sorted(root.glob(f"{market}_*.parquet"))[0]
    return None

def load_entries(market, entries=None, *, panel_cache=PANEL_CACHE, baseline_dir=BASELINE_DIR) -> pd.DataFrame:
    """CALIB-only entry set with every arm's inputs; EVAL rows are dropped, never read (float32)."""
    path = _entry_path(market, entries)
    if path is None:
        from src.swing_bsh.hold_filter_gate import baseline_returns    # lazy: heavy import, fib fallback only
        base = baseline_returns(market, baseline_dir)                  # frozen fib entries + WI-030 event exit
        frame = pd.DataFrame({"symbol": base["symbol"].astype(str), "date": pd.to_datetime(base["date"]),
                              "fold": np.zeros(len(base), "int64"),
                              "r_event": base["r_frozen"].to_numpy("float32"),
                              "t_event": np.full(len(base), EVENT_HORIZON_FIB, "int64")})
    else:
        raw = pd.read_parquet(path)
        if {"symbol", "date"} - set(raw.columns):
            raise KeyError(f"entry artifact {path} lacks {sorted({'symbol', 'date'} - set(raw.columns))}")
        if "entry" in raw.columns or "selected" in raw.columns:        # WI-066/067 screener output shape
            flag = raw["entry"] if "entry" in raw.columns else raw["selected"]
            raw = raw[flag.to_numpy(bool)].reset_index(drop=True)
        r_event = raw["r_event"] if "r_event" in raw.columns else raw.get("r_frozen", raw.get("r"))
        if r_event is None:
            raise KeyError(f"entry artifact {path} carries no event-exit return (r_event/r_frozen/r)")
        frame = pd.DataFrame({"symbol": raw["symbol"].astype(str), "date": pd.to_datetime(raw["date"]),
                              "r_event": pd.to_numeric(r_event, errors="coerce").to_numpy("float32"),
                              "fold": (np.asarray(raw["fold"], "int64") if "fold" in raw.columns
                                       else np.zeros(len(raw), "int64")),
                              "t_event": (np.asarray(raw["t_event"], "int64") if "t_event" in raw.columns
                                          else np.full(len(raw), EVENT_HORIZON_FIB, "int64"))})
        given = [f"r_h{int(h)}" for h in HORIZONS]                     # a given horizon is never re-derived
        for col in [c for r in EVENT_RULES for c in (f"t_event_{r}", f"r_event_{r}")] + given:
            if col in raw.columns:
                frame[col] = raw[col].to_numpy()
    frame = attach_horizons(frame, market, panel_cache=panel_cache)
    frame = frame[pd.to_datetime(frame["date"]) < H.CALIB_END]         # CALIB only: EVAL never read
    need = ["r_event", "t_event"] + [f"r_h{int(h)}" for h in HORIZONS]
    frame = frame.dropna(subset=need).reset_index(drop=True)           # complete-panel intersection, all arms
    if frame.empty:
        raise ValueError(f"no finite CALIB entries for market={market} ({path})")
    frame["fold"], frame["t_event"] = frame["fold"].to_numpy("int64"), frame["t_event"].to_numpy("int64")
    for col in ["r_event"] + [f"r_h{int(h)}" for h in HORIZONS]:
        frame[col] = frame[col].to_numpy("float32")
    return frame.sort_values(["date", "symbol"], kind="mergesort").reset_index(drop=True)

def synthetic_fixture(market=SMOKE_MARKET, n_entries=SMOKE_ENTRIES, seed=SMOKE_SEED) -> pd.DataFrame:
    """Deterministic planted timing edge, no `data/` read: h13 pays, h55 decays, an early stop fires."""
    rng = np.random.default_rng(int(seed))
    n = int(n_entries)
    fold = (np.arange(n) % 5).astype("int64")
    early = rng.random(n) < 0.25                                       # the event stop fires before h13
    return pd.DataFrame({
        "symbol": np.array([f"{market}{i % 40:02d}" for i in range(n)]),
        "date": pd.date_range("2021-01-04", periods=n, freq="B"),
        "fold": fold, "t_event": np.where(early, 8, EVENT_HORIZON_FIB).astype("int64"),
        "r_event": (np.where(early, -0.020, 0.0) + rng.normal(0.0, 0.010, n)).astype("float32"),
        "r_h13": (0.010 + 0.001 * fold + rng.normal(0.0, 0.012, n)).astype("float32"),
        "r_h55": (-0.002 + rng.normal(0.0, 0.020, n)).astype("float32")})

def write_calib_report(path, market, arms, *, smoke=False) -> Path:
    """CALIB comparison card: per-horizon net edge, fold report and stop/continue for every arm."""
    ev = next(a for a in arms if a["arm"] == "event_exit")
    best = max(arms, key=lambda a: float(a["net_edge_bps"]) if np.isfinite(a["net_edge_bps"]) else -np.inf)
    lines = [f"# L2 time exits — fixed h13/h55 + hybrid vs event exits on identical entries ({market})", "",
             f"- Generated (UTC): {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
             "- Scope: CALIB only (EVAL unread — WI-071); horizons pre-registered ex ante, no learned chooser"
             + ("  (smoke / synthetic)" if smoke else ""),
             f"- Entries: {int(ev['n_entries']):,} identical rows (key `{ev['entry_key']}`) in every arm; "
             f"{ev['fold_report']['n_folds']} folds",
             f"- Baseline: the frozen event exit on those same rows; cost {costs.single_leg_cost():.0f} bps "
             f"single-leg round trip (materiality floor {H.MATERIALITY_FLOOR_BPS:.0f} bps)",
             f"- Best arm `{best['arm']}`: net {_fmt(best['net_edge_bps'])} bps vs the event exit, absolute "
             f"{_fmt(best['abs_net_edge_bps'])} bps (event exit absolute {_fmt(ev['abs_net_edge_bps'])} bps)",
             "- Stop/continue: " + "; ".join(f"`{a['arm']}` {'STOP' if a['stop']['stop'] else 'CONTINUE'}"
                                             for a in arms),
             "", "| arm | entries | hold (dates) | gross vs event (bps) | net vs event (bps) | "
                 "absolute net (bps) | max fold share | folds + | ceiling | Stop flag |",
             "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |"]
    for a in arms:
        rep = a["fold_report"]
        lines.append(f"| `{a['arm']}` | {int(a['n_entries']):,} | {a['holding_dates']:.1f} | "
                     f"{_fmt(a['gross_edge_bps'], '{:+.1f}')} | {_fmt(a['net_edge_bps'], '{:+.1f}')} | "
                     f"{_fmt(a['abs_net_edge_bps'], '{:+.1f}')} | {rep['max_fold_share']:.3f} | "
                     f"{rep['n_positive_folds']}/{rep['n_folds']} | "
                     f"{'pass' if rep['fold_ceiling_ok'] else 'FAIL'} | "
                     f"{'STOP' if a['stop']['stop'] else 'CONTINUE'} |")
    reasons = "; ".join(f"`{a['arm']}` {r}" for a in arms for r in a["stop"]["reasons"])
    lines += ["", f"| `{best['arm']}` fold | net edge (bps) |", "| ---: | ---: |"] + [
        f"| {f} | {1e4 * float(v):+.1f} |" for f, v in sorted(best["per_fold_net_edge"].items())]
    lines += ["", "- Fold report (mandatory, fails closed): " + (reasons or "no stop reasons — all arms clean"),
              "- Layer separation: no learner refit, no AUC selection, one-shot EVAL in WI-071 after the freeze.",
              "", "Record-only: no shortlist, no deployment, no live trading."]
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")
    return path

def run_market(market, entries_frame, *, report_root=REPORTS_ROOT, smoke=False) -> list[dict]:
    """One market: score every arm on one entry set → CALIB card + fold reports; prints one line."""
    arms = compare_arms(entries_frame)
    suffix = "_smoke" if smoke else ""
    path = write_calib_report(Path(report_root) / f"calib_{market}{suffix}.md", market, arms, smoke=smoke)
    for a in arms:
        foldrep.write_fold_report(a["fold_report"], Path(report_root) / f"fold_{a['arm']}_{market}{suffix}.json")
    ev = next(a for a in arms if a["arm"] == "event_exit")
    best = max(arms, key=lambda a: float(a["net_edge_bps"]))
    print(f"[l2.timeexit] {market}: n={int(ev['n_entries'])} best={best['arm']} "
          f"net={_fmt(best['net_edge_bps'], '{:+.0f}')}bps vs event {_fmt(ev['net_edge_bps'], '{:+.0f}')}bps "
          f"{'STOP' if best['stop']['stop'] else 'CONTINUE'} -> {path.name}")
    return arms

def main(argv=None) -> int:
    """CLI: `--smoke` (synthetic, `*_smoke` roots) or the full CALIB run (PM gate)."""
    ap = argparse.ArgumentParser(description="WI-068 fixed time exits + hybrid vs event exits (D-027 §5 (a))")
    ap.add_argument("--smoke", action="store_true", help="synthetic run into the *_smoke roots")
    ap.add_argument("--market", default=None, help="limit to one market (default: both)")
    ap.add_argument("--entries", default=None, help="entry-set parquet (or dir); default: WI-066/067, else fib")
    args = ap.parse_args(argv)
    markets = (args.market,) if args.market else MARKETS
    if args.smoke:
        for mk in markets:
            run_market(mk, synthetic_fixture(mk), report_root=REPORTS_SMOKE_ROOT, smoke=True)
        print(f"[l2.timeexit] smoke artifacts -> {REPORTS_SMOKE_ROOT} | EXIT:0")
        return 0
    for mk in markets:
        run_market(mk, load_entries(mk, args.entries), report_root=REPORTS_ROOT)
    print(f"[l2.timeexit] calib reports -> {REPORTS_ROOT} | EXIT:0")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
