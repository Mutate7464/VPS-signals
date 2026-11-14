"""Helper functions for per-case quarantine triage analysis."""

import pandas as pd
from pathlib import Path
from typing import Tuple, Optional

from src.verify_synced_data import cb01_spike_indices


# Simple split/distribution fractions (excluding 1.0: a ratio near unity is *no*
# level shift, i.e. the price reverted toward the pre-spike level = genuine vol).
SIMPLE_STEP_RATIOS = (
    0.25, 0.33, 0.5, 0.67, 0.75, 1.25, 1.33, 1.5, 1.67, 2.0, 2.5, 3.0, 4.0,
)
STEP_RATIO_TOL = 0.1
# A permanent corp-action step leaves a *flat* new level; genuine volatility keeps
# moving, so the post-spike window is dispersed. Threshold is relative to the level.
STEP_PERSISTENCE_MAX_SPREAD = 0.35


def persistence_spread(df: pd.DataFrame, spike_idx: int) -> Optional[float]:
    """Relative dispersion of the post-spike level window [spike+5, spike+20].

    This is the persistence guard used by :func:`level_step_test`: a permanent
    corporate-action step leaves a flat new level (small spread), while genuine
    volatility keeps ranging. Read-only; returns None when not computable.
    """
    post_window = slice(min(len(df), spike_idx + 5), min(len(df), spike_idx + 20))
    post_close = df.loc[post_window, 'close']
    post_median = post_close.median()
    if len(post_close) == 0 or not post_median:
        return None
    return float((post_close.max() - post_close.min()) / post_median)


def level_step_test(df: pd.DataFrame, spike_idx: int) -> Tuple[Optional[float], Optional[float], Optional[str]]:
    """
    Level-step test: ratio of median close over [spike+5, spike+20] vs median over
    [spike-20, spike-2]. A permanent level shift with a clean ratio near a simple fraction
    (≈2, ≈0.5, ≈4 ...) = corp-action artifact; reversion toward pre-spike level = genuine vol.

    Two guards distinguish a genuine step from a reversal:
      * the ratio must be near a non-unity simple fraction (a ratio ≈ 1 means the price
        came back to the pre-spike level -> genuine vol, cf. the 2020-03-09 cluster);
      * the post-spike level must persist (tight dispersion), not keep ranging.

    Args:
        df: DataFrame with OHLCV data sorted by date
        spike_idx: Index of the spike day

    Returns:
        Tuple of (ratio, clean_ratio_flag, recommendation)
    """
    # Define windows around spike
    pre_window = slice(max(0, spike_idx - 20), max(0, spike_idx - 2))
    post_window = slice(min(len(df), spike_idx + 5), min(len(df), spike_idx + 20))

    # Calculate medians
    pre_median = df.loc[pre_window, 'close'].median()
    post_median = df.loc[post_window, 'close'].median()

    # Avoid division by zero
    if pre_median == 0:
        return None, None, "Cannot calculate ratio due to zero pre-spike median"

    ratio = post_median / pre_median

    # Check if ratio is close to a non-unity simple fraction
    clean_ratio = None
    for sr in SIMPLE_STEP_RATIOS:
        if abs(ratio - sr) < STEP_RATIO_TOL:
            clean_ratio = sr
            break

    if clean_ratio is None:
        return ratio, None, "GENUINE_VOL"  # No clean step: reversal / genuine volatility

    # Persistence: a corp action leaves a flat new level across the post window.
    spread = persistence_spread(df, spike_idx)
    if spread is not None and spread > STEP_PERSISTENCE_MAX_SPREAD:
        return ratio, None, "GENUINE_VOL"  # Clean ratio but the level kept ranging

    return ratio, clean_ratio, "SPLIT_LOOKALIKE"  # Persistent clean step -> corp action


def volume_corroboration(df: pd.DataFrame, spike_idx: int) -> Tuple[Optional[float], Optional[str]]:
    """
    Volume corroboration: median volume ratio (post/pre). Splits leave volume stepping too.
    
    Args:
        df: DataFrame with OHLCV data sorted by date
        spike_idx: Index of the spike day
        
    Returns:
        Tuple of (volume_ratio, recommendation)
    """
    # Define windows around spike
    pre_window = slice(max(0, spike_idx - 5), max(0, spike_idx))
    post_window = slice(min(len(df), spike_idx + 1), min(len(df), spike_idx + 6))
    
    # Calculate medians
    pre_median = df.loc[pre_window, 'volume'].median()
    post_median = df.loc[post_window, 'volume'].median()
    
    # Avoid division by zero
    if pre_median == 0:
        return None, "Cannot calculate volume ratio due to zero pre-spike median"
    
    volume_ratio = post_median / pre_median
    
    # Volume stepping typically indicates splits (large increase in volume)
    # For genuine volatility, volumes are usually more stable
    if volume_ratio > 2.0:
        return volume_ratio, "SPLIT_LOOKALIKE"
    else:
        return volume_ratio, "GENUINE_VOL"


# Return magnitude that counts as a "material" move in the wider window.
MATERIAL_MOVE_ABS = 0.2
# Bars after the spike day treated as the spike event itself (1-2 day event).
SPIKE_EVENT_BARS = 2
# Wide window (bars either side) searched for *separated* material moves.
PATH_WINDOW_BARS = 10


def multi_day_path_analysis(df: pd.DataFrame, spike_idx: int) -> Tuple[bool, Optional[str]]:
    """
    Multi-day path: spike isolated (1-2 days) vs continuation/reversal regime.

    A data artifact / corp-action jump is a *1-2 day* event: the material move is
    confined to the bars immediately around the spike. A genuine regime (crash,
    meme squeeze, biotech move) keeps producing material moves on other, separated
    sessions in the surrounding window.

    Args:
        df: DataFrame with OHLCV data sorted by date
        spike_idx: Index of the spike day

    Returns:
        Tuple of (is_isolated, recommendation)
    """
    n = len(df)
    if spike_idx <= 0 or spike_idx >= n:
        return False, "GENUINE_VOL"

    pre_close = float(df.iloc[spike_idx - 1]['close'])
    if pre_close == 0:
        return False, "GENUINE_VOL"

    spike_return = float(df.iloc[spike_idx]['close']) / pre_close - 1
    if abs(spike_return) < 0.5:
        # Not a material spike -- nothing to isolate.
        return False, "GENUINE_VOL"

    # Bars belonging to the spike event itself (its own 1-2 day window).
    event = set(range(max(1, spike_idx - 1), min(n - 1, spike_idx + SPIKE_EVENT_BARS) + 1))
    # A separated material move counts if it is at least this big.
    threshold = max(MATERIAL_MOVE_ABS, 0.5 * abs(spike_return))

    start_idx = max(1, spike_idx - PATH_WINDOW_BARS)
    end_idx = min(n - 1, spike_idx + PATH_WINDOW_BARS)
    for i in range(start_idx, end_idx + 1):
        if i in event:
            continue
        prev = float(df.iloc[i - 1]['close'])
        if prev == 0:
            continue
        if abs(float(df.iloc[i]['close']) / prev - 1) >= threshold:
            # Material move on a separated session -> continuation/reversal regime.
            return False, "GENUINE_VOL"

    return True, "SPLIT_LOOKALIKE"  # Material move confined to the spike event


def combine_verdicts(level_recommendation: Optional[str], path_recommendation: Optional[str]) -> str:
    """Final combination rule for the quarantine classifier (WI-010 / ADR D-010).

    `SPLIT_LOOKALIKE` requires **both** independent pieces of structural evidence:

      1. a persistent non-unity level step (`level_step_test`, persistence guard
         included), and
      2. an isolated multi-day path (`multi_day_path_analysis`).

    Volume corroboration is deliberately *not* an input: a volume-only anomaly
    (e.g. the 2020-03-09 crash cluster, where a 2-4x volume spike accompanies a
    genuine crash) must never label a ticker split-like on its own. Volume remains
    reported evidence for the human reviewer.
    """
    if level_recommendation == "SPLIT_LOOKALIKE" and path_recommendation == "SPLIT_LOOKALIKE":
        return "SPLIT_LOOKALIKE"
    return "GENUINE_VOL"


def quarantine_verdict(analysis: dict) -> str:
    """Map a classifier result to the report verdict vocabulary (read-only).

    REINSTATE / KEEP_QUARANTINED / FIX_DATA / OWNER_ACTION / AMBIGUOUS — the same
    vocabulary as the WI-008 baseline report. No verdict here changes state; the
    per-row decision stays with the human gate.
    """
    status = analysis.get("status")

    if status == "NO_FILE":
        return "OWNER_ACTION"  # e.g. parquet never downloaded — admin-owned
    if status in ("ERROR", "READ_ERROR"):
        return "AMBIGUOUS"
    if status == "NO_SPIKE":
        # CB-01 no longer trips on disk: the quarantine reason is resolved.
        return "REINSTATE"
    if analysis.get("non_positive_close"):
        # Non-positive closes make the ratio family meaningless: data must be
        # repaired before any reinstate/keep decision (ICL-style evidence).
        return "FIX_DATA"
    if analysis.get("recommendation") == "SPLIT_LOOKALIKE":
        return "KEEP_QUARANTINED"
    return "REINSTATE"


def analyze_ticker_parquet(symbol: str, market: str, base_dir: Optional[Path] = None) -> dict:
    """
    Analyze a ticker's parquet file for quarantine triage.

    The classifier verdict comes from the single tested combination rule
    (:func:`combine_verdicts`): a persistent non-unity level step AND an isolated
    multi-day path are jointly required for `SPLIT_LOOKALIKE`. Volume is returned
    as evidence only and never votes. Use :func:`quarantine_verdict` for the
    report-level verdict.

    Memory-bounded: one symbol's parquet at a time, three columns only.

    Args:
        symbol: Ticker symbol
        market: Market (USD/CAD)
        base_dir: Repository root override (tests); defaults to this repo.

    Returns:
        Dictionary with analysis results
    """
    root = Path(base_dir) if base_dir is not None else Path(__file__).resolve().parents[1]
    parquet_path = root / "data" / "raw_ohlcv" / f"market={market}" / f"symbol={symbol}.parquet"

    if not parquet_path.exists():
        return {
            "symbol": symbol,
            "market": market,
            "status": "NO_FILE",
            "error": f"Parquet file not found: {parquet_path}"
        }

    try:
        # Arrow column scan: only the columns this analysis needs (bounded memory).
        df = pd.read_parquet(parquet_path, columns=["date", "close", "volume"])
        df = df.sort_values("date").reset_index(drop=True)

        # Data sanity: non-positive closes invalidate every ratio-based test.
        non_positive_close = bool((df["close"].astype("float64") <= 0).any())

        # CB-01 spike indices (single source of truth: > +100% or < -50%).
        spike_indices = cb01_spike_indices(df)

        if len(spike_indices) == 0:
            return {
                "symbol": symbol,
                "market": market,
                "status": "NO_SPIKE",
                "non_positive_close": non_positive_close,
                "error": "No spikes found"
            }

        # Analyze the first spike
        spike_idx = int(spike_indices[0])

        # Perform all analyses
        level_ratio, clean_ratio, level_recommendation = level_step_test(df, spike_idx)
        volume_ratio, volume_recommendation = volume_corroboration(df, spike_idx)
        is_isolated, path_recommendation = multi_day_path_analysis(df, spike_idx)

        # Final rule: conjunction of level-step persistence and isolated path.
        # (volume_recommendation is evidence only -- deliberately not an input)
        final_recommendation = combine_verdicts(level_recommendation, path_recommendation)

        # Format the spike date properly
        spike_date = str(df.iloc[spike_idx]["date"].date()) if hasattr(df.iloc[spike_idx]["date"], 'date') else str(df.iloc[spike_idx]["date"])

        # Cast numpy scalars to plain floats for a stable downstream API.
        level_ratio_f = None if level_ratio is None else float(level_ratio)
        volume_ratio_f = None if volume_ratio is None else float(volume_ratio)
        spread_f = persistence_spread(df, spike_idx)

        return {
            "symbol": symbol,
            "market": market,
            "spike_date": spike_date,
            "spike_return": float(df["close"].astype("float64").pct_change().iloc[spike_idx]),
            "level_ratio": level_ratio_f,
            "clean_ratio": clean_ratio,
            "persistence_spread": spread_f,
            "level_verdict": level_recommendation,
            "volume_ratio": volume_ratio_f,
            "volume_verdict": volume_recommendation,
            "is_isolated": is_isolated,
            "path_verdict": path_recommendation,
            "non_positive_close": non_positive_close,
            "recommendation": final_recommendation,
            "status": "SUCCESS"
        }

    except Exception as e:
        return {
            "symbol": symbol,
            "market": market,
            "status": "ERROR",
            "error": str(e)
        }