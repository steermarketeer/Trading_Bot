# Combined score: main concepts + indicators -> certainty 1-10

Every trade gets a **certainty from 1 to 10** = the model's expected win probability at a 1R target x 10. The model weighs the main concepts first (which concept, confluence, structure, weekly/daily trend) and then the indicators that helped that kind of trade. **Every number below is out-of-sample:** each year (2022-2025) is scored by a model trained only on earlier years, and the holdout (from 2025-11-01) by the model trained on all research data. Win rates are before costs; avg R is after costs. At 1R the after-cost break-even is about 52% on 1D and 55% on 4h.

## Reversal trades (S/R zone bounce (confirmed), trendline bounce (confirmed), liquidity sweep (stop hunt) reversal, change of character (first reversal break))

### Is the certainty honest? (predicted vs actual)

A 6/10 trade should win about 60% of the time.

| certainty | trades 2022-25 | actual win @1R 2022-25 | holdout trades | actual win @1R holdout |
|---|---|---|---|---|
| 2/10 | 1 | 100% | 0 | - |
| 3/10 | 71 | 48% | 2 | 50% |
| 4/10 | 1077 | 45% | 185 | 50% |
| 5/10 | 2932 | 50% | 813 | 47% |
| 6/10 | 506 | 52% | 103 | 51% |
| 7/10 | 3 | 33% | 1 | 0% |

### Taking only confident trades

| rule | period | trades | trades/week | win @1R | win @1.5R | win @2R | avg R @1R after costs | avg R @2R after costs |
|---|---|---|---|---|---|---|---|---|
| all trades | 2022-25 | 4590 | 23.0 | 49% | 39% | 32% | -0.22 | -0.21 |
| all trades | holdout | 1104 | 22.4 | 48% | 38% | 30% | -0.26 | -0.28 |
| certainty >= 5 | 2022-25 | 3441 | 17.3 | 50% | 41% | 33% | -0.19 | -0.17 |
| certainty >= 5 | holdout | 917 | 18.6 | 48% | 38% | 30% | -0.27 | -0.29 |
| certainty >= 6 | 2022-25 | 509 | 2.6 | 51% | 39% | 31% | -0.17 | -0.24 |
| certainty >= 6 | holdout | 104 | 2.2 | 51% | 40% | 31% | -0.14 | -0.13 |
| certainty >= 7 | 2022-25 | 3 | 0.1 | 33% | 0% | 0% | -0.45 | -1.12 |
| certainty >= 7 | holdout | 1 | - | 0% | 0% | 0% | -1.07 | -1.07 |

### Certainty >= 6, year by year

| year | trades | win @1R | win @2R | avg R @1R after costs |
|---|---|---|---|---|
| 2022 | 130 | 53% | 33% | -0.08 |
| 2023 | 204 | 45% | 25% | -0.38 |
| 2024 | 91 | 53% | 41% | -0.10 |
| 2025 | 84 | 63% | 36% | +0.13 |
| holdout | 104 | 51% | 31% | -0.14 |

### What the score is made of (weights of the final model; + raises certainty, - lowers it)

| factor | weight |
|---|---|
| weekly trend (close vs EMA50) with the trade | +0.08 |
| RSI in trade direction | +0.08 |
| confluence: trendline break | +0.06 |
| distance from EMA200 (our side +) | +0.06 |
| RSI divergence | +0.05 |
| confluence: trendline bounce (confirmed) | +0.04 |
| trendline touches | +0.03 |
| number of concepts agreeing | +0.01 |
| volume divergence | +0.01 |
| daily ADX < 20 (quiet market) | +0.01 |
| confluence: liquidity run (break of equal highs/lows) | +0.00 |
| daily chart (vs 4h) | +0.00 |
| confluence: liquidity sweep (stop hunt) reversal | -0.00 |
| candle closed near our end | -0.00 |
| confluence: S/R zone bounce (confirmed) | -0.00 |
| event candle volume | -0.01 |
| volume into the event | -0.01 |
| bounce candle volume | -0.01 |
| daily trend with the trade | -0.02 |
| confluence: S/R zone breakout | -0.03 |
| confluence: change of character (first reversal break) | -0.04 |
| confluence: break of structure (continuation) | -0.04 |
| weekly Supertrend with the trade | -0.04 |
| concept: trendline bounce (confirmed) | -0.07 |
| concept: liquidity sweep (stop hunt) reversal | -0.08 |
| chart structure with the trade | -0.08 |
| concept: change of character (first reversal break) | -0.11 |

### Why do confident trades still lose? (certainty >= 6, 2022-25)

- 237 losses. **38% failed within 2 candles**; **36% went at least +0.5R our way first**; 0% gapped through the stop.

Biggest differences between winners and losers among these trades (gap in standard deviations):

| factor | avg for winners | avg for losers | gap |
|---|---|---|---|
| concept: liquidity sweep (stop hunt) reversal | 0.01 | 0.05 | -0.22 |
| distance from EMA200 (our side +) | 2.91 | 2.31 | +0.16 |
| volume into the event | 1.29 | 1.46 | -0.16 |
| confluence: trendline bounce (confirmed) | 0.22 | 0.16 | +0.15 |
| RSI divergence | 0.15 | 0.21 | -0.14 |
| concept: trendline bounce (confirmed) | 0.26 | 0.32 | -0.13 |
| trendline touches | 0.60 | 0.74 | -0.13 |
| confluence: change of character (first reversal break) | 0.05 | 0.02 | +0.12 |

## Breakout trades (S/R zone breakout, trendline break, liquidity run (break of equal highs/lows), break of structure (continuation), break of a swing in a range)

### Is the certainty honest? (predicted vs actual)

A 6/10 trade should win about 60% of the time.

| certainty | trades 2022-25 | actual win @1R 2022-25 | holdout trades | actual win @1R holdout |
|---|---|---|---|---|
| 3/10 | 15 | 73% | 0 | - |
| 4/10 | 617 | 50% | 89 | 42% |
| 5/10 | 3083 | 51% | 971 | 50% |
| 6/10 | 1285 | 51% | 286 | 50% |
| 7/10 | 256 | 61% | 41 | 46% |
| 8/10 | 45 | 62% | 1 | 100% |
| 9/10 | 7 | 14% | 0 | - |
| 10/10 | 1 | 0% | 0 | - |

### Taking only confident trades

| rule | period | trades | trades/week | win @1R | win @1.5R | win @2R | avg R @1R after costs | avg R @2R after costs |
|---|---|---|---|---|---|---|---|---|
| all trades | 2022-25 | 5309 | 26.6 | 52% | 42% | 34% | -0.22 | -0.20 |
| all trades | holdout | 1388 | 28.1 | 49% | 39% | 32% | -0.30 | -0.31 |
| certainty >= 5 | 2022-25 | 4677 | 23.5 | 52% | 42% | 35% | -0.21 | -0.19 |
| certainty >= 5 | holdout | 1299 | 26.3 | 50% | 39% | 32% | -0.28 | -0.29 |
| certainty >= 6 | 2022-25 | 1594 | 8.0 | 53% | 42% | 35% | -0.16 | -0.12 |
| certainty >= 6 | holdout | 328 | 6.7 | 49% | 39% | 28% | -0.24 | -0.34 |
| certainty >= 7 | 2022-25 | 309 | 1.6 | 60% | 46% | 39% | +0.03 | +0.10 |
| certainty >= 7 | holdout | 42 | 0.9 | 48% | 31% | 19% | -0.17 | -0.39 |

### Certainty >= 6, year by year

| year | trades | win @1R | win @2R | avg R @1R after costs |
|---|---|---|---|---|
| 2022 | 449 | 55% | 38% | -0.07 |
| 2023 | 552 | 50% | 32% | -0.26 |
| 2024 | 328 | 52% | 38% | -0.18 |
| 2025 | 265 | 54% | 34% | -0.10 |
| holdout | 328 | 49% | 28% | -0.24 |

### What the score is made of (weights of the final model; + raises certainty, - lowers it)

| factor | weight |
|---|---|
| distance from EMA20 our way | +0.21 |
| event candle volume | +0.10 |
| DI spread our way | +0.10 |
| 2h volume climax our way | +0.07 |
| Bollinger position our way | +0.07 |
| 2h money flow our way | +0.05 |
| weekly trend (close vs EMA50) with the trade | +0.04 |
| confluence: trendline bounce (confirmed) | +0.04 |
| confluence: liquidity run (break of equal highs/lows) | +0.04 |
| confluence: trendline break | +0.03 |
| trendline touches | +0.03 |
| confluence: liquidity sweep (stop hunt) reversal | +0.02 |
| 4h volume climax our way | +0.01 |
| number of concepts agreeing | +0.01 |
| 2h EMA20 slope our way | +0.01 |
| confluence: S/R zone bounce (confirmed) | +0.00 |
| daily chart (vs 4h) | +0.00 |
| 4h momentum our way | -0.00 |
| weekly Supertrend with the trade | -0.01 |
| confluence: S/R zone breakout | -0.01 |
| chart structure with the trade | -0.02 |
| concept: liquidity run (break of equal highs/lows) | -0.02 |
| daily trend with the trade | -0.03 |
| confluence: break of structure (continuation) | -0.03 |
| concept: trendline break | -0.04 |
| MACD histogram our way | -0.04 |
| concept: break of structure (continuation) | -0.05 |
| confluence: change of character (first reversal break) | -0.07 |
| event candle size | -0.07 |
| 2h DI our way | -0.09 |
| concept: break of a swing in a range | -0.09 |
| RSI in trade direction | -0.26 |

### Why do confident trades still lose? (certainty >= 6, 2022-25)

- 740 losses. **46% failed within 2 candles**; **42% went at least +0.5R our way first**; 0% gapped through the stop.

Biggest differences between winners and losers among these trades (gap in standard deviations):

| factor | avg for winners | avg for losers | gap |
|---|---|---|---|
| 2h volume climax our way | 0.24 | 0.16 | +0.19 |
| Bollinger position our way | 1.06 | 1.00 | +0.17 |
| distance from EMA20 our way | 1.79 | 1.59 | +0.15 |
| RSI in trade direction | 64.03 | 62.48 | +0.14 |
| MACD histogram our way | 0.15 | 0.13 | +0.14 |
| 2h DI our way | 0.04 | -0.09 | +0.14 |
| 2h EMA20 slope our way | 0.14 | 0.01 | +0.13 |
| 4h momentum our way | 0.15 | 0.03 | +0.12 |

