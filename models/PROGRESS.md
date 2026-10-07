# Project progress — ETH trading bot

Last updated: 2026-09-28 (S3 in triple shadow)

## Overall status

**Three walk-forward PASS strategies frozen.** Shadow runs **S1+S2+S3**. No live trading.

| # | Strategy | Distinct idea | WF (approx) | In shadow? |
|---|---|---|---|---|
| S1 | `both_align_no_stop` | Both sides, align, cool5/stable5 | 5/8, +33%, PF 1.20 | Yes |
| S2 | `both_cool7_stable7` | Stricter cool7/stable7 | 6/8, +43%, PF 1.95 | Yes |
| **S3** | **`both_btc_confirm`** | **Both sides + BTC trend confirm** | **5/8, +76%, PF 1.93** | **Yes** |

Also PASS in #3 search: `both_btc_cool7`, `align_both_sma30_nostop`.

## S3 rules (`both_btc_confirm`)
- Both long/short with SMA alignment
- Entry SMA50, exit SMA30
- Regime stable 5d, cooldown 5d, DD halt 25%
- **BTC must confirm** (BTC close > SMA50 for longs; < for shorts)
- Stateless / no trade-pattern memory

Frozen: `models/htf_v6_s3_winner.json`

## Shadow (triple)
```powershell
python shadow_htf_v4.py
# first-time S3 only:
python shadow_htf_v4.py --bootstrap-s3-only --bootstrap-days 90
```
See `shadow/README.md`. Digests: `shadow/latest.json` (+ latest_s1/s2/s3).

Task Scheduler: `ETH Shadow HTF` daily ~05:10 local. If it fails with `0x800710E0`, run admin script `fix_shadow_task.ps1` and re-enter the stored password.

## UI
```powershell
streamlit run ui/app.py
```
Paper dashboard (`ui/`) — status, agreement, trades/signals, run shadow. No live orders.

## Order book (standalone, not wired to S1–S3)
```powershell
python record_orderbook.py
# defaults: ETH+BTC, 5s, depth 20 → data/orderbook/*.csv.gz
```
See `data/orderbook/README.md`.

## Next
1. Keep daily shadow on S1+S2+S3 (catch-up ok if a day is missed)  
2. Fix scheduler reliability if `0x800710E0` recurs  
3. Build live shell (testnet / kill switch) while shadow continues  
4. Tiny live only after more weeks + real Bull entry/exit sample  
 
