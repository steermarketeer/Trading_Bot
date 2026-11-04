# Which indicators would have caught the failures?

Same trades as the failure analysis. Research: signals before 2025-10-12, split into two halves at 2023-01-01. Holdout: from 2025-11-01 (used only in section 3).

- Hints tested: **268** (178 new + 90 from before); **235** had enough trades (>= 30 warned, >= 10 in each half).
- A hint **catches failures** only if (1) trades it warned about failed more often, with a false-discovery-controlled q < 0.10 across all 235 tests, and (2) that was true in **both** halves of the research period.
- *pts* = percentage points of extra fail rate when the hint warned.
- Trades overlap in time, so the real uncertainty is somewhat larger than the statistics assume. The two-halves rule and the holdout check are there to catch that.

## 1. Indicators that catch failures

**None** passed all checks.

## 2. Reverse signals: a 'warning' that came before BETTER trades

| TF | indicator state | trades | fail if present | fail if not | half 1 | half 2 | q |
|---|---|---|---|---|---|---|---|
| 1D | ADX < 20 (no trend) | 216 | 52% | 66% | -10 pts | -18 pts | 0.043 |
| 1W | Supertrend against | 464 | 58% | 69% | -3 pts | -19 pts | 0.081 |

These look 'wrong' but trades did better with them. That's typical of mean reversion: e.g. a long while short-term momentum is still down is a pullback entry.

## 3. If we had used them: win rate

Research = where the indicators were chosen (optimistic). **Holdout = never used for choosing: the honest number.**

| rule | research trades | win | fail | avg R | margin/trade @5x | holdout trades | win | fail | avg R | margin/trade @5x |
|---|---|---|---|---|---|---|---|---|---|---|
| every trade | 878 | 31% | 63% | +0.02 | -2.4% | 123 | 32% | 66% | -0.01 | -3.1% |
| skip weekly MACD fade (earlier filter B) | 747 | 33% | 61% | +0.07 | -1.3% | 103 | 34% | 63% | +0.06 | -1.2% |
| only when Supertrend against (1W) | 464 | 35% | 58% | +0.16 | +1.2% | 65 | 31% | 66% | -0.03 | -3.6% |
| only when ADX < 20 (no trend) (1D) | 216 | 41% | 52% | +0.33 | +7.0% | 19 | 42% | 58% | +0.26 | +1.9% |

Note: the holdout has only ~120 trades, so a few percentage points either way is within luck.

## 4. Consistent but not significant (watch list)

Pointed the right way in both halves but didn't clear the bar. More data (4h trades, forward shadow) may confirm them.

| TF | indicator warning | new? | warned | extra fail | half 1 | half 2 | q |
|---|---|---|---|---|---|---|---|
| 1D | Chaikin Money Flow against | new | 409 | +9 pts | +14 pts | +5 pts | 0.33 |
| 1h | ADX < 20 (no trend) | new | 153 | +12 pts | +13 pts | +11 pts | 0.33 |
| 1W | MACD momentum fading |  | 131 | +12 pts | +3 pts | +19 pts | 0.33 |
| context | BTC daily trend against | new | 379 | +8 pts | +14 pts | +2 pts | 0.49 |
| context | far from SMA200 | new | 109 | +11 pts | +4 pts | +28 pts | 0.68 |
| 4h | below/above VWAP(20) | new | 180 | +9 pts | +9 pts | +8 pts | 0.68 |
| 15m | MFI stretched | new | 72 | +12 pts | +5 pts | +21 pts | 0.82 |
| 4h | OBV vs its EMA20 against | new | 204 | +7 pts | +12 pts | +2 pts | 0.82 |
| 8h | Supertrend against | new | 341 | +6 pts | +10 pts | +3 pts | 0.82 |
| 1D | Ichimoku cloud against |  | 337 | +6 pts | +10 pts | +2 pts | 0.82 |
| 6h | Supertrend against | new | 312 | +6 pts | +7 pts | +6 pts | 0.82 |
| 12h | -DI/+DI against | new | 312 | +6 pts | +4 pts | +8 pts | 0.82 |
| 1h | reversal candle against | new | 90 | +9 pts | +1 pts | +16 pts | 0.90 |
| 8h | OBV vs its EMA20 against | new | 258 | +6 pts | +9 pts | +2 pts | 0.95 |
| 6h | OBV vs its EMA20 against | new | 235 | +6 pts | +8 pts | +3 pts | 0.95 |

Everything (all 268 hints with all numbers): `indicator_hints.csv`.

## Indicator settings

ADX/DI 14 (Wilder) · Stochastic 14,3 (80/20) · CCI 20 (+/-100) · Williams %R 14 (-20/-80) · MFI 14 (80/20) · OBV vs EMA20 · CMF 20 · rolling VWAP 20 · Supertrend 10,3 · Parabolic SAR 0.02/0.2 · Keltner EMA20 +/- 2xATR10 · Donchian 20 · ATR14 vs ATR50 · volume climax 3x 20-avg · engulfing / shooting star / hammer · ROC 10 · funding avg of 3 >= 0.03% or < 0 · BTC EMA50 daily + weekly trend · ETH/BTC vs EMA50 · swing levels (daily K=5, 120d; weekly K=3, 2y) · SMA200 x1.4 / x0.7 · weekend.
