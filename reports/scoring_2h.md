# Combined score: main concepts + indicators -> certainty 1-10

Every trade gets a **certainty from 1 to 10** = the model's expected win probability at a 1R target x 10. The model weighs the main concepts first (which concept, confluence, structure, weekly/daily trend) and then the indicators that helped that kind of trade. **Every number below is out-of-sample:** each year (2022-2025) is scored by a model trained only on earlier years, and the holdout (from 2025-11-01) by the model trained on all research data. Win rates are before costs; avg R is after costs. At 1R the after-cost break-even is about 52% on 1D and 55% on 4h.

## Reversal trades (S/R zone bounce (confirmed), trendline bounce (confirmed), liquidity sweep (stop hunt) reversal, change of character (first reversal break))

### Is the certainty honest? (predicted vs actual)

A 6/10 trade should win about 60% of the time.

| certainty | trades 2022-25 | actual win @1R 2022-25 | holdout trades | actual win @1R holdout |
|---|---|---|---|---|
| 2/10 | 3 | 67% | 0 | - |
| 3/10 | 83 | 49% | 0 | - |
| 4/10 | 651 | 51% | 168 | 47% |
| 5/10 | 1689 | 48% | 463 | 49% |
| 6/10 | 236 | 52% | 35 | 43% |
| 7/10 | 64 | 55% | 4 | 25% |
| 8/10 | 4 | 50% | 0 | - |
| 9/10 | 1 | 0% | 0 | - |

### Taking only confident trades

| rule | period | trades | trades/week | win @1R | win @1.5R | win @2R | avg R @1R after costs | avg R @2R after costs |
|---|---|---|---|---|---|---|---|---|
| all trades | 2022-25 | 2731 | 13.7 | 49% | 39% | 32% | -0.15 | -0.13 |
| all trades | holdout | 670 | 13.6 | 48% | 38% | 31% | -0.19 | -0.17 |
| certainty >= 5 | 2022-25 | 1994 | 10.0 | 48% | 39% | 32% | -0.18 | -0.14 |
| certainty >= 5 | holdout | 502 | 10.2 | 48% | 38% | 32% | -0.19 | -0.15 |
| certainty >= 6 | 2022-25 | 305 | 1.5 | 52% | 40% | 33% | -0.10 | -0.12 |
| certainty >= 6 | holdout | 39 | 0.8 | 41% | 33% | 26% | -0.30 | -0.30 |
| certainty >= 7 | 2022-25 | 69 | 0.4 | 54% | 42% | 29% | -0.05 | -0.20 |
| certainty >= 7 | holdout | 4 | 0.1 | 25% | 25% | 25% | -0.61 | -0.36 |

### Certainty >= 6, year by year

| year | trades | win @1R | win @2R | avg R @1R after costs |
|---|---|---|---|---|
| 2022 | 107 | 57% | 39% | +0.01 |
| 2023 | 116 | 42% | 22% | -0.33 |
| 2024 | 28 | 75% | 61% | +0.38 |
| 2025 | 54 | 52% | 30% | -0.08 |
| holdout | 39 | 41% | 26% | -0.30 |

### What the score is made of (weights of the final model; + raises certainty, - lowers it)

| factor | weight |
|---|---|
| RSI in trade direction | +0.12 |
| confluence: liquidity sweep (stop hunt) reversal | +0.12 |
| confluence: S/R zone bounce (confirmed) | +0.06 |
| volume divergence | +0.04 |
| number of concepts agreeing | +0.04 |
| daily trend with the trade | +0.03 |
| confluence: liquidity run (break of equal highs/lows) | +0.03 |
| trendline touches | +0.02 |
| event candle volume | +0.02 |
| confluence: change of character (first reversal break) | +0.02 |
| confluence: S/R zone breakout | +0.02 |
| RSI divergence | +0.01 |
| candle closed near our end | +0.01 |
| weekly trend (close vs EMA50) with the trade | +0.01 |
| daily ADX < 20 (quiet market) | +0.00 |
| daily chart (vs 4h) | +0.00 |
| chart structure with the trade | -0.00 |
| confluence: trendline bounce (confirmed) | -0.01 |
| confluence: break of structure (continuation) | -0.02 |
| weekly Supertrend with the trade | -0.02 |
| confluence: trendline break | -0.03 |
| concept: change of character (first reversal break) | -0.03 |
| volume into the event | -0.05 |
| concept: liquidity sweep (stop hunt) reversal | -0.05 |
| concept: trendline bounce (confirmed) | -0.07 |
| bounce candle volume | -0.07 |
| distance from EMA200 (our side +) | -0.08 |

### Why do confident trades still lose? (certainty >= 6, 2022-25)

- 146 losses. **36% failed within 2 candles**; **28% went at least +0.5R our way first**; 0% gapped through the stop.

Biggest differences between winners and losers among these trades (gap in standard deviations):

| factor | avg for winners | avg for losers | gap |
|---|---|---|---|
| confluence: liquidity sweep (stop hunt) reversal | 0.41 | 0.27 | +0.28 |
| number of concepts agreeing | 1.53 | 1.24 | +0.26 |
| volume into the event | 1.43 | 1.24 | +0.24 |
| concept: liquidity sweep (stop hunt) reversal | 0.00 | 0.02 | -0.21 |
| daily trend with the trade | 0.13 | -0.04 | +0.17 |
| confluence: trendline bounce (confirmed) | 0.14 | 0.09 | +0.17 |
| confluence: S/R zone bounce (confirmed) | 0.31 | 0.24 | +0.15 |
| trendline touches | 0.94 | 1.15 | -0.15 |

## Breakout trades (S/R zone breakout, trendline break, liquidity run (break of equal highs/lows), break of structure (continuation), break of a swing in a range)

### Is the certainty honest? (predicted vs actual)

A 6/10 trade should win about 60% of the time.

| certainty | trades 2022-25 | actual win @1R 2022-25 | holdout trades | actual win @1R holdout |
|---|---|---|---|---|
| 1/10 | 1 | 0% | 0 | - |
| 2/10 | 6 | 67% | 0 | - |
| 3/10 | 65 | 54% | 0 | - |
| 4/10 | 461 | 49% | 53 | 45% |
| 5/10 | 1356 | 53% | 408 | 49% |
| 6/10 | 718 | 56% | 211 | 52% |
| 7/10 | 318 | 62% | 68 | 54% |
| 8/10 | 55 | 73% | 11 | 55% |

### Taking only confident trades

| rule | period | trades | trades/week | win @1R | win @1.5R | win @2R | avg R @1R after costs | avg R @2R after costs |
|---|---|---|---|---|---|---|---|---|
| all trades | 2022-25 | 2980 | 15.0 | 54% | 43% | 36% | -0.08 | -0.08 |
| all trades | holdout | 751 | 15.2 | 50% | 39% | 31% | -0.18 | -0.24 |
| certainty >= 5 | 2022-25 | 2447 | 12.3 | 55% | 44% | 36% | -0.06 | -0.06 |
| certainty >= 5 | holdout | 698 | 14.2 | 51% | 39% | 31% | -0.17 | -0.23 |
| certainty >= 6 | 2022-25 | 1091 | 5.5 | 58% | 47% | 39% | +0.02 | +0.07 |
| certainty >= 6 | holdout | 290 | 6.0 | 52% | 40% | 32% | -0.12 | -0.16 |
| certainty >= 7 | 2022-25 | 373 | 1.9 | 64% | 50% | 42% | +0.14 | +0.20 |
| certainty >= 7 | holdout | 79 | 1.7 | 54% | 44% | 38% | -0.06 | +0.04 |

### Certainty >= 6, year by year

| year | trades | win @1R | win @2R | avg R @1R after costs |
|---|---|---|---|---|
| 2022 | 246 | 56% | 39% | +0.01 |
| 2023 | 338 | 58% | 38% | -0.04 |
| 2024 | 224 | 62% | 43% | +0.09 |
| 2025 | 283 | 59% | 39% | +0.05 |
| holdout | 290 | 52% | 32% | -0.12 |

### What the score is made of (weights of the final model; + raises certainty, - lowers it)

| factor | weight |
|---|---|
| Bollinger position our way | +0.21 |
| 2h volume climax our way | +0.19 |
| distance from EMA20 our way | +0.18 |
| confluence: break of structure (continuation) | +0.08 |
| 4h volume climax our way | +0.08 |
| confluence: S/R zone breakout | +0.08 |
| 4h momentum our way | +0.06 |
| number of concepts agreeing | +0.04 |
| confluence: liquidity sweep (stop hunt) reversal | +0.04 |
| DI spread our way | +0.04 |
| event candle volume | +0.03 |
| confluence: trendline bounce (confirmed) | +0.03 |
| trendline touches | +0.03 |
| confluence: trendline break | +0.02 |
| confluence: S/R zone bounce (confirmed) | +0.02 |
| weekly trend (close vs EMA50) with the trade | +0.01 |
| daily chart (vs 4h) | +0.00 |
| confluence: liquidity run (break of equal highs/lows) | -0.00 |
| daily trend with the trade | -0.02 |
| 2h money flow our way | -0.02 |
| 2h DI our way | -0.03 |
| concept: break of structure (continuation) | -0.03 |
| weekly Supertrend with the trade | -0.04 |
| concept: liquidity run (break of equal highs/lows) | -0.04 |
| concept: break of a swing in a range | -0.06 |
| MACD histogram our way | -0.07 |
| concept: trendline break | -0.08 |
| chart structure with the trade | -0.09 |
| 2h EMA20 slope our way | -0.09 |
| confluence: change of character (first reversal break) | -0.12 |
| event candle size | -0.18 |
| RSI in trade direction | -0.18 |

### Why do confident trades still lose? (certainty >= 6, 2022-25)

- 443 losses. **45% failed within 2 candles**; **38% went at least +0.5R our way first**; 0% gapped through the stop.

Biggest differences between winners and losers among these trades (gap in standard deviations):

| factor | avg for winners | avg for losers | gap |
|---|---|---|---|
| 2h volume climax our way | 0.55 | 0.43 | +0.26 |
| 2h money flow our way | 0.56 | 0.39 | +0.20 |
| confluence: change of character (first reversal break) | 0.08 | 0.14 | -0.19 |
| distance from EMA20 our way | 1.77 | 1.56 | +0.17 |
| number of concepts agreeing | 1.65 | 1.46 | +0.16 |
| event candle volume | 3.18 | 2.87 | +0.15 |
| chart structure with the trade | -0.01 | -0.12 | +0.15 |
| RSI in trade direction | 64.44 | 62.88 | +0.15 |

