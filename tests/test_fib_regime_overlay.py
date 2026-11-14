"""Synthetic tests for scripts/fib_regime_overlay.py (WI-022); no data/ or reports/ reads.

1. tercile cut points come from CALIB (<2022-05-02) dates only: altering EVAL rows cannot
   move the cuts or the CALIB event labels (no leakage into the frozen gate choice);
2. 63d breadth on a 3-symbol fixture equals a hand count;
3. choose_rule returns 'NONE' when no candidate set has 5 positive CALIB fold edges.
"""
import os
import sys

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scripts'))
import fib_regime_overlay as fr


def _daily_fixture():
    """Deterministic per-(market, date) regime series spanning CALIB and EVAL dates."""
    dates = pd.date_range('2021-01-01', '2023-12-31', freq='D').strftime('%Y-%m-%d')
    x = np.arange(len(dates), dtype=float)
    return pd.DataFrame({'market': 'US', 'date': dates, 'r1': np.sin(x / 23.0),
                         'r1_s5': np.sin(x / 23.0) + 0.25, 'r2': 0.5 + 0.3 * np.cos(x / 17.0),
                         'n_tickers': 9})


def test_tercile_cuts_unchanged_when_eval_rows_altered():
    daily = _daily_fixture()
    cal_mask = pd.to_datetime(daily['date']) < fr.CALIB_END
    ev_mask = pd.to_datetime(daily['date']) >= fr.EVAL_START
    assert cal_mask.sum() > 50 and ev_mask.sum() > 50
    cal = daily[cal_mask]
    cuts = {}
    for col in ('r1_s5', 'r2'):
        q1, q2 = cal[col].quantile(1 / 3), cal[col].quantile(2 / 3)
        cuts[col] = fr.tercile_cuts(daily, 'US', col)
        assert cuts[col] == pytest.approx((q1, q2))  # CALIB-dates-only quantiles
    # alter EVAL rows (values and row count): cuts must not move
    mut = daily.copy()
    mut.loc[ev_mask, ['r1_s5', 'r2']] = mut.loc[ev_mask, ['r1_s5', 'r2']] * 1000.0 + 7.0
    mut = mut[~(ev_mask & (np.arange(len(mut)) % 2 == 0))]
    assert len(mut) < len(daily) and mut['r1_s5'].max() > 100.0
    for col in ('r1_s5', 'r2'):
        assert fr.tercile_cuts(mut, 'US', col) == pytest.approx(cuts[col])
        full = (mut[col].quantile(1 / 3), mut[col].quantile(2 / 3))
        assert cuts[col] != pytest.approx(full)  # proves CALIB-only, not full-sample
    # CALIB event labels (sparse event dates) are stable under the EVAL mutation
    ev = pd.DataFrame({'market': 'US', 'date': cal['date'].to_numpy()[::10]})
    lab, lab2 = fr.add_terciles(ev, daily), fr.add_terciles(ev, mut)
    assert list(lab['r1_terc']) == list(lab2['r1_terc'])
    assert list(lab['r2_terc']) == list(lab2['r2_terc'])
    assert set(lab['r1_terc']) == {'T1', 'T2', 'T3'}
    q1, q2 = cuts['r1_s5']
    expect = ['T1' if x <= q1 else 'T2' if x <= q2 else 'T3' for x in lab['r1_s5']]
    assert list(lab['r1_terc']) == expect


def _write_ohlcv(path, closes):
    dates = pd.date_range('2021-01-01', periods=len(closes), freq='D').strftime('%Y-%m-%d')
    c = np.asarray(closes, dtype=float)
    df = pd.DataFrame({'date': dates, 'open': c, 'high': c + 1.0, 'low': c - 1.0,
                       'close': c, 'volume': np.full(len(c), 100.0)})
    pq.write_table(pa.Table.from_pandas(df), path)


def test_breadth_equals_hand_count_on_3_symbol_fixture(tmp_path, monkeypatch):
    monkeypatch.delenv('FIB_SMOKE', raising=False)
    n = 70
    up = np.arange(1, n + 1, dtype=float)    # rising: close > 63d mean wherever defined
    down = np.arange(n, 0, -1, dtype=float)  # falling: close < 63d mean everywhere
    flat = np.full(n, 50.0)                  # flat: close == 63d mean -> never above
    for market, sym, closes in (('market=US', 'A', up), ('market=US', 'B', down),
                                ('market=CAD', 'C', flat)):
        d = tmp_path / market
        d.mkdir(parents=True, exist_ok=True)
        _write_ohlcv(d / f'symbol={sym}.parquet', closes)
    out = tmp_path / 'out'
    out.mkdir()
    files = sorted(str(p) for p in tmp_path.glob('market=*/symbol=*.parquet'))
    daily = fr.build_regime_daily(str(out), files=files)
    assert list(pd.read_csv(out / 'regime_daily.csv').columns) \
        == ['market', 'date', 'r1', 'r1_s5', 'r2', 'n_tickers']

    def row(mk, date):
        r = daily[(daily['market'] == mk) & (daily['date'] == date)]
        assert len(r) == 1
        return r.iloc[0]

    def dstr(k):
        return (pd.Timestamp('2021-01-01') + pd.Timedelta(days=k)).strftime('%Y-%m-%d')

    # last bar (t=69): 39 bars and 63 bars exist for all 3 symbols
    assert row('ALL', dstr(69)).n_tickers == 2      # A, B (flat C: sd3=sd39=0 -> bbw NaN)
    assert row('ALL', dstr(69)).r2 == pytest.approx(1 / 3)  # above63: A only; valid63: 3
    assert row('US', dstr(69)).n_tickers == 2
    assert row('US', dstr(69)).r2 == pytest.approx(1 / 2)   # A above its mean, B below
    rc = row('CAD', dstr(69))
    assert rc.n_tickers == 0 and rc.r2 == pytest.approx(0.0) and np.isnan(rc.r1)

    def bbw(cl):
        w3, w39 = np.asarray(cl[-3:]), np.asarray(cl[-39:])
        return (4 * np.std(w3, ddof=1) / np.mean(w3)) / (4 * np.std(w39, ddof=1) / np.mean(w39))

    exp_r1 = (np.log(bbw(up)) + np.log(bbw(down))) / 2.0
    assert row('US', dstr(69)).r1 == pytest.approx(exp_r1, rel=1e-9)
    assert row('ALL', dstr(69)).r1 == pytest.approx(exp_r1, rel=1e-9)
    # t=38 (39 bars first available): 2 finite-log tickers, no 63d window yet
    r38 = row('ALL', dstr(38))
    assert r38.n_tickers == 2 and np.isnan(r38.r2)
    # t=10: no bbw window and no 63d window yet
    r10 = row('ALL', dstr(10))
    assert r10.n_tickers == 0 and np.isnan(r10.r1) and np.isnan(r10.r2)
    # r1_s5 = 5-row rolling mean of r1 within each market
    us = daily[daily['market'] == 'US'].sort_values('date').reset_index(drop=True)
    assert us['r1_s5'].iloc[-1] == pytest.approx(us['r1'].tail(5).mean(), rel=1e-9)


def _calib_frame(fwd):
    """30 resolved+screened CALIB bottoms, terciles cycling T1,T2,T3 (10 each)."""
    dates = pd.date_range('2021-01-04', periods=30, freq='D').strftime('%Y-%m-%d')
    terc = [('T1', 'T2', 'T3')[i % 3] for i in range(30)]
    return pd.DataFrame({'market': 'US', 'date': dates, 'screen_bottom': True,
                         'fwd_mfe_pct': fwd, 'r1_terc': terc, 'r2_terc': terc})


def test_choose_rule_none_when_no_set_has_five_positive_folds():
    # every outcome fails (0.0 < 19.5): all fold edges are exactly 0 -> nothing eligible
    assert fr.choose_rule(_calib_frame(np.zeros(30)), 'r1_terc') == 'NONE'
    assert fr.choose_rule(_calib_frame(np.zeros(30)), 'r2_terc') == 'NONE'
    # T3 bottoms hit in 4 of 5 folds only (fold 3 = idx 12..17 misses): every candidate
    # set has at most 4 positive fold edges -> still NONE
    fwd = np.where(np.arange(30) % 3 == 2, 25.0, 0.0)
    fwd[[14, 17]] = 0.0
    assert fr.choose_rule(_calib_frame(fwd), 'r1_terc') == 'NONE'
    # positive control: T3 hits in all 5 folds -> {T3} chosen (max mean fold edge)
    assert fr.choose_rule(_calib_frame(np.where(np.arange(30) % 3 == 2, 25.0, 0.0)),
                          'r1_terc') == {'T3'}
