# Fixing the remaining failures: breaks / rejections, failures, trendlines

Start: v3.1 ETH trades (one position per move) with the two journal filters. **win % = profit after costs.** The combination is chosen on 2022 - Oct 2025 only; the holdout (Nov 2025 on) is the honest check. Definitions: docs/trading_definitions.md.

## Start vs chosen

|  | rules | trades 2022-25 | win % | avg R | trades holdout | win % holdout | avg R holdout |
|---|---|---|---|---|---|---|---|
| start (v3.1 + journal filters) | enter at signal + fixed target | 129 | 57% | +0.82 | 33 | 58% | +0.65 |
| chosen on 2022 - 2025 | enter at signal + fixed target + bounce stop below Fib 0.786 | 129 | 57% | +0.88 | 33 | 64% | +1.15 |

## Account (A+ 4%, others 2%, max 5x)

|  | period | trades | per week | win % | avg R | profit factor | account | worst drop |
|---|---|---|---|---|---|---|---|---|
| start | 2022 - Oct 2025 | 129 | 0.65 | 57% | +0.82 | 2.80 | 16.78x | -16% |
| start | holdout | 33 | 0.68 | 58% | +0.65 | 2.48 | 1.85x | -13% |
| chosen | 2022 - Oct 2025 | 129 | 0.65 | 57% | +0.88 | 2.91 | 19.33x | -16% |
| chosen | holdout | 33 | 0.68 | 64% | +1.15 | 4.05 | 2.47x | -13% |

## Every combination (sorted by the 2022 - 2025 t-score)

| rules | trades 2022-25 | win % | avg R | t-score | good years /4 | holdout trades | holdout win % | holdout avg R |
|---|---|---|---|---|---|---|---|---|
| enter at signal + fixed target + bounce stop below Fib 0.786 | 129 | 57% | +0.88 | 5.15 | 4 | 33 | 64% | +1.15 |
| enter at signal + fixed target | 129 | 57% | +0.82 | 4.97 | 4 | 33 | 58% | +0.65 |
| enter at signal + fixed target + Fib extension target + bounce stop below 0.786 | 129 | 55% | +0.78 | 4.64 | 4 | 33 | 61% | +0.96 |
| enter at signal + fixed target + strong breaking candle + bounce stop below Fib 0.786 | 100 | 56% | +0.94 | 4.58 | 4 | 27 | 70% | +1.44 |
| enter at signal + fixed target + Fib extension target at liquidity | 129 | 55% | +0.74 | 4.54 | 3 | 33 | 55% | +0.54 |
| enter at signal + fixed target + strong breaking candle | 100 | 56% | +0.87 | 4.38 | 4 | 27 | 63% | +0.83 |
| enter at signal + failure exit (any) | 129 | 51% | +0.33 | 4.23 | 4 | 33 | 42% | +0.20 |
| enter at signal + fixed target + strong breaking candle + Fib extension target + bounce stop below 0.786 | 100 | 55% | +0.84 | 4.22 | 4 | 27 | 67% | +1.20 |
| enter at signal + fixed target + no trendline in the way | 76 | 59% | +0.86 | 4.18 | 4 | 17 | 53% | +0.41 |
| enter at signal + failure exit (any) + no trendline in the way | 76 | 54% | +0.46 | 4.15 | 4 | 17 | 47% | +0.46 |
| enter at signal + fixed target + strong breaking candle + Fib extension target at liquidity | 100 | 55% | +0.79 | 4.11 | 4 | 27 | 59% | +0.69 |
| enter at signal + failure exit (in profit) | 129 | 67% | +0.37 | 4.10 | 4 | 33 | 67% | +0.33 |
| enter at signal + failure exit (in profit) + no trendline in the way | 76 | 68% | +0.49 | 4.07 | 4 | 17 | 71% | +0.52 |
| enter at signal + failure exit (in profit) + bounce stop below Fib 0.786 | 129 | 67% | +0.36 | 4.05 | 4 | 33 | 70% | +0.54 |
| enter at signal + failure exit (in profit) + no trendline in the way + bounce stop below Fib 0.786 | 76 | 68% | +0.50 | 4.04 | 4 | 17 | 76% | +0.67 |
| enter at signal + fixed target + no trendline in the way + bounce stop below Fib 0.786 | 76 | 58% | +0.80 | 3.92 | 4 | 17 | 59% | +0.82 |
| enter at signal + failure exit (any) + strong breaking candle | 100 | 51% | +0.32 | 3.89 | 4 | 27 | 44% | +0.21 |
| enter at signal + failure exit (in profit) + Fib extension target at liquidity | 129 | 66% | +0.35 | 3.84 | 4 | 33 | 64% | +0.24 |
| enter at signal + failure exit (in profit) + Fib extension target + bounce stop below 0.786 | 129 | 67% | +0.35 | 3.78 | 4 | 33 | 67% | +0.44 |
| enter at signal + failure exit (in profit) + strong breaking candle + Fib extension target at liquidity | 100 | 71% | +0.37 | 3.76 | 4 | 27 | 70% | +0.27 |
| enter at signal + failure exit (in profit) + strong breaking candle | 100 | 71% | +0.37 | 3.74 | 4 | 27 | 74% | +0.39 |
| enter at signal + failure exit (in profit) + no trendline in the way + Fib extension target at liquidity | 76 | 67% | +0.47 | 3.70 | 4 | 17 | 65% | +0.34 |
| enter at signal + failure exit (in profit) + no trendline in the way + Fib extension target + bounce stop below 0.786 | 76 | 67% | +0.48 | 3.68 | 4 | 17 | 71% | +0.48 |
| enter at signal + failure exit (in profit) + strong breaking candle + bounce stop below Fib 0.786 | 100 | 72% | +0.36 | 3.68 | 4 | 27 | 78% | +0.64 |
| enter at signal + failure exit (in profit) + strong breaking candle + Fib extension target + bounce stop below 0.786 | 100 | 72% | +0.36 | 3.67 | 4 | 27 | 74% | +0.52 |
| enter at signal + fixed target + no trendline in the way + Fib extension target at liquidity | 76 | 57% | +0.76 | 3.67 | 3 | 17 | 47% | +0.20 |
| enter at signal + failure exit (any) + no trendline in the way + strong breaking candle | 56 | 52% | +0.43 | 3.55 | 4 | 13 | 54% | +0.50 |
| enter at signal + fixed target + no trendline in the way + Fib extension target + bounce stop below 0.786 | 76 | 55% | +0.71 | 3.44 | 4 | 17 | 53% | +0.61 |
| enter at signal + failure exit (in profit) + no trendline in the way + strong breaking candle | 56 | 71% | +0.46 | 3.42 | 4 | 13 | 85% | +0.65 |
| enter at signal + failure exit (in profit) + no trendline in the way + strong breaking candle + Fib extension target at liquidity | 56 | 71% | +0.46 | 3.41 | 4 | 13 | 77% | +0.41 |
| enter at signal + failure exit (in profit) + no trendline in the way + strong breaking candle + bounce stop below Fib 0.786 | 56 | 71% | +0.48 | 3.38 | 4 | 13 | 92% | +0.84 |
| enter at signal + failure exit (in profit) + no trendline in the way + strong breaking candle + Fib extension target + bounce stop below 0.786 | 56 | 71% | +0.47 | 3.37 | 4 | 13 | 85% | +0.60 |
| enter at signal + fixed target + no trendline in the way + strong breaking candle | 56 | 57% | +0.85 | 3.37 | 4 | 13 | 62% | +0.65 |
| retest entry + fixed target | 44 | 61% | +0.97 | 3.31 | 4 | 13 | 54% | +0.62 |
| enter at signal + fixed target + no trendline in the way + strong breaking candle + bounce stop below Fib 0.786 | 56 | 55% | +0.78 | 3.08 | 4 | 13 | 69% | +1.19 |
| enter at signal + fixed target + no trendline in the way + strong breaking candle + Fib extension target at liquidity | 56 | 55% | +0.76 | 3.08 | 4 | 13 | 54% | +0.37 |
| retest entry + fixed target + strong breaking candle | 33 | 61% | +1.08 | 2.94 | 4 | 10 | 60% | +0.84 |
| retest entry + failure exit (in profit) + no trendline in the way | 30 | 73% | +0.43 | 2.90 | 4 | 7 | 43% | -0.02 |
| enter at signal + fixed target + no trendline in the way + strong breaking candle + Fib extension target + bounce stop below 0.786 | 56 | 54% | +0.70 | 2.82 | 4 | 13 | 62% | +0.92 |
| retest entry + failure exit (in profit) | 44 | 73% | +0.34 | 2.74 | 4 | 13 | 62% | +0.22 |
| retest entry + failure exit (in profit) + strong breaking candle | 33 | 76% | +0.33 | 2.62 | 4 | 10 | 70% | +0.38 |
| retest entry + failure exit (in profit) + no trendline in the way + strong breaking candle | 23 | 74% | +0.41 | 2.55 | 3 | 5 | 60% | +0.23 |
| retest entry + fixed target + no trendline in the way | 30 | 60% | +0.83 | 2.50 | 4 | 7 | 29% | -0.38 |
| retest entry + fixed target + no trendline in the way + strong breaking candle | 23 | 57% | +0.80 | 1.95 | 3 | 5 | 40% | -0.10 |
| retest entry + failure exit (any) + no trendline in the way | 30 | 47% | +0.10 | 0.90 | 2 | 7 | 43% | +0.23 |
| retest entry + failure exit (any) + no trendline in the way + strong breaking candle | 23 | 43% | +0.07 | 0.58 | 1 | 5 | 60% | +0.44 |
| retest entry + failure exit (any) + strong breaking candle | 33 | 45% | +0.04 | 0.52 | 1 | 10 | 60% | +0.37 |
| retest entry + failure exit (any) | 44 | 45% | +0.05 | 0.51 | 2 | 13 | 54% | +0.25 |

## Fibonacci confluence (same trades in every row)

| Fibonacci | exit | filter | trades 2022-25 | win % | avg R | trades holdout | win % holdout | avg R holdout |
|---|---|---|---|---|---|---|---|---|
| no Fibonacci | fixed / Fib target |  | 129 | 57% | +0.82 | 33 | 58% | +0.65 |
| no Fibonacci | fixed / Fib target | strong breaking candle | 100 | 56% | +0.87 | 27 | 63% | +0.83 |
| no Fibonacci | + failure exit |  | 129 | 67% | +0.37 | 33 | 67% | +0.33 |
| no Fibonacci | + failure exit | strong breaking candle | 100 | 71% | +0.37 | 27 | 74% | +0.39 |
| target at a Fib extension that coincides with liquidity | fixed / Fib target |  | 129 | 55% | +0.74 | 33 | 55% | +0.54 |
| target at a Fib extension that coincides with liquidity | fixed / Fib target | strong breaking candle | 100 | 55% | +0.79 | 27 | 59% | +0.69 |
| target at a Fib extension that coincides with liquidity | + failure exit |  | 129 | 66% | +0.35 | 33 | 64% | +0.24 |
| target at a Fib extension that coincides with liquidity | + failure exit | strong breaking candle | 100 | 71% | +0.37 | 27 | 70% | +0.27 |
| bounces: stop below Fib 0.786 | fixed / Fib target |  | 129 | 57% | +0.88 | 33 | 64% | +1.15 |
| bounces: stop below Fib 0.786 | fixed / Fib target | strong breaking candle | 100 | 56% | +0.94 | 27 | 70% | +1.44 |
| bounces: stop below Fib 0.786 | + failure exit |  | 129 | 67% | +0.36 | 33 | 70% | +0.54 |
| bounces: stop below Fib 0.786 | + failure exit | strong breaking candle | 100 | 72% | +0.36 | 27 | 78% | +0.64 |
| both | fixed / Fib target |  | 129 | 55% | +0.78 | 33 | 61% | +0.96 |
| both | fixed / Fib target | strong breaking candle | 100 | 55% | +0.84 | 27 | 67% | +1.20 |
| both | + failure exit |  | 129 | 67% | +0.35 | 33 | 67% | +0.44 |
| both | + failure exit | strong breaking candle | 100 | 72% | +0.36 | 27 | 74% | +0.52 |

