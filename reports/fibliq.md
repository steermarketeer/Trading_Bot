# Liquidity + Fibonacci execution for the v3.1 signals

The v3.1 signal is the spot; entry, stop and target come from Fibonacci and untaken liquidity known at the signal. One position per move. **win % = profit after all costs.** The combination is chosen on 2022 - Oct 2025 only; the holdout (Nov 2025 - Oct 2026) is the honest test.

## Current vs chosen

| setup |  | entry · stop · target | trades 2022-25 | win % | avg R | trades holdout | win % holdout | avg R holdout | avg reward:risk |
|---|---|---|---|---|---|---|---|---|---|
| breakout | current (v3.1) | E0-S0-T0 | 103 | 60% | +0.69 | 27 | 52% | +0.46 | 2.00 |
| breakout | chosen on research | E0-S0-T0 | 103 | 60% | +0.69 | 27 | 52% | +0.46 | 2.00 |
| bounce | current (v3.1) | E0-S0-T0 | 186 | 36% | +0.31 | 42 | 48% | +0.62 | 3.00 |
| bounce | chosen on research | E0-S2-T0 | 187 | 37% | +0.34 | 42 | 50% | +0.81 | 3.00 |

## Account (A+ 4%, others 2%, max 5x)

| strategy | period | trades | per week | win % | avg R | profit factor | account | worst drop |
|---|---|---|---|---|---|---|---|---|
| current (v3.1, one position per move) | 2022 - Oct 2025 | 293 | 1.47 | 45% | +0.45 | 1.78 | 24.75x | -36% |
| current (v3.1, one position per move) | holdout | 69 | 1.48 | 49% | +0.56 | 2.05 | 2.36x | -23% |
| chosen liquidity + Fibonacci | 2022 - Oct 2025 | 293 | 1.47 | 46% | +0.48 | 1.84 | 27.45x | -37% |
| chosen liquidity + Fibonacci | holdout | 69 | 1.48 | 51% | +0.68 | 2.31 | 2.77x | -20% |

## Every combination: breakouts (sorted by research t-score)

| entry · stop · target | trades 2022-25 | win % | avg R | t-score | good years /4 | holdout trades | holdout win % | holdout avg R | avg R:R |
|---|---|---|---|---|---|---|---|---|---|
| market at signal · setup's own stop · setup's own R target | 103 | 60% | +0.69 | 4.77 | 4 | 27 | 52% | +0.46 | 2.00 |
| market at signal · setup's own stop · Fib extension 1.618 | 103 | 47% | +0.87 | 3.57 | 3 | 27 | 30% | -0.06 | 4.39 |
| market at signal · setup's own stop · Fib extension 1.272 | 85 | 55% | +0.65 | 3.25 | 3 | 25 | 40% | +0.03 | 2.48 |
| market at signal · below liquidity past Fib 0.618 · Fib extension 1.618 | 32 | 66% | +0.49 | 2.84 | 3 | 10 | 60% | +0.40 | 1.42 |
| market at signal · below liquidity past Fib 0.618 · setup's own R target | 103 | 55% | +0.24 | 2.22 | 3 | 27 | 41% | -0.02 | 2.00 |
| market at signal · setup's own stop · next untaken liquidity | 62 | 47% | +0.67 | 2.17 | 4 | 19 | 26% | -0.37 | 5.09 |
| market at signal · below Fib 0.786 · setup's own R target | 103 | 54% | +0.21 | 2.05 | 3 | 27 | 41% | -0.02 | 2.00 |
| market at signal · below Fib 0.786 · Fib extension 1.618 | 16 | 69% | +0.49 | 2.03 | 3 | 3 | 67% | +0.31 | 1.40 |
| market at signal · below liquidity past Fib 0.618 · next untaken liquidity | 20 | 65% | +0.43 | 2.00 | 3 | 10 | 20% | -0.18 | 2.51 |
| market at signal · below Fib 0.786 · next untaken liquidity | 18 | 56% | +0.31 | 1.54 | 3 | 9 | 22% | -0.09 | 2.29 |
| limit at Fib 0.382 · below Fib 0.786 · next untaken liquidity | 17 | 53% | +0.25 | 0.83 | 3 | 4 | 75% | +0.80 | 2.51 |
| limit at Fib 0.382 · setup's own stop · setup's own R target | 6 | 50% | +0.41 | 0.60 | 2 | 1 | 0% | -1.13 | 2.00 |
| limit at Fib 0.5 · below Fib 0.786 · setup's own R target | 19 | 42% | +0.15 | 0.45 | 3 | 3 | 67% | +0.42 | 2.00 |
| limit at Fib 0.5 · below Fib 0.786 · Fib extension 1.272 | 19 | 37% | +0.16 | 0.45 | 2 | 3 | 67% | +0.61 | 2.60 |
| limit at Fib 0.5 · below Fib 0.786 · Fib extension 1.618 | 19 | 37% | +0.17 | 0.43 | 2 | 3 | 67% | +0.99 | 3.76 |
| limit at Fib 0.5 · below Fib 0.786 · next untaken liquidity | 19 | 37% | +0.11 | 0.29 | 2 | 3 | 67% | +0.35 | 3.09 |
| limit at Fib 0.5 · below liquidity past Fib 0.618 · Fib extension 1.618 | 19 | 32% | +0.12 | 0.25 | 2 | 3 | 67% | +0.91 | 4.55 |
| limit at Fib 0.382 · below liquidity past Fib 0.618 · next untaken liquidity | 19 | 42% | +0.07 | 0.23 | 3 | 6 | 67% | +0.76 | 2.66 |
| limit at Fib 0.5 · below liquidity past Fib 0.618 · Fib extension 1.272 | 19 | 32% | +0.04 | 0.11 | 1 | 3 | 67% | +0.54 | 3.14 |
| limit at Fib 0.382 · below Fib 0.786 · setup's own R target | 26 | 42% | +0.01 | 0.04 | 2 | 7 | 57% | +0.72 | 2.00 |
| limit at Fib 0.382 · below Fib 0.786 · Fib extension 1.272 | 26 | 42% | +0.01 | 0.02 | 2 | 7 | 57% | +0.54 | 1.58 |
| limit at Fib 0.5 · below liquidity past Fib 0.618 · next untaken liquidity | 19 | 32% | +0.00 | 0.01 | 2 | 3 | 67% | +0.28 | 3.63 |
| market at signal · below liquidity past Fib 0.618 · Fib extension 1.272 | 1 | 0% | -0.28 | 0.00 | 0 | 1 | 100% | +1.52 | 1.45 |
| market at signal · below Fib 0.786 · Fib extension 1.272 | 1 | 0% | -0.25 | 0.00 | 0 | 0 | - |  | 1.22 |
| limit at Fib 0.382 · below Fib 0.786 · Fib extension 1.618 | 26 | 38% | -0.04 | -0.15 | 2 | 7 | 57% | +0.58 | 2.41 |
| limit at Fib 0.382 · below liquidity past Fib 0.618 · Fib extension 1.618 | 26 | 35% | -0.05 | -0.16 | 2 | 7 | 57% | +0.58 | 2.75 |
| limit at Fib 0.382 · setup's own stop · next untaken liquidity | 5 | 20% | -0.23 | -0.24 | 1 | 1 | 0% | -1.13 | 11.14 |
| limit at Fib 0.382 · setup's own stop · Fib extension 1.272 | 6 | 17% | -0.29 | -0.32 | 1 | 1 | 0% | -1.13 | 8.80 |
| limit at Fib 0.382 · below liquidity past Fib 0.618 · setup's own R target | 26 | 38% | -0.09 | -0.38 | 2 | 7 | 57% | +0.61 | 2.00 |
| limit at Fib 0.382 · below liquidity past Fib 0.618 · Fib extension 1.272 | 24 | 33% | -0.11 | -0.41 | 2 | 6 | 67% | +0.71 | 1.87 |
| limit at Fib 0.5 · below liquidity past Fib 0.618 · setup's own R target | 19 | 32% | -0.20 | -0.70 | 1 | 3 | 67% | +0.36 | 2.00 |
| limit at Fib 0.382 · setup's own stop · Fib extension 1.618 | 6 | 0% | -1.14 | -20.09 | 0 | 1 | 0% | -1.13 | 13.45 |

## Every combination: bounces (sorted by research t-score)

| entry · stop · target | trades 2022-25 | win % | avg R | t-score | good years /4 | holdout trades | holdout win % | holdout avg R | avg R:R |
|---|---|---|---|---|---|---|---|---|---|
| market at signal · below Fib 0.786 · setup's own R target | 187 | 37% | +0.34 | 2.55 | 3 | 42 | 50% | +0.81 | 3.00 |
| market at signal · setup's own stop · setup's own R target | 186 | 36% | +0.31 | 2.26 | 4 | 42 | 48% | +0.62 | 3.00 |
| market at signal · below liquidity past Fib 0.618 · setup's own R target | 188 | 36% | +0.30 | 2.24 | 4 | 42 | 40% | +0.41 | 3.00 |
| limit at Fib 0.382 · below Fib 0.786 · setup's own R target | 108 | 37% | +0.41 | 2.21 | 3 | 24 | 42% | +0.64 | 3.00 |
| limit at Fib 0.382 · below liquidity past Fib 0.618 · setup's own R target | 109 | 36% | +0.35 | 1.91 | 2 | 24 | 29% | +0.11 | 3.00 |
| market at signal · below Fib 0.786 · Fib extension 1.618 | 124 | 48% | +0.23 | 1.78 | 3 | 25 | 68% | +0.92 | 2.11 |
| limit at Fib 0.382 · setup's own stop · setup's own R target | 108 | 33% | +0.28 | 1.54 | 2 | 24 | 50% | +0.92 | 3.00 |
| limit at Fib 0.382 · below Fib 0.786 · Fib extension 1.618 | 108 | 37% | +0.23 | 1.38 | 2 | 24 | 46% | +0.70 | 2.84 |
| limit at Fib 0.382 · below liquidity past Fib 0.618 · Fib extension 1.618 | 109 | 35% | +0.23 | 1.31 | 2 | 24 | 33% | +0.12 | 3.42 |
| limit at Fib 0.382 · below Fib 0.786 · next untaken liquidity | 73 | 40% | +0.20 | 1.03 | 2 | 19 | 53% | +0.98 | 2.71 |
| market at signal · below liquidity past Fib 0.618 · Fib extension 1.618 | 128 | 41% | +0.13 | 1.01 | 3 | 25 | 52% | +0.38 | 2.48 |
| market at signal · below Fib 0.786 · next untaken liquidity | 53 | 43% | +0.22 | 1.00 | 2 | 9 | 56% | +1.54 | 2.82 |
| limit at Fib 0.5 · setup's own stop · next untaken liquidity | 43 | 40% | +0.25 | 0.97 | 3 | 11 | 55% | +2.03 | 3.87 |
| market at signal · setup's own stop · next untaken liquidity | 46 | 43% | +0.22 | 0.97 | 3 | 9 | 78% | +1.77 | 2.07 |
| limit at Fib 0.5 · setup's own stop · setup's own R target | 73 | 32% | +0.19 | 0.90 | 2 | 16 | 44% | +0.69 | 3.00 |
| limit at Fib 0.5 · below Fib 0.786 · next untaken liquidity | 74 | 30% | +0.13 | 0.59 | 2 | 16 | 38% | +0.94 | 3.35 |
| limit at Fib 0.5 · setup's own stop · Fib extension 1.618 | 69 | 36% | +0.11 | 0.54 | 2 | 16 | 44% | +0.71 | 3.80 |
| limit at Fib 0.5 · below Fib 0.786 · Fib extension 1.618 | 77 | 26% | +0.12 | 0.53 | 2 | 16 | 38% | +0.91 | 4.12 |
| limit at Fib 0.5 · below Fib 0.786 · setup's own R target | 77 | 30% | +0.11 | 0.52 | 2 | 16 | 38% | +0.45 | 3.00 |
| limit at Fib 0.382 · setup's own stop · next untaken liquidity | 56 | 39% | +0.08 | 0.42 | 3 | 11 | 64% | +1.68 | 2.85 |
| limit at Fib 0.382 · setup's own stop · Fib extension 1.618 | 93 | 39% | +0.04 | 0.26 | 3 | 20 | 50% | +0.62 | 3.28 |
| market at signal · below liquidity past Fib 0.618 · next untaken liquidity | 58 | 38% | +0.05 | 0.26 | 2 | 13 | 31% | +0.33 | 3.15 |
| limit at Fib 0.382 · below liquidity past Fib 0.618 · next untaken liquidity | 86 | 34% | +0.04 | 0.24 | 2 | 20 | 45% | +0.52 | 3.08 |
| limit at Fib 0.5 · below liquidity past Fib 0.618 · Fib extension 1.618 | 77 | 23% | +0.05 | 0.20 | 2 | 16 | 19% | +0.09 | 5.46 |
| market at signal · setup's own stop · Fib extension 1.618 | 99 | 37% | -0.00 | -0.03 | 2 | 18 | 61% | +0.65 | 2.07 |
| limit at Fib 0.5 · below liquidity past Fib 0.618 · setup's own R target | 77 | 27% | -0.01 | -0.07 | 2 | 16 | 31% | +0.15 | 3.00 |
| market at signal · below Fib 0.786 · Fib extension 1.272 | 37 | 41% | -0.02 | -0.10 | 2 | 7 | 57% | +0.83 | 2.51 |
| market at signal · below liquidity past Fib 0.618 · Fib extension 1.272 | 52 | 38% | -0.05 | -0.27 | 2 | 13 | 46% | +0.05 | 2.55 |
| limit at Fib 0.5 · below liquidity past Fib 0.618 · next untaken liquidity | 71 | 24% | -0.07 | -0.29 | 2 | 16 | 25% | +0.52 | 4.52 |
| limit at Fib 0.5 · setup's own stop · Fib extension 1.272 | 47 | 34% | -0.08 | -0.40 | 2 | 13 | 46% | +0.46 | 3.28 |
| limit at Fib 0.382 · below Fib 0.786 · Fib extension 1.272 | 108 | 38% | -0.05 | -0.42 | 2 | 24 | 50% | +0.39 | 1.90 |
| limit at Fib 0.382 · below liquidity past Fib 0.618 · Fib extension 1.272 | 102 | 33% | -0.09 | -0.63 | 2 | 22 | 36% | -0.02 | 2.38 |
| limit at Fib 0.5 · below Fib 0.786 · Fib extension 1.272 | 77 | 26% | -0.15 | -0.83 | 1 | 16 | 38% | +0.44 | 2.87 |
| market at signal · setup's own stop · Fib extension 1.272 | 40 | 30% | -0.23 | -1.09 | 1 | 7 | 71% | +0.79 | 1.74 |
| limit at Fib 0.5 · below liquidity past Fib 0.618 · Fib extension 1.272 | 77 | 23% | -0.22 | -1.17 | 1 | 16 | 25% | +0.12 | 3.80 |
| limit at Fib 0.382 · setup's own stop · Fib extension 1.272 | 50 | 26% | -0.37 | -2.14 | 0 | 11 | 64% | +0.72 | 3.16 |

