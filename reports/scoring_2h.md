# Combined score: main concepts + indicators -> certainty 1-10

Every trade gets a **certainty from 1 to 10** = the model's expected win probability at a 1R target x 10. The model weighs the main concepts first (which concept, confluence, structure, weekly/daily trend) and then the indicators that helped that kind of trade. **Every number below is out-of-sample:** each year (2022-2025) is scored by a model trained only on earlier years, and the holdout (from 2025-11-01) by the model trained on all research data. Win rates are before costs; avg R is after costs. At 1R the after-cost break-even is about 52% on 1D and 55% on 4h.

## Reversal trades (S/R zone bounce (confirmed), trendline bounce (confirmed), liquidity sweep (stop hunt) reversal, change of character (first reversal break))

### Is the certainty honest? (predicted vs actual)

A 6/10 trade should win about 60% of the time.

| certainty | trades 2022-25 | actual win @1R 2022-25 | holdout trades | actual win @1R holdout |
|---|---|---|---|---|
| 2/10 | 3 | 67% | 0 | - |
| 3/10 | 84 | 48% | 0 | - |
| 4/10 | 648 | 50% | 173 | 46% |
| 5/10 | 1683 | 48% | 456 | 49% |
| 6/10 | 240 | 53% | 37 | 46% |
| 7/10 | 67 | 55% | 4 | 25% |
| 8/10 | 5 | 40% | 0 | - |
| 9/10 | 1 | 0% | 0 | - |

### Taking only confident trades

| rule | period | trades | trades/week | win @1R | win @1.5R | win @2R | avg R @1R after costs | avg R @2R after costs |
|---|---|---|---|---|---|---|---|---|
| all trades | 2022-25 | 2731 | 13.7 | 49% | 39% | 32% | -0.15 | -0.13 |
| all trades | holdout | 670 | 13.6 | 48% | 38% | 31% | -0.19 | -0.17 |
| certainty >= 5 | 2022-25 | 1996 | 10.0 | 49% | 39% | 33% | -0.17 | -0.14 |
| certainty >= 5 | holdout | 497 | 10.1 | 48% | 38% | 32% | -0.19 | -0.15 |
| certainty >= 6 | 2022-25 | 313 | 1.6 | 53% | 40% | 34% | -0.07 | -0.11 |
| certainty >= 6 | holdout | 41 | 0.8 | 44% | 37% | 27% | -0.24 | -0.22 |
| certainty >= 7 | 2022-25 | 73 | 0.4 | 53% | 42% | 29% | -0.06 | -0.19 |
| certainty >= 7 | holdout | 4 | 0.1 | 25% | 25% | 25% | -0.61 | -0.36 |

### Certainty >= 6, year by year

| year | trades | win @1R | win @2R | avg R @1R after costs |
|---|---|---|---|---|
| 2022 | 116 | 59% | 41% | +0.05 |
| 2023 | 118 | 42% | 21% | -0.33 |
| 2024 | 28 | 71% | 57% | +0.31 |
| 2025 | 51 | 57% | 33% | +0.02 |
| holdout | 41 | 44% | 27% | -0.24 |

### What the score is made of (weights of the final model; + raises certainty, - lowers it)

| factor | weight |
|---|---|
| RSI in trade direction | +0.13 |
| confluence: liquidity sweep (stop hunt) reversal | +0.12 |
| confluence: S/R zone bounce (confirmed) | +0.06 |
| daily trend with the trade | +0.05 |
| volume divergence | +0.04 |
| number of concepts agreeing | +0.04 |
| weekly trend (close vs EMA50) with the trade | +0.03 |
| confluence: liquidity run (break of equal highs/lows) | +0.03 |
| trendline touches | +0.02 |
| event candle volume | +0.02 |
| confluence: change of character (first reversal break) | +0.02 |
| confluence: S/R zone breakout | +0.02 |
| RSI divergence | +0.01 |
| candle closed near our end | +0.01 |
| daily ADX < 20 (quiet market) | +0.00 |
| daily chart (vs 4h) | +0.00 |
| chart structure with the trade | -0.00 |
| confluence: trendline bounce (confirmed) | -0.01 |
| confluence: break of structure (continuation) | -0.02 |
| confluence: trendline break | -0.03 |
| concept: change of character (first reversal break) | -0.03 |
| weekly Supertrend with the trade | -0.04 |
| volume into the event | -0.05 |
| concept: liquidity sweep (stop hunt) reversal | -0.05 |
| concept: trendline bounce (confirmed) | -0.07 |
| bounce candle volume | -0.07 |
| distance from EMA200 (our side +) | -0.10 |

### Why do confident trades still lose? (certainty >= 6, 2022-25)

- 146 losses. **35% failed within 2 candles**; **27% went at least +0.5R our way first**; 0% gapped through the stop.

Biggest differences between winners and losers among these trades (gap in standard deviations):

| factor | avg for winners | avg for losers | gap |
|---|---|---|---|
| confluence: liquidity sweep (stop hunt) reversal | 0.39 | 0.27 | +0.24 |
| concept: liquidity sweep (stop hunt) reversal | 0.00 | 0.02 | -0.21 |
| distance from EMA200 (our side +) | 0.30 | 0.91 | -0.18 |
| number of concepts agreeing | 1.46 | 1.27 | +0.17 |
| confluence: trendline bounce (confirmed) | 0.14 | 0.09 | +0.15 |
| daily ADX < 20 (quiet market) | -0.16 | -0.22 | +0.15 |
| volume into the event | 1.38 | 1.27 | +0.14 |
| daily trend with the trade | 0.20 | 0.05 | +0.14 |

## Breakout trades (S/R zone breakout, trendline break, liquidity run (break of equal highs/lows), break of structure (continuation), break of a swing in a range)

### Is the certainty honest? (predicted vs actual)

A 6/10 trade should win about 60% of the time.

| certainty | trades 2022-25 | actual win @1R 2022-25 | holdout trades | actual win @1R holdout |
|---|---|---|---|---|
| 1/10 | 1 | 0% | 0 | - |
| 2/10 | 7 | 57% | 0 | - |
| 3/10 | 63 | 54% | 0 | - |
| 4/10 | 469 | 50% | 51 | 45% |
| 5/10 | 1350 | 52% | 411 | 49% |
| 6/10 | 714 | 57% | 208 | 51% |
| 7/10 | 319 | 61% | 70 | 56% |
| 8/10 | 56 | 75% | 11 | 55% |
| 9/10 | 1 | 0% | 0 | - |

### Taking only confident trades

| rule | period | trades | trades/week | win @1R | win @1.5R | win @2R | avg R @1R after costs | avg R @2R after costs |
|---|---|---|---|---|---|---|---|---|
| all trades | 2022-25 | 2980 | 15.0 | 54% | 43% | 36% | -0.08 | -0.08 |
| all trades | holdout | 751 | 15.2 | 50% | 39% | 31% | -0.18 | -0.24 |
| certainty >= 5 | 2022-25 | 2440 | 12.3 | 55% | 44% | 36% | -0.06 | -0.07 |
| certainty >= 5 | holdout | 700 | 14.2 | 51% | 39% | 31% | -0.17 | -0.22 |
| certainty >= 6 | 2022-25 | 1090 | 5.5 | 59% | 48% | 40% | +0.03 | +0.08 |
| certainty >= 6 | holdout | 289 | 6.0 | 52% | 40% | 32% | -0.12 | -0.17 |
| certainty >= 7 | 2022-25 | 376 | 1.9 | 63% | 50% | 41% | +0.14 | +0.19 |
| certainty >= 7 | holdout | 81 | 1.7 | 56% | 46% | 38% | -0.03 | +0.05 |

### Certainty >= 6, year by year

| year | trades | win @1R | win @2R | avg R @1R after costs |
|---|---|---|---|---|
| 2022 | 249 | 56% | 39% | +0.01 |
| 2023 | 339 | 59% | 39% | -0.01 |
| 2024 | 220 | 62% | 43% | +0.10 |
| 2025 | 282 | 59% | 39% | +0.05 |
| holdout | 289 | 52% | 32% | -0.12 |

### What the score is made of (weights of the final model; + raises certainty, - lowers it)

| factor | weight |
|---|---|
| Bollinger position our way | +0.21 |
| 2h volume climax our way | +0.19 |
| distance from EMA20 our way | +0.18 |
| confluence: break of structure (continuation) | +0.08 |
| confluence: S/R zone breakout | +0.08 |
| 4h volume climax our way | +0.08 |
| 4h momentum our way | +0.06 |
| number of concepts agreeing | +0.04 |
| DI spread our way | +0.04 |
| confluence: liquidity sweep (stop hunt) reversal | +0.04 |
| trendline touches | +0.03 |
| confluence: trendline bounce (confirmed) | +0.03 |
| event candle volume | +0.03 |
| confluence: trendline break | +0.02 |
| confluence: S/R zone bounce (confirmed) | +0.02 |
| weekly trend (close vs EMA50) with the trade | +0.01 |
| daily chart (vs 4h) | +0.00 |
| confluence: liquidity run (break of equal highs/lows) | -0.00 |
| daily trend with the trade | -0.01 |
| 2h money flow our way | -0.03 |
| 2h DI our way | -0.03 |
| concept: break of structure (continuation) | -0.03 |
| weekly Supertrend with the trade | -0.04 |
| concept: liquidity run (break of equal highs/lows) | -0.04 |
| concept: break of a swing in a range | -0.06 |
| MACD histogram our way | -0.07 |
| 2h EMA20 slope our way | -0.08 |
| concept: trendline break | -0.09 |
| chart structure with the trade | -0.09 |
| confluence: change of character (first reversal break) | -0.12 |
| event candle size | -0.18 |
| RSI in trade direction | -0.19 |

### Why do confident trades still lose? (certainty >= 6, 2022-25)

- 437 losses. **45% failed within 2 candles**; **37% went at least +0.5R our way first**; 0% gapped through the stop.

Biggest differences between winners and losers among these trades (gap in standard deviations):

| factor | avg for winners | avg for losers | gap |
|---|---|---|---|
| 2h volume climax our way | 0.55 | 0.43 | +0.24 |
| 2h money flow our way | 0.56 | 0.38 | +0.21 |
| confluence: change of character (first reversal break) | 0.08 | 0.14 | -0.19 |
| distance from EMA20 our way | 1.76 | 1.57 | +0.16 |
| number of concepts agreeing | 1.64 | 1.46 | +0.15 |
| event candle volume | 3.17 | 2.87 | +0.14 |
| weekly trend (close vs EMA50) with the trade | 0.14 | 0.28 | -0.14 |
| RSI in trade direction | 64.40 | 62.96 | +0.14 |

