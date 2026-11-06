# After a pump or dump: is the extreme tested before the sideways resolves?

Trader's concept (22 Nov 2024 review): after a pump the price goes sideways and the high gets tested first, mostly. Definitions in the module docstring (impulse >= 2 ATR in 6 candles, close in the top 30%; sideways = 3 candles without a close beyond the extreme or the origin; tested = a high within 0.25 ATR of the extreme before a close beyond it or beyond the origin). **Control**: the same measurement on windows whose leg is < 1.5 ATR (no impulse) at the same close position. 90% interval from a calendar-month bootstrap pooled across the six coins.

## Six coins (BTC, ETH, BNB, SOL, XRP, DOGE)

| tf | move | period | impulses | went sideways | continued at once | reversed at once | extreme tested before the range resolved | 90% low | 90% high | same for small legs (< 1.5 ATR) | control n | first test = sweep | = touch | = direct break | resolved up | resolved down | candles to the test (median) | retrace before the test (median share of the leg) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1D | dump | 2022 - Oct 2025 | 384 | 61% | 36% | 2% | 74% | 68% | 80% | 56% | 16 | 22% | 33% | 12% | 54% | 38% | 5.0 | 51% |
| 1D | dump | holdout | 118 | 59% | 38% | 3% | 86% | 76% | 93% | 0% | 2 | 26% | 40% | 9% | 69% | 17% | 5.0 | 45% |
| 1D | pump | 2022 - Oct 2025 | 508 | 53% | 46% | 1% | 75% | 69% | 80% | 58% | 12 | 21% | 35% | 14% | 59% | 37% | 4.0 | 50% |
| 1D | pump | holdout | 97 | 67% | 29% | 4% | 68% | 56% | 79% | 100% | 2 | 34% | 23% | 11% | 52% | 40% | 6.0 | 66% |
| 4h | dump | 2022 - Oct 2025 | 2641 | 60% | 38% | 2% | 72% | 69% | 74% | 74% | 54 | 23% | 30% | 12% | 56% | 37% | 5.0 | 48% |
| 4h | dump | holdout | 808 | 56% | 42% | 2% | 79% | 74% | 83% | 74% | 23 | 24% | 29% | 17% | 60% | 34% | 5.0 | 49% |
| 4h | pump | 2022 - Oct 2025 | 2915 | 57% | 41% | 2% | 77% | 74% | 79% | 66% | 96 | 24% | 33% | 12% | 60% | 32% | 5.0 | 50% |
| 4h | pump | holdout | 700 | 56% | 41% | 3% | 73% | 69% | 76% | 65% | 26 | 21% | 33% | 10% | 52% | 38% | 5.0 | 48% |

### Retest of the price (the impulse close), the midpoint and the origin

first = what happened first in the sideways (after the price moved away): the high was tested, the impulse close was retested, a break after a pullback, a continuation without any 1 ATR pullback, or neither (reversed / timed out).

| tf | move | period | sideways impulses | high tested first | close retested first | broke first | continued without a pullback | neither | close retested | held -> continued | closed below -> continued | never retested -> continued | midpoint retested | held -> continued | failed -> continued | origin retested | held -> continued | retest with RSI cooled >= 5 -> continued | n | RSI not cooled -> continued | n | continuations with RSI lower at the break than at the impulse |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1D | dump | 2022 - Oct 2025 | 236 | 39% | 31% | 10% | 3% | 17% | 51% | 63% | 42% | 55% | 77% | 48% | 32% | 21% | 14% | 38% | 48 | 64% | 72 | 16% |
| 1D | dump | holdout | 70 | 47% | 30% | 4% | 4% | 14% | 54% | 93% | 55% | 53% | 53% | 52% | 30% | 19% | 31% | 54% | 13 | 96% | 25 | 19% |
| 1D | pump | 2022 - Oct 2025 | 271 | 38% | 33% | 9% | 3% | 18% | 52% | 72% | 55% | 54% | 75% | 51% | 23% | 24% | 9% | 54% | 68 | 71% | 72 | 30% |
| 1D | pump | holdout | 65 | 51% | 12% | 9% | 0% | 28% | 38% | 87% | 30% | 45% | 89% | 47% | 45% | 26% | 18% | 40% | 10 | 80% | 15 | 15% |
| 4h | dump | 2022 - Oct 2025 | 1579 | 40% | 30% | 8% | 3% | 20% | 52% | 70% | 48% | 51% | 75% | 45% | 31% | 23% | 16% | 46% | 303 | 69% | 516 | 18% |
| 4h | dump | holdout | 456 | 41% | 28% | 11% | 6% | 14% | 54% | 69% | 48% | 61% | 73% | 53% | 29% | 21% | 15% | 44% | 95 | 69% | 152 | 19% |
| 4h | pump | 2022 - Oct 2025 | 1656 | 42% | 27% | 9% | 4% | 17% | 50% | 71% | 56% | 55% | 76% | 52% | 31% | 25% | 22% | 56% | 328 | 70% | 503 | 25% |
| 4h | pump | holdout | 391 | 42% | 24% | 7% | 5% | 21% | 46% | 66% | 46% | 50% | 75% | 38% | 33% | 26% | 15% | 41% | 71 | 65% | 110 | 18% |

### Is the extreme at a strong S/R level (within 0.5 ATR)?  The sweep as an exit signal lives or dies here

| tf | move | period | extreme | sideways impulses | continued | extreme tested | sweeps | sweep -> continued | sweep -> reversed | touches | touch -> continued |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1D | dump | 2022 - Oct 2025 | at a strong level | 176 | 57% | 73% | 35 | 63% | 34% | 58 | 74% |
| 1D | dump | 2022 - Oct 2025 | elsewhere | 60 | 45% | 75% | 18 | 44% | 28% | 20 | 60% |
| 1D | dump | holdout | at a strong level | 57 | 77% | 86% | 15 | 93% | 0% | 20 | 80% |
| 1D | dump | holdout | elsewhere | 13 | 31% | 85% | 3 | - | - | 8 | 12% |
| 1D | pump | 2022 - Oct 2025 | at a strong level | 175 | 59% | 75% | 34 | 74% | 21% | 64 | 70% |
| 1D | pump | 2022 - Oct 2025 | elsewhere | 96 | 58% | 74% | 23 | 74% | 17% | 30 | 70% |
| 1D | pump | holdout | at a strong level | 52 | 56% | 69% | 18 | 78% | 17% | 13 | 77% |
| 1D | pump | holdout | elsewhere | 13 | 38% | 62% | 4 | - | - | 2 | - |
| 4h | dump | 2022 - Oct 2025 | at a strong level | 822 | 57% | 72% | 197 | 75% | 18% | 252 | 70% |
| 4h | dump | 2022 - Oct 2025 | elsewhere | 757 | 55% | 72% | 159 | 64% | 24% | 223 | 66% |
| 4h | dump | holdout | at a strong level | 255 | 60% | 78% | 61 | 70% | 15% | 75 | 63% |
| 4h | dump | holdout | elsewhere | 201 | 60% | 79% | 48 | 52% | 38% | 57 | 75% |
| 4h | pump | 2022 - Oct 2025 | at a strong level | 853 | 58% | 76% | 194 | 69% | 20% | 273 | 67% |
| 4h | pump | 2022 - Oct 2025 | elsewhere | 803 | 62% | 77% | 201 | 75% | 17% | 268 | 72% |
| 4h | pump | holdout | at a strong level | 228 | 50% | 73% | 45 | 58% | 29% | 78 | 58% |
| 4h | pump | holdout | elsewhere | 163 | 56% | 72% | 37 | 73% | 14% | 50 | 66% |

### After the first test of the high, how did the range resolve?

| tf | move | period | first test | n | continued (close beyond the extreme) | reversed (close beyond the origin) | neither in 40 candles | candles to resolve (median) |
|---|---|---|---|---|---|---|---|---|
| 1D | dump | 2022 - Oct 2025 | sweep | 53 | 57% | 32% | 11% | 13.0 |
| 1D | dump | 2022 - Oct 2025 | touch | 78 | 71% | 23% | 6% | 13.0 |
| 1D | dump | 2022 - Oct 2025 | break | 28 | 100% | 0% | 0% | 6.0 |
| 1D | dump | 2022 - Oct 2025 | no pullback | 15 | 100% | 0% | 0% | 5.0 |
| 1D | dump | 2022 - Oct 2025 | pulled back, never tested | 62 | 0% | 89% | 11% | 12.0 |
| 1D | dump | holdout | sweep | 18 | 94% | 0% | 6% | 9.0 |
| 1D | dump | holdout | touch | 28 | 61% | 11% | 29% | 11.0 |
| 1D | dump | holdout | break | 6 | 100% | 0% | 0% | 4.5 |
| 1D | dump | holdout | no pullback | 8 | 100% | 0% | 0% | 4.0 |
| 1D | dump | holdout | pulled back, never tested | 10 | 0% | 90% | 10% | 9.0 |
| 1D | pump | 2022 - Oct 2025 | sweep | 57 | 74% | 19% | 7% | 8.0 |
| 1D | pump | 2022 - Oct 2025 | touch | 94 | 70% | 26% | 4% | 11.0 |
| 1D | pump | 2022 - Oct 2025 | break | 37 | 100% | 0% | 0% | 6.0 |
| 1D | pump | 2022 - Oct 2025 | no pullback | 14 | 100% | 0% | 0% | 5.5 |
| 1D | pump | 2022 - Oct 2025 | pulled back, never tested | 69 | 0% | 94% | 6% | 10.0 |
| 1D | pump | holdout | sweep | 22 | 73% | 23% | 5% | 11.0 |
| 1D | pump | holdout | touch | 15 | 73% | 20% | 7% | 12.0 |
| 1D | pump | holdout | break | 7 | 100% | 0% | 0% | 8.0 |
| 1D | pump | holdout | pulled back, never tested | 21 | 0% | 86% | 14% | 9.5 |
| 4h | dump | 2022 - Oct 2025 | sweep | 356 | 70% | 21% | 9% | 11.0 |
| 4h | dump | 2022 - Oct 2025 | touch | 475 | 68% | 23% | 9% | 13.0 |
| 4h | dump | 2022 - Oct 2025 | break | 189 | 100% | 0% | 0% | 7.0 |
| 4h | dump | 2022 - Oct 2025 | no pullback | 116 | 100% | 0% | 0% | 5.0 |
| 4h | dump | 2022 - Oct 2025 | pulled back, never tested | 443 | 0% | 90% | 10% | 9.0 |
| 4h | dump | holdout | sweep | 109 | 62% | 25% | 13% | 15.0 |
| 4h | dump | holdout | touch | 132 | 68% | 27% | 5% | 12.0 |
| 4h | dump | holdout | break | 78 | 100% | 0% | 0% | 6.0 |
| 4h | dump | holdout | no pullback | 39 | 100% | 0% | 0% | 5.0 |
| 4h | dump | holdout | pulled back, never tested | 98 | 0% | 94% | 6% | 10.0 |
| 4h | pump | 2022 - Oct 2025 | sweep | 395 | 72% | 19% | 9% | 11.0 |
| 4h | pump | 2022 - Oct 2025 | touch | 541 | 69% | 21% | 10% | 12.0 |
| 4h | pump | 2022 - Oct 2025 | break | 206 | 100% | 0% | 0% | 8.0 |
| 4h | pump | 2022 - Oct 2025 | no pullback | 126 | 100% | 0% | 0% | 4.0 |
| 4h | pump | 2022 - Oct 2025 | pulled back, never tested | 388 | 0% | 88% | 12% | 10.0 |
| 4h | pump | holdout | sweep | 82 | 65% | 22% | 13% | 10.0 |
| 4h | pump | holdout | touch | 128 | 61% | 29% | 10% | 11.0 |
| 4h | pump | holdout | break | 38 | 100% | 0% | 0% | 8.0 |
| 4h | pump | holdout | no pullback | 36 | 100% | 0% | 0% | 5.0 |
| 4h | pump | holdout | pulled back, never tested | 107 | 0% | 89% | 11% | 10.0 |

## ETH only

| tf | move | period | impulses | went sideways | continued at once | reversed at once | extreme tested before the range resolved | 90% low | 90% high | same for small legs (< 1.5 ATR) | control n | first test = sweep | = touch | = direct break | resolved up | resolved down | candles to the test (median) | retrace before the test (median share of the leg) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1D | dump | 2022 - Oct 2025 | 73 | 62% | 38% | 0% | 69% | 57% | 79% | 67% | 3 | 18% | 36% | 13% | 49% | 47% | 5.0 | 54% |
| 1D | dump | holdout | 20 | 45% | 55% | 0% | 67% | - | - | - | 0 | 22% | 33% | 11% | 44% | 33% | 4.0 | 36% |
| 1D | pump | 2022 - Oct 2025 | 93 | 55% | 45% | 0% | 82% | 73% | 91% | 100% | 3 | 18% | 37% | 20% | 69% | 31% | 6.0 | 51% |
| 1D | pump | holdout | 19 | 68% | 26% | 5% | 54% | - | - | - | 0 | 31% | 8% | 15% | 54% | 38% | 5.0 | 66% |
| 4h | dump | 2022 - Oct 2025 | 450 | 60% | 38% | 2% | 70% | 66% | 75% | 71% | 7 | 25% | 26% | 12% | 54% | 39% | 5.0 | 50% |
| 4h | dump | holdout | 117 | 63% | 36% | 1% | 80% | 72% | 87% | 75% | 4 | 31% | 30% | 11% | 61% | 32% | 5.0 | 42% |
| 4h | pump | 2022 - Oct 2025 | 497 | 56% | 41% | 2% | 79% | 75% | 82% | 79% | 14 | 25% | 35% | 11% | 62% | 29% | 5.0 | 48% |
| 4h | pump | holdout | 100 | 62% | 36% | 2% | 74% | 66% | 82% | 83% | 6 | 24% | 35% | 8% | 50% | 40% | 6.0 | 49% |

### Retest of the price (the impulse close), the midpoint and the origin

first = what happened first in the sideways (after the price moved away): the high was tested, the impulse close was retested, a break after a pullback, a continuation without any 1 ATR pullback, or neither (reversed / timed out).

| tf | move | period | sideways impulses | high tested first | close retested first | broke first | continued without a pullback | neither | close retested | held -> continued | closed below -> continued | never retested -> continued | midpoint retested | held -> continued | failed -> continued | origin retested | held -> continued | retest with RSI cooled >= 5 -> continued | n | RSI not cooled -> continued | n | continuations with RSI lower at the break than at the impulse |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1D | dump | 2022 - Oct 2025 | 45 | 44% | 24% | 9% | 2% | 20% | 47% | 64% | 40% | 46% | 84% | 44% | 45% | 27% | 17% | 33% | 9 | 67% | 12 | 27% |
| 1D | pump | 2022 - Oct 2025 | 51 | 31% | 41% | 12% | 0% | 16% | 53% | 80% | 75% | 58% | 73% | 71% | 22% | 18% | 33% | 75% | 12 | 80% | 15 | 37% |
| 1D | pump | holdout | 13 | 31% | 8% | 15% | 0% | 46% | 31% | - | - | 33% | 85% | 50% | - | 31% | - | - | 1 | - | 3 | 43% |
| 4h | dump | 2022 - Oct 2025 | 269 | 39% | 33% | 4% | 3% | 21% | 58% | 73% | 45% | 46% | 77% | 44% | 32% | 23% | 15% | 44% | 63 | 70% | 94 | 17% |
| 4h | dump | holdout | 74 | 46% | 34% | 5% | 5% | 9% | 65% | 65% | 59% | 58% | 69% | 54% | 21% | 23% | 12% | 59% | 17 | 65% | 31 | 20% |
| 4h | pump | 2022 - Oct 2025 | 280 | 44% | 29% | 7% | 5% | 15% | 55% | 71% | 58% | 59% | 72% | 54% | 30% | 25% | 32% | 56% | 62 | 71% | 92 | 26% |
| 4h | pump | holdout | 62 | 47% | 32% | 5% | 2% | 15% | 60% | 52% | 44% | 52% | 77% | 37% | 31% | 31% | 11% | 31% | 13 | 58% | 24 | 19% |

### Is the extreme at a strong S/R level (within 0.5 ATR)?  The sweep as an exit signal lives or dies here

| tf | move | period | extreme | sideways impulses | continued | extreme tested | sweeps | sweep -> continued | sweep -> reversed | touches | touch -> continued |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1D | dump | 2022 - Oct 2025 | at a strong level | 30 | 53% | 70% | 5 | 60% | 40% | 10 | 70% |
| 1D | dump | 2022 - Oct 2025 | elsewhere | 15 | 40% | 67% | 3 | - | - | 6 | 67% |
| 1D | pump | 2022 - Oct 2025 | at a strong level | 34 | 65% | 79% | 7 | 43% | 57% | 11 | 91% |
| 1D | pump | 2022 - Oct 2025 | elsewhere | 17 | 76% | 88% | 2 | - | - | 8 | 75% |
| 4h | dump | 2022 - Oct 2025 | at a strong level | 121 | 57% | 71% | 34 | 76% | 21% | 32 | 72% |
| 4h | dump | 2022 - Oct 2025 | elsewhere | 148 | 51% | 70% | 33 | 58% | 30% | 37 | 65% |
| 4h | dump | holdout | at a strong level | 41 | 54% | 76% | 14 | 86% | 0% | 12 | 42% |
| 4h | dump | holdout | elsewhere | 33 | 70% | 85% | 9 | 56% | 33% | 10 | 90% |
| 4h | pump | 2022 - Oct 2025 | at a strong level | 138 | 62% | 80% | 28 | 68% | 11% | 51 | 69% |
| 4h | pump | 2022 - Oct 2025 | elsewhere | 142 | 62% | 77% | 43 | 81% | 12% | 46 | 72% |
| 4h | pump | holdout | at a strong level | 28 | 54% | 75% | 7 | 57% | 43% | 9 | 67% |
| 4h | pump | holdout | elsewhere | 34 | 47% | 74% | 8 | 62% | 12% | 13 | 54% |

### After the first test of the high, how did the range resolve?

| tf | move | period | first test | n | continued (close beyond the extreme) | reversed (close beyond the origin) | neither in 40 candles | candles to resolve (median) |
|---|---|---|---|---|---|---|---|---|
| 1D | dump | 2022 - Oct 2025 | sweep | 8 | 50% | 38% | 12% | 12.0 |
| 1D | dump | 2022 - Oct 2025 | touch | 16 | 69% | 25% | 6% | 12.0 |
| 1D | dump | 2022 - Oct 2025 | break | 6 | 100% | 0% | 0% | 6.0 |
| 1D | dump | 2022 - Oct 2025 | pulled back, never tested | 14 | 0% | 100% | 0% | 9.0 |
| 1D | pump | 2022 - Oct 2025 | sweep | 9 | 56% | 44% | 0% | 9.0 |
| 1D | pump | 2022 - Oct 2025 | touch | 19 | 84% | 16% | 0% | 12.0 |
| 1D | pump | 2022 - Oct 2025 | break | 10 | 100% | 0% | 0% | 7.0 |
| 1D | pump | 2022 - Oct 2025 | pulled back, never tested | 9 | 0% | 100% | 0% | 10.0 |
| 1D | pump | holdout | pulled back, never tested | 6 | 0% | 83% | 17% | 7.0 |
| 4h | dump | 2022 - Oct 2025 | sweep | 67 | 67% | 25% | 7% | 11.0 |
| 4h | dump | 2022 - Oct 2025 | touch | 69 | 68% | 22% | 10% | 13.5 |
| 4h | dump | 2022 - Oct 2025 | break | 33 | 100% | 0% | 0% | 6.0 |
| 4h | dump | 2022 - Oct 2025 | no pullback | 20 | 100% | 0% | 0% | 4.0 |
| 4h | dump | 2022 - Oct 2025 | pulled back, never tested | 80 | 0% | 91% | 9% | 7.0 |
| 4h | dump | holdout | sweep | 23 | 74% | 13% | 13% | 11.0 |
| 4h | dump | holdout | touch | 22 | 64% | 32% | 5% | 14.0 |
| 4h | dump | holdout | break | 8 | 100% | 0% | 0% | 5.5 |
| 4h | dump | holdout | no pullback | 6 | 100% | 0% | 0% | 5.5 |
| 4h | dump | holdout | pulled back, never tested | 15 | 0% | 93% | 7% | 10.5 |
| 4h | pump | 2022 - Oct 2025 | sweep | 71 | 76% | 11% | 13% | 11.0 |
| 4h | pump | 2022 - Oct 2025 | touch | 97 | 70% | 20% | 10% | 13.0 |
| 4h | pump | 2022 - Oct 2025 | break | 30 | 100% | 0% | 0% | 8.0 |
| 4h | pump | 2022 - Oct 2025 | no pullback | 22 | 100% | 0% | 0% | 4.0 |
| 4h | pump | 2022 - Oct 2025 | pulled back, never tested | 60 | 0% | 90% | 10% | 12.0 |
| 4h | pump | holdout | sweep | 15 | 60% | 27% | 13% | 14.0 |
| 4h | pump | holdout | touch | 22 | 59% | 27% | 14% | 13.0 |
| 4h | pump | holdout | break | 5 | 100% | 0% | 0% | 8.0 |
| 4h | pump | holdout | pulled back, never tested | 16 | 0% | 94% | 6% | 8.0 |

## Same close position, impulse vs small leg (six coins, 2022 - Oct 2025)

If the test rate is the same at the same distance from the high, the concept is proximity, not the pump.

| tf | close below the extreme (ATR) | impulses | tested | small legs | tested | impulse resolved up | small leg resolved up |
|---|---|---|---|---|---|---|---|
| 4h | [0.0, 0.25) | 544 | 76% | 76 | 71% | 59% | 61% |
| 4h | [0.25, 0.5) | 992 | 74% | 74 | 66% | 60% | 59% |

## Reading

- **The extreme is tested first, mostly: yes.** After a pump of >= 2 ATR that goes sideways, the high is revisited (after a pullback of at least 1 ATR) before the range resolves in 75% of daily cases and 77% of 4h cases (90% intervals 69 - 80%), dumps 72 - 74%; the holdout agrees (68 - 86%). Small legs at the same distance test 56 - 74%, so part of it is proximity and part is the pump.
- **The test of the high is not the exit.** After a sweep (wick above the high, close back below) the range still resolves UP 70 - 74% of the time (daily pumps 74%, 4h 72%; holdout 65 - 73%); a touch 69 - 70%. At a strong S/R level it is the same (daily pumps 74%, 4h 69%). The 16 Dec 2024 sweep of 4,099 was the 1-in-5 case, not the rule. The exit study confirms it: exiting after a sweep of the trade's high earns +0.62R vs +0.88R.
- **The retest of the price is the key: supported.** The price comes back to the pump's close (after first trading 0.5 ATR above it) in about half the sideways cases. When that retest HOLDS (close no more than 0.25 ATR below) the range resolves up 72% (daily pumps) and 71% (4h); when it closes below, 55 - 56%; with no retest at all, 54 - 55%. Dumps mirror it (63 - 70% vs 42 - 48%). The holdout agrees (daily pumps 87% vs 30%, 4h 66% vs 46%). A held retest of the pump's close is the best continuation marker in this study.
- **RSI cooling at the retest does not help.** A retest with RSI at least 5 points below the impulse RSI continues 54 - 56%, one with RSI still warm 70 - 71%: the slow, cooled retest is the weaker one. In continuations the RSI at the break is lower than at the impulse only 25 - 30% of the time. So 'RSI 70 at 3,358, then RSI 60 with the price well above' is the minority picture; most continuations break with a higher RSI.
- **What it means for the bot:** hold through the sideways; do not exit on the test of the high; a held retest of the pump's close is the signal to stay (or to add); a failed retest (close below) is a coin flip. The 'pulled back, never tested -> reversed' row is true by construction (the only other way out of the range is down) and is not a finding.

Audit: round 29b, independent re-implementation of all 14,597 windows (six coins, 4h + 1D, both sides) with zero mismatches; one result-impacting issue found and fixed (the research rows included 2019 - 2021 data under a '2022 - Oct 2025' label; now filtered, shares moved by up to 4 points); tables reproduced after the fix.
