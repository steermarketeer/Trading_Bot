# Bollinger bands in detail: when price reaches the outer band, does it go further or fail back?

Every candle that reaches the upper band (and, mirrored, the lower band) on ETH. **go further** = price moves as far beyond that close as the close is from the middle band, before it comes back to the middle band (a fair, symmetric test: a coin flip would be 50%). **fail** = it comes back to the middle band first. Research 2020 - Oct 2025; the holdout (Nov 2025 on) is shown to check the pattern holds.

## 1h (13,678 band reaches 2020 - Oct 2025; price went further 50% of the time)

| at the band | cases | went further | holdout cases | holdout went further |
|---|---|---|---|---|
| close outside | 5,675 | 52% | 850 | 55% |
| not close outside | 8,003 | 48% | 1347 | 47% |
| walk | 2,654 | 54% | 424 | 53% |
| not walk | 11,024 | 49% | 1773 | 50% |
| squeeze breakout | 3,946 | 50% | 652 | 50% |
| not squeeze breakout | 9,732 | 49% | 1545 | 50% |
| bulge | 2,070 | 58% | 278 | 58% |
| not bulge | 11,608 | 48% | 1919 | 49% |
| bands expanding | 10,076 | 51% | 1625 | 51% |
| not bands expanding | 3,602 | 47% | 572 | 49% |
| opposite band turned | 6,079 | 48% | 996 | 50% |
| not opposite band turned | 7,599 | 51% | 1201 | 50% |
| %b non-confirmation | 3,264 | 50% | 461 | 50% |
| not %b non-confirmation | 10,414 | 49% | 1736 | 50% |
| volume high | 6,079 | 51% | 1050 | 47% |
| not volume high | 7,599 | 49% | 1147 | 53% |
| RSI > 75 | 1,020 | 61% | 167 | 54% |
| not RSI > 75 | 12,658 | 49% | 2030 | 50% |
| upper wick | 6,722 | 48% | 1078 | 48% |
| not upper wick | 6,956 | 51% | 1119 | 52% |
| higher TF at band | 3,523 | 53% | 573 | 50% |
| not higher TF at band | 10,155 | 48% | 1624 | 50% |
| higher TF trend | 8,764 | 50% | 1432 | 51% |
| not higher TF trend | 4,904 | 49% | 765 | 49% |

### 1h: the two-condition mixes where price failed most and went further most (>= 150 cases)

| at the band | cases | went further | holdout cases | holdout went further |
|---|---|---|---|---|
| not bands expanding + upper wick | 1,830 | 44% | 286 | 45% |
| not bands expanding + %b non-confirmation | 602 | 44% | 85 | 51% |
| opposite band turned + upper wick | 3,123 | 46% | 517 | 47% |
| not close outside + not bands expanding | 2,742 | 46% | 446 | 47% |
| not bands expanding + higher TF at band | 542 | 46% | 82 | 46% |
| upper wick + not higher TF at band | 4,900 | 46% | 773 | 49% |
| walk + RSI > 75 | 597 | 64% | 88 | 51% |
| not opposite band turned + RSI > 75 | 740 | 65% | 123 | 53% |
| bulge + RSI > 75 | 705 | 65% | 92 | 63% |
| RSI > 75 + not higher TF at band | 216 | 65% | 53 | 57% |
| squeeze breakout + RSI > 75 | 189 | 66% | 39 | 26% |
| squeeze breakout + bulge | 208 | 69% | 19 | 42% |

## 4h (3,362 band reaches 2020 - Oct 2025; price went further 49% of the time)

| at the band | cases | went further | holdout cases | holdout went further |
|---|---|---|---|---|
| close outside | 1,444 | 52% | 238 | 47% |
| not close outside | 1,918 | 47% | 317 | 47% |
| walk | 754 | 51% | 111 | 47% |
| not walk | 2,608 | 49% | 444 | 48% |
| squeeze breakout | 1,015 | 46% | 200 | 44% |
| not squeeze breakout | 2,347 | 50% | 355 | 49% |
| bulge | 568 | 62% | 77 | 60% |
| not bulge | 2,794 | 47% | 478 | 45% |
| bands expanding | 2,483 | 50% | 403 | 46% |
| not bands expanding | 879 | 48% | 152 | 51% |
| opposite band turned | 1,427 | 49% | 243 | 52% |
| not opposite band turned | 1,935 | 49% | 312 | 44% |
| %b non-confirmation | 878 | 52% | 128 | 46% |
| not %b non-confirmation | 2,484 | 48% | 427 | 48% |
| volume high | 1,299 | 51% | 249 | 50% |
| not volume high | 2,063 | 48% | 306 | 45% |
| RSI > 75 | 311 | 64% | 38 | 63% |
| not RSI > 75 | 3,051 | 48% | 517 | 46% |
| upper wick | 1,568 | 47% | 269 | 48% |
| not upper wick | 1,794 | 51% | 286 | 47% |
| higher TF at band | 633 | 58% | 99 | 55% |
| not higher TF at band | 2,729 | 47% | 456 | 46% |
| higher TF trend | 1,984 | 51% | 328 | 48% |
| not higher TF trend | 1,332 | 46% | 227 | 46% |

### 4h: the two-condition mixes where price failed most and went further most (>= 150 cases)

| at the band | cases | went further | holdout cases | holdout went further |
|---|---|---|---|---|
| squeeze breakout + not higher TF trend | 414 | 41% | 92 | 43% |
| squeeze breakout + upper wick | 479 | 42% | 103 | 50% |
| upper wick + not higher TF trend | 632 | 42% | 104 | 44% |
| not close outside + not higher TF trend | 778 | 44% | 128 | 46% |
| not close outside + squeeze breakout | 493 | 44% | 85 | 47% |
| not bulge + upper wick | 1,298 | 44% | 223 | 45% |
| bands expanding + RSI > 75 | 284 | 65% | 33 | 64% |
| not squeeze breakout + RSI > 75 | 247 | 66% | 25 | 76% |
| volume high + RSI > 75 | 179 | 67% | 24 | 62% |
| bulge + opposite band turned | 171 | 67% | 23 | 78% |
| RSI > 75 + higher TF at band | 203 | 68% | 30 | 70% |
| bulge + RSI > 75 | 210 | 68% | 19 | 84% |

## 1D (506 band reaches 2020 - Oct 2025; price went further 58% of the time)

| at the band | cases | went further | holdout cases | holdout went further |
|---|---|---|---|---|
| close outside | 202 | 61% | 35 | 69% |
| not close outside | 304 | 56% | 41 | 37% |
| walk | 108 | 68% | 16 | 56% |
| not walk | 398 | 55% | 60 | 50% |
| squeeze breakout | 153 | 59% | 30 | 63% |
| not squeeze breakout | 353 | 57% | 46 | 43% |
| bulge | 72 | 67% | 5 | 40% |
| not bulge | 434 | 56% | 71 | 52% |
| bands expanding | 380 | 60% | 56 | 52% |
| not bands expanding | 126 | 52% | 20 | 50% |
| opposite band turned | 231 | 56% | 35 | 37% |
| not opposite band turned | 275 | 60% | 41 | 63% |
| %b non-confirmation | 146 | 63% | 16 | 56% |
| not %b non-confirmation | 360 | 56% | 60 | 50% |
| volume high | 151 | 65% | 22 | 59% |
| not volume high | 355 | 55% | 54 | 48% |
| RSI > 75 | 53 | 75% | 3 | 100% |
| not RSI > 75 | 453 | 56% | 73 | 49% |
| upper wick | 223 | 54% | 32 | 41% |
| not upper wick | 283 | 61% | 44 | 59% |
| higher TF at band | 128 | 61% | 8 | 38% |
| not higher TF at band | 378 | 57% | 68 | 53% |
| higher TF trend | 262 | 57% | 33 | 52% |
| not higher TF trend | 195 | 57% | 43 | 51% |

### 1D: the two-condition mixes where price failed most and went further most (>= 150 cases)

| at the band | cases | went further | holdout cases | holdout went further |
|---|---|---|---|---|
| not bulge + upper wick | 188 | 52% | 30 | 40% |
| not volume high + upper wick | 162 | 52% | 27 | 37% |
| not walk + upper wick | 180 | 52% | 25 | 36% |
| opposite band turned + not volume high | 183 | 52% | 26 | 35% |
| not squeeze breakout + not volume high | 249 | 53% | 31 | 35% |
| not RSI > 75 + upper wick | 215 | 53% | 32 | 41% |
| not bulge + not upper wick | 246 | 60% | 41 | 61% |
| not opposite band turned + not upper wick | 166 | 61% | 27 | 67% |
| close outside + not upper wick | 173 | 62% | 30 | 70% |
| bands expanding + not upper wick | 221 | 62% | 33 | 58% |
| not upper wick + higher TF trend | 150 | 62% | 18 | 61% |
| close outside + bands expanding | 174 | 63% | 29 | 62% |

