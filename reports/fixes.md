# Fixing the remaining failures: breaks / rejections, failures, trendlines

Start: v3.1 ETH trades (one position per move) with the two journal filters. **win % = profit after costs.** The combination is chosen on 2022 - Oct 2025 only; the holdout (Nov 2025 on) is the honest check. Definitions: docs/trading_definitions.md.

## Start vs chosen

|  | rules | trades 2022-25 | win % | avg R | trades holdout | win % holdout | avg R holdout |
|---|---|---|---|---|---|---|---|
| start (v3.1 + journal filters) | enter at signal + fixed target | 129 | 57% | +0.71 | 33 | 58% | +0.68 |
| chosen on 2022 - 2025 | enter at signal + fixed target | 129 | 57% | +0.71 | 33 | 58% | +0.68 |

## Account (A+ 4%, others 2%, max 5x)

|  | period | trades | per week | win % | avg R | profit factor | account | worst drop |
|---|---|---|---|---|---|---|---|---|
| start | 2022 - Oct 2025 | 129 | 0.65 | 57% | +0.71 | 2.55 | 13.89x | -16% |
| start | holdout | 33 | 0.68 | 58% | +0.68 | 2.53 | 1.87x | -13% |
| chosen | 2022 - Oct 2025 | 129 | 0.65 | 57% | +0.71 | 2.55 | 13.89x | -16% |
| chosen | holdout | 33 | 0.68 | 58% | +0.68 | 2.53 | 1.87x | -13% |

## Every combination (sorted by the 2022 - 2025 t-score)

| rules | trades 2022-25 | win % | avg R | t-score | good years /4 | holdout trades | holdout win % | holdout avg R |
|---|---|---|---|---|---|---|---|---|
| enter at signal + fixed target | 129 | 57% | +0.71 | 4.96 | 4 | 33 | 58% | +0.68 |
| enter at signal + fixed target + strong breaking candle | 100 | 56% | +0.72 | 4.34 | 4 | 27 | 63% | +0.85 |
| enter at signal + failure exit (any) | 129 | 51% | +0.33 | 4.23 | 4 | 33 | 42% | +0.20 |
| enter at signal + failure exit (any) + no trendline in the way | 76 | 54% | +0.46 | 4.15 | 4 | 17 | 47% | +0.46 |
| enter at signal + fixed target + no trendline in the way | 76 | 59% | +0.75 | 4.14 | 4 | 17 | 53% | +0.51 |
| enter at signal + failure exit (in profit) | 129 | 67% | +0.37 | 4.10 | 4 | 33 | 67% | +0.33 |
| enter at signal + failure exit (in profit) + no trendline in the way | 76 | 68% | +0.49 | 4.07 | 4 | 17 | 71% | +0.52 |
| enter at signal + failure exit (any) + strong breaking candle | 100 | 51% | +0.32 | 3.89 | 4 | 27 | 44% | +0.21 |
| retest entry + fixed target | 45 | 64% | +0.88 | 3.83 | 4 | 12 | 58% | +0.70 |
| enter at signal + failure exit (in profit) + strong breaking candle | 100 | 71% | +0.37 | 3.74 | 4 | 27 | 74% | +0.39 |
| enter at signal + failure exit (any) + no trendline in the way + strong breaking candle | 56 | 52% | +0.43 | 3.55 | 4 | 13 | 54% | +0.50 |
| enter at signal + failure exit (in profit) + no trendline in the way + strong breaking candle | 56 | 71% | +0.46 | 3.42 | 4 | 13 | 85% | +0.65 |
| enter at signal + fixed target + no trendline in the way + strong breaking candle | 56 | 57% | +0.71 | 3.27 | 4 | 13 | 62% | +0.79 |
| retest entry + fixed target + strong breaking candle | 32 | 62% | +0.93 | 3.20 | 4 | 9 | 67% | +0.97 |
| retest entry + failure exit (in profit) | 45 | 73% | +0.35 | 2.84 | 4 | 12 | 67% | +0.39 |
| retest entry + fixed target + no trendline in the way | 30 | 63% | +0.73 | 2.77 | 4 | 6 | 33% | -0.13 |
| retest entry + failure exit (in profit) + no trendline in the way | 30 | 73% | +0.40 | 2.77 | 4 | 6 | 50% | +0.28 |
| retest entry + failure exit (in profit) + strong breaking candle | 32 | 78% | +0.34 | 2.58 | 4 | 9 | 78% | +0.63 |
| retest entry + failure exit (in profit) + no trendline in the way + strong breaking candle | 22 | 77% | +0.42 | 2.52 | 3 | 4 | 75% | +0.75 |
| retest entry + fixed target + no trendline in the way + strong breaking candle | 22 | 59% | +0.65 | 2.00 | 3 | 4 | 50% | +0.35 |
| retest entry + failure exit (any) | 45 | 42% | +0.06 | 0.67 | 2 | 12 | 58% | +0.37 |
| retest entry + failure exit (any) + no trendline in the way | 30 | 40% | +0.07 | 0.67 | 2 | 6 | 50% | +0.48 |
| retest entry + failure exit (any) + no trendline in the way + strong breaking candle | 22 | 41% | +0.06 | 0.46 | 1 | 4 | 75% | +0.88 |
| retest entry + failure exit (any) + strong breaking candle | 32 | 44% | +0.03 | 0.41 | 1 | 9 | 67% | +0.56 |

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

