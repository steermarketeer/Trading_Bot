# Repeated tests of support / resistance: break or massive reversal?

*Break* = a close beyond the level by >= 0.5 ATR. *Massive reversal* = price moves >= 3 ATR away from the level in the bounce direction first. Looked at up to 40 candles ahead. Tests of the same zone are counted over the previous 300 candles.

## 2h chart

### What happens at the Nth test of a level

| test of the level | tests | held at close | all: then BROKE | all: then MASSIVE REVERSAL | if held: then BROKE | if held: then MASSIVE REVERSAL |
|---|---|---|---|---|---|---|
| 1st | 325 | 58% | 69% | 30% | 58% | 40% |
| 2nd | 302 | 70% | 61% | 37% | 51% | 46% |
| 3rd | 285 | 72% | 62% | 34% | 53% | 41% |
| 4th | 260 | 70% | 62% | 34% | 51% | 45% |
| 5th | 250 | 70% | 59% | 37% | 54% | 43% |
| 6th-7th | 466 | 69% | 66% | 31% | 56% | 40% |
| 8th+ | 3040 | 70% | 67% | 31% | 59% | 38% |

### After failed breakouts (closed through, then back within 3 candles)

| earlier failed breaks of this level | tests | then BROKE | then MASSIVE REVERSAL |
|---|---|---|---|
| 0 | 1993 | 65% | 32% |
| 1 | 1026 | 65% | 31% |
| 2 | 772 | 66% | 31% |
| 3+ | 1137 | 66% | 32% |

### Trading the bounce (confirmed by the next candle)

Win % = profit after costs; avg R after costs.

| trades | period | n | win 1:1 | win 1.5:1 | win 2:1 | win 3:1 | avg R 1:1 | avg R 1.5:1 | avg R 2:1 | avg R 3:1 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1st-3rd test | research | 311 | 52% | 43% | 38% | 32% | -0.06 | -0.04 | +0.00 | +0.04 |
| 1st-3rd test | holdout | 43 | 40% | 26% | 21% | 21% | -0.31 | -0.47 | -0.55 | -0.54 |
| 4th+ test | research | 1434 | 50% | 41% | 36% | 29% | -0.12 | -0.10 | -0.06 | -0.06 |
| 4th+ test | holdout | 268 | 50% | 41% | 37% | 32% | -0.14 | -0.14 | -0.07 | -0.04 |
| 4th+ test, after >= 1 failed break | research | 1027 | 50% | 41% | 36% | 29% | -0.13 | -0.11 | -0.08 | -0.08 |
| 4th+ test, after >= 1 failed break | holdout | 195 | 52% | 42% | 38% | 34% | -0.10 | -0.11 | -0.04 | +0.04 |
| any test, after >= 2 failed breaks | research | 665 | 51% | 42% | 36% | 29% | -0.11 | -0.11 | -0.08 | -0.07 |
| any test, after >= 2 failed breaks | holdout | 113 | 49% | 39% | 36% | 31% | -0.18 | -0.19 | -0.08 | -0.05 |

## 4h chart

### What happens at the Nth test of a level

| test of the level | tests | held at close | all: then BROKE | all: then MASSIVE REVERSAL | if held: then BROKE | if held: then MASSIVE REVERSAL |
|---|---|---|---|---|---|---|
| 1st | 270 | 61% | 70% | 28% | 60% | 37% |
| 2nd | 265 | 68% | 67% | 31% | 54% | 43% |
| 3rd | 235 | 71% | 60% | 34% | 53% | 41% |
| 4th | 222 | 68% | 63% | 31% | 51% | 40% |
| 5th | 212 | 70% | 71% | 26% | 63% | 34% |
| 6th-7th | 372 | 69% | 68% | 28% | 59% | 36% |
| 8th+ | 1910 | 69% | 67% | 30% | 58% | 38% |

### After failed breakouts (closed through, then back within 3 candles)

| earlier failed breaks of this level | tests | then BROKE | then MASSIVE REVERSAL |
|---|---|---|---|
| 0 | 1628 | 65% | 31% |
| 1 | 631 | 70% | 26% |
| 2 | 629 | 68% | 29% |
| 3+ | 598 | 65% | 34% |

### Trading the bounce (confirmed by the next candle)

Win % = profit after costs; avg R after costs.

| trades | period | n | win 1:1 | win 1.5:1 | win 2:1 | win 3:1 | avg R 1:1 | avg R 1.5:1 | avg R 2:1 | avg R 3:1 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1st-3rd test | research | 260 | 54% | 47% | 42% | 37% | +0.01 | +0.09 | +0.13 | +0.20 |
| 1st-3rd test | holdout | 43 | 53% | 42% | 33% | 28% | +0.00 | +0.01 | -0.06 | -0.01 |
| 4th+ test | research | 961 | 52% | 43% | 36% | 30% | -0.06 | -0.04 | -0.04 | -0.02 |
| 4th+ test | holdout | 186 | 41% | 34% | 29% | 25% | -0.26 | -0.25 | -0.23 | -0.15 |
| 4th+ test, after >= 1 failed break | research | 633 | 52% | 43% | 36% | 30% | -0.07 | -0.04 | -0.07 | -0.01 |
| 4th+ test, after >= 1 failed break | holdout | 124 | 44% | 35% | 31% | 27% | -0.23 | -0.22 | -0.21 | -0.14 |
| any test, after >= 2 failed breaks | research | 417 | 54% | 45% | 38% | 32% | -0.01 | -0.00 | -0.01 | +0.03 |
| any test, after >= 2 failed breaks | holdout | 66 | 44% | 39% | 32% | 29% | -0.23 | -0.12 | -0.17 | -0.07 |

## 1D chart

### What happens at the Nth test of a level

| test of the level | tests | held at close | all: then BROKE | all: then MASSIVE REVERSAL | if held: then BROKE | if held: then MASSIVE REVERSAL |
|---|---|---|---|---|---|---|
| 1st | 144 | 68% | 76% | 23% | 68% | 31% |
| 2nd | 136 | 65% | 69% | 27% | 62% | 33% |
| 3rd | 130 | 65% | 71% | 26% | 62% | 35% |
| 4th | 111 | 68% | 66% | 32% | 54% | 45% |
| 5th | 108 | 69% | 69% | 28% | 67% | 29% |
| 6th-7th | 172 | 67% | 66% | 33% | 57% | 40% |
| 8th+ | 611 | 66% | 69% | 30% | 59% | 40% |

### After failed breakouts (closed through, then back within 3 candles)

| earlier failed breaks of this level | tests | then BROKE | then MASSIVE REVERSAL |
|---|---|---|---|
| 0 | 776 | 71% | 27% |
| 1 | 246 | 63% | 35% |
| 2 | 178 | 70% | 27% |
| 3+ | 212 | 68% | 32% |

### Trading the bounce (confirmed by the next candle)

Win % = profit after costs; avg R after costs.

| trades | period | n | win 1:1 | win 1.5:1 | win 2:1 | win 3:1 | avg R 1:1 | avg R 1.5:1 | avg R 2:1 | avg R 3:1 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1st-3rd test | research | 126 | 50% | 38% | 32% | 26% | -0.03 | -0.08 | -0.10 | -0.03 |
| 1st-3rd test | holdout | 15 | 60% | 53% | 53% | 47% | +0.17 | +0.22 | +0.46 | +0.39 |
| 4th+ test | research | 334 | 56% | 48% | 41% | 37% | +0.10 | +0.15 | +0.18 | +0.35 |
| 4th+ test | holdout | 61 | 59% | 51% | 43% | 39% | +0.14 | +0.23 | +0.20 | +0.36 |
| 4th+ test, after >= 1 failed break | research | 204 | 57% | 49% | 44% | 40% | +0.10 | +0.18 | +0.24 | +0.45 |
| 4th+ test, after >= 1 failed break | holdout | 43 | 60% | 51% | 42% | 40% | +0.17 | +0.24 | +0.16 | +0.36 |
| any test, after >= 2 failed breaks | research | 124 | 56% | 48% | 44% | 38% | +0.07 | +0.13 | +0.22 | +0.32 |
| any test, after >= 2 failed breaks | holdout | 21 | 48% | 48% | 43% | 33% | -0.09 | +0.15 | +0.24 | +0.29 |

