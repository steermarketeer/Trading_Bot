"""
Incremental refresh of Binance USDT-M 5m klines and funding rates (public endpoints, no keys).

Fixes vs legacy refresh_recent_data.py:
  * only CLOSED candles are stored (legacy saved the still-forming candle and never corrected it)
  * funding rates are refreshed too (legacy left them stale, so the shadow stopped charging funding)
"""
from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

BASE = "https://fapi.binance.com"
KLINE_COLS = [
    "open_time", "open", "high", "low", "close", "volume", "close_time",
    "quote_volume", "trades", "taker_buy_base", "taker_buy_quote", "ignore",
]
FIVE_MIN = 300_000


def _get(path: str, params: dict, retries: int = 5):
    for i in range(retries):
        try:
            r = requests.get(BASE + path, params=params, timeout=30)
            if r.status_code in (418, 429):
                time.sleep(30 * (i + 1))
                continue
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            print(f"  retry {i + 1}: {e}")
            time.sleep(3 * (i + 1))
    raise RuntimeError(f"Binance request failed: {path} {params}")


def _now_ms() -> int:
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def refresh_klines(data_dir: Path, symbol: str, days: int = 10) -> int:
    path = Path(data_dir) / "klines" / f"{symbol}_5m.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    now = _now_ms()
    existing = pd.read_csv(path) if path.exists() else pd.DataFrame(columns=KLINE_COLS[:-1])
    start = int(existing["open_time"].max()) + FIVE_MIN if len(existing) else now - days * 86_400_000
    rows, cur = [], start
    while cur < now:
        batch = _get("/fapi/v1/klines", {"symbol": symbol, "interval": "5m", "startTime": cur, "limit": 1500})
        if not batch:
            break
        rows.extend(b for b in batch if int(b[6]) < now)  # close_time in the past = closed candle
        cur = int(batch[-1][0]) + FIVE_MIN
        time.sleep(0.25)
    if not rows:
        return 0
    df = pd.DataFrame(rows, columns=KLINE_COLS).drop(columns=["ignore"])
    for c in ("open", "high", "low", "close", "volume", "quote_volume", "taker_buy_base", "taker_buy_quote"):
        df[c] = df[c].astype(float)
    df["trades"] = df["trades"].astype(int)
    out = pd.concat([existing, df], ignore_index=True).drop_duplicates("open_time").sort_values("open_time")
    out.to_csv(path, index=False)
    return len(df)


def refresh_funding(data_dir: Path, symbol: str) -> int:
    path = Path(data_dir) / "funding" / f"{symbol}.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = pd.read_csv(path) if path.exists() else pd.DataFrame(columns=["fundingTime", "fundingRate"])
    start = int(existing["fundingTime"].max()) + 1 if len(existing) else _now_ms() - 30 * 86_400_000
    rows, cur = [], start
    while True:
        batch = _get("/fapi/v1/fundingRate", {"symbol": symbol, "startTime": cur, "limit": 1000})
        if not batch:
            break
        rows.extend({"fundingTime": int(b["fundingTime"]), "fundingRate": float(b["fundingRate"])} for b in batch)
        cur = int(batch[-1]["fundingTime"]) + 1
        if len(batch) < 1000:
            break
        time.sleep(0.25)
    if not rows:
        return 0
    out = pd.concat([existing, pd.DataFrame(rows)], ignore_index=True)
    out = out.drop_duplicates("fundingTime").sort_values("fundingTime")
    out.to_csv(path, index=False)
    return len(rows)


def refresh_all(data_dir: Path, symbols: list[str], days: int = 10) -> None:
    for sym in symbols:
        k = refresh_klines(data_dir, sym, days)
        f = refresh_funding(data_dir, sym)
        print(f"refresh {sym}: +{k} 5m candles, +{f} funding rows")
