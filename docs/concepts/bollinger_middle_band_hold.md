# The middle-band hold after a pump: theory and evidence

**The concept (the trader's words):** when price goes sideways on the upper Bollinger band after a pump, it usually
comes to the middle band. If it holds there, it pumps again. If it cannot hold, it dumps.

Evidence: `reports/bb_pause.md` (the sequence, its size, the concept in full) and `reports/bb_pause_why.md` (why it
works and why it fails). Events on 1h, 4h and daily ETH, mirrored for dumps, 2020 - Oct 2025, holdout Nov 2025 on.

## 1. What the theory says

The same pattern appears under different names in every school, and each one explains a part of it.

Sources are mostly secondary (trading-education pages and search summaries of the authors' sites); they were not all
re-checked against the original books.

| School | Its name for it | What it says happens at the middle |
|---|---|---|
| **John Bollinger** | a pause in a band walk; the 20-period average as the trend's base | In a strong trend the middle band is support; tags of the upper band are not sell signals; a close back at / below the middle band after a walk is the sign momentum is fading. ([TradingView](https://in.tradingview.com/support/solutions/43000501840/), [Capital.com](https://capital.com/en-au/learn/technical-analysis/bollinger-bands)) |
| **Wyckoff** | re-accumulation after a markup; the test / spring; the last point of support (LPS) | After a sign of strength, a pullback to former resistance on smaller spread and volume (a test on high volume means supply is still there) that holds as a higher low is the LPS before the next markup; a spring dips under support and recovers; a close back below the spring low cancels the read, and a failed test means distribution, not accumulation. ([StockCharts](https://articles.stockcharts.com/article/articles-wyckoff-2016-04-wyckoff-buy-strategies/), [LuxAlgo](https://www.luxalgo.com/library/concept/spring.md)) |
| **Al Brooks** | the first pullback to the moving average in a strong trend; the 20-gap bar | After 20 or more bars on one side of the average (a 20-gap bar), a pullback to it is likely; the first touch is usually followed by a test of the trend's extreme (often only a test, not a big new leg). Our events need only 3 sideways candles, so his rule applies only loosely. ([Brooks, Trading Price Action, ch. 13 – 14](https://www.oreilly.com/library/view/trading-price-action/9781118172339/OEBPS/9781118172339_epub_c_14.htm)) |
| **Bulkowski** | the flag / pennant after a flagpole | Flags continue, but less reliably than people think: a 44% break-even failure rate and a 9% average rise for flags, 54% and 7% for pennants; the best flags have a long, near-vertical pole. ([thepatternsite.com flags](https://thepatternsite.com/flags.html), [pennants](https://thepatternsite.com/pennants.html)) |
| **ICT / smart money** | equilibrium of the dealing range; a liquidity sweep before continuation | The midpoint of the leg is equilibrium: below it is discount. Price sweeps the liquidity resting under the lows (late buyers' stops), then continues to the liquidity above the old high. ([LuxAlgo](https://www.luxalgo.com/library/concept/premium-and-discount/), [Equiti](https://www.equiti.com/jo-en/news/trading-ideas/ict-50-percent-rule-premium-discount-fvg/)) |
| Elliott | wave 4 | A sideways, shallow correction after the strongest wave (3), before a final wave 5. |

**The mechanism the schools describe** (a theory; section 2 shows how much of it the data can confirm). The pump brings in late buyers. While price goes sideways, their average entry
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

### Why it works and why it does not: what the data can and cannot show
The trader's own definition, "pump again" = a new high above everything so far, is measured before a close 0.5 ATR below
the middle band (a failure level that does not depend on the touch candle; 1h + 4h + 1D: 40% of holds made a new high).
**Geometry first:** how far the close is from the old high, and how far from the failure level, decides a lot by
itself (closer to the high = more new highs). Conditions like a long wick or a deep touch change those distances, so each
condition is compared **within groups of the same timeframe and the same two distances**.

| At the touch (holds, 1h + 4h + 1D) | Raw difference | **At the same distances** | Verdict |
|---|---|---|---|
| Wick rejection (close in the top half) | +13 pts | +1 pt | geometry: the close sits nearer the old high |
| Volume >= 1.5x the sideways average | +6 pts | +3 pts | not proven |
| Deep touch (pierced > 0.25 ATR below the middle) | -1 pt | +3 pts | not proven |
| Swept the sideways low (a real sweep / spring) | -6 pts | -3 pts | not proven |
| RSI down to 40 – 50 | -16 pts | -4 pts | geometry: the old high is further away |
| Daily above its EMA 200 | +9 pts | +5 pts (p 0.08) | a tendency, not proven |
| **Bands contracted during the sideways** (width <= 0.8x the pump's) | +10 pts | **+8 pts (p 0.02, holdout +6)** | **likely** |
| Crowd leaning long at the touch (long / short ratio above its 30-day median) | -6 pts | -9 pts (p 0.03) | the holdout points the other way: not proven |

On the failures the same squeeze matters the other way: when the bands contracted during the sideways, a failed hold dumped
to the sideways low **less** often (-12 points at the same distances, p 0.002; 83 cases, 12 in the holdout). Nothing else
about the pump, the sideways or the touch candle passes once the geometry is removed. On the fair test (1.5 ATR either
way) none of the conditions moves the result.

An earlier version of this document credited the wick, the touch volume and a deep touch with a clean gradient (24% ->
54% new highs). That was measured with a failure level at the touch candle's own low, which those conditions push
further away; it was geometry, not buyers defending (audit round 12).

### How big the next move is
When the daily hold is confirmed by two more closes above the middle band, price made a new top before failing about half
the time (47%), the typical run was 1 ATR (7%), the top quarter of runs was 4.8 ATR or more, and 38% ran 3 ATR or more.
In about 6 of 10 cases the hold failed within 30 days. Big when it works, not always.

## 3. So, why it happens and why not

- **What is solid:** after a pump and sideways, price does come back to the middle band (but that is how the bands
  behave anyway), and on the daily a hold was followed by the trend 61% of the time (44 cases, not yet proven).
- **The one condition the data supports:** the move continues more often when the bands **contract** during the sideways
  pause. That is Bollinger's squeeze inside a trend: volatility is stored and released in the trend's direction. When the
  bands stay wide during the pause, the market is still fighting, and the middle band is less reliable.
- **What the data cannot confirm:** that a wick, volume or a sweep at the middle band (buyers defending, Wyckoff
  absorption, an ICT sweep) makes the pump more likely. Once the distance to the old high and to the failure level are
  held equal, none of them shows an effect. This does not prove the theory wrong; it means our measurements of
  "defense" do not capture it, or the samples are too small.
- **The close at the middle band alone decides nothing** on 1h / 4h (47 – 51% on the fair test). The daily looks better but
  has only 44 + 20 cases.

## 4. Next steps

1. **More daily cases:** ETH has only ~65 daily events. The same test on BTC and the other coins in `data/klines` would
   multiply the daily sample and show whether the daily effect (61%) is real.
2. **Test on the trades,** before any use: (a) no trade against a daily trend pausing above its middle band while the bands
   contract; (b) the entry from a daily hold with contracting bands, stop below the failure level, target the old high,
   in R with costs.

Audit: reports/bb_pause.md audited in rounds 9 – 11; reports/bb_pause_why.md and this document in round 12 (its main
finding, the geometry, is fixed here) and round 13.
