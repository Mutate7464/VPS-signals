"""WI-027b: unsupervised regime states (sklearn GaussianMixture, 3 & 4 components) with soft
state probabilities as downstream ML features, compared against WI-027's rule-based labels.
Frozen: CALIB-only fit (date < 2022-05-02), EVAL predicted once with the frozen model; one
pooled GMM (market ignored; per-market rows descriptive); features [r1, r1_s5, r2, ret63,
ret126, realized_vol63] float32, standardized (scaler fit on CALIB only) — ret63/ret126 =
63/126-trading-day log returns, realized_vol63 = std of 63-bar log returns x sqrt(252), on
cross_section()'s per-(market, date) close series (reused from fib_regime_labels; no future
data); outputs -> out_dir: regime_daily_soft.csv (extended columns + gmm probs/labels,
append-only) + GMM_STATES.md (characterization SUGGESTIONS ONLY, per-state edge via WI-023
group_stats, fold5 callout, WI-027 comparison, VERDICT, EXIT:0); no hmmlearn; no live trading."""
import argparse, glob, os, sys

import numpy as np
import pandas as pd
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # sibling script imports
from fib_regime_labels import CALIB_END, EXT_COLS, MARKETS, MEDPLUS, N_FOLDS, cross_section
from fib_regime_overlay import load_bottom_events
from fib_trade_labels import group_stats

RAW_GLOB = 'data/raw_ohlcv/market=*/*.parquet'    # data_dir constant (PM-fixed WI-027 pattern)
FEATURES = ['r1', 'r1_s5', 'r2', 'ret63', 'ret126', 'realized_vol63']
N_COMPS = (3, 4)
NA_STATE = 'na'                    # bottoms with no GMM label (incomplete features) — not a state
SUGGEST = {('bull', 'low'): 'calm bull', ('bull', 'high'): 'volatile bull',
           ('bear', 'low'): 'calm bear', ('bear', 'high'): 'volatile bear',
           ('flat', 'low'): 'calm chop', ('flat', 'high'): 'volatile chop'}
EDGE_COLS = (['state', 'market', 'n_events', 'n_screened', 'screen_rate', 'base_rate_medplus',
              'screen_rate_medplus', 'edge_pp', 'mean_39d_fwd_ret']
             + ['fwd_ret_fold%d_mean' % k for k in range(1, N_FOLDS + 1)] + ['n_folds_pos'])

def market_return_features(feat):
    """ret63/ret126 (63/126-trading-day log returns) + realized_vol63 (std of 63-bar log returns
    times sqrt(252)) per (market, date) on cross_section close series; float32."""
    out = []
    for mk, sub in feat.groupby('market', sort=False):
        sub = sub.sort_values('date', kind='mergesort')
        with np.errstate(divide='ignore', invalid='ignore'):
            lr = np.log(pd.Series(sub['close_mean'].astype('float64').to_numpy()))
            r63, r126, vol63 = lr - lr.shift(63), lr - lr.shift(126), \
                lr.diff().rolling(63).std() * np.sqrt(252.0)
        out.append(pd.DataFrame({'market': mk, 'date': sub['date'].to_numpy(),
                                 'ret63': r63.to_numpy(), 'ret126': r126.to_numpy(),
                                 'realized_vol63': vol63.to_numpy()}).astype(
            {'ret63': 'float32', 'ret126': 'float32', 'realized_vol63': 'float32'}))
    return (pd.concat(out, ignore_index=True) if out else
            pd.DataFrame(columns=['market', 'date'] + FEATURES[3:]))

def fit_gmm(X, n_components, random_state=0):
    """Blueprint GMM: GaussianMixture(random_state=0, n_init=10, covariance_type='full')."""
    return GaussianMixture(n_components=n_components, random_state=random_state, n_init=10,
                           covariance_type='full').fit(X)

def gmm_states(daily):
    """Standardize FEATURES (CALIB-only scaler), fit pooled GMM-3/GMM-4 on CALIB, predict soft
    probs + argmax labels ONCE for every complete row (CALIB + EVAL) with the frozen models."""
    X = daily[FEATURES].astype('float32')
    calib = (pd.to_datetime(daily['date']) < pd.Timestamp(CALIB_END)).to_numpy()
    ok = X.notna().all(axis=1).to_numpy()
    fit = ok & calib
    if not fit.any():
        raise ValueError('no complete CALIB feature rows for the GMM fit')
    scaler = StandardScaler().fit(X[fit].to_numpy('float32'))
    Z = np.full((len(daily), len(FEATURES)), np.nan, dtype='float32')
    Z[ok] = scaler.transform(X[ok].to_numpy('float32')).astype('float32')
    for k in N_COMPS:
        P = fit_gmm(Z[fit], k).predict_proba(Z[ok]).astype('float32')
        probs = np.full((len(daily), k), np.nan, dtype='float32')
        probs[ok] = P
        daily[['gmm%d_s%d_prob' % (k, j) for j in range(k)]] = probs
        lab = np.full(len(daily), np.nan)
        lab[ok] = P.argmax(axis=1)
        daily['gmm%d_label' % k] = lab
    return daily

def state_characterization(daily, k):
    """CALIB-only per-state raw-feature means + n_dates + SUGGESTIONS ONLY name (bull/bear/flat
    from mean ret63; vol vs CALIB median realized_vol63)."""
    lab = 'gmm%d_label' % k
    sub = daily[(pd.to_datetime(daily['date']) < pd.Timestamp(CALIB_END)).to_numpy()
                & daily[lab].notna().to_numpy()]
    med = float(sub['realized_vol63'].median()) if len(sub) else np.nan
    rows = []
    for s in range(k):
        g = sub[sub[lab] == s]
        m = {f: (float(g[f].mean()) if len(g) else np.nan) for f in FEATURES}
        key = (('bull' if m['ret63'] > 0 else 'bear' if m['ret63'] < 0 else 'flat'),
               'low' if np.isfinite(m['realized_vol63']) and np.isfinite(med)
               and m['realized_vol63'] <= med else 'high')
        rows.append({'state': 's%d' % s, 'n_dates': int(len(g)), **m, 'suggestion': SUGGEST[key]})
    return pd.DataFrame(rows)

def join_states(ev, daily, label_col):
    """Bottoms (type filter like WI-027) + own-market GMM state on (market, date); none -> NA_STATE."""
    if 'type' in ev.columns:
        ev = ev[ev['type'] == 'bottom']
    ev = ev.merge(daily.loc[daily['market'] != 'ALL', ['market', 'date', label_col]],
                  on=['market', 'date'], how='left')
    ev['state'] = ev[label_col].map(lambda x: NA_STATE if pd.isna(x) else 's%d' % int(x))
    return ev

def state_edge_table(ev, daily, label_col, states):
    """Conditional edge per state x market on CALIB bottoms (own-market states) — same computation
    and format as WI-027's edge_table, GMM states instead of regimes."""
    ev = join_states(ev, daily, label_col)
    ev = ev[(pd.to_datetime(ev['date']) < pd.Timestamp(CALIB_END)).to_numpy()].reset_index(drop=True)
    res = ev['fwd_mfe_pct'].notna().to_numpy()
    base = {mk: float(ev.loc[res & (np.ones(len(ev), bool) if mk == 'ALL' else
        (ev['market'] == mk).to_numpy()), 'grade'].isin(MEDPLUS).mean()) for mk in MARKETS}
    order = list(states) + ([NA_STATE] if (ev['state'] == NA_STATE).any() else [])
    rows = []
    for mk in MARKETS:
        mev = ev if mk == 'ALL' else ev[ev['market'] == mk]
        for st in order:
            g = mev[mev['state'] == st]
            scr = g[np.asarray(g['screen_bottom'], dtype=bool)]
            sres = scr[scr['fwd_mfe_pct'].notna()]      # resolved screened only
            srm = float(sres['grade'].isin(MEDPLUS).mean()) if len(sres) else np.nan
            gg = sres.rename(columns={'fwd_ret_pct': 'ret', 'grade': 'reason'})[['date', 'ret', 'reason']]
            gs = group_stats(gg, 'CALIB')               # WI-023 reuse; n==0 -> NaN folds
            rows.append({'state': st, 'market': mk, 'n_events': int(len(g)),
                         'n_screened': int(len(scr)),
                         'screen_rate': len(scr) / len(g) if len(g) else np.nan,
                         'base_rate_medplus': base[mk], 'screen_rate_medplus': srm,
                         'edge_pp': (srm - base[mk]) * 100.0, 'mean_39d_fwd_ret': gs['mean_ret'],
                         'n_folds_pos': gs['n_folds_pos'], **{'fwd_ret_fold%d_mean' % j:
                         gs['fold%d_mean' % j] for j in range(1, N_FOLDS + 1)}})
    return pd.DataFrame(rows, columns=EDGE_COLS).astype(
        {c: 'float32' for c in EDGE_COLS if c not in ('state', 'market', 'n_events', 'n_screened')})

def fold5_states(ev, daily, label_col):
    """fold5 = 5th contiguous equal-count block of pooled CALIB screened resolved bottoms (same
    as WI-027); returns (d0, d1, {state: n}) with own-market states."""
    ev = join_states(ev, daily, label_col)
    m = (np.asarray(ev['screen_bottom'], dtype=bool) & ev['fwd_mfe_pct'].notna().to_numpy()
         & (pd.to_datetime(ev['date']) < pd.Timestamp(CALIB_END)).to_numpy())
    ev = ev[m].sort_values('date', kind='mergesort')
    if not len(ev):
        return None, None, {}
    b = ev.iloc[np.array_split(np.arange(len(ev)), N_FOLDS)[-1]]
    return b['date'].min(), b['date'].max(), {s: int(v) for s, v in b['state'].value_counts().items()}

def stable_states(edge):
    """Pooled-ALL fold-stable states (n_folds_pos==N_FOLDS); NA_STATE is never a state."""
    pooled = edge[edge['market'] == 'ALL']
    return {s for s in pooled.loc[np.isfinite(pooled['n_folds_pos'])
            & (pooled['n_folds_pos'] == N_FOLDS), 'state'] if s != NA_STATE}

def fold5_isolated(stable, fold5_counts):
    """True iff a majority of fold5 bottoms fall in states that FAIL (outside the stable set)."""
    n5 = sum(fold5_counts.values())
    return n5 > 0 and sum(fold5_counts.get(s, 0) for s in stable) * 2 < n5

def gmm_verdict(edges, fold5_counts):
    """PASS iff for the 3- OR the 4-state GMM: >=1 state fold-stable on pooled ALL AND fold5
    isolated; FAIL otherwise (EXIT:0 printed regardless — descriptive)."""
    return 'PASS' if any(bool(stable_states(e)) and fold5_isolated(stable_states(e), c)
                         for e, c in zip(edges, fold5_counts)) else 'FAIL'

def states_md(daily, edges, f5s, verdict):
    """GMM_STATES.md lines: characterization (SUGGESTIONS ONLY) + edge tables + fold5 callout
    + WI-027 comparison + VERDICT."""
    fi = lambda x: '-' if x is None or not np.isfinite(x) else str(int(x))
    lines = ['# GMM STATES (WI-027b): unsupervised GMM (3 & 4 components) soft states', '',
             'GaussianMixture(random_state=0, n_init=10, covariance_type=full), sklearn only '
             '(no hmmlearn); fit on CALIB (date < %s) pooled rows (market ignored; per-market '
             'rows descriptive); features %s, float32, standardized (scaler fit on CALIB only);'
             ' EVAL predicted once with the frozen model.' % (CALIB_END, ', '.join(FEATURES)), '']
    for k, edge in zip(N_COMPS, edges):
        lines += ['## %d-state GMM' % k, '', '### Per-state characterization (CALIB dates '
                  'only; names are SUGGESTIONS ONLY — downstream stages use the raw '
                  'probability vector, never the name)', '', '| state | n_dates | %s | '
                  'suggestion |' % ' | '.join('mean %s' % f for f in FEATURES),
                  '|' + '---|' * (len(FEATURES) + 3)]
        for _, r in state_characterization(daily, k).iterrows():
            lines.append('| %s | %d | %s | %s |' % (r['state'], int(r['n_dates']),
                ' | '.join('%.6f' % float(r[f]) for f in FEATURES), r['suggestion']))
        lines += ['', '### Per-state conditional edge (CALIB bottoms, own-market states; '
                  'same format as WI-027 REGIME_LABELS.md; pooled ALL is the headline)', '',
                  '| state | market | n_events | screened rate | edge_pp | n_folds_pos |',
                  '|---|---|---|---|---|---|']
        lines += ['| %s | %s | %d | %.4f | %.4f | %s |' % (r['state'], r['market'],
            int(r['n_events']), r['screen_rate'], r['edge_pp'], fi(r['n_folds_pos']))
            for _, r in edge.iterrows()] + ['']
    lines += ['## fold5 callout (5th contiguous equal-count block of pooled CALIB screened '
             'resolved bottoms; WI-027 fold5: 2020-01-29 -> 2022-04-29)']
    for k, edge, (d0, d1, f5c) in zip(N_COMPS, edges, f5s):
        if d0 is None:
            lines.append('- %d-state: no fold5 bottoms' % k)
            continue
        st = sorted(stable_states(edge))
        n5, ins = sum(f5c.values()), sum(f5c.get(s, 0) for s in st)
        lines.append('- %d-state fold5: %s -> %s | states: %s | fold-stable (pooled ALL '
                     'n_folds_pos==%d): %s | fold5 in failing states: %d/%d' % (
                     k, d0, d1, ', '.join('%s (n=%d)' % kv for kv in sorted(f5c.items())),
                     N_FOLDS, ', '.join(st) or 'none', n5 - ins, n5))
    lines += ['', '## Comparison vs WI-027 rule-based labels (research ladder stage 1b)',
              '- WI-027 fold-stable rows (n_folds_pos==%d): up_high/USD + chop_normal/ALL '
              '(rule-based VERDICT: PASS).' % N_FOLDS]
    for k, edge, (d0, d1, f5c) in zip(N_COMPS, edges, f5s):
        st = sorted(stable_states(edge))
        iso = fold5_isolated(set(st), f5c) if st else False
        lines.append('- GMM-%d fold-stable states: %s%s' % (k, ', '.join(st) or 'none',
                     ' + fold5 isolated' if iso else ''))
    lines += ['- Which labeling is better: %s' % ('the GMM matches/beats the rule-based '
              'fold-stability + fold5 isolation on this run.' if verdict == 'PASS' else
              'the rule-based labels keep the edge on this run (no GMM state clears).'),
              '- Raw probability vectors feed downstream ML either way; state names are '
              'SUGGESTIONS ONLY.', '', 'VERDICT: %s' % verdict]
    return lines

def main(out_dir='reports/fib_swings', smoke=None):
    """Full chain: WI-027 extended daily + return features -> GMM soft states -> outputs."""
    os.makedirs(out_dir, exist_ok=True)
    keep = {s.strip() for s in (smoke or os.environ.get('FIB_SMOKE', '') or '').split(',')
            if s.strip()} or None
    data_dir = 'reports/fib_swings'
    daily = pd.read_csv(os.path.join(data_dir, 'regime_daily_extended.csv'))
    daily = daily.merge(market_return_features(cross_section(sorted(glob.glob(RAW_GLOB)), keep)),
                        on=['market', 'date'], how='left')
    daily = gmm_states(daily)
    cols = [c for k in N_COMPS for c in ['gmm%d_s%d_prob' % (k, j) for j in range(k)] + ['gmm%d_label' % k]]
    out = daily[EXT_COLS + cols].copy()
    for k in N_COMPS:               # int labels; unpredicted rows (incomplete features) stay empty
        out['gmm%d_label' % k] = out['gmm%d_label' % k].astype('Int64')
    out.to_csv(os.path.join(out_dir, 'regime_daily_soft.csv'), index=False)
    ev = load_bottom_events(data_dir)
    edges = [state_edge_table(ev, daily, 'gmm%d_label' % k, ['s%d' % j for j in range(k)]) for k in N_COMPS]
    f5s = [fold5_states(ev, daily, 'gmm%d_label' % k) for k in N_COMPS]
    v = gmm_verdict(edges, [c for _, _, c in f5s])
    with open(os.path.join(out_dir, 'GMM_STATES.md'), 'w') as f:
        f.write('\n'.join(states_md(daily, edges, f5s, v)) + '\n')
    print('rows=%d | VERDICT: %s' % (len(daily), v), flush=True)
    print('EXIT:0', flush=True)

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='WI-027b unsupervised GMM regime states (soft probs)')
    ap.add_argument('--out', default='reports/fib_swings')
    ap.add_argument('--smoke', default=None, help='symbols csv (fallback: FIB_SMOKE env)')
    a = ap.parse_args()
    main(a.out, a.smoke)
