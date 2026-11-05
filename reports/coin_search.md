# Each coin's own best rule combination (searched on 2022 - Oct 2025, tested on the holdout)

5,184 breakout and 72 bounce combinations per coin, built only from the main-rule detectors. Chosen by a rule fixed in advance (enough trades, profitable in >= 3 of 4 research years, best t-score). **win % = profit after all costs.** The holdout (Nov 2025 - Oct 2026) was not used to choose anything, so it is the honest result; the research numbers are flattered by the search.

## The rule chosen for each coin and setup

| coin | setup | chosen combination | trades 2022-25 | win % | avg R | trades holdout | win % holdout | avg R holdout |
|---|---|---|---|---|---|---|---|---|
| ETH | breakout | 2h+4h+1D, certainty>=7, stop>=0.4%, drop quietest 0%, BTC 4h agrees, 6h MACD agrees, target 1.5R | 324 | 69% | +0.64 | 79 | 59% | +0.39 |
| ETH | bounce | level tested >= 3x, bounce volume >= 0.8x touch, BTC 4h agrees, target 3R | 182 | 39% | +0.40 | 45 | 44% | +0.41 |
| BTC | breakout | 2h+4h, certainty>=6, stop>=0.6%, drop quietest 0%, 6h MACD agrees, weekly trend agrees, clean risk zone, target 3R | 340 | 38% | +0.33 | 56 | 25% | -0.13 |
| SOL | breakout | 2h+4h+1D, certainty>=6, stop>=0.4%, drop quietest 0%, BTC 4h agrees, 6h MACD agrees, target 1.5R | 1056 | 55% | +0.32 | 327 | 42% | -0.05 |
| SOL | bounce | level tested >= 3x, bounce volume >= 1x touch, BTC 4h agrees, target 3R | 96 | 42% | +0.46 | 40 | 38% | +0.29 |
| BNB | breakout | 2h+4h+1D, certainty>=6, stop>=0.8%, drop quietest 0%, BTC 4h agrees, 6h MACD agrees, target 1.5R | 1034 | 50% | +0.16 | 292 | 41% | -0.08 |
| BNB | bounce | level tested >= 5x, bounce volume >= 0.8x touch, BTC 4h agrees, target 2.5R | 157 | 41% | +0.34 | 59 | 31% | -0.09 |
| XRP | breakout | 2h+4h, certainty>=6, stop>=0.8%, drop quietest 0%, BTC 4h agrees, 6h MACD agrees, target 3R | 878 | 34% | +0.18 | 230 | 27% | -0.03 |
| XRP | bounce | level tested >= 5x, bounce volume >= 1x touch, BTC 4h agrees, target 3R | 69 | 36% | +0.37 | 19 | 47% | +0.63 |
| DOGE | breakout | 2h+4h, certainty>=6, stop>=0.6%, drop quietest 0%, BTC 4h agrees, 6h MACD agrees, target 2.5R | 812 | 38% | +0.21 | 193 | 30% | -0.08 |
| DOGE | bounce | level tested >= 3x, bounce volume >= 0x touch, BTC 4h agrees, target 2.5R | 106 | 42% | +0.31 | 16 | 25% | -0.28 |

No combination qualified (not traded): BTC bounce.

## Win % per coin (both setups; breakouts 3% risk, bounces 2%, max 5x)

| coin | period | trades | per week | win % | avg R | profit factor | account | worst drop |
|---|---|---|---|---|---|---|---|---|
| ETH | 2022 - Oct 2025 | 506 | 2.53 | 58% | +0.55 | 2.25 | 595.63x | -36% |
| ETH | holdout | 124 | 2.40 | 54% | +0.40 | 1.80 | 2.90x | -29% |
| BTC | 2022 - Oct 2025 | 340 | 1.70 | 38% | +0.33 | 1.46 | 5.83x | -66% |
| BTC | holdout | 56 | 1.08 | 25% | -0.13 | 0.84 | 0.67x | -57% |
| SOL | 2022 - Oct 2025 | 1152 | 5.76 | 54% | +0.33 | 1.67 | 4507.35x | -75% |
| SOL | holdout | 367 | 7.10 | 42% | -0.01 | 0.98 | 0.37x | -87% |
| BNB | 2022 - Oct 2025 | 1191 | 5.96 | 49% | +0.18 | 1.33 | 32.63x | -67% |
| BNB | holdout | 351 | 6.79 | 39% | -0.09 | 0.87 | 0.22x | -91% |
| XRP | 2022 - Oct 2025 | 947 | 4.74 | 34% | +0.19 | 1.27 | 4.38x | -97% |
| XRP | holdout | 249 | 4.81 | 29% | +0.02 | 1.03 | 0.45x | -92% |
| DOGE | 2022 - Oct 2025 | 918 | 4.59 | 38% | +0.22 | 1.34 | 17.24x | -88% |
| DOGE | holdout | 209 | 4.04 | 29% | -0.09 | 0.88 | 0.32x | -87% |
| ALL COINS, one account | 2022 - Oct 2025 | 5054 | 25.27 | 46% | +0.27 | 1.46 | 220521.90x | -98% |
| ALL COINS, one account | holdout | 1356 | 26.22 | 37% | -0.00 | 0.99 | 0.01x | -100% |

## How much the search flatters (top 5 combinations per coin and setup, research only)

**ETH breakout**

| combination | trades | win % | avg R | t-score | profitable years (of 4) |
|---|---|---|---|---|---|
| 2h+4h+1D, certainty>=7, stop>=0.4%, drop quietest 0%, BTC 4h agrees, 6h MACD agrees, target 1.5R | 324 | 69% | +0.64 | 9.81 | 4 |
| 2h+4h+1D, certainty>=7, stop>=0.8%, drop quietest 0%, BTC 4h agrees, 6h MACD agrees, target 2R | 306 | 64% | +0.80 | 9.78 | 4 |
| 2h+4h+1D, certainty>=7, stop>=0.4%, drop quietest 0%, BTC 4h agrees, 6h MACD agrees, target 2R | 324 | 64% | +0.78 | 9.76 | 4 |
| 2h+4h+1D, certainty>=7, stop>=0.8%, drop quietest 0%, BTC 4h agrees, 6h MACD agrees, target 1.5R | 306 | 69% | +0.65 | 9.72 | 4 |
| 2h+4h+1D, certainty>=7, stop>=0.6%, drop quietest 0%, BTC 4h agrees, 6h MACD agrees, target 1.5R | 319 | 69% | +0.64 | 9.69 | 4 |

**ETH bounce**

| combination | trades | win % | avg R | t-score | profitable years (of 4) |
|---|---|---|---|---|---|
| level tested >= 3x, bounce volume >= 0.8x touch, BTC 4h agrees, target 3R | 178 | 39% | +0.39 | 2.80 | 4 |
| level tested >= 4x, bounce volume >= 0x touch, BTC 4h agrees, target 4R | 232 | 34% | +0.39 | 2.79 | 4 |
| level tested >= 3x, bounce volume >= 0.8x touch, BTC 4h agrees, target 2.5R | 178 | 42% | +0.35 | 2.77 | 4 |
| level tested >= 4x, bounce volume >= 0.8x touch, BTC 4h agrees, target 3R | 166 | 39% | +0.40 | 2.75 | 4 |
| level tested >= 3x, bounce volume >= 0.8x touch, BTC 4h agrees, target 4R | 178 | 36% | +0.43 | 2.71 | 4 |

**BTC breakout**

| combination | trades | win % | avg R | t-score | profitable years (of 4) |
|---|---|---|---|---|---|
| 2h+4h, certainty>=6, stop>=0.6%, drop quietest 0%, 6h MACD agrees, weekly trend agrees, clean risk zone, target 3R | 340 | 38% | +0.33 | 3.15 | 4 |
| 2h+4h, certainty>=6, stop>=0.4%, drop quietest 0%, 6h MACD agrees, weekly trend agrees, clean risk zone, target 3R | 379 | 38% | +0.31 | 3.11 | 4 |
| 2h+4h+1D, certainty>=7, stop>=0.4%, drop quietest 0%, BTC 4h agrees, clean risk zone, target 3R | 327 | 38% | +0.32 | 3.00 | 3 |
| 2h+4h+1D, certainty>=7, stop>=0.6%, drop quietest 20%, target 3R | 371 | 38% | +0.29 | 2.98 | 3 |
| 2h+4h+1D, certainty>=7, stop>=0.4%, drop quietest 20%, target 3R | 374 | 38% | +0.29 | 2.97 | 3 |

**BTC bounce**

| combination | trades | win % | avg R | t-score | profitable years (of 4) |
|---|---|---|---|---|---|
| level tested >= 5x, bounce volume >= 0x touch, BTC 4h agrees, target 4R | 229 | 26% | +0.11 | 0.84 | 2 |
| level tested >= 4x, bounce volume >= 0x touch, BTC 4h agrees, target 4R | 254 | 25% | +0.07 | 0.53 | 2 |
| level tested >= 3x, bounce volume >= 0x touch, BTC 4h agrees, target 4R | 279 | 25% | +0.06 | 0.51 | 2 |
| level tested >= 5x, bounce volume >= 1x touch, BTC 4h agrees, target 4R | 124 | 24% | +0.05 | 0.29 | 2 |
| level tested >= 5x, bounce volume >= 0.8x touch, BTC 4h agrees, target 4R | 160 | 24% | +0.04 | 0.28 | 2 |

**SOL breakout**

| combination | trades | win % | avg R | t-score | profitable years (of 4) |
|---|---|---|---|---|---|
| 2h+4h+1D, certainty>=6, stop>=0.4%, drop quietest 0%, BTC 4h agrees, 6h MACD agrees, target 1.5R | 1053 | 55% | +0.31 | 8.05 | 4 |
| 2h+4h+1D, certainty>=6, stop>=0.6%, drop quietest 0%, BTC 4h agrees, 6h MACD agrees, target 1.5R | 1050 | 55% | +0.31 | 8.03 | 4 |
| 2h+4h+1D, certainty>=6, stop>=0.8%, drop quietest 0%, BTC 4h agrees, 6h MACD agrees, target 1.5R | 1027 | 55% | +0.31 | 7.80 | 4 |
| 2h+4h+1D, certainty>=6, stop>=0.4%, drop quietest 0%, BTC 4h agrees, target 1.5R | 1406 | 53% | +0.26 | 7.66 | 4 |
| 2h+4h+1D, certainty>=6, stop>=0.6%, drop quietest 0%, BTC 4h agrees, target 1.5R | 1403 | 53% | +0.26 | 7.64 | 4 |

**SOL bounce**

| combination | trades | win % | avg R | t-score | profitable years (of 4) |
|---|---|---|---|---|---|
| level tested >= 3x, bounce volume >= 1x touch, BTC 4h agrees, target 3R | 92 | 40% | +0.41 | 2.15 | 4 |
| level tested >= 3x, bounce volume >= 0.8x touch, BTC 4h agrees, target 3R | 130 | 38% | +0.33 | 2.09 | 4 |
| level tested >= 3x, bounce volume >= 0x touch, BTC 4h agrees, target 3R | 178 | 35% | +0.26 | 1.91 | 4 |
| level tested >= 4x, bounce volume >= 1x touch, BTC 4h agrees, target 3R | 78 | 40% | +0.38 | 1.86 | 4 |
| level tested >= 4x, bounce volume >= 1x touch, BTC 4h agrees, target 4R | 78 | 36% | +0.44 | 1.82 | 3 |

**BNB breakout**

| combination | trades | win % | avg R | t-score | profitable years (of 4) |
|---|---|---|---|---|---|
| 2h+4h+1D, certainty>=6, stop>=0.8%, drop quietest 0%, BTC 4h agrees, 6h MACD agrees, target 1.5R | 1034 | 50% | +0.16 | 4.05 | 3 |
| 2h+4h+1D, certainty>=6, stop>=0.8%, drop quietest 0%, BTC 4h agrees, target 1.5R | 1314 | 49% | +0.14 | 3.92 | 3 |
| 2h+4h+1D, certainty>=6, stop>=0.8%, drop quietest 0%, 6h MACD agrees, target 1.5R | 1228 | 49% | +0.13 | 3.70 | 3 |
| 2h+4h+1D, certainty>=6, stop>=0.6%, drop quietest 0%, BTC 4h agrees, 6h MACD agrees, target 1.5R | 1133 | 49% | +0.14 | 3.68 | 3 |
| 2h+4h+1D, certainty>=6, stop>=0.4%, drop quietest 0%, BTC 4h agrees, 6h MACD agrees, target 1.5R | 1210 | 50% | +0.13 | 3.63 | 3 |

**BNB bounce**

| combination | trades | win % | avg R | t-score | profitable years (of 4) |
|---|---|---|---|---|---|
| level tested >= 5x, bounce volume >= 0.8x touch, BTC 4h agrees, target 2.5R | 157 | 41% | +0.34 | 2.58 | 4 |
| level tested >= 5x, bounce volume >= 1x touch, target 3R | 142 | 39% | +0.40 | 2.57 | 3 |
| level tested >= 5x, bounce volume >= 1x touch, target 2.5R | 142 | 42% | +0.35 | 2.48 | 3 |
| level tested >= 5x, bounce volume >= 0x touch, BTC 4h agrees, target 2.5R | 223 | 39% | +0.28 | 2.48 | 4 |
| level tested >= 5x, bounce volume >= 0.8x touch, target 2.5R | 197 | 40% | +0.29 | 2.47 | 3 |

**XRP breakout**

| combination | trades | win % | avg R | t-score | profitable years (of 4) |
|---|---|---|---|---|---|
| 2h+4h, certainty>=6, stop>=0.8%, drop quietest 0%, BTC 4h agrees, 6h MACD agrees, target 3R | 878 | 34% | +0.18 | 2.91 | 3 |
| 2h+4h, certainty>=6, stop>=0.8%, drop quietest 0%, BTC 4h agrees, target 3R | 1135 | 33% | +0.16 | 2.86 | 3 |
| 2h+4h, certainty>=6, stop>=0.6%, drop quietest 0%, BTC 4h agrees, 6h MACD agrees, target 3R | 935 | 33% | +0.17 | 2.77 | 4 |
| 2h+4h+1D, certainty>=6, stop>=0.8%, drop quietest 0%, BTC 4h agrees, target 3R | 1288 | 32% | +0.14 | 2.72 | 3 |
| 2h+4h, certainty>=6, stop>=0.4%, drop quietest 0%, BTC 4h agrees, 6h MACD agrees, target 3R | 960 | 33% | +0.16 | 2.65 | 4 |

**XRP bounce**

| combination | trades | win % | avg R | t-score | profitable years (of 4) |
|---|---|---|---|---|---|
| level tested >= 5x, bounce volume >= 1x touch, BTC 4h agrees, target 3R | 68 | 35% | +0.33 | 1.44 | 4 |
| level tested >= 5x, bounce volume >= 1x touch, BTC 4h agrees, target 4R | 68 | 31% | +0.34 | 1.30 | 3 |
| level tested >= 5x, bounce volume >= 1x touch, BTC 4h agrees, target 2.5R | 68 | 38% | +0.26 | 1.26 | 4 |
| level tested >= 5x, bounce volume >= 1x touch, target 4R | 89 | 28% | +0.24 | 1.09 | 4 |
| level tested >= 5x, bounce volume >= 1x touch, target 3R | 89 | 31% | +0.19 | 0.99 | 3 |

**DOGE breakout**

| combination | trades | win % | avg R | t-score | profitable years (of 4) |
|---|---|---|---|---|---|
| 2h+4h, certainty>=6, stop>=0.6%, drop quietest 0%, BTC 4h agrees, 6h MACD agrees, target 2.5R | 812 | 38% | +0.21 | 3.59 | 3 |
| 2h+4h, certainty>=6, stop>=0.6%, drop quietest 0%, BTC 4h agrees, 6h MACD agrees, clean risk zone, target 2.5R | 580 | 39% | +0.25 | 3.58 | 3 |
| 2h+4h, certainty>=6, stop>=0.4%, drop quietest 0%, BTC 4h agrees, 6h MACD agrees, clean risk zone, target 2.5R | 591 | 39% | +0.25 | 3.53 | 3 |
| 2h+4h, certainty>=6, stop>=0.4%, drop quietest 0%, BTC 4h agrees, 6h MACD agrees, target 2.5R | 825 | 38% | +0.20 | 3.49 | 3 |
| 2h+4h, certainty>=7, stop>=0.6%, drop quietest 0%, BTC 4h agrees, 6h MACD agrees, clean risk zone, target 2.5R | 139 | 46% | +0.49 | 3.39 | 3 |

**DOGE bounce**

| combination | trades | win % | avg R | t-score | profitable years (of 4) |
|---|---|---|---|---|---|
| level tested >= 3x, bounce volume >= 0x touch, BTC 4h agrees, target 2.5R | 102 | 40% | +0.27 | 1.64 | 3 |
| level tested >= 5x, bounce volume >= 0x touch, BTC 4h agrees, target 3R | 69 | 41% | +0.34 | 1.59 | 4 |
| level tested >= 3x, bounce volume >= 0x touch, BTC 4h agrees, target 3R | 102 | 37% | +0.27 | 1.55 | 4 |
| level tested >= 3x, bounce volume >= 0x touch, BTC 4h agrees, target 2R | 102 | 43% | +0.20 | 1.40 | 3 |
| level tested >= 3x, bounce volume >= 0x touch, target 2.5R | 130 | 38% | +0.20 | 1.40 | 2 |

