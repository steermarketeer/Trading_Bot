# Exit rules: how should a trade be closed?

Each trade is replayed on **5-minute candles** (stop checked before target inside each 5m candle; a moved stop applies from the next 5m candle). Results in R (1R = the initial risk), **after fees and slippage**. *win* = the trade ended with a profit after costs. *PF* = profit factor (gross wins / gross losses). The rule to use is chosen on the research years only (2022-25 for breakouts, 2020-25 for zone bounces), then checked on the holdout.
## Summary: best exit per trade set (chosen on research, then checked on holdout)

| trades | best exit (research) | research n | research win | research avg R | holdout n | holdout win | holdout avg R |
|---|---|---|---|---|---|---|---|
| Breakouts, certainty >= 7 | atr_trail_3_after1R | 333 | 33% | +0.60 | 38 | 32% | -0.25 |
| Breakouts, certainty >= 6 | atr_trail_3_after1R | 1016 | 30% | +0.37 | 223 | 27% | -0.04 |
| 1D S/R zone bounce (all) | atr_trail_3 | 437 | 34% | +0.43 | 76 | 34% | +0.60 |

Rule names: fixed_T = fixed target; beX_T = stop to entry after +X R, target T; partial_* = half off at +1R then the rest to target/trail with stop at entry; atr_trail_k = trailing stop k x ATR ("_after1R" = starts after +1R); low3_trail = stop under the lowest low of the last 3 candles; timeN_2R = 2R target but exit after N candles if +0.5R was never reached.


## Breakouts, certainty >= 7

Research 333 trades, holdout 38 trades.

**Year by year (avg R after costs, win % in brackets):**

| year | trades | fixed_1R | partial_2R | fixed_2R | be1_2R | atr_trail_2 | atr_trail_3 |
|---|---|---|---|---|---|---|---|
| 2022 | 79 | +0.22 (65%) | +0.31 (65%) | +0.47 (52%) | +0.40 (42%) | +0.63 (48%) | +1.12 (38%) |
| 2023 | 139 | -0.01 (55%) | +0.06 (55%) | +0.12 (40%) | +0.13 (35%) | +0.02 (36%) | +0.73 (30%) |
| 2024 | 36 | +0.02 (56%) | -0.06 (56%) | -0.50 (19%) | -0.14 (19%) | -0.58 (17%) | -1.01 (0%) |
| 2025 | 79 | +0.11 (59%) | +0.18 (59%) | +0.32 (48%) | +0.25 (37%) | +0.48 (52%) | +0.55 (47%) |
| holdout | 38 | +0.34 (71%) | +0.33 (71%) | +0.42 (50%) | +0.32 (34%) | +0.05 (42%) | -0.29 (29%) |

All rules, sorted by research avg R:

| exit rule | win (research) | avg R (research) | PF | win (holdout) | avg R (holdout) | PF (holdout) |
|---|---|---|---|---|---|---|
| atr_trail_3_after1R | 33% | +0.60 | 1.89 | 32% | -0.25 | 0.60 |
| atr_trail_3 | 33% | +0.59 | 1.91 | 29% | -0.29 | 0.53 |
| atr_trail_2 | 41% | +0.21 | 1.42 | 42% | +0.05 | 1.12 |
| be1_2R | 35% | +0.19 | 1.41 | 34% | +0.32 | 1.92 |
| fixed_2R | 43% | +0.18 | 1.30 | 50% | +0.42 | 1.77 |
| atr_trail_2_after1R | 42% | +0.17 | 1.30 | 45% | +0.07 | 1.18 |
| be1_3R | 23% | +0.16 | 1.33 | 21% | +0.16 | 1.45 |
| time6_2R | 41% | +0.16 | 1.27 | 39% | +0.19 | 1.33 |
| partial_2R | 58% | +0.14 | 1.30 | 71% | +0.33 | 2.05 |
| time3_2R | 40% | +0.13 | 1.26 | 53% | +0.12 | 1.27 |
| partial_3R | 58% | +0.12 | 1.27 | 71% | +0.25 | 1.80 |
| partial_trail2ATR | 58% | +0.11 | 1.24 | 71% | +0.22 | 1.69 |
| fixed_3R | 31% | +0.11 | 1.14 | 37% | +0.14 | 1.21 |
| be0.5_2R | 23% | +0.11 | 1.33 | 18% | +0.13 | 1.60 |
| fixed_1.5R | 47% | +0.08 | 1.14 | 61% | +0.44 | 2.01 |
| fixed_1R | 58% | +0.08 | 1.18 | 71% | +0.34 | 2.10 |
| be0.5_3R | 14% | +0.06 | 1.18 | 16% | +0.17 | 1.74 |
| atr_trail_1.5_after1R | 47% | +0.04 | 1.08 | 63% | +0.22 | 1.53 |
| atr_trail_1.5 | 42% | +0.03 | 1.06 | 50% | +0.13 | 1.36 |
| low3_trail | 27% | +0.02 | 1.07 | 37% | +0.26 | 2.00 |

## Breakouts, certainty >= 6

Research 1016 trades, holdout 223 trades.

**Year by year (avg R after costs, win % in brackets):**

| year | trades | fixed_1R | partial_2R | fixed_2R | be1_2R | atr_trail_2 | atr_trail_3 |
|---|---|---|---|---|---|---|---|
| 2022 | 230 | +0.09 (58%) | +0.14 (58%) | +0.21 (43%) | +0.18 (34%) | +0.16 (37%) | +0.47 (30%) |
| 2023 | 316 | +0.08 (59%) | +0.13 (59%) | +0.14 (42%) | +0.19 (35%) | +0.16 (36%) | +0.29 (27%) |
| 2024 | 204 | +0.09 (59%) | +0.10 (59%) | +0.06 (40%) | +0.12 (32%) | +0.37 (32%) | +0.58 (29%) |
| 2025 | 266 | -0.06 (51%) | -0.05 (51%) | -0.06 (35%) | -0.03 (27%) | +0.15 (33%) | +0.13 (31%) |
| holdout | 223 | +0.02 (56%) | +0.02 (56%) | +0.06 (39%) | +0.01 (27%) | +0.04 (31%) | -0.04 (27%) |

All rules, sorted by research avg R:

| exit rule | win (research) | avg R (research) | PF | win (holdout) | avg R (holdout) | PF (holdout) |
|---|---|---|---|---|---|---|
| atr_trail_3_after1R | 30% | +0.37 | 1.52 | 27% | -0.04 | 0.95 |
| atr_trail_3 | 29% | +0.35 | 1.49 | 27% | -0.04 | 0.95 |
| atr_trail_2 | 35% | +0.20 | 1.34 | 31% | +0.04 | 1.06 |
| atr_trail_2_after1R | 37% | +0.19 | 1.31 | 34% | +0.05 | 1.09 |
| be1_3R | 23% | +0.14 | 1.28 | 20% | +0.02 | 1.05 |
| be1_2R | 32% | +0.12 | 1.24 | 27% | +0.01 | 1.02 |
| partial_trail2ATR | 57% | +0.12 | 1.25 | 56% | +0.02 | 1.03 |
| fixed_3R | 31% | +0.11 | 1.15 | 31% | +0.05 | 1.07 |
| partial_3R | 57% | +0.09 | 1.19 | 56% | +0.02 | 1.04 |
| fixed_2R | 40% | +0.09 | 1.14 | 39% | +0.06 | 1.09 |
| atr_trail_1.5_after1R | 43% | +0.08 | 1.15 | 43% | +0.05 | 1.09 |
| partial_2R | 57% | +0.08 | 1.17 | 56% | +0.02 | 1.03 |
| time6_2R | 38% | +0.08 | 1.13 | 36% | +0.05 | 1.07 |
| time3_2R | 38% | +0.07 | 1.12 | 35% | -0.02 | 0.97 |
| low3_trail | 27% | +0.06 | 1.14 | 30% | +0.32 | 1.83 |
| fixed_1.5R | 46% | +0.05 | 1.09 | 46% | +0.05 | 1.08 |
| atr_trail_1.5 | 38% | +0.05 | 1.11 | 37% | +0.02 | 1.04 |
| fixed_1R | 57% | +0.05 | 1.10 | 56% | +0.02 | 1.04 |
| be0.5_2R | 21% | +0.04 | 1.13 | 19% | -0.03 | 0.91 |
| be0.5_3R | 14% | +0.04 | 1.10 | 13% | -0.03 | 0.93 |

## 1D S/R zone bounce (all)

Research 437 trades, holdout 76 trades.

**Year by year (avg R after costs, win % in brackets):**

| year | trades | fixed_1R | partial_2R | fixed_2R | be1_2R | atr_trail_2 | atr_trail_3 |
|---|---|---|---|---|---|---|---|
| 2020 | 32 | -0.03 (50%) | +0.03 (50%) | +0.19 (41%) | +0.10 (31%) | +0.23 (38%) | +0.96 (28%) |
| 2021 | 55 | +0.08 (55%) | +0.12 (55%) | +0.24 (42%) | +0.15 (31%) | +0.46 (40%) | +0.79 (40%) |
| 2022 | 76 | +0.26 (64%) | +0.25 (64%) | +0.26 (43%) | +0.24 (32%) | +0.53 (42%) | +0.69 (38%) |
| 2023 | 114 | +0.13 (59%) | +0.09 (59%) | +0.02 (38%) | +0.07 (28%) | +0.29 (37%) | +0.17 (32%) |
| 2024 | 92 | -0.02 (50%) | +0.02 (50%) | +0.11 (38%) | +0.06 (29%) | +0.51 (36%) | +0.36 (33%) |
| 2025 | 68 | +0.03 (53%) | +0.03 (53%) | +0.01 (35%) | +0.03 (26%) | +0.31 (37%) | +0.14 (31%) |
| holdout | 76 | +0.15 (59%) | +0.11 (59%) | +0.25 (45%) | +0.07 (26%) | +0.49 (43%) | +0.60 (34%) |

All rules, sorted by research avg R:

| exit rule | win (research) | avg R (research) | PF | win (holdout) | avg R (holdout) | PF (holdout) |
|---|---|---|---|---|---|---|
| atr_trail_3 | 34% | +0.43 | 1.70 | 34% | +0.60 | 2.02 |
| atr_trail_3_after1R | 34% | +0.43 | 1.68 | 36% | +0.62 | 2.05 |
| atr_trail_2 | 38% | +0.40 | 1.79 | 43% | +0.49 | 2.02 |
| atr_trail_2_after1R | 41% | +0.39 | 1.71 | 45% | +0.47 | 1.91 |
| fixed_3R | 34% | +0.25 | 1.38 | 41% | +0.36 | 1.60 |
| partial_trail2ATR | 56% | +0.21 | 1.47 | 59% | +0.16 | 1.38 |
| atr_trail_1.5_after1R | 45% | +0.21 | 1.41 | 43% | +0.19 | 1.40 |
| atr_trail_1.5 | 38% | +0.19 | 1.43 | 39% | +0.14 | 1.36 |
| be1_3R | 23% | +0.19 | 1.40 | 20% | +0.10 | 1.24 |
| low3_trail | 25% | +0.16 | 1.52 | 29% | +0.13 | 1.51 |
| partial_3R | 56% | +0.14 | 1.30 | 59% | +0.13 | 1.30 |
| fixed_2R | 39% | +0.12 | 1.19 | 45% | +0.25 | 1.45 |
| be0.5_3R | 17% | +0.12 | 1.32 | 11% | -0.01 | 0.96 |
| time3_2R | 39% | +0.11 | 1.24 | 39% | +0.21 | 1.47 |
| time6_2R | 38% | +0.11 | 1.19 | 46% | +0.29 | 1.60 |
| be1_2R | 29% | +0.11 | 1.23 | 26% | +0.07 | 1.15 |
| fixed_1.5R | 46% | +0.10 | 1.18 | 51% | +0.23 | 1.47 |
| partial_2R | 56% | +0.09 | 1.21 | 59% | +0.11 | 1.26 |
| fixed_1R | 56% | +0.09 | 1.19 | 59% | +0.15 | 1.35 |
| be0.5_2R | 21% | +0.04 | 1.11 | 17% | +0.03 | 1.10 |

