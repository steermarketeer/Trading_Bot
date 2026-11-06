# Trendline breaks: how often does price come back to retest the line?

Six coins (BTC, ETH, BNB, SOL, XRP, DOGE). A break = the first close beyond the line by >= 0.25 ATR; a retest = price comes back within 0.25 ATR of the extended line. Rising lines broken down and falling lines broken up (mirrored) pooled. **After a rejected retest**: right = price then moves 1.5 ATR further away from the line before 1.5 ATR back (50% = coin flip).

| timeframe | lines | period | breaks | retest within 5 candles | within 10 | within 20 | median candles to the retest | median run away before it (ATR) | retest rejected (closes back on the broken side) | line reclaimed (break failed) | closed on the line | after a rejected retest: right | 90% low | 90% high | same test taken at the break itself | retested on the very next candle | retest after first moving >= 1 ATR away (within 20) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 4h | all breaks | 2020 - Oct 2025 | 2845 | 58% | 64% | 68% | 1 | 1.0 | 76% | 11% | 13% | 53% | 51% | 56% | 55% | 40% | 51% |
| 4h | all breaks | holdout | 520 | 64% | 70% | 75% | 1 | 1.0 | 73% | 14% | 13% | 51% | 45% | 57% | 50% | 43% | 60% |
| 4h | lines with 3+ touches | 2020 - Oct 2025 | 427 | 62% | 69% | 73% | 1 | 1.1 | 77% | 11% | 12% | 59% | 54% | 63% | 56% | 41% | 58% |
| 4h | lines with 3+ touches | holdout | 86 | 66% | 69% | 73% | 1 | 0.9 | 78% | 10% | 13% | 35% | 23% | 50% | 45% | 45% | 59% |
| 4h | 2-touch lines | 2020 - Oct 2025 | 2418 | 58% | 64% | 67% | 1 | 1.0 | 75% | 11% | 13% | 52% | 50% | 55% | 55% | 40% | 50% |
| 4h | 2-touch lines | holdout | 434 | 64% | 70% | 76% | 1 | 1.0 | 73% | 15% | 13% | 54% | 48% | 61% | 50% | 42% | 60% |
| 4h | steep lines | 2020 - Oct 2025 | 980 | 50% | 55% | 57% | 1 | 0.9 | 73% | 13% | 13% | 55% | 50% | 60% | 55% | 32% | 40% |
| 4h | steep lines | holdout | 139 | 59% | 65% | 68% | 2 | 1.1 | 71% | 18% | 11% | 60% | 50% | 68% | 43% | 32% | 55% |
| 1h | all breaks | 2020 - Oct 2025 | 11377 | 61% | 66% | 70% | 1 | 1.0 | 75% | 13% | 12% | 51% | 50% | 52% | 52% | 44% | 54% |
| 1h | all breaks | holdout | 1935 | 61% | 67% | 71% | 1 | 1.0 | 75% | 14% | 12% | 49% | 47% | 52% | 50% | 44% | 54% |
| 1h | lines with 3+ touches | 2020 - Oct 2025 | 1885 | 65% | 71% | 76% | 1 | 1.0 | 77% | 10% | 13% | 52% | 49% | 55% | 53% | 47% | 60% |
| 1h | lines with 3+ touches | holdout | 288 | 67% | 74% | 78% | 1 | 1.0 | 76% | 13% | 10% | 50% | 41% | 59% | 46% | 49% | 60% |
| 1h | 2-touch lines | 2020 - Oct 2025 | 9492 | 60% | 65% | 69% | 1 | 1.0 | 75% | 13% | 12% | 50% | 49% | 51% | 52% | 43% | 52% |
| 1h | 2-touch lines | holdout | 1647 | 60% | 66% | 70% | 1 | 1.0 | 74% | 14% | 12% | 49% | 46% | 52% | 51% | 43% | 53% |
| 1h | steep lines | 2020 - Oct 2025 | 3430 | 50% | 55% | 58% | 1 | 0.9 | 75% | 14% | 12% | 51% | 49% | 53% | 51% | 34% | 41% |
| 1h | steep lines | holdout | 611 | 48% | 54% | 57% | 1 | 1.0 | 76% | 15% | 9% | 51% | 47% | 56% | 54% | 33% | 42% |
| 1D | all breaks | 2020 - Oct 2025 | 456 | 54% | 61% | 64% | 1 | 0.9 | 79% | 11% | 11% | 55% | 49% | 61% | 61% | 40% | 47% |
| 1D | all breaks | holdout | 82 | 60% | 61% | 63% | 1 | 1.0 | 85% | 6% | 10% | 42% | 27% | 54% | 50% | 35% | 46% |
| 1D | lines with 3+ touches | 2020 - Oct 2025 | 69 | 52% | 61% | 64% | 1 | 1.1 | 84% | 2% | 14% | 56% | 38% | 72% | 79% | 35% | 51% |
| 1D | lines with 3+ touches | holdout | 14 | 64% | 64% | 64% | 1 | 0.6 | 56% | 0% | 44% | 20% | 0% | 40% | 57% | 43% | 36% |
| 1D | 2-touch lines | 2020 - Oct 2025 | 387 | 55% | 60% | 64% | 1 | 0.9 | 78% | 12% | 10% | 55% | 49% | 62% | 58% | 41% | 46% |
| 1D | 2-touch lines | holdout | 68 | 59% | 60% | 63% | 1 | 1.0 | 91% | 7% | 2% | 45% | 31% | 56% | 48% | 34% | 49% |
| 1D | steep lines | 2020 - Oct 2025 | 150 | 43% | 50% | 52% | 1 | 0.8 | 74% | 17% | 9% | 57% | 44% | 69% | 60% | 33% | 33% |
| 1D | steep lines | holdout | 29 | 55% | 55% | 59% | 2 | 1.1 | 100% | 0% | 0% | 47% | 25% | 67% | 50% | 28% | 55% |

**Most quick retests are mechanical.** A break only has to close 0.25 ATR beyond the line, and a retest is a wick back within 0.25 ATR: when the break closes close to the line, the very next candle reaches it about as often as any ordinary candle reaches the same distance (round 18 audit: 40 - 44% observed vs 42 - 43% for ordinary candles), and it closes back on the broken side about as often as an ordinary candle at that level does. The meaningful number is the strict retest (price first moves >= 1 ATR away, then comes back). Below, by how far the break closed beyond the line:

| timeframe | break close beyond the line | breaks 2020-25 | retested on the next candle | retested within 20 | strict retest |
|---|---|---|---|---|---|
| 4h | 0.25 - 0.5 ATR | 1197 | 62% | 82% | 52% |
| 4h | 0.5 - 1 ATR | 1120 | 31% | 64% | 55% |
| 4h | 1 ATR or more | 528 | 8% | 44% | 44% |
| 1h | 0.25 - 0.5 ATR | 4825 | 67% | 83% | 52% |
| 1h | 0.5 - 1 ATR | 4525 | 34% | 67% | 58% |
| 1h | 1 ATR or more | 2027 | 11% | 47% | 47% |
| 1D | 0.25 - 0.5 ATR | 215 | 61% | 78% | 47% |
| 1D | 0.5 - 1 ATR | 160 | 28% | 59% | 52% |
| 1D | 1 ATR or more | 81 | 7% | 36% | 36% |

Audit: round 18 (findings applied), round 19 pending.
