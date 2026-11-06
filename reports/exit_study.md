# Exit study on the chosen version

Same 162 trades, entries, initial stops, replay, costs and funding; only the exit changes. **win % = profit after costs.** Chosen on 2022 - Oct 2025 (best t-score, >= 3 of 4 good years); the holdout is shown once.

Check: the 'fixed' rows reproduce the chosen version's trades to 0.00e+00 R.

## all trades

Chosen on 2022-25 (t-score): **half at +2R, rest to break-even and run**; most profit on 2022-25: **break-even after +2R**

| exit | trades | win % | avg R | profit factor | t-score | good years /4 | account 2022-25 | worst drop | avg hold (days) | holdout win % | holdout avg R | holdout account | holdout drop |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| fixed target (as now) | 129 | 57% | +0.88 | 2.91 | 5.15 | 4 | 19.33x | -16% | 12.0 | 64% | +1.15 | 2.47x | -13% |
| break-even after +1R | 129 | 42% | +0.71 | 3.25 | 4.65 | 4 | 11.97x | -11% | 9.4 | 58% | +1.16 | 2.39x | -11% |
| break-even after +1.5R | 129 | 50% | +0.81 | 3.00 | 4.88 | 4 | 14.64x | -14% | 11.0 | 64% | +1.16 | 2.48x | -13% |
| break-even after +2R | 129 | 57% | +0.92 | 3.18 | 5.46 | 4 | 21.20x | -14% | 11.6 | 64% | +1.15 | 2.46x | -13% |
| exit on the first 4h close against the entry | 129 | 43% | +0.67 | 3.19 | 4.66 | 4 | 10.36x | -22% | 6.5 | 42% | +0.68 | 1.73x | -10% |
| Chandelier 2 ATR (after +1R) | 129 | 60% | +0.80 | 3.03 | 5.37 | 4 | 17.28x | -14% | 6.3 | 67% | +1.14 | 2.46x | -13% |
| Chandelier 3 ATR (after +1R) | 129 | 59% | +0.82 | 2.97 | 5.17 | 4 | 17.65x | -14% | 8.5 | 67% | +1.20 | 2.54x | -13% |
| trail below the last 4h swing low (after +1R) | 129 | 60% | +0.73 | 2.89 | 5.32 | 4 | 15.21x | -14% | 5.9 | 70% | +1.18 | 2.52x | -13% |
| half at +2R, rest to break-even and run | 129 | 60% | +0.81 | 2.94 | 5.67 | 4 | 17.17x | -14% | 11.6 | 64% | +1.01 | 2.28x | -13% |
| Chandelier 3 ATR, no target | 129 | 47% | +0.89 | 2.67 | 3.53 | 3 | 11.54x | -34% | 10.6 | 45% | +0.55 | 1.16x | -23% |
| 4h swing trail, no target | 129 | 50% | +0.74 | 2.54 | 3.53 | 4 | 10.26x | -23% | 7.2 | 48% | +0.54 | 1.14x | -25% |
| exit after a daily sweep of the trade's high (after +1R) | 129 | 60% | +0.62 | 2.55 | 4.79 | 4 | 11.52x | -14% | 6.1 | 70% | +0.81 | 1.98x | -13% |
| exit after a daily sweep of the trade's high (from entry) | 129 | 64% | +0.60 | 3.00 | 5.07 | 4 | 10.92x | -14% | 3.4 | 61% | +0.53 | 1.67x | -14% |
| exit after a 4h sweep of the trade's high (after +1R) | 129 | 64% | +0.48 | 2.36 | 4.49 | 4 | 7.58x | -14% | 5.4 | 70% | +0.80 | 1.90x | -14% |
| entry filter: skip all three liquidity reasons | 106 | 59% | +0.98 | 3.25 | 5.15 | 4 | 14.00x | -23% | 11.4 | 71% | +1.29 | 2.22x | -11% |

## breakouts

Chosen on 2022-25 (t-score): **trail below the last 4h swing low (after +1R)**; most profit on 2022-25: **trail below the last 4h swing low (after +1R)**

| exit | trades | win % | avg R | profit factor | t-score | good years /4 | account 2022-25 | worst drop | avg hold (days) | holdout win % | holdout avg R | holdout account | holdout drop |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| fixed target (as now) | 78 | 62% | +0.74 | 2.80 | 4.47 | 4 | 7.96x | -10% | 1.7 | 59% | +0.69 | 1.67x | -13% |
| break-even after +1R | 78 | 45% | +0.58 | 3.13 | 4.07 | 4 | 5.56x | -9% | 1.2 | 50% | +0.64 | 1.56x | -14% |
| break-even after +1.5R | 78 | 51% | +0.59 | 2.55 | 3.75 | 4 | 5.67x | -9% | 1.4 | 59% | +0.69 | 1.67x | -13% |
| break-even after +2R | 78 | 62% | +0.74 | 2.80 | 4.47 | 4 | 7.96x | -10% | 1.7 | 59% | +0.69 | 1.67x | -13% |
| exit on the first 4h close against the entry | 78 | 51% | +0.62 | 2.84 | 4.09 | 4 | 5.40x | -16% | 1.2 | 41% | +0.45 | 1.40x | -10% |
| Chandelier 2 ATR (after +1R) | 78 | 62% | +0.74 | 2.85 | 4.52 | 4 | 8.06x | -10% | 1.5 | 59% | +0.69 | 1.67x | -13% |
| Chandelier 3 ATR (after +1R) | 78 | 62% | +0.75 | 2.85 | 4.54 | 4 | 8.16x | -10% | 1.7 | 59% | +0.69 | 1.67x | -13% |
| trail below the last 4h swing low (after +1R) | 78 | 62% | +0.76 | 2.90 | 4.62 | 4 | 8.34x | -10% | 1.5 | 59% | +0.69 | 1.67x | -13% |
| half at +2R, rest to break-even and run | 78 | 62% | +0.74 | 2.80 | 4.47 | 4 | 7.96x | -10% | 1.7 | 59% | +0.69 | 1.67x | -13% |
| Chandelier 3 ATR, no target | 78 | 41% | +0.74 | 2.23 | 2.33 | 3 | 5.19x | -33% | 3.7 | 27% | -0.30 | 0.75x | -35% |
| 4h swing trail, no target | 78 | 44% | +0.80 | 2.46 | 2.56 | 3 | 6.13x | -28% | 3.6 | 27% | -0.34 | 0.72x | -38% |
| exit after a daily sweep of the trade's high (after +1R) | 78 | 62% | +0.72 | 2.81 | 4.43 | 4 | 7.64x | -10% | 1.5 | 59% | +0.60 | 1.54x | -15% |
| exit after a daily sweep of the trade's high (from entry) | 78 | 62% | +0.69 | 2.85 | 4.39 | 4 | 7.17x | -10% | 1.0 | 59% | +0.60 | 1.54x | -15% |
| exit after a 4h sweep of the trade's high (after +1R) | 78 | 65% | +0.63 | 2.95 | 4.36 | 4 | 6.05x | -9% | 1.0 | 59% | +0.51 | 1.43x | -17% |
| entry filter: skip all three liquidity reasons | 68 | 62% | +0.75 | 2.83 | 4.21 | 4 | 5.88x | -17% | 1.7 | 69% | +0.98 | 1.72x | -11% |

## 1D bounces

Chosen on 2022-25 (t-score): **half at +2R, rest to break-even and run**; most profit on 2022-25: **break-even after +2R**

| exit | trades | win % | avg R | profit factor | t-score | good years /4 | account 2022-25 | worst drop | avg hold (days) | holdout win % | holdout avg R | holdout account | holdout drop |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| fixed target (as now) | 51 | 49% | +1.09 | 3.04 | 3.12 | 4 | 2.59x | -16% | 27.7 | 73% | +2.08 | 1.52x | -2% |
| break-even after +1R | 51 | 37% | +0.91 | 3.38 | 2.85 | 4 | 2.24x | -14% | 21.9 | 73% | +2.19 | 1.55x | -2% |
| break-even after +1.5R | 51 | 49% | +1.14 | 3.61 | 3.35 | 4 | 2.72x | -14% | 25.7 | 73% | +2.10 | 1.52x | -2% |
| break-even after +2R | 51 | 51% | +1.19 | 3.73 | 3.50 | 4 | 2.86x | -14% | 26.8 | 73% | +2.07 | 1.51x | -2% |
| exit on the first 4h close against the entry | 51 | 29% | +0.76 | 3.85 | 2.66 | 4 | 1.98x | -8% | 14.7 | 45% | +1.12 | 1.26x | -2% |
| Chandelier 2 ATR (after +1R) | 51 | 57% | +0.89 | 3.32 | 3.14 | 4 | 2.25x | -11% | 13.6 | 82% | +2.05 | 1.50x | -2% |
| Chandelier 3 ATR (after +1R) | 51 | 55% | +0.92 | 3.15 | 2.95 | 3 | 2.27x | -14% | 18.8 | 82% | +2.23 | 1.56x | -2% |
| trail below the last 4h swing low (after +1R) | 51 | 59% | +0.69 | 2.86 | 2.84 | 4 | 1.90x | -12% | 12.5 | 91% | +2.17 | 1.54x | -2% |
| half at +2R, rest to break-even and run | 51 | 59% | +0.92 | 3.15 | 3.54 | 4 | 2.30x | -12% | 26.8 | 73% | +1.65 | 1.40x | -2% |
| Chandelier 3 ATR, no target | 51 | 55% | +1.11 | 3.61 | 2.70 | 4 | 2.56x | -14% | 21.2 | 82% | +2.23 | 1.56x | -2% |
| 4h swing trail, no target | 51 | 59% | +0.64 | 2.73 | 2.82 | 4 | 1.82x | -12% | 12.8 | 91% | +2.32 | 1.59x | -2% |
| exit after a daily sweep of the trade's high (after +1R) | 51 | 59% | +0.46 | 2.15 | 2.19 | 4 | 1.55x | -13% | 13.2 | 91% | +1.23 | 1.30x | -2% |
| exit after a daily sweep of the trade's high (from entry) | 51 | 69% | +0.46 | 3.49 | 2.59 | 3 | 1.56x | -6% | 7.0 | 64% | +0.40 | 1.09x | -2% |
| exit after a 4h sweep of the trade's high (after +1R) | 51 | 61% | +0.26 | 1.64 | 1.67 | 3 | 1.28x | -12% | 12.1 | 91% | +1.39 | 1.34x | -2% |
| entry filter: skip all three liquidity reasons | 38 | 55% | +1.39 | 3.90 | 3.30 | 3 | 2.46x | -16% | 28.9 | 75% | +1.89 | 1.32x | -2% |

## Reading

- Breakouts (2 : 1): nothing beats the fixed target by more than noise; break-even after +2R and the partial exit are the same trade as the fixed target (2R = the target). The trails after +1R add +0.01 .. +0.02R.
- 1D bounces (5 : 1): **break-even after +2R** is the only exit that improves both the profit and the t-score on 2022-25 (+1.19R vs +1.09R, 2.86x vs 2.59x, drop -14% vs -16%) without hurting the holdout (+2.07R vs +2.08R). It changes 5 research trades (losers that had run 2R and came back to the stop, now ~0R) and 1 holdout trade. Five trades is a logical, small edge, not a proof.
- Every early exit on a 4h signal against the trade (first 4h close against, Chandelier, swing trail) wins more often but earns less per trade: the trades it saves are smaller than the winners it cuts.
- No target + trailing stop loses in both periods (fewer, bigger winners do not pay for the many trail stops).
- Exiting after a sweep of the trade's running high (the 22 Nov 2024 reading; daily or 4h, with or without waiting for +1R) earns +0.48 .. +0.62R vs +0.88R: the sweep of a high continues up about 3 times in 4 (reports/sideways_test.md), so it is not an exit.
- Skipping the 'all three liquidity reasons' trades raises the average R but lowers the account (fewer trades) and deepens the drawdown; it is a post-hoc hypothesis and stays out.

Audit: rounds 28 and 29a, independent re-implementation of the replay for all 162 trades x 14 exits, the booking, every table line and the SKIP3 flags; zero result-impacting issues.
