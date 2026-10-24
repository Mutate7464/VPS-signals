# D-003 — Technical Trading Approach with IBKR Constraints

**Status:** proposed
**Date:** 2026-10-24

## Context

Following the E3-E5 diagnostic cycle (WI-002), we identified that:
- Continuous signal exists but binary classification fails (H3 SUPPORTED)
- Feature expansion didn't solve the core problem (H2 NOT SUPPORTED)
- Predictability floor breached - simple factors predict returns (H4 NOT SUPPORTED)

The admin decision was to pursue target/metric redesign leveraging the continuous signal. However, we are constrained to technical data available through IBKR API without access to fundamental financial statements or alternative data.

## Options Considered

### Option 1: Pure Technical Approach
- Leverage only price/volume data available through IBKR
- Focus on technical indicators and machine learning with technical features
- Implement contrastive learning for pairwise asset ranking
- Use regime detection based on volatility/volume metrics

### Option 2: Hybrid Technical-Factor Approach
- Combine technical signals with simple factor-like constructs
- Use technical proxies for traditional factors (e.g., momentum via price trends)
- Implement signal stacking with multiple technical approaches

### Option 3: Enhanced Technical ML Approach
- Develop sophisticated machine learning models using technical features
- Implement ensemble methods with multiple technical models
- Use dynamic feature selection based on market regimes

## Decision

**Selected: Option 2 - Hybrid Technical-Factor Approach**

This approach combines the strengths of both worlds:
- Leverages all available IBKR data (price/volume)
- Implements factor-like thinking using technical proxies
- Maintains interpretability while capturing complex interactions
- Aligns with the continuous signal finding from E3-E5 diagnostics

## Consequences

### Positive
- Fully compatible with IBKR API constraints
- Builds on proven technical analysis principles
- Enables pairwise ranking for top-N trade selection
- Supports regime-adaptive strategies
- Maintains clear economic interpretation

### Negative
- May require more development time to implement properly
- Need to validate technical factor proxies against traditional factors
- Complexity in combining multiple signal layers

## Implementation Plan

1. Create technical factor proxies using available data
2. Implement contrastive learning framework for pairwise ranking
3. Develop regime detection using volatility/volume metrics
4. Build signal stacking framework
5. Implement ensemble methods
6. Create dynamic feature selection logic
7. Generate top 10 trade recommendations daily