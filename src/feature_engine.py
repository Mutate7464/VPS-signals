"""Sprint 2 — Multi-horizon point-in-time feature engine (classic + frontier).

Every indicator is computed strictly on trailing windows (<= t) and cast to
float32. No future data is referenced. `tests/test_leakage.py` gates the
causal-invariance guarantee (future perturbation must not alter features at
t <= cutoff).

CLI:
    python -m src.feature_engine --market USD --validate-leakage
    python -m src.feature_engine --market ALL   # USD + CAD
"""

from __future__ import annotations

import argparse
import datetime as dt
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from src.state_manager import init_dirs, update_state
from src.targets import TARGET_COLUMNS, compute_targets, wilder_atr

BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw_ohlcv"
FIXTURE_DIR = BASE_DIR / "data" / "raw_ohlcv_test"
FEATURES_DIR = BASE_DIR / "data" / "features"
REPORT_PATH = BASE_DIR / "reports" / "sprint2_feature_summary.md"

WINDOWS = [5, 10, 20, 50, 100]
RSI_WINDOWS = [5, 14, 21]
HURST_WINDOWS = [20, 50, 100]
ENTROPY_WINDOWS = [10, 20]
ATR_WINDOW = 20
FRAC_DIFF_D = 0.40
FRAC_DIFF_WINDOW = 100


# --------------------------------------------------------------------------- #
# Classic indicators
# --------------------------------------------------------------------------- #
def _rsi(close: pd.Series, window: int) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = gain.ewm(alpha=1.0 / window, min_periods=window, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / window, min_periods=window, adjust=False).mean()
    rs = avg_gain / (avg_loss + 1e-12)
    return 100.0 - 100.0 / (1.0 + rs)


def _adx(df: pd.DataFrame, window: int):
    high = df["high"].astype("float64")
    low = df["low"].astype("float64")
    close = df["close"].astype("float64")
    up = high.diff()
    down = -low.diff()
    plus_dm = up.where((up > down) & (up > 0.0), 0.0)
    minus_dm = down.where((down > up) & (down > 0.0), 0.0)
    prev_close = close.shift(1)
    tr = pd.concat(
        [high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1
    ).max(axis=1)
    atr = tr.ewm(alpha=1.0 / window, min_periods=window, adjust=False).mean()
    plus_di = 100.0 * plus_dm.ewm(alpha=1.0 / window, min_periods=window, adjust=False).mean() / (atr + 1e-12)
    minus_di = 100.0 * minus_dm.ewm(alpha=1.0 / window, min_periods=window, adjust=False).mean() / (atr + 1e-12)
    dx = 100.0 * (plus_di - minus_di).abs() / (plus_di + minus_di + 1e-12)
    adx = dx.ewm(alpha=1.0 / window, min_periods=window, adjust=False).mean()
    return adx, plus_di - minus_di


def _efficiency_ratio(close: pd.Series, window: int) -> pd.Series:
    change = close.diff(window).abs()
    volatility = close.diff().abs().rolling(window, min_periods=window).sum()
    return change / (volatility + 1e-12)


# --------------------------------------------------------------------------- #
# Frontier indicators
# --------------------------------------------------------------------------- #
def _hurst_rs(x: np.ndarray) -> float:
    """Rescaled-range Hurst exponent over a trailing window (raw rolling apply)."""
    x = np.asarray(x, dtype="float64")
    x = x[~np.isnan(x)]
    n = len(x)
    if n < 8:
        return np.nan
    max_lag = min(n // 4, 20)
    lags = np.arange(2, max_lag + 1)
    rs_vals = []
    for lag in lags:
        chunk_rs = []
        for i in range(0, n - lag + 1, lag):
            c = x[i : i + lag]
            if len(c) < 2 or np.std(c) == 0.0:
                continue
            dev = np.cumsum(c - c.mean())
            r = dev.max() - dev.min()
            s = c.std(ddof=0)
            if s > 0.0:
                chunk_rs.append(r / s)
        rs_vals.append(np.mean(chunk_rs) if chunk_rs else np.nan)
    rs_vals = np.asarray(rs_vals, dtype="float64")
    mask = ~np.isnan(rs_vals) & (rs_vals > 0.0)
    if mask.sum() < 2:
        return np.nan
    return float(np.polyfit(np.log(lags[mask]), np.log(rs_vals[mask]), 1)[0])


def _frac_diff_fixed(series: pd.Series, d: float, window: int) -> pd.Series:
    """Fixed-window fractional differentiation (trailing convolution of log price)."""
    weights = [1.0]
    for k in range(1, window):
        weights.append(-weights[-1] * (d - k + 1) / k)
    w_rev = np.asarray(weights, dtype="float64")[::-1]

    def _apply(a: np.ndarray) -> float:
        return float(np.dot(w_rev, a))

    return series.rolling(window, min_periods=window).apply(_apply, raw=True)


def _shannon_entropy(x: np.ndarray) -> float:
    """Shannon entropy of discretized log returns (raw rolling apply)."""
    x = np.asarray(x, dtype="float64")
    x = x[np.isfinite(x)]
    if len(x) < 4:
        return np.nan
    rets = np.diff(np.log(x))
    rets = rets[np.isfinite(rets)]
    if len(rets) == 0:
        return np.nan
    counts, _ = np.histogram(rets, bins=10)
    p = counts / counts.sum()
    p = p[p > 0]
    if p.size == 0:
        return 0.0
    return float(-np.sum(p * np.log(p)))


def _kalman_filter(x: np.ndarray, q: float = 1e-4, r: float = 1e-2) -> np.ndarray:
    """1D Kalman filter (random-walk state + noise), forward recursion (causal)."""
    x = np.asarray(x, dtype="float64")
    n = len(x)
    states = np.empty(n)
    state = x[0]
    p = 1.0
    for i in range(n):
        p = p + q
        k = p / (p + r)
        state = state + k * (x[i] - state)
        p = (1.0 - k) * p
        states[i] = state
    return states


def _vwap_zscore(df: pd.DataFrame, window: int) -> pd.Series:
    typical = (df["high"] + df["low"] + df["close"]) / 3.0
    pv = typical * df["volume"]
    vwap = pv.rolling(window, min_periods=window).sum() / (
        df["volume"].rolling(window, min_periods=window).sum() + 1e-12
    )
    dev = df["close"] - vwap
    m = dev.rolling(window, min_periods=window).mean()
    s = dev.rolling(window, min_periods=window).std(ddof=1)
    return (dev - m) / (s + 1e-12)


def _amihud(df: pd.DataFrame, window: int) -> pd.Series:
    ret = df["close"].pct_change().abs()
    dollar_vol = (df["close"] * df["volume"]) + 1e-12
    return (ret / dollar_vol).rolling(window, min_periods=window).mean()


def _yang_zhang_vol(df: pd.DataFrame, window: int) -> pd.Series:
    ho = np.log(df["high"] / df["open"])
    lo = np.log(df["low"] / df["open"])
    co = np.log(df["close"] / df["open"])
    oc = np.log(df["open"] / df["close"].shift(1))
    rs = ho * (ho - co) + lo * (lo - co)
    k = 0.34 / (1.34 + (window + 1) / (window - 1))
    sig_o2 = oc.rolling(window, min_periods=window).var(ddof=1)
    sig_c2 = co.rolling(window, min_periods=window).var(ddof=1)
    sig_rs2 = rs.rolling(window, min_periods=window).mean()
    var = sig_o2 + k * sig_c2 + (1 - k) * sig_rs2
    return np.sqrt(var) * np.sqrt(252.0)


# --------------------------------------------------------------------------- #
# Feature assembly
# --------------------------------------------------------------------------- #
def compute_features(df: pd.DataFrame) -> pd.DataFrame:
    """Compute the full point-in-time feature matrix (float32).

    Assumes `df` is sorted by date with columns
    [date, open, high, low, close, volume] and a clean 0..n-1 index.
    """
    close = df["close"].astype("float64")
    high = df["high"].astype("float64")
    low = df["low"].astype("float64")

    feats = pd.DataFrame(index=df.index)
    if "date" in df.columns:
        feats["date"] = df["date"]

    atr20 = wilder_atr(df, ATR_WINDOW).astype("float64")

    # Classic: RSI (+ 5d slope)
    for w in RSI_WINDOWS:
        feats[f"rsi_{w}"] = _rsi(close, w).astype("float32")
    feats["rsi_14_slope_5"] = feats["rsi_14"].diff(5).astype("float32")

    # Classic: Bollinger %B + width
    for w in WINDOWS:
        sma = close.rolling(w, min_periods=w).mean()
        std = close.rolling(w, min_periods=w).std(ddof=1)
        upper = sma + 2.0 * std
        lower = sma - 2.0 * std
        feats[f"bb_pct_b_{w}"] = ((close - lower) / (upper - lower + 1e-12)).astype("float32")
        feats[f"bb_width_{w}"] = ((upper - lower) / (sma + 1e-12)).astype("float32")

    # Classic: ATR-normalized MACD (12, 26, 9)
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    macd_hist = macd_line - macd_line.ewm(span=9, adjust=False).mean()
    feats["macd_norm_line"] = (macd_line / (atr20 + 1e-12)).astype("float32")
    feats["macd_norm_hist"] = (macd_hist / (atr20 + 1e-12)).astype("float32")

    # Classic: ADX + DI spread
    for w in WINDOWS:
        adx, di_spread = _adx(df, w)
        feats[f"adx_{w}"] = adx.astype("float32")
        feats[f"di_spread_{w}"] = di_spread.astype("float32")

    # Classic: ATR percentage
    for w in WINDOWS:
        feats[f"atr_pct_{w}"] = (wilder_atr(df, w) / (close + 1e-12)).astype("float32")

    # Classic: OBV z-score
    obv = (np.sign(close.diff()).fillna(0.0) * df["volume"]).cumsum()
    obv_slope = obv.diff()
    for w in WINDOWS:
        m = obv_slope.rolling(w, min_periods=w).mean()
        s = obv_slope.rolling(w, min_periods=w).std(ddof=1)
        feats[f"obv_zscore_{w}"] = ((obv_slope - m) / (s + 1e-12)).astype("float32")

    # Frontier: Hurst exponent
    for w in HURST_WINDOWS:
        feats[f"hurst_{w}"] = close.rolling(w, min_periods=w).apply(_hurst_rs, raw=True).astype("float32")

    # Frontier: fractional differentiation of log close
    feats["frac_diff_close"] = _frac_diff_fixed(np.log(close), FRAC_DIFF_D, FRAC_DIFF_WINDOW).astype("float32")

    # Frontier: Shannon entropy
    for w in ENTROPY_WINDOWS:
        feats[f"entropy_{w}"] = close.rolling(w, min_periods=w).apply(_shannon_entropy, raw=True).astype("float32")

    # Frontier: Kalman filter spread / ATR
    kf = _kalman_filter(close.to_numpy())
    feats["kalman_spread_atr"] = ((close - kf) / (atr20 + 1e-12)).astype("float32")

    # Frontier: KAMA efficiency ratio
    for w in WINDOWS:
        feats[f"kama_er_{w}"] = _efficiency_ratio(close, w).astype("float32")

    # Frontier: VWAP z-score
    for w in WINDOWS:
        feats[f"vwap_zscore_{w}"] = _vwap_zscore(df, w).astype("float32")

    # Frontier: Amihud illiquidity
    for w in WINDOWS:
        feats[f"amihud_{w}"] = _amihud(df, w).astype("float32")

    # Frontier: Yang-Zhang volatility
    for w in WINDOWS:
        feats[f"yangzhang_{w}"] = _yang_zhang_vol(df, w).astype("float32")

    return feats


# --------------------------------------------------------------------------- #
# Data loading + dataset building
# --------------------------------------------------------------------------- #
def load_market_frame(market: str) -> pd.DataFrame:
    """Load raw OHLCV for a market (real synced data if present, else fixture)."""
    mdir = RAW_DIR / f"market={market}"
    roots = [RAW_DIR] if (mdir.exists() and list(mdir.glob("*.parquet"))) else [FIXTURE_DIR]
    frames = []
    for root in roots:
        m = root / f"market={market}"
        if not m.exists():
            continue
        for p in sorted(m.glob("*.parquet")):
            symbol = p.stem.split("=", 1)[-1]
            d = pd.read_parquet(p)
            d["symbol"] = symbol
            d["market"] = market
            frames.append(d)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def build_market_dataset(market: str):
    """Load -> features + targets -> drop undefined-label rows -> int8 targets."""
    df = load_market_frame(market)
    if df.empty:
        return None, []
    df = df.sort_values(["symbol", "date"]).reset_index(drop=True)

    # Compute per-symbol so target/feature windows don't straddle ticker boundaries.
    feat_parts, targ_parts = [], []
    for sym, g in df.groupby("symbol", sort=False):
        g = g.sort_values("date").reset_index(drop=True)
        f = compute_features(g)
        t = compute_targets(g)
        f = pd.concat([f, t], axis=1)
        f["symbol"] = sym
        f["market"] = market
        feat_parts.append(f)
    merged = pd.concat(feat_parts, ignore_index=True)

    merged = merged.dropna(subset=TARGET_COLUMNS)
    for c in TARGET_COLUMNS:
        merged[c] = merged[c].astype("int8")
    return merged, TARGET_COLUMNS


# --------------------------------------------------------------------------- #
# Summary + CLI
# --------------------------------------------------------------------------- #
def write_summary(summaries: dict) -> None:
    lines = [
        "# Sprint 2 — Feature Engineering & Target Summary (Gate 2)",
        "",
        f"- Generated (UTC): {dt.datetime.now(dt.timezone.utc).isoformat()}",
        "",
    ]
    for market, s in summaries.items():
        lines += [
            f"## {market}",
            "",
            f"- Ticker count: **{s['n_symbols']}**",
            f"- Labeled rows: **{s['n_rows']}**",
            f"- Feature columns: **{s['n_features']}**",
            f"- Feature dtype: `float32` | Target dtype: `int8`",
            f"- Mean NaN fraction across features: **{s['nan_frac']:.2%}**",
            "",
            "### Target class balance",
            "",
            "| Target | Positive | Negative | Positive rate |",
            "| :--- | ---: | ---: | ---: |",
        ]
        for t in TARGET_COLUMNS:
            pos = s["balance"][t]["pos"]
            neg = s["balance"][t]["neg"]
            tot = pos + neg
            rate = pos / tot if tot else 0.0
            lines.append(f"| `{t}` | {pos} | {neg} | {rate:.2%} |")
        lines.append("")
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines) + "\n")


def main() -> int:
    init_dirs()
    parser = argparse.ArgumentParser()
    parser.add_argument("--market", choices=["USD", "CAD", "ALL"], default="ALL")
    parser.add_argument("--validate-leakage", action="store_true")
    args = parser.parse_args()

    if args.validate_leakage:
        print("[feature_engine] running anti-leakage tests...")
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/test_leakage.py", "-q"],
            cwd=BASE_DIR, capture_output=True, text=True,
        )
        print(proc.stdout)
        if proc.returncode != 0:
            print(proc.stderr, file=sys.stderr)
            return 1

    markets = ["USD", "CAD"] if args.market == "ALL" else [args.market]
    FEATURES_DIR.mkdir(parents=True, exist_ok=True)

    summaries = {}
    for mkt in markets:
        merged, target_cols = build_market_dataset(mkt)
        if merged is None or merged.empty:
            print(f"[feature_engine] {mkt}: no data available, skipping.")
            continue
        feat_cols = [c for c in merged.columns if c not in target_cols + ["date", "symbol", "market"]]

        merged[["date", "symbol", "market"] + feat_cols].to_parquet(
            FEATURES_DIR / f"features_{mkt}.parquet", index=False
        )
        merged[["date", "symbol", "market"] + target_cols].to_parquet(
            FEATURES_DIR / f"targets_{mkt}.parquet", index=False
        )

        balance = {}
        for t in target_cols:
            balance[t] = {"pos": int((merged[t] == 1).sum()), "neg": int((merged[t] == 0).sum())}
        nan_frac = float(merged[feat_cols].isna().mean().mean())

        summaries[mkt] = {
            "n_symbols": int(merged["symbol"].nunique()),
            "n_rows": int(len(merged)),
            "n_features": len(feat_cols),
            "balance": balance,
            "nan_frac": nan_frac,
        }
        print(
            f"[feature_engine] {mkt}: {summaries[mkt]['n_rows']} labeled rows, "
            f"{summaries[mkt]['n_features']} features, {summaries[mkt]['n_symbols']} symbols"
        )

    if summaries:
        write_summary(summaries)
        update_state("EP-02", "gate_2", {
            "markets": {k: {"n_features": v["n_features"], "n_rows": v["n_rows"]} for k, v in summaries.items()},
        })
        print(f"[feature_engine] summary -> {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
