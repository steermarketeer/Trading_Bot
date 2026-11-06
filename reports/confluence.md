# Confluence: all the studied concepts voting on the bot's own trades

162 ETH trades of the research-chosen version (v3.1 + journal filters + 0.786 bounce stop). Each concept votes +1 (for) or -1 (against) at the entry; the directions were fixed from the studies before looking at these trades. **win % = profit after costs.** Small samples: this shows the direction, not proof.

## Each vote

| vote | period | trades with the vote | win % | avg R | trades without | win % | avg R |
|---|---|---|---|---|---|---|---|
| V1 RSI first push | 2022 - Oct 2025 | 21 | 33% | -0.05 | 108 | 64% | +0.96 |
| V1 RSI first push | holdout | 6 | 67% | +0.94 | 27 | 63% | +1.04 |
| V2 Bollinger strength | 2022 - Oct 2025 | 74 | 61% | +0.84 | 55 | 56% | +0.72 |
| V2 Bollinger strength | holdout | 16 | 56% | +0.82 | 17 | 71% | +1.22 |
| V3 breakout volume 2x | 2022 - Oct 2025 | 68 | 63% | +0.78 | 61 | 54% | +0.80 |
| V3 breakout volume 2x | holdout | 19 | 63% | +0.83 | 14 | 64% | +1.29 |
| V4 strong candle with the daily trend | 2022 - Oct 2025 | 16 | 69% | +0.84 | 113 | 58% | +0.78 |
| V4 strong candle with the daily trend | holdout | 1 | 100% | +0.11 | 32 | 62% | +1.05 |
| V5 liquidity within 1 ATR ahead | 2022 - Oct 2025 | 2 | 50% | -0.07 | 127 | 59% | +0.80 |
| V5 liquidity within 1 ATR ahead | holdout | 1 | 0% | -1.21 | 32 | 66% | +1.09 |
| V6 ceiling before the target | 2022 - Oct 2025 | 107 | 57% | +0.76 | 22 | 68% | +0.96 |
| V6 ceiling before the target | holdout | 31 | 61% | +0.97 | 2 | 100% | +1.94 |
| V7 trendline in the way | 2022 - Oct 2025 | 53 | 57% | +0.78 | 76 | 61% | +0.80 |
| V7 trendline in the way | holdout | 16 | 69% | +1.32 | 17 | 59% | +0.74 |
| V8 weekly has no room | 2022 - Oct 2025 | 20 | 60% | +0.79 | 109 | 59% | +0.79 |
| V8 weekly has no room | holdout | 1 | 0% | -1.02 | 32 | 66% | +1.09 |
| V9 three failures against | 2022 - Oct 2025 | 8 | 75% | +1.49 | 121 | 58% | +0.75 |
| V9 three failures against | holdout | 4 | 75% | +1.40 | 29 | 62% | +0.97 |
| V10 daily pause against | 2022 - Oct 2025 | 11 | 36% | -0.00 | 118 | 61% | +0.87 |
| V10 daily pause against | holdout | 5 | 100% | +1.94 | 28 | 57% | +0.86 |

## By total score

| score | period | trades | win % | avg R | profit factor |
|---|---|---|---|---|---|
| score <= -2 | 2022 - Oct 2025 | 18 | 61% | +1.05 | 3.59 |
| score <= -2 | holdout | 6 | 83% | +1.93 | 10.47 |
| score -1 | 2022 - Oct 2025 | 34 | 53% | +0.73 | 2.43 |
| score -1 | holdout | 9 | 78% | +1.62 | 7.53 |
| score 0 | 2022 - Oct 2025 | 34 | 50% | +0.51 | 1.99 |
| score 0 | holdout | 12 | 42% | +0.32 | 1.57 |
| score +1 | 2022 - Oct 2025 | 29 | 76% | +1.14 | 5.31 |
| score +1 | holdout | 5 | 60% | +0.36 | 1.82 |
| score >= +2 | 2022 - Oct 2025 | 14 | 57% | +0.59 | 2.28 |
| score >= +2 | holdout | 1 | 100% | +1.98 | inf |

## Using the score as a filter

| rule | period | trades | win % | avg R | account | worst drop |
|---|---|---|---|---|---|---|
| all trades | 2022 - Oct 2025 | 129 | 59% | +0.79 | 16.89x | -16% |
| all trades | holdout | 33 | 64% | +1.02 | 2.32x | -13% |
| skip score <= -1 | 2022 - Oct 2025 | 77 | 61% | +0.76 | 6.50x | -12% |
| skip score <= -1 | holdout | 18 | 50% | +0.43 | 1.32x | -13% |
| skip score <= -2 | 2022 - Oct 2025 | 111 | 59% | +0.75 | 11.92x | -16% |
| skip score <= -2 | holdout | 27 | 59% | +0.82 | 1.85x | -13% |

Audit: pending.
