# PLAN — WI-009 / Contrastive Learning for Technical Trading

**GOAL:** Implement contrastive learning framework for pairwise asset ranking using only IBKR technical data to generate top 10 trade recommendations.

**CONSTRAINTS:**
- Use only price/volume data available through IBKR API
- float32 tensors, bounded memory usage
- No fundamental data or alternative data sources
- Compatible with existing codebase structure

## STEPS

### [ ] Step 1 — Design contrastive learning architecture
- Define Siamese network structure for pairwise asset comparison
- Specify input features (technical indicators from IBKR data)
- Design loss function for relative ranking optimization
Acceptance: Architecture diagram and pseudocode in `docs/tech_approach/2026-W44/contrastive_design.md`

### [ ] Step 2 — Implement technical feature extraction
- Extract RSI, MACD, Bollinger Bands, ATR, volume indicators from IBKR data
- Normalize features appropriately for neural network input
- Create feature engineering pipeline compatible with contrastive framework
Acceptance: `src/features/technical_features.py` with unit tests passing

### [ ] Step 3 — Build contrastive model
- Implement Siamese network using PyTorch/TensorFlow
- Create training loop with appropriate loss function
- Implement inference pipeline for pairwise comparisons
Acceptance: `src/models/contrastive_ranking.py` with training script

### [ ] Step 4 — Validate with synthetic data
- Generate synthetic price series with known relative performance
- Train model on synthetic data to verify approach
- Validate ranking consistency and accuracy
Acceptance: Validation report in `docs/tech_approach/2026-W44/reports/contrastive_validation.md`

### [ ] Step 5 — Create ranking pipeline
- Implement system to rank all assets against each other
- Generate composite scores for each asset
- Extract top 10 trade recommendations with confidence scores
Acceptance: `scripts/rank_assets.py` producing ranked output

### [ ] Step 6 — Integration testing
- Test complete pipeline with sample IBKR data
- Verify memory usage and performance constraints
- Document usage and limitations
Acceptance: Integration test passes with sample data

## OUT OF SCOPE
- Live trading implementation
- Order execution systems
- Complex feature engineering beyond technical indicators
- Real-time data processing (focus on daily batch processing)

## EXECUTION LOG

| Time | Step | Outcome | Concern? |
|---|---|---|---|
| 2026-10-24 TBD | 1 |  |  |

STATUS: PLAN