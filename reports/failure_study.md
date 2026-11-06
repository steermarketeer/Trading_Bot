# Failure study of the chosen version (bounces 5 : 1)

162 ETH trades: 129 in 2022 - Oct 2025, 33 in the holdout. **win % = profit after costs.** For every candidate reason: how many losers vs winners carry it, win % with vs without, Fisher's exact test on 2022-25 (one-sided: the reason lowers the win %), and the holdout. **holds** = p < 0.05 and the holdout agrees; 162 trades show direction, not proof.

## Each reason, across all trades

| reason | period | losers with it | winners with it | trades with it | win % with | avg R with | win % without | avg R without | total R of those trades | p (research) | holds out |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ceiling | 2022 - Oct 2025 | 88% | 79% | 107 | 54% | +0.86 | 68% | +0.96 | +92.30 | 0.167 |  |
| ceiling | holdout | 100% | 90% | 31 | 61% | +1.10 | 100% | +1.94 | +34.20 |  |  |
| trendline | 2022 - Oct 2025 | 43% | 40% | 53 | 55% | +0.99 | 58% | +0.80 | +52.72 | 0.429 |  |
| trendline | holdout | 42% | 52% | 16 | 69% | +1.51 | 59% | +0.82 | +24.08 |  |  |
| daily against | 2022 - Oct 2025 | 41% | 36% | 49 | 53% | +0.61 | 59% | +1.05 | +29.88 | 0.326 |  |
| daily against | holdout | 67% | 48% | 18 | 56% | +0.87 | 73% | +1.50 | +15.63 |  |  |
| weekly no room | 2022 - Oct 2025 | 14% | 16% | 20 | 60% | +1.14 | 56% | +0.83 | +22.87 | 0.717 |  |
| weekly no room | holdout | 8% | 0% | 1 | 0% | -1.02 | 66% | +1.22 | -1.02 |  |  |
| vol shock | 2022 - Oct 2025 | 34% | 49% | 55 | 65% | +0.84 | 50% | +0.91 | +46.01 | 0.974 |  |
| vol shock | holdout | 50% | 43% | 15 | 60% | +0.74 | 67% | +1.50 | +11.08 |  |  |
| liq at stop | 2022 - Oct 2025 | 52% | 45% | 62 | 53% | +0.75 | 60% | +1.00 | +46.35 | 0.287 |  |
| liq at stop | holdout | 58% | 48% | 17 | 59% | +1.12 | 69% | +1.19 | +19.05 |  |  |
| stretched | 2022 - Oct 2025 | 41% | 56% | 64 | 64% | +0.86 | 49% | +0.90 | +55.03 | 0.970 |  |
| stretched | holdout | 58% | 62% | 20 | 65% | +0.78 | 62% | +1.74 | +15.52 |  |  |
| vertical day | 2022 - Oct 2025 | 2% | 3% | 3 | 67% | +0.90 | 56% | +0.88 | +2.71 | 0.822 |  |
| vertical day | holdout | 0% | 0% | 0 | - |  | 64% | +1.15 | +0.00 |  |  |
| pause against | 2022 - Oct 2025 | 12% | 5% | 11 | 36% | -0.00 | 58% | +0.96 | -0.04 | 0.137 |  |
| pause against | holdout | 0% | 24% | 5 | 100% | +1.94 | 57% | +1.01 | +9.69 |  |  |
| top failure against | 2022 - Oct 2025 | 0% | 4% | 3 | 100% | +1.95 | 56% | +0.85 | +5.85 | 1.000 |  |
| top failure against | holdout | 0% | 0% | 0 | - |  | 64% | +1.15 | +0.00 |  |  |
| 3 failures against | 2022 - Oct 2025 | 4% | 8% | 8 | 75% | +1.71 | 55% | +0.83 | +13.65 | 0.931 |  |
| 3 failures against | holdout | 8% | 14% | 4 | 75% | +1.07 | 62% | +1.17 | +4.27 |  |  |
| weak break | 2022 - Oct 2025 | 21% | 23% | 29 | 59% | +0.67 | 56% | +0.94 | +19.56 | 0.677 |  |
| weak break | holdout | 33% | 10% | 6 | 33% | -0.12 | 70% | +1.44 | -0.73 |  |  |
| 4h against | 2022 - Oct 2025 | 55% | 25% | 49 | 37% | +0.28 | 69% | +1.25 | +13.53 | 0.000 | yes |
| 4h against | holdout | 50% | 38% | 14 | 57% | +1.02 | 68% | +1.25 | +14.34 |  | yes |
| gave back | 2022 - Oct 2025 | 36% | 0% | 20 | 0% | -1.11 | 67% | +1.24 | -22.14 | 0.000 | yes |
| gave back | holdout | 33% | 0% | 4 | 0% | -1.14 | 72% | +1.47 | -4.56 |  | yes |

## No entry-time reason holds out in both periods.

## Every loss, with its reasons (for the discussion)

| entry | setup | side | R | exit | reasons at entry | after entry |
|---|---|---|---|---|---|---|
| 2023-12-05 00:00 | 1D bounce | long | -1.29 | stop | ceiling, weekly no room, liq at stop | 4h against, gave back |
| 2024-11-22 00:00 | 1D bounce | long | -1.29 | stop | ceiling, weekly no room | gave back |
| 2023-03-27 16:00 | breakout | short | -1.24 | stop | ceiling, daily against, vol shock, stretched, pause against, weak break | - |
| 2026-07-11 16:00 | A+ breakout | long | -1.22 | stop | ceiling, trendline, daily against, liq at stop, weak break | gave back |
| 2026-05-07 16:00 | breakout | short | -1.21 | stop | ceiling, stretched, 3 failures against, weak break | 4h against, gave back |
| 2023-12-05 18:00 | A+ breakout | long | -1.21 | stop | weekly no room, vol shock, stretched | 4h against |
| 2023-06-10 08:00 | A+ breakout | short | -1.18 | stop | ceiling, daily against, stretched, weak break | 4h against, gave back |
| 2024-03-25 16:00 | breakout | long | -1.16 | stop | ceiling, weekly no room, stretched, pause against | gave back |
| 2022-04-25 02:00 | A+ breakout | short | -1.16 | stop | ceiling, vol shock, stretched | 4h against, gave back |
| 2022-04-25 08:00 | A+ breakout | short | -1.14 | stop | ceiling | 4h against |
| 2023-04-05 00:00 | 1D bounce | long | -1.13 | stop | ceiling, trendline | gave back |
| 2026-01-02 18:00 | breakout | long | -1.13 | stop | ceiling, daily against, vol shock, stretched, weak break | - |
| 2023-04-11 00:00 | 1D bounce | long | -1.12 | stop | ceiling | gave back |
| 2024-11-03 04:00 | breakout | short | -1.12 | stop | ceiling, trendline, liq at stop, weak break | 4h against, gave back |
| 2026-01-05 02:00 | A+ breakout | long | -1.11 | stop | ceiling, trendline, daily against, vol shock, liq at stop, stretched | 4h against |
| 2022-08-25 08:00 | breakout | long | -1.11 | stop | ceiling, trendline, daily against, weak break | - |
| 2022-11-08 06:00 | A+ breakout | short | -1.11 | stop | vol shock, stretched, pause against, weak break | 4h against |
| 2023-03-18 00:00 | A+ breakout | long | -1.11 | stop | trendline, stretched, weak break | gave back |
| 2025-12-17 18:00 | breakout | short | -1.11 | stop | ceiling | gave back |
| 2024-06-14 18:00 | A+ breakout | short | -1.11 | stop | trendline, daily against, stretched | 4h against |
| 2022-11-02 20:00 | breakout | short | -1.11 | stop | ceiling, trendline, vol shock, pause against, weak break | gave back |
| 2023-02-02 04:00 | A+ breakout | long | -1.10 | stop | ceiling, trendline, weekly no room, weak break | 4h against, gave back |
| 2022-10-24 00:00 | breakout | long | -1.09 | stop | ceiling, daily against, vol shock, liq at stop, stretched | 4h against |
| 2024-09-13 16:00 | breakout | long | -1.09 | stop | ceiling, daily against, vol shock, liq at stop, pause against | gave back |
| 2024-04-12 20:00 | A+ breakout | short | -1.09 | stop | daily against, vol shock, stretched, weak break | 4h against, gave back |
| 2024-09-23 04:00 | breakout | long | -1.09 | stop | ceiling, trendline, daily against, stretched | 4h against |
| 2024-05-22 00:00 | 1D bounce | long | -1.09 | stop | ceiling, liq at stop | - |
| 2025-01-27 08:00 | A+ breakout | short | -1.08 | stop | daily against, vol shock, stretched, weak break | - |
| 2022-03-17 00:00 | 1D bounce | long | -1.08 | stop | ceiling, daily against | 4h against, gave back |
| 2023-05-05 16:00 | A+ breakout | long | -1.08 | stop | ceiling, vol shock, liq at stop, stretched, weak break | gave back |
| 2026-03-13 14:00 | A+ breakout | long | -1.08 | stop | ceiling, daily against, vol shock, liq at stop, stretched | 4h against |
| 2025-10-27 00:00 | breakout | long | -1.08 | stop | ceiling, liq at stop | - |
| 2026-01-14 00:00 | A+ breakout | long | -1.08 | stop | ceiling, daily against, vol shock, liq at stop, stretched, weak break | - |
| 2026-04-14 00:00 | A+ breakout | long | -1.07 | stop | ceiling, trendline, daily against, vol shock, stretched | 4h against |
| 2023-07-13 18:00 | A+ breakout | long | -1.07 | stop | ceiling, vol shock, stretched | - |
| 2024-01-11 00:00 | A+ breakout | long | -1.07 | stop | weekly no room, vol shock, liq at stop, stretched | - |
| 2023-03-22 20:00 | breakout | short | -1.07 | stop | ceiling, trendline, daily against, vol shock, stretched, pause against | 4h against |
| 2023-02-22 16:00 | breakout | short | -1.06 | stop | ceiling, daily against, liq at stop | 4h against |
| 2024-10-29 00:00 | 1D bounce | long | -1.06 | stop | ceiling, trendline, daily against, liq at stop | gave back |
| 2025-06-06 00:00 | breakout | short | -1.05 | stop | ceiling, vol shock | 4h against |
| 2026-04-08 00:00 | A+ breakout | long | -1.05 | stop | ceiling, trendline, daily against, vol shock, stretched | 4h against |
| 2023-04-14 00:00 | 1D bounce | long | -1.05 | stop | ceiling, liq at stop | - |
| 2025-01-16 00:00 | 1D bounce | long | -1.05 | stop | ceiling, liq at stop | 4h against |
| 2025-03-19 12:00 | breakout | long | -1.05 | stop | ceiling, daily against, vol shock, liq at stop, stretched, pause against | - |
| 2025-01-13 12:00 | A+ breakout | short | -1.04 | stop | ceiling, daily against, vol shock, stretched | gave back |
| 2024-07-20 00:00 | 1D bounce | long | -1.04 | stop | ceiling, trendline | 4h against |
| 2025-10-11 00:00 | A+ breakout | short | -1.04 | stop | ceiling, daily against, vol shock, vertical day, weak break | - |
| 2024-09-24 00:00 | 1D bounce | long | -1.03 | stop | ceiling, trendline, daily against, liq at stop | 4h against |
| 2023-10-02 00:00 | 1D bounce | long | -1.03 | stop | ceiling, trendline, vol shock, liq at stop, stretched | 4h against |
| 2025-06-10 00:00 | 1D bounce | long | -1.03 | stop | ceiling, trendline, liq at stop, stretched | - |
| 2023-09-22 00:00 | 1D bounce | short | -1.03 | stop | ceiling, trendline, weekly no room, liq at stop | 4h against |
| 2025-01-20 00:00 | 1D bounce | short | -1.03 | stop | ceiling, daily against | 4h against |
| 2023-10-10 00:00 | 1D bounce | short | -1.02 | stop | ceiling, trendline, liq at stop | 4h against, gave back |
| 2025-01-14 00:00 | 1D bounce | short | -1.02 | stop | ceiling, daily against, vol shock, liq at stop | 4h against |
| 2023-10-13 00:00 | 1D bounce | short | -1.02 | stop | ceiling, trendline, liq at stop | - |
| 2026-06-25 00:00 | 1D bounce | short | -1.02 | stop | ceiling, weekly no room, liq at stop | gave back |
| 2026-03-05 00:00 | 1D bounce | long | -1.01 | stop | ceiling, trendline, daily against, liq at stop | 4h against |
| 2024-11-05 00:00 | 1D bounce | short | -1.01 | stop | ceiling, liq at stop | 4h against |
| 2025-10-18 00:00 | 1D bounce | short | -1.01 | stop | ceiling, trendline, daily against, liq at stop | 4h against |
| 2025-06-23 00:00 | 1D bounce | short | -1.01 | stop | ceiling, trendline, liq at stop | 4h against |
| 2024-07-05 00:00 | 1D bounce | short | -1.00 | stop | ceiling, trendline, liq at stop, stretched | - |
| 2024-08-28 00:00 | A+ breakout | short | -0.99 | stop | ceiling, trendline, liq at stop, stretched | 4h against, gave back |
| 2024-05-09 00:00 | 1D bounce | short | -0.99 | stop | ceiling, trendline, daily against, liq at stop | 4h against |
| 2022-12-17 00:00 | 1D bounce | short | -0.98 | stop | ceiling, liq at stop | 4h against |
| 2024-05-02 00:00 | 1D bounce | short | -0.98 | stop | ceiling, trendline, daily against, liq at stop, 3 failures against | - |
| 2024-06-25 00:00 | 1D bounce | short | -0.92 | stop | ceiling, trendline, daily against, liq at stop, 3 failures against | 4h against, gave back |
| 2026-06-04 00:00 | 1D bounce | short | -0.39 | time | ceiling, liq at stop | - |
| 2025-03-10 18:00 | A+ breakout | short | -0.26 | time | ceiling, weekly no room, stretched | - |

Audit: pending.
