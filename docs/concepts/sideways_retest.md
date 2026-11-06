# After a pump or dump: the test of the extreme and the retest of the price

Trader's concept (22 Nov 2024 review): "when going sideways after a pump or a dump, the price gets tested first, mostly.
The retest of the price is the key. RSI at 70 with the price at 3,358, later RSI at 60 with the price well above."

Study: `bot/study/sideways_test.py`, report `reports/sideways_test.md` (six coins, 4h and daily, 2022 - Oct 2025, holdout
Nov 2025 on, audited round 29b).

## Definitions (close-based, ATR = 14 of the last closed candle)
- Impulse: in 6 candles the price moved >= 2 ATR from its lowest low to a high made on the last or second-last candle,
  and closed in the top 30% of that leg.
- Sideways: the next 3 candles close neither above the high nor below the origin low.
- Resolution: the first close above the high (continuation) or below the origin (reversal), within 40 candles.
- Test of the high: after a pullback of >= 1 ATR, a later candle's high within 0.25 ATR of the high (sweep if above it
  and closing back below; touch otherwise).
- Retest of the price: after trading >= 0.5 ATR above the impulse close, a later candle's low back at that close; it
  held if that candle closes no more than 0.25 ATR below.

## What holds
1. The extreme is tested before the sideways resolves in about 3 of 4 cases (daily 75%, 4h 77%; dumps 72 - 74%;
   holdout 68 - 86%). Small legs at the same distance: 56 - 74%, so proximity explains part of it.
2. A held retest of the impulse close is the continuation marker: daily pumps 72% continue vs 55% after a failed
   retest and 54% with none; 4h 71% vs 56% / 55%; dumps 63 - 70% vs 42 - 48%; holdout agrees.

## What does not hold
3. The sweep of the high is not a reversal signal: after a sweep the range continues 70 - 74% (at a strong S/R level
   too: 69 - 74%). The 16 Dec 2024 sweep of 4,099 was the minority case. Exiting after a sweep of the trade's high
   loses money on our trades (+0.62R vs +0.88R, `reports/exit_study.md`).
4. RSI cooling at the retest (>= 5 points below the impulse) continues less (54 - 56%) than a warm retest (70 - 71%);
   most continuations break with a higher RSI than at the impulse (70 - 75%).

## For the bot
Hold through the sideways. Do not exit on the test of the high. A held retest of the pump's close says stay; a failed
one is a coin flip. Still to test: entering on the held retest (a pullback entry) instead of at the pump's close, and
the stop under the retest low.

## Addendum: the textbook top (three failed tops, the line breaks, the retest fails, the price falls)
Study `bot/study/textbook_top.py`, report `reports/textbook_top.md` (six coins, 15m / 1h / 4h, audited round 30).
The structure is common and well drawn: after three confirmed swing highs at one cap the rising line breaks, is retested
7 times in 10 and the retest is rejected half the time. The fall afterwards is a coin flip (53 - 54% on the 15m, 51 - 52%
in the holdout; 1h 52 - 53%; 4h 55 - 59% on 52 cases) and the short at the rejected retest loses after costs on every
timeframe. Three tops add nothing to the line break and the line break adds nothing to three tops. The pattern says what
a top looks like after the fact; the higher-timeframe side and the liquidity below decide whether the fall comes.
