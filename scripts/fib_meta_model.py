"""Pass 5b: meta-label filter vs frozen screen on fib bottom events (WI-024).

Reads <out>/exit_policy_choice.json. Null policy -> META_MODEL.md gets
VERDICT: BLOCKED_PRECONDITION (no exit policy cleared). Else y = ret of that
policy from <out>/trade_labels_w39.parquet, clipped [-0.15, 0.15], NaN dropped.
Split: CALIB date < 2022-05-02; EVAL >= 2022-07-01. Equal-volume selection on
EVAL via the CALIB score quantile reproducing the screen's CALIB flag rate.
Models: SCREEN score, RIDGE (StandardScaler+Ridge alpha=1.0, CALIB-median
impute), XGB (monotone -1 on rsi_f63/spread15_39, 0 elsewhere). 5-block purged
CV (60-day purge) + 20-rep permutation null. n_jobs=2, float32-safe.
"""
import argparse
import json
import os

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor

try:
    import psutil
except ImportError:  # pragma: no cover
    psutil = None

KEYS = ['symbol', 'market', 'date']
FEATURES = ['rsi_f63', 'spread15_39', 'bbw_ratio', 'rsi24_39', 'rsi15_slope5',
            'dd63', 'dd63_days', 'days_since_prev_bottom', 'mom_12_1', 'vol21',
            'atrp63', 'r1_s5', 'r2', 'prior_p_medplus', 'is_usd', 'screen_bottom']
MONOTONE = [-1 if f in ('rsi_f63', 'spread15_39') else 0 for f in FEATURES]
CALIB_END = pd.Timestamp('2022-05-02')
EVAL_START = pd.Timestamp('2022-07-01')
PURGE_DAYS = 60
N_BLOCKS = 5
N_PERM = 20
BLOCKED_VERDICT = 'VERDICT: BLOCKED_PRECONDITION (no exit policy cleared)'


def purge_keep_mask(train_dates, block_start, block_end, days=PURGE_DAYS):
    """True = keep row: NOT within `days` calendar days of the test block."""
    t = pd.to_datetime(pd.Series(np.asarray(train_dates))).reset_index(drop=True)
    lo = pd.Timestamp(block_start) - pd.Timedelta(days=days)
    hi = pd.Timestamp(block_end) + pd.Timedelta(days=days)
    return ~((t >= lo) & (t <= hi))


def xgb_model():
    return XGBRegressor(max_depth=3, n_estimators=300, learning_rate=0.05,
                        subsample=0.8, colsample_bytree=0.8,
                        min_child_weight=50, n_jobs=2, random_state=0,
                        monotone_constraints=MONOTONE)


def ridge_model():
    return Pipeline([('sc', StandardScaler()), ('ridge', Ridge(alpha=1.0))])


def shuffle_within_date(y, dates, seed):
    rng = np.random.default_rng(seed)
    y = np.asarray(y, dtype=float).copy()
    d = np.asarray(dates)
    for u in pd.unique(d):
        ix = np.where(d == u)[0]
        y[ix] = y[ix[rng.permutation(len(ix))]]
    return y


def make_y(feat, labels, policy):
    lab = labels[labels['policy'] == policy]
    m = feat[FEATURES + KEYS].merge(lab[KEYS + ['ret']], on=KEYS, how='inner')
    m['y'] = m['ret'].astype('float64').clip(-0.15, 0.15)
    m = m[m['y'].notna()].copy()
    m['date'] = m['date'].astype(str)
    return m


def model_scores(name, cal, evl):
    """Return (cal_scores, eval_scores) for a model name."""
    if name == 'SCREEN':
        return (cal['screen_bottom'].astype(float) - 0.001 * cal['rsi_f63'],
                evl['screen_bottom'].astype(float) - 0.001 * evl['rsi_f63'])
    if name == 'RIDGE':
        med = cal[FEATURES].median()
        xc, xe = cal[FEATURES].fillna(med), evl[FEATURES].fillna(med)
        mdl = ridge_model().fit(xc, cal['y'])
        return mdl.predict(xc), mdl.predict(xe)
    mdl = xgb_model().fit(cal[FEATURES], cal['y'])
    return mdl.predict(cal[FEATURES]), mdl.predict(evl[FEATURES])


def report(name, cal_scores, ev_scores, evl, flag_rate):
    thr = float(np.quantile(np.asarray(cal_scores, dtype=float), 1 - flag_rate))
    es = np.asarray(ev_scores, dtype=float)
    sel = es >= thr
    y = evl['y'].to_numpy()
    r = {'model': name, 'n_selected': int(sel.sum())}
    r['mean_ret'] = float(y[sel].mean()) if sel.sum() else np.nan
    r['hit_rate'] = float((y[sel] > 0).mean()) if sel.sum() else np.nan
    ok = np.isfinite(es) & np.isfinite(y)
    r['eval_spearman'] = (float(spearmanr(es[ok], y[ok]).correlation)
                          if ok.sum() > 1 else np.nan)
    if sel.sum():
        d2 = pd.DataFrame({'date': evl['date'].to_numpy()[sel],
                           'market': evl['market'].to_numpy()[sel], 'y': y[sel]})
        yr = pd.to_datetime(d2['date']).dt.year
        r['per_year_mean_ret'] = {int(k): round(float(v), 5)
                                 for k, v in d2.groupby(yr)['y'].mean().items()}
        r['per_market_mean_ret'] = {str(k): round(float(v), 5)
                                     for k, v in d2.groupby('market')['y'].mean().items()}
    else:
        r['per_year_mean_ret'] = {}
        r['per_market_mean_ret'] = {}
    return r


def cv_spearmans(cal, n_blocks=N_BLOCKS):
    cal = cal.sort_values('date').reset_index(drop=True)
    dt = pd.to_datetime(cal['date'])
    blocks = pd.qcut(dt.rank(method='first'), n_blocks, labels=False)
    out = []
    for b in range(n_blocks):
        te = (blocks.to_numpy() == b)
        tb, tr = cal[te], cal[~te]
        keep = purge_keep_mask(tr['date'], dt[te].min(), dt[te].max()).to_numpy()
        tr2 = tr[keep]
        row = {'fold': b, 'n_train': int(len(tr2)), 'n_test': int(len(tb))}
        if len(tr2) > 10 and len(tb) > 1:
            med = tr2[FEATURES].median()
            pr = ridge_model().fit(tr2[FEATURES].fillna(med), tr2['y'])
            row['ridge_spearman'] = float(
                spearmanr(pr.predict(tb[FEATURES].fillna(med)), tb['y']).correlation)
            mx = xgb_model().fit(tr2[FEATURES], tr2['y'])
            row['xgb_spearman'] = float(
                spearmanr(mx.predict(tb[FEATURES]), tb['y']).correlation)
        else:
            row['ridge_spearman'] = np.nan
            row['xgb_spearman'] = np.nan
        out.append(row)
    return out


def permutation_null(cal, evl, flag_rate, n_rep=N_PERM, seed=0):
    nulls = []
    cx, ex = cal[FEATURES], evl[FEATURES]
    for rep in range(n_rep):
        y0 = shuffle_within_date(cal['y'], cal['date'], seed + rep)
        mdl = xgb_model().fit(cx, y0)
        cs, es = mdl.predict(cx), mdl.predict(ex)
        thr = np.quantile(cs, 1 - flag_rate)
        sel = es >= thr
        y = evl['y'].to_numpy()
        nulls.append(float(y[sel].mean()) if sel.sum() else np.nan)
    return nulls


def main(out_dir='reports/fib_swings'):
    os.makedirs(out_dir, exist_ok=True)
    with open(f'{out_dir}/exit_policy_choice.json') as fh:
        policy = json.load(fh).get('policy')
    md_path = f'{out_dir}/META_MODEL.md'
    if policy is None:
        with open(md_path, 'w') as fh:
            fh.write('# META MODEL (WI-024)\n\n' + BLOCKED_VERDICT + '\n')
        print(BLOCKED_VERDICT, flush=True)
        print('EXIT:0', flush=True)
        return
    feat = pd.read_parquet(f'{out_dir}/event_features.parquet')
    labels = pd.read_parquet(f'{out_dir}/trade_labels_w39.parquet')
    d = make_y(feat, labels, policy)
    dt = pd.to_datetime(d['date'])
    cal = d[dt < CALIB_END].reset_index(drop=True)
    evl = d[dt >= EVAL_START].reset_index(drop=True)
    flag_rate = float(cal['screen_bottom'].mean()) if len(cal) else 0.0
    results = {}
    for name in ('SCREEN', 'RIDGE', 'XGB'):
        cs, es = model_scores(name, cal, evl)
        results[name] = report(name, cs, es, evl, flag_rate)
    cvrows = cv_spearmans(cal)
    nulls = permutation_null(cal, evl, flag_rate)
    xgb_m, scr_m = results['XGB']['mean_ret'], results['SCREEN']['mean_ret']
    finite_nulls = [m for m in nulls if np.isfinite(m)]
    wins = int(sum(xgb_m > m for m in finite_nulls))
    delta = xgb_m - scr_m
    ok = (np.isfinite(delta) and delta >= 0.005
          and np.isfinite(results['XGB']['eval_spearman'])
          and results['XGB']['eval_spearman'] > 0 and wins >= 19)
    verdict = 'PASS' if ok else 'FAIL'
    pd.DataFrame([results[n] for n in ('SCREEN', 'RIDGE', 'XGB')]).to_csv(
        f'{out_dir}/meta_model_results.csv', index=False)
    ridge_delta = results['RIDGE']['mean_ret'] - scr_m
    if psutil is not None:
        peak_rss = psutil.Process().memory_info().rss / 1e6
    else:  # pragma: no cover
        import resource
        peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e3
    lines = ['# META MODEL (WI-024)', '',
             f'policy: {policy} | screen CALIB flag_rate: {flag_rate:.4f}', '',
             '| model | n_selected | mean_ret | hit_rate | eval_spearman |',
             '|---|---|---|---|---|']
    for name in ('SCREEN', 'RIDGE', 'XGB'):
        r = results[name]
        lines.append(f"| {name} | {r['n_selected']} | {r['mean_ret']:.4f} | "
                     f"{r['hit_rate']:.3f} | {r['eval_spearman']:.3f} |")
    lines += ['', f'## CALIB sanity CV ({N_BLOCKS} contiguous date blocks, '
                  f'{PURGE_DAYS}-day purge, fold Spearman)', '',
              '| fold | ridge_spearman | xgb_spearman |', '|---|---|---|']
    for row in cvrows:
        lines.append(f"| {row['fold']} | {row['ridge_spearman']:.3f} | "
                     f"{row['xgb_spearman']:.3f} |")
    lines += ['', f'## Permutation null (XGB, {N_PERM} reps, EVAL selected mean_ret)',
              '', ', '.join(f'{m:.4f}' for m in nulls), '',
              f'XGB beats {wins}/{N_PERM} null reps.', '',
              f'RIDGE vs SCREEN: mean_ret delta {ridge_delta:+.4f} '
              + ('(RIDGE beats SCREEN)' if ridge_delta > 0 else '(SCREEN beats RIDGE)'),
              '', f'peak_rss_mb: {peak_rss:.1f}', '', f'VERDICT: {verdict}']
    with open(md_path, 'w') as fh:
        fh.write('\n'.join(lines) + '\n')
    print(f'XGB mean_ret {xgb_m:.4f} vs SCREEN {scr_m:.4f} | null wins {wins}/'
          f'{N_PERM} | {verdict}', flush=True)
    print('EXIT:0', flush=True)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='WI-024 meta-label model')
    ap.add_argument('--out', default='reports/fib_swings')
    main(ap.parse_args().out)