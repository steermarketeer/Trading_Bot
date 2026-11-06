# Trading system architecture (ETH perpetuals; paper first, live-ready)

Goal: a simple system that takes correct decisions, built to stop the three failure types seen in the journal:
**false breakouts (traps), stops placed inside liquidity, and missed reversals at key pivots** (the short that should
have been taken at 27 Mar 2023, 16 Dec 2024, 7 Jun 2024).

Every rule below carries an evidence tag from the audited studies (25 audit rounds, zero open result-impacting issues):

- **PROVEN**: passed the project's test (p < 0.01 and the holdout agrees) or is the research-chosen strategy rule.
- **MARKER**: a strong statistical marker on our trades but not a tradeable rule by itself (e.g. known only after entry).
- **LEAD**: pointed the right way in one period only, or post hoc; to watch, not to trade.
- **NONE**: tested and found to be a coin flip / lost after costs. Kept out of the decision path.
- **UNTESTED**: not yet measured; may enter only after the same fair test.

Reports: `reports/fixes.md`, `selfreview.md`, `indicator_deep.md`, `bollinger.md`, `bb_pause_*.md`, `trendline_*.md`,
`three_failures.md`, `confluence.md`, `journal_ml.md`, `manager.md`. Definitions: `docs/trading_definitions.md`.

## Module 1: strategy architecture and edge

### 1.1 The edge, as measured
The research-chosen strategy (`bot/live/v3.py` + the journal filters + the 0.786 bounce stop):
2022 - Oct 2025 **129 trades, 59% win, +0.79R, account 16.9x, worst drop 16%**; holdout (Nov 2025 on) 33 trades, 64%,
+1.02R. It is a **price-action strategy**: structure, levels, liquidity, the candle close. Indicators are context.

What single indicators add on top of it: nothing measurable (`confluence.md`, `learned.md`). The flow features the
brief asks for (CVD trend / divergence, VWAP day / week, volume-profile POC and LVN) already exist in
`bot/study/flow.py` and were inputs to the journal ML: top-ranked by the model, yet the model had **no out-of-sample
edge** (`journal_ml.md`). So they are *not* the fakeout fix. The fakeout fix in our data is the close rule (1.3).

### 1.2 Setups (entries), with formulas
Notation: `ATR_tf` = Wilder ATR(14) of the setup's timeframe; `d` = +1 long / -1 short; everything from **closed** candles.

**Breakout** (2h / 4h / 1D; zone break, range break, trendline break, BOS, liquidity run), PROVEN (strategy rule):

```
level L (zone edge / range extreme / swing);  signal candle j closes beyond it:
    d * (C_j - L) >= max(0.25 * ATR_tf,  0.01 * L  if tf == 1D)
certainty(j) >= 7                        # frozen scoring model, bot/live/v3.py
stop_pct >= 0.006;  ATR% >= q20(tf)      # not the quietest 20% of the timeframe
clean risk zone: no confirmed swing (1h, own tf) between entry and stop;
                 no equal-high/low pool within 0.5 ATR of the stop
entry = O_{j+1} (next open after the close);  stop S = L_j (long) / H_j (short) beyond the pool;
target T = entry + d * 2 * |entry - S|
```

**1D bounce** (3 : 1), PROVEN (strategy rule):

```
strong daily zone Z (3+ swings or a weekly swing) tested >= 4 times; touch candle t with bounce volume >= 0.8 x touch
confirmed by the next daily close on the bounce side;  entry = next open
stop S = F_0.786 of the 1h leg - d * 0.001 * entry     # the 0.786 REPLACES the v3.1 stop (tighter in 37 of 62
                                                        # bounces); v3.1 stop only if the 0.786 is not beyond the entry
                                                        # PROVEN: +0.71 -> +0.79R, holdout +0.68 -> +1.02R
target T = entry + d * 3 * |entry - S|
```

**Journal filters** (skip the trade), PROVEN (chosen on 2022 - 25, hold in the holdout):
- an untaken **double / triple top** (equal highs within max(0.25%, 0.5 ATR)) between entry and target;
- **3+ rejections** at the resistance ahead (touch within 0.25 ATR, close back by >= 0.25 ATR).

**Breaking-candle quality**, PROVEN in general (`indicator_deep`: 4h breakout on >= 2x volume 58% vs 46%; close > 1 ATR
beyond 62%), but as a strategy filter it only helped in the holdout, so it is logged as context, not enforced:
```
vol_j >= 2 * mean(vol_{j-20..j-1});   d * (C_j - L) >= 1 * ATR_tf
```

### 1.3 Anti-fakeout: the close rule (the actual fix for traps)
- MARKER: trades whose **first 4h close after entry is back against the entry** win 29% vs 59% (`selfreview.md`).
  Known only after entry, so it becomes the **early-exit rule**: if the first 4h close after entry is on the wrong side
  of the entry price, exit at the next open (tested as "failure exit": raises win % to 67 - 72%, lowers avg R to
  +0.37; see 2.4 before adopting).
- MARKER: a **ceiling (resistance / untaken 4h high) between entry and target** → 43% vs 68% win. Already enforced
  through the journal filters for double tops; a general "liquidity target" (first untaken HTF swing >= 1.2R) replaces
  a fixed ratio only when it is at least as far as 2R - tested, not better (`bounce_fix.md`), so targets stay fixed and
  the ceiling is a *skip* when it is under 1.2R away (the 22 May 2024 lesson).
- NONE: entering on a trendline retest (`trendline_trade.md`: -0.13R per trade on 4h); the squeeze breakout as a
  signal (46 - 47%); CVD / VWAP breakouts as signals (no edge in `journal_ml.md`).

### 1.4 Catching the missed reversals: the top-failure setup (UNTESTED as a trade; three journal examples)
The misses share one shape: **a failure at a higher-timeframe pool, then a close below the failure structure's low**.
Two sub-shapes (definitions in `docs/trading_definitions.md` sections 2 and 9):
```
HTF pool P = an untaken daily / weekly swing high, or daily equal highs (buy-side liquidity)
(a) sweep (SFP):     H_j > P and C_j < P                                   # wick through the pool, closes back below
(b) failed pushes:   price within 0.5 ATR of P without a close above it, 2+ pushes with lower highs
trigger:  the first 4h close below the lowest low of the failure structure (the neckline)
confirm:  the next close of the higher timeframe (1D) also below the neckline
entry = next open after the trigger (or the confirmation); stop = the structure's high * 1.001;
target = the first untaken swing low >= 1.2R below, else 2R
```
Examples: 16 Dec 2024 (a), the 4,110 wick over the 4,099 top, close 3,985 → 3,100; 7 Jun 2024 (b), failed pushes
3,980 / 3,934 / 3,892 under 4,099, close 3,680 below the 3,705 pullback low → 2,800; 27 Mar 2023 (b on the 1h), three
pushes at 1,765 - 1,770 under the 1,782 / 1,800 highs, the 13:00 close below the push low → 1,684. The plain "three
failures anywhere" version is a coin flip (`three_failures.md`); what these have in common is the **HTF pool**. Built
and tested step by step: detector first (shown on the three dates), then the fair test on six coins, then the trade test.

### 1.5 Regime filter
- PROVEN (strategy rule): skip when ATR% is in the bottom 20% of the timeframe's research distribution.
- LEAD: volatility shock (signal candle >= 2.5 ATR) - no edge in our trades; the 27 Mar 2023 "wait it out" is judgment.
- NONE as a signal, LEAD as context: squeeze (BandWidth in the lowest 20% of 120) → the breakout is often a head
  fake; a bulge (BandWidth in the top 20%) → continuation (`bollinger.md` 62% vs 47%; expanding bands alone: no edge). Used as a context flag in logs.
- Donchian / Bollinger "squeeze release" as an entry: UNTESTED; add to the fair-test queue, not to the engine.

### 1.6 Patterns
Implemented: double / triple tops and bottoms (`bot/study/defs.py`, PROVEN as a filter), head & shoulders and
triangles (`bot/study/patterns.py`, UNTESTED as trades). W bottoms = double bottoms. Next: the fair test on all six
coins for H&S / inverse H&S neckline closes, then the bar-by-bar trade test.

## Module 2: risk and money management (`bot/live/risk.py`)

```
risk fraction  r = 0.02 (breakout, bounce), 0.04 (A+ breakout)          # PROVEN (strategy rule)
stop distance  Δ = |entry - S|  (price-action stop; never a fixed % or ATR multiple)
quantity       q = r * E / Δ                                               # fixed-fractional, volatility-adaptive via Δ
leverage cap   q * entry <= 5 * E   (then q is cut)                        # PROVEN (strategy rule)
Kelly check    f* = p - (1 - p) / b   with p = 0.59, b = avg win / avg loss = 2.08 / 1.06 ≈ 2.0  →  f* ≈ 0.38
               we use ~1/20 Kelly: p on 162 trades is uncertain by ±8 points, and 1/4 Kelly would still be ~10%
daily stop     halt new entries when (realised + unrealised) loss today >= 4% of the day's opening equity; LATCHED
               until the day rolls (a recovery during the day does not re-enable entries)
weekly stop    the same at 8% of the week's opening equity, an independent latch cleared only by the week roll
exposure       sum of open notional <= 5 * E;  one position per move (same candle + direction deduplicated)
VaR (1 day)    VaR_99 = Σ notional_i * 2.326 * σ_daily,  σ_daily ≈ ATR_1D / price;  cap VaR_99 at 35% of E (= the 5x
               cap at 3% volatility; in higher volatility it bites first and cuts the size, never below 25% of plan)
trailing stop  Chandelier: S_t = max(S_{t-1}, HH_n - 3 * ATR_1D) for longs (mirror for shorts), armed only after
               the trade reached +1R.  UNTESTED on our trades; the evidence so far says fixed targets beat early
               exits (failure exit: win 72% but avg R +0.37 vs +0.83; the ML manager found no exit that beats holding).
               It ships OFF and is tested before it is switched on.
```

## Module 3: system architecture (`bot/live/`)

```
DataHandler       bot/refresh.py + bot/data.py (REST klines, funding, OI; retries) → async wrapper that emits a
                  BarEvent on each CLOSED 5m / 2h / 4h / 1D candle (close_time == next open; no partial bars)
StrategyEngine    bot/live/v3.py generate_signals on closed candles → Signal(setup, side, entry, stop, target, tf,
                  context flags: breaking-candle quality, ceiling, squeeze/bulge, 4h-close confirmation)
RiskManager       bot/live/risk.py: size, limits, daily/weekly stops, exposure, VaR, (Chandelier, off)
ExecutionHandler  bot/live/execution.py: PaperExecution (5m-candle fills with the backtests' cost model: taker 0.04% +
                  5 bps slippage, limit targets need 0.02% through, stop before target, the 60-candle time exit, funding
                  at 00/08/16 UTC) and a Binance adapter behind a flag (post-only limit at the next open, market for the
                  unfilled remainder after N seconds, the real fill price read back, the stop placed at once or the
                  position closed; retries with backoff)
CircuitBreaker    bot/live/breaker.py: stale data, API errors, flash move, kill-switch file → HALT / FLATTEN
```
One engine for backtest and shadow stays the law (`CLAUDE.md`): the live loop replays the same functions on the
same closed candles, so paper results are comparable with the backtests to within 0.002R per trade (funding and the 60-candle time exit
are charged when the live loop calls apply_funding / passes expires_at, in the order stated in `execution.py`).

## Module 4: backtesting and anti-overfitting (in force since the start)
- No look-ahead: every detector uses candles closed at the decision time; swings count only once confirmed
  (`cf <= last closed`); the cloud / weekly / daily contexts use the last *closed* higher-tf candle; entries at the next
  open; 25 audit rounds specifically hunted look-ahead (and found and fixed it twice).
- Research 2020/2022 - Oct 2025, **holdout Nov 2025 on, never used to choose**. Walk-forward by year with a 62-day
  gap for every ML. Rules chosen by t-score with >= 60 trades and >= 3 of 4 good years.
- Significance: time-shifted copies (400) for event studies; calendar-month block bootstrap for multi-coin tests;
  Benjamini-Hochberg across the conditions tested; geometry controls (same distance to target / failure level).
- Monte Carlo for the live plan: (a) block bootstrap of months → distribution of yearly return and max drawdown;
  (b) trade-order reshuffles → the drawdown you must be able to sit through (to be added to `reports/fixes.md`).
- Metrics (per year and holdout): win %, avg R, profit factor, account multiple, max drawdown (closed and
  mark-to-market), Sharpe = mean(daily r) / sd(daily r) * sqrt(365), Sortino (downside sd), Calmar = CAGR / max DD.

## Module 5: production and fail-safes
- Infrastructure: one small cloud VM (2 vCPU) is enough for one symbol on 5m candles; data in parquet (today) with
  TimescaleDB optional later; Redis is not needed at this cadence. Secrets only in the environment (never in the
  repo or chat); Binance keys trade-only, no withdrawals, IP-restricted. Paper mode is the default; live needs an
  explicit `LIVE=1` and a signed config fingerprint.
- Circuit breaker (`bot/live/breaker.py`): trips to HALT (no new entries) on stale data (>= 2 missed 5m candles) or
  3 API errors in 5 minutes (the daily / weekly stops are latched in the RiskManager and clear at the roll, not here); trips to FLATTEN (close everything at market) on a flash move
  (5m range > 6 x ATR_5m or price gap > 3%), a kill-switch file, or a lost heartbeat for 3 minutes. Manual reset only.

## Build order (each step: code → tests → audit → shadow)
1. `bot/live/risk.py`, `bot/live/breaker.py`, `bot/live/execution.py` (paper) with unit tests - done in this commit.
2. The failure-to-short setup (1.4): fair test on six coins, then the trade test.
3. Early-exit rule (1.3) decision: adopt or not, on 2022 - 25 only.
4. Live loop (`bot/live/run.py`): closed-candle events → v3.1 signals → RiskManager → PaperExecution; shadow for weeks.
5. Monte Carlo + metrics report; then the Binance adapter on testnet.
