# Strategy v2 failures: liquidity vs indicators

Liquidity measured at entry from swings already confirmed (1h + the trade's timeframe, last 100 candles). Win % after costs. Research 2022 - Oct 2025, holdout Nov 2025 on.

## research: 602 trades, 336 losses

- **36% of losses were stop hunts**: stopped out, then price still reached our target.
- **54% were wick stops**: the candle that hit our stop closed back on our side.

### Liquidity at entry

| liquidity condition | trades with it | win % with | win % without | avg R with | avg R without | losses that were stop hunts |
|---|---|---|---|---|---|---|
| swing liquidity inside our risk zone | 360 | 37% | 55% | +0.26 | +0.54 | 36% |
| equal highs/lows (pool) near our stop | 289 | 35% | 53% | +0.19 | +0.54 | 34% |
| round number near our stop | 427 | 41% | 51% | +0.33 | +0.48 | 36% |
| untaken liquidity between entry and target | 396 | 37% | 58% | +0.21 | +0.68 | 38% |

### Indicators (for comparison: how much they separate winners from losers)

| indicator (present / warning) | trades | win % when present | win % when not | gap |
|---|---|---|---|---|
| m_1h_rsi_ext | 282 | 56% | 34% | +22 pts |
| m_2h_climax | 218 | 58% | 36% | +21 pts |
| n_btc_4h | 554 | 46% | 25% | +21 pts |
| m_4h_supertrend | 460 | 48% | 32% | +15 pts |
| m_4h_rsi_ext | 175 | 52% | 41% | +11 pts |
| n_squeeze | 298 | 39% | 49% | -10 pts |
| m_6h_macd | 528 | 45% | 35% | +10 pts |
| m_1D_trend | 403 | 42% | 48% | -5 pts |
| m_1W_trend | 335 | 42% | 47% | -5 pts |
| m_6h_macd_fade | 78 | 45% | 44% | +1 pts |

### Fix: stop placed beyond the nearby liquidity (target = same R multiple of the new risk)

| setup | trades | stops moved | win % now | win % with wider stop | avg R now | avg R wider stop |
|---|---|---|---|---|---|---|
| 1D bounce | 275 | 97% | 35% | 37% | +0.27 | +0.30 |
| A+ breakout | 182 | 76% | 58% | 53% | +0.64 | +0.47 |
| breakout | 145 | 80% | 44% | 43% | +0.22 | +0.16 |
| ALL | 602 | 87% | 44% | 43% | +0.37 | +0.32 |

## holdout: 123 trades, 64 losses

- **31% of losses were stop hunts**: stopped out, then price still reached our target.
- **50% were wick stops**: the candle that hit our stop closed back on our side.

### Liquidity at entry

| liquidity condition | trades with it | win % with | win % without | avg R with | avg R without | losses that were stop hunts |
|---|---|---|---|---|---|---|
| swing liquidity inside our risk zone | 69 | 38% | 61% | +0.28 | +0.73 | 28% |
| equal highs/lows (pool) near our stop | 58 | 36% | 58% | +0.20 | +0.72 | 22% |
| round number near our stop | 94 | 47% | 52% | +0.47 | +0.52 | 22% |
| untaken liquidity between entry and target | 80 | 42% | 58% | +0.39 | +0.64 | 28% |

### Indicators (for comparison: how much they separate winners from losers)

| indicator (present / warning) | trades | win % when present | win % when not | gap |
|---|---|---|---|---|
| m_1h_rsi_ext | 63 | 60% | 35% | +25 pts |
| m_2h_climax | 59 | 58% | 39% | +19 pts |
| m_4h_rsi_ext | 38 | 61% | 42% | +18 pts |
| m_1W_trend | 50 | 58% | 41% | +17 pts |
| m_6h_macd | 111 | 47% | 58% | -11 pts |
| m_6h_macd_fade | 23 | 39% | 50% | -11 pts |
| n_squeeze | 62 | 45% | 51% | -6 pts |
| m_1D_trend | 74 | 49% | 47% | +2 pts |
| m_4h_supertrend | 91 | 48% | 47% | +1 pts |

### Fix: stop placed beyond the nearby liquidity (target = same R multiple of the new risk)

| setup | trades | stops moved | win % now | win % with wider stop | avg R now | avg R wider stop |
|---|---|---|---|---|---|---|
| 1D bounce | 61 | 98% | 39% | 43% | +0.36 | +0.37 |
| A+ breakout | 41 | 66% | 61% | 49% | +0.74 | +0.38 |
| breakout | 21 | 81% | 48% | 48% | +0.32 | +0.27 |
| ALL | 123 | 85% | 48% | 46% | +0.48 | +0.36 |

