# Close the long, confirm, then short: tested on every v3.1 ETH trade

One position per move. **win % = profit after all costs.** The idea came from holdout trades, so **2022 - Oct 2025 is the clean test**.

## Results

| strategy | period | trades | per week | win % | avg R | profit factor | account | worst drop |
|---|---|---|---|---|---|---|---|---|
| v3.1 now | 2022 - Oct 2025 (clean test) | 296 | 1.48 | 45% | +0.45 | 1.77 | 25.13x | -36% |
| v3.1 now | holdout | 71 | 1.46 | 49% | +0.56 | 2.04 | 2.49x | -23% |
| step 1: close on a 4h band failure (any trend) | 2022 - Oct 2025 (clean test) | 296 | 1.48 | 45% | +0.31 | 1.96 | 13.85x | -27% |
| step 1: close on a 4h band failure (any trend) | holdout | 71 | 1.46 | 49% | +0.33 | 1.97 | 1.98x | -23% |
| step 1b: close on a band failure only in a bearish trend | 2022 - Oct 2025 (clean test) | 296 | 1.48 | 45% | +0.40 | 1.83 | 19.24x | -36% |
| step 1b: close on a band failure only in a bearish trend | holdout | 71 | 1.46 | 49% | +0.49 | 2.15 | 2.29x | -24% |
| step 1b + confirmed shorts (steps 2-3) | 2022 - Oct 2025 (clean test) | 327 | 1.64 | 43% | +0.32 | 1.63 | 14.33x | -43% |
| step 1b + confirmed shorts (steps 2-3) | holdout | 78 | 1.61 | 47% | +0.45 | 1.97 | 2.24x | -26% |

## Step 1 in detail: longs the band failure would close early

| period | daily trend | closed early | would have lost anyway | would have won | R saved (+) / given up (−) |
|---|---|---|---|---|---|
| 2022 - Oct 2025 | bearish (below daily EMA 200) | 59 | 40 | 19 | -15.10 |
| 2022 - Oct 2025 | bullish | 95 | 58 | 37 | -24.66 |
| holdout | bearish (below daily EMA 200) | 16 | 10 | 6 | -4.39 |
| holdout | bullish | 21 | 10 | 11 | -11.40 |

## Steps 2-3: the confirmed shorts

| period | shorts | win % | avg R | profit factor | avg reward:risk |
|---|---|---|---|---|---|
| 2022 - Oct 2025 | 31 | 16% | -0.44 | 0.46 | 3.15 |
| holdout | 7 | 29% | -0.04 | 0.95 | 2.87 |

