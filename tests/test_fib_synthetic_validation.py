"""WI-031 tests — synthetic data only (no data/ or reports/ reads)."""
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                '..', 'scripts'))
import fib_synthetic_validation as fsv  # noqa: E402
import fib_trade_labels as ftl  # noqa: E402
import fib_meta_model as fmm  # noqa: E402
import fib_entry_window as few  # noqa: E402

SMALL = dict(n_symbols=3, n_days=200, n_seeds=2)


def test_gate_code_is_imported_not_reimplemented():
    """The gate under test must be the REAL production code, not a copy."""
    assert fsv.group_stats is ftl.group_stats
    assert fsv.simulate is ftl.simulate
    assert fsv.ensemble_mean is few.ensemble_mean
    assert fsv.purge_keep_mask is fmm.purge_keep_mask


def test_scenario_edge_masks():
    n = 4000
    assert not fsv.edge_active('NULL', n).any()
    assert fsv.edge_active('CONSTANT', n).all()
    ch = fsv.edge_active('CHAOTIC', n)
    blocks = (np.arange(n) // (n // 25)) % 5
    assert set(np.unique(blocks[ch])) == {0, 2, 4}
    assert 0.55 < ch.mean() < 0.65


def test_generator_determinism_and_float32():
    d1, m1 = fsv.simulate_market('NULL', 7, 3, 200)
    d2, m2 = fsv.simulate_market('NULL', 7, 3, 200)
    assert len(d1) == 200 and len(m1) == 3
    for sym in m1:
        for k in 'ohlc':
            assert m1[sym][k].dtype == np.float32
            assert np.array_equal(m1[sym][k], m2[sym][k])
        assert m1[sym]['market'] in ('CAD', 'USD')
    # same seeded path across scenarios; only the planted-edge mask differs
    _, mc = fsv.simulate_market('CONSTANT', 7, 3, 200)
    assert np.array_equal(m1['S000']['c'], mc['S000']['c'])
    assert not np.array_equal(m1['S000']['active'], mc['S000']['active'])


def test_planted_edge_changes_labels():
    dates, m0 = fsv.simulate_market('NULL', 3, 2, 400)
    _, m1 = fsv.simulate_market('CONSTANT', 3, 2, 400)
    r0 = np.array([r[5] for r in fsv.market_labels('S000', m0['S000'], dates)],
                  dtype='float64')
    r1 = np.array([r[5] for r in fsv.market_labels('S000', m1['S000'], dates)],
                  dtype='float64')
    assert len(r0) == len(r1) > 0
    assert not np.allclose(r0, r1)


def test_build_labels_columns_and_dtypes():
    dates, mkts = fsv.simulate_market('CONSTANT', 1, 3, 400)
    ev = fsv.build_labels(dates, mkts)
    assert len(ev) > 0
    for col in ('symbol', 'date', 'market', 'screen_bottom', 'ret', 'hit'):
        assert col in ev.columns
    assert ev['ret'].dtype == np.float32
    assert set(ev['market']) <= {'CAD', 'USD'}


def test_variant_accepts_matrix():
    ok = dict(mean_ret=0.02, pooled_mean=0.01, pooled_t=3.0)
    strict = fsv.variant_accepts(dict(ok, n_folds_pos=5))
    assert strict['strict_5of5'] and strict['loose_3of5_pooled']
    four = fsv.variant_accepts(dict(ok, n_folds_pos=4))
    assert not four['strict_5of5']
    assert four['loose_4of5'] and four['loose_4of5_pooled']
    three = fsv.variant_accepts(dict(ok, n_folds_pos=3))
    assert three['loose_3of5_pooled'] and not three['loose_4of5']
    no_edge = fsv.variant_accepts(dict(mean_ret=-0.01, pooled_mean=-0.01,
                                       pooled_t=0.5, n_folds_pos=5))
    assert not any(no_edge.values())
    weak_t = fsv.variant_accepts(dict(ok, pooled_t=1.5, n_folds_pos=2))
    assert not weak_t['pooled_only_t2']


def test_pooled_oof_runs_and_is_finite_or_nan():
    dates, mkts = fsv.simulate_market('NULL', 2, 3, 400)
    ev = fsv.build_labels(dates, mkts)
    cut = dates[int(0.6 * 400)]
    cal = ev[(ev['date'] < cut) & ev['ret'].notna()]
    out = fsv.pooled_oof(cal)
    assert set(out) == {'pooled_mean', 'pooled_t', 'n_oof'}
    assert isinstance(out['n_oof'], int)


def test_evaluate_seed_rows():
    rows = fsv.evaluate_seed('NULL', 0, SMALL['n_symbols'], SMALL['n_days'])
    assert len(rows) == len(fsv.VARIANTS)
    assert {r['variant'] for r in rows} == set(fsv.VARIANTS)
    assert all(r['accept'] in (0, 1) for r in rows)


def test_end_to_end_outputs(tmp_path):
    out = str(tmp_path)
    fsv.main(out, SMALL['n_symbols'], SMALL['n_days'], SMALL['n_seeds'])
    csv = os.path.join(out, 'gate_comparison.csv')
    md = os.path.join(out, 'SYNTHETIC_VALIDATION.md')
    assert os.path.exists(csv) and os.path.exists(md)
    import pandas as pd
    df = pd.read_csv(csv, keep_default_na=False, na_values=[''])
    assert len(df) == 3 * len(fsv.VARIANTS) * SMALL['n_seeds']
    assert set(df['scenario']) == {'NULL', 'CONSTANT', 'CHAOTIC'}
    assert df['accept_rate'].between(0, 1).all()
    body = open(md).read()
    assert 'VERDICT: ADOPT_' in body and 'Calibration check' in body