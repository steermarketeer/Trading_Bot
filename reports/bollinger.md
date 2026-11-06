# Bollinger bands in detail: when price reaches the outer band, does it go further or fail back?

Every candle that reaches the upper band (and, mirrored, the lower band) on ETH. **go further** = price moves as far beyond that close as the close is from the middle band, before it comes back to the middle band (a fair, symmetric test: a coin flip would be 50%). **fail** = it comes back to the middle band first. Research 2020 - Oct 2025; the holdout (Nov 2025 on) is shown to check the pattern holds.

## 1h (13,683 band reaches 2020 - Oct 2025; price went further 50% of the time)

| at the band | cases | went further | holdout cases | holdout went further |
|---|---|---|---|---|
| close outside | 5,678 | 52% | 850 | 55% |
| not close outside | 8,005 | 48% | 1347 | 47% |
| walk | 2,655 | 53% | 424 | 53% |
| not walk | 11,028 | 49% | 1773 | 50% |
| squeeze breakout | 3,946 | 50% | 652 | 50% |
| not squeeze breakout | 9,737 | 49% | 1545 | 50% |
| bulge | 2,073 | 58% | 278 | 58% |
| not bulge | 11,610 | 48% | 1919 | 49% |
| bands expanding | 10,079 | 51% | 1625 | 51% |
| not bands expanding | 3,604 | 47% | 572 | 49% |
| opposite band turned | 6,082 | 48% | 996 | 50% |
| not opposite band turned | 7,601 | 51% | 1201 | 50% |
| %b non-confirmation | 3,264 | 50% | 461 | 50% |
| not %b non-confirmation | 10,419 | 49% | 1736 | 50% |
| volume high | 6,080 | 51% | 1050 | 47% |
| not volume high | 7,603 | 49% | 1147 | 53% |
| RSI > 75 | 1,020 | 61% | 167 | 54% |
| not RSI > 75 | 12,663 | 49% | 2030 | 50% |
| upper wick | 6,724 | 48% | 1078 | 48% |
| not upper wick | 6,959 | 51% | 1119 | 52% |
| higher TF at band | 3,526 | 53% | 573 | 50% |
| not higher TF at band | 10,157 | 48% | 1624 | 50% |
| higher TF trend | 8,767 | 50% | 1432 | 51% |
| not higher TF trend | 4,916 | 49% | 765 | 49% |

### 1h: the two-condition mixes where price failed most and went further most (>= 150 cases)

| at the band | cases | went further | holdout cases | holdout went further |
|---|---|---|---|---|
| not bands expanding + upper wick | 1,831 | 44% | 286 | 45% |
| not bands expanding + %b non-confirmation | 602 | 44% | 85 | 51% |
| opposite band turned + upper wick | 3,124 | 46% | 517 | 47% |
| not close outside + not bands expanding | 2,743 | 46% | 446 | 47% |
| not bands expanding + higher TF at band | 542 | 46% | 82 | 46% |
| upper wick + not higher TF at band | 4,901 | 46% | 773 | 49% |
| walk + RSI > 75 | 597 | 64% | 88 | 51% |
| not opposite band turned + RSI > 75 | 740 | 65% | 123 | 53% |
| bulge + RSI > 75 | 705 | 65% | 92 | 63% |
| RSI > 75 + not higher TF at band | 216 | 65% | 53 | 57% |
| squeeze breakout + RSI > 75 | 189 | 66% | 39 | 26% |
| squeeze breakout + bulge | 208 | 69% | 19 | 42% |

## 4h (3,371 band reaches 2020 - Oct 2025; price went further 49% of the time)

| at the band | cases | went further | holdout cases | holdout went further |
|---|---|---|---|---|
| close outside | 1,449 | 52% | 238 | 47% |
| not close outside | 1,922 | 47% | 317 | 47% |
| walk | 756 | 51% | 111 | 47% |
| not walk | 2,615 | 49% | 444 | 48% |
| squeeze breakout | 1,017 | 46% | 200 | 44% |
| not squeeze breakout | 2,354 | 51% | 355 | 49% |
| bulge | 568 | 62% | 77 | 60% |
| not bulge | 2,803 | 47% | 478 | 45% |
| bands expanding | 2,491 | 50% | 403 | 46% |
| not bands expanding | 880 | 48% | 152 | 51% |
| opposite band turned | 1,431 | 50% | 243 | 52% |
| not opposite band turned | 1,940 | 49% | 312 | 44% |
| %b non-confirmation | 880 | 52% | 128 | 46% |
| not %b non-confirmation | 2,491 | 48% | 427 | 48% |
| volume high | 1,304 | 51% | 249 | 50% |
| not volume high | 2,067 | 48% | 306 | 45% |
| RSI > 75 | 314 | 64% | 38 | 63% |
| not RSI > 75 | 3,057 | 48% | 517 | 46% |
| upper wick | 1,571 | 47% | 269 | 48% |
| not upper wick | 1,800 | 51% | 286 | 47% |
| higher TF at band | 634 | 58% | 99 | 55% |
| not higher TF at band | 2,737 | 47% | 456 | 46% |
| higher TF trend | 1,993 | 51% | 328 | 48% |
| not higher TF trend | 1,378 | 46% | 227 | 46% |

### 4h: the two-condition mixes where price failed most and went further most (>= 150 cases)

| at the band | cases | went further | holdout cases | holdout went further |
|---|---|---|---|---|
| squeeze breakout + not higher TF trend | 419 | 41% | 92 | 43% |
| squeeze breakout + upper wick | 480 | 42% | 103 | 50% |
| upper wick + not higher TF trend | 656 | 43% | 104 | 44% |
| not close outside + squeeze breakout | 493 | 44% | 85 | 47% |
| not close outside + not higher TF trend | 804 | 44% | 128 | 46% |
| not bulge + upper wick | 1,301 | 44% | 223 | 45% |
| close outside + bulge | 266 | 65% | 29 | 59% |
| not squeeze breakout + RSI > 75 | 248 | 66% | 25 | 76% |
| volume high + RSI > 75 | 181 | 67% | 24 | 62% |
| bulge + opposite band turned | 171 | 67% | 23 | 78% |
| RSI > 75 + higher TF at band | 203 | 68% | 30 | 70% |
| bulge + RSI > 75 | 210 | 68% | 19 | 84% |

## 1D (512 band reaches 2020 - Oct 2025; price went further 57% of the time)

| at the band | cases | went further | holdout cases | holdout went further |
|---|---|---|---|---|
| close outside | 202 | 61% | 35 | 69% |
| not close outside | 310 | 55% | 41 | 37% |
| walk | 108 | 68% | 16 | 56% |
| not walk | 404 | 55% | 60 | 50% |
| squeeze breakout | 153 | 59% | 30 | 63% |
| not squeeze breakout | 359 | 57% | 46 | 43% |
| bulge | 72 | 67% | 5 | 40% |
| not bulge | 440 | 56% | 71 | 52% |
| bands expanding | 385 | 59% | 56 | 52% |
| not bands expanding | 127 | 53% | 20 | 50% |
| opposite band turned | 233 | 56% | 35 | 37% |
| not opposite band turned | 279 | 59% | 41 | 63% |
| %b non-confirmation | 147 | 63% | 16 | 56% |
| not %b non-confirmation | 365 | 55% | 60 | 50% |
| volume high | 154 | 64% | 22 | 59% |
| not volume high | 358 | 55% | 54 | 48% |
| RSI > 75 | 53 | 75% | 3 | 100% |
| not RSI > 75 | 459 | 55% | 73 | 49% |
| upper wick | 226 | 54% | 32 | 41% |
| not upper wick | 286 | 60% | 44 | 59% |
| higher TF at band | 128 | 61% | 8 | 38% |
| not higher TF at band | 384 | 56% | 68 | 53% |
| higher TF trend | 263 | 57% | 33 | 52% |
| not higher TF trend | 249 | 58% | 43 | 51% |

### 1D: the two-condition mixes where price failed most and went further most (>= 150 cases)

| at the band | cases | went further | holdout cases | holdout went further |
|---|---|---|---|---|
| not bulge + upper wick | 191 | 51% | 30 | 40% |
| not walk + upper wick | 183 | 51% | 25 | 36% |
| not volume high + upper wick | 163 | 52% | 27 | 37% |
| opposite band turned + not volume high | 184 | 53% | 26 | 35% |
| not RSI > 75 + upper wick | 218 | 53% | 32 | 41% |
| not close outside + upper wick | 197 | 53% | 27 | 37% |
| not squeeze breakout + not opposite band turned | 152 | 61% | 16 | 62% |
| bands expanding + not higher TF trend | 176 | 61% | 31 | 45% |
| bands expanding + not upper wick | 223 | 61% | 33 | 58% |
| close outside + not upper wick | 173 | 62% | 30 | 70% |
| not upper wick + higher TF trend | 150 | 62% | 18 | 61% |
| close outside + bands expanding | 174 | 63% | 29 | 62% |

