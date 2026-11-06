# Why the middle-band hold pumps again, and why it sometimes fails

Pump -> 3+ sideways closes above the middle band -> first touch of the middle band. **Hold** = the touch closes above the middle band; **fail** = at / below it. Mirrored for dumps. Outcomes: the **fair test** (1.5 ATR either way, coin flip 50%) and the trader's **far target** (hold: a new high above everything so far; fail: the sideways low; before a close 0.5 ATR beyond the middle band, within 30 candles). The far-target difference is shown raw and **at the same distances** (within groups of the same timeframe, distance to the target and distance to the failure level); only the same-distance column removes the geometry. **real** = p < 0.01 at the same distances and the holdout (also at the same distances) points the same way. **Many conditions are tested in each table (about 20): one with p < 0.05 is expected by chance alone,** so a single 'likely' is a lead, not a finding. The fail-side target includes the touch candle's own low (the hold-side target includes its high), so a touch that already traded beyond the sideways low does not count as reaching the target by itself.

## hold -> does it pump again? · 1h + 4h + 1D together: 1449 cases 2020 - Oct 2025, **right 47%** (fair test); holdout 204, right 49%

Far target (the trader's definition): 40% made a new high above everything so far before a close 0.5 ATR below the middle band.

| condition at the touch | cases with it | fair test: difference | fair test: noise | far target: raw difference | far target: same distances | same distances: noise | holdout cases with it | holdout, same distances | real (p<0.01 at same distances, holdout agrees) / likely (p<0.05) |
|---|---|---|---|---|---|---|---|---|---|
| liquidity: crowd leaning with the pump (long/short ratio above its 30-day median) | 232 | -7 pts | 0.047 | -6 pts | -9 pts | 0.030 | 58 | +7 pts |  |
| sideways: tight (range <= 2 ATR) | 702 | -3 pts | 0.329 | -0 pts | -5 pts | 0.075 | 107 | +4 pts |  |
| pump: volume >= 2x | 412 | +4 pts | 0.219 | -5 pts | -4 pts | 0.177 | 69 | +20 pts |  |
| touch: RSI 40-50 | 111 | -3 pts | 0.671 | -16 pts | -4 pts | 0.591 | 17 | -19 pts |  |
| touch: swept the sideways low | 866 | +1 pts | 0.661 | -6 pts | -3 pts | 0.284 | 117 | +1 pts |  |
| pump: close > 0.5 ATR beyond the band | 282 | +3 pts | 0.449 | -3 pts | -3 pts | 0.446 | 40 | -8 pts |  |
| sideways: volume dried up (<= 0.6x the pump's) | 814 | +4 pts | 0.209 | -4 pts | -2 pts | 0.304 | 118 | -2 pts |  |
| context: higher timeframe at / above its upper band | 598 | +2 pts | 0.544 | -2 pts | -1 pts | 0.676 | 75 | -0 pts |  |
| sideways: 3+ rejections at the upper band | 229 | +1 pts | 0.781 | +5 pts | -1 pts | 0.840 | 51 | +2 pts |  |
| context: higher timeframe above its EMA 50 | 1042 | -2 pts | 0.658 | +1 pts | -0 pts | 0.963 | 143 | +11 pts |  |
| liquidity: open interest rose > 5% during the sideways | 32 | +4 pts | 0.721 | +0 pts | +0 pts | 0.983 | 2 |  |  |
| touch: wick rejection (close in the top half) | 586 | -1 pts | 0.641 | +13 pts | +1 pts | 0.845 | 88 | +1 pts |  |
| touch: deep (> 0.25 ATR below the middle band) | 176 | +2 pts | 0.618 | -1 pts | +3 pts | 0.579 | 28 | +14 pts |  |
| sideways: a higher high than the pump candle | 952 | +2 pts | 0.387 | +7 pts | +3 pts | 0.299 | 121 | +12 pts |  |
| touch: volume >= 1.5x the sideways average | 341 | +1 pts | 0.898 | +6 pts | +3 pts | 0.267 | 63 | +3 pts |  |
| pump: leg into the pump >= 4 ATR | 1150 | +5 pts | 0.172 | +1 pts | +4 pts | 0.224 | 163 | -8 pts |  |
| sideways: 6+ candles | 934 | +5 pts | 0.082 | +3 pts | +4 pts | 0.140 | 129 | +0 pts |  |
| context: daily above its EMA 200 | 718 | -1 pts | 0.666 | +9 pts | +5 pts | 0.080 | 109 | +3 pts |  |
| sideways: equal highs at the top (liquidity above) | 1374 | -3 pts | 0.571 | +3 pts | +7 pts | 0.332 | 198 | -30 pts |  |
| sideways: bands contracted (width <= 0.8x the pump's) | 284 | +5 pts | 0.150 | +10 pts | +8 pts | 0.017 | 52 | +1 pts | likely |

## hold -> does it pump again? · 4h: 267 cases 2020 - Oct 2025, **right 49%** (fair test); holdout 43, right 53%

Far target (the trader's definition): 42% made a new high above everything so far before a close 0.5 ATR below the middle band.

| condition at the touch | cases with it | fair test: difference | fair test: noise | far target: raw difference | far target: same distances | same distances: noise | holdout cases with it | holdout, same distances | real (p<0.01 at same distances, holdout agrees) / likely (p<0.05) |
|---|---|---|---|---|---|---|---|---|---|
| liquidity: crowd leaning with the pump (long/short ratio above its 30-day median) | 40 | -10 pts | 0.284 | -12 pts | -14 pts | 0.160 | 11 |  |  |
| sideways: tight (range <= 2 ATR) | 113 | -7 pts | 0.314 | +0 pts | -6 pts | 0.367 | 21 | -25 pts |  |
| sideways: volume dried up (<= 0.6x the pump's) | 110 | +9 pts | 0.182 | -3 pts | -3 pts | 0.721 | 20 | -50 pts |  |
| touch: swept the sideways low | 140 | +0 pts | 1.000 | -6 pts | -2 pts | 0.738 | 24 | -26 pts |  |
| sideways: bands contracted (width <= 0.8x the pump's) | 54 | +8 pts | 0.359 | +8 pts | -1 pts | 0.938 | 12 |  |  |
| pump: volume >= 2x | 54 | +13 pts | 0.105 | -1 pts | -0 pts | 0.993 | 13 | +0 pts |  |
| context: higher timeframe at / above its upper band | 120 | +5 pts | 0.546 | +0 pts | +2 pts | 0.783 | 18 |  |  |
| sideways: equal highs at the top (liquidity above) | 252 | +10 pts | 0.641 | +9 pts | +3 pts | 0.835 | 42 |  |  |
| pump: close > 0.5 ATR beyond the band | 47 | +10 pts | 0.244 | -1 pts | +3 pts | 0.698 | 8 | +2 pts |  |
| sideways: a higher high than the pump candle | 197 | +12 pts | 0.102 | +12 pts | +4 pts | 0.554 | 29 | +35 pts |  |
| sideways: 3+ rejections at the upper band | 41 | +8 pts | 0.377 | +14 pts | +5 pts | 0.606 | 11 |  |  |
| sideways: 6+ candles | 170 | +11 pts | 0.110 | +12 pts | +10 pts | 0.127 | 32 |  |  |
| context: higher timeframe above its EMA 50 | 186 | +0 pts | 1.000 | +9 pts | +10 pts | 0.209 | 29 | -3 pts |  |
| context: daily above its EMA 200 | 139 | -5 pts | 0.569 | +10 pts | +10 pts | 0.122 | 27 | -13 pts |  |
| touch: wick rejection (close in the top half) | 96 | -5 pts | 0.486 | +12 pts | +11 pts | 0.249 | 12 |  |  |
| touch: volume >= 1.5x the sideways average | 66 | -7 pts | 0.347 | +5 pts | +11 pts | 0.165 | 10 |  |  |
| pump: leg into the pump >= 4 ATR | 217 | +14 pts | 0.052 | +9 pts | +13 pts | 0.137 | 36 |  |  |
| touch: deep (> 0.25 ATR below the middle band) | 37 | -0 pts | 1.000 | +5 pts | +15 pts | 0.122 | 7 |  |  |
| touch: RSI 40-50 | 19 | -2 pts | 1.000 | -11 pts | +19 pts | 0.317 | 6 |  |  |

## hold -> does it pump again? · 1D: 44 cases 2020 - Oct 2025, **right 61%** (fair test); holdout 3, right 33%

Far target (the trader's definition): 48% made a new high above everything so far before a close 0.5 ATR below the middle band.

| condition at the touch | cases with it | fair test: difference | fair test: noise | far target: raw difference | far target: same distances | same distances: noise | holdout cases with it | holdout, same distances | real (p<0.01 at same distances, holdout agrees) / likely (p<0.05) |
|---|---|---|---|---|---|---|---|---|---|
| sideways: 6+ candles | 28 | -2 pts | not tested (n < 60) | -23 pts |  | not tested (n < 60) | 2 |  |  |
| sideways: tight (range <= 2 ATR) | 22 | +5 pts | not tested (n < 60) | -5 pts |  | not tested (n < 60) | 1 |  |  |
| sideways: volume dried up (<= 0.6x the pump's) | 16 | -8 pts | not tested (n < 60) | -46 pts |  | not tested (n < 60) | 1 |  |  |
| sideways: a higher high than the pump candle | 29 | -28 pts | not tested (n < 60) | +2 pts |  | not tested (n < 60) | 2 |  |  |
| touch: wick rejection (close in the top half) | 15 | -12 pts | not tested (n < 60) | -2 pts |  | not tested (n < 60) | 0 |  |  |
| touch: swept the sideways low | 26 | +10 pts | not tested (n < 60) | +15 pts |  | not tested (n < 60) | 1 |  |  |
| context: higher timeframe at / above its upper band | 17 | -15 pts | not tested (n < 60) | -11 pts |  | not tested (n < 60) | 0 |  |  |

## fail -> does it dump? · 1h + 4h + 1D together: 398 cases 2020 - Oct 2025, **right 51%** (fair test); holdout 68, right 47%

Far target (the trader's definition): 76% took out the sideways low before a close 0.5 ATR above the middle band.

| condition at the touch | cases with it | fair test: difference | fair test: noise | far target: raw difference | far target: same distances | same distances: noise | holdout cases with it | holdout, same distances | real (p<0.01 at same distances, holdout agrees) / likely (p<0.05) |
|---|---|---|---|---|---|---|---|---|---|
| touch: wick rejection (close in the top half) | 16 | -14 pts | 0.307 | -46 pts | -20 pts | 0.339 | 3 |  |  |
| touch: RSI < 40 | 17 | +2 pts | 1.000 | +7 pts | -10 pts | 0.519 | 7 |  |  |
| context: higher timeframe above its EMA 50 | 273 | +1 pts | 1.000 | -14 pts | -9 pts | 0.060 | 53 |  |  |
| touch: volume >= 1.5x the sideways average | 255 | -0 pts | 1.000 | -5 pts | -5 pts | 0.309 | 50 | +0 pts |  |
| sideways: tight (range <= 2 ATR) | 239 | -0 pts | 1.000 | +4 pts | -5 pts | 0.332 | 44 |  |  |
| sideways: 3+ rejections at the upper band | 59 | -12 pts | 0.150 | -6 pts | -4 pts | 0.524 | 15 | -3 pts |  |
| pump: close > 0.5 ATR beyond the band | 80 | +1 pts | 1.000 | -6 pts | -3 pts | 0.571 | 17 |  |  |
| sideways: bands contracted (width <= 0.8x the pump's) | 83 | -8 pts | 0.287 | -18 pts | -1 pts | 0.938 | 12 | +3 pts |  |
| liquidity: crowd leaning with the pump (long/short ratio above its 30-day median) | 96 | -6 pts | 0.364 | -0 pts | +0 pts | 0.978 | 20 |  |  |
| context: daily above its EMA 200 | 194 | +1 pts | 0.925 | -9 pts | +0 pts | 0.965 | 34 | -3 pts |  |
| touch: swept the sideways low | 344 | +14 pts | 0.112 | +26 pts | +1 pts | 0.958 | 58 |  |  |
| context: higher timeframe at / above its upper band | 145 | +3 pts | 0.599 | -6 pts | +1 pts | 0.830 | 38 | +0 pts |  |
| pump: leg into the pump >= 4 ATR | 313 | -1 pts | 0.885 | -4 pts | +2 pts | 0.766 | 62 |  |  |
| sideways: a higher high than the pump candle | 253 | -2 pts | 0.843 | +0 pts | +2 pts | 0.574 | 36 | -13 pts |  |
| touch: RSI 40-50 | 218 | -4 pts | 0.509 | +13 pts | +3 pts | 0.586 | 33 | -10 pts |  |
| sideways: volume dried up (<= 0.6x the pump's) | 201 | -2 pts | 0.678 | +2 pts | +4 pts | 0.299 | 38 | -6 pts |  |
| pump: volume >= 2x | 102 | -6 pts | 0.294 | +2 pts | +6 pts | 0.227 | 21 | -10 pts |  |
| sideways: 6+ candles | 243 | -1 pts | 0.835 | -3 pts | +6 pts | 0.212 | 38 | -2 pts |  |
| sideways: equal highs at the top (liquidity above) | 383 | +25 pts | 0.060 | -4 pts | +7 pts | 0.554 | 63 |  |  |
| touch: deep (> 0.25 ATR below the middle band) | 341 | +4 pts | 0.623 | -2 pts | +21 pts | 0.037 | 57 |  | likely |

## fail -> does it dump? · 4h: 86 cases 2020 - Oct 2025, **right 56%** (fair test); holdout 15, right 47%

Far target (the trader's definition): 80% took out the sideways low before a close 0.5 ATR above the middle band.

| condition at the touch | cases with it | fair test: difference | fair test: noise | far target: raw difference | far target: same distances | same distances: noise | holdout cases with it | holdout, same distances | real (p<0.01 at same distances, holdout agrees) / likely (p<0.05) |
|---|---|---|---|---|---|---|---|---|---|
| pump: close > 0.5 ATR beyond the band | 18 | -7 pts | 0.613 | -10 pts | -17 pts | 0.085 | 2 |  |  |
| context: higher timeframe above its EMA 50 | 58 | -7 pts | 0.723 | -8 pts | -16 pts | 0.165 | 9 |  |  |
| pump: leg into the pump >= 4 ATR | 67 | +4 pts | 0.800 | -12 pts | -10 pts | 0.372 | 14 |  |  |
| context: higher timeframe at / above its upper band | 25 | -5 pts | 0.808 | -6 pts | -9 pts | 0.439 | 9 |  |  |
| touch: volume >= 1.5x the sideways average | 59 | -10 pts | 0.456 | -13 pts | -5 pts | 0.723 | 13 |  |  |
| sideways: tight (range <= 2 ATR) | 56 | +4 pts | 0.835 | +5 pts | +1 pts | 0.808 | 11 |  |  |
| sideways: 6+ candles | 44 | +7 pts | 0.763 | +8 pts | +3 pts | 0.666 | 8 |  |  |
| pump: volume >= 2x | 18 | +7 pts | 0.813 | +4 pts | +5 pts | 0.681 | 4 |  |  |
| sideways: a higher high than the pump candle | 51 | -7 pts | 0.668 | +0 pts | +6 pts | 0.623 | 5 |  |  |
| context: daily above its EMA 200 | 44 | +6 pts | 0.643 | +7 pts | +7 pts | 0.481 | 6 |  |  |
| sideways: volume dried up (<= 0.6x the pump's) | 31 | +4 pts | 0.868 | +1 pts | +7 pts | 0.521 | 8 |  |  |
| touch: RSI 40-50 | 55 | +2 pts | 1.000 | +14 pts | +11 pts | 0.377 | 11 |  |  |
| liquidity: crowd leaning with the pump (long/short ratio above its 30-day median) | 30 | -0 pts | 1.000 | -9 pts |  | not tested (n < 60) | 8 |  |  |

## fail -> does it dump? · 1D: 20 cases 2020 - Oct 2025, **right 55%** (fair test); holdout 2, right 0%

Far target (the trader's definition): 65% took out the sideways low before a close 0.5 ATR above the middle band.

