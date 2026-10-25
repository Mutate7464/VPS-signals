# WI-011 — decision-rule specification (data only, human gate)

- Generated (UTC): 2026-10-25T21:41:55Z
- Derived from Steps 4–6 of `docs/plans/2026-10-25-WI-011-condition-first-meta-analysis.md`; cost evidence in `reports/wi011_tradeable_conditions.md`.
- These are **data specifications only**. Nothing here is optimised, backtested, sized or implemented; no long-only rule survives at this universe size, so the specification is N/A by the plan's own pre-authorised conclusion.

HUMAN_GATE: STOP

ENTRY: N/A — no rule passed the Step 6 criteria.
HOLD_WINDOW: N/A — the 5–15 trading-day envelope was never reached by a qualifying rule.
EXIT_INVALIDATION: N/A — no rule survives to specify an exit.

NO_TRADE_DEFAULT: no new positions from WI-011 conditions. The candidate *states* (trend/chop, volatility regime, liquidity regime, 52-week channel position, and the Step 5 cross-sectional return-rank rules) remain descriptive context only — usable for annotation and post-hoc attribution, not as entries.

CONDITION_FLAGS (context only, not entries): `trend_up`/`trend_down`/`trend_chop`, `er_trending`/`er_choppy`, `vol_low`/`vol_high`, `liq_illiquid`/`liq_liquid`, `ch52_high`/`ch52_low`, `mom_pos`/`mom_neg`, `rev1m_pos`/`rev1m_neg`, plus the Step 3 `ind_*` own-history extremes. The one effect worth carrying forward as *information* is the cross-sectional framing: `cs_top_quartile_120` / `cs_bottom_quartile_120` show the largest within-date components (about +50 and +19 bps at a 20d horizon), i.e. 6–12 month relative winners and losers both outrun the middle of the distribution.

FACTOR_TILTS (observed, descriptive): the CAD universe over 2016–2026 drifts up (all-rows mean +181 bps per 20 trading days); `vol_high`, `dollarvol_high` and the 52-week-low states carry the largest *market* components, so any rule built on them is a market-timing bet rather than a name-selection bet.

WORKED_EXAMPLE: N/A — the plan requires a worked example only when a survivor exists.

REASON FOR N/A: 73 candidate cells cleared the stable within-date screen, 10 cleared net expectancy, but 0 cleared frequency and concurrency as well — see `reports/wi011_tradeable_conditions.md` for the full table and the explicit no-survivor conclusion.

## What the human gate is being asked to decide

1. Accept the negative result: WI-011 conditions are descriptive, not tradeable, at this universe size and cadence — and stop the condition-first branch.
2. Or authorise a **new** plan for a narrower trigger + execution assumption (screener design, portfolio construction) that WI-011 explicitly excludes.
3. Or confirm/correct the cost assumptions (IBKR CAD schedule parameters and the CAD 5,000 notional), which is the one input that could move candidates across the net-expectancy line.

No implementation, backtest, optimisation or order flow follows from this document without that decision.
