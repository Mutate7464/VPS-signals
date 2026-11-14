"""Pass 5a: event feature table on fib bottom events (WI-024).

Reads <out>/trailing_events_w39.csv (all bottoms; keep_default_na=False,
na_values=['']) and raw OHLCV per symbol, computes the fixed feature list,
writes <out>/event_features.parquet. Features cast float32 immediately.
Frozen: CALIB_END_PRIOR='2022-05-02', GRADE_MED=19.5, shrink (k+10g)/(n+10).
"""
import argparse
import glob
import os

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

try:
    from fib_walkforward import rsi, symbol_from_path
except ImportError:  # imported as scripts.fib_event_features
    from scripts.fib_walkforward import rsi, symbol_from_path

CALIB_END_PRIOR = '2022-05-02'
GRADE_MED = 19.5
KEYS = ['symbol', 'market', 'date']
FEATURES = ['rsi_f63', 'spread15_39', 'bbw_ratio', 'rsi24_39', 'rsi15_slope5',
            'dd63', 'dd63_days', 'days_since_prev_bottom', 'mom_12_1', 'vol21',
            'atrp63', 'r1_s5', 'r2', 'prior_p_medplus', 'is_usd', 'screen_bottom']


def prior_p_medplus(ev, calib_end=CALIB_END_PRIOR, grade_med=GRADE_MED):
    """Per-symbol share of fwd_mfe_pct >= grade_med on CALIB (date < calib_end)
    resolved bottoms, shrunk (k + 10*g)/(n + 10), g = global CALIB share."""
    d = ev[ev['type'] == 'bottom'] if 'type' in ev.columns else ev
    cal = d[(pd.to_datetime(d['date']) < pd.Timestamp(calib_end))
            & d['fwd_mfe_pct'].notna()]
    if not len(cal):
        return pd.Series(dtype='float32')
    g = float((cal['fwd_mfe_pct'] >= grade_med).mean())
    n = cal.groupby('symbol').size()
    k = cal[cal['fwd_mfe_pct'] >= grade_med].groupby('symbol').size()
    k = k.reindex(n.index, fill_value=0)
    return ((k + 10 * g) / (n + 10)).astype('float32')


def symbol_features(df):
    """Indicator frame per symbol (rsi imported from fib_walkforward)."""
    c = df['close'].astype('float64')
    h = df['high'].astype('float64')
    l = df['low'].astype('float64')
    r15 = rsi(c, 15)
    out = pd.DataFrame(index=df.index)
    out['rsi24_39'] = rsi(c, 24) - rsi(c, 39)
    out['rsi15_slope5'] = r15 - r15.shift(5)
    out['dd63'] = c / c.rolling(63).max() - 1
    out['dd63_days'] = c.rolling(63).apply(
        lambda a: len(a) - 1 - int(np.argmax(a[::-1])), raw=True)
    out['mom_12_1'] = c.shift(21) / c.shift(252) - 1
    out['vol21'] = np.log(c).diff().rolling(21).std() * np.sqrt(252)
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()],
                   axis=1).max(axis=1)
    out['atrp63'] = tr.ewm(alpha=1 / 63, adjust=False).mean() / c
    return out


def main(out_dir='reports/fib_swings'):
    ev = pd.read_csv(f'{out_dir}/trailing_events_w39.csv',
                     keep_default_na=False, na_values=[''])
    ev = ev[ev['type'] == 'bottom'].copy()
    ev['date'] = ev['date'].astype(str)
    keep = None
    smoke = os.environ.get('FIB_SMOKE', '').strip()
    if smoke:  # FIB_SMOKE=AAPL,RY -> keep only those symbols
        keep = {s.strip() for s in smoke.split(',') if s.strip()}
    paths = {}
    for f in sorted(glob.glob('data/raw_ohlcv/market=*/*.parquet')):
        sym, mkt = symbol_from_path(f)
        paths[(sym, mkt)] = f
    prior = prior_p_medplus(ev)
    reg = pd.read_csv(f'{out_dir}/regime_daily.csv')
    reg['date'] = reg['date'].astype(str)
    regcols = [c for c in ('market', 'date', 'r1_s5', 'r2') if c in reg.columns]
    rows = []
    for (sym, mkt), g in ev.groupby(['symbol', 'market'], sort=False):
        if keep is not None and sym not in keep:
            continue
        f = paths.get((sym, mkt))
        if f is None:
            continue
        df = pq.read_table(f).to_pandas().sort_values('date').reset_index(drop=True)
        feats = symbol_features(df)
        dstr = df['date'].astype(str).to_numpy()
        pos = {d: i for i, d in enumerate(dstr)}
        gd = g.sort_values('date')
        prev_pos = None
        for _, erow in gd.iterrows():
            d = str(erow['date'])
            p = pos.get(d)
            if p is None:
                continue
            row = feats.iloc[p].to_dict()
            row['days_since_prev_bottom'] = (
                float(p - prev_pos) if prev_pos is not None else np.nan)
            for col in ('rsi_f63', 'spread15_39', 'bbw_ratio', 'screen_bottom'):
                row[col] = erow[col]
            row.update(symbol=sym, market=mkt, date=d)
            rows.append(row)
            prev_pos = p
    ft = pd.DataFrame(rows)
    ft['prior_p_medplus'] = ft['symbol'].map(prior)
    ft['is_usd'] = (ft['market'].str.upper() == 'USD').astype('int8')
    if len(ft):
        ft = ft.merge(reg[regcols], on=['market', 'date'], how='left')
        sb = ft['screen_bottom']
        if sb.dtype == object:
            ft['screen_bottom'] = sb.map({True: 1, 'True': 1, False: 0, 'False': 0})
        for col in FEATURES:
            if col not in ft.columns:
                ft[col] = np.nan
        ft[FEATURES] = ft[FEATURES].astype('float32')
        ft = ft[KEYS + FEATURES]
    os.makedirs(out_dir, exist_ok=True)
    ft.to_parquet(f'{out_dir}/event_features.parquet', index=False)
    print('event_features rows:', len(ft), flush=True)
    print('EXIT:0', flush=True)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='WI-024 event feature table')
    ap.add_argument('--out', default='reports/fib_swings')
    main(ap.parse_args().out)