"""WI-047 — T1 feature inventory of the WI-036 detection-bar panel (research only).

`binary_features_ext.build_variant_panel` assembles the panel from seven blocks
(WI-016 grid, raw volume/VWAP/barCount, event-quality meta, calendar, breadth,
sector one-hots/ranks, cross-sectional ranks). This module *parses* that source
file with `ast` (it never builds a panel), so the inventory can be re-run when the
panel grows: every column gets a D-025 Tier-1 family plus the WI-040 winner-cell
OOF permutation evidence (`reports/wi040_calibration.md`: USD/CAD `exact_full_k0.8`
/ `b_hold` / xgboost / h13).

L1 license (D-023 §2): inventory + attribution only — no model claim, nothing
here is an adopted feature.
"""

from __future__ import annotations

import ast
import itertools
from pathlib import Path

import pandas as pd

from src.feature_engine import wi016_feature_names

BASE_DIR = Path(__file__).resolve().parents[2]
MODULE_PATH = Path(__file__).resolve().parent / "binary_features_ext.py"
SECTOR_MAP_PATH = BASE_DIR / "config" / "sector_map.csv"
MAX_SECTORS = 12
MIN_COVERAGE = 0.95
CS_PREFIX = "cs_"

# WI-040 winner-cell OOF permutation importance (mean AUC drop), top-20 per market.
ATTRIBUTION_USD: dict[str, float] = {
    "cs_entropy_102": 0.0292, "entropy_24": 0.0130, "atr_pct_3": 0.0094, "hurst_15": 0.0072,
    "kama_er_15": 0.0065, "hurst_39": 0.0053, "adx_144": 0.0050, "month": 0.0017,
    "di_spread_233": 0.0008, "adx_21": 0.0006, "entropy_9": 0.0005, "adx_3": 0.0002,
    "dow": 0.0001, "state_is_bottom": 0.0001,
}
ATTRIBUTION_CAD: dict[str, float] = {
    "atr_pct_3": 0.0469, "di_spread_3": 0.0163, "range_compression_8_55": 0.0106,
    "entropy_39": 0.0059, "hurst_39": 0.0030, "adx_21": 0.0029, "kama_er_15": 0.0017,
    "swing_depth_atr": 0.0002, "cs_di_spread_144": 0.0001, "k": 0.0,
}

# Ordered rules -> D-025 Tier-1 family (exact keys first, then first prefix match wins).
FAMILY_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("sector", ("sec_", "srel_")),
    ("cross_sectional", (CS_PREFIX,)),
    ("breadth", ("breadth_",)),
    ("event_quality", ("swing_depth_atr", "bars_since_opp", "dd_age")),
    ("calendar", ("dow", "month")),
    ("entropy_fractal", ("entropy_", "hurst_", "kama_er_", "frac_diff_")),
    ("volatility", ("atr_pct_", "bb_width_", "yangzhang_", "range_width_", "range_compression_", "gap_z")),
    ("volume_liquidity", ("volume_", "vwap_dist", "vwap_zscore_", "obv_zscore_", "amihud_", "bar_count_")),
    ("mean_reversion", ("rsi_", "bb_pct_b_", "range_pos_", "kalman_spread_",
                        "pct_from_high", "pct_from_low")),
    ("momentum", ("adx_", "di_spread_", "macd_norm_", "donchian_break_", "fib_dist_")),
)
KEYS: tuple[str, ...] = ("symbol", "date", "state", "close", "atr", "k")
FAMILIES: tuple[str, ...] = ("keys",) + tuple(f for f, _ in FAMILY_RULES)


def classify(column: str) -> str | None:
    """D-025 Tier-1 family of one panel column (`None` = unclassified)."""
    if column in KEYS or column.startswith("state_is_"):
        return "keys"
    for family, prefixes in FAMILY_RULES:
        if column.startswith(prefixes):
            return family
    return None


# --------------------------------------------------------------------------- #
# Source parser — the panel schema is read out of binary_features_ext.py
# --------------------------------------------------------------------------- #
_PLACEHOLDER = r"\d+"


def _literal(node) -> str | None:
    """Concrete column name from a literal key, pattern from an f-string key."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        return "".join(v.value if isinstance(v, ast.Constant) and isinstance(v.value, str)
                       else _PLACEHOLDER for v in node.values)
    return None


def _subscripts(owner: ast.AST, name: str) -> list[str]:
    """Literal/pattern subscripts on `name`, e.g. `out["vwap_dist"]`."""
    return sorted({p for n in ast.walk(owner) if isinstance(n, ast.Subscript)
                   and isinstance(n.value, ast.Name) and n.value.id == name
                   for p in [_literal(n.slice)] if p})


def _expand(templates: list[str], values: list[str]) -> list[str]:
    """Materialise `f"volume_z_{w}"` patterns for a `for w in (21, 55)` loop."""
    out: list[str] = []
    for t in templates:
        n = t.count(_PLACEHOLDER)
        for combo in itertools.product(values, repeat=n) if n else [()]:
            s = t
            for v in combo:
                s = s.replace(_PLACEHOLDER, v, 1)
            out.append(s)
    return out


def _loop_values(owner: ast.AST, var: str) -> list[str]:
    """Numeric literals of the first `for <var> in (...)` loop in `owner`."""
    for n in ast.walk(owner):
        if isinstance(n, ast.For) and isinstance(n.target, ast.Name) and n.target.id == var:
            return [str(c.value) for c in ast.walk(n.iter) if isinstance(c, ast.Constant)]
    return []


def _df_dict_keys(owner: ast.AST) -> list[str]:
    """Keys of `pd.DataFrame({...})` literals inside `owner`."""
    return [k.value for n in ast.walk(owner) if isinstance(n, ast.Call)
            and isinstance(n.func, ast.Attribute) and n.func.attr == "DataFrame"
            and n.args and isinstance(n.args[0], ast.Dict)
            for k in n.args[0].keys if isinstance(k, ast.Constant)]


def _assigned_node(owner: ast.AST, var: str) -> ast.AST | None:
    for n in ast.walk(owner):
        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == var
                                             for t in n.targets):
            return n.value
    return None


def parse_panel_schema(path: Path = MODULE_PATH) -> dict:
    """Structural schema of the panel builder, parsed from source (no execution)."""
    tree = ast.parse(Path(path).read_text())
    top = {t.targets[0].id: t.value for t in tree.body if isinstance(t, ast.Assign)
           and isinstance(t.targets[0], ast.Name)}
    fns = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    ext, eq, sec, build = (fns["_ext_raw_features"], fns["_event_quality"],
                           fns["_sector_block"], fns["build_variant_panel"])
    cal = _assigned_node(build, "cal")
    bd_cols = [e.value for n in ast.walk(build) if isinstance(n, ast.Call)
               and isinstance(n.func, ast.Attribute) and n.func.attr == "DataFrame"
               for kw in n.keywords if kw.arg == "columns" and isinstance(kw.value, ast.List)
               for e in kw.value.elts if isinstance(e, ast.Constant)]
    startswith = sorted({s.value for n in ast.walk(fns["candidate_features"])
                         if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                         and n.func.attr == "startswith" for a in n.args
                         for s in ast.walk(a)
                         if isinstance(s, ast.Constant) and isinstance(s.value, str)})
    return {
        "smooth_prefixes": [s.value for s in ast.walk(top["SMOOTH_PREFIXES"])
                            if isinstance(s, ast.Constant)],
        "sector_rank": [s.value for s in ast.walk(top["SECTOR_RANK_FEATURES"])
                        if isinstance(s, ast.Constant)],
        "ext_prefixes": list(startswith),
        "ext_columns": _expand(_subscripts(ext, "out"), _loop_values(ext, "w")),
        "event_quality": _df_dict_keys(eq),
        "calendar": _df_dict_keys(cal) if cal is not None else [],
        "breadth": [c for c in bd_cols if c != "date"],
        "key_columns": _subscripts(build, "keep"),
        "sector_prefixes": sorted({t.split(_PLACEHOLDER)[0] for t in _subscripts(sec, "out") + [
            _literal(n.key) for n in ast.walk(sec) if isinstance(n, ast.DictComp)]}),
        "cs_prefix": "".join(a.value for n in ast.walk(fns["_cross_sectional"])
                             if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                             and n.func.attr == "add_prefix" for a in n.args),
    }


def sector_names(path: Path = SECTOR_MAP_PATH) -> list[str]:
    """Top-`MAX_SECTORS` sectors by universe count (mirrors `_sector_block`)."""
    if not Path(path).exists():
        return []
    sec = pd.read_csv(path, usecols=["sector"])["sector"].fillna("UNKNOWN")
    return [str(s) for s in sec.value_counts().index[:MAX_SECTORS]]


def panel_schema(parsed: dict | None = None, sectors: list[str] | None = None) -> dict[str, str]:
    """`column -> block` for the full panel schema (reconstructed, data-free)."""
    p = parsed or parse_panel_schema()
    grid = wi016_feature_names()
    blocks = {"key": p["key_columns"], "wi016": grid, "ext": p["ext_columns"],
              "event_quality": p["event_quality"], "calendar": p["calendar"],
              "breadth": p["breadth"]}
    schema = {c: b for b, cols in blocks.items() for c in cols}
    for s in (sector_names() if sectors is None else sectors):
        schema[f"sec_{s}"] = "sector"
    for f in p["sector_rank"]:
        if f in schema:
            schema[f"srel_{f}"] = "sector"
    for c in grid:
        if c.startswith(tuple(p["smooth_prefixes"])):
            schema[f"{p['cs_prefix']}{c}"] = "cs_rank"
    return schema


def build_inventory(panel=None, parsed: dict | None = None,
                    sectors: list[str] | None = None) -> pd.DataFrame:
    """One row per panel column: block, Tier-1 family, WI-040 evidence, aligned flag.

    `panel` is a DataFrame or an iterable of column names. When omitted, the
    schema is reconstructed from the parsed source (no data access).
    """
    schema = panel_schema(parsed, sectors)
    cols = list(panel.columns) if isinstance(panel, pd.DataFrame) else (
        list(panel) if panel is not None else list(schema))
    rows = [{"column": c, "block": schema.get(c, "unparsed"), "family": classify(c),
             "usd_auc_drop": ATTRIBUTION_USD.get(c), "cad_auc_drop": ATTRIBUTION_CAD.get(c)}
            for c in cols]
    inv = pd.DataFrame(rows)
    inv["aligned"] = inv["family"].notna() & (inv["usd_auc_drop"].fillna(0) + inv["cad_auc_drop"].fillna(0) > 0)
    return inv[["column", "block", "family", "aligned", "usd_auc_drop", "cad_auc_drop"]]


def coverage(inventory: pd.DataFrame) -> float:
    """Fraction of inventory rows carrying a Tier-1 family."""
    return float(inventory["family"].notna().mean()) if len(inventory) else 0.0


def unmatched(inventory: pd.DataFrame) -> list[str]:
    """Columns no family rule claims — the honest gap the report must explain."""
    return inventory.loc[inventory["family"].isna(), "column"].tolist()


def family_summary(inventory: pd.DataFrame) -> pd.DataFrame:
    """Per-family column counts + best WI-040 evidence (rows sorted by size)."""
    g = inventory.dropna(subset=["family"]).groupby("family")
    out = pd.DataFrame({"columns": g["column"].nunique(), "aligned": g["aligned"].sum(),
                        "usd_auc_drop_max": g["usd_auc_drop"].max(),
                        "cad_auc_drop_max": g["cad_auc_drop"].max()})
    return out.astype({"aligned": int}).sort_values("columns", ascending=False)


def main() -> int:
    """Smoke: exit 0 only when the inventory classifies >= MIN_COVERAGE of columns."""
    inv = build_inventory()
    fam = family_summary(inv)
    print(f"WI-047 inventory: {len(inv)} panel columns, {int(inv['family'].notna().sum())} classified, "
          f"coverage {coverage(inv):.3f} (bar {MIN_COVERAGE:.2f})")
    print("unmatched: " + (", ".join(unmatched(inv)) or "none"))
    print("families (n/aligned): " + "; ".join(
        f"{f} {int(r['columns'])}/{int(r['aligned'])}" for f, r in fam.iterrows()))
    return 0 if coverage(inv) >= MIN_COVERAGE else 1


if __name__ == "__main__":
    raise SystemExit(main())
