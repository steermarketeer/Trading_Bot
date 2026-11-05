# Combined score: main concepts + indicators -> certainty 1-10

Every trade gets a **certainty from 1 to 10** = the model's expected win probability at a 1R target x 10. The model weighs the main concepts first (which concept, confluence, structure, weekly/daily trend) and then the indicators that helped that kind of trade. **Every number below is out-of-sample:** each year (2022-2025) is scored by a model trained only on earlier years, and the holdout (from 2025-11-01) by the model trained on all research data. Win rates are before costs; avg R is after costs. At 1R the after-cost break-even is about 52% on 1D and 55% on 4h.

## Reversal trades (S/R zone bounce (confirmed), trendline bounce (confirmed), liquidity sweep (stop hunt) reversal, change of character (first reversal break))

### Is the certainty honest? (predicted vs actual)

A 6/10 trade should win about 60% of the time.

| certainty | trades 2022-25 | actual win @1R 2022-25 | holdout trades | actual win @1R holdout |
|---|---|---|---|---|
| 1/10 | 18 | 22% | 2 | 0% |
| 2/10 | 20 | 45% | 4 | 50% |
| 3/10 | 34 | 59% | 7 | 57% |
| 4/10 | 114 | 50% | 38 | 42% |
| 5/10 | 208 | 54% | 93 | 44% |
| 6/10 | 115 | 44% | 33 | 42% |
| 7/10 | 32 | 53% | 8 | 38% |
| 8/10 | 16 | 50% | 1 | 100% |
| 9/10 | 5 | 60% | 0 | - |

### Taking only confident trades

| rule | period | trades | trades/week | win @1R | win @1.5R | win @2R | avg R @1R after costs | avg R @2R after costs |
|---|---|---|---|---|---|---|---|---|
| all trades | 2022-25 | 562 | 3.9 | 50% | 40% | 33% | -0.05 | -0.04 |
| all trades | holdout | 186 | 3.9 | 44% | 35% | 31% | -0.18 | -0.07 |
| certainty >= 5 | 2022-25 | 376 | 2.6 | 51% | 40% | 34% | -0.03 | -0.01 |
| certainty >= 5 | holdout | 135 | 2.8 | 44% | 36% | 33% | -0.17 | -0.03 |
| certainty >= 6 | 2022-25 | 168 | 1.2 | 47% | 33% | 28% | -0.10 | -0.16 |
| certainty >= 6 | holdout | 42 | 0.9 | 43% | 36% | 33% | -0.19 | -0.00 |
| certainty >= 7 | 2022-25 | 53 | 0.4 | 53% | 32% | 26% | +0.00 | -0.16 |
| certainty >= 7 | holdout | 9 | 0.3 | 44% | 33% | 33% | -0.16 | +0.17 |

### Certainty >= 6, year by year

| year | trades | win @1R | win @2R | avg R @1R after costs |
|---|---|---|---|---|
| 2023 | 81 | 53% | 37% | -0.00 |
| 2024 | 55 | 33% | 9% | -0.39 |
| 2025 | 32 | 56% | 38% | +0.15 |
| holdout | 42 | 43% | 33% | -0.19 |

### What the score is made of (weights of the final model; + raises certainty, - lowers it)

| factor | weight |
|---|---|
| bounce candle volume | +0.30 |
| confluence: S/R zone bounce (confirmed) | +0.19 |
| daily trend with the trade | +0.16 |
| confluence: break of structure (continuation) | +0.15 |
| trendline touches | +0.11 |
| candle closed near our end | +0.10 |
| weekly trend (close vs EMA50) with the trade | +0.08 |
| volume divergence | +0.08 |
| number of concepts agreeing | +0.06 |
| chart structure with the trade | +0.05 |
| confluence: liquidity run (break of equal highs/lows) | +0.02 |
| confluence: trendline bounce (confirmed) | +0.02 |
| confluence: S/R zone breakout | +0.02 |
| daily chart (vs 4h) | +0.00 |
| concept: change of character (first reversal break) | -0.01 |
| distance from EMA200 (our side +) | -0.01 |
| confluence: change of character (first reversal break) | -0.02 |
| daily ADX < 20 (quiet market) | -0.03 |
| confluence: trendline break | -0.03 |
| volume into the event | -0.07 |
| weekly Supertrend with the trade | -0.10 |
| RSI divergence | -0.10 |
| concept: liquidity sweep (stop hunt) reversal | -0.11 |
| RSI in trade direction | -0.14 |
| confluence: liquidity sweep (stop hunt) reversal | -0.16 |
| event candle volume | -0.26 |
| concept: trendline bounce (confirmed) | -0.31 |

### Why do confident trades still lose? (certainty >= 6, 2022-25)

- 87 losses. **33% failed within 2 candles**; **36% went at least +0.5R our way first**; 0% gapped through the stop.

Biggest differences between winners and losers among these trades (gap in standard deviations):

| factor | avg for winners | avg for losers | gap |
|---|---|---|---|
| daily ADX < 20 (quiet market) | -0.27 | -0.44 | +0.36 |
| confluence: S/R zone breakout | 0.43 | 0.28 | +0.31 |
| bounce candle volume | 1.45 | 1.18 | +0.27 |
| confluence: trendline bounce (confirmed) | 0.20 | 0.11 | +0.25 |
| candle closed near our end | 0.74 | 0.69 | +0.25 |
| volume into the event | 0.99 | 0.89 | +0.24 |
| number of concepts agreeing | 1.51 | 1.20 | +0.23 |
| event candle volume | 1.42 | 1.23 | +0.20 |

## Breakout trades (S/R zone breakout, trendline break, liquidity run (break of equal highs/lows), break of structure (continuation), break of a swing in a range)

### Is the certainty honest? (predicted vs actual)

A 6/10 trade should win about 60% of the time.

| certainty | trades 2022-25 | actual win @1R 2022-25 | holdout trades | actual win @1R holdout |
|---|---|---|---|---|
| 2/10 | 14 | 43% | 0 | - |
| 3/10 | 60 | 57% | 7 | 57% |
| 4/10 | 131 | 54% | 55 | 49% |
| 5/10 | 157 | 50% | 75 | 53% |
| 6/10 | 116 | 51% | 55 | 45% |
| 7/10 | 58 | 52% | 6 | 83% |
| 8/10 | 45 | 62% | 2 | 50% |
| 9/10 | 14 | 29% | 0 | - |
| 10/10 | 6 | 33% | 0 | - |

### Taking only confident trades

| rule | period | trades | trades/week | win @1R | win @1.5R | win @2R | avg R @1R after costs | avg R @2R after costs |
|---|---|---|---|---|---|---|---|---|
| all trades | 2022-25 | 601 | 4.2 | 52% | 42% | 37% | -0.03 | +0.04 |
| all trades | holdout | 200 | 4.2 | 51% | 42% | 32% | -0.04 | -0.05 |
| certainty >= 5 | 2022-25 | 396 | 2.8 | 51% | 42% | 37% | -0.05 | +0.05 |
| certainty >= 5 | holdout | 138 | 2.9 | 51% | 42% | 33% | -0.04 | -0.02 |
| certainty >= 6 | 2022-25 | 239 | 1.7 | 51% | 41% | 37% | -0.04 | +0.04 |
| certainty >= 6 | holdout | 63 | 1.3 | 49% | 35% | 22% | -0.07 | -0.35 |
| certainty >= 7 | 2022-25 | 123 | 0.9 | 52% | 45% | 39% | -0.02 | +0.11 |
| certainty >= 7 | holdout | 8 | 0.3 | 75% | 50% | 0% | +0.45 | -0.74 |

### Certainty >= 6, year by year

| year | trades | win @1R | win @2R | avg R @1R after costs |
|---|---|---|---|---|
| 2023 | 102 | 48% | 33% | -0.12 |
| 2024 | 66 | 58% | 42% | +0.09 |
| 2025 | 71 | 51% | 37% | -0.03 |
| holdout | 63 | 49% | 22% | -0.07 |

### What the score is made of (weights of the final model; + raises certainty, - lowers it)

| factor | weight |
|---|---|
| trendline touches | +0.21 |
| Bollinger position our way | +0.17 |
| confluence: S/R zone bounce (confirmed) | +0.16 |
| confluence: trendline break | +0.13 |
| concept: liquidity run (break of equal highs/lows) | +0.10 |
| confluence: liquidity run (break of equal highs/lows) | +0.09 |
| 2h volume climax our way | +0.08 |
| chart structure with the trade | +0.08 |
| number of concepts agreeing | +0.08 |
| event candle size | +0.07 |
| DI spread our way | +0.06 |
| concept: break of a swing in a range | +0.05 |
| RSI in trade direction | +0.05 |
| concept: break of structure (continuation) | +0.04 |
| 2h DI our way | +0.03 |
| 2h EMA20 slope our way | +0.03 |
| daily chart (vs 4h) | +0.00 |
| confluence: trendline bounce (confirmed) | -0.00 |
| weekly trend (close vs EMA50) with the trade | -0.00 |
| MACD histogram our way | -0.01 |
| confluence: break of structure (continuation) | -0.03 |
| confluence: change of character (first reversal break) | -0.04 |
| confluence: liquidity sweep (stop hunt) reversal | -0.04 |
| concept: trendline break | -0.06 |
| weekly Supertrend with the trade | -0.06 |
| event candle volume | -0.06 |
| 4h volume climax our way | -0.06 |
| 2h money flow our way | -0.08 |
| confluence: S/R zone breakout | -0.10 |
| 4h momentum our way | -0.13 |
| daily trend with the trade | -0.14 |
| distance from EMA20 our way | -0.20 |

### Why do confident trades still lose? (certainty >= 6, 2022-25)

- 116 losses. **47% failed within 2 candles**; **42% went at least +0.5R our way first**; 0% gapped through the stop.

Biggest differences between winners and losers among these trades (gap in standard deviations):

| factor | avg for winners | avg for losers | gap |
|---|---|---|---|
| number of concepts agreeing | 2.50 | 1.92 | +0.42 |
| weekly Supertrend with the trade | -0.33 | 0.07 | -0.41 |
| confluence: S/R zone breakout | 0.34 | 0.19 | +0.34 |
| confluence: S/R zone bounce (confirmed) | 0.78 | 0.63 | +0.33 |
| confluence: trendline bounce (confirmed) | 0.25 | 0.15 | +0.26 |
| confluence: trendline break | 0.54 | 0.43 | +0.21 |
| concept: break of structure (continuation) | 0.11 | 0.05 | +0.20 |
| weekly trend (close vs EMA50) with the trade | -0.19 | -0.03 | -0.15 |

