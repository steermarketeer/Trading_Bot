# Strategy v2: filtered 2:1 breakouts (+ A+) and 1D 4th-test bounces (3:1)

Breakouts: certainty >= 7 on 2h / 4h / 1D, stop >= 0.6%, not the quietest 20% of markets, **BTC 4h trend agrees and 6h MACD agrees**. **A+** = also breaking into a low-volume zone (volume profile). Bounces: 1D zone tested 4+ times, confirmed bounce, 3:1. Every trade replayed on 5-minute candles; market-order costs. **win %** = trades closed in profit. Research 2022 - Oct 2025 (scored out-of-sample), holdout Nov 2025 on.

## Win % per trade

| period | setup | trades | win % | avg R after costs |
|---|---|---|---|---|
| 2022 | 1D 4th-test bounce (3:1) | 50 | 46% | +0.73 |
| 2022 | A+ breakout (2:1) | 34 | 76% | +1.20 |
| 2022 | ALL TRADES | 117 | 53% | +0.71 |
| 2022 | breakout (2:1) | 33 | 39% | +0.17 |
| 2023 | 1D 4th-test bounce (3:1) | 99 | 34% | +0.18 |
| 2023 | A+ breakout (2:1) | 64 | 42% | +0.23 |
| 2023 | ALL TRADES | 190 | 38% | +0.20 |
| 2023 | breakout (2:1) | 27 | 44% | +0.23 |
| 2024 | 1D 4th-test bounce (3:1) | 75 | 33% | +0.22 |
| 2024 | A+ breakout (2:1) | 25 | 48% | +0.32 |
| 2024 | ALL TRADES | 125 | 39% | +0.26 |
| 2024 | breakout (2:1) | 25 | 48% | +0.33 |
| 2025 | 1D 4th-test bounce (3:1) | 51 | 29% | +0.07 |
| 2025 | A+ breakout (2:1) | 59 | 68% | +0.91 |
| 2025 | ALL TRADES | 170 | 48% | +0.41 |
| 2025 | breakout (2:1) | 60 | 45% | +0.21 |
| holdout | 1D 4th-test bounce (3:1) | 61 | 39% | +0.36 |
| holdout | A+ breakout (2:1) | 41 | 61% | +0.74 |
| holdout | ALL TRADES | 123 | 48% | +0.48 |
| holdout | breakout (2:1) | 21 | 48% | +0.32 |
| 2022-25 total | 1D 4th-test bounce (3:1) | 275 | 35% | +0.27 |
| 2022-25 total | A+ breakout (2:1) | 182 | 58% | +0.64 |
| 2022-25 total | ALL TRADES | 602 | 44% | +0.37 |
| 2022-25 total | breakout (2:1) | 145 | 44% | +0.22 |
| holdout total | 1D 4th-test bounce (3:1) | 61 | 39% | +0.36 |
| holdout total | A+ breakout (2:1) | 41 | 61% | +0.74 |
| holdout total | ALL TRADES | 123 | 48% | +0.48 |
| holdout total | breakout (2:1) | 21 | 48% | +0.32 |

Trades per week: research 3.0, holdout 2.6.

## Account (compounding, overlapping positions, leverage cap 5x)

| period | risk per trade | end equity | winning weeks* | winning months | avg week | avg month | weeks >= +20% | max drawdown |
|---|---|---|---|---|---|---|---|---|
| 2022-25 | flat 2% | 30.33x | 45% | 64% | +2.1% | +8.5% | 8% | -45% |
| 2022-25 | flat 3% | 87.85x | 46% | 62% | +3.1% | +12.4% | 12% | -61% |
| 2022-25 | tiered: A+ 4%, others 2% | 122.60x | 45% | 56% | +3.1% | +13.3% | 12% | -59% |
| 2022-25 | tiered: A+ 5%, breakout 3%, bounce 2% | 245.71x | 47% | 60% | +3.8% | +16.2% | 14% | -62% |
| holdout | flat 2% | 2.75x | 53% | 82% | +2.2% | +8.7% | 2% | -19% |
| holdout | flat 3% | 4.13x | 53% | 73% | +3.4% | +13.2% | 8% | -28% |
| holdout | tiered: A+ 4%, others 2% | 4.40x | 53% | 82% | +3.2% | +11.9% | 10% | -27% |
| holdout | tiered: A+ 5%, breakout 3%, bounce 2% | 5.64x | 50% | 82% | +3.8% | +13.9% | 10% | -33% |

*weeks in which at least one trade closed.

