# Target ratio sweep on the research-chosen version

Same 162 trades, entries, stops, replay, costs and funding; only the fixed reward:risk ratio changes, per family. **win % = profit after costs.** Chosen on 2022 - Oct 2025 (best t-score, >= 3 of 4 good years); the holdout is shown for every ratio and never used to choose.

Check: the 2 : 1 (breakouts) / 3 : 1 (bounces) rows reproduce the chosen version's trades to 0.00e+00 R.

## breakouts (78 trades 2022-25, 22 holdout)

Chosen on 2022-25: **1 : 1**

| target | win % | avg R | profit factor | targets hit | t-score | good years /4 | account 2022-25 | worst drop | holdout win % | holdout avg R | holdout account |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 : 1 | 78% | +0.50 | 3.09 | 78% | 5.19 | 4 | 4.28x | -9% | 73% | +0.38 | 1.28x |
| 1.25 : 1 | 71% | +0.52 | 2.60 | 71% | 4.34 | 4 | 4.76x | -9% | 64% | +0.36 | 1.27x |
| 1.5 : 1 | 67% | +0.60 | 2.62 | 67% | 4.35 | 4 | 5.86x | -9% | 59% | +0.40 | 1.35x |
| 1.75 : 1 | 64% | +0.67 | 2.74 | 60% | 4.44 | 4 | 6.83x | -11% | 59% | +0.54 | 1.50x |
| 2 : 1 | 62% | +0.74 | 2.80 | 58% | 4.47 | 4 | 7.96x | -10% | 59% | +0.69 | 1.67x |
| 2.5 : 1 | 56% | +0.79 | 2.69 | 49% | 4.10 | 4 | 8.77x | -21% | 45% | +0.50 | 1.39x |
| 3 : 1 | 53% | +0.82 | 2.59 | 41% | 3.76 | 3 | 8.34x | -29% | 36% | +0.28 | 1.11x |
| 3.5 : 1 | 51% | +0.94 | 2.79 | 38% | 3.91 | 3 | 10.57x | -29% | 32% | +0.18 | 0.99x |
| 4 : 1 | 50% | +1.01 | 2.87 | 35% | 3.86 | 3 | 12.62x | -29% | 32% | +0.13 | 0.99x |
| 5 : 1 | 45% | +0.82 | 2.39 | 22% | 2.93 | 3 | 6.79x | -29% | 27% | -0.29 | 0.75x |
| 6 : 1 | 44% | +0.91 | 2.52 | 18% | 2.94 | 3 | 8.62x | -29% | 27% | -0.24 | 0.77x |
| no target (60-candle limit) | 44% | +0.84 | 2.39 | 0% | 2.57 | 3 | 6.59x | -29% | 27% | -0.30 | 0.75x |

## 1D bounces (51 trades 2022-25, 11 holdout)

Chosen on 2022-25: **2.5 : 1**

| target | win % | avg R | profit factor | targets hit | t-score | good years /4 | account 2022-25 | worst drop | holdout win % | holdout avg R | holdout account |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 : 1 | 65% | +0.27 | 1.75 | 65% | 2.00 | 4 | 1.30x | -9% | 91% | +0.80 | 1.19x |
| 1.25 : 1 | 59% | +0.29 | 1.67 | 57% | 1.82 | 3 | 1.31x | -13% | 82% | +0.82 | 1.19x |
| 1.5 : 1 | 59% | +0.43 | 2.00 | 57% | 2.46 | 4 | 1.51x | -11% | 82% | +1.03 | 1.24x |
| 1.75 : 1 | 59% | +0.53 | 2.25 | 53% | 2.83 | 4 | 1.67x | -11% | 82% | +1.23 | 1.30x |
| 2 : 1 | 59% | +0.64 | 2.51 | 51% | 3.16 | 4 | 1.85x | -10% | 73% | +1.22 | 1.29x |
| 2.5 : 1 | 59% | +0.83 | 2.95 | 45% | 3.61 | 4 | 2.20x | -10% | 73% | +1.37 | 1.33x |
| 3 : 1 | 55% | +0.87 | 2.85 | 39% | 3.34 | 4 | 2.23x | -16% | 73% | +1.69 | 1.41x |
| 3.5 : 1 | 51% | +0.86 | 2.66 | 29% | 3.00 | 3 | 2.15x | -16% | 73% | +1.91 | 1.47x |
| 4 : 1 | 49% | +0.90 | 2.69 | 27% | 2.92 | 3 | 2.23x | -16% | 73% | +1.81 | 1.44x |
| 5 : 1 | 49% | +1.09 | 3.04 | 24% | 3.12 | 4 | 2.59x | -16% | 73% | +2.08 | 1.52x |
| 6 : 1 | 49% | +1.09 | 3.03 | 16% | 2.97 | 4 | 2.55x | -16% | 73% | +1.93 | 1.47x |
| no target (60-candle limit) | 49% | +1.32 | 3.47 | 0% | 2.87 | 4 | 3.06x | -16% | 73% | +2.30 | 1.57x |

## Both families together

| targets | period | trades | win % | avg R | profit factor | account | worst drop |
|---|---|---|---|---|---|---|---|
| current (breakouts 2 : 1, bounces 3 : 1) | 2022 - Oct 2025 | 129 | 59% | +0.79 | 2.82 | 16.89x | -16% |
| current (breakouts 2 : 1, bounces 3 : 1) | holdout | 33 | 64% | +1.02 | 3.71 | 2.32x | -13% |
| chosen (1 : 1 / 2.5 : 1) | 2022 - Oct 2025 | 129 | 71% | +0.63 | 3.02 | 9.14x | -10% |
| chosen (1 : 1 / 2.5 : 1) | holdout | 33 | 73% | +0.71 | 3.63 | 1.69x | -11% |

Audit: pending.
