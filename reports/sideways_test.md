# After a pump or dump: is the extreme tested before the sideways resolves?

Trader's concept (22 Nov 2024 review): after a pump the price goes sideways and the high gets tested first, mostly. Definitions in the module docstring (impulse >= 2 ATR in 6 candles, close in the top 30%; sideways = 3 candles without a close beyond the extreme or the origin; tested = a high within 0.25 ATR of the extreme before a close beyond it or beyond the origin). **Control**: the same measurement on windows whose leg is < 1.5 ATR (no impulse) at the same close position. 90% interval from a calendar-month bootstrap pooled across the six coins.

## Six coins (BTC, ETH, BNB, SOL, XRP, DOGE)

| tf | move | period | impulses | went sideways | continued at once | reversed at once | extreme tested before the range resolved | 90% low | 90% high | same for small legs (< 1.5 ATR) | control n | first test = sweep | = touch | = direct break | resolved up | resolved down | candles to the test (median) | retrace before the test (median share of the leg) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1D | dump | 2022 - Oct 2025 | 516 | 62% | 35% | 3% | 71% | 66% | 76% | 55% | 29 | 24% | 31% | 10% | 52% | 41% | 5.0 | 51% |
| 1D | dump | holdout | 118 | 59% | 38% | 3% | 86% | 76% | 93% | 0% | 2 | 26% | 40% | 9% | 69% | 17% | 5.0 | 45% |
| 1D | pump | 2022 - Oct 2025 | 808 | 50% | 49% | 1% | 77% | 72% | 81% | 50% | 18 | 23% | 34% | 16% | 63% | 32% | 4.0 | 51% |
| 1D | pump | holdout | 97 | 67% | 29% | 4% | 68% | 56% | 79% | 100% | 2 | 34% | 23% | 11% | 52% | 40% | 6.0 | 66% |
| 4h | dump | 2022 - Oct 2025 | 3685 | 60% | 37% | 2% | 72% | 70% | 74% | 66% | 101 | 23% | 31% | 11% | 55% | 38% | 5.0 | 49% |
| 4h | dump | holdout | 808 | 56% | 42% | 2% | 79% | 74% | 83% | 74% | 23 | 24% | 29% | 17% | 60% | 34% | 5.0 | 49% |
| 4h | pump | 2022 - Oct 2025 | 4472 | 55% | 44% | 2% | 77% | 76% | 79% | 64% | 149 | 23% | 34% | 13% | 61% | 31% | 5.0 | 49% |
| 4h | pump | holdout | 700 | 56% | 41% | 3% | 73% | 69% | 76% | 65% | 26 | 21% | 33% | 10% | 52% | 38% | 5.0 | 48% |

### Retest of the price (the impulse close), the midpoint and the origin

first = what happened first in the sideways (after the price moved away): the high was tested, the impulse close was retested, a break after a pullback, a continuation without any 1 ATR pullback, or neither (reversed / timed out).

| tf | move | period | sideways impulses | high tested first | close retested first | broke first | continued without a pullback | neither | close retested | held -> continued | closed below -> continued | never retested -> continued | midpoint retested | held -> continued | failed -> continued | origin retested | held -> continued | retest with RSI cooled >= 5 -> continued | n | RSI not cooled -> continued | n | continuations with RSI lower at the break than at the impulse |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1D | dump | 2022 - Oct 2025 | 320 | 39% | 31% | 9% | 2% | 19% | 53% | 62% | 44% | 51% | 78% | 45% | 29% | 22% | 16% | 38% | 60 | 62% | 110 | 16% |
| 1D | dump | holdout | 70 | 47% | 30% | 4% | 4% | 14% | 54% | 93% | 55% | 53% | 53% | 52% | 30% | 19% | 31% | 54% | 13 | 96% | 25 | 19% |
| 1D | pump | 2022 - Oct 2025 | 403 | 41% | 32% | 9% | 2% | 16% | 54% | 77% | 62% | 56% | 75% | 56% | 32% | 23% | 14% | 61% | 107 | 77% | 110 | 33% |
| 1D | pump | holdout | 65 | 51% | 12% | 9% | 0% | 28% | 38% | 87% | 30% | 45% | 89% | 47% | 45% | 26% | 18% | 40% | 10 | 80% | 15 | 15% |
| 4h | dump | 2022 - Oct 2025 | 2223 | 40% | 31% | 7% | 3% | 19% | 53% | 67% | 47% | 51% | 76% | 44% | 30% | 23% | 15% | 45% | 438 | 65% | 742 | 18% |
| 4h | dump | holdout | 456 | 41% | 28% | 11% | 6% | 14% | 54% | 69% | 48% | 61% | 73% | 53% | 29% | 21% | 15% | 44% | 95 | 69% | 152 | 19% |
| 4h | pump | 2022 - Oct 2025 | 2445 | 43% | 27% | 9% | 4% | 16% | 50% | 73% | 55% | 57% | 76% | 53% | 34% | 25% | 24% | 56% | 500 | 71% | 722 | 26% |
| 4h | pump | holdout | 391 | 42% | 24% | 7% | 5% | 21% | 46% | 66% | 46% | 50% | 75% | 38% | 33% | 26% | 15% | 41% | 71 | 65% | 110 | 18% |

### Is the extreme at a strong S/R level (within 0.5 ATR)?  The sweep as an exit signal lives or dies here

| tf | move | period | extreme | sideways impulses | continued | extreme tested | sweeps | sweep -> continued | sweep -> reversed | touches | touch -> continued |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1D | dump | 2022 - Oct 2025 | at a strong level | 228 | 55% | 71% | 50 | 70% | 28% | 69 | 70% |
| 1D | dump | 2022 - Oct 2025 | elsewhere | 92 | 46% | 72% | 26 | 50% | 27% | 30 | 63% |
| 1D | dump | holdout | at a strong level | 57 | 77% | 86% | 15 | 93% | 0% | 20 | 80% |
| 1D | dump | holdout | elsewhere | 13 | 31% | 85% | 3 | - | - | 8 | 12% |
| 1D | pump | 2022 - Oct 2025 | at a strong level | 218 | 62% | 76% | 43 | 77% | 16% | 81 | 74% |
| 1D | pump | 2022 - Oct 2025 | elsewhere | 185 | 65% | 78% | 49 | 80% | 14% | 55 | 75% |
| 1D | pump | holdout | at a strong level | 52 | 56% | 69% | 18 | 78% | 17% | 13 | 77% |
| 1D | pump | holdout | elsewhere | 13 | 38% | 62% | 4 | - | - | 2 | - |
| 4h | dump | 2022 - Oct 2025 | at a strong level | 1062 | 55% | 72% | 257 | 70% | 21% | 329 | 68% |
| 4h | dump | 2022 - Oct 2025 | elsewhere | 1161 | 55% | 72% | 261 | 66% | 23% | 360 | 68% |
| 4h | dump | holdout | at a strong level | 255 | 60% | 78% | 61 | 70% | 15% | 75 | 63% |
| 4h | dump | holdout | elsewhere | 201 | 60% | 79% | 48 | 52% | 38% | 57 | 75% |
| 4h | pump | 2022 - Oct 2025 | at a strong level | 1077 | 59% | 76% | 246 | 70% | 19% | 346 | 66% |
| 4h | pump | 2022 - Oct 2025 | elsewhere | 1368 | 63% | 78% | 326 | 75% | 18% | 475 | 72% |
| 4h | pump | holdout | at a strong level | 228 | 50% | 73% | 45 | 58% | 29% | 78 | 58% |
| 4h | pump | holdout | elsewhere | 163 | 56% | 72% | 37 | 73% | 14% | 50 | 66% |

### After the first test of the high, how did the range resolve?

| tf | move | period | first test | n | continued (close beyond the extreme) | reversed (close beyond the origin) | neither in 40 candles | candles to resolve (median) |
|---|---|---|---|---|---|---|---|---|
| 1D | dump | 2022 - Oct 2025 | sweep | 76 | 63% | 28% | 9% | 13.0 |
| 1D | dump | 2022 - Oct 2025 | touch | 99 | 68% | 23% | 9% | 13.0 |
| 1D | dump | 2022 - Oct 2025 | break | 32 | 100% | 0% | 0% | 6.0 |
| 1D | dump | 2022 - Oct 2025 | no pullback | 20 | 100% | 0% | 0% | 5.0 |
| 1D | dump | 2022 - Oct 2025 | pulled back, never tested | 93 | 0% | 92% | 8% | 10.0 |
| 1D | dump | holdout | sweep | 18 | 94% | 0% | 6% | 9.0 |
| 1D | dump | holdout | touch | 28 | 61% | 11% | 29% | 11.0 |
| 1D | dump | holdout | break | 6 | 100% | 0% | 0% | 4.5 |
| 1D | dump | holdout | no pullback | 8 | 100% | 0% | 0% | 4.0 |
| 1D | dump | holdout | pulled back, never tested | 10 | 0% | 90% | 10% | 9.0 |
| 1D | pump | 2022 - Oct 2025 | sweep | 92 | 78% | 15% | 7% | 9.0 |
| 1D | pump | 2022 - Oct 2025 | touch | 136 | 74% | 21% | 5% | 9.0 |
| 1D | pump | 2022 - Oct 2025 | break | 64 | 100% | 0% | 0% | 7.0 |
| 1D | pump | 2022 - Oct 2025 | no pullback | 18 | 100% | 0% | 0% | 5.0 |
| 1D | pump | 2022 - Oct 2025 | pulled back, never tested | 93 | 0% | 94% | 6% | 11.0 |
| 1D | pump | holdout | sweep | 22 | 73% | 23% | 5% | 11.0 |
| 1D | pump | holdout | touch | 15 | 73% | 20% | 7% | 12.0 |
| 1D | pump | holdout | break | 7 | 100% | 0% | 0% | 8.0 |
| 1D | pump | holdout | pulled back, never tested | 21 | 0% | 86% | 14% | 9.5 |
| 4h | dump | 2022 - Oct 2025 | sweep | 518 | 68% | 22% | 10% | 11.0 |
| 4h | dump | 2022 - Oct 2025 | touch | 689 | 68% | 23% | 9% | 12.0 |
| 4h | dump | 2022 - Oct 2025 | break | 248 | 100% | 0% | 0% | 6.5 |
| 4h | dump | 2022 - Oct 2025 | no pullback | 146 | 100% | 0% | 0% | 5.0 |
| 4h | dump | 2022 - Oct 2025 | pulled back, never tested | 622 | 0% | 90% | 10% | 9.0 |
| 4h | dump | holdout | sweep | 109 | 62% | 25% | 13% | 15.0 |
| 4h | dump | holdout | touch | 132 | 68% | 27% | 5% | 12.0 |
| 4h | dump | holdout | break | 78 | 100% | 0% | 0% | 6.0 |
| 4h | dump | holdout | no pullback | 39 | 100% | 0% | 0% | 5.0 |
| 4h | dump | holdout | pulled back, never tested | 98 | 0% | 94% | 6% | 10.0 |
| 4h | pump | 2022 - Oct 2025 | sweep | 572 | 73% | 19% | 9% | 11.0 |
| 4h | pump | 2022 - Oct 2025 | touch | 821 | 70% | 20% | 10% | 12.0 |
| 4h | pump | 2022 - Oct 2025 | break | 321 | 100% | 0% | 0% | 7.0 |
| 4h | pump | 2022 - Oct 2025 | no pullback | 180 | 100% | 0% | 0% | 4.0 |
| 4h | pump | 2022 - Oct 2025 | pulled back, never tested | 551 | 0% | 88% | 12% | 10.0 |
| 4h | pump | holdout | sweep | 82 | 65% | 22% | 13% | 10.0 |
| 4h | pump | holdout | touch | 128 | 61% | 29% | 10% | 11.0 |
| 4h | pump | holdout | break | 38 | 100% | 0% | 0% | 8.0 |
| 4h | pump | holdout | no pullback | 36 | 100% | 0% | 0% | 5.0 |
| 4h | pump | holdout | pulled back, never tested | 107 | 0% | 89% | 11% | 10.0 |

## ETH only

| tf | move | period | impulses | went sideways | continued at once | reversed at once | extreme tested before the range resolved | 90% low | 90% high | same for small legs (< 1.5 ATR) | control n | first test = sweep | = touch | = direct break | resolved up | resolved down | candles to the test (median) | retrace before the test (median share of the leg) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1D | dump | 2022 - Oct 2025 | 97 | 62% | 37% | 1% | 65% | 54% | 75% | 50% | 4 | 17% | 33% | 12% | 43% | 52% | 5.0 | 52% |
| 1D | dump | holdout | 20 | 45% | 55% | 0% | 67% | - | - | - | 0 | 22% | 33% | 11% | 44% | 33% | 4.0 | 36% |
| 1D | pump | 2022 - Oct 2025 | 167 | 48% | 52% | 0% | 86% | 80% | 93% | 75% | 4 | 28% | 36% | 18% | 74% | 24% | 6.0 | 53% |
| 1D | pump | holdout | 19 | 68% | 26% | 5% | 54% | - | - | - | 0 | 31% | 8% | 15% | 54% | 38% | 5.0 | 66% |
| 4h | dump | 2022 - Oct 2025 | 651 | 62% | 35% | 3% | 70% | 67% | 73% | 60% | 15 | 23% | 28% | 12% | 54% | 39% | 5.0 | 50% |
| 4h | dump | holdout | 117 | 63% | 36% | 1% | 80% | 72% | 87% | 75% | 4 | 31% | 30% | 11% | 61% | 32% | 5.0 | 42% |
| 4h | pump | 2022 - Oct 2025 | 868 | 52% | 46% | 2% | 81% | 78% | 84% | 65% | 20 | 24% | 35% | 13% | 64% | 29% | 5.0 | 48% |
| 4h | pump | holdout | 100 | 62% | 36% | 2% | 74% | 66% | 82% | 83% | 6 | 24% | 35% | 8% | 50% | 40% | 6.0 | 49% |

### Retest of the price (the impulse close), the midpoint and the origin

first = what happened first in the sideways (after the price moved away): the high was tested, the impulse close was retested, a break after a pullback, a continuation without any 1 ATR pullback, or neither (reversed / timed out).

| tf | move | period | sideways impulses | high tested first | close retested first | broke first | continued without a pullback | neither | close retested | held -> continued | closed below -> continued | never retested -> continued | midpoint retested | held -> continued | failed -> continued | origin retested | held -> continued | retest with RSI cooled >= 5 -> continued | n | RSI not cooled -> continued | n | continuations with RSI lower at the break than at the impulse |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1D | dump | 2022 - Oct 2025 | 60 | 37% | 35% | 8% | 2% | 18% | 53% | 47% | 40% | 43% | 85% | 39% | 38% | 28% | 12% | 27% | 11 | 52% | 21 | 27% |
| 1D | pump | 2022 - Oct 2025 | 80 | 42% | 34% | 11% | 0% | 12% | 51% | 82% | 84% | 64% | 76% | 76% | 44% | 20% | 44% | 85% | 20 | 81% | 21 | 36% |
| 1D | pump | holdout | 13 | 31% | 8% | 15% | 0% | 46% | 31% | - | - | 33% | 85% | 50% | - | 31% | - | - | 1 | - | 3 | 43% |
| 4h | dump | 2022 - Oct 2025 | 402 | 37% | 34% | 5% | 2% | 21% | 56% | 72% | 48% | 48% | 77% | 44% | 33% | 22% | 17% | 42% | 96 | 72% | 129 | 16% |
| 4h | dump | holdout | 74 | 46% | 34% | 5% | 5% | 9% | 65% | 65% | 59% | 58% | 69% | 54% | 21% | 23% | 12% | 59% | 17 | 65% | 31 | 20% |
| 4h | pump | 2022 - Oct 2025 | 455 | 43% | 27% | 9% | 6% | 14% | 50% | 75% | 57% | 61% | 71% | 53% | 41% | 23% | 33% | 58% | 92 | 73% | 137 | 25% |
| 4h | pump | holdout | 62 | 47% | 32% | 5% | 2% | 15% | 60% | 52% | 44% | 52% | 77% | 37% | 31% | 31% | 11% | 31% | 13 | 58% | 24 | 19% |

### Is the extreme at a strong S/R level (within 0.5 ATR)?  The sweep as an exit signal lives or dies here

| tf | move | period | extreme | sideways impulses | continued | extreme tested | sweeps | sweep -> continued | sweep -> reversed | touches | touch -> continued |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1D | dump | 2022 - Oct 2025 | at a strong level | 39 | 44% | 64% | 6 | 50% | 50% | 12 | 58% |
| 1D | dump | 2022 - Oct 2025 | elsewhere | 21 | 43% | 67% | 4 | - | - | 8 | 75% |
| 1D | pump | 2022 - Oct 2025 | at a strong level | 42 | 69% | 81% | 9 | 56% | 44% | 14 | 93% |
| 1D | pump | 2022 - Oct 2025 | elsewhere | 38 | 79% | 92% | 13 | 100% | 0% | 15 | 67% |
| 4h | dump | 2022 - Oct 2025 | at a strong level | 173 | 53% | 69% | 44 | 70% | 25% | 47 | 70% |
| 4h | dump | 2022 - Oct 2025 | elsewhere | 229 | 55% | 71% | 49 | 61% | 29% | 65 | 72% |
| 4h | dump | holdout | at a strong level | 41 | 54% | 76% | 14 | 86% | 0% | 12 | 42% |
| 4h | dump | holdout | elsewhere | 33 | 70% | 85% | 9 | 56% | 33% | 10 | 90% |
| 4h | pump | 2022 - Oct 2025 | at a strong level | 180 | 63% | 81% | 35 | 69% | 14% | 64 | 67% |
| 4h | pump | 2022 - Oct 2025 | elsewhere | 275 | 64% | 81% | 73 | 79% | 14% | 93 | 68% |
| 4h | pump | holdout | at a strong level | 28 | 54% | 75% | 7 | 57% | 43% | 9 | 67% |
| 4h | pump | holdout | elsewhere | 34 | 47% | 74% | 8 | 62% | 12% | 13 | 54% |

### After the first test of the high, how did the range resolve?

| tf | move | period | first test | n | continued (close beyond the extreme) | reversed (close beyond the origin) | neither in 40 candles | candles to resolve (median) |
|---|---|---|---|---|---|---|---|---|
| 1D | dump | 2022 - Oct 2025 | sweep | 10 | 40% | 50% | 10% | 12.0 |
| 1D | dump | 2022 - Oct 2025 | touch | 20 | 65% | 25% | 10% | 11.5 |
| 1D | dump | 2022 - Oct 2025 | break | 7 | 100% | 0% | 0% | 6.0 |
| 1D | dump | 2022 - Oct 2025 | pulled back, never tested | 21 | 0% | 100% | 0% | 9.0 |
| 1D | pump | 2022 - Oct 2025 | sweep | 22 | 82% | 18% | 0% | 10.5 |
| 1D | pump | 2022 - Oct 2025 | touch | 29 | 79% | 14% | 7% | 8.0 |
| 1D | pump | 2022 - Oct 2025 | break | 14 | 100% | 0% | 0% | 7.5 |
| 1D | pump | 2022 - Oct 2025 | pulled back, never tested | 11 | 0% | 100% | 0% | 10.0 |
| 1D | pump | holdout | pulled back, never tested | 6 | 0% | 83% | 17% | 7.0 |
| 4h | dump | 2022 - Oct 2025 | sweep | 93 | 66% | 27% | 8% | 11.0 |
| 4h | dump | 2022 - Oct 2025 | touch | 112 | 71% | 21% | 7% | 13.0 |
| 4h | dump | 2022 - Oct 2025 | break | 48 | 100% | 0% | 0% | 6.0 |
| 4h | dump | 2022 - Oct 2025 | no pullback | 29 | 100% | 0% | 0% | 4.0 |
| 4h | dump | 2022 - Oct 2025 | pulled back, never tested | 120 | 0% | 90% | 10% | 7.5 |
| 4h | dump | holdout | sweep | 23 | 74% | 13% | 13% | 11.0 |
| 4h | dump | holdout | touch | 22 | 64% | 32% | 5% | 14.0 |
| 4h | dump | holdout | break | 8 | 100% | 0% | 0% | 5.5 |
| 4h | dump | holdout | no pullback | 6 | 100% | 0% | 0% | 5.5 |
| 4h | dump | holdout | pulled back, never tested | 15 | 0% | 93% | 7% | 10.5 |
| 4h | pump | 2022 - Oct 2025 | sweep | 108 | 76% | 14% | 10% | 11.0 |
| 4h | pump | 2022 - Oct 2025 | touch | 157 | 68% | 23% | 10% | 12.0 |
| 4h | pump | 2022 - Oct 2025 | break | 61 | 100% | 0% | 0% | 6.0 |
| 4h | pump | 2022 - Oct 2025 | no pullback | 41 | 100% | 0% | 0% | 4.0 |
| 4h | pump | 2022 - Oct 2025 | pulled back, never tested | 88 | 0% | 92% | 8% | 11.0 |
| 4h | pump | holdout | sweep | 15 | 60% | 27% | 13% | 14.0 |
| 4h | pump | holdout | touch | 22 | 59% | 27% | 14% | 13.0 |
| 4h | pump | holdout | break | 5 | 100% | 0% | 0% | 8.0 |
| 4h | pump | holdout | pulled back, never tested | 16 | 0% | 94% | 6% | 8.0 |

## Same close position, impulse vs small leg (six coins, 2022 - Oct 2025)

If the test rate is the same at the same distance from the high, the concept is proximity, not the pump.

| tf | close below the extreme (ATR) | impulses | tested | small legs | tested | impulse resolved up | small leg resolved up |
|---|---|---|---|---|---|---|---|
| 1D | [0.25, 0.5) | 235 | 76% | 30 | 53% | 59% | 43% |
| 4h | [0.0, 0.25) | 829 | 77% | 130 | 62% | 61% | 54% |
| 4h | [0.25, 0.5) | 1422 | 74% | 120 | 69% | 59% | 56% |

Audit: pending.
