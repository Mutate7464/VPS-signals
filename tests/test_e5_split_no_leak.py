"""WI-009 — regression test for the purged-split mask (leak guard).

Found during QA review of WI-009, in both `src/factors/e5_baseline.py` and
`scripts/diag_signal.py::run_e5`: the split index sets were mapped onto panel
rows through `pd.factorize` date codes.

`PurgedWalkForwardSplit` is fed the *sorted unique* date array, so the index sets
it returns are POSITIONS into that array. Factorize codes are assigned by order
of first appearance (symbol iteration order), so the two agree only when the
first symbol happens to own every early date. When it does not — which is the
real case (CAD: they disagree for 100% of rows, max gap 1839) — the mask drags
held-out rows into the training fold: a train/val leak.

This test fails if anyone reverts to the code-based mask.
"""

import numpy as np
import pandas as pd
import pytest

from src.factors.e5_baseline import date_positions
from src.xgb_trainer import PurgedWalkForwardSplit

EMBARGO_TD = 5


def _staggered_panel(first_symbol_starts_late: bool, n_dates=40, d=6):
    dates = pd.date_range("2020-01-01", periods=n_dates, freq="B")
    rows = []
    for k, sym in enumerate(["AAA", "BBB", "CCC", "DDD"]):
        if first_symbol_starts_late and k == 0:
            sym_dates = dates[10:]
        else:
            sym_dates = dates
        for dt_ in sym_dates:
            rows.append((dt_, sym, *range(d)))
    cols = ["date", "symbol"] + [f"f{i}" for i in range(d)]
    return pd.DataFrame(rows, columns=cols).reset_index(drop=True)


def _splits_and_masks(panel):
    uniq = np.sort(pd.unique(panel["date"]))
    pos = date_positions(panel["date"])
    codes, _ = pd.factorize(panel["date"])
    splits = list(PurgedWalkForwardSplit(n_splits=3, embargo_td=EMBARGO_TD).split(uniq))
    return uniq, pos, codes, splits


def test_first_symbol_starting_late_is_the_real_case():
    """Guard the premise: the codes really do diverge from positions."""
    panel = _staggered_panel(first_symbol_starts_late=True)
    _, pos, codes, _ = _splits_and_masks(panel)
    assert not np.array_equal(codes, pos), "this fixture no longer reproduces the bug premise"

    # And with a full first symbol (the coincidence), they agree.
    panel2 = _staggered_panel(first_symbol_starts_late=False)
    _, pos2, codes2, _ = _splits_and_masks(panel2)
    assert np.array_equal(codes2, pos2)


@pytest.mark.parametrize("late", [True, False])
def test_position_mask_respects_the_embargo(late):
    """The production mask (positions) must separate train and val by the embargo."""
    panel = _staggered_panel(first_symbol_starts_late=late)
    uniq, pos, _, splits = _splits_and_masks(panel)
    dates = panel["date"].to_numpy()

    for tr_idx, va_idx in splits:
        tr_rows = np.isin(pos, tr_idx)
        va_rows = np.isin(pos, va_idx)

        assert not (tr_rows & va_rows).any(), "a date is in both train and val"

        train_dates = np.sort(pd.unique(dates[tr_rows]))
        val_dates = np.sort(pd.unique(dates[va_rows]))
        assert train_dates.size and val_dates.size

        # Embargo: at least EMBARGO_TD distinct trading dates between them.
        gap = int(np.searchsorted(uniq, val_dates[0]) - np.searchsorted(uniq, train_dates[-1]))
        assert gap > EMBARGO_TD, f"embargo violated: gap={gap} <= {EMBARGO_TD}"


def test_factorize_code_mask_would_leak():
    """Documents the defect: the code-based mask pulls held-out rows into train."""
    panel = _staggered_panel(first_symbol_starts_late=True)
    uniq, pos, codes, splits = _splits_and_masks(panel)

    tr_idx, va_idx = splits[0]
    correct_tr = np.isin(pos, tr_idx)
    leaky_tr = np.isin(codes, tr_idx)

    assert not np.array_equal(correct_tr, leaky_tr)
    leaked = leaky_tr & ~correct_tr
    assert leaked.any(), "expected the code-based mask to leak rows into train"

    # Show the leak is not merely 'more training data': rows whose dates follow
    # the validation fold start would be trained on.
    dates = panel["date"].to_numpy()
    leaked_dates = np.sort(pd.unique(dates[leaked]))
    val_start = np.sort(pd.unique(dates[np.isin(pos, va_idx)]))[0]
    assert leaked_dates.max() >= val_start, "leaked rows land at/after the val fold"