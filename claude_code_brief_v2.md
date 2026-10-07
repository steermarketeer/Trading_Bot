# Claude Code brief v2 — ETH 5-minute ML trading bot

Paste everything below this line as the first message in a Claude Code session opened in the `trading-bot` folder (which contains `download_data.py`). This is a large build: work section by section, commit after each, and write progress notes to `PROGRESS.md` so the work can resume after any interruption. Create a Python virtual environment first and install: pandas numpy requests lightgbm scikit-learn optuna shap hmmlearn torch websockets matplotlib pyarrow. Use parquet for all derived datasets.

---

## 1. Data

- Run `download_data.py` as-is. It is already configured for **ETHUSDT and BTCUSDT**, **5m and 1m** candles, full Binance USDT-M perpetual history (`DAYS=2600`; ETHUSDT perps start Nov 2019), and funding-rate history. Files land in `data/klines/<SYMBOL>_5m.csv`, `data/klines/<SYMBOL>_1m.csv`, `data/funding/<SYMBOL>.csv`. Report candle count and earliest date for each file. Rerunning resumes; it does not re-download.
- **Trade-level data (aggTrades)** — this is very large (many GB per year). Download the **monthly** zips for the most recent **24 months only** from `https://data.binance.vision/data/futures/um/monthly/aggTrades/ETHUSDT/`. Stream each zip, build the derived bars and whale/absorption features, then discard the raw trades; never hold them in memory. For history older than 24 months, approximate activity bars and volume features from the 1m klines, and say so in the report.
- **Open interest and long/short ratios**: the public API only returns ~30 days, so download the daily zips from `https://data.binance.vision/data/futures/um/daily/metrics/ETHUSDT/` (and BTCUSDT): 5-minute open interest, top-trader long/short ratios, taker buy/sell ratios. This archive begins around late 2021; earlier bars get missing values, which LightGBM handles natively. Merge onto the 5m candles.
- **Liquidations**: no public history. Write an always-on recorder for the `<symbol>@forceOrder` websocket stream appending to `data/liquidations/`. In the backtest use funding rate, OI change and OI-vs-price divergence as the liquidation-pressure proxy and say so in the report.
- **Order-book recorder**: depth snapshots every 5m to `data/orderbook/`, for the next model version.
- **Daily external features**: ETH ETF net flows, exchange net-flows, on-chain (gas fees, active addresses, stablecoin supply on Ethereum, exchange reserves) from free public APIs; fear & greed index. Cache to `data/daily/`. If a source is unavailable, skip it and list it in the report; do not fabricate.
- **Event calendar**: `data/events.csv` with FOMC, CPI, monthly options expiry, US holidays. Create it from the known schedule.
- Resample 15m / 1h / 4h / 1d / 1w / 1M from the 5m data. Never fetch higher timeframes separately.
- **Data-quality guard**: detect bad prints, gaps and exchange outages; exclude flagged candles from training and log them.
- If any download URL has changed, check the parent directory listing on data.binance.vision and adapt; do not guess file names.

## 2. Bars

Build **activity bars** (volume bars and dollar bars) from aggTrades alongside the 5m time bars. Run the whole pipeline on both bar types and report which performs better; the bot may use either or ensemble them.

## 3. Master regime gate (rule-based, above all models)

Compute weekly/monthly regime by rule, not model: weekly close vs weekly 20 and 50 SMA; weekly Ichimoku cloud position; monthly higher-highs/higher-lows vs lower-highs/lower-lows; BTC's weekly regime as a modifier. Output **Bull / Bear / Neutral**. Bull → longs only, Bear → shorts only, Neutral → no trades. Every model inherits this. Log the regime on every candle.

**Early regime-flip detector**: a Hidden Markov Model on weekly returns and volatility that flags a likely regime transition. It advises (logged, shown in reports, available as a feature); it does not override the gate.

**Cycle position**: months since the last BTC halving and the phase of the four-year cycle, as features.

## 4. Feature engineering (~500+ features per bar)

Compute each family at several settings across 5m / 15m / 1h / 4h / 1d, plus weekly and monthly structure context:

- **Trend**: MACD (line, signal, histogram, histogram slope), Ichimoku (all five lines, cloud thickness, price vs cloud, TK cross, Kumo twist), Supertrend, ADX/DI, EMA/SMA stacks and slopes, Parabolic SAR.
- **Momentum**: RSI, Stochastic, CCI, ROC, Williams %R, MFI.
- **Volatility**: ATR, Bollinger (width, %B), Keltner, Donchian, realised volatility over several windows, squeeze flag (Bollinger inside Keltner).
- **Volume**: OBV, CMF, VWAP (session and anchored), volume z-score, taker buy/sell delta and ratio, trade count, volume-at-price.
- **Market structure**: swing highs/lows (several lookbacks), HH/HL/LH/LL sequence state, break of structure and change of character flags, Fibonacci retracement/extension distances.
- **Trend lines**: from swing highs/lows, fit candidate lines through swing pairs and keep those with the most touches and fewest violations; rising support, falling resistance and parallel channels on every timeframe from 5m to weekly and monthly. Per line, per bar: distance in ATR units, slope, touch count, age, break and volume-confirmed break, retest from the far side, confluence with S/R and Ichimoku levels.
- **Support / resistance**: cluster swing highs/lows across all timeframes into scored bands; add volume-profile high-volume nodes, previous day/week/month highs, lows and closes, round-number levels, anchored VWAPs from major swings. Per level, per bar: distance in ATR units above and below, strength (touches, volume, timeframe agreement), age and last-retest recency, role-flip flag, last-reaction magnitude, confluence count with trend lines, Ichimoku and round numbers.
- **Liquidity sweeps / stop hunts**: wick through a level or trend line followed by a close back on the original side; flag the sweep, its depth in ATR and the reclaim.
- **Divergences**: explicit regular and hidden divergence flags between price and MACD, RSI, OBV.
- **Whale prints and absorption** (from aggTrades): unusually large single trades, clusters of them, and heavy volume with no price progress at a level.
- **Weekly / monthly structure context** (features, not targets): weekly and monthly swing points, position inside the current weekly and monthly range, monthly trend direction, distance to weekly/monthly S/R, weekly Ichimoku state.
- **BTC context**: BTC's trend/momentum/structure set at 1h/4h/1d, BTC weekly regime, ETH/BTC ratio and its trend, rolling ETH–BTC correlation and beta. **Lead-lag mining**: test whether BTC, the spot-vs-perp basis, or OI leads ETH by 1–30 bars; keep and use only leads that survive walk-forward.
- **Perp data**: funding rate (current, change, z-score), open interest (level, change, OI-vs-price divergence), long/short ratios, taker buy/sell ratio, hours to next funding settlement.
- **Sessions and clock**: Asia / London / New York session flags and time-since-open, weekend flag, funding settlement windows (00/08/16 UTC), day of week, hour of day, options-expiry proximity. **Calendar heatmap**: return, range and volume by day-of-week × hour across the full history; expose as features and derive data-justified no-trade windows if any period is consistently slow or negative — test the weekend hypothesis explicitly and report it.
- **Event proximity**: bars to/from each event in `events.csv`; measure each event's effect and report.
- **Daily external features** from §1, forward-filled onto the bars.
- **Volatility forecast**: a separate model predicting whether a large move (in ATR terms) occurs within the next N bars, without direction. Its output is a feature and a readiness flag.
- **Position-aware features** (for the exit model): time in trade, unrealised P&L vs max adverse excursion, distance to the active trend line / S&R.

## 5. Alpha mining — the bot invents indicators (under strict control)

Genetic search over formulas combining raw price, volume and perp data. Rules:
- Evaluate every candidate walk-forward only; apply a multiple-testing correction (e.g. deflated Sharpe / Bonferroni-style threshold scaled to the number tested). A candidate must beat luck, not zero.
- **Novelty filter**: discard any candidate with |correlation| > 0.7 to an existing feature.
- **Quarantine**: survivors enter as shadow features for a fixed period and are promoted only if they keep working on unseen data.
- **Readable ledger** `alphas.md`: each invented indicator as a plain formula with its full performance history. Nothing unreadable enters the model.
- **Hard cap**: at most 20 active; a new entrant displaces the weakest.
- **Kill on decay**: retire automatically when out-of-sample performance decays, and log the retirement.

## 6. Labels

Triple-barrier per horizon — **5m-scale, 1h, 4h, 1d**: which is hit first, profit target, exit level, or the time limit? Label = up-win / down-win / timeout. Two barrier modes, report both:
- **Mode A (fixed)**: exit level = 10% of margin at the configured leverage; target = 20% of margin (2:1).
- **Mode B (volatility-scaled)**: barriers sized to each horizon's ATR, keeping 2:1.
All labels net of taker fees both sides and funding.

## 7. Models

- **Primary**: LightGBM, one per horizon (5m, 1h, 4h, 1d), trained separately per regime (Bull set, Bear set), long and short. Probability output; act only above a tuned confidence threshold. Report calibration. Handle class imbalance. Prune features by importance and retrain.
- **Sequence model**: a small transformer or LSTM on raw bar sequences (last 200 bars), same labels. **Ensemble** with LightGBM; report each alone and combined.
- **Meta-labelling**: a second LightGBM trained on the primary ensemble's own out-of-sample errors, predicting when it is wrong; it vetoes low-confidence trades.
- **Learned horizon stacking**: keep the regime gate as a hard rule; within it, a stacking model learns how to weigh the four horizon probabilities. Report the hard-rule stack vs the learned stack.
- **"Last 50 times" retrieval**: for every entry, find the most similar historical setups (same regime, structure and indicator state, nearest-neighbour in feature space) and record what happened next; log it per trade and expose it as a feature.
- **Adaptive thresholds**: per regime and per session, tuned in walk-forward.
- **Automated tuning**: Optuna over thresholds, windows and model settings with the walk-forward result as the objective; keep only robust optima (flat neighbourhoods, not spikes).
- **Signal deduplication**: repeated fires on the same thesis within a short window are treated as one position, not several.

## 8. Decision rule

1. Master regime gate sets the allowed direction.
2. Within it, the horizon stack (hard-rule version and learned version, reported separately) must agree.
3. The 5m model fires the entry above its confidence threshold.
4. Meta-labeller may veto.

## 9. Position management — simulate all, we choose after

**Primary run: no-stop diagnostic mode.** No protective exit; trades close only on target, horizon expiry, or model reversal (liquidation still modelled exactly as the exchange would apply it). Classify every trade as right-immediately / wrong-then-recovered / wrong-and-stayed-wrong. Log max adverse and favourable excursion in ATR, time to recovery, and the full feature snapshot at entry. Cluster the wrong trades by regime, session, hour, nearby S/R and trend lines, and indicator state; report the common patterns. Report the MAE distribution of recovered trades.

Then run exit variants on identical entries and report each:
- **A** Fixed target / exit (per the label barriers)
- **B** Partial take-profit at 1:1, remainder trails
- **C** Structure trail — behind the last swing or the active trend line
- **D** Time exit at horizon expiry
- **E** Model-driven exit — a separate model predicts continue-vs-reverse

**Sizing**: config parameter. Sweep 100% / 50% / 25% of available margin per trade at 5X and 7X, and add **confidence-scaled sizing** (size from calibrated probability) as a variant. Report the full grid.

## 10. Execution realism (non-negotiable)

Taker fees both sides (and maker where the execution engine uses post-only orders), funding every 8h, slippage, liquidation via maintenance margin, exchange minimum notional, **stop-first fills** when a bar breaches both target and exit. Never fill at the close for an intra-bar event.

## 11. Validation

- Walk-forward with purging and embargo (overlapping labels never leak).
- **Simulate the retraining schedule**: monthly retrain on a rolling window with **champion/challenger** promotion — a new model is deployed only if it beats the incumbent on the most recent out-of-sample data.
- Final 6 months fully out-of-sample, untouched until the final report.
- **Stress replays**: March 2020, the LUNA and FTX weeks of 2022, the Aug 2025 top → 2026 decline. Report the bot's behaviour in each.
- **Monte Carlo**: reshuffle the trade sequence 10,000 times; report the distribution of final equity and max drawdown.
- Flag overfitting: in-sample vs out-of-sample gap, importance concentrated in few noisy features, results that vanish when a threshold moves slightly, alpha-mining survivors that fail quarantine.

## 12. Live-bot autonomy (build now, used after the sim)

- **Drift detection**: track live hit-rate and calibration against the backtest's band; pause and retrain automatically when outside it.
- **State recovery and reconciliation**: persist every order, trade and position; on restart, reconcile against Binance and correct any difference.
- **Execution engine**: post-only maker orders wherever possible, websocket reconnection, rate-limit handling, partial-fill handling.
- **Shadow mode**: live signals with simulated fills against real prices, auto-compared to the backtest, before any real money.
- **Daily digest**: one message per day (trades, P&L, regime, drift/retrain events). No per-trade alerts.
- Designed to run on a VPS near Binance (Tokyo/Singapore).

## 13. Reporting — start from $10

Per horizon, per regime, per bar type, per model (LightGBM / sequence / ensemble): accuracy vs baseline, precision at threshold, calibration, top-30 feature importance, contribution of invented alphas.

Full stacked backtest per exit variant and per sizing/leverage cell: total return, max drawdown, win rate, profit factor, average win/loss, trade count, in-sample vs out-of-sample.

Tag every trade with-trend or counter-trend; report performance and consecutive-exit-hit counts for each. Run a control with the regime gate disabled to quantify what it saves. Report the calendar heatmap and the weekend result. Report lead-lag findings, event effects, and HMM flip warnings vs actual flips.

Log top-5 SHAP reasons and the "last 50 times" outcome per trade.

**Funnel report**: for the full history, count candles entering the funnel and surviving each stage in order — data-quality guard, regime gate, calendar windows, volatility forecast, higher-horizon agreement, 5m threshold, meta-labeller veto, deduplication, entry — and report the win rate of the survivors at each stage, so it is clear which gate does the real work.

Write `README.md` (how to run everything), `results.md` (all of the above, with the three most important findings in plain language at the top), and `alphas.md`.

## 14. Multi-coin prep (method only, for phase two)

Rank Binance USDT perps by liquidity and spread; cluster by return correlation so the portfolio never holds many copies of one trade; allocate capital across clusters. Write the method; do not run it yet.
