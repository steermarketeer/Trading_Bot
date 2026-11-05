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
| step 1b + confirmed shorts (steps 2-3) | 2022 - Oct 2025 (clean test) | 343 | 1.72 | 42% | +0.30 | 1.58 | 13.48x | -45% |
| step 1b + confirmed shorts (steps 2-3) | holdout | 79 | 1.63 | 48% | +0.45 | 1.99 | 2.27x | -26% |

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
| 2022 - Oct 2025 | 47 | 19% | -0.32 | 0.58 | 3.32 |
| holdout | 8 | 38% | +0.06 | 1.10 | 3.02 |

