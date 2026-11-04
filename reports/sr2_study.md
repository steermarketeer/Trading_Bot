# Support / resistance v2: bounce candle, retests, breakouts, 1h / 4h / 1D, and a machine-learning filter

**Read the win rates against their break-even:** before costs a 1R target needs >50%, 1.5R >40%, 2R >33%. Fees + slippage (0.18% round trip) cost a fixed share of each R, so the real 1R break-even is higher: it's shown as *needed @1R after costs*. **avg R columns are after costs.** Research = before 2025-11-01; holdout = from 2025-11-01 (never used to choose).

## Summary: win % at a 1R target (break-even 50% before costs; see 'needed after costs')

| TF | trade | research trades | research win @1R | needed after costs | research avg R after costs | holdout trades | holdout win @1R | holdout avg R after costs |
|---|---|---|---|---|---|---|---|---|
| 1h | Reversal, enter right after the touch | 4870 | 49% | 61% | -0.29 | 846 | 45% | -0.39 |
| 1h | Reversal, wait for the bounce candle | 2423 | 51% | 57% | -0.13 | 418 | 47% | -0.22 |
| 1h | Breakout, trade the break | 2141 | 53% | 60% | -0.17 | 429 | 47% | -0.33 |
| 1h | ML picked: Reversal, wait for the bounce candle | 449 | 53% | 58% | -0.10 | 100 | 42% | -0.33 |
| 1h | ML picked: Reversal, enter right after the touch | 574 | 55% | 60% | -0.14 | 134 | 51% | -0.25 |
| 1h | ML picked: Breakout, trade the break | 229 | 60% | 58% | +0.04 | 61 | 48% | -0.27 |
| 4h | Reversal, enter right after the touch | 2388 | 52% | 56% | -0.09 | 455 | 50% | -0.13 |
| 4h | Reversal, wait for the bounce candle | 1219 | 52% | 54% | -0.04 | 233 | 44% | -0.20 |
| 4h | Breakout, trade the break | 1092 | 54% | 55% | -0.04 | 197 | 48% | -0.16 |
| 4h | ML picked: Reversal, wait for the bounce candle | 130 | 61% | 54% | +0.15 | 88 | 39% | -0.32 |
| 4h | ML picked: Reversal, enter right after the touch | 346 | 55% | 55% | -0.02 | 100 | 45% | -0.24 |
| 4h | ML picked: Breakout, trade the break | 98 | 58% | 54% | +0.07 | 58 | 53% | -0.05 |
| 1D | Reversal, enter right after the touch | 895 | 48% | 52% | -0.09 | 183 | 54% | +0.03 |
| 1D | Reversal, wait for the bounce candle | 437 | 55% | 51% | +0.08 | 95 | 59% | +0.14 |
| 1D | Breakout, trade the break | 457 | 50% | 52% | -0.05 | 106 | 48% | -0.09 |
| 1D | ML picked: Reversal, enter right after the touch | 71 | 48% | 52% | -0.09 | 47 | 70% | +0.35 |

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
| 2022 | 406 | 50% | 135 | 53% | 43% | 36% | -0.08 |
| 2023 | 540 | 50% | 150 | 52% | 42% | 34% | -0.16 |
| 2024 | 413 | 53% | 85 | 51% | 42% | 32% | -0.14 |
| 2025 | 429 | 53% | 79 | 57% | 46% | 38% | -0.01 |

**All test years together: picked 449 trades, win @1R 53%, @1.5R 43%, @2R 35%.**

**Holdout (final model, never seen): all 418 trades win @1R 47%; picked 100 trades win @1R 42%, @1.5R 35%, @2R 27%.**

Most important features:

f_bbody, f_bvol_vs_touch, f_vol_approach, f_range, f_bclose_pos, f_wick, atr_pct, f_pierce, f_speed, f_vol_touch, f_macd, f_ret_20, f_bb_pos, f_adx, f_rsi, f_bvol, f_vol_slope, f_di, f_d_e200, touch_n

### Machine-learning filter: Reversal, enter right after the touch (1h)

LightGBM on 290 features (this timeframe + hint states on 10 timeframes). Each year is predicted by a model trained only on earlier years (with a gap); the model keeps the top 20% most confident trades, using a cut-off fixed on training data.

| test year | all trades | all: win @1R | picked | picked: win @1R | picked: win @1.5R | picked: win @2R | picked: avg R @1R |
|---|---|---|---|---|---|---|---|
| 2022 | 805 | 47% | 193 | 51% | 45% | 40% | -0.19 |
| 2023 | 1125 | 47% | 163 | 51% | 41% | 37% | -0.28 |
| 2024 | 802 | 51% | 99 | 69% | 62% | 54% | +0.15 |
| 2025 | 883 | 48% | 119 | 54% | 46% | 41% | -0.12 |

**All test years together: picked 574 trades, win @1R 55%, @1.5R 47%, @2R 42%.**

**Holdout (final model, never seen): all 846 trades win @1R 45%; picked 134 trades win @1R 51%, @1.5R 40%, @2R 34%.**

Most important features:

f_vol_approach, f_vol_touch, atr_pct, f_pierce, f_body, f_wick, f_rsi, f_speed, f_adx, f_d_e200, f_ret_20, f_d_e20, f_macd, f_bb_pos, f_range, m_2h_climax, f_di, f_vol_slope, f_hour, touch_n

### Machine-learning filter: Breakout, trade the break (1h)

LightGBM on 290 features (this timeframe + hint states on 10 timeframes). Each year is predicted by a model trained only on earlier years (with a gap); the model keeps the top 20% most confident trades, using a cut-off fixed on training data.

| test year | all trades | all: win @1R | picked | picked: win @1R | picked: win @1.5R | picked: win @2R | picked: avg R @1R |
|---|---|---|---|---|---|---|---|
| 2022 | 362 | 56% | 68 | 60% | 46% | 37% | +0.07 |
| 2023 | 505 | 48% | 68 | 54% | 46% | 40% | -0.12 |
| 2024 | 334 | 55% | 49 | 67% | 57% | 47% | +0.20 |
| 2025 | 379 | 52% | 44 | 59% | 48% | 36% | +0.03 |

**All test years together: picked 229 trades, win @1R 60%, @1.5R 48%, @2R 40%.**

**Holdout (final model, never seen): all 429 trades win @1R 47%; picked 61 trades win @1R 48%, @1.5R 41%, @2R 34%.**

Most important features:

f_body, atr_pct, f_di, f_wick, f_d_e200, f_vol_approach, f_adx, f_pierce, f_macd, f_ret_20, f_bb_pos, f_vol_touch, f_d_e20, f_range, f_d_e50, f_speed, f_rsi, f_hour, bars_since_touch, f_vol_slope

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
| m_2h_slope | > 0 (supports) | 58% | 45% | 0.005 |
| f_macd | > median | 59% | 48% | 0.013 |
| m_2h_di | > 0 (supports) | 57% | 46% | 0.025 |
| m_1h_slope | > 0 (supports) | 57% | 45% | 0.025 |
| m_30m_cloud | > 0 (supports) | 57% | 47% | 0.039 |
| m_4h_macd | > 0 (supports) | 57% | 47% | 0.039 |
| m_2h_climax | > 0 (supports) | 67% | 52% | 0.039 |
| m_4h_roc_against | > 0 (supports) | 57% | 47% | 0.040 |
| f_range | > median | 58% | 49% | 0.042 |
| m_2h_cmf | > 0 (supports) | 57% | 47% | 0.042 |
| m_15m_cloud | > 0 (supports) | 56% | 47% | 0.042 |
| m_1h_macd | > 0 (supports) | 56% | 46% | 0.042 |
| bars_since_touch | > median | 59% | 50% | 0.042 |
| f_di | > median | 58% | 49% | 0.042 |
| m_1h_trend | > 0 (supports) | 56% | 46% | 0.042 |

### Machine-learning filter: Reversal, wait for the bounce candle (4h)

LightGBM on 290 features (this timeframe + hint states on 10 timeframes). Each year is predicted by a model trained only on earlier years (with a gap); the model keeps the top 20% most confident trades, using a cut-off fixed on training data.

| test year | all trades | all: win @1R | picked | picked: win @1R | picked: win @1.5R | picked: win @2R | picked: avg R @1R |
|---|---|---|---|---|---|---|---|
| 2024 | 209 | 57% | 57 | 72% | 60% | 49% | +0.35 |
| 2025 | 224 | 56% | 73 | 52% | 40% | 34% | -0.01 |

**All test years together: picked 130 trades, win @1R 61%, @1.5R 48%, @2R 41%.**

**Holdout (final model, never seen): all 231 trades win @1R 44%; picked 88 trades win @1R 39%, @1.5R 30%, @2R 26%.**

Most important features:

atr_pct, touch_n, f_pierce, f_vol_approach, f_vol_slope, f_bbody, f_bb_pos, f_bclose_pos, f_speed, f_body, f_d_e200, f_di, f_bvol_vs_touch, f_range, f_d_e20, f_wick, f_vol_touch, f_bvol, f_ret_20, bars_since_touch

### Machine-learning filter: Reversal, enter right after the touch (4h)

LightGBM on 290 features (this timeframe + hint states on 10 timeframes). Each year is predicted by a model trained only on earlier years (with a gap); the model keeps the top 20% most confident trades, using a cut-off fixed on training data.

| test year | all trades | all: win @1R | picked | picked: win @1R | picked: win @1.5R | picked: win @2R | picked: avg R @1R |
|---|---|---|---|---|---|---|---|
| 2022 | 384 | 51% | 91 | 53% | 38% | 33% | -0.04 |
| 2023 | 560 | 52% | 75 | 48% | 40% | 31% | -0.21 |
| 2024 | 428 | 53% | 70 | 61% | 51% | 43% | +0.10 |
| 2025 | 407 | 55% | 110 | 58% | 46% | 39% | +0.06 |

**All test years together: picked 346 trades, win @1R 55%, @1.5R 44%, @2R 36%.**

**Holdout (final model, never seen): all 454 trades win @1R 50%; picked 100 trades win @1R 45%, @1.5R 36%, @2R 32%.**

Most important features:

f_pierce, f_vol_slope, f_vol_touch, f_d_e200, f_macd, f_vol_approach, f_wick, f_body, f_speed, f_rsi, f_range, atr_pct, f_bb_pos, f_adx, bars_since_touch, touch_n, f_d_e20, f_d_e50, f_ret_20, f_dow

### Machine-learning filter: Breakout, trade the break (4h)

LightGBM on 290 features (this timeframe + hint states on 10 timeframes). Each year is predicted by a model trained only on earlier years (with a gap); the model keeps the top 20% most confident trades, using a cut-off fixed on training data.

| test year | all trades | all: win @1R | picked | picked: win @1R | picked: win @1.5R | picked: win @2R | picked: avg R @1R |
|---|---|---|---|---|---|---|---|
| 2024 | 157 | 57% | 39 | 62% | 49% | 46% | +0.14 |
| 2025 | 205 | 58% | 59 | 56% | 49% | 41% | +0.03 |

**All test years together: picked 98 trades, win @1R 58%, @1.5R 49%, @2R 43%.**

**Holdout (final model, never seen): all 196 trades win @1R 48%; picked 58 trades win @1R 53%, @1.5R 48%, @2R 43%.**

Most important features:

f_macd, f_d_e200, atr_pct, f_vol_touch, f_pierce, f_range, f_speed, f_adx, bars_since_touch, f_bb_pos, f_wick, f_di, f_ret_20, f_vol_approach, f_body, f_vol_slope, m_12h_obv, touch_n, f_rsi, f_hour

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
| 2024 | 178 | 49% | 48 | 48% | 42% | 38% | -0.10 |
| 2025 | 132 | 52% | 23 | 48% | 43% | 39% | -0.09 |

**All test years together: picked 71 trades, win @1R 48%, @1.5R 42%, @2R 38%.**

**Holdout (final model, never seen): all 182 trades win @1R 54%; picked 47 trades win @1R 70%, @1.5R 55%, @2R 46%.**

Most important features:

f_speed, f_di, f_rsi, f_vol_touch, atr_pct, f_ret_20, f_pierce, f_macd, f_d_e20, f_bb_pos, f_d_e200, f_adx, f_wick, f_dow, f_vol_approach, f_vol_slope, f_range, m_1W_cmf, bars_since_touch, f_d_e50

