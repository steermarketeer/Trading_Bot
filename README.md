# ETH trading bot

Paper-only for now: **no code in this repo places exchange orders.**

The bot trades ETHUSDT perpetuals on the daily chart, filtered by a weekly/monthly regime gate.
Strategies are YAML files you can edit. One engine runs backtests and the paper shadow, so the
two always follow the same rules.

- `IMPLEMENTATION_PLAN.md`: review findings and roadmap
- `STRATEGY_GUIDE.md`: how to fine-tune or add strategies

## Setup (once)

```bash
python -m venv .venv
# Windows: .venv\Scripts\Activate.ps1     macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Full history (first time only, ~20-30 min): `python download_data.py`

## Everyday commands

| What | Command |
|---|---|
| Data quality / coverage | `python -m bot check-data` |
| Backtest every strategy | `python -m bot backtest` |
| Backtest one, a date range, save trades | `python -m bot backtest strategies/s3_btc_confirm.yaml --start 2022-01-01 --save results` |
| Same, legacy-like costs (no funding/slippage) | `python -m bot backtest --no-funding --slippage-bps 0` |
| Start the paper shadow fresh | `python -m bot shadow --reset --backfill-days 90` |
| Daily paper run (refreshes data first) | `python -m bot shadow` |
| Tests | `python -m pytest -q tests` |

Daily automation: point Task Scheduler at `scripts/run_shadow.ps1` (Windows), or cron at
`scripts/run_shadow.sh` (Linux/VPS).


## Strategy v3 (current) - paper trading

Rules frozen from research (see `reports/strategy_v2.md`, `reports/failure_liquidity.md`):
2:1 breakouts on 2h / 4h / 1D with certainty >= 7, BTC 4h + 6h MACD agreement, a clean risk zone (no swing
liquidity or equal-high/low pool between entry and stop), A+ when breaking into a low-volume zone; plus 1D bounces
at zones tested 4+ times (5:1 since the ratio sweep; the research-chosen 0.786 stop and journal filters are not yet wired live). Risk: A+ 4%, others 2%, leverage cap 5x. **No exchange orders.**

| What | Command |
|---|---|
| Refit / freeze the v3 models (only after new research) | `python -m bot freeze-v3` |
| Start paper trading from today | `python -m bot shadow-v3` |
| Paper run without downloading | `python -m bot shadow-v3 --no-refresh` |
| Restart from a date (e.g. to replay) | `python -m bot shadow-v3 --reset --start 2025-11-01` |

Schedule `scripts/run_shadow_v3.ps1` (Windows) or `scripts/run_shadow_v3.sh` (cron) every 2 hours at :10 UTC.
Output in `shadow_v3/`: `latest.json` (summary, open positions), `trades.csv`, `equity.csv`, `run.log`.
A replay of the holdout period (Nov 2025 - Oct 2026) is in `reports/v3_holdout_replay/`; it reproduces the research
holdout trades exactly (107/107 identical).

## Layout

```
bot/                 new package (use this)
  config.py          config.yaml + strategy YAML loading (unknown keys are rejected)
  data.py            5m klines -> completed daily bars, funding, data-quality checks
  regime.py          Bull/Bear/Neutral regime gate (no lookahead, tested)
  engine.py          THE trading rules: fills, stops, liquidation, fees, funding, halts
  backtest.py        backtest runner + metrics + buy-and-hold benchmark
  shadow.py          daily paper trading on the same engine
  refresh.py         incremental Binance download (closed candles + funding)
  strategies/        strategy classes (htf_trend = legacy S1/S2/S3 family)
strategies/*.yaml    strategy settings you tune
config.yaml          costs, data paths, regime lag, which strategies the shadow runs
tests/               pytest suite
shadow_v2/           new shadow output (state, trades.csv, days.csv, latest.json)
```

Legacy scripts (`strategy_htf_v*.py`, `shadow_htf_v4.py`, `train_*.py`, `backtest_*.py`) and the
`shadow/` folder are unchanged. The Streamlit UI (`ui/`) still reads the legacy `shadow/` folder.
They'll be moved to `research/` once the new shadow replaces the old one.

## How a day is simulated

1. 00:00 UTC funding for a position held overnight (longs pay positive rates, shorts receive)
2. yesterday's order fills at today's **open** (+ slippage, + taker fee)
3. protective stop / liquidation from today's **high/low**; a gap through the level fills at the open
4. 08:00 and 16:00 UTC funding
5. mark-to-market, drawdown check (halts resume after `halt_days`)
6. the strategy looks at today's **close** and may place an order for tomorrow's open
