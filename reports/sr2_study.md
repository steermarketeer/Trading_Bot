# Support / resistance v2: bounce candle, retests, breakouts, 1h / 4h / 1D, and a machine-learning filter

**Read the win rates against their break-even:** before costs a 1R target needs >50%, 1.5R >40%, 2R >33%. Fees + slippage (0.18% round trip) cost a fixed share of each R, so the real 1R break-even is higher: it's shown as *needed @1R after costs*. **avg R columns are after costs.** Research = before 2025-11-01; holdout = from 2025-11-01 (never used to choose).

## Summary: win % at a 1R target (break-even 50% before costs; see 'needed after costs')

| TF | trade | research trades | research win @1R | needed after costs | research avg R after costs | holdout trades | holdout win @1R | holdout avg R after costs |
|---|---|---|---|---|---|---|---|---|
| 1h | Reversal, enter right after the touch | 4870 | 49% | 61% | -0.29 | 846 | 45% | -0.39 |
| 1h | Reversal, wait for the bounce candle | 2423 | 51% | 57% | -0.13 | 418 | 47% | -0.22 |
| 1h | Breakout, trade the break | 2141 | 53% | 60% | -0.17 | 429 | 47% | -0.33 |
| 1h | ML picked: Reversal, wait for the bounce candle | 454 | 53% | 58% | -0.09 | 102 | 46% | -0.25 |
| 1h | ML picked: Reversal, enter right after the touch | 584 | 53% | 60% | -0.17 | 130 | 50% | -0.26 |
| 1h | ML picked: Breakout, trade the break | 222 | 58% | 58% | +0.01 | 58 | 47% | -0.29 |
| 4h | Reversal, enter right after the touch | 2388 | 52% | 56% | -0.09 | 455 | 50% | -0.13 |
| 4h | Reversal, wait for the bounce candle | 1219 | 52% | 54% | -0.04 | 233 | 44% | -0.20 |
| 4h | Breakout, trade the break | 1092 | 54% | 55% | -0.04 | 197 | 48% | -0.16 |
| 4h | ML picked: Reversal, wait for the bounce candle | 123 | 62% | 54% | +0.18 | 93 | 39% | -0.31 |
| 4h | ML picked: Reversal, enter right after the touch | 369 | 51% | 55% | -0.09 | 87 | 56% | -0.00 |
| 4h | ML picked: Breakout, trade the break | 96 | 59% | 54% | +0.10 | 58 | 53% | -0.03 |
| 1D | Reversal, enter right after the touch | 895 | 48% | 52% | -0.09 | 183 | 54% | +0.03 |
| 1D | Reversal, wait for the bounce candle | 437 | 55% | 51% | +0.08 | 95 | 59% | +0.14 |
| 1D | Breakout, trade the break | 457 | 50% | 52% | -0.05 | 106 | 48% | -0.09 |
| 1D | ML picked: Reversal, enter right after the touch | 74 | 54% | 52% | +0.03 | 54 | 67% | +0.28 |

## 1h chart

### Win rates

| trade | period | trades | win @1R | needed @1R after costs | win @1.5R (b/e 40%+) | win @2R (b/e 33%+) | avg R @1R after costs | avg R @2R after costs |
|---|---|---|---|---|---|---|---|---|
| Reversal, enter right after the touch | research | 4870 | 49% | 61% | 40% | 33% | -0.29 | -0.25 |
| Reversal, enter right after the touch | holdout | 846 | 45% | 63% | 36% | 30% | -0.39 | -0.37 |
| Reversal, wait for the bounce candle | research | 2423 | 51% | 57% | 41% | 33% | -0.13 | -0.11 |
| Reversal, wait for the bounce candle | holdout | 418 | 47% | 58% | 38% | 30% | -0.22 | -0.23 |
| Breakout, trade the break | research | 2141 | 53% | 60% | 43% | 35% | -0.17 | -0.16 |
| Breakout, trade the break | holdout | 429 | 47% | 62% | 37% | 32% | -0.33 | -0.30 |

### Retests: does price come back before breaking?

*held* = share of touches where the level held at the candle close. Win rates are for the bounce-confirmed reversal.

| touch of the zone | touches | level held | trades | win @1R | needed @1R after costs | win @1.5R (b/e 40%+) | win @2R (b/e 33%+) | avg R @1R after costs | avg R @2R after costs |
|---|---|---|---|---|---|---|---|---|---|
| 1st | 656 | 65% | 215 | 48% | 55% | 40% | 31% | -0.06 | +0.07 |
| 2nd | 622 | 70% | 214 | 55% | 56% | 45% | 34% | -0.00 | +0.00 |
| 3rd | 577 | 72% | 219 | 50% | 57% | 39% | 31% | -0.13 | -0.17 |
| 4th+ | 5156 | 70% | 1775 | 51% | 58% | 41% | 34% | -0.16 | -0.14 |

### Bounce-candle volume

Volume of the bounce (confirmation) candle vs its 20-candle average:

| bounce volume | trades | win @1R | needed @1R after costs | win @1.5R (b/e 40%+) | win @2R (b/e 33%+) | avg R @1R after costs | avg R @2R after costs |
|---|---|---|---|---|---|---|---|
| low <0.7x | 848 | 49% | 59% | 41% | 33% | -0.22 | -0.21 |
| normal | 726 | 52% | 57% | 42% | 34% | -0.13 | -0.13 |
| high 1.2-2x | 494 | 52% | 56% | 42% | 34% | -0.08 | -0.03 |
| very high >2x | 355 | 51% | 54% | 39% | 32% | -0.01 | +0.04 |

Bounce-candle volume vs the touch candle's volume:

| bounce vs touch | trades | win @1R | needed @1R after costs | win @1.5R (b/e 40%+) | win @2R (b/e 33%+) | avg R @1R after costs | avg R @2R after costs |
|---|---|---|---|---|---|---|---|
| less than touch | 1023 | 51% | 57% | 42% | 33% | -0.14 | -0.11 |
| similar | 896 | 52% | 58% | 41% | 35% | -0.12 | -0.11 |
| more than touch | 504 | 48% | 56% | 39% | 31% | -0.15 | -0.13 |

### Breakouts: why do some breaks hold?

- 2141 breaks; **55% were false breaks** (closed back on the old side within 6 candles).

Features that separate breaks that worked (win @1R) from those that failed (q < 0.10 and same direction in both halves):

| feature | split | win if high | win if low | q |
|---|---|---|---|---|
| m_1h_climax | > 0 (supports) | 60% | 51% | 0.066 |

### Machine-learning filter: Reversal, wait for the bounce candle (1h)

LightGBM on 290 features (this timeframe + hint states on 10 timeframes). Each year is predicted by a model trained only on earlier years (with a gap); the model keeps the top 20% most confident trades, using a cut-off fixed on training data.

| test year | all trades | all: win @1R | picked | picked: win @1R | picked: win @1.5R | picked: win @2R | picked: avg R @1R |
|---|---|---|---|---|---|---|---|
| 2022 | 406 | 50% | 145 | 52% | 43% | 35% | -0.11 |
| 2023 | 540 | 50% | 147 | 54% | 42% | 35% | -0.11 |
| 2024 | 413 | 53% | 90 | 53% | 46% | 33% | -0.08 |
| 2025 | 429 | 53% | 72 | 56% | 43% | 36% | -0.04 |

**All test years together: picked 454 trades, win @1R 53%, @1.5R 43%, @2R 35%.**

**Holdout (final model, never seen): all 418 trades win @1R 47%; picked 102 trades win @1R 46%, @1.5R 38%, @2R 29%.**

Most important features:

f_bbody, f_vol_approach, f_range, f_bclose_pos, atr_pct, f_pierce, f_wick, f_bvol_vs_touch, f_vol_touch, f_macd, f_speed, f_vol_slope, f_ret_20, f_body, f_adx, f_rsi, f_bvol, f_bb_pos, f_d_e200, f_di

### Machine-learning filter: Reversal, enter right after the touch (1h)

LightGBM on 290 features (this timeframe + hint states on 10 timeframes). Each year is predicted by a model trained only on earlier years (with a gap); the model keeps the top 20% most confident trades, using a cut-off fixed on training data.

| test year | all trades | all: win @1R | picked | picked: win @1R | picked: win @1.5R | picked: win @2R | picked: avg R @1R |
|---|---|---|---|---|---|---|---|
| 2022 | 805 | 47% | 201 | 51% | 43% | 38% | -0.20 |
| 2023 | 1125 | 47% | 150 | 49% | 39% | 35% | -0.31 |
| 2024 | 802 | 51% | 110 | 65% | 59% | 53% | +0.09 |
| 2025 | 883 | 48% | 123 | 52% | 45% | 38% | -0.17 |

**All test years together: picked 584 trades, win @1R 53%, @1.5R 45%, @2R 40%.**

**Holdout (final model, never seen): all 846 trades win @1R 45%; picked 130 trades win @1R 50%, @1.5R 39%, @2R 33%.**

Most important features:

f_vol_approach, f_pierce, atr_pct, f_wick, f_vol_touch, f_bb_pos, f_rsi, f_body, f_speed, f_macd, f_d_e200, f_range, f_vol_slope, f_ret_20, f_adx, f_hour, m_2h_climax, f_di, f_d_e20, f_d_e50

### Machine-learning filter: Breakout, trade the break (1h)

LightGBM on 290 features (this timeframe + hint states on 10 timeframes). Each year is predicted by a model trained only on earlier years (with a gap); the model keeps the top 20% most confident trades, using a cut-off fixed on training data.

| test year | all trades | all: win @1R | picked | picked: win @1R | picked: win @1.5R | picked: win @2R | picked: avg R @1R |
|---|---|---|---|---|---|---|---|
| 2022 | 362 | 56% | 68 | 59% | 46% | 37% | +0.03 |
| 2023 | 505 | 48% | 59 | 53% | 46% | 39% | -0.14 |
| 2024 | 334 | 55% | 52 | 63% | 52% | 42% | +0.13 |
| 2025 | 379 | 52% | 43 | 58% | 47% | 37% | +0.02 |

**All test years together: picked 222 trades, win @1R 58%, @1.5R 47%, @2R 39%.**

**Holdout (final model, never seen): all 429 trades win @1R 47%; picked 58 trades win @1R 47%, @1.5R 40%, @2R 34%.**

Most important features:

f_body, atr_pct, f_wick, f_d_e200, f_vol_touch, f_ret_20, f_adx, f_di, f_vol_approach, f_pierce, f_d_e20, f_macd, f_bb_pos, f_d_e50, f_hour, f_range, f_rsi, f_speed, f_vol_slope, bars_since_touch

## 4h chart

### Win rates

| trade | period | trades | win @1R | needed @1R after costs | win @1.5R (b/e 40%+) | win @2R (b/e 33%+) | avg R @1R after costs | avg R @2R after costs |
|---|---|---|---|---|---|---|---|---|
| Reversal, enter right after the touch | research | 2388 | 52% | 56% | 41% | 35% | -0.09 | -0.08 |
| Reversal, enter right after the touch | holdout | 455 | 50% | 56% | 40% | 35% | -0.13 | -0.07 |
| Reversal, wait for the bounce candle | research | 1219 | 52% | 54% | 42% | 34% | -0.04 | -0.01 |
| Reversal, wait for the bounce candle | holdout | 233 | 44% | 54% | 35% | 29% | -0.20 | -0.19 |
| Breakout, trade the break | research | 1092 | 54% | 55% | 44% | 37% | -0.04 | +0.02 |
| Breakout, trade the break | holdout | 197 | 48% | 56% | 39% | 32% | -0.16 | -0.16 |

### Retests: does price come back before breaking?

*held* = share of touches where the level held at the candle close. Win rates are for the bounce-confirmed reversal.

| touch of the zone | touches | level held | trades | win @1R | needed @1R after costs | win @1.5R (b/e 40%+) | win @2R (b/e 33%+) | avg R @1R after costs | avg R @2R after costs |
|---|---|---|---|---|---|---|---|---|---|
| 1st | 348 | 61% | 112 | 54% | 53% | 43% | 33% | +0.04 | +0.05 |
| 2nd | 332 | 69% | 113 | 56% | 53% | 48% | 41% | +0.06 | +0.21 |
| 3rd | 297 | 73% | 112 | 54% | 53% | 47% | 45% | -0.00 | +0.26 |
| 4th+ | 2503 | 69% | 882 | 51% | 54% | 40% | 32% | -0.07 | -0.08 |

### Bounce-candle volume

Volume of the bounce (confirmation) candle vs its 20-candle average:

| bounce volume | trades | win @1R | needed @1R after costs | win @1.5R (b/e 40%+) | win @2R (b/e 33%+) | avg R @1R after costs | avg R @2R after costs |
|---|---|---|---|---|---|---|---|
| low <0.7x | 433 | 50% | 55% | 39% | 33% | -0.11 | -0.11 |
| normal | 433 | 52% | 54% | 42% | 35% | -0.03 | -0.01 |
| high 1.2-2x | 241 | 50% | 53% | 44% | 36% | -0.05 | +0.09 |
| very high >2x | 112 | 58% | 52% | 47% | 35% | +0.17 | +0.20 |

Bounce-candle volume vs the touch candle's volume:

| bounce vs touch | trades | win @1R | needed @1R after costs | win @1.5R (b/e 40%+) | win @2R (b/e 33%+) | avg R @1R after costs | avg R @2R after costs |
|---|---|---|---|---|---|---|---|
| less than touch | 476 | 52% | 54% | 42% | 33% | -0.04 | -0.06 |
| similar | 456 | 51% | 54% | 42% | 35% | -0.06 | +0.02 |
| more than touch | 287 | 52% | 53% | 41% | 35% | -0.02 | +0.04 |

### Breakouts: why do some breaks hold?

- 1092 breaks; **54% were false breaks** (closed back on the old side within 6 candles).

Features that separate breaks that worked (win @1R) from those that failed (q < 0.10 and same direction in both halves):

| feature | split | win if high | win if low | q |
|---|---|---|---|---|
| f_macd | > median | 59% | 48% | 0.018 |
| m_2h_slope | > 0 (supports) | 58% | 46% | 0.018 |
| m_2h_di | > 0 (supports) | 57% | 46% | 0.028 |
| m_2h_climax | > 0 (supports) | 67% | 52% | 0.063 |
| m_4h_roc_against | > 0 (supports) | 57% | 47% | 0.063 |
| f_range | > median | 58% | 49% | 0.063 |
| m_2h_cmf | > 0 (supports) | 57% | 47% | 0.063 |
| bars_since_touch | > median | 59% | 50% | 0.063 |
| f_di | > median | 58% | 49% | 0.063 |
| m_4h_macd | > 0 (supports) | 57% | 48% | 0.063 |
| m_15m_macd_fade | > 0 (supports) | 28% | 54% | 0.063 |
| m_30m_cloud | > 0 (supports) | 57% | 48% | 0.063 |
| m_1h_supertrend | > 0 (supports) | 57% | 48% | 0.063 |
| f_d_e20 | > median | 58% | 49% | 0.063 |
| m_1h_slope | > 0 (supports) | 56% | 47% | 0.099 |

### Machine-learning filter: Reversal, wait for the bounce candle (4h)

LightGBM on 290 features (this timeframe + hint states on 10 timeframes). Each year is predicted by a model trained only on earlier years (with a gap); the model keeps the top 20% most confident trades, using a cut-off fixed on training data.

| test year | all trades | all: win @1R | picked | picked: win @1R | picked: win @1.5R | picked: win @2R | picked: avg R @1R |
|---|---|---|---|---|---|---|---|
| 2024 | 209 | 57% | 54 | 72% | 59% | 46% | +0.37 |
| 2025 | 224 | 56% | 69 | 54% | 46% | 39% | +0.03 |

**All test years together: picked 123 trades, win @1R 62%, @1.5R 52%, @2R 42%.**

**Holdout (final model, never seen): all 231 trades win @1R 44%; picked 93 trades win @1R 39%, @1.5R 28%, @2R 23%.**

Most important features:

atr_pct, touch_n, f_vol_approach, f_bb_pos, f_vol_touch, f_range, f_bbody, f_pierce, f_bclose_pos, f_body, f_vol_slope, f_wick, f_bvol, f_macd, f_speed, f_d_e200, f_di, f_adx, f_bvol_vs_touch, f_d_e20

### Machine-learning filter: Reversal, enter right after the touch (4h)

LightGBM on 290 features (this timeframe + hint states on 10 timeframes). Each year is predicted by a model trained only on earlier years (with a gap); the model keeps the top 20% most confident trades, using a cut-off fixed on training data.

| test year | all trades | all: win @1R | picked | picked: win @1R | picked: win @1.5R | picked: win @2R | picked: avg R @1R |
|---|---|---|---|---|---|---|---|
| 2022 | 384 | 51% | 95 | 48% | 37% | 29% | -0.13 |
| 2023 | 560 | 52% | 95 | 44% | 36% | 28% | -0.28 |
| 2024 | 428 | 53% | 73 | 56% | 48% | 42% | -0.01 |
| 2025 | 407 | 55% | 106 | 58% | 46% | 37% | +0.05 |

**All test years together: picked 369 trades, win @1R 51%, @1.5R 41%, @2R 34%.**

**Holdout (final model, never seen): all 454 trades win @1R 50%; picked 87 trades win @1R 56%, @1.5R 44%, @2R 39%.**

Most important features:

f_pierce, f_vol_slope, f_d_e200, f_macd, f_wick, f_vol_touch, f_vol_approach, f_range, f_body, f_adx, f_speed, f_rsi, f_d_e20, bars_since_touch, atr_pct, f_ret_20, f_bb_pos, touch_n, f_d_e50, f_di

### Machine-learning filter: Breakout, trade the break (4h)

LightGBM on 290 features (this timeframe + hint states on 10 timeframes). Each year is predicted by a model trained only on earlier years (with a gap); the model keeps the top 20% most confident trades, using a cut-off fixed on training data.

| test year | all trades | all: win @1R | picked | picked: win @1R | picked: win @1.5R | picked: win @2R | picked: avg R @1R |
|---|---|---|---|---|---|---|---|
| 2024 | 157 | 57% | 39 | 62% | 49% | 46% | +0.12 |
| 2025 | 205 | 58% | 57 | 58% | 51% | 40% | +0.08 |

**All test years together: picked 96 trades, win @1R 59%, @1.5R 50%, @2R 43%.**

**Holdout (final model, never seen): all 196 trades win @1R 48%; picked 58 trades win @1R 53%, @1.5R 48%, @2R 45%.**

Most important features:

f_macd, atr_pct, f_d_e200, bars_since_touch, f_range, f_vol_touch, f_pierce, f_speed, f_adx, f_ret_20, f_bb_pos, f_di, f_vol_approach, f_wick, f_vol_slope, f_body, m_12h_obv, f_hour, f_rsi, touch_n

## 1D chart

### Win rates

| trade | period | trades | win @1R | needed @1R after costs | win @1.5R (b/e 40%+) | win @2R (b/e 33%+) | avg R @1R after costs | avg R @2R after costs |
|---|---|---|---|---|---|---|---|---|
| Reversal, enter right after the touch | research | 895 | 48% | 52% | 40% | 34% | -0.09 | -0.02 |
| Reversal, enter right after the touch | holdout | 183 | 54% | 52% | 44% | 35% | +0.03 | +0.01 |
| Reversal, wait for the bounce candle | research | 437 | 55% | 51% | 44% | 37% | +0.08 | +0.12 |
| Reversal, wait for the bounce candle | holdout | 95 | 59% | 52% | 45% | 38% | +0.14 | +0.14 |
| Breakout, trade the break | research | 457 | 50% | 52% | 42% | 36% | -0.05 | +0.06 |
| Breakout, trade the break | holdout | 106 | 48% | 52% | 38% | 34% | -0.09 | -0.03 |

### Retests: does price come back before breaking?

*held* = share of touches where the level held at the candle close. Win rates are for the bounce-confirmed reversal.

| touch of the zone | touches | level held | trades | win @1R | needed @1R after costs | win @1.5R (b/e 40%+) | win @2R (b/e 33%+) | avg R @1R after costs | avg R @2R after costs |
|---|---|---|---|---|---|---|---|---|---|
| 1st | 177 | 69% | 56 | 46% | 51% | 38% | 25% | -0.08 | -0.23 |
| 2nd | 169 | 68% | 64 | 52% | 51% | 41% | 33% | +0.00 | +0.02 |
| 3rd | 167 | 65% | 54 | 61% | 51% | 41% | 35% | +0.19 | +0.03 |
| 4th+ | 839 | 65% | 263 | 57% | 51% | 48% | 41% | +0.11 | +0.24 |

### Bounce-candle volume

Volume of the bounce (confirmation) candle vs its 20-candle average:

| bounce volume | trades | win @1R | needed @1R after costs | win @1.5R (b/e 40%+) | win @2R (b/e 33%+) | avg R @1R after costs | avg R @2R after costs |
|---|---|---|---|---|---|---|---|
| low <0.7x | 99 | 57% | 52% | 41% | 36% | +0.09 | +0.05 |
| normal | 200 | 56% | 51% | 46% | 37% | +0.08 | +0.10 |
| high 1.2-2x | 108 | 52% | 51% | 42% | 37% | +0.02 | +0.15 |
| very high >2x | 30 | 60% | 51% | 50% | 40% | +0.24 | +0.37 |

Bounce-candle volume vs the touch candle's volume:

| bounce vs touch | trades | win @1R | needed @1R after costs | win @1.5R (b/e 40%+) | win @2R (b/e 33%+) | avg R @1R after costs | avg R @2R after costs |
|---|---|---|---|---|---|---|---|
| less than touch | 83 | 49% | 51% | 36% | 28% | -0.01 | -0.16 |
| similar | 217 | 54% | 51% | 45% | 39% | +0.06 | +0.15 |
| more than touch | 137 | 60% | 51% | 48% | 40% | +0.17 | +0.23 |

### Breakouts: why do some breaks hold?

- 457 breaks; **54% were false breaks** (closed back on the old side within 6 candles).

Features that separate breaks that worked (win @1R) from those that failed (q < 0.10 and same direction in both halves):

None passed.

### Machine-learning filter: Reversal, enter right after the touch (1D)

LightGBM on 290 features (this timeframe + hint states on 10 timeframes). Each year is predicted by a model trained only on earlier years (with a gap); the model keeps the top 20% most confident trades, using a cut-off fixed on training data.

| test year | all trades | all: win @1R | picked | picked: win @1R | picked: win @1.5R | picked: win @2R | picked: avg R @1R |
|---|---|---|---|---|---|---|---|
| 2024 | 178 | 49% | 47 | 55% | 47% | 43% | +0.05 |
| 2025 | 132 | 52% | 27 | 52% | 52% | 44% | -0.01 |

**All test years together: picked 74 trades, win @1R 54%, @1.5R 49%, @2R 43%.**

**Holdout (final model, never seen): all 182 trades win @1R 54%; picked 54 trades win @1R 67%, @1.5R 52%, @2R 38%.**

Most important features:

f_speed, f_vol_touch, f_adx, atr_pct, f_di, f_d_e50, f_d_e20, f_ret_20, f_range, f_wick, f_pierce, f_macd, f_rsi, m_1W_macd_fade, f_vol_slope, f_dow, f_bb_pos, f_vol_approach, touch_n, m_1W_cmf

