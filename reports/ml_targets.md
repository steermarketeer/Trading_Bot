# ML profit-taking: the target chosen per trade (never below 1.25:1)

Trades: the v3.1 strategy (626 trades 2022 - Oct 2026). Models learn from 16,534 main-rule trades + the v3.1 trades, walk-forward (each year scored by models that never saw it). **win % = profit after all costs** (market entry, limit target exit, market stop, actual funding).

Limit fills are conservative: price must trade 0.02% through the target.

## Results

| period | profit-taking | trades | win % | avg R per trade | profit factor | avg target |
|---|---|---|---|---|---|---|
| 2022-2025 (research, walk-forward) | fixed targets (v3.1: 2:1 breakouts, 3:1 bounces) | 520 | 47% | +0.41 | 1.74 | 2.37R |
| 2022-2025 (research, walk-forward) | liquidity rule: just before the next pool / zone (no ML) | 520 | 41% | +0.31 | 1.50 | 3.05R |
| 2022-2025 (research, walk-forward) | ML target (best expected R) | 520 | 46% | +0.35 | 1.61 | 2.43R |
| 2022-2025 (research, walk-forward) | ML target + skip trades with negative expected R | 426 | 44% | +0.32 | 1.54 | 2.54R |
| holdout Nov 2025 - Oct 2026 | fixed targets (v3.1: 2:1 breakouts, 3:1 bounces) | 106 | 52% | +0.58 | 2.14 | 2.42R |
| holdout Nov 2025 - Oct 2026 | liquidity rule: just before the next pool / zone (no ML) | 106 | 47% | +0.38 | 1.67 | 3.03R |
| holdout Nov 2025 - Oct 2026 | ML target (best expected R) | 106 | 45% | +0.35 | 1.60 | 2.55R |
| holdout Nov 2025 - Oct 2026 | ML target + skip trades with negative expected R | 92 | 46% | +0.41 | 1.71 | 2.69R |

## By year: fixed vs ML target

| period | trades | win % fixed | avg R fixed | win % ML | avg R ML |
|---|---|---|---|---|---|
| 2022 | 98 | 58% | +0.85 | 55% | +0.63 |
| 2023 | 164 | 40% | +0.20 | 38% | +0.18 |
| 2024 | 99 | 39% | +0.22 | 42% | +0.25 |
| 2025 | 159 | 50% | +0.48 | 50% | +0.40 |
| holdout | 106 | 52% | +0.58 | 45% | +0.35 |

## By setup

| period | setup | trades | win % fixed | avg R fixed | win % ML | avg R ML | avg ML target |
|---|---|---|---|---|---|---|---|
| research | 1D bounce | 193 | 37% | +0.34 | 41% | +0.31 | 2.78R |
| research | A+ breakout | 182 | 59% | +0.64 | 55% | +0.48 | 2.05R |
| research | breakout | 145 | 43% | +0.22 | 39% | +0.22 | 2.45R |
| holdout | 1D bounce | 44 | 45% | +0.55 | 45% | +0.61 | 2.81R |
| holdout | A+ breakout | 41 | 61% | +0.76 | 54% | +0.39 | 2.26R |
| holdout | breakout | 21 | 48% | +0.33 | 29% | -0.29 | 2.60R |

## Which targets the ML picks (trades per target)

| period | 1.25R | 1.5R | 2R | 2.5R | 3R | 4R |
|---|---|---|---|---|---|---|
| 2022 | 30 | 10 | 20 | 9 | 5 | 24 |
| 2023 | 21 | 14 | 31 | 15 | 26 | 57 |
| 2024 | 34 | 7 | 19 | 12 | 9 | 18 |
| 2025 | 44 | 34 | 6 | 19 | 24 | 32 |
| holdout | 14 | 13 | 15 | 17 | 27 | 20 |

## Is the model's probability honest? (chosen target, all periods out-of-sample)

| predicted chance | trades | avg predicted | actually reached |
|---|---|---|---|
| (0.0, 0.3] | 112 | 24% | 35% |
| (0.3, 0.4] | 150 | 35% | 37% |
| (0.4, 0.5] | 180 | 45% | 44% |
| (0.5, 0.6] | 121 | 55% | 46% |
| (0.6, 0.7] | 59 | 64% | 46% |
| (0.7, 1.0] | 4 | 71% | 0% |

## Account (A+ 4% risk, others 2%, max 5x, compounding)

| period | profit-taking | end / start | worst drop |
|---|---|---|---|
| research 2022-2025 | fixed targets (v3.1: 2:1 breakouts, 3:1 bounces) | 118.94x | -52% |
| research 2022-2025 | liquidity rule: just before the next pool / zone (no ML) | 25.88x | -74% |
| research 2022-2025 | ML target (best expected R) | 49.69x | -53% |
| research 2022-2025 | ML target + skip trades with negative expected R | 18.52x | -49% |
| holdout | fixed targets (v3.1: 2:1 breakouts, 3:1 bounces) | 4.77x | -24% |
| holdout | liquidity rule: just before the next pool / zone (no ML) | 2.37x | -30% |
| holdout | ML target (best expected R) | 2.39x | -36% |
| holdout | ML target + skip trades with negative expected R | 2.30x | -35% |

