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
On the fair test (1.5 ATR either way), a hold is right 47% (1h + 4h + 1D together, 1,449 cases; holdout 49%) and a
failure 51%: **on average the close at the middle band does not tell the direction.** The daily alone looks better
(holds 61%, 44 cases), but it is not proven (about 9% chance of noise; 4 holdout cases, 1 right).

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
| Bands contracted during the sideways (width <= 0.8x the pump's) | +10 pts | +8 pts (p 0.02) | a lead only: it comes from the 1h (1h alone +11 pts, p 0.005; 4h -1 pt; daily too few); holdout at the same distances +0.4 pt; the best of ~20 conditions x 3 timeframes |
| Crowd leaning long at the touch (long / short ratio above its 30-day median) | -6 pts | -9 pts (p 0.03) | the holdout points the other way: not proven |

On the failures nothing passes either. (Measured with a target that includes the touch candle's own low, the same way the
hold's target includes its high; an earlier run left the touch low out, so in 86% of failures the target had already
been hit by the touch candle itself, which made "a sweep of the sideways low" and "the squeeze" look decisive. They are
not: +1 pt and -1 pt once measured symmetrically. One condition, a deep touch, shows +21 pts at p 0.04, but with ~20
conditions tested one such result is expected by chance.) On the fair test (1.5 ATR either way) no condition passes on either side (the best, the crowd leaning long, has p 0.05
among ~20 tests).

An earlier version of this document credited the wick, the touch volume and a deep touch with a clean gradient (24% ->
54% new highs). That was measured with a failure level at the touch candle's own low, which those conditions push
further away; it was geometry, not buyers defending (audit rounds 12 and 13).

### How big the next move is
When the daily hold is confirmed by two more closes above the middle band, price made a new top before failing about half
the time (47%), the typical run was 1 ATR (7%), the top quarter of runs was 4.8 ATR or more, and 38% ran 3 ATR or more.
In about 6 of 10 cases the hold failed within 30 days. Big when it works, not always.

## 3. So, why it happens and why not

- **What is solid:** after a pump and sideways, price does come back to the middle band (but that is how the bands
  behave anyway), and on the daily a hold was followed by the trend 61% of the time (44 cases, not yet proven).
- **What the data cannot confirm:** any reason **why** one hold pumps and another fails. Once the distance to the old
  high and to the failure level are held equal, none of the pump, sideways or touch conditions makes a difference that
  survives: not the wick, the volume, a deep touch or a sweep (the buyers-defending / Wyckoff absorption / ICT sweep
  story), not the daily trend, not the RSI. The only lead is a squeeze during the pause on the 1h (Bollinger's idea that
  stored volatility is released in the trend's direction), and it is not seen on the 4h or in the holdout.
- This does not prove the theory wrong. It means either our measurements of "defense" do not capture what a trader sees,
  or ETH alone has too few clean cases, above all on the daily, where the concept looks strongest.
- **The close at the middle band alone decides nothing**: 47% / 51% for holds / failures over 1h + 4h + 1D together (4h
  failures 56%, not proven).

## 4. Six coins and the weekly chart

**Six coins** (BTC, ETH, BNB, SOL, XRP, DOGE; `reports/bb_pause_coins.md`): the daily hold is right **52%** (236 cases, 90%
range 46 – 58%) and the 4h hold 50% (1,500 cases); failures 53% / 52%. ETH's daily 61% was the best of the six (BTC 48%,
XRP 46%). Conditions (compared at the same distances, groups pooled across coins, p by a bootstrap of calendar
months because coins move together): 52 tested, 7 reach p < 0.05 (about 3 expected by chance), **none survives a
false-discovery correction**. Leads on the 4h only, not proven: equal highs left at the top of the sideways (holds +15 pts,
holdout +25), a wick rejection at the touch (+11, holdout +20).

**The weekly chart** (`reports/bb_pause_weekly.md`; weeks open Monday 00:00 UTC). First split (W1 - W3): daily holds
*with* a bullish weekly did worse (43% vs 61% for the weekly middle band). After seeing that, the trader explained it: the
daily pause is followed by a new pump when *the weekly has not yet reached its highest value*. That explanation was
turned into three readings and tested once; it is **post hoc** (proposed after the first split was seen):

| Daily holds, six coins (fair test) | The weekly has room | It does not |
|---|---|---|
| the weekly candle has not reached its upper band | 56% (137) | 42% (85) |
| an older weekly high (5 – 52 weeks back) is still above price | 52% (162) | 32% (40) |
| weekly RSI below 70 | 53% (183) | 41% (39) |
| **all three** (2020 – Oct 2025) | **57% (120)** | **35% (82)** |
| all three, holdout (Nov 2025 on) | 42% (26) | 69% (16) |

The split points the way the trader says, but it is weaker than it looks:
- it largely re-describes the first split: 70 of the 82 "no room" holds are weeks above a rising weekly middle band.
  Within those weeks the room effect is 49% vs 34%; within the others 61% vs 42% (12 cases);
- at the same distances to the target and the failure level the far-target difference is +5 points (p 0.48);
- it is one of six weekly readings plus a combination, inside a study of about 50 conditions, after the data was seen;
- the holdout points the other way (42% vs 69%, on 26 and 16 cases); on the 4h the weekly makes no difference.
So it is a hypothesis to test on new data, not a finding.

**Follow the weekly.** The trader's next reading (also post hoc): after the touch, price follows the weekly trend whatever the touch
candle does (a bearish weekly turns a daily pump down at the middle band; a bullish weekly turns a daily dump up). On the
six coins, following the weekly after the touch was right **44% on the daily** (221 – 281 cases, 2020 - Oct 2025) and
48 – 49% on the 4h; the holdout, mostly a falling market, was 63 – 64% on the daily and 51 – 52% on the 4h. The two periods
disagree, so this is not a rule either (`reports/bb_pause_weekly.md`).

**"Touches the middle, keeps on the upper side, then the pump comes"** (`reports/bb_pause_stay.md`). Decided after the
first N closes after the touch all stay above the middle band:

| New high above everything so far (six coins, 2020 - Oct 2025) | 1 close above | 2 | 3 | 5 |
|---|---|---|---|---|
| daily, after a pump and sideways | 36% | 40% | 46% | 48% |
| daily, holdout | 38% | 43% | 46% | 56% |
| 4h, after a pump and sideways | 37% | 40% | 44% | 49% |
| 4h, holdout | 36% | 42% | 47% | 59% |

The longer price keeps on the upper side, the more often the new high comes, in both periods. But each close above the
middle also brings price closer to the old high (median 1.9 -> 1.4 ATR) and further from the failure level, and at the
same distances the trader's sequence does **not** beat an ordinary middle-band hold (-0 to -8 points; holdout -3 to +8).
On the fair test (1.5 ATR either way) all of these are 48 – 56%. So "it keeps on the upper side" describes a move that is
already working; it does not add a prediction beyond how far the old high is.

## 5. Next steps

1. **The weekly-room rule** is the lead to follow: watch it on new data (the holdout grows every week) before using it.
2. **Test on the trades,** before any use: (a) no trade against a daily trend pausing above its middle band; (b) the entry from a daily
   hold, stop below the failure level, target the old high, in R with costs. (The squeeze is not used: it is a 1h-only
   lead.)

Audit: reports/bb_pause.md audited in rounds 9 – 11; reports/bb_pause_why.md and this document in rounds 12 and 13 (the
geometry and the fail-side target are fixed here) and round 14.
