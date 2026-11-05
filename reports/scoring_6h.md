# Combined score: main concepts + indicators -> certainty 1-10

Every trade gets a **certainty from 1 to 10** = the model's expected win probability at a 1R target x 10. The model weighs the main concepts first (which concept, confluence, structure, weekly/daily trend) and then the indicators that helped that kind of trade. **Every number below is out-of-sample:** each year (2022-2025) is scored by a model trained only on earlier years, and the holdout (from 2025-11-01) by the model trained on all research data. Win rates are before costs; avg R is after costs. At 1R the after-cost break-even is about 52% on 1D and 55% on 4h.

## Reversal trades (S/R zone bounce (confirmed), trendline bounce (confirmed), liquidity sweep (stop hunt) reversal, change of character (first reversal break))

### Is the certainty honest? (predicted vs actual)

A 6/10 trade should win about 60% of the time.

| certainty | trades 2022-25 | actual win @1R 2022-25 | holdout trades | actual win @1R holdout |
|---|---|---|---|---|
| 2/10 | 1 | 0% | 0 | - |
| 3/10 | 40 | 50% | 5 | 20% |
| 4/10 | 255 | 46% | 55 | 49% |
| 5/10 | 538 | 49% | 197 | 46% |
| 6/10 | 263 | 50% | 42 | 36% |
| 7/10 | 70 | 46% | 7 | 57% |
| 8/10 | 4 | 50% | 1 | 0% |

### Taking only confident trades

| rule | period | trades | trades/week | win @1R | win @1.5R | win @2R | avg R @1R after costs | avg R @2R after costs |
|---|---|---|---|---|---|---|---|---|
| all trades | 2022-25 | 1171 | 5.9 | 48% | 37% | 31% | -0.10 | -0.11 |
| all trades | holdout | 307 | 6.3 | 45% | 32% | 25% | -0.18 | -0.29 |
| certainty >= 5 | 2022-25 | 875 | 4.4 | 49% | 38% | 31% | -0.09 | -0.11 |
| certainty >= 5 | holdout | 247 | 5.1 | 45% | 32% | 25% | -0.18 | -0.27 |
| certainty >= 6 | 2022-25 | 337 | 1.7 | 49% | 39% | 30% | -0.09 | -0.14 |
| certainty >= 6 | holdout | 50 | 1.1 | 38% | 28% | 16% | -0.31 | -0.56 |
| certainty >= 7 | 2022-25 | 74 | 0.4 | 46% | 32% | 24% | -0.13 | -0.28 |
| certainty >= 7 | holdout | 8 | 0.2 | 50% | 25% | 0% | -0.07 | -1.07 |

### Certainty >= 6, year by year

| year | trades | win @1R | win @2R | avg R @1R after costs |
|---|---|---|---|---|
| 2022 | 121 | 49% | 28% | -0.09 |
| 2023 | 104 | 48% | 27% | -0.12 |
| 2024 | 54 | 44% | 31% | -0.19 |
| 2025 | 58 | 57% | 40% | +0.08 |
| holdout | 50 | 38% | 16% | -0.31 |

### What the score is made of (weights of the final model; + raises certainty, - lowers it)

| factor | weight |
|---|---|
| RSI divergence | +0.16 |
| daily trend with the trade | +0.11 |
| confluence: liquidity sweep (stop hunt) reversal | +0.11 |
| RSI in trade direction | +0.10 |
| weekly trend (close vs EMA50) with the trade | +0.09 |
| concept: liquidity sweep (stop hunt) reversal | +0.06 |
| confluence: liquidity run (break of equal highs/lows) | +0.05 |
| confluence: trendline break | +0.04 |
| volume into the event | +0.04 |
| event candle volume | +0.02 |
| confluence: break of structure (continuation) | +0.02 |
| trendline touches | +0.01 |
| daily chart (vs 4h) | +0.00 |
| candle closed near our end | -0.00 |
| weekly Supertrend with the trade | -0.02 |
| number of concepts agreeing | -0.03 |
| bounce candle volume | -0.03 |
| daily ADX < 20 (quiet market) | -0.03 |
| confluence: trendline bounce (confirmed) | -0.03 |
| concept: trendline bounce (confirmed) | -0.04 |
| confluence: S/R zone breakout | -0.05 |
| confluence: change of character (first reversal break) | -0.07 |
| confluence: S/R zone bounce (confirmed) | -0.09 |
| volume divergence | -0.09 |
| concept: change of character (first reversal break) | -0.10 |
| chart structure with the trade | -0.12 |
| distance from EMA200 (our side +) | -0.15 |

### Why do confident trades still lose? (certainty >= 6, 2022-25)

- 169 losses. **33% failed within 2 candles**; **37% went at least +0.5R our way first**; 0% gapped through the stop.

Biggest differences between winners and losers among these trades (gap in standard deviations):

| factor | avg for winners | avg for losers | gap |
|---|---|---|---|
| concept: trendline bounce (confirmed) | 0.20 | 0.33 | -0.29 |
| trendline touches | 0.49 | 0.82 | -0.29 |
| concept: liquidity sweep (stop hunt) reversal | 0.07 | 0.02 | +0.23 |
| candle closed near our end | 0.64 | 0.68 | -0.22 |
| daily trend with the trade | 0.10 | 0.30 | -0.21 |
| RSI in trade direction | 52.49 | 54.95 | -0.20 |
| confluence: liquidity sweep (stop hunt) reversal | 0.11 | 0.06 | +0.18 |
| confluence: change of character (first reversal break) | 0.01 | 0.03 | -0.18 |

## Breakout trades (S/R zone breakout, trendline break, liquidity run (break of equal highs/lows), break of structure (continuation), break of a swing in a range)

### Is the certainty honest? (predicted vs actual)

A 6/10 trade should win about 60% of the time.

| certainty | trades 2022-25 | actual win @1R 2022-25 | holdout trades | actual win @1R holdout |
|---|---|---|---|---|
| 1/10 | 14 | 21% | 0 | - |
| 2/10 | 14 | 71% | 0 | - |
| 3/10 | 44 | 50% | 5 | 40% |
| 4/10 | 295 | 57% | 43 | 44% |
| 5/10 | 471 | 53% | 165 | 53% |
| 6/10 | 348 | 50% | 100 | 44% |
| 7/10 | 110 | 46% | 5 | 40% |
| 8/10 | 25 | 36% | 0 | - |
| 9/10 | 3 | 0% | 0 | - |

### Taking only confident trades

| rule | period | trades | trades/week | win @1R | win @1.5R | win @2R | avg R @1R after costs | avg R @2R after costs |
|---|---|---|---|---|---|---|---|---|
| all trades | 2022-25 | 1324 | 6.7 | 52% | 43% | 35% | -0.06 | -0.02 |
| all trades | holdout | 318 | 6.5 | 49% | 40% | 33% | -0.12 | -0.08 |
| certainty >= 5 | 2022-25 | 957 | 4.9 | 50% | 43% | 35% | -0.08 | -0.03 |
| certainty >= 5 | holdout | 270 | 5.5 | 50% | 40% | 35% | -0.10 | -0.03 |
| certainty >= 6 | 2022-25 | 486 | 2.5 | 48% | 42% | 34% | -0.11 | -0.06 |
| certainty >= 6 | holdout | 105 | 2.2 | 44% | 39% | 36% | -0.21 | -0.00 |
| certainty >= 7 | 2022-25 | 138 | 0.7 | 43% | 38% | 29% | -0.20 | -0.15 |
| certainty >= 7 | holdout | 5 | 0.1 | 40% | 40% | 40% | -0.27 | +0.13 |

### Certainty >= 6, year by year

| year | trades | win @1R | win @2R | avg R @1R after costs |
|---|---|---|---|---|
| 2022 | 147 | 45% | 31% | -0.17 |
| 2023 | 147 | 44% | 29% | -0.24 |
| 2024 | 102 | 57% | 41% | +0.07 |
| 2025 | 90 | 52% | 37% | -0.03 |
| holdout | 105 | 44% | 36% | -0.21 |

### What the score is made of (weights of the final model; + raises certainty, - lowers it)

| factor | weight |
|---|---|
| trendline touches | +0.25 |
| MACD histogram our way | +0.21 |
| RSI in trade direction | +0.16 |
| confluence: S/R zone bounce (confirmed) | +0.10 |
| Bollinger position our way | +0.09 |
| event candle volume | +0.07 |
| concept: liquidity run (break of equal highs/lows) | +0.06 |
| concept: break of structure (continuation) | +0.04 |
| daily trend with the trade | +0.03 |
| 4h volume climax our way | +0.03 |
| confluence: trendline bounce (confirmed) | +0.02 |
| number of concepts agreeing | +0.02 |
| confluence: change of character (first reversal break) | +0.02 |
| confluence: break of structure (continuation) | +0.02 |
| confluence: liquidity run (break of equal highs/lows) | +0.00 |
| daily chart (vs 4h) | +0.00 |
| confluence: S/R zone breakout | -0.00 |
| 2h money flow our way | -0.01 |
| concept: break of a swing in a range | -0.01 |
| 2h DI our way | -0.01 |
| 4h momentum our way | -0.02 |
| chart structure with the trade | -0.03 |
| 2h volume climax our way | -0.03 |
| event candle size | -0.03 |
| weekly Supertrend with the trade | -0.04 |
| 2h EMA20 slope our way | -0.04 |
| weekly trend (close vs EMA50) with the trade | -0.05 |
| confluence: trendline break | -0.06 |
| confluence: liquidity sweep (stop hunt) reversal | -0.08 |
| DI spread our way | -0.14 |
| distance from EMA20 our way | -0.22 |
| concept: trendline break | -0.30 |

### Why do confident trades still lose? (certainty >= 6, 2022-25)

- 247 losses. **45% failed within 2 candles**; **40% went at least +0.5R our way first**; 0% gapped through the stop.

Biggest differences between winners and losers among these trades (gap in standard deviations):

| factor | avg for winners | avg for losers | gap |
|---|---|---|---|
| MACD histogram our way | 0.16 | 0.10 | +0.28 |
| weekly trend (close vs EMA50) with the trade | -0.12 | 0.16 | -0.28 |
| weekly Supertrend with the trade | -0.08 | 0.19 | -0.27 |
| number of concepts agreeing | 1.71 | 1.40 | +0.26 |
| confluence: S/R zone bounce (confirmed) | 0.52 | 0.43 | +0.19 |
| 4h momentum our way | 0.60 | 0.44 | +0.18 |
| 2h volume climax our way | 0.10 | 0.16 | -0.18 |
| distance from EMA20 our way | 1.31 | 1.08 | +0.18 |

