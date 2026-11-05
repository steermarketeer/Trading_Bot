# Bollinger middle band: do aggressive buyers defend it?

Every v3.1 ETH trade, one position per move. **win % = profit after all costs.** The idea came from the journal (holdout trades), so **2022 - Oct 2025 is the clean test**.

## Results

| rule | period | trades | per week | win % | avg R | profit factor | avg reward:risk | account | worst drop |
|---|---|---|---|---|---|---|---|---|---|
| v3.1 now (one position per move) | 2022 - Oct 2025 (clean test) | 296 | 1.48 | 45% | +0.45 | 1.77 | 2.65 | 25.13x | -36% |
| v3.1 now (one position per move) | holdout | 71 | 1.46 | 49% | +0.56 | 2.04 | 2.61 | 2.49x | -23% |
| X · exit on a 1h close through the middle band (before +1R) | 2022 - Oct 2025 (clean test) | 296 | 1.48 | 34% | +0.22 | 2.13 | 2.65 | 7.38x | -27% |
| X · exit on a 1h close through the middle band (before +1R) | holdout | 71 | 1.46 | 32% | +0.18 | 1.73 | 2.61 | 1.68x | -16% |
| E · enter only after the 1h middle band is defended | 2022 - Oct 2025 (clean test) | 206 | 1.03 | 38% | +0.32 | 1.50 | 2.90 | 3.39x | -28% |
| E · enter only after the 1h middle band is defended | holdout | 46 | 0.95 | 43% | +0.41 | 1.71 | 2.86 | 1.46x | -18% |
| E + X | 2022 - Oct 2025 (clean test) | 206 | 1.03 | 18% | -0.03 | 0.82 | 2.90 | 0.89x | -23% |
| E + X | holdout | 46 | 0.95 | 13% | -0.02 | 0.88 | 2.86 | 1.02x | -13% |

## Per setup

| rule | setup | period | trades | win % | avg R |
|---|---|---|---|---|---|
| base | A+ breakout | 2022-25 | 65 | 66% | +0.86 |
| base | A+ breakout | holdout | 20 | 60% | +0.72 |
| base | breakout | 2022-25 | 38 | 50% | +0.41 |
| base | breakout | holdout | 8 | 38% | -0.01 |
| base | 1D bounce | 2022-25 | 193 | 36% | +0.32 |
| base | 1D bounce | holdout | 43 | 47% | +0.58 |
| X | A+ breakout | 2022-25 | 65 | 55% | +0.69 |
| X | A+ breakout | holdout | 20 | 60% | +0.82 |
| X | breakout | 2022-25 | 38 | 47% | +0.45 |
| X | breakout | holdout | 8 | 25% | -0.23 |
| X | 1D bounce | 2022-25 | 193 | 25% | +0.01 |
| X | 1D bounce | holdout | 43 | 21% | -0.03 |
| E | A+ breakout | 2022-25 | 20 | 55% | +0.41 |
| E | A+ breakout | holdout | 5 | 40% | +0.48 |
| E | breakout | 2022-25 | 13 | 23% | -0.30 |
| E | breakout | holdout | 3 | 33% | +0.21 |
| E | 1D bounce | 2022-25 | 173 | 38% | +0.35 |
| E | 1D bounce | holdout | 38 | 45% | +0.42 |
| E+X | A+ breakout | 2022-25 | 20 | 25% | +0.05 |
| E+X | A+ breakout | holdout | 5 | 40% | +0.57 |
| E+X | breakout | 2022-25 | 13 | 15% | -0.09 |
| E+X | breakout | holdout | 3 | 0% | -0.33 |
| E+X | 1D bounce | 2022-25 | 173 | 18% | -0.03 |
| E+X | 1D bounce | holdout | 38 | 11% | -0.08 |

