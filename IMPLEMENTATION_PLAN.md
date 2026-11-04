# Implementation plan — ETH trading bot

Written 2026-11-04 after a code review of the `main` branch (commit `2dc5b2d`).

## Where the project actually is

- **What the brief asked for** (`claude_code_brief_v2.md`): a 5-minute ML system with 500+ features, LightGBM and a sequence model, meta-labelling, alpha mining, and a live execution engine.
- **What got built:** the 5m LightGBM models were trained and they lost money on holdout (accuracy 35%, profit factor 0.03–0.6, see `models/holdout_backtest*.json`). The project then switched to a **rule-based daily trend follower**: a weekly/monthly regime gate plus daily SMA entries and exits (S1/S2/S3). It is paper-traded with `shadow_htf_v4.py` and shown in a Streamlit dashboard (`ui/`).
- **Not built:** an execution engine, exchange connectivity, order/position persistence, reconciliation, a kill switch, tests, a dependency file for the core code, and deployment off the Windows laptop.
- **Shadow status:** all three sleeves are at **−15% to −20%** after 3 paper trades each. The last data refresh and run was 2026-10-13, so the shadow has been stopped for about 3 weeks.

## What is wrong (most severe first)

### A. The results are less reliable than they look
1. **The "walk-forward" doesn't use its training window.** `eval_cfg_walkforward` runs fixed configs only on the test folds. Across v4→v7, roughly 60 configs were scored on the same 8–9 OOS folds, and the winner was whichever scored best there. That is selection on the test set, so the "OOS +188%" figure is in-sample in practice.
2. **The sample is tiny.** The v7 winner made 34 trades in 4.5 years (3–6 per fold). The pass gate counts a fold as "edged" when it has ≥3 trades. A fold with no losses gets PF = 999, which inflates the median PF.
3. **The headline number depends on where the folds start.** Moving the fold start by 30-day steps (my check, script in the scratchpad) changed the v7 winner's OOS return from +189% to +61%/+102%/+109%/+72%/+102%, and it **failed** the gate at a +30-day offset. The base S3 failed at +120 days. The sign holds up (positive at every offset), but the size of the return is luck.
4. **Most of the v7 gain comes from the ATR filter, not the stop.** For S3, stop 10/12/15% gives exactly the no-stop result. The stop never fires because it is only checked on the daily close.

### B. The backtest and shadow simulation are not realistic
5. **Stops are checked on the daily close only.** Intraday wicks are ignored, so a "10% stop" can lose 15–20% or more.
6. **Fills come a day late.** The signal uses yesterday's close (`close_lag`), but the fill is at *today's* close. That is 24h of extra delay. Live, you would act at today's open.
7. **No funding, slippage, or leverage.** Perp funding over multi-day holds matters (often 0.01% per 8h or more, and much higher in trends). Only `FEE=0.0004` is charged.
8. **The drawdown halt can never resume.** Resuming requires equity to recover, but equity only changes when a trade closes, and a halted sleeve opens no trades. This affects both `run_cfg` and `shadow_htf_v4.process_bar`. S1 is at −19.8% against a 25% halt, so one more loss stops it for good.
9. **Two copies of the strategy logic.** `run_cfg` (backtest) and `process_bar` (shadow) are separate implementations that can drift apart. Live code would make a third copy.

### C. Shadow and ops bugs
10. **`shadow/s1_both_align_no_stop/trades.csv` is corrupt.** The header has 8 columns but the last row has 9, because a `strategy` column was added later. The UI hides this with `on_bad_lines="skip"`, so S1's latest trade silently drops out of the dashboard.
11. **The "shadow" history is mostly backfilled.** The 90-day bootstrap replays history, so it is not forward evidence. Nothing marks which rows are backfill and which are live.
12. **The shadow has stalled.** Klines end 2026-10-13. It depends on a Windows Task Scheduler job on a laptop (`fix_shadow_task.ps1`, `D:\Trading Bot`), and nothing alerts when it stops.
13. **S1 and S3 are nearly the same trade.** They have identical equity curves so far, so "3 strategies" is effectively 2.

### D. Repo hygiene
14. 160 MB of CSV and parquet files are committed to git, plus a `.docx`.
15. There is no `requirements.txt` or `pyproject.toml` for the core code (only `ui/requirements.txt` with streamlit), and no tests.
16. About 20 flat scripts named by version (`strategy_htf_v4_pass`, `v5_search`, `v6_s3_search`, …), with dead ML scripts mixed in with live code.

## Plan

### Phase 0 — Clean foundation (1–2 sessions)
- [ ] Add `pyproject.toml` / `requirements.txt` (pandas, numpy, requests, pyarrow, lightgbm, streamlit).
- [ ] Restructure into a package:
  ```
  bot/
    data/        download + refresh + quality checks
    regime.py
    strategy/    one pure function: (state, bar) -> (new_state, actions)
    engine/      backtest runner + shadow runner share strategy/
    validation/  walk-forward, robustness, reports
    exec/        (Phase 4) exchange adapter
  research/      old v1–v7 scripts kept for reference
  ui/
  tests/
  ```
- [ ] Stop committing `data/` and big `models/` artifacts. Regenerate them with the download script or use Git LFS. Keep only the small frozen config JSONs.
- [ ] Use cross-platform paths and a single `config.yaml` (symbols, fees, funding, slippage, sizing).
- [ ] Repair `trades.csv`: use a fixed schema and write with the csv module or parquet, never by appending a mismatched header.

### Phase 1 — Correct and realistic engine (2–3 sessions)
- [ ] **One strategy core** used by backtest, shadow and (later) live. Add a test that backtest and shadow produce identical trades on the same bars.
- [ ] Fill at the **next daily open** after the signal, plus configurable slippage.
- [ ] **Intraday stops** from the daily high/low, with stop-first when both target and stop are hit. Use 5m data to resolve the order when needed.
- [ ] **Funding cost** from `data/funding/*.csv` for every 8h settlement the position is held.
- [ ] **Leverage + liquidation** model (maintenance margin), with sizing as a parameter.
- [ ] Fix the **halt deadlock**: resume after N days or when the regime flips, not on equity recovery.
- [ ] Unit tests: regime has no lookahead, cooldown, halt/resume, stop-first, funding math.

### Phase 2 — Honest validation (2 sessions)
- [ ] **Lock a final holdout**: the last 12 months, untouched until the end.
- [ ] **True walk-forward**: choose the config on each *train* window only, then score on the next test window. Report that chosen-on-train result, not the best fixed config.
- [ ] Record **how many configs were ever tried** and apply a deflated-Sharpe / multiple-testing haircut.
- [ ] Robustness report: fold-offset sweep (as above), ±20% parameter neighbourhood, bootstrap / Monte Carlo of trades for return and drawdown confidence intervals.
- [ ] **Benchmarks**: buy-and-hold ETH, plain 50/200 SMA, regime gate alone. The strategy has to beat these net of costs.
- [ ] Re-score S1/S2/S3/v7 under the Phase 1 engine. Decision point: keep 1–2 sleeves, or rethink.

### Phase 3 — Real forward shadow (start right after Phase 1, runs ≥4–6 weeks)
- [ ] Reset shadow state; **forward-only** from the reset date, with the backfill flagged separately.
- [ ] Move it off the laptop: Linux VPS (Tokyo/Singapore) + cron/systemd, or GitHub Actions on a schedule.
- [ ] Alerts: daily digest + "no run in 26h" / "data stale" alarm (Telegram or email).
- [ ] Compare shadow fills with what the backtest engine says for the same days, every day.

### Phase 4 — Execution layer (testnet first, 3–4 sessions)
- [ ] Exchange adapter for Binance USDT-M (testnet), via `ccxt` or the official connector.
- [ ] SQLite store for orders, fills, positions and equity; **reconcile with the exchange on every start**.
- [ ] Order logic: limit or post-only near the open with a market fallback, partial fills, retries, rate limits.
- [ ] Risk limits: max position, max daily loss, **kill switch** (a file or env flag plus a UI button), and isolated margin.
- [ ] API keys only from env or a secrets file (trade-only, IP-whitelisted, no withdrawals). Never in the repo.
- [ ] Run on testnet in parallel with shadow for 2+ weeks.

### Phase 5 — Small live
- [ ] Go live only if the Phase 2 numbers survive and the shadow tracks the backtest.
- [ ] Start tiny, at 1–2× leverage. Weekly review of drift between live, shadow and backtest.

### Phase 6 — Optional, later
- ML as a **filter on the HTF signals** (should this daily entry be taken?), not a 5m scalper. That has already failed here.
- Multi-coin (brief §14) once ETH works live.

## Suggested next step
Phase 0 + Phase 1 together: restructure, write the single strategy core with realistic fills, stops and funding, and fix the halt and CSV bugs. Then re-run the numbers before deciding anything else.
