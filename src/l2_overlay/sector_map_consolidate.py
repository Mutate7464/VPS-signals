"""WI-073 — one canonical sector map: panel-complete `config/sector_map.csv` + conflict ledger.

D-027 §11 (sector map assumed ABSENT until confirmed) is retired by this card: the map is a data
product, not a trading claim (no gate layer). Precedence is declared and deterministic — for a
symbol present in both sources `config/` wins and the override is recorded in
`data/sector_map_conflicts.csv`; a blank never overwrites a non-blank. Symbols absent from both
maps are gap-filled from IBKR contract metadata ONLY (`ib_async`, the `ibkr_ingest.py` pattern) in
the foreground smoke/full run; a metadata miss — or an unreachable gateway — leaves the row blank
and never aborts the run. No sector is invented (WI-073 §1): a blank stays blank and is named in
the report. Sources are read with `na_filter=False` because the literal ticker `NA` (National Bank
of Canada, CAD) must not be coerced to NaN by pandas' default `na_values`.

    uv run python -m src.l2_overlay.sector_map_consolidate --smoke   # synthetic root; real network probe
    uv run python -m src.l2_overlay.sector_map_consolidate           # real root (network gap-fill)

Invariants: n_jobs=2 (unused here — no feature math), no EVAL read, no edits outside `write_files`.
Consumer contract: `swing_bsh.binary_features_ext.load_sector_map` reads the output unchanged.
"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]
CONFIG_MAP_PATH = BASE_DIR / "config/sector_map.csv"
IBKR_MAP_PATH = BASE_DIR / "IBKRDownload/sector_map.csv"
PANEL_ROOT = BASE_DIR / "data/raw_ohlcv"
CONFLICTS_PATH = BASE_DIR / "data/sector_map_conflicts.csv"
REPORT_PATH = BASE_DIR / "reports/sector_map_consolidation.md"

COLUMNS = ("symbol", "market", "sector", "industry", "sub_group", "company_name", "tc_rating")
MARKETS = ("USD", "CAD")
CONFLICT_COLUMNS = ("symbol", "market", "config_sector", "ibkr_sector", "source_won")
BENCHMARK_SYMBOL, BENCHMARK_SECTOR = "SPY", "Benchmark"
IB_HOST, IB_PORT, IB_CLIENT_ID = "127.0.0.1", 4001, 131
IB_CONNECT_TIMEOUT, IB_SYMBOL_TIMEOUT = 4.0, 6.0
N_JOBS = 2
__all__ = ["ACCURACY_NOTE", "BENCHMARK_SECTOR", "COLUMNS", "COLUMN_ORDER", "CONFLICT_COLUMNS",
           "CONFIG_MAP_PATH", "IBKR_MAP_PATH", "MARKETS", "N_JOBS", "PANEL_ROOT", "REPORT_PATH",
           "SECTOR_COLUMN_ORDER", "SOURCE_PRECEDENCE", "canonical_rows", "consolidate", "coverage",
           "fetch_missing_ibkr", "load_sources", "main", "panel_symbols", "pick_sector",
           "report_markdown", "unresolved_blanks", "wi070_readiness"]

logging.getLogger("ib_async").setLevel(logging.WARNING)
logger = logging.getLogger("sector_map_consolidate")

SOURCE_PRECEDENCE = {"config": 0, "ibkr": 1, "network": 2}   # lower wins
COLUMN_ORDER = COLUMNS
SECTOR_COLUMN_ORDER = COLUMNS

# Wording accuracy (WI-073 §1): a blank-sector row here means "not populated by the sources on
# hand", NOT "the instrument has no sector". ETFs (SMH, XEG, …) genuinely have none.
ACCURACY_NOTE = ('A blank sector means "no value in the sources on hand" (candidate: ETF/trust or '
                 "just not published in the reference screens) — it is never a claim that the "
                 "instrument belongs to no sector.")

# Constituent-level replaces are deliberately ABSENT: WI-073 §1 — "it does NOT invent sectors".
# The only declared gap-fill source is IBKR contract metadata (`fetch_missing_ibkr`); a symbol
# absent from both maps (e.g. an ETF with no issuer sector) keeps a blank sector and is named in
# the report's residual list.


def _read_map(path: Path) -> pd.DataFrame:
    """Read one source map losslessly: `na_filter=False` keeps the literal ticker `NA` as text."""
    if not Path(path).exists():
        return pd.DataFrame(columns=list(COLUMNS))
    return _clean(pd.read_csv(path, dtype=str, na_filter=False))


def _clean(frame: pd.DataFrame) -> pd.DataFrame:
    """Normalise one source map to `COLUMNS`, symbols upper-cased, empties as `""`."""
    out = frame.copy()
    for col in COLUMNS:
        if col not in out.columns:
            out[col] = ""
    out = out.loc[:, list(COLUMNS)]
    out["symbol"] = out["symbol"].astype(str).str.strip().str.upper()
    out["market"] = out["market"].astype(str).str.strip().str.upper()
    for col in COLUMNS[2:]:
        out[col] = out[col].fillna("").astype(str).str.strip()
    out = out[(out["symbol"] != "") & (out["market"] != "") & (out["symbol"] != "NAN")]
    # "NAN" is the shape a NaN symbol takes after `astype(str)` when a caller reads with pandas'
    # default `na_values`; it is never a real ticker here (checked 2026-11-16) and must not become
    # a phantom row. `_read_map` avoids the coercion in the first place via `na_filter=False`.
    return out.drop_duplicates(subset=["symbol", "market"], keep="first").reset_index(drop=True)



def panel_symbols(panel_root: Path = PANEL_ROOT) -> dict[str, list[str]]:
    """`market -> sorted panel symbols` from the `market=<M>/symbol=<S>.parquet` layout."""
    root = Path(panel_root)
    found: dict[str, list[str]] = {}
    for market_dir in sorted(root.glob("market=*")):
        market = market_dir.name.split("=", 1)[1].upper()
        symbols = sorted({p.name[len("symbol="):-len(".parquet")].upper()
                          for p in market_dir.glob("symbol=*.parquet")})
        if symbols:
            found[market] = symbols
    return found


def load_sources(*, root: Path = BASE_DIR) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, list[str]]]:
    """`(config_df, ibkr_df, panel_symbols)` — missing source files degrade to empty frames."""
    root = Path(root)
    config_df = _read_map(root / "config/sector_map.csv")
    ibkr_df = _read_map(root / "IBKRDownload/sector_map.csv")
    return config_df, ibkr_df, panel_symbols(root / "data/raw_ohlcv")


def _keyed(frame: pd.DataFrame) -> dict[tuple[str, str], dict]:
    """`(symbol, market) -> row dict` for one cleaned source frame."""
    if frame is None or not len(frame):
        return {}
    return {(str(r["symbol"]), str(r["market"])): r for r in frame.to_dict("records")}


def pick_sector(config_sector: str, ibkr_sector: str, network_sector: str = "") -> tuple[str, str]:
    """`(sector, source_won)` under the declared precedence; a blank never overwrites a non-blank."""
    for value, source in ((config_sector, "config"), (ibkr_sector, "ibkr"), (network_sector, "network")):
        if str(value).strip():
            return str(value).strip(), source
    return "", ""


def fetch_missing_ibkr(symbols, *, markets=None, host: str = IB_HOST, port: int = IB_PORT,
                       timeout: float = IB_SYMBOL_TIMEOUT, connect_timeout: float = IB_CONNECT_TIMEOUT,
                       ib=None) -> dict[tuple[str, str], str]:
    """IBKR contract metadata for `symbols` (network; foreground smoke/full run only).

    `symbols` is a `{market: [symbol]}` mapping. Returns `{(symbol, market): sector}`; a symbol whose
    contract metadata carries no sector, or whose request errors/times out, is simply absent (the
    row stays blank). Returns `{}` when no gateway answers — never raises (network call).
    """
    wanted = {m.upper(): [str(s).upper() for s in syms] for m, syms in dict(symbols or {}).items()}
    wanted = {m: syms for m, syms in wanted.items() if syms}
    if not wanted:
        return {}
    fill: dict[tuple[str, str], str] = {}
    try:
        from ib_async import IB, Stock                            # local import: no hard dependency
        own = ib is None
        if own:
            ib = IB()
            ib.connect(host, port, clientId=IB_CLIENT_ID, timeout=connect_timeout, readonly=True)
        try:
            for market, syms in wanted.items():
                currency = "CAD" if market == "CAD" else "USD"
                for symbol in syms:
                    try:
                        contract = Stock(symbol, "SMART", currency)
                        details = ib.run(ib.reqContractDetailsAsync(contract), timeout=timeout)
                        sector = next((str(d.contract.sector).strip() for d in (details or [])
                                       if getattr(d.contract, "sector", "")), "")
                        if sector:
                            fill[(symbol, market)] = sector
                    except Exception as exc:                      # per-symbol: miss stays blank
                        logger.debug("IBKR metadata miss for %s/%s: %s", market, symbol, exc)
        finally:
            if own:
                try:
                    ib.disconnect()
                except Exception:
                    pass
    except Exception as exc:                                      # no gateway → nothing filled
        logger.warning("IBKR gap-fill unavailable (%s); %d candidate symbols left blank",
                       exc, sum(len(v) for v in wanted.values()))
        return fill
    return fill


def canonical_rows(config_df: pd.DataFrame, ibkr_df: pd.DataFrame,
                   network_fill: dict[tuple[str, str], str] | None = None,
                   panels: dict[str, list[str]] | None = None) -> list[dict]:
    """Row-level merge under `SOURCE_PRECEDENCE` — pure, deterministic, no I/O.

    Panel symbols absent from both maps still get a row (blank sector): the coverage invariant is
    "every panel symbol present", and `candidate reading` in the report explains the blank.
    """
    network_fill = dict(network_fill or {})
    cfg = _keyed(config_df)
    ibk = _keyed(ibkr_df)
    panel_keys = {(str(s).upper(), str(m).upper()) for m, syms in (panels or {}).items() for s in syms}
    keys = set(cfg) | set(ibk) | panel_keys | {(s, m) for (s, m) in network_fill}
    rows = []
    for symbol, market in sorted(keys, key=lambda k: (k[1], k[0])):
        base = dict(cfg.get((symbol, market)) or ibk.get((symbol, market)) or {})
        base = {col: str(base.get(col, "")).strip() for col in COLUMNS}
        base["symbol"], base["market"] = symbol, market
        sector, source = pick_sector(base["sector"], ibk.get((symbol, market), {}).get("sector", ""),
                                     network_fill.get((symbol, market), ""))
        base["sector"] = sector
        default_source = "config" if (symbol, market) in cfg else "ibkr"
        base["_source_won"] = source or default_source
        rows.append(base)
    return rows


def consolidate(config_df: pd.DataFrame, ibkr_df: pd.DataFrame, panels: dict[str, list[str]],
                fill_rows: dict[tuple[str, str], str] | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Pure merge → `(canonical_df, conflicts_df)`. Config precedence, blanks never overwrite."""
    rows = canonical_rows(config_df, ibkr_df, dict(fill_rows or {}), panels)

    ibk_map = _keyed(ibkr_df)
    cfg_map = _keyed(config_df)
    conflicts = []
    for row in rows:
        key = (row["symbol"], row["market"])
        cfg_sector, ibk_sector = cfg_map.get(key, {}).get("sector", ""), ibk_map.get(key, {}).get("sector", "")
        if (cfg_sector or "").strip() and (ibk_sector or "").strip() \
                and cfg_sector.strip() != ibk_sector.strip():
            conflicts.append({"symbol": key[0], "market": key[1], "config_sector": cfg_sector.strip(),
                              "ibkr_sector": ibk_sector.strip(), "source_won": "config"})
    known = {(s, m) for m, syms in panels.items() for s in syms}
    canonical = pd.DataFrame(rows, columns=list(COLUMNS))
    canonical = canonical.loc[:, list(COLUMNS)]
    canonical = canonical[canonical["symbol"].ne("") & canonical["market"].ne("")]
    if known:                                    # panel members first, then the wider config universe
        in_panel = canonical.apply(lambda r: (r["symbol"], r["market"]) in known, axis=1)
        canonical = pd.concat([canonical[in_panel], canonical[~in_panel]], ignore_index=True)
    conflicts_df = pd.DataFrame(conflicts, columns=list(CONFLICT_COLUMNS))
    return canonical.reset_index(drop=True), conflicts_df.reset_index(drop=True)


def coverage(canonical: pd.DataFrame, panels: dict[str, list[str]]) -> dict[str, dict[str, int]]:
    """Per-market `{panel, mapped, non_blank}` counts for the report."""
    stats: dict[str, dict[str, int]] = {}
    sectors = canonical.set_index(["symbol", "market"])["sector"]
    for market, syms in panels.items():
        present = [s for s in syms if (str(s).upper(), str(market).upper()) in sectors.index]
        non_blank = [s for s in present if str(sectors.get((str(s).upper(), str(market).upper()), "")).strip()]
        stats[market] = {"panel": len(syms), "mapped": len(present), "non_blank": len(non_blank)}
    return stats


def unresolved_blanks(canonical: pd.DataFrame, panels: dict[str, list[str]]) -> list[dict[str, str]]:
    """Panel symbols whose canonical sector is blank, as `{symbol, market}` rows (report input)."""
    sectors = canonical.set_index(["symbol", "market"])["sector"]
    out = [{"symbol": s, "market": m} for m, syms in panels.items() for s in syms
           if not str(sectors.get((str(s).upper(), str(m).upper()), "")).strip()]
    return sorted(out, key=lambda r: (r["market"], r["symbol"]))


def wi070_readiness(blanks, coverage_stats=None) -> str:
    """WI-070 readiness line: mapped ⇒ non-blank sector, or the residual is named here."""
    if not blanks:
        return "WI-070 readiness: PASS — every panel symbol maps to a non-blank sector."
    named = ", ".join(f"{r['symbol']}.{r['market']}" for r in blanks)
    return f"WI-070 readiness: CONDITIONAL — {len(blanks)} panel symbols have a blank sector: {named}."


def dirty_blanks(blanks, canonical: pd.DataFrame, network_fill: dict) -> list[dict[str, str]]:
    """Blank panel symbols the network step tried to fill (candidate: ETF/trust, not "no sector")."""
    tried = set(network_fill)
    return [r for r in blanks if (r["symbol"], r["market"]) in tried]


def report_markdown(canonical: pd.DataFrame, conflicts: pd.DataFrame, panels: dict[str, list[str]],
                    *, before_stats: dict[str, dict[str, int]] | None = None,
                    network_fill=None, attempts: int = 0) -> str:
    """Coverage before/after, conflicts count, remaining blanks, WI-070 readiness line.

    `before_stats` is the incumbent `config/sector_map.csv` coverage measured by `main` *before*
    the consolidation overwrites it; omitted → the before-columns read 0.
    """
    stats = coverage(canonical, panels)
    blanks = unresolved_blanks(canonical, panels)
    before_stats = before_stats or {}
    lines = ["# Sector map consolidation (WI-073)", "",
             "Sources: `config/sector_map.csv` (precedence winner) + `IBKRDownload/sector_map.csv`; "
             f"network gap-fill attempts: {attempts} "
             f"(sectors returned: {len(network_fill or {})}).", "",
             "`before` = incumbent `config/sector_map.csv` as loaded; `after` = consolidated output.",
             "", "## Coverage per market (panel symbols)", "",
             "| market | panel | mapped before | non-blank before | mapped after | non-blank after |",
             "|---|---|---|---|---|---|"]
    for market, row in stats.items():
        prior = before_stats.get(market, {})
        lines.append(f"| {market} | {row['panel']} | {prior.get('mapped', 0)} | "
                     f"{prior.get('non_blank', 0)} | {row['mapped']} | {row['non_blank']} |")
    if before_stats == stats:
        lines += ["", "Note: `before` == `after` — this run consolidated an already-consolidated "
                      "map (re-run); the incumbent baseline is no longer on disk."]
    lines += ["", f"Conflicts recorded (`data/sector_map_conflicts.csv`): {len(conflicts)} "
                  f"(config won on every row).", "", "## Remaining blanks", "",
              f"{len(blanks)} panel symbols appear in the price panels but carry a sector in "
              f"neither source map. {ACCURACY_NOTE}", ""]
    if blanks:
        lines.append("| symbol | market | candidate reading |")
        lines.append("|---|---|---|")
        tried = set(network_fill or {})
        for row in blanks:
            reading = "ETF/trust or IBKR metadata miss" if (row["symbol"], row["market"]) in tried \
                else "absent from both source maps"
            lines.append(f"| {row['symbol']} | {row['market']} | {reading} |")
        lines.append("")
    if "NA" in set(canonical["symbol"].astype(str)):
        lines += ["Consumer caveat: the literal ticker `NA` is written to the map, but "
                  "`load_sector_map` reads `NA` as NaN under pandas' default `na_values` — the "
                  "read-only consumer cannot key that one symbol.", ""]
    lines += ["## WI-070 readiness", "", wi070_readiness(blanks), "",
              f"Unresolved blanks: {len(blanks)}.", ""]
    return "\n".join(lines)


def main(argv=None) -> int:
    """Consolidate, write `config/sector_map.csv` + conflicts CSV + report; stdout ≤5 lines."""
    parser = argparse.ArgumentParser(description="WI-073 sector map consolidation")
    parser.add_argument("--smoke", action="store_true", help="synthetic root; still probes IBKR")
    parser.add_argument("--root", default=None, help="override repo root (tests only)")
    parser.add_argument("--no-network", action="store_true", help="skip the IBKR gap-fill probe")
    args = parser.parse_args(argv)
    root = Path(args.root) if args.root else BASE_DIR

    config_df, ibkr_df, panels = load_sources(root=root)
    before_stats = coverage(config_df, panels)          # incumbent map, read before we overwrite it
    mapped = set(_keyed(config_df)) | set(_keyed(ibkr_df))
    missing = {m: [s.upper() for s in syms if (str(s).upper(), str(m).upper()) not in mapped]
               for m, syms in panels.items()}
    fill_rows, attempts = {}, 0
    if not args.no_network:
        attempts = sum(len(v) for v in missing.values())
        fill_rows = fetch_missing_ibkr(missing)
    canonical, conflicts = consolidate(config_df, ibkr_df, panels, fill_rows)

    (root / "config").mkdir(parents=True, exist_ok=True)
    (root / "data").mkdir(parents=True, exist_ok=True)
    (root / "reports").mkdir(parents=True, exist_ok=True)
    canonical.to_csv(root / "config/sector_map.csv", index=False)
    conflicts.to_csv(root / "data/sector_map_conflicts.csv", index=False)
    (root / "reports/sector_map_consolidation.md").write_text(
        report_markdown(canonical, conflicts, panels, before_stats=before_stats,
                        network_fill=fill_rows, attempts=attempts))

    stats = coverage(canonical, panels)
    blanks = unresolved_blanks(canonical, panels)
    print(f"sector_map_consolidate: {len(canonical)} rows "
          f"(cfg {len(config_df)} / ibkr {len(ibkr_df)} / network {len(fill_rows)})")
    print("coverage " + " | ".join(f"{m} {r['non_blank']}/{r['panel']} non-blank"
                                   for m, r in stats.items()))
    print(f"conflicts {len(conflicts)} (config won) | blanks {len(blanks)} | ibkr probes {attempts}")
    print(wi070_readiness(blanks))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
