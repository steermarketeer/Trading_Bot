# Trading definitions (single source of truth)

Every chart, study and machine-learning input in this project uses these definitions. Each one is coded once, in
`bot/study/defs.py`, and tested on the journal trades. Change a definition here first, then in the code.

Sources: classic chart analysis (Edwards & Magee; Bulkowski, *Encyclopedia of Chart Patterns*), Wyckoff,
John Bollinger's own band rules, price action (pin bars), and liquidity / smart-money conventions (ICT / SMC).
Where sources disagree, the choice and the reason are written down.

Notation: ATR = 14-candle Wilder ATR of the timeframe being read. "Close" always means a candle close; a wick alone
never breaks anything. Everything is known only after the candle that shows it has closed.

## 1. Structure

| Term | Definition | Source / note |
|---|---|---|
| Swing high / low | A candle whose high (low) is the highest (lowest) of the 5 candles on each side. Known 5 candles later. | Fractal swing, standard |
| HH / LH / HL / LL | Each new swing high compared with the previous swing high (higher = HH, lower = LH); lows the same (HL / LL). | Market structure |
| Uptrend / downtrend structure | Last two swing highs AND last two swing lows rising (HH + HL) / falling (LH + LL). | Market structure |
| Break of structure (BOS) | A **close** beyond the last confirmed swing **in the direction of the current structure**. | ICT/SMC; close, not wick |
| Change of character (CHoCH) | A close beyond the last confirmed swing **against** the current structure (first counter-break). | ICT/SMC |
| Displacement | A strong candle: range >= 1.5 ATR and body >= 60% of the range. | ICT/SMC "conviction move" |
| Market structure shift (MSS) | A CHoCH made by a displacement candle. | ICT/SMC |

## 2. Levels and liquidity

| Term | Definition | Source / note |
|---|---|---|
| Support / resistance zone | Swing highs / lows from 4h, 1D, 1W clustered within 1%; strong = 3+ swings or a weekly swing. | Project rule (unchanged) |
| Touch / test | Price comes within 0.25 ATR of a level, whatever happens next. A touch is NOT a rejection. | |
| **Equal highs / lows = double / triple top / bottom** | 2 (double) or 3+ (triple) swing highs (lows) within max(0.25%, 0.5 ATR) of each other (Bulkowski uses ~3% on daily stock charts; the tolerance scales with the timeframe's volatility), at least 5 candles apart, with a pullback between them of at least 1 ATR. | Bulkowski (tops close in price, valley between) |
| Double top / bottom **confirmed** | A close below the valley low between the tops (above the peak for a bottom). Unconfirmed until then. | Bulkowski: the close below the valley is the trigger |
| Liquidity pool | Resting stops just beyond untaken equal highs / lows or an untaken swing: buy-side above highs, sell-side below lows. | ICT/SMC |
| Untaken | No price has traded beyond the pool since it formed. | |
| Liquidity sweep (grab) | A wick beyond a pool, then the **same candle closes back inside**. Stops taken, no breakout. | ICT/SMC; Wyckoff spring (below) / upthrust (above) |
| Spring / upthrust | A sweep of a trading range's low / high that is followed through: the next candles close back inside and move away. | Wyckoff |
| Liquidation cluster | Estimated price where leveraged positions get liquidated (from open interest; an estimate). | Project (bot/study/liquidation.py) |

## 3. Reactions at a level

| Term | Definition | Source / note |
|---|---|---|
| **Rejection** | At a level (touch or pierce): the candle closes back on the other side of the level, the wick toward the level is >= 50% of the candle's range, and the close is in the far half of the candle. Strong rejection: wick >= 2/3 of the range. | Pin-bar / rejection-candle convention |
| Rejection count | Number of rejection candles at the same level (within 0.25 ATR) in the last 30 candles. Separate from equal highs: rejections can be at different prices. | |
| Failed push | A swing high below the last rejected high (a lower high after a rejection). | |

## 4. Breakouts

| Term | Definition | Source / note |
|---|---|---|
| Breakout | A close beyond the level by at least 0.25 ATR (short timeframes) / 1% (daily and above). | Edwards & Magee use 3% for long-term lines, 1% short-term; ATR filter for crypto intraday |
| Confirmed breakout | The breakout is still beyond the level on the next close of the higher timeframe (2h → 4h, 4h → 1D), or on two consecutive closes. | Two-close / higher-timeframe close rule |
| Fakeout (failed breakout) | A breakout whose close comes back inside the level within 3 candles. | Standard |
| Retest | After a confirmed breakout, price returns within 0.25 ATR of the broken level and closes on the breakout side (old resistance holds as support). | Break-and-retest |
| Failed retest | The retest closes back through the level: the breakout is invalid. | |

## 5. Trendlines

| Term | Definition | Source / note |
|---|---|---|
| Trendline | A line through two confirmed swing lows (rising) or highs (falling). Valid from the 3rd touch (within 0.25 ATR) without a close through it. | 2 touches to draw, 3 to confirm |
| Trendline break | A close beyond the line by at least 0.25 ATR (1% on daily). | Same filter as breakouts |

## 6. Bollinger bands (20, 2)

| Term | Definition | Source / note |
|---|---|---|
| Tag | A touch of the upper / lower band. **Not a signal by itself.** | John Bollinger |
| Band walk | Several closes at / beyond the band in a row: a strong trend, not a reversal. | John Bollinger |
| Band failure | A close beyond the band, then a close back inside within 3 candles. | |
| M top / W bottom | First high tags or closes beyond the upper band; the second high fails to reach the band (or tags it but closes inside); confirmed by a close through the middle band. Mirror for W bottoms. | John Bollinger |
| Middle band | 20-period SMA; the target of a W-bottom bounce and the confirmation line of M / W. | John Bollinger |

## 7. Indicators (supporting only, never the reason for a trade)

| Term | Definition |
|---|---|
| MACD divergence | Price makes a higher high (lower low) between two swings while the MACD line makes a lower high (higher low). |
| RSI stretched | RSI(14) above 70 / below 30. |
| Volume fading | Each successive push (swing high) on lower volume than the one before. |
| EMA trend | Close above / below EMA 20, 50, 200 of that timeframe. |

## 8. Fibonacci

Retracements 0.236 / 0.382 / 0.5 / 0.618 / 0.786 and extensions 1.272 / 1.618 of the last leg: lowest low → highest
high after it (longs), using only candles closed before the decision.
