"""WI-030: learned conditional exit policy on fib bottom events.

Per-event pick of one of the 32 WI-023 grid cells (target x stop x max_days x
entry) from 16 event features + regime one-hot + WI-025 MFE horizon prior.
Oracle = per-event argmax ret over the 32 cells (trade_labels_w39.parquet).
CALIB (< 2022-05-02): 5 purged date-block folds, 60-day purge; bar = chosen
mean ret > 0 in all 5. EVAL (>= 2022-07-01) scored once on the final CALIB fit.
Horizon39 = 1 if market q50 MFE >= cross-market median (39d), else 0 (20d);
quantile_results.csv only publishes market-level q50 levels. n_jobs=2, float32.
Outputs (out_dir): exit_policy_learned.csv, EXIT_POLICY.md.
"""
import argparse
import json
import os

import numpy as np
import pandas as pd
from xgboost import XGBClassifier

KEYS = ['symbol', 'market', 'date']
FEATURES = ['rsi_f63', 'spread15_39', 'bbw_ratio', 'rsi24_39', 'rsi15_slope5',
            'dd63', 'dd63_days', 'days_since_prev_bottom', 'mom_12_1', 'vol21',
            'atrp63', 'r1_s5', 'r2', 'prior_p_medplus', 'is_usd', 'screen_bottom']
CALIB_END = '2022-05-02'
EVAL_START = '2022-07-01'
PURGE_DAYS = 60
N_BLOCKS = 5
N_TREES = 200
SMOKE_TREES = 40
SMOKE_SYMBOLS = 25
DEFAULT_OUT = 'reports/fib_swings'
SMOKE_OUT, OUT_COLS = '/tmp/fib_exit_policy_smoke', ['symbol', 'market', 'date', 'period', 'fold',
            'oracle_policy', 'chosen_policy', 'chosen_ret', 'pred_prob']


def load_labels(out_dir):
    lab = pd.read_parquet(f'{out_dir}/trade_labels_w39.parquet',
                          columns=KEYS + ['policy', 'ret'])
    lab['date'] = lab['date'].astype(str)
    lab['policy'] = lab['policy'].astype(str)
    lab['ret'] = lab['ret'].astype('float32')
    return lab


def oracle_labels(lab):
    r = lab.dropna(subset=['ret'])
    ix = r.groupby(KEYS, sort=False)['ret'].idxmax()
    o = r.loc[ix, KEYS + ['policy', 'ret']].rename(
        columns={'policy': 'oracle_policy', 'ret': 'oracle_ret'})
    return o.reset_index(drop=True)


def horizon_map(out_dir):
    """Market -> max_days prior (20/39) from the published q50 MFE levels."""
    q = pd.read_csv(f'{out_dir}/quantile_results.csv')
    q = q[(q['target'] == 'fwd_mfe_pct') & (q['alpha'].astype(str) == '0.5')]
    q = q[q['market'].isin(['CAD', 'USD'])]
    if q.empty:
        return {}
    thr = float(q['model_pinball'].astype('float64').median())
    return {str(m): (39 if float(v) >= thr else 20)
            for m, v in zip(q['market'], q['model_pinball'])}


def build_dataset(out_dir, smoke=False):
    feat = pd.read_parquet(f'{out_dir}/event_features.parquet')
    feat['date'] = feat['date'].astype(str)
    feat = feat.drop_duplicates(KEYS)
    symbols = None
    if smoke:
        symbols = set(sorted(feat['symbol'].unique())[:SMOKE_SYMBOLS])
        feat = feat[feat['symbol'].isin(symbols)]
    lab = load_labels(out_dir)
    if symbols is not None:
        lab = lab[lab['symbol'].isin(symbols)]
    policies = sorted(lab['policy'].unique())
    oracle = oracle_labels(lab)
    d = feat.merge(oracle, on=KEYS, how='inner')
    reg = pd.read_csv(f'{out_dir}/regime_daily_extended.csv',
                      usecols=['market', 'date', 'regime'])
    reg['date'] = reg['date'].astype(str)
    d = d.merge(reg.drop_duplicates(['market', 'date']), on=['market', 'date'],
                how='left')
    d['regime'] = d['regime'].fillna('unknown').astype(str)
    hmap = horizon_map(out_dir)
    d['horizon39'] = (d['market'].map(hmap).fillna(20) >= 39).astype('float32')
    d = pd.get_dummies(d, columns=['regime'], prefix='rg', dtype='float32')
    d['cell'] = pd.Categorical(d['oracle_policy'],
                               categories=policies).codes.astype('int32')
    d[FEATURES] = d[FEATURES].astype('float32')
    feats = FEATURES + [c for c in d.columns if c.startswith('rg_')] \
        + ['horizon39']
    return d, lab, policies, feats, hmap


def purged_blocks(df, n_blocks=N_BLOCKS):
    dt = pd.to_datetime(df['date'])
    return pd.qcut(dt.rank(method='first'), n_blocks, labels=False).to_numpy()


def purge_keep(dates, lo, hi, days=PURGE_DAYS):
    t = pd.to_datetime(pd.Series(np.asarray(dates)))
    lo = pd.Timestamp(lo) - pd.Timedelta(days=days)
    hi = pd.Timestamp(hi) + pd.Timedelta(days=days)
    return (~((t >= lo) & (t <= hi))).to_numpy()


def fit_predict(Xtr, ytr, Xte, n_classes, n_trees=N_TREES, seed=0):
    y = np.asarray(ytr, dtype='int32')
    present = np.unique(y)
    if len(present) < 2 or len(y) < 10 or len(Xte) == 0:
        prob = np.zeros((len(Xte), n_classes), dtype='float32')
        if len(present):
            prob[:, int(present[0])] = 1.0
        return prob
    remap = {int(c): i for i, c in enumerate(present)}
    yr = np.fromiter((remap[int(v)] for v in y), dtype='int32', count=len(y))
    mdl = XGBClassifier(objective='multi:softprob', num_class=len(present),
                        max_depth=3, n_estimators=n_trees, learning_rate=0.05,
                        subsample=0.8, colsample_bytree=0.8,
                        min_child_weight=50, n_jobs=2, random_state=seed,
                        tree_method='hist', verbosity=0)
    mdl.fit(Xtr, yr)
    prob = np.zeros((len(Xte), n_classes), dtype='float32')
    prob[:, present] = mdl.predict_proba(Xte).astype('float32')
    return prob


def select_and_score(eff, prob, policies, fold, lab):
    """Argmax cell -> chosen policy -> realized ret (left merge)."""
    eff = eff.copy()
    eff['cell_chosen'] = prob.argmax(1)
    eff['pred_prob'] = prob.max(1).astype('float32')
    eff['chosen_policy'] = [policies[i] for i in eff['cell_chosen']]
    eff['fold'] = fold
    m = eff[KEYS + ['chosen_policy']].merge(
        lab[KEYS + ['policy', 'ret']], left_on=KEYS + ['chosen_policy'],
        right_on=KEYS + ['policy'], how='left', sort=False)
    eff['chosen_ret'] = m['ret'].astype('float32').to_numpy()
    return eff


def cv_folds(cal, lab, policies, feats, n_trees):
    blk = purged_blocks(cal)
    dt = pd.to_datetime(cal['date'])
    oof, rows = [], []
    for k in range(N_BLOCKS):
        te_m = blk == k
        te = cal[te_m].reset_index(drop=True)
        tr = cal[~te_m]
        keep = purge_keep(tr['date'], dt[te_m].min(), dt[te_m].max())
        tr = tr[keep]
        prob = fit_predict(tr[feats], tr['cell'], te[feats], len(policies),
                           n_trees)
        te = select_and_score(te, prob, policies, k, lab)
        oof.append(te)
        r = te['chosen_ret'].dropna()
        rows.append({'fold': k, 'n_train': int(len(tr)), 'n_test': int(len(te)),
                     'n_resolved': int(len(r)),
                     'mean_ret': float(r.mean()) if len(r) else np.nan,
                     'hit_rate': float((r > 0).mean()) if len(r) else np.nan})
    return pd.concat(oof, ignore_index=True), rows


def baseline_policy(out_dir, cal, lab):
    path = f'{out_dir}/exit_policy_choice.json'
    if os.path.exists(path):
        with open(path) as fh:
            choice = json.load(fh).get('policy')
        if choice:
            return str(choice)
    sub = cal[KEYS].merge(lab[KEYS + ['policy', 'ret']], on=KEYS, how='inner')
    means = sub.dropna(subset=['ret']).groupby('policy')['ret'].mean()
    return str(means.idxmax()) if len(means) else None


def policy_mean(keys, lab, policy):
    if not policy:
        return np.nan, 0
    p = lab[lab['policy'] == str(policy)]
    m = keys[KEYS].merge(p[KEYS + ['ret']], on=KEYS, how='left', sort=False)
    r = m['ret'].dropna()
    return (float(r.mean()) if len(r) else np.nan), int(len(r))


def write_report(out_dir, rows, base, cal_oof, cal_base, ev, ev_learned, ev_base, hmap, verdict):
    lines = ['# EXIT POLICY LEARNED (WI-030)', '',
             f'Oracle: argmax over 32 cells ({sum(r["n_test"] for r in rows)} CALIB + {len(ev)} EVAL).',
             f'Features: 16 event features + regime one-hot + horizon prior {hmap}.',
             '', f'## CALIB purged CV ({N_BLOCKS} blocks, {PURGE_DAYS}d purge)', '',
             '| fold | n_train | n_test | n_resolved | mean_ret | hit_rate |',
             '|---|---|---|---|---|---|']
    for r in rows:
        lines.append(f"| {r['fold']} | {r['n_train']} | {r['n_test']} | "
                     f"{r['n_resolved']} | {r['mean_ret']:.4f} | "
                     f"{r['hit_rate']:.3f} |")
    pos = sum(1 for r in rows if np.isfinite(r['mean_ret']) and r['mean_ret'] > 0)
    lines += ['', f'fold-stable: {pos}/{N_BLOCKS} folds with mean_ret > 0.', '',
              f'pooled OOF mean_ret {cal_oof:+.4f} vs frozen baseline '
              f'{base} {cal_base:+.4f}', '',
              '## EVAL (scored once with the final CALIB fit)', '',
              f'n={len(ev)} | learned mean_ret {ev_learned:+.4f} vs frozen baseline {base} '
              f'{ev_base:+.4f} (edge {ev_learned - ev_base:+.4f})', '',
              f'VERDICT: {verdict}']
    with open(f'{out_dir}/EXIT_POLICY.md', 'w') as fh:
        fh.write('\n'.join(lines) + '\n')


def main(out_dir=None, smoke=False, src_dir=None):
    if src_dir is None:
        src_dir = DEFAULT_OUT if (smoke and out_dir is None) else (out_dir or DEFAULT_OUT)
    out_dir = out_dir or (SMOKE_OUT if smoke else DEFAULT_OUT)
    os.makedirs(out_dir, exist_ok=True)
    d, lab, policies, feats, hmap = build_dataset(src_dir, smoke)
    dt = pd.to_datetime(d['date'])
    cal = d[dt < pd.Timestamp(CALIB_END)].reset_index(drop=True)
    ev = d[dt >= pd.Timestamp(EVAL_START)].reset_index(drop=True)
    if len(cal) < 2 * N_BLOCKS or len(ev) == 0:
        raise SystemExit('EXIT_POLICY: insufficient CALIB/EVAL events')
    n_trees = SMOKE_TREES if smoke else N_TREES
    oof, rows = cv_folds(cal, lab, policies, feats, n_trees)
    base = baseline_policy(src_dir, cal, lab)
    cal_oof = float(oof['chosen_ret'].dropna().mean())
    cal_base, _ = policy_mean(cal[KEYS], lab, base)
    prob = fit_predict(cal[feats], cal['cell'], ev[feats], len(policies), n_trees)
    ev_sel = select_and_score(ev, prob, policies, -1, lab)
    ev_learned = float(ev_sel['chosen_ret'].dropna().mean())
    ev_base, _ = policy_mean(ev[KEYS], lab, base)
    calib_edge = cal_oof - cal_base
    eval_edge = ev_learned - ev_base
    stable = all(np.isfinite(r['mean_ret']) and r['mean_ret'] > 0 for r in rows)
    verdict = 'PASS' if (stable and np.isfinite(eval_edge) and eval_edge > 0) else 'FAIL'
    oof['period'], ev_sel['period'] = 'CALIB', 'EVAL'
    learned = pd.concat([oof[OUT_COLS], ev_sel[OUT_COLS]], ignore_index=True)
    learned['chosen_ret'] = learned['chosen_ret'].astype('float32')
    learned.to_csv(f'{out_dir}/exit_policy_learned.csv', index=False)
    write_report(out_dir, rows, base, cal_oof, cal_base, ev_sel, ev_learned,
                 ev_base, hmap, verdict)
    print(f'EXIT_POLICY base={base} calib_edge={calib_edge:+.4f} '
          f'eval_edge={eval_edge:+.4f} verdict={verdict}', flush=True)
    print(f'folds_pos={sum(1 for r in rows if r["mean_ret"] > 0)}/{N_BLOCKS} '
          f'rows={len(learned)}', flush=True)
    print('EXIT:0', flush=True)

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='WI-030 learned exit policy')
    ap.add_argument('--out', default=None)
    ap.add_argument('--smoke', action='store_true')
    a = ap.parse_args()
    main(a.out, a.smoke)