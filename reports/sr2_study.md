# Support / resistance v2: bounce candle, retests, breakouts, 1h / 4h / 1D, and a machine-learning filter

**Read the win rates against their break-even:** a 1R target (same size as the stop) needs **>50%**, 1.5R needs >40%, 2R needs >33%. Research = before 2025-11-01; holdout = from 2025-11-01 (never used to choose).

## Summary: win % at a 1R target (break-even 50%)

| TF | trade | research trades | research win @1R | research win @2R | holdout trades | holdout win @1R | holdout win @2R |
|---|---|---|---|---|---|---|---|
| 1D | Reversal, enter right after the touch | 895 | 48% | 34% | 183 | 54% | 35% |
| 1D | Reversal, wait for the bounce candle | 437 | 55% | 37% | 95 | 59% | 38% |
| 1D | Breakout, trade the break | 457 | 50% | 36% | 106 | 48% | 34% |
| 1D | ML picked: Reversal, enter right after the touch | 71 | 48% | 38% | 47 | 70% | 46% |

## 1D chart

### Win rates

| trade | period | trades | win @1R (b/e 50%) | win @1.5R (b/e 40%) | win @2R (b/e 33%) | avg R @1R | avg R @2R |
|---|---|---|---|---|---|---|---|
| Reversal, enter right after the touch | research | 895 | 48% | 40% | 34% | -0.04 | +0.04 |
| Reversal, enter right after the touch | holdout | 183 | 54% | 44% | 35% | +0.09 | +0.06 |
| Reversal, wait for the bounce candle | research | 437 | 55% | 44% | 37% | +0.11 | +0.15 |
| Reversal, wait for the bounce candle | holdout | 95 | 59% | 45% | 38% | +0.17 | +0.18 |
| Breakout, trade the break | research | 457 | 50% | 42% | 36% | -0.00 | +0.11 |
| Breakout, trade the break | holdout | 106 | 48% | 38% | 34% | -0.04 | +0.02 |

### Retests: does price come back before breaking?

*held* = share of touches where the level held at the candle close. Win rates are for the bounce-confirmed reversal.

| touch of the zone | touches | level held | trades | win @1R (b/e 50%) | win @1.5R (b/e 40%) | win @2R (b/e 33%) | avg R @1R | avg R @2R |
|---|---|---|---|---|---|---|---|---|
| 1st | 177 | 69% | 56 | 46% | 38% | 25% | -0.06 | -0.21 |
| 2nd | 169 | 68% | 64 | 52% | 41% | 33% | +0.03 | +0.05 |
| 3rd | 167 | 65% | 54 | 61% | 41% | 35% | +0.22 | +0.06 |
| 4th+ | 839 | 65% | 263 | 57% | 48% | 41% | +0.14 | +0.27 |

### Bounce-candle volume

Volume of the bounce (confirmation) candle vs its 20-candle average:

| bounce volume | trades | win @1R (b/e 50%) | win @1.5R (b/e 40%) | win @2R (b/e 33%) | avg R @1R | avg R @2R |
|---|---|---|---|---|---|---|
| low <0.7x | 99 | 57% | 41% | 36% | +0.13 | +0.09 |
| normal | 200 | 56% | 46% | 37% | +0.11 | +0.13 |
| high 1.2-2x | 108 | 52% | 42% | 37% | +0.05 | +0.18 |
| very high >2x | 30 | 60% | 50% | 40% | +0.25 | +0.39 |

Bounce-candle volume vs the touch candle's volume:

| bounce vs touch | trades | win @1R (b/e 50%) | win @1.5R (b/e 40%) | win @2R (b/e 33%) | avg R @1R | avg R @2R |
|---|---|---|---|---|---|---|
| less than touch | 83 | 49% | 36% | 28% | +0.02 | -0.12 |
| similar | 217 | 54% | 45% | 39% | +0.09 | +0.19 |
| more than touch | 137 | 60% | 48% | 40% | +0.20 | +0.26 |

### Breakouts: why do some breaks hold?

- 457 breaks; **54% were false breaks** (closed back on the old side within 6 candles).

Features that separate breaks that worked (win @1R) from those that failed (q < 0.10 and same direction in both halves):

None passed.

### Machine-learning filter: Reversal, enter right after the touch (1D)

LightGBM on 290 features (this timeframe + hint states on 10 timeframes). Each year is predicted by a model trained only on earlier years (with a gap); the model keeps the top 20% most confident trades, using a cut-off fixed on training data.

| test year | all trades | all: win @1R | picked | picked: win @1R | picked: win @1.5R | picked: win @2R | picked: avg R @1R |
|---|---|---|---|---|---|---|---|
| 2024 | 178 | 49% | 48 | 48% | 42% | 38% | -0.04 |
| 2025 | 132 | 52% | 23 | 48% | 43% | 39% | -0.04 |

**All test years together: picked 71 trades, win @1R 48%, @1.5R 42%, @2R 38%.**

**Holdout (final model, never seen): all 182 trades win @1R 54%; picked 47 trades win @1R 70%, @1.5R 55%, @2R 46%.**

Most important features:

f_speed, f_di, f_rsi, f_vol_touch, atr_pct, f_ret_20, f_pierce, f_macd, f_d_e20, f_bb_pos, f_d_e200, f_adx, f_wick, f_dow, f_vol_approach, f_vol_slope, f_range, m_1W_cmf, bars_since_touch, f_d_e50

