# The middle-band hold after a pump, on six coins (4h and daily)

Same events and outcomes as `reports/bb_pause_why.md`. **right** = the fair test (1.5 ATR either way; a coin flip = 50%). **far** = the trader's definition (hold: a new high above everything so far; fail: the sideways low; before a close 0.5 ATR beyond the middle band). 90% intervals and **p** from a bootstrap of whole calendar months (coins move together). Research 2020 - Oct 2025, holdout Nov 2025 on.

## Does the close at the middle band tell the direction?

| timeframe | event | coin | cases 2020-25 | right (fair test) | 90% low | 90% high | chance it is not above 50% | far target reached | holdout cases | holdout right |
|---|---|---|---|---|---|---|---|---|---|---|
| 1D | hold -> pump again | all six | 236 | 52% | 46% | 58% | 0.344 | 40% | 42 | 52% |
| 1D | hold -> pump again | BTC | 42 | 48% | 36% | 60% |  | 45% | 10 | 60% |
| 1D | hold -> pump again | ETH | 44 | 61% | 49% | 73% |  | 48% | 3 | 33% |
| 1D | hold -> pump again | BNB | 30 | 57% | 41% | 72% |  | 40% | 8 | 75% |
| 1D | hold -> pump again | SOL | 43 | 49% | 36% | 61% |  | 33% | 7 | 14% |
| 1D | hold -> pump again | XRP | 39 | 46% | 32% | 60% |  | 36% | 6 | 33% |
| 1D | hold -> pump again | DOGE | 38 | 50% | 38% | 62% |  | 37% | 8 | 75% |
| 1D | fail -> dump | all six | 87 | 53% | 43% | 63% | 0.325 | 71% | 9 | 11% |
| 1D | fail -> dump | BTC | 14 | 50% | 26% | 71% |  | 79% | 0 |  |
| 1D | fail -> dump | ETH | 20 | 55% | 35% | 74% |  | 65% | 2 | 0% |
| 1D | fail -> dump | BNB | 19 | 47% | 32% | 67% |  | 68% | 2 | 0% |
| 1D | fail -> dump | SOL | 8 | 62% | 38% | 88% |  | 88% | 1 | 0% |
| 1D | fail -> dump | XRP | 18 | 56% | 39% | 78% |  | 61% | 3 | 33% |
| 1D | fail -> dump | DOGE | 8 | 50% | 25% | 75% |  | 88% | 1 | 0% |
| 4h | hold -> pump again | all six | 1500 | 50% | 47% | 52% | 0.547 | 42% | 280 | 55% |
| 4h | hold -> pump again | BTC | 262 | 50% | 45% | 55% |  | 49% | 47 | 38% |
| 4h | hold -> pump again | ETH | 267 | 49% | 45% | 53% |  | 42% | 43 | 53% |
| 4h | hold -> pump again | BNB | 267 | 53% | 48% | 58% |  | 45% | 56 | 54% |
| 4h | hold -> pump again | SOL | 236 | 50% | 45% | 55% |  | 41% | 46 | 54% |
| 4h | hold -> pump again | XRP | 249 | 46% | 41% | 51% |  | 37% | 44 | 61% |
| 4h | hold -> pump again | DOGE | 219 | 50% | 45% | 55% |  | 41% | 44 | 68% |
| 4h | fail -> dump | all six | 442 | 52% | 47% | 56% | 0.277 | 80% | 92 | 50% |
| 4h | fail -> dump | BTC | 82 | 61% | 52% | 69% |  | 87% | 13 | 38% |
| 4h | fail -> dump | ETH | 86 | 56% | 48% | 64% |  | 80% | 15 | 47% |
| 4h | fail -> dump | BNB | 72 | 47% | 38% | 57% |  | 79% | 13 | 46% |
| 4h | fail -> dump | SOL | 69 | 49% | 39% | 60% |  | 74% | 24 | 42% |
| 4h | fail -> dump | XRP | 73 | 49% | 41% | 58% |  | 79% | 14 | 71% |
| 4h | fail -> dump | DOGE | 60 | 43% | 33% | 55% |  | 77% | 13 | 62% |

## 1D · hold -> pump again: conditions, all coins (236 cases; strata coin x distances)

About 20 conditions per table: one p < 0.05 is expected by chance.

| condition | cases with it | fair test: difference | far: raw difference | far: same distances | noise | holdout, same distances |
|---|---|---|---|---|---|---|
| pump: leg into the pump >= 4 ATR | 194 | -7 pts | -15 pts | -26 pts | 0.050 | +0 pts |
| pump: volume >= 2x | 58 | -9 pts | -21 pts | -23 pts | 0.057 | +0 pts |
| sideways: 6+ candles | 131 | -3 pts | -7 pts | -12 pts | 0.195 |  |
| context: higher timeframe at / above its upper band | 92 | -11 pts | -6 pts | -10 pts | 0.379 | -33 pts |
| sideways: 3+ rejections at the upper band | 41 | -4 pts | +2 pts | -10 pts | 0.444 |  |
| sideways: tight (range <= 2 ATR) | 126 | +13 pts | +10 pts | -3 pts | 0.688 | -50 pts |
| sideways: volume dried up (<= 0.6x the pump's) | 102 | +4 pts | +1 pts | -2 pts | 0.805 |  |
| pump: close > 0.5 ATR beyond the band | 57 | -3 pts | +1 pts | -2 pts | 0.870 |  |
| context: daily above its EMA 200 | 160 | -23 pts | -6 pts | +0 pts | 1.000 | -100 pts |
| touch: deep (> 0.25 ATR below the middle band) | 34 | -5 pts | -5 pts | +1 pts | 0.973 | +0 pts |
| sideways: bands contracted (width <= 0.8x the pump's) | 46 | -5 pts | +5 pts | +3 pts | 0.805 | +50 pts |
| sideways: equal highs at the top (liquidity above) | 216 | +2 pts | +5 pts | +4 pts | 0.925 | +0 pts |
| sideways: a higher high than the pump candle | 137 | -8 pts | +1 pts | +4 pts | 0.626 |  |
| touch: volume >= 1.5x the sideways average | 46 | +1 pts | +7 pts | +5 pts | 0.693 | +0 pts |
| context: higher timeframe above its EMA 50 | 139 | -15 pts | -6 pts | +10 pts | 0.479 | -33 pts |
| touch: wick rejection (close in the top half) | 104 | -10 pts | +3 pts | +16 pts | 0.200 |  |

## 1D · fail -> dump: conditions, all coins (87 cases; strata coin x distances)

About 20 conditions per table: one p < 0.05 is expected by chance.

| condition | cases with it | fair test: difference | far: raw difference | far: same distances | noise | holdout, same distances |
|---|---|---|---|---|---|---|
| sideways: 6+ candles | 53 | -5 pts | -18 pts | -50 pts | 1.000 |  |
| touch: volume >= 1.5x the sideways average | 36 | +5 pts | -3 pts | -50 pts | 1.000 |  |
| pump: leg into the pump >= 4 ATR | 64 | +31 pts | +2 pts | -33 pts | 0.491 |  |
| context: higher timeframe at / above its upper band | 21 | -11 pts | -18 pts | -33 pts | 1.000 |  |
| sideways: volume dried up (<= 0.6x the pump's) | 26 | +12 pts | +3 pts | -25 pts | 1.000 |  |
| sideways: a higher high than the pump candle | 54 | -3 pts | -7 pts | -17 pts | 1.000 |  |
| context: daily above its EMA 200 | 41 | -19 pts | -19 pts | +0 pts | 1.000 |  |
| touch: deep (> 0.25 ATR below the middle band) | 66 | +7 pts | -6 pts | +0 pts | 1.000 |  |
| context: higher timeframe above its EMA 50 | 50 | -4 pts | -5 pts | +33 pts | 1.000 |  |
| touch: RSI 40-50 | 43 | +6 pts | +20 pts | +33 pts | 1.000 |  |
| sideways: tight (range <= 2 ATR) | 50 | -7 pts | +2 pts | +67 pts | 0.486 |  |

## 4h · hold -> pump again: conditions, all coins (1500 cases; strata coin x distances)

About 20 conditions per table: one p < 0.05 is expected by chance.

| condition | cases with it | fair test: difference | far: raw difference | far: same distances | noise | holdout, same distances |
|---|---|---|---|---|---|---|
| sideways: tight (range <= 2 ATR) | 756 | -7 pts | -0 pts | -4 pts | 0.135 | -14 pts |
| sideways: volume dried up (<= 0.6x the pump's) | 605 | +1 pts | -3 pts | -4 pts | 0.145 | -18 pts |
| pump: leg into the pump >= 4 ATR | 1209 | +5 pts | -3 pts | -4 pts | 0.357 | +5 pts |
| pump: volume >= 2x | 321 | +0 pts | -4 pts | -2 pts | 0.481 | -7 pts |
| pump: close > 0.5 ATR beyond the band | 294 | +2 pts | -2 pts | -0 pts | 0.990 | -0 pts |
| context: higher timeframe at / above its upper band | 644 | +3 pts | -4 pts | +1 pts | 0.716 | +1 pts |
| sideways: bands contracted (width <= 0.8x the pump's) | 283 | +4 pts | +7 pts | +2 pts | 0.666 | -2 pts |
| context: daily above its EMA 200 | 831 | -3 pts | +3 pts | +2 pts | 0.451 | -7 pts |
| context: higher timeframe above its EMA 50 | 1051 | +2 pts | +5 pts | +3 pts | 0.329 | -3 pts |
| touch: volume >= 1.5x the sideways average | 373 | -3 pts | +6 pts | +4 pts | 0.214 | +5 pts |
| touch: deep (> 0.25 ATR below the middle band) | 204 | -1 pts | +1 pts | +6 pts | 0.190 | -2 pts |
| sideways: 6+ candles | 859 | +8 pts | +9 pts | +6 pts | 0.045 | -0 pts |
| sideways: a higher high than the pump candle | 975 | +6 pts | +8 pts | +6 pts | 0.050 | +13 pts |
| touch: wick rejection (close in the top half) | 601 | +2 pts | +14 pts | +7 pts | 0.075 | +13 pts |
| touch: RSI 40-50 | 115 | -1 pts | -7 pts | +8 pts | 0.204 | +8 pts |
| sideways: 3+ rejections at the upper band | 256 | +4 pts | +8 pts | +9 pts | 0.015 | +22 pts |
| sideways: equal highs at the top (liquidity above) | 1408 | +7 pts | +12 pts | +12 pts | 0.055 | +41 pts |

## 4h · fail -> dump: conditions, all coins (442 cases; strata coin x distances)

About 20 conditions per table: one p < 0.05 is expected by chance.

| condition | cases with it | fair test: difference | far: raw difference | far: same distances | noise | holdout, same distances |
|---|---|---|---|---|---|---|
| pump: leg into the pump >= 4 ATR | 348 | -7 pts | -12 pts | -13 pts | 0.012 | +25 pts |
| sideways: bands contracted (width <= 0.8x the pump's) | 75 | -11 pts | -27 pts | -11 pts | 0.130 | +50 pts |
| context: higher timeframe at / above its upper band | 156 | -8 pts | -9 pts | -7 pts | 0.097 | +18 pts |
| pump: close > 0.5 ATR beyond the band | 91 | -3 pts | -2 pts | -6 pts | 0.264 | +0 pts |
| context: higher timeframe above its EMA 50 | 288 | -7 pts | -11 pts | -4 pts | 0.424 | +0 pts |
| touch: deep (> 0.25 ATR below the middle band) | 365 | +6 pts | -9 pts | -3 pts | 0.751 | +50 pts |
| sideways: a higher high than the pump candle | 260 | -0 pts | -8 pts | -3 pts | 0.506 | -17 pts |
| sideways: 6+ candles | 236 | +0 pts | -3 pts | +1 pts | 0.910 | +12 pts |
| sideways: volume dried up (<= 0.6x the pump's) | 172 | +0 pts | +5 pts | +2 pts | 0.586 | -15 pts |
| context: daily above its EMA 200 | 222 | -3 pts | -2 pts | +3 pts | 0.603 | +0 pts |
| sideways: tight (range <= 2 ATR) | 260 | +8 pts | +10 pts | +3 pts | 0.414 | -13 pts |
| touch: volume >= 1.5x the sideways average | 249 | +4 pts | -4 pts | +4 pts | 0.384 | +0 pts |
| sideways: 3+ rejections at the upper band | 65 | +3 pts | -3 pts | +4 pts | 0.424 | +25 pts |
| touch: RSI 40-50 | 257 | +6 pts | +13 pts | +4 pts | 0.444 | -17 pts |
| pump: volume >= 2x | 109 | +5 pts | +6 pts | +7 pts | 0.177 | -50 pts |
| sideways: equal highs at the top (liquidity above) | 415 | +19 pts | +22 pts | +20 pts | 0.020 | +0 pts |

