# Three failures at the same cap -> trade the other side

Six coins, 15m and 1h, mirrored. **win % = profit after costs.** Fair test = 1.5 ATR either way (50% = coin flip), 90% interval by a bootstrap of calendar months. Research 2020 - Oct 2025, holdout Nov 2025 on.

| timeframe | trigger: close below | target | side | trades 2020-25 | win % | avg R | median reward:risk | fair test | 90% low | 90% high | holdout trades | holdout win % | holdout avg R |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1h | last push | 2R | short (failures to go up) | 10395 | 34% | -0.12 | 2.0 | 51% | 49% | 52% | 1853 | 34% | -0.15 |
| 1h | last push | 2R | long (failures to go down) | 9846 | 35% | -0.11 | 2.0 | 50% | 49% | 51% | 1770 | 33% | -0.21 |
| 1h | last push | 2R | both | 20241 | 35% | -0.11 | 2.0 | 50% | 50% | 51% | 3623 | 34% | -0.18 |
| 1h | last push | liquidity | short (failures to go up) | 10395 | 33% | -0.16 | 2.0 | 51% | 49% | 52% | 1853 | 34% | -0.16 |
| 1h | last push | liquidity | long (failures to go down) | 9846 | 34% | -0.13 | 2.0 | 50% | 49% | 51% | 1770 | 31% | -0.24 |
| 1h | last push | liquidity | both | 20241 | 33% | -0.14 | 2.0 | 50% | 50% | 51% | 3623 | 32% | -0.20 |
| 1h | neckline | 2R | short (failures to go up) | 5776 | 35% | -0.09 | 2.0 | 50% | 49% | 51% | 1039 | 37% | -0.06 |
| 1h | neckline | 2R | long (failures to go down) | 5911 | 37% | -0.07 | 2.0 | 49% | 48% | 50% | 1009 | 34% | -0.18 |
| 1h | neckline | 2R | both | 11687 | 36% | -0.08 | 2.0 | 50% | 49% | 50% | 2048 | 36% | -0.12 |
| 1h | neckline | liquidity | short (failures to go up) | 5776 | 36% | -0.11 | 2.0 | 50% | 49% | 51% | 1039 | 38% | -0.07 |
| 1h | neckline | liquidity | long (failures to go down) | 5911 | 37% | -0.08 | 2.0 | 49% | 48% | 50% | 1009 | 34% | -0.21 |
| 1h | neckline | liquidity | both | 11687 | 36% | -0.09 | 2.0 | 50% | 49% | 50% | 2048 | 36% | -0.14 |
| 15m | last push | 2R | short (failures to go up) | 41302 | 34% | -0.23 | 2.0 | 50% | 50% | 51% | 7254 | 33% | -0.31 |
| 15m | last push | 2R | long (failures to go down) | 39473 | 33% | -0.25 | 2.0 | 49% | 48% | 50% | 6915 | 32% | -0.38 |
| 15m | last push | 2R | both | 80775 | 34% | -0.24 | 2.0 | 50% | 49% | 50% | 14169 | 32% | -0.34 |
| 15m | last push | liquidity | short (failures to go up) | 41302 | 28% | -0.29 | 3.2 | 50% | 50% | 51% | 7254 | 29% | -0.30 |
| 15m | last push | liquidity | long (failures to go down) | 39473 | 29% | -0.27 | 2.8 | 49% | 48% | 50% | 6915 | 27% | -0.41 |
| 15m | last push | liquidity | both | 80775 | 29% | -0.28 | 3.0 | 50% | 49% | 50% | 14169 | 28% | -0.36 |
| 15m | neckline | 2R | short (failures to go up) | 23081 | 34% | -0.17 | 2.0 | 50% | 49% | 51% | 4008 | 37% | -0.16 |
| 15m | neckline | 2R | long (failures to go down) | 23192 | 35% | -0.18 | 2.0 | 48% | 48% | 49% | 3846 | 34% | -0.28 |
| 15m | neckline | 2R | both | 46273 | 35% | -0.18 | 2.0 | 49% | 49% | 50% | 7854 | 35% | -0.22 |
| 15m | neckline | liquidity | short (failures to go up) | 23081 | 33% | -0.21 | 2.3 | 50% | 49% | 51% | 4008 | 35% | -0.17 |
| 15m | neckline | liquidity | long (failures to go down) | 23192 | 34% | -0.20 | 2.1 | 48% | 48% | 49% | 3846 | 32% | -0.30 |
| 15m | neckline | liquidity | both | 46273 | 33% | -0.20 | 2.2 | 49% | 49% | 50% | 7854 | 34% | -0.23 |

Funding is included for ETH only (no funding data for the other coins).

Audit: round 21, no result-impacting issue.
