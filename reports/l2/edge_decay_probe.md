# WI-045 — CALIB->EVAL edge-decay probe (frozen WI-042 artifacts, Layer 1)

- Generated (UTC): 2026-11-10T20:34:39Z
- Input: `rerun_modern.json` read-only — 20 ratified ADOPT cells; cost floor 25 bps is already inside `r_frozen` (WI-042)
- **Mechanism ranking (decay 87.0 bps over 20 ratified ADOPT cells) — 1. fold-concentration 55.0% (17 cells); 2. cost-floor 44.8% (3 cells); 3. tau-mass 0.2% (0 cells)**
- Layer separation: derived from the frozen artifact only — no learner refit, no EVAL scoring, no new verdicts (D-023/D-025 Layer 1); verdicts stay PROVISIONAL.

| cell | tau | CALIB n | selected | mass kept | net bps | cost | gross bps | decay bps | top fold (share) | tau-mass | fold-conc | cost-floor | driver |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- | ---: | ---: | ---: | :--- |
| `CAD|wi028|stack|all` | 0.10 | 5,315 | 5,302 | 0.998 | +1.36 | 25 | +26.36 | +1.36 | 1 (1.00) | 0.00 | 0.51 | 0.49 | **fold-concentration** |
| `CAD|wi028|stack|up_high` | 0.10 | 1,786 | 1,782 | 0.998 | +0.49 | 25 | +25.49 | +0.49 | 1 (1.00) | 0.00 | 0.50 | 0.49 | **fold-concentration** |
| `CAD|wi028|stack|up_normal` | 0.10 | 1,302 | 1,297 | 0.996 | +9.83 | 25 | +34.83 | +9.83 | 1 (0.95) | 0.00 | 0.57 | 0.43 | **fold-concentration** |
| `CAD|wi030|stack|all` | 0.70 | 5,315 | 5,303 | 0.998 | +3.38 | 25 | +28.38 | +3.38 | 1 (0.94) | 0.00 | 0.51 | 0.48 | **fold-concentration** |
| `CAD|wi030|stack|up_high` | 0.70 | 1,786 | 1,780 | 0.997 | +3.66 | 25 | +28.66 | +3.66 | 1 (0.67) | 0.00 | 0.43 | 0.56 | **cost-floor** |
| `CAD|wi030|stack|up_normal` | 0.70 | 1,302 | 1,297 | 0.996 | +9.83 | 25 | +34.83 | +9.83 | 1 (0.95) | 0.00 | 0.57 | 0.43 | **fold-concentration** |
| `CAD|wi033|raw|all` | 0.50 | 5,315 | 5,309 | 0.999 | +3.26 | 25 | +28.26 | +3.26 | 1 (1.00) | 0.00 | 0.53 | 0.47 | **fold-concentration** |
| `CAD|wi033|raw|up_high` | 0.50 | 1,786 | 1,784 | 0.999 | +2.75 | 25 | +27.75 | +2.75 | 1 (1.00) | 0.00 | 0.53 | 0.47 | **fold-concentration** |
| `CAD|wi033|raw|up_normal` | 0.50 | 1,302 | 1,298 | 0.997 | +8.95 | 25 | +33.95 | +8.95 | 1 (1.00) | 0.00 | 0.57 | 0.42 | **fold-concentration** |
| `CAD|wi033|stack|all` | 0.50 | 5,315 | 5,304 | 0.998 | +2.35 | 25 | +27.35 | +2.35 | 1 (1.00) | 0.00 | 0.52 | 0.48 | **fold-concentration** |
| `CAD|wi033|stack|up_high` | 0.70 | 1,786 | 1,777 | 0.995 | +1.62 | 25 | +26.62 | +1.62 | 1 (1.00) | 0.00 | 0.51 | 0.48 | **fold-concentration** |
| `CAD|wi033|stack|up_normal` | 0.50 | 1,302 | 1,297 | 0.996 | +9.83 | 25 | +34.83 | +9.83 | 1 (0.95) | 0.00 | 0.57 | 0.43 | **fold-concentration** |
| `CAD|wi037|raw|all` | 0.50 | 5,315 | 5,307 | 0.998 | +2.55 | 25 | +27.55 | +2.55 | 1 (1.00) | 0.00 | 0.52 | 0.48 | **fold-concentration** |
| `CAD|wi037|raw|up_high` | 0.50 | 1,786 | 1,784 | 0.999 | +2.75 | 25 | +27.75 | +2.75 | 1 (1.00) | 0.00 | 0.53 | 0.47 | **fold-concentration** |
| `CAD|wi037|raw|up_normal` | 0.50 | 1,302 | 1,298 | 0.997 | +8.95 | 25 | +33.95 | +8.95 | 1 (1.00) | 0.00 | 0.57 | 0.42 | **fold-concentration** |
| `CAD|wi037|stack|all` | 0.20 | 5,315 | 5,308 | 0.999 | +2.91 | 25 | +27.91 | +2.91 | 1 (1.00) | 0.00 | 0.53 | 0.47 | **fold-concentration** |
| `CAD|wi037|stack|up_high` | 0.20 | 1,786 | 1,784 | 0.999 | +2.75 | 25 | +27.75 | +2.75 | 1 (1.00) | 0.00 | 0.53 | 0.47 | **fold-concentration** |
| `CAD|wi037|stack|up_normal` | 0.50 | 1,302 | 1,297 | 0.996 | +9.83 | 25 | +34.83 | +9.83 | 1 (0.95) | 0.00 | 0.57 | 0.43 | **fold-concentration** |
| `USD|wi028|raw|all` | 0.50 | 10,268 | 10,267 | 1.000 | +0.22 | 25 | +25.22 | +0.00 | 3 (0.52) | 0.00 | 0.34 | 0.66 | **cost-floor** |
| `USD|wi028|raw|up_high` | 0.50 | 4,059 | 4,058 | 1.000 | +0.64 | 25 | +25.64 | +0.00 | 3 (0.56) | 0.00 | 0.36 | 0.64 | **cost-floor** |

## Fold contributions (frozen harness table, n_events-weighted)

| cell | fold | events | selected | edge bps | contribution bps |
| :--- | ---: | ---: | ---: | ---: | ---: |
| `CAD|wi028|stack|all` | 0 | 2,820 | 2,813 | -3.366 | -0.5734 |
| `CAD|wi028|stack|all` | 1 | 3,136 | 3,130 | +5.308 | +1.0057 |
| `CAD|wi028|stack|all` | 2 | 3,907 | 3,907 | +0.000 | +0.0000 |
| `CAD|wi028|stack|all` | 3 | 3,570 | 3,570 | +0.000 | +0.0000 |
| `CAD|wi028|stack|all` | 4 | 3,119 | 3,119 | +0.000 | +0.0000 |
| `CAD|wi028|stack|up_high` | 0 | 1,327 | 1,325 | -2.870 | -0.8810 |
| `CAD|wi028|stack|up_high` | 1 | 459 | 457 | +9.279 | +0.9852 |
| `CAD|wi028|stack|up_high` | 2 | 1,178 | 1,178 | +0.000 | +0.0000 |
| `CAD|wi028|stack|up_high` | 3 | 123 | 123 | +0.000 | +0.0000 |
| `CAD|wi028|stack|up_high` | 4 | 1,236 | 1,236 | +0.000 | +0.0000 |
| `CAD|wi028|stack|up_normal` | 0 | 456 | 455 | +1.514 | +0.0967 |
| `CAD|wi028|stack|up_normal` | 1 | 846 | 842 | +14.928 | +1.7696 |
| `CAD|wi028|stack|up_normal` | 2 | 2,096 | 2,096 | +0.000 | +0.0000 |
| `CAD|wi028|stack|up_normal` | 3 | 2,729 | 2,729 | +0.000 | +0.0000 |
| `CAD|wi028|stack|up_normal` | 4 | 1,010 | 1,010 | +0.000 | +0.0000 |
| `CAD|wi030|stack|all` | 0 | 2,820 | 2,814 | +0.407 | +0.0693 |
| `CAD|wi030|stack|all` | 1 | 3,136 | 3,130 | +5.308 | +1.0057 |
| `CAD|wi030|stack|all` | 2 | 3,907 | 3,907 | +0.000 | +0.0000 |
| `CAD|wi030|stack|all` | 3 | 3,570 | 3,570 | +0.000 | +0.0000 |
| `CAD|wi030|stack|all` | 4 | 3,119 | 3,119 | +0.000 | +0.0000 |
| `CAD|wi030|stack|up_high` | 0 | 1,327 | 1,323 | +1.558 | +0.4781 |
| `CAD|wi030|stack|up_high` | 1 | 459 | 457 | +9.279 | +0.9852 |
| `CAD|wi030|stack|up_high` | 2 | 1,178 | 1,178 | +0.000 | +0.0000 |
| `CAD|wi030|stack|up_high` | 3 | 123 | 123 | +0.000 | +0.0000 |
| `CAD|wi030|stack|up_high` | 4 | 1,236 | 1,236 | +0.000 | +0.0000 |
| `CAD|wi030|stack|up_normal` | 0 | 456 | 455 | +1.514 | +0.0967 |
| `CAD|wi030|stack|up_normal` | 1 | 846 | 842 | +14.928 | +1.7696 |
| `CAD|wi030|stack|up_normal` | 2 | 2,096 | 2,096 | +0.000 | +0.0000 |
| `CAD|wi030|stack|up_normal` | 3 | 2,729 | 2,729 | +0.000 | +0.0000 |
| `CAD|wi030|stack|up_normal` | 4 | 1,010 | 1,010 | +0.000 | +0.0000 |
| `CAD|wi033|raw|all` | 0 | 2,820 | 2,820 | +0.000 | +0.0000 |
| `CAD|wi033|raw|all` | 1 | 3,136 | 3,130 | +5.308 | +1.0057 |
| `CAD|wi033|raw|all` | 2 | 3,907 | 3,907 | +0.000 | +0.0000 |
| `CAD|wi033|raw|all` | 3 | 3,570 | 3,570 | +0.000 | +0.0000 |
| `CAD|wi033|raw|all` | 4 | 3,119 | 3,119 | +0.000 | +0.0000 |
| `CAD|wi033|raw|up_high` | 0 | 1,327 | 1,327 | +0.000 | +0.0000 |
| `CAD|wi033|raw|up_high` | 1 | 459 | 457 | +9.279 | +0.9852 |
| `CAD|wi033|raw|up_high` | 2 | 1,178 | 1,178 | +0.000 | +0.0000 |
| `CAD|wi033|raw|up_high` | 3 | 123 | 123 | +0.000 | +0.0000 |
| `CAD|wi033|raw|up_high` | 4 | 1,236 | 1,236 | +0.000 | +0.0000 |
| `CAD|wi033|raw|up_normal` | 0 | 456 | 456 | +0.000 | +0.0000 |
| `CAD|wi033|raw|up_normal` | 1 | 846 | 842 | +14.928 | +1.7696 |
| `CAD|wi033|raw|up_normal` | 2 | 2,096 | 2,096 | +0.000 | +0.0000 |
| `CAD|wi033|raw|up_normal` | 3 | 2,729 | 2,729 | +0.000 | +0.0000 |
| `CAD|wi033|raw|up_normal` | 4 | 1,010 | 1,010 | +0.000 | +0.0000 |
| `CAD|wi033|stack|all` | 0 | 2,820 | 2,815 | -1.567 | -0.2669 |
| `CAD|wi033|stack|all` | 1 | 3,136 | 3,130 | +5.308 | +1.0057 |
| `CAD|wi033|stack|all` | 2 | 3,907 | 3,907 | +0.000 | +0.0000 |
| `CAD|wi033|stack|all` | 3 | 3,570 | 3,570 | +0.000 | +0.0000 |
| `CAD|wi033|stack|all` | 4 | 3,119 | 3,119 | +0.000 | +0.0000 |
| `CAD|wi033|stack|up_high` | 0 | 1,327 | 1,320 | -0.930 | -0.2854 |
| `CAD|wi033|stack|up_high` | 1 | 459 | 457 | +9.279 | +0.9852 |
| `CAD|wi033|stack|up_high` | 2 | 1,178 | 1,178 | +0.000 | +0.0000 |
| `CAD|wi033|stack|up_high` | 3 | 123 | 123 | +0.000 | +0.0000 |
| `CAD|wi033|stack|up_high` | 4 | 1,236 | 1,236 | +0.000 | +0.0000 |
| `CAD|wi033|stack|up_normal` | 0 | 456 | 455 | +1.514 | +0.0967 |
| `CAD|wi033|stack|up_normal` | 1 | 846 | 842 | +14.928 | +1.7696 |
| `CAD|wi033|stack|up_normal` | 2 | 2,096 | 2,096 | +0.000 | +0.0000 |
| `CAD|wi033|stack|up_normal` | 3 | 2,729 | 2,729 | +0.000 | +0.0000 |
| `CAD|wi033|stack|up_normal` | 4 | 1,010 | 1,010 | +0.000 | +0.0000 |
| `CAD|wi037|raw|all` | 0 | 2,820 | 2,818 | -1.262 | -0.2151 |
| `CAD|wi037|raw|all` | 1 | 3,136 | 3,130 | +5.308 | +1.0057 |
| `CAD|wi037|raw|all` | 2 | 3,907 | 3,907 | +0.000 | +0.0000 |
| `CAD|wi037|raw|all` | 3 | 3,570 | 3,570 | +0.000 | +0.0000 |
| `CAD|wi037|raw|all` | 4 | 3,119 | 3,119 | +0.000 | +0.0000 |
| `CAD|wi037|raw|up_high` | 0 | 1,327 | 1,327 | +0.000 | +0.0000 |
| `CAD|wi037|raw|up_high` | 1 | 459 | 457 | +9.279 | +0.9852 |
| `CAD|wi037|raw|up_high` | 2 | 1,178 | 1,178 | +0.000 | +0.0000 |
| `CAD|wi037|raw|up_high` | 3 | 123 | 123 | +0.000 | +0.0000 |
| `CAD|wi037|raw|up_high` | 4 | 1,236 | 1,236 | +0.000 | +0.0000 |
| `CAD|wi037|raw|up_normal` | 0 | 456 | 456 | +0.000 | +0.0000 |
| `CAD|wi037|raw|up_normal` | 1 | 846 | 842 | +14.928 | +1.7696 |
| `CAD|wi037|raw|up_normal` | 2 | 2,096 | 2,096 | +0.000 | +0.0000 |
| `CAD|wi037|raw|up_normal` | 3 | 2,729 | 2,729 | +0.000 | +0.0000 |
| `CAD|wi037|raw|up_normal` | 4 | 1,010 | 1,010 | +0.000 | +0.0000 |
| `CAD|wi037|stack|all` | 0 | 2,820 | 2,819 | -0.631 | -0.1075 |
| `CAD|wi037|stack|all` | 1 | 3,136 | 3,130 | +5.308 | +1.0057 |
| `CAD|wi037|stack|all` | 2 | 3,907 | 3,907 | +0.000 | +0.0000 |
| `CAD|wi037|stack|all` | 3 | 3,570 | 3,570 | +0.000 | +0.0000 |
| `CAD|wi037|stack|all` | 4 | 3,119 | 3,119 | +0.000 | +0.0000 |
| `CAD|wi037|stack|up_high` | 0 | 1,327 | 1,327 | +0.000 | +0.0000 |
| `CAD|wi037|stack|up_high` | 1 | 459 | 457 | +9.279 | +0.9852 |
| `CAD|wi037|stack|up_high` | 2 | 1,178 | 1,178 | +0.000 | +0.0000 |
| `CAD|wi037|stack|up_high` | 3 | 123 | 123 | +0.000 | +0.0000 |
| `CAD|wi037|stack|up_high` | 4 | 1,236 | 1,236 | +0.000 | +0.0000 |
| `CAD|wi037|stack|up_normal` | 0 | 456 | 455 | +1.514 | +0.0967 |
| `CAD|wi037|stack|up_normal` | 1 | 846 | 842 | +14.928 | +1.7696 |
| `CAD|wi037|stack|up_normal` | 2 | 2,096 | 2,096 | +0.000 | +0.0000 |
| `CAD|wi037|stack|up_normal` | 3 | 2,729 | 2,729 | +0.000 | +0.0000 |
| `CAD|wi037|stack|up_normal` | 4 | 1,010 | 1,010 | +0.000 | +0.0000 |
| `USD|wi028|raw|all` | 0 | 5,109 | 5,108 | +0.463 | +0.0767 |
| `USD|wi028|raw|all` | 1 | 6,253 | 6,253 | +0.000 | +0.0000 |
| `USD|wi028|raw|all` | 2 | 6,857 | 6,823 | +1.311 | +0.2911 |
| `USD|wi028|raw|all` | 3 | 6,601 | 6,583 | +1.849 | +0.3952 |
| `USD|wi028|raw|all` | 4 | 6,064 | 6,064 | +0.000 | +0.0000 |
| `USD|wi028|raw|up_high` | 0 | 2,775 | 2,774 | +0.994 | +0.2226 |
| `USD|wi028|raw|up_high` | 1 | 1,284 | 1,284 | +0.000 | +0.0000 |
| `USD|wi028|raw|up_high` | 2 | 1,857 | 1,843 | +0.904 | +0.1354 |
| `USD|wi028|raw|up_high` | 3 | 1,577 | 1,574 | +3.546 | +0.4514 |
| `USD|wi028|raw|up_high` | 4 | 4,897 | 4,897 | +0.000 | +0.0000 |

- Fold reconstruction `sum(contrib) = +0.432 bps`; the frozen table spans calib|ev, so `fold_recon_gap_bps` reports the gap to the CALIB edge instead of hiding it.
- Record-only diagnostic: no shortlist, no deployment, no live trading.
