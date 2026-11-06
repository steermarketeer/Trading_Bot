# Indicators: what each one is, what the ETH data proves, and which to use for what

Evidence: `reports/indicator_learn.md` (every classic signal, one fair test), `reports/bollinger.md` (the outer band in
detail), `reports/indicator_deep.md` (every indicator, average, candlestick and structure signal in detail: which
conditions make it work or fail). Applied to the trades: `reports/learned.md`.

**Fair test:** at the signal close, does price move 1.5 ATR the way the signal claims before 1.5 ATR against (30 candles)?
A coin flip is 50%. **Real or noise:** each result is compared with 400 copies of the same signal moved to random dates
(the clustering of nearby events is kept). A result counts as **real** only if fewer than 1% of the copies match it
(p < 0.01) **and** the holdout (Nov 2025 on) points the same way. Of 851 detailed conditions tested (834 distinct),
**26 pass; noise alone would pass about 4.** Everything below that is not marked real is a tendency the data cannot prove.

The main rules (structure, levels, liquidity, closes) come first; indicators only support them.

Audit: independent rounds 1 - 8 (code and every number in this document); all result-impacting findings fixed; the
Ichimoku part and the fixes ranking passed round 8 with no result-impacting issue.

## The short answer

| Indicator | Verdict | Proven use (p < 0.01, holdout agrees) | Not proven / do not use |
|---|---|---|---|
| **RSI (14)** | **use, as momentum** | 4h RSI crossing above 70 = **up** (59%, all 6 years, holdout 57%); the **first** push above 70 in 50 candles: **69%** (holdout 65%) | selling "overbought" / buying "oversold" (41%, lost every year); selling RSI leaving 70 inside a Bollinger bulge (4h 38%, 1h 41%) |
| **Volume** | **use, for breakouts** | a 4h 20-candle breakout on **>= 2x volume: 58%** vs 46% without (holdout 53%); closing **> 1 ATR** beyond: 62% (holdout 58%) | "1 - 2x volume fails" (a tendency, not proven) |
| **Bollinger (20, 2)** | **use, for move strength** | at the upper band, price goes further: 4h with a **bulge (62%)**, **RSI > 75 (64%)**, **the daily also at its band (58%)**; 1h with a bulge (58%), RSI > 75 (61%), a close outside, a walk, expanding bands, or the 4h at its band (+3.6 to +4.9 pts). It fails back more often on 1h with an upper wick or the opposite band turning (-3.5 / -3.8 pts). The 4h close outside (52% vs 47%), the 1h opposite band and the 1h '4h at its band' pass the rule only by a nearly flat holdout (within 0.4 pts): weak | the band by itself (a coin flip on 1h / 4h: band reaches go further 50% / 49%; on the daily band reaches go further 58%, not proven); squeeze breakouts (not proven) |
| **EMA 20 / 50 / 200** | **context only** | none on 4h / daily. On 1h: an EMA 50 pullback with RSI 40 - 50 (Cardwell range) holds better (51% vs 43%, holdout 56%); the 1h golden / death cross 55% (holdout 51%) | the 4h golden cross (56% but 34% in the holdout), pullbacks to the EMA 20 (4h 45%), the EMA 200 retest (not proven) |
| **Candlesticks** | **only with context** | a 4h strong full-body candle **with the daily trend: 60%** vs 43% against (holdout 52%); in oversold (RSI < 40) the **1h engulfing (45%)** and the **4h hammer (40%)** fail | any pattern by itself: 40 – 55% on 1h / 4h; a few daily patterns look better (three white soldiers 61%, morning star 61%) on small samples, not proven |
| **Trendlines** | **mixed, no rule** | steep rejections fail on 4h (40%, holdout 35%) but do better on 1h (51% vs 47%, holdout +5): opposite on the two timeframes, so no usable rule. Rejections overall are 47 – 48% on 1h / 4h (52% on the daily) | "3 touches = strong" (not proven; the tendency is the opposite) |
| **Market structure** | price action is the main rule | no BOS / CHoCH condition passes (on 1h with ~900 cases each; on 4h / daily the samples are smaller) | |
| **Fibonacci** | only at confluence | none proven in this test | a level by itself |
| **Ichimoku** | **promising on the daily, not proven** | on 1h a Kijun bounce works with RSI > 60 (57% vs 47%, holdout 57%) or expanding bands (53% vs 46%) and fails above a thick cloud (44% vs 54%, holdout 45%); entering the cloud from below does worse with the Chikou free (46% vs 52%; weak: holdout only -1 pt) | daily cloud breakout 62% (p 0.007) and the full Hosoda breakout (Chikou free, bullish future cloud) 69% (36 cases, p 0.010), 4h kumo twist 57% (p 0.002): all strong in 2020 - 25 but **against in the holdout** (42%, 40%, 44% on 12, 5, 55 cases); TK crosses 51 – 54%; Kijun bounces 47 – 49% on 1h / 4h |
| **MACD** | **drop** | nothing on 4h / daily. On 1h a cross is right 52% (real but too small to use); it does better with expanding bands, volume or liquidity ahead (+5 – 6 pts), which is the context, not MACD | every MACD signal on its own; it repeats the EMAs (0.94) and RSI (0.87) |
| **ATR** | use for distances | | direction |

Three rules from the data, before any single indicator:

1. **On the 1h almost everything is a coin flip (46 – 55%).** Decisions belong on the 4h and the daily; the 1h and 15m
   only time the entry.
2. **Most indicators say the same thing.** On 4h, RSI, %b, distance from EMA 20 and the 20-candle return correlate
   0.77 – 0.98; MACD correlates 0.94 with the distance from EMA 50. Only **BandWidth** and **volume** carry new
   information (correlations near 0). Bollinger's own rule: don't stack indicators that measure the same thing. So the
   set is price action + RSI (momentum) + BandWidth (volatility) + volume + the daily EMA 200 (regime).
3. **Liquidity pulls price.** On the 1h, five different signals (engulfing, EMA 20 reclaim, MACD cross, trendline
   rejection, volume breakout) all work better, by 4 – 8 points (real, holdout agrees), when an **untaken swing high sits
   within 1 ATR ahead**. Price goes to the nearby liquidity, as you teach.

## Each indicator

### RSI (Wilder, 1978)
Momentum: the share of up-moves over 14 candles. Wilder used failure swings and divergences, never "70 = sell".
Cardwell / Brown: in uptrends RSI lives in 40 – 80. **Proven on ETH, on the 4h:** above 70 is strength (59%), above all
the first push (69%). Selling it is the losing side (41%). Leaving 70 inside a bulge is not a sell (38% right on 4h, 41%
on 1h). On the 1h (53%) and the daily (49%) the 70 cross itself is not proven. Wilder's failure swing and RSI
divergence: not proven either way.

### Volume
Participation. Edwards & Magee: real breakouts expand volume. **Proven:** >= 2x volume and a close > 1 ATR beyond the
range make a 4h breakout work (58 – 62%). The strong-breaking-candle filter (>= 1.2x volume, body >= 60%, range >= 1.5
ATR) is not in the research-chosen version (see the last section).

### Bollinger bands (John Bollinger)
Two readings: %b (where price is; the same as RSI) and BandWidth (volatility; new information). Bollinger's rules: tags
are not signals; closes outside are continuation more often than reversal; squeezes precede moves but often start with a
head fake; the opposite band turning ends a move. **Proven:** strength at the band means the move continues (4h: bulge,
RSI > 75, the daily at its band; 1h: bulge, RSI > 75, a close outside, a walk, expanding bands, the 4h at its band), and
on 1h an upper wick or the opposite band turning means it fails back more often, as Bollinger says. The 4h close outside
(52% vs 47%) passes only by a nearly flat holdout (+0.2 pts), as do the 1h opposite band and the 1h '4h at its band'
(within 0.4 pts): weak. The 4h upper wick is not confirmed by the holdout. The
two-condition mixes in `reports/bollinger.md` are descriptive only.

### Moving averages
Smoothed price, so trend; they lag by design. **Proven:** no 4h / daily average signal. On 1h the Cardwell pullback (EMA
50 with RSI 40 – 50) and the golden / death cross (55%, holdout 51%) hold, but both are small edges on a noisy timeframe.
Use the daily EMA 200 for the regime and the EMAs for "is there a trend".

### Candlesticks and candle structure
No pattern works alone. **Proven:** a 4h strong full-body candle works with the daily trend (60%) and not against it
(43%); in oversold (RSI < 40) the 1h engulfing (45%) and the 4h hammer (40%) fail. Tendencies on the 4h (not proven): a hammer
just above an untaken low fails (38%), because that low is liquidity and is taken first; an engulfing at the lower band
does better (56%). On the 1h the engulfing at the lower band does slightly worse (48%), so even the tendency is not general.

### Trendlines
Mixed: steep lines fail as support on 4h (40%) but hold slightly better on 1h (51%). No usable steepness rule.
Tendency: more touches = more likely to break, because stops gather under the line (liquidity).

### Ichimoku (Goichi Hosoda)
Five lines: Tenkan (9-candle midpoint), Kijun (26), the cloud (Senkou A = Tenkan/Kijun midpoint, Senkou B = 52-candle
midpoint, both drawn 26 candles ahead) and the Chikou (the close drawn 26 back). Hosoda's reading: price above the cloud =
uptrend; a TK cross is strong above the cloud, neutral inside, weak below; a cloud breakout needs the Chikou clear of the
old candles and a bullish cloud ahead; the Kijun is the equilibrium price that pullbacks return to; a price inside the
cloud tends to travel to the other edge. **On ETH:** the lines repeat the averages (price vs Kijun correlates 0.93 with
price vs EMA 20, price vs the cloud 0.94 with price vs EMA 50, 4h). The daily cloud breakout, the full Hosoda breakout
and the 4h kumo twist were strong in 2020 - 25 (57 – 69%) but went the other way in the holdout on few cases, so they are
promising, not proven. Proven only on the 1h: the Kijun bounce needs momentum (RSI > 60) or expanding bands and fails above a thick
cloud.
The TK cross, the Kijun bounce on 4h, edge-to-edge and the Chikou cross are coin flips.

### MACD (Appel; histogram by Aspray)
Two EMAs' difference: the same information as the EMAs and RSI. Nothing on 4h / daily; the 1h cross (52%) is real but too
small to trade, and it only improves with context that works without MACD. Dropped.

### Fibonacci
Not proven as a signal in this test. In the strategy it is used only for the 1D-bounce stop below the 0.786, which
helped in the strategy test (`reports/fixes.md`); a Fib level alone is never used.

## The 5 Dec 2023 trade read with these rules
At the 4 Dec 08:00 4h top (2,277): bulge, RSI 81 after 85, the daily at its upper band (the three proven "keep going"
signs), in a daily uptrend. So no big short; the pullback goes to the middle band (2,186 vs 2,177) and the long is where the
middle band holds on the close (2,200). That matches the trader's read.

## What this means for the bot (tested on the trades, `reports/learned.md`)
The version the selection rule picks on 2022 - Oct 2025 is **v3.1 + the journal filters + the 1D-bounce stop below the
0.786** (129 trades, 59% win, +0.79R; holdout 33 trades, 64%, +1.02R; `reports/fixes.md`). The strong-breaking-candle
filter is **not** part of it: on that version it cuts 2022 - 25 trades from 129 to 100 for +0.79 -> +0.83R, so the
t-score falls (5.53 -> 4.98); its clear gain is only in the holdout (+1.02 -> +1.28R), which cannot be used to choose it.

Every lesson above was turned into a filter before looking at the trades and run on that version. **None improved it in a
meaningful way.** By the 2022 - 25 t-score the base scores 5.53; the best filter, the weak band touch, scores 5.62 by
skipping a single losing trade (noise, not a rule); all of the first four together 5.56. Two filters never fire (fading
momentum never occurs on these trades; thin volume < 1x never occurs either). The others skip sets of trades whose total R
is positive in 2022 - 25 (the 2x-volume rule R6 skips +4.36R; in the holdout its 3 skipped trades were -0.50R), so they
cost more than they save. The 4h-close lesson is a strong marker (trades whose first 4h close goes back against the entry
win 29% vs 59%, `reports/selfreview.md`), but it is only known after the entry. The retest entry built on it earned more
per trade in 2022 - 25 (+0.82R vs +0.71R) but took only 44 trades instead of 129, too few for the selection rule
(>= 60), and earned less in the holdout (+0.52R vs +0.68R), so it was not adopted (`reports/fixes.md`).

Where the remaining losses come from: across all v3.1 trades, a **resistance or untaken 4h high between the entry and the
target** goes with losing (win 43% when present vs 68% when absent; holdout 48% vs 100%; it is present in most trades, and
the self-review table has no significance test, `reports/selfreview.md`), and the journal shows it on 22 Nov
2024 (the 3R target beyond the 4,099 top). The journal's two stops just inside the liquidity (5 Dec 2023, 22 Nov 2024)
are single examples: systematically, untaken liquidity just beyond the stop does **not** mark losers (41% of losers vs 39%
of winners, holdout 44% vs 46%, `reports/selfreview.md`).
