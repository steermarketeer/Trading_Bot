# Why the middle-band hold pumps again, and why it sometimes fails

Pump -> 3+ sideways closes above the middle band -> first touch of the middle band. **Hold** (the touch closes above the middle band): success = price takes out every high so far before a close below the touch low (within 30 candles). **Fail** (the touch closes at / below it): success = price takes out the sideways low before a close above the touch high. Mirrored for dumps. **noise**: the time-shift test (400 shifts, clustering kept); below 0.01 = real, and the holdout must point the same way.

## hold -> does it pump again? · 1h + 4h + 1D together: 1444 cases 2020 - Oct 2025, **right 48%** (fair test); holdout 204, right 49%

Far targets (description only, not a fair test): 32% took out every high so far before a close below the touch low.

| condition at the touch | cases with it | fair test: with it | fair test: without | difference | noise | holdout cases with it | holdout difference | real (p<0.01, holdout agrees) / likely (p<0.05) |
|---|---|---|---|---|---|---|---|---|
| liquidity: crowd leaning with the pump (long/short ratio above its 30-day median) | 231 | 41% | 48% | -7 pts | 0.047 | 58 | -6 pts | likely |
| sideways: equal highs at the top (liquidity above) | 1369 | 47% | 51% | -3 pts | 0.656 | 198 | -35 pts |  |
| touch: RSI 40-50 | 111 | 45% | 48% | -3 pts | 0.621 | 17 | -2 pts |  |
| sideways: tight (range <= 2 ATR) | 697 | 46% | 49% | -3 pts | 0.362 | 107 | -3 pts |  |
| touch: wick rejection (close in the top half) | 585 | 46% | 48% | -2 pts | 0.554 | 88 | -8 pts |  |
| context: higher timeframe above its EMA 50 | 1038 | 47% | 48% | -2 pts | 0.683 | 143 | +9 pts |  |
| context: daily above its EMA 200 | 715 | 46% | 48% | -1 pts | 0.701 | 109 | +11 pts |  |
| touch: volume >= 1.5x the sideways average | 340 | 48% | 47% | +1 pts | 0.908 | 63 | +9 pts |  |
| touch: swept the sideways low | 862 | 48% | 47% | +1 pts | 0.696 | 117 | +5 pts |  |
| sideways: 3+ rejections at the upper band | 227 | 49% | 47% | +2 pts | 0.661 | 51 | +10 pts |  |
| context: higher timeframe at / above its upper band | 597 | 49% | 47% | +2 pts | 0.514 | 75 | +7 pts |  |
| sideways: a higher high than the pump candle | 947 | 48% | 46% | +2 pts | 0.392 | 121 | +18 pts |  |
| touch: deep (> 0.25 ATR below the middle band) | 175 | 50% | 47% | +3 pts | 0.541 | 28 | +22 pts |  |
| pump: close > 0.5 ATR beyond the band | 281 | 50% | 47% | +3 pts | 0.389 | 40 | +4 pts |  |
| sideways: volume dried up (<= 0.6x the pump's) | 810 | 49% | 45% | +4 pts | 0.177 | 118 | +2 pts |  |
| pump: volume >= 2x | 410 | 50% | 46% | +4 pts | 0.212 | 69 | +11 pts |  |
| liquidity: open interest rose > 5% during the sideways | 32 | 50% | 46% | +4 pts | 0.766 | 2 |  |  |
| sideways: 6+ candles | 933 | 49% | 45% | +4 pts | 0.122 | 129 | -5 pts |  |
| pump: leg into the pump >= 4 ATR | 1149 | 48% | 44% | +5 pts | 0.175 | 163 | -24 pts |  |
| sideways: bands contracted (width <= 0.8x the pump's) | 284 | 51% | 47% | +5 pts | 0.130 | 52 | -4 pts |  |

**The trader's own definition, 'pump again' = a new high above everything so far** (before a close below the touch low; same far target for every case, so conditions can be compared with each other):

| condition at the touch | cases with it | new high: with it | new high: without | difference | noise | holdout cases with it | holdout difference | real (p<0.01, holdout agrees) / likely (p<0.05) |
|---|---|---|---|---|---|---|---|---|
| touch: RSI 40-50 | 111 | 16% | 33% | -17 pts | 0.002 | 17 | -13 pts | yes |
| liquidity: crowd leaning with the pump (long/short ratio above its 30-day median) | 231 | 26% | 33% | -7 pts | 0.050 | 58 | +2 pts |  |
| liquidity: open interest rose > 5% during the sideways | 32 | 28% | 32% | -4 pts | 0.723 | 2 |  |  |
| sideways: volume dried up (<= 0.6x the pump's) | 810 | 30% | 33% | -3 pts | 0.294 | 118 | -7 pts |  |
| pump: close > 0.5 ATR beyond the band | 281 | 30% | 32% | -2 pts | 0.603 | 40 | +0 pts |  |
| pump: volume >= 2x | 410 | 30% | 32% | -2 pts | 0.581 | 69 | +5 pts |  |
| touch: swept the sideways low | 862 | 31% | 32% | -1 pts | 0.643 | 117 | +2 pts |  |
| context: higher timeframe at / above its upper band | 597 | 31% | 32% | -1 pts | 0.773 | 75 | +5 pts |  |
| sideways: equal highs at the top (liquidity above) | 1369 | 32% | 31% | +1 pts | 0.875 | 198 | -38 pts |  |
| sideways: tight (range <= 2 ATR) | 697 | 32% | 31% | +1 pts | 0.628 | 107 | +0 pts |  |
| sideways: 6+ candles | 933 | 32% | 31% | +1 pts | 0.536 | 129 | -1 pts |  |
| sideways: 3+ rejections at the upper band | 227 | 33% | 31% | +2 pts | 0.519 | 51 | +2 pts |  |
| pump: leg into the pump >= 4 ATR | 1149 | 32% | 30% | +2 pts | 0.546 | 163 | -11 pts |  |
| sideways: a higher high than the pump candle | 947 | 33% | 29% | +4 pts | 0.102 | 121 | +12 pts |  |
| context: higher timeframe above its EMA 50 | 1038 | 33% | 28% | +4 pts | 0.095 | 143 | +8 pts |  |
| sideways: bands contracted (width <= 0.8x the pump's) | 284 | 38% | 30% | +8 pts | 0.022 | 52 | -1 pts |  |
| context: daily above its EMA 200 | 715 | 35% | 27% | +8 pts | 0.010 | 109 | +7 pts | yes |
| touch: deep (> 0.25 ATR below the middle band) | 175 | 40% | 30% | +10 pts | 0.005 | 28 | +23 pts | yes |
| touch: volume >= 1.5x the sideways average | 340 | 41% | 29% | +12 pts | 0.002 | 63 | +26 pts | yes |
| touch: wick rejection (close in the top half) | 585 | 40% | 26% | +14 pts | 0.002 | 88 | +15 pts | yes |

## hold -> does it pump again? · 4h: 266 cases 2020 - Oct 2025, **right 49%** (fair test); holdout 43, right 53%

Far targets (description only, not a fair test): 34% took out every high so far before a close below the touch low.

| condition at the touch | cases with it | fair test: with it | fair test: without | difference | noise | holdout cases with it | holdout difference | real (p<0.01, holdout agrees) / likely (p<0.05) |
|---|---|---|---|---|---|---|---|---|
| liquidity: crowd leaning with the pump (long/short ratio above its 30-day median) | 40 | 40% | 50% | -10 pts | 0.272 | 11 | +1 pts |  |
| touch: volume >= 1.5x the sideways average | 66 | 44% | 51% | -7 pts | 0.284 | 10 | +35 pts |  |
| sideways: tight (range <= 2 ATR) | 112 | 46% | 52% | -6 pts | 0.319 | 21 | -11 pts |  |
| touch: wick rejection (close in the top half) | 96 | 46% | 51% | -5 pts | 0.434 | 12 | +53 pts |  |
| context: daily above its EMA 200 | 138 | 46% | 51% | -5 pts | 0.541 | 27 | +25 pts |  |
| touch: RSI 40-50 | 19 | 47% | 49% | -2 pts | 1.000 | 6 | -23 pts |  |
| touch: deep (> 0.25 ATR below the middle band) | 37 | 49% | 49% | -1 pts | 1.000 | 7 | +56 pts |  |
| context: higher timeframe above its EMA 50 | 185 | 49% | 49% | +0 pts | 1.000 | 29 | +37 pts |  |
| touch: swept the sideways low | 139 | 50% | 49% | +1 pts | 0.953 | 24 | -17 pts |  |
| context: higher timeframe at / above its upper band | 120 | 52% | 47% | +4 pts | 0.621 | 18 | +4 pts |  |
| sideways: bands contracted (width <= 0.8x the pump's) | 54 | 56% | 48% | +8 pts | 0.382 | 12 | +18 pts |  |
| sideways: 3+ rejections at the upper band | 41 | 56% | 48% | +8 pts | 0.362 | 11 | +1 pts |  |
| sideways: equal highs at the top (liquidity above) | 251 | 50% | 40% | +10 pts | 0.643 | 42 |  |  |
| sideways: volume dried up (<= 0.6x the pump's) | 109 | 55% | 45% | +10 pts | 0.177 | 20 | -7 pts |  |
| pump: close > 0.5 ATR beyond the band | 47 | 57% | 47% | +10 pts | 0.222 | 8 | +11 pts |  |
| sideways: 6+ candles | 170 | 53% | 43% | +10 pts | 0.125 | 32 | -14 pts |  |
| sideways: a higher high than the pump candle | 196 | 53% | 40% | +13 pts | 0.105 | 29 | +26 pts |  |
| pump: leg into the pump >= 4 ATR | 217 | 52% | 39% | +13 pts | 0.097 | 36 | -21 pts |  |
| pump: volume >= 2x | 53 | 60% | 46% | +14 pts | 0.092 | 13 | +23 pts |  |

**The trader's own definition, 'pump again' = a new high above everything so far** (before a close below the touch low; same far target for every case, so conditions can be compared with each other):

| condition at the touch | cases with it | new high: with it | new high: without | difference | noise | holdout cases with it | holdout difference | real (p<0.01, holdout agrees) / likely (p<0.05) |
|---|---|---|---|---|---|---|---|---|
| liquidity: crowd leaning with the pump (long/short ratio above its 30-day median) | 40 | 28% | 37% | -9 pts | 0.409 | 11 | -22 pts |  |
| touch: RSI 40-50 | 19 | 26% | 34% | -8 pts | 0.648 | 6 | -21 pts |  |
| touch: swept the sideways low | 139 | 31% | 37% | -6 pts | 0.332 | 24 | -22 pts |  |
| sideways: volume dried up (<= 0.6x the pump's) | 109 | 32% | 35% | -3 pts | 0.656 | 20 | -28 pts |  |
| context: higher timeframe at / above its upper band | 120 | 32% | 35% | -2 pts | 0.708 | 18 | +7 pts |  |
| pump: volume >= 2x | 53 | 34% | 34% | +0 pts | 1.000 | 13 | -6 pts |  |
| pump: close > 0.5 ATR beyond the band | 47 | 34% | 34% | +0 pts | 1.000 | 8 | +3 pts |  |
| sideways: tight (range <= 2 ATR) | 112 | 35% | 33% | +2 pts | 0.808 | 21 | -12 pts |  |
| context: higher timeframe above its EMA 50 | 185 | 35% | 31% | +3 pts | 0.686 | 29 | +20 pts |  |
| pump: leg into the pump >= 4 ATR | 217 | 35% | 31% | +4 pts | 0.656 | 36 | -10 pts |  |
| sideways: 6+ candles | 170 | 36% | 29% | +7 pts | 0.249 | 32 | -2 pts |  |
| sideways: equal highs at the top (liquidity above) | 251 | 34% | 27% | +8 pts | 0.589 | 42 |  |  |
| sideways: bands contracted (width <= 0.8x the pump's) | 54 | 41% | 32% | +9 pts | 0.319 | 12 | +9 pts |  |
| context: daily above its EMA 200 | 138 | 38% | 29% | +9 pts | 0.185 | 27 | +6 pts |  |
| touch: volume >= 1.5x the sideways average | 66 | 41% | 32% | +9 pts | 0.187 | 10 | +33 pts |  |
| sideways: a higher high than the pump candle | 196 | 37% | 24% | +13 pts | 0.052 | 29 | +9 pts |  |
| touch: wick rejection (close in the top half) | 96 | 43% | 29% | +14 pts | 0.010 | 12 | +79 pts | yes |
| touch: deep (> 0.25 ATR below the middle band) | 37 | 46% | 32% | +14 pts | 0.142 | 7 | +44 pts |  |
| sideways: 3+ rejections at the upper band | 41 | 49% | 31% | +18 pts | 0.025 | 11 | -10 pts |  |

## hold -> does it pump again? · 1D: 44 cases 2020 - Oct 2025, **right 61%** (fair test); holdout 3, right 33%

Far targets (description only, not a fair test): 39% took out every high so far before a close below the touch low.

| condition at the touch | cases with it | fair test: with it | fair test: without | difference | noise | holdout cases with it | holdout difference | real (p<0.01, holdout agrees) / likely (p<0.05) |
|---|---|---|---|---|---|---|---|---|
| sideways: a higher high than the pump candle | 29 | 52% | 80% | -28 pts | 1.000 | 2 |  |  |
| touch: wick rejection (close in the top half) | 15 | 53% | 66% | -12 pts | 1.000 | 0 |  |  |
| context: higher timeframe at / above its upper band | 18 | 56% | 67% | -11 pts | 1.000 | 0 |  |  |
| sideways: volume dried up (<= 0.6x the pump's) | 16 | 56% | 64% | -8 pts | 1.000 | 1 |  |  |
| sideways: 6+ candles | 28 | 61% | 62% | -2 pts | 1.000 | 2 |  |  |
| sideways: tight (range <= 2 ATR) | 22 | 64% | 59% | +5 pts | 1.000 | 1 |  |  |
| touch: swept the sideways low | 26 | 65% | 56% | +10 pts | 1.000 | 1 |  |  |

**The trader's own definition, 'pump again' = a new high above everything so far** (before a close below the touch low; same far target for every case, so conditions can be compared with each other):

| condition at the touch | cases with it | new high: with it | new high: without | difference | noise | holdout cases with it | holdout difference | real (p<0.01, holdout agrees) / likely (p<0.05) |
|---|---|---|---|---|---|---|---|---|
| sideways: volume dried up (<= 0.6x the pump's) | 16 | 19% | 50% | -31 pts | 1.000 | 1 |  |  |
| sideways: 6+ candles | 28 | 29% | 56% | -28 pts | 1.000 | 2 |  |  |
| sideways: a higher high than the pump candle | 29 | 34% | 47% | -12 pts | 1.000 | 2 |  |  |
| context: higher timeframe at / above its upper band | 18 | 33% | 42% | -8 pts | 1.000 | 0 |  |  |
| touch: wick rejection (close in the top half) | 15 | 40% | 38% | +2 pts | 1.000 | 0 |  |  |
| sideways: tight (range <= 2 ATR) | 22 | 41% | 36% | +5 pts | 1.000 | 1 |  |  |
| touch: swept the sideways low | 26 | 50% | 22% | +28 pts | 1.000 | 1 |  |  |

## fail -> does it dump? · 1h + 4h + 1D together: 396 cases 2020 - Oct 2025, **right 51%** (fair test); holdout 68, right 47%

Far targets (description only, not a fair test): 94% took out the sideways low before a close above the touch high.

| condition at the touch | cases with it | fair test: with it | fair test: without | difference | noise | holdout cases with it | holdout difference | real (p<0.01, holdout agrees) / likely (p<0.05) |
|---|---|---|---|---|---|---|---|---|
| touch: wick rejection (close in the top half) | 16 | 38% | 51% | -14 pts | 0.314 | 3 |  |  |
| sideways: 3+ rejections at the upper band | 59 | 41% | 53% | -12 pts | 0.125 | 15 | +8 pts |  |
| sideways: bands contracted (width <= 0.8x the pump's) | 83 | 45% | 52% | -8 pts | 0.202 | 12 | -17 pts |  |
| pump: volume >= 2x | 100 | 46% | 52% | -6 pts | 0.282 | 21 | -27 pts |  |
| liquidity: crowd leaning with the pump (long/short ratio above its 30-day median) | 96 | 46% | 52% | -6 pts | 0.339 | 20 | -3 pts |  |
| touch: RSI 40-50 | 217 | 49% | 53% | -3 pts | 0.616 | 33 | -15 pts |  |
| sideways: volume dried up (<= 0.6x the pump's) | 199 | 50% | 52% | -2 pts | 0.686 | 38 | -17 pts |  |
| pump: leg into the pump >= 4 ATR | 311 | 50% | 52% | -1 pts | 0.870 | 62 | -22 pts |  |
| sideways: a higher high than the pump candle | 252 | 50% | 51% | -1 pts | 0.903 | 36 | -11 pts |  |
| sideways: 6+ candles | 242 | 50% | 51% | -1 pts | 0.940 | 38 | -17 pts |  |
| sideways: tight (range <= 2 ATR) | 238 | 50% | 51% | -1 pts | 0.888 | 44 | +28 pts |  |
| touch: volume >= 1.5x the sideways average | 253 | 51% | 51% | -0 pts | 1.000 | 50 | +11 pts |  |
| context: higher timeframe above its EMA 50 | 272 | 51% | 51% | -0 pts | 1.000 | 53 | -8 pts |  |
| context: daily above its EMA 200 | 193 | 50% | 50% | +0 pts | 1.000 | 34 | -6 pts |  |
| pump: close > 0.5 ATR beyond the band | 80 | 51% | 51% | +1 pts | 1.000 | 17 | -31 pts |  |
| touch: RSI < 40 | 17 | 53% | 51% | +2 pts | 1.000 | 7 | +27 pts |  |
| context: higher timeframe at / above its upper band | 144 | 53% | 49% | +3 pts | 0.551 | 39 | -8 pts |  |
| touch: deep (> 0.25 ATR below the middle band) | 339 | 51% | 47% | +4 pts | 0.641 | 57 | +13 pts |  |
| touch: swept the sideways low | 343 | 52% | 40% | +13 pts | 0.160 | 58 | +20 pts |  |
| sideways: equal highs at the top (liquidity above) | 381 | 52% | 27% | +25 pts | 0.092 | 63 | +8 pts |  |

## fail -> does it dump? · 4h: 86 cases 2020 - Oct 2025, **right 56%** (fair test); holdout 15, right 47%

Far targets (description only, not a fair test): 98% took out the sideways low before a close above the touch high.

| condition at the touch | cases with it | fair test: with it | fair test: without | difference | noise | holdout cases with it | holdout difference | real (p<0.01, holdout agrees) / likely (p<0.05) |
|---|---|---|---|---|---|---|---|---|
| touch: volume >= 1.5x the sideways average | 59 | 53% | 63% | -10 pts | 0.456 | 13 |  |  |
| pump: close > 0.5 ATR beyond the band | 18 | 50% | 57% | -7 pts | 0.613 | 2 |  |  |
| context: higher timeframe above its EMA 50 | 58 | 53% | 61% | -7 pts | 0.723 | 9 | -6 pts |  |
| sideways: a higher high than the pump candle | 51 | 53% | 60% | -7 pts | 0.668 | 5 | -10 pts |  |
| context: higher timeframe at / above its upper band | 25 | 52% | 57% | -5 pts | 0.808 | 9 | -33 pts |  |
| liquidity: crowd leaning with the pump (long/short ratio above its 30-day median) | 30 | 53% | 55% | -2 pts | 1.000 | 8 | -20 pts |  |
| touch: RSI 40-50 | 55 | 56% | 55% | +2 pts | 1.000 | 11 |  |  |
| sideways: volume dried up (<= 0.6x the pump's) | 31 | 58% | 55% | +4 pts | 0.868 | 8 | -20 pts |  |
| sideways: tight (range <= 2 ATR) | 56 | 57% | 53% | +4 pts | 0.835 | 11 |  |  |
| pump: leg into the pump >= 4 ATR | 67 | 57% | 53% | +4 pts | 0.800 | 14 |  |  |
| context: daily above its EMA 200 | 44 | 59% | 53% | +6 pts | 0.643 | 6 | -22 pts |  |
| pump: volume >= 2x | 18 | 61% | 54% | +7 pts | 0.813 | 4 |  |  |
| sideways: 6+ candles | 44 | 59% | 52% | +7 pts | 0.763 | 8 | +7 pts |  |

## fail -> does it dump? · 1D: 20 cases 2020 - Oct 2025, **right 55%** (fair test); holdout 2, right 0%

Far targets (description only, not a fair test): 90% took out the sideways low before a close above the touch high.

