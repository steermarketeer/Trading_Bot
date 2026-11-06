# Indicators: what each one is, what the ETH data says, and which to use for what

Evidence: `reports/indicator_learn.md` (every classic signal, one fair test) and `reports/bollinger.md` (the upper / lower
band in detail). Fair test: at the signal close, does price move 1.5 ATR the way the signal claims before 1.5 ATR
against? A coin flip is 50%. A signal counts only if it beats 50% in most years **and** in the holdout. The main rules
(structure, levels, liquidity, closes) come first; indicators only support them.

## The short answer

| Indicator | Measures | Verdict | Use it for | Do not use it for |
|---|---|---|---|---|
| **Volume** | participation | **use** | confirming a breakout close; spotting buyers slowing | anything alone |
| **RSI (14)** | momentum | **use, read as momentum** | strength: RSI > 70 at a breakout / at the upper band = continuation | selling "overbought" or buying "oversold" (wrong on ETH, every year) |
| **Bollinger (20, 2)** | volatility (BandWidth) and stretch (%b) | **use, two parts only** | BandWidth: bulge / expanding = strong move, contracting + wick = failing; the middle band as the pullback reference **in a strong move** | a tag or a close outside the band as a signal by itself |
| **EMA 200 (daily)** | the long-term regime | **use as context** | which side to favour, and how much to trust a failure | entries; crosses |
| EMA 20 / 50 | short trend | context only | stacked trend = trend exists | crosses, pullbacks to the EMA 20 as entries (lose on 4h) |
| **MACD** | momentum (difference of two EMAs) | **drop** | at most divergence as a note | any signal: no edge on any timeframe, and it repeats the EMAs and RSI |
| Fibonacci | where a pullback may stop | use only at confluence | stop below the 0.786; targets only where liquidity agrees | a level alone |
| ATR | volatility size | use | stop and target distances, tolerances | direction |

Two rules from the data, before any single indicator:

1. **On the 1h, every indicator signal is close to a coin flip (45 – 55%).** Indicators carry information only on the 4h and
   the daily. Decisions use the 4h / daily; the 1h and 15m only time the entry.
2. **Most indicators say the same thing.** On the 4h, RSI, %b, distance from EMA 20 and the 20-candle return have
   rank correlations of 0.85 – 0.98: they all measure where price is relative to its recent average. MACD correlates
   0.94 with the distance from EMA 50. Only **BandWidth** (volatility) and **volume** carry information the others do
   not (correlations near 0). John Bollinger's own rule: do not stack indicators that measure the same thing. So the
   set is: price action + **one** momentum gauge (RSI) + **one** volatility gauge (BandWidth) + **volume** + the
   **daily EMA 200** for the regime.

## Each indicator

### Volume
- What: how much traded. Edwards & Magee: a real breakout comes with expanding volume; a breakout on thin volume is
  suspect. Liquidity is where volume trades; "buyers slowing" is volume fading on each push.
- Data: a 20-candle breakout close with volume >= 1.5x average is right **56%** on 4h (5 of 6 years) and **61%** on
  the daily (5 of 5); the same breakout on low volume is right **44%** (4h, 1 of 5 years). Holdout 4h is weaker (47%,
  128 cases), so it confirms, it does not decide.
- Use: confirm breakouts by the breaking candle's volume (already in the strong-breaking-candle filter, which helped);
  read fading volume on pushes as the buyers slowing. Never alone.

### RSI (Wilder, 1978)
- What: momentum, the share of up-moves in the last 14 candles. Wilder himself used failure swings and divergences,
  not "above 70 = sell". Andrew Cardwell / Constance Brown: in an uptrend RSI lives in 40 – 80 and readings above 70
  are strength.
- Data (4h): RSI crossing **above 70** is right as a *bullish* signal **59%**, in **6 of 6 years**, holdout 57%.
  Selling it ("overbought") is right **41%**, 0 of 6 years. Leaving the extreme (back below 70) as a sell: 46%, 0 of 6.
  At the upper Bollinger band, RSI > 75 means price went further **64%** (holdout 63%).
  Divergence: 49% on 4h, no edge. The Cardwell 40 – 50 dip: 52%, small.
- Use: RSI is the momentum gauge. A high RSI argues **against** shorting and **for** holding / buying the pullback.
  It is the strongest single indicator signal we have, and it is read the opposite of the textbook.

### Bollinger bands (John Bollinger)
- What: a 20-candle average with bands 2 standard deviations away. Two separate readings: **%b** (where price is in the
  bands: the same information as RSI, correlation 0.91) and **BandWidth** (how wide the bands are: volatility, new
  information). Bollinger's rules: tags are not signals; a close outside is a continuation sign more often than a
  reversal; a squeeze precedes a big move but often starts with a head fake; walking the band = strong trend; when the
  opposite band turns back after a bulge, the move is ending; M tops / W bottoms are confirmed by a close through the
  middle band.
- Data (4h, fair symmetric test): a close outside the band alone: **50%** (coin flip, as Bollinger says). Squeeze
  breakout: 46 – 47%, often a head fake. Band failure (close outside, then back inside) as a reversal: 53%, holdout 54%:
  small. **What decides whether price goes further from the upper band:**

  | At the upper band (4h) | Went further | Holdout |
  |---|---|---|
  | bulge (BandWidth in the top 20% of 120 candles) | **62%** | 60% |
  | RSI > 75 | **64%** | 63% |
  | the daily also at its upper band | 58% | 55% |
  | bulge + RSI > 75 | **68%** | 84% (19 cases) |
  | squeeze breakout + daily trend down | **41%** | 43% |
  | upper wick + daily trend down | **43%** | 44% |
  | bands not expanding + upper wick (1h) | **44%** | 45% |

  So **a stall at the upper band in a bulge with RSI > 75 and the daily at its band is a pause**: price comes back to
  the middle band and goes higher (5 Dec 2023: every one of these was present at the 2,277 top). **A touch with an upper
  wick while the bands stop expanding, or against the daily trend, fails back.**
- Use: BandWidth tells the move's strength; the middle band is the pullback target / support only in a strong move.
  Never trade a tag or a close outside by itself.

### Moving averages (EMA 20 / 50 / 200)
- What: smoothed price, i.e. trend. They lag by design.
- Data: crosses are 51 – 56% on every timeframe; the 4h golden cross was 56% in 6 of 6 years but **34% in the holdout**
  (44 cases). **Buying a pullback to the EMA 20 in a stacked uptrend on 4h: 45%, 1 of 6 years** (it loses).
  The EMA 50 pullback: 50%.
- Use: the daily EMA 200 as the regime (which side, and whether a failure is a reversal or only a pullback, the
  definitions' context rule). Not entries.

### MACD (Appel; histogram by Aspray)
- What: EMA 12 minus EMA 26, and its 9-EMA signal line: smoothed momentum built from moving averages.
- Data: line / signal crosses 45 – 53% on every timeframe (the 'cross above zero' version is the worst, 45% on 4h); histogram turns 49 – 53%; zero crosses 51 – 54%;
  divergence 47 – 54% with small samples. It correlates 0.94 with the distance from EMA 50 and 0.87 with RSI.
- Verdict: drop it as a signal. It adds nothing that RSI and the EMAs do not already say, and none of its signals beat
  a coin flip reliably. On the charts it can stay as a picture.

### Fibonacci
- Earlier tests (`reports/fibliq.md`, `reports/fixes.md`): a Fibonacci level alone does nothing; the stop below the 1h
  leg's 0.786 improved the 1D bounces in both periods; extension targets did not. Use only where it meets a level or
  liquidity.

### ATR (Wilder)
- Volatility size, no direction. It sets distances: stops beyond the liquidity by a fraction of ATR, tolerances for
  touches and equal highs, the fair-test distance above.

## The 5 Dec 2023 trade read with these rules

At the 4 Dec 08:00 4h top (2,277): bulge, bands expanding, RSI 81 after 85, volume 2x, the daily at its upper band,
daily trend up. Weakness only from the upper wick and the %b non-confirmation. Verdict: a pause in a strong move, so
**no big short**; the short is only to the middle band (it reached 2,186 vs the band at 2,177), and the long is where
the middle band holds on the close (2,200). That matches the trader's reading. Across all 1D bounces, a pullback to the
4h middle band within 3 days marks the weaker bounces (2022 - 25: 24% win vs 67% without; holdout 50% vs 57%), and
entering at the band does not rescue them (`reports/pullback.md`): the band is a reference, not an entry by itself.
