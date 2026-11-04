# 2:1 fixes and the combined strategy

All numbers after market-order costs, every trade replayed on 5-minute candles. **win %** = trades that ended in profit. Research = up to Oct 2025 (scored out-of-sample, 2022-25); holdout = Nov 2025 onward.

## 1. Fixing 2:1 breakouts (certainty >= 7, 2h / 4h / 1D)

F1 = stop at least 0.6% away · F2 = not the quietest 20% of markets · F3 = daily trend not against · F4 = entry at least 0.25 ATR beyond the broken level.

| fix | period | trades | trades/wk | win % at 2:1 | avg R 2:1 | win % half@1:1+2:1 | avg R half |
|---|---|---|---|---|---|---|---|
| no fix | research | 709 | 3.6 | 44% | +0.18 | 61% | +0.17 |
| no fix | holdout | 117 | 2.4 | 46% | +0.22 | 61% | +0.14 |
| F1 stop >= 0.6% | research | 681 | 3.4 | 44% | +0.20 | 61% | +0.18 |
| F1 stop >= 0.6% | holdout | 111 | 2.3 | 47% | +0.25 | 61% | +0.17 |
| F2 volatility | research | 568 | 2.9 | 43% | +0.20 | 61% | +0.19 |
| F2 volatility | holdout | 95 | 2.0 | 47% | +0.27 | 62% | +0.17 |
| F3 daily trend | research | 476 | 2.4 | 42% | +0.14 | 60% | +0.14 |
| F3 daily trend | holdout | 58 | 1.3 | 47% | +0.30 | 52% | +0.05 |
| F4 real breakout | research | 601 | 3.0 | 44% | +0.20 | 61% | +0.19 |
| F4 real breakout | holdout | 100 | 2.1 | 50% | +0.35 | 61% | +0.20 |
| F1 + F2 | research | 564 | 2.8 | 44% | +0.21 | 61% | +0.19 |
| F1 + F2 | holdout | 93 | 1.9 | 47% | +0.27 | 62% | +0.19 |
| F1 + F3 | research | 458 | 2.3 | 42% | +0.15 | 60% | +0.16 |
| F1 + F3 | holdout | 56 | 1.2 | 46% | +0.31 | 54% | +0.08 |
| F1 + F2 + F3 | research | 378 | 1.9 | 42% | +0.15 | 61% | +0.17 |
| F1 + F2 + F3 | holdout | 48 | 1.1 | 52% | +0.49 | 58% | +0.20 |
| all four | research | 319 | 1.6 | 42% | +0.15 | 62% | +0.20 |
| all four | holdout | 45 | 1.0 | 53% | +0.54 | 58% | +0.23 |

**Chosen on research (best avg R at 2:1 with >= 150 trades): F1 + F2.**

## 2. 1D level tested 4+ times: bounce trade

| period | trades | win % 1:1 | win % 2:1 | win % 3:1 | avg R 1:1 | avg R 2:1 | avg R 3:1 |
|---|---|---|---|---|---|---|---|
| research | 334 | 57% | 41% | 37% | +0.11 | +0.18 | +0.35 |
| holdout | 61 | 59% | 43% | 39% | +0.14 | +0.20 | +0.36 |

## 3. Combined strategy: fixed 2:1 breakouts + 1D 4th-test bounces (3:1)

### Win % per trade, year by year

| year | setup | trades | win % | avg R after costs |
|---|---|---|---|---|
| 2022 | 1D 4th-test bounce (3:1) | 50 | 46% | +0.73 |
| 2022 | COMBINED | 186 | 50% | +0.54 |
| 2022 | breakout (2:1) | 136 | 51% | +0.48 |
| 2023 | 1D 4th-test bounce (3:1) | 99 | 34% | +0.18 |
| 2023 | COMBINED | 260 | 37% | +0.10 |
| 2023 | breakout (2:1) | 161 | 39% | +0.06 |
| 2024 | 1D 4th-test bounce (3:1) | 75 | 33% | +0.22 |
| 2024 | COMBINED | 172 | 35% | +0.08 |
| 2024 | breakout (2:1) | 97 | 36% | -0.03 |
| 2025 | 1D 4th-test bounce (3:1) | 51 | 29% | +0.07 |
| 2025 | COMBINED | 221 | 43% | +0.22 |
| 2025 | breakout (2:1) | 170 | 46% | +0.27 |
| holdout | 1D 4th-test bounce (3:1) | 61 | 39% | +0.36 |
| holdout | COMBINED | 154 | 44% | +0.30 |
| holdout | breakout (2:1) | 93 | 47% | +0.27 |

### Account (compounding, positions can overlap, leverage cap 5x)

| period | risk / trade | trades | end equity | winning weeks | median week | avg week | weeks >= +20% | max drawdown |
|---|---|---|---|---|---|---|---|---|
| 2022-25 | 2% | 839 | 12.32x | 49% | +0.0% | +1.8% | 8% | -57% |
| 2022-25 | 3% | 839 | 19.15x | 49% | +0.0% | +2.6% | 14% | -77% |
| 2022-25 | 5% | 839 | 10.79x | 49% | +0.0% | +4.2% | 19% | -96% |
| holdout | 2% | 154 | 2.07x | 45% | +0.0% | +1.7% | 2% | -27% |
| holdout | 3% | 154 | 2.63x | 45% | +0.0% | +2.7% | 8% | -39% |
| holdout | 5% | 154 | 3.88x | 45% | +0.0% | +5.1% | 12% | -61% |

