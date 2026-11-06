"""WI-021 accounting tests for scripts/fib_walkforward.py — synthetic data only.

Never reads files under data/, never invokes main()/the full-universe job.
"""
import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
import fib_walkforward as fw  # noqa: E402


def test_symbol_from_path():
    # (a) symbol= prefix stripped; market= taken from the parent dir name
    assert fw.symbol_from_path(
        'data/raw_ohlcv/market=CAD/symbol=RY.parquet') == ('RY', 'CAD')


def _flat_tail_frame(n=400):
    close = np.concatenate([np.linspace(200.0, 100.0, 200), np.full(200, 100.0)])
    return pd.DataFrame({
        'date': pd.date_range('2015-01-01', periods=n, freq='D').astype(str),
        'close': close, 'high': close, 'low': close})


def test_bottom_events_and_unresolved_tail_grades():
    # (b) 400-bar falling-then-flat series
    df = _flat_tail_frame()
    events = fw.events_for_symbol(df, 'TEST', 'TEST')
    bottoms = [e for e in events if e['type'] == 'bottom']
    assert len(bottoms) >= 1
    tail_dates = set(df['date'].astype(str).to_numpy()[-fw.W:])
    tail_events = [e for e in events if e['date'] in tail_dates]
    assert tail_events, 'expected clustered events inside the last 39 bars'
    assert all(e['grade'] is None for e in tail_events)   # Fix 2: never 'weak'


def _row(**kw):
    base = dict(symbol='X', market='MKT', date='2023-01-01', type='bottom',
                rsi_f63=50.0, spread15_39=0.0, bbw_ratio=1.0,
                fwd_mfe_pct=10.0, fwd_mae_pct=-5.0, fwd_ret_pct=1.0,
                screen_bottom=False, screen_top=False, grade='weak')
    base.update(kw)
    return base


def test_stats_resolved_rows_only_bottom():
    # (c) 3 resolved base rows (2 screened+resolved, 1 unscreened) + 1
    # unresolved screened row whose fwd_ret_pct is still non-NaN.
    df = pd.DataFrame([
        _row(date='2023-01-01', rsi_f63=30.0, spread15_39=-12.0,
             fwd_mfe_pct=25.0, fwd_ret_pct=10.0, screen_bottom=True, grade='med'),
        _row(date='2023-01-02', rsi_f63=35.0, spread15_39=-9.0,
             fwd_mfe_pct=5.0, fwd_ret_pct=1.0, screen_bottom=True, grade='weak'),
        _row(date='2023-01-03', rsi_f63=50.0, spread15_39=0.0,
             fwd_mfe_pct=40.0, fwd_ret_pct=20.0, screen_bottom=False, grade='strong'),
        _row(date='2023-01-04', rsi_f63=20.0, spread15_39=-20.0,
             fwd_mfe_pct=np.nan, fwd_mae_pct=np.nan, fwd_ret_pct=3.0,
             screen_bottom=True, grade=None),
    ])
    s = fw.stats(df, 'bottom')
    assert s['outcome_metric'] == 'mfe>=19.5'
    assert s['n_events'] == 4            # all base rows, resolved or not
    assert s['n_screened'] == 3          # all screened rows, resolved or not
    assert s['flag_rate'] == pytest.approx(0.75)
    # resolved base rows only: hits 25 True, 5 False, 40 True -> 2/3 (not 2/4)
    assert s['base_rate_medplus'] == pytest.approx(2 / 3)
    # resolved screened rows only: 25 True, 5 False -> 1/2 (not 1/3)
    assert s['screen_rate_medplus'] == pytest.approx(0.5)
    assert s['fwd_mfe_base_med'] == pytest.approx(25.0)
    assert s['fwd_mfe_screened_med'] == pytest.approx(15.0)
    # medians exclude the unresolved row even though its fwd_ret_pct=3.0
    assert s['fwd_ret_base_med'] == pytest.approx(10.0)      # not 6.5
    assert s['fwd_ret_screened_med'] == pytest.approx(5.5)   # not 3.0


def test_stats_top_side_uses_fwd_mae():
    # (d) side 'top' outcome is fwd_mae_pct; unresolved row has fwd_mfe_pct=50
    df = pd.DataFrame([
        _row(date='2023-01-01', type='top', rsi_f63=70.0, spread15_39=9.0,
             fwd_mae_pct=-25.0, fwd_mfe_pct=10.0, fwd_ret_pct=-10.0,
             screen_top=True, grade='med'),
        _row(date='2023-01-02', type='top', rsi_f63=65.0, spread15_39=8.0,
             fwd_mae_pct=-5.0, fwd_mfe_pct=30.0, fwd_ret_pct=-1.0,
             screen_top=True, grade='weak'),
        _row(date='2023-01-03', type='top', rsi_f63=55.0, spread15_39=2.0,
             fwd_mae_pct=-40.0, fwd_mfe_pct=2.0, fwd_ret_pct=-20.0,
             screen_top=False, grade='strong'),
        _row(date='2023-01-04', type='top', rsi_f63=75.0, spread15_39=12.0,
             fwd_mae_pct=np.nan, fwd_mfe_pct=50.0, fwd_ret_pct=np.nan,
             screen_top=True, grade=None),
    ])
    s = fw.stats(df, 'top')
    assert s['outcome_metric'] == 'mae<=-19.5'
    assert s['n_events'] == 4
    assert s['n_screened'] == 3
    # fwd_mae_pct <= -19.5 on resolved base: -25 True, -5 False, -40 True -> 2/3
    # (using fwd_mfe_pct>=19.5 instead would give 1/2)
    assert s['base_rate_medplus'] == pytest.approx(2 / 3)
    # resolved screened only (rows 1,2): 1/2; the unresolved row 4 is excluded
    # despite fwd_mfe_pct=50 (wrong column or no ok-filter -> 2/3 or 1/3)
    assert s['screen_rate_medplus'] == pytest.approx(0.5)
