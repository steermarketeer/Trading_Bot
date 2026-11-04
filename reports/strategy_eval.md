# 2:1 fixes and the combined strategy

All numbers after market-order costs, every trade replayed on 5-minute candles. **win %** = trades that ended in profit. Research = up to Oct 2025 (scored out-of-sample, 2022-25); holdout = Nov 2025 onward.

## 1. Fixing 2:1 breakouts (certainty >= 7, 2h / 4h / 1D)

F1 = stop at least 0.6% away · F2 = not the quietest 20% of markets · F3 = daily trend not against · F4 = entry at least 0.25 ATR beyond the broken level.

| fix | period | trades | trades/wk | win % at 2:1 | avg R 2:1 | win % half@1:1+2:1 | avg R half |
|---|---|---|---|---|---|---|---|
| no fix | research | 704 | 3.5 | 44% | +0.20 | 61% | +0.18 |
| no fix | holdout | 114 | 2.4 | 46% | +0.20 | 60% | +0.11 |
| F1 stop >= 0.6% | research | 676 | 3.4 | 44% | +0.21 | 61% | +0.19 |
| F1 stop >= 0.6% | holdout | 108 | 2.2 | 46% | +0.23 | 60% | +0.14 |
| F2 volatility | research | 563 | 2.8 | 44% | +0.22 | 61% | +0.20 |
| F2 volatility | holdout | 92 | 1.9 | 47% | +0.25 | 61% | +0.15 |
| F3 daily trend | research | 472 | 2.4 | 43% | +0.15 | 61% | +0.16 |
| F3 daily trend | holdout | 57 | 1.3 | 44% | +0.22 | 49% | -0.02 |
| F4 real breakout | research | 598 | 3.0 | 44% | +0.22 | 62% | +0.21 |
| F4 real breakout | holdout | 97 | 2.0 | 49% | +0.34 | 60% | +0.18 |
| F1 + F2 | research | 559 | 2.8 | 44% | +0.22 | 61% | +0.21 |
| F1 + F2 | holdout | 90 | 1.9 | 47% | +0.25 | 61% | +0.16 |
| F1 + F3 | research | 454 | 2.3 | 43% | +0.16 | 61% | +0.17 |
| F1 + F3 | holdout | 55 | 1.2 | 44% | +0.22 | 51% | +0.01 |
| F1 + F2 + F3 | research | 374 | 1.9 | 42% | +0.16 | 61% | +0.19 |
| F1 + F2 + F3 | holdout | 47 | 1.0 | 49% | +0.39 | 55% | +0.12 |
| all four | research | 318 | 1.6 | 42% | +0.17 | 63% | +0.22 |
| all four | holdout | 44 | 1.0 | 50% | +0.44 | 55% | +0.14 |

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
| 2022 | COMBINED | 183 | 52% | +0.60 |
| 2022 | breakout (2:1) | 133 | 54% | +0.56 |
| 2023 | 1D 4th-test bounce (3:1) | 99 | 34% | +0.18 |
| 2023 | COMBINED | 260 | 37% | +0.10 |
| 2023 | breakout (2:1) | 161 | 39% | +0.06 |
| 2024 | 1D 4th-test bounce (3:1) | 75 | 33% | +0.22 |
| 2024 | COMBINED | 170 | 35% | +0.09 |
| 2024 | breakout (2:1) | 95 | 37% | -0.01 |
| 2025 | 1D 4th-test bounce (3:1) | 51 | 29% | +0.07 |
| 2025 | COMBINED | 221 | 42% | +0.21 |
| 2025 | breakout (2:1) | 170 | 46% | +0.25 |
| holdout | 1D 4th-test bounce (3:1) | 61 | 39% | +0.36 |
| holdout | COMBINED | 151 | 44% | +0.29 |
| holdout | breakout (2:1) | 90 | 47% | +0.25 |

### Account (compounding, positions can overlap, leverage cap 5x)

| period | risk / trade | trades | end equity | winning weeks | median week | avg week | weeks >= +20% | max drawdown |
|---|---|---|---|---|---|---|---|---|
| 2022-25 | 2% | 834 | 14.61x | 49% | +0.0% | +1.9% | 9% | -57% |
| 2022-25 | 3% | 834 | 24.81x | 49% | +0.0% | +2.8% | 13% | -76% |
| 2022-25 | 5% | 834 | 17.14x | 49% | +0.0% | +4.5% | 18% | -96% |
| holdout | 2% | 151 | 1.97x | 43% | -0.2% | +1.6% | 2% | -27% |
| holdout | 3% | 151 | 2.45x | 43% | -0.4% | +2.5% | 8% | -39% |
| holdout | 5% | 151 | 3.46x | 43% | -0.7% | +4.8% | 12% | -61% |

