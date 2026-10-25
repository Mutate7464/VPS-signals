"""Unit tests for quarantine analysis functions."""

import numpy as np
import pandas as pd
import pytest
from src.quarantine_analysis import (
    level_step_test, 
    volume_corroboration, 
    multi_day_path_analysis
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])