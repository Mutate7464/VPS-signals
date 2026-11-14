"""WI-023: first-touch trade labels + exit-policy grid for fib trailing bottoms.

Simulates a fixed 32-policy grid (target x stop x max_days x entry) on every
trailing-bottom event from reports/fib_swings/trailing_events_w39.csv against
raw OHLCV, one symbol at a time (symbol-sequential parquet reads). Writes
per-event trade labels, a CALIB/EVAL policy grid, and chooses ONE policy from
CALIB screened data only (EVAL is never used for choosing). float32 returns.

Frozen (never touch): 25 bps cost, CALIB < '2022-05-02' (39-day-label embargo),
EVAL >= '2022-07-01', grid = target {0.10,0.15} x stop {0.05,0.08,0.10,atr1.5}
x max_days {20,39} x entry {close,next_open}.

Outputs -> out_dir (default reports/fib_swings):
  trade_labels_w39.parquet   one row per (bottom event, policy), ret float32
  exit_policy_grid.csv       policy x period x market x set summary stats
  exit_policy_choice.json    the single chosen policy (or NO_POLICY_CLEARS)
"""
import argparse
import json
import os

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

COST = 0.0025                     # 25 bps round-trip
EMBARGO_START = '2022-05-02'      # CALIB = date < '2022-05-02' (39-day label)
EVAL_START = '2022-07-01'         # EVAL = date >= '2022-07-01'
EVENTS_CSV = 'reports/fib_swings/trailing_events_w39.csv'
N_FOLDS = 5
TARGETS = [('t10', 0.10), ('t15', 0.15)]
STOPS = [('s5', 0.05), ('s8', 0.08), ('s10', 0.10), ('satr', 'atr1.5')]
STOP_RANK = {'s5': 0, 's8': 1, 's10': 2, 'satr': 3}   # tie-break: smaller stop
MAX_DAYS = [('d20', 20), ('d39', 39)]
ENTRIES = ['close', 'next_open']
POLICIES = [                        # target x stop x max_days x entry (32)
    (f'{tk}_{sk}_{dk}_{em}', tv, sv, dv, em)
    for tk, tv in TARGETS for sk, sv in STOPS
    for dk, dv in MAX_DAYS for em in ENTRIES]
HIT_REASONS = ['target', 'target_gap']
COLS = ['symbol', 'market', 'date', 'screen_bottom', 'policy', 'ret', 'reason',
        'days']
GRID_COLS = ['policy', 'period', 'market', 'set', 'n', 'hit_rate', 'mean_ret',
             'median_ret', 'p10_ret', 'max_consec_losses', 'fold1_mean',
             'fold2_mean', 'fold3_mean', 'fold4_mean', 'fold5_mean',
             'n_folds_pos']


def simulate(o, h, l, c, i, entry, tgt_pct, stop_px, max_days, entry_mode):
    """First-touch exit sim from event bar i -> (ret, reason, days)."""
    T = entry * (1 + tgt_pct)
    S = stop_px
    if i + max_days >= len(c):
        return (np.nan, 'unresolved', 0)
    for j in range(i + 1, i + max_days + 1):
        if entry_mode == 'close' or j > i + 1:      # gap rule off on bar i+1
            if o[j] <= S:
                return (o[j] / entry - 1 - COST, 'stop_gap', j - i)
            if o[j] >= T:
                return (o[j] / entry - 1 - COST, 'target_gap', j - i)
        if l[j] <= S and h[j] >= T:                  # conservative: stop wins
            return (S / entry - 1 - COST, 'stop_tie', j - i)
        if l[j] <= S:
            return (S / entry - 1 - COST, 'stop', j - i)
        if h[j] >= T:
            return (T / entry - 1 - COST, 'target', j - i)
    return (c[i + max_days] / entry - 1 - COST, 'time', max_days)


def atr14(h, l, c):
    """Wilder ATR14: TR=max(h-l, |h-c_prev|, |l-c_prev|); ewm(alpha=1/14)."""
    cp = np.concatenate(([np.nan], c[:-1]))
    tr = np.maximum.reduce([h - l, np.abs(h - cp), np.abs(l - cp)])
    return pd.Series(tr).ewm(alpha=1 / 14, adjust=False).mean().to_numpy()


def labels_for_symbol(sym, market, g, o, h, l, c, dmap, a14):
    """One row per (bottom event, policy) for this symbol's events."""
    rows = []
    n = len(c)
    for date, sb in zip(g['date'].to_numpy(), g['screen_bottom'].to_numpy()):
        i = dmap.get(date)
        if i is None:
            continue
        for pid, tv, sv, dv, em in POLICIES:
            entry = c[i] if em == 'close' else (o[i + 1] if i + 1 < n else np.nan)
            stop_px = entry - 1.5 * a14[i] if sv == 'atr1.5' else entry * (1 - sv)
            ret, reason, days = simulate(o, h, l, c, i, entry, tv, stop_px, dv, em)
            rows.append((sym, market, date, bool(sb), pid, ret, reason, days))
    return rows


def group_stats(g, period):
    """Resolved-only group stats; folds/n_folds_pos on CALIB only."""
    n = len(g)
    if n == 0:
        out = {'n': 0, 'hit_rate': np.nan, 'mean_ret': np.nan,
               'median_ret': np.nan, 'p10_ret': np.nan,
               'max_consec_losses': 0, 'n_folds_pos': np.nan}
        folds = [np.nan] * N_FOLDS
    else:
        gs = g.sort_values('date', kind='mergesort')   # stable by date
        rets = gs['ret'].to_numpy(dtype='float64')
        consec = cur = 0
        for v in rets:                                 # runs of ret < 0
            cur = cur + 1 if v < 0 else 0
            consec = max(consec, cur)
        out = {'n': n,
               'hit_rate': float(gs['reason'].isin(HIT_REASONS).mean()),
               'mean_ret': float(rets.mean()),
               'median_ret': float(np.median(rets)),
               'p10_ret': float(np.percentile(rets, 10)),
               'max_consec_losses': consec, 'n_folds_pos': np.nan}
        if period == 'CALIB':       # 5 contiguous equal-count date blocks
            folds = [float(rets[b].mean()) if len(b) else np.nan
                     for b in np.array_split(np.arange(n), N_FOLDS)]
            out['n_folds_pos'] = int(sum(m > 0 for m in folds))
        else:
            folds = [np.nan] * N_FOLDS
    for k, m in enumerate(folds, 1):
        out[f'fold{k}_mean'] = m
    return out


def main(out_dir='reports/fib_swings'):
    ev = pd.read_csv(EVENTS_CSV, keep_default_na=False, na_values=[''])
    ev = ev[ev['type'] == 'bottom'][['symbol', 'market', 'date',
                                     'screen_bottom']].copy()
    ev['screen_bottom'] = ev['screen_bottom'].apply(
        lambda v: str(v).strip().lower() == 'true')
    ev['date'] = ev['date'].astype(str).str.slice(0, 10)
    smoke = os.environ.get('FIB_SMOKE', '')
    if smoke.strip():          # FIB_SMOKE=AAPL,RY -> keep only those symbols
        ev = ev[ev['symbol'].isin({s.strip() for s in smoke.split(',')
                                   if s.strip()})]
    os.makedirs(out_dir, exist_ok=True)

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
        rows.extend(labels_for_symbol(sym, market, g, o, h, l, c, dmap,
                                      atr14(h, l, c)))
    lab = pd.DataFrame(rows, columns=COLS)
    lab['ret'] = lab['ret'].astype('float32')
    lab['days'] = lab['days'].astype('int16')
    lab['screen_bottom'] = lab['screen_bottom'].astype(bool)
    lab['reason'] = lab['reason'].astype('category')
    lab.to_parquet(f'{out_dir}/trade_labels_w39.parquet', index=False)
    print('trade_labels rows:', len(lab), 'policies:', len(POLICIES), flush=True)

    grid_rows = []
    for pid, *_ in POLICIES:
        p = lab[lab['policy'] == pid]
        for period in ('CALIB', 'EVAL'):
            pp = (p[p['date'] < EMBARGO_START] if period == 'CALIB'
                  else p[p['date'] >= EVAL_START])
            for mkt in ('CAD', 'USD', 'ALL'):
                pm = pp if mkt == 'ALL' else pp[pp['market'] == mkt]
                for sname in ('all', 'screened'):
                    g = pm if sname == 'all' else pm[pm['screen_bottom']]
                    g = g[g['ret'].notna()]          # resolved rows only
                    grid_rows.append({'policy': pid, 'period': period,
                                      'market': mkt, 'set': sname,
                                      **group_stats(g, period)})
    grid = pd.DataFrame(grid_rows, columns=GRID_COLS)
    grid.to_csv(f'{out_dir}/exit_policy_grid.csv', index=False)
    print('grid rows:', len(grid), flush=True)

    sub = grid[(grid['period'] == 'CALIB') & (grid['market'] == 'ALL')
               & (grid['set'] == 'screened')]
    elig = sub[(sub['mean_ret'] >= 0.005) & (sub['n_folds_pos'] == N_FOLDS)]
    if len(elig):
        elig = elig.copy()
        elig['rank'] = elig['policy'].str.split('_').str[1].map(STOP_RANK)
        best = elig.sort_values(['mean_ret', 'rank'],
                                ascending=[False, True]).iloc[0]
        choice = {'policy': best['policy'],
                  'reason': 'max calib mean_ret among eligible '
                            '(mean_ret>=0.005, n_folds_pos==5)',
                  'calib_mean_ret': float(best['mean_ret'])}
    else:
        choice = {'policy': None, 'reason': 'NO_POLICY_CLEARS',
                  'calib_mean_ret': None}
    with open(f'{out_dir}/exit_policy_choice.json', 'w') as f:
        json.dump(choice, f, indent=2)
    print('exit policy choice:', choice['policy'], flush=True)
    print('EXIT:0', flush=True)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='WI-023 fib exit-policy grid')
    ap.add_argument('--out', default='reports/fib_swings')
    main(ap.parse_args().out)
