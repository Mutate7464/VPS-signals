"""WI-025: quantile model of 39-day MFE/MAE on fib bottom events.

Reads <out>/event_features.parquet (WI-024 features) and joins targets
fwd_mfe_pct / fwd_mae_pct from <out>/trailing_events_w39.csv on
(symbol, date). CALIB: date < '2022-05-02'; EVAL: date >= '2022-07-01'.
XGB quantile regression (q10/q50/q90), per-symbol empirical baseline,
pinball-loss comparison, coverage and interval width on EVAL.
"""
import argparse
import os

import numpy as np
import pandas as pd

KEYS = ['symbol', 'market', 'date']
FEATURES = ['rsi_f63', 'spread15_39', 'bbw_ratio', 'rsi24_39', 'rsi15_slope5',
            'dd63', 'dd63_days', 'days_since_prev_bottom', 'mom_12_1', 'vol21',
            'atrp63', 'r1_s5', 'r2', 'prior_p_medplus', 'is_usd', 'screen_bottom']
TARGETS = ['fwd_mfe_pct', 'fwd_mae_pct']
ALPHAS = [0.1, 0.5, 0.9]
CALIB_END = '2022-05-02'
EVAL_START = '2022-07-01'
MIN_CALIB = 20


def pinball_loss(y, pred, alpha):
    """Mean pinball (quantile) loss: mean(max(a*(y-pred), (a-1)*(y-pred)))."""
    y = np.asarray(y, dtype='float64')
    pred = np.asarray(pred, dtype='float64')
    d = y - pred
    return float(np.mean(np.maximum(alpha * d, (alpha - 1.0) * d)))


def sort_quantiles(pred):
    """Sort each row's 3 quantile predictions ascending (no crossing)."""
    return np.sort(np.asarray(pred, dtype='float64'), axis=1)


def empirical_quantiles(df, value_col, alphas=ALPHAS):
    """Per-symbol empirical quantiles; symbols with < MIN_CALIB CALIB events
    fall back to the global CALIB quantiles."""
    counts = df.groupby('symbol').size()
    glob = np.percentile(df[value_col].to_numpy(dtype='float64'),
                         [100 * a for a in alphas])
    out = {}
    for sym, g in df.groupby('symbol', sort=False):
        if counts.loc[sym] < MIN_CALIB:
            out[sym] = glob.astype('float64')
        else:
            out[sym] = np.percentile(g[value_col].to_numpy(dtype='float64'),
                                     [100 * a for a in alphas])
    return out


def load_data(out_dir):
    ft = pd.read_parquet(f'{out_dir}/event_features.parquet')
    ev = pd.read_csv(f'{out_dir}/trailing_events_w39.csv',
                     keep_default_na=False, na_values=[''])
    tgt = ev[ev['type'] == 'bottom'] if 'type' in ev.columns else ev
    tgt = tgt[['symbol', 'date'] + TARGETS].copy()
    tgt['date'] = tgt['date'].astype(str)
    ft['date'] = ft['date'].astype(str)
    d = ft.merge(tgt, on=['symbol', 'date'], how='inner')
    d = d.dropna(subset=TARGETS).reset_index(drop=True)
    d[FEATURES] = d[FEATURES].astype('float32')
    return d


def fit_predict(X_cal, y_cal, X_eval):
    """XGB quantile regression; returns EVAL predictions (n, 3) sorted."""
    from xgboost import XGBRegressor
    m = XGBRegressor(objective='reg:quantileerror', quantile_alpha=ALPHAS,
                     max_depth=3, n_estimators=300, learning_rate=0.05,
                     min_child_weight=50, n_jobs=2, random_state=0)
    m.fit(X_cal, y_cal)
    return sort_quantiles(m.predict(X_eval))


def evaluate(d, out_dir):
    cal = d[pd.to_datetime(d['date']) < pd.Timestamp(CALIB_END)]
    ev = d[pd.to_datetime(d['date']) >= pd.Timestamp(EVAL_START)].copy()
    ev = ev.dropna(subset=FEATURES).reset_index(drop=True)
    rows = []
    glob_q = {t: {s: np.percentile(
        cal[t].to_numpy('float64'), [100 * a for a in ALPHAS])
        for s in cal['market'].str.upper().unique()} for t in TARGETS}
    for target in TARGETS:
        base_q = {}
        for mkt in sorted(d['market'].str.upper().unique()):
            sub = cal[cal['market'].str.upper() == mkt]
            if len(sub):
                bq = empirical_quantiles(sub, target)
                g = glob_q[target][mkt]
                base_q[mkt] = {s: (v if not np.isnan(v).any() else g)
                               for s, v in bq.items()}
        model_p = fit_predict(cal[FEATURES].to_numpy('float32'),
                              cal[target].to_numpy('float64'),
                              ev[FEATURES].to_numpy('float32'))
        ev_mkt = ev['market'].str.upper().to_numpy()
        for mkt_scope in ('CAD', 'USD', 'ALL'):
            mask = np.ones(len(ev), dtype=bool) if mkt_scope == 'ALL' \
                else (ev_mkt == mkt_scope)
            if not mask.any():
                continue
            y = ev.loc[mask, target].to_numpy('float64')
            mp = model_p[mask]
            bq = base_q.get(mkt_scope, base_q.get(
                next(iter(base_q)) if base_q else 'CAD', {}))
            gb = glob_q[target].get(mkt_scope, glob_q[target].get(
                next(iter(glob_q[target])) if glob_q[target] else 'CAD',
                np.array([np.nan] * 3)))
            bp = np.stack([bq.get(s, gb) for s in ev.loc[mask, 'symbol']])
            for i, a in enumerate(ALPHAS):
                rows.append({'target': target, 'market': mkt_scope,
                             'alpha': a, 'model_pinball': pinball_loss(y, mp[:, i], a),
                             'baseline_pinball': pinball_loss(y, bp[:, i], a)})
            cov = float(np.mean((y >= mp[:, 0]) & (y <= mp[:, 2])))
            width = float(np.median(mp[:, 2] - mp[:, 0]))
            rows.append({'target': target, 'market': mkt_scope,
                         'alpha': 'coverage', 'model_pinball': cov,
                         'baseline_pinball': np.nan})
            rows.append({'target': target, 'market': mkt_scope,
                         'alpha': 'width_med', 'model_pinball': width,
                         'baseline_pinball': np.nan})
    res = pd.DataFrame(rows)
    res.to_csv(f'{out_dir}/quantile_results.csv', index=False)

    def ok(t, m):
        r = res[(res['target'] == t) & (res['market'] == m)]
        pin = r[r['alpha'].isin(ALPHAS)]
        model_pin = pin['model_pinball'].astype('float64').mean()
        base_pin = pin['baseline_pinball'].astype('float64').mean()
        cov = r[r['alpha'] == 'coverage']['model_pinball'].astype('float64').iloc[0]
        return model_pin < base_pin, 0.75 <= cov <= 0.85, model_pin, base_pin, cov

    verdict = 'PASS'
    lines = []
    for t in TARGETS:
        for m in ('CAD', 'USD'):
            better, cov_ok, mp_, bp_, cov = ok(t, m)
            lines.append(f"{t} | {m}: model_pin {mp_:.3f} vs base_pin {bp_:.3f} "
                          f"(better={better}) coverage={cov:.3f} "
                          f"(in-range={cov_ok})")
            if not (better and cov_ok):
                verdict = 'FAIL'
    with open(f'{out_dir}/QUANTILE_MODEL.md', 'w') as f:
        f.write('# WI-025 quantile model of rally (MFE) and drawdown (MAE)\n\n')
        f.write('CALIB date < %s; EVAL date >= %s; '
                'XGB reg:quantileerror q10/q50/q90 vs per-symbol empirical '
                'baseline (global fallback < %d CALIB events).\n\n'
                % (CALIB_END, EVAL_START, MIN_CALIB))
        for ln in lines:
            f.write(ln + '\n')
        f.write(f'\nVERDICT: {verdict}\n')
    return verdict


def main(out_dir='reports/fib_swings'):
    d = load_data(out_dir)
    verdict = evaluate(d, out_dir)
    print('rows:', len(d), flush=True)
    print('VERDICT:', verdict, flush=True)
    print('EXIT:0', flush=True)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='WI-025 fib quantile model')
    ap.add_argument('--out', default='reports/fib_swings')
    main(ap.parse_args().out)