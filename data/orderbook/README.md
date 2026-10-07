# Order book recorder (standalone)

Records Binance USDT-M **depth snapshots** for research / future fill studies.

**Not used by S1 / S2 / S3 shadow strategies.**

## Defaults
| Setting | Value |
|---|---|
| Symbols | ETHUSDT, BTCUSDT |
| Interval | 5 seconds |
| Depth | 20 levels |

## Run (continuous)

```powershell
cd "D:\Trading Bot"
.\.venv\Scripts\Activate.ps1
python record_orderbook.py
```

## Useful flags

```powershell
python record_orderbook.py --once
python record_orderbook.py --max-snapshots 3
python record_orderbook.py --interval 1 --levels 10
```

## Output

Daily gzip CSVs:

```
data/orderbook/ETHUSDT_depth20_YYYY-MM-DD.csv.gz
data/orderbook/BTCUSDT_depth20_YYYY-MM-DD.csv.gz
```

Columns include `ts_utc`, `mid`, `spread`, `spread_bps`, `imbalance`, and per-level `bid_px_N` / `bid_qty_N` / `ask_px_N` / `ask_qty_N`.

Stop with Ctrl+C. For 24/7 capture, schedule or run in a dedicated terminal / Task Scheduler (separate from the daily shadow job).

## UI

SHADOW DESK → **Liquidity** tab reads these files (spread, imbalance, depth ladder, daily summary). Not used by S1/S2/S3.
