"""Pass 4: trailing-window (tradable, no look-ahead) swing signals + walk-forward.

Port of reports/fib_swings/_src_snapshot/fib_walkforward.py with the 5 WI-021
accounting fixes:
  Fix 1: stats() applies outcome.notna() to BOTH base and screened sets
         (n_events/n_screened stay on full sets; rates/medians resolved-only).
  Fix 2: events with NaN outcome (bottom: fwd_mfe_pct, top: fwd_mae_pct) get
         grade None, never 'weak'.
  Fix 3: screen_bottom/screen_top (+market) exist BEFORE the events to_csv,
         so trailing_events_w39.csv carries them.
  Fix 4: top-side outcome hit is fwd_mae_pct <= -19.5 (was fwd_mfe_pct >= 19.5).
  Fix 5: rally priors computed on resolved bottoms only (fwd_mfe_pct.notna()).

Frozen (never touch): W=39, GRADE_MED=19.5, GRADE_STRONG=33.9,
CALIB_END='2022-07-01', RSI formula, event definition, 10-bar clustering,
screen thresholds (bottom rsi_f63<42 AND spread15_39<-8; top rsi_f63>58 AND
spread15_39>7). Reads are symbol-sequential (one parquet at a time).

Outputs -> out_dir (default reports/fib_swings):
  trailing_events_w39.csv        per-event records with grade + screen flags
  walkforward_validation.csv     split + per-year stats
  precision_at10.csv             per-period precision@10 stats
  rally_grade_priors.csv         per-ticker: share of strong/med rallies at bottoms
"""
import argparse
import glob
import os

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

W = 39
GRADE_MED, GRADE_STRONG = 19.5, 33.9   # % MFE tercile cut points (w=39, pass 1)
CALIB_END = '2022-07-01'


def rsi(close, n):
    d = close.diff()
    ru = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    rd = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + ru / rd.replace(0, np.nan))


def symbol_from_path(path):
    """('RY', 'CAD') for data/raw_ohlcv/market=CAD/symbol=RY.parquet."""
    sym = os.path.basename(path).replace('.parquet', '')
    if sym.startswith('symbol='):
        sym = sym.split('=', 1)[1]
    parent = os.path.basename(os.path.dirname(path))
    market = parent.split('market=', 1)[1] if 'market=' in parent else ''
    return sym, market


def events_for_symbol(df, sym, market):
    """Snapshot per-file loop (lines 46-97) + market/screen keys + Fix 2."""
    c = df['close'].astype('float64')
    r15, r39, r63 = rsi(c, 15), rsi(c, 39), rsi(c, 63)
    sd3 = c.rolling(3).std(); ma3 = c.rolling(3).mean()
    sd39 = c.rolling(39).std(); ma39 = c.rolling(39).mean()
    bbw_ratio = (4 * sd3 / ma3) / (4 * sd39 / ma39)
    spread = r15 - r39

    low = df['low'].astype('float64'); high = df['high'].astype('float64')
    tmin = low.rolling(W).min(); tmax = high.rolling(W).max()
    nb = (low == tmin).to_numpy()   # new 39d trailing low today
    nh = (high == tmax).to_numpy()  # new 39d trailing high today
    n = len(df)
    close = c.to_numpy()
    # forward 39d MFE / MAE from close
    mfe = np.full(n, np.nan); mae = np.full(n, np.nan)
    fwd = np.full(n, np.nan)
    fh = high.to_numpy(); fl = low.to_numpy()
    for t in range(n - W):
        mfe[t] = fh[t + 1:t + 1 + W].max() / close[t] - 1
        mae[t] = fl[t + 1:t + 1 + W].min() / close[t] - 1
        fwd[t] = close[t + W] / close[t] - 1

    # cluster events: keep first, then require >=10-bar gap
    def cluster(mask):
        idxs = np.where(mask)[0]
        keep = []
        for ix in idxs:
            if not keep or ix - keep[-1] >= 10:
                keep.append(ix)
        return keep

    dates = df['date'].astype(str).to_numpy()
    rows = []
    for ix in cluster(nb):
        pop = mfe[ix] * 100
        # Fix 2: unresolved (NaN outcome) -> grade None, never 'weak'
        grade = None if np.isnan(pop) else (
            'strong' if pop >= GRADE_STRONG else ('med' if pop >= GRADE_MED else 'weak'))
        rows.append({'symbol': sym, 'market': market, 'date': dates[ix],
                     'type': 'bottom',
                     'rsi_f63': r63.iloc[ix], 'spread15_39': spread.iloc[ix],
                     'bbw_ratio': bbw_ratio.iloc[ix],
                     'fwd_mfe_pct': pop, 'fwd_mae_pct': mae[ix] * 100,
                     'fwd_ret_pct': fwd[ix] * 100,
                     'screen_bottom': bool(r63.iloc[ix] < 42 and spread.iloc[ix] < -8),
                     'screen_top': False,
                     'grade': grade})
    for ix in cluster(nh):
        pop = mae[ix] * 100
        # Fix 2: unresolved (NaN outcome) -> grade None, never 'weak'
        grade = None if np.isnan(pop) else (
            'strong' if pop <= -GRADE_STRONG else ('med' if pop <= -GRADE_MED else 'weak'))
        rows.append({'symbol': sym, 'market': market, 'date': dates[ix], 'type': 'top',
                     'rsi_f63': r63.iloc[ix], 'spread15_39': spread.iloc[ix],
                     'bbw_ratio': bbw_ratio.iloc[ix],
                     'fwd_mfe_pct': mfe[ix] * 100, 'fwd_mae_pct': pop,
                     'fwd_ret_pct': fwd[ix] * 100,
                     'screen_bottom': False,
                     'screen_top': bool(r63.iloc[ix] > 58 and spread.iloc[ix] > 7),
                     'grade': grade})
    return rows


def stats(d, side='bottom'):
    """Split/per-year stats. Fix 1: resolved-only rates/medians on BOTH sets
    (counts on full sets). Fix 4: side-correct outcome hit."""
    sc = f'screen_{side}'
    base = d[d.type == side]
    hit = d[d[sc]]
    ocol = 'fwd_mfe_pct' if side == 'bottom' else 'fwd_mae_pct'
    metric = 'mfe>=19.5' if side == 'bottom' else 'mae<=-19.5'
    bres = base[base[ocol].notna()]   # Fix 1: resolved base rows
    hres = hit[hit[ocol].notna()]     # Fix 1: resolved screened rows
    if side == 'bottom':              # Fix 4: outcome hit per side
        b_hit, h_hit = bres[ocol] >= GRADE_MED, hres[ocol] >= GRADE_MED
    else:
        b_hit, h_hit = bres[ocol] <= -GRADE_MED, hres[ocol] <= -GRADE_MED
    return {
        'n_events': len(base), 'n_screened': len(hit),
        'flag_rate': len(hit) / max(len(base), 1),
        'base_rate_medplus': b_hit.mean(),
        'screen_rate_medplus': h_hit.mean() if len(hres) else np.nan,
        'fwd_mfe_base_med': bres.fwd_mfe_pct.median(),
        'fwd_mfe_screened_med': hres.fwd_mfe_pct.median() if len(hres) else np.nan,
        'fwd_ret_base_med': bres.fwd_ret_pct.median(),
        'fwd_ret_screened_med': hres.fwd_ret_pct.median() if len(hres) else np.nan,
        'outcome_metric': metric,
    }


def main(out_dir='reports/fib_swings'):
    files = sorted(glob.glob('data/raw_ohlcv/market=*/*.parquet'))
    keep = None
    smoke = os.environ.get('FIB_SMOKE', '')
    if smoke.strip():  # FIB_SMOKE=AAPL,RY -> keep only those symbols
        keep = {s.strip() for s in smoke.split(',') if s.strip()}
    rows = []
    for f in files:  # symbol-sequential reads
        sym, market = symbol_from_path(f)
        if keep is not None and sym not in keep:
            continue
        df = pq.read_table(f).to_pandas().sort_values('date').reset_index(drop=True)
        if len(df) < 300:
            continue
        rows.extend(events_for_symbol(df, sym, market))
    ev = pd.DataFrame(rows)  # Fix 3: market + screen flags already in rows
    os.makedirs(out_dir, exist_ok=True)
    ev.to_csv(f'{out_dir}/trailing_events_w39.csv', index=False)
    print('events:', len(ev), 'bottoms:', (ev.type == 'bottom').sum(),
          'tops:', (ev.type == 'top').sum(), flush=True)

    out = []
    d = pd.to_datetime(ev.date)
    for period, mask in [('CALIB <2022-07-01', d < CALIB_END),
                         ('EVAL >=2022-07-01', d >= CALIB_END)]:
        out.append({'period': period, 'side': 'bottom', **stats(ev[mask])})
        out.append({'period': period, 'side': 'top', **stats(ev[mask], 'top')})
    ev['year'] = d.dt.year
    for y, g in ev.groupby('year'):
        out.append({'period': str(y), 'side': 'bottom', **stats(g)})
        out.append({'period': str(y), 'side': 'top', **stats(g, 'top')})
    wf = pd.DataFrame(out)
    wf.to_csv(f'{out_dir}/walkforward_validation.csv', index=False)
    print(wf.to_string(index=False), flush=True)

    # precision@10 (bottoms, evaluation period only + full) - unchanged
    p10 = []
    b = ev[(ev.type == 'bottom') & ev.screen_bottom & ev.fwd_mfe_pct.notna()].copy()
    b['date'] = pd.to_datetime(b.date)
    for period, m in [('FULL', np.ones(len(b), bool)),
                      ('EVAL >=2022-07-01', b.date >= CALIB_END)]:
        bb = b[m]
        if not len(bb):
            continue
        top10 = bb.groupby('date').apply(
            lambda g: g.nsmallest(10, 'rsi_f63'), include_groups=False)
        p10.append({
            'period': period, 'n_signal_days': bb.date.nunique(),
            'n_events': len(bb),
            'median_fwd_mfe_all_screened_pct': bb.fwd_mfe_pct.median(),
            'median_fwd_mfe_top10_pct': top10.fwd_mfe_pct.median(),
            'p_medplus_all_screened': (bb.fwd_mfe_pct >= GRADE_MED).mean(),
            'p_medplus_top10': (top10.fwd_mfe_pct >= GRADE_MED).mean(),
            'median_fwd_ret_top10_pct': top10.fwd_ret_pct.median(),
        })
    pd.DataFrame(p10).to_csv(f'{out_dir}/precision_at10.csv', index=False)
    print(pd.DataFrame(p10).to_string(index=False), flush=True)

    # per-ticker rally-grade priors (bottoms) - Fix 5: resolved bottoms only
    bo = ev[(ev.type == 'bottom') & ev.fwd_mfe_pct.notna()]
    priors = bo.groupby(['symbol']).agg(
        n_bottoms=('fwd_mfe_pct', 'count'),
        med_rally_pct=('fwd_mfe_pct', 'median'),
        p_medplus=('fwd_mfe_pct', lambda s: (s >= GRADE_MED).mean()),
        p_strong=('fwd_mfe_pct', lambda s: (s >= GRADE_STRONG).mean()),
        med_fwd_ret=('fwd_ret_pct', 'median')).reset_index()
    priors.to_csv(f'{out_dir}/rally_grade_priors.csv', index=False)
    print('PASS4 DONE', flush=True)
    print('EXIT:0', flush=True)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='Pass-4 walk-forward validation')
    ap.add_argument('--out', default='reports/fib_swings')
    main(ap.parse_args().out)
