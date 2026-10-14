# Project progress — ETH trading bot

Last updated: 2026-10-13 (v7 stop search PASS + desk portfolio UI)

## Overall status

**Three walk-forward PASS strategies frozen.** Shadow runs **S1+S2+S3**. No live trading.

| # | Strategy | Distinct idea | WF (approx) | In shadow? |
|---|---|---|---|---|
| S1 | `both_align_no_stop` | Both sides, align, cool5/stable5 | 5/8, +33%, PF 1.20 | Yes |
| S2 | `both_cool7_stable7` | Stricter cool7/stable7 | 6/8, +43%, PF 1.95 | Yes |
| **S3** | **`both_btc_confirm`** | **Both sides + BTC trend confirm** | **5/8, +76%, PF 1.93** | **Yes** |

Also PASS in #3 search: `both_btc_cool7`, `align_both_sma30_nostop`.

## v7 stop search (2026-10-13) — PASS

Risk overlay search on S1/S2/S3 bases (`strategy_htf_v7_stop_search.py`).

- **Gate:** ≥50% edged folds, median PF > 1, compounded OOS > 0
- **Winner (frozen):** `both_btc_confirm__stop10_atr06`  
  stop 10% · atr_max 0.06 · edged **5/9** · OOS **+188.6%** · medPF **3.12** · worst DD **-8.6%**
- Artifacts: `models/htf_v7_stop_winner.json`, `htf_v7_stop_summary.json`, `htf_v7_stop_leaderboard.csv`
- S2 + stops did **not** clear the PASS gate (edged 3–4/9)
- Several S1/S3 stop variants also PASS; best stop-aware pick is the BTC+stop10+atr06 variant
- **Shadow sleeves unchanged** — v7 is frozen research; swap/augment only after explicit review (do not panic-retune on ~3 paper trades)

## S1 ≈ S3 note

S1 and S3 often take the same side (BTC filter is a twin, not full diversification). Desk portfolio views: **equal weight**, **agreement_2of3**, **S2-primary**. Prefer agreement / S2-primary for delivery risk framing.

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
Paper dashboard (`ui/`) — WF context, full equity, portfolio views (equal / agreement / S2-primary), S1≈S3 note, liquidity, trades/signals, run shadow. No live orders.

Helpers: `ui/desk_portfolio.py`, `ui/desk_visibility.py`, `ui/desk_chat.py`.

## Order book (standalone, not wired to S1–S3)
```powershell
python record_orderbook.py
# defaults: ETH+BTC, 5s, depth 20 → data/orderbook/*.csv.gz
```
See `data/orderbook/README.md`.

## Next
1. Keep daily shadow on S1+S2+S3 (catch-up ok if a day is missed)  
2. After more paper sample, decide whether to add v7 stop sleeve or replace S3 base  
3. Build live shell (testnet / kill switch) while shadow continues  
4. Tiny live only after more weeks + real Bull entry/exit sample  
