"""
Binance USDT-M Futures historical data downloader.
Run this on YOUR machine (needs internet access to fapi.binance.com).

Setup:
    pip install requests pandas
    python download_data.py

Downloads, for each symbol in SYMBOLS (default ETHUSDT + BTCUSDT):
  - OHLCV klines at each interval in INTERVALS (default 5m and 1m) for the last DAYS days
  - Funding-rate history (required for a realistic backtest)

Output:  ./data/klines/<SYMBOL>_<interval>.csv   ./data/funding/<SYMBOL>.csv   ./data/symbols.txt
Expect ~10 minutes per symbol per interval for the full history.
Resume-safe: re-running only fetches candles newer than what's already saved.
"""
import os
import time
from datetime import datetime, timezone

import pandas as pd
import requests

# ---------------- CONFIG ----------------
SYMBOLS   = ["ETHUSDT", "BTCUSDT"]   # explicit list; set to [] to rank top-N by volume instead
TOP_N     = 30                       # only used when SYMBOLS is empty
INTERVALS = ["5m", "1m"]             # 5m for the model, 1m for activity bars / fill checks
DAYS      = 2600                     # full Binance perp history (ETHUSDT starts Nov 2019)
DATA_DIR  = "data"
SLEEP    = 0.3         # seconds between requests (keeps us under rate limits)
EXCLUDE  = {"USDCUSDT", "BUSDUSDT", "FDUSDUSDT", "TUSDUSDT", "USDPUSDT"}  # stablecoin pairs
BASE     = "https://fapi.binance.com"
# ----------------------------------------

INTERVAL_MS = {"1m": 60_000, "3m": 180_000, "5m": 300_000, "15m": 900_000,
               "30m": 1_800_000, "1h": 3_600_000, "4h": 14_400_000, "1d": 86_400_000}

session = requests.Session()


def get(path, params=None, retries=5):
    for i in range(retries):
        try:
            r = session.get(BASE + path, params=params, timeout=30)
            if r.status_code in (418, 429):
                wait = 30 * (i + 1)
                print(f"  rate limited, sleeping {wait}s")
                time.sleep(wait)
                continue
            r.raise_for_status()
            return r.json()
        except Exception as e:
            print(f"  error: {e}  (retry {i + 1}/{retries})")
            time.sleep(5 * (i + 1))
    raise RuntimeError(f"request failed: {path} {params}")


def top_symbols(n):
    info = get("/fapi/v1/exchangeInfo")
    perps = {s["symbol"] for s in info["symbols"]
             if s["contractType"] == "PERPETUAL"
             and s["quoteAsset"] == "USDT"
             and s["status"] == "TRADING"}
    tickers = get("/fapi/v1/ticker/24hr")
    ranked = sorted(
        (t for t in tickers if t["symbol"] in perps and t["symbol"] not in EXCLUDE),
        key=lambda t: float(t["quoteVolume"]), reverse=True)
    return [t["symbol"] for t in ranked[:n]]


def download_klines(symbol, interval, days):
    path = f"{DATA_DIR}/klines/{symbol}_{interval}.csv"
    cols = ["open_time", "open", "high", "low", "close", "volume", "close_time",
            "quote_volume", "trades", "taker_buy_base", "taker_buy_quote", "ignore"]
    end_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    start_ms = end_ms - days * 86_400_000

    existing = None
    if os.path.exists(path):
        existing = pd.read_csv(path)
        if len(existing):
            start_ms = int(existing["open_time"].max()) + INTERVAL_MS[interval]

    rows, cur = [], start_ms
    while cur < end_ms:
        batch = get("/fapi/v1/klines",
                    {"symbol": symbol, "interval": interval, "startTime": cur, "limit": 1500})
        if not batch:
            break
        rows.extend(batch)
        cur = batch[-1][0] + INTERVAL_MS[interval]
        time.sleep(SLEEP)

    if not rows:
        return len(existing) if existing is not None else 0

    df = pd.DataFrame(rows, columns=cols).drop(columns=["ignore"])
    num = ["open", "high", "low", "close", "volume", "quote_volume",
           "taker_buy_base", "taker_buy_quote"]
    df[num] = df[num].astype(float)
    df["trades"] = df["trades"].astype(int)
    if existing is not None and len(existing):
        df = pd.concat([existing, df], ignore_index=True)
    df = df.drop_duplicates("open_time").sort_values("open_time")
    df.to_csv(path, index=False)
    return len(df)


def download_funding(symbol, days):
    path = f"{DATA_DIR}/funding/{symbol}.csv"
    end_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    start_ms = end_ms - days * 86_400_000
    rows, cur = [], start_ms
    while cur < end_ms:
        batch = get("/fapi/v1/fundingRate",
                    {"symbol": symbol, "startTime": cur, "endTime": end_ms, "limit": 1000})
        if not batch:
            break
        rows.extend(batch)
        cur = batch[-1]["fundingTime"] + 1
        time.sleep(SLEEP)
        if len(batch) < 1000:
            break
    df = pd.DataFrame(rows)
    if len(df):
        df = df[["fundingTime", "fundingRate"]].astype({"fundingRate": float})
        df = df.drop_duplicates("fundingTime").sort_values("fundingTime")
    df.to_csv(path, index=False)
    return len(df)


if __name__ == "__main__":
    os.makedirs(f"{DATA_DIR}/klines", exist_ok=True)
    os.makedirs(f"{DATA_DIR}/funding", exist_ok=True)

    symbols = SYMBOLS or top_symbols(TOP_N)
    print(f"Symbols: {', '.join(symbols)}\n")
    with open(f"{DATA_DIR}/symbols.txt", "w") as f:
        f.write("\n".join(symbols))

    for i, s in enumerate(symbols, 1):
        print(f"[{i}/{len(symbols)}] {s}")
        for itv in INTERVALS:
            n = download_klines(s, itv, DAYS)
            print(f"  klines {itv:>3}: {n:,} rows")
        print(f"  funding   : {download_funding(s, DAYS):,} rows")

    print("\nDone. Data saved to ./data/")
