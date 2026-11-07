"""WI-028: entry-window measurement — all-bottoms ensemble label under first-touch
barrier sim at offset entries (k=0 at-bottom vs k=3/k=5 confirmed delay).

Per trailing-bottom event (type=='bottom'), runs the WI-023 first-touch barrier
simulation (simulate() reused verbatim) at three entry timings:
  k=0  entry = close at the event bar (WI-023 current behavior, taken from
       trade_labels_w39.parquet close-entry rows);
  k=3 / k=5  confirmed delay: if NO new 39d-low occurred during the whole
       window [i+1..i+k] (min(low[i+1..i+k]) > low[i]), entry = close[i+k];
       otherwise the event produces NO trade (unresolved) for that k.
Policies: target {0.10,0.15} x stop {0.05,0.08,0.10,atr} x max_days {20,39},
entry='close' (the close-entry half of the WI-023 grid). float32 returns.
CALIB only for the summary (EVAL reserved for final scoring).

Outputs -> out_dir (default reports/fib_swings):
  entry_window_labels.parquet   one row per (bottom event, policy, k)
  entry_window_summary.csv      k x regime x market (CALIB only)
  ENTRY_WINDOW.md                per-k tables + VERDICT
"""
import argparse
import os
import sys

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fib_trade_labels import (COST, EMBARGO_START, POLICIES, atr14,  # noqa: E402
                              simulate)

KS = [0, 3, 5]
CLOSE_POLICIES = [(pid, tv, sv, dv)                # 16 close-entry policies
                  for pid, tv, sv, dv, em in POLICIES if em == 'close']
COLS = ['symbol', 'market', 'date', 'k', 'policy', 'ret', 'reason', 'days']
SUM_COLS = ['k', 'regime', 'market', 'n', 'n_resolved', 'mean_ret', 'hit_rate',
            'median_ret', 'p10_ret', 'fold1_mean', 'fold2_mean', 'fold3_mean',
            'fold4_mean', 'fold5_mean', 'n_folds_pos']
N_FOLDS = 5


def find_entry_index(l, i, k):
    """k=0 -> i; k>0 -> i+k iff min(low[i+1..i+k]) > low[i], else None."""
    if k == 0:
        return i
    if i + k >= len(l):
        return None
    if l[i + 1:i + k + 1].min() > l[i]:
        return i + k
    return None


def simulate_at(o, h, l, c, i, k, tv, sv, dv, a14):
    """(ret, reason, days) for one policy entered at the k-offset bar."""
    j = find_entry_index(l, i, k)
    if j is None:
        return (np.nan, 'unresolved', 0)
    entry = c[j]
    stop_px = entry - 1.5 * a14[j] if sv == 'atr1.5' else entry * (1 - sv)
    return simulate(o, h, l, c, j, entry, tv, stop_px, dv, 'close')


def ensemble_mean(lab):
    """Per (symbol, date) event: mean(ret) across policies (the ensemble label)."""
    return lab.groupby(['symbol', 'date'], as_index=False)['ret'].mean()


def _regime_map(reg):
    """(market, date) -> regime; per-market row preferred, 'ALL' row fallback."""
    m = {}
    r = reg[reg['market'] != 'ALL']
    for mk, d, g in zip(r['market'], r['date'].astype(str).str.slice(0, 10),
                        r['regime']):
        m[(mk, d)] = g
    ra = reg[reg['market'] == 'ALL']
    for d, g in zip(ra['date'].astype(str).str.slice(0, 10), ra['regime']):
        m.setdefault(('ALL', d), g)
    return m


def _stats(g):
    """Resolved-only stats + 5 contiguous date-block folds (CALIB)."""
    n = len(g)
    res = g[g['ret'].notna()]
    n_res = len(res)
    if n_res == 0:
        out = {'n': n, 'n_resolved': 0, 'mean_ret': np.nan, 'hit_rate': np.nan,
               'median_ret': np.nan, 'p10_ret': np.nan,
               'n_folds_pos': np.nan}
        return {**out, **{f'fold{x}_mean': np.nan for x in range(1, 6)}}
    gs = res.sort_values('date', kind='mergesort')
    rets = gs['ret'].to_numpy(dtype='float64')
    folds = [float(rets[b].mean()) if len(b) else np.nan
             for b in np.array_split(np.arange(n_res), N_FOLDS)]
    out = {'n': n, 'n_resolved': n_res, 'mean_ret': float(rets.mean()),
           'hit_rate': float((rets > 0).mean()),
           'median_ret': float(np.median(rets)),
           'p10_ret': float(np.percentile(rets, 10)),
           'n_folds_pos': int(sum(m > 0 for m in folds))}
    return {**out, **{f'fold{x}_mean': m for x, m in enumerate(folds, 1)}}


def main(out_dir='reports/fib_swings', smoke=None):
    data_dir = 'reports/fib_swings'
    ev = pd.read_csv(f'{data_dir}/trailing_events_w39.csv',
                     keep_default_na=False, na_values=[''])
    ev = ev[ev['type'] == 'bottom'][['symbol', 'market', 'date']].copy()
    ev['date'] = ev['date'].astype(str).str.slice(0, 10)
    if smoke:
        ev = ev[ev['symbol'].isin({s.strip() for s in smoke.split(',')
                                   if s.strip()})]

    # k=0 rows: WI-023's already-computed close-entry trade labels.
    lab0 = pd.read_parquet(f'{data_dir}/trade_labels_w39.parquet')
    lab0 = lab0[lab0['policy'].str.endswith('_close')][
        ['symbol', 'market', 'date', 'policy', 'ret', 'reason', 'days']].copy()
    lab0.insert(3, 'k', 0)
    if smoke:
        lab0 = lab0[lab0['symbol'].isin(set(ev['symbol']))]

    # k=3 / k=5 rows: confirmed-delay simulation on raw OHLCV.
    rows = []
    for (market, sym), g in ev.groupby(['market', 'symbol'], sort=True):
        path = f'data/raw_ohlcv/market={market}/symbol={sym}.parquet'
        if not os.path.exists(path):
            continue
        df = pq.read_table(path).to_pandas().sort_values('date')
        df = df.reset_index(drop=True)
        o = df['open'].to_numpy(dtype='float64')
        h = df['high'].to_numpy(dtype='float64')
        l = df['low'].to_numpy(dtype='float64')
        c = df['close'].to_numpy(dtype='float64')
        dmap = {d: k for k, d in enumerate(df['date'].astype(str)
                                           .str.slice(0, 10))}
        a14 = atr14(h, l, c)
        for date in g['date'].to_numpy():
            i = dmap.get(date)
            if i is None:
                continue
            for k in KS[1:]:
                for pid, tv, sv, dv in CLOSE_POLICIES:
                    ret, reason, days = simulate_at(o, h, l, c, i, k, tv, sv,
                                                    dv, a14)
                    rows.append((sym, market, date, k, pid, ret, reason, days))
    labk = pd.DataFrame(rows, columns=COLS)
    lab = pd.concat([lab0[COLS], labk], ignore_index=True)
    lab['ret'] = lab['ret'].astype('float32')
    lab['days'] = lab['days'].astype('int16')
    lab['k'] = lab['k'].astype('int16')
    lab['reason'] = lab['reason'].astype('category')
    os.makedirs(out_dir, exist_ok=True)
    lab.to_parquet(f'{out_dir}/entry_window_labels.parquet', index=False)
    print('entry_window rows:', len(lab), 'policies:',
          len(CLOSE_POLICIES), flush=True)

    # summary: CALIB only, k x regime x market.
    reg = pd.read_csv(f'{data_dir}/regime_daily_extended.csv',
                      keep_default_na=False, na_values=[''])
    rmap = _regime_map(reg)
    cal = lab[lab['date'] < EMBARGO_START].copy()
    cal['regime'] = [rmap.get((mk, d), rmap.get(('ALL', d), 'unknown'))
                     for mk, d in zip(cal['market'], cal['date'])]
    srows = []
    for k in KS:
        kk = cal[cal['k'] == k]
        for mkt in ('CAD', 'USD', 'ALL'):
            km = kk if mkt == 'ALL' else kk[kk['market'] == mkt]
            if not len(km):
                continue
            srows.append({'k': k, 'regime': 'ALL', 'market': mkt,
                          **_stats(km)})
            for rg in sorted(km['regime'].dropna().unique()):
                srows.append({'k': k, 'regime': rg, 'market': mkt,
                              **_stats(km[km['regime'] == rg])})
    summ = pd.DataFrame(srows)
    summ = summ[SUM_COLS]
    summ.to_csv(f'{out_dir}/entry_window_summary.csv', index=False)
    print('summary rows:', len(summ), flush=True)

    _write_md(out_dir, summ)
    print('EXIT:0', flush=True)


def _verdict(sub):
    """sub: CALIB ALL overall rows per k -> (verdict, winner k)."""
    by = {int(r['k']): r for _, r in sub.iterrows()}
    if 0 not in by:
        return 'INCONCLUSIVE', None
    best0 = (by[0]['mean_ret'], by[0]['hit_rate'], by[0]['n_folds_pos'])
    wins = {}
    for k in (3, 5):
        if k not in by:
            continue
        b = (by[k]['mean_ret'], by[k]['hit_rate'], by[k]['n_folds_pos'])
        wins[k] = sum((b[0] > best0[0], b[1] > best0[1], b[2] > best0[2]))
    dom = all(w <= 0 for w in wins.values()) or not wins
    if dom:
        return 'RECOMMEND_AT_BOTTOM', 0
    for k, w in wins.items():
        if w == 3:
            return f'RECOMMEND_DELAYED_k{k}', k
    return 'INCONCLUSIVE', None


def _write_md(out_dir, summ):
    lines = ['# Entry-window measurement (WI-028)', '',
             'All-bottoms ensemble (close-entry policies) at entry offsets',
             'k=0 (at-bottom) vs k=3 / k=5 (confirmed delay, no new 39d-low',
             'in the k-day window). CALIB only (date < %s).' % EMBARGO_START,
             '', '## Overall (ALL market, all-bottoms)', '']
    ov = summ[(summ['market'] == 'ALL') & (summ['regime'] == 'ALL')]
    lines.append(ov.drop(columns=['market', 'regime'])
                 .to_string(index=False))
    lines += ['', '## Per-regime breakdown (ALL market)', '']
    rg = summ[(summ['market'] == 'ALL') & (summ['regime'] != 'ALL')]
    lines.append(rg.drop(columns=['market']).to_string(index=False))
    lines += ['', '## Fold stability (ALL market, folds on CALIB resolved)', '']
    fs = ov[['k', 'fold1_mean', 'fold2_mean', 'fold3_mean', 'fold4_mean',
             'fold5_mean', 'n_folds_pos']]
    lines.append(fs.to_string(index=False))
    verdict, wk = _verdict(ov)
    lines += ['', '## Callout', '']
    for k in (3, 5):
        row = ov[ov['k'] == k]
        row0 = ov[ov['k'] == 0]
        if len(row) and len(row0):
            lines.append(
                f'k={k} regime n_folds_pos==5 where k=0 does not? '
                f'k={k}: {int(row.iloc[0]["n_folds_pos"])} vs '
                f'k=0: {int(row0.iloc[0]["n_folds_pos"])}')
    lines += ['', f'VERDICT: {verdict}', '']
    with open(f'{out_dir}/ENTRY_WINDOW.md', 'w') as f:
        f.write('\n'.join(lines))


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='WI-028 entry-window sim')
    ap.add_argument('--out', default='reports/fib_swings')
    ap.add_argument('--smoke', default=None,
                    help='comma-separated symbols (default FIB_SMOKE env)')
    a = ap.parse_args()
    main(a.out, a.smoke if a.smoke else os.environ.get('FIB_SMOKE', ''))