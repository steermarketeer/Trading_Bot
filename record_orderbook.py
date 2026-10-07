"""
Standalone Binance USDT-M order-book snapshot recorder.

NOT wired into S1/S2/S3 shadow strategies. Research / future fill-slippage only.

Defaults (recommended):
    symbols  ETHUSDT + BTCUSDT
    interval 5 seconds
    levels   20

Usage:
    .\\.venv\\Scripts\\python.exe record_orderbook.py
    .\\.venv\\Scripts\\python.exe record_orderbook.py --interval 1 --levels 10
    .\\.venv\\Scripts\\python.exe record_orderbook.py --once
    .\\.venv\\Scripts\\python.exe record_orderbook.py --max-snapshots 3

Output:
    data/orderbook/<SYMBOL>_depth<N>_YYYY-MM-DD.csv.gz
"""
from __future__ import annotations

import argparse
import csv
import gzip
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "data" / "orderbook"
BASE = "https://fapi.binance.com"
ALLOWED_LIMITS = {5, 10, 20, 50, 100, 500, 1000}
DEFAULT_SYMBOLS = ["ETHUSDT", "BTCUSDT"]


def get_depth(session: requests.Session, symbol: str, limit: int, retries: int = 4) -> dict:
    for i in range(retries):
        try:
            r = session.get(
                BASE + "/fapi/v1/depth",
                params={"symbol": symbol, "limit": limit},
                timeout=15,
            )
            if r.status_code in (418, 429):
                time.sleep(15 * (i + 1))
                continue
            r.raise_for_status()
            return r.json()
        except Exception as e:
            print(f"  {symbol} depth error: {e} (retry {i + 1}/{retries})")
            time.sleep(2 * (i + 1))
    raise RuntimeError(f"depth failed for {symbol}")


def flatten_snapshot(symbol: str, levels: int, payload: dict, ts: datetime) -> dict:
    bids = payload.get("bids") or []
    asks = payload.get("asks") or []
    row: dict = {
        "ts_utc": ts.isoformat(),
        "symbol": symbol,
        "last_update_id": payload.get("lastUpdateId"),
        "n_bid_levels": min(levels, len(bids)),
        "n_ask_levels": min(levels, len(asks)),
    }

    bid_qty_sum = 0.0
    ask_qty_sum = 0.0
    best_bid = None
    best_ask = None

    for i in range(levels):
        if i < len(bids):
            px, qty = float(bids[i][0]), float(bids[i][1])
            if i == 0:
                best_bid = px
            bid_qty_sum += qty
            row[f"bid_px_{i + 1}"] = px
            row[f"bid_qty_{i + 1}"] = qty
        else:
            row[f"bid_px_{i + 1}"] = None
            row[f"bid_qty_{i + 1}"] = None

        if i < len(asks):
            px, qty = float(asks[i][0]), float(asks[i][1])
            if i == 0:
                best_ask = px
            ask_qty_sum += qty
            row[f"ask_px_{i + 1}"] = px
            row[f"ask_qty_{i + 1}"] = qty
        else:
            row[f"ask_px_{i + 1}"] = None
            row[f"ask_qty_{i + 1}"] = None

    mid = None
    spread = None
    if best_bid is not None and best_ask is not None and best_bid > 0:
        mid = (best_bid + best_ask) / 2.0
        spread = best_ask - best_bid
    denom = bid_qty_sum + ask_qty_sum
    imbalance = ((bid_qty_sum - ask_qty_sum) / denom) if denom > 0 else None

    row["best_bid"] = best_bid
    row["best_ask"] = best_ask
    row["mid"] = mid
    row["spread"] = spread
    row["spread_bps"] = (spread / mid * 10_000.0) if mid and spread is not None else None
    row["bid_qty_sum"] = bid_qty_sum
    row["ask_qty_sum"] = ask_qty_sum
    row["imbalance"] = imbalance
    return row


def fieldnames(levels: int) -> list[str]:
    base = [
        "ts_utc", "symbol", "last_update_id",
        "best_bid", "best_ask", "mid", "spread", "spread_bps",
        "bid_qty_sum", "ask_qty_sum", "imbalance",
        "n_bid_levels", "n_ask_levels",
    ]
    for i in range(1, levels + 1):
        base.extend([f"bid_px_{i}", f"bid_qty_{i}", f"ask_px_{i}", f"ask_qty_{i}"])
    return base


def out_path(symbol: str, levels: int, day: str) -> Path:
    return OUT_DIR / f"{symbol}_depth{levels}_{day}.csv.gz"


def append_row(path: Path, row: dict, cols: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not path.exists() or path.stat().st_size == 0
    with gzip.open(path, "at", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        if write_header:
            w.writeheader()
        w.writerow(row)


def snapshot_once(session: requests.Session, symbols: list[str], levels: int, cols: list[str]) -> None:
    ts = datetime.now(timezone.utc)
    day = ts.strftime("%Y-%m-%d")
    for symbol in symbols:
        payload = get_depth(session, symbol, levels)
        row = flatten_snapshot(symbol, levels, payload, ts)
        path = out_path(symbol, levels, day)
        append_row(path, row, cols)
        mid = row.get("mid")
        spr = row.get("spread_bps")
        mid_s = f"{mid:.2f}" if mid is not None else "n/a"
        spr_s = f"{spr:.3f}" if spr is not None else "n/a"
        print(f"  {ts.isoformat()} {symbol} mid={mid_s} spread_bps={spr_s} -> {path.name}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Record Binance futures order-book snapshots (standalone)")
    ap.add_argument("--symbols", nargs="+", default=DEFAULT_SYMBOLS)
    ap.add_argument("--interval", type=float, default=5.0, help="seconds between snapshots (default 5)")
    ap.add_argument("--levels", type=int, default=20, choices=sorted(ALLOWED_LIMITS),
                    help="depth levels (Binance limit; default 20)")
    ap.add_argument("--once", action="store_true", help="take one snapshot per symbol and exit")
    ap.add_argument("--max-snapshots", type=int, default=0,
                    help="stop after N cycles (0 = run forever)")
    args = ap.parse_args()

    if args.interval <= 0:
        raise SystemExit("--interval must be > 0")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cols = fieldnames(args.levels)
    session = requests.Session()

    print("=" * 60)
    print("ORDER BOOK RECORDER - standalone (not wired to shadow strategies)")
    print(f"symbols={args.symbols}  interval={args.interval}s  levels={args.levels}")
    print(f"output={OUT_DIR}")
    print("=" * 60)

    n = 0
    try:
        while True:
            t0 = time.monotonic()
            try:
                snapshot_once(session, args.symbols, args.levels, cols)
            except Exception as e:
                print(f"WARN cycle failed: {e}")
            n += 1
            if args.once or (args.max_snapshots and n >= args.max_snapshots):
                break
            elapsed = time.monotonic() - t0
            sleep_for = max(0.0, args.interval - elapsed)
            time.sleep(sleep_for)
    except KeyboardInterrupt:
        print("\nStopped by user.")

    print(f"Done. cycles={n}")


if __name__ == "__main__":
    main()
