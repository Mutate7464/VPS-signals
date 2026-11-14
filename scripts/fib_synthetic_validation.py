"""WI-031: synthetic validation of the fib fold-stability gate.

GARCH(1,1) vol + 2-state Markov drift, ~4000 days: NULL (no edge), CONSTANT
(+0.5%/event over the 0.5% gate floor) and CHAOTIC (edge only in regimes 1/3/5
of a 5-block cycle). REAL pieces imported, never reimplemented: WI-023
`simulate`, WI-028 `ensemble_mean`, `group_stats` fold rule, `purge_keep_mask` CV.
Variants: strict_5of5, loose_4of5 (+pooled), pooled_only_t2, loose_3of5_pooled.
Out (default reports/fib_swings): gate_comparison.csv + SYNTHETIC_VALIDATION.md.
"""
import argparse
import os
import sys
import time
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fib_trade_labels import (HIT_REASONS, N_FOLDS, POLICIES, atr14,  # noqa: E402
                              group_stats, simulate)
from fib_entry_window import ensemble_mean  # noqa: E402
from fib_meta_model import purge_keep_mask  # noqa: E402

SCENARIOS = ('NULL', 'CONSTANT', 'CHAOTIC')
# path drifts vs label space (transfer ~0.8): BOUNCE centres NULL at zero, EDGE is
# +0.5%/event over the WI-023 0.5% floor (label lift ~1.0%)
BOUNCE, EDGE, GATE_MIN_MEAN = 0.0045, 0.0125, 0.005
CALIB_FRAC, HORIZON = 0.60, 39
MU = np.array([0.0003, -0.0003])     # Markov state drift
CLOSE_POLICIES = [(p, tv, sv, dv) for p, tv, sv, dv, em in POLICIES if em == 'close']
FEATS = ['dd63', 'mom63', 'vol21', 'rsi14', 'gap63', 'low_ratio', 'logc']
COLS = ['symbol', 'market', 'date', 'screen_bottom', 'policy', 'ret', 'reason'] + FEATS
VARIANTS = ('strict_5of5', 'loose_4of5', 'loose_4of5_pooled', 'pooled_only_t2',
            'loose_3of5_pooled')

def edge_active(scenario, n):
    """NULL never; CONSTANT always; CHAOTIC in blocks 1/3/5 of a 5-block cycle."""
    if scenario == 'CONSTANT':
        return np.ones(n, dtype=bool)
    if scenario == 'NULL':
        return np.zeros(n, dtype=bool)
    return ((np.arange(n) // max(5, n // 25)) % 5) % 2 == 0

def garch(rng, n, a=0.08, b=0.90, vol=0.012):
    """GARCH(1,1) returns; cast float32 immediately (repo law)."""
    w, s2, r = vol * vol * (1 - a - b), np.empty(n), np.empty(n)
    s2[0], r[0] = vol * vol, vol * rng.standard_normal()
    for t in range(1, n):
        s2[t] = w + a * r[t - 1] ** 2 + b * s2[t - 1]
        r[t] = np.sqrt(s2[t]) * rng.standard_normal()
    return r.astype('float32'), np.sqrt(s2).astype('float32')

def simulate_market(scenario, seed, n_symbols=100, n_days=4000):
    """-> (dates, {symbol: o/h/l/c float32, market, active mask})."""
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range('2004-01-01', periods=n_days).strftime('%Y-%m-%d')
    active, mkts = edge_active(scenario, n_days), {}
    for k in range(n_symbols):
        r, sv = garch(rng, n_days)
        st = (np.cumsum(rng.random(n_days) > 0.99) % 2).astype('int8')
        c = 100.0 * np.exp(np.cumsum(r + MU[st]))
        o = np.concatenate(([100.0], c[:-1] * np.exp(
            rng.standard_normal(n_days)[1:] * 0.3 * sv[1:])))
        u = np.abs(rng.standard_normal(n_days)) * 0.5 * sv + 1e-3
        v = np.abs(rng.standard_normal(n_days)) * 0.5 * sv + 1e-3
        mkts[f'S{k:03d}'] = dict(
            market='USD' if k % 2 else 'CAD', active=active, o=o.astype('float32'),
            h=(np.maximum(o, c) * (1 + u)).astype('float32'), c=c.astype('float32'),
            l=(np.minimum(o, c) * (1 - v)).astype('float32'))
    return dates, mkts

def event_features(c, l, idx, pos):  # pre-event only: slices end at i, plant at i+1
    i = int(idx[pos])
    prev = int(idx[pos - 1]) if pos else max(0, i - 120)
    w = c[max(0, i - 63):i + 1].astype('float64')
    d = np.diff(np.log(c[max(0, i - 21):i + 1].astype('float64') + 1e-9))
    dd = np.diff(w[-15:])
    up = float(np.clip(dd, 0, None).mean()) if len(dd) else 0.0
    dn = float(-np.clip(dd, None, 0).mean()) if len(dd) else 0.0
    return (float(c[i] / w.max() - 1), float(np.log(c[i] / w[0])),
            float(d.std()) if len(d) > 1 else np.nan,
            float(100 * up / (up + dn + 1e-12)), float((i - prev) / 63.0),
            float(l[i] / c[i] - 1), float(np.log(c[i])))

def market_labels(sym, md, dates):
    """One row per (39d-low event, close policy) on the planted synthetic path."""
    n = len(md['c'])
    rm = pd.Series(md['l']).rolling(39, min_periods=39).min().to_numpy()
    cand = np.where((np.arange(n) >= 38) & (md['l'] <= rm))[0]
    idx, last = [], -10 ** 9                     # greedy 5-bar suppression
    for i in cand:
        if i - last >= 5:
            idx.append(int(i))
            last = int(i)
    fac = np.ones(n)                             # plant the edge on [i+1, i+H]
    for i in idx:                                # baseline bounce + scenario edge
        j, g = min(i + HORIZON, n - 1), BOUNCE + EDGE * md['active'][i]
        fac[i + 1:j + 1] *= np.exp(g * np.arange(1, j - i + 1) / HORIZON)
    o, h, l, c = md['o'] * fac, md['h'] * fac, md['l'] * fac, md['c'] * fac
    a14 = atr14(h.astype('float64'), l.astype('float64'), c.astype('float64'))
    # screen flag on the unplanted path -> screen independent of planted edge
    rm63 = pd.Series(md['c']).rolling(63, min_periods=20).min().to_numpy()
    rows = []
    for pos, i in enumerate(idx):
        sb = bool(md['c'][i] <= 1.05 * rm63[i]) if np.isfinite(rm63[i]) else True
        f = event_features(c, l, idx, pos)
        for pid, tv, sv, dv in CLOSE_POLICIES:
            entry = float(c[i])
            stop = entry - 1.5 * a14[i] if sv == 'atr1.5' else entry * (1 - sv)
            ret, reason, _ = simulate(o, h, l, c, int(i), entry, tv, stop, dv, 'close')
            rows.append((sym, md['market'], dates[i], sb, pid, ret, reason) + f)
    return rows

def build_labels(dates, mkts):
    """Per-event WI-028 ensemble label + features + target-hit share."""
    rows = []
    for sym, md in mkts.items():
        rows.extend(market_labels(sym, md, dates))
    if not rows:
        return pd.DataFrame(columns=['symbol', 'date', 'market', 'screen_bottom',
                                     'ret', 'hit'] + FEATS)
    lab = pd.DataFrame(rows, columns=COLS)
    lab['ret'], lab[FEATS] = lab['ret'].astype('float32'), lab[FEATS].astype('float32')
    ev = ensemble_mean(lab)                            # real WI-028 ensemble rule
    keys = lab.drop_duplicates(['symbol', 'date'])[
        ['symbol', 'date', 'market', 'screen_bottom'] + FEATS]
    hit = lab.groupby(['symbol', 'date'], as_index=False)['reason'].agg(
        hit=lambda r: float(r.isin(HIT_REASONS).mean()))
    ev = ev.merge(keys, on=['symbol', 'date']).merge(hit, on=['symbol', 'date'])
    return ev.sort_values('date').reset_index(drop=True)

def stability_stats(ev, cut):
    """REAL fold-stability rule via fib_trade_labels.group_stats (imported)."""
    cal = ev[(ev['date'] < cut) & ev['ret'].notna() & ev['screen_bottom']].copy()
    if len(cal) < N_FOLDS:
        return dict(n_folds_pos=np.nan, mean_ret=np.nan, n_calib=0)
    # group_stats needs a reason column for hit_rate only; gate = folds + mean.
    cal['reason'] = np.where(cal['hit'] >= 0.5, 'target', 'stop')
    s = group_stats(cal, 'CALIB')
    return dict(n_folds_pos=float(s['n_folds_pos']), mean_ret=float(s['mean_ret']),
                n_calib=int(len(cal)))

def pooled_oof(cal, n_blocks=N_FOLDS):
    """Purged 5-block CV (purge_keep_mask) -> pooled out-of-fold selection."""
    if len(cal) < 2 * n_blocks:
        return dict(pooled_mean=np.nan, pooled_t=np.nan, n_oof=0)
    x, y = cal[FEATS].to_numpy('float64'), cal['ret'].to_numpy('float64')
    d = pd.to_datetime(cal['date'])
    blk = pd.qcut(d.rank(method='first'), n_blocks, labels=False).to_numpy()
    preds = np.full(len(y), np.nan)
    for b in range(n_blocks):
        te = blk == b
        keep = purge_keep_mask(d[~te], d[te].min(), d[te].max()).to_numpy()
        tr = np.where(~te)[0][keep]
        if len(tr) < n_blocks * 2:
            continue
        med = np.nanmedian(x[tr], axis=0)
        fill = lambda a: np.nan_to_num(np.where(np.isfinite(a), a, med), nan=0.0)
        preds[te] = Ridge(alpha=1.0).fit(fill(x[tr]), y[tr]).predict(fill(x[te]))
    sel = np.isfinite(preds) & (preds > 0)
    n = int(sel.sum())
    if n < 2:
        return dict(pooled_mean=np.nan, pooled_t=np.nan, n_oof=n)
    m, sd = float(y[sel].mean()), float(y[sel].std(ddof=1))
    return dict(pooled_mean=m, n_oof=n,
                pooled_t=float(m / (sd / np.sqrt(n))) if sd > 0 else np.inf)

def variant_accepts(s):
    """Accept/reject of each gate variant given one seed's statistics."""
    f, m = s.get('n_folds_pos'), s.get('mean_ret')
    pm, pt = s.get('pooled_mean'), s.get('pooled_t')
    ok_m, ok_p = bool(np.isfinite(m) and m >= GATE_MIN_MEAN), bool(
        np.isfinite(pm) and pm > 0)
    return {'strict_5of5': f == 5 and ok_m, 'loose_4of5': f >= 4 and ok_m,
            'loose_4of5_pooled': f >= 4 and ok_m and ok_p,
            'pooled_only_t2': ok_p and bool(np.isfinite(pt) and pt > 2),
            'loose_3of5_pooled': f >= 3 and ok_m and ok_p}

def evaluate_seed(scenario, seed, n_symbols, n_days):
    dates, mkts = simulate_market(scenario, seed, n_symbols, n_days)
    ev = build_labels(dates, mkts)
    cut = dates[int(CALIB_FRAC * n_days)]
    s = stability_stats(ev, cut)
    s.update(pooled_oof(ev[(ev['date'] < cut) & ev['ret'].notna()
                          & ev['screen_bottom']]))
    return [dict(scenario=scenario, seed=seed, variant=v, n_events=len(ev),
                 n_calib=s['n_calib'], n_folds_pos=s['n_folds_pos'],
                 mean_ret=s['mean_ret'], pooled_mean=s['pooled_mean'],
                 pooled_t=s['pooled_t'], accept=int(a))
            for v, a in variant_accepts(s).items()]

def recommend(fp, det):
    """Loosened variant with the best detection gain at comparable NULL FP."""
    strict = fp['strict_5of5']
    cands = [v for v in VARIANTS if v != 'strict_5of5'
             and fp[v] <= strict + 0.05 and det[v] > det['strict_5of5']]
    if not cands:
        return 'strict_5of5', ('No loosened variant detects more chaotic edge at '
                               'comparable FP; keep strict 5/5.')
    pick = max(cands, key=lambda v: det[v] - fp[v])
    return pick, (f'Adopt {pick}: CHAOTIC detection {det[pick]:.2f} vs strict '
                  f'{det["strict_5of5"]:.2f}, NULL FP {fp[pick]:.2f} vs {strict:.2f}.')

def write_md(df, cpu, out):
    agg = df.groupby(['scenario', 'variant'])['accept'].mean().unstack()
    fp, const, det = agg.loc['NULL'], agg.loc['CONSTANT'], agg.loc['CHAOTIC']
    rec, rec_txt = recommend(fp, det)
    lines = ['# SYNTHETIC VALIDATION — fold-stability gate (WI-031)', '',
             f'NULL/CONSTANT/CHAOTIC x {df["seed"].nunique()} seeds | gate code imported', '',
             '## Accept rate (NULL = false positive)', '',
             '| variant | NULL FP | CONSTANT | CHAOTIC |', '|---|---|---|---|']
    lines += [f'| {v} | {fp[v]:.3f} | {const[v]:.3f} | {det[v]:.3f} |' for v in VARIANTS]
    fp0, fr = fp['strict_5of5'], 1 - const['strict_5of5']
    lines += ['', '## Calibration check (strict 5/5)', '',
              f'edge {EDGE:.4f} over the {GATE_MIN_MEAN:.1%} floor | NULL FP {fp0:.3f} '
              f'vs CONSTANT false-rejection {fr:.3f} | gap {abs(fp0 - fr):.3f}',
              '', '## CPU (core-seconds, hard cap 4 core-hours = 14400)', '']
    lines += [f'- {k}: {v:.0f}' for k, v in cpu.items()]
    lines += [f'- total: {sum(cpu.values()):.0f}', '', '## Recommendation', '', rec_txt,
              '', f'VERDICT: ADOPT_{rec.upper()}', '']
    with open(f'{out}/SYNTHETIC_VALIDATION.md', 'w') as f:
        f.write('\n'.join(lines))

def main(out='reports/fib_swings', n_symbols=100, n_days=4000, n_seeds=20):
    os.makedirs(out, exist_ok=True)
    rows, cpu = [], {}
    for sc in SCENARIOS:
        t0 = time.process_time()
        for seed in range(n_seeds):
            rows.extend(evaluate_seed(sc, seed, n_symbols, n_days))
        cpu[sc] = time.process_time() - t0
        df = pd.DataFrame(rows)
        agg = df.groupby(['scenario', 'variant'])['accept'].mean().rename(
            'accept_rate').reset_index()
        df.merge(agg, on=['scenario', 'variant'], how='left').to_csv(
            f'{out}/gate_comparison.csv', index=False)      # per-scenario checkpoint
        print(f'{sc}: {cpu[sc]:.1f} core-s', flush=True)
    write_md(pd.DataFrame(rows), cpu, out)
    print(f'total core-s {sum(cpu.values()):.0f} | rows {len(rows)}', flush=True)
    print('EXIT:0', flush=True)

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='WI-031 synthetic gate validation')
    ap.add_argument('--out', default='reports/fib_swings')
    ap.add_argument('--symbols', type=int, default=100)
    ap.add_argument('--days', type=int, default=4000)
    ap.add_argument('--seeds', type=int, default=20)
    a = ap.parse_args()
    main(a.out, a.symbols, a.days, a.seeds)
