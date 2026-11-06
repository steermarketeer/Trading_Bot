# Why the middle-band hold pumps again, and why it sometimes fails

Pump -> 3+ sideways closes above the middle band -> first touch of the middle band. **Hold** = the touch closes above the middle band; **fail** = at / below it. Mirrored for dumps. Outcomes: the **fair test** (1.5 ATR either way, coin flip 50%) and the trader's **far target** (hold: a new high above everything so far; fail: the sideways low; before a close 0.5 ATR beyond the middle band, within 30 candles). The far-target difference is shown raw and **at the same distances** (within groups of the same timeframe, distance to the target and distance to the failure level); only the same-distance column removes the geometry. **real** = p < 0.01 at the same distances and the holdout points the same way.

## hold -> does it pump again? · 1h + 4h + 1D together: 1449 cases 2020 - Oct 2025, **right 47%** (fair test); holdout 204, right 49%

Far target (the trader's definition): 40% made a new high above everything so far before a close 0.5 ATR below the middle band.

| condition at the touch | cases with it | fair test: difference | fair test: noise | far target: raw difference | far target: same distances | same distances: noise | holdout cases with it | holdout far difference (raw) | real (p<0.01 at same distances, holdout agrees) / likely (p<0.05) |
|---|---|---|---|---|---|---|---|---|---|
| liquidity: crowd leaning with the pump (long/short ratio above its 30-day median) | 232 | -7 pts | 0.047 | -6 pts | -9 pts | 0.030 | 58 | +4 pts |  |
| sideways: tight (range <= 2 ATR) | 702 | -3 pts | 0.329 | -0 pts | -5 pts | 0.075 | 107 | -1 pts |  |
| pump: volume >= 2x | 412 | +4 pts | 0.219 | -5 pts | -4 pts | 0.177 | 69 | +9 pts |  |
| touch: RSI 40-50 | 111 | -3 pts | 0.671 | -16 pts | -4 pts | 0.591 | 17 | -20 pts |  |
| touch: swept the sideways low | 866 | +1 pts | 0.661 | -6 pts | -3 pts | 0.284 | 117 | -10 pts |  |
| pump: close > 0.5 ATR beyond the band | 282 | +3 pts | 0.449 | -3 pts | -3 pts | 0.446 | 40 | -2 pts |  |
| sideways: volume dried up (<= 0.6x the pump's) | 814 | +4 pts | 0.209 | -4 pts | -2 pts | 0.304 | 118 | -8 pts |  |
| context: higher timeframe at / above its upper band | 599 | +2 pts | 0.504 | -2 pts | -1 pts | 0.726 | 75 | -1 pts |  |
| sideways: 3+ rejections at the upper band | 229 | +1 pts | 0.781 | +5 pts | -1 pts | 0.840 | 51 | +5 pts |  |
| context: higher timeframe above its EMA 50 | 1042 | -2 pts | 0.658 | +1 pts | -0 pts | 0.963 | 143 | +10 pts |  |
| liquidity: open interest rose > 5% during the sideways | 32 | +4 pts | 0.721 | +0 pts | +0 pts | 0.983 | 2 |  |  |
| touch: wick rejection (close in the top half) | 586 | -1 pts | 0.641 | +13 pts | +1 pts | 0.845 | 88 | +13 pts |  |
| touch: deep (> 0.25 ATR below the middle band) | 176 | +2 pts | 0.618 | -1 pts | +3 pts | 0.579 | 28 | +14 pts |  |
| sideways: a higher high than the pump candle | 952 | +2 pts | 0.387 | +7 pts | +3 pts | 0.299 | 121 | +13 pts |  |
| touch: volume >= 1.5x the sideways average | 341 | +1 pts | 0.898 | +6 pts | +3 pts | 0.267 | 63 | +16 pts |  |
| pump: leg into the pump >= 4 ATR | 1150 | +5 pts | 0.172 | +1 pts | +4 pts | 0.224 | 163 | -12 pts |  |
| sideways: 6+ candles | 934 | +5 pts | 0.082 | +3 pts | +4 pts | 0.140 | 129 | +1 pts |  |
| context: daily above its EMA 200 | 718 | -1 pts | 0.666 | +9 pts | +5 pts | 0.080 | 109 | +3 pts |  |
| sideways: equal highs at the top (liquidity above) | 1374 | -3 pts | 0.571 | +3 pts | +7 pts | 0.332 | 198 | -26 pts |  |
| sideways: bands contracted (width <= 0.8x the pump's) | 284 | +5 pts | 0.150 | +10 pts | +8 pts | 0.017 | 52 | +6 pts | likely |

## hold -> does it pump again? · 4h: 267 cases 2020 - Oct 2025, **right 49%** (fair test); holdout 43, right 53%

Far target (the trader's definition): 42% made a new high above everything so far before a close 0.5 ATR below the middle band.

| condition at the touch | cases with it | fair test: difference | fair test: noise | far target: raw difference | far target: same distances | same distances: noise | holdout cases with it | holdout far difference (raw) | real (p<0.01 at same distances, holdout agrees) / likely (p<0.05) |
|---|---|---|---|---|---|---|---|---|---|
| liquidity: crowd leaning with the pump (long/short ratio above its 30-day median) | 40 | -10 pts | 0.284 | -12 pts | -14 pts | 0.160 | 11 | -23 pts |  |
| sideways: tight (range <= 2 ATR) | 113 | -7 pts | 0.314 | +0 pts | -6 pts | 0.367 | 21 | -21 pts |  |
| sideways: volume dried up (<= 0.6x the pump's) | 110 | +9 pts | 0.182 | -3 pts | -3 pts | 0.721 | 20 | -36 pts |  |
| touch: swept the sideways low | 140 | +0 pts | 1.000 | -6 pts | -2 pts | 0.738 | 24 | -34 pts |  |
| sideways: bands contracted (width <= 0.8x the pump's) | 54 | +8 pts | 0.359 | +8 pts | -1 pts | 0.938 | 12 | +20 pts |  |
| pump: volume >= 2x | 54 | +13 pts | 0.105 | -1 pts | -0 pts | 0.993 | 13 | -8 pts |  |
| context: higher timeframe at / above its upper band | 120 | +5 pts | 0.546 | +0 pts | +2 pts | 0.783 | 18 | +0 pts |  |
| sideways: equal highs at the top (liquidity above) | 252 | +10 pts | 0.641 | +9 pts | +3 pts | 0.835 | 42 |  |  |
| pump: close > 0.5 ATR beyond the band | 47 | +10 pts | 0.244 | -1 pts | +3 pts | 0.698 | 8 | +7 pts |  |
| sideways: a higher high than the pump candle | 197 | +12 pts | 0.102 | +12 pts | +4 pts | 0.554 | 29 | +23 pts |  |
| sideways: 3+ rejections at the upper band | 41 | +8 pts | 0.377 | +14 pts | +5 pts | 0.606 | 11 | +2 pts |  |
| sideways: 6+ candles | 170 | +11 pts | 0.110 | +12 pts | +10 pts | 0.127 | 32 | -2 pts |  |
| context: higher timeframe above its EMA 50 | 186 | +0 pts | 1.000 | +9 pts | +10 pts | 0.209 | 29 | +23 pts |  |
| context: daily above its EMA 200 | 139 | -5 pts | 0.569 | +10 pts | +10 pts | 0.122 | 27 | +1 pts |  |
| touch: wick rejection (close in the top half) | 96 | -5 pts | 0.486 | +12 pts | +11 pts | 0.249 | 12 | +66 pts |  |
| touch: volume >= 1.5x the sideways average | 66 | -7 pts | 0.347 | +5 pts | +11 pts | 0.165 | 10 | +21 pts |  |
| pump: leg into the pump >= 4 ATR | 217 | +14 pts | 0.052 | +9 pts | +13 pts | 0.137 | 36 | -15 pts |  |
| touch: deep (> 0.25 ATR below the middle band) | 37 | -0 pts | 1.000 | +5 pts | +15 pts | 0.122 | 7 | +33 pts |  |
| touch: RSI 40-50 | 19 | -2 pts | 1.000 | -11 pts | +19 pts | 0.317 | 6 | -32 pts |  |

## hold -> does it pump again? · 1D: 44 cases 2020 - Oct 2025, **right 61%** (fair test); holdout 3, right 33%

Far target (the trader's definition): 48% made a new high above everything so far before a close 0.5 ATR below the middle band.

| condition at the touch | cases with it | fair test: difference | fair test: noise | far target: raw difference | far target: same distances | same distances: noise | holdout cases with it | holdout far difference (raw) | real (p<0.01 at same distances, holdout agrees) / likely (p<0.05) |
|---|---|---|---|---|---|---|---|---|---|
| sideways: 6+ candles | 28 | -2 pts | not tested (n < 60) | -23 pts |  | not tested (n < 60) | 2 |  |  |
| sideways: tight (range <= 2 ATR) | 22 | +5 pts | not tested (n < 60) | -5 pts |  | not tested (n < 60) | 1 |  |  |
| sideways: volume dried up (<= 0.6x the pump's) | 16 | -8 pts | not tested (n < 60) | -46 pts |  | not tested (n < 60) | 1 |  |  |
| sideways: a higher high than the pump candle | 29 | -28 pts | not tested (n < 60) | +2 pts |  | not tested (n < 60) | 2 |  |  |
| touch: wick rejection (close in the top half) | 15 | -12 pts | not tested (n < 60) | -2 pts |  | not tested (n < 60) | 0 |  |  |
| touch: swept the sideways low | 26 | +10 pts | not tested (n < 60) | +15 pts |  | not tested (n < 60) | 1 |  |  |
| context: higher timeframe at / above its upper band | 18 | -11 pts | not tested (n < 60) | -6 pts |  | not tested (n < 60) | 0 |  |  |

## fail -> does it dump? · 1h + 4h + 1D together: 398 cases 2020 - Oct 2025, **right 51%** (fair test); holdout 68, right 47%

Far target (the trader's definition): 93% took out the sideways low before a close 0.5 ATR above the middle band.

| condition at the touch | cases with it | fair test: difference | fair test: noise | far target: raw difference | far target: same distances | same distances: noise | holdout cases with it | holdout far difference (raw) | real (p<0.01 at same distances, holdout agrees) / likely (p<0.05) |
|---|---|---|---|---|---|---|---|---|---|
| sideways: bands contracted (width <= 0.8x the pump's) | 83 | -8 pts | 0.287 | -25 pts | -12 pts | 0.002 | 12 | -30 pts | yes |
| pump: leg into the pump >= 4 ATR | 313 | -1 pts | 0.885 | -8 pts | -5 pts | 0.269 | 62 | -10 pts |  |
| sideways: 6+ candles | 243 | -1 pts | 0.835 | -11 pts | -4 pts | 1.000 | 38 | -16 pts |  |
| sideways: a higher high than the pump candle | 253 | -2 pts | 0.843 | -6 pts | -3 pts | 0.279 | 36 | -17 pts |  |
| context: higher timeframe above its EMA 50 | 273 | +1 pts | 1.000 | -7 pts | -1 pts | 0.763 | 53 | -3 pts |  |
| context: higher timeframe at / above its upper band | 145 | +3 pts | 0.599 | -5 pts | -1 pts | 0.678 | 39 | -9 pts |  |
| sideways: 3+ rejections at the upper band | 59 | -12 pts | 0.150 | -6 pts | -1 pts | 0.778 | 15 | -14 pts |  |
| sideways: equal highs at the top (liquidity above) | 383 | +25 pts | 0.060 | -7 pts | +0 pts | 1.000 | 63 | -10 pts |  |
| touch: RSI < 40 | 17 | +2 pts | 1.000 | +7 pts | +0 pts | 1.000 | 7 | +10 pts |  |
| context: daily above its EMA 200 | 194 | +1 pts | 0.925 | -1 pts | +1 pts | 0.778 | 34 | +0 pts |  |
| pump: close > 0.5 ATR beyond the band | 80 | +1 pts | 1.000 | -1 pts | +1 pts | 0.723 | 17 | -20 pts |  |
| touch: volume >= 1.5x the sideways average | 255 | -0 pts | 1.000 | +9 pts | +2 pts | 0.584 | 50 | +18 pts |  |
| pump: volume >= 2x | 102 | -6 pts | 0.294 | +1 pts | +3 pts | 0.337 | 21 | -22 pts |  |
| sideways: volume dried up (<= 0.6x the pump's) | 201 | -2 pts | 0.678 | +3 pts | +3 pts | 0.202 | 38 | -10 pts |  |
| liquidity: crowd leaning with the pump (long/short ratio above its 30-day median) | 96 | -6 pts | 0.364 | +4 pts | +3 pts | 0.319 | 20 | +5 pts |  |
| touch: RSI 40-50 | 218 | -4 pts | 0.509 | +14 pts | +5 pts | 0.204 | 33 | +17 pts |  |
| touch: deep (> 0.25 ATR below the middle band) | 341 | +4 pts | 0.623 | +11 pts | +5 pts | 0.237 | 57 | +0 pts |  |
| sideways: tight (range <= 2 ATR) | 239 | -0 pts | 1.000 | +15 pts | +6 pts | 0.060 | 44 | +25 pts |  |
| touch: wick rejection (close in the top half) | 16 | -14 pts | 0.307 | +0 pts | +8 pts | 0.299 | 3 |  |  |
| touch: swept the sideways low | 344 | +14 pts | 0.112 | +46 pts | +40 pts | 0.002 | 58 | +48 pts | yes |

## fail -> does it dump? · 4h: 86 cases 2020 - Oct 2025, **right 56%** (fair test); holdout 15, right 47%

Far target (the trader's definition): 97% took out the sideways low before a close 0.5 ATR above the middle band.

| condition at the touch | cases with it | fair test: difference | fair test: noise | far target: raw difference | far target: same distances | same distances: noise | holdout cases with it | holdout far difference (raw) | real (p<0.01 at same distances, holdout agrees) / likely (p<0.05) |
|---|---|---|---|---|---|---|---|---|---|
| sideways: a higher high than the pump candle | 51 | -7 pts | 0.668 | -6 pts | -7 pts | 0.249 | 5 | -20 pts |  |
| context: higher timeframe above its EMA 50 | 58 | -7 pts | 0.723 | -5 pts | -6 pts | 0.369 | 9 | -11 pts |  |
| context: higher timeframe at / above its upper band | 25 | -5 pts | 0.808 | -1 pts | -5 pts | 0.441 | 9 | -11 pts |  |
| pump: leg into the pump >= 4 ATR | 67 | +4 pts | 0.800 | -4 pts | -5 pts | 1.000 | 14 |  |  |
| context: daily above its EMA 200 | 44 | +6 pts | 0.643 | -2 pts | -4 pts | 0.469 | 6 | -17 pts |  |
| sideways: 6+ candles | 44 | +7 pts | 0.763 | -7 pts | +0 pts | 1.000 | 8 | -12 pts |  |
| touch: volume >= 1.5x the sideways average | 59 | -10 pts | 0.456 | +6 pts | +1 pts | 0.895 | 13 |  |  |
| pump: volume >= 2x | 18 | +7 pts | 0.813 | +4 pts | +4 pts | 1.000 | 4 |  |  |
| touch: RSI 40-50 | 55 | +2 pts | 1.000 | +10 pts | +4 pts | 1.000 | 11 |  |  |
| pump: close > 0.5 ATR beyond the band | 18 | -7 pts | 0.613 | +4 pts | +7 pts | 0.529 | 2 |  |  |
| sideways: volume dried up (<= 0.6x the pump's) | 31 | +4 pts | 0.868 | +5 pts | +7 pts | 0.234 | 8 | -12 pts |  |
| sideways: tight (range <= 2 ATR) | 56 | +4 pts | 0.835 | +10 pts | +10 pts | 0.304 | 11 |  |  |
| liquidity: crowd leaning with the pump (long/short ratio above its 30-day median) | 30 | -0 pts | 1.000 | +0 pts |  | not tested (n < 60) | 8 | -12 pts |  |

## fail -> does it dump? · 1D: 20 cases 2020 - Oct 2025, **right 55%** (fair test); holdout 2, right 0%

Far target (the trader's definition): 90% took out the sideways low before a close 0.5 ATR above the middle band.

