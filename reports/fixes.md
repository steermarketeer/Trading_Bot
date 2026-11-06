# Fixing the remaining failures: breaks / rejections, failures, trendlines

Start: v3.1 ETH trades (one position per move) with the two journal filters. **win % = profit after costs.** The combination is chosen on 2022 - Oct 2025 only; the holdout (Nov 2025 on) is the honest check. Definitions: docs/trading_definitions.md.

## Start vs chosen

|  | rules | trades 2022-25 | win % | avg R | trades holdout | win % holdout | avg R holdout |
|---|---|---|---|---|---|---|---|
| start (v3.1 + journal filters) | enter at signal + fixed target | 129 | 57% | +0.71 | 33 | 58% | +0.68 |
| chosen on 2022 - 2025 | enter at signal + fixed target + bounce stop below Fib 0.786 | 129 | 59% | +0.79 | 33 | 64% | +1.02 |

## Account (A+ 4%, others 2%, max 5x)

|  | period | trades | per week | win % | avg R | profit factor | account | worst drop |
|---|---|---|---|---|---|---|---|---|
| start | 2022 - Oct 2025 | 129 | 0.65 | 57% | +0.71 | 2.55 | 13.89x | -16% |
| start | holdout | 33 | 0.68 | 58% | +0.68 | 2.53 | 1.87x | -13% |
| chosen | 2022 - Oct 2025 | 129 | 0.65 | 59% | +0.79 | 2.82 | 16.89x | -16% |
| chosen | holdout | 33 | 0.68 | 64% | +1.02 | 3.71 | 2.32x | -13% |

## Every combination (sorted by the 2022 - 2025 t-score)

| rules | trades 2022-25 | win % | avg R | t-score | good years /4 | holdout trades | holdout win % | holdout avg R |
|---|---|---|---|---|---|---|---|---|
| enter at signal + fixed target + bounce stop below Fib 0.786 | 129 | 59% | +0.79 | 5.53 | 4 | 33 | 64% | +1.02 |
| enter at signal + fixed target + Fib extension target + bounce stop below 0.786 | 129 | 57% | +0.73 | 5.00 | 4 | 33 | 61% | +0.86 |
| enter at signal + fixed target + strong breaking candle + bounce stop below Fib 0.786 | 100 | 59% | +0.83 | 4.98 | 4 | 27 | 70% | +1.28 |
| enter at signal + fixed target | 129 | 57% | +0.71 | 4.96 | 4 | 33 | 58% | +0.68 |
| enter at signal + fixed target + strong breaking candle + Fib extension target + bounce stop below 0.786 | 100 | 58% | +0.77 | 4.64 | 4 | 27 | 67% | +1.08 |
| enter at signal + fixed target + Fib extension target at liquidity | 129 | 55% | +0.66 | 4.53 | 3 | 33 | 55% | +0.57 |
| enter at signal + fixed target + no trendline in the way + bounce stop below Fib 0.786 | 76 | 61% | +0.80 | 4.39 | 4 | 17 | 59% | +0.74 |
| enter at signal + fixed target + strong breaking candle | 100 | 56% | +0.72 | 4.34 | 4 | 27 | 63% | +0.85 |
| enter at signal + failure exit (any) | 129 | 51% | +0.33 | 4.23 | 4 | 33 | 42% | +0.20 |
| enter at signal + failure exit (any) + no trendline in the way | 76 | 54% | +0.46 | 4.15 | 4 | 17 | 47% | +0.46 |
| enter at signal + fixed target + no trendline in the way | 76 | 59% | +0.75 | 4.14 | 4 | 17 | 53% | +0.51 |
| enter at signal + failure exit (in profit) | 129 | 67% | +0.37 | 4.10 | 4 | 33 | 67% | +0.33 |
| enter at signal + fixed target + strong breaking candle + Fib extension target at liquidity | 100 | 55% | +0.68 | 4.10 | 4 | 27 | 59% | +0.72 |
| enter at signal + failure exit (in profit) + no trendline in the way | 76 | 68% | +0.49 | 4.07 | 4 | 17 | 71% | +0.52 |
| enter at signal + failure exit (in profit) + bounce stop below Fib 0.786 | 129 | 67% | +0.36 | 4.05 | 4 | 33 | 70% | +0.48 |
| enter at signal + failure exit (in profit) + no trendline in the way + bounce stop below Fib 0.786 | 76 | 68% | +0.51 | 4.04 | 4 | 17 | 76% | +0.67 |
| enter at signal + failure exit (any) + strong breaking candle | 100 | 51% | +0.32 | 3.89 | 4 | 27 | 44% | +0.21 |
| enter at signal + fixed target + no trendline in the way + Fib extension target + bounce stop below 0.786 | 76 | 58% | +0.74 | 3.85 | 4 | 17 | 53% | +0.53 |
| enter at signal + failure exit (in profit) + Fib extension target at liquidity | 129 | 66% | +0.35 | 3.84 | 4 | 33 | 64% | +0.24 |
| enter at signal + failure exit (in profit) + Fib extension target + bounce stop below 0.786 | 129 | 67% | +0.35 | 3.78 | 4 | 33 | 67% | +0.38 |
| enter at signal + failure exit (in profit) + strong breaking candle + Fib extension target at liquidity | 100 | 71% | +0.37 | 3.76 | 4 | 27 | 70% | +0.27 |
| enter at signal + failure exit (in profit) + strong breaking candle | 100 | 71% | +0.37 | 3.74 | 4 | 27 | 74% | +0.39 |
| enter at signal + failure exit (in profit) + no trendline in the way + Fib extension target at liquidity | 76 | 67% | +0.47 | 3.70 | 4 | 17 | 65% | +0.34 |
| enter at signal + failure exit (in profit) + no trendline in the way + Fib extension target + bounce stop below 0.786 | 76 | 67% | +0.48 | 3.69 | 4 | 17 | 71% | +0.48 |
| enter at signal + failure exit (in profit) + strong breaking candle + bounce stop below Fib 0.786 | 100 | 72% | +0.37 | 3.68 | 4 | 27 | 78% | +0.56 |
| enter at signal + failure exit (in profit) + strong breaking candle + Fib extension target + bounce stop below 0.786 | 100 | 72% | +0.37 | 3.68 | 4 | 27 | 74% | +0.45 |
| enter at signal + fixed target + no trendline in the way + Fib extension target at liquidity | 76 | 57% | +0.68 | 3.60 | 3 | 17 | 47% | +0.30 |
| enter at signal + failure exit (any) + no trendline in the way + strong breaking candle | 56 | 52% | +0.43 | 3.55 | 4 | 13 | 54% | +0.50 |
| enter at signal + fixed target + no trendline in the way + strong breaking candle + bounce stop below Fib 0.786 | 56 | 59% | +0.77 | 3.55 | 4 | 13 | 69% | +1.09 |
| retest entry + fixed target | 44 | 61% | +0.82 | 3.43 | 4 | 13 | 54% | +0.52 |
| enter at signal + failure exit (in profit) + no trendline in the way + strong breaking candle | 56 | 71% | +0.46 | 3.42 | 4 | 13 | 85% | +0.65 |
| enter at signal + failure exit (in profit) + no trendline in the way + strong breaking candle + Fib extension target at liquidity | 56 | 71% | +0.46 | 3.41 | 4 | 13 | 77% | +0.41 |
| enter at signal + failure exit (in profit) + no trendline in the way + strong breaking candle + bounce stop below Fib 0.786 | 56 | 71% | +0.48 | 3.38 | 4 | 13 | 92% | +0.84 |
| enter at signal + failure exit (in profit) + no trendline in the way + strong breaking candle + Fib extension target + bounce stop below 0.786 | 56 | 71% | +0.48 | 3.37 | 4 | 13 | 85% | +0.60 |
| enter at signal + fixed target + no trendline in the way + strong breaking candle + Fib extension target + bounce stop below 0.786 | 56 | 57% | +0.73 | 3.28 | 4 | 13 | 62% | +0.81 |
| enter at signal + fixed target + no trendline in the way + strong breaking candle | 56 | 57% | +0.71 | 3.27 | 4 | 13 | 62% | +0.79 |
| retest entry + fixed target + strong breaking candle | 33 | 61% | +0.88 | 3.03 | 4 | 10 | 60% | +0.70 |
| enter at signal + fixed target + no trendline in the way + strong breaking candle + Fib extension target at liquidity | 56 | 55% | +0.66 | 2.98 | 4 | 13 | 54% | +0.51 |
| retest entry + failure exit (in profit) + no trendline in the way | 30 | 73% | +0.43 | 2.90 | 4 | 7 | 43% | -0.02 |
| retest entry + failure exit (in profit) | 44 | 73% | +0.34 | 2.74 | 4 | 13 | 62% | +0.22 |
| retest entry + failure exit (in profit) + strong breaking candle | 33 | 76% | +0.33 | 2.62 | 4 | 10 | 70% | +0.38 |
| retest entry + failure exit (in profit) + no trendline in the way + strong breaking candle | 23 | 74% | +0.41 | 2.55 | 3 | 5 | 60% | +0.23 |
| retest entry + fixed target + no trendline in the way | 30 | 60% | +0.66 | 2.45 | 4 | 7 | 29% | -0.38 |
| retest entry + fixed target + no trendline in the way + strong breaking candle | 23 | 57% | +0.58 | 1.81 | 3 | 5 | 40% | -0.10 |
| retest entry + failure exit (any) + no trendline in the way | 30 | 47% | +0.10 | 0.90 | 2 | 7 | 43% | +0.23 |
| retest entry + failure exit (any) + no trendline in the way + strong breaking candle | 23 | 43% | +0.07 | 0.58 | 1 | 5 | 60% | +0.44 |
| retest entry + failure exit (any) + strong breaking candle | 33 | 45% | +0.04 | 0.52 | 1 | 10 | 60% | +0.37 |
| retest entry + failure exit (any) | 44 | 45% | +0.05 | 0.51 | 2 | 13 | 54% | +0.25 |

## Fibonacci confluence (same trades in every row)

| Fibonacci | exit | filter | trades 2022-25 | win % | avg R | trades holdout | win % holdout | avg R holdout |
|---|---|---|---|---|---|---|---|---|
| no Fibonacci | fixed / Fib target |  | 129 | 57% | +0.71 | 33 | 58% | +0.68 |
| no Fibonacci | fixed / Fib target | strong breaking candle | 100 | 56% | +0.72 | 27 | 63% | +0.85 |
| no Fibonacci | + failure exit |  | 129 | 67% | +0.37 | 33 | 67% | +0.33 |
| no Fibonacci | + failure exit | strong breaking candle | 100 | 71% | +0.37 | 27 | 74% | +0.39 |
| target at a Fib extension that coincides with liquidity | fixed / Fib target |  | 129 | 55% | +0.66 | 33 | 55% | +0.57 |
| target at a Fib extension that coincides with liquidity | fixed / Fib target | strong breaking candle | 100 | 55% | +0.68 | 27 | 59% | +0.72 |
| target at a Fib extension that coincides with liquidity | + failure exit |  | 129 | 66% | +0.35 | 33 | 64% | +0.24 |
| target at a Fib extension that coincides with liquidity | + failure exit | strong breaking candle | 100 | 71% | +0.37 | 27 | 70% | +0.27 |
| bounces: stop below Fib 0.786 | fixed / Fib target |  | 129 | 59% | +0.79 | 33 | 64% | +1.02 |
| bounces: stop below Fib 0.786 | fixed / Fib target | strong breaking candle | 100 | 59% | +0.83 | 27 | 70% | +1.28 |
| bounces: stop below Fib 0.786 | + failure exit |  | 129 | 67% | +0.36 | 33 | 70% | +0.48 |
| bounces: stop below Fib 0.786 | + failure exit | strong breaking candle | 100 | 72% | +0.37 | 27 | 78% | +0.56 |
| both | fixed / Fib target |  | 129 | 57% | +0.73 | 33 | 61% | +0.86 |
| both | fixed / Fib target | strong breaking candle | 100 | 58% | +0.77 | 27 | 67% | +1.08 |
| both | + failure exit |  | 129 | 67% | +0.35 | 33 | 67% | +0.38 |
| both | + failure exit | strong breaking candle | 100 | 72% | +0.37 | 27 | 74% | +0.45 |

