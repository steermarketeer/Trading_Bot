# Meta-labeling: the main rules pick the trade, the model can only veto it

v3.1 trades with fixed targets (2:1 breakouts, 3:1 bounces); scored out-of-sample: 2023-2025 walk-forward (258 trades) and the holdout (106 trades). **win % = profit after all costs.** Veto rule fixed in advance: remove trades the model rates below the worst 25% of its training trades.

## Win % with and without the veto (25% rule)

| period | rule | trades | per week | win % | avg R | profit factor | account | worst drop |
|---|---|---|---|---|---|---|---|---|
| research 2023-2025 | no veto (v3.1) | 258 | 1.74 | 46% | +0.38 | 1.67 | 10.72x | -39% |
| research 2023-2025 | veto: per setup, main rules + liquidity | 225 | 1.52 | 44% | +0.31 | 1.53 | 4.74x | -34% |
| research 2023-2025 | veto: per setup, + indicators | 240 | 1.62 | 47% | +0.40 | 1.71 | 10.36x | -30% |
| research 2023-2025 | veto: pooled, main rules + liquidity | 195 | 1.32 | 45% | +0.33 | 1.58 | 5.42x | -29% |
| research 2023-2025 | veto: pooled, + indicators | 229 | 1.55 | 47% | +0.41 | 1.73 | 10.24x | -29% |
| holdout | no veto (v3.1) | 106 | 2.18 | 52% | +0.58 | 2.14 | 4.77x | -24% |
| holdout | veto: per setup, main rules + liquidity | 85 | 1.75 | 56% | +0.71 | 2.54 | 4.32x | -22% |
| holdout | veto: per setup, + indicators | 93 | 1.91 | 56% | +0.68 | 2.46 | 5.03x | -22% |
| holdout | veto: pooled, main rules + liquidity | 84 | 1.73 | 54% | +0.60 | 2.23 | 3.84x | -22% |
| holdout | veto: pooled, + indicators | 76 | 1.56 | 54% | +0.61 | 2.26 | 3.85x | -21% |

## Per setup (model trained only on that setup's own trades)

| period | setup | trades | win % no veto | avg R no veto | kept (main rules) | win % kept | avg R kept | win % vetoed | kept (+ indicators) | win % kept | win % vetoed |
|---|---|---|---|---|---|---|---|---|---|---|---|
| research | A+ breakout | 84 | 61% | +0.71 | 65 | 55% | +0.55 | 79% | 76 | 62% | 50% |
| research | breakout | 85 | 45% | +0.22 | 79 | 43% | +0.17 | 67% | 82 | 45% | 33% |
| research | 1D bounce | 89 | 34% | +0.21 | 81 | 35% | +0.26 | 25% | 82 | 34% | 29% |
| holdout | A+ breakout | 41 | 61% | +0.76 | 34 | 62% | +0.78 | 57% | 40 | 62% | 0% |
| holdout | breakout | 21 | 48% | +0.33 | 16 | 62% | +0.78 | 0% | 20 | 50% | 0% |
| holdout | 1D bounce | 44 | 45% | +0.55 | 35 | 49% | +0.62 | 33% | 33 | 52% | 27% |

## How strict should the veto be? (reference only - 25% was fixed in advance)

| model | period | trades (veto 10%) | win % | avg R | trades (25%) | win % | avg R | trades (40%) | win % | avg R |
|---|---|---|---|---|---|---|---|---|---|---|
| per setup, main rules + liquidity | research | 247 | 45% | +0.35 | 225 | 44% | +0.31 | 182 | 45% | +0.34 |
| per setup, main rules + liquidity | holdout | 100 | 53% | +0.61 | 85 | 56% | +0.71 | 76 | 55% | +0.69 |
| per setup, + indicators | research | 248 | 47% | +0.40 | 240 | 47% | +0.40 | 219 | 47% | +0.41 |
| per setup, + indicators | holdout | 98 | 55% | +0.68 | 93 | 56% | +0.68 | 81 | 56% | +0.68 |
| pooled, main rules + liquidity | research | 237 | 46% | +0.39 | 195 | 45% | +0.33 | 166 | 46% | +0.35 |
| pooled, main rules + liquidity | holdout | 95 | 53% | +0.58 | 84 | 54% | +0.60 | 72 | 53% | +0.55 |
| pooled, + indicators | research | 248 | 47% | +0.40 | 229 | 47% | +0.41 | 212 | 47% | +0.40 |
| pooled, + indicators | holdout | 96 | 55% | +0.68 | 76 | 54% | +0.61 | 64 | 56% | +0.64 |

