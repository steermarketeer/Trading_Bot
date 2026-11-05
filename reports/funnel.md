# Which rule removes the most trades?

Breakouts on 2h / 4h / 1D since 2022 (6,567 main-rule breakout events, ~26 per week). win % = profit after costs at 2:1 (candle data).

## Funnel: rules applied one after another

| rule | trades removed | win % of removed trades | trades left | per week | win % of the rest |
|---|---|---|---|---|---|
| all main-rule breakouts | 0 | - | 6567 | 26.33 | 36% |
| + certainty 7/10+ | 5739 | 35% | 828 | 3.32 | 44% |
| + stop >= 0.6% | 34 | 41% | 794 | 3.18 | 44% |
| + not the quietest 20% | 135 | 44% | 659 | 2.64 | 44% |
| + BTC 4h agrees | 73 | 19% | 586 | 2.35 | 47% |
| + 6h MACD agrees | 195 | 37% | 391 | 1.57 | 52% |
| + clean risk zone | 113 | 40% | 278 | 1.11 | 57% |

## Drop one rule at a time (all other rules kept)

| rule dropped | trades | per week | win % | avg R |
|---|---|---|---|---|
| none (v3 breakouts) | 278 | 1.11 | 57% | +0.59 |
| certainty 7/10+ | 1749 | 7.01 | 40% | +0.06 |
| stop >= 0.6% | 282 | 1.13 | 57% | +0.58 |
| not the quietest 20% | 324 | 1.30 | 56% | +0.55 |
| BTC 4h agrees | 291 | 1.17 | 55% | +0.53 |
| 6h MACD agrees | 377 | 1.51 | 51% | +0.43 |
| clean risk zone | 391 | 1.57 | 52% | +0.46 |

## 1D bounces funnel (3:1)

| rule | trades | per week | win % (3:1) |
|---|---|---|---|
| strong-zone touches (1D) | 1401 | 5.63 | - |
| + held at close | 924 | 3.72 | - |
| + confirmation candle (traded) | 439 | 1.77 | 35% |
| + 4th test or later | 345 | 1.39 | 36% |

Bounces on the 1st-3rd test: win 32%, avg +0.09 R vs 4th+: avg +0.29 R.

