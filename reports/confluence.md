# Confluence: all the studied concepts voting on the bot's own trades

162 ETH trades of the research-chosen version (v3.1 + journal filters + 0.786 bounce stop). Each concept votes +1 (for) or -1 (against) at the entry; the directions come from the studies, not from these trades, except that V10 was prompted by one of them (27 Mar 2023), V6 comes from a review of holdout trades and V8 is post hoc. V3 is compared within breakouts only. **win % = profit after costs.** Small samples: this shows the direction, not proof.

## Each vote

| vote | period | trades with the vote | win % | avg R | trades without | win % | avg R |
|---|---|---|---|---|---|---|---|
| V1 RSI first push | 2022 - Oct 2025 | 21 | 33% | -0.05 | 108 | 61% | +1.06 |
| V1 RSI first push | holdout | 6 | 67% | +0.94 | 27 | 63% | +1.20 |
| V2 Bollinger strength | 2022 - Oct 2025 | 74 | 59% | +0.97 | 55 | 53% | +0.76 |
| V2 Bollinger strength | holdout | 16 | 56% | +0.78 | 17 | 71% | +1.51 |
| V3 breakout volume 2x | 2022 - Oct 2025 | 68 | 63% | +0.78 | 10 | 50% | +0.44 |
| V3 breakout volume 2x | holdout | 19 | 63% | +0.83 | 3 | 33% | -0.17 |
| V4 strong candle with the daily trend | 2022 - Oct 2025 | 16 | 69% | +0.87 | 113 | 55% | +0.88 |
| V4 strong candle with the daily trend | holdout | 1 | 100% | +0.11 | 32 | 62% | +1.19 |
| V5 liquidity within 1 ATR ahead | 2022 - Oct 2025 | 2 | 50% | -0.07 | 127 | 57% | +0.89 |
| V5 liquidity within 1 ATR ahead | holdout | 1 | 0% | -1.21 | 32 | 66% | +1.23 |
| V6 ceiling before the target | 2022 - Oct 2025 | 107 | 54% | +0.86 | 22 | 68% | +0.96 |
| V6 ceiling before the target | holdout | 31 | 61% | +1.10 | 2 | 100% | +1.94 |
| V7 trendline in the way | 2022 - Oct 2025 | 53 | 55% | +0.99 | 76 | 58% | +0.80 |
| V7 trendline in the way | holdout | 16 | 69% | +1.51 | 17 | 59% | +0.82 |
| V8 weekly has no room | 2022 - Oct 2025 | 20 | 60% | +1.14 | 109 | 56% | +0.83 |
| V8 weekly has no room | holdout | 1 | 0% | -1.02 | 32 | 66% | +1.22 |
| V9 three failures against | 2022 - Oct 2025 | 8 | 75% | +1.71 | 121 | 55% | +0.83 |
| V9 three failures against | holdout | 4 | 75% | +1.07 | 29 | 62% | +1.17 |
| V10 daily pause against | 2022 - Oct 2025 | 11 | 36% | -0.00 | 118 | 58% | +0.96 |
| V10 daily pause against | holdout | 5 | 100% | +1.94 | 28 | 57% | +1.01 |

## By total score, per setup family (bounces score lower by construction: V3 is breakouts only and V6 fires on almost every 3R bounce, so the families are shown apart)

| setup | score | period | trades | win % | avg R | profit factor |
|---|---|---|---|---|---|---|
| breakouts | score <= -2 | 2022 - Oct 2025 | 5 | 40% | +0.12 | 1.18 |
| breakouts | score <= -2 | holdout | 3 | 67% | +0.89 | 3.19 |
| breakouts | score -1 | 2022 - Oct 2025 | 14 | 64% | +0.84 | 3.10 |
| breakouts | score -1 | holdout | 5 | 80% | +1.31 | 6.40 |
| breakouts | score 0 | 2022 - Oct 2025 | 21 | 52% | +0.50 | 2.04 |
| breakouts | score 0 | holdout | 9 | 44% | +0.26 | 1.43 |
| breakouts | score +1 | 2022 - Oct 2025 | 24 | 75% | +1.11 | 4.99 |
| breakouts | score +1 | holdout | 4 | 50% | +0.42 | 1.77 |
| breakouts | score >= +2 | 2022 - Oct 2025 | 14 | 57% | +0.59 | 2.28 |
| breakouts | score >= +2 | holdout | 1 | 100% | +1.98 | inf |
| 1D bounces | score <= -2 | 2022 - Oct 2025 | 13 | 69% | +2.26 | 8.37 |
| 1D bounces | score <= -2 | holdout | 3 | 100% | +3.49 | inf |
| 1D bounces | score -1 | 2022 - Oct 2025 | 20 | 30% | +0.34 | 1.46 |
| 1D bounces | score -1 | holdout | 4 | 75% | +2.84 | 12.20 |
| 1D bounces | score 0 | 2022 - Oct 2025 | 13 | 46% | +0.97 | 2.75 |
| 1D bounces | score 0 | holdout | 3 | 33% | +0.31 | 1.66 |
| 1D bounces | score +1 | 2022 - Oct 2025 | 5 | 80% | +1.36 | 7.95 |
| 1D bounces | score +1 | holdout | 1 | 100% | +0.11 | inf |
| 1D bounces | score >= +2 | 2022 - Oct 2025 | 0 | - |  |  |
| 1D bounces | score >= +2 | holdout | 0 | - |  |  |

## Using the score as a filter, per setup family

| setup | rule | period | trades | win % | avg R | account | worst drop |
|---|---|---|---|---|---|---|---|
| breakouts | all trades | 2022 - Oct 2025 | 78 | 62% | +0.74 | 7.96x | -10% |
| breakouts | all trades | holdout | 22 | 59% | +0.69 | 1.67x | -13% |
| breakouts | skip score <= -1 | 2022 - Oct 2025 | 59 | 63% | +0.77 | 5.17x | -9% |
| breakouts | skip score <= -1 | holdout | 14 | 50% | +0.43 | 1.28x | -13% |
| breakouts | skip score <= -2 | 2022 - Oct 2025 | 73 | 63% | +0.78 | 7.77x | -10% |
| breakouts | skip score <= -2 | holdout | 19 | 58% | +0.66 | 1.56x | -13% |
| 1D bounces | all trades | 2022 - Oct 2025 | 51 | 49% | +1.09 | 2.59x | -16% |
| 1D bounces | all trades | holdout | 11 | 73% | +2.08 | 1.52x | -2% |
| 1D bounces | skip score <= -1 | 2022 - Oct 2025 | 18 | 56% | +1.08 | 1.44x | -6% |
| 1D bounces | skip score <= -1 | holdout | 4 | 50% | +0.26 | 1.02x | -3% |
| 1D bounces | skip score <= -2 | 2022 - Oct 2025 | 38 | 42% | +0.69 | 1.58x | -10% |
| 1D bounces | skip score <= -2 | holdout | 8 | 62% | +1.55 | 1.26x | -3% |

Audit: round 22 (setup-family split, V3 within breakouts, V7 with each trade's own target; no vote bug).
