# SHADOW DESK (Streamlit UI)

Paper-only monitor for the ETH HTF triple shadow (S1 / S2 / S3).

## What you get
- Brand overview with **PAPER ONLY / LIVE OFF** banners
- **Desk chat** — natural-language Q&A (rules-first, grounded in shadow data; optional `OPENAI_API_KEY` polish)
- Agreement + ETH close + last day + average equity
- **Ops health** — shadow last run, Task Scheduler result, order-book / klines age
- **Why this decision** — per-strategy gate checklist (regime, stable, SMA, BTC, cooldown)
- **Open paper positions** — entry, unrealized, days held, exit watch
- Per-strategy cards (side, equity, trades, regime, status)
- Overview: regime+price strip, agreement timeline, equity chart
- **Run history** — invocation log (`run_history.jsonl`) + daily S1/S2/S3 results
- **Liquidity** — spread, imbalance, depth ladder, ETH vs BTC (from `data/orderbook/`)
- **Run shadow** button (calls `shadow_htf_v4.py`)
- Model policy view

Liquidity charts need the order-book recorder running:

```powershell
python record_orderbook.py
```

Does **not** place exchange orders.

## Install (once)

```powershell
cd "D:\Trading Bot"
.\.venv\Scripts\Activate.ps1
pip install streamlit
```

## Run

```powershell
cd "D:\Trading Bot"
.\.venv\Scripts\Activate.ps1
streamlit run ui/app.py
```

Browser opens on `http://localhost:8501`.

## Daily shadow (unchanged)

Automation still uses Task Scheduler + `python shadow_htf_v4.py`. The UI is optional for viewing and manual runs.
