# Trendline breaks: how often does price come back to retest the line?

Six coins (BTC, ETH, BNB, SOL, XRP, DOGE). A break = the first close beyond the line by >= 0.25 ATR; a retest = price comes back within 0.25 ATR of the extended line. Rising lines broken down and falling lines broken up (mirrored) pooled. **After a rejected retest**: right = price then moves 1.5 ATR further away from the line before 1.5 ATR back (50% = coin flip).

| timeframe | lines | period | breaks | retest within 5 candles | within 10 | within 20 | median candles to the retest | median run away before it (ATR) | retest rejected (closes back on the broken side) | line reclaimed (break failed) | closed on the line | after a rejected retest: right | retest after first moving >= 1 ATR away (within 20) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 4h | all breaks | 2020 - Oct 2025 | 2845 | 58% | 64% | 68% | 1 | 1.1 | 76% | 11% | 13% | 53% | 49% |
| 4h | all breaks | holdout | 520 | 64% | 70% | 75% | 1 | 1.2 | 73% | 14% | 13% | 51% | 57% |
| 4h | lines with 3+ touches | 2020 - Oct 2025 | 427 | 62% | 69% | 73% | 1 | 1.2 | 77% | 11% | 12% | 59% | 55% |
| 4h | lines with 3+ touches | holdout | 86 | 66% | 69% | 73% | 1 | 1.2 | 78% | 10% | 13% | 35% | 56% |
| 4h | 2-touch lines | 2020 - Oct 2025 | 2418 | 58% | 64% | 67% | 1 | 1.1 | 75% | 11% | 13% | 52% | 47% |
| 4h | 2-touch lines | holdout | 434 | 64% | 70% | 76% | 1 | 1.2 | 73% | 15% | 13% | 54% | 58% |
| 4h | steep lines | 2020 - Oct 2025 | 980 | 50% | 55% | 57% | 1 | 1.1 | 73% | 13% | 13% | 55% | 38% |
| 4h | steep lines | holdout | 139 | 59% | 65% | 68% | 2 | 1.2 | 71% | 18% | 11% | 60% | 53% |
| 1h | all breaks | 2020 - Oct 2025 | 11377 | 61% | 66% | 70% | 1 | 1.1 | 75% | 13% | 12% | 51% | 51% |
| 1h | all breaks | holdout | 1935 | 61% | 67% | 71% | 1 | 1.1 | 75% | 14% | 12% | 49% | 51% |
| 1h | lines with 3+ touches | 2020 - Oct 2025 | 1885 | 65% | 71% | 76% | 1 | 1.2 | 77% | 10% | 13% | 52% | 57% |
| 1h | lines with 3+ touches | holdout | 288 | 67% | 74% | 78% | 1 | 1.1 | 76% | 13% | 10% | 50% | 57% |
| 1h | 2-touch lines | 2020 - Oct 2025 | 9492 | 60% | 65% | 69% | 1 | 1.1 | 75% | 13% | 12% | 50% | 49% |
| 1h | 2-touch lines | holdout | 1647 | 60% | 66% | 70% | 1 | 1.1 | 74% | 14% | 12% | 49% | 50% |
| 1h | steep lines | 2020 - Oct 2025 | 3430 | 50% | 55% | 58% | 1 | 1.1 | 75% | 14% | 12% | 51% | 39% |
| 1h | steep lines | holdout | 611 | 48% | 54% | 57% | 1 | 1.2 | 76% | 15% | 9% | 51% | 41% |
| 1D | all breaks | 2020 - Oct 2025 | 456 | 54% | 61% | 64% | 1 | 1.1 | 79% | 11% | 11% | 55% | 44% |
| 1D | all breaks | holdout | 82 | 60% | 61% | 63% | 1 | 1.1 | 85% | 6% | 10% | 42% | 43% |
| 1D | lines with 3+ touches | 2020 - Oct 2025 | 69 | 52% | 61% | 64% | 1 | 1.4 | 84% | 2% | 14% | 56% | 49% |
| 1D | lines with 3+ touches | holdout | 14 | 64% | 64% | 64% | 1 | 1.0 | 56% | 0% | 44% | 20% | 29% |
| 1D | 2-touch lines | 2020 - Oct 2025 | 387 | 55% | 60% | 64% | 1 | 1.1 | 78% | 12% | 10% | 55% | 43% |
| 1D | 2-touch lines | holdout | 68 | 59% | 60% | 63% | 1 | 1.1 | 91% | 7% | 2% | 45% | 46% |
| 1D | steep lines | 2020 - Oct 2025 | 150 | 43% | 50% | 52% | 1 | 1.0 | 74% | 17% | 9% | 57% | 31% |
| 1D | steep lines | holdout | 29 | 55% | 55% | 59% | 2 | 1.1 | 100% | 0% | 0% | 47% | 48% |

Audit: pending.
