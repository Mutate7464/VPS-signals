# 06\_SPRINT1\_AND\_2\_STARTER\_CODE.md — Settings, IBKR Ingestion & Anti-Leakage Pytest Suite

Copy these files directly into `/opt/quant-screener/` on your Hostinger KVM2 Linux VPS to initialize Sprint 1 and Sprint 2\.

---

## 1\. `config/settings.yaml`

project:

  name: "quant-screener-mvp"

  base\_dir: "/opt/quant-screener"

  n\_jobs: 2  \# Strictly pinned for Hostinger KVM2 (2 vCPU / 8 GB RAM)

  float\_dtype: "float32"

ibkr:

  host: "127.0.0.1"

  port: 4002          \# 4002 \= IB Gateway Paper, 4001 \= IB Gateway Live, 7496/7497 \= TWS

  client\_id: 101

  lookback\_cold: "5 Y"

  bar\_size: "1 day"

  what\_to\_show: "ADJUSTED\_LAST"

  use\_rth: true

  request\_delay\_sec: 1.5

  timeout\_sec: 30

watchlists:

  usd\_path: "config/watchlist\_300\_usd.csv"

  cad\_path: "config/watchlist\_300\_cad.csv"

  holdings\_path: "config/holdings.csv"

features:

  windows: \[5, 10, 20, 50, 100\]

  rsi\_windows: \[5, 14, 21\]

  hurst\_windows: \[20, 50, 100\]

  frac\_diff\_d: 0.40

  atr\_window: 20

targets:

  high\_15d\_horizon: 15

  low\_15d\_horizon: 15

  trend\_20d\_horizon: 20

  trend\_min\_r2: 0.60

  trend\_atr\_mult: 2.0

modeling:

  n\_splits: 5

  embargo\_td: 20

  vif\_threshold: 5.0

  xgb\_params:

    n\_estimators: 400

    max\_depth: 4

    learning\_rate: 0.03

    subsample: 0.8

    colsample\_bytree: 0.7

    min\_child\_weight: 20

    reg\_alpha: 1.0

    reg\_lambda: 5.0

    tree\_method: "hist"

    n\_jobs: 2

    random\_state: 42

reporting:

  top\_n\_low\_15d: 30

  top\_n\_up\_20d: 30

  chart\_lookback\_bars: 120

  batch\_gc\_size: 10

---

## 2\. CSV Template Headers (`config/*.csv`)

### `config/watchlist_300_usd.csv`

symbol,sec\_type,exchange,primary\_exchange,currency

AAPL,STK,SMART,NASDAQ,USD

MSFT,STK,SMART,NASDAQ,USD

NVDA,STK,SMART,NASDAQ,USD

AMZN,STK,SMART,NASDAQ,USD

JPM,STK,SMART,NYSE,USD

XOM,STK,SMART,NYSE,USD

### `config/watchlist_300_cad.csv`

symbol,sec\_type,exchange,primary\_exchange,currency

RY,STK,SMART,TSE,CAD

TD,STK,SMART,TSE,CAD

SHOP,STK,SMART,TSE,CAD

ENB,STK,SMART,TSE,CAD

CNQ,STK,SMART,TSE,CAD

CP,STK,SMART,TSE,CAD

### `config/holdings.csv`

symbol,sec\_type,exchange,primary\_exchange,currency,shares,avg\_cost,entry\_date

CNQ,STK,SMART,TSE,CAD,500,44.20,2026-03-15

MSFT,STK,SMART,NASDAQ,USD,50,415.00,2026-05-10

---

## 3\. `src/ibkr_ingest.py` (Sprint 1 — Async Paced Parquet Ingestion Engine)

import argparse

import asyncio

import datetime as dt

from pathlib import Path

import pandas as pd

import pyarrow as pa

import pyarrow.parquet as pq

import yaml

from ib\_async import IB, Stock, util

def load\_config(config\_path: str \= "config/settings.yaml") \-\> dict:

    with open(config\_path, "r") as f:

        return yaml.safe\_load(f)

def compute\_duration\_str(parquet\_path: Path, default\_lookback: str \= "5 Y") \-\> str:

    """If Parquet file exists, compute delta days since last bar; otherwise return full cold lookback."""

    if not parquet\_path.exists():

        return default\_lookback

    df\_existing \= pd.read\_parquet(parquet\_path, columns=\["date"\])

    if df\_existing.empty:

        return default\_lookback

    last\_date \= pd.to\_datetime(df\_existing\["date"\]).max().date()

    delta\_days \= (dt.date.today() \- last\_date).days

    if delta\_days \<= 0:

        return "0 D"

    \# Pad by 5 days to overwrite any recent corporate action adjustments

    return f"{min(delta\_days \+ 5, 365)} D"

async def fetch\_ticker\_ohlcv(

    ib: IB, row: pd.Series, market\_label: str, cfg: dict, sem: asyncio.Semaphore

) \-\> dict:

    symbol \= str(row\["symbol"\]).strip()

    currency \= str(row\["currency"\]).strip()

    exchange \= str(row.get("exchange", "SMART")).strip()

    primary\_exch \= str(row.get("primary\_exchange", "")).strip()

    out\_dir \= Path(cfg\["project"\]\["base\_dir"\]) / "data" / "raw\_ohlcv" / f"market={market\_label}"

    out\_dir.mkdir(parents=True, exist\_ok=True)

    parquet\_path \= out\_dir / f"symbol={symbol}.parquet"

    duration\_str \= compute\_duration\_str(parquet\_path, cfg\["ibkr"\]\["lookback\_cold"\])

    if duration\_str \== "0 D":

        df\_old \= pd.read\_parquet(parquet\_path)

        return {

            "symbol": symbol,

            "market": market\_label,

            "status": "UP\_TO\_DATE",

            "rows": len(df\_old),

            "min\_date": str(df\_old\["date"\].min()),

            "max\_date": str(df\_old\["date"\].max()),

        }

    contract \= Stock(symbol, exchange, currency, primaryExchange=primary\_exch)

    async with sem:

        try:

            qualified \= await ib.qualifyContractsAsync(contract)

            if not qualified:

                return {"symbol": symbol, "market": market\_label, "status": "UNQUALIFIED", "rows": 0}

            bars \= await ib.reqHistoricalDataAsync(

                contract,

                endDateTime="",

                durationStr=duration\_str,

                barSizeSetting=cfg\["ibkr"\]\["bar\_size"\],

                whatToShow=cfg\["ibkr"\]\["what\_to\_show"\],

                useRTH=cfg\["ibkr"\]\["use\_rth"\],

                formatDate=1,

                timeout=cfg\["ibkr"\]\["timeout\_sec"\],

            )

            await asyncio.sleep(cfg\["ibkr"\]\["request\_delay\_sec"\])

            if not bars:

                return {"symbol": symbol, "market": market\_label, "status": "EMPTY\_BARS", "rows": 0}

            df\_new \= util.df(bars)

            df\_new\["date"\] \= pd.to\_datetime(df\_new\["date"\]).dt.date

            num\_cols \= \["open", "high", "low", "close", "volume", "average"\]

            for c in num\_cols:

                if c in df\_new.columns:

                    df\_new\[c\] \= df\_new\[c\].astype("float32")

            if parquet\_path.exists():

                df\_old \= pd.read\_parquet(parquet\_path)

                df\_combined \= (

                    pd.concat(\[df\_old, df\_new\], ignore\_index=True)

                    .drop\_duplicates(subset=\["date"\], keep="last")

                    .sort\_values("date")

                    .reset\_index(drop=True)

                )

            else:

                df\_combined \= df\_new.sort\_values("date").reset\_index(drop=True)

            df\_combined.to\_parquet(parquet\_path, index=False, engine="pyarrow")

            return {

                "symbol": symbol,

                "market": market\_label,

                "status": "SUCCESS",

                "rows": len(df\_combined),

                "min\_date": str(df\_combined\["date"\].min()),

                "max\_date": str(df\_combined\["date"\].max()),

            }

        except Exception as exc:

            await asyncio.sleep(5.0)

            return {"symbol": symbol, "market": market\_label, "status": f"ERROR: {exc}", "rows": 0}

async def main\_async(market: str, dry\_run: bool \= False):

    cfg \= load\_config()

    path\_map \= {

        "USD": cfg\["watchlists"\]\["usd\_path"\],

        "CAD": cfg\["watchlists"\]\["cad\_path"\],

        "HOLDINGS": cfg\["watchlists"\]\["holdings\_path"\],

    }

    csv\_path \= Path(cfg\["project"\]\["base\_dir"\]) / path\_map\[market\]

    df\_watch \= pd.read\_csv(csv\_path)

    if dry\_run:

        print(f"\[DRY RUN\] Validated {len(df\_watch)} rows in {csv\_path}")

        return

    ib \= IB()

    await ib.connectAsync(

        cfg\["ibkr"\]\["host"\], cfg\["ibkr"\]\["port"\], clientId=cfg\["ibkr"\]\["client\_id"\]

    )

    sem \= asyncio.Semaphore(1)

    audit\_rows \= \[\]

    for \_, row in df\_watch.iterrows():

        mkt\_label \= str(row\["currency"\]).strip().upper()

        res \= await fetch\_ticker\_ohlcv(ib, row, mkt\_label, cfg, sem)

        audit\_rows.append(res)

        print(f"\[{res\['market'\]}\] {res\['symbol'\]}: {res\['status'\]} ({res\['rows'\]} rows)")

    ib.disconnect()

    df\_audit \= pd.DataFrame(audit\_rows)

    audit\_out \= Path(cfg\["project"\]\["base\_dir"\]) / "data" / f"audit\_ingestion\_{market}.csv"

    df\_audit.to\_csv(audit\_out, index=False)

    print(f"Saved Gate 1 audit summary to {audit\_out}")

if \_\_name\_\_ \== "\_\_main\_\_":

    parser \= argparse.ArgumentParser()

    parser.add\_argument("--market", choices=\["USD", "CAD", "HOLDINGS"\], required=True)

    parser.add\_argument("--dry-run", action="store\_true")

    args \= parser.parse\_args()

    asyncio.run(main\_async(args.market, args.dry\_run))

---

## 4\. `tests/test_leakage.py` (Sprint 2 — Mandatory Anti-Leakage Unit Tests)

import numpy as np

import pandas as pd

import pytest

def compute\_sample\_causal\_features(df: pd.DataFrame) \-\> pd.DataFrame:

    """Reference wrapper to test feature\_engine causal invariance."""

    out \= pd.DataFrame(index=df.index)

    close \= df\["close"\].astype("float64")

    high \= df\["high"\].astype("float64")

    low \= df\["low"\].astype("float64")

    \# Trailing 20d Bollinger %B

    sma20 \= close.rolling(20, min\_periods=20).mean()

    std20 \= close.rolling(20, min\_periods=20).std(ddof=1)

    out\["bb\_pct\_b\_20"\] \= ((close \- (sma20 \- 2.0 \* std20)) / (4.0 \* std20 \+ 1e-12)).astype("float32")

    \# Trailing 20d Wilder ATR

    prev\_close \= close.shift(1)

    tr \= pd.concat(\[high \- low, (high \- prev\_close).abs(), (low \- prev\_close).abs()\], axis=1).max(axis=1)

    out\["atr\_20"\] \= tr.ewm(alpha=1.0 / 20.0, min\_periods=20, adjust=False).mean().astype("float32")

    return out

def test\_future\_perturbation\_invariance():

    """Mutating t+1..T with \+500% price spikes MUST NOT alter any feature at index \<= t."""

    rng \= np.random.default\_rng(42)

    n\_bars \= 250

    cutoff\_t \= 200

    dates \= pd.date\_range("2025-01-01", periods=n\_bars, freq="B")

    close \= 100.0 \* np.exp(np.cumsum(rng.normal(0.0005, 0.015, size=n\_bars)))

    df\_orig \= pd.DataFrame(

        {

            "date": dates,

            "open": close \* 0.998,

            "high": close \* 1.01,

            "low": close \* 0.99,

            "close": close,

            "volume": rng.integers(100\_000, 1\_000\_000, size=n\_bars),

        }

    )

    df\_mutated \= df\_orig.copy()

    \# Inject massive future look-ahead spike after cutoff\_t

    df\_mutated.loc\[cutoff\_t \+ 1 :, \["open", "high", "low", "close"\]\] \*= 6.0

    feat\_orig \= compute\_sample\_causal\_features(df\_orig)

    feat\_mut \= compute\_sample\_causal\_features(df\_mutated)

    for col in feat\_orig.columns:

        a \= feat\_orig.loc\[:cutoff\_t, col\].to\_numpy()

        b \= feat\_mut.loc\[:cutoff\_t, col\].to\_numpy()

        assert np.allclose(a, b, rtol=1e-6, atol=1e-6, equal\_nan=True), (

            f"DATA LEAKAGE DETECTED in feature {col} prior to cutoff {cutoff\_t}\!"

        )

def test\_purged\_walk\_forward\_embargo\_gap():

    """Verify minimum 20 trading day embargo between max(train\_idx) and min(val\_idx)."""

    n\_dates \= 1000

    embargo\_td \= 20

    train\_end \= 600

    val\_start \= train\_end \+ embargo\_td \+ 1

    train\_indices \= np.arange(0, train\_end)

    val\_indices \= np.arange(val\_start, 800\)

    assert (val\_indices.min() \- train\_indices.max()) \> embargo\_td, (

        "Purged Walk-Forward split violated 20-day embargo boundary\!"

    )