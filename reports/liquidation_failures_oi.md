# Why trades fail: liquidations and thin volume

All 626 v3.1 trades (2022 - Oct 2026; 329 losers after costs). Liquidation map built from REAL Binance open interest (5m, increases = new positions, split long/short by taker buys), using only candles closed before entry.

## 0. Does the map predict real liquidations? (Coinalyze, Binance ETHUSDT, per day)

Spearman rank correlation with actual liquidations (USD). 'move only' = the day's move alone; a useful map must beat it.

| map built from | days | long liqs: map | long liqs: move only | short liqs: map | short liqs: move only |
|---|---|---|---|---|---|
| volume | 1479 | 0.51 | 0.64 | 0.45 | 0.57 |
| oi | 1479 | 0.44 | 0.64 | 0.39 | 0.57 |

## 1. What price did after stopping us out

- stopped trades: **321**
- price came back to our entry within the time limit: **70%**
- price went on to reach our original target: **37%** (we were right on direction, wrong on the stop)
- stop candle closed back on our side (wick stop): **61%**
- median hunt depth beyond our stop before turning back: **0.50R**

- of the hunts that came back, the turn happened within 0.5R of the biggest estimated long/short liquidation cluster in **32%** of cases

## 2. Reasons known BEFORE the trade: how often in losers vs winners

A reason only explains losses if it is clearly more common in losers than in winners.

| reason | period | in losers | in winners | trades with it | win % with | win % without |
|---|---|---|---|---|---|---|
| liquidation magnet just beyond the stop | research | 37% | 30% | 174 | 41% | 49% |
| liquidation magnet just beyond the stop | holdout | 39% | 24% | 33 | 39% | 58% |
| bigger liquidation magnet against us | research | 22% | 20% | 109 | 44% | 47% |
| bigger liquidation magnet against us | holdout | 22% | 20% | 22 | 50% | 52% |
| thin volume toward the stop | research | 13% | 17% | 76 | 53% | 45% |
| thin volume toward the stop | holdout | 6% | 18% | 13 | 77% | 48% |
| little liquidation fuel to the target | research | 30% | 38% | 174 | 52% | 44% |
| little liquidation fuel to the target | holdout | 29% | 42% | 38 | 61% | 47% |
| higher timeframe against (1D structure / weekly trend / 1D pattern) | research | 46% | 45% | 238 | 46% | 47% |
| higher timeframe against (1D structure / weekly trend / 1D pattern) | holdout | 67% | 60% | 67 | 49% | 56% |
| stop inside normal noise (< 1 ATR) | research | 31% | 22% | 140 | 39% | 49% |
| stop inside normal noise (< 1 ATR) | holdout | 20% | 27% | 25 | 60% | 49% |

## 3. Every losing trade: how many reasons it had

| reasons found | losing trades |
|---|---|
| 0 | 25 |
| 1 | 114 |
| 2 | 112 |
| 3 | 62 |
| 4 | 15 |
| 5 | 1 |

Winners with 0 reasons: 11%; losers with 0 reasons: 8%.

## 4. If we skip trades with each reason (win % after costs)

| period | rule | trades | win % | avg R | profit factor | account | worst drop |
|---|---|---|---|---|---|---|---|
| research | v3.1 (no change) | 520 | 47% | +0.41 | 1.74 | 118.94x | -52% |
| research | skip: liquidation magnet just beyond the stop | 346 | 49% | +0.45 | 1.85 | 67.76x | -31% |
| research | skip: bigger liquidation magnet against us | 411 | 47% | +0.42 | 1.75 | 87.93x | -39% |
| research | skip: thin volume toward the stop | 444 | 45% | +0.38 | 1.67 | 44.09x | -40% |
| research | skip: little liquidation fuel to the target | 346 | 44% | +0.36 | 1.62 | 17.77x | -55% |
| research | skip: higher timeframe against (1D structure / weekly trend / 1D pattern) | 282 | 47% | +0.43 | 1.78 | 11.77x | -64% |
| research | skip: stop inside normal noise (< 1 ATR) | 380 | 49% | +0.48 | 1.94 | 95.15x | -38% |
| research | skip: liquidation magnet beyond stop AND thin volume toward it | 507 | 47% | +0.43 | 1.79 | 144.65x | -44% |
| holdout | v3.1 (no change) | 106 | 52% | +0.58 | 2.14 | 4.77x | -24% |
| holdout | skip: liquidation magnet just beyond the stop | 73 | 58% | +0.74 | 2.57 | 4.20x | -21% |
| holdout | skip: bigger liquidation magnet against us | 84 | 52% | +0.63 | 2.23 | 3.89x | -21% |
| holdout | skip: thin volume toward the stop | 93 | 48% | +0.44 | 1.81 | 2.79x | -24% |
| holdout | skip: little liquidation fuel to the target | 68 | 47% | +0.52 | 1.93 | 2.11x | -16% |
| holdout | skip: higher timeframe against (1D structure / weekly trend / 1D pattern) | 39 | 56% | +0.82 | 2.86 | 1.99x | -12% |
| holdout | skip: stop inside normal noise (< 1 ATR) | 81 | 49% | +0.48 | 1.90 | 2.79x | -23% |
| holdout | skip: liquidation magnet beyond stop AND thin volume toward it | 104 | 52% | +0.58 | 2.13 | 4.63x | -24% |

## 5. Liquidation magnet beyond the stop, per setup

| period | setup | trades | with magnet | win % with | win % without |
|---|---|---|---|---|---|
| research | A+ breakout | 182 | 21 | 57% | 59% |
| research | breakout | 145 | 8 | 62% | 42% |
| research | 1D bounce | 193 | 145 | 38% | 35% |
| holdout | A+ breakout | 41 | 3 | 67% | 61% |
| holdout | breakout | 21 | 1 | 0% | 50% |
| holdout | 1D bounce | 44 | 29 | 38% | 60% |

## 6. Fix: put the stop beyond the hunt (same $ risk, so a smaller position)

Decided at the entry. 'same target price' keeps our target; the reward:risk gets smaller.

| period | stop | trades | win % | avg R | profit factor | account | worst drop |
|---|---|---|---|---|---|---|---|
| research | original stop | 520 | 47% | +0.41 | 1.74 | 118.94x | -52% |
| research | stop 0.5R further, same target price | 520 | 54% | +0.30 | 1.66 | 33.90x | -58% |
| research | stop 0.5R further, same R target | 520 | 46% | +0.31 | 1.58 | 26.47x | -60% |
| research | stop beyond the liquidation cluster, same target price | 520 | 50% | +0.38 | 1.74 | 103.61x | -49% |
| research |   A+ breakout: original stop | 182 | 59% | +0.64 | 2.52 |  |  |
| research |   A+ breakout: stop 0.5R further, same target price | 182 | 63% | +0.41 | 2.19 |  |  |
| research |   A+ breakout: stop 0.5R further, same R target | 182 | 55% | +0.47 | 2.13 |  |  |
| research |   A+ breakout: stop beyond the liquidation cluster, same target price | 182 | 59% | +0.62 | 2.48 |  |  |
| research |   breakout: original stop | 145 | 43% | +0.22 | 1.36 |  |  |
| research |   breakout: stop 0.5R further, same target price | 145 | 54% | +0.17 | 1.36 |  |  |
| research |   breakout: stop 0.5R further, same R target | 145 | 42% | +0.12 | 1.19 |  |  |
| research |   breakout: stop beyond the liquidation cluster, same target price | 145 | 43% | +0.21 | 1.35 |  |  |
| research |   1D bounce: original stop | 193 | 37% | +0.34 | 1.52 |  |  |
| research |   1D bounce: stop 0.5R further, same target price | 193 | 46% | +0.28 | 1.53 |  |  |
| research |   1D bounce: stop 0.5R further, same R target | 193 | 41% | +0.31 | 1.52 |  |  |
| research |   1D bounce: stop beyond the liquidation cluster, same target price | 193 | 47% | +0.27 | 1.52 |  |  |
| holdout | original stop | 106 | 52% | +0.58 | 2.14 | 4.77x | -24% |
| holdout | stop 0.5R further, same target price | 106 | 59% | +0.44 | 2.11 | 3.20x | -26% |
| holdout | stop 0.5R further, same R target | 106 | 44% | +0.25 | 1.44 | 1.51x | -37% |
| holdout | stop beyond the liquidation cluster, same target price | 106 | 55% | +0.47 | 1.99 | 3.81x | -25% |
| holdout |   A+ breakout: original stop | 41 | 61% | +0.76 | 2.76 |  |  |
| holdout |   A+ breakout: stop 0.5R further, same target price | 41 | 63% | +0.47 | 2.32 |  |  |
| holdout |   A+ breakout: stop 0.5R further, same R target | 41 | 39% | +0.03 | 1.06 |  |  |
| holdout |   A+ breakout: stop beyond the liquidation cluster, same target price | 41 | 61% | +0.73 | 2.70 |  |  |
| holdout |   breakout: original stop | 21 | 48% | +0.33 | 1.56 |  |  |
| holdout |   breakout: stop 0.5R further, same target price | 21 | 62% | +0.38 | 1.91 |  |  |
| holdout |   breakout: stop 0.5R further, same R target | 21 | 38% | -0.01 | 0.99 |  |  |
| holdout |   breakout: stop beyond the liquidation cluster, same target price | 21 | 48% | +0.33 | 1.56 |  |  |
| holdout |   1D bounce: original stop | 44 | 45% | +0.55 | 2.00 |  |  |
| holdout |   1D bounce: stop 0.5R further, same target price | 44 | 55% | +0.44 | 2.04 |  |  |
| holdout |   1D bounce: stop 0.5R further, same R target | 44 | 52% | +0.57 | 2.26 |  |  |
| holdout |   1D bounce: stop beyond the liquidation cluster, same target price | 44 | 52% | +0.30 | 1.65 |  |  |

## 7. Fair check of the liquidation-magnet reason (removing the stop-width effect)

| magnet defined as | period | setup | trades with magnet | win % with | win % without |
|---|---|---|---|---|---|
| top third within its own setup | research | all | 175 | 45% | 48% |
| top third within its own setup | research | A+ breakout | 61 | 54% | 61% |
| top third within its own setup | research | breakout | 49 | 37% | 47% |
| top third within its own setup | research | 1D bounce | 65 | 42% | 35% |
| top third within its own setup | holdout | all | 14 | 71% | 49% |
| top third within its own setup | holdout | A+ breakout | 4 | 75% | 59% |
| top third within its own setup | holdout | breakout | 4 | 75% | 41% |
| top third within its own setup | holdout | 1D bounce | 6 | 67% | 42% |
| top third of weight per 1% of price | research | all | 174 | 39% | 50% |
| top third of weight per 1% of price | research | A+ breakout | 34 | 53% | 60% |
| top third of weight per 1% of price | research | breakout | 9 | 44% | 43% |
| top third of weight per 1% of price | research | 1D bounce | 131 | 35% | 42% |
| top third of weight per 1% of price | holdout | all | 24 | 54% | 51% |
| top third of weight per 1% of price | holdout | A+ breakout | 3 | 67% | 61% |
| top third of weight per 1% of price | holdout | breakout | 0 | - | 48% |
| top third of weight per 1% of price | holdout | 1D bounce | 21 | 52% | 39% |

