# The middle-band hold after a pump: theory and evidence

**The concept (the trader's words):** when price goes sideways on the upper Bollinger band after a pump, it usually
comes to the middle band. If it holds there, it pumps again. If it cannot hold, it dumps.

Evidence: `reports/bb_pause.md` (the sequence, its size, the concept in full) and `reports/bb_pause_why.md` (why it
works and why it fails). Events on 1h, 4h and daily ETH, mirrored for dumps, 2020 - Oct 2025, holdout Nov 2025 on.

## 1. What the theory says

The same pattern appears under different names in every school, and each one explains a part of it.

| School | Its name for it | What it says happens at the middle |
|---|---|---|
| **John Bollinger** | a pause in a band walk; the 20-period average as the trend's base | In a strong trend the middle band is support; tags of the upper band are not sell signals; a close back at / below the middle band after a walk is the sign momentum is fading. ([TradingView](https://in.tradingview.com/support/solutions/43000501840/), [Capital.com](https://capital.com/en-au/learn/technical-analysis/bollinger-bands)) |
| **Wyckoff** | re-accumulation after a markup; the test / spring; the last point of support (LPS) | After a sign of strength, a pullback to former resistance on smaller spread and volume that holds as a higher low is the LPS before the next markup; a spring dips under support and recovers; a close back below the spring low cancels the read, and a failed test means distribution, not accumulation. ([StockCharts](https://articles.stockcharts.com/article/articles-wyckoff-2016-04-wyckoff-buy-strategies/), [LuxAlgo](https://www.luxalgo.com/library/concept/spring.md)) |
| **Al Brooks** | the first pullback to the moving average in a strong trend; the 20-gap bar | After many bars on one side of the average, a pullback to it is likely; the first touch is usually followed by a test of the trend's extreme (often only a test, not a big new leg). ([Brooks, Trading Price Action, ch. 13 – 14](https://www.oreilly.com/library/view/trading-price-action/9781118172339/OEBPS/9781118172339_epub_c_14.htm)) |
| **Bulkowski** | the flag / pennant after a flagpole | Flags continue, but less reliably than people think: a 44% break-even failure rate and a 9% average rise for flags, 54% and 7% for pennants; the best flags have a long, near-vertical pole. ([thepatternsite.com flags](https://thepatternsite.com/flags.html), [pennants](https://thepatternsite.com/pennants.html)) |
| **ICT / smart money** | equilibrium of the dealing range; a liquidity sweep before continuation | The midpoint of the leg is equilibrium: below it is discount. Price sweeps the liquidity resting under the lows (late buyers' stops), then continues to the liquidity above the old high. ([LuxAlgo](https://www.luxalgo.com/library/concept/premium-and-discount/), [Equiti](https://www.equiti.com/jo-en/news/trading-ideas/ict-50-percent-rule-premium-discount-fvg/)) |
| Elliott | wave 4 | A sideways, shallow correction after the strongest wave (3), before a final wave 5. |

**One mechanism behind all of them.** The pump brings in late buyers. While price goes sideways, their average entry
price is roughly the 20-candle average, i.e. the middle band. When price comes back to it, the question is whether real
buyers defend that price (**absorption**: the selling is met, often after the stops just under the level are taken)
or whether the late buyers give up (**distribution**: no one defends, their stops and liquidations below become the fuel
for the dump). The candle at the middle band shows which one is happening.

## 2. What the data says

### Part 1: "it usually comes to the middle band": true, but mechanical
After a pump and 3+ sideways closes above the middle band, price came to within 0.25 ATR of the middle band before a
new close beyond the outer band about 83% of the time (4h and daily). **But upper-half stretches with no pump before them do
almost the same** (78% on 4h, 81% on the daily): the middle band is a 20-candle average that rises toward price during a sideways phase, and a wick
within 0.25 ATR is an easy touch. So part 1 is a property of the bands, not evidence for the pump. (About 45% of these
"touches" did not actually reach the band; they came within the tolerance.)

### Parts 2 and 3: "holds -> pump again, fails -> dump": not on average
On the fair test (1.5 ATR either way), a hold is right 48% (1h + 4h + 1D together, 1,444 cases; holdout 49%) and a
failure 51%: **on average the close at the middle band does not tell the direction.** The daily alone looks better
(holds 61%, 44 cases), but it is not proven (about 9% chance of noise, 3 holdout cases).

### Why it works and why it does not: the touch candle decides
Measured on the trader's own definition, "pump again" = a new high above everything so far before a close below the touch
low, five conditions at the touch are **real** (time-shift test p < 0.01, the holdout agrees), on 1h + 4h + 1D:

| At the touch of the middle band | New high, with it | Without it | Theory |
|---|---|---|---|
| **Wick rejection** (close in the top half of the candle) | **40%** | 26% | Bollinger / Wyckoff: buyers defend the base |
| **Volume >= 1.5x the sideways average** | **41%** | 29% | Wyckoff absorption: the selling is met |
| **Deep touch**: pierced > 0.25 ATR below the middle, still closed above | **40%** | 30% | ICT sweep / Wyckoff spring: stops under the level taken, then reclaimed |
| Daily above its EMA 200 | 35% | 27% | every school: only in a trend |
| **RSI already down to 40 – 50** | **16%** | 33% | momentum is gone: the pump has lost its force |

Together, the three defense signs (wick, volume, depth) give a clear gradient, the same on 1h and 4h and in the holdout:

| Defense signs at the touch | New high (2020 – Oct 2025) | Holdout |
|---|---|---|
| none | 24% (623 cases) | 17% |
| one | 34% (592) | 28% |
| two | 45% (179) | 61% |
| all three | 54% (50) | 46% (13) |

Likely but not proven (p < 0.05): when the crowd leans long at the touch (account long / short ratio above its 30-day
median), fewer holds pump (fair test 41% vs 48%): crowded late longs are the liquidity that gets flushed.

**Not real** (no difference that passes the test): the size of the pump, how long or how tight the sideways was, whether
the bands contracted, whether volume dried up during the sideways, a higher high during the sideways, three rejections at
the top, equal highs left at the top, and rising open interest during the sideways.

### How big the next move is
When the daily hold is confirmed by two more closes above the middle band, price made a new top before failing about half
the time (47%), the typical run was 1 ATR (7%), the top quarter of runs was 4.8 ATR or more, and 38% ran 3 ATR or more.
In about 6 of 10 cases the hold failed within 30 days. Big when it works, not always.

## 3. So, why it happens and why not

- **It pumps again** when the touch shows **real buyers defending the middle**: price pierces below it (taking the stops
  under the level), is pushed back with a long wick, on high volume, while momentum is still alive (RSI not collapsed to
  40 – 50), in a daily uptrend. That is Wyckoff's absorption / spring and ICT's sweep below equilibrium, at Bollinger's
  base. With all three defense signs, a new high comes about half the time (54%), twice as often as with none (24%).
- **It does not** when price **drifts** into the middle band: small candles, no wick, no volume, RSI already down to
  40 – 50. Nobody defends; the late buyers are trapped; the hold is an illusion and usually gives way.
- **The close at the middle band alone decides nothing** (48 – 51% on the fair test). The concept is right, but its signal
  is **how** the touch happens, not **whether** it closes above.
- Daily vs 4h: the same mechanism works on both (the gradient holds on 1h and 4h); the daily simply has few cases.

## 4. For the bot (not yet tested on the trades)

Two uses follow, both to be tested on the strategy's trades before anything is adopted:
1. **Context:** don't take a trade against a daily or 4h move whose middle-band touch shows two or three defense signs
   (27 Mar 2023: the daily touch pierced, wicked and held; our short went into it).
2. **Entry:** after a pump and sideways, buy the middle-band touch only with two or three defense signs, stop under the
   touch low, target the old high. Test it in R with costs before any use.

Audit: reports/bb_pause.md audited in rounds 9 – 11 (all findings fixed); reports/bb_pause_why.md and this document are
audited in round 12.
