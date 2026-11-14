"""WI-030 tests: oracle labels, purge, horizon prior, smoke end-to-end."""
import numpy as np
import pandas as pd
import pytest

from scripts import fib_exit_policy as fep

POLICIES = [f'{t}_{s}_{d}_{e}' for t in ('t10', 't15')
            for s in ('s5', 's8', 's10', 'satr')
            for d in ('d20', 'd39') for e in ('close', 'next_open')]
BEST = 't10_s5_d20_close'
SECOND = 't15_s5_d39_next_open'


def _fixture(tmp_path):
    rng = np.random.default_rng(3)
    spec = [('AAA', 'CAD'), ('BBB', 'USD'), ('CCC', 'CAD')]
    dates = list(pd.date_range('2020-01-01', periods=40, freq='18D')) \
        + list(pd.date_range('2022-08-01', periods=6, freq='30D'))
    feats, labels = [], []
    for i, ts in enumerate(dates):
        sym, mkt = spec[i % 3]
        date = ts.strftime('%Y-%m-%d')
        row = {'symbol': sym, 'market': mkt, 'date': date}
        for f in fep.FEATURES:
            row[f] = float(rng.normal())
        row['is_usd'] = 1.0 if mkt == 'USD' else 0.0
        row['screen_bottom'] = float(rng.integers(0, 2))
        feats.append(row)
        for p in POLICIES:
            ret = -0.01 + 0.004 * rng.normal()
            if p == BEST:
                ret = 0.06 + 0.003 * rng.normal()
            elif p == SECOND:
                ret = 0.04 + 0.003 * rng.normal()
            labels.append({'symbol': sym, 'market': mkt, 'date': date,
                           'screen_bottom': bool(row['screen_bottom']),
                           'policy': p, 'ret': np.float32(ret),
                           'reason': 'target' if ret > 0 else 'stop',
                           'days': np.int16(10)})
    pd.DataFrame(feats).to_parquet(tmp_path / 'event_features.parquet')
    pd.DataFrame(labels).to_parquet(tmp_path / 'trade_labels_w39.parquet')
    reg = pd.DataFrame(feats)[['market', 'date']].drop_duplicates()
    reg['regime'] = ['up_normal', 'down_high', 'chop_normal'][:len(reg)] \
        if len(reg) < 3 else np.resize(
            ['up_normal', 'down_high', 'chop_normal'], len(reg))
    reg.to_csv(tmp_path / 'regime_daily_extended.csv', index=False)
    pd.DataFrame([
        {'target': 'fwd_mfe_pct', 'market': 'CAD', 'alpha': 0.5,
         'model_pinball': 4.0, 'baseline_pinball': 4.5},
        {'target': 'fwd_mfe_pct', 'market': 'USD', 'alpha': 0.5,
         'model_pinball': 6.0, 'baseline_pinball': 6.5},
    ]).to_csv(tmp_path / 'quantile_results.csv', index=False)
    return tmp_path


def test_oracle_labels_argmax():
    lab = pd.DataFrame({
        'symbol': ['A'] * 4, 'market': ['CAD'] * 4,
        'date': ['2020-01-01'] * 4,
        'policy': ['p0', 'p1', 'p2', 'p3'],
        'ret': np.array([0.01, -0.02, 0.03, np.nan], dtype='float32')})
    out = fep.oracle_labels(lab)
    assert len(out) == 1
    assert out.iloc[0]['oracle_policy'] == 'p2'


def test_purge_keep_excludes_buffer():
    dates = pd.Series(['2020-01-01', '2020-02-15', '2020-06-01'])
    keep = fep.purge_keep(dates, '2020-01-01', '2020-03-01', days=60)
    assert keep.tolist() == [False, False, True]


def test_horizon_map_threshold(tmp_path):
    _fixture(tmp_path)
    hmap = fep.horizon_map(str(tmp_path))
    assert hmap == {'CAD': 20, 'USD': 39}


def test_fit_predict_expands_sparse_classes():
    x = np.zeros((20, 3), dtype='float32')
    y = np.array([0] * 10 + [5] * 10)
    p = fep.fit_predict(x, y, x[:4], n_classes=8, n_trees=5)
    assert p.shape == (4, 8)
    assert np.allclose(p.sum(axis=1), 1.0)


def test_main_smoke_end_to_end(tmp_path):
    _fixture(tmp_path)
    fep.main(str(tmp_path), smoke=True)
    learned = pd.read_csv(tmp_path / 'exit_policy_learned.csv')
    md = (tmp_path / 'EXIT_POLICY.md').read_text()
    assert set(learned['period']) == {'CALIB', 'EVAL'}
    assert learned['fold'].nunique() == fep.N_BLOCKS + 1
    assert learned['chosen_ret'].notna().all()
    assert 'fold-stable: ' in md and 'VERDICT: ' in md
    assert set(learned['chosen_policy']).issubset(set(POLICIES))