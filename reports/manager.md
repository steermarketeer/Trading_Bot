# Machine-learning trade manager: your failure concepts as measurements, the machine combines them

At every 4h close inside a trade the model predicts what holding earns versus closing now (after costs). It exits at the first close where holding is predicted to lose more than a margin chosen on earlier years. Every number below is out-of-sample: each year is managed by a model trained only on earlier years; the holdout (Nov 2025 on) last. **win % = profit after costs.**

Margins chosen per period (exit when predicted gain from holding < margin, in R):

| period | margin | training trades | training 4h closes |
|---|---|---|---|
| 2022 | -1.00 | 2028 | 15293 |
| 2023 | -1.00 | 3686 | 33009 |
| 2024 | -1.00 | 5929 | 60265 |
| 2025 | -1.00 | 7681 | 79525 |
| holdout | -1.00 | 9307 | 100454 |

## Hold to stop / target vs the machine-learning manager

| trades | period | n | win % (hold) | avg R (hold) | win % (ML manager) | avg R (ML manager) | closed early by ML | account (hold) | worst drop | account (ML) | worst drop |
|---|---|---|---|---|---|---|---|---|---|---|---|
| v3.1 after journal filters, entry at signal, fixed target | 2022 - Oct 2025 | 129 | 57% | +0.71 | 57% | +0.71 | 1% | 13.89x | -16% | 13.99x | -16% |
| v3.1 after journal filters, entry at signal, fixed target | holdout | 33 | 58% | +0.68 | 58% | +0.68 | 0% | 1.87x | -13% | 1.87x | -13% |
| v3.1 filtered, bounce stop below 0.786 + strong breaking candle | 2022 - Oct 2025 | 100 | 59% | +0.83 | 59% | +0.79 | 3% | 9.08x | -12% | 8.48x | -12% |
| v3.1 filtered, bounce stop below 0.786 + strong breaking candle | holdout | 27 | 70% | +1.28 | 70% | +1.28 | 0% | 2.31x | -8% | 2.31x | -8% |
| v3.1 filtered: 1D bounces only (base) | 2022 - Oct 2025 | 51 | 49% | +0.67 | 49% | +0.68 | 2% |  |  |  |  |
| v3.1 filtered: 1D bounces only (base) | holdout | 11 | 55% | +0.65 | 55% | +0.65 | 0% |  |  |  |  |
| v3.1 filtered: breakouts only (base) | 2022 - Oct 2025 | 78 | 62% | +0.74 | 62% | +0.74 | 0% |  |  |  |  |
| v3.1 filtered: breakouts only (base) | holdout | 22 | 59% | +0.69 | 59% | +0.69 | 0% |  |  |  |  |
| all main-rule signals (2 : 1) | 2022 - Oct 2025 | 6743 | 35% | -0.09 | 35% | -0.09 | 0% |  |  |  |  |
| all main-rule signals (2 : 1) | holdout | 1658 | 32% | -0.19 | 32% | -0.19 | 0% |  |  |  |  |

## By year (v3.1 filtered, entry at signal, fixed target)

| period | trades | win % hold | avg R hold | win % ML | avg R ML |
|---|---|---|---|---|---|
| 2022 | 26 | 69% | +1.19 | 69% | +1.20 |
| 2023 | 29 | 45% | +0.19 | 45% | +0.19 |
| 2024 | 39 | 54% | +0.61 | 54% | +0.61 |
| 2025 | 35 | 60% | +0.90 | 60% | +0.90 |
| holdout | 33 | 58% | +0.68 | 58% | +0.68 |

## What the manager leans on most (holdout model)

| input | share of the model's decisions |
|---|---|
| cd_e200 | 10% |
| cd_tl_ceiling | 8% |
| cd_tl_support | 6% |
| cd_macd_line | 6% |
| stop_pct | 6% |
| cd_liq_ahead | 5% |
| cd_macd_h | 4% |
| cd_e50 | 4% |
| cd_liq_behind | 4% |
| cd_vol | 3% |
| cd_rsi | 2% |
| cd_macd_slope | 2% |
| cd_tl_ceiling_n | 2% |
| mfe | 2% |
| c4_eq_behind | 2% |
| r_now | 2% |
| cd_bb | 2% |
| cd_close_pos | 2% |
| mae | 2% |
| c4_eq_ahead | 2% |

## Does the model see anything? (trained on trades ended before Nov 2023, tested on 2024 - Oct 2025)

Rank correlation between predicted and actual gain from holding: **-0.029** (40,316 4h closes). If the model saw something, the actual gain would rise from group 1 to group 10.

| group (1 = model most wants to exit) | predicted gain from holding | actual gain from holding | 4h closes |
|---|---|---|---|
| 1 | -0.49 | +0.26 | 4,032 |
| 2 | -0.30 | +0.14 | 4,032 |
| 3 | -0.19 | +0.14 | 4,031 |
| 4 | -0.10 | +0.19 | 4,032 |
| 5 | -0.02 | +0.12 | 4,031 |
| 6 | +0.07 | +0.06 | 4,032 |
| 7 | +0.15 | +0.01 | 4,031 |
| 8 | +0.25 | +0.08 | 4,032 |
| 9 | +0.39 | +0.07 | 4,031 |
| 10 | +0.65 | +0.20 | 4,032 |

## Your failure signals on their own (2022 - Oct 2025): average gain from HOLDING after the signal

Positive = holding on to the stop / target still earned more than closing at that close.

| signal at a 4h close | 4h closes | gain from holding when present | when absent |
|---|---|---|---|
| 1h failure (lower high, close below pullback low) on this close | 16802 | +0.09 | +0.14 |
| 1h failure after the trade was +0.5R | 11660 | +0.10 | +0.14 |
| 4h failure on this close | 6415 | +0.13 | +0.13 |
| daily failure since the peak | 20647 | +0.28 | +0.10 |
| 3+ 4h rejections at the trade's top | 51310 | +0.15 | +0.12 |
| sweep of the top (wick above, close back below), 4h | 75368 | +0.12 | +0.16 |
| v3.1 trades: daily failure since the peak | 11277 | +0.35 | +0.24 |

