"""Sprint 1 — Async-paced IBKR OHLCV ingestion engine with adaptive pacing.

Downloads ADJUSTED_LAST daily bars into partitioned Parquet files under
`data/raw_ohlcv/market={USD|CAD}/symbol={SYM}.parquet`. Incremental delta
fetches are computed from the last stored bar date.

Key features (v2):
  - Sliding-window RateLimiter
  - Adaptive concurrency — auto-throttle on IBKR pacing errors (420/162)
  - PacingProfile — learns and persists rate limits between runs
  - Surge-and-settle: burst discovery → cruise at 80% of ceiling
  - Exchange translation map (TSE→SMART/TSE, NYSE, NASDAQ, ARCA)
  - Trading calendar awareness (NYSE/TSX via pandas_market_calendars)
  - Download plan: Bulk / Mid / Delta / Skip classification
  - Gap detection against trading calendar + --fixgap
  - Batch contract qualification
  - Permission-error flagging (162 "No market data permissions")
  - Incremental progress saves every N tickers
  - Hardcoded benchmark tickers (SPY/QQQ for USD, XIU/XIC/XDIV for CAD)
  - Sort by duration: shortest Delta first → Mid → Bulk
  - Variable timeouts by query type
  - Connection warm-up probe
  - Per-market parallelism via --client-id

NOTE: this module is executed on the M1 MacBook Air (local IB Gateway on
`127.0.0.1:4001/4002`), NOT on the Linux VPS. It is synced here for completeness.
"""

import argparse
import asyncio
import datetime as dt
import json
import logging
import os
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo

import pandas as pd
import yaml

# ib_async is only available on the M1 Mac where IB Gateway runs.
# Dry-run and config validation work without it.
try:
    from ib_async import IB, Stock, util
    HAS_IB_ASYNC = True
except ImportError:
    HAS_IB_ASYNC = False

# Optional: trading calendar for gap detection
try:
    import pandas_market_calendars as mcal
    HAS_MCAL = True
except ImportError:
    HAS_MCAL = False

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("IBKRIngest")
logging.getLogger("ib_async").setLevel(logging.WARNING)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
EXCHANGE_MAP = {
    "TSE":     {"exchange": "SMART", "primaryExchange": "TSE",     "currency": "CAD"},
    "TSX":     {"exchange": "SMART", "primaryExchange": "TSE",     "currency": "CAD"},
    "TSXV":    {"exchange": "SMART", "primaryExchange": "VENTURE", "currency": "CAD"},
    "NEO":     {"exchange": "SMART", "primaryExchange": "AEQS",    "currency": "CAD"},
    "NASDAQ":  {"exchange": "SMART", "primaryExchange": "NASDAQ",  "currency": "USD"},
    "NYSE":    {"exchange": "SMART", "primaryExchange": "NYSE",    "currency": "USD"},
    "ARCA":    {"exchange": "SMART", "primaryExchange": "ARCA",    "currency": "USD"},
    "AMEX":    {"exchange": "SMART", "primaryExchange": "AMEX",    "currency": "USD"},
}

BENCHMARK_TICKERS = {
    "USD": [("SPY", "ARCA"), ("QQQ", "NASDAQ")],
    "CAD": [("XIU", "TSE"), ("XIC", "TSE"), ("XDIV", "TSE")],
}

PROFILE_DIR = Path("data")

# Structured pacing event log (JSON lines) — one entry per hit/throttle/restore.
PACING_LOG_NAME = "pacing_events.jsonl"

# Retry constants for transient IBKR failures (cancelled queries, empty responses)
MAX_RETRIES = 2
RETRY_DELAY_SEC = 30.0


# ===================================================================
# Rate Limiter (sliding window)
# ===================================================================
class RateLimiter:
    """Sliding-window rate limiter — enforces max_calls per period_seconds."""

    def __init__(self, max_calls: int, period_seconds: float):
        self.max_calls = max_calls
        self.period = period_seconds
        self.calls: list[float] = []
        self._lock = asyncio.Lock()

    async def acquire(self):
        async with self._lock:
            now = time.monotonic()
            self.calls = [t for t in self.calls if now - t < self.period]
            if len(self.calls) >= self.max_calls:
                sleep_time = self.period - (now - self.calls[0])
                if sleep_time > 0:
                    logger.debug(f"RateLimiter throttle {sleep_time:.2f}s")
                    await asyncio.sleep(sleep_time)
            self.calls.append(time.monotonic())

    @property
    def current_count(self) -> int:
        now = time.monotonic()
        return len([t for t in self.calls if now - t < self.period])


# ===================================================================
# Pacing Profile (learned rate tracking)
# ===================================================================
@dataclass
class PacingProfile:
    market: str = ""
    discovered_throughput: float = 0.0       # successful req/min sustained
    safe_concurrency: int = 3                 # semaphore size that works
    safe_rate_per_minute: float = 45.0        # rate limiter ceiling
    last_updated: str = ""                    # ISO date
    total_runs: int = 0
    total_pacing_hits: int = 0
    total_requests: int = 0
    avg_latency_ms: float = 0.0
    # Ramp-up calibration fields
    ramp_ceiling: int = 0                     # discovered concurrency ceiling
    ramp_error_type: str = ""                 # what triggered the ceiling (420/162/msg-rate)

    @classmethod
    def load(cls, path: Path) -> Optional["PacingProfile"]:
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text())
            return cls(**data)
        except Exception:
            return None

    def save(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.last_updated = dt.date.today().isoformat()
        path.write_text(json.dumps(asdict(self), indent=2))

    def is_stale(self, max_age_days: int = 7) -> bool:
        if not self.last_updated:
            return True
        try:
            last = dt.date.fromisoformat(self.last_updated)
            return (dt.date.today() - last).days > max_age_days
        except Exception:
            return True

    def update_from_run(self, throughput: float, concurrency: int, pacing_hits: int,
                        requests: int, avg_latency_ms: float):
        """Exponential-moving-average update after a completed run."""
        alpha = 0.3  # weight for new observation
        if self.total_runs == 0:
            self.discovered_throughput = throughput
            self.safe_concurrency = concurrency
            self.safe_rate_per_minute = throughput * 0.80
        else:
            self.discovered_throughput = (1 - alpha) * self.discovered_throughput + alpha * throughput
            self.safe_concurrency = max(1, int((1 - alpha) * self.safe_concurrency + alpha * concurrency))
            self.safe_rate_per_minute = self.discovered_throughput * 0.80
        self.total_runs += 1
        self.total_pacing_hits += pacing_hits
        self.total_requests += requests
        if self.total_runs == 1:
            self.avg_latency_ms = avg_latency_ms
        else:
            self.avg_latency_ms = (1 - alpha) * self.avg_latency_ms + alpha * avg_latency_ms


# ===================================================================
# OHLCV Index — metadata index replacing per-file Parquet scans
# ===================================================================
@dataclass
class IndexEntry:
    symbol: str
    market: str
    min_date: str = ""
    max_date: str = ""
    rows: int = 0
    last_downloaded: str = ""
    primary_exchange: str = "SMART"
    currency: str = "USD"


class IndexManager:
    """Fast metadata index over the raw_ohlcv Parquet directory.

    Avoids scanning every .parquet file on each run.  The index is a single
    Parquet file with one row per ticker.  On startup it is loaded if fresh
    (< max_age_minutes old), otherwise rebuilt from disk in one pass.
    """

    COLUMNS = ["market", "symbol", "min_date", "max_date", "rows",
               "last_downloaded", "primary_exchange", "currency"]

    def __init__(self, path: Path, max_age_minutes: int = 60):
        self.path = path
        self.max_age_minutes = max_age_minutes
        self.df: Optional[pd.DataFrame] = None
        self._dirty: set[str] = set()  # symbols modified in-memory

    # ------------------------------------------------------------------
    def load_or_rebuild(self, raw_dir: Path, market: str) -> pd.DataFrame:
        """Return the index DataFrame, rebuilding from Parquet files if stale."""
        if self._is_fresh():
            logger.info("Index loaded from %s  (%d entries, %.0f min old)",
                         self.path, len(self.df),
                         (dt.datetime.now() - self._mtime()).total_seconds() / 60)
            return self.df[self.df["market"] == market].copy()

        logger.info("Index missing or stale — rebuilding from %s ...", raw_dir)
        self._rebuild(raw_dir)
        self.df.to_parquet(self.path, index=False, engine="pyarrow")
        logger.info("Index rebuilt: %d entries → %s", len(self.df), self.path)
        return self.df[self.df["market"] == market].copy()

    # ------------------------------------------------------------------
    def update(self, symbol: str, market: str, min_date, max_date, rows: int,
               primary_exchange: str = "SMART", currency: str = "USD"):
        """Upsert a single ticker entry after a successful download."""
        if self.df is None:
            self.df = pd.DataFrame(columns=self.COLUMNS)

        min_s = str(min_date) if min_date else ""
        max_s = str(max_date) if max_date else ""
        now = dt.datetime.now().isoformat(timespec="seconds")
        mask = (self.df["symbol"] == symbol) & (self.df["market"] == market)

        if mask.any():
            idx = self.df[mask].index[0]
            self.df.at[idx, "min_date"] = min_s
            self.df.at[idx, "max_date"] = max_s
            self.df.at[idx, "rows"] = rows
            self.df.at[idx, "last_downloaded"] = now
            self.df.at[idx, "primary_exchange"] = primary_exchange
            self.df.at[idx, "currency"] = currency
        else:
            new_row = pd.DataFrame([{
                "market": market, "symbol": symbol,
                "min_date": min_s, "max_date": max_s, "rows": rows,
                "last_downloaded": now,
                "primary_exchange": primary_exchange, "currency": currency,
            }])
            self.df = pd.concat([self.df, new_row], ignore_index=True)
        self._dirty.add(symbol)

    # ------------------------------------------------------------------
    def flush(self):
        """Persist index to disk."""
        if self.df is not None and self._dirty:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.df.to_parquet(self.path, index=False, engine="pyarrow")
            logger.debug("Index flushed: %d entries → %s", len(self.df), self.path)
            self._dirty.clear()

    # ------------------------------------------------------------------
    def check_integrity(self, raw_dir: Path, market: str) -> list[str]:
        """Cross-check index against disk.  Returns list of tickers needing repair.

        Detects: index entry with no Parquet file (missing), Parquet file with
        no index entry (orphan), row-count mismatch (truncated/corrupt).
        """
        if self.df is None:
            return []
        issues: list[str] = []
        market_df = self.df[self.df["market"] == market]
        for _, row in market_df.iterrows():
            sym = row["symbol"]
            pq_path = raw_dir / f"symbol={sym}.parquet"
            if not pq_path.exists():
                issues.append(f"{sym}: index entry but file missing")
                continue
            try:
                actual = pd.read_parquet(pq_path, columns=["date"])
                if len(actual) != row["rows"] and row["rows"] > 0:
                    issues.append(f"{sym}: rows mismatch index={row['rows']} disk={len(actual)}")
            except Exception as e:
                issues.append(f"{sym}: read error ({e})")

        # Check for orphans (files with no index entry)
        indexed = set(market_df["symbol"])
        for pq_path in raw_dir.glob("symbol=*.parquet"):
            sym = pq_path.stem.split("=", 1)[-1]
            if sym not in indexed:
                issues.append(f"{sym}: orphan file (no index entry)")
        return issues

    # ------------------------------------------------------------------
    def _is_fresh(self) -> bool:
        if not self.path.exists():
            return False
        try:
            self.df = pd.read_parquet(self.path)
        except Exception:
            logger.warning("Corrupt index — will rebuild")
            self.df = None
            return False
        if self.df.empty:
            return False
        age = (dt.datetime.now() - self._mtime()).total_seconds() / 60
        return age < self.max_age_minutes

    def _mtime(self) -> dt.datetime:
        return dt.datetime.fromtimestamp(self.path.stat().st_mtime)

    def _rebuild(self, raw_dir: Path):
        """Scan all Parquet files and rebuild the index from scratch."""
        rows = []
        for pq_path in sorted(raw_dir.glob("symbol=*.parquet")):
            sym = pq_path.stem.split("=", 1)[-1]
            try:
                df = pd.read_parquet(pq_path, columns=["date"])
                if df.empty:
                    continue
                df["date"] = pd.to_datetime(df["date"]).dt.normalize()
                rows.append({
                    "market": raw_dir.name.split("=", 1)[-1],
                    "symbol": sym,
                    "min_date": str(df["date"].min().date()),
                    "max_date": str(df["date"].max().date()),
                    "rows": len(df),
                    "last_downloaded": "",
                    "primary_exchange": "SMART",
                    "currency": "CAD" if "cad" in raw_dir.name.lower() else "USD",
                })
            except Exception:
                logger.debug("Skipping unreadable: %s", pq_path)
        self.df = pd.DataFrame(rows, columns=self.COLUMNS)


# ===================================================================
# Downloader
# ===================================================================
class IngestDownloader:
    """Async OHLCV downloader with adaptive pacing, calendar awareness, and gap detection."""

    def __init__(self, market: str, cfg: dict, dry_run: bool = False,
                 limit: int = 0, fix_gap: bool = False, delta_only: bool = False,
                 client_id: Optional[int] = None, scan_sources: bool = True):
        self.watchlist_market = market.upper()   # original: USD / CAD / HOLDINGS
        self.market = market.upper()
        # Holdings has mixed currencies; use CAD calendar settings but keep
        # the HOLDINGS label for watchlist + data-dir resolution.
        if self.market == "HOLDINGS":
            self.market = "CAD"
        self.cfg = cfg
        self.dry_run = dry_run
        self.limit = limit
        self.fix_gap = fix_gap
        self.delta_only = delta_only
        self.client_id = client_id if client_id is not None else cfg["ibkr"]["client_id"]
        self.scan_sources = scan_sources

        ib_cfg = cfg["ibkr"]
        self.ib_host = ib_cfg["host"]
        self.ib_port = ib_cfg["port"]
        self.request_delay = ib_cfg.get("request_delay_sec", 1.5)
        self.lookback_cold = ib_cfg.get("lookback_cold", "5 Y")
        self.bar_size = ib_cfg.get("bar_size", "1 day")
        self.what_to_show = ib_cfg.get("what_to_show", "ADJUSTED_LAST")
        self.use_rth = ib_cfg.get("use_rth", True)
        self.timeout_sec = ib_cfg.get("timeout_sec", 30)

        # Pacing config (new keys in settings.yaml)
        self.requests_per_window = ib_cfg.get("requests_per_window", 45)
        self.window_seconds = ib_cfg.get("window_seconds", 60)
        self.download_concurrency = ib_cfg.get("download_concurrency", 3)
        self.min_concurrency = ib_cfg.get("min_concurrency", 1)
        self.pacing_backoff_sleep = ib_cfg.get("pacing_backoff_sleep", 15.0)
        self.pacing_hit_threshold = ib_cfg.get("pacing_hit_threshold", 3)
        self.hmds_cancel_threshold = ib_cfg.get("hmds_cancel_threshold", 3)
        self.global_pause_sleep = ib_cfg.get("global_pause_sleep", 120.0)
        self.qualify_batch_size = ib_cfg.get("qualify_batch_size", 25)
        self.qualify_batch_delay = ib_cfg.get("qualify_batch_delay_sec", 2.0)
        self.hmds_warmup_probe = ib_cfg.get("hmds_warmup_probe_sec", 10.0)
        self.hmds_warmup_poll = ib_cfg.get("hmds_warmup_poll_sec", 1.0)
        self.save_every = ib_cfg.get("save_every", 25)

        self.base_dir = Path(cfg["project"]["base_dir"])
        self.raw_dir = self.base_dir / "data" / "raw_ohlcv" / f"market={self.watchlist_market}"

        # OHLCV metadata index (fast path over per-file scans)
        self.index_max_age = ib_cfg.get("index_max_age_minutes", 60)
        self.index = IndexManager(
            self.base_dir / "data" / "ohlcv_index.parquet",
            max_age_minutes=self.index_max_age,
        )
        self.batch_bars_threshold = ib_cfg.get("batch_bars_threshold", 5000)
        self.batch_cooldown_sec = ib_cfg.get("batch_cooldown_sec", 120.0)

        # Structured pacing event log
        self.pacing_log_path = self.base_dir / "data" / PACING_LOG_NAME

        # IB connection (None if ib_async not installed; dry-run works without it)
        self.ib = IB() if HAS_IB_ASYNC else None

        # Rate limiting & concurrency
        self.limiter = RateLimiter(self.requests_per_window, self.window_seconds)
        self.concurrency = self.download_concurrency
        self.sem = asyncio.Semaphore(self.concurrency)

        # Pacing state
        self._consecutive_pacing = 0
        self._pace_lock = asyncio.Lock()
        self._pacing_hits_total = 0

        # HMDS cancellation tracking (counts consecutive cancels for pacing)
        self._consecutive_hmds_cancels = 0
        self._hmds_cancel_total = 0

        # ── Ramp-up calibration state ──
        self.ramp_probe_batch = ib_cfg.get("ramp_probe_batch", 5)
        self.ramp_confirm_mult = ib_cfg.get("ramp_confirm_multiplier", 2)
        self.ramp_profile_max_age = ib_cfg.get("ramp_profile_max_age_days", 3)
        self._ramp_level = 15                 # current concurrency under test
        self._ramp_successes = 0             # successes at current level
        self._ramp_ceiling: Optional[int] = None  # discovered safe max
        self._ramp_confirm_successes = 0     # successes during confirm
        self._ramp_confirm_needed = 0        # target successes for confirm
        self._ramp_retries_at_level = 0      # retries (IGNORE errors) at current level

        # Progress counters
        self.total = self.completed = self.loaded = self.failed = self.skipped = 0
        self.start_time: Optional[float] = None

        # Latency tracking
        self._latencies: list[float] = []

        # Error/status per ticker
        self.ticker_status: dict[str, dict] = {}

        # Pacing profile
        profile_path = PROFILE_DIR / f"pacing_profile_{self.market.lower()}.json"
        self.profile = PacingProfile.load(profile_path)
        self.profile_path = profile_path
        self._ramp_phase = "init"  # init | ramp | confirm | cruise | abort

        # Trading calendars
        self.trading_days_nyse = None
        self.trading_days_tsx = None
        self.latest_complete_day_nyse = None
        self.latest_complete_day_tsx = None
        self._init_calendars()

        # Register error handler
        if self.ib is not None:
            self.ib.errorEvent += self._on_ib_error

    # ------------------------------------------------------------------
    # Calendars
    # ------------------------------------------------------------------
    def _init_calendars(self):
        if not HAS_MCAL:
            logger.warning("pandas_market_calendars not installed; gap detection disabled")
            return
        try:
            cal_end = pd.Timestamp.now()
            # NYSE
            self.nyse = mcal.get_calendar("NYSE")
            nyse_schedule = self.nyse.schedule(
                start_date=cal_end - pd.Timedelta(days=365 * 21), end_date=cal_end
            )
            self.trading_days_nyse = mcal.date_range(nyse_schedule, frequency="1D").tz_convert(None).normalize()

            # TSX
            self.tsx = mcal.get_calendar("TSX")
            tsx_schedule = self.tsx.schedule(
                start_date=cal_end - pd.Timedelta(days=365 * 21), end_date=cal_end
            )
            self.trading_days_tsx = mcal.date_range(tsx_schedule, frequency="1D").tz_convert(None).normalize()

            now_et = dt.datetime.now(ZoneInfo("America/New_York"))
            today = pd.Timestamp.now().normalize()

            def _latest_complete_day(trading_days):
                past = trading_days[trading_days <= today]
                if len(past) == 0:
                    return None
                if past[-1] == today and (now_et.hour < 17 or (now_et.hour == 17 and now_et.minute < 30)):
                    return past[-2] if len(past) >= 2 else None
                return past[-1]

            self.latest_complete_day_nyse = _latest_complete_day(self.trading_days_nyse)
            self.latest_complete_day_tsx = _latest_complete_day(self.trading_days_tsx)
            logger.info(
                "Latest complete trading day: TSX=%s, NYSE=%s",
                self.latest_complete_day_tsx, self.latest_complete_day_nyse,
            )
        except Exception as e:
            logger.warning(f"Calendar init failed: {e}")

    def _trading_days_for(self, primary_exchange: str):
        """Return the appropriate trading-day index for a primary exchange."""
        if primary_exchange in ("NYSE", "NASDAQ", "ARCA", "AMEX"):
            return self.trading_days_nyse
        return self.trading_days_tsx

    def _latest_complete_day_for(self, primary_exchange: str):
        if primary_exchange in ("NYSE", "NASDAQ", "ARCA", "AMEX"):
            return self.latest_complete_day_nyse
        return self.latest_complete_day_tsx

    # ------------------------------------------------------------------
    # IB Error Handling
    # ------------------------------------------------------------------
    def _on_ib_error(self, reqId, errorCode, errorString, contract):
        symbol = contract.symbol if contract else f"reqId:{reqId}"

        # ── Gateway message-rate warning (code 0) ──────────────────────────
        # "Approaching max rate of 50 messages per second (44)"
        # This is the root cause of cascading HMDS cancellations.
        # Treat it as a hard pacing signal — throttle immediately.
        if errorCode == 0 and "max rate" in errorString.lower():
            logger.warning("[gateway] 🔴 MSG-RATE: %s", errorString)
            self._log_pacing_event(
                "msg_rate_warning", symbol="", error_code=errorCode,
                error_msg=errorString,
                concurrency_before=self.concurrency, concurrency_after=self.concurrency,
            )
            # In ramp/confirm: msg-rate warning is a hard ceiling signal
            if self._ramp_phase in ("ramp", "confirm") and not self._ramp_ceiling:
                self._ramp_set_ceiling("msg_rate")
            elif self._ramp_phase == "confirm" and self._ramp_ceiling:
                self._ramp_ceiling = max(1, self._ramp_ceiling - 1)
                self._ramp_confirm_successes = 0
                self.concurrency = self._ramp_ceiling
                self.sem = asyncio.Semaphore(self.concurrency)
                logger.warning("⚠️ Confirm ceiling failed (msg-rate) → %d", self._ramp_ceiling)
            else:
                asyncio.create_task(self._on_pacing_hit())
            return

        # ── Pacing errors (420 or 162 with pacing/limited keyword) ─────────
        is_pacing = (errorCode == 420) or (
            errorCode == 162 and ("pacing" in errorString.lower() or "limited" in errorString.lower())
        )
        if is_pacing:
            logger.warning("[%s] 🔴 Pacing error %s: %s", symbol, errorCode, errorString)
            self._log_pacing_event(
                "pacing_error", symbol=symbol, error_code=errorCode,
                error_msg=errorString,
                concurrency_before=self.concurrency, concurrency_after=self.concurrency,
            )
            asyncio.create_task(self._on_pacing_hit())
            return

        # ── HMDS cancellations (162 "Historical Market Data Service") ──────
        # These are NOT transient network failures — they mean the HMDS farm
        # is saturated.  Count consecutive cancels and treat them as a pacing
        # signal to throttle concurrency.
        if errorCode == 162 and "historical market data" in errorString.lower():
            self._consecutive_hmds_cancels += 1
            self._hmds_cancel_total += 1
            logger.error("[%s] HMDS cancelled (consecutive=%d/%d total=%d): %s",
                         symbol, self._consecutive_hmds_cancels,
                         self.hmds_cancel_threshold, self._hmds_cancel_total, errorString)
            self._log_pacing_event(
                "hmds_cancel", symbol=symbol, error_code=errorCode,
                error_msg=errorString,
                concurrency_before=self.concurrency, concurrency_after=self.concurrency,
            )
            if self._consecutive_hmds_cancels >= self.hmds_cancel_threshold:
                logger.warning("🔴 HMDS cancel threshold reached (%d consecutive) — triggering pacing backoff",
                               self._consecutive_hmds_cancels)
                # In ramp/confirm: treat as hard error → set ceiling
                if self._ramp_phase in ("ramp", "confirm") and not self._ramp_ceiling:
                    self._ramp_set_ceiling("hmds_cancel")
                elif self._ramp_phase == "confirm" and self._ramp_ceiling:
                    self._ramp_ceiling = max(1, self._ramp_ceiling - 1)
                    self._ramp_confirm_successes = 0
                    self.concurrency = self._ramp_ceiling
                    self.sem = asyncio.Semaphore(self.concurrency)
                    logger.warning("⚠️ Confirm ceiling failed (HMDS) → %d", self._ramp_ceiling)
                else:
                    asyncio.create_task(self._on_pacing_hit())
            self.ticker_status[symbol] = {
                "error": f"IBKR cancelled: {errorString}",
                "transient_fail": True,
            }
            return

        # Permission errors
        if errorCode == 162 and "no market data permissions" in errorString.lower():
            logger.error("[%s] ❌ Permission error: %s", symbol, errorString)
            self.ticker_status[symbol] = {
                "error": "No market data permissions",
                "permanent_fail": True,
            }

    def _log_pacing_event(self, event: str, symbol: str = "", error_code: int = 0,
                          error_msg: str = "", concurrency_before: int = 0,
                          concurrency_after: int = 0):
        """Append one structured JSON line to the pacing event log."""
        try:
            entry = {
                "ts": dt.datetime.now().isoformat(timespec="seconds"),
                "market": self.market,
                "event": event,
                "symbol": symbol,
                "error_code": error_code,
                "error_msg": error_msg,
                "phase": self._ramp_phase,
                "concurrency_before": concurrency_before,
                "concurrency_after": concurrency_after,
                "consecutive_hits": self._consecutive_pacing,
                "pacing_hits_total": self._pacing_hits_total,
            }
            self.pacing_log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.pacing_log_path, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            pass  # logging must never crash the download

    async def _on_pacing_hit(self):
        async with self._pace_lock:
            self._consecutive_pacing += 1
            self._pacing_hits_total += 1
            prev_c = self.concurrency

            # ── Ramp/confirm phase: hard error → set ceiling immediately ──
            if self._ramp_phase in ("ramp", "confirm") and not self._ramp_ceiling:
                # In ramp: this IS the ceiling discovery
                self._ramp_set_ceiling("pacing_hit")
                return
            if self._ramp_phase == "confirm" and self._ramp_ceiling:
                # Ceiling was wrong — drop it
                self._ramp_ceiling = max(1, self._ramp_ceiling - 1)
                self._ramp_confirm_successes = 0
                self.concurrency = self._ramp_ceiling
                self.sem = asyncio.Semaphore(self.concurrency)
                logger.warning("⚠️ Confirm ceiling failed → %d", self._ramp_ceiling)
                if self._ramp_ceiling == 0:
                    logger.error("❌ ABORT: even concurrency=1 fails")
                    self._ramp_phase = "abort"
                return

            # ── Cruise phase: standard reactive backoff ──
            if self._consecutive_pacing >= self.pacing_hit_threshold:
                logger.warning("🔴 GLOBAL_PAUSE %.0fs  reason=consecutive_hits>=%d  concurrency→%d",
                               self.global_pause_sleep, self.pacing_hit_threshold, self.min_concurrency)
                await asyncio.sleep(self.global_pause_sleep)
                self._consecutive_pacing = 0
                self._consecutive_hmds_cancels = 0
                self.concurrency = self.min_concurrency
                self.sem = asyncio.Semaphore(self.concurrency)
                self._log_pacing_event(
                    "global_pause", symbol="", concurrency_before=prev_c,
                    concurrency_after=self.concurrency,
                )
            else:
                new_c = max(self.concurrency - max(self.concurrency // 2, 1), self.min_concurrency)
                if new_c < self.concurrency:
                    logger.warning("⚠️ Throttling: %d→%d  reason=pacing_hit  consecutive=%d/%d",
                                   self.concurrency, new_c, self._consecutive_pacing, self.pacing_hit_threshold)
                    self.concurrency = new_c
                    self.sem = asyncio.Semaphore(self.concurrency)
                    self._log_pacing_event(
                        "throttle", symbol="", concurrency_before=prev_c,
                        concurrency_after=self.concurrency,
                    )
                await asyncio.sleep(self.pacing_backoff_sleep)

    def _reset_pacing(self):
        self._consecutive_pacing = 0
        self._consecutive_hmds_cancels = 0  # reset HMDS counter on success
        # If we were in discovery phase and got successful downloads,
        # gradually restore concurrency toward starting level
        if self.concurrency < self.download_concurrency and self._consecutive_pacing == 0:
            new_c = min(self.concurrency + 1, self.download_concurrency)
            if new_c != self.concurrency:
                prev_c = self.concurrency
                self.concurrency = new_c
                self.sem = asyncio.Semaphore(self.concurrency)
                logger.info("✅ Restoring: %d→%d  reason=success_streak", prev_c, new_c)
                self._log_pacing_event(
                    "restore", symbol="", concurrency_before=prev_c,
                    concurrency_after=self.concurrency,
                )

    # ------------------------------------------------------------------
    # Ramp-up calibration — methodical concurrency discovery
    # ------------------------------------------------------------------
    def _ramp_is_hard_error(self, error_code: int, error_msg: str) -> bool:
        """Classify an error as 'hard' (defines ceiling) vs 'soft' (ignore for ramp)."""
        # Message-rate warning: gateway pipe limit
        if error_code == 0 and "max rate" in error_msg.lower():
            return True
        # Pacing violation: explicit IBKR backoff
        if error_code == 420:
            return True
        # HMDS cancel with pacing keyword: same as 420
        if error_code == 162 and ("pacing" in error_msg.lower() or "limited" in error_msg.lower()):
            return True
        # Permissions, empty responses, network errors: ticker-specific, ignore
        return False

    def _ramp_set_ceiling(self, trigger: str):
        """A hard error occurred — set the ramp ceiling to the previous safe level."""
        ceiling = max(1, self._ramp_level - 1)
        self._ramp_ceiling = ceiling
        self._ramp_phase = "confirm"
        self._ramp_confirm_successes = 0
        self._ramp_confirm_needed = self.ramp_probe_batch * self.ramp_confirm_mult
        self.concurrency = ceiling
        self.sem = asyncio.Semaphore(self.concurrency)
        logger.warning("🔴 Ramp ceiling: %d  trigger=%s  (error at level %d)  → confirm with %d tickers",
                       ceiling, trigger, self._ramp_level, self._ramp_confirm_needed)

    def _ramp_bump(self):
        """All probe_batch tickers succeeded at current level — try higher."""
        self._ramp_level += 1
        self._ramp_successes = 0
        self._ramp_retries_at_level = 0
        self.concurrency = self._ramp_level
        self.sem = asyncio.Semaphore(self.concurrency)
        logger.info("⬆ Ramp: concurrency → %d", self._ramp_level)

    def _ramp_handle_success(self):
        """Called on each SUCCESS during ramp/confirm phases."""
        if self._ramp_phase == "ramp":
            self._ramp_successes += 1
            self._ramp_retries_at_level = 0
            if self._ramp_successes >= self.ramp_probe_batch:
                self._ramp_bump()
        elif self._ramp_phase == "confirm":
            self._ramp_confirm_successes += 1
            if self._ramp_confirm_successes >= self._ramp_confirm_needed:
                self._ramp_phase = "cruise"
                logger.info("✅ Ceiling confirmed: concurrency=%d  (profile saved)", self._ramp_ceiling)
                # Persist to profile
                if self.profile is None:
                    self.profile = PacingProfile(market=self.market)
                self.profile.safe_concurrency = self._ramp_ceiling
                self.profile.ramp_ceiling = self._ramp_ceiling
                self.profile.last_updated = dt.date.today().isoformat()
                self.profile.save(self.profile_path)

    def _ramp_handle_retry(self):
        """Called when a ticker fails with an IGNORE error (permission, empty, network).
        Counts toward a retry limit per level to prevent infinite loops."""
        if self._ramp_phase in ("ramp", "confirm"):
            self._ramp_retries_at_level += 1
            max_retries = self.ramp_probe_batch * 3
            if self._ramp_retries_at_level >= max_retries:
                logger.warning("⚠️ Ramp: %d retries at level %d — forced ceiling",
                               self._ramp_retries_at_level, self._ramp_level)
                if self._ramp_phase == "ramp":
                    self._ramp_set_ceiling("retry_limit")
                else:
                    # In confirm, drop ceiling by 1
                    self._ramp_ceiling = max(1, (self._ramp_ceiling or 1) - 1)
                    if self._ramp_ceiling == 0:
                        logger.error("❌ ABORT: even concurrency=1 fails")
                        self._ramp_phase = "abort"
                    else:
                        self._ramp_confirm_successes = 0
                        self.concurrency = self._ramp_ceiling
                        self.sem = asyncio.Semaphore(self.concurrency)
                        self._ramp_retries_at_level = 0
                        logger.warning("⚠️ Confirm failed — retrying at %d", self._ramp_ceiling)

    # ------------------------------------------------------------------
    # Watchlist loading
    # ------------------------------------------------------------------
    def _load_watchlist(self) -> pd.DataFrame:
        path_map = {
            "USD": self.cfg["watchlists"]["usd_path"],
            "CAD": self.cfg["watchlists"]["cad_path"],
            "HOLDINGS": self.cfg["watchlists"]["holdings_path"],
        }
        csv_path = self.base_dir / path_map[self.watchlist_market]
        if not csv_path.exists():
            logger.error("Watchlist not found: %s", csv_path)
            return pd.DataFrame()

        df = pd.read_csv(csv_path)
        required = ["symbol"]
        missing = [c for c in required if c not in df.columns]
        if missing:
            logger.error("Watchlist missing columns: %s", missing)
            return pd.DataFrame()

        df["symbol"] = df["symbol"].astype(str).str.strip()
        df = df[df["symbol"].notna() & (df["symbol"] != "")]

        # Add benchmark tickers if not already present
        for bench_sym, bench_exch in BENCHMARK_TICKERS.get(self.market, []):
            if bench_sym not in df["symbol"].values:
                new_row = {
                    "symbol": bench_sym,
                    "sec_type": "STK",
                    "exchange": "SMART",
                    "primary_exchange": bench_exch,
                    "currency": "CAD" if self.market == "CAD" else "USD",
                }
                for col in df.columns:
                    if col not in new_row:
                        new_row[col] = ""
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

        logger.info("Loaded %d tickers from %s (+ benchmarks)", len(df), csv_path)
        return df

    # ------------------------------------------------------------------
    # Source-file scanner (IV_*/TC_*/IBKRtemp.csv)
    # ------------------------------------------------------------------
    def _scan_source_files(self, df_watch: pd.DataFrame) -> list[dict]:
        """Scan IV_*/TC_*/IBKRtemp.csv for tickers not in the watchlist.

        Returns list of plan dicts (Bulk type) for newly discovered tickers.
        Only scans files relevant to the current market.
        """
        script_dir = Path(__file__).resolve().parent
        watch_symbols = set(df_watch["symbol"].astype(str).str.strip())
        mkt_pfx = "US" if self.market == "USD" else "CD"

        discovered: dict[str, dict] = {}  # symbol → {primary_exchange, currency}

        # --- Parse IV files (market-filtered) ---
        iv_pattern = f"IV_{mkt_pfx}_*.csv"
        for fp in sorted(script_dir.glob(iv_pattern)):
            try:
                df_iv = pd.read_csv(fp)
                sym_col = "Symbol" if "Symbol" in df_iv.columns else None
                if sym_col is None:
                    continue
                exch_col = "Exch" if "Exch" in df_iv.columns else None
                for _, row in df_iv.iterrows():
                    sym = str(row[sym_col]).strip().replace(".TO", "")
                    if not sym or sym.lower() in ("nan", "none", "") or sym in watch_symbols:
                        continue
                    exch_raw = str(row[exch_col]).strip().upper() if exch_col and pd.notna(row[exch_col]) else ""
                    pe = self._resolve_primary_exchange(exch_raw, self.market)
                    discovered[sym] = {"primary_exchange": pe, "currency": "CAD" if self.market == "CAD" else "USD"}
            except Exception:
                logger.debug("Skipping unparseable IV file: %s", fp)

        # --- Parse TC files (market-filtered) ---
        tc_pattern = f"TC_{mkt_pfx}_*.csv"
        for fp in sorted(script_dir.glob(tc_pattern)):
            try:
                df_tc = pd.read_csv(fp)
                sym_col = next((c for c in df_tc.columns if c.lower() in ("symbol", "ticker")), None)
                if sym_col is None:
                    continue
                exch_col = next((c for c in df_tc.columns if c.lower() in ("exchange", "exch")), None)
                for _, row in df_tc.iterrows():
                    sym = str(row[sym_col]).strip().replace(".TO", "")
                    if not sym or sym.lower() in ("nan", "none", "") or sym in watch_symbols:
                        continue
                    exch_raw = str(row[exch_col]).strip().upper() if exch_col and pd.notna(row[exch_col]) else ""
                    pe = self._resolve_primary_exchange(exch_raw, self.market)
                    discovered[sym] = {"primary_exchange": pe, "currency": "CAD" if self.market == "CAD" else "USD"}
            except Exception:
                logger.debug("Skipping unparseable TC file: %s", fp)

        # --- Parse IBKRtemp.csv (filter by market exchange) ---
        opt_path = script_dir / "IBKRtemp.csv"
        if opt_path.exists():
            try:
                with open(opt_path, "r") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("CSVEXPORT") or line.startswith("COLUMN"):
                            continue
                        parts = [p.strip() for p in line.split(",")]
                        if len(parts) < 4 or parts[0] != "DES":
                            continue
                        sym = parts[1]
                        exch_field = parts[3]
                        if "/" in exch_field:
                            pe_raw = exch_field.split("/")[-1].strip().upper()
                        else:
                            pe_raw = exch_field.strip().upper()
                        if pe_raw == "VALUE":
                            continue
                        if sym in watch_symbols or sym in discovered:
                            continue
                        # Filter by market: CAD exchanges for CAD, everything else for USD
                        cad_exchanges = {"TSE", "TSX", "TSXV", "VENTURE", "AEQS"}
                        is_cad = pe_raw in cad_exchanges
                        if (self.market == "CAD" and not is_cad) or (self.market == "USD" and is_cad):
                            continue
                        currency = "CAD" if is_cad else "USD"
                        pe = self._resolve_primary_exchange(pe_raw, currency)
                        discovered[sym] = {"primary_exchange": pe, "currency": currency}
            except Exception:
                logger.debug("Skipping unparseable IBKRtemp.csv")

        if discovered:
            logger.info("Source scan: discovered %d new tickers not in watchlist", len(discovered))
            for sym in sorted(discovered)[:10]:
                logger.info("  + %s  (%s / %s)", sym, discovered[sym]["primary_exchange"], discovered[sym]["currency"])
            if len(discovered) > 10:
                logger.info("  ... and %d more", len(discovered) - 10)

        # Build Bulk plan entries for discovered tickers
        entries = []
        for sym, info in discovered.items():
            entries.append({
                "symbol": sym,
                "primary_exchange": info["primary_exchange"],
                "currency": info["currency"],
                "query_type": "Bulk",
                "days_needed": 365 * 20,
                "missing_days": 0,
                "parquet_path": self.raw_dir / f"symbol={sym}.parquet",
                "ex_info": EXCHANGE_MAP.get(info["primary_exchange"], {
                    "exchange": "SMART",
                    "primaryExchange": info["primary_exchange"],
                    "currency": info["currency"],
                }),
                "last_date": "",
                "start_date": "",
            })
        return entries

    @staticmethod
    def _resolve_primary_exchange(exch_raw: str, market: str) -> str:
        """Map raw exchange string to canonical primary_exchange."""
        if not exch_raw:
            return "TSE" if market == "CAD" else "SMART"
        e = exch_raw.upper()
        if e in ("NYSE AMERICAN", "NYSEAMERICAN", "NYSE MKT"):
            e = "AMEX"
        if e == "TSX":
            e = "TSE"
        if e in EXCHANGE_MAP:
            return EXCHANGE_MAP[e]["primaryExchange"]
        return "TSE" if market == "CAD" else "SMART"

    # ------------------------------------------------------------------
    # Download plan
    # ------------------------------------------------------------------
    def _build_download_plan(self, df_watch: pd.DataFrame) -> pd.DataFrame:
        """Classify each ticker: Skip / Delta / Mid / Bulk — using the index for speed."""
        self.raw_dir.mkdir(parents=True, exist_ok=True)

        # Load index (rebuilds if stale)
        idx_df = self.index.load_or_rebuild(self.raw_dir, self.watchlist_market)
        idx_lookup = {}
        if not idx_df.empty:
            for _, row in idx_df.iterrows():
                idx_lookup[row["symbol"]] = row

        plans = []
        for _, row in df_watch.iterrows():
            symbol = str(row["symbol"]).strip()
            primary_exch = str(row.get("primary_exchange", "SMART")).strip().upper()
            currency = str(row.get("currency", "CAD" if self.market == "CAD" else "USD")).strip()

            ex_info = EXCHANGE_MAP.get(primary_exch, {
                "exchange": "SMART",
                "primaryExchange": primary_exch,
                "currency": "CAD" if self.market == "CAD" else "USD",
            })

            parquet_path = self.raw_dir / f"symbol={symbol}.parquet"
            lcd = self._latest_complete_day_for(primary_exch)
            t_days = self._trading_days_for(primary_exch)

            # Fast path: use index
            last_date = None
            start_date = None
            missing_days = 0

            if symbol in idx_lookup:
                entry = idx_lookup[symbol]
                if entry["max_date"]:
                    last_date = pd.Timestamp(entry["max_date"])
                if entry["min_date"]:
                    start_date = pd.Timestamp(entry["min_date"])

                # Gap detection from index
                if t_days is not None and lcd is not None and start_date is not None:
                    mask = (t_days >= start_date) & (t_days <= lcd)
                    expected = t_days[mask]
                    actual_rows = int(entry["rows"])
                    missing_days = max(0, len(expected) - actual_rows) if actual_rows > 0 else len(expected)
            elif parquet_path.exists():
                # Index didn't have this ticker but file exists — fall back to file read
                try:
                    df_existing = pd.read_parquet(parquet_path, columns=["date"])
                    if not df_existing.empty:
                        df_existing["date"] = pd.to_datetime(df_existing["date"]).dt.normalize()
                        last_date = df_existing["date"].max()
                        start_date = df_existing["date"].min()
                        if t_days is not None and lcd is not None:
                            mask = (t_days >= start_date) & (t_days <= lcd)
                            expected = t_days[mask]
                            actual = set(df_existing["date"])
                            missing_days = len([d for d in expected if d not in actual])
                except Exception:
                    pass

            # Classify
            if lcd is None or last_date is None:
                query_type = "Bulk"
                days_needed = 365 * 20
            elif self.fix_gap and missing_days > 0:
                query_type = "Bulk"
                days_needed = 365 * 20
            elif last_date >= lcd:
                query_type = "Skip"
                days_needed = 0
            else:
                gap = (lcd - last_date).days
                days_needed = gap
                if gap < 15:
                    query_type = "Delta"
                elif gap < 365:
                    query_type = "Mid"
                else:
                    query_type = "Bulk"

            plans.append({
                "symbol": symbol,
                "primary_exchange": primary_exch,
                "currency": currency,
                "query_type": query_type,
                "days_needed": days_needed,
                "missing_days": missing_days,
                "parquet_path": parquet_path,
                "ex_info": ex_info,
                "last_date": str(last_date.date()) if last_date else "",
                "start_date": str(start_date.date()) if start_date else "",
            })

        # --- Append source-scanned tickers (new discoveries not in watchlist) ---
        if self.scan_sources:
            source_entries = self._scan_source_files(df_watch)
            if source_entries:
                plans.extend(source_entries)

        df_plan = pd.DataFrame(plans)
        # Sort: Skip first (no-op), then Delta → Mid → Bulk (shortest duration first)
        type_order = {"Skip": 0, "Delta": 1, "Mid": 2, "Bulk": 3}
        df_plan["_sort"] = df_plan["query_type"].map(type_order).fillna(4)
        df_plan = df_plan.sort_values(["_sort", "days_needed"]).drop(columns=["_sort"]).reset_index(drop=True)

        # Delta-only mode: keep only Skip + Delta rows for fast daily updates.
        if self.delta_only:
            before = len(df_plan)
            df_plan = df_plan[df_plan["query_type"].isin(["Skip", "Delta"])]
            logger.info("Delta-only filter: %d → %d tickers (dropped %d Bulk/Mid)",
                         before, len(df_plan), before - len(df_plan))

        # ---- Integrity check (index vs disk) ----
        if not self.dry_run:
            issues = self.index.check_integrity(self.raw_dir, self.market)
            if issues:
                logger.warning("Index integrity issues detected (%d):", len(issues))
                for issue in issues[:10]:
                    logger.warning("  %s", issue)
                if len(issues) > 10:
                    logger.warning("  ... and %d more", len(issues) - 10)

        # Log summary
        counts = df_plan["query_type"].value_counts().to_dict()
        total_bars = int(df_plan["days_needed"].sum())
        logger.info(
            "Download plan: Skip=%d Delta=%d Mid=%d Bulk=%d  (est. %d bars total)",
            counts.get("Skip", 0), counts.get("Delta", 0),
            counts.get("Mid", 0), counts.get("Bulk", 0), total_bars,
        )
        return df_plan

    # ------------------------------------------------------------------
    # Duration string builder
    # ------------------------------------------------------------------
    @staticmethod
    def _duration_str(query_type: str, days_needed: int) -> str:
        if query_type == "Bulk":
            return "20 Y"
        elif query_type == "Delta":
            return f"{max(days_needed + 5, 5)} D"
        elif query_type == "Mid":
            return f"{max(days_needed // 30 + 1, 1)} M"
        return "1 D"

    @staticmethod
    def _timeout_for(query_type: str) -> int:
        if query_type == "Bulk":
            return 45
        elif query_type == "Mid":
            return 20
        return 10

    # ------------------------------------------------------------------
    # Single ticker download
    # ------------------------------------------------------------------
    async def _download_ticker(self, plan: dict) -> dict:
        symbol = plan["symbol"]
        ex_info = plan["ex_info"]
        query_type = plan["query_type"]
        days_needed = plan["days_needed"]
        parquet_path = plan["parquet_path"]
        lcd = self._latest_complete_day_for(plan["primary_exchange"])

        result = {
            "symbol": symbol,
            "market": self.market,
            "status": "FAILED",
            "rows": 0,
            "min_date": "",
            "max_date": "",
            "error": "",
            "query_type": query_type,
            "duration_used": "",
            "primary_exchange": plan.get("primary_exchange", "SMART"),
            "currency": plan.get("currency", "USD"),
        }

        dur_str = self._duration_str(query_type, days_needed)
        result["duration_used"] = dur_str
        timeout = self._timeout_for(query_type)

        for attempt in range(1, MAX_RETRIES + 1):
            async with self.sem:
                try:
                    await self.limiter.acquire()

                    # Clear any previous error
                    self.ticker_status.pop(symbol, None)

                    contract = Stock(
                        symbol,
                        ex_info["exchange"],
                        ex_info.get("currency", "USD"),
                        primaryExchange=ex_info.get("primaryExchange", ""),
                    )

                    t0 = time.monotonic()
                    bars = await self.ib.reqHistoricalDataAsync(
                        contract,
                        endDateTime="",
                        durationStr=dur_str,
                        barSizeSetting=self.bar_size,
                        whatToShow=self.what_to_show,
                        useRTH=self.use_rth,
                        formatDate=1,
                        timeout=timeout,
                    )
                    elapsed_ms = (time.monotonic() - t0) * 1000
                    self._latencies.append(elapsed_ms)

                    # Check for callback-driven errors
                    if symbol in self.ticker_status:
                        err = self.ticker_status[symbol]
                        if err.get("permanent_fail"):
                            # Permission errors — no retry
                            result["error"] = err.get("error", "Unknown")
                            result["status"] = "PERM_FAIL"
                            return result
                        if err.get("transient_fail") and attempt < MAX_RETRIES:
                            logger.warning(
                                "[%s] Transient failure (attempt %d/%d), retrying in %ds: %s",
                                symbol, attempt, MAX_RETRIES, RETRY_DELAY_SEC, err.get("error", ""),
                            )
                            await asyncio.sleep(RETRY_DELAY_SEC)
                            continue  # retry
                        # Transient but exhausted retries, or unknown callback error
                        result["error"] = err.get("error", "Unknown")
                        result["status"] = "FAILED"
                        return result

                    if not bars:
                        if attempt < MAX_RETRIES:
                            logger.warning(
                                "[%s] Empty response (attempt %d/%d), retrying in %ds",
                                symbol, attempt, MAX_RETRIES, RETRY_DELAY_SEC,
                            )
                            await asyncio.sleep(RETRY_DELAY_SEC)
                            continue  # retry
                        result["error"] = "Empty response (no bars returned)"
                        return result

                    # Successful download — reset pacing counter
                    self._reset_pacing()

                    df_new = util.df(bars)
                    df_new["date"] = pd.to_datetime(df_new["date"]).dt.date
                    num_cols = ["open", "high", "low", "close", "volume", "average"]
                    for c in num_cols:
                        if c in df_new.columns:
                            df_new[c] = df_new[c].astype("float32")

                    # Truncate to latest complete trading day
                    if lcd is not None:
                        df_new = df_new[df_new["date"] <= lcd.date()]
                    if df_new.empty:
                        result["error"] = "All bars filtered out (after LCD check)"
                        return result

                    # Merge with existing
                    if parquet_path.exists() and query_type != "Bulk":
                        df_old = pd.read_parquet(parquet_path)
                        df_old["date"] = pd.to_datetime(df_old["date"]).dt.date
                        df_combined = (
                            pd.concat([df_old, df_new], ignore_index=True)
                            .drop_duplicates(subset=["date"], keep="last")
                            .sort_values("date")
                            .reset_index(drop=True)
                        )
                    else:
                        df_combined = df_new.sort_values("date").reset_index(drop=True)

                    df_combined.to_parquet(parquet_path, index=False, engine="pyarrow")

                    result["status"] = "SUCCESS"
                    result["rows"] = len(df_combined)
                    result["min_date"] = str(df_combined["date"].min())
                    result["max_date"] = str(df_combined["date"].max())
                    return result  # success — exit retry loop and semaphore

                except Exception as exc:
                    if attempt < MAX_RETRIES:
                        logger.warning(
                            "[%s] Exception (attempt %d/%d), retrying in %ds: %s",
                            symbol, attempt, MAX_RETRIES, RETRY_DELAY_SEC, str(exc)[:80],
                        )
                        await asyncio.sleep(RETRY_DELAY_SEC)
                        continue  # retry
                    result["error"] = str(exc)[:200]
                    logger.error("[%s] Exception (exhausted retries): %s", symbol, str(exc)[:120])
                    await asyncio.sleep(5.0)

        return result  # exhausted all retries

    # ------------------------------------------------------------------
    # Batch qualification
    # ------------------------------------------------------------------
    async def _qualify_contracts(self, df_plan: pd.DataFrame) -> set:
        """Staggered contract qualification — avoids message-rate storms.

        Firing 300+ qualifyContractsAsync messages simultaneously saturates
        the IBKR gateway 50 msg/sec limit, which triggers cascading HMDS
        cancellations.  We chunk into batches of qualify_batch_size with
        a delay between batches.
        """
        to_download = df_plan[df_plan["query_type"] != "Skip"]
        if to_download.empty:
            return set()

        # Build all contracts up-front
        contracts = []
        symbols_in_order = []
        for _, row in to_download.iterrows():
            ex_info = row["ex_info"]
            c = Stock(
                row["symbol"],
                ex_info["exchange"],
                ex_info.get("currency", "USD"),
                primaryExchange=ex_info.get("primaryExchange", ""),
            )
            contracts.append(c)
            symbols_in_order.append(row["symbol"])

        # Staggered qualification in batches.
        # Use smaller batches during ramp to avoid polluting the calibration.
        if self._ramp_phase in ("ramp", "confirm"):
            batch_size = min(self.qualify_batch_size, 10)
        else:
            batch_size = self.qualify_batch_size
        passed: set[str] = set()

        for i in range(0, len(contracts), batch_size):
            batch_contracts = contracts[i:i + batch_size]
            batch_symbols = symbols_in_order[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(contracts) + batch_size - 1) // batch_size

            if total_batches > 1:
                logger.info("Qualifying batch %d/%d (%d contracts) ...",
                             batch_num, total_batches, len(batch_contracts))
            else:
                logger.info("Qualifying %d contracts ...", len(batch_contracts))

            try:
                qualified = await self.ib.qualifyContractsAsync(*batch_contracts)
                for contract, sym in zip(batch_contracts, batch_symbols):
                    if contract.conId > 0:
                        passed.add(sym)
                    else:
                        logger.warning("[%s] ❌ Contract qualification failed — skipping", sym)
            except Exception as e:
                logger.error("Qualification batch %d error: %s — falling back (try-all)", batch_num, e)
                passed.update(batch_symbols)

            # Pause between batches to avoid gateway message-rate saturation
            if i + batch_size < len(contracts):
                await asyncio.sleep(self.qualify_batch_delay)

        logger.info("Qualified: %d/%d contracts (%d batches)",
                     len(passed), len(contracts), total_batches)
        return passed

    # ------------------------------------------------------------------
    # Main run
    # ------------------------------------------------------------------
    async def run(self):
        logger.info("=" * 60)
        logger.info("IBKR Ingest — market=%s  dry_run=%s  limit=%s  fix_gap=%s",
                     self.market, self.dry_run, self.limit or "all", self.fix_gap)
        logger.info("=" * 60)

        # 1. Load watchlist
        df_watch = self._load_watchlist()
        if df_watch.empty:
            logger.error("Empty watchlist — aborting")
            return

        if self.dry_run:
            logger.info("[DRY RUN] Validated %d rows in watchlist", len(df_watch))
            # Build plan anyway to show forecast (including source-scan)
            df_plan = self._build_download_plan(df_watch)
            non_skip = df_plan[df_plan["query_type"] != "Skip"]
            logger.info("[DRY RUN] Would download %d tickers (%d Skip)", len(non_skip), len(df_plan) - len(non_skip))
            total_bars = int(df_plan["days_needed"].sum())
            logger.info("[DRY RUN] Estimated bars: %d  batches: %d",
                         total_bars, max(1, total_bars // self.batch_bars_threshold))
            # Save pacing profile even on dry run (so it persists learning)
            if self.profile:
                self.profile.save(self.profile_path)
            return

        if not HAS_IB_ASYNC:
            logger.error("ib_async not installed. Install on M1 Mac: pip install ib_async")
            return

        # 2. Load pacing profile and initialize ramp
        ramp_from_profile = False
        if self.profile and not self.profile.is_stale(max_age_days=self.ramp_profile_max_age):
            logger.info("Loaded pacing profile: throughput=%.1f req/min  concurrency=%d  ramp_ceiling=%d  (age: %s days)",
                         self.profile.discovered_throughput, self.profile.safe_concurrency,
                         self.profile.ramp_ceiling,
                         (dt.date.today() - dt.date.fromisoformat(self.profile.last_updated)).days)
            if self.profile.ramp_ceiling and self.profile.ramp_ceiling >= 1:
                # Start just below known ceiling, probe to confirm
                self._ramp_level = self.profile.ramp_ceiling
                self._ramp_ceiling = self.profile.ramp_ceiling
                self._ramp_phase = "confirm"
                self._ramp_confirm_needed = self.ramp_probe_batch * self.ramp_confirm_mult
                self.concurrency = max(1, self._ramp_ceiling - 1)
                self.sem = asyncio.Semaphore(self.concurrency)
                self.limiter = RateLimiter(int(self.profile.safe_rate_per_minute), 60)
                ramp_from_profile = True
                logger.info("Ramp: starting at %d (ceiling=%d from profile) → confirm phase",
                             self.concurrency, self._ramp_ceiling)
            else:
                # Profile exists but no ramp ceiling — use legacy safe_concurrency
                self.concurrency = self.profile.safe_concurrency
                self.sem = asyncio.Semaphore(self.concurrency)
                self.limiter = RateLimiter(int(self.profile.safe_rate_per_minute), 60)
                self._ramp_phase = "cruise"

        if not ramp_from_profile:
            if self.profile:
                logger.info("Pacing profile stale (>%d days) or missing ramp ceiling — full recalibrate",
                             self.ramp_profile_max_age)
            else:
                logger.info("No pacing profile found — full ramp calibration")
            # Small watchlist (< probe_batch * 2)? Skip ramp, run conservatively
            if len(df_watch) < self.ramp_probe_batch * 2:
                logger.info("Small watchlist (%d tickers) — skipping ramp, concurrency=1", len(df_watch))
                self._ramp_ceiling = 1
                self._ramp_phase = "cruise"
                self.concurrency = 1
                self.sem = asyncio.Semaphore(1)
                self.limiter = RateLimiter(30, 60)
            else:
                self._ramp_phase = "ramp"
                manual_start = (self.cfg.get("ibkr", {}).get("ramp_start_concurrency", 0) or 0)
                self._ramp_level = manual_start if manual_start > 0 else 1
                self._ramp_successes = 0
                self._ramp_ceiling = None
                self.concurrency = self._ramp_level
                self.sem = asyncio.Semaphore(self.concurrency)
                self.limiter = RateLimiter(30, 60)  # gentle rate limit during ramp
                logger.info("Ramp calibration: starting at concurrency=%d", self._ramp_level)

        # 3. Build download plan
        df_plan = self._build_download_plan(df_watch)

        # 4. Connect to IBKR
        try:
            await self.ib.connectAsync(self.ib_host, self.ib_port, clientId=self.client_id)
        except Exception as e:
            logger.error("IBKR connection failed: %s", e)
            return
        if self.ib is None or not self.ib.isConnected():
            logger.error("IBKR not connected — aborting")
            return
        logger.info("Connected to IBKR %s:%d (clientId=%d)", self.ib_host, self.ib_port, self.client_id)

        # 5. HMDS farm warm-up — wait for the historical data farm to activate.
        # The farm starts inactive and IBKR sends message 2106 when ready.
        # A blind sleep is the simplest approach; polling would require
        # parsing the IB message stream which ib_async doesn't expose simply.
        logger.info("Waiting %.0fs for HMDS historical data farm to activate...", self.hmds_warmup_probe)
        await asyncio.sleep(self.hmds_warmup_probe)
        logger.info("HMDS farm warm-up complete")

        # 6. Connection warm-up probe
        logger.info("Warm-up probe: requesting 1-day bar for liquid ticker...")
        try:
            probe_symbol = "SPY" if self.market == "USD" else "XIU"
            probe_exch = "ARCA" if self.market == "USD" else "TSE"
            probe_ex_info = EXCHANGE_MAP[probe_exch]
            probe_contract = Stock(
                probe_symbol, probe_ex_info["exchange"], probe_ex_info["currency"],
                primaryExchange=probe_ex_info["primaryExchange"],
            )
            _ = await self.ib.reqHistoricalDataAsync(
                probe_contract, endDateTime="", durationStr="1 D",
                barSizeSetting=self.bar_size, whatToShow=self.what_to_show,
                useRTH=self.use_rth, formatDate=1, timeout=10,
            )
            logger.info("Warm-up probe OK")
        except Exception as e:
            logger.warning("Warm-up probe failed (non-fatal): %s", e)

        # 7. Batch qualify contracts
        qualified_symbols = await self._qualify_contracts(df_plan)

        # 8. Prepare download queue
        to_download = df_plan[df_plan["query_type"] != "Skip"].copy()
        # Filter to qualified
        if qualified_symbols:
            pre_count = len(to_download)
            to_download = to_download[to_download["symbol"].isin(qualified_symbols)]
            if len(to_download) < pre_count:
                logger.info("Dropped %d tickers that failed qualification", pre_count - len(to_download))

        if self.limit > 0:
            to_download = to_download.head(self.limit)
            logger.info("Limited to %d tickers", self.limit)

        if to_download.empty:
            logger.info("All data up-to-date — nothing to download")
            if self.ib is not None:
                self.ib.disconnect()
            return

        self.total = len(to_download)
        self.start_time = time.monotonic()

        # Proactive batch planning: if total bars exceed threshold, warn and plan cooldowns
        total_bars = int(to_download["days_needed"].sum())
        batch_count = max(1, total_bars // self.batch_bars_threshold)
        logger.info("Starting download: %d tickers  ramp=%s  concurrency=%d  est_bars=%d  batches=%d",
                     self.total, self._ramp_phase, self.concurrency, total_bars, batch_count)
        if batch_count > 1:
            logger.info("Proactive batching: %d batches planned (~%d bars each), %.0fs cooldown between",
                         batch_count, self.batch_bars_threshold, self.batch_cooldown_sec)

        # 9. Download loop with batch cooldowns
        tasks = [
            self._download_ticker(plan)
            for _, plan in to_download.iterrows()
        ]

        audit_rows = []
        pacing_hits_before_batch = 0
        batch_num = 1
        bars_in_batch = 0

        for coro in asyncio.as_completed(tasks):
            res = await coro
            self.completed += 1
            sym = res["symbol"]

            if res["status"] == "SUCCESS":
                self.loaded += 1
                # Update index with fresh metadata
                self.index.update(
                    symbol=sym, market=self.market,
                    min_date=res.get("min_date", ""),
                    max_date=res.get("max_date", ""),
                    rows=res.get("rows", 0),
                    primary_exchange=res.get("primary_exchange", "SMART"),
                    currency=res.get("currency", "USD"),
                )
            elif res["status"] == "SKIP":
                self.skipped += 1
            else:
                self.failed += 1

            audit_rows.append(res)

            # ── Ramp calibration: bump on success, handle retries ──
            if res["status"] == "SUCCESS":
                self._ramp_handle_success()
            elif res["status"] in ("FAILED", "PERM_FAIL"):
                # Check if this was a hard error already handled by callbacks,
                # or a soft error (permission/empty/network) that should count as retry
                if not self._ramp_is_hard_error(0, res.get("error", "")):
                    self._ramp_handle_retry()

            # ── Abort check ──
            if self._ramp_phase == "abort":
                logger.error("❌ ABORT: ramp calibration failed at concurrency=1")
                self.ib.disconnect()
                return

            # Progress
            elapsed = time.monotonic() - self.start_time
            pct = (self.completed / self.total * 100)
            rate = self.completed / (elapsed / 60) if elapsed > 0 else 0
            logger.info(
                "[%3d/%d - %5.1f%%] %s → %s  (rate: %.0f/min  conc:%d  ramp:%s)",
                self.completed, self.total, pct, sym, res["status"],
                rate, self.concurrency, self._ramp_phase,
            )

            # Incremental save with batch summary
            if self.completed % self.save_every == 0:
                pacing_hits_this_batch = self._pacing_hits_total - pacing_hits_before_batch
                self._batch_summary(
                    batch_num, self.save_every,
                    success=self.loaded - (self.total - self.completed - self.failed - self.skipped),
                    failed=self.failed, perm_fail=0, pacing_hits_batch=pacing_hits_this_batch,
                )
                self._save_audit(audit_rows)
                pacing_hits_before_batch = self._pacing_hits_total

                # Proactive batch cooldown if needed
                bars_in_batch += sum(
                    r.get("days_needed", 0) for r in audit_rows[-self.save_every:]
                    if r["status"] == "SUCCESS"
                )
                if bars_in_batch >= self.batch_bars_threshold and self.completed < self.total:
                    logger.info("⏸ Batch cooldown %.0fs (bars_threshold=%d reached) ...",
                                 self.batch_cooldown_sec, self.batch_bars_threshold)
                    await asyncio.sleep(self.batch_cooldown_sec)
                    bars_in_batch = 0
                    batch_num += 1

        # 10. Final save
        self._save_audit(audit_rows)

        # 11. Update pacing profile
        total_elapsed_min = (time.monotonic() - self.start_time) / 60.0
        final_throughput = self.loaded / total_elapsed_min if total_elapsed_min > 0 else 0
        avg_latency = sum(self._latencies) / len(self._latencies) * 1000 if self._latencies else 0  # ms

        if self.profile is None:
            self.profile = PacingProfile(market=self.market)
        self.profile.update_from_run(
            throughput=final_throughput,
            concurrency=self.concurrency,
            pacing_hits=self._pacing_hits_total,
            requests=self.loaded,
            avg_latency_ms=avg_latency,
        )
        # Persist ramp ceiling if discovered
        if self._ramp_ceiling:
            self.profile.ramp_ceiling = self._ramp_ceiling
            self.profile.ramp_error_type = "ramp_calibrated"
        self.profile.save(self.profile_path)

        # 12. Disconnect
        if self.ib is not None:
            self.ib.disconnect()

        # 13. Summary + final pacing report
        logger.info("=" * 60)
        logger.info("Download complete: ✅%d loaded  ⏭%d skipped  ❌%d failed  (%.1f min)",
                     self.loaded, self.skipped, self.failed, total_elapsed_min)
        self._final_pacing_report()

    def _batch_summary(self, batch_num: int, batch_size: int, success: int, failed: int,
                       perm_fail: int, pacing_hits_batch: int):
        """Log a per-batch summary after each save_every tickers."""
        elapsed = time.monotonic() - self.start_time if self.start_time else 0
        rate = self.completed / (elapsed / 60) if elapsed > 0 else 0
        avg_lat = (sum(self._latencies) / len(self._latencies)) if self._latencies else 0
        logger.info(
            "── Batch %d/%d complete (saved) ──  ✅%d ❌%d ⛔%d  "
            "pacing_hits=%d  avg_lat=%.0fms  rate=%.0f/min  conc=%d  ramp=%s",
            batch_num, batch_size, success, failed, perm_fail,
            pacing_hits_batch, avg_lat * 1000, rate, self.concurrency, self._ramp_phase,
        )

    def _final_pacing_report(self):
        """Print and log a final summary of pacing behavior for the run."""
        elapsed_min = (time.monotonic() - self.start_time) / 60.0 if self.start_time else 0
        throughput = self.loaded / elapsed_min if elapsed_min > 0 else 0
        avg_lat_s = (sum(self._latencies) / len(self._latencies)) if self._latencies else 0
        hit_pct = (self._pacing_hits_total / max(self.total, 1)) * 100

        lines = [
            "",
            "═" * 55,
            f"Pacing Report — market={self.market}",
            "═" * 55,
            f"Total requests:    {self.completed:>6}",
            f"Successful:        {self.loaded:>6}",
            f"Failed:            {self.failed:>6}",
            f"Pacing hits:       {self._pacing_hits_total:>6}  ({hit_pct:.1f}%)",
            f"HMDS cancels:      {self._hmds_cancel_total:>6}",
            f"Avg latency:       {avg_lat_s * 1000:>6.0f} ms",
            f"Throughput:        {throughput:>6.1f} req/min",
            f"Final concurrency: {self.concurrency:>6}",
            f"Ramp phase:        {self._ramp_phase:>11}",
            f"Ramp ceiling:      {str(self._ramp_ceiling):>11}",
        ]

        if self.profile:
            lines.extend([
                f"Profile concurrency: {self.profile.safe_concurrency}",
                f"Profile rate:        {self.profile.safe_rate_per_minute:.0f}/min",
                f"Profile ramp ceil:   {self.profile.ramp_ceiling}",
            ])

        lines.append("═" * 55)
        report = "\n".join(lines)
        logger.info(report)

        # Persist pacing events summary alongside the audit
        try:
            pacing_log_exists = self.pacing_log_path.exists()
            pacing_events_count = sum(1 for _ in open(self.pacing_log_path)) if pacing_log_exists else 0
            logger.info("Pacing event log: %s  (%d events)", self.pacing_log_path, pacing_events_count)
        except Exception:
            pass

    def _save_audit(self, audit_rows: list[dict]):
        """Save incremental audit CSV + index + pacing profile."""
        df_audit = pd.DataFrame(audit_rows)
        audit_path = self.base_dir / "data" / f"audit_ingestion_{self.market.lower()}.csv"
        df_audit.to_csv(audit_path, index=False)
        # Flush index
        self.index.flush()
        # Also save pacing profile after each incremental save
        if self.profile:
            self.profile.save(self.profile_path)


# ===================================================================
# CLI Entry Point
# ===================================================================
def load_config(config_path: str = "settings.yaml") -> dict:
    """Load YAML config, resolved from the script's own directory (self-contained kit)."""
    cfg_path = Path(__file__).resolve().parent / config_path
    with open(cfg_path, "r") as f:
        return yaml.safe_load(f)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="IBKR OHLCV ingestion engine with adaptive pacing (Sprint 1)"
    )
    parser.add_argument("--market", choices=["USD", "CAD", "HOLDINGS"], required=True,
                        help="Which watchlist to process")
    parser.add_argument("--dry-run", action="store_true",
                        help="Validate watchlist without connecting to IBKR")
    parser.add_argument("--limit", type=int, default=0,
                        help="Limit to first N tickers (for testing)")
    parser.add_argument("--fixgap", action="store_true",
                        help="Re-download full history when gaps are detected")
    parser.add_argument("--delta-only", action="store_true",
                        help="Skip Bulk/Mid queries; only download Delta updates (<15 days missing)")
    parser.add_argument("--client-id", type=int, default=None,
                        help="IBKR client ID (for parallel market runs; default from settings.yaml)")
    parser.add_argument("--no-scan-sources", action="store_true",
                        help="Disable auto-discovery of new tickers from IV/TC/IBKRtemp source files")
    parser.add_argument("--config", default="settings.yaml",
                        help="Path to settings YAML (relative to script directory)")
    args = parser.parse_args()

    cfg = load_config(args.config)

    # Handle HOLDINGS market: use holdings_path, market label from currency column
    original_market = args.market
    if original_market == "HOLDINGS":
        logger.info("HOLDINGS market — processing with CAD calendar settings")

    downloader = IngestDownloader(
        market=original_market,  # pass original so watchlist/data-dir use "HOLDINGS"
        cfg=cfg,
        dry_run=args.dry_run,
        limit=args.limit,
        fix_gap=args.fixgap,
        delta_only=args.delta_only,
        client_id=args.client_id,
        scan_sources=not args.no_scan_sources and original_market != "HOLDINGS",
    )
    asyncio.run(downloader.run())