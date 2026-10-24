# Brief for Contrastive Learning Implementation

## Goal
Implement contrastive learning framework for pairwise asset ranking using only IBKR technical data to generate top 10 trade recommendations.

## Acceptance Criteria
1. Framework can compare any two assets and determine which is more likely to outperform
2. Ranking system produces consistent ordering across all assets
3. Top 10 trades can be extracted with confidence scores
4. Implementation uses only price/volume data available through IBKR API

## Relevant Repo Facts
- File paths: `src/contrastive_learning.py`, `scripts/rank_assets.py`
- Model names: `ContrastiveRankingModel`
- Gate definitions: Must pass validation with synthetic data before live testing
- Constraints: float32 tensors, bounded memory usage, no fundamental data

## Non-goals
- Implementing full trading strategy
- Live trading or order execution
- Complex feature engineering beyond technical indicators

## Source Pointers
- BOARD.md row WI-009
- Design doc: `docs/workflow/designs/D-003-technical-trading-approach.md`
- Previous plan: `docs/plans/2026-10-23-WI-002-e3-e5-features-alignment-floor.md`

## Implementation Notes
- Use existing technical features (RSI, MACD, Bollinger Bands, etc.) as input
- Implement Siamese network architecture for pairwise comparison
- Focus on relative performance rather than absolute predictions
- Ensure compatibility with IBKR data frequency and format