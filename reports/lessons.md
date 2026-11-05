# Your journal lessons as rules: tested on every v3.1 ETH trade

One position per move. **win % = profit after all costs.** The lessons came from holdout trades (h039, h030, h029), so **2022 - Oct 2025 is the clean test**; the holdout is shown but is no longer untouched.

## Results

| rule | period | trades | per week | win % | avg R | profit factor | account | worst drop |
|---|---|---|---|---|---|---|---|---|
| v3.1 now (one position per move) | 2022 - Oct 2025 (clean test) | 296 | 1.48 | 45% | +0.45 | 1.77 | 25.13x | -36% |
| v3.1 now (one position per move) | holdout (lessons came from here) | 71 | 1.46 | 49% | +0.56 | 2.04 | 2.49x | -23% |
| L1 15m failure exit | 2022 - Oct 2025 (clean test) | 296 | 1.48 | 41% | +0.17 | 1.94 | 4.64x | -17% |
| L1 15m failure exit | holdout (lessons came from here) | 71 | 1.46 | 41% | +0.16 | 1.77 | 1.46x | -15% |
| L1b 15m double top in the first 24h, before +1R | 2022 - Oct 2025 (clean test) | 296 | 1.48 | 43% | +0.35 | 1.72 | 13.22x | -37% |
| L1b 15m double top in the first 24h, before +1R | holdout (lessons came from here) | 71 | 1.46 | 39% | +0.29 | 1.60 | 1.70x | -25% |
| L1b + L4 | 2022 - Oct 2025 (clean test) | 282 | 1.41 | 44% | +0.38 | 1.80 | 14.31x | -30% |
| L1b + L4 | holdout (lessons came from here) | 65 | 1.34 | 40% | +0.35 | 1.75 | 1.73x | -23% |
| L2 skip breakouts under daily EMA200 with a ceiling before target | 2022 - Oct 2025 (clean test) | 258 | 1.29 | 43% | +0.43 | 1.73 | 11.38x | -37% |
| L2 skip breakouts under daily EMA200 with a ceiling before target | holdout (lessons came from here) | 53 | 1.09 | 53% | +0.72 | 2.50 | 2.38x | -14% |
| L3 skip breakouts against falling 4h highs | 2022 - Oct 2025 (clean test) | 273 | 1.36 | 44% | +0.46 | 1.78 | 18.88x | -37% |
| L3 skip breakouts against falling 4h highs | holdout (lessons came from here) | 70 | 1.44 | 50% | +0.58 | 2.11 | 2.55x | -23% |
| L4 skip the second try at a failed level | 2022 - Oct 2025 (clean test) | 282 | 1.41 | 45% | +0.47 | 1.83 | 25.93x | -30% |
| L4 skip the second try at a failed level | holdout (lessons came from here) | 65 | 1.34 | 51% | +0.60 | 2.15 | 2.42x | -21% |
| L1 + L2 + L3 + L4 | 2022 - Oct 2025 (clean test) | 236 | 1.18 | 41% | +0.15 | 1.94 | 2.63x | -14% |
| L1 + L2 + L3 + L4 | holdout (lessons came from here) | 48 | 0.99 | 44% | +0.24 | 3.40 | 1.48x | -2% |

## L1 in detail: trades the 15m failure exit closed early

| period | trades exited early | share of trades | would have lost anyway | would have won | R gained (+) / lost (−) in total |
|---|---|---|---|---|---|
| L1 (first version), 2022 - Oct 2025 | 246 | 83% | 152 | 94 | -82.50 |
| L1 (first version), holdout | 57 | 80% | 31 | 26 | -28.20 |
| L1b (first 24h, true double top), 2022 - Oct 2025 | 65 | 22% | 40 | 25 | -29.76 |
| L1b (first 24h, true double top), holdout | 18 | 25% | 8 | 10 | -18.51 |

## L1F: the opposite trade after a 15m failure (to the liquidity on the other side)

| period | flip trades | win % | avg R (own risk) | profit factor |
|---|---|---|---|---|
| 2022 - Oct 2025 | 23 | 52% | +0.20 | 1.38 |
| holdout | 6 | 17% | -0.72 | 0.22 |

## Filters: win % of the trades each rule removes vs keeps

| rule | period | trades removed | win % of removed | win % of kept |
|---|---|---|---|---|
| L2 under daily EMA200 + ceiling | 2022 - Oct 2025 | 38 | 55% | 43% |
| L3 falling 4h highs | 2022 - Oct 2025 | 23 | 48% | 44% |
| L4 second try | 2022 - Oct 2025 | 14 | 29% | 45% |
| L2 under daily EMA200 + ceiling | holdout | 18 | 39% | 53% |
| L3 falling 4h highs | holdout | 1 | 0% | 50% |
| L4 second try | holdout | 6 | 33% | 51% |

