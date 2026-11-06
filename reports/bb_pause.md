# Pump -> sideways in the upper half -> first touch of the middle band: does the trend resume?

Fair test: 1.5 ATR in the claimed direction before 1.5 ATR against (30 candles). **A coin flip = 50%.** Up and mirrored down versions pooled. Research 2020 - Oct 2025; holdout Nov 2025 on. **chance it is noise**: events moved to random dates (400 shifts, clustering kept); below 0.01 = real.

## 4h

| event | cases 2020-25 | right | chance it is noise | years above 50% | holdout cases | holdout right |
|---|---|---|---|---|---|---|
| touch holds (closes back above the middle band): claim the trend resumes | 267 | 49% | 0.783 | 3/6 | 44 | 52% |
| touch breaks (closes below the middle band): claim the pause turns | 86 | 56% | 0.302 | 3/6 | 15 | 47% |
| any middle-band touch-and-hold in a rising band, without the pump-and-sideways | 544 | 45% | 0.052 | 1/6 | 78 | 49% |

### 4h: how big is the move after the touch?

From the touch close, over the next 30 candles, until a close below the touch candle's low (that close = the hold failed). **new top** = price trades above the pump's top (or any higher high made before the decision) first. Run = the furthest price got after the decision, in ATR of the decision candle.

| event | period | cases | new top before failing | hold failed within 30 | run: lower quarter (ATR) | run: median (ATR) | run: upper quarter (ATR) | median run % | runs >= 3 ATR |
|---|---|---|---|---|---|---|---|---|---|
| touch holds after a pump and sideways | 2020 - Oct 2025 | 274 | 33% | 78% | 0.3 | 1.0 | 2.6 | 2.4% | 22% |
| touch holds after a pump and sideways | holdout | 43 | 35% | 77% | 0.2 | 0.6 | 2.9 | 1.3% | 23% |
| ... and the next 2 closes stay above the middle band (measured from the 2nd) | 2020 - Oct 2025 | 174 | 38% | 72% | 0.3 | 1.0 | 2.9 | 2.2% | 25% |
| ... and the next 2 closes stay above the middle band (measured from the 2nd) | holdout | 24 | 58% | 58% | 0.4 | 1.8 | 5.5 | 2.8% | 38% |
| touch-and-hold without the sequence | 2020 - Oct 2025 | 554 | 36% | 80% | 0.1 | 0.8 | 2.2 | 1.6% | 18% |
| touch-and-hold without the sequence | holdout | 78 | 31% | 82% | 0.1 | 0.5 | 1.9 | 0.8% | 18% |
| ... without the sequence, next 2 closes above the middle band | 2020 - Oct 2025 | 328 | 50% | 69% | 0.4 | 1.3 | 3.0 | 2.7% | 25% |
| ... without the sequence, next 2 closes above the middle band | holdout | 41 | 56% | 68% | 0.2 | 1.0 | 2.7 | 1.5% | 22% |

### 4h: the trader's concept, all of it

After a pump and 3+ closes above the middle band (2020 - Oct 2025): price touched the middle band first in **366** cases, made a new pump (close beyond the outer band) without touching it in **77**, and did neither within 20 candles in 6. So it came to within 0.25 ATR of the middle band first 83% of the time. **That is the normal rate, not something the pump causes:** upper-half stretches with no pump in the 20 candles before came to the middle band first 78% of the time (119 vs 33). The middle band is a 20-candle average and rises toward price during sideways, and a touch (a wick within 0.25 ATR) is easier than a new close beyond the outer band.

| decided on | event | cases 2020-25 | right | chance it is noise | holdout cases | holdout right |
|---|---|---|---|---|---|---|
| touch candle's close | held the middle band -> claim: pump again | 267 | 49% | 0.783 | 44 | 52% |
| touch candle's close | failed to hold -> claim: dump | 86 | 56% | 0.302 | 15 | 47% |
| touch candle's close | both halves together | 353 | 51% | 0.781 | 59 | 51% |
| + 2 confirming closes | held the middle band -> claim: pump again | 173 | 40% | 0.010 | 25 | 48% |
| + 2 confirming closes | failed to hold -> claim: dump | 62 | 61% | 0.062 | 9 | 44% |
| + 2 confirming closes | both halves together | 235 | 46% | 0.282 | 34 | 47% |

## 1D

| event | cases 2020-25 | right | chance it is noise | years above 50% | holdout cases | holdout right |
|---|---|---|---|---|---|---|
| touch holds (closes back above the middle band): claim the trend resumes | 44 | 61% | 0.092 | 5/6 | 4 | 25% |
| touch breaks (closes below the middle band): claim the pause turns | 20 | 55% | 0.666 | 1/2 | 2 | 0% |
| any middle-band touch-and-hold in a rising band, without the pump-and-sideways | 93 | 45% | 0.431 | 2/6 | 17 | 41% |

### 1D: how big is the move after the touch?

From the touch close, over the next 30 candles, until a close below the touch candle's low (that close = the hold failed). **new top** = price trades above the pump's top (or any higher high made before the decision) first. Run = the furthest price got after the decision, in ATR of the decision candle.

| event | period | cases | new top before failing | hold failed within 30 | run: lower quarter (ATR) | run: median (ATR) | run: upper quarter (ATR) | median run % | runs >= 3 ATR |
|---|---|---|---|---|---|---|---|---|---|
| touch holds after a pump and sideways | 2020 - Oct 2025 | 45 | 38% | 67% | 0.5 | 1.0 | 4.6 | 7.7% | 33% |
| touch holds after a pump and sideways | holdout | 3 | 0% | 100% | 0.2 | 0.4 | 0.5 | 1.4% | 0% |
| ... and the next 2 closes stay above the middle band (measured from the 2nd) | 2020 - Oct 2025 | 34 | 47% | 59% | 0.2 | 1.0 | 4.8 | 7.3% | 38% |
| ... and the next 2 closes stay above the middle band (measured from the 2nd) | holdout | 2 | 0% | 100% | 0.2 | 0.5 | 0.7 | 1.9% | 0% |
| touch-and-hold without the sequence | 2020 - Oct 2025 | 94 | 36% | 76% | 0.1 | 0.7 | 3.7 | 3.6% | 28% |
| touch-and-hold without the sequence | holdout | 14 | 29% | 93% | 0.2 | 0.4 | 1.7 | 2.5% | 7% |
| ... without the sequence, next 2 closes above the middle band | 2020 - Oct 2025 | 54 | 50% | 63% | 0.3 | 1.3 | 5.0 | 6.3% | 37% |
| ... without the sequence, next 2 closes above the middle band | holdout | 9 | 33% | 89% | 0.3 | 0.4 | 1.4 | 1.9% | 11% |

### 1D: the trader's concept, all of it

After a pump and 3+ closes above the middle band (2020 - Oct 2025): price touched the middle band first in **65** cases, made a new pump (close beyond the outer band) without touching it in **13**, and did neither within 20 candles in 0. So it came to within 0.25 ATR of the middle band first 83% of the time. **That is the normal rate, not something the pump causes:** upper-half stretches with no pump in the 20 candles before came to the middle band first 81% of the time (25 vs 6). The middle band is a 20-candle average and rises toward price during sideways, and a touch (a wick within 0.25 ATR) is easier than a new close beyond the outer band.

| decided on | event | cases 2020-25 | right | chance it is noise | holdout cases | holdout right |
|---|---|---|---|---|---|---|
| touch candle's close | held the middle band -> claim: pump again | 44 | 61% | 0.092 | 4 | 25% |
| touch candle's close | failed to hold -> claim: dump | 20 | 55% | 0.666 | 2 | 0% |
| touch candle's close | both halves together | 64 | 59% | 0.110 | 6 | 17% |
| + 2 confirming closes | held the middle band -> claim: pump again | 35 | 57% | 0.354 | 3 | 33% |
| + 2 confirming closes | failed to hold -> claim: dump | 12 | 67% | not tested (n < 20) | 0 | - |
| + 2 confirming closes | both halves together | 47 | 60% | 0.165 | 3 | 33% |

Daily up-version events (touch holds after a pump and sideways): 2020-04-13, 2020-05-07, 2020-06-11, 2020-08-19, 2020-10-16, 2020-10-26, 2021-01-11, 2021-05-16, 2021-08-18, 2021-10-27, 2021-11-14, 2022-07-26, 2023-01-29, 2023-03-27, 2023-04-09, 2023-11-14, 2024-01-18, 2024-03-15, 2024-12-09, 2025-05-25, 2025-08-19, 2026-01-19, 2026-04-23, 2026-09-07, 2026-10-02

