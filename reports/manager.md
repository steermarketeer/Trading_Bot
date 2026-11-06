# Machine-learning trade manager: your failure concepts as measurements, the machine combines them

At every 4h close inside a trade the model predicts what holding earns versus closing now (after costs). It exits at the first close where holding is predicted to lose more than a margin chosen on earlier years. Every number below is out-of-sample: each year is managed by a model trained only on earlier years; the holdout (Nov 2025 on) last. **win % = profit after costs.**

Margins chosen per period (exit when predicted gain from holding < margin, in R):

| period | margin | training trades | training 4h closes |
|---|---|---|---|
| 2022 | -1.00 | 2028 | 15293 |
| 2023 | -1.00 | 3686 | 35243 |
| 2024 | -1.00 | 5929 | 65050 |
| 2025 | -1.00 | 7681 | 86136 |
| holdout | -1.00 | 9307 | 110109 |

## Hold to stop / target vs the machine-learning manager

| trades | period | n | win % (hold) | avg R (hold) | win % (ML manager) | avg R (ML manager) | closed early by ML | account (hold) | worst drop | account (ML) | worst drop |
|---|---|---|---|---|---|---|---|---|---|---|---|
| v3.1 after journal filters, entry at signal, fixed target | 2022 - Oct 2025 | 129 | 57% | +0.82 | 57% | +0.81 | 3% | 16.78x | -16% | 16.30x | -16% |
| v3.1 after journal filters, entry at signal, fixed target | holdout | 33 | 58% | +0.65 | 58% | +0.65 | 0% | 1.85x | -13% | 1.85x | -13% |
| v3.1 filtered, bounce stop below 0.786 + strong breaking candle | 2022 - Oct 2025 | 100 | 56% | +0.94 | 56% | +0.85 | 5% | 10.45x | -13% | 9.06x | -13% |
| v3.1 filtered, bounce stop below 0.786 + strong breaking candle | holdout | 27 | 70% | +1.44 | 70% | +1.44 | 0% | 2.45x | -9% | 2.45x | -9% |
| v3.1 filtered: 1D bounces only (base) | 2022 - Oct 2025 | 51 | 49% | +0.95 | 49% | +0.91 | 8% |  |  |  |  |
| v3.1 filtered: 1D bounces only (base) | holdout | 11 | 55% | +0.58 | 55% | +0.58 | 0% |  |  |  |  |
| v3.1 filtered: breakouts only (base) | 2022 - Oct 2025 | 78 | 62% | +0.74 | 62% | +0.74 | 0% |  |  |  |  |
| v3.1 filtered: breakouts only (base) | holdout | 22 | 59% | +0.69 | 59% | +0.69 | 0% |  |  |  |  |
| all main-rule signals (2 : 1) | 2022 - Oct 2025 | 6731 | 35% | -0.09 | 35% | -0.09 | 1% |  |  |  |  |
| all main-rule signals (2 : 1) | holdout | 1658 | 32% | -0.19 | 32% | -0.19 | 0% |  |  |  |  |

## By year (v3.1 filtered, entry at signal, fixed target)

| period | trades | win % hold | avg R hold | win % ML | avg R ML |
|---|---|---|---|---|---|
| 2022 | 26 | 69% | +1.21 | 69% | +1.23 |
| 2023 | 29 | 45% | +0.24 | 45% | +0.24 |
| 2024 | 39 | 54% | +0.80 | 54% | +0.75 |
| 2025 | 35 | 60% | +1.05 | 60% | +1.03 |
| holdout | 33 | 58% | +0.65 | 58% | +0.65 |

## What the manager leans on most (holdout model)

| input | share of the model's decisions |
|---|---|
| cd_tl_ceiling | 9% |
| cd_e200 | 8% |
| stop_pct | 6% |
| cd_tl_support | 5% |
| cd_macd_line | 5% |
| cd_macd_h | 5% |
| cd_liq_ahead | 4% |
| cd_liq_behind | 3% |
| cd_e50 | 3% |
| to_target | 3% |
| mfe | 3% |
| cd_vol | 2% |
| cd_tl_ceiling_n | 2% |
| mae | 2% |
| cd_rsi | 2% |
| cd_macd_slope | 2% |
| c4_eq_behind | 2% |
| r_now | 2% |
| cd_bb | 2% |
| cd_e20 | 2% |

## Does the model see anything? (trained on trades ended before Nov 2023, tested on 2024 - Oct 2025)

Rank correlation between predicted and actual gain from holding: **+0.020** (43,048 4h closes). If the model saw something, the actual gain would rise from group 1 to group 10.

| group (1 = model most wants to exit) | predicted gain from holding | actual gain from holding | 4h closes |
|---|---|---|---|
| 1 | -0.68 | +0.33 | 4,305 |
| 2 | -0.34 | +0.32 | 4,305 |
| 3 | -0.22 | +0.27 | 4,305 |
| 4 | -0.13 | +0.15 | 4,304 |
| 5 | -0.04 | +0.11 | 4,305 |
| 6 | +0.05 | +0.11 | 4,305 |
| 7 | +0.14 | +0.13 | 4,304 |
| 8 | +0.25 | +0.19 | 4,305 |
| 9 | +0.41 | +0.24 | 4,305 |
| 10 | +0.80 | +0.47 | 4,305 |

## Your failure signals on their own (2022 - Oct 2025): average gain from HOLDING after the signal

Positive = holding on to the stop / target still earned more than closing at that close.

| signal at a 4h close | 4h closes | gain from holding when present | when absent |
|---|---|---|---|
| 1h failure (lower high, close below pullback low) on this close | 17396 | +0.13 | +0.20 |
| 1h failure after the trade was +0.5R | 12325 | +0.14 | +0.20 |
| 4h failure on this close | 6702 | +0.15 | +0.20 |
| daily failure since the peak | 24540 | +0.37 | +0.14 |
| 3+ 4h rejections at the trade's top | 59165 | +0.25 | +0.13 |
| sweep of the top (wick above, close back below), 4h | 83439 | +0.20 | +0.17 |
| v3.1 trades: daily failure since the peak | 15608 | +0.48 | +0.37 |

