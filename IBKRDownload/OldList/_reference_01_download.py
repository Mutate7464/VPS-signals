"""
01_download_error_driven.py — IBKR Async Download (Error-Driven Pacing)

Key differences vs 01_download.py:
  - Error-Driven Pacing: Concurrency is only reduced when specific IBKR pacing errors (Code 420 or 162 with 'pacing' msg) are received.
  - Permission Flagging: Explicitly identifies Error 162 "No market data permissions" and flags them for the index.
  - Log suppression: Suppresses "updatePortfolio: PortfolioItem" noise from the display.
"""

import os
import sys
import glob
import time
import asyncio
import argparse
import shutil
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import pandas_market_calendars as mcal
from ib_insync import IB, Stock, util

from config import (
    BASE_DIR, RAW_DATA_DIR, INDEX_CSV_PATH,
    IB_HOST, IB_PORT,
    PACING_REQUESTS_LIMIT, PACING_WINDOW_SECONDS,
    DOWNLOAD_CONCURRENCY, MIN_CONCURRENCY,
    PACING_BACKOFF_SLEEP, PACING_HIT_THRESHOLD,
    GLOBAL_PAUSE_SLEEP, SAVE_EVERY
)

# Standard logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('DownloadErrorDriven')

# Suppress ib_insync portfolio updates and connection noise
logging.getLogger('ib_insync').setLevel(logging.WARNING)

# ---------------------------------------------------------------------------
# Rate Limiter
# ---------------------------------------------------------------------------
class RateLimiter:
    def __init__(self, max_calls: int, period: float):
        self.max_calls = max_calls
        self.period    = period
        self.calls     = []
        self.lock      = asyncio.Lock()

    async def acquire(self):
        async with self.lock:
            now = asyncio.get_event_loop().time()
            self.calls = [t for t in self.calls if now - t < self.period]
            if len(self.calls) >= self.max_calls:
                sleep_time = self.period - (now - self.calls[0])
                if sleep_time > 0:
                    logger.info(f"Rate limit — local throttle {sleep_time:.2f}s")
                    await asyncio.sleep(sleep_time)
            self.calls.append(asyncio.get_event_loop().time())

# ---------------------------------------------------------------------------
# Downloader
# ---------------------------------------------------------------------------
class Downloader:
    def __init__(self, dry_run: bool = False, limit: int = 0):
        self.dry_run  = dry_run
        self.limit    = limit
        self.ib       = IB()
        self.limiter  = RateLimiter(PACING_REQUESTS_LIMIT, PACING_WINDOW_SECONDS)
        self.sem      = asyncio.Semaphore(DOWNLOAD_CONCURRENCY)
        self.concurrency = DOWNLOAD_CONCURRENCY
        
        # Exchange Translation Map (IBKR uses 'TSE' for Toronto Stock Exchange)
        self.exchange_map = {
            'TSE': {'exchange': 'SMART', 'primaryExchange': 'TSE', 'currency': 'CAD', 'secType': 'STK'},
            'TSX': {'exchange': 'SMART', 'primaryExchange': 'TSE', 'currency': 'CAD', 'secType': 'STK'},
            'TSXV': {'exchange': 'SMART', 'primaryExchange': 'VENTURE', 'currency': 'CAD', 'secType': 'STK'},
            'NEO': {'exchange': 'SMART', 'primaryExchange': 'AEQS', 'currency': 'CAD', 'secType': 'STK'},
            'NASDAQ': {'exchange': 'SMART', 'primaryExchange': 'NASDAQ', 'currency': 'USD', 'secType': 'STK'},
            'NYSE': {'exchange': 'SMART', 'primaryExchange': 'NYSE', 'currency': 'USD', 'secType': 'STK'},
            'ARCA': {'exchange': 'SMART', 'primaryExchange': 'ARCA', 'currency': 'USD', 'secType': 'STK'},
        }

        # Progress counters
        self.total = self.completed = self.loaded = self.failed = self.skipped = 0
        self.start_time = None
        
        # Pacing state
        self._consecutive_pacing = 0
        self._pace_lock = asyncio.Lock()
        
        # Error tracking (per request)
        self.ticker_errors = {}

        # ---------- Calendars (TSX & NYSE) ----------
        cal_end = pd.Timestamp.now()
        
        # TSX
        self.tsx = mcal.get_calendar('TSX')
        tsx_schedule = self.tsx.schedule(start_date=cal_end - pd.Timedelta(days=365*21), end_date=cal_end)
        self.trading_days_tsx = mcal.date_range(tsx_schedule, frequency='1D').tz_convert(None).normalize()
        
        # NYSE
        self.nyse = mcal.get_calendar('NYSE')
        nyse_schedule = self.nyse.schedule(start_date=cal_end - pd.Timedelta(days=365*21), end_date=cal_end)
        self.trading_days_nyse = mcal.date_range(nyse_schedule, frequency='1D').tz_convert(None).normalize()
        
        now_et = datetime.now(ZoneInfo('America/New_York'))
        today = pd.Timestamp.now().normalize()
        
        def get_lcd(trading_days):
            past = trading_days[trading_days <= today]
            if len(past) == 0: return None
            elif past[-1] == today and (now_et.hour < 17 or (now_et.hour == 17 and now_et.minute < 30)):
                return past[-2] if len(past) >= 2 else None
            return past[-1]
            
        self.latest_complete_day_tsx = get_lcd(self.trading_days_tsx)
        self.latest_complete_day_nyse = get_lcd(self.trading_days_nyse)
        logger.info(f"Latest complete trading day: TSX={self.latest_complete_day_tsx}, NYSE={self.latest_complete_day_nyse}")

        # Register event handler
        self.ib.errorEvent += self._on_ib_error

    def _on_ib_error(self, reqId, errorCode, errorString, contract):
        """
        IBKR Error Event Handler.
        Specifically looks for:
          - Pacing errors (Code 420 or 162 with 'pacing' string)
          - Permission errors (Code 162 with 'No market data permissions')
        """
        symbol = contract.symbol if contract else f"reqId:{reqId}"
        
        # 1. Pacing Errors
        is_pacing = (errorCode == 420) or (errorCode == 162 and ("pacing" in errorString.lower() or "limited" in errorString.lower()))
        if is_pacing:
            logger.warning(f"[{symbol}] 🔴 IBKR Pacing Error {errorCode}: {errorString}")
            # Use create_task since this is a callback from the event loop
            asyncio.create_task(self._on_pacing_hit())
            return

        # 2. Permission Errors
        if errorCode == 162 and "No market data permissions" in errorString:
            logger.error(f"[{symbol}] ❌ Permission Error: {errorString}")
            self.ticker_errors[symbol] = f"Error 162: No market data permissions"

    async def _on_pacing_hit(self):
        """React ONLY to confirmed pacing errors."""
        async with self._pace_lock:
            self._consecutive_pacing += 1
            if self._consecutive_pacing >= PACING_HIT_THRESHOLD:
                logger.warning(f"🔴 Global pause {GLOBAL_PAUSE_SLEEP}s due to confirmed pacing")
                await asyncio.sleep(GLOBAL_PAUSE_SLEEP)
                self._consecutive_pacing = 0
            else:
                new_c = max(self.concurrency - max(self.concurrency // 2, 1), MIN_CONCURRENCY)
                if new_c < self.concurrency:
                    logger.warning(f"⚠️ Confirming pacing hit — Throttling concurrency: {self.concurrency} → {new_c}")
                    self.concurrency = new_c
                    self.sem = asyncio.Semaphore(self.concurrency)
                await asyncio.sleep(PACING_BACKOFF_SLEEP)

    def _reset_pacing(self):
        self._consecutive_pacing = 0

    def load_index(self) -> pd.DataFrame:
        if os.path.exists(INDEX_CSV_PATH): index_df = pd.read_csv(INDEX_CSV_PATH)
        else: index_df = pd.DataFrame(columns=['Symbol', 'Exchange'])
        if 'Symbol' in index_df.columns:
            index_df['Symbol'] = index_df['Symbol'].astype(str).str.strip().replace(['nan', 'None', ''], np.nan)
            index_df = index_df.dropna(subset=['Symbol'])
            
            # Clean any old '.TO' suffixes from TSE/TSX symbols in the existing index
            if 'Exchange' in index_df.columns:
                mask = index_df['Exchange'].isin(['TSE', 'TSX']) & index_df['Symbol'].str.endswith('.TO')
                if mask.any():
                    index_df.loc[mask, 'Symbol'] = index_df.loc[mask, 'Symbol'].str[:-3]
                    index_df.loc[mask, 'Status'] = 'Pending'
                    for col in ['Error_Detail', 'Error_Action', 'Query_Type', 'Data_Start_Date', 'Data_End_Date']:
                        if col in index_df.columns:
                            index_df.loc[mask, col] = ''
                    for col in ['Missing_Days', 'Days_Needed']:
                        if col in index_df.columns:
                            index_df.loc[mask, col] = 0

                # Self-heal: Reset status to 'Pending' for clean Canadian symbols that previously failed with 'Empty response' (caused by .TO suffix)
                if 'Status' in index_df.columns:
                    heal_mask = (
                        index_df['Exchange'].isin(['TSE', 'TSX']) &
                        (index_df['Status'] == 'Failed') &
                        (index_df['Error_Detail'] == 'Empty response')
                    )
                    if heal_mask.any():
                        index_df.loc[heal_mask, 'Status'] = 'Pending'
                        for col in ['Error_Detail', 'Error_Action', 'Query_Type', 'Data_Start_Date', 'Data_End_Date']:
                            if col in index_df.columns:
                                index_df.loc[heal_mask, col] = ''
                        for col in ['Missing_Days', 'Days_Needed']:
                            if col in index_df.columns:
                                index_df.loc[heal_mask, col] = 0
                    
                # Drop duplicates that may have arisen (e.g. CIA and CIA.TO both becoming CIA)
                if 'Status' in index_df.columns:
                    status_priority = {'Loaded': 0, 'Pending': 1, 'Failed': 2, 'Skipped': 3}
                    index_df['status_priority'] = index_df['Status'].map(status_priority).fillna(4)
                    index_df = index_df.sort_values(by=['Symbol', 'status_priority'])
                    index_df = index_df.drop_duplicates(subset=['Symbol'], keep='first')
                    index_df = index_df.drop(columns=['status_priority'])
                else:
                    index_df = index_df.drop_duplicates(subset=['Symbol'], keep='first')
        if 'Type' in index_df.columns: 
            index_df['Type'] = pd.Series([np.nan] * len(index_df), dtype=object)
        
        # Ensure we process IV files first, so TC data (Sector & Industry) can override them later
        all_files = sorted(glob.glob(os.path.join(BASE_DIR, "IV_*.csv"))) + sorted(glob.glob(os.path.join(BASE_DIR, "TC_*.csv")))
        
        for file_path in all_files:
            fname = os.path.basename(file_path)
            is_tc = fname.startswith("TC_")
            is_iv = fname.startswith("IV_")
            type_name = fname.replace("TC_", "").replace("IV_", "").replace(".csv", "")
            
            try: df = pd.read_csv(file_path, engine='python', on_bad_lines=self._fix_bad_lines)
            except: continue
            
            # Map columns according to the source file
            sym_col = 'Symbol' if 'Symbol' in df.columns else ('Ticker' if 'Ticker' in df.columns else None)
            if not sym_col or df.empty: continue
            
            df['Symbol'] = df[sym_col].astype(str).str.strip().str.strip('"').replace(['nan', 'None', ''], np.nan)
            df = df.dropna(subset=['Symbol'])
            
            exch_col = 'Exchange' if 'Exchange' in df.columns else ('Exch' if 'Exch' in df.columns else None)
            if exch_col: df['Exchange'] = df[exch_col].astype(str).str.strip().str.upper().replace('TSX', 'TSE')
            else: df['Exchange'] = 'TSE'
            
            # Filter out non-TSX Canada exchanges (like TSXV, NEO, VENTURE, AEQS)
            # while preserving TSX/TSE and USD exchanges (NASDAQ, NYSE, ARCA).
            if 'Exchange' in df.columns:
                non_tsx_canada = df['Exchange'].isin(['TSXV', 'NEO', 'VENTURE', 'AEQS'])
                df = df[~non_tsx_canada]
            
            if is_iv:
                # Strip '.TO' suffix for TSX/TSE exchanges
                mask = df['Exchange'].isin(['TSE', 'TSX']) & df['Symbol'].str.endswith('.TO')
                df.loc[mask, 'Symbol'] = df.loc[mask, 'Symbol'].str[:-3]
            
            sec_col = None
            if is_tc and 'Sector & Industry' in df.columns: sec_col = 'Sector & Industry'
            elif is_iv and 'Sub-group' in df.columns: sec_col = 'Sub-group'
            elif 'Sector' in df.columns: sec_col = 'Sector'
            if sec_col: df['Sector'] = df[sec_col]
            else: df['Sector'] = np.nan
            
            cname_col = 'Company Name' if 'Company Name' in df.columns else ('Description' if 'Description' in df.columns else None)
            if cname_col: df['Company Name'] = df[cname_col]
            else: df['Company Name'] = np.nan
            
            for _, row in df.iterrows():
                sym, exch, sec, cname = row['Symbol'], row['Exchange'], row['Sector'], row['Company Name']
                mask = pd.Series([False]*len(index_df), index=index_df.index)
                if pd.notna(cname) and 'Company Name' in index_df.columns and 'Error_Action' in index_df.columns:
                    m = (index_df['Company Name'] == cname) & (index_df['Error_Action'] == 'fixed')
                    if m.any(): mask = m
                if not mask.any() and 'Symbol' in index_df.columns: mask = index_df['Symbol'] == sym
                
                if mask.any():
                    i = index_df.index[mask][0]
                    if not ('Error_Action' in index_df.columns and index_df.at[i, 'Error_Action'] == 'fixed'):
                        index_df.at[i, 'Symbol'] = sym
                        index_df.at[i, 'Exchange'] = exch
                        if pd.notna(sec) and str(sec).strip() and str(sec).strip() != 'nan': index_df.at[i, 'Sector'] = str(sec).strip()
                        if pd.notna(cname) and str(cname).strip() and str(cname).strip() != 'nan': index_df.at[i, 'Company Name'] = str(cname).strip()
                    et = str(index_df.at[i, 'Type']) if 'Type' in index_df.columns else ''
                    ep = [p.strip() for p in et.split(',') if p.strip() and p.strip() not in ('nan', 'None')]
                    if type_name not in ep: ep.append(type_name); index_df.at[i, 'Type'] = ', '.join(sorted(ep))
                else:
                    nr = {'Symbol': sym, 'Exchange': exch, 'Type': type_name}
                    if pd.notna(sec) and str(sec).strip() and str(sec).strip() != 'nan': nr['Sector'] = str(sec).strip()
                    if pd.notna(cname) and str(cname).strip() and str(cname).strip() != 'nan': nr['Company Name'] = str(cname).strip()
                    index_df = pd.concat([index_df, pd.DataFrame([nr])], ignore_index=True)

        # Process sold holdings: move from holdings.csv to transactions.csv
        holdings_csv = os.path.join(BASE_DIR, 'holdings.csv')
        transactions_csv = os.path.join(BASE_DIR, 'transactions.csv')
        if os.path.exists(holdings_csv):
            try:
                h_df = pd.read_csv(holdings_csv)
                if 'Sell_Date' in h_df.columns and 'Sell_Price' in h_df.columns:
                    sold_mask = h_df['Sell_Date'].notna() & (h_df['Sell_Date'].astype(str).str.strip() != '')
                    if sold_mask.any():
                        sold_df = h_df[sold_mask]
                        # Append to transactions.csv
                        if os.path.exists(transactions_csv):
                            t_df = pd.read_csv(transactions_csv)
                            t_df = pd.concat([t_df, sold_df], ignore_index=True)
                        else:
                            t_df = sold_df
                        t_df.to_csv(transactions_csv, index=False)
                        
                        # Remove from holdings.csv
                        h_df = h_df[~sold_mask]
                        h_df.to_csv(holdings_csv, index=False)
                        logger.info(f"Moved {len(sold_df)} sold holdings from holdings.csv to transactions.csv")
            except Exception as e:
                logger.error(f"Error processing sold holdings: {e}")

        # Integrate holdings.csv so active holdings are always in the index and never dropped
        if os.path.exists(holdings_csv):
            try:
                hold_df = pd.read_csv(holdings_csv)
                sym_col = 'Ticker' if 'Ticker' in hold_df.columns else ('Symbol' if 'Symbol' in hold_df.columns else None)
                if sym_col:
                    hold_df = hold_df[hold_df[sym_col].notna()]
                    for _, row in hold_df.iterrows():
                        sym = str(row[sym_col]).strip()
                        if not sym or sym == 'nan': continue
                        
                        # Look up exchange from existing index, default to TSE if not found
                        exch = 'TSE'
                        if 'Symbol' in index_df.columns:
                            match = index_df[index_df['Symbol'] == sym]
                            if not match.empty:
                                exch = str(match.iloc[0].get('Exchange', 'TSE')).strip()
                        
                        # Strip .TO suffix for Canadian exchanges
                        if exch in ('TSE', 'TSX') and sym.endswith('.TO'):
                            sym = sym[:-3]
                            
                        mask = pd.Series([False]*len(index_df), index=index_df.index)
                        if 'Symbol' in index_df.columns:
                            mask = index_df['Symbol'] == sym
                            
                        if mask.any():
                            i = index_df.index[mask][0]
                            if pd.isna(index_df.at[i, 'Exchange']) or str(index_df.at[i, 'Exchange']).strip() == '' or str(index_df.at[i, 'Exchange']).strip() == 'nan':
                                index_df.at[i, 'Exchange'] = exch
                            et = str(index_df.at[i, 'Type']) if 'Type' in index_df.columns else ''
                            ep = [p.strip() for p in et.split(',') if p.strip() and p.strip() not in ('nan', 'None')]
                            if 'Holding' not in ep:
                                ep.append('Holding')
                                index_df.at[i, 'Type'] = ', '.join(sorted(ep))
                        else:
                            nr = {'Symbol': sym, 'Exchange': exch, 'Type': 'Holding'}
                            index_df = pd.concat([index_df, pd.DataFrame([nr])], ignore_index=True)
            except Exception as e:
                logger.error(f"Error merging holdings.csv into index: {e}")

        for col, d in {'Status':'Pending','Error_Action':'','Query_Type':'','Days_Needed':0,'Missing_Days':0,'Error_Detail':'','Last_Update_Date':'','Data_Start_Date':'','Data_End_Date':''}.items():
            if col not in index_df.columns: index_df[col] = d
            
        # STRICT WHITELIST: Drop any tickers that are no longer in the current TC*.csv or IV*.csv files
        index_df = index_df.dropna(subset=['Type'])
        index_df = index_df[index_df['Type'].astype(str).str.strip() != '']
        
        # --- HARDCODED INDEX DOWNLOADS ---
        # Guarantees baseline data is available for feature engineering
        is_usd = 'USD' in BASE_DIR.upper()
        if is_usd:
            hardcoded = [
                {'Symbol': 'SPY', 'Exchange': 'ARCA', 'Type': 'Index'},
                {'Symbol': 'QQQ', 'Exchange': 'NASDAQ', 'Type': 'Index'}
            ]
        else:
            hardcoded = [
                {'Symbol': 'XIU', 'Exchange': 'TSE', 'Type': 'Index'},
                {'Symbol': 'XIC', 'Exchange': 'TSE', 'Type': 'Index'},
                {'Symbol': 'XDIV', 'Exchange': 'TSE', 'Type': 'Index'}
            ]
        for row_data in hardcoded:
            if 'Symbol' in index_df.columns and not (index_df['Symbol'] == row_data['Symbol']).any():
                for col, d in {'Status':'Pending','Error_Action':'','Query_Type':'','Days_Needed':0,'Missing_Days':0,'Error_Detail':'','Last_Update_Date':'','Data_Start_Date':'','Data_End_Date':''}.items():
                    if col not in row_data: row_data[col] = d
                index_df = pd.concat([index_df, pd.DataFrame([row_data])], ignore_index=True)

        index_df.to_csv(INDEX_CSV_PATH, index=False)
        return index_df

    def validate_local_data(self, index_df: pd.DataFrame) -> pd.DataFrame:
        logger.info("🔍 Validating local data (start, end, gaps)...")
        for i, row in index_df.iterrows():
            sym = str(row.get('Symbol', '')).strip()
            exch = str(row.get('Exchange', 'TSE')).strip().upper()
            if not sym or sym == 'nan': continue
            
            t_days = self.trading_days_nyse if exch in ('NYSE', 'NASDAQ', 'ARCA') else self.trading_days_tsx
            
            parquet_path = os.path.join(RAW_DATA_DIR, f"{sym}.parquet")
            if os.path.exists(parquet_path):
                try:
                    df_p = pd.read_parquet(parquet_path, columns=['Date'])
                    if df_p.empty: continue
                    
                    df_p['Date'] = pd.to_datetime(df_p['Date']).dt.tz_localize(None).dt.normalize()
                    start_date, end_date = df_p['Date'].min(), df_p['Date'].max()
                    
                    # Check for gaps using appropriate calendar
                    mask = (t_days >= start_date) & (t_days <= end_date)
                    expected_days = t_days[mask]
                    actual_days = set(df_p['Date'])
                    missing = [d for d in expected_days if d not in actual_days]
                    
                    index_df.at[i, 'Data_Start_Date'] = str(start_date.date())
                    index_df.at[i, 'Data_End_Date'] = str(end_date.date())
                    index_df.at[i, 'Missing_Days'] = len(missing)
                    
                    if len(missing) > 0:
                        logger.warning(f"[{sym}] Found {len(missing)} missing days between {start_date.date()} and {end_date.date()}")
                except Exception as e:
                    logger.error(f"[{sym}] Validation error: {e}")
            else:
                # Audit: File is missing, reset index dates
                index_df.at[i, 'Data_Start_Date'] = ''
                index_df.at[i, 'Data_End_Date'] = ''
                index_df.at[i, 'Missing_Days'] = 0
        
        index_df.to_csv(INDEX_CSV_PATH, index=False)
        return index_df

    def build_download_plan(self, index_df: pd.DataFrame, fix_gap: bool = False) -> pd.DataFrame:
        for i, row in index_df.iterrows():
            sym, exch = str(row.get('Symbol', '')).strip(), str(row.get('Exchange', 'TSE')).strip().upper()
            lcd = self.latest_complete_day_nyse if exch in ('NYSE', 'NASDAQ', 'ARCA') else self.latest_complete_day_tsx
            if not sym or sym == 'nan' or exch.upper() not in ('TSE', 'TSX', 'NASDAQ', 'NYSE', 'ARCA'): index_df.at[i, 'Query_Type'] = 'Skip'; continue
            ea, st = str(row.get('Error_Action', '')).strip().lower(), str(row.get('Status', '')).strip()
            if ea == 'error' or (st in ('Failed', 'Skipped') and ea != 'fixed'): index_df.at[i, 'Query_Type'] = 'Skip'; continue
            parquet_path, last_date = os.path.join(RAW_DATA_DIR, f"{sym}.parquet"), None
            ce = str(row.get('Data_End_Date', '')).strip()
            if ce and ce != 'nan':
                try: last_date = pd.to_datetime(ce).tz_localize(None).normalize()
                except: pass
            if last_date is None and os.path.exists(parquet_path):
                try:
                    df_p = pd.read_parquet(parquet_path, columns=['Date'])
                    if not df_p.empty: 
                        last_date = pd.to_datetime(df_p['Date']).max().tz_localize(None).normalize()
                        index_df.at[i, 'Data_End_Date'] = str(last_date.date())
                        index_df.at[i, 'Data_Start_Date'] = str(pd.to_datetime(df_p['Date']).min().date())
                except: pass
            
            missing_days = int(row.get('Missing_Days', 0))
            
            if lcd is None or last_date is None or not os.path.exists(parquet_path): index_df.at[i, 'Query_Type'], index_df.at[i, 'Days_Needed'] = 'Bulk', 365*20
            elif fix_gap and missing_days > 0:
                index_df.at[i, 'Query_Type'], index_df.at[i, 'Days_Needed'] = 'Bulk', 365*20
                logger.info(f"[{sym}] Gap repair triggered ({missing_days} days missing)")
            elif last_date >= lcd: index_df.at[i, 'Query_Type'], index_df.at[i, 'Status'] = 'Skip', 'Loaded'
            else:
                gap = (lcd - last_date).days
                index_df.at[i, 'Days_Needed'] = gap
                index_df.at[i, 'Query_Type'] = 'Delta' if gap < 15 else ('Mid' if gap < 365 else 'Bulk')
        index_df.to_csv(INDEX_CSV_PATH, index=False)
        return index_df

    def _fix_bad_lines(self, bad_line):
        if len(bad_line) > 9:
            extra = len(bad_line) - 9
            bad_line[7] = ",".join(bad_line[7: 7 + extra + 1])
            del bad_line[8: 8 + extra]
        return bad_line

    async def download_ticker(self, ticker: str, exchange: str, qt: str, days: int) -> dict:
        result = {'ticker': ticker, 'status': 'Failed', 'data_start': '', 'data_end': '', 'error': ''}
        parquet_path = os.path.join(RAW_DATA_DIR, f"{ticker}.parquet")
        dur_str = ('20 Y' if qt == 'Bulk' else (f'{max(days+5, 5)} D' if qt == 'Delta' else f'{max(days//30+1, 1)} M'))
        
        async with self.sem:
            try:
                await self.limiter.acquire()
                # Clear any previous error for this ticker
                self.ticker_errors.pop(ticker, None)
                
                # Translation layer for Exchange
                ex_info = self.exchange_map.get(exchange.upper(), {'exchange': 'SMART', 'primaryExchange': exchange.upper(), 'currency': 'CAD', 'secType': 'STK'})
                
                contract = Stock(ticker, ex_info['exchange'], ex_info['currency'])
                contract.primaryExchange = ex_info['primaryExchange']
                contract.secType = ex_info['secType']
                
                t0 = time.monotonic()
                bars = await self.ib.reqHistoricalDataAsync(
                    contract, endDateTime='', durationStr=dur_str,
                    barSizeSetting='1 day', whatToShow='ADJUSTED_LAST',
                    useRTH=True, formatDate=1, keepUpToDate=False, timeout=0
                )
                elapsed = time.monotonic() - t0
                
                # Check for callback-driven errors (Permission/Pacing)
                if ticker in self.ticker_errors:
                    result['error'] = self.ticker_errors[ticker]
                    return result

                if not bars:
                    # If we don't have an explicit error yet, but bars are empty, it's a "soft" failure
                    result['error'] = 'Empty response'
                    return result

                self._reset_pacing()
                df = util.df(bars).rename(columns={'open':'Open','high':'High','low':'Low','close':'Close','volume':'Volume'})
                df['Date'] = pd.to_datetime(df['date']).dt.tz_localize(None).dt.normalize()
                lcd = self.latest_complete_day_nyse if exchange.upper() in ('NYSE', 'NASDAQ', 'ARCA') else self.latest_complete_day_tsx
                if lcd: df = df[df['Date'] <= lcd]
                if df.empty: result['error'] = 'Filtered to empty'; return result

                if os.path.exists(parquet_path) and qt != 'Bulk':
                    old = pd.read_parquet(parquet_path)
                    old['Date'] = pd.to_datetime(old['Date']).dt.tz_localize(None).dt.normalize()
                    df = pd.concat([old, df]).drop_duplicates(subset=['Date'], keep='last').sort_values('Date').reset_index(drop=True)
                else: df = df.sort_values('Date').reset_index(drop=True)

                df.to_parquet(parquet_path, index=False)
                result['status'], result['data_start'], result['data_end'] = 'Loaded', str(df['Date'].min().date()), str(df['Date'].max().date())
                logger.info(f"[{ticker}] ✅ {len(df)} rows ({dur_str} / {elapsed:.1f}s)")

            except Exception as e:
                result['error'] = str(e)
                logger.error(f"[{ticker}] Exception: {e}")
        return result

    async def run(self, fix_gap: bool = False):
        logger.info("======= STEP 1: IBKR Data Ingestion (Async Download) =======")
        """
        Workflow:
        1. Load/Merge TC_* files into index.csv
        2. Audit/Update local data (Data Start/End/Gaps)
        3. Build download plan and execute
        """
        # Step 1: Load/Merge
        logger.info("Step 1: Loading TC_* files and merging with index...")
        index_df = self.load_index()
        
        # Step 2: Audit/Update (Always run validation to ensure index matches local state)
        logger.info("Step 2: Auditing local data vs index...")
        index_df = self.validate_local_data(index_df)
        
        # Step 3: Download
        logger.info("Step 3: Building download plan and executing...")
        index_df = self.build_download_plan(index_df, fix_gap=fix_gap)
        
        to_download = index_df[index_df['Query_Type'] != 'Skip'].copy()
        if self.limit > 0: to_download = to_download.head(self.limit)
        
        if to_download.empty: logger.info("All data current."); return

        try:
            await self.ib.connectAsync(IB_HOST, IB_PORT, clientId=2)
        except Exception as e:
            logger.error(f"IBKR connection failed: {e}")
            logger.warning("Proceeding without new downloads.")
            return
            
        if not self.ib.isConnected(): logger.error("No connection."); return

        # Batch Qualify
        contracts = []
        for _, row in to_download.iterrows():
            sym = str(row['Symbol']).strip()
            exch = str(row.get('Exchange', 'TSE')).strip().upper()
            ex_info = self.exchange_map.get(exch, {'exchange': 'SMART', 'primaryExchange': exch, 'currency': 'CAD' if exch in ('TSE', 'TSX') else 'USD', 'secType': 'STK'})
            c = Stock(sym, ex_info['exchange'], ex_info['currency'])
            c.primaryExchange = ex_info['primaryExchange']
            contracts.append(c)
            
        qualified = await self.ib.qualifyContractsAsync(*contracts)
        
        # Filter to_download to only those that qualified successfully
        valid_download = []
        for (idx, row), contract in zip(to_download.iterrows(), contracts):
            sym = str(row['Symbol']).strip()
            if contract.conId <= 0:
                logger.warning(f"[{sym}] ❌ Contract qualification failed. Skipping download.")
                mask = index_df['Symbol'] == sym
                index_df.loc[mask, 'Status'] = 'Failed'
                index_df.loc[mask, 'Error_Detail'] = 'Contract qualification failed'
                index_df.loc[mask, 'Last_Update_Date'] = str(pd.Timestamp.now().date())
            else:
                valid_download.append(row)
                
        # Save index immediately if we marked any as failed
        if len(valid_download) < len(to_download):
            index_df.to_csv(INDEX_CSV_PATH, index=False)
            
        if self.dry_run:
            logger.info("DRY RUN — skipping downloads."); self.ib.disconnect(); return

        if not valid_download:
            logger.info("No valid contracts to download after qualification."); self.ib.disconnect(); return

        self.total = len(valid_download)
        tasks = [
            self.download_ticker(
                str(row['Symbol']).strip(), 
                str(row.get('Exchange', 'TSX')).strip(), 
                str(row.get('Query_Type', 'Bulk')).strip(), 
                int(row.get('Days_Needed', 0))
            ) for row in valid_download
        ]
        
        for coro in asyncio.as_completed(tasks):
            res = await coro
            self.completed += 1
            st = res.get('status', 'Failed')
            if st == 'Loaded': self.loaded += 1
            else: self.failed += 1
            
            sym, mask = res.get('ticker', ''), index_df['Symbol'] == res.get('ticker', '')
            index_df.loc[mask, 'Status'], index_df.loc[mask, 'Error_Detail'], index_df.loc[mask, 'Last_Update_Date'] = st, res.get('error', ''), str(pd.Timestamp.now().date())
            
            # Explicitly mark permission errors to stop retrying them
            if "No market data permissions" in res.get('error', ''):
                index_df.loc[mask, 'Error_Action'] = 'error'

            if res.get('data_start'): index_df.loc[mask, 'Data_Start_Date'] = res['data_start']
            if res.get('data_end'): index_df.loc[mask, 'Data_End_Date'] = res['data_end']
            
            pct = (self.completed / self.total * 100)
            logger.info(f"[{self.completed:3d}/{self.total} - {pct:5.1f}%] {sym} -> {st} (Pace:{len(self.limiter.calls)}/{PACING_REQUESTS_LIMIT}) | Conc:{self.concurrency}")
            if self.completed % SAVE_EVERY == 0: index_df.to_csv(INDEX_CSV_PATH, index=False)

        index_df.to_csv(INDEX_CSV_PATH, index=False)
        self.ib.disconnect()
        logger.info(f"Done. ✅{self.loaded} loaded ❌{self.failed} failed")

if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    p = argparse.ArgumentParser()
    p.add_argument('--dry-run', action='store_true')
    p.add_argument('--limit', type=int, default=0)
    p.add_argument('--fixgap', action='store_true', help='Validate existing data for gaps and date ranges')
    args = p.parse_args()
    asyncio.run(Downloader(dry_run=args.dry_run, limit=args.limit).run(fix_gap=args.fixgap))
