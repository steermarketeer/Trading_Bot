# Exit rules: how should a trade be closed?

Each trade is replayed on **5-minute candles** (stop checked before target inside each 5m candle; a moved stop applies from the next 5m candle). Results in R (1R = the initial risk), **after fees and slippage**. *win* = the trade ended with a profit after costs. *PF* = profit factor (gross wins / gross losses). The rule to use is chosen on the research years only (2022-25 for breakouts, 2020-25 for zone bounces), then checked on the holdout.
## Summary: best exit per trade set (chosen on research, then checked on holdout)

| trades | best exit (research) | research n | research win | research avg R | holdout n | holdout win | holdout avg R |
|---|---|---|---|---|---|---|---|
| Breakouts, certainty >= 7 | atr_trail_3_after1R | 331 | 34% | +0.61 | 37 | 30% | -0.28 |
| Breakouts, certainty >= 6 | atr_trail_3_after1R | 1015 | 30% | +0.38 | 230 | 27% | +0.01 |
| 1D S/R zone bounce (all) | atr_trail_3 | 437 | 34% | +0.43 | 76 | 34% | +0.60 |

Rule names: fixed_T = fixed target; beX_T = stop to entry after +X R, target T; partial_* = half off at +1R then the rest to target/trail with stop at entry; atr_trail_k = trailing stop k x ATR ("_after1R" = starts after +1R); low3_trail = stop under the lowest low of the last 3 candles; timeN_2R = 2R target but exit after N candles if +0.5R was never reached.


## Breakouts, certainty >= 7

Research 331 trades, holdout 37 trades.

**Year by year (avg R after costs, win % in brackets):**

| year | trades | fixed_1R | partial_2R | fixed_2R | be1_2R | atr_trail_2 | atr_trail_3 |
|---|---|---|---|---|---|---|---|
| 2022 | 80 | +0.26 (66%) | +0.36 (66%) | +0.53 (54%) | +0.46 (44%) | +0.65 (50%) | +1.19 (40%) |
| 2023 | 138 | +0.00 (55%) | +0.07 (55%) | +0.13 (41%) | +0.14 (35%) | +0.03 (36%) | +0.74 (30%) |
| 2024 | 34 | +0.04 (56%) | -0.03 (56%) | -0.46 (21%) | -0.11 (21%) | -0.52 (18%) | -0.95 (3%) |
| 2025 | 79 | +0.11 (59%) | +0.17 (59%) | +0.28 (47%) | +0.22 (35%) | +0.45 (51%) | +0.43 (46%) |
| holdout | 37 | +0.33 (70%) | +0.30 (70%) | +0.38 (49%) | +0.27 (32%) | +0.02 (41%) | -0.32 (27%) |

All rules, sorted by research avg R:

| exit rule | win (research) | avg R (research) | PF | win (holdout) | avg R (holdout) | PF (holdout) |
|---|---|---|---|---|---|---|
| atr_trail_3_after1R | 34% | +0.61 | 1.93 | 30% | -0.28 | 0.56 |
| atr_trail_3 | 34% | +0.60 | 1.94 | 27% | -0.32 | 0.49 |
| atr_trail_2 | 41% | +0.23 | 1.45 | 41% | +0.02 | 1.06 |
| be1_2R | 36% | +0.21 | 1.46 | 32% | +0.27 | 1.77 |
| fixed_2R | 43% | +0.20 | 1.33 | 49% | +0.38 | 1.68 |
| atr_trail_2_after1R | 43% | +0.18 | 1.34 | 43% | +0.05 | 1.11 |
| be1_3R | 23% | +0.18 | 1.38 | 19% | +0.11 | 1.30 |
| time6_2R | 41% | +0.18 | 1.31 | 38% | +0.14 | 1.24 |
| time3_2R | 40% | +0.16 | 1.31 | 51% | +0.07 | 1.15 |
| partial_2R | 59% | +0.15 | 1.35 | 70% | +0.30 | 1.93 |
| partial_3R | 59% | +0.14 | 1.31 | 70% | +0.22 | 1.68 |
| be0.5_2R | 23% | +0.12 | 1.38 | 16% | +0.08 | 1.36 |
| fixed_3R | 31% | +0.12 | 1.17 | 35% | +0.09 | 1.13 |
| partial_trail2ATR | 59% | +0.12 | 1.27 | 70% | +0.19 | 1.60 |
| fixed_1.5R | 47% | +0.10 | 1.17 | 59% | +0.41 | 1.92 |
| fixed_1R | 59% | +0.09 | 1.21 | 70% | +0.33 | 2.01 |
| be0.5_3R | 15% | +0.08 | 1.25 | 14% | +0.12 | 1.50 |
| atr_trail_1.5_after1R | 48% | +0.06 | 1.13 | 62% | +0.19 | 1.46 |
| atr_trail_1.5 | 43% | +0.04 | 1.10 | 49% | +0.11 | 1.31 |
| low3_trail | 27% | +0.02 | 1.06 | 35% | +0.22 | 1.82 |

## Breakouts, certainty >= 6

Research 1015 trades, holdout 230 trades.

**Year by year (avg R after costs, win % in brackets):**

| year | trades | fixed_1R | partial_2R | fixed_2R | be1_2R | atr_trail_2 | atr_trail_3 |
|---|---|---|---|---|---|---|---|
| 2022 | 230 | +0.09 (58%) | +0.14 (58%) | +0.22 (43%) | +0.19 (34%) | +0.18 (38%) | +0.49 (30%) |
| 2023 | 315 | +0.07 (59%) | +0.13 (59%) | +0.13 (42%) | +0.19 (35%) | +0.13 (35%) | +0.27 (27%) |
| 2024 | 207 | +0.10 (59%) | +0.11 (59%) | +0.06 (40%) | +0.13 (32%) | +0.37 (32%) | +0.62 (29%) |
| 2025 | 263 | -0.04 (52%) | -0.03 (52%) | -0.04 (35%) | -0.01 (27%) | +0.17 (34%) | +0.15 (32%) |
| holdout | 230 | +0.00 (55%) | +0.00 (55%) | +0.06 (39%) | +0.00 (27%) | +0.04 (32%) | +0.01 (27%) |

All rules, sorted by research avg R:

| exit rule | win (research) | avg R (research) | PF | win (holdout) | avg R (holdout) | PF (holdout) |
|---|---|---|---|---|---|---|
| atr_trail_3_after1R | 30% | +0.38 | 1.54 | 27% | +0.01 | 1.01 |
| atr_trail_3 | 29% | +0.36 | 1.52 | 27% | +0.01 | 1.01 |
| atr_trail_2 | 35% | +0.20 | 1.35 | 32% | +0.04 | 1.07 |
| atr_trail_2_after1R | 37% | +0.19 | 1.32 | 35% | +0.05 | 1.09 |
| be1_3R | 23% | +0.15 | 1.30 | 20% | +0.03 | 1.05 |
| be1_2R | 32% | +0.12 | 1.25 | 27% | +0.00 | 1.01 |
| fixed_3R | 32% | +0.12 | 1.17 | 31% | +0.06 | 1.07 |
| partial_trail2ATR | 57% | +0.12 | 1.26 | 55% | +0.01 | 1.01 |
| partial_3R | 57% | +0.10 | 1.21 | 55% | +0.01 | 1.03 |
| fixed_2R | 40% | +0.09 | 1.15 | 39% | +0.06 | 1.09 |
| atr_trail_1.5_after1R | 43% | +0.09 | 1.17 | 43% | +0.05 | 1.08 |
| partial_2R | 57% | +0.09 | 1.19 | 55% | +0.00 | 1.01 |
| time6_2R | 39% | +0.09 | 1.14 | 36% | +0.05 | 1.08 |
| time3_2R | 38% | +0.08 | 1.14 | 35% | -0.01 | 0.98 |
| low3_trail | 27% | +0.07 | 1.17 | 30% | +0.32 | 1.82 |
| atr_trail_1.5 | 38% | +0.06 | 1.12 | 38% | +0.03 | 1.05 |
| fixed_1.5R | 46% | +0.06 | 1.10 | 45% | +0.04 | 1.07 |
| fixed_1R | 57% | +0.05 | 1.11 | 55% | +0.00 | 1.01 |
| be0.5_2R | 21% | +0.05 | 1.15 | 19% | -0.04 | 0.90 |
| be0.5_3R | 14% | +0.04 | 1.12 | 14% | -0.02 | 0.96 |

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

