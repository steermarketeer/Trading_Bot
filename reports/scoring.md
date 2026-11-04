# Combined score: main concepts + indicators -> certainty 1-10

Every trade gets a **certainty from 1 to 10** = the model's expected win probability at a 1R target x 10. The model weighs the main concepts first (which concept, confluence, structure, weekly/daily trend) and then the indicators that helped that kind of trade. **Every number below is out-of-sample:** each year (2022-2025) is scored by a model trained only on earlier years, and the holdout (from 2025-11-01) by the model trained on all research data. Win rates are before costs; avg R is after costs. At 1R the after-cost break-even is about 52% on 1D and 55% on 4h.

## Reversal trades (S/R zone bounce (confirmed), trendline bounce (confirmed), liquidity sweep (stop hunt) reversal, change of character (first reversal break))

### Is the certainty honest? (predicted vs actual)

A 6/10 trade should win about 60% of the time.

| certainty | trades 2022-25 | actual win @1R 2022-25 | holdout trades | actual win @1R holdout |
|---|---|---|---|---|
| 1/10 | 2 | 0% | 0 | - |
| 2/10 | 12 | 42% | 0 | - |
| 3/10 | 75 | 48% | 0 | - |
| 4/10 | 430 | 53% | 49 | 53% |
| 5/10 | 956 | 53% | 354 | 48% |
| 6/10 | 449 | 53% | 111 | 50% |
| 7/10 | 88 | 51% | 5 | 20% |
| 8/10 | 5 | 60% | 0 | - |

### Taking only confident trades

| rule | period | trades | trades/week | win @1R | win @1.5R | win @2R | avg R @1R after costs | avg R @2R after costs |
|---|---|---|---|---|---|---|---|---|
| all trades | 2022-25 | 2017 | 10.2 | 52% | 42% | 34% | -0.03 | -0.03 |
| all trades | holdout | 519 | 10.6 | 49% | 38% | 29% | -0.10 | -0.17 |
| certainty >= 5 | 2022-25 | 1498 | 7.6 | 53% | 42% | 34% | -0.02 | -0.03 |
| certainty >= 5 | holdout | 470 | 9.6 | 48% | 37% | 29% | -0.11 | -0.19 |
| certainty >= 6 | 2022-25 | 542 | 2.7 | 52% | 42% | 32% | -0.01 | -0.05 |
| certainty >= 6 | holdout | 116 | 2.4 | 49% | 37% | 29% | -0.07 | -0.16 |
| certainty >= 7 | 2022-25 | 93 | 0.5 | 52% | 41% | 30% | +0.02 | -0.07 |
| certainty >= 7 | holdout | 5 | 0.1 | 20% | 20% | 0% | -0.71 | -1.11 |

### Certainty >= 6, year by year

| year | trades | win @1R | win @2R | avg R @1R after costs |
|---|---|---|---|---|
| 2022 | 164 | 49% | 24% | -0.05 |
| 2023 | 173 | 51% | 30% | -0.03 |
| 2024 | 101 | 49% | 34% | -0.09 |
| 2025 | 104 | 62% | 44% | +0.20 |
| holdout | 116 | 49% | 29% | -0.07 |

### What the score is made of (weights of the final model; + raises certainty, - lowers it)

| factor | weight |
|---|---|
| weekly trend (close vs EMA50) with the trade | +0.11 |
| event candle volume | +0.09 |
| confluence: liquidity sweep (stop hunt) reversal | +0.07 |
| RSI in trade direction | +0.07 |
| daily trend with the trade | +0.06 |
| confluence: trendline break | +0.05 |
| RSI divergence | +0.05 |
| number of concepts agreeing | +0.04 |
| daily chart (vs 4h) | +0.03 |
| volume divergence | +0.03 |
| confluence: S/R zone breakout | +0.02 |
| confluence: liquidity run (break of equal highs/lows) | +0.01 |
| confluence: trendline bounce (confirmed) | +0.00 |
| candle closed near our end | -0.00 |
| daily ADX < 20 (quiet market) | -0.00 |
| confluence: change of character (first reversal break) | -0.00 |
| confluence: S/R zone bounce (confirmed) | -0.00 |
| concept: trendline bounce (confirmed) | -0.01 |
| volume into the event | -0.02 |
| trendline touches | -0.03 |
| confluence: break of structure (continuation) | -0.03 |
| concept: change of character (first reversal break) | -0.04 |
| chart structure with the trade | -0.07 |
| concept: liquidity sweep (stop hunt) reversal | -0.07 |
| distance from EMA200 (our side +) | -0.10 |
| weekly Supertrend with the trade | -0.11 |
| bounce candle volume | -0.11 |

### Why do confident trades still lose? (certainty >= 6, 2022-25)

- 251 losses. **33% failed within 2 candles**; **35% went at least +0.5R our way first**; 0% gapped through the stop.

Biggest differences between winners and losers among these trades (gap in standard deviations):

| factor | avg for winners | avg for losers | gap |
|---|---|---|---|
| concept: trendline bounce (confirmed) | 0.21 | 0.31 | -0.23 |
| trendline touches | 0.48 | 0.71 | -0.22 |
| concept: change of character (first reversal break) | 0.11 | 0.06 | +0.17 |
| confluence: trendline break | 0.45 | 0.38 | +0.15 |
| confluence: break of structure (continuation) | 0.05 | 0.02 | +0.15 |
| confluence: liquidity sweep (stop hunt) reversal | 0.06 | 0.03 | +0.13 |
| RSI in trade direction | 58.38 | 57.08 | +0.12 |
| chart structure with the trade | -0.21 | -0.13 | -0.12 |

## Breakout trades (S/R zone breakout, trendline break, liquidity run (break of equal highs/lows), break of structure (continuation), break of a swing in a range)

### Is the certainty honest? (predicted vs actual)

A 6/10 trade should win about 60% of the time.

| certainty | trades 2022-25 | actual win @1R 2022-25 | holdout trades | actual win @1R holdout |
|---|---|---|---|---|
| 2/10 | 4 | 75% | 0 | - |
| 3/10 | 59 | 51% | 1 | 0% |
| 4/10 | 413 | 53% | 49 | 53% |
| 5/10 | 801 | 53% | 250 | 41% |
| 6/10 | 684 | 55% | 209 | 50% |
| 7/10 | 287 | 59% | 40 | 72% |
| 8/10 | 44 | 52% | 0 | - |

### Taking only confident trades

| rule | period | trades | trades/week | win @1R | win @1.5R | win @2R | avg R @1R after costs | avg R @2R after costs |
|---|---|---|---|---|---|---|---|---|
| all trades | 2022-25 | 2292 | 11.6 | 54% | 44% | 37% | -0.01 | +0.04 |
| all trades | holdout | 549 | 11.1 | 48% | 39% | 33% | -0.15 | -0.10 |
| certainty >= 5 | 2022-25 | 1816 | 9.2 | 55% | 44% | 37% | -0.00 | +0.04 |
| certainty >= 5 | holdout | 499 | 10.2 | 47% | 40% | 34% | -0.15 | -0.08 |
| certainty >= 6 | 2022-25 | 1015 | 5.1 | 56% | 45% | 38% | +0.03 | +0.09 |
| certainty >= 6 | holdout | 249 | 5.1 | 54% | 45% | 37% | -0.01 | +0.04 |
| certainty >= 7 | 2022-25 | 331 | 1.7 | 58% | 47% | 42% | +0.08 | +0.20 |
| certainty >= 7 | holdout | 40 | 0.9 | 72% | 62% | 49% | +0.38 | +0.38 |

### Certainty >= 6, year by year

| year | trades | win @1R | win @2R | avg R @1R after costs |
|---|---|---|---|---|
| 2022 | 230 | 57% | 41% | +0.08 |
| 2023 | 315 | 59% | 40% | +0.07 |
| 2024 | 207 | 58% | 37% | +0.08 |
| 2025 | 263 | 50% | 34% | -0.08 |
| holdout | 249 | 54% | 37% | -0.01 |

### What the score is made of (weights of the final model; + raises certainty, - lowers it)

| factor | weight |
|---|---|
| DI spread our way | +0.22 |
| Bollinger position our way | +0.13 |
| confluence: S/R zone bounce (confirmed) | +0.10 |
| 2h volume climax our way | +0.08 |
| distance from EMA20 our way | +0.06 |
| 4h momentum our way | +0.06 |
| confluence: break of structure (continuation) | +0.05 |
| concept: break of structure (continuation) | +0.05 |
| 4h volume climax our way | +0.05 |
| weekly trend (close vs EMA50) with the trade | +0.05 |
| number of concepts agreeing | +0.05 |
| confluence: S/R zone breakout | +0.04 |
| 2h DI our way | +0.04 |
| concept: liquidity run (break of equal highs/lows) | +0.02 |
| confluence: liquidity sweep (stop hunt) reversal | +0.02 |
| daily trend with the trade | +0.02 |
| event candle size | +0.02 |
| confluence: change of character (first reversal break) | +0.02 |
| confluence: liquidity run (break of equal highs/lows) | +0.01 |
| confluence: trendline bounce (confirmed) | +0.01 |
| 2h money flow our way | +0.00 |
| 2h EMA20 slope our way | -0.02 |
| concept: break of a swing in a range | -0.02 |
| trendline touches | -0.02 |
| weekly Supertrend with the trade | -0.03 |
| event candle volume | -0.04 |
| daily chart (vs 4h) | -0.04 |
| MACD histogram our way | -0.04 |
| concept: trendline break | -0.07 |
| confluence: trendline break | -0.09 |
| chart structure with the trade | -0.12 |
| RSI in trade direction | -0.31 |

### Why do confident trades still lose? (certainty >= 6, 2022-25)

- 442 losses. **45% failed within 2 candles**; **40% went at least +0.5R our way first**; 0% gapped through the stop.

Biggest differences between winners and losers among these trades (gap in standard deviations):

| factor | avg for winners | avg for losers | gap |
|---|---|---|---|
| number of concepts agreeing | 1.97 | 1.72 | +0.21 |
| 2h volume climax our way | 0.30 | 0.22 | +0.18 |
| confluence: S/R zone breakout | 0.36 | 0.29 | +0.17 |
| confluence: change of character (first reversal break) | 0.13 | 0.08 | +0.16 |
| event candle size | 1.91 | 1.78 | +0.14 |
| 4h volume climax our way | 0.24 | 0.19 | +0.13 |
| weekly Supertrend with the trade | -0.03 | 0.10 | -0.13 |
| Bollinger position our way | 1.01 | 0.97 | +0.12 |

