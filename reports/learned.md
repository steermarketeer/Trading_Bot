# What the indicator studies taught, applied to the current best version

Rules written from the general studies (docs/indicators.md) before looking at these trades. **win % = profit after costs.** 2022 - Oct 2025 and the holdout (Nov 2025 on).

| version | period | trades | win % | avg R | profit factor | account | worst drop |
|---|---|---|---|---|---|---|---|
| current best version | 2022 - Oct 2025 | 100 | 59% | +0.83 | 2.93 | 9.08x | -12% |
| current best version | holdout | 27 | 70% | +1.28 | 5.40 | 2.31x | -8% |
| + R1 + R2 + R3 + R4 (all learned filters) | 2022 - Oct 2025 | 92 | 61% | +0.88 | 3.16 | 8.26x | -12% |
| + R1 + R2 + R3 + R4 (all learned filters) | holdout | 22 | 68% | +1.27 | 5.11 | 1.79x | -10% |
| + R6 + R7 + R8 (deep-study filters) | 2022 - Oct 2025 | 44 | 57% | +0.61 | 2.37 | 2.79x | -9% |
| + R6 + R7 + R8 (deep-study filters) | holdout | 11 | 73% | +1.11 | 4.70 | 1.44x | -7% |
| + exit X (bounce touches the 4h middle band) | 2022 - Oct 2025 | 100 | 53% | +0.63 | 3.44 | 6.54x | -12% |
| + exit X (bounce touches the 4h middle band) | holdout | 27 | 52% | +0.64 | 3.31 | 1.69x | -9% |

## Each rule: which trades it would skip

| rule | period | skipped | of them losers | of them winners | R of the skipped trades | trades kept | win % kept | avg R kept |
|---|---|---|---|---|---|---|---|---|
| R1 weak band touch at entry | 2022 - Oct 2025 | 1 | 1 | 0 | -1.02 | 99 | 60% | +0.84 |
| R1 weak band touch at entry | holdout | 0 | 0 | 0 | +0.00 | 27 | 70% | +1.28 |
| R2 fading momentum (buy RSI < 30 / sell RSI > 70) | 2022 - Oct 2025 | 0 | 0 | 0 | +0.00 | 100 | 59% | +0.83 |
| R2 fading momentum (buy RSI < 30 / sell RSI > 70) | holdout | 0 | 0 | 0 | +0.00 | 27 | 70% | +1.28 |
| R3 squeeze breakout against the daily trend | 2022 - Oct 2025 | 7 | 4 | 3 | +2.53 | 93 | 60% | +0.86 |
| R3 squeeze breakout against the daily trend | holdout | 5 | 1 | 4 | +6.70 | 22 | 68% | +1.27 |
| R4 breakout on thin volume | 2022 - Oct 2025 | 0 | 0 | 0 | +0.00 | 100 | 59% | +0.83 |
| R4 breakout on thin volume | holdout | 0 | 0 | 0 | +0.00 | 27 | 70% | +1.28 |
| R5 against the daily EMA 200 (information) | 2022 - Oct 2025 | 35 | 16 | 19 | +22.80 | 65 | 62% | +0.92 |
| R5 against the daily EMA 200 (information) | holdout | 14 | 5 | 9 | +14.22 | 13 | 77% | +1.56 |
| R6 breakout volume below 2x (2x proven to help; 1-2x failing is not proven) | 2022 - Oct 2025 | 4 | 2 | 2 | +1.84 | 96 | 59% | +0.84 |
| R6 breakout volume below 2x (2x proven to help; 1-2x failing is not proven) | holdout | 1 | 0 | 1 | +1.94 | 26 | 69% | +1.25 |
| R7 bearish RSI divergence at a breakout (4h) | 2022 - Oct 2025 | 7 | 2 | 5 | +7.55 | 93 | 58% | +0.81 |
| R7 bearish RSI divergence at a breakout (4h) | holdout | 4 | 2 | 2 | +1.80 | 23 | 74% | +1.42 |
| R8 1D bounce after only a shallow 4h pullback (< 0.45 of the leg) | 2022 - Oct 2025 | 45 | 18 | 27 | +46.36 | 55 | 58% | +0.66 |
| R8 1D bounce after only a shallow 4h pullback (< 0.45 of the leg) | holdout | 11 | 3 | 8 | +18.59 | 16 | 69% | +1.00 |

