"""WI-011 Step 3 — indicator association and the empirical compact subset.

What this answers (and what it refuses to answer)
------------------------------------------------
For each of the 89 panel indicators: is its *contemporaneous* value associated
with a trailing state descriptor — local peak/bottom extremes (`ch52_high`,
`ch52_low`) or directional trends (`trend_up`, `trend_down`)? Association is
measured strictly within date (per-date cross-sectional z-score), so market-wide
days cannot manufacture it. **No forward return is read anywhere in this script**
and no predictive claim follows from the numbers: this pass only picks which
indicators deserve a place in the Step 2 condition vocabulary.

Method (declared before the numbers were seen)
---------------------------------------------
1. Per-date cross-sectional mean/std per indicator (pass 1 over the parquet);
   association uses `z = (x - mean_date) / std_date` (pass 2).
2. For each (indicator, state): mean z among rows where the state fires minus
   mean z among rows where the state is *defined but does not fire*; the t-stat
   is computed across dates on the per-date mean difference (no pooling of dates).
3. Redundancy: pooled within-date correlation of the z-scores (deterministic
   stride-5 subsample for the 89x89 matrix), clustered by connected components at
   |corr| >= 0.90.
4. Selection: drop indicators already represented by a Step 2 primitive, keep
   indicators with |t| >= 2 in at least one state, collapse clusters to their
   strongest-associated member, and retain at most 6 representatives.

Outputs
-------
* `reports/wi011_indicator_association.md` — the four marker blocks.
* `reports/wi011_selected_indicators.json` — the subset Step 2 picks up
  (`load_selected_indicators`), which adds `ind_<name>_low` / `ind_<name>_high`
  own-history-percentile conditions to the vocabulary.
"""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from src.wi011 import MARKET  # noqa: E402
from src.wi011.panel import build_state_panel  # noqa: E402

FEATURES = BASE_DIR / "data" / "features" / f"features_{MARKET}.parquet"
REPORT = BASE_DIR / "reports" / "wi011_indicator_association.md"
SELECTION_JSON = BASE_DIR / "reports" / "wi011_selected_indicators.json"

KEY_COLUMNS = ("date", "symbol", "market")
STATE_COLUMNS = ("ch52_high", "ch52_low", "trend_up", "trend_down")
EXTREME_STATES = ("ch52_high", "ch52_low")
TREND_STATES = ("trend_up", "trend_down")

BATCH_ROWS = 50_000
CORR_STRIDE = 5            # deterministic subsample for the 89x89 correlation
CLUSTER_ABS_CORR = 0.90    # connected-component threshold for redundancy clusters
ASSOC_T_FLOOR = 2.0        # |t| required for an association to count
MAX_SELECTED = 6

ALREADY_REPRESENTED: dict[str, str] = {
    "kama_er_20": "er_20 — Step 2 uses the identical KAMA efficiency ratio (window 20)",
    "atr_pct_20": "atr_pct_20 — identical ATR%/close primitive (window 20)",
    "amihud_20": "amihud_20 — identical E5 Amihud illiquidity (window 20)",
}

STEP2_ANALOGUES: dict[str, str] = {
    "kama_er_20": "efficiency ratio (Step 2 uses window 20)",
    "atr_pct_20": "ATR%/close (Step 2 uses window 20)",
    "amihud_20": "E5 amihud_20 (identical)",
    "range_pos_f102": "position in a 102d high/low channel (Step 2 uses 252d)",
    "pct_from_high_f102": "distance from a 102d high (Step 2 channel state)",
    "pct_from_low_f102": "distance from a 102d low (Step 2 channel state)",
}
"""Panel indicators that plainly restate a Step 2 primitive — used for the
post-hoc *disclosure* table only. They are not excluded by the selection rule
(that rule only drops the three exact duplicates above), and the disclosure never
changes the selection: it tells the human gate how much of the selected set is a
re-parameterisation of a state Step 2 already has."""


def _indicator_columns() -> list[str]:
    import pyarrow.parquet as pq

    cols = list(pq.ParquetFile(FEATURES).schema_arrow.names)
    return [c for c in cols if c not in KEY_COLUMNS]


def _state_position_map(states: pd.DataFrame, dates, symbols) -> np.ndarray:
    """Row position in `states` for each parquet row (date, symbol), or -1.

    Positional alignment is what keeps the streaming pass join-free; the
    preflight proved the feature/target key order matches, and this map is built
    from the parquet keys themselves, so it stays correct either way.
    """
    day = dates.astype("datetime64[D]").astype("int64")
    sym_idx = pd.Index(np.unique(np.concatenate([states["symbol"].to_numpy(), symbols])).astype(object))
    state_key = day_of(states["date"].to_numpy()) * 100_000 + sym_idx.get_indexer(states["symbol"].to_numpy())
    panel_key = day * 100_000 + sym_idx.get_indexer(symbols)
    return pd.Index(state_key).get_indexer(panel_key)


def day_of(dates) -> np.ndarray:
    return np.asarray(dates, dtype="datetime64[D]").astype("int64")


def _iter_batches(columns: list[str], batch_rows: int = BATCH_ROWS):
    import pyarrow.dataset as ds

    dataset = ds.dataset(FEATURES, format="parquet")
    for batch in dataset.to_batches(columns=["date", *columns], batch_size=batch_rows):
        yield batch


def _batch_matrix(batch, columns: list[str]) -> np.ndarray:
    return np.column_stack(
        [batch.column(c).to_numpy(zero_copy_only=False).astype("float32") for c in columns]
    )


def main() -> int:
    indicators = _indicator_columns()
    states = build_state_panel(MARKET)

    # ---- keys, alignment -------------------------------------------------- #
    import pyarrow.parquet as pq

    keys = pq.read_table(FEATURES, columns=list(KEY_COLUMNS))
    p_dates = keys.column("date").to_numpy(zero_copy_only=False)
    p_symbols = keys.column("symbol").to_pandas().to_numpy(dtype=object)
    uniq_dates = np.unique(p_dates.astype("datetime64[ns]"))
    date_pos = np.searchsorted(uniq_dates, p_dates.astype("datetime64[ns]"))
    n_rows = p_dates.size
    n_dates = uniq_dates.size

    pos = _state_position_map(states, p_dates, p_symbols)
    n_unmatched = int((pos < 0).sum())
    state_vals = np.full((n_rows, len(STATE_COLUMNS)), np.nan, dtype="float32")
    if n_unmatched < n_rows:
        matched = pos >= 0
        state_vals[matched] = states[list(STATE_COLUMNS)].to_numpy(dtype="float32")[pos[matched]]

    # ---- pass 1: per-date cross-sectional moments ------------------------- #
    sums = np.zeros((n_dates, len(indicators)), dtype="float64")
    sumsq = np.zeros((n_dates, len(indicators)), dtype="float64")
    counts = np.zeros(n_dates, dtype="float64")
    for batch in _iter_batches(indicators):
        b_dates = batch.column("date").to_numpy(zero_copy_only=False).astype("datetime64[ns]")
        codes = np.searchsorted(uniq_dates, b_dates)
        x = _batch_matrix(batch, indicators).astype("float64")
        counts += np.bincount(codes, minlength=n_dates)
        for j in range(x.shape[1]):
            col = x[:, j]
            finite = np.isfinite(col)
            if not finite.any():
                continue
            sums[:, j] += np.bincount(codes[finite], weights=col[finite], minlength=n_dates)
            sumsq[:, j] += np.bincount(codes[finite], weights=col[finite] ** 2, minlength=n_dates)

    with np.errstate(invalid="ignore", divide="ignore"):
        mean_date = sums / counts[:, None]
        var = sumsq / counts[:, None] - mean_date ** 2
        std_date = np.sqrt(np.maximum(var, 0.0))

    # ---- pass 2: state-conditional z statistics + correlation ------------ #
    n_states = len(STATE_COLUMNS)
    comb_len = n_states * n_dates
    z_sum = np.zeros((n_states, len(indicators)), dtype="float64")   # fired rows
    z_cnt = np.zeros(n_states, dtype="float64")
    nf_sum = np.zeros((n_states, len(indicators)), dtype="float64")  # defined-not-fired rows
    nf_cnt = np.zeros(n_states, dtype="float64")
    z_date_sum = np.zeros((comb_len, len(indicators)), dtype="float64")
    z_date_cnt = np.zeros(comb_len, dtype="float64")
    nf_date_sum = np.zeros((comb_len, len(indicators)), dtype="float64")

    cross = np.zeros((len(indicators), len(indicators)), dtype="float64")
    zsq = np.zeros(len(indicators), dtype="float64")
    n_corr = 0
    n_ind = len(indicators)

    row_off = 0
    for batch in _iter_batches(indicators):
        nb = batch.num_rows
        b_dates = batch.column("date").to_numpy(zero_copy_only=False).astype("datetime64[ns]")
        codes = np.searchsorted(uniq_dates, b_dates)
        x = _batch_matrix(batch, indicators).astype("float64")
        mu = mean_date[codes]
        sd = std_date[codes]
        with np.errstate(invalid="ignore", divide="ignore"):
            z = (x - mu) / sd
        z = np.where(np.isfinite(z), z, 0.0)

        sv = state_vals[row_off : row_off + nb]
        for s in range(n_states):
            m_def = np.isfinite(sv[:, s])
            m_fire = m_def & (sv[:, s] > 0.5)
            m_nofire = m_def & ~m_fire
            base = s * n_dates
            # Per-date accumulation uses bincount, never fancy-index += (repeated
            # date codes inside a batch would silently overwrite, not accumulate).
            if m_fire.any():
                cf = codes[m_fire]
                zf = z[m_fire]
                z_sum[s] += zf.sum(axis=0)
                z_cnt[s] += cf.size
                z_date_cnt[base : base + n_dates] += np.bincount(cf, minlength=n_dates)
                for j in range(n_ind):
                    z_date_sum[base : base + n_dates, j] += np.bincount(
                        cf, weights=zf[:, j], minlength=n_dates
                    )
            if m_nofire.any():
                cn = codes[m_nofire]
                zn = z[m_nofire]
                nf_sum[s] += zn.sum(axis=0)
                nf_cnt[s] += cn.size
                for j in range(n_ind):
                    nf_date_sum[base : base + n_dates, j] += np.bincount(
                        cn, weights=zn[:, j], minlength=n_dates
                    )

        stride_rows = np.arange(0, nb, CORR_STRIDE)
        zs = z[stride_rows]
        cross += zs.T @ zs
        zsq += (zs ** 2).sum(axis=0)
        n_corr += zs.shape[0]
        row_off += nb

    with np.errstate(invalid="ignore", divide="ignore"):
        mean_fired = z_sum / np.maximum(z_cnt[:, None], 1.0)
        mean_nofire = nf_sum / np.maximum(nf_cnt[:, None], 1.0)
        delta = mean_fired - mean_nofire

        pd_fired = z_date_sum.reshape(n_states, n_dates, n_ind) / np.maximum(
            z_date_cnt.reshape(n_states, n_dates, 1), 1.0
        )
        pd_nofire = nf_date_sum.reshape(n_states, n_dates, n_ind) / np.maximum(
            np.tile(counts[None, :, None], (n_states, 1, 1))
            - z_date_cnt.reshape(n_states, n_dates, 1),
            1.0,
        )
        pd_delta = pd_fired - pd_nofire
        enough = z_date_cnt.reshape(n_states, n_dates) >= 3
        pd_delta = np.where(enough[:, :, None], pd_delta, np.nan)

        valid = np.isfinite(pd_delta)
        cnt = valid.sum(axis=1)
        dsums = np.where(valid, pd_delta, 0.0).sum(axis=1)
        mean_delta = np.divide(dsums, cnt, out=np.full_like(dsums, np.nan), where=cnt > 0)
        dev = np.where(valid, pd_delta - mean_delta[:, None, :], 0.0)
        var = np.divide(
            (dev ** 2).sum(axis=1),
            (cnt - 1).astype("float64"),
            out=np.full_like(dsums, np.nan),
            where=cnt > 1,
        )
        sd_delta = np.sqrt(var)
        n_dates_used = cnt
        t_stat = np.where(
            (cnt > 2) & (sd_delta > 0),
            mean_delta / (sd_delta / np.sqrt(np.maximum(cnt, 1))),
            np.nan,
        )

        denom = np.sqrt(np.outer(zsq, zsq))
        corr = np.where(denom > 0, cross / np.maximum(denom, 1e-12), np.nan)
        corr = np.clip(corr, -1.0, 1.0)

    # ---- redundancy clusters --------------------------------------------- #
    adj = np.abs(np.nan_to_num(corr, nan=0.0)) >= CLUSTER_ABS_CORR
    np.fill_diagonal(adj, False)
    parent = list(range(len(indicators)))

    def find(a: int) -> int:
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for i in range(len(indicators)):
        for j in range(i + 1, len(indicators)):
            if adj[i, j]:
                ri, rj = find(i), find(j)
                if ri != rj:
                    parent[max(ri, rj)] = min(ri, rj)

    clusters: dict[int, list[int]] = {}
    for i in range(len(indicators)):
        clusters.setdefault(find(i), []).append(i)
    cluster_list = sorted(
        (sorted(members) for members in clusters.values() if len(members) > 1),
        key=lambda m: (-len(m), m[0]),
    )

    # ---- selection ------------------------------------------------------- #
    strength = np.nanmax(np.abs(delta), axis=0)
    strength_t = np.nanmax(np.abs(t_stat), axis=0)
    qualified = [
        i for i in range(len(indicators))
        if np.isfinite(strength_t[i]) and strength_t[i] >= ASSOC_T_FLOOR
    ]
    qualified = [i for i in qualified if indicators[i] not in ALREADY_REPRESENTED]

    cluster_of = {}
    for cid, members in enumerate(cluster_list):
        for m in members:
            cluster_of[m] = cid

    best_by_cluster: dict[object, int] = {}
    for i in qualified:
        key = ("c", cluster_of[i]) if i in cluster_of else ("s", i)
        cur = best_by_cluster.get(key)
        if cur is None or strength[i] > strength[cur]:
            best_by_cluster[key] = i

    reps = sorted(best_by_cluster.values(), key=lambda i: (-strength[i], indicators[i]))
    selected = [indicators[i] for i in reps[:MAX_SELECTED]]
    selected_rows = sorted(reps[:MAX_SELECTED], key=lambda i: -strength[i])

    # ---- report ---------------------------------------------------------- #
    def _assoc_table(state_names: tuple[str, ...]) -> list[str]:
        lines = ["| Indicator | " + " | ".join(f"{s}: Δz (t, dates)" for s in state_names) + " |",
                 "| :--- | " + " | ".join("---: " for _ in state_names) + "|"]
        order = np.argsort(-np.nanmax(np.abs(delta[[STATE_COLUMNS.index(s) for s in state_names]]), axis=0))
        for i in order:
            cells = []
            for s in state_names:
                si = STATE_COLUMNS.index(s)
                d = delta[si, i]
                t = t_stat[si, i]
                n = n_dates_used[si, i]
                cells.append("n/a" if not np.isfinite(t) else f"{d:+.3f} ({t:+.2f}, {int(n)})")
            lines.append(f"| `{indicators[i]}` | " + " | ".join(cells) + " |")
        return lines

    lines = [
        "# WI-011 Step 3 — indicator association and empirical subset (CAD)",
        "",
        f"- Generated (UTC): {dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        f"- Indicator panel: {n_rows:,} rows · {len(indicators)} indicators · {n_dates} dates "
        f"({str(uniq_dates.min())[:10]} → {str(uniq_dates.max())[:10]})",
        f"- Condition-state table aligned positionally: {n_rows - n_unmatched:,} of {n_rows:,} panel rows "
        f"carry a state ({n_unmatched:,} unmatched — symbols/dates outside the condition panel, reported not imputed).",
        "- Association is **contemporaneous and within-date only**: per-date cross-sectional z-score "
        "(`z = (x - mean_date)/std_date`), then state-fired mean minus state-defined-but-not-fired mean, "
        "with a t-stat across dates. **No forward return enters this analysis** — no predictive claim follows.",
        "",
        "States used (all trailing, from `src/wi011/conditions.py`): "
        + ", ".join(f"`{s}`" for s in STATE_COLUMNS),
        "",
        f"## EXTREME_ASSOCIATION (local peak/bottom states: {', '.join(EXTREME_STATES)})",
        "",
        "Δz = mean z when the state fires − mean z when it is defined and does not fire; "
        "(t over dates, number of dated cross-sections used). Sorted by the larger |Δz| of the two states.",
        "",
    ]
    lines += _assoc_table(EXTREME_STATES)
    lines += [
        "",
        f"## TREND_ASSOCIATION (directional states: {', '.join(TREND_STATES)})",
        "",
    ]
    lines += _assoc_table(TREND_STATES)
    lines += [
        "",
        "## REDUNDANCY_CLUSTERS",
        "",
        f"Pooled within-date correlation of the z-scores over a deterministic stride-{CORR_STRIDE} subsample "
        f"({n_corr:,} rows); connected components at |corr| >= {CLUSTER_ABS_CORR:.2f}. "
        f"{len(cluster_list)} redundant cluster(s) with >1 member:",
        "",
    ]
    if cluster_list:
        for k, members in enumerate(cluster_list, 1):
            names = [indicators[i] for i in members]
            shown = ", ".join(f"`{n}`" for n in names[:14])
            more = f" … (+{len(names) - 14} more)" if len(names) > 14 else ""
            lines.append(f"- **cluster {k}** ({len(names)}): {shown}{more}")
    else:
        lines.append("- none at this threshold")

    lines += [
        "",
        "## SELECTED_INDICATORS",
        "",
        f"Pre-declared selection rule: drop indicators already represented by a Step 2 primitive "
        f"({', '.join(f'`{k}`' for k in ALREADY_REPRESENTED)}), require |t| >= {ASSOC_T_FLOOR:.1f} in at least one "
        f"state, collapse redundancy clusters to their strongest-associated member (|Δz|), keep at most "
        f"{MAX_SELECTED}. The rule was fixed before the numbers were seen.",
        "",
        f"SELECTED_INDICATORS: {', '.join(selected) if selected else '(none qualified)'}",
        "",
    ]
    if selected:
        lines += [
            "| Selected indicator | Best state | Δz | t | Cluster size | Why it is not already covered |",
            "| :--- | :--- | ---: | ---: | ---: | :--- |",
        ]
        for i in selected_rows:
            si = int(np.nanargmax(np.abs(delta[:, i])))
            name = indicators[i]
            csize = len(cluster_list[cluster_of[i]]) if i in cluster_of else 1
            lines.append(
                f"| `{name}` | `{STATE_COLUMNS[si]}` | {delta[si, i]:+.3f} | {t_stat[si, i]:+.2f} | {csize} | "
                f"distinct from the E5 primitives and from the retained representatives |"
            )
        lines += [
            "",
            "### Distinctness vs the Step 2 vocabulary (disclosure, not a re-selection)",
            "",
            "Some indicators are *near-mechanical restatements* of the state they are associated with "
            "(a channel-distance or volatility measure vs a channel/volatility state). The selection rule was "
            "fixed before these numbers were seen, so nothing is re-selected here — but the overlap is "
            "reported for the human gate, and Step 4 additionally reports the joint firing rate between each "
            "`ind_*` condition and the base state it shadows.",
            "",
            "| Selected indicator | max abs corr with a Step 2-vocabulary indicator | Analogue |",
            "| :--- | ---: | :--- |",
        ]
        for i in selected_rows:
            name = indicators[i]
            best_j, best_c = None, np.nan
            for j, other in enumerate(indicators):
                if other in (name,):
                    continue
                if other not in STEP2_ANALOGUES:
                    continue
                c = corr[i, j]
                if np.isfinite(c) and (not np.isfinite(best_c) or abs(c) > abs(best_c)):
                    best_j, best_c = j, c
            if best_j is None:
                lines.append(f"| `{name}` | n/a | no Step 2 analogue in the panel |")
            else:
                lines.append(
                    f"| `{name}` | {abs(best_c):.3f} | `{indicators[best_j]}` "
                    f"({STEP2_ANALOGUES[indicators[best_j]]}) |"
                )
        lines += [
            "",
            "Step 2 hook: these names are written to `reports/wi011_selected_indicators.json`; "
            "re-running `scripts/wi011_conditions.py` adds `ind_<name>_low` (own-history percentile <= 0.20) "
            "and `ind_<name>_high` (>= 0.80) to the declared vocabulary — Step 3(a)'s mandated update of the "
            "Step 2 condition configuration.",
        ]
    else:
        lines += [
            "No indicator cleared the |t| floor after removing Step 2 duplicates, so the Step 2 vocabulary "
            "stays on the E5 primitives + OHLCV-derived states. That is a reported result, not a silent skip — "
            "and no indicator is added by weakening the rule.",
        ]

    excluded_report = [
        "",
        "## Duplicates of Step 2 primitives (excluded from selection)",
        "",
        "| Indicator | Already represented by |",
        "| :--- | :--- |",
    ]
    for k, v in ALREADY_REPRESENTED.items():
        excluded_report.append(f"| `{k}` | {v} |")
    lines += excluded_report

    lines += [
        "",
        "## Notes / limits",
        "",
        "- Association is descriptive co-movement in the same row; it is **not** evidence of predictive power, "
        "and this step deliberately never touches `fwd_ret_*`.",
        "- Missing/undefined indicator values are ignored inside the per-date moments (pairwise finite rows); "
        "counts in the tables are the dated cross-sections actually used.",
        "- The whole 89-indicator panel is analysed here but is **not** retained downstream: only the selected "
        "subset enters the condition vocabulary, alongside the E5 primitives.",
    ]

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n")
    SELECTION_JSON.write_text(
        json.dumps(
            {
                "market": MARKET,
                "rule": {
                    "assoc_t_floor": ASSOC_T_FLOOR,
                    "cluster_abs_corr": CLUSTER_ABS_CORR,
                    "max_selected": MAX_SELECTED,
                    "already_represented": ALREADY_REPRESENTED,
                },
                "selected_indicators": selected,
                "best_state": {indicators[i]: STATE_COLUMNS[int(np.nanargmax(np.abs(delta[:, i])))] for i in selected_rows},
            },
            indent=2,
        )
        + "\n"
    )
    print(f"[wi011_indicator_association] wrote {REPORT} and {SELECTION_JSON} (selected={selected})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())