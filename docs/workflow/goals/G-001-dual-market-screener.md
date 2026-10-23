# G-001 — Dual-Market Quant Screener (the original intention)

**Source of truth:** `Design/01 Master Handover and Workflow.md` §1 (frozen v1.0 spec). This goal doc is the pointer; the Design package is the intention. Never edited — superseded only.

**Intention (one line):** an institutional-grade, zero-leakage screening + portfolio-defense pipeline over 300 USD / 300 CAD equities and active holdings, producing daily dual-mode PDF tearsheets (Defense: exit urgency on holdings; Discovery: top-30 bottom-inflection and top-30 upward-trend picks per market).

**Success criteria (from Design/05 governance thresholds):**
- All 4 target models pass Gate 4: P@K lift ≥1.5×, BSS >0.05, PR-AUC lift >1.35×, deflated IC ρ>0.04 (t>2.5), placebo test clean.
- Daily output reproducible from fresh synced data with no manual code intervention.
- Human gate at every sprint boundary (AGENTS.md protocol).

**Non-goals (v1.0):** automated order execution (human gate always), live trading, EP-06/07/08 (backlog).

**Current state:** pipeline built end-to-end; Gate 4 FAILED on all USD targets (models ≈ random). Work items: WI-001 (done, QA exception), WI-002 (signal remediation — active), WI-005 (post-MVP backlog).
