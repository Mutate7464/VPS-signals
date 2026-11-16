# Sector map consolidation (WI-073)

Sources: `config/sector_map.csv` (precedence winner) + `IBKRDownload/sector_map.csv`; network gap-fill attempts: 0 (sectors returned: 0).

`before` = incumbent `config/sector_map.csv` as loaded; `after` = consolidated output.

## Coverage per market (panel symbols)

| market | panel | mapped before | non-blank before | mapped after | non-blank after |
|---|---|---|---|---|---|
| CAD | 394 | 394 | 378 | 394 | 378 |
| USD | 674 | 674 | 631 | 674 | 631 |

Note: `before` == `after` — this run consolidated an already-consolidated map (re-run); the incumbent baseline is no longer on disk.

Conflicts recorded (`data/sector_map_conflicts.csv`): 67 (config won on every row).

## Remaining blanks

59 panel symbols appear in the price panels but carry a sector in neither source map. A blank sector means "no value in the sources on hand" (candidate: ETF/trust or just not published in the reference screens) — it is never a claim that the instrument belongs to no sector.

| symbol | market | candidate reading |
|---|---|---|
| AFM | CAD | absent from both source maps |
| ALV | CAD | absent from both source maps |
| HLF | CAD | absent from both source maps |
| HME | CAD | absent from both source maps |
| HPS.A | CAD | absent from both source maps |
| LGD | CAD | absent from both source maps |
| MCD | CAD | absent from both source maps |
| STC | CAD | absent from both source maps |
| VFV | CAD | absent from both source maps |
| XEG | CAD | absent from both source maps |
| XGD | CAD | absent from both source maps |
| XRE | CAD | absent from both source maps |
| XSP | CAD | absent from both source maps |
| ZAG | CAD | absent from both source maps |
| ZCN | CAD | absent from both source maps |
| ZEB | CAD | absent from both source maps |
| AAL | USD | absent from both source maps |
| AAOI | USD | absent from both source maps |
| ARM | USD | absent from both source maps |
| BA | USD | absent from both source maps |
| BABA | USD | absent from both source maps |
| BRK B | USD | absent from both source maps |
| CMCSA | USD | absent from both source maps |
| CPB | USD | absent from both source maps |
| CPRT | USD | absent from both source maps |
| CRWD | USD | absent from both source maps |
| CYTK | USD | absent from both source maps |
| DAL | USD | absent from both source maps |
| DIS | USD | absent from both source maps |
| DKS | USD | absent from both source maps |
| F | USD | absent from both source maps |
| FND | USD | absent from both source maps |
| GILD | USD | absent from both source maps |
| GM | USD | absent from both source maps |
| HAL | USD | absent from both source maps |
| HIMS | USD | absent from both source maps |
| IBIT | USD | absent from both source maps |
| KBR | USD | absent from both source maps |
| KHC | USD | absent from both source maps |
| KR | USD | absent from both source maps |
| LUV | USD | absent from both source maps |
| MMM | USD | absent from both source maps |
| MRK | USD | absent from both source maps |
| MXL | USD | absent from both source maps |
| NKE | USD | absent from both source maps |
| NOK | USD | absent from both source maps |
| PFE | USD | absent from both source maps |
| PG | USD | absent from both source maps |
| PM | USD | absent from both source maps |
| RKLB | USD | absent from both source maps |
| RRC | USD | absent from both source maps |
| S | USD | absent from both source maps |
| SLB | USD | absent from both source maps |
| SMH | USD | absent from both source maps |
| TEM | USD | absent from both source maps |
| TSLA | USD | absent from both source maps |
| VZ | USD | absent from both source maps |
| WMS | USD | absent from both source maps |
| ZS | USD | absent from both source maps |

Consumer caveat: the literal ticker `NA` is written to the map, but `load_sector_map` reads `NA` as NaN under pandas' default `na_values` — the read-only consumer cannot key that one symbol.

## WI-070 readiness

WI-070 readiness: CONDITIONAL — 59 panel symbols have a blank sector: AFM.CAD, ALV.CAD, HLF.CAD, HME.CAD, HPS.A.CAD, LGD.CAD, MCD.CAD, STC.CAD, VFV.CAD, XEG.CAD, XGD.CAD, XRE.CAD, XSP.CAD, ZAG.CAD, ZCN.CAD, ZEB.CAD, AAL.USD, AAOI.USD, ARM.USD, BA.USD, BABA.USD, BRK B.USD, CMCSA.USD, CPB.USD, CPRT.USD, CRWD.USD, CYTK.USD, DAL.USD, DIS.USD, DKS.USD, F.USD, FND.USD, GILD.USD, GM.USD, HAL.USD, HIMS.USD, IBIT.USD, KBR.USD, KHC.USD, KR.USD, LUV.USD, MMM.USD, MRK.USD, MXL.USD, NKE.USD, NOK.USD, PFE.USD, PG.USD, PM.USD, RKLB.USD, RRC.USD, S.USD, SLB.USD, SMH.USD, TEM.USD, TSLA.USD, VZ.USD, WMS.USD, ZS.USD.

Unresolved blanks: 59.
