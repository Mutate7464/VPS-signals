"""WI-027: point-in-time 3x2 regime labels (trend {up,down,chop} x vol {normal,high}) -> conditional
edge table on CALIB (date < '2022-05-02' hardcoded; EVAL not computed); research ladder stage 1.
Outputs -> out_dir: regime_daily_extended.csv (regime_daily.csv rows + atrp63/vol21/trend/vol_cat/
regime, append-only), regime_conditional_edge.csv (bottom screen per regime x market, 5 contiguous
folds reusing WI-023 group_stats), REGIME_LABELS.md (fold5 callout + VERDICT; prints EXIT:0).
Frozen: 63/126d windows, 0.001 flat-noise, ATR(63)/close, vol21 = std(21-bar log ret) x sqrt(252),
cross-sectional medians, CALIB-frozen cuts, high = BOTH, close = cross-sectional mean (ALL
fallback), symbol-sequential reads, --smoke/FIB_SMOKE, float32, no future data."""
import argparse, glob, os, sys

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # sibling script imports
from fib_regime_overlay import load_bottom_events                # frozen WI-021 loader
from fib_walkforward import symbol_from_path                   # WI-021 symbol/market helper
from fib_trade_labels import group_stats                        # WI-023 fold machinery

CALIB_END = '2022-05-02'                # same 39-day-label embargo as WI-023
N_FOLDS = 5
TREND_LEVELS, VOL_LEVELS = ('up', 'down', 'chop'), ('normal', 'high')
REGIMES = ['%s_%s' % (t, v) for t in TREND_LEVELS for v in VOL_LEVELS]
MARKETS = ('CAD', 'USD', 'ALL')
MEDPLUS = ('med', 'strong')              # grade >= med
EXT_COLS = ['market', 'date', 'r1', 'r1_s5', 'r2', 'n_tickers', 'atrp63', 'vol21', 'trend',
            'vol_cat', 'regime']
EDGE_COLS = (['regime', 'market', 'n_events', 'n_screened', 'screen_rate', 'base_rate_medplus',
              'screen_rate_medplus', 'edge_pp', 'mean_39d_fwd_ret']
             + ['fwd_ret_fold%d_mean' % k for k in range(1, N_FOLDS + 1)] + ['n_folds_pos'])

def trailing_return(close, t, n):
    """close[t]/close[t-n] - 1 (NaN if not computable); touches indices <= t only."""
    if t - n < 0 or close[t] == 0 or not (np.isfinite(close[t - n]) and np.isfinite(close[t])):
        return np.nan
    return float(close[t]) / float(close[t - n]) - 1.0

def trend_category(ret63, ret126):
    """up/down/chop from trailing 63d & 126d returns; flat-noise |ret63| <= 0.001 -> chop."""
    if np.isfinite(ret63) and np.isfinite(ret126) and ret63 > 0 and ret126 > 0 and ret63 > 0.001:
        return 'up'
    if np.isfinite(ret63) and np.isfinite(ret126) and ret63 < 0 and ret126 < 0 and ret63 < -0.001:
        return 'down'
    return 'chop'

def trend_label_at(close, t):
    """Point-in-time trend label at index t (reads close[t-126..t] only)."""
    return trend_category(trailing_return(close, t, 63), trailing_return(close, t, 126))

def trailing_returns(close):
    """Trailing 63d & 126d return arrays, computed per index (point-in-time)."""
    return (np.array([trailing_return(close, t, 63) for t in range(len(close))]),
            np.array([trailing_return(close, t, 126) for t in range(len(close))]))

def wilder_atrp63(h, l, c):
    """Wilder ATR(63)/close per bar (repo atr14 convention, n=63)."""
    cp = np.concatenate(([np.nan], c[:-1]))
    tr = np.maximum.reduce([h - l, np.abs(h - cp), np.abs(l - cp)])
    with np.errstate(divide='ignore', invalid='ignore'):
        return pd.Series(tr).ewm(alpha=1 / 63, adjust=False).mean().to_numpy() / c

def vol21(c):
    """std of 21-bar log returns x sqrt(252) (pandas rolling std)."""
    return (np.log(c).diff().rolling(21).std() * np.sqrt(252.0)).to_numpy()

def cross_section(files, keep=None):
    """Symbol-sequential reads -> per-(market, date) close_mean + atrp63/vol21 medians (+ ALL pool)."""
    frames = []
    for f in files:                     # one parquet at a time
        sym, market = symbol_from_path(f)
        if keep is not None and sym not in keep:
            continue
        df = pq.read_table(f).to_pandas().sort_values('date').reset_index(drop=True)
        if not {'date', 'high', 'low', 'close'} <= set(df.columns):
            continue
        cs = df['close'].astype('float64')
        h, l = (df[k].astype('float64').to_numpy() for k in ('high', 'low'))
        g = pd.DataFrame({'market': market, 'date': df['date'].astype(str).to_numpy(),
                          'close': cs.to_numpy(), 'atrp63': wilder_atrp63(h, l, cs.to_numpy()),
                          'vol21': vol21(cs)}).astype(  # float32 immediately after calculation
            {'close': 'float32', 'atrp63': 'float32', 'vol21': 'float32'})
        frames.append(g)
    if not frames:
        return pd.DataFrame(columns=['market', 'date', 'close_mean', 'atrp63', 'vol21'])
    per = pd.concat(frames, ignore_index=True)   # NaNs skipped by mean/median
    med = lambda by: per.groupby(by, as_index=False).agg(close_mean=('close', 'mean'),
        atrp63=('atrp63', 'median'), vol21=('vol21', 'median'))
    pool = med(['date'])
    pool.insert(0, 'market', 'ALL')
    return pd.concat([med(['market', 'date']), pool], ignore_index=True)

def trend_labels(feat):
    """trend per (market, date) from the market-level close_mean; ALL-pool fallback."""
    allsub = feat[feat['market'] == 'ALL'].sort_values('date', kind='mergesort')
    a63, a126 = trailing_returns(np.asarray(allsub['close_mean'], dtype='float64'))
    fb = dict(zip(allsub['date'].to_numpy(), zip(a63, a126)))
    out = []
    for mk, sub in feat.groupby('market', sort=False):
        sub = sub.sort_values('date', kind='mergesort')
        dts = sub['date'].to_numpy()
        r63, r126 = trailing_returns(np.asarray(sub['close_mean'], dtype='float64'))
        r63 = [x if np.isfinite(x) else fb.get(d, (np.nan, np.nan))[0] for x, d in zip(r63, dts)]
        r126 = [y if np.isfinite(y) else fb.get(d, (np.nan, np.nan))[1] for y, d in zip(r126, dts)]
        out.append(pd.DataFrame({'market': mk, 'date': dts,
                                 'trend': list(map(trend_category, r63, r126))}))
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame(columns=['market', 'date', 'trend'])

def frozen_cuts(daily, market):
    """CALIB (< 2022-05-02) median cut points of atrp63 & vol21, frozen (never updated)."""
    m = (daily['market'] == market) & (pd.to_datetime(daily['date']) < pd.Timestamp(CALIB_END))
    v = daily.loc[m, ['atrp63', 'vol21']].dropna()
    return ({'atrp63': float(v['atrp63'].median()), 'vol21': float(v['vol21'].median())}
            if len(v) else {'atrp63': np.nan, 'vol21': np.nan})

def vol_category(atrp63, vol21v, cuts):
    """'high' iff BOTH atrp63 and vol21 exceed their frozen CALIB medians; else 'normal'."""
    a_cut, v_cut = cuts['atrp63'], cuts['vol21']
    if not all(np.isfinite(x) for x in (atrp63, vol21v, a_cut, v_cut)):
        return 'normal'                 # all other dates (incl. missing data)
    return 'high' if (atrp63 > a_cut and vol21v > v_cut) else 'normal'

def _join_labels(ev, lab):
    """Bottoms + own-market regime label on (market, date); missing label -> chop_normal."""
    if 'type' in ev.columns:
        ev = ev[ev['type'] == 'bottom']
    ev = ev.merge(lab[lab['market'] != 'ALL'][['market', 'date', 'regime']], on=['market', 'date'],
                  how='left')
    ev['regime'] = ev['regime'].fillna('chop_normal')
    return ev

def fold5_summary(ev, lab):
    """fold5 = 5th contiguous equal-count block of pooled CALIB screened resolved bottoms."""
    ev = _join_labels(ev, lab)
    m = (np.asarray(ev['screen_bottom'], dtype=bool) & ev['fwd_mfe_pct'].notna().to_numpy()
         & (pd.to_datetime(ev['date']) < pd.Timestamp(CALIB_END)).to_numpy())
    ev = ev[m].sort_values('date', kind='mergesort')
    if not len(ev):
        return None, None, {}
    b = ev.iloc[np.array_split(np.arange(len(ev)), N_FOLDS)[-1]]
    return b['date'].min(), b['date'].max(), {k: int(v) for k, v in b['regime'].value_counts().items()}

def verdict_pass(edge, fold5_regimes):
    """PASS iff >=1 regime x market fold-stable (n_folds_pos==N_FOLDS, screened events) AND
    fold5 isolated to identifiable regime(s): non-empty proper subset of regimes seen."""
    if not len(edge):
        return False
    stable = edge[np.isfinite(edge['n_folds_pos']) & (edge['n_folds_pos'] == N_FOLDS)]
    hit, seen = set(fold5_regimes), set(edge.loc[edge['n_screened'] > 0, 'regime'])
    return bool(len(stable)) and len(hit) > 0 and hit < seen

def edge_table(ev, lab):
    """Conditional edge rows per regime x market on CALIB bottoms (own-market labels);
    base = all-regime share of this market's resolved CALIB bottoms with grade >= med."""
    ev = _join_labels(ev, lab)
    ev = ev[pd.to_datetime(ev['date']) < pd.Timestamp(CALIB_END)].reset_index(drop=True)
    base = {mk: float(ev.loc[ev['fwd_mfe_pct'].notna() & (ev['market'] == mk if mk != 'ALL'
        else np.ones(len(ev), bool)), 'grade'].isin(MEDPLUS).mean()) for mk in MARKETS}
    rows = []
    for mk in MARKETS:
        mev = ev if mk == 'ALL' else ev[ev['market'] == mk]
        for rg in REGIMES:
            g = mev[mev['regime'] == rg]
            scr = g[np.asarray(g['screen_bottom'], dtype=bool)]
            sres = scr[scr['fwd_mfe_pct'].notna()]      # resolved screened only
            srm = float(sres['grade'].isin(MEDPLUS).mean()) if len(sres) else np.nan
            gg = sres.rename(columns={'fwd_ret_pct': 'ret', 'grade': 'reason'})[['date', 'ret', 'reason']]
            gs = group_stats(gg, 'CALIB')               # WI-023 reuse; n==0 -> NaN folds
            rows.append({'regime': rg, 'market': mk, 'n_events': int(len(g)), 'n_screened': int(len(scr)),
                         'screen_rate': len(scr) / len(g) if len(g) else np.nan,
                         'base_rate_medplus': base[mk], 'screen_rate_medplus': srm,
                         'edge_pp': (srm - base[mk]) * 100.0, 'mean_39d_fwd_ret': gs['mean_ret'],
                         'n_folds_pos': gs['n_folds_pos'],
                         **{'fwd_ret_fold%d_mean' % k: gs['fold%d_mean' % k]
                            for k in range(1, N_FOLDS + 1)}})
    return pd.DataFrame(rows, columns=EDGE_COLS).astype(  # float32 output
        {c: 'float32' for c in EDGE_COLS if c not in ('regime', 'market', 'n_events',
                                                      'n_screened')})

def main(out_dir='reports/fib_swings', smoke=None):
    """Full chain: raw OHLCV (symbol-sequential; --smoke/FIB_SMOKE) -> extended daily -> edge."""
    os.makedirs(out_dir, exist_ok=True)
    keep = {s.strip() for s in (smoke or os.environ.get('FIB_SMOKE', '') or '').split(',')
            if s.strip()} or None
    pj = os.path.join(out_dir, 'regime_daily.csv')
    daily = (pd.read_csv(pj) if os.path.exists(pj) else pd.DataFrame(
        columns=['market', 'date', 'r1', 'r1_s5', 'r2', 'n_tickers']))
    feat = cross_section(sorted(glob.glob('data/raw_ohlcv/market=*/*.parquet')), keep)
    ext = daily.merge(feat, on=['market', 'date'], how='outer')
    ext = ext.merge(trend_labels(feat), on=['market', 'date'], how='outer')
    vout = [pd.DataFrame({'market': mk, 'date': sub['date'].to_numpy(), 'vol_cat':
                          [vol_category(a, v, frozen_cuts(feat, mk)) for a, v in
                           zip(sub['atrp63'], sub['vol21'])]})
            for mk, sub in feat.groupby('market', sort=False)]
    vlab = pd.concat(vout, ignore_index=True) if vout else pd.DataFrame(columns=['market', 'date', 'vol_cat'])
    ext = ext.merge(vlab, on=['market', 'date'], how='outer')
    ext['trend'] = ext['trend'].fillna('chop')         # 'everything else' defaults
    ext['vol_cat'] = ext['vol_cat'].fillna('normal')   # 'all other dates'
    ext['regime'] = ext['trend'] + '_' + ext['vol_cat']
    ext[['atrp63', 'vol21']] = ext[['atrp63', 'vol21']].astype('float32')
    ext = ext.sort_values(['market', 'date'], kind='mergesort').reset_index(drop=True)
    ext = ext.reindex(columns=EXT_COLS)   # drop helper cols; existing r1/r1_s5/r2 untouched
    ext.to_csv(os.path.join(out_dir, 'regime_daily_extended.csv'), index=False)
    ev = load_bottom_events(out_dir)
    lab = ext[['market', 'date', 'regime']]
    edge = edge_table(ev, lab)
    edge.to_csv(os.path.join(out_dir, 'regime_conditional_edge.csv'), index=False)
    d0, d1, f5r = fold5_summary(ev, lab)
    fi = lambda x: '-' if not np.isfinite(x) else str(int(x))
    lines = ['# REGIME LABELS (WI-027): trend {up,down,chop} x vol {normal,high}', '',
             'Bottom screen per regime on CALIB (date < %s; EVAL not computed); pooled '
             '(ALL) is the headline, per-market rows are descriptive.' % CALIB_END, '',
             '| regime | market | n_events | screened rate | edge_pp | n_folds_pos |',
             '|---|---|---|---|---|---|']
    lines += ['| %s | %s | %d | %.4f | %.4f | %s |' % (r['regime'], r['market'], r['n_events'],
              r['screen_rate'], r['edge_pp'], fi(r['n_folds_pos'])) for _, r in edge.iterrows()]
    lines += ['', '## fold5 callout (the fatal fold from the overnight chain; '
                  'expected range 2020-01 -> 2022-04)']
    if d0 is not None:
        lines += ['- fold5 (5th contiguous equal-count block of pooled CALIB screened '
                  'resolved bottoms): %s -> %s' % (d0, d1), '- fold5 regime(s): %s'
                  % ', '.join('%s (n=%d)' % kv for kv in sorted(f5r.items()))]
        pooled = edge[edge['market'] == 'ALL']
        for rg in sorted(f5r):
            nf = float(pooled.loc[pooled['regime'] == rg, 'n_folds_pos'].iloc[0])
            lines.append('- %s fold-stability (pooled): n_folds_pos=%s -> %s' % (rg, fi(nf),
                         'FAILS' if not (np.isfinite(nf) and nf == N_FOLDS) else 'holds'))
        stable = edge[np.isfinite(edge['n_folds_pos']) & (edge['n_folds_pos'] == N_FOLDS)]
        lines.append('- fold-stable rows (n_folds_pos==%d): %s' % (N_FOLDS, '; '.join(
            '%s/%s' % (r['regime'], r['market']) for _, r in stable.iterrows()) or 'none'))
    v = 'PASS' if verdict_pass(edge, f5r) else 'FAIL'
    lines.append('VERDICT: %s' % v)
    open(os.path.join(out_dir, 'REGIME_LABELS.md'), 'w').write('\n'.join(lines) + '\n')
    print('rows ext=%d edge=%d | VERDICT: %s' % (len(ext), len(edge), v), flush=True)
    print('EXIT:0', flush=True)

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='WI-027 fib regime labels (3x2) -> conditional edge')
    ap.add_argument('--out', default='reports/fib_swings')
    ap.add_argument('--smoke', default=None, help='symbols csv (fallback: FIB_SMOKE env)')
    a = ap.parse_args()
    main(a.out, a.smoke)
