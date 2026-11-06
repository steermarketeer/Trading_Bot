# Self-review with the precise definitions

367 v3.1 ETH trades, one position per move (200 losers). **win % = profit after costs.** Definitions: docs/trading_definitions.md. A pattern marks losers only if the win % with it is clearly lower in BOTH periods.

## Each pattern

| pattern | period | trades with it | in losers | in winners | win % with | win % without | avg R with | avg R without |
|---|---|---|---|---|---|---|---|---|
| Rejected (4h) at the resistance between entry and target | 2022 - Oct 2025 | 188 | 72% | 53% | 37% | 57% | +0.29 | +0.73 |
| Rejected (4h) at the resistance between entry and target | holdout | 46 | 67% | 63% | 48% | 52% | +0.55 | +0.56 |
| 3+ rejections / failed pushes at that resistance | 2022 - Oct 2025 | 128 | 50% | 35% | 36% | 51% | +0.29 | +0.57 |
| 3+ rejections / failed pushes at that resistance | holdout | 28 | 44% | 34% | 43% | 53% | +0.50 | +0.59 |
| Failed pushes each lower than the last | 2022 - Oct 2025 | 1 | 1% | 0% | 0% | 45% | -1.04 | +0.45 |
| Failed pushes each lower than the last | holdout | 0 | 0% | 0% | - | 49% |  | +0.56 |
| Confirmed 1h double / triple top against the trade, before entry | 2022 - Oct 2025 | 4 | 1% | 2% | 50% | 45% | +0.93 | +0.44 |
| Confirmed 1h double / triple top against the trade, before entry | holdout | 1 | 3% | 0% | 0% | 50% | -1.02 | +0.58 |
| Untaken equal highs (double / triple top) between entry and target | 2022 - Oct 2025 | 136 | 51% | 39% | 38% | 50% | +0.35 | +0.53 |
| Untaken equal highs (double / triple top) between entry and target | holdout | 29 | 56% | 26% | 31% | 62% | +0.11 | +0.86 |
| Untaken equal lows within 0.5R beyond the stop | 2022 - Oct 2025 | 50 | 13% | 21% | 56% | 42% | +0.64 | +0.41 |
| Untaken equal lows within 0.5R beyond the stop | holdout | 10 | 8% | 20% | 70% | 46% | +1.19 | +0.45 |
| 15m double / triple top after entry, confirmed (neckline close) | 2022 - Oct 2025 | 225 | 88% | 61% | 36% | 72% | +0.23 | +1.13 |
| 15m double / triple top after entry, confirmed (neckline close) | holdout | 54 | 86% | 66% | 43% | 71% | +0.39 | +1.09 |

## Marks losers in both periods

- 3+ rejections / failed pushes at that resistance
- Untaken equal highs (double / triple top) between entry and target
- 15m double / triple top after entry, confirmed (neckline close)


## How selective the markers are (a marker that also flags most winners explains nothing)

- earlier markers (EMA 200 in the way, falling 4h highs, second try, no 4h confirmation): flag 159 of 200 losers and 83 of 167 winners
- new markers above: flag 188 of 200 losers and 122 of 167 winners
- either: 199 losers and 139 winners

