"""Unit tests for quarantine analysis functions."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from src.quarantine_analysis import (
    level_step_test, 
    volume_corroboration, 
    multi_day_path_analysis,
    analyze_ticker_parquet,
    combine_verdicts,
    quarantine_verdict,
)


def test_level_step_test_step_case():
    """Test level_step_test with a clear step case (split-like)."""
    # Create synthetic data with a clear step (e.g., price jumps from 10 to 20)
    dates = pd.date_range('2020-01-01', periods=30, freq='B')
    close_prices = [10.0] * 10 + [20.0] * 20  # Price jumps from 10 to 20
    volume = [1000.0] * 30
    
    df = pd.DataFrame({
        'date': dates,
        'close': close_prices,
        'volume': volume
    })
    
    # Spike at index 10 (where price jumps)
    ratio, clean_ratio, recommendation = level_step_test(df, 10)
    
    # Should detect a clean ratio around 2.0
    assert ratio is not None
    assert abs(ratio - 2.0) < 0.1
    assert clean_ratio is not None
    assert recommendation == "SPLIT_LOOKALIKE"


def test_level_step_test_reversal_case():
    """Test level_step_test with a reversal case (genuine volatility)."""
    # Create simple volatility case that should not produce clean ratio
    dates = pd.date_range('2020-01-01', periods=30, freq='B')
    close_prices = [10.0] * 10 + [11.0] * 10 + [9.0] * 10  # Volatility without clear step
    volume = [1000.0] * 30
    
    df = pd.DataFrame({
        'date': dates,
        'close': close_prices,
        'volume': volume
    })
    
    # Spike at index 10
    ratio, clean_ratio, recommendation = level_step_test(df, 10)
    
    # Should not produce a clean ratio - just make sure it doesn't crash
    assert ratio is not None
    assert recommendation == "GENUINE_VOL"


def test_volume_corroboration_step_case():
    """Test volume_corroboration with a clear volume step case (split-like)."""
    # Create synthetic data with volume spike at the same time as price spike
    dates = pd.date_range('2020-01-01', periods=30, freq='B')
    close_prices = [10.0] * 10 + [20.0] * 20  # Price jumps from 10 to 20
    volume = [1000.0] * 10 + [5000.0] * 20  # Volume also spikes
    
    df = pd.DataFrame({
        'date': dates,
        'close': close_prices,
        'volume': volume
    })
    
    # Spike at index 10
    ratio, recommendation = volume_corroboration(df, 10)
    
    # Should detect high volume ratio
    assert ratio is not None
    assert ratio > 2.0
    assert recommendation == "SPLIT_LOOKALIKE"


def test_volume_corroboration_volatility_case():
    """Test volume_corroboration with volatility case (stable volume)."""
    # Create synthetic data with stable volume
    dates = pd.date_range('2020-01-01', periods=30, freq='B')
    close_prices = [10.0] * 5 + [15.0] * 5 + [12.0] * 10 + [8.0] * 10  # Volatility
    volume = [1000.0] * 30  # Stable volume
    
    df = pd.DataFrame({
        'date': dates,
        'close': close_prices,
        'volume': volume
    })
    
    # Spike at index 10
    ratio, recommendation = volume_corroboration(df, 10)
    
    # Should detect low volume ratio
    assert ratio is not None
    assert ratio <= 2.0
    assert recommendation == "GENUINE_VOL"


def test_multi_day_path_analysis_isolated():
    """Test multi_day_path_analysis with an isolated spike."""
    # Create synthetic data with clearly isolated spike
    dates = pd.date_range('2020-01-01', periods=30, freq='B')
    close_prices = [10.0] * 5 + [100.0] * 2 + [10.0] * 23  # Large spike at index 5
    volume = [1000.0] * 30
    
    df = pd.DataFrame({
        'date': dates,
        'close': close_prices,
        'volume': volume
    })
    
    # Spike at index 5
    is_isolated, recommendation = multi_day_path_analysis(df, 5)
    
    # Should detect isolated spike
    assert is_isolated is True
    assert recommendation == "SPLIT_LOOKALIKE"


def test_multi_day_path_analysis_continuation():
    """Test multi_day_path_analysis with continuation regime."""
    # Create synthetic data with continuation regime - sustained volatility
    dates = pd.date_range('2020-01-01', periods=30, freq='B')
    # Create data with sustained moderate returns
    close_prices = [10.0] * 5 + [12.0] * 10 + [8.0] * 15  # Moderate fluctuations
    volume = [1000.0] * 30
    
    df = pd.DataFrame({
        'date': dates,
        'close': close_prices,
        'volume': volume
    })
    
    # Test at index 5 (middle of the sustained pattern)
    is_isolated, recommendation = multi_day_path_analysis(df, 5)
    
    # Should not detect isolated spike - it's part of a sustained pattern
    assert is_isolated is False
    assert recommendation == "GENUINE_VOL"


# --------------------------------------------------------------------------- #
# WI-010 — final combination rule (conjunction; volume is evidence only)
# --------------------------------------------------------------------------- #
def _write_ticker_parquet(root, symbol, market, closes, volume=None):
    """Write a synthetic ticker parquet under `root/data/raw_ohlcv`."""
    out_dir = Path(root) / "data" / "raw_ohlcv" / f"market={market}"
    out_dir.mkdir(parents=True, exist_ok=True)
    closes = [float(c) for c in closes]
    n = len(closes)
    if volume is None:
        volume = [1000.0] * n
    df = pd.DataFrame(
        {
            "date": pd.bdate_range("2020-01-01", periods=n),
            "open": closes,
            "high": closes,
            "low": closes,
            "close": closes,
            "volume": [float(v) for v in volume],
        }
    )
    df.to_parquet(out_dir / f"symbol={symbol}.parquet", index=False)
    return Path(root)


def _split_like_isolated():
    """Clean 2:1 step (corp-action shape) with no separated material moves."""
    return [9.9] * 30 + [20.0] * 25


def _split_like_with_continuation():
    """Same clean step, but a large separated move on another session = regime."""
    return [9.9] * 30 + [20.0] * 4 + [9.0] + [20.0] * 20


def _volume_only_split_vote():
    """Volume steps 6x while level and path both say genuine volatility.

    A single spike that reverts, a ranging post window (level ratio ~1) and a
    separated material move: only the volume test votes SPLIT_LOOKALIKE.
    """
    closes = [10.0] * 30 + [21.0] + [10.0] * 2 + [16.0] * 2 + [10.0] * 20
    volume = [1000.0] * 31 + [6000.0] * 5 + [1000.0] * (len(closes) - 36)
    return closes, volume


def _isolated_path_no_step():
    """Spike contained in its own 1-2 day window, no clean level step (ratio ~1)."""
    return [9.9] * 30 + [20.0] * 4 + [10.0] * 21


def _crash_ranging_level():
    """-52.5% crash whose post level is near 0.25 of pre but keeps ranging."""
    return [40.0] * 20 + [19.0] + [11.5] * 4 + [8.0, 15.0] * 11


def _crash_persistent_near_fraction():
    """-52.5% crash whose post level holds near 0.2875 (OXY/USD-like residual)."""
    return [40.0] * 20 + [19.0] + [11.5] * 30


@pytest.mark.parametrize(
    "level,path,expected",
    [
        ("SPLIT_LOOKALIKE", "SPLIT_LOOKALIKE", "SPLIT_LOOKALIKE"),
        ("SPLIT_LOOKALIKE", "GENUINE_VOL", "GENUINE_VOL"),
        ("GENUINE_VOL", "SPLIT_LOOKALIKE", "GENUINE_VOL"),
        ("GENUINE_VOL", "GENUINE_VOL", "GENUINE_VOL"),
        (None, None, "GENUINE_VOL"),
    ],
)
def test_combine_verdicts_requires_both_signals(level, path, expected):
    """A volume-only (or single-signal) case must never be split-lookalike."""
    assert combine_verdicts(level, path) == expected


def test_volume_only_signal_does_not_produce_split_lookalike(tmp_path):
    closes, volume = _volume_only_split_vote()
    root = _write_ticker_parquet(tmp_path, "VOLONLY", "USD", closes, volume)

    result = analyze_ticker_parquet("VOLONLY", "USD", base_dir=root)

    assert result["status"] == "SUCCESS"
    assert result["volume_ratio"] > 2.0                      # volume votes split
    assert result["volume_verdict"] == "SPLIT_LOOKALIKE"
    assert result["level_verdict"] == "GENUINE_VOL"
    assert result["path_verdict"] == "GENUINE_VOL"
    assert result["recommendation"] == "GENUINE_VOL"          # but loses the vote
    assert quarantine_verdict(result) == "REINSTATE"


def test_level_step_alone_is_not_split_lookalike(tmp_path):
    """Clean persistent step + a separated material move -> genuine regime."""
    root = _write_ticker_parquet(tmp_path, "REGIME", "USD", _split_like_with_continuation())

    result = analyze_ticker_parquet("REGIME", "USD", base_dir=root)

    assert result["level_verdict"] == "SPLIT_LOOKALIKE"
    assert result["path_verdict"] == "GENUINE_VOL"
    assert result["recommendation"] == "GENUINE_VOL"
    assert quarantine_verdict(result) == "REINSTATE"


def test_isolated_path_alone_is_not_split_lookalike(tmp_path):
    """Isolated path + no persistent clean level step -> genuine volatility."""
    root = _write_ticker_parquet(tmp_path, "PATHONLY", "USD", _isolated_path_no_step())

    result = analyze_ticker_parquet("PATHONLY", "USD", base_dir=root)

    assert result["path_verdict"] == "SPLIT_LOOKALIKE"
    assert result["level_verdict"] == "GENUINE_VOL"
    assert quarantine_verdict(result) == "REINSTATE"


def test_both_signals_split_lookalike_keeps_quarantined(tmp_path):
    root = _write_ticker_parquet(tmp_path, "SPLIT", "USD", _split_like_isolated())

    result = analyze_ticker_parquet("SPLIT", "USD", base_dir=root)

    assert result["level_verdict"] == "SPLIT_LOOKALIKE"
    assert result["path_verdict"] == "SPLIT_LOOKALIKE"
    assert result["recommendation"] == "SPLIT_LOOKALIKE"
    assert quarantine_verdict(result) == "KEEP_QUARANTINED"


def test_crash_with_ranging_level_is_not_split_lookalike(tmp_path):
    """2020-03-09 cluster shape: crash whose post level keeps ranging."""
    root = _write_ticker_parquet(tmp_path, "CRASH", "USD", _crash_ranging_level())

    result = analyze_ticker_parquet("CRASH", "USD", base_dir=root)

    assert result["level_verdict"] == "GENUINE_VOL"
    assert result["persistence_spread"] > 0.35
    assert quarantine_verdict(result) == "REINSTATE"


def test_known_residual_crash_holding_near_fraction(tmp_path):
    """Characterization of the disclosed residual (OXY/USD shape).

    A crash whose post level holds near a simple fraction passes the conjunction
    and stays KEEP_QUARANTINED. This is documented in the WI-010 report as a
    residual finding for the human gate; tightening the tolerance is a rule
    change beyond this consolidation.
    """
    root = _write_ticker_parquet(tmp_path, "NEARFRAC", "USD", _crash_persistent_near_fraction())

    result = analyze_ticker_parquet("NEARFRAC", "USD", base_dir=root)

    assert result["level_verdict"] == "SPLIT_LOOKALIKE"
    assert result["path_verdict"] == "SPLIT_LOOKALIKE"
    assert quarantine_verdict(result) == "KEEP_QUARANTINED"


def test_negative_close_data_is_fix_data(tmp_path):
    closes = [20.0] * 30 + [21.0] + [(-5.0) for _ in range(24)]
    root = _write_ticker_parquet(tmp_path, "NEG", "USD", closes)

    result = analyze_ticker_parquet("NEG", "USD", base_dir=root)

    assert result["non_positive_close"] is True
    assert quarantine_verdict(result) == "FIX_DATA"


def test_quarantine_verdict_status_mapping(tmp_path):
    assert quarantine_verdict({"symbol": "X", "market": "USD", "status": "NO_FILE"}) == "OWNER_ACTION"
    assert quarantine_verdict({"status": "ERROR"}) == "AMBIGUOUS"
    assert quarantine_verdict({"status": "NO_SPIKE", "non_positive_close": False}) == "REINSTATE"

    root = _write_ticker_parquet(tmp_path, "FLAT", "USD", [10.0] * 40)
    result = analyze_ticker_parquet("FLAT", "USD", base_dir=root)
    assert result["status"] == "NO_SPIKE"
    assert quarantine_verdict(result) == "REINSTATE"


@pytest.mark.parametrize(
    "symbol,market",
    [
        ("OVV", "CAD"),
        ("OVV", "USD"),
        ("WES", "USD"),
        ("CVE", "CAD"),
        ("CVE", "USD"),
        ("APA", "USD"),
        ("MTDR", "USD"),
        ("GME", "USD"),
    ],
)
def test_real_genuine_move_anchors_are_not_split_lookalikes(symbol, market):
    """Regression lock on the named anchors (2020-03-09 cluster + GME).

    OXY/USD is deliberately absent: it is the disclosed residual misread (see
    `test_known_residual_crash_holding_near_fraction` and the WI-010 report).
    Skips when the local OHLCV data is not synced.
    """
    root = Path(__file__).resolve().parents[1]
    parquet = root / "data" / "raw_ohlcv" / f"market={market}" / f"symbol={symbol}.parquet"
    if not parquet.exists():
        pytest.skip(f"{parquet} not present in this checkout")

    result = analyze_ticker_parquet(symbol, market, base_dir=root)

    assert result["status"] == "SUCCESS"
    assert result["recommendation"] == "GENUINE_VOL"
    assert quarantine_verdict(result) == "REINSTATE"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])