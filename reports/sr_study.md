# Support / resistance reversal study

When price touches a strong zone, what decides whether it reverses or breaks? Zones come from swings confirmed before the touch (weekly / daily / 4h, >= 3 touches or a weekly swing). Decision at the touch candle's close; the reversal trade enters the next open with the stop beyond the zone and wick, target 2x risk.
Research = events before 2025-11-01 (halves split at 2023-01-01); holdout = from 2025-11-01.

## 4h chart

- Zone touches: **4164**. The level held at the touch candle's close **69%** of the time (close back on the zone's side).
- Reversal trades (held at close): research **2390**, win **35%**, fail **64%**, avg **+0.05 R** (break-even ~33%).

### Which conditions make the reversal work? (research)

*diff* = win rate with this condition minus without it. HELPS/HURTS = q < 0.10 across all rows AND the same direction in both halves.

| feature | value | trades | win | win without | diff | avg R | half 1 | half 2 | q | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| ema200_side | with | 1290 | 37% | 32% | +6 pts | +0.14 | +7 pts | +5 pts | 0.099 | HELPS REVERSAL |
| ema200_side | against | 1100 | 32% | 37% | -6 pts | -0.04 | -7 pts | -5 pts | 0.099 | HURTS REVERSAL |

### Volume: the key question

Win rate of the reversal trade by **volume into the level** (rows) x **volume on the touch candle** (columns), research period:

| volume into level \ touch volume | climax >3x | high 1.5-3x | low <0.7x | normal |
|---|---|---|---|---|
| fading | 47% (n=19) | 37% (n=108) | 30% (n=253) | 34% (n=288) |
| rising | 30% (n=47) | 38% (n=232) | 34% (n=92) | 37% (n=389) |
| steady | 22% (n=27) | 37% (n=205) | 37% (n=239) | 32% (n=491) |

vol_slope x structure_vs:

| vol_slope | structure_vs | trades | win | avg R |
|---|---|---|---|---|
| fading | against | 162 | 35% | +0.04 |
| fading | range | 265 | 33% | -0.00 |
| fading | with | 178 | 31% | -0.07 |
| flat | against | 195 | 34% | +0.03 |
| flat | range | 293 | 32% | -0.04 |
| flat | with | 217 | 35% | +0.04 |
| rising | against | 288 | 40% | +0.22 |
| rising | range | 491 | 37% | +0.15 |
| rising | with | 301 | 32% | -0.02 |

vol_div x rsi_div:

| vol_div | rsi_div | trades | win | avg R |
|---|---|---|---|---|
| no | no | 2159 | 34% | +0.05 |
| no | yes | 59 | 27% | -0.15 |
| yes | no | 110 | 39% | +0.19 |
| yes | yes | 62 | 40% | +0.24 |

vol_touch x wick:

| vol_touch | wick | trades | win | avg R |
|---|---|---|---|---|
| climax >3x | medium | 29 | 34% | +0.03 |
| climax >3x | small | 41 | 32% | +0.16 |
| climax >3x | strong >=0.5 | 23 | 26% | -0.08 |
| high 1.5-3x | medium | 243 | 38% | +0.16 |
| high 1.5-3x | small | 166 | 39% | +0.24 |
| high 1.5-3x | strong >=0.5 | 136 | 35% | +0.09 |
| low <0.7x | medium | 288 | 36% | +0.07 |
| low <0.7x | small | 118 | 32% | -0.03 |
| low <0.7x | strong >=0.5 | 178 | 31% | -0.05 |
| normal | medium | 536 | 33% | -0.01 |
| normal | small | 314 | 36% | +0.10 |
| normal | strong >=0.5 | 318 | 33% | +0.00 |

vol_approach x weekly_trend_vs:

| vol_approach | weekly_trend_vs | trades | win | avg R |
|---|---|---|---|---|
| fading | against | 196 | 39% | +0.17 |
| fading | flat | 254 | 29% | -0.12 |
| fading | with | 218 | 34% | +0.04 |
| rising | against | 230 | 40% | +0.24 |
| rising | flat | 285 | 36% | +0.10 |
| rising | with | 245 | 33% | +0.01 |
| steady | against | 279 | 34% | +0.04 |
| steady | flat | 361 | 34% | +0.02 |
| steady | with | 322 | 34% | +0.05 |

### Every condition (research)

| feature | value | trades | win | win without | diff | avg R | half 1 | half 2 | q | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| daily_trend_vs | against | 1128 | 33% | 36% | -3 pts | +0.01 | -8 pts | +0 pts | 0.54 | noise |
| daily_trend_vs | with | 1238 | 36% | 33% | +2 pts | +0.09 | +6 pts | -0 pts | 0.54 | noise |
| ema200_side | against | 1100 | 32% | 37% | -6 pts | -0.04 | -7 pts | -5 pts | 0.10 | HURTS REVERSAL |
| ema200_side | with | 1290 | 37% | 32% | +6 pts | +0.14 | +7 pts | +5 pts | 0.10 | HELPS REVERSAL |
| ema50_side | against | 1134 | 33% | 36% | -2 pts | +0.01 | -4 pts | -1 pts | 0.54 | consistent, not significant |
| ema50_side | with | 1256 | 36% | 33% | +2 pts | +0.09 | +4 pts | +1 pts | 0.54 | consistent, not significant |
| macd_turn | no | 1177 | 33% | 36% | -2 pts | +0.01 | -5 pts | -0 pts | 0.54 | consistent, not significant |
| macd_turn | yes | 1213 | 36% | 33% | +2 pts | +0.10 | +5 pts | +0 pts | 0.54 | consistent, not significant |
| retest | first touch | 1723 | 35% | 34% | +1 pts | +0.06 | +2 pts | +2 pts | 0.78 | consistent, not significant |
| retest | retest | 667 | 34% | 35% | -1 pts | +0.03 | -2 pts | -2 pts | 0.78 | consistent, not significant |
| rsi | normal | 2121 | 35% | 32% | +3 pts | +0.06 | +8 pts | -0 pts | 0.54 | noise |
| rsi | stretched | 269 | 32% | 35% | -3 pts | -0.03 | -8 pts | +0 pts | 0.54 | noise |
| rsi_div | no | 2269 | 35% | 34% | +1 pts | +0.05 | -4 pts | +4 pts | 0.93 | noise |
| rsi_div | yes | 121 | 34% | 35% | -1 pts | +0.05 | +4 pts | -4 pts | 0.93 | noise |
| speed | fast >2 | 397 | 33% | 35% | -2 pts | +0.02 | -6 pts | +1 pts | 0.69 | noise |
| speed | medium | 503 | 33% | 35% | -1 pts | +0.02 | +1 pts | -3 pts | 0.72 | noise |
| speed | slow <1 | 1490 | 35% | 33% | +2 pts | +0.07 | +3 pts | +1 pts | 0.54 | consistent, not significant |
| structure | down | 668 | 33% | 35% | -2 pts | +0.01 | -3 pts | -2 pts | 0.60 | consistent, not significant |
| structure | range | 1049 | 35% | 34% | +0 pts | +0.06 | +3 pts | -1 pts | 0.93 | noise |
| structure | up | 673 | 36% | 34% | +2 pts | +0.09 | -1 pts | +3 pts | 0.67 | noise |
| structure_vs | against | 645 | 37% | 34% | +3 pts | +0.12 | -1 pts | +6 pts | 0.54 | noise |
| structure_vs | range | 1049 | 35% | 34% | +0 pts | +0.06 | +3 pts | -1 pts | 0.93 | noise |
| structure_vs | with | 696 | 32% | 35% | -3 pts | -0.01 | -2 pts | -4 pts | 0.54 | consistent, not significant |
| sweep | no | 1111 | 36% | 33% | +3 pts | +0.11 | +7 pts | +1 pts | 0.53 | consistent, not significant |
| sweep | yes | 1279 | 33% | 36% | -3 pts | +0.01 | -7 pts | -1 pts | 0.53 | consistent, not significant |
| vol_approach | fading | 668 | 34% | 35% | -1 pts | +0.02 | -1 pts | -2 pts | 0.71 | consistent, not significant |
| vol_approach | rising | 760 | 36% | 34% | +3 pts | +0.11 | +1 pts | +3 pts | 0.54 | consistent, not significant |
| vol_approach | steady | 962 | 34% | 35% | -1 pts | +0.03 | -0 pts | -1 pts | 0.74 | consistent, not significant |
| vol_div | no | 2218 | 34% | 40% | -5 pts | +0.04 | -6 pts | -5 pts | 0.54 | consistent, not significant |
| vol_div | yes | 172 | 40% | 34% | +5 pts | +0.21 | +6 pts | +5 pts | 0.54 | consistent, not significant |
| vol_slope | fading | 605 | 33% | 35% | -2 pts | -0.01 | -4 pts | -1 pts | 0.54 | consistent, not significant |
| vol_slope | flat | 705 | 33% | 35% | -2 pts | +0.00 | -3 pts | -0 pts | 0.61 | consistent, not significant |
| vol_slope | rising | 1080 | 36% | 33% | +4 pts | +0.12 | +6 pts | +1 pts | 0.53 | consistent, not significant |
| vol_touch | climax >3x | 93 | 31% | 35% | -4 pts | +0.06 | -5 pts | -3 pts | 0.69 | consistent, not significant |
| vol_touch | high 1.5-3x | 545 | 38% | 34% | +4 pts | +0.17 | +6 pts | +2 pts | 0.53 | consistent, not significant |
| vol_touch | low <0.7x | 584 | 34% | 35% | -1 pts | +0.01 | -1 pts | -1 pts | 0.78 | consistent, not significant |
| vol_touch | normal | 1168 | 34% | 35% | -1 pts | +0.02 | -2 pts | -0 pts | 0.69 | consistent, not significant |
| weekly_trend_vs | against | 705 | 37% | 33% | +4 pts | +0.14 | +1 pts | +5 pts | 0.53 | consistent, not significant |
| weekly_trend_vs | flat | 900 | 33% | 35% | -2 pts | +0.00 | -3 pts | -1 pts | 0.54 | consistent, not significant |
| weekly_trend_vs | with | 785 | 34% | 35% | -1 pts | +0.03 | +2 pts | -4 pts | 0.78 | noise |
| wick | medium | 1096 | 35% | 34% | +0 pts | +0.05 | -1 pts | +1 pts | 0.93 | noise |
| wick | small | 639 | 36% | 34% | +2 pts | +0.11 | +3 pts | +1 pts | 0.67 | consistent, not significant |
| wick | strong >=0.5 | 655 | 33% | 35% | -2 pts | +0.00 | -2 pts | -3 pts | 0.57 | consistent, not significant |
| zone_touches | 3-4 | 1052 | 33% | 36% | -3 pts | +0.00 | -0 pts | -4 pts | 0.53 | consistent, not significant |
| zone_touches | 5+ | 1338 | 36% | 33% | +3 pts | +0.10 | +0 pts | +4 pts | 0.53 | consistent, not significant |
| zone_weekly | no | 1751 | 35% | 34% | +0 pts | +0.05 | +3 pts | -0 pts | 0.93 | noise |
| zone_weekly | yes | 639 | 34% | 35% | -0 pts | +0.06 | -3 pts | +0 pts | 0.93 | noise |

### Turning it into a rule (4h)

Account simulation at up to **5x**: one trade at a time, compounding, after fees and slippage (funding not included). Trades whose stop lies beyond the liquidation price are skipped. *final* = ending equity as a multiple of the start; *median week* = typical week's return.

| rule | sizing | research trades | win | avg R | final | median week | weeks >= +20% | losing weeks | max drawdown | holdout trades | holdout win | holdout R | holdout final | holdout max DD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| every reversal trade | full margin 5x | 2390 | 35% | +0.05 | 0.00x | +0.0% | 21% | 48% | -100% | 453 | 35% | +0.07 | 0.47x | -83% |
| every reversal trade | risk 10%/trade (<=5x) | 2390 | 35% | +0.05 | 0.00x | +0.0% | 12% | 47% | -100% | 453 | 35% | +0.07 | 2.53x | -64% |
| every reversal trade | risk 2%/trade (<=5x) | 2390 | 35% | +0.05 | 0.40x | +0.0% | 0% | 46% | -82% | 453 | 35% | +0.07 | 1.72x | -21% |
| apply all HELPS (require) + HURTS (avoid) | full margin 5x | 1290 | 37% | +0.14 | 0.00x | +0.0% | 21% | 45% | -100% | 240 | 38% | +0.15 | 6.64x | -77% |
| apply all HELPS (require) + HURTS (avoid) | risk 10%/trade (<=5x) | 1290 | 37% | +0.14 | 0.14x | +0.0% | 11% | 44% | -99% | 240 | 38% | +0.15 | 2.28x | -71% |
| apply all HELPS (require) + HURTS (avoid) | risk 2%/trade (<=5x) | 1290 | 37% | +0.14 | 1.53x | +0.0% | 0% | 43% | -51% | 240 | 38% | +0.15 | 1.31x | -31% |
| only ema200_side = with | full margin 5x | 1290 | 37% | +0.14 | 0.00x | +0.0% | 21% | 45% | -100% | 240 | 38% | +0.15 | 6.64x | -77% |
| only ema200_side = with | risk 10%/trade (<=5x) | 1290 | 37% | +0.14 | 0.14x | +0.0% | 11% | 44% | -99% | 240 | 38% | +0.15 | 2.28x | -71% |
| only ema200_side = with | risk 2%/trade (<=5x) | 1290 | 37% | +0.14 | 1.53x | +0.0% | 0% | 43% | -51% | 240 | 38% | +0.15 | 1.31x | -31% |

## 1D chart

- Zone touches: **1695**. The level held at the touch candle's close **66%** of the time (close back on the zone's side).
- Reversal trades (held at close): research **895**, win **34%**, fail **65%**, avg **+0.04 R** (break-even ~33%).

### Which conditions make the reversal work? (research)

*diff* = win rate with this condition minus without it. HELPS/HURTS = q < 0.10 across all rows AND the same direction in both halves.

No single condition passed all checks.

### Volume: the key question

Win rate of the reversal trade by **volume into the level** (rows) x **volume on the touch candle** (columns), research period:

| volume into level \ touch volume | climax >3x | high 1.5-3x | low <0.7x | normal |
|---|---|---|---|---|
| fading | 0% (n=1) | 31% (n=13) | 27% (n=52) | 35% (n=148) |
| rising | 29% (n=7) | 40% (n=40) | 33% (n=52) | 37% (n=89) |
| steady | 0% (n=1) | 36% (n=69) | 35% (n=133) | 33% (n=290) |

vol_slope x structure_vs:

| vol_slope | structure_vs | trades | win | avg R |
|---|---|---|---|---|
| fading | against | 60 | 33% | +0.00 |
| fading | range | 97 | 28% | -0.16 |
| fading | with | 69 | 38% | +0.13 |
| flat | against | 135 | 32% | -0.04 |
| flat | range | 158 | 35% | +0.05 |
| flat | with | 139 | 37% | +0.12 |
| rising | against | 63 | 33% | +0.03 |
| rising | range | 105 | 40% | +0.20 |
| rising | with | 69 | 30% | -0.05 |

vol_div x rsi_div:

| vol_div | rsi_div | trades | win | avg R |
|---|---|---|---|---|
| no | no | 849 | 34% | +0.04 |
| no | yes | 15 | 13% | -0.60 |
| yes | no | 17 | 47% | +0.41 |
| yes | yes | 14 | 36% | +0.07 |

vol_touch x wick:

| vol_touch | wick | trades | win | avg R |
|---|---|---|---|---|
| climax >3x | medium | 2 | 50% | +0.50 |
| climax >3x | small | 4 | 0% | -0.53 |
| climax >3x | strong >=0.5 | 3 | 33% | +0.33 |
| high 1.5-3x | medium | 44 | 41% | +0.23 |
| high 1.5-3x | small | 53 | 34% | +0.05 |
| high 1.5-3x | strong >=0.5 | 25 | 36% | +0.10 |
| low <0.7x | medium | 120 | 36% | +0.07 |
| low <0.7x | small | 54 | 35% | +0.06 |
| low <0.7x | strong >=0.5 | 63 | 25% | -0.24 |
| normal | medium | 231 | 30% | -0.10 |
| normal | small | 178 | 37% | +0.10 |
| normal | strong >=0.5 | 118 | 41% | +0.22 |

vol_approach x weekly_trend_vs:

| vol_approach | weekly_trend_vs | trades | win | avg R |
|---|---|---|---|---|
| fading | against | 68 | 37% | +0.10 |
| fading | flat | 59 | 24% | -0.26 |
| fading | with | 87 | 36% | +0.07 |
| rising | against | 45 | 42% | +0.27 |
| rising | flat | 75 | 33% | +0.04 |
| rising | with | 68 | 35% | +0.06 |
| steady | against | 148 | 41% | +0.22 |
| steady | flat | 187 | 35% | +0.06 |
| steady | with | 158 | 27% | -0.18 |

### Every condition (research)

| feature | value | trades | win | win without | diff | avg R | half 1 | half 2 | q | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| daily_trend_vs | against | 382 | 34% | 35% | -1 pts | +0.01 | -10 pts | +4 pts | 0.88 | noise |
| daily_trend_vs | with | 513 | 35% | 34% | +1 pts | +0.05 | +10 pts | -4 pts | 0.88 | noise |
| ema200_side | against | 409 | 35% | 34% | +1 pts | +0.05 | -10 pts | +8 pts | 0.88 | noise |
| ema200_side | with | 486 | 34% | 35% | -1 pts | +0.02 | +10 pts | -8 pts | 0.88 | noise |
| ema50_side | against | 382 | 34% | 35% | -1 pts | +0.01 | -10 pts | +4 pts | 0.88 | noise |
| ema50_side | with | 513 | 35% | 34% | +1 pts | +0.05 | +10 pts | -4 pts | 0.88 | noise |
| macd_turn | no | 395 | 32% | 36% | -4 pts | -0.03 | -3 pts | -5 pts | 0.88 | consistent, not significant |
| macd_turn | yes | 500 | 36% | 32% | +4 pts | +0.09 | +3 pts | +5 pts | 0.88 | consistent, not significant |
| retest | first touch | 400 | 33% | 35% | -2 pts | +0.00 | +1 pts | -4 pts | 0.88 | noise |
| retest | retest | 495 | 35% | 33% | +2 pts | +0.06 | -1 pts | +4 pts | 0.88 | noise |
| rsi | normal | 840 | 34% | 36% | -2 pts | +0.03 | -27 pts | +8 pts | 0.88 | noise |
| rsi | stretched | 55 | 36% | 34% | +2 pts | +0.11 | +27 pts | -8 pts | 0.88 | noise |
| speed | fast >2 | 89 | 33% | 34% | -2 pts | +0.00 | -3 pts | -1 pts | 0.88 | consistent, not significant |
| speed | medium | 150 | 35% | 34% | +0 pts | +0.04 | -10 pts | +8 pts | 0.96 | noise |
| speed | slow <1 | 656 | 34% | 34% | +1 pts | +0.04 | +9 pts | -5 pts | 0.96 | noise |
| structure | down | 242 | 36% | 34% | +3 pts | +0.10 | +8 pts | -1 pts | 0.88 | noise |
| structure | range | 360 | 34% | 34% | +0 pts | +0.04 | -5 pts | +4 pts | 0.96 | noise |
| structure | up | 293 | 32% | 35% | -3 pts | -0.02 | -2 pts | -3 pts | 0.88 | consistent, not significant |
| structure_vs | against | 258 | 33% | 35% | -2 pts | -0.02 | +0 pts | -4 pts | 0.88 | noise |
| structure_vs | range | 360 | 34% | 34% | +0 pts | +0.04 | -5 pts | +4 pts | 0.96 | noise |
| structure_vs | with | 277 | 36% | 34% | +2 pts | +0.08 | +6 pts | -0 pts | 0.88 | noise |
| sweep | no | 391 | 36% | 33% | +2 pts | +0.07 | +1 pts | +3 pts | 0.88 | consistent, not significant |
| sweep | yes | 504 | 33% | 36% | -2 pts | +0.01 | -1 pts | -3 pts | 0.88 | consistent, not significant |
| vol_approach | fading | 214 | 33% | 35% | -2 pts | -0.01 | +0 pts | -4 pts | 0.88 | noise |
| vol_approach | rising | 188 | 36% | 34% | +2 pts | +0.10 | +5 pts | +1 pts | 0.88 | consistent, not significant |
| vol_approach | steady | 493 | 34% | 34% | -0 pts | +0.03 | -3 pts | +2 pts | 0.99 | noise |
| vol_div | no | 864 | 34% | 42% | -8 pts | +0.03 | -17 pts | -2 pts | 0.88 | consistent, not significant |
| vol_div | yes | 31 | 42% | 34% | +8 pts | +0.26 | - | +2 pts | 0.88 | noise |
| vol_slope | fading | 226 | 32% | 35% | -3 pts | -0.03 | -3 pts | -2 pts | 0.88 | consistent, not significant |
| vol_slope | flat | 432 | 35% | 34% | +1 pts | +0.04 | +1 pts | +1 pts | 0.92 | consistent, not significant |
| vol_slope | rising | 237 | 35% | 34% | +2 pts | +0.08 | +2 pts | +1 pts | 0.88 | consistent, not significant |
| vol_touch | high 1.5-3x | 122 | 37% | 34% | +3 pts | +0.12 | +5 pts | +2 pts | 0.88 | consistent, not significant |
| vol_touch | low <0.7x | 237 | 33% | 35% | -2 pts | -0.01 | +4 pts | -6 pts | 0.88 | noise |
| vol_touch | normal | 527 | 35% | 34% | +1 pts | +0.04 | -6 pts | +5 pts | 0.96 | noise |
| weekly_trend_vs | against | 261 | 40% | 32% | +8 pts | +0.20 | +3 pts | +11 pts | 0.88 | consistent, not significant |
| weekly_trend_vs | flat | 321 | 33% | 35% | -2 pts | -0.00 | -6 pts | -0 pts | 0.88 | consistent, not significant |
| weekly_trend_vs | with | 313 | 31% | 36% | -5 pts | -0.06 | +4 pts | -10 pts | 0.88 | noise |
| wick | medium | 397 | 33% | 35% | -2 pts | -0.01 | -1 pts | -3 pts | 0.88 | consistent, not significant |
| wick | small | 289 | 35% | 34% | +1 pts | +0.07 | +4 pts | -0 pts | 0.88 | noise |
| wick | strong >=0.5 | 209 | 35% | 34% | +1 pts | +0.07 | -4 pts | +5 pts | 0.88 | noise |
| zone_touches | 3-4 | 402 | 32% | 37% | -5 pts | -0.05 | -4 pts | -6 pts | 0.88 | consistent, not significant |
| zone_touches | 5+ | 493 | 37% | 32% | +5 pts | +0.10 | +4 pts | +6 pts | 0.88 | consistent, not significant |
| zone_weekly | no | 648 | 33% | 36% | -3 pts | +0.01 | +2 pts | -6 pts | 0.88 | noise |
| zone_weekly | yes | 247 | 36% | 33% | +3 pts | +0.10 | -2 pts | +6 pts | 0.88 | noise |

### Turning it into a rule (1D)

Account simulation at up to **5x**: one trade at a time, compounding, after fees and slippage (funding not included). Trades whose stop lies beyond the liquidation price are skipped. *final* = ending equity as a multiple of the start; *median week* = typical week's return.

| rule | sizing | research trades | win | avg R | final | median week | weeks >= +20% | losing weeks | max drawdown | holdout trades | holdout win | holdout R | holdout final | holdout max DD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| every reversal trade | full margin 5x | 895 | 34% | +0.04 | 0.00x | +0.0% | 16% | 34% | -100% | 179 | 35% | +0.06 | 0.01x | -100% |
| every reversal trade | risk 10%/trade (<=5x) | 895 | 34% | +0.04 | 0.20x | +0.0% | 3% | 31% | -94% | 179 | 35% | +0.06 | 0.44x | -77% |
| every reversal trade | risk 2%/trade (<=5x) | 895 | 34% | +0.04 | 0.98x | +0.0% | 0% | 31% | -35% | 179 | 35% | +0.06 | 0.90x | -23% |

## Feature definitions

- **vol_touch**: touch-candle volume / 20-candle average
- **vol_approach**: avg volume of the 5 candles into the level / the 5 before them (<0.8 fading, >1.25 rising)
- **vol_slope**: volume trend over the last 10 candles (fading / flat / rising)
- **vol_div**: price made a new 20-candle extreme into the level on LOWER volume than the previous extreme
- **wick**: rejection wick: share of the candle range on the level side (>=0.5 strong)
- **sweep**: candle pierced the zone level and closed back on the zone's side
- **rsi**: RSI(14) at the touch: stretched toward the level (<35 at support / >65 at resistance)
- **rsi_div**: RSI divergence at the touch (price new 20-candle extreme, RSI not)
- **macd_turn**: MACD histogram turned in the reversal direction on the touch candle
- **ema50_side**: close vs EMA50 on this timeframe: with the reversal / against
- **ema200_side**: close vs EMA200 on this timeframe: with the reversal / against
- **structure**: market structure from the last 2 confirmed swing highs and lows: up / down / range
- **structure_vs**: structure with or against the reversal direction
- **speed**: approach speed: ATRs travelled in the 5 candles into the level (fast > 2)
- **retest**: zone touched in the previous 30 candles (retest) vs first touch
- **zone_weekly**: zone contains a weekly swing
- **zone_touches**: number of swings forming the zone (3-4 / 5+)
- **weekly_trend_vs**: weekly trend with / against the reversal direction
- **daily_trend_vs**: daily close vs daily EMA50 with / against the reversal direction (4h study only)

Raw events: `sr_touches_4h.csv`, `sr_touches_1D.csv`; all condition stats: `sr_features_*.csv`.
