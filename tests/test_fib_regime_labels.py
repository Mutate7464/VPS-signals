"""Synthetic tests for scripts/fib_regime_labels.py (WI-027 2g); no data/ or
reports/ reads — synthetic frames only.

Covers: trend categories (point-in-time, flat-noise filter), volatility
categories (CALIB-frozen cut points), the (market, date) regime join with
WI-023 group_stats fold reuse, and fold5 isolation -> VERDICT PASS detection.
"""
import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                '..', 'scripts'))
import fib_regime_labels as frl


def make_events(rows):
    """Synthetic bottom-event frame; grade from fwd_mfe_pct (WI-021 convention)."""
    df = pd.DataFrame(rows, columns=['symbol', 'market', 'date', 'screen_bottom',
                                     'fwd_mfe_pct', 'fwd_ret_pct'])
    df['type'] = 'bottom'
    df['grade'] = [None if not np.isfinite(m) else
                   ('strong' if m >= 33.9 else ('med' if m >= 19.5 else 'weak'))
                   for m in df['fwd_mfe_pct']]
    return df


def test_trend_categories():
    assert frl.trend_category(0.05, 0.02) == 'up'
    assert frl.trend_category(0.002, -0.01) == 'chop'      # mixed signs
    assert frl.trend_category(-0.05, -0.02) == 'down'
    assert frl.trend_category(0.0005, 0.02) == 'chop'      # flat-noise |ret63|<=0.001
    assert frl.trend_category(-0.0005, -0.02) == 'chop'
    assert frl.trend_category(np.nan, 0.02) == 'chop'      # insufficient history
    n = 200
    up = np.linspace(100.0, 260.0, n)
    lab = [frl.trend_label_at(up, t) for t in range(n)]
    assert lab[:63] == ['chop'] * 63                       # no 63d history yet
    assert lab[63:126] == ['chop'] * 63                   # 63d known, 126d not
    assert set(lab[126:]) == {'up'}                        # both windows green
    down = np.linspace(260.0, 100.0, n)
    assert {frl.trend_label_at(down, t) for t in range(126, n)} == {'down'}
    assert {frl.trend_label_at(np.full(n, 100.0), t)
            for t in range(126, n)} == {'chop'}           # flat -> near-zero -> chop

    class Rec(list):                                      # point-in-time probe
        def __init__(self, vals):
            super().__init__(vals)
            self.hits = []

        def __getitem__(self, i):
            self.hits.append(int(i))
            return list.__getitem__(self, i)

    rec = Rec(up.tolist())
    for t in (126, 150, 199):
        rec.hits.clear()
        assert frl.trend_label_at(rec, t) == 'up'
        assert rec.hits and max(rec.hits) <= t            # never touches future rows


def test_vol_categories():
    cuts = {'atrp63': 0.02, 'vol21': 0.30}
    assert frl.vol_category(0.03, 0.40, cuts) == 'high'   # both above cuts
    assert frl.vol_category(0.03, 0.20, cuts) == 'normal'  # only atrp63 above
    assert frl.vol_category(0.01, 0.40, cuts) == 'normal'  # only vol21 above
    assert frl.vol_category(0.01, 0.20, cuts) == 'normal'   # both below
    assert frl.vol_category(0.02, 0.30, cuts) == 'normal'   # strict > cut
    assert frl.vol_category(np.nan, 0.40, cuts) == 'normal'
    daily = pd.DataFrame({
        'market': ['CAD'] * 5 + ['USD'] * 3,
        'date': ['2021-01-04', '2021-01-05', '2021-06-01', '2022-05-02', '2022-06-01',
                 '2021-02-01', '2021-02-02', '2021-02-03'],
        'atrp63': [0.010, 0.020, 0.030, 0.040, 0.050, 0.9, 0.9, 0.9],
        'vol21': [0.100, 0.200, 0.300, 0.400, 0.500, 0.9, 0.9, 0.9]})
    cu = frl.frozen_cuts(daily, 'CAD')
    assert cu['atrp63'] == pytest.approx(0.020)            # CALIB CAD rows only
    assert cu['vol21'] == pytest.approx(0.200)             # (2022-05-02+ excluded,
    assert frl.vol_category(0.025, 0.35, cu) == 'high'     #  USD rows never leak)
    recomputed = {'atrp63': float(np.median([0.010, 0.020, 0.030, 0.040, 0.050])),
                  'vol21': float(np.median([0.100, 0.200, 0.300, 0.400, 0.500]))}
    # a value between the frozen and the recomputed medians keeps the FROZEN label:
    # the cut point is never recomputed on EVAL dates
    assert frl.vol_category(0.025, 0.35, recomputed) == 'normal'


def test_regime_join(monkeypatch):
    calls = []
    real = frl.group_stats

    def spy(g, period):
        calls.append((len(g), period))
        return real(g, period)

    monkeypatch.setattr(frl, 'group_stats', spy)
    lab = pd.DataFrame({
        'market': ['CAD'] * 3 + ['USD'] * 3,
        'date': ['2021-01-04', '2021-01-05', '2021-01-06'] * 2,
        'regime': ['chop_normal'] * 3 + ['up_normal'] * 3})
    ev = make_events([
        ('A', 'CAD', '2021-01-04', True, 25.0, 2.0),    # resolved, grade med
        ('B', 'CAD', '2021-01-05', False, 10.0, -1.0),  # not screened
        ('C', 'CAD', '2021-01-06', True, 5.0, -3.0),    # resolved, grade weak
        ('D', 'USD', '2021-01-04', True, 30.0, 4.0),    # own-market label up_normal
        ('E', 'USD', '2021-01-05', True, np.nan, np.nan),  # unresolved screened
        ('F', 'CAD', '2022-07-01', True, 20.0, 1.0)])     # EVAL: outside CALIB
    edge = frl.edge_table(ev, lab)
    assert calls and all(p == 'CALIB' for _, p in calls)  # group_stats reused
    r = edge.set_index(['regime', 'market'])
    # own-market join: CAD rows carry chop_normal, USD rows up_normal
    assert r.loc[('chop_normal', 'CAD'), 'n_events'] == 3
    assert r.loc[('up_normal', 'USD'), 'n_events'] == 2
    assert r.loc[('up_normal', 'USD'), 'n_screened'] == 2  # unresolved still counted
    assert r.loc[('up_normal', 'CAD'), 'n_events'] == 0    # no cross-market leak
    assert r.loc[('chop_normal', 'USD'), 'n_events'] == 0
    assert r.loc[('chop_normal', 'CAD'), 'screen_rate'] == pytest.approx(2 / 3)
    assert edge[edge['market'] == 'ALL']['n_events'].sum() == 5  # EVAL row excluded
    # base = all-regime resolved rate per market; screen_rate_medplus resolved only
    assert r.loc[('chop_normal', 'CAD'), 'base_rate_medplus'] == pytest.approx(1 / 3)
    assert r.loc[('chop_normal', 'CAD'), 'screen_rate_medplus'] == pytest.approx(0.5)
    assert r.loc[('chop_normal', 'CAD'), 'edge_pp'] == pytest.approx(
        (0.5 - 1 / 3) * 100, rel=1e-5)
    assert r.loc[('chop_normal', 'ALL'), 'base_rate_medplus'] == pytest.approx(0.5)
    assert r.loc[('chop_normal', 'ALL'), 'screen_rate_medplus'] == pytest.approx(0.5)
    assert r.loc[('chop_normal', 'ALL'), 'mean_39d_fwd_ret'] == pytest.approx(-0.5)
    # folds: reuse group_stats machinery — fold count and sign agreement
    from fib_trade_labels import group_stats
    scr = ev[ev['screen_bottom'] & ev['fwd_mfe_pct'].notna()
             & (ev['date'] < '2022-05-02')]
    grp = scr[scr['market'] == 'CAD']                  # == pooled chop_normal group
    gg = pd.DataFrame({'date': grp['date'].to_numpy(),
                       'ret': grp['fwd_ret_pct'].astype('float64').to_numpy(),
                       'reason': grp['grade'].to_numpy()})
    gs = group_stats(gg, 'CALIB')
    row = r.loc[('chop_normal', 'ALL')]
    for k in range(1, 6):
        assert row['fwd_ret_fold%d_mean' % k] == pytest.approx(
            gs['fold%d_mean' % k], nan_ok=True)
    assert row['n_folds_pos'] == gs['n_folds_pos']
    srt = grp.sort_values('date', kind='mergesort')
    manual = [float(srt['fwd_ret_pct'].to_numpy()[b].mean()) if len(b) else np.nan
              for b in np.array_split(np.arange(len(srt)), 5)]
    for k in range(1, 6):
        assert row['fwd_ret_fold%d_mean' % k] == pytest.approx(manual[k - 1],
                                                               nan_ok=True)
    assert row['n_folds_pos'] == int(sum(m > 0 for m in manual)) == 1


def _iso_events(chop_last_ret=1.0):
    """25 synthetic CAD bottoms: 20 chop_normal (Jan) + 5 down_normal (Jun, last)."""
    chop = [('S%02d' % i, 'CAD', '2021-01-%02d' % (i + 1), True, 25.0,
             (chop_last_ret if i == 19 else 1.0)) for i in range(20)]
    down = [('D%02d' % i, 'CAD', '2021-06-%02d' % (i + 1), True, 5.0, -1.0)
            for i in range(5)]
    return make_events(chop + down)


def _iso_labels():
    return pd.DataFrame({
        'market': ['CAD'] * 25,
        'date': ['2021-01-%02d' % (i + 1) for i in range(20)]
                + ['2021-06-%02d' % (i + 1) for i in range(5)],
        'regime': ['chop_normal'] * 20 + ['down_normal'] * 5})


def test_fold5_isolation():
    ev, lab = _iso_events(), _iso_labels()
    edge = frl.edge_table(ev, lab)
    d0, d1, f5r = frl.fold5_summary(ev, lab)
    assert (d0, d1) == ('2021-06-01', '2021-06-05')        # fold5 = last block
    assert f5r == {'down_normal': 5}                        # isolated to one regime
    r = edge.set_index(['regime', 'market'])
    assert r.loc[('chop_normal', 'ALL'), 'n_folds_pos'] == 5  # other regime stable
    assert r.loc[('down_normal', 'ALL'), 'n_folds_pos'] == 0  # fold5 regime FAILS
    assert frl.verdict_pass(edge, f5r) is True              # VERDICT PASS detection
    # control 1: no fold-stable regime -> FAIL
    ev1 = _iso_events(chop_last_ret=-10.0)
    edge1 = frl.edge_table(ev1, lab)
    assert edge1['n_folds_pos'].max() < 5
    assert frl.verdict_pass(edge1, frl.fold5_summary(ev1, lab)[2]) is False
    # control 2: fold5 not isolated (single regime spans everything) -> FAIL
    lab1 = lab.copy()
    lab1['regime'] = 'chop_normal'
    edge2 = frl.edge_table(ev, lab1)
    f2 = frl.fold5_summary(ev, lab1)[2]
    assert f2 == {'chop_normal': 5}
    assert frl.verdict_pass(edge2, f2) is False
