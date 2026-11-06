"""WI-022: regime overlay (R1 vol term structure, R2 breadth63) on the frozen fib bottom screen.
Pass A reads raw OHLCV symbol-sequentially, keeping only per-(market, date) accumulators, and
writes regime_daily.csv. Pass B joins trailing_events_w39.csv bottoms on (market, date) with
their OWN market's r1_s5/r2. Cut points = 1/3 & 2/3 quantiles over CALIB (<2022-05-02) dates
only; EVAL (>=2022-07-01) scored once. Frozen: outcome fwd_mfe_pct >= 19.5, keep floor 0.30,
5 contiguous equal-count CALIB folds, sets {T1},{T2},{T3},{T1,T2},{T2,T3},{T1,T3}; R1R2 =
intersection of the two gated sets. Outputs -> out_dir: regime_daily.csv,
regime_overlay_results.csv (incl. UNGATED), regime_overlay_per_year.csv, REGIME_OVERLAY.md."""
import argparse, glob, json, os

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

CALIB_END, EVAL_START = '2022-05-02', '2022-07-01'
GRADE_MED, KEEP_RATE_MIN, N_FOLDS = 19.5, 0.30, 5
CAND_SETS = [('T1',), ('T2',), ('T3',), ('T1', 'T2'), ('T2', 'T3'), ('T1', 'T3')]
RESULT_COLS = ['rule', 'period', 'market', 'n_bottoms', 'n_screened', 'n_gated', 'keep_rate',
               'base_rate', 'screen_rate', 'gated_rate', 'gated_edge_pp', 'mean_ret_screened',
               'mean_ret_gated']

def bbw_ratio(close):
    """(4*std3/mean3)/(4*std39/mean39) of close, pandas rolling as in fib_walkforward."""
    return ((4 * close.rolling(3).std() / close.rolling(3).mean())
            / (4 * close.rolling(39).std() / close.rolling(39).mean()))

def accumulate_symbol(acc, df, market):
    """Fold one symbol's bars into per-(market, date) accumulators (finite log only)."""
    c = df['close'].astype('float64')
    with np.errstate(divide='ignore', invalid='ignore'):
        lb = np.log(bbw_ratio(c)).to_numpy()
    ma63 = c.rolling(63).mean().to_numpy()
    fin = np.isfinite(lb)
    g = pd.DataFrame({'date': df['date'].astype(str).to_numpy(),
                      'sum_log': np.where(fin, lb, 0.0), 'count': fin,
                      'n_above63': c.to_numpy() > ma63, 'n_valid63': np.isfinite(ma63)})
    for r in g.groupby('date', as_index=False).sum(numeric_only=True).itertuples(index=False):
        e = acc.setdefault((market, r.date), [0.0, 0, 0, 0])
        e[0] += float(r.sum_log); e[1] += int(r.count); e[2] += int(r.n_above63); e[3] += int(r.n_valid63)

def regime_daily_from_acc(acc):
    """Daily frame + market 'ALL' (sum of both) -> r1, r1_s5, r2, n_tickers."""
    cols = ['market', 'date', 'r1', 'r1_s5', 'r2', 'n_tickers']
    if not acc:
        return pd.DataFrame(columns=cols)
    df = pd.DataFrame([dict(market=m, date=d, sum_log=v[0], count=v[1],
                            n_above63=v[2], n_valid63=v[3]) for (m, d), v in acc.items()])
    agg = df.groupby('date', as_index=False).sum(numeric_only=True)
    agg.insert(0, 'market', 'ALL')
    df = pd.concat([df, agg], ignore_index=True)
    with np.errstate(invalid='ignore'):
        df['r1'] = df['sum_log'] / df['count']
        df['r2'] = df['n_above63'] / df['n_valid63']
    df['n_tickers'] = df['count']
    df = df.sort_values(['market', 'date']).reset_index(drop=True)
    df['r1_s5'] = df.groupby('market')['r1'].transform(lambda s: s.rolling(5).mean())
    return df[cols]

def build_regime_daily(out_dir, files=None):
    """Pass A: parquet files one at a time (FIB_SMOKE keeps listed symbols); writes CSV."""
    if files is None:
        files = sorted(glob.glob('data/raw_ohlcv/market=*/*.parquet'))
    keep = {s.strip() for s in os.environ.get('FIB_SMOKE', '').split(',') if s.strip()} or None
    acc = {}
    for f in files:  # symbol-sequential reads
        sym = os.path.basename(f).replace('.parquet', '')
        sym = sym.split('=', 1)[1] if sym.startswith('symbol=') else sym
        parent = os.path.basename(os.path.dirname(f))
        market = parent.split('market=', 1)[1] if 'market=' in parent else ''
        if keep is not None and sym not in keep:
            continue
        df = pq.read_table(f).to_pandas().sort_values('date').reset_index(drop=True)
        if {'close', 'date'} <= set(df.columns):
            accumulate_symbol(acc, df, market)
    daily = regime_daily_from_acc(acc)
    daily.to_csv(os.path.join(out_dir, 'regime_daily.csv'), index=False)
    return daily

def load_bottom_events(out_dir):
    """Frozen WI-021 bottoms: empty-string NA only; numeric/bool coercion."""
    ev = pd.read_csv(os.path.join(out_dir, 'trailing_events_w39.csv'),
                     keep_default_na=False, na_values=[''])
    ev = ev[ev['type'] == 'bottom'].reset_index(drop=True)
    for col in ('rsi_f63', 'spread15_39', 'bbw_ratio', 'fwd_mfe_pct', 'fwd_mae_pct', 'fwd_ret_pct'):
        if col in ev.columns:
            ev[col] = pd.to_numeric(ev[col], errors='coerce')
    s = ev['screen_bottom'] if 'screen_bottom' in ev.columns else pd.Series(False, index=ev.index)
    ev['screen_bottom'] = s if s.dtype == bool else s.astype(str).str.strip().str.lower().eq('true')
    return ev

def tercile_cuts(daily, market, col):
    """1/3 and 2/3 quantiles of col over CALIB (<2022-05-02) dates of this market."""
    m = (daily['market'] == market) & (pd.to_datetime(daily['date']) < CALIB_END)
    v = daily.loc[m, col].dropna()
    return (float(v.quantile(1 / 3)), float(v.quantile(2 / 3))) if len(v) else (np.nan, np.nan)

def add_terciles(ev, daily):
    """Join own-market r1_s5/r2, then label T1/T2/T3 from per-market CALIB cut points."""
    ev = ev.merge(daily[['market', 'date', 'r1_s5', 'r2']], on=['market', 'date'], how='left')
    for tcol, vcol in (('r1_terc', 'r1_s5'), ('r2_terc', 'r2')):
        ev[tcol] = None
        for mk in ev['market'].unique():
            q1, q2 = tercile_cuts(daily, mk, vcol)
            mm = ev['market'] == mk
            ev.loc[mm, tcol] = ev.loc[mm, vcol].apply(
                lambda x: None if pd.isna(x) or pd.isna(q1)
                else 'T1' if x <= q1 else 'T2' if x <= q2 else 'T3')
    return ev

def eval_candidate(cal, terc_col, allowed):
    """(5 fold edges, CALIB keep rate) for one candidate set on pooled CALIB bottoms."""
    res = cal[cal['fwd_mfe_pct'].notna()].sort_values('date')
    edges = []
    for f in np.array_split(np.arange(len(res)), N_FOLDS):
        g = res.iloc[f]
        base = (g['fwd_mfe_pct'] >= GRADE_MED).mean() if len(g) else np.nan
        gg = g[np.asarray(g['screen_bottom']) & np.asarray(g[terc_col].isin(allowed))]
        edges.append(((gg['fwd_mfe_pct'] >= GRADE_MED).mean() if len(gg) else np.nan) - base)
    scr = cal[np.asarray(cal['screen_bottom'])]
    return edges, (float(np.asarray(scr[terc_col].isin(allowed)).sum() / len(scr)) if len(scr) else np.nan)

def choose_rule(cal, terc_col):
    """Max mean fold edge among eligible sets; 'NONE' if no set is eligible."""
    best, best_mean = 'NONE', -np.inf
    for allowed in CAND_SETS:
        edges, keep = eval_candidate(cal, terc_col, allowed)
        if all(np.isfinite(e) and e > 0 for e in edges) and np.isfinite(keep) \
                and keep >= KEEP_RATE_MIN and float(np.mean(edges)) > best_mean:
            best, best_mean = set(allowed), float(np.mean(edges))
    return best

def gate_mask(ev, rule, r1_set, r2_set):
    """screen AND tercile membership per rule ('UNGATED' passes None sets -> screen only)."""
    m = np.asarray(ev['screen_bottom'], dtype=bool).copy()
    if r1_set is not None:
        m &= np.asarray(ev['r1_terc'].isin(r1_set))
    if r2_set is not None:
        m &= np.asarray(ev['r2_terc'].isin(r2_set))
    return m

def stats_row(sub, screen, gate):
    """Counts on full sets; outcome rates / mean rets on resolved rows only (Fix-1 style)."""
    res = np.asarray(sub['fwd_mfe_pct'].notna())
    def mv(m, col):
        r = res & np.asarray(m, dtype=bool)
        return float(sub.loc[r, col].mean()) if r.any() else np.nan
    sub = sub.assign(hit=np.asarray(sub['fwd_mfe_pct'] >= GRADE_MED))
    n_s, n_g = int(np.asarray(screen).sum()), int(np.asarray(gate).sum())
    base, s_rate, g_rate = mv(np.ones(len(sub), bool), 'hit'), mv(screen, 'hit'), mv(gate, 'hit')
    return {'n_bottoms': len(sub), 'n_screened': n_s, 'n_gated': n_g,
            'keep_rate': n_g / n_s if n_s else np.nan, 'base_rate': base,
            'screen_rate': s_rate, 'gated_rate': g_rate, 'gated_edge_pp': (g_rate - base) * 100.0,
            'mean_ret_screened': mv(screen, 'fwd_ret_pct'), 'mean_ret_gated': mv(gate, 'fwd_ret_pct')}

def policy_lines(out_dir, ev, rules):
    """Mean trade-label ret for screened vs gated under the chosen exit policy (if any)."""
    pj = os.path.join(out_dir, 'exit_policy_choice.json')
    try:
        j = json.load(open(pj)) if os.path.exists(pj) else {}
    except Exception:
        j = {}
    policy = j.get('policy') if isinstance(j, dict) else None
    if not policy or not os.path.exists(os.path.join(out_dir, 'trade_labels_w39.parquet')):
        return []
    lab = pd.read_parquet(os.path.join(out_dir, 'trade_labels_w39.parquet'))
    pc = next((c for c in ('policy', 'exit_policy', 'policy_name') if c in lab.columns), None)
    lab = lab[np.asarray(lab[pc].astype(str) == policy)] if pc is not None else lab
    rc = next((c for c in ('ret_pct', 'return_pct', 'exit_ret_pct', 'ret', 'fwd_ret_pct')
               if c in lab.columns and c not in ev.columns), None)
    keys = [k for k in ('symbol', 'market', 'date') if k in lab.columns and k in ev.columns]
    if rc is None or 'date' not in keys:
        return []
    m = ev.merge(lab[keys + [rc]].drop_duplicates(keys), on=keys, how='left')
    out = ['## Exit-policy mean ret (policy=%s, trade_labels_w39.parquet)' % policy]
    for rule, s1, s2 in rules:
        out.append('- %s: mean_ret_screened=%.4f mean_ret_gated=%.4f'
                   % (rule, m.loc[np.asarray(m['screen_bottom'], bool), rc].mean(),
                      m.loc[gate_mask(m, rule, s1, s2), rc].mean()))
    return out

def rule_verdict(res, pery, rule):
    """PASS = EVAL ALL gated edge >= screen edge AND 2026 gated edge >= 0 AND keep >= 0.30."""
    er = res[(res['rule'] == rule) & (res['period'] == 'EVAL') & (res['market'] == 'ALL')]
    if not len(er):
        return None
    er = er.iloc[0]
    yr = pery.loc[(pery['rule'] == rule) & (pery['period'] == '2026'), 'gated_edge_pp']
    yr = float(yr.iloc[0]) if len(yr) else None
    c1 = all(np.isfinite(x) for x in (er.gated_rate, er.base_rate, er.screen_rate)) and \
        (er.gated_rate - er.base_rate) >= (er.screen_rate - er.base_rate)
    c2 = yr is not None and np.isfinite(yr) and yr >= 0
    c3 = np.isfinite(er.keep_rate) and er.keep_rate >= KEEP_RATE_MIN
    return 'PASS' if (c1 and c2 and c3) else 'FAIL'

def main(out_dir='reports/fib_swings'):
    os.makedirs(out_dir, exist_ok=True)
    ev = add_terciles(load_bottom_events(out_dir), build_regime_daily(out_dir))
    d = pd.to_datetime(ev['date'])
    cal = ev[(d < CALIB_END).to_numpy()]
    r1_set, r2_set = choose_rule(cal, 'r1_terc'), choose_rule(cal, 'r2_terc')
    rules = [('UNGATED', None, None)]
    rules += [('R1', r1_set, None)] if r1_set != 'NONE' else []
    rules += [('R2', None, r2_set)] if r2_set != 'NONE' else []
    rules += [('R1R2', r1_set, r2_set)] if 'NONE' not in (r1_set, r2_set) else []
    mks = {'ALL': np.ones(len(ev), bool)}
    mks.update((mk, np.asarray(ev['market'] == mk)) for mk in sorted(set(ev['market'])) if mk != 'ALL')
    pms = [('CALIB', (d < CALIB_END).to_numpy()), ('EVAL', (d >= EVAL_START).to_numpy())]
    rows = []
    for rule, s1, s2 in rules:
        scr = np.asarray(ev['screen_bottom'], dtype=bool)
        gate = gate_mask(ev, rule, s1, s2)
        for period, pm in pms:
            for mk, mm in mks.items():
                rows.append({'rule': rule, 'period': period, 'market': mk,
                             **stats_row(ev[pm & mm], scr[pm & mm], gate[pm & mm])})
        for y in sorted(pd.unique(d.dt.year)):
            ym = np.asarray(d.dt.year == y)
            rows.append({'rule': rule, 'period': str(y), 'market': 'ALL',
                         **stats_row(ev[ym], scr[ym], gate[ym])})
    res = pd.DataFrame([r for r in rows if r['period'] in ('CALIB', 'EVAL')], columns=RESULT_COLS)
    pery = pd.DataFrame([r for r in rows if r['period'] not in ('CALIB', 'EVAL')], columns=RESULT_COLS)
    res.to_csv(os.path.join(out_dir, 'regime_overlay_results.csv'), index=False)
    pery.to_csv(os.path.join(out_dir, 'regime_overlay_per_year.csv'), index=False)
    have = {r for r, _, _ in rules}
    fs = lambda s: 'NONE' if s == 'NONE' else '{%s}' % ','.join(sorted(s))
    print('R1: %s | R2: %s' % (fs(r1_set), fs(r2_set)), flush=True)
    lines = ['# REGIME OVERLAY (WI-022): R1 vol term structure + R2 breadth63', '',
             'Chosen sets (CALIB < %s, %d contiguous equal-count folds, keep_rate >= %.2f):'
             % (CALIB_END, N_FOLDS, KEEP_RATE_MIN),
             '- R1 (r1_s5 terciles): %s' % fs(r1_set), '- R2 (r2 terciles): %s' % fs(r2_set),
             '- R1R2: %s' % (('%s & %s' % (fs(r1_set), fs(r2_set))) if 'R1R2' in have else 'skipped (a chosen set is NONE)'), '']
    lines += policy_lines(out_dir, ev, rules) + ['']
    verdicts = []
    for rule in ('R1', 'R2', 'R1R2'):
        if rule in have or rule != 'R1R2':
            v = rule_verdict(res, pery, rule) or 'FAIL'  # NONE rule -> FAIL
            verdicts.append(v)
            lines.append('VERDICT %s: %s' % (rule, v))
    final = 'PASS' if 'PASS' in verdicts else 'FAIL'
    lines.append('VERDICT: %s' % final)
    with open(os.path.join(out_dir, 'REGIME_OVERLAY.md'), 'w') as f:
        f.write('\n'.join(lines) + '\n')
    print('VERDICT: %s' % final, flush=True)
    print('EXIT:0', flush=True)

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='WI-022 regime overlay on fib bottom screen')
    ap.add_argument('--out', default='reports/fib_swings')
    main(ap.parse_args().out)
