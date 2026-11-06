# Indicators: what each one is, what the ETH data proves, and which to use for what

Evidence: `reports/indicator_learn.md` (every classic signal, one fair test), `reports/bollinger.md` (the outer band in
detail), `reports/indicator_deep.md` (every indicator, average, candlestick and structure signal in detail: which
conditions make it work or fail). Applied to the trades: `reports/learned.md`.

**Fair test:** at the signal close, does price move 1.5 ATR the way the signal claims before 1.5 ATR against (30 candles)?
A coin flip is 50%. **Real or noise:** each result is compared with 400 copies of the same signal moved to random dates
(the clustering of nearby events is kept). A result counts as **real** only if fewer than 1% of the copies match it
(p < 0.01) **and** the holdout (Nov 2025 on) points the same way. Of 635 detailed conditions tested (621 distinct),
**22 pass; noise alone would pass about 3.** Everything below that is not marked real is a tendency the data cannot prove.

The main rules (structure, levels, liquidity, closes) come first; indicators only support them.

## The short answer

| Indicator | Verdict | Proven use (p < 0.01, holdout agrees) | Not proven / do not use |
|---|---|---|---|
| **RSI (14)** | **use, as momentum** | 4h RSI crossing above 70 = **up** (59%, all 6 years, holdout 57%); the **first** push above 70 in 50 candles: **69%** (holdout 65%) | selling "overbought" / buying "oversold" (41%, lost every year); selling RSI leaving 70 inside a Bollinger bulge (4h 38%, 1h 41%) |
| **Volume** | **use, for breakouts** | a 4h 20-candle breakout on **>= 2x volume: 58%** vs 46% without (holdout 53%); closing **> 1 ATR** beyond: 62% (holdout 58%) | "1 - 2x volume fails" (a tendency, not proven) |
| **Bollinger (20, 2)** | **use, for move strength** | at the upper band, price goes further: 4h with a **bulge (62%)**, **RSI > 75 (64%)**, **the daily also at its band (58%)**; 1h with a close outside, a walk, expanding bands, or the 4h at its band (+3.6 to +4.9 pts). It fails back more often on 1h with an upper wick or the opposite band turning (-3.5 / -3.8 pts) | the band by itself (a tag or close outside is 50 – 52% overall); squeeze breakouts (not proven) |
| **EMA 20 / 50 / 200** | **context only** | none on 4h / daily. On 1h: an EMA 50 pullback with RSI 40 - 50 (Cardwell range) holds better (51% vs 43%, holdout 56%); the 1h golden / death cross 55% (holdout 51%) | the 4h golden cross (56% but 34% in the holdout), pullbacks to the EMA 20 (4h 45%), the EMA 200 retest (not proven) |
| **Candlesticks** | **only with context** | a 4h strong full-body candle **with the daily trend: 60%** vs 43% against (holdout 52%); in oversold (RSI < 40) the **1h engulfing (45%)** and the **4h hammer (40%)** fail | any pattern by itself: 40 – 55% on 1h / 4h; a few daily patterns look better (three white soldiers 61%, morning star 61%) on small samples, not proven |
| **Trendlines** | **mixed, no rule** | steep rejections fail on 4h (40%, holdout 35%) but do better on 1h (51% vs 47%, holdout +5): opposite on the two timeframes, so no usable rule. Rejections overall are 47 – 48% | "3 touches = strong" (not proven; the tendency is the opposite) |
| **Market structure** | price action is the main rule | no BOS / CHoCH condition passes (on 1h with ~900 cases each; on 4h / daily the samples are smaller) | |
| **Fibonacci** | only at confluence | none proven in this test | a level by itself |
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
Cardwell / Brown: in uptrends RSI lives in 40 – 80. **Proven on ETH:** above 70 is strength (59%), above all the first
push (69%). Selling it is the losing side (41%). Leaving 70 inside a bulge is not a sell (38% right on 4h). Wilder's
failure swing and RSI divergence: not proven either way.

### Volume
Participation. Edwards & Magee: real breakouts expand volume. **Proven:** >= 2x volume and a close > 1 ATR beyond the
range make a 4h breakout work (58 – 62%); the strategy's strong-breaking-candle rule already uses volume on the breaking
candle.

### Bollinger bands (John Bollinger)
Two readings: %b (where price is; the same as RSI) and BandWidth (volatility; new information). Bollinger's rules: tags
are not signals; closes outside are continuation more often than reversal; squeezes precede moves but often start with a
head fake; the opposite band turning ends a move. **Proven:** strength at the band means the move continues (4h: bulge,
RSI > 75, the daily at its band; 1h: a close outside, a walk, expanding bands, the 4h at its band), and on 1h an upper
wick or the opposite band turning means it fails back more often, as Bollinger says. On 4h a close outside is real in
2020 – 25 (52% vs 47%) but almost flat in the holdout; the 4h upper wick is not confirmed by the holdout. The
two-condition mixes in `reports/bollinger.md` are descriptive only.

### Moving averages
Smoothed price, so trend; they lag by design. **Proven:** no 4h / daily average signal. On 1h the Cardwell pullback (EMA
50 with RSI 40 – 50) and the golden / death cross (55%, holdout 51%) hold, but both are small edges on a noisy timeframe.
Use the daily EMA 200 for the regime and the EMAs for "is there a trend".

### Candlesticks and candle structure
No pattern works alone. **Proven:** a 4h strong full-body candle works with the daily trend (60%) and not against it
(43%); in oversold (RSI < 40) the 1h engulfing (45%) and the 4h hammer (40%) fail. Tendencies (not proven): a hammer
just above an untaken low fails (38%), because that low is liquidity and is taken first; an engulfing at the lower band
does better (56%).

### Trendlines
Mixed: steep lines fail as support on 4h (40%) but hold slightly better on 1h (51%). No usable steepness rule.
Tendency: more touches = more likely to break, because stops gather under the line (liquidity).

### MACD (Appel; histogram by Aspray)
Two EMAs' difference: the same information as the EMAs and RSI. Nothing on 4h / daily; the 1h cross (52%) is real but too
small to trade, and it only improves with context that works without MACD. Dropped.

### Fibonacci
Not proven as a signal in this test. In the strategy it is used only for the 1D-bounce stop below the 0.786, which
helped in the strategy test (`reports/fixes.md`); a Fib level alone is never used.

## The 5 Dec 2023 trade read with these rules
At the 4 Dec 08:00 4h top (2,277): bulge, RSI 81 after 85, the daily at its upper band, daily trend up: all three proven
"keep going" signs. So no big short; the pullback goes to the middle band (2,186 vs 2,177) and the long is where the
middle band holds on the close (2,200). That matches the trader's read.

## What this means for the bot (tested on the trades, `reports/learned.md`)
Every lesson was turned into a filter before looking at the trades and run on the current best version (100 trades
2022 - Oct 2025, 27 holdout). **None improved it in a meaningful way.** The weak-band-touch rule skips a single losing
trade; two rules never fire (the strong-breaking-candle rule already removes those trades); every other rule skips a set
of trades whose total R is **positive** in both periods, so skipping them loses money. The best version already holds what
worked in the strategy tests (volume on the breaking candle, which is also proven here; waiting for the 4h close and the
0.786 bounce stop, which helped in the strategy tests). The losses left are about **liquidity**: targets beyond big
liquidity (4,099 on 22 Nov 2024) and stops just inside it (5 Dec 2023, 22 Nov 2024).
