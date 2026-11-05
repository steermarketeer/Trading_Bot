# Re-entries after stop hunts (v3 trades)

A stopped-out v3 trade is re-entered ONCE if, within 10 candles of its chart, a candle closes back beyond the trigger level; entry next open, stop beyond the stop-hunt wick + 0.25 ATR, target 2:1 (breakouts) / 3:1 (bounces). 5m replay, market-order costs. win % = profit after costs.

## Trigger: close back beyond the original ENTRY

Stop-outs available: research 271, holdout 56.

| re-entry of | period | re-entries | win % | avg R after costs |
|---|---|---|---|---|
| 1D 4th-test bounce (3:1) RE-ENTRY | research | 52 | 33% | +0.21 |
| A+ breakout (2:1) RE-ENTRY | research | 11 | 9% | -0.79 |
| breakout (2:1) RE-ENTRY | research | 19 | 26% | -0.24 |
| ALL re-entries | research | 82 | 28% | -0.03 |
| 1D 4th-test bounce (3:1) RE-ENTRY | holdout | 5 | 80% | +1.89 |
| A+ breakout (2:1) RE-ENTRY | holdout | 3 | 0% | -1.06 |
| breakout (2:1) RE-ENTRY | holdout | 4 | 25% | -0.33 |
| ALL re-entries | holdout | 12 | 42% | +0.42 |

## Trigger: close back beyond the original STOP

Stop-outs available: research 271, holdout 56.

| re-entry of | period | re-entries | win % | avg R after costs |
|---|---|---|---|---|
| 1D 4th-test bounce (3:1) RE-ENTRY | research | 136 | 24% | -0.11 |
| A+ breakout (2:1) RE-ENTRY | research | 35 | 23% | -0.44 |
| breakout (2:1) RE-ENTRY | research | 38 | 24% | -0.44 |
| ALL re-entries | research | 209 | 23% | -0.23 |
| 1D 4th-test bounce (3:1) RE-ENTRY | holdout | 28 | 29% | +0.09 |
| A+ breakout (2:1) RE-ENTRY | holdout | 7 | 57% | +0.60 |
| breakout (2:1) RE-ENTRY | holdout | 6 | 33% | -0.18 |
| ALL re-entries | holdout | 41 | 34% | +0.14 |

## Whole strategy with re-entries (risk A+ 4% / others 2%, cap 5x)

| version | period | trades | trades/week | win % | avg R | account | max drawdown |
|---|---|---|---|---|---|---|---|
| v3 only | research | 499 | 2.5 | 45% | +0.41 | 101.78x | -58% |
| v3 + re-entries (entry) | research | 581 | 2.9 | 43% | +0.35 | 61.10x | -72% |
| v3 only | holdout | 113 | 2.3 | 50% | +0.54 | 4.76x | -27% |
| v3 + re-entries (entry) | holdout | 125 | 2.6 | 49% | +0.52 | 4.82x | -27% |
| v3 + re-entries (stop) | research | 708 | 3.6 | 39% | +0.22 | 21.05x | -86% |
| v3 + re-entries (stop) | holdout | 154 | 3.2 | 45% | +0.43 | 5.56x | -30% |

