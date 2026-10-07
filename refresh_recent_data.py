"""
Refresh recent Binance USDT-M 5m klines (resume-safe append).

Used by the HTF v4 shadow logger so decisions use up-to-date candles.
Does NOT place orders. Does NOT download full history (use download_data.py for that).

Usage:
    .\\.venv\\Scripts\\python.exe refresh_recent_data.py
    .\\.venv\\Scripts\\python.exe refresh_recent_data.py --days 14
"""
from __future__ import annotations

import argparse
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

BASE = "https://fapi.binance.com"
DATA_DIR = Path("data")
INTERVAL_MS = {"5m": 300_000, "1m": 60_000}
COLS = [
    "open_time", "open", "high", "low", "close", "volume", "close_time",
    "quote_volume", "trades", "taker_buy_base", "taker_buy_quote", "ignore",
]


def get_json(path: str, params: dict, retries: int = 5):
    for i in range(retries):
        try:
            r = requests.get(BASE + path, params=params, timeout=30)
            if r.status_code in (418, 429):
                time.sleep(30 * (i + 1))
                continue
            r.raise_for_status()
            return r.json()
        except Exception as e:
            print(f"  retry {i + 1}: {e}")
            time.sleep(3 * (i + 1))
    raise RuntimeError(f"failed {path} {params}")


def refresh_klines(symbol: str, interval: str, days: int) -> int:
    path = DATA_DIR / "klines" / f"{symbol}_{interval}.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    end_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    start_ms = end_ms - days * 86_400_000

    existing = None
    if path.exists():
        existing = pd.read_csv(path)
        if len(existing):
            start_ms = int(existing["open_time"].max()) + INTERVAL_MS[interval]

    rows, cur = [], start_ms
    while cur < end_ms:
        batch = get_json("/fapi/v1/klines", {
            "symbol": symbol, "interval": interval,
            "startTime": cur, "limit": 1500,
        })
        if not batch:
            break
        rows.extend(batch)
        cur = batch[-1][0] + INTERVAL_MS[interval]
        time.sleep(0.25)

    if not rows:
        return len(existing) if existing is not None else 0

    df = pd.DataFrame(rows, columns=COLS).drop(columns=["ignore"])
    for c in ["open", "high", "low", "close", "volume", "quote_volume",
              "taker_buy_base", "taker_buy_quote"]:
        df[c] = df[c].astype(float)
    df["trades"] = df["trades"].astype(int)
    if existing is not None and len(existing):
        df = pd.concat([existing, df], ignore_index=True)
    df = df.drop_duplicates("open_time").sort_values("open_time")
    df.to_csv(path, index=False)
    return len(df)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=10, help="lookback window to refresh")
    args = ap.parse_args()
    for sym in ("ETHUSDT", "BTCUSDT"):
        n = refresh_klines(sym, "5m", args.days)
        print(f"{sym} 5m -> {n:,} rows")
    print("Done.")


if __name__ == "__main__":
    main()
