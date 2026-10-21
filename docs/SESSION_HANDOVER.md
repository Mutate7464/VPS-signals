# SESSION_HANDOVER.md — OpenCode Live Context Ledger

- **Last Updated (UTC):** 2026-10-21 03:03 UTC
- **Active Sprint & Gate Status:** **All gates approved (1–5). Pipeline MVP complete.** Next: production run on real synced IBKR data.
- **Latest Synced Market Date:** DRY RUN (pre-sync). Entire pipeline ran end-to-end on the synthetic random-walk fixture (5 USD + 5 CAD).
- **Peak VPS Memory Observed:** 288 MB max RSS (`pdf_compiler`, both markets, 28 chart pages, 15 s wall clock).
- **Key Artifacts Generated This Session:**
  - `src/pdf_compiler.py` — 4-panel annotated tearsheets via matplotlib `Agg` + `PdfPages` (vector PDF, no GUI), manual candlesticks (no mplfinance/reportlab deps), CB-06 batching (`gc.collect()` every 10 pages).
  - `reports/screener_USD_20261021.pdf` (14 pages) and `reports/screener_CAD_20261021.pdf` (14 pages).
  - Sections: (1) Portfolio Defense by Exit Urgency, (2) Top-N P_15d_Low, (3) Top-N P_20d_Up.
- **Gate 5 outcome:** smoke test (`--top-n 2`) passed → 8 pages; full run (`--top-n 30`) → 14 pages each. `state/PDF_BLOCKED` absent, so rendering proceeded.
- **Deviations to confirm:** matplotlib vector PDF + manual candlesticks instead of `mplfinance` + `ReportLab` (avoids two heavyweight deps; same output intent). Top-SHAP panel plots the raw underlying feature when the driver is a `_cs_pct` rank.
- **Active Anomalies / Quarantined Tickers:** None.
- **Exact Next Command / Prompt for Next Session:**
  - Pull PDFs to the M1 Mac for visual review: `rsync -avz root@<VPS_IP>:/home/yycuser/projects/signals/reports/*.pdf ~/quant-screener-local/reports/`
  - To run for real: ingest on M1 (`python3 -m src.ibkr_ingest --market {USD|CAD|HOLDINGS}`), sync via `sync_to_vps.sh`, then re-run Sprints 1→5 (verify → features/targets → metadata → train → pdf) on the synced data.
