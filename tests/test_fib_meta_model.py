"""WI-024 tests (synthetic data only): purge window, prior shrinkage ignoring
EVAL rows, monotone vector, null-policy BLOCKED_PRECONDITION verdict."""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from scripts import fib_event_features as fef
from scripts import fib_meta_model as fmm


def test_purge_removes_rows_within_60_days():
    dates = pd.to_datetime(['2020-10-01', '2021-03-15', '2021-05-15', '2021-09-01'])
    mask = fmm.purge_keep_mask(dates, '2021-04-01', '2021-04-30')
    assert mask.tolist() == [True, False, False, True]
    # rows inside the +/-60d window drop; 61+ days after the block stays
    edge_in = fmm.purge_keep_mask(pd.to_datetime(['2021-05-30', '2021-07-01']),
                                  '2021-04-01', '2021-04-30')
    assert edge_in.tolist() == [False, True]


def test_prior_p_medplus_ignores_eval_rows():
    ev = pd.DataFrame({
        'symbol': ['A', 'A', 'A', 'B', 'B'],
        'date': ['2021-01-04', '2021-03-04', '2021-05-04',
                 '2021-02-04', '2021-06-04'],
        'type': 'bottom',
        'fwd_mfe_pct': [25.0, 5.0, 50.0, 30.0, 10.0]})
    p1 = fef.prior_p_medplus(ev)
    # shrink math: g = 3/5; A: (2+10g)/(3+10) = 8/13; B: (1+10g)/(2+10) = 7/12
    assert np.isclose(p1['A'], 8 / 13)
    assert np.isclose(p1['B'], 7 / 12)
    extra = pd.concat([ev, pd.DataFrame({
        'symbol': ['A', 'C'], 'date': ['2022-08-01', '2022-09-01'],
        'type': 'bottom', 'fwd_mfe_pct': [99.0, 99.0]})], ignore_index=True)
    p2 = fef.prior_p_medplus(extra)
    assert np.isclose(p2['A'], p1['A'])
    assert np.isclose(p2['B'], p1['B'])


def test_monotone_vector_matches_features():
    assert len(fmm.FEATURES) == 16
    assert len(fmm.MONOTONE) == len(fmm.FEATURES)
    for f, m in zip(fmm.FEATURES, fmm.MONOTONE):
        assert m == (-1 if f in ('rsi_f63', 'spread15_39') else 0)


def test_null_policy_writes_blocked_verdict(tmp_path):
    (tmp_path / 'exit_policy_choice.json').write_text(
        json.dumps({'policy': None, 'reason': 'NO_POLICY_CLEARS',
                    'calib_mean_ret': None}))
    fmm.main(str(tmp_path))
    md = (tmp_path / 'META_MODEL.md').read_text()
    assert 'VERDICT: BLOCKED_PRECONDITION (no exit policy cleared)' in md