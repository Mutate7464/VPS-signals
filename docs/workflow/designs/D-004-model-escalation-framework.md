# Planning Process Update - Model Escalation Framework

## Overview
This document outlines the updated planning process for model escalation within the opencode workflow, incorporating the new escalation paths and human gating requirements.

## Model Escalation Framework

### Build Agent Escalation Path
1. **Base Tier**: `openrouter/deepseek/deepseek-v4.1-flash`
   - Used for standard execution tasks
   - Cost-effective for routine operations

2. **Intermediate Tier**: `openrouter/deepseek/deepseek-v4.1-pro`
   - Applied when base tier encounters difficulties
   - Better reasoning capabilities while maintaining cost efficiency

3. **A1 Tier**: `openrouter/google/gemini-4-argon` (discounted model)
   - Leverages current promotional pricing
   - Strong capabilities for complex tasks
   - Requires human approval before deployment

4. **Frontier Tier**: `openrouter/anthropic/claude-opus-5.5`
   - Reserved for breakthrough scenarios only
   - Highest cost tier with maximum capabilities
   - Strict human gating with prework requirements

### Troubleshooter Escalation Path
1. **A1 Tier**: `openrouter/google/gemini-4-argon` (discounted model)
   - First escalation for troubleshooting complex issues
   - Cost-optimized alternative to frontier models

2. **Frontier Tier**: `openrouter/anthropic/claude-opus-5.5`
   - Reserved for intractable problems requiring maximum reasoning
   - Requires comprehensive documentation and human approval

## Human Gating Requirements

### Pre-Escalation Checklist
- [ ] Evidence bundle compiled (failing commands, full errors, files involved)
- [ ] Attempts documented in EXECUTION LOG
- [ ] Plan step that is blocked clearly identified
- [ ] Intervention brief prepared (SITUATION/CONCERNS/FACTORS/GOAL)
- [ ] Cost analysis performed for proposed escalation

### Prework Requirements for Frontier Models
- [ ] Complete root cause investigation using systematic debugging approach
- [ ] Document all attempted fixes with outcomes
- [ ] Prepare evidence bundle for escalated model
- [ ] Confirm goal alignment with board's G-## objectives
- [ ] Obtain explicit human approval before model switching

## Cost Optimization Strategies

### Gemini 4 Argon Discount Utilization
- Take advantage of current promotional pricing for A1 escalation tier
- Monitor OpenRouter for discount expiration dates
- Document cost savings achieved through discount utilization
- Evaluate performance/cost ratio periodically

### Tier Usage Guidelines
1. Reserve frontier models for breakthrough scenarios only
2. Exhaust lower tiers before escalating to higher-cost models
3. Document ROI justification for all frontier model usage
4. Regular cost/benefit analysis of model performance

## Implementation Process

### Configuration Management
- Maintain backup of current configuration before changes
- Test new configuration in isolated environment first
- Verify all model references are correctly specified
- Document all changes in version control

### Monitoring and Maintenance
- Regular review of escalation triggers and outcomes
- Cost tracking for all model usage
- Performance evaluation of discounted models
- Adjustment of escalation paths based on experience

## Benefits of Updated Framework

1. **Cost Efficiency**: Leveraging discounted models reduces overall operational costs
2. **Performance**: Maintained high-quality output through tiered escalation approach
3. **Control**: Human gating preserves oversight on expensive model usage
4. **Flexibility**: Clear paths for both routine and breakthrough scenarios
5. **Transparency**: Comprehensive documentation enables informed decision-making